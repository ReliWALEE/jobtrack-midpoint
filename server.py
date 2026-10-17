"""JobTrack midpoint: dependency-free HTTP API with SQLite persistence."""
import argparse, json, os, sqlite3, threading
from datetime import date, datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parent
STATUSES = ('Saved', 'Applied', 'Interview', 'Offer', 'Rejected')
TYPES = ('Full-time', 'Part-time', 'Contract', 'Internship')
FIELDS = ('company','title','location','salary','employment_type','status','applied_date','url','notes')

def connect(path):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    return db

def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute("""CREATE TABLE IF NOT EXISTS applications (
          id INTEGER PRIMARY KEY, company TEXT NOT NULL, title TEXT NOT NULL,
          location TEXT NOT NULL, salary INTEGER, employment_type TEXT NOT NULL,
          status TEXT NOT NULL, applied_date TEXT NOT NULL, url TEXT NOT NULL,
          notes TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")

def validate(data):
    if not isinstance(data, dict): raise ValueError('Expected a JSON object')
    if set(data) - set(FIELDS): raise ValueError('Unknown application field')
    out = {}
    for key in FIELDS:
        value = data.get(key, {'status':'Saved','employment_type':'Full-time','applied_date':date.today().isoformat()}.get(key,''))
        if key == 'salary':
            if value is None or value == '': value = None
            elif isinstance(value,bool) or not isinstance(value,int) or not 0 <= value <= 10000000:
                raise ValueError('Salary must be an annual USD integer between 0 and 10000000')
        else:
            if not isinstance(value,str) or len(value)>5000: raise ValueError(f'Invalid {key}')
            value=value.strip()
        out[key]=value
    if not out['company'] or not out['title']: raise ValueError('Company and title are required')
    if out['status'] not in STATUSES: raise ValueError('Invalid status')
    if out['employment_type'] not in TYPES: raise ValueError('Invalid employment type')
    try: date.fromisoformat(out['applied_date'])
    except ValueError: raise ValueError('Use a valid YYYY-MM-DD date')
    if out['url'] and (urlsplit(out['url']).scheme not in ('http','https') or not urlsplit(out['url']).netloc):
        raise ValueError('URL must start with http:// or https://')
    return out

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT/'web'),**kwargs)
    def respond(self, code, value):
        body=json.dumps(value).encode(); self.send_response(code)
        self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/health':
            with connect(self.server.db_path) as db: db.execute('SELECT 1')
            return self.respond(200,{'status':'ok','database':'sqlite'})
        if path=='/api/applications':
            try:
                q=parse_qs(urlsplit(self.path).query); clauses=[]; params=[]
                for key in ('status','employment_type'):
                    if q.get(key,[''])[0]: clauses.append(key+' = ?'); params.append(q[key][0])
                for key,op in (('salary_min','>='),('salary_max','<=')):
                    if q.get(key,[''])[0]:
                        bound=int(q[key][0])
                        if not 0 <= bound <= 10000000: raise ValueError('Salary bounds must be between 0 and 10000000')
                        clauses.append('salary '+op+' ?'); params.append(bound)
                if q.get('q',[''])[0]:
                    clauses.append('(company LIKE ? OR title LIKE ? OR location LIKE ?)'); params.extend(['%'+q['q'][0]+'%']*3)
                sort=q.get('sort',['updated_at'])[0]; direction=q.get('direction',['desc'])[0]
                if sort not in ('company','title','salary','applied_date','updated_at','status'): raise ValueError('Invalid sort')
                if direction not in ('asc','desc'): raise ValueError('Invalid direction')
                sql='SELECT * FROM applications'+(' WHERE '+' AND '.join(clauses) if clauses else '')
                sql+=f' ORDER BY {sort} IS NULL, {sort} {direction}, id DESC'
                with connect(self.server.db_path) as db: rows=[dict(x) for x in db.execute(sql,params)]
                return self.respond(200,rows)
            except ValueError as e: return self.respond(400,{'error':str(e)})
        if path.startswith('/api/'): return self.respond(404,{'error':'Not found'})
        return super().do_GET()
    def mutate(self,method):
        path=urlsplit(self.path).path
        try:
            item_id=None
            if method!='POST':
                pieces=path.strip('/').split('/')
                if len(pieces)!=3 or pieces[:2]!=['api','applications']: return self.respond(404,{'error':'Not found'})
                item_id=int(pieces[2])
            elif path!='/api/applications': return self.respond(404,{'error':'Not found'})
            # Same-origin JSON writes only. The extension opens a reviewed draft in the dashboard.
            origin=self.headers.get('Origin')
            if origin and origin not in ('http://'+self.headers.get('Host',''),'https://'+self.headers.get('Host','')):
                return self.respond(403,{'error':'Cross-origin writes are blocked'})
            with connect(self.server.db_path) as db:
                if item_id is not None and not db.execute('SELECT id FROM applications WHERE id=?',(item_id,)).fetchone():
                    return self.respond(404,{'error':'Application not found'})
                if method=='DELETE':
                    db.execute('DELETE FROM applications WHERE id=?',(item_id,)); db.commit(); return self.respond(200,{'deleted':item_id})
                if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.respond(415,{'error':'Use application/json'})
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=65536: return self.respond(413,{'error':'Body must be 1–65536 bytes'})
                data=validate(json.loads(self.rfile.read(size)))
                now=datetime.now(timezone.utc).isoformat()
                if method=='POST':
                    cursor=db.execute('INSERT INTO applications ('+','.join(FIELDS)+',created_at,updated_at) VALUES ('+','.join('?' for _ in range(11))+')',[*data.values(),now,now]); item_id=cursor.lastrowid
                else: db.execute('UPDATE applications SET '+','.join(k+'=?' for k in FIELDS)+',updated_at=? WHERE id=?', [*data.values(),now,item_id])
                db.commit(); result=dict(db.execute('SELECT * FROM applications WHERE id=?',(item_id,)).fetchone())
            return self.respond(201 if method=='POST' else 200,result)
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e: return self.respond(400,{'error':str(e)})
    def do_POST(self): self.mutate('POST')
    def do_PUT(self): self.mutate('PUT')
    def do_DELETE(self): self.mutate('DELETE')

def create_server(host='127.0.0.1',port=8000,db_path=None):
    db_path=str(db_path or os.environ.get('JOBTRACK_DB',ROOT/'data/jobtrack.sqlite3')); initialize(db_path)
    server=ThreadingHTTPServer((host,port),Handler); server.db_path=db_path; return server
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--host',default='127.0.0.1'); parser.add_argument('--port',type=int,default=8000); args=parser.parse_args()
    server=create_server(args.host,args.port); print(f'JobTrack: http://{args.host}:{server.server_port}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()

import json, tempfile, threading, unittest, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import create_server

class API(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/'db.sqlite3'; self.start()
 def start(self):
  self.server=create_server(port=0,db_path=self.path); self.thread=threading.Thread(target=self.server.serve_forever); self.thread.start(); self.base='http://127.0.0.1:'+str(self.server.server_port)
 def stop(self):
  self.server.shutdown(); self.server.server_close(); self.thread.join()
 def tearDown(self): self.stop(); self.tmp.cleanup()
 def call(self,method='GET',path='/api/applications',data=None,headers=None):
  hdr={'Content-Type':'application/json'}; hdr.update(headers or {})
  req=Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers=hdr)
  try:
   with urlopen(req) as r:return r.status,json.load(r)
  except HTTPError as e:return e.code,json.load(e)
 def add(self,**kw):
  data={'company':'Example','title':'Engineer','salary':90000,'status':'Applied','employment_type':'Full-time','applied_date':'2026-10-16'};data.update(kw);return self.call('POST',data=data)
 def test_crud(self):
  code,row=self.add();self.assertEqual(code,201);i=row['id'];self.assertEqual(len(self.call()[1]),1)
  update={k:v for k,v in row.items() if k not in ('id','created_at','updated_at')};update['status']='Interview'
  self.assertEqual(self.call('PUT',f'/api/applications/{i}',update)[1]['status'],'Interview')
  self.assertEqual(self.call('DELETE',f'/api/applications/{i}')[0],200);self.assertEqual(self.call()[1],[])
 def test_restart_persistence(self):
  self.add();self.stop();self.start();self.assertEqual(self.call()[1][0]['company'],'Example')
 def test_combined_filters(self):
  self.add();self.add(company='Other',status='Saved',employment_type='Contract',salary=150000)
  self.assertEqual(len(self.call(path='/api/applications?status=Applied&employment_type=Full-time&salary_min=80000&salary_max=100000&q=Engineer')[1]),1)
 def test_salary_sort_and_unknown_last(self):
  for value in (None,100000,50000):self.add(salary=value)
  self.assertEqual([x['salary'] for x in self.call(path='/api/applications?sort=salary&direction=asc')[1]],[50000,100000,None])
  self.assertEqual([x['salary'] for x in self.call(path='/api/applications?sort=salary&direction=desc')[1]],[100000,50000,None])
 def test_unknown_salary_excluded(self):
  self.add(salary=None);self.assertEqual(self.call(path='/api/applications?salary_min=0')[1],[])
 def test_invalid_fields(self):
  for data in ({'company':''},{'status':'Bad'},{'salary':-1},{'salary':1.5},{'salary':True},{'employment_type':'Bad'},{'url':'javascript:alert(1)'},{'applied_date':'2026-02-30'}):
   with self.subTest(data=data):self.assertEqual(self.add(**data)[0],400)
 def test_missing_and_bad_routes(self):
  self.assertEqual(self.call('DELETE','/api/applications/999')[0],404);self.assertEqual(self.call(path='/api/nope')[0],404)
 def test_injection_and_bad_query(self):
  self.add(company="Robert'); DROP TABLE applications;--")
  self.assertEqual(len(self.call()[1]),1)
  self.assertEqual(self.call(path='/api/applications?sort=DROP')[0],400)
  self.assertEqual(self.call(path='/api/applications?salary_min=abc')[0],400)
  self.assertEqual(self.call(path='/api/applications?salary_min=99999999999999999999999')[0],400)
 def test_cross_origin_block(self):self.assertEqual(self.call('POST',data={'company':'X','title':'Y'},headers={'Origin':'https://evil.example'})[0],403)
 def test_invalid_json_and_media(self):
  self.assertEqual(self.call('POST',data={'company':'X','title':'Y'},headers={'Content-Type':'text/plain'})[0],415)
  self.assertEqual(self.call('POST',data=[])[0],400)
 def test_health(self):
  self.assertEqual(self.call(path='/api/health')[1]['database'],'sqlite')
if __name__=='__main__':unittest.main()

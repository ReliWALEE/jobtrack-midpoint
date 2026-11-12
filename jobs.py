"""Job discovery through provider APIs, with persistent caching and safe imports."""
import hashlib
import json
import os
import socket
import sqlite3
import threading
import time
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

KEY_PATH = Path(__file__).resolve().with_name('.env')

def configured_key():
    """Read only this setting; never execute or export dotenv file contents."""
    if 'JSEARCH_API_KEY' in os.environ:
        return os.environ['JSEARCH_API_KEY'].strip()
    try:
        for line in KEY_PATH.read_text(encoding='utf-8').splitlines():
            name, separator, value = line.partition('=')
            if separator and name.strip() == 'JSEARCH_API_KEY':
                return value.strip().strip('\"\'')
    except (OSError, UnicodeError):
        pass
    return ''

REMOTIVE_URL = 'https://remotive.com/api/remote-jobs'
JSEARCH_URL = 'https://api.openwebninja.com/jsearch/search-v2'
TYPE_MAP = {'full_time': 'Full-time', 'fulltime': 'Full-time', 'full-time': 'Full-time',
            'part_time': 'Part-time', 'parttime': 'Part-time', 'part-time': 'Part-time',
            'contract': 'Contract', 'contractor': 'Contract', 'internship': 'Internship', 'intern': 'Internship'}

class ProviderError(Exception):
    pass

def safe_url(value):
    if not isinstance(value, str) or len(value) > 5000:
        return ''
    try:
        parts = urlsplit(value)
        return value if parts.scheme in ('http', 'https') and parts.netloc and not parts.username else ''
    except ValueError:
        return ''

def string(value, limit=1000):
    return value[:limit].strip() if isinstance(value, str) else ''

def normalize(item, provider, publisher=''):
    """Keep source provenance; never turn a range/hourly/foreign salary into annual USD."""
    if not isinstance(item, dict):
        return None
    if provider == 'remotive':
        title, company = item.get('title'), item.get('company_name')
        url = safe_url(item.get('url'))
        location = string(item.get('candidate_required_location')) or 'Remote'
        employment = item.get('job_type', '')
        salary_label = string(item.get('salary')) or 'Not listed'
        salary = None
        source, source_id = 'Remotive', item.get('id')
        posted = string(item.get('publication_date'))
    else:
        title, company = item.get('job_title'), item.get('employer_name')
        source = string(item.get('job_publisher')) or 'JSearch'
        url = safe_url(item.get('job_apply_link'))
        # Preserve the selected publisher's link when multiple boards carry the same job.
        if publisher:
            options = [x for x in item.get('apply_options', []) if isinstance(x, dict)] if isinstance(item.get('apply_options', []), list) else []
            matching = next((x for x in options if string(x.get('publisher')).lower() == publisher and safe_url(x.get('apply_link'))), None)
            if matching:
                source, url = string(matching['publisher']), safe_url(matching['apply_link'])
            elif source.lower() != publisher:
                return None
        location = string(item.get('job_location')) or ', '.join(string(item.get(k)) for k in ('job_city', 'job_state', 'job_country') if string(item.get(k)))
        employment = item.get('job_employment_type', '')
        salary_label = string(item.get('job_salary_string')) or 'Not listed'
        low, high = item.get('job_min_salary'), item.get('job_max_salary')
        currency, period = item.get('job_salary_currency'), item.get('job_salary_period')
        salary = low if type(low) is int and low == high and 0 <= low <= 10000000 and currency == 'USD' and period == 'YEAR' else None
        if salary_label == 'Not listed' and type(low) in (int, float) and type(high) in (int, float):
            salary_label = f'{currency or "Currency unspecified"} {low:,}–{high:,} / {period or "period unspecified"}'
        source_id = item.get('job_id')
        posted = string(item.get('job_posted_at_datetime_utc'))
    title, company = string(title), string(company)
    if not title or not company or not url:
        return None
    identity = provider + ':' + str(source_id or url) + ':' + url
    return {'id': hashlib.sha256(identity.encode()).hexdigest()[:32], 'title': title, 'company': company,
            'location': location, 'employment_type': TYPE_MAP.get(string(employment).lower(), 'Not specified'),
            'salary': salary, 'salary_label': salary_label, 'source': source, 'provider': provider,
            'url': url, 'posted_at': posted}

class JobDiscovery:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        self.lock = threading.Lock()
        with closing(sqlite3.connect(self.db_path)) as db, db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS job_cache (cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL, fetched_at REAL NOT NULL, attempted_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS discovered_jobs (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS job_imports (job_id TEXT PRIMARY KEY, application_id INTEGER NOT NULL);
            ''')

    def sources(self):
        configured = bool(configured_key())
        return {'sources': [
            {'id': 'remotive', 'name': 'Remotive · remote jobs', 'ready': True},
            {'id': 'jsearch', 'name': 'All boards · JSearch', 'ready': configured},
            {'id': 'indeed', 'name': 'Indeed · via JSearch', 'ready': configured},
            {'id': 'linkedin', 'name': 'LinkedIn · via JSearch', 'ready': configured}],
            'jsearch_ready': configured}

    def fetch(self, url, key=None):
        headers = {'Accept': 'application/json', 'User-Agent': 'JobTrack/1.1 (personal job discovery)'}
        if key:
            headers['x-api-key'] = key
        try:
            with urlopen(Request(url, headers=headers), timeout=15) as response:
                data = response.read(8_000_001)
                if len(data) > 8_000_000:
                    raise ProviderError('The job source returned too much data. Try again later.')
                return json.loads(data)
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise ProviderError('The job source rejected access. Check your API key and plan.') from None
            if exc.code == 429:
                raise ProviderError('The job source reached its request limit. Please try later.') from None
            raise ProviderError('The job source is temporarily unavailable. Please try later.') from None
        except (URLError, TimeoutError, socket.timeout, UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError('Could not reach the job source. Check your connection and try later.') from None

    def search(self, provider='remotive', query='', location=''):
        if provider not in ('remotive', 'jsearch', 'indeed', 'linkedin'):
            raise ValueError('Unknown job source')
        if len(query) > 200 or len(location) > 200:
            raise ValueError('Search and location must each be at most 200 characters')
        query, location = query.strip(), location.strip()
        key = configured_key()
        if provider != 'remotive' and not key:
            raise ProviderError('Connect a JSearch API key to search Indeed, LinkedIn, and other boards. Remotive remote jobs work without an account.')
        if provider != 'remotive' and not query:
            raise ValueError('Enter a job title or keyword')
        # One global Remotive fetch per six hours; filtering happens locally.
        cache_key = 'remotive' if provider == 'remotive' else json.dumps([provider, query.lower(), location.lower()])
        ttl = 21600 if provider == 'remotive' else 900
        warning = ''
        with self.lock, closing(sqlite3.connect(self.db_path)) as db, db:
            now = time.time()
            cache = db.execute('SELECT payload, fetched_at, attempted_at FROM job_cache WHERE cache_key=?', (cache_key,)).fetchone()
            rows = json.loads(cache[0]) if cache else []
            fetched = cache[1] if cache else 0
            if not cache or now - cache[2] >= ttl:
                try:
                    if provider == 'remotive':
                        data = self.fetch(REMOTIVE_URL)
                        raw = data.get('jobs') if isinstance(data, dict) else None
                    else:
                        text = query + (' in ' + location if location else '')
                        if provider in ('indeed', 'linkedin'):
                            text += ' via ' + provider
                        data = self.fetch(JSEARCH_URL + '?' + urlencode({'query': text, 'country': 'us', 'language': 'en', 'page': 1, 'num_pages': 1}), key)
                        raw = data.get('data') if isinstance(data, dict) else None
                        if isinstance(raw, dict):
                            raw = raw.get('jobs')  # search-v2 wraps jobs with a pagination cursor
                    if not isinstance(raw, list):
                        raise ProviderError('The job source returned an unexpected response. Try again later.')
                    rows = [job for item in raw if (job := normalize(item, 'remotive' if provider == 'remotive' else 'jsearch', provider if provider in ('indeed', 'linkedin') else ''))]
                    rows = list({job['id']: job for job in rows}.values())
                    fetched = now
                except ProviderError as exc:
                    if not cache:
                        # Cache a failed attempt briefly rather than hammer the provider on every click.
                        db.execute('INSERT INTO job_cache VALUES (?,?,?,?)', (cache_key, '[]', 0, now - ttl + 60))
                        db.commit()
                        raise
                    warning = str(exc) + ' Showing previously fetched listings; availability may have changed.'
                db.execute('INSERT OR REPLACE INTO job_cache VALUES (?,?,?,?)', (cache_key, json.dumps(rows), fetched, now))
            if not fetched:
                raise ProviderError('The job source could not be loaded. Wait a minute before trying again.')
            db.executemany('INSERT OR REPLACE INTO discovered_jobs VALUES (?,?)', [(row['id'], json.dumps(row)) for row in rows])
            saved_ids = {r[0] for r in db.execute('SELECT job_id FROM job_imports JOIN applications ON applications.id=job_imports.application_id')}
            saved_urls = {r[0] for r in db.execute("SELECT url FROM applications WHERE url<>''")}
        if now - fetched >= ttl and not warning:
            warning = 'Showing previously fetched listings because the source could not be refreshed. Availability may have changed.'
        if provider == 'remotive':
            words = query.lower().split()
            rows = [r for r in rows if all(word in (r['title']+' '+r['company']).lower() for word in words)
                    and (not location or location.lower() in r['location'].lower())]
        total = len(rows)
        return {'jobs': [dict(r, saved=r['id'] in saved_ids or r['url'] in saved_urls) for r in rows[:50]],
                'total': total, 'fetched_at': datetime.fromtimestamp(fetched, timezone.utc).isoformat(),
                'cached': bool(cache and fetched == cache[1]), 'warning': warning,
                'notice': ('Remote listings from Remotive, delayed by 24 hours. Location means eligibility; check each posting. Feed refreshes at most every six hours.' if provider == 'remotive' else 'Listings supplied by JSearch. Publisher coverage varies; check the original posting. Searches are cached for 15 minutes.')}

    def save(self, job_id):
        with self.lock, closing(sqlite3.connect(self.db_path)) as db, db:
            db.row_factory = sqlite3.Row
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT payload FROM discovered_jobs WHERE id=?', (job_id,)).fetchone()
            if not row:
                raise LookupError('Listing not found. Search again to load it.')
            job = json.loads(row[0])
            existing = db.execute('SELECT applications.* FROM applications LEFT JOIN job_imports ON applications.id=job_imports.application_id WHERE job_imports.job_id=? OR applications.url=? LIMIT 1', (job_id, job['url'])).fetchone()
            if existing:
                return dict(existing), False
            now = datetime.now(timezone.utc).isoformat()
            notes = f"Source: {job['source']} (via {job['provider']}). Listed salary: {job['salary_label']}. Review the original posting before applying."
            cursor = db.execute('INSERT INTO applications (company,title,location,salary,employment_type,status,applied_date,url,notes,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                                (job['company'], job['title'], job['location'], job['salary'], job['employment_type'], 'Saved', date.today().isoformat(), job['url'], notes, now, now))
            db.execute('INSERT OR REPLACE INTO job_imports VALUES (?,?)', (job_id, cursor.lastrowid))
            result = dict(db.execute('SELECT * FROM applications WHERE id=?', (cursor.lastrowid,)).fetchone())
            return result, True

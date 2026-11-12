"""Discovery contract tests use fixtures; the suite never calls a paid/live API."""
import json
import os
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jobs import JobDiscovery, ProviderError, normalize
from server import create_server, database

REMOTE = {'id': 42, 'title': 'Python Engineer', 'company_name': 'Example',
          'url': 'https://remotive.com/remote-jobs/software-dev/example-42',
          'candidate_required_location': 'United States', 'job_type': 'full_time',
          'salary': '$90,000–$120,000', 'publication_date': '2026-11-10T12:00:00'}
BROAD = {'job_id': 'abc', 'job_title': 'Developer', 'employer_name': 'Example',
         'job_apply_link': 'https://www.linkedin.com/jobs/view/123', 'job_publisher': 'LinkedIn',
         'job_location': 'Chicago, IL', 'job_employment_type': 'FULLTIME',
         'job_min_salary': 100000, 'job_max_salary': 100000,
         'job_salary_currency': 'USD', 'job_salary_period': 'YEAR'}

class Discovery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'jobs.sqlite3'
        self.server = create_server(port=0, db_path=self.path)
        self.jobs = self.server.jobs
        self.env = patch.dict(os.environ, {'JSEARCH_API_KEY': ''})
        self.env.start()
    def tearDown(self):
        self.env.stop(); self.server.server_close(); self.tmp.cleanup()
    def test_remotive_fetch_once_and_filter_locally(self):
        with patch.object(self.jobs, 'fetch', return_value={'jobs':[REMOTE, dict(REMOTE, id=43, title='Designer', url='https://remotive.com/43')]}) as fetch:
            result = self.jobs.search(query='python', location='United States')
            self.assertEqual(len(result['jobs']), 1)
            self.assertIsNone(result['jobs'][0]['salary'])
            self.assertEqual(self.jobs.search(query='designer')['total'], 1)
            self.assertEqual(self.jobs.search(location='Berlin')['total'], 0)
            self.assertEqual(fetch.call_count, 1)
        # Persistent cache survives server restart and contains real provider attribution.
        with patch.object(JobDiscovery, 'fetch', side_effect=AssertionError('must use cache')):
            result = JobDiscovery(self.path).search()
            self.assertTrue(result['cached']); self.assertEqual(result['jobs'][0]['source'], 'Remotive')
    def test_save_idempotent_and_preserve_edits(self):
        with patch.object(self.jobs, 'fetch', return_value={'jobs':[REMOTE]}):
            job = self.jobs.search()['jobs'][0]
        first, created = self.jobs.save(job['id']); self.assertTrue(created)
        with database(self.path) as db:
            db.execute("UPDATE applications SET status='Interview',notes='My note' WHERE id=?", (first['id'],))
        second, created = self.jobs.save(job['id'])
        self.assertFalse(created); self.assertEqual(second['id'], first['id'])
        self.assertEqual(second['status'], 'Interview'); self.assertEqual(second['notes'], 'My note')
        self.assertTrue(self.jobs.search()['jobs'][0]['saved'])
        with database(self.path) as db: db.execute('DELETE FROM applications WHERE id=?', (first['id'],))
        self.assertFalse(self.jobs.search()['jobs'][0]['saved'])
        self.assertTrue(self.jobs.save(job['id'])[1])
    def test_concurrent_save_and_duplicate_url(self):
        with patch.object(self.jobs, 'fetch', return_value={'jobs':[REMOTE]}):
            job = self.jobs.search()['jobs'][0]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(self.jobs.save, [job['id'],job['id']]))
        self.assertEqual(sum(created for _, created in results), 1)
        with database(self.path) as db: self.assertEqual(db.execute('SELECT count(*) FROM applications').fetchone()[0], 1)
    def test_missing_key_and_invalid_query_never_fetch(self):
        with patch.object(self.jobs, 'fetch') as fetch:
            for source in ('jsearch','indeed','linkedin'):
                with self.assertRaises(ProviderError): self.jobs.search(source, 'engineer')
            with self.assertRaises(ValueError): self.jobs.search('bad')
            with self.assertRaises(ValueError): self.jobs.search(query='x'*201)
            fetch.assert_not_called()
        self.assertFalse(self.jobs.sources()['jsearch_ready'])
    def test_jsearch_query_key_and_publisher_selection(self):
        with patch.dict(os.environ, {'JSEARCH_API_KEY':'test-key'}), patch.object(self.jobs,'fetch',return_value={'data':[BROAD]}) as fetch:
            row = self.jobs.search('linkedin','developer','Chicago')['jobs'][0]
            self.assertEqual(row['source'], 'LinkedIn'); self.assertEqual(row['salary'], 100000)
            url, key = fetch.call_args.args
            self.assertIn('via+linkedin', url); self.assertIn('Chicago', url); self.assertEqual(key,'test-key')
            self.assertNotIn('test-key', url)
            self.assertTrue(self.jobs.sources()['jsearch_ready'])
            self.assertEqual(self.jobs.search('linkedin','developer','Chicago')['total'], 1)
            self.assertEqual(fetch.call_count, 1)
    def test_failure_retry_throttle_and_stale_cache(self):
        with patch.object(self.jobs,'fetch',side_effect=ProviderError('Offline')) as fetch:
            for _ in range(2):
                with self.assertRaises(ProviderError): self.jobs.search()
            self.assertEqual(fetch.call_count, 1)
        with database(self.path) as db: db.execute('DELETE FROM job_cache')
        with patch.object(self.jobs,'fetch',return_value={'jobs':[REMOTE]}): self.jobs.search()
        with database(self.path) as db: db.execute('UPDATE job_cache SET attempted_at=0')
        with patch.object(self.jobs,'fetch',side_effect=ProviderError('Offline')):
            result = self.jobs.search()
            self.assertEqual(len(result['jobs']),1); self.assertIn('previously fetched',result['warning'])
    def test_bad_provider_payload_and_missing_listing(self):
        with patch.object(self.jobs,'fetch',return_value={'error':'bad'}):
            with self.assertRaises(ProviderError): self.jobs.search()
        with self.assertRaises(LookupError): self.jobs.save('unknown')
    def test_fetch_errors_are_safe_and_bounded(self):
        for error in (URLError('secret'), TimeoutError('secret'), HTTPError('https://example.com',429,'secret',{},None), HTTPError('https://example.com',401,'secret',{},None)):
            with self.subTest(error=error), patch('jobs.urlopen',side_effect=error):
                with self.assertRaises(ProviderError) as caught: self.jobs.fetch('https://example.com', 'private-key')
                self.assertNotIn('secret',str(caught.exception)); self.assertNotIn('private-key',str(caught.exception))
    def test_normalize_untrusted_and_salary_units(self):
        for item in (None, {}, dict(REMOTE,url='javascript:alert(1)'),dict(REMOTE,url='https://[bad')):
            self.assertIsNone(normalize(item,'remotive'))
        for changes in ({'job_max_salary':120000},{'job_salary_period':'HOUR'},{'job_salary_currency':'EUR'},{'job_min_salary':True,'job_max_salary':True}):
            self.assertIsNone(normalize(dict(BROAD,**changes),'jsearch')['salary'])
        self.assertEqual(normalize(dict(REMOTE,job_type=''),'remotive')['employment_type'],'Not specified')
        multi = dict(BROAD,apply_options=[{'publisher':'Indeed','apply_link':'https://indeed.com/viewjob?jk=123'}])
        self.assertEqual(normalize(multi,'jsearch','indeed')['url'],'https://indeed.com/viewjob?jk=123')
        self.assertIsNone(normalize(BROAD,'jsearch','indeed'))
    def test_http_contract_cross_origin_save_and_restart(self):
        thread = threading.Thread(target=self.server.serve_forever); thread.start()
        base = f'http://127.0.0.1:{self.server.server_port}'
        try:
            with patch.object(self.jobs,'fetch',return_value={'jobs':[REMOTE]}):
                with urlopen(base+'/api/jobs?q=Python') as r: job=json.load(r)['jobs'][0]
            with urlopen(Request(base+'/api/jobs/'+job['id']+'/save',method='POST')) as r:
                self.assertEqual(r.status,201); result=json.load(r)
            with urlopen(Request(base+'/api/jobs/'+job['id']+'/save',method='POST')) as r:
                self.assertEqual(r.status,200); self.assertFalse(json.load(r)['created'])
            with self.assertRaises(HTTPError) as caught:
                urlopen(Request(base+'/api/jobs/'+job['id']+'/save',method='POST',headers={'Origin':'https://other.example'}))
            self.assertEqual(caught.exception.code,403)
            with urlopen(base+'/api/applications') as r: self.assertEqual(len(json.load(r)),1)
            with urlopen(base+'/api/job-sources') as r: self.assertFalse(json.load(r)['jsearch_ready'])
            self.assertEqual(JobDiscovery(self.path).save(job['id'])[0]['id'],result['application']['id'])
        finally:
            self.server.shutdown(); thread.join()

if __name__ == '__main__': unittest.main()

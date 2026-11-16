"""Account-rotation tests: fixture-driven, never network, never paid APIs."""
import io
import json
import sys
import tempfile
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import account_factory
import jobs
from account_factory import (AccountError, Response, acquire_run_key,
                             create_mailbox, exchange_api_key,
                             extract_verification_link, fetch_access_token,
                             parse_hidden_fields, primary_form, remember_account,
                             signup_openwebninja)

SIGNUP_PAGE = '''<form data-form-primary="true" method="POST">
  <input type="hidden" name="state" value="S-123_abc">
  <input type="hidden" name="passwordPolicy.isFlexible" value="false">
  <input type="hidden" name="strengthPolicy" value="good">
  <input type="hidden" name="complexityOptions.minLength" value="8">
  <label>Email<input id="email" name="email" type="text"></label>
  <label>Password<input id="password" name="password" type="password"></label>
</form>
<form data-provider="google" method="post">
  <input type="hidden" name="connection" value="google-oauth2">
  <button>Continue with Google</button>
</form>'''

LOGIN_PAGE = '''<form data-form-primary="true" method="POST">
  <input type="hidden" name="state" value="L-987_def">
  <label>Email<input id="username" name="username" type="text"></label>
  <label>Password<input id="password" name="password" type="password"></label>
</form>
<form data-provider="google" method="post">
  <input type="hidden" name="connection" value="google-oauth2">
</form>'''

TICKET_PAGE = '''<html><body><h1>Verify your email</h1>
<form method="POST"><input type="hidden" name="state" value="TICKETSTATE"></form></body></html>'''

VERIFIED_PAGE = '<html><body><h1>Email Verified!</h1><a href="#">Continue</a></body></html>'
VERIFY_URL = 'https://login.openwebninja.com/u/email-verification?ticket=T123'
API_KEY_BODY = '{"apiKey": "KEYFRESH-test-42"}'


class FakeBrowser:
    def __init__(self):
        self.calls = []

        class _Jar:
            def clear(self):
                pass
        self.jar = _Jar()

    def request(self, method, url, data=None, headers=None, json_body=False):
        body = data.decode() if isinstance(data, bytes) else (data or '')
        record = {'method': method, 'url': url, 'body': body}
        self.calls.append(record)

        def route():
            if '/api/auth/signup' in url and method == 'GET':
                return Response(200, 'https://app.openwebninja.com/api/auth/signup', SIGNUP_PAGE)
            if '/u/signup?state=' in url and method == 'POST':
                return Response(200, 'https://app.openwebninja.com/verify-email?email=new@example.test', 'ok')
            if 'email-verification' in url and method == 'GET':
                return Response(200, VERIFY_URL, TICKET_PAGE)
            if 'email-verification' in url and method == 'POST':
                return Response(200, VERIFY_URL, VERIFIED_PAGE)
            if '/api/auth/login' in url and method == 'GET':
                return Response(200, 'https://login.openwebninja.com/u/login?state=L-987_def', LOGIN_PAGE)
            if '/u/login?state=' in url and method == 'POST':
                return Response(200, 'https://app.openwebninja.com/', '<html>Welcome back</html>')
            if '/api/auth/token' in url and method == 'GET':
                return Response(200, account_factory.TOKEN_URL, json.dumps({'accessToken': 'tok_test'}))
            raise AssertionError(f'unexpected request {method} {url}')
        return route()


def fake_mailtm_factory(polls_before_message=1):
    state = {'polls': 0}
    calls = []

    def fake(token, path, payload=None, log=None):
        calls.append((token, path))
        if path == '/domains':
            return {'hydra:member': [{'domain': 'example.test', 'isActive': True}]}
        if path == '/accounts':
            calls[-1] += ('payload', payload['address'])
            return {'id': 'acct-1'}
        if path == '/token':
            return {'token': 'MAILTOKEN'}
        if path == '/messages':
            state['polls'] += 1
            if state['polls'] <= polls_before_message:
                return {'hydra:member': []}
            return {'hydra:member': [{'id': 'm1'}]}
        if path.startswith('/messages/'):
            return {'text': '',
                    'html': [f'<p>Please verify:</p><a href="{VERIFY_URL}">click here</a>']}
        raise AssertionError(path)
    return fake, calls


def fake_key_endpoint(body=API_KEY_BODY):
    """Stands in for urllib's urlopen on the gateway get-or-create call."""
    class Reply:
        status = 200
        def read(self, n=-1):
            return body.encode()
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    def urlopen(req, timeout=0):
        return Reply()
    return urlopen


@patch('account_factory.time.sleep', lambda *_: None)
class AcquisitionHappyPathTests(unittest.TestCase):

    def run_full_flow(self, browser):
        mailtm, calls = fake_mailtm_factory()
        with patch('account_factory.Session', lambda: browser), \
             patch('account_factory._mailtm', mailtm), \
             patch('account_factory.urllib.request.urlopen', fake_key_endpoint()):
            with tempfile.TemporaryDirectory() as tmp:
                db_path = Path(tmp) / 'jobtrack.sqlite3'
                key = acquire_run_key(log=lambda *_: None, persist_path=db_path)
        return key

    def test_returns_fresh_api_key_and_persists_account(self):
        key = self.run_full_flow(FakeBrowser())
        self.assertEqual(key, 'KEYFRESH-test-42')

    def test_signup_post_copies_only_primary_form_fields(self):
        browser = FakeBrowser()
        self.run_full_flow(browser)
        signup_posts = [c for c in browser.calls if c['method'] == 'POST' and '/u/signup?state=' in c['url']]
        self.assertEqual(len(signup_posts), 1)
        fields = dict(pair.split('=', 1) for pair in signup_posts[0]['body'].split('&'))
        self.assertNotIn('connection', fields)           # social form must not leak in
        self.assertEqual(fields.get('state'), 'S-123_abc')
        self.assertIn('email', fields)
        self.assertIn('password', fields)

    def test_login_post_uses_scraped_state_and_credentials(self):
        browser = FakeBrowser()
        self.run_full_flow(browser)
        login_posts = [c for c in browser.calls if c['method'] == 'POST' and '/u/login?state=' in c['url']]
        self.assertEqual(len(login_posts), 1)
        self.assertIn('username=', login_posts[0]['body'])
        self.assertIn('password=', login_posts[0]['body'])

    def test_persisted_row_lands_in_service_accounts_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / 'jobtrack.sqlite3'
            browser = FakeBrowser()
            mailtm, _ = fake_mailtm_factory()
            with patch('account_factory.Session', lambda: browser), \
                 patch('account_factory._mailtm', mailtm), \
                 patch('account_factory.urllib.request.urlopen', fake_key_endpoint()):
                acquire_run_key(log=lambda *_: None, persist_path=db_path)
            with sqlite3.connect(db_path) as db:
                rows = db.execute('SELECT email, api_key FROM service_accounts').fetchall()
            self.assertEqual(len(rows), 1)
            self.assertTrue(rows[0][0].endswith('@example.test'))
            self.assertEqual(rows[0][1], 'KEYFRESH-test-42')


@patch('account_factory.time.sleep', lambda *_: None)
class RotationFailurePathTests(unittest.TestCase):

    def test_unreadable_signup_page_raises_accounterror(self):
        class Blank(FakeBrowser):
            def request(self, method, url, **kw):
                if '/api/auth/signup' in url:
                    return Response(200, url, '<div>nothing here</div>')
                return super().request(method, url, **kw)
        with patch('account_factory.Session', lambda: Blank()):
            mailtm, _ = fake_mailtm_factory()
            with patch('account_factory._mailtm', mailtm), \
                 self.assertRaises(AccountError) as ctx:
                acquire_run_key(log=lambda *_: None)
        self.assertIn('signup transaction state', str(ctx.exception))

    def test_wrong_signup_landing_raises_accounterror(self):
        class OffScript(FakeBrowser):
            def request(self, method, url, **kw):
                result = super().request(method, url, **kw)
                if '/u/signup?state=' in url and method == 'POST':
                    return Response(200, 'https://login.openwebninja.com/u/signup?state=x', SIGNUP_PAGE)
                return result
        with patch('account_factory.Session', lambda: OffScript()), \
             patch('account_factory._mailtm', *fake_mailtm_factory()[:1]), \
             self.assertRaises(AccountError) as ctx:
            acquire_run_key(log=lambda *_: None)
        self.assertIn('captcha or stricter checks', str(ctx.exception))

    def test_missing_verification_email_times_out_cleanly(self):
        with patch('account_factory.Session', lambda: FakeBrowser()), \
             patch('account_factory._mailtm', side_effect=self.empty_messages()), \
             self.assertRaises(AccountError) as ctx:
            acquire_run_key(log=lambda *_: None)
        self.assertIn('never arrived', str(ctx.exception))

    @staticmethod
    def empty_messages():
        state = {}

        def fake(token, path, payload=None, log=None):
            if path == '/domains':
                return {'hydra:member': [{'domain': 'example.test', 'isActive': True}]}
            if path == '/accounts':
                return {'id': 'a'}
            if path == '/token':
                return {'token': 't'}
            if path == '/messages':
                state.setdefault('n', 0)
                state['n'] += 1
                return {'hydra:member': []}
            raise AssertionError(path)
        return fake

    def test_access_token_absent_raises_accounterror(self):
        class NoToken(FakeBrowser):
            def request(self, method, url, **kw):
                if '/api/auth/token' in url:
                    return Response(200, url, '{}')
                return super().request(method, url, **kw)
        with patch('account_factory.Session', lambda: NoToken()), \
             patch('account_factory._mailtm', *fake_mailtm_factory()[:1]), \
             self.assertRaises(AccountError) as ctx:
            acquire_run_key(log=lambda *_: None)
        self.assertIn('access token', str(ctx.exception))

    def test_exchange_failure_maps_to_accounterror(self):
        error = HTTPError(account_factory.API_KEY_URL, 403, 'Forbidden', {}, io.BytesIO(b'message'))

        def boom(*_a, **_k):
            raise error
        with patch('account_factory.urllib.request.urlopen', boom), \
             self.assertRaises(AccountError) as ctx:
            exchange_api_key('tok')
        self.assertIn('403', str(ctx.exception))


@patch('account_factory.time.sleep', lambda *_: None)
class MailboxCreationTests(unittest.TestCase):

    @staticmethod
    def scripted_urlopen(accounts_outcomes):
        """Serve /domains and /token; replay `accounts_outcomes` on POST /accounts."""
        state = {'accounts_seen': []}

        class Reply:
            def __init__(self, body_bytes):
                self.status = 201
                self.read = lambda n=-1: body_bytes
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False

        def urlopen(req, timeout=0):
            url = req.get_full_url()
            if '/domains' in url:
                return Reply(b'{"hydra:member": [{"domain": "example.test", "isActive": true}]}')
            if '/accounts' in url:
                outcome = accounts_outcomes[len(state['accounts_seen'])] if len(state['accounts_seen']) < len(accounts_outcomes) else 'ok'
                sent = json.loads(req.data.decode())
                state['accounts_seen'].append(sent['address'])
                if outcome == 'ok':
                    return Reply(b'{"id": "acct"}')
                raise HTTPError('https://api.mail.tm/accounts', 422 if outcome == '422' else 429,
                                'Unprocessable Entity', {}, io.BytesIO(b'{"msg":"quota"}'))
            if '/token' in url:
                return Reply(b'{"token": "MAILTOKEN", "id": "acct"}')
            raise AssertionError(url)
        return urlopen, state

    def test_transient_rejections_retry_with_regenerated_identity(self):
        urlopen, state = self.scripted_urlopen(['422', '429', 'ok'])
        with patch('account_factory.urllib.request.urlopen', urlopen):
            address, _password, token = create_mailbox()
        seen = state['accounts_seen']
        self.assertEqual(len(seen), 3)                     # three creation attempts
        self.assertEqual(len(set(seen)), 3)                # identity regenerated each time
        self.assertEqual(address, seen[-1])                # accepted address is the last one
        self.assertEqual(token, 'MAILTOKEN')

    def test_persistent_rejection_raises_accounterror(self):
        urlopen, state = self.scripted_urlopen(['429'] * 9)
        with patch('account_factory._MAILBOX_ATTEMPTS', 5), \
             patch('account_factory.urllib.request.urlopen', urlopen), \
             self.assertRaises(AccountError) as ctx:
            create_mailbox()
        self.assertIn('could not register a free mailbox', str(ctx.exception))
        self.assertEqual(len(state['accounts_seen']), 5)   # bounded attempts


class ParserAndKeyPrecedenceTests(unittest.TestCase):

    def test_parse_hidden_fields_both_attribute_orders_and_entities(self):
        fragment = '<input name="a" value="one&amp;two"><input value=\'three\' name=\'b\'>'
        self.assertEqual(parse_hidden_fields(fragment), {'a': 'one&two', 'b': 'three'})

    def test_primary_form_excludes_google_connection_field(self):
        body = primary_form(SIGNUP_PAGE)
        self.assertIn('name="state"', body)
        self.assertNotIn('connection', body)

    def test_verification_link_found_in_html_only_message(self):
        message = {'text': '', 'html': ['<p>Please verify:</p>',
                                        '<a href="' + VERIFY_URL + '">click here</a>']}
        self.assertEqual(extract_verification_link(message), VERIFY_URL)

    def test_runtime_key_wins_over_env_then_restores(self):
        with patch.object(jobs, 'KEY_PATH', Path('/nonexistent/.env')), \
             patch.dict('os.environ', {'JSEARCH_API_KEY': 'ENVKEY'}):
            previous = jobs.runtime_key()
            try:
                jobs.set_runtime_key('RUNKEY')
                self.assertEqual(jobs.configured_key(), 'RUNKEY')
                jobs.set_runtime_key('')
                self.assertEqual(jobs.configured_key(), 'ENVKEY')
            finally:
                jobs.set_runtime_key(previous)


class PersistenceHelperTests(unittest.TestCase):

    def test_remember_and_last_saved_key_roundtrip_with_retention_cap(self):
        from account_factory import last_saved_key
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / 'jobtrack.sqlite3'
            for index in range(25):
                remember_account(db_path, f'user{index}@example.test', f'key-{index}')
            self.assertEqual(last_saved_key(db_path), 'key-24')  # newest wins
            with sqlite3.connect(db_path) as db:
                count = db.execute('SELECT COUNT(*) FROM service_accounts').fetchone()[0]
            self.assertLessEqual(count, 20)                      # table stays bounded

    def test_last_saved_key_tolerates_missing_db(self):
        from account_factory import last_saved_key
        self.assertIsNone(last_saved_key('/nonexistent/dir/missing.sqlite3'))


if __name__ == '__main__':
    unittest.main()

"""Per-run rotation of disposable OpenWeb Ninja accounts for fresh free credits.

Each JobTrack run creates a throwaway mail.tm mailbox, registers a new
OpenWeb Ninja account through their Auth0 hosted login (driven by parsing the
rendered signup HTML - no headless browser), confirms the emailed
verification ticket, signs back in, and exchanges the dashboard session for
an API key. That key feeds job discovery for the lifetime of the process,
while older runs' credits stay untouched elsewhere.

Everything here is deliberately dependency-free. Automatic startup reports
failure when a fresh account cannot be created; it does not reuse an old key.
"""
import datetime
import http.cookiejar
import json
import re
import secrets
import sqlite3
import string
import time
import urllib.error
import urllib.parse
import urllib.request

APP_BASE = 'https://app.openwebninja.com'
LOGIN_BASE = 'https://login.openwebninja.com'
GATEWAY_BASE = 'https://rpuo5v9cbe.execute-api.us-east-1.amazonaws.com/v1'
API_KEY_URL = GATEWAY_BASE + '/get-or-create-api-key'
TOKEN_URL = APP_BASE + '/api/auth/token'
MAILTM_BASE = 'https://api.mail.tm'
USER_AGENT = 'JobTrack/1.2 (single-user job tracker; rotates its own free-tier account)'


class AccountError(RuntimeError):
    """The per-run account rotation could not be completed."""


class Response:
    def __init__(self, status, url, text):
        self.status = status
        self.url = url
        self.text = text


class Session:
    """Cookie-aware HTTP client whose redirects follow like a browser tab."""

    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def request(self, method, url, data=None, headers=None, json_body=False):
        hdrs = {'User-Agent': USER_AGENT}
        hdrs.update(headers or {})
        payload = None
        if json_body and data is not None:
            payload = json.dumps(data).encode()
            hdrs.setdefault('Content-Type', 'application/json')
        elif data is not None:
            payload = data.encode() if isinstance(data, str) else data
        req = urllib.request.Request(url, data=payload, headers=hdrs, method=method)
        try:
            with self.opener.open(req, timeout=25) as reply:
                return Response(reply.status, reply.geturl(), reply.read(2_000_000).decode('utf-8', 'replace'))
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read(2_000_000).decode('utf-8', 'replace')
            except Exception:
                body = ''
            finally:
                exc.close()
            return Response(exc.code, exc.url or url, body)


# --- parsers kept pure so unit tests need no network -------------------------

def html_unescape(text):
    for entity, char in (('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'), ('&quot;', '"'), ('&#39;', "'")):
        text = text.replace(entity, char)
    return text


def parse_hidden_fields(html_fragment):
    """name/value pairs from <input> tags regardless of attribute order."""
    fields = {}
    for tag in re.finditer(r'<input\b[^>]*>', html_fragment):
        name_match = re.search(r'''(?i)\bname\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))''', tag.group(0))
        if not name_match:
            continue
        name = next((g for g in name_match.groups() if g is not None), '')
        value_match = re.search(r'''(?i)\bvalue\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))''', tag.group(0))
        value = next((g for g in value_match.groups() if g is not None), '') if value_match else ''
        fields[html_unescape(name)] = html_unescape(value)
    return fields


def primary_form(html_text):
    """Body of the email/password universal-login form, excluding social buttons."""
    match = re.search(r'''<form\b[^>]*data-form-primary=["']true["'][^>]*>(.*?)</form>''',
                      html_text, re.S | re.I)
    return match.group(1) if match else ''


def extract_verification_link(message_json):
    """First plausible ticket URL from an email body (plain text, or HTML list/string)."""
    body = message_json.get('text') or ''
    if not str(body).strip():
        raw = message_json.get('html')
        if isinstance(raw, list):
            body = '\n'.join(part for part in raw if isinstance(part, str))
        elif isinstance(raw, str):
            body = raw
    urls = re.findall(r'https?://[^\s"\'<>]+', body)
    candidates = [u for u in urls if 'email-verification' in u]
    return candidates[0] if candidates else None


# --- mail.tm ------------------------------------------------------------------

def _mailtm(token, path, payload=None, log=None):
    """Single mail.tm request; rides out transient 429/422 limits on reads."""
    is_write = payload is not None
    for attempt in range(5):
        req = urllib.request.Request(MAILTM_BASE + path,
            data=json.dumps(payload).encode() if is_write else None,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json',
                     'User-Agent': USER_AGENT,
                     **({'Authorization': 'Bearer ' + token} if token else {})},
            method='POST' if is_write else 'GET')
        try:
            with urllib.request.urlopen(req, timeout=25) as reply:
                return json.loads(reply.read().decode())
        except urllib.error.HTTPError as exc:
            detail = ''
            try:
                detail = exc.read(500).decode('utf-8', 'replace')
            except Exception:
                detail = ''
            finally:
                exc.close()
            if exc.code in (429, 422) and not is_write:
                if log:
                    log(f'mail.tm {exc.code} on {path}, waiting before retry ({attempt + 1}/5)')
                time.sleep(min(60, 12 * (attempt + 1)))
                continue
            raise AccountError(f'mail.tm refused {path}: HTTP {exc.code} {detail[:120]}') from None
    raise AccountError(f'mail.tm kept refusing reads of {path}')


# mail.tm throttles account creation per IP with opaque rolling limits;
# observed behavior on 2026-11-12: steady rapid retries stayed blocked for
# 30+ minutes while identities always succeeded when spaced minutes apart.
# Later attempts therefore breathe longer (~36-45 min worst case total).
_MAILBOX_ATTEMPTS = 12
_MAILBOX_PAUSE_S = 450
_MAILBOX_PAUSE_FACTOR_S = 30

_ALPHABET = string.ascii_lowercase + string.digits


def _fresh_identity(domain):
    user = 'jobtrack' + ''.join(secrets.choice(_ALPHABET) for _ in range(8))
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
    return f'{user}@{domain}', password


def _members(payload):
    """mail.tm returns hydra envelopes or bare lists depending on its mood."""
    if isinstance(payload, dict):
        value = payload.get('hydra:member', payload.get('member'))
        if isinstance(value, list):
            return value
        raise AccountError(f'unexpected mail.tm payload shape for {payload.get("@id", "")}')
    if isinstance(payload, list):
        return payload
    raise AccountError('unexpected mail.tm payload shape')


def create_mailbox(log=lambda *_: None):
    """Register a disposable mailbox; returns (address, password, bearer token).

    mail.tm intermittently rejects requests (rate limits, some username
    shapes), so every failed registration retries with a new identity.
    """
    domain = next((d['domain'] for d in _members(_mailtm(None, '/domains')) if d.get('isActive')), None)
    if not domain:
        raise AccountError('mail.tm reports no active mail domain')
    last_error = None
    for attempt in range(_MAILBOX_ATTEMPTS):
        if attempt:
            time.sleep(min(_MAILBOX_PAUSE_S, _MAILBOX_PAUSE_FACTOR_S * attempt))
        address, password = _fresh_identity(domain)
        try:
            _mailtm(None, '/accounts', payload={'address': address, 'password': password}, log=log)
            token = _mailtm(None, '/token', payload={'address': address, 'password': password})['token']
            return address, password, token
        except AccountError as exc:
            last_error = exc
            if log:
                log(f'mailbox attempt {attempt + 1} failed ({exc}); rotating identity')
    raise AccountError(f'could not register a free mailbox after several attempts: {last_error}')


def poll_verification_link(mailbox_token, attempts=24, pause_s=5):
    """Wait for OpenWeb Ninja's verification mail and pull out the ticket URL."""
    seen_ids = set()
    for _ in range(attempts):
        time.sleep(pause_s)
        items = _members(_mailtm(mailbox_token, '/messages'))
        for message in items:
            if message.get('id') in seen_ids:
                continue
            seen_ids.add(message.get('id'))
            full = _mailtm(mailbox_token, '/messages/' + str(message.get('id')))
            link = extract_verification_link(full)
            if link:
                return link
    return None


def confirm_email(link, browser):
    """Click the Auth0 ticket page and submit its confirmation form."""
    page = browser.request('GET', link, headers={'Accept': 'text/html'})
    fragment = page.text
    form = re.search(r'''<form\b[^>]*method=["']?post["']?[^>]*>(.*?)</form>''', fragment, re.S | re.I)
    if not form:
        # Some tenants confirm directly on GET when no continuation form exists.
        return 'verified' in fragment.lower()
    action_match = re.search(r'''action\s*=\s*["']([^"']+)["']''', form.group(0), re.I)
    action = urllib.parse.urljoin(page.url, action_match.group(1)) if action_match else page.url
    fields = parse_hidden_fields(form.group(1))
    result = browser.request('POST', action,
                             data=urllib.parse.urlencode(fields),
                             headers={'Content-Type': 'application/x-www-form-urlencoded'})
    if result.status >= 400:
        return False
    repeated_form = bool(re.search(r'''<form\b[^>]*method=["']?post''', result.text, re.I)) and \
                    any(k == 'state' for k in parse_hidden_fields(result.text))
    failure_hint = re.search(r'(?i)\b(expired|error|invalid)', result.text)
    return not (repeated_form and failure_hint)


def signup_openwebninja(browser, address, password):
    """Register through the scraped universal-login signup form.

    Auth0 serves two forms: the credential form plus an unrelated Google
    button whose hidden "connection" field must NOT leak into our POST.
    """
    landing = browser.request('GET', APP_BASE + '/api/auth/signup', headers={'Accept': 'text/html'})
    if landing.status != 200:
        raise AccountError(f'OpenWeb Ninja signup route returned HTTP {landing.status}')
    fields = {k: v for k, v in parse_hidden_fields(primary_form(landing.text)).items()
              if k not in ('email', 'password')}
    state = fields.get('state', '')
    if not state:
        raise AccountError('could not read the signup transaction state; provider page changed')
    form_url = LOGIN_BASE + '/u/signup?state=' + urllib.parse.quote(state, safe='')
    sent = dict(fields)
    sent.update({'email': address, 'password': password})
    outcome = browser.request('POST', form_url, data=urllib.parse.urlencode(sent),
                              headers={'Content-Type': 'application/x-www-form-urlencoded',
                                       'Referer': landing.url})
    if outcome.status >= 400:
        raise AccountError(f'signup POST failed with HTTP {outcome.status}')
    if 'verify-email' not in outcome.url:
        # A bounced-back signup page usually means policy violations or bot checks.
        raise AccountError('signup did not reach the verification step; '
                           'provider may have added captcha or stricter checks')


def login_openwebninja(browser, address, password):
    """Fresh-session sign-in; ends up holding the app session cookie."""
    browser.jar.clear()
    entry = browser.request('GET', APP_BASE + '/api/auth/login', headers={'Accept': 'text/html'})
    if entry.status != 200 or '/u/login' not in entry.url:
        raise AccountError(f'login redirect went off-script ({entry.status} {entry.url[:80]})')
    fields = {k: v for k, v in parse_hidden_fields(primary_form(entry.text)).items()
              if k not in ('username', 'email', 'password')}
    fields.update({'username': address, 'password': password})
    result = browser.request('POST', entry.url, data=urllib.parse.urlencode(fields),
                             headers={'Content-Type': 'application/x-www-form-urlencoded',
                                      'Referer': entry.url})
    host = urllib.parse.urlsplit(result.url).netloc
    if result.status >= 400 or 'app.openwebninja.com' not in host or '/u/' in urllib.parse.urlsplit(result.url).path:
        raise AccountError(f'sign-in did not establish a dashboard session ({result.status})')


def fetch_access_token(browser, retries=3, pause_s=4):
    """Dashboard-held access token for the backend audience."""
    delay = 0
    for attempt in range(retries):
        if delay:
            time.sleep(delay)
        delay = pause_s
        reply = browser.request('GET', TOKEN_URL, headers={'Accept': 'application/json'})
        try:
            access = json.loads(reply.text).get('accessToken', '')
        except ValueError:
            access = ''
        if access:
            return access
    raise AccountError('dashboard did not hand out an access token after sign-in')


def exchange_api_key(access_token):
    req = urllib.request.Request(API_KEY_URL, data=b'', method='POST',
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + access_token,
                 'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=25) as reply:
            body = json.loads(reply.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read(300).decode('utf-8', 'replace')
        except Exception:
            detail = ''
        finally:
            exc.close()
        raise AccountError(f'API-key exchange refused: HTTP {exc.code} {detail[:120]}') from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AccountError(f'API-key endpoint unreachable: {exc}') from None
    key = body.get('apiKey') if isinstance(body, dict) else None
    if not key:
        raise AccountError('API-key response had no apiKey field')
    return key


_KEY_RETENTION_ROWS = 20


def remember_account(db_path, address, api_key):
    """Persist the rotated account for observability and later reuse."""
    try:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with sqlite3.connect(str(db_path)) as db:
            db.execute('''CREATE TABLE IF NOT EXISTS service_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
                email TEXT NOT NULL, api_key TEXT NOT NULL)''')
            db.execute('INSERT INTO service_accounts (created_at,email,api_key) VALUES (?,?,?)',
                       (now, address, api_key))
            db.execute('''DELETE FROM service_accounts WHERE id NOT IN
                          (SELECT id FROM service_accounts ORDER BY id DESC LIMIT ?)''',
                       (_KEY_RETENTION_ROWS,))
    except Exception:  # observability/reuse only - must never kill the run
        pass


def last_saved_key(db_path):
    """Read account history; automatic startup never reuses this key."""
    try:
        with sqlite3.connect(str(db_path)) as db:
            row = db.execute('SELECT api_key FROM service_accounts ORDER BY id DESC LIMIT 1').fetchone()
            return row[0] if row else None
    except Exception:
        return None


def acquire_run_key(log=lambda *_: None, persist_path=None):
    """Rotate: mailbox -> signup -> email confirmation -> login -> API key."""
    browser = Session()
    address, password, mailbox_token = create_mailbox(log=log)
    log(f'created disposable mailbox {address}')
    signup_openwebninja(browser, address, password)
    link = poll_verification_link(mailbox_token, attempts=24, pause_s=5)
    if not link:
        raise AccountError('the verification email never arrived within ~2 minutes')
    if not confirm_email(link, browser):
        raise AccountError('the verification ticket could not be confirmed')
    login_openwebninja(browser, address, password)
    access = fetch_access_token(browser)
    api_key = exchange_api_key(access)
    if persist_path:
        remember_account(persist_path, address, api_key)
    return api_key

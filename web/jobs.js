const $ = s => document.querySelector(s);
let sequence = 0, ready = false;
let accountSetup = {mode: 'manual', status: 'manual'};
const prefsKey = 'jobtrack.discovery.v1';
function text(tag, value, className) {
  const node = document.createElement(tag); node.textContent = value;
  if (className) node.className = className;
  return node;
}
function prefs() {
  return {q: $('#job-query').value, location: $('#job-location').value,
    source: $('#job-source').value, auto: $('#auto-refresh').checked};
}
function remember() { try { localStorage.setItem(prefsKey, JSON.stringify(prefs())); } catch {} }
function connection() {
  const needsKey = $('#job-source').value !== 'remotive' && !ready;
  const automatic = accountSetup.mode === 'automatic';
  $('#connect-source').hidden = !needsKey || automatic;
  $('#account-setup').hidden = !automatic;
  $('#account-setup').textContent = automatic ? ({
    pending: 'Creating a fresh account for this run. Job searches will connect automatically when ready.',
    ready: 'Job sources connected with a fresh account for this run.',
    failed: 'Could not create a fresh account for this run. Check the server logs and restart to try again. Remotive is still available.'
  }[accountSetup.status] || '') : '';
  $('#source-help').textContent = $('#job-source').value === 'remotive'
    ? 'Remotive remote jobs · No account needed. Location filters the employer’s eligibility text; “Worldwide” roles may also be relevant.'
    : 'JSearch searches public listings across job boards. Results keep the publisher name and original posting link.';
  return needsKey;
}
async function request(path, options) {
  const response = await fetch('/api/' + path, options);
  const data = await response.json();
  if (!response.ok) throw Error(data.error || 'Could not load jobs');
  return data;
}
async function search() {
  remember(); const version = ++sequence;
  try { await refreshSources(); }
  catch (error) {
    if (version === sequence) {
      $('#jobs-message').textContent = 'Could not check job sources: ' + error.message;
      $('#find-jobs').disabled = false; $('#find-jobs').textContent = 'Find jobs';
    }
    return;
  }
  if (version !== sequence) return;
  if (connection()) {
    $('#job-list').replaceChildren(); $('#jobs-empty').hidden = true;
    $('#find-jobs').disabled = false; $('#find-jobs').textContent = 'Find jobs';
    $('#result-count').textContent = accountSetup.status === 'pending' ? 'Connecting job source…'
      : accountSetup.status === 'failed' ? 'Job source unavailable' : 'Connect this source to search';
    $('#jobs-message').textContent = ''; $('#freshness').textContent = '';
    return;
  }
  const p = prefs(), params = new URLSearchParams({q:p.q, location:p.location, source:p.source});
  $('#find-jobs').disabled = true; $('#find-jobs').textContent = 'Finding…';
  $('#jobs-message').textContent = 'Looking for opportunities…';
  $('#job-list').replaceChildren(); $('#jobs-empty').hidden = true;
  try {
    const data = await request('jobs?' + params);
    if (version !== sequence) return;
    $('#result-count').textContent = data.jobs.length + (data.total > data.jobs.length ? ' of ' + data.total : '') + (data.total === 1 ? ' opportunity' : ' opportunities');
    $('#freshness').textContent = 'Feed updated ' + new Date(data.fetched_at).toLocaleString();
    $('#jobs-message').textContent = data.warning || '';
    $('#source-help').textContent = data.notice;
    $('#jobs-empty').hidden = data.jobs.length !== 0;
    for (const job of data.jobs) {
      const card = text('article', '', 'job-card');
      card.append(text('span', job.source + (job.provider === 'jsearch' ? ' · via JSearch' : ''), 'source-label'),
        text('h3', job.title), text('p', job.company, 'job-company'),
        text('p', job.location || 'Location not listed'),
        text('p', job.employment_type + ' · ' + job.salary_label, 'job-details'));
      if (job.posted_at && !Number.isNaN(Date.parse(job.posted_at))) card.append(text('small', 'Posted ' + new Date(job.posted_at).toLocaleDateString()));
      const actions = text('div', '', 'job-actions'), link = text('a', 'View on ' + job.source + ' ↗');
      // API validates http(s) URLs; textContent keeps provider strings out of markup.
      if (/^https?:\/\//i.test(job.url)) link.href = job.url;
      link.target = '_blank'; link.rel = 'noopener noreferrer';
      const button = text('button', job.saved ? 'Saved to applications ✓' : '+ Save to applications');
      button.disabled = job.saved;
      button.onclick = async () => {
        button.disabled = true; button.textContent = 'Saving…';
        try {
          const result = await request('jobs/' + encodeURIComponent(job.id) + '/save', {method:'POST'});
          button.textContent = 'Saved to applications ✓';
          $('#jobs-message').textContent = result.created ? job.title + ' saved. Open Applications to edit its details or status.' : 'This listing is already in your applications.';
        } catch (error) {
          button.disabled = false; button.textContent = '+ Save to applications';
          $('#jobs-message').textContent = error.message;
        }
      };
      actions.append(link, button); card.append(actions); $('#job-list').append(card);
    }
  } catch (error) {
    if (version !== sequence) return;
    $('#result-count').textContent = 'Search unavailable';
    $('#jobs-message').textContent = error.message;
    $('#freshness').textContent = '';
  } finally {
    if (version === sequence) { $('#find-jobs').disabled = false; $('#find-jobs').textContent = 'Find jobs'; }
  }
}
$('#job-search').onsubmit = event => { event.preventDefault(); search(); };
$('#job-source').onchange = () => { connection(); search(); };
$('#auto-refresh').onchange = remember;
$('#setup-help').onclick = () => { $('#setup-instructions').hidden = !$('#setup-instructions').hidden; };
async function refreshSources() {
  const data = await request('job-sources');
  ready = data.jsearch_ready;
  accountSetup = data.account_setup || {mode: 'manual', status: 'manual'};
}
async function init() {
  try {
    const saved = JSON.parse(localStorage.getItem(prefsKey) || 'null');
    if (saved) {
      $('#job-query').value = typeof saved.q === 'string' ? saved.q.slice(0,200) : '';
      $('#job-location').value = typeof saved.location === 'string' ? saved.location.slice(0,200) : '';
      if (['remotive','jsearch','indeed','linkedin'].includes(saved.source)) $('#job-source').value = saved.source;
      $('#auto-refresh').checked = saved.auto === true;
    }
  } catch {}
  search();
}
setInterval(async () => {
  if (accountSetup.status !== 'pending' || document.hidden) return;
  try {
    await refreshSources();
    if (accountSetup.status !== 'pending') {
      connection();
      if ($('#job-source').value !== 'remotive') search();
    }
  } catch (error) { $('#jobs-message').textContent = 'Could not check account setup: ' + error.message; }
}, 5000);
setInterval(() => { if ($('#auto-refresh').checked && !document.hidden && !$('#find-jobs').disabled) search(); }, 30 * 60 * 1000);
init();

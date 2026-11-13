const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function setup(initialStatus, mode = 'automatic') {
  const nodes = new Map(), timers = [], calls = [];
  const node = () => ({value:'', checked:false, hidden:false, disabled:false,
    textContent:'', children:[], append(...items) { this.children.push(...items); },
    replaceChildren(...items) { this.children = items; }});
  const get = selector => {
    if (!nodes.has(selector)) nodes.set(selector, node());
    return nodes.get(selector);
  };
  get('#job-query').value = 'engineer';
  get('#job-source').value = 'linkedin';
  const state = {status:initialStatus, mode};
  const context = vm.createContext({
    URLSearchParams, Date, console,
    document:{hidden:false, querySelector:get, createElement:node},
    localStorage:{getItem:()=>null, setItem:()=>{}},
    setInterval:(callback, ms) => { timers.push({callback, ms}); return timers.length; },
    fetch:async url => {
      calls.push(url);
      if (url === '/api/job-sources') return {ok:true, json:async () => ({
        jsearch_ready:state.status === 'ready', account_setup:{mode:state.mode, status:state.status}})};
      if (url.startsWith('/api/jobs?')) return {ok:true, json:async () => ({
        jobs:[], total:0, fetched_at:'2026-11-12T12:00:00Z', warning:'', notice:'Fixture feed'})};
      throw Error('Unexpected request ' + url);
    }
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/jobs.js'), 'utf8'), context);
  return {get, timers, calls, state, context};
}
const settle = () => new Promise(resolve => setImmediate(resolve));

test('pending setup automatically connects after a fresh key is issued', async () => {
  const f = setup('pending'); await settle();
  assert.match(f.get('#account-setup').textContent, /Creating a fresh account/);
  assert.equal(f.get('#connect-source').hidden, true);
  assert.equal(f.calls.some(url => url.startsWith('/api/jobs?')), false);
  f.state.status = 'ready';
  await f.timers.find(timer => timer.ms === 5000).callback(); await settle();
  assert.equal(f.calls.filter(url => url.startsWith('/api/jobs?')).length, 1);
  assert.match(f.get('#account-setup').textContent, /connected with a fresh account/);
  assert.equal(f.get('#result-count').textContent, '0 opportunities');
});

test('failed fresh-account setup is visible and does not fetch with old credentials', async () => {
  const f = setup('pending'); await settle();
  f.state.status = 'failed';
  await f.timers.find(timer => timer.ms === 5000).callback(); await settle();
  assert.match(f.get('#account-setup').textContent, /Could not create a fresh account/);
  assert.equal(f.get('#result-count').textContent, 'Job source unavailable');
  assert.equal(f.get('#connect-source').hidden, true);
  assert.equal(f.calls.some(url => url.startsWith('/api/jobs?')), false);
});

test('manual Find jobs refreshes provider readiness without reloading', async () => {
  const f = setup('manual', 'manual'); await settle();
  assert.equal(f.get('#connect-source').hidden, false);
  f.state.status = 'ready';
  await f.context.search();
  assert.equal(f.get('#connect-source').hidden, true);
  assert.equal(f.calls.filter(url => url.startsWith('/api/jobs?')).length, 1);
});

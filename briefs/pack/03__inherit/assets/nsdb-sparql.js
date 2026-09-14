/* newsroom.sgit.ai — the graph console (/databases/graph.html).
   Oxigraph (a SPARQL 1.1 store written in Rust, compiled to WebAssembly, vendored) running in
   the reader's browser over /portugal/data/triples.nt — the Portugal graph re-serialised at
   build with its ontology inside. The store is built on load and discarded on close; there is
   no write path and SPARQL UPDATE is not exposed. Every fetch is same-origin.
   Publishes window.__tools.sparql after a 'tool:ready' event (read-only). */
import init, { Store } from './vendor/oxigraph/web.js';

const $ = (s) => document.querySelector(s);
const T = { engine: null, data: null, store: null, queries: [] };
let store = null, examples = [], prefixes = '', current = null;

const SHORT = [
  ['https://newsroom.sgit.ai/portugal/id/', 'p:'],
  ['https://newsroom.sgit.ai/portugal/verb/', 'v:'],
  ['https://newsroom.sgit.ai/portugal/type/', 't:'],
  ['https://newsroom.sgit.ai/portugal/prop/', 'a:'],
  ['http://www.w3.org/2000/01/rdf-schema#', 'rdfs:'],
  ['http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'rdf:'],
  ['http://www.w3.org/2002/07/owl#', 'owl:'],
  ['http://www.w3.org/2001/XMLSchema#', 'xsd:'],
];
function short(iri) { for (const [l, s] of SHORT) if (iri.startsWith(l)) return s + iri.slice(l.length); return '<' + iri + '>'; }
function fmt(ms) { return ms < 10 ? ms.toFixed(1) + ' ms' : Math.round(ms) + ' ms'; }
function kb(n) { return n < 1048576 ? Math.round(n / 1024) + ' KB' : (n / 1048576).toFixed(1) + ' MB'; }
function setMeter(id, big, small) {
  const el = document.getElementById(id); if (!el) return;
  el.textContent = big; const em = el.parentNode.querySelector('em'); if (em && small) em.textContent = small;
}
async function fetchText(url) { const r = await fetch(url); if (!r.ok) throw new Error('fetch ' + url + ' → ' + r.status); return r.text(); }

function cell(term) {
  if (!term) return { type: 'unbound', value: null };
  if (term.termType === 'NamedNode') return { type: 'iri', value: term.value, short: short(term.value) };
  if (term.termType === 'Literal') return { type: 'literal', value: term.value, lang: term.language || undefined, datatype: term.datatype && term.datatype.value !== 'http://www.w3.org/2001/XMLSchema#string' ? short(term.datatype.value) : undefined };
  if (term.termType === 'BlankNode') return { type: 'blank', value: '_:' + term.value };
  return { type: term.termType, value: term.value };
}

function withPrefixes(q) { return /^\s*PREFIX\s/im.test(q) ? q : prefixes + q; }

function exec(q) {
  const t = performance.now();
  const res = store.query(withPrefixes(q));
  const ms = performance.now() - t;
  if (typeof res === 'boolean') return { kind: 'ask', answer: res, ms };
  const arr = Array.isArray(res) ? res : Array.from(res);
  if (arr.length && arr[0] instanceof Map) {
    const cols = [...arr[0].keys()];
    for (const b of arr) for (const k of b.keys()) if (!cols.includes(k)) cols.push(k);
    return { kind: 'select', columns: cols, rows: arr.map((b) => cols.map((c) => cell(b.get(c)))), ms };
  }
  if (arr.length && arr[0] && arr[0].subject) {
    return { kind: 'construct', triples: arr.map((qd) => ({ s: cell(qd.subject), p: cell(qd.predicate), o: cell(qd.object) })), ms };
  }
  return { kind: 'select', columns: [], rows: [], ms };
}

function tableEl(columns, rows) {
  const wrap = document.createElement('div'); wrap.className = 'res';
  const t = document.createElement('table');
  const thead = t.createTHead().insertRow();
  for (const c of columns) { const th = document.createElement('th'); th.textContent = c; thead.appendChild(th); }
  const tb = t.createTBody(); const max = 500;
  rows.slice(0, max).forEach((r) => {
    const tr = tb.insertRow();
    r.forEach((c) => {
      const td = tr.insertCell();
      if (c.type === 'unbound') { td.textContent = '—'; td.className = 'null'; }
      else if (c.type === 'iri') { td.textContent = c.short; td.title = c.value; }
      else if (c.type === 'literal') { td.textContent = c.value + (c.lang ? ' @' + c.lang : '') + (c.datatype ? ' ^^' + c.datatype : ''); if (/^-?\d+(\.\d+)?$/.test(c.value)) td.className = 'n'; }
      else td.textContent = c.value;
    });
  });
  if (rows.length > max) { const tr = tb.insertRow(); const td = tr.insertCell(); td.colSpan = columns.length; td.className = 'null'; td.textContent = '… ' + (rows.length - max) + ' more not shown'; }
  wrap.appendChild(t); return wrap;
}

function describe(ab) {
  if (!ab) return '';
  if (ab.kind === 'ask') return 'ASK → ' + ab.answer + ' at build ' + ab.version;
  if (ab.kind === 'construct') return ab.triples + ' triples at build ' + ab.version;
  return ab.rows + ' row' + (ab.rows === 1 ? '' : 's') + ' at build ' + ab.version;
}

function select(id, andRun) {
  const e = examples.find((x) => x.id === id); if (!e) return;
  current = e; $('#q').value = e.sparql;
  $('#q-note').textContent = e.note + (e.at_build ? ' (' + describe(e.at_build) + ')' : '');
  $('#cypher').textContent = e.cypher; $('#alt').hidden = false;
  document.querySelectorAll('.nsdb .ex button').forEach((b) => b.classList.toggle('here', b.dataset.id === id));
  if (andRun && store) run();
}

function run() {
  const q = $('#q').value.trim(); if (!q || !store) return;
  const out = $('#out'), status = $('#status'); out.textContent = '';
  try {
    const r = exec(q);
    T.queries.push({ ms: r.ms, kind: r.kind });
    let agree = '';
    if (current && current.sparql.trim() === q && current.at_build) {
      const ab = current.at_build;
      const same = (ab.kind === 'ask' && r.kind === 'ask' && ab.answer === r.answer) || (ab.kind === 'select' && r.kind === 'select' && ab.rows === r.rows.length) || (ab.kind === 'construct' && r.kind === 'construct' && ab.triples === r.triples.length);
      agree = ' · ' + describe(ab) + (same ? ' · agrees' : ' · DIFFERS');
    }
    if (r.kind === 'ask') {
      setMeter('m-query', String(r.answer), fmt(r.ms));
      status.innerHTML = 'ASK → <b>' + r.answer + '</b> in <b>' + fmt(r.ms) + '</b>' + agree;
      const d = document.createElement('div'); d.className = 'note'; d.textContent = 'ASK answered ' + r.answer + '.'; out.appendChild(d);
    } else if (r.kind === 'construct') {
      setMeter('m-query', r.triples.length + ' triples', fmt(r.ms));
      status.innerHTML = '<b>' + r.triples.length + '</b> triples constructed in <b>' + fmt(r.ms) + '</b>' + agree;
      out.appendChild(tableEl(['subject', 'predicate', 'object'], r.triples.map((t) => [t.s, t.p, t.o])));
    } else {
      setMeter('m-query', r.rows.length + ' rows', fmt(r.ms));
      status.innerHTML = '<b>' + r.rows.length + '</b> row' + (r.rows.length === 1 ? '' : 's') + ' in <b>' + fmt(r.ms) + '</b>' + agree;
      out.appendChild(tableEl(r.columns, r.rows));
    }
  } catch (e) {
    status.textContent = '';
    const d = document.createElement('div'); d.className = 'err'; d.textContent = String(e && e.message ? e.message : e); out.appendChild(d);
  }
}

function link() {
  const u = new URL(location.href); u.search = ''; u.hash = 'q=' + encodeURIComponent($('#q').value.trim());
  history.replaceState(null, '', u.toString());
  if (navigator.clipboard) navigator.clipboard.writeText(u.toString()).then(() => { $('#status').textContent = 'link copied'; }, () => { $('#status').textContent = 'link is in the address bar'; });
  else $('#status').textContent = 'link is in the address bar';
}

function publish() {
  const API = {
    run: (q) => exec(q),
    prefixes,
    examples: () => examples.map((e) => ({ id: e.id, title: e.title, sparql: e.sparql, cypher: e.cypher, at_build: e.at_build })),
    timings: () => ({ engine: T.engine, data: T.data, store: T.store, total: T.total, queries: T.queries.slice() }),
    size: () => store.size,
    select: (id) => select(id, true),
    meta: { name: 'nsdb-sparql', engine: 'oxigraph 0.5.11 (web)', readonly: true },
  };
  window.__tools = window.__tools || {}; window.__tools.sparql = API;
  window.dispatchEvent(new CustomEvent('tool:ready', { detail: { name: 'nsdb-sparql' } }));
}

async function boot() {
  const note = $('#q-note');
  try {
    const t0 = performance.now();
    const exTxt = await fetchText('data/queries-sparql.json');
    const ex = JSON.parse(exTxt); examples = ex.queries; prefixes = ex.prefixes;
    document.querySelectorAll('.nsdb .ex button').forEach((b) => b.addEventListener('click', () => select(b.dataset.id, true)));
    const te = performance.now();
    await init();
    T.engine = { ms: performance.now() - te };
    setMeter('m-engine', fmt(T.engine.ms), 'web_bg.wasm 3.9 MB, compiled + initialised');
    const td = performance.now();
    const nt = await fetchText('../portugal/data/triples.nt');
    T.data = { bytes: nt.length, ms: performance.now() - td };
    setMeter('m-data', kb(nt.length), fmt(T.data.ms));
    const ts = performance.now();
    store = new Store();
    store.load(nt, { format: 'application/n-triples' });
    T.store = { triples: store.size, ms: performance.now() - ts };
    setMeter('m-store', store.size.toLocaleString() + ' triples', fmt(T.store.ms));
    T.total = performance.now() - t0;
    note.textContent = 'Ready: ' + store.size.toLocaleString() + ' triples in the store, ' + fmt(T.total) + ' from first byte to last triple. Pick a worked query or write one; prefixes are added if you leave them out.';
    $('#run').disabled = false;
    const u = new URL(location.href);
    const exId = u.searchParams.get('example');
    const q = u.hash.startsWith('#q=') ? decodeURIComponent(u.hash.slice(3)) : null;
    if (q) { $('#q').value = q; run(); }
    else select(exId && examples.some((e) => e.id === exId) ? exId : examples[0].id, true);
    publish();
  } catch (e) {
    note.textContent = 'The console could not start: ' + (e && e.message ? e.message : e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  $('#run').addEventListener('click', run);
  $('#prefixes').addEventListener('click', () => { const q = $('#q'); if (!/^\s*PREFIX\s/im.test(q.value)) q.value = prefixes + q.value; });
  $('#link').addEventListener('click', link);
  $('#q').addEventListener('keydown', (e) => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); run(); } });
  boot();
});

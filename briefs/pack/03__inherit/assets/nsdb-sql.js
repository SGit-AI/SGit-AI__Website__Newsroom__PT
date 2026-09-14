/* newsroom.sgit.ai — the SQL console (/databases/sql.html).
   SQLite compiled to WebAssembly (sql.js, vendored) over the Portugal section's JSON files.
   The tables are built on load from data/tables.json, the SAME spec databases/build/build.py
   runs through Python's sqlite3 at build time, so what a reader queries is what the build
   tested. Nothing is sent anywhere: every fetch is same-origin, and there is no write path.
   Publishes window.__tools.sql after a 'tool:ready' event (read-only), the convention the
   estate's graph readers use, so the console, Playwright and an agent are equal consumers. */
(function () {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const T = { engine: null, data: null, tables: null, queries: [] };
  let db = null, spec = null, examples = [], current = null;

  function get(o, path) {
    for (const p of path.split('.')) { if (o && typeof o === 'object' && p in o) o = o[p]; else return null; }
    return o === undefined ? null : o;
  }
  function conv(v) {
    if (v === null || v === undefined) return null;
    if (typeof v === 'boolean') return v ? 1 : 0;
    if (typeof v === 'object') return JSON.stringify(v);
    return v;
  }
  function fmt(ms) { return ms < 10 ? ms.toFixed(1) + ' ms' : Math.round(ms) + ' ms'; }
  function kb(n) { return n < 1048576 ? Math.round(n / 1024) + ' KB' : (n / 1048576).toFixed(1) + ' MB'; }
  function setMeter(id, big, small) {
    const el = document.getElementById(id); if (!el) return;
    el.textContent = big; const em = el.parentNode.querySelector('em'); if (em && small) em.textContent = small;
  }

  async function fetchText(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error('fetch ' + url + ' → ' + r.status);
    return r.text();
  }

  async function boot() {
    const note = $('#q-note'), status = $('#status');
    try {
      const t0 = performance.now();
      const [specTxt, exTxt] = await Promise.all([fetchText('data/tables.json'), fetchText('data/queries-sql.json')]);
      spec = JSON.parse(specTxt); examples = JSON.parse(exTxt).queries;
      renderExamples();
      const te = performance.now();
      const SQL = await initSqlJs({ locateFile: (f) => '../assets/vendor/' + f });
      T.engine = { ms: performance.now() - te };
      setMeter('m-engine', fmt(T.engine.ms), 'sql-wasm.wasm 643 KB, compiled + initialised');
      db = new SQL.Database();
      const td = performance.now();
      const files = {}; let bytes = 0;
      for (const f of [...new Set(spec.tables.map((t) => t.file))]) {
        const txt = await fetchText(spec.base + f); bytes += txt.length; files[f] = JSON.parse(txt);
      }
      T.data = { bytes, ms: performance.now() - td, files: Object.keys(files).length };
      setMeter('m-data', kb(bytes), T.data.files + ' files / ' + fmt(T.data.ms));
      const tt = performance.now(); let rows = 0; const counts = {};
      for (const t of spec.tables) {
        const arr = get(files[t.file], t.path) || [];
        const names = t.columns.map((c) => '"' + c.name + '"');
        db.run('CREATE TABLE "' + t.name + '" (' + names.join(', ') + ')');
        const stmt = db.prepare('INSERT INTO "' + t.name + '" VALUES (' + t.columns.map(() => '?').join(', ') + ')');
        for (const r of arr) { stmt.run(t.columns.map((c) => conv(get(r, c.from)))); rows++; }
        stmt.free(); counts[t.name] = arr.length;
      }
      T.tables = { rows, ms: performance.now() - tt, counts };
      setMeter('m-tables', spec.tables.length + ' tables', rows + ' rows / ' + fmt(T.tables.ms));
      T.total = performance.now() - t0;
      note.textContent = 'Ready: ' + spec.tables.length + ' tables, ' + rows + ' rows, ' + fmt(T.total) + ' from first byte to last insert. Pick a worked query or write one.';
      $('#run').disabled = false;
      const u = new URL(location.href);
      const ex = u.searchParams.get('example');
      const q = u.hash.startsWith('#q=') ? decodeURIComponent(u.hash.slice(3)) : null;
      if (q) { $('#q').value = q; run(); }
      else select(ex && examples.some((e) => e.id === ex) ? ex : examples[0].id, true);
      publish();
    } catch (e) {
      note.textContent = 'The console could not start: ' + (e && e.message ? e.message : e);
      if (status) status.textContent = '';
    }
  }

  function renderExamples() {
    const box = $('.nsdb .ex');
    box.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => select(b.dataset.id, true)));
  }

  function select(id, andRun) {
    const e = examples.find((x) => x.id === id); if (!e) return;
    current = e; $('#q').value = e.sql;
    $('#q-note').textContent = e.note + ' (' + e.at_build.rows + ' row' + (e.at_build.rows === 1 ? '' : 's') + ' at build ' + e.at_build.version + ')';
    document.querySelectorAll('.nsdb .ex button').forEach((b) => b.classList.toggle('here', b.dataset.id === id));
    if (andRun && db) run();
  }

  function exec(sql) {
    const t = performance.now();
    const res = db.exec(sql);
    const ms = performance.now() - t;
    const first = res[0] || { columns: [], values: [] };
    return { columns: first.columns, rows: first.values, ms, sets: res.length };
  }

  function run() {
    const sql = $('#q').value.trim(); if (!sql || !db) return;
    const out = $('#out'), status = $('#status');
    out.textContent = '';
    try {
      const r = exec(sql);
      T.queries.push({ ms: r.ms, rows: r.rows.length });
      setMeter('m-query', r.rows.length + ' rows', fmt(r.ms));
      status.innerHTML = '<b>' + r.rows.length + '</b> row' + (r.rows.length === 1 ? '' : 's') + ' in <b>' + fmt(r.ms) + '</b>' +
        (current && current.sql.trim() === sql ? ' · ' + current.at_build.rows + ' at build' + (current.at_build.rows === r.rows.length ? ' · agrees' : ' · DIFFERS') : '');
      out.appendChild(table(r.columns, r.rows));
    } catch (e) {
      status.textContent = '';
      const d = document.createElement('div'); d.className = 'err'; d.textContent = String(e && e.message ? e.message : e);
      out.appendChild(d);
    }
  }

  function table(columns, rows) {
    const wrap = document.createElement('div'); wrap.className = 'res';
    const t = document.createElement('table');
    const thead = t.createTHead().insertRow();
    for (const c of columns) { const th = document.createElement('th'); th.textContent = c; thead.appendChild(th); }
    const tb = t.createTBody();
    const max = 500;
    rows.slice(0, max).forEach((r) => {
      const tr = tb.insertRow();
      r.forEach((v) => {
        const td = tr.insertCell();
        if (v === null) { td.textContent = 'NULL'; td.className = 'null'; }
        else { td.textContent = typeof v === 'string' && v.length > 240 ? v.slice(0, 240) + '…' : String(v); if (typeof v === 'number') td.className = 'n'; }
      });
    });
    if (rows.length > max) { const tr = tb.insertRow(); const td = tr.insertCell(); td.colSpan = columns.length; td.className = 'null'; td.textContent = '… ' + (rows.length - max) + ' more rows not shown'; }
    wrap.appendChild(t);
    return wrap;
  }

  function schema() {
    const rows = spec.tables.map((t) => [t.name, T.tables.counts[t.name], t.columns.map((c) => c.name).join(', '), t.file + ' → ' + t.path]);
    $('#out').textContent = ''; $('#out').appendChild(table(['table', 'rows', 'columns', 'from'], rows));
    $('#status').textContent = spec.tables.length + ' tables';
  }

  function link() {
    const u = new URL(location.href); u.search = ''; u.hash = 'q=' + encodeURIComponent($('#q').value.trim());
    history.replaceState(null, '', u.toString());
    if (navigator.clipboard) navigator.clipboard.writeText(u.toString()).then(() => { $('#status').textContent = 'link copied'; }, () => { $('#status').textContent = 'link is in the address bar'; });
    else $('#status').textContent = 'link is in the address bar';
  }

  function publish() {
    const API = {
      run: (sql) => { const r = exec(sql); return { columns: r.columns, rows: r.rows, ms: r.ms }; },
      tables: () => spec.tables.map((t) => ({ name: t.name, rows: T.tables.counts[t.name], columns: t.columns.map((c) => c.name), file: t.file, path: t.path })),
      examples: () => examples.map((e) => ({ id: e.id, title: e.title, sql: e.sql, at_build: e.at_build })),
      timings: () => ({ engine: T.engine, data: T.data, tables: T.tables, total: T.total, queries: T.queries.slice() }),
      select: (id) => select(id, true),
      meta: { name: 'nsdb-sql', engine: 'sql.js 1.14.2 (SQLite)', readonly: true },
    };
    window.__tools = window.__tools || {}; window.__tools.sql = API;
    window.dispatchEvent(new CustomEvent('tool:ready', { detail: { name: 'nsdb-sql' } }));
  }

  document.addEventListener('DOMContentLoaded', () => {
    $('#run').addEventListener('click', run);
    $('#schema').addEventListener('click', schema);
    $('#link').addEventListener('click', link);
    $('#q').addEventListener('keydown', (e) => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); run(); } });
    boot();
  });
})();

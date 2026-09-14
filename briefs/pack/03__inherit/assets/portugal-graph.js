/* @module portugal-graph
   The Portugal Startups section as one explorable graph. Cytoscape.js, vendored — the
   same build graphs.sgit.ai uses for its own graph pages, and the control vocabulary is
   deliberately that site's (/v1/altitudes/graph.html): packs instead of levels, otherwise
   the same instrument, because a reader who has used one should not have to learn the
   other.

   Four ideas drive the controls, inherited:
     1. Start anywhere. Any node can be the centre, with a radius, so the graph is explored
        from a person as easily as from the event.
     2. Every edge names both directions, so a path can be READ as a sentence whichever way
        you walk it — and here in either language, because every verb carries its Portuguese.
     3. A view is a thing you can keep: settings, zoom, pan and hand-moved positions save to
        a file and restore exactly.
     4. Nodes arrive in packs. The reader starts with the event, the organisations and the
        people, and switches the programme, the evidence, the changes, the coverage and the
        stories on one block at a time.

   And one of this section's own: every node carries the frozen source it came from, and
   the detail pane shows it, with the hash, because a graph node with no way back to bytes
   is a drawing.

   The page publishes a small API on window.__graph (read + view levels) and fires a
   'tool:ready' event, the same convention as the universe reader on graphs.sgit.ai, so the
   browser console, Playwright and an LLM agent are equal consumers. */
(function () {
  'use strict';
  var el = document.getElementById('cy');
  if (!el || typeof cytoscape === 'undefined') { return; }

  var D = null, cy = null, VERB = {}, INV = {}, PT = {}, TYPE = {}, TAX = {}, NODE = {};
  var collapsed = [], pathEnds = { a: null, b: null }, focusId = null;

  var cfg = {
    packs: {}, types: {}, verbs: {},
    colour: 'type', layout: 'force', iterations: 2000, stabilise: false,
    labels: 'below', wrap: 18, maxlen: 30, size: 'degree',
    radius: 0, edgeLabels: 'none', lang: 'en', search: ''
  };

  var ROLE_C = { investor: '#7c3aed', founder: '#b45309', advisor: '#0e7490', other: '#8a8d94' };
  var PACK_C = { event: '#0f766e', orgs: '#1d4ed8', people: '#b45309', sessions: '#115e59',
                 sources: '#8a8d94', changes: '#b91c1c', coverage: '#a16207', stories: '#5b4d8f',
                 topics: '#7c3aed', tags: '#0e7490' };
  var TAX_C = { entity: '#b45309', programme: '#0f766e', evidence: '#8a8d94', output: '#5b4d8f',
                themes: '#7c3aed', derived: '#0e7490' };

  function esc(t) { return String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function clip(t) { t = String(t); return t.length > cfg.maxlen ? t.slice(0, cfg.maxlen - 1) + '…' : t; }
  function verbLabel(v, inverse) {
    var e = VERB[v]; if (!e) { return v; }
    if (cfg.lang === 'pt') { return inverse ? e.pt.inverse : e.pt.verb; }
    return inverse ? e.inverse : v;
  }

  /* ------------------------------------------------------------- build */
  function colourOf(n) {
    if (cfg.colour === 'pack') { return PACK_C[n.pack] || '#8a8d94'; }
    if (cfg.colour === 'role') { return n.type === 'Person' ? (ROLE_C[n.role_class] || ROLE_C.other) : '#d5d0c2'; }
    if (cfg.colour === 'class') { return TAX_C[TAX[n.type]] || '#8a8d94'; }
    return (TYPE[n.type] && TYPE[n.type].colour) || '#8a8d94';
  }
  function degree(id) { return (D._deg && D._deg[id]) || 0; }
  function sizeOf(n) {
    if (cfg.size === 'fixed') { return 28; }
    return Math.max(22, Math.min(80, 20 + Math.sqrt(degree(n.id)) * 9));
  }
  function visibleNode(n) {
    if (!cfg.packs[n.pack]) { return false; }
    if (cfg.types[n.type] === false) { return false; }
    if (cfg.search) {
      var q = cfg.search.toLowerCase();
      var hay = (n.label + ' ' + (n.role || '') + ' ' + (n.org || '') + ' ' + n.type).toLowerCase();
      if (hay.indexOf(q) === -1) { return false; }
    }
    return true;
  }
  function build() {
    var els = [], on = {};
    D.nodes.forEach(function (n) {
      if (!visibleNode(n)) { return; }
      on[n.id] = 1;
      els.push({ data: { id: n.id, type: n.type, pack: n.pack, label: clip(n.label),
        col: colourOf(n), w: sizeOf(n), gone: n.no_longer_listed ? 1 : 0, ph: n.placeholder ? 1 : 0 } });
    });
    D.edges.forEach(function (e) {
      if (!on[e.source] || !on[e.target]) { return; }
      if (!cfg.packs[e.pack]) { return; }
      if (cfg.verbs[e.verb] === false) { return; }
      els.push({ data: { id: e.id, source: e.source, target: e.target, verb: e.verb, pack: e.pack,
        label: verbLabel(e.verb, false) } });
    });
    return els;
  }

  /* ------------------------------------------------------------- style */
  function style() {
    var inside = cfg.labels === 'inside', px = Math.round(cfg.wrap * 6.4);
    var base = {
      'background-color': 'data(col)', 'label': cfg.labels === 'none' ? '' : 'data(label)',
      'font-size': inside ? 9 : 8, 'color': inside ? '#fff' : '#3a3b40',
      'text-wrap': 'wrap', 'text-max-width': inside ? px : 100,
      'border-width': 1, 'border-color': '#fff'
    };
    if (inside) {
      base['shape'] = 'round-rectangle'; base['text-valign'] = 'center'; base['text-halign'] = 'center';
      base['width'] = 'label'; base['height'] = 'label'; base['padding'] = '8px'; base['font-weight'] = 500;
    } else {
      base['width'] = 'data(w)'; base['height'] = 'data(w)';
      base['text-valign'] = 'bottom'; base['text-margin-y'] = 3;
    }
    var edgeLbl = cfg.edgeLabels === 'none' ? '' : 'data(label)';
    return [
      { selector: 'node', style: base },
      { selector: 'node[type = "Event"]', style: { shape: inside ? 'round-rectangle' : 'star', 'border-width': 3, 'border-color': '#c9a227' } },
      { selector: 'node[type = "Story"]', style: { shape: inside ? 'round-rectangle' : 'diamond' } },
      { selector: 'node[type = "Snapshot"]', style: { shape: inside ? 'round-rectangle' : 'hexagon' } },
      { selector: 'node[type = "Source"]', style: { shape: inside ? 'round-rectangle' : 'rectangle' } },
      { selector: 'node[type = "Coverage"]', style: { shape: inside ? 'round-rectangle' : 'round-tag' } },
      { selector: 'node[gone = 1]', style: { 'border-width': 3, 'border-color': '#b91c1c', 'border-style': 'dashed' } },
      { selector: 'node[ph = 1]', style: { 'border-width': 2, 'border-color': '#b91c1c', 'border-style': 'dotted' } },
      { selector: 'node[type = "group"]', style: { shape: 'round-rectangle', 'border-width': 3, 'border-style': 'double', 'border-color': '#0f766e', 'font-weight': 'bold' } },
      { selector: 'edge', style: {
          width: 1, 'line-color': '#cfcabc', 'curve-style': 'bezier',
          'target-arrow-shape': 'triangle', 'target-arrow-color': '#cfcabc', 'arrow-scale': .7,
          label: edgeLbl, 'font-size': 7, color: '#8a8578', 'text-rotation': 'autorotate',
          'text-background-color': '#faf9f5', 'text-background-opacity': .85, 'text-background-padding': 1 } },
      { selector: 'edge[verb = "absent_from"]', style: { 'line-color': '#b91c1c', 'target-arrow-color': '#b91c1c', 'line-style': 'dashed' } },
      { selector: 'edge[verb = "present_in"]', style: { 'line-color': '#9cc5be', 'target-arrow-color': '#9cc5be', 'line-style': 'dashed' } },
      { selector: 'edge[verb = "attested_by"], edge[verb = "captured_in"], edge[verb = "stands_on"]', style: { 'line-color': '#e0dccf', 'target-arrow-color': '#e0dccf' } },
      { selector: 'edge[verb = "covers"], edge[verb = "published_by"]', style: { 'line-color': '#d9b25a', 'target-arrow-color': '#d9b25a' } },
      { selector: '.dim', style: { opacity: .1 } },
      { selector: '.hot', style: { opacity: 1, 'border-width': 4, 'border-color': '#0f766e' } },
      { selector: '.onpath', style: { 'line-color': '#0f766e', 'target-arrow-color': '#0f766e', width: 4, opacity: 1, 'z-index': 99 } },
      { selector: '.pend', style: { 'border-width': 5, 'border-color': '#c9a227', opacity: 1 } }
    ];
  }

  function layoutOpts() {
    if (cfg.layout === 'bands') {
      var pos = bands();
      return { name: 'preset', positions: function (n) { return pos[n.id()] || { x: 0, y: 0 }; }, fit: true, padding: 26, animate: false };
    }
    if (cfg.layout === 'concentric') {
      var rank = { Event: 9, Place: 8, Organisation: 6, Person: 5, Session: 4, Stage: 4, Story: 3, Coverage: 2, Snapshot: 2, Source: 1 };
      return { name: 'concentric', concentric: function (n) { return rank[n.data('type')] || 1; },
               levelWidth: function () { return 1; }, padding: 24, animate: false };
    }
    if (cfg.layout === 'grid') { return { name: 'grid', padding: 24, animate: false }; }
    var big = cfg.labels === 'inside';
    var bb = { x1: 0, y1: 0, w: Math.max(el.clientWidth - 40, 600), h: Math.max(el.clientHeight - 40, 420) };
    return { name: 'cose', animate: false, padding: 26, boundingBox: bb, fit: true,
             nodeRepulsion: big ? 48000 : 14000, idealEdgeLength: big ? 180 : 80,
             nodeOverlap: big ? 28 : 12, componentSpacing: big ? 140 : 80,
             nestingFactor: .8, gravity: .32, numIter: cfg.iterations,
             coolingFactor: cfg.stabilise ? .997 : .99, initialTemp: cfg.stabilise ? 260 : 200, randomize: true };
  }
  /* one band per taxonomy class, top to bottom: programme, entities, output, evidence */
  function bands() {
    var order = ['programme', 'entity', 'output', 'evidence'], W = Math.max(el.clientWidth, 900);
    var GAP = cfg.labels === 'inside' ? 180 : 120, ROW = cfg.labels === 'inside' ? 120 : 100, pos = {}, y = 0;
    order.forEach(function (cls) {
      var ids = cy.nodes().filter(function (n) { return TAX[n.data('type')] === cls; }).map(function (n) { return n.id(); });
      if (!ids.length) { return; }
      var per = Math.max(4, Math.floor(W / GAP)), rows = Math.ceil(ids.length / per);
      ids.forEach(function (id, i) {
        var r = Math.floor(i / per), inRow = Math.min(per, ids.length - r * per);
        pos[id] = { x: (i % per + .5) * (W / inRow), y: y + r * ROW };
      });
      y += rows * ROW + 110;
    });
    return pos;
  }

  /* ------------------------------------------------------------- draw */
  function draw(keepPositions) {
    var pos = null;
    if (keepPositions && cy) { pos = {}; cy.nodes().forEach(function (n) { pos[n.id()] = n.position(); }); }
    var zoom = cy ? cy.zoom() : null, pan = cy ? cy.pan() : null;
    if (cy) { cy.destroy(); }
    cy = cytoscape({ container: el, elements: build(), style: style(),
                     layout: { name: 'preset', animate: false }, wheelSensitivity: .25, maxZoom: 4, minZoom: .08 });
    if (pos) {
      cy.nodes().forEach(function (n) { if (pos[n.id()]) { n.position(pos[n.id()]); } });
      if (zoom) { cy.zoom(zoom); cy.pan(pan); }
    } else { cy.layout(layoutOpts()).run(); }
    wire(); applyRadius(); stats();
  }
  function relayout() { cy.layout(layoutOpts()).run(); stats(); }
  function wire() {
    cy.on('tap', 'node', function (e) {
      if (e.originalEvent && e.originalEvent.shiftKey) { setPathEnd(e.target); return; }
      detail(e.target);
    });
    cy.on('dbltap', 'node', function (e) {
      var n = e.target;
      if (n.data('type') === 'group') { expandGroup(n.id()); return; }
      focusOn(n.id(), Math.max(1, cfg.radius || 1));
    });
    cy.on('tap', function (e) { if (e.target === cy) { cy.elements().removeClass('dim hot onpath'); clearDetail(); } });
  }
  function stats() {
    var s = document.getElementById('gstats'); if (!s) { return; }
    s.textContent = cy.nodes(':visible').length + ' nodes · ' + cy.edges(':visible').length + ' edges' +
      (collapsed.length ? ' · ' + collapsed.length + ' collapsed' : '') + (cfg.radius ? ' · radius ' + cfg.radius : '') +
      (cfg.search ? ' · filtered by "' + cfg.search + '"' : '');
  }

  /* --------------------------------------------------- focus and radius */
  function focusOn(id, r) {
    focusId = id; cfg.radius = r;
    var f = document.querySelector('[name="radius"]'); if (f) { f.value = String(r); }
    var o = document.getElementById('out-radius'); if (o) { o.textContent = r; }
    applyRadius(); detail(cy.$id(id));
  }
  function applyRadius() {
    if (!cfg.radius || !focusId || !cy.$id(focusId).length) { cy.elements().style('display', 'element'); return; }
    var keep = cy.$id(focusId);
    for (var i = 0; i < cfg.radius; i++) { keep = keep.closedNeighborhood(); }
    cy.elements().style('display', 'none'); keep.style('display', 'element');
  }

  /* ------------------------------------------------------ collapse group */
  function collapseSelection() {
    var sel = cy.$(':selected').filter('node');
    if (sel.length < 2) { note('Select two or more nodes first (shift-drag a box, or ctrl-click).'); return; }
    var gid = 'grp-' + (collapsed.length + 1), members = sel.map(function (n) { return n.id(); });
    var pos = { x: 0, y: 0 };
    sel.forEach(function (n) { pos.x += n.position('x') / sel.length; pos.y += n.position('y') / sel.length; });
    collapsed.push({ id: gid, members: members, json: sel.union(sel.connectedEdges()).jsons() });
    cy.add({ group: 'nodes', data: { id: gid, type: 'group', pack: 'group', label: members.length + ' collapsed', col: '#0f766e', w: 44 }, position: pos });
    var seen = {};
    sel.connectedEdges().forEach(function (e) {
      var other = members.indexOf(e.source().id()) > -1 ? e.target().id() : e.source().id();
      if (members.indexOf(other) > -1 || seen[other + e.data('verb')]) { return; }
      seen[other + e.data('verb')] = 1;
      cy.add({ group: 'edges', data: { id: 'g-' + gid + '-' + other + '-' + e.data('verb'),
        source: members.indexOf(e.source().id()) > -1 ? gid : other, target: members.indexOf(e.source().id()) > -1 ? other : gid,
        verb: e.data('verb'), label: e.data('label') } });
    });
    sel.remove(); stats();
  }
  function expandGroup(gid) {
    var idx = -1; collapsed.forEach(function (g, i) { if (g.id === gid) { idx = i; } });
    if (idx < 0) { return; }
    cy.$id(gid).connectedEdges().remove(); cy.$id(gid).remove(); cy.add(collapsed[idx].json); collapsed.splice(idx, 1); stats();
  }

  /* ------------------------------------------------------------- paths */
  function setPathEnd(n) {
    if (!pathEnds.a) { pathEnds.a = n.id(); n.addClass('pend'); note('Path start: ' + n.data('label') + '. Shift-click a second node.'); return; }
    if (pathEnds.a === n.id()) { cy.$id(pathEnds.a).removeClass('pend'); pathEnds.a = null; note('Path start cleared.'); return; }
    pathEnds.b = n.id();
    var dij = cy.elements().dijkstra({ root: cy.$id(pathEnds.a), directed: false });
    var path = dij.pathTo(cy.$id(pathEnds.b));
    cy.elements().removeClass('onpath dim');
    if (!path || path.length < 2) { note('No path between those two under the current packs and filters.'); return; }
    path.addClass('onpath'); cy.elements().not(path).addClass('dim'); readPath(path);
    cy.$id(pathEnds.a).removeClass('pend'); pathEnds = { a: null, b: null };
  }
  /* A path is only worth having if it reads. Each edge is walked in the direction the path
     goes and named with its verb or its inverse — in whichever language is selected. */
  function readPath(path) {
    var out = [], prev = null;
    path.forEach(function (e) {
      if (e.isNode()) { prev = e; return; }
      var fwd = prev && e.source().id() === prev.id();
      out.push({ from: (fwd ? e.source() : e.target()).data('label'), verb: verbLabel(e.data('verb'), !fwd),
                 to: (fwd ? e.target() : e.source()).data('label') });
      prev = fwd ? e.target() : e.source();
    });
    var d = document.getElementById('gdetail'); if (!d) { return; }
    d.innerHTML = '<h3>' + (cfg.lang === 'pt' ? 'O caminho, lido como frases' : 'The path, read as sentences') + '</h3>' +
      '<p class="small dim">' + out.length + ' hop' + (out.length === 1 ? '' : 's') + '. ' +
      'Each edge is named in the direction the path walks it, using its inverse where the walk goes backwards. ' +
      '<button class="altib" data-lang="' + (cfg.lang === 'pt' ? 'en' : 'pt') + '">read it in ' + (cfg.lang === 'pt' ? 'English' : 'português') + '</button></p>' +
      '<ol class="gpath">' + out.map(function (h) {
        return '<li><b>' + esc(h.from) + '</b> <code>' + esc(h.verb) + '</code> <b>' + esc(h.to) + '</b></li>';
      }).join('') + '</ol>';
    window.__lastPath = path;
  }

  /* ------------------------------------------------------- the path query */
  var QCAP = 300;
  function pattern() {
    var f = document.getElementById('gq'); if (!f) { return null; }
    var p = { start: f.querySelector('[name="q-start"]').value, steps: [] };
    for (var i = 1; i <= 3; i++) {
      var v = f.querySelector('[name="q-verb' + i + '"]'), d = f.querySelector('[name="q-dir' + i + '"]'), n = f.querySelector('[name="q-node' + i + '"]');
      if (!v || v.value === 'stop') { break; }
      p.steps.push({ verb: v.value, dir: d.value, node: n.value });
    }
    return p;
  }
  function matchNode(n, filter) {
    if (filter === 'any') { return true; }
    if (filter.indexOf('type:') === 0) { return n.data('type') === filter.slice(5); }
    if (filter.indexOf('role:') === 0) { var d = NODE[n.id()]; return !!d && d.role_class === filter.slice(5); }
    if (filter === 'gone') { return n.data('gone') === 1; }
    if (filter === 'placeholder') { return n.data('ph') === 1; }
    return n.id() === filter;
  }
  function runQuery() {
    var p = pattern();
    if (!p || !p.steps.length) { qresult('<p class="small dim">Add at least one step.</p>'); return; }
    var starts = cy.nodes().filter(function (n) { return matchNode(n, p.start); }), paths = [], capped = false;
    function walk(node, i, trail, seen) {
      if (paths.length >= QCAP) { capped = true; return; }
      if (i >= p.steps.length) { paths.push(trail.slice()); return; }
      var st = p.steps[i];
      var edges = st.dir === 'in' ? node.incomers('edge') : st.dir === 'out' ? node.outgoers('edge') : node.connectedEdges();
      edges.forEach(function (e) {
        if (st.verb !== 'any' && e.data('verb') !== st.verb) { return; }
        var other = e.source().id() === node.id() ? e.target() : e.source();
        if (st.dir === 'in' && e.target().id() !== node.id()) { return; }
        if (st.dir === 'out' && e.source().id() !== node.id()) { return; }
        if (seen[other.id()] || !matchNode(other, st.node)) { return; }
        seen[other.id()] = 1;
        trail.push({ e: e, from: node, to: other, back: e.source().id() !== node.id() });
        walk(other, i + 1, trail, seen); trail.pop(); delete seen[other.id()];
      });
    }
    starts.forEach(function (n) { var seen = {}; seen[n.id()] = 1; walk(n, 0, [], seen); });
    if (!paths.length) {
      qresult('<p class="small dim">No paths match that pattern under the current packs. That is a result, not a failure: it is the difference between "we did not look" and "we looked and there is nothing there".</p>');
      return;
    }
    var h = ['<p class="small dim"><b>' + paths.length + (capped ? '+' : '') + ' path' + (paths.length === 1 ? '' : 's') + '</b>' +
             (capped ? ' &mdash; <b>capped at ' + QCAP + '</b>, so the list is incomplete and says so.' : '') + ' Click one to trace it.</p><ol class="gpath">'];
    paths.forEach(function (t, i) {
      h.push('<li><a href="#" data-qpath="' + i + '">' + t.map(function (hop) {
        return '<b>' + esc(hop.from.data('label')) + '</b> <code>' + esc(verbLabel(hop.e.data('verb'), hop.back)) + '</code> <b>' + esc(hop.to.data('label')) + '</b>';
      }).join(' &rarr; ') + '</a></li>');
    });
    h.push('</ol>'); qresult(h.join('')); window.__qpaths = paths;
  }
  function qresult(h) { var d = document.getElementById('gqout'); if (d) { d.innerHTML = h; } }
  function showQPath(i) {
    var t = (window.__qpaths || [])[i]; if (!t) { return; }
    var els = cy.collection();
    t.forEach(function (hop) { els = els.union(hop.e).union(hop.from).union(hop.to); });
    cy.elements().removeClass('onpath').addClass('dim'); els.removeClass('dim').addClass('onpath');
  }
  function note(t) {
    var d = document.getElementById('gnote');
    if (d) { d.textContent = t; setTimeout(function () { if (d.textContent === t) { d.textContent = ''; } }, 6000); }
  }

  /* ------------------------------------------------------------- detail */
  function clearDetail() {
    var d = document.getElementById('gdetail');
    if (d) { d.innerHTML = '<p class="small dim">Click a node to open it. <b>Double-click</b> to centre the graph on it at the current radius. <b>Shift-click two nodes</b> to trace a path and read it as sentences &mdash; in English or Portuguese.</p>'; }
  }
  function field(k, v) { return v == null || v === '' ? '' : '<p class="small"><b>' + esc(k) + ':</b> ' + v + '</p>'; }
  function detail(node) {
    var d = document.getElementById('gdetail'), id = node.id(), n = NODE[id], h = [];
    cy.elements().removeClass('dim hot');
    if (!cfg.radius) { cy.elements().addClass('dim'); node.closedNeighborhood().removeClass('dim'); }
    node.addClass('hot');
    if (node.data('type') === 'group') {
      h.push('<h3>' + node.data('label') + '</h3><p class="small dim">A group you collapsed. Double-click it to expand.</p>');
    } else if (n) {
      var t = TYPE[n.type] || {};
      h.push('<h3>' + esc(n.label) + '</h3>');
      h.push('<p class="small dim">' + esc(t.label || n.type) + (t.pt ? ' · ' + esc(t.pt) : '') + ' · pack <code>' + esc(n.pack) + '</code></p>');
      if (n.no_longer_listed) { h.push('<p class="small" style="color:#b91c1c"><b>No longer on the published list.</b> Reason: not stated by the source, and not guessed by us.</p>'); }
      if (n.placeholder) { h.push('<p class="small" style="color:#b91c1c"><b>A placeholder, not an organisation</b> &mdash; kept because the source lists it, flagged because it is not one.</p>'); }
      h.push(field('Listed role', esc(n.role)));
      h.push(field('Listed under', esc(n.org)));
      if (n.role_class_label) { h.push(field('Class (formula)', esc(n.role_class_label))); }
      h.push(field('When', esc(n.day ? n.day + (n.time ? ' · ' + n.time : '') : n.date || n.published || (n.dates ? n.dates.join(' – ') : null))));
      h.push(field('Kind', esc(n.kind)));
      h.push(field('Publisher', esc(n.publisher)));
      if (n.also_called) { h.push(field('Also called', esc(n.also_called))); }
      if (n.url) { h.push(field('Original', '<a href="' + esc(n.url) + '">' + esc(n.url.replace(/^https?:\/\//, '').slice(0, 60)) + '</a>')); }
      if (n.page && !/^https?:/.test(n.page)) { h.push(field('Read', '<a href="' + esc(n.page) + '">this story</a>')); }
      else if (n.page) { h.push(field('Their page', '<a href="' + esc(n.page) + '">on the event site</a>' + (n.linkedin ? ' · <a href="' + esc(n.linkedin) + '">LinkedIn</a>' : ''))); }
      if (n.sha256) { h.push(field('SHA-256', '<code>' + esc(n.sha256.slice(0, 24)) + '…</code>' + (n.frozen ? ' · <a href="' + esc(n.frozen) + '">frozen copy</a>' : ''))); }
      h.push(field('Walks back to', '<code>' + esc(n.source) + '</code> <span class="dim">(a frozen, hashed copy in this repository)</span>'));
      /* every edge, both ways, as sentences */
      var out = [], inn = [];
      node.connectedEdges().forEach(function (e) {
        var fwd = e.source().id() === id, other = fwd ? e.target() : e.source();
        (fwd ? out : inn).push('<code>' + esc(verbLabel(e.data('verb'), !fwd)) + '</code> ' + esc(other.data('label')));
      });
      if (out.length) { h.push('<p class="small"><b>' + esc(n.label) + '</b><br>' + out.join('<br>') + '</p>'); }
      if (inn.length) { h.push('<p class="small"><b>' + esc(n.label) + '</b> (read the other way)<br>' + inn.join('<br>') + '</p>'); }
    }
    h.push('<p class="small dim"><button class="altib" data-focus="' + esc(id) + '">Centre the graph here</button> ' +
           '<button class="altib" data-lang="' + (cfg.lang === 'pt' ? 'en' : 'pt') + '">verbs in ' + (cfg.lang === 'pt' ? 'English' : 'português') + '</button></p>');
    if (d) { d.innerHTML = h.join('\n'); }
  }

  /* ------------------------------------------------- capture and restore */
  function viewSpec() {
    return { kind: 'newsroom.sgit.ai portugal graph view', version: D.version, saved: new Date().toISOString().slice(0, 10),
      cfg: JSON.parse(JSON.stringify(cfg)), zoom: cy.zoom(), pan: cy.pan(),
      collapsed: collapsed.map(function (g) { return { id: g.id, members: g.members }; }), focus: focusId,
      positions: cy.nodes().map(function (n) { return { id: n.id(), x: Math.round(n.position('x')), y: Math.round(n.position('y')) }; }) };
  }
  function download(name, blob) {
    var a = document.createElement('a'), u = URL.createObjectURL(blob);
    a.href = u; a.download = name; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(u); a.remove(); }, 500);
  }
  function savePng() { download('portugal-graph-' + D.snapshot + '.png', cy.png({ output: 'blob', full: true, scale: 2, bg: '#faf9f5' })); note('PNG saved.'); }
  function saveView() { download('portugal-graph-view-' + D.snapshot + '.json', new Blob([JSON.stringify(viewSpec(), null, 1)], { type: 'application/json' })); note('View saved: settings, zoom, pan, groups and every node position.'); }
  function loadView(spec) {
    try {
      if (!spec || !spec.cfg) { throw new Error('not a view spec'); }
      Object.keys(spec.cfg).forEach(function (k) { cfg[k] = spec.cfg[k]; });
      syncForm(); focusId = spec.focus || null; collapsed = []; draw(false);
      var pos = {}; (spec.positions || []).forEach(function (p) { pos[p.id] = { x: p.x, y: p.y }; });
      cy.nodes().forEach(function (n) { if (pos[n.id()]) { n.position(pos[n.id()]); } });
      if (spec.zoom) { cy.zoom(spec.zoom); cy.pan(spec.pan); }
      applyRadius(); stats(); note('View restored, positions and all.');
    } catch (e) { note('That file is not a view spec (' + e.message + ').'); }
  }
  function syncForm() {
    var f = document.getElementById('gcfg'); if (!f) { return; }
    Object.keys(cfg.packs).forEach(function (k) { var c = f.querySelector('[name="pack-' + k + '"]'); if (c) { c.checked = !!cfg.packs[k]; } });
    Object.keys(cfg.types).forEach(function (k) { var c = f.querySelector('[name="type-' + k + '"]'); if (c) { c.checked = cfg.types[k] !== false; } });
    Object.keys(cfg.verbs).forEach(function (k) { var c = f.querySelector('[name="verb-' + k + '"]'); if (c) { c.checked = cfg.verbs[k] !== false; } });
    ['stabilise'].forEach(function (k) { var c = f.querySelector('[name="' + k + '"]'); if (c) { c.checked = !!cfg[k]; } });
    ['colour', 'layout', 'labels', 'size', 'edgeLabels', 'lang'].forEach(function (k) {
      var r = f.querySelector('[name="' + k + '"][value="' + cfg[k] + '"]'); if (r) { r.checked = true; } });
    ['iterations', 'wrap', 'maxlen', 'radius'].forEach(function (k) {
      var i = f.querySelector('[name="' + k + '"]'); if (i) { i.value = String(cfg[k]); var o = document.getElementById('out-' + k); if (o) { o.textContent = cfg[k]; } } });
    var s = f.querySelector('[name="search"]'); if (s) { s.value = cfg.search || ''; }
  }

  /* ------------------------------------------------------------- events */
  document.addEventListener('change', function (e) {
    var t = e.target; if (!t.name || !t.closest('#gcfg')) { return; }
    if (t.name.indexOf('pack-') === 0) { cfg.packs[t.name.slice(5)] = t.checked; draw(false); return; }
    if (t.name.indexOf('type-') === 0) { cfg.types[t.name.slice(5)] = t.checked; draw(false); return; }
    if (t.name.indexOf('verb-') === 0) { cfg.verbs[t.name.slice(5)] = t.checked; draw(false); return; }
    if (t.type === 'checkbox') { cfg[t.name] = t.checked; }
    else if (t.type === 'range') { cfg[t.name] = +t.value; }
    else { cfg[t.name] = t.value; }
    var o = document.getElementById('out-' + t.name); if (o) { o.textContent = t.value; }
    if (t.name === 'radius') { applyRadius(); stats(); return; }
    if (t.name === 'iterations' || t.name === 'stabilise') { return; }
    if (t.name === 'lang') { cy.style(style()); draw(true); return; }
    if (t.name === 'labels' || t.name === 'wrap' || t.name === 'edgeLabels') { cy.style(style()); draw(true); return; }
    draw(t.name === 'colour' || t.name === 'size' || t.name === 'maxlen');
  });
  document.addEventListener('input', function (e) {
    var t = e.target; if (t.name !== 'search' || !t.closest('#gcfg')) { return; }
    clearTimeout(window.__gsearchT);
    window.__gsearchT = setTimeout(function () { cfg.search = t.value.trim(); draw(false); }, 220);
  });
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (t.hasAttribute && t.hasAttribute('data-focus')) { focusOn(t.getAttribute('data-focus'), Math.max(1, cfg.radius || 2)); return; }
    if (t.hasAttribute && t.hasAttribute('data-lang')) {
      cfg.lang = t.getAttribute('data-lang'); syncForm(); cy.style(style()); draw(true);
      if (window.__lastPath) { readPath(window.__lastPath); } else if (focusId && cy.$id(focusId).length) { detail(cy.$id(focusId)); }
      return;
    }
    var qp = t.closest && t.closest('[data-qpath]'); if (qp) { e.preventDefault(); showQPath(+qp.getAttribute('data-qpath')); return; }
    if (t.id === 'gqrun') { runQuery(); return; }
    if (t.hasAttribute && t.hasAttribute('data-preset')) {
      e.preventDefault();
      var pre = JSON.parse(t.getAttribute('data-preset')), f = document.getElementById('gq');
      if (pre.packs) { Object.keys(cfg.packs).forEach(function (k) { cfg.packs[k] = pre.packs.indexOf(k) > -1; }); syncForm(); draw(false); }
      if (pre.start) {
        f.querySelector('[name="q-start"]').value = pre.start;
        [1, 2, 3].forEach(function (i) {
          var st = pre.steps[i - 1] || { verb: 'stop', dir: 'out', node: 'any' };
          f.querySelector('[name="q-verb' + i + '"]').value = st.verb; f.querySelector('[name="q-dir' + i + '"]').value = st.dir; f.querySelector('[name="q-node' + i + '"]').value = st.node;
        });
        runQuery();
      }
      return;
    }
    switch (t.id) {
      case 'gfit': cy.fit(undefined, 30); break;
      case 'greset': cy.elements().removeClass('dim hot onpath pend'); focusId = null; cfg.radius = 0; cfg.search = ''; window.__lastPath = null; syncForm(); draw(false); clearDetail(); break;
      case 'grelayout': relayout(); break;
      case 'gstable': cfg.stabilise = true; cfg.iterations = Math.max(cfg.iterations, 6000); syncForm(); relayout(); note('Ran a long layout (' + cfg.iterations + ' iterations).'); break;
      case 'gpng': savePng(); break;
      case 'gsave': saveView(); break;
      case 'gload': document.getElementById('gfile').click(); break;
      case 'gcollapse': collapseSelection(); break;
      case 'gexpandall': collapsed.slice().forEach(function (g) { expandGroup(g.id); }); break;
      case 'gfull': { var w = document.querySelector('.gwrap'); if (!document.fullscreenElement) { w.requestFullscreen && w.requestFullscreen(); } else { document.exitFullscreen(); } break; }
      case 'gwide': document.querySelector('.gwrap').classList.toggle('gwide'); setTimeout(function () { cy.resize(); cy.fit(undefined, 30); }, 60); break;
    }
  });
  document.addEventListener('change', function (e) {
    if (e.target.id !== 'gfile' || !e.target.files || !e.target.files[0]) { return; }
    var r = new FileReader();
    r.onload = function () { try { loadView(JSON.parse(r.result)); } catch (x) { note('Could not read that file.'); } };
    r.readAsText(e.target.files[0]); e.target.value = '';
  });
  (function resizers() {
    var drag = null;
    document.addEventListener('pointerdown', function (e) {
      var h = e.target.closest('[data-gresize]'); if (!h) { return; }
      drag = { how: h.getAttribute('data-gresize'), x: e.clientX, y: e.clientY, h: el.getBoundingClientRect().height,
               w: document.querySelector('.gdetail').getBoundingClientRect().width };
      h.setPointerCapture(e.pointerId); document.body.classList.add('altdragging'); e.preventDefault();
    });
    document.addEventListener('pointermove', function (e) {
      if (!drag) { return; }
      if (drag.how === 'v') { el.style.height = Math.max(300, drag.h + (e.clientY - drag.y)) + 'px'; }
      else { document.querySelector('.gwrap').style.setProperty('--gdw', Math.max(180, Math.min(640, drag.w - (e.clientX - drag.x))) + 'px'); }
      cy.resize();
    });
    document.addEventListener('pointerup', function () { if (!drag) { return; } drag = null; document.body.classList.remove('altdragging'); cy.resize(); });
  })();
  document.addEventListener('fullscreenchange', function () { setTimeout(function () { cy.resize(); cy.fit(undefined, 30); }, 80); });

  /* ------------------------------------------------------------- the API
     Read and view levels only. Nothing here writes data — the graph is a projection of
     files in the repository and the only way to change it is to change those and rebuild. */
  var API = {
    meta: { name: 'portugal-graph', levels: ['read', 'view'], log: [] },
    get_graph: function () { return Promise.resolve({ version: D.version, snapshot: D.snapshot, counts: D.counts, packs: D.packs }); },
    get_nodes: function (p) { p = p || {}; return Promise.resolve(D.nodes.filter(function (n) { return (!p.type || n.type === p.type) && (!p.pack || n.pack === p.pack); })); },
    get_node: function (p) { var n = NODE[p.id]; if (!n) { return Promise.reject(new Error('unknown id ' + p.id)); } return Promise.resolve(n); },
    get_edges: function (p) { p = p || {}; return Promise.resolve(D.edges.filter(function (e) { return (!p.verb || e.verb === p.verb) && (!p.id || e.source === p.id || e.target === p.id); })); },
    get_ontology: function () { return Promise.resolve({ node_types: D._ont.node_types, edges: D._ont.edges, banned: D._ont.banned }); },
    search: function (p) { var q = String(p.text || '').toLowerCase(); return Promise.resolve(D.nodes.filter(function (n) { return (n.label + ' ' + (n.role || '') + ' ' + (n.org || '')).toLowerCase().indexOf(q) > -1; })); },
    get_state: function () { return Promise.resolve({ cfg: JSON.parse(JSON.stringify(cfg)), focus: focusId, visible: cy ? cy.nodes(':visible').length : 0 }); },
    select_node: function (p) { var n = cy.$id(p.id); if (!n.length) { return Promise.reject(new Error('not on canvas: ' + p.id)); } detail(n); return Promise.resolve(true); },
    set_verbs: function (p) { Object.keys(cfg.verbs).forEach(function (k) { cfg.verbs[k] = (p.verbs || []).indexOf(k) > -1; }); syncForm(); draw(false); return Promise.resolve(cfg.verbs); },
    set_packs: function (p) { Object.keys(cfg.packs).forEach(function (k) { cfg.packs[k] = (p.packs || []).indexOf(k) > -1; }); syncForm(); draw(false); return Promise.resolve(cfg.packs); },
    explore: function (p) { focusOn(p.id, p.degrees || 1); return Promise.resolve(true); },
    set_layout: function (p) { cfg.layout = p.layout; syncForm(); relayout(); return Promise.resolve(true); },
    set_language: function (p) { cfg.lang = p.lang === 'pt' ? 'pt' : 'en'; syncForm(); cy.style(style()); draw(true); return Promise.resolve(cfg.lang); },
    fit_graph: function () { cy.fit(undefined, 30); return Promise.resolve(true); },
    graph_snapshot: function (p) { return Promise.resolve(cy.png({ output: 'base64uri', full: !!(p && p.full), scale: 2, bg: '#faf9f5' })); },
    reset_view: function () { document.getElementById('greset').click(); return Promise.resolve(true); }
  };
  Object.keys(API).forEach(function (k) {
    if (k === 'meta') { return; }
    var fn = API[k];
    API[k] = function (p) {
      var t0 = Date.now();
      return fn(p).then(function (r) { API.meta.log.push({ method: k, params: p, ms: Date.now() - t0 }); if (API.meta.log.length > 500) { API.meta.log.shift(); } return r; });
    };
  });

  /* ------------------------------------------------------------- boot */
  var qs = {};
  location.search.replace(/^\?/, '').split('&').forEach(function (kv) { var p = kv.split('='); if (p[0]) { qs[decodeURIComponent(p[0])] = decodeURIComponent(p[1] || ''); } });
  Promise.all([fetch('data/graph.json').then(function (r) { return r.json(); }),
               fetch('data/ontology.json').then(function (r) { return r.json(); })])
  .then(function (rs) {
    D = rs[0]; D._ont = rs[1];
    D._ont.edges.forEach(function (e) { VERB[e.verb] = e; INV[e.verb] = e.inverse; INV[e.inverse] = e.verb; PT[e.verb] = e.pt; });
    D._ont.node_types.forEach(function (t) { TYPE[t.id] = t; });
    D._ont.taxonomy.forEach(function (c) { c.types.forEach(function (t) { TAX[t] = c.id; }); });
    D.nodes.forEach(function (n) { NODE[n.id] = n; });
    D._deg = {}; D.edges.forEach(function (e) { D._deg[e.source] = (D._deg[e.source] || 0) + 1; D._deg[e.target] = (D._deg[e.target] || 0) + 1; });
    D.packs.forEach(function (p) { cfg.packs[p.id] = !!p.default; });
    if (qs.packs) { Object.keys(cfg.packs).forEach(function (k) { cfg.packs[k] = qs.packs.split(',').indexOf(k) > -1; }); }
    D._ont.node_types.forEach(function (t) { cfg.types[t.id] = true; });
    document.querySelectorAll('#gcfg [name^="verb-"]').forEach(function (c) { cfg.verbs[c.name.slice(5)] = c.checked; });
    if (qs.lang === 'pt') { cfg.lang = 'pt'; }
    var inv = document.getElementById('ginventory');
    if (inv) {
      inv.innerHTML = D.packs.map(function (p) { return '<b>' + p.nodes + '</b> ' + esc(p.label.toLowerCase()); }).join(' · ') +
        ' &middot; snapshot <code>' + esc(D.snapshot) + '</code>';
    }
    syncForm(); clearDetail(); draw(false);
    if (qs.focus && NODE[qs.focus]) { focusOn(qs.focus, +(qs.radius || 1)); }
    window.__graph = API; window.__tools = window.__tools || {}; window.__tools['portugal-graph'] = API;
    window.dispatchEvent(new CustomEvent('tool:ready', { detail: { name: 'portugal-graph' } }));
  }).catch(function (e) {
    el.innerHTML = '<p class="small dim" style="padding:1rem">Could not load the graph data (' + esc(e.message) + '). The machine surface is <a href="data/graph.json">data/graph.json</a>.</p>';
  });
})();

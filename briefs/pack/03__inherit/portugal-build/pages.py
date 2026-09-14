#!/usr/bin/env python3
"""portugal/ — the front page, the graph page and the file explorer.

Imported by build.py, which hands each builder its own namespace (B) so these pages use the
same shell, masthead, disclaimer and escaping as every other page in the section. Kept apart
from build.py for the same reason governance/build/floor.py is: an interactive instrument is
a different kind of artefact from a projection of prose, and mixing them made both harder to
read.

The graph page reuses graphs.sgit.ai's instrument — Cytoscape.js vendored, and the same
control vocabulary — so a reader who has used one does not have to learn the other. The
explorer is the platform's vault-browser idea rendered from a manifest, for a section that is
not in a vault yet; the estate's guidance is not to rebuild what the platform has, and this
page says on its face that it goes when the vault browser takes over.
"""
import json
from datetime import date

FRONT_CSS = ('<style>.front-mast h1{margin-bottom:.1rem}.dateline{font-family:var(--mono);font-size:.74rem;'
             'letter-spacing:.06em;color:var(--dim);margin:0 0 1rem}.cards.front .card.lead{grid-column:1/-1;'
             'border-left:4px solid var(--accent)}.cards.front .card.lead h3{font-size:1.25rem}</style>')

GRAPH_CSS = """
<style>
main.doc{max-width:min(1900px,97vw)}   /* the instrument needs the width; the shell's reading measure does not apply here */
.gwrap{--gdw:300px;display:grid;grid-template-columns:236px minmax(0,1fr) 11px var(--gdw);gap:.8rem;margin:1.2rem 0 .8rem;align-items:start}
.gwrap.gwide{grid-template-columns:minmax(0,1fr)}
.gwrap.gwide .gcfg,.gwrap.gwide .gdetail,.gwrap.gwide .gresize-h{display:none}
.gwrap:fullscreen{background:var(--bg);padding:.6rem;gap:.6rem;align-content:start}
.gwrap:fullscreen #cy{height:calc(100vh - 90px)}
.gcfg{margin:0;display:flex;flex-direction:column;gap:.6rem;max-height:min(76vh,740px);overflow-y:auto}
.gcfg fieldset{margin:0;border:1px solid var(--line);border-radius:10px;padding:.5rem .7rem .6rem;background:#fff}
.gcfg legend{font:700 .68rem/1 var(--sans);letter-spacing:.09em;text-transform:uppercase;color:var(--dim2);padding:0 .3rem}
.gcfg label{display:block;font-size:.82rem;margin:.18rem 0;cursor:pointer}
.gcfg input{margin-right:.35rem}
.gcfg input[type=search]{width:100%;font:inherit;font-size:.82rem;padding:.35rem .5rem;border:1px solid var(--line2);border-radius:7px;margin:0}
.gcfg button{font:inherit;font-size:.8rem;padding:.25rem .6rem;margin:.15rem .3rem .15rem 0;border:1px solid var(--line);border-radius:7px;background:#fff;cursor:pointer}
.gcfg button:hover{border-color:var(--accent);color:var(--accent-dk)}
.gcfg .grange{display:block;font-size:.78rem;color:var(--dim);margin:.3rem 0}
.gcfg .grange input[type=range]{width:100%;margin-top:.1rem}
.gcfg output{font-weight:700;color:var(--accent-dk)}
.gcfg fieldset p{margin:.35rem 0 0}
.gmid{display:flex;flex-direction:column;min-width:0}
#cy{height:min(76vh,740px);border:1px solid var(--line);border-radius:12px;background:#fdfcf9}
.gresize-v{height:9px;cursor:row-resize;position:relative}
.gresize-v::before{content:"";position:absolute;left:36%;right:36%;top:3px;height:3px;border-radius:3px;background:var(--line)}
.gresize-v:hover::before{background:var(--accent)}
.gresize-h{cursor:col-resize;position:relative}
.gresize-h::before{content:"";position:absolute;inset:0 4px;border-radius:3px;background:var(--line)}
.gresize-h:hover::before{background:var(--accent)}
.gdetail{border:1px solid var(--line);border-radius:12px;padding:.8rem .95rem;background:#fff;max-height:min(76vh,740px);overflow-y:auto}
.gdetail h3{margin:.1rem 0 .3rem;font-size:.98rem}
.gdetail p{margin:.35rem 0;font-size:.88rem}
.altib{font:inherit;font-size:.72rem;padding:.15rem .55rem;border:1px solid var(--line);border-radius:999px;background:#fff;cursor:pointer;color:var(--dim);white-space:nowrap;text-decoration:none;display:inline-block;margin:.15rem .2rem .15rem 0}
.altib:hover{border-color:var(--accent);color:var(--accent-dk);text-decoration:none}
body.altdragging{cursor:col-resize;user-select:none}
.gpath{margin:.4rem 0 0;padding-left:1.2rem;font-size:.88rem}
.gpath li{margin:.3rem 0}
.gpath code{background:#e9f3f1;border-color:#9cc5be}
.gqrow{display:flex;align-items:center;gap:.45rem;margin:.35rem 0;flex-wrap:wrap}
.gqrow label{font-size:.85rem;display:flex;align-items:center;gap:.4rem}
.gqrow select{font:inherit;font-size:.85rem;padding:.25rem .4rem;border:1px solid var(--line2);border-radius:6px;background:#fff;max-width:100%}
.gqn{font-family:var(--mono);font-size:.72rem;color:var(--dim2);width:1.2rem}
.gqout .gpath a{color:inherit}
.gqout .gpath a:hover{text-decoration:none;background:#f4f8f7}
.swatch{display:inline-block;width:.7em;height:.7em;border-radius:50%;margin-right:.35em;vertical-align:-.05em}
@media(max-width:1100px){.gwrap,.gwrap.gwide{grid-template-columns:1fr}.gresize-h{display:none}#cy{height:60vh}.gdetail,.gcfg{max-height:none}}
</style>"""


# ------------------------------------------------------------------ front ---
def build_index(B):
    """The front page. A newspaper's, not a section hub's: a lead, the wire, what is on
    this week, what the press says, the room as a graph, and who made it — every number
    computed, every source frozen."""
    esc, page, write, masthead, disclaimer, agent_block = (
        B["esc"], B["page"], B["write"], B["masthead"], B["disclaimer"], B["agent_block"])
    STORIES, TEAM, GRAPH, PEOPLE, ORGS, SOURCES, CHANGES, SESSIONS, COVERAGE, EVENT, SRC, LATEST = (
        B["STORIES"], B["TEAM"], B["GRAPH"], B["PEOPLE"], B["ORGS"], B["SOURCES"], B["CHANGES"],
        B["SESSIONS"], B["COVERAGE"], B["EVENT"], B["SRC"], B["LATEST"])
    up = ""
    ch = CHANGES["changes"][-1] if CHANGES["changes"] else None
    lead, rest = STORIES["stories"][0], STORIES["stories"][1:]

    def card(st, big=False):
        return (f'<div class="card{" lead" if big else ""}">'
                f'<span class="tag">{esc(st["kicker"])}</span>'
                f'<h3><a href="stories/{st["slug"]}.html">{esc(st["title"])}</a></h3>'
                f'<p>{esc(st["standfirst"])}</p>'
                f'<p class="dim small" style="margin-top:.6rem">{esc(st["published"])} &middot; '
                f'{len(st["stands_on"])} frozen source{"s" if len(st["stands_on"]) != 1 else ""} &middot; '
                f'reviewed by {esc(TEAM["editor_of_record"]["name"])}</p></div>')

    days = {}
    for sn in SESSIONS["sessions"]:
        days.setdefault(sn["day"], []).append(sn)
    stage_label = {st["id"]: st["label"] for st in SESSIONS["stages"]}
    prog = ""
    for d in sorted(days):
        rows = "".join(
            f'<li><span class="when">{esc(sn["time"])}</span><span class="what"><b>{esc(sn["title"])}</b>'
            + (f' <span class="dim small">&middot; {esc(stage_label[sn["stage"]])}</span>' if sn["stage"] else "")
            + "</span></li>" for sn in days[d])
        prog += f'<h3>{esc(d)}</h3><ul class="timeline">{rows}</ul>'

    cov = "".join(
        f'<tr><td><a href="{esc(c["url"])}">{esc(c["title"][:70])}{"&hellip;" if len(c["title"]) > 70 else ""}</a><br>'
        f'<span class="dim small">{esc(c["publisher"])} &middot; {esc(c["kind"])}'
        + (f' &middot; {esc(c["published"])}' if c.get("published") else "") + "</span></td>"
        f'<td class="small">{esc(c["what_it_says"])}</td>'
        f'<td class="small"><a href="{esc(SRC[c["source"]]["frozen"])}">frozen</a><br><code>{esc(c["sha256"][:12])}&hellip;</code></td></tr>'
        for c in COVERAGE["items"])
    excluded = "".join(f'<p class="small dim"><b>Excluded:</b> {esc(x["why"])}</p>' for x in COVERAGE.get("excluded", []))

    roles = "".join(
        f'<li><a href="team/{esc(r["id"])}/index.html"><b>{esc(r["name"])}</b></a> &mdash; {esc(r["gravity"])}</li>'
        for r in TEAM["roles"])
    investors = sum(1 for n in GRAPH["nodes"] if n["type"] == "Person" and n.get("role_class") == "investor")

    moving = ""
    if ch:
        moving = (f'<h2 id="moving">The list is moving</h2>'
                  f'<p>Between the two snapshots this section holds, the published speaker list went from '
                  f'<b>{ch["count_from"]} to {ch["count_to"]}</b>: {len(ch["added"])} names added and '
                  f'{len(ch["removed"])} removed. Both copies are in this repository and both are hashed. '
                  f'<a href="summit/changes.html">Name by name &rarr;</a></p>')

    body = f"""{masthead(up, "index.html")}
{FRONT_CSS}
<div class="front-mast">
  <h1>{esc(STORIES["masthead"])}</h1>
  <p class="dateline">Lisbon &middot; {esc(LATEST)} &middot; <b>{B["days_to_doors"]()} days</b> to Startup Summit Lisbon
  &middot; edition built from snapshot <code>{esc(LATEST)}</code></p>
</div>
<p class="lead">{esc(STORIES["beat"])} <b>Every claim on this site walks back to a hashed copy of
somebody else&rsquo;s page</b> &mdash; we connect the dots, we do not draw them.</p>

{disclaimer(up)}

<div class="cards front">
  {card(lead, True)}
  {"".join(card(st) for st in rest)}
</div>

<div class="proof">
  <div class="n"><b>{GRAPH["counts"]["nodes"]}</b><span>nodes in the graph</span></div>
  <div class="n"><b>{GRAPH["counts"]["edges"]}</b><span>typed edges, each with an inverse</span></div>
  <div class="n"><b>{PEOPLE["count"]}</b><span>speakers &middot; {ORGS["count"]} organisations</span></div>
  <div class="n"><b>{SOURCES["count"]}</b><span>frozen, hashed sources</span></div>
</div>

<h2 id="graph">The room, as a graph</h2>
<p>The event, its speakers, the organisations they are listed under, the programme, the
evidence and what the press says &mdash; <b>one graph, {GRAPH["counts"]["nodes"]} nodes, every
edge a verb you can read as a sentence in English or Portuguese.</b> Start with the people and
switch the other blocks on one at a time.</p>
<div class="cards">
  <div class="card"><span class="tag">Explore</span><h3><a href="graph.html">The graph</a></h3>
    <p>Filter by pack, colour by type or by who is investor-side, trace a path between any two
    nodes and read it aloud, keep a view. The same instrument graphs.sgit.ai uses.</p></div>
  <div class="card"><span class="tag">Inspect</span><h3><a href="explorer.html">The files</a></h3>
    <p>Every JSON file the section is built from, every frozen page with its hash &mdash;
    rendered, as a graph, and raw. Nothing on this site exists that is not in that list.</p></div>
  <div class="card"><span class="tag">Who is there</span><h3><a href="summit/people.html">{PEOPLE["count"]} speakers</a></h3>
    <p>Filter by name, role or organisation. {investors} are investor-side <em>by listed
    title</em> &mdash; a published formula, not a fact about anybody.</p></div>
</div>

<h2 id="today">This week in Lisbon</h2>
<p>The programme as <a href="{esc(EVENT["url"])}/agenda">the event&rsquo;s own agenda page</a>
publishes it, transcribed from the frozen copy and checked against it verbatim by the gate.
The page calls itself a summarised view and says more is announced weekly.</p>
{prog}
<p class="small dim">{esc(SESSIONS["ai_note"])}</p>

<h2 id="press">What the press says</h2>
<p><b>{COVERAGE["count"]} pages by other publishers</b>, each fetched, frozen and hashed before
it was cited. The summaries are ours; nothing is quoted. Follow the link for what they actually
wrote. Machine surface: <a href="data/coverage.json">coverage.json</a>.</p>
<div class="tablewrap"><table>
  <thead><tr><th>Who</th><th>What it says, in our words</th><th>Our copy</th></tr></thead>
  <tbody>{cov}</tbody>
</table></div>
{excluded}

{moving}

<h2 id="made">How this is made</h2>
<p>Seven agent roles and a named human. <b>{esc(TEAM["editor_of_record"]["name"])} is the editor
of record</b> and reads every page before it publishes. The roles, each with a centre of gravity
and a list of what it refuses:</p>
<ul>{roles}</ul>
<p><a href="method.html">The method</a> &middot; <a href="team.html">The team</a> &middot;
<a href="notice.html">If you are named here</a> &middot; <a href="about.html">The limits</a></p>

<h2 id="builders">For builders</h2>
<p>This section is the first pass of a publication that will move to its own domain. The
commissioning brief for the natively Portuguese newsroom that follows it &mdash; written for
the agent that will build it &mdash; is
<a href="../documents/pt-newsroom.html"><b>here</b></a>, and it opens by saying which of its
own problems this section has already solved.</p>

{agent_block(
    "The front page of Portugal Startups. Machine surfaces: <code>/portugal/data/graph.json</code> "
    "(the whole section as a graph, with packs), <code>ontology.json</code> (types and verbs with "
    "inverses, in English and Portuguese), <code>coverage.json</code> (third-party pages, frozen "
    "and hashed, summarised not quoted), <code>sessions.json</code>, <code>people.json</code>, "
    "<code>sources.json</code>. Every source is primary and hashed; every claim walks back to one. "
    "The role_class on a person is a published FORMULA over the listed title, not a fact. This "
    "publication assesses nobody and explains no absence from anybody's list.")}
"""
    return write("index.html", page("index.html", STORIES["masthead"],
        "Portugal Startups — the Portuguese startup ecosystem from primary sources, frozen and hashed. This week: Startup Summit Lisbon, as a graph.",
        body, '<a href="../index.html">newsroom.sgit.ai</a> / portugal'))


# ------------------------------------------------------------------ graph ---
def build_graph_page(B):
    esc, page, write, masthead, disclaimer, agent_block = (
        B["esc"], B["page"], B["write"], B["masthead"], B["disclaimer"], B["agent_block"])
    GRAPH, ONTOLOGY = B["GRAPH"], B["ONTOLOGY"]
    up = ""
    packs = "".join(
        f'<label><input type="checkbox" name="pack-{esc(p["id"])}"{" checked" if p["default"] else ""}> '
        f'<b>{esc(p["label"])}</b> <span class="small dim">({p["nodes"]})</span></label>' for p in GRAPH["packs"])
    types = "".join(
        f'<label><input type="checkbox" name="type-{esc(t["id"])}" checked>'
        f'<span class="swatch" style="background:{esc(t["colour"])}"></span>{esc(t["label"])} '
        f'<span class="small dim">&middot; {esc(t["pt"])} &middot; {GRAPH["counts"]["by_type"].get(t["id"], 0)}</span></label>'
        for t in ONTOLOGY["node_types"])
    verbopts = "".join(f'<option value="{esc(v)}">{esc(v)}</option>' for v in sorted({e["verb"] for e in ONTOLOGY["edges"]}))
    OFF = {"speaks_at", "attested_by"}
    verb_count = {}
    for e in GRAPH["edges"]:
        verb_count[e["verb"]] = verb_count.get(e["verb"], 0) + 1
    verbs_ctl = "".join(
        f'<label><input type="checkbox" name="verb-{esc(v)}"{"" if v in OFF else " checked"}> <code>{esc(v)}</code> '
        f'<span class="small dim">{verb_count.get(v, 0)}</span></label>'
        for v in sorted({e["verb"] for e in ONTOLOGY["edges"]}))
    typeopts = "".join(f'<option value="type:{esc(t["id"])}">{esc(t["label"].lower())}</option>' for t in ONTOLOGY["node_types"])
    extra = ('<option value="role:investor">an investor-side person (by title)</option>'
             '<option value="role:founder">a founder/operator (by title)</option>'
             '<option value="gone">someone no longer listed</option>'
             '<option value="placeholder">a placeholder organisation</option>')

    def step(i, first):
        stop = '<option value="stop">— stop here —</option>'
        return (f'<div class="gqrow"><span class="gqn">{i}</span>'
                f'<select name="q-verb{i}">{"" if first else stop}<option value="any">any edge</option>{verbopts}{stop if first else ""}</select>'
                f'<select name="q-dir{i}"><option value="out">forwards</option><option value="in">backwards</option><option value="any">either way</option></select>'
                f'<select name="q-node{i}"><option value="any">anything</option>{typeopts}{extra}</select></div>')

    erows = "".join(
        f'<tr><td><code>{esc(e["verb"])}</code><br><span class="dim small">{esc(e["pt"]["verb"])}</span></td>'
        f'<td><code>{esc(e["inverse"])}</code><br><span class="dim small">{esc(e["pt"]["inverse"])}</span></td>'
        f'<td class="small">{esc(e["domain"])} &rarr; {esc(e["range"])}</td>'
        f'<td class="small">{esc(e["reads"].replace("{s}", "A").replace("{t}", "B"))}</td></tr>'
        for e in ONTOLOGY["edges"])
    brows = "".join(f'<tr><td><code>{esc(b["verb"])}</code></td><td class="small">{esc(b["why"])}</td></tr>' for b in ONTOLOGY["banned"])
    frows = "".join(
        f'<tr><td><b>{esc(r["class"])}</b></td><td class="small">{esc(r["label"])}</td><td><code>{esc(r["pattern"])}</code></td></tr>'
        for r in ONTOLOGY["formulas"][0]["rules"])
    presets = [
        ("The room: event, organisations, people", {"packs": ["event", "orgs", "people"]}),
        ("The programme", {"packs": ["event", "sessions"]}),
        ("What moved between snapshots", {"packs": ["event", "people", "changes", "sources"]}),
        ("What the press says", {"packs": ["event", "coverage"]}),
        ("Our stories and what they stand on", {"packs": ["event", "stories", "sources"]}),
        ("Organisations with an investor-side speaker", {"packs": ["event", "orgs", "people"], "start": "type:Organisation",
                                                          "steps": [{"verb": "listed_under", "dir": "in", "node": "role:investor"}]}),
        ("Who is no longer listed, and which snapshot still has them", {"packs": ["event", "people", "changes", "sources"], "start": "gone",
                                                                        "steps": [{"verb": "present_in", "dir": "out", "node": "type:Snapshot"}]}),
        ("Topics: what the event says each speaker speaks on", {"packs": ["people", "topics"]}),
        ("Derived tags: industries, technologies, ideas, offerings", {"packs": ["people", "tags"]}),
        ("Organisations whose speakers speak on AI", {"packs": ["orgs", "people", "topics"], "start": "type:Organisation",
                                                     "steps": [{"verb": "listed_under", "dir": "in", "node": "type:Person"},
                                                               {"verb": "speaks_on", "dir": "out", "node": "AI"}]}),
    ]
    preset_html = "".join(
        f'<a href="#" class="altib" data-preset=\'{json.dumps(pre)}\'>{esc(label)}</a>' for label, pre in presets)

    body = f"""{masthead(up, "graph.html")}
<h1>The graph</h1>
<p class="lead">{GRAPH["counts"]["nodes"]} nodes, {GRAPH["counts"]["edges"]} edges, one event. <b>Start
with the people and switch the other blocks on one at a time.</b> Click a node to open it,
double-click to centre on it, shift-click two to read the path between them as sentences
&mdash; in English or in Portuguese. Machine surfaces: <a href="data/graph.json">graph.json</a>
&middot; <a href="data/ontology.json">ontology.json</a>.</p>

{disclaimer(up)}

<div class="note"><p style="margin-top:0"><b>The instrument is borrowed, on purpose.</b> This is
the same graph engine and the same control vocabulary as
<a href="https://graphs.sgit.ai/v1/altitudes/graph.html">graphs.sgit.ai</a>&rsquo;s own graph
pages &mdash; Cytoscape.js vendored into this site, packs instead of levels, otherwise the same
panel. A reader who has used one should not have to learn the other. What is this section&rsquo;s
own: every node carries the frozen, hashed source it came from, and the detail pane shows it.</p>
<p style="margin-bottom:0"><b>Query it instead of drawing it.</b> The same graph is loaded into two real
database engines in your browser, with no server: <a href="../databases/sql.html">SQL</a> (SQLite over the
section&rsquo;s JSON) and <a href="../databases/graph.html">SPARQL</a> (Oxigraph over the same graph as
triples, ontology inside the store). Worked queries on both, with the count each returned at build.</p></div>

<div class="gwrap">
  <form id="gcfg" class="gcfg">
    <fieldset><legend>Find</legend>
      <input type="search" name="search" placeholder="name, role, organisation&hellip;" aria-label="Filter nodes">
    </fieldset>
    <fieldset><legend>Packs &middot; blocks of nodes</legend>{packs}
      <p class="small dim">Switch a block on and its nodes and edges join the graph.</p></fieldset>
    <fieldset><legend>Types</legend>{types}</fieldset>
    <fieldset><legend>Edges</legend>{verbs_ctl}
      <p class="small dim"><code>speaks_at</code> is off by default: 64 spokes into one node hide everything else. <code>attested_by</code> is off because every node carries its source in the detail pane anyway.</p></fieldset>
    <fieldset><legend>Colour by</legend>
      <label><input type="radio" name="colour" value="type" checked> what kind of node</label>
      <label><input type="radio" name="colour" value="pack"> which pack</label>
      <label><input type="radio" name="colour" value="role"> investor / founder / advisor, by listed title</label>
      <label><input type="radio" name="colour" value="class"> taxonomy class</label>
    </fieldset>
    <fieldset><legend>Labels</legend>
      <label><input type="radio" name="labels" value="inside"> inside the node</label>
      <label><input type="radio" name="labels" value="below" checked> below the node</label>
      <label><input type="radio" name="labels" value="none"> none</label>
      <label class="grange">wrap at <output id="out-wrap">18</output> chars
        <input type="range" name="wrap" min="10" max="46" step="2" value="18"></label>
      <label class="grange">cut at <output id="out-maxlen">30</output> chars
        <input type="range" name="maxlen" min="12" max="90" step="2" value="30"></label>
      <label><input type="radio" name="edgeLabels" value="none" checked> no edge labels</label>
      <label><input type="radio" name="edgeLabels" value="verb"> name the edges</label>
      <label><input type="radio" name="lang" value="en" checked> verbs in English</label>
      <label><input type="radio" name="lang" value="pt"> verbos em português</label>
    </fieldset>
    <fieldset><legend>Size by</legend>
      <label><input type="radio" name="size" value="degree" checked> how connected</label>
      <label><input type="radio" name="size" value="fixed"> uniform</label>
    </fieldset>
    <fieldset><legend>Layout</legend>
      <label><input type="radio" name="layout" value="force" checked> force</label>
      <label><input type="radio" name="layout" value="bands"> bands, by taxonomy class</label>
      <label><input type="radio" name="layout" value="concentric"> concentric</label>
      <label><input type="radio" name="layout" value="grid"> grid</label>
      <label class="grange">iterations <output id="out-iterations">2000</output>
        <input type="range" name="iterations" min="300" max="12000" step="300" value="2000"></label>
      <label><input type="checkbox" name="stabilise"> cool slowly (settles further)</label>
      <button type="button" id="grelayout">Re-run layout</button>
      <button type="button" id="gstable">Run until settled</button>
    </fieldset>
    <fieldset><legend>Explore from one place</legend>
      <label class="grange">radius <output id="out-radius">0</output> hops
        <input type="range" name="radius" min="0" max="4" step="1" value="0"></label>
      <p class="small dim">0 shows everything. Above 0, only what is within that many hops of the centred node.</p>
      <button type="button" id="gcollapse">Collapse selection</button>
      <button type="button" id="gexpandall">Expand all groups</button>
    </fieldset>
    <fieldset><legend>Keep this view</legend>
      <button type="button" id="gpng">Save PNG</button>
      <button type="button" id="gsave">Save view (.json)</button>
      <button type="button" id="gload">Load view</button>
      <input type="file" id="gfile" accept="application/json" hidden>
    </fieldset>
    <fieldset><legend>Screen</legend>
      <button type="button" id="gwide">Hide the panels</button>
      <button type="button" id="gfull">Full screen</button>
      <button type="button" id="gfit">Fit to screen</button>
      <button type="button" id="greset">Clear</button>
      <p class="small dim" id="gstats"></p>
    </fieldset>
  </form>
  <div class="gmid">
    <div id="cy"></div>
    <div class="gresize-v" data-gresize="v" title="Drag to make the graph taller"></div>
  </div>
  <div class="gresize-h" data-gresize="h" title="Drag to resize the panel"></div>
  <aside id="gdetail" class="gdetail"></aside>
</div>
<p class="small dim" id="gnote"></p>
<p class="small dim" id="ginventory"></p>

<h2 id="presets">Start here</h2>
<p class="small">Each button sets the packs and, where it makes sense, runs a query.</p>
<p>{preset_html}</p>

<h2 id="query">Query the paths</h2>
<p>Tracing answers <em>how do these two connect?</em> This answers <b>show me every route
shaped like this</b>: a start filter, then up to three edge-and-node steps, walked
breadth-first with a bound &mdash; and it says when it hit the bound, because a query that
silently truncates is worse than one that refuses.</p>
<form id="gq" class="gq">
  <div class="gqrow"><label>Start at
    <select name="q-start">{typeopts}<option value="role:investor">an investor-side person (by title)</option>
    <option value="gone">someone no longer listed</option><option value="any">anything</option></select></label></div>
  {step(1, True)}{step(2, False)}{step(3, False)}
  <div class="gqrow"><button type="button" id="gqrun" class="altib">Run the query</button></div>
</form>
<div id="gqout" class="gqout"></div>

<h2 id="vocabulary">The vocabulary</h2>
<p>Every edge is a verb with a distinct, named inverse, and every verb carries its Portuguese.
Walked forwards a path uses the verb; walked backwards it uses the inverse; either way it is a
sentence. Inherited from <a href="{esc(ONTOLOGY["inherits_from"]["page"])}">graphs.sgit.ai&rsquo;s
edge grammar</a>.</p>
<div class="tablewrap"><table>
  <thead><tr><th>Verb</th><th>Inverse</th><th>Domain &rarr; range</th><th>Reads as</th></tr></thead>
  <tbody>{erows}</tbody>
</table></div>
<h3>Banned</h3>
<div class="tablewrap"><table><thead><tr><th>Verb</th><th>Why</th></tr></thead><tbody>{brows}</tbody></table></div>
<h3>The one formula</h3>
<p>{esc(ONTOLOGY["formulas"][0]["note"])}</p>
<div class="tablewrap"><table><thead><tr><th>Class</th><th>Shown as</th><th>Pattern, against the listed title</th></tr></thead><tbody>{frows}</tbody></table></div>

{agent_block(
    "Fetch <code>/portugal/data/graph.json</code> and <code>/portugal/data/ontology.json</code> "
    "rather than parsing this page. Every node names its frozen source; every edge is a verb "
    "with a named inverse in both languages. <b>This page also publishes an API</b>: after the "
    "<code>tool:ready</code> event, <code>window.__graph</code> exposes read methods "
    "(<code>get_graph</code>, <code>get_nodes</code>, <code>get_node</code>, <code>get_edges</code>, "
    "<code>get_ontology</code>, <code>search</code>) and view methods (<code>set_packs</code>, "
    "<code>explore</code>, <code>select_node</code>, <code>set_layout</code>, <code>set_language</code>, "
    "<code>fit_graph</code>, <code>graph_snapshot</code>, <code>reset_view</code>). Nothing writes. "
    "The <code>role_class</code> on a person is a published formula over the listed title, not a fact.")}

{GRAPH_CSS}
<script src="../assets/vendor/cytoscape.min.js"></script>
<script src="../assets/portugal-graph.js" defer></script>
"""
    return write("graph.html", page("graph.html", "The graph",
        f'{GRAPH["counts"]["nodes"]} nodes and {GRAPH["counts"]["edges"]} typed edges: the event, its speakers, their organisations, the programme, the evidence and the press, explorable block by block.',
        body, '<a href="../index.html">newsroom.sgit.ai</a> / <a href="index.html">portugal</a> / graph'))


# --------------------------------------------------------------- explorer ---
def build_explorer(B):
    esc, page, write, masthead, disclaimer, agent_block = (
        B["esc"], B["page"], B["write"], B["masthead"], B["disclaimer"], B["agent_block"])
    MANIFEST = B["MANIFEST"]
    up = ""
    groups = {}
    for f in MANIFEST["files"]:
        top = f["path"].split("/")[0] if "/" in f["path"] else "."
        if f["path"].startswith("sources/frozen/"):
            parts = f["path"].split("/")
            top = "sources/frozen/" + parts[2] + ("/coverage" if len(parts) > 4 else "")
        groups.setdefault(top, []).append(f)
    tree = ""
    for g in sorted(groups):
        items = "".join(
            f'<li><a href="#" data-path="{esc(f["path"])}" data-kind="{esc(f["kind"])}" data-sha="{esc(f["sha256"])}" data-bytes="{f["bytes"]}">'
            f'{esc(f["path"].split("/")[-1])}</a> <span class="dim small">{f["bytes"]:,}b</span></li>'
            for f in groups[g])
        tree += (f'<details{" open" if g in ("data", "content") else ""}><summary><b>{esc(g)}/</b> '
                 f'<span class="dim small">{len(groups[g])}</span></summary><ul>{items}</ul></details>')
    pack_of = {"people.json": "people", "orgs.json": "orgs", "event.json": "event", "sessions.json": "sessions",
               "sources.json": "sources", "changes.json": "changes", "coverage.json": "coverage",
               "stories.json": "stories", "graph.json": "event,orgs,people,sessions,sources,changes,coverage,stories"}

    body = f"""{masthead(up, "explorer.html")}
<h1>The files</h1>
<p class="lead">Every file this section is built from &mdash; <b>{MANIFEST["count"]} of them</b>,
each with its size and SHA-256 &mdash; rendered, as a graph, and raw. If it is not in this
list, it is not on this site. Machine surface: <a href="data/manifest.json">manifest.json</a>.</p>

{disclaimer(up)}

<div class="note"><p style="margin-top:0"><b>What this is, and what it is not.</b> The platform
this site sits on has a vault browser that does exactly this for any vault, and the estate&rsquo;s
guidance is not to rebuild what the platform has. This section is not in a vault yet, so this
page is the same idea rendered from a manifest: a folder on the left, and the file on the
right in three views. When the section moves into a vault, the vault browser takes over and
this page goes.</p>
<p style="margin-bottom:0"><b>Query the files instead of opening them.</b> Every JSON file listed here is loaded into <a href="../databases/sql.html">a SQLite console</a> and the graph into <a href="../databases/graph.html">a SPARQL console</a>, both running in your browser with no server; the loader spec names the file and field behind every column, so a cell in a result is one click from the file it came from.</p></div>

<div class="xwrap">
  <nav class="xtree" aria-label="Files">{tree}</nav>
  <section class="xpane">
    <div class="xtabs" role="tablist">
      <button type="button" class="on" data-tab="render">Rendered</button>
      <button type="button" data-tab="graph">Graph</button>
      <button type="button" data-tab="raw">JSON / raw</button>
      <span id="xmeta" class="dim small"></span>
    </div>
    <div id="xrender" class="xview"><p class="dim small">Pick a file on the left.</p></div>
    <div id="xgraph" class="xview" hidden><iframe id="xframe" title="The graph, filtered to this file" loading="lazy"></iframe></div>
    <pre id="xraw" class="xview" hidden></pre>
  </section>
</div>

{agent_block(
    "The manifest at <code>/portugal/data/manifest.json</code> lists every file this section is "
    "built from with its SHA-256. Fetch the JSON files directly rather than this page. Frozen "
    "copies under <code>sources/frozen/</code> are unmodified third-party bytes held as evidence "
    "and are not rendered here — only linked, with their hash.")}

<style>
main.doc{{max-width:min(1600px,97vw)}}
.xwrap{{display:grid;grid-template-columns:260px minmax(0,1fr);gap:1rem;margin:1.2rem 0;align-items:start}}
.xtree{{border:1px solid var(--line);border-radius:12px;background:#fff;padding:.6rem .8rem;max-height:76vh;overflow:auto;font-size:.84rem}}
.xtree details{{margin:.2rem 0}} .xtree summary{{cursor:pointer;padding:.15rem 0}}
.xtree ul{{list-style:none;margin:.1rem 0 .3rem;padding-left:.9rem}} .xtree li{{margin:.12rem 0;overflow-wrap:anywhere}}
.xtree a.on{{font-weight:700;color:var(--accent-dk)}}
.xpane{{border:1px solid var(--line);border-radius:12px;background:#fff;min-height:60vh;min-width:0}}
.xtabs{{display:flex;gap:.3rem;align-items:center;border-bottom:1px solid var(--line);padding:.5rem .7rem;flex-wrap:wrap}}
.xtabs button{{font:inherit;font-size:.82rem;padding:.3rem .7rem;border:1px solid var(--line);border-radius:7px;background:#fff;cursor:pointer}}
.xtabs button.on{{background:var(--accent);border-color:var(--accent);color:#fff}}
.xtabs #xmeta{{margin-left:auto;font-family:var(--mono);font-size:.7rem}}
.xview{{padding:.9rem 1rem;max-height:70vh;overflow:auto;font-size:.88rem}}
pre.xview{{font-family:var(--mono);font-size:.76rem;line-height:1.5;background:var(--term-bg);color:#e6edf3;border-radius:0 0 12px 12px;margin:0;white-space:pre-wrap;overflow-wrap:anywhere}}
#xframe{{width:100%;height:70vh;border:0;border-radius:0 0 12px 12px}}
.xview table{{border-collapse:collapse;width:100%;font-size:.82rem;margin:.5rem 0}}
.xview th,.xview td{{border-bottom:1px solid var(--line);padding:.3rem .5rem;text-align:left;vertical-align:top}}
.xview th{{background:var(--panel2);font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:var(--dim);white-space:nowrap}}
.xview td{{min-width:6rem}}
.xview dl{{display:grid;grid-template-columns:max-content 1fr;gap:.25rem .9rem}} .xview dt{{color:var(--dim);font-size:.78rem}} .xview dd{{margin:0;overflow-wrap:anywhere}}
@media(max-width:800px){{.xwrap{{grid-template-columns:1fr}}.xtree{{max-height:40vh}}.xview dl{{grid-template-columns:1fr}}}}
</style>
<script src="../assets/vendor/marked.min.js"></script>
<script>
(function(){{
  var PACK = {json.dumps(pack_of)};
  var render = document.getElementById('xrender'), raw = document.getElementById('xraw'),
      frame = document.getElementById('xframe'), meta = document.getElementById('xmeta');
  function esc(t){{ return String(t==null?'':t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}
  function isRows(a){{ return a.length && a.every(function(x){{ return x && typeof x==='object' && !Array.isArray(x); }}); }}
  function cell(v){{
    if (v==null) return '<span class="dim">—</span>';
    if (typeof v==='string') return /^https?:\\/\\//.test(v) ? "<a href='"+esc(v)+"'>"+esc(v.replace(/^https?:\\/\\//,'').slice(0,70))+'</a>' : esc(v);
    if (typeof v!=='object') return esc(v);
    if (Array.isArray(v)) return v.length + ' item' + (v.length===1?'':'s');
    return '{{' + Object.keys(v).length + ' fields}}';
  }}
  function table(rows){{
    var cols = []; rows.forEach(function(r){{ Object.keys(r).forEach(function(k){{ if (cols.indexOf(k)<0) cols.push(k); }}); }});
    cols = cols.slice(0, 9);
    return '<div style="overflow-x:auto"><table><thead><tr>' + cols.map(function(c){{ return '<th>'+esc(c)+'</th>'; }}).join('') + '</tr></thead><tbody>' +
      rows.map(function(r){{ return '<tr>' + cols.map(function(c){{ return '<td>'+cell(r[c])+'</td>'; }}).join('') + '</tr>'; }}).join('') + '</tbody></table></div>';
  }}
  function obj(o, depth){{
    var h = '<dl>';
    Object.keys(o).forEach(function(k){{
      var v = o[k];
      if (Array.isArray(v) && isRows(v)) h += '<dt>'+esc(k)+'</dt><dd><b>'+v.length+' rows</b>'+table(v)+'</dd>';
      else if (Array.isArray(v)) h += '<dt>'+esc(k)+'</dt><dd>'+v.map(cell).join(' · ')+'</dd>';
      else if (v && typeof v==='object' && depth<2) h += '<dt>'+esc(k)+'</dt><dd>'+obj(v, depth+1)+'</dd>';
      else h += '<dt>'+esc(k)+'</dt><dd>'+cell(v)+'</dd>';
    }});
    return h + '</dl>';
  }}
  function show(path, kind, sha, bytes){{
    meta.textContent = bytes.toLocaleString() + ' bytes · sha256 ' + sha.slice(0,16) + '…';
    document.querySelectorAll('.xtree a').forEach(function(a){{ a.classList.toggle('on', a.dataset.path===path); }});
    var name = path.split('/').pop();
    frame.src = 'graph.html?packs=' + (PACK[name] || 'event');
    if (kind==='frozen') {{
      render.innerHTML = '<p><b>' + esc(name) + '</b> is a frozen copy of somebody else\\'s page, held as evidence. ' +
        'It is not rendered here on purpose — this publication links rather than reproduces. ' +
        "<a href='" + esc(path) + "'>Download it</a>, hash it, and compare with the register.</p><p class='dim small'>sha256 " + esc(sha) + '</p>';
      raw.textContent = '(not shown — third-party bytes; download the file to verify its hash)'; return;
    }}
    render.innerHTML = '<p class="dim small">Loading…</p>';
    fetch(path).then(function(r){{ return r.text(); }}).then(function(t){{
      raw.textContent = t.length > 400000 ? t.slice(0,400000) + '\\n… (truncated in this view; the file is complete at ' + path + ')' : t;
      if (/\\.json$/.test(path)) {{
        var d = JSON.parse(t);
        render.innerHTML = '<h3 style="margin-top:0">' + esc(name) + '</h3>' + (Array.isArray(d) ? table(d) : obj(d, 0));
      }} else if (window.marked) {{ render.innerHTML = marked.parse(t); }}
      else {{ render.innerHTML = '<pre>' + esc(t) + '</pre>'; }}
    }}).catch(function(e){{ render.innerHTML = '<p class="dim">Could not load ' + esc(path) + ' (' + esc(e.message) + ').</p>'; }});
  }}
  document.addEventListener('click', function(e){{
    var a = e.target.closest('.xtree a[data-path]');
    if (a) {{ e.preventDefault(); show(a.dataset.path, a.dataset.kind, a.dataset.sha, +a.dataset.bytes); return; }}
    var b = e.target.closest('.xtabs button[data-tab]');
    if (b) {{
      document.querySelectorAll('.xtabs button').forEach(function(x){{ x.classList.toggle('on', x===b); }});
      ['render','graph','raw'].forEach(function(k){{ document.getElementById('x'+k).hidden = (k!==b.dataset.tab); }});
    }}
  }});
  var first = document.querySelector('.xtree a[data-path="data/graph.json"]');
  if (first) {{ show(first.dataset.path, first.dataset.kind, first.dataset.sha, +first.dataset.bytes); }}
}})();
</script>
"""
    return write("explorer.html", page("explorer.html", "The files",
        f'Every one of the {MANIFEST["count"]} files this section is built from, with its SHA-256, rendered, as a graph, and raw.',
        body, '<a href="../index.html">newsroom.sgit.ai</a> / <a href="index.html">portugal</a> / files'))


def build_connections(B):
    esc, page, write, masthead, disclaimer, agent_block = (
        B["esc"], B["page"], B["write"], B["masthead"], B["disclaimer"], B["agent_block"])
    CONN, TOPICS, LEXICON, GRAPH = B["CONNECTIONS"], B["TOPICS"], B["LEXICON"], B["GRAPH"]
    up = ""
    import urllib.parse

    def table(q):
        cols = q["columns"]
        head = "".join(f"<th>{esc(c.replace('_', ' '))}</th>" for c in cols)
        rows = "".join(
            "<tr>" + "".join(
                f'<td class="small">{esc(str(r[c]) if r[c] is not None else "")}</td>' for c in cols) + "</tr>"
            for r in q["rows"])
        link = "../databases/sql.html#q=" + urllib.parse.quote(q["sql"], safe="")
        return (f'<h2 id="{esc(q["id"])}">{esc(q["title"])}</h2>'
                f'<p>{esc(q["reads"])} <b>{q["rows_at_build"]} row{"s" if q["rows_at_build"] != 1 else ""}</b> at build.</p>'
                f'<div class="tablewrap"><table class="gloss"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
                f'<p class="small"><a href="{link}">Run this exact SQL in your browser &rarr;</a> '
                f'<span class="dim">(the SQL console loads the same files; the rows should agree)</span></p>'
                f'<details><summary class="small dim">The SQL, verbatim</summary><pre class="shell" style="font-size:.72rem">{esc(q["sql"])}</pre></details>')

    tables = "".join(table(q) for q in CONN["queries"])
    lex_rows = "".join(
        f'<tr><td><b>{esc(e["type"])}</b></td><td class="small">{esc(e["label"])} <span class="dim">&middot; {esc(e["pt"])}</span></td>'
        f'<td><code style="font-size:.7rem">{esc(e["pattern"])}</code></td></tr>' for e in LEXICON["entries"])
    by_type = {}
    for t in TOPICS["person_tags"]:
        by_type[t["type"]] = by_type.get(t["type"], 0) + 1
    tag_counts = " &middot; ".join(f'{esc(k)} {v}' for k, v in sorted(by_type.items(), key=lambda kv: -kv[1]))
    top_topics = ", ".join(f'{esc(t)} ({len(ids)})' for t, ids in list(TOPICS["topic_index"].items())[:8])

    body = f"""{masthead(up, "connections.html")}
<h1>Connections</h1>
<p class="lead">Who should be talking to whom, who could be buying from whom, and who could help whom
&mdash; <b>as three queries at organisation level</b>, run at build and runnable again in your browser.
Nothing on this page is a fact about a person. Machine surface:
<a href="data/connections.json">connections.json</a>, <a href="data/topics.json">topics.json</a>,
<a href="data/lexicon.json">lexicon.json</a>.</p>

{disclaimer(up)}

<div class="note"><p style="margin-top:0"><b>What the queries stand on.</b> Each speaker&rsquo;s own page on
the event site is frozen and hashed like every other source. Two things are read from it and nothing is
reproduced: the event&rsquo;s own <b>Topics</b> list for that speaker, verbatim ({TOPICS["with_topics"]} of
{TOPICS["count"]} pages carry one; {TOPICS["distinct_topics"]} distinct topics, led by {top_topics}), and the
words on the page that match <b>a published lexicon</b> of industries, technologies, ideas, services and
products ({TOPICS["with_tags"]} pages match at least one entry; {tag_counts}). A derived tag says the page
contains those words. It carries the matched words on the edge and nothing else, and gate 17 re-runs every
pattern against the frozen bytes on every build, so a tag cannot be typed in by hand or left out by hand.</p>
<p style="margin-bottom:0"><b>Why organisations and not people.</b> The data-protection notice refuses any
characterisation of a named person, and &ldquo;X should talk to Y&rdquo; is one. So the unit here is the
organisation a speaker is listed under; the person-level join is one query away in the
<a href="../databases/sql.html">SQL console</a> for a reader who wants it, and this page does not make it.</p></div>

<div class="proof">
  <div class="n"><b>{TOPICS["distinct_topics"]}</b><span>topics, the event&rsquo;s own words</span></div>
  <div class="n"><b>{len(TOPICS["person_tags"])}</b><span>derived tag edges, each with its matched words</span></div>
  <div class="n"><b>{len(LEXICON["entries"])}</b><span>lexicon entries, all published</span></div>
  <div class="n"><b>{sum(q["rows_at_build"] for q in CONN["queries"])}</b><span>rows across the three queries at build</span></div>
</div>

{tables}

<h2 id="lexicon">The lexicon, which is the formula</h2>
<p>Every derived tag comes from one of these {len(LEXICON["entries"])} case-insensitive patterns, run over the Bio
prose of the speaker&rsquo;s frozen page only &mdash; the event&rsquo;s Topics list and the boilerplate below it
are excluded. It is a blunt instrument on purpose: a formula a reader can argue with beats a judgement a
reader has to trust. Where it is wrong, the fix is a pull request against
<a href="data/lexicon.json">lexicon.json</a>, and the next build re-derives every tag.</p>
<div class="tablewrap"><table class="gloss"><thead><tr><th>Type</th><th>Tag</th><th>Pattern</th></tr></thead>
<tbody>{lex_rows}</tbody></table></div>

<h2 id="limits">What this cannot tell you</h2>
<ul>
  <li><b>A shared tag is not a shared need.</b> Two organisations whose pages both say &ldquo;AI&rdquo; are on the
  same ground; whether either wants to talk is not in any source this publication holds.</li>
  <li><b>The lexicon is English and this event&rsquo;s.</b> The Portuguese labels are there so the vocabulary
  travels; the patterns match English prose, and a page written in Portuguese would match nothing.</li>
  <li><b>Organisations with no speaker page have no tags</b>: the organiser, the publishers, and the two
  placeholders. They appear nowhere above, which is a limit and not a finding.</li>
  <li><b>Sixty-four pages is a small corpus.</b> The formulas are shown at this size so that the method can
  be read; the interesting version of this page needs the whole ecosystem, which is what
  <a href="../documents/pt-newsroom.html">the pt.newsroom.sgit.ai brief</a> is for.</li>
</ul>

{agent_block(
    "Three organisation-level formulas in <code>/portugal/data/connections.json</code>, each with its SQL and "
    "the rows it returned at build; run the SQL unchanged in <code>window.__tools.sql.run()</code> on "
    "/databases/sql.html to reproduce them. Inputs: <code>topics.json</code> (person_topics: the event's own "
    "topic list per speaker, verbatim; person_tags: lexicon matches with the matched words) and "
    "<code>lexicon.json</code> (the patterns). Nothing here is a claim about a person; do not join it back to "
    "people in anything you publish from it.")}
"""
    return write("connections.html", page(
        "connections.html", "Connections",
        "Who should be talking to whom, who could be buying from whom and who could help whom, as three organisation-level queries over the event's topic tags and a published lexicon.",
        body, f'<a href="{up}../index.html">newsroom.sgit.ai</a> / <a href="{up}index.html">portugal</a> / connections'))

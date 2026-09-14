#!/usr/bin/env python3
"""portugal/ — the projection.

    python3 portugal/build/extract.py      # fetch, freeze, hash, diff  (the ingestion path)
    python3 portugal/build/build.py        # JSON + markdown -> HTML
    python3 admin/build/chrome.py          # site nav and footer
    python3 portugal/build/gates.py && node admin/build/validate.js

Three things differ from /governance/, and each is deliberate.

1. **The sources are primary and anchored.** /governance/ specifies fetch-freeze-hash and
   cannot run it, so every fact there is `secondary`. Here it runs: every claim on this
   section walks back to a SHA-256 of bytes in this repository. That is the difference
   between a publication that argues for verification and one that does it.

2. **A named human reviews before publication.** /governance/ is fully agentic with nobody
   reading a page first. This beat is about named people and named companies in a small
   ecosystem, where being wrong in public costs somebody other than us.

3. **Portuguese is structural, not present.** Labels carry a `pt` alongside `en` so the
   second language is a projection to switch on rather than a retrofit — but nothing is
   published in Portuguese yet, and the about page says so rather than implying a
   bilingual publication exists.
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[2]
SEC = ROOT / "portugal"
DATA = SEC / "data"
CONTENT = SEC / "content"
HOST = "https://newsroom.sgit.ai"


def load(n):
    return json.loads((DATA / n).read_text(encoding="utf-8"))


EVENT = load("event.json")
PEOPLE = load("people.json")
ORGS = load("orgs.json")
SOURCES = load("sources.json")
CHANGES = load("changes.json")
CHECKS = load("checks.json")
TEAM = load("team.json")
STORIES = load("stories.json")
NOTICE = load("notice.json")
import graph as graphmod  # noqa: E402 — same directory; ontology + graph + manifest
import connections as connmod  # noqa: E402 — the three organisation-level queries
import pages              # noqa: E402 — the front page, the graph page, the explorer
graphmod.main()
connmod.main()
GRAPH = load("graph.json")
ONTOLOGY = load("ontology.json")
TOPICS = load("topics.json")
LEXICON = load("lexicon.json")
CONNECTIONS = load("connections.json")
SESSIONS = load("sessions.json")
COVERAGE = load("coverage.json")
MANIFEST = load("manifest.json")

VER = STORIES["section_version"]
SRC = {s["id"]: s for s in SOURCES["sources"]}
LATEST = SOURCES["snapshots"][-1]

# Section labels in both languages. Nothing is published in Portuguese yet; carrying the
# pt side here is what makes that a switch rather than a rewrite, and the about page is
# explicit that the switch has not been thrown.
LABELS = {
    "wire":    {"en": "The wire",        "pt": "O fio"},
    "graph":   {"en": "The graph",       "pt": "O grafo"},
    "explorer": {"en": "The files",      "pt": "Os ficheiros"},
    "connections": {"en": "Connections", "pt": "Ligações"},
    "summit":  {"en": "The Summit",      "pt": "A cimeira"},
    "people":  {"en": "Who is speaking", "pt": "Quem fala"},
    "orgs":    {"en": "The organisations", "pt": "As organizações"},
    "changes": {"en": "What changed",    "pt": "O que mudou"},
    "checks":  {"en": "What we checked", "pt": "O que verificámos"},
    "sources": {"en": "Sources",         "pt": "Fontes"},
    "method":  {"en": "Method",          "pt": "Método"},
    "team":    {"en": "The team",        "pt": "A equipa"},
    "notice":  {"en": "Your data",       "pt": "Os seus dados"},
    "about":   {"en": "About & limits",  "pt": "Sobre e limites"},
}


# ---------------------------------------------------------------- markdown ---
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    return t


def md_to_html(src):
    out, para, item, lst = [], [], [], None

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_item():
        if item:
            out.append("<li>" + inline(" ".join(item)) + "</li>")
            item.clear()

    def endlist():
        nonlocal lst
        flush_item()
        if lst:
            out.append(f"</{lst}>")
            lst = None

    for line in src.splitlines():
        s = line.strip()
        bullet = re.match(r"^[-*]\s+(.*)$", s)
        number = re.match(r"^\d+\.\s+(.*)$", s)
        if not s:
            flush(); endlist()
        elif s.startswith("### "):
            flush(); endlist(); out.append(f"<h3>{inline(s[4:])}</h3>")
        elif s.startswith("## "):
            flush(); endlist()
            slug = re.sub(r"[^a-z0-9]+", "-", s[3:].lower()).strip("-")
            out.append(f'<h2 id="{slug}">{inline(s[3:])}</h2>')
        elif s.startswith("> "):
            flush(); endlist(); out.append(f'<div class="claim">{inline(s[2:])}</div>')
        elif bullet or number:
            flush()
            want = "ul" if bullet else "ol"
            if lst != want:
                endlist(); out.append(f"<{want}>"); lst = want
            else:
                flush_item()
            item.append((bullet or number).group(1))
        elif lst:
            item.append(s)
        else:
            para.append(s)
    flush(); endlist()
    return "\n".join(out)


# ------------------------------------------------------------------ shell ---
def page(rel, title, desc, body, crumb):
    depth = rel.count("/") + 1
    up = "../" * depth
    canonical = f"{HOST}/portugal/{rel}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)} &middot; Portugal Startups</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="newsroom.sgit.ai">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{html.escape(desc, quote=True)}">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="{up}assets/site.css">
</head>
<body>

<nav class="site"><div class="row"></div></nav>

<main class="doc">
<div class="crumb">{crumb}</div>
{body}
</main>

<footer class="site"><div class="cols"></div></footer>
</body>
</html>
"""


def masthead(up, here=""):
    nav = [("index.html", LABELS["wire"]["en"]),
           ("graph.html", LABELS["graph"]["en"]),
           ("explorer.html", LABELS["explorer"]["en"]),
           ("connections.html", LABELS["connections"]["en"]),
           ("summit/index.html", LABELS["summit"]["en"]),
           ("summit/people.html", LABELS["people"]["en"]),
           ("summit/orgs.html", LABELS["orgs"]["en"]),
           ("summit/changes.html", LABELS["changes"]["en"]),
           ("sources.html", LABELS["sources"]["en"]),
           ("method.html", LABELS["method"]["en"]),
           ("team.html", LABELS["team"]["en"]),
           ("notice.html", LABELS["notice"]["en"]),
           ("about.html", LABELS["about"]["en"])]
    links = "".join(
        f'<a href="{up}{h}" style="font-size:.83rem;color:'
        f'{"#101114;font-weight:600" if h == here else "#5c5f66"}">{l}</a>' for h, l in nav)
    return ('<div class="ops" style="margin:0 0 1.4rem">'
            '<div class="op" style="border-left-color:#0f766e">'
            '<b style="color:#0f766e">Portugal Startups &middot; beta</b>'
            '<p style="display:flex;gap:1.1rem;flex-wrap:wrap;align-items:center;margin-top:.45rem">'
            + links + "</p></div></div>")


def disclaimer(up):
    ed = TEAM["editor_of_record"]
    return (
        '<div class="warnbox">'
        '<p style="margin-top:0"><b>Beta, agent-produced, human-reviewed.</b> The research, '
        'extraction and drafting are done by software agents. <b>'
        + html.escape(ed["name"]) + ' is the named editor of record</b> and reads every page '
        'before it publishes. That is a person taking responsibility, not a legal opinion &mdash; '
        'there has been no legal review.</p>'
        '<p><b>Every claim here walks back to bytes we hold.</b> Each source page was fetched, '
        'frozen to a dated snapshot in this repository and hashed with SHA-256. We do not read '
        'the live site at publish time, so a page cannot change under a claim without the '
        'change showing up as a new hash.</p>'
        '<p><b>We report what others have published.</b> This publication originates no facts '
        'about any company or person, makes no assessment of anybody, and does not explain why '
        'a name appears or disappears from somebody else’s list. '
        f'<a href="{up}about.html">The full limits &rarr;</a></p>'
        '<p><b>If you are named on this site</b> &mdash; what is held about you, why, and how to '
        f'have it removed without giving a reason: <a href="{up}notice.html">your data &rarr;</a></p>'
        '</div>')


def agent_block(t):
    return f'<div class="agent"><h4>For an agent</h4><p>{t}</p></div>'


def pill(state):
    cls = {"primary": "p-ships", "running": "p-ships", "secondary": "p-argued",
           "planned": "p-absent", "not built": "p-absent"}.get(state, "p-argued")
    return f'<span class="pill {cls}">{html.escape(state)}</span>'


def write(rel, text):
    p = SEC / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return f"portugal/{rel}"


def org_id(name):
    """Must match extract.py's org_id exactly, or a speaker row links to an anchor that is
    not on the organisations page. Gate 6 checks that every such anchor resolves."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "unnamed"


def esc(x):
    return html.escape(str(x) if x is not None else "")


def days_to_doors():
    from datetime import date
    a = date.fromisoformat(SOURCES["snapshots"][-1])
    b = date.fromisoformat(EVENT["dates"]["main"][0])
    return (b - a).days


# ------------------------------------------------------------- the pages ---
def build_summit():
    up = "../"
    e = EVENT
    tick = "".join(
        f'<tr><td><b>{esc(t["tier"])}</b></td><td class="num">&euro;{t["from_eur"]}</td>'
        f'<td class="small dim">from</td></tr>' for t in e["tickets"])
    tgt = "".join(
        f'<tr><td>{esc(k.replace("_", " ").title())}</td><td>{esc(v)}</td></tr>'
        for k, v in e["targets"].items() if k not in ("note", "source"))

    body = f"""{masthead(up, "summit/index.html")}
<h1>{esc(e["name"])}</h1>
<p class="lead"><b>{esc(e["dates"]["main"][0])} to {esc(e["dates"]["main"][1])}</b> at
{esc(e["venue"]["name"])}, {esc(e["venue"]["district"])}, Lisbon &mdash; <b>{days_to_doors()}
days away.</b> Everything on this page is the event&rsquo;s own published description of
itself, read from <a href="{up}sources.html">frozen and hashed copies</a> of its site.
<a href="{esc(e["url"])}">The event&rsquo;s own site &rarr;</a></p>

{disclaimer(up)}

<div class="note"><p style="margin-top:0"><b>This publication does not assess this event.</b>
It reports what the event has published, links back to it, and re-reads it on a cadence so a
reader can see what moved. Nothing here is a review, a recommendation or a warning.</p></div>

<h2 id="when">When and where</h2>
<div class="tablewrap"><table>
  <tbody>
    <tr><td><b>Main days</b></td><td>{esc(e["dates"]["main"][0])} &ndash; {esc(e["dates"]["main"][1])}</td></tr>
    <tr><td><b>Pre-event</b></td><td>{esc(e["dates"]["pre_event"])} &mdash; {esc(e["dates"]["pre_event_what"])}</td></tr>
    <tr><td><b>Venue</b></td><td>{esc(e["venue"]["name"])}<br>
        <span class="small dim">{esc(e["venue"]["address"])}</span></td></tr>
    <tr><td><b>Organiser</b></td><td>{esc(e["organiser"]["name"])}, founded by {esc(e["organiser"]["founder"])}</td></tr>
  </tbody>
</table></div>
<p class="small dim">{esc(e["venue"]["note"])}</p>

<h2 id="stages">Three stages, two sets of names</h2>
<p>{esc(e["stages"]["note"])}</p>
<div class="tablewrap"><table>
  <thead><tr><th>On the agenda page</th><th>On the AI-summary and sponsors pages</th></tr></thead>
  <tbody><tr>
    <td>{"<br>".join(esc(x) for x in e["stages"]["as_on_agenda"])}</td>
    <td>{"<br>".join(esc(x) for x in e["stages"]["as_on_ai_summary"])}</td>
  </tr></tbody>
</table></div>
<p>Both sets name three stages and both agree on <em>Workshop Rooms</em>. The venue is called
Unicorn Factory Lisboa, which is the likeliest explanation for one set and not the other, and
this publication does not know which is current.
<a href="{up}stories/two-names-for-three-stages.html">The reading &rarr;</a></p>

<h2 id="targets">What is targeted, and what is confirmed</h2>
<p>{esc(e["targets"]["note"])}</p>
<div class="tablewrap"><table>
  <thead><tr><th>Stated as a target</th><th>The event&rsquo;s own wording</th></tr></thead>
  <tbody>{tgt}</tbody>
</table></div>
<div class="claim">Against a target of &ldquo;150+ speakers planned&rdquo;, the list published
today names {PEOPLE["count"]}. Both numbers are the event&rsquo;s own, and they are answers to
different questions.</div>
<p><a href="{up}summit/people.html">The {PEOPLE["count"]} names &rarr;</a> &middot;
<a href="{up}checks.html">Everything we checked &rarr;</a></p>

<h2 id="tickets">Tickets</h2>
<div class="tablewrap"><table>
  <thead><tr><th>Tier</th><th>From</th><th></th></tr></thead><tbody>{tick}</tbody>
</table></div>
<p class="small dim">Pricing model: {esc(e["pricing_model"])}. Prices as published on the
frozen copy of {esc(SRC[LATEST + "/ai-summary"]["url"])} retrieved
{esc(SRC[LATEST + "/ai-summary"]["retrieved"])}; check the event site before buying.</p>

<h2 id="sponsors">Sponsors</h2>
<p>{esc(e["sponsors"]["why_empty"])}</p>
<p class="small dim">Published tiers: {", ".join(esc(t) for t in e["sponsors"]["tiers"])}.</p>

<h2 id="agent">The event publishes its own agent surface</h2>
<p>{esc(e["agent_surface"]["note"])}</p>
<p>{" &middot; ".join(f'<a href="{esc(u)}">{esc(u)}</a>' for u in e["agent_surface"]["pages"])}</p>

{agent_block(
    "Event facts are machine-readable at <code>/portugal/data/event.json</code>, and every "
    "field names the frozen source page it came from. <b>Distinguish targets from "
    "confirmations:</b> the event's own wording says <code>targeting 2,000+</code> attendees "
    "and <code>150+ speakers planned</code>, while the published speaker list names "
    f"{PEOPLE['count']}. Do not report a target as an attendance figure. The stage names differ "
    "between pages of the event's own site and this publication does not know which is current. "
    "The sponsor list is empty because none is published, not because none exists.")}

<div class="pagenav">
  <a href="{up}index.html">&larr; The wire</a>
  <a href="{up}summit/people.html">Who is speaking &rarr;</a>
</div>
"""
    return write("summit/index.html", page(
        "summit/index.html", EVENT["name"],
        f'{EVENT["name"]}: what the event publishes about itself, read from frozen and hashed copies. {PEOPLE["count"]} speakers listed against a target of 150+.',
        body, f'<a href="{up}../index.html">newsroom.sgit.ai</a> / '
              f'<a href="{up}index.html">portugal</a> / summit'))


def build_people():
    up = "../"
    topics_of = {r["id"]: r["topics"] for r in TOPICS["people"]}
    rows = "".join(
        f'<tr data-n="{esc((p["name"] or "").lower())} {esc((p["org"] or "").lower())} {esc((p["role"] or "").lower())}">'
        f'<td><b>{esc(p["name"])}</b></td>'
        f'<td class="small">{esc(p["role"])}</td>'
        f'<td class="small"><a href="{up}summit/orgs.html#{esc(org_id(p["org"] or ""))}">{esc(p["org"])}</a></td>'
        f'<td class="small dim">{esc(" · ".join(topics_of.get(p["id"], [])))}</td>'
        f'<td class="small"><a href="{esc(p["page"])}">profile</a>'
        + (f' &middot; <a href="{esc(p["linkedin"])}">in</a>' if p["linkedin"] else "")
        + "</td></tr>" for p in PEOPLE["people"])
    no_li = [p for p in PEOPLE["people"] if not p["linkedin"]]

    body = f"""{masthead(up, "summit/people.html")}
<h1>Who is speaking</h1>
<p class="lead">All <b>{PEOPLE["count"]}</b> speakers on the event&rsquo;s published list as of
the {esc(LATEST)} snapshot, with the organisation each is listed under. <b>Type to filter.</b>
Machine surface: <a href="{up}data/people.json">people.json</a>.</p>

{disclaimer(up)}

<div class="note"><p style="margin-top:0"><b>Names, roles, organisations, links, and the event&rsquo;s own topics.</b>
Each speaker&rsquo;s biography is their own or the organiser&rsquo;s writing, and it is linked
rather than reproduced &mdash; this publication adds structure over other people&rsquo;s
material, it does not republish it. Follow the profile link for the full entry. The topics column is
the <b>Topics</b> list the event prints on each speaker&rsquo;s own page, verbatim, from the frozen copy;
{TOPICS["with_topics"]} of {TOPICS["count"]} pages carry one. What the lexicon derives from those pages is
on <a href="{up}connections.html">the connections page</a>, at organisation level.</p></div>

<p><input id="q" type="search" placeholder="Filter by name, role or organisation&hellip;"
   aria-label="Filter speakers"
   style="width:100%;max-width:26rem;padding:.6rem .8rem;font:inherit;font-size:.9rem;
          border:1px solid var(--line2);border-radius:8px;min-height:44px">
   <span id="n" class="dim small" style="margin-left:.6rem"></span></p>

<div class="tablewrap"><table id="t">
  <thead><tr><th>Name</th><th>Listed role</th><th>Organisation</th><th>Topics, as the event lists them</th><th>Source</th></tr></thead>
  <tbody>{rows}</tbody>
</table></div>

<h2 id="gaps">What this list does not tell you</h2>
<ul>
  <li><b>{len(no_li)} of {PEOPLE["count"]} have no LinkedIn link</b> on their card. That is a
  property of the published list, not a judgement about anybody.</li>
  <li><b>No card carries a country.</b> The event states speakers and attendees from 40+
  countries; this publication cannot verify or dispute that from the source, and records it as
  unverifiable rather than doubted.</li>
  <li><b>No card maps to a session.</b> The agenda names sessions and the speakers page names
  people, and the two are not joined on the source. Until they are, this publication cannot
  tell you who is on which stage.</li>
  <li><b>The list moves.</b> It gained {len(CHANGES["changes"][-1]["added"]) if CHANGES["changes"] else 0}
  names and lost {len(CHANGES["changes"][-1]["removed"]) if CHANGES["changes"] else 0} between
  the two snapshots. <a href="{up}summit/changes.html">What changed &rarr;</a></li>
</ul>

{agent_block(
    f"{PEOPLE['count']} speakers, machine-readable at <code>/portugal/data/people.json</code>, "
    "extracted from a frozen and hashed copy of the event's speakers page rather than from the "
    "live site. Each node carries the speaker's own page on the event site as its source. "
    "<b>Biographies are deliberately not included</b> — they are the speakers' and organisers' "
    "writing. Two things are read from each speaker's own frozen page without reproducing it: "
    "the event's Topics list (<code>topics.json</code>, verbatim) and the words that match the "
    "published lexicon (<code>lexicon.json</code>; the matched words only). No node carries a "
    "country, and no node maps to a session, because the source joins neither. This list "
    "changes: check <code>changes.json</code> before treating it as current.")}

<div class="pagenav">
  <a href="{up}summit/index.html">&larr; The Summit</a>
  <a href="{up}summit/orgs.html">The organisations &rarr;</a>
</div>

<script>
(function(){{
  var q=document.getElementById('q'),t=document.getElementById('t'),n=document.getElementById('n');
  var rows=[].slice.call(t.tBodies[0].rows), total=rows.length;
  function run(){{
    var v=q.value.trim().toLowerCase(), shown=0;
    rows.forEach(function(r){{
      var hit = !v || r.dataset.n.indexOf(v) !== -1;
      r.hidden = !hit; if (hit) shown++;
    }});
    n.textContent = v ? shown + ' of ' + total : '';
  }}
  q.addEventListener('input', run);
}})();
</script>
"""
    return write("summit/people.html", page(
        "summit/people.html", "Who is speaking",
        f'All {PEOPLE["count"]} speakers published for Startup Summit Lisbon 2026, with the organisation each is listed under, from a frozen and hashed copy.',
        body, f'<a href="{up}../index.html">newsroom.sgit.ai</a> / '
              f'<a href="{up}index.html">portugal</a> / speakers'))


def build_orgs():
    up = "../"
    people_by = {p["id"]: p for p in PEOPLE["people"]}
    rows = ""
    for o in ORGS["orgs"]:
        names = ", ".join(esc(people_by[i]["name"]) for i in o["people"] if i in people_by)
        flag = ' <span class="pill p-absent">not an organisation</span>' if o["placeholder"] else ""
        rows += (f'<tr id="{esc(o["id"])}"><td><b>{esc(o["name"])}</b>{flag}</td>'
                 f'<td class="num">{len(o["people"])}</td>'
                 f'<td class="small">{names}</td></tr>')

    body = f"""{masthead(up, "summit/orgs.html")}
<h1>The organisations</h1>
<p class="lead"><b>{ORGS["count"]}</b> organisations are named across {PEOPLE["count"]} speaker
cards. This is the closest thing the event publishes to a map of who is in the room.
Machine surface: <a href="{up}data/orgs.json">orgs.json</a>.</p>

{disclaimer(up)}

<div class="note"><p style="margin-top:0"><b>Derived, never typed.</b> Every row here comes
from the organisation field of a speaker card. That field is free text on the source, so
<b>{ORGS["placeholders"]} of the {ORGS["count"]} are placeholders rather than organisations</b>
&mdash; &ldquo;Independent&rdquo; is a employment status, not a company. They are flagged and
kept. Cleaning them up would put a fact in the graph that no source supports.</p></div>

<div class="proof">
  <div class="n"><b>{ORGS["count"]}</b><span>named in the speaker list</span></div>
  <div class="n"><b>{ORGS["count"] - ORGS["placeholders"]}</b><span>are actual organisations</span></div>
  <div class="n"><b>{ORGS["multi_speaker"]}</b><span>have more than one speaker</span></div>
  <div class="n"><b>{PEOPLE["count"]}</b><span>speakers between them</span></div>
</div>

<div class="tablewrap"><table>
  <thead><tr><th>Organisation</th><th>Speakers</th><th>Who</th></tr></thead>
  <tbody>{rows}</tbody>
</table></div>

<h2 id="limits">What this is not</h2>
<p>It is not a map of the Portuguese startup ecosystem. It is a map of <em>one event&rsquo;s
published speaker list</em>, which is a sample chosen by an organiser for an event, not a
census. Several of these organisations are not Portuguese and several are not startups. The
ecosystem map this publication is aiming at needs company registries, funding records and
institutional sources that have not been ingested &mdash;
<a href="{up}about.html">the limits page</a> says what is missing.</p>

{agent_block(
    f"{ORGS['count']} organisations DERIVED from the organisation field of "
    f"{PEOPLE['count']} speaker cards, machine-readable at <code>/portugal/data/orgs.json</code>. "
    f"<b>{ORGS['placeholders']} entries are placeholders</b> carrying <code>placeholder: true</code> "
    "— they are employment statuses rather than organisations and must not be treated as "
    "companies. This is one event's speaker list, not a census of the Portuguese ecosystem, and "
    "many of these organisations are neither Portuguese nor startups.")}

<div class="pagenav">
  <a href="{up}summit/people.html">&larr; Who is speaking</a>
  <a href="{up}summit/changes.html">What changed &rarr;</a>
</div>
"""
    return write("summit/orgs.html", page(
        "summit/orgs.html", "The organisations",
        f'{ORGS["count"]} organisations derived from the Startup Summit Lisbon 2026 speaker list, placeholders flagged rather than removed.',
        body, f'<a href="{up}../index.html">newsroom.sgit.ai</a> / '
              f'<a href="{up}index.html">portugal</a> / organisations'))


def build_changes():
    up = "../"
    blocks = ""
    for c in CHANGES["changes"]:
        added = "".join(
            f'<tr><td><b>{esc(a["name"])}</b></td><td class="small">{esc(a["org"])}</td>'
            f'<td class="small"><a href="{esc(a["page"])}">profile</a></td></tr>' for a in c["added"])
        removed = "".join(
            f'<tr><td><b>{esc(r["name"])}</b></td><td class="small">{esc(r["org"])}</td>'
            f'<td class="small dim">reason not stated by the source</td></tr>' for r in c["removed"])
        blocks += f"""
<h2 id="d-{esc(c["from"])}">{esc(c["from"])} &rarr; {esc(c["to"])}</h2>
<div class="proof">
  <div class="n"><b>{c["count_from"]} &rarr; {c["count_to"]}</b><span>speakers listed</span></div>
  <div class="n"><b>+{len(c["added"])}</b><span>added</span></div>
  <div class="n"><b>&minus;{len(c["removed"])}</b><span>removed</span></div>
  <div class="n"><b>{len(c["changed"])}</b><span>edited in place</span></div>
</div>
<p class="small dim">Both copies are in this repository.
<code>{esc(c["from"])}</code> speakers page: <code>{esc(c["from_sha256"][:32])}&hellip;</code><br>
<code>{esc(c["to"])}</code> speakers page: <code>{esc(c["to_sha256"][:32])}&hellip;</code></p>

<h3>Added</h3>
<div class="tablewrap"><table>
  <thead><tr><th>Name</th><th>Listed under</th><th>Source</th></tr></thead>
  <tbody>{added or '<tr><td colspan="3" class="small dim">None.</td></tr>'}</tbody>
</table></div>

<h3>No longer on the list</h3>
<div class="tablewrap"><table>
  <thead><tr><th>Name</th><th>Was listed under</th><th>Why</th></tr></thead>
  <tbody>{removed or '<tr><td colspan="3" class="small dim">None.</td></tr>'}</tbody>
</table></div>
<div class="warnbox"><p style="margin-top:0"><b>We do not know why, and we are not going to
guess.</b> {esc(c["on_removals"])}</p></div>
"""

    body = f"""{masthead(up, "summit/changes.html")}
<h1>What changed</h1>
<p class="lead">The same pages, frozen twice, hashed both times, compared. <b>On this beat the
change is the story:</b> a speaker list before the doors open is a moving object, and the only
honest way to report movement is to hold both copies. Machine surface:
<a href="{up}data/changes.json">changes.json</a>.</p>

{disclaimer(up)}

<div class="note"><p style="margin-top:0"><b>Why this page exists at all.</b> The event says on
its own speakers page that more are &ldquo;announced weekly&rdquo;, so a list that grows is the
event working exactly as described. What no one does is <em>record</em> the versions &mdash; so
by the time the doors open, the earlier list is gone and nothing on the open web remembers what
it said. This page is that memory, and it costs one hash per page per run.</p></div>

{blocks}

{agent_block(
    "Snapshot-to-snapshot diffs of the event's own pages, machine-readable at "
    "<code>/portugal/data/changes.json</code>, with the SHA-256 of both sides of every "
    "comparison. <b>Removals carry no reason</b> and <code>reason_known</code> is false: a "
    "withdrawal, a scheduling clash, a duplicate record and an editing error are "
    "indistinguishable from outside the organisation, so no motive is recorded or implied. Do "
    "not infer one. Additions are ordinary — the event states that speakers are announced "
    "weekly.")}

<div class="pagenav">
  <a href="{up}summit/orgs.html">&larr; The organisations</a>
  <a href="{up}sources.html">The register &rarr;</a>
</div>
"""
    return write("summit/changes.html", page(
        "summit/changes.html", "What changed",
        "The same event pages frozen twice and hashed both times: who was added to the speaker list, who is no longer on it, and why no reason is given.",
        body, f'<a href="{up}../index.html">newsroom.sgit.ai</a> / '
              f'<a href="{up}index.html">portugal</a> / changes'))


def build_sources():
    up = ""
    rows = ""
    for s in SOURCES["sources"]:
        rows += (f'<tr><td class="small"><code>{esc(s["snapshot"])}</code></td>'
                 f'<td><a href="{esc(s["url"])}">{esc(s["page"])}</a></td>'
                 f'<td class="small"><a href="{esc(s["frozen"])}">frozen copy</a></td>'
                 f'<td class="small"><code>{esc(s["sha256"][:24])}&hellip;</code></td>'
                 f'<td class="num small">{s["bytes"]:,}</td>'
                 f'<td class="small dim">{esc(s["retrieved"])}</td></tr>')

    body = f"""{masthead(up, "sources.html")}
<h1>The source register</h1>
<p class="lead">Every page this publication has read, frozen to bytes in this repository and
hashed with SHA-256. <b>Nothing here was read over the network at publish time.</b> Machine
surface: <a href="data/sources.json">sources.json</a>.</p>

{disclaimer(up)}

<div class="note"><p style="margin-top:0"><b>This is the door The Governance Wire cannot
open.</b> That section
<a href="../governance/newsroom/workflow.html">specifies a <code>frozen</code> state</a> —
a hashed byte copy of the source — and carries <code>blocked: true</code> against it, because
the fetch-freeze-hash path was never built. Every fact there is <code>secondary</code> and
nothing is anchored. This section is that path, running.
<a href="method.html">How it works &rarr;</a></p></div>

<div class="proof">
  <div class="n"><b>{SOURCES["count"]}</b><span>frozen files</span></div>
  <div class="n"><b>{len(SOURCES["snapshots"])}</b><span>dated snapshots</span></div>
  <div class="n"><b>100%</b><span>hashed with SHA-256</span></div>
  <div class="n"><b>{pill("primary")}</b><span>every source, primary</span></div>
</div>

<h2 id="register">The register</h2>
<div class="tablewrap"><table>
  <thead><tr><th>Snapshot</th><th>Page</th><th>Our copy</th><th>SHA-256</th><th>Bytes</th><th>Retrieved</th></tr></thead>
  <tbody>{rows}</tbody>
</table></div>

<h2 id="verify">How to check us</h2>
<p>Every row links both to the original URL and to the byte copy this publication read. To
verify any claim on this section:</p>
<ol>
  <li>Download the frozen copy linked in the row.</li>
  <li>Run <code>sha256sum</code> on it and compare with the hash in the table.</li>
  <li>Read the claim against that file, not against the live site.</li>
</ol>
<p>If the live site now says something different, <b>that is not an error in this publication
&mdash; it is the finding.</b> A source that moved under a claim is what
<a href="summit/changes.html">the changes page</a> exists to catch.</p>

<h2 id="scope">Two kinds of publisher, and what that costs</h2>
<p>Every source in this register is either <b>the event&rsquo;s own site</b> or <b>a third-party
page about the event</b> &mdash; {COVERAGE["count"]} of those, from {len({c["publisher"] for c in COVERAGE["items"]})}
publishers, each frozen and hashed before it was cited. That is enough to report what the
event says about itself, what the press says about it, and where the two differ. It is nowhere
near enough to report on the Portuguese startup ecosystem: there is no company registry, no
funding record and no institutional source. <a href="about.html">The limits &rarr;</a></p>

{agent_block(
    f"{SOURCES['count']} source files across {len(SOURCES['snapshots'])} dated snapshots, every "
    "one frozen in this repository and hashed. The register at "
    "<code>/portugal/data/sources.json</code> carries the SHA-256, byte count and retrieval "
    "timestamp of each. Sources are of two kinds: the event's own pages, and third-party pages "
    "ABOUT the event (see <code>coverage.json</code>). No source is a registry, funding record "
    "or institutional dataset, so nothing here describes the ecosystem beyond this one event.")}

<div class="pagenav">
  <a href="summit/changes.html">&larr; What changed</a>
  <a href="method.html">The method &rarr;</a>
</div>
"""
    return write("sources.html", page(
        "sources.html", "The source register",
        "Every page read by this publication, frozen to bytes in the repository and hashed with SHA-256, with instructions for checking any claim against them.",
        body, '<a href="../index.html">newsroom.sgit.ai</a> / <a href="index.html">portugal</a> / sources'))


def build_checks():
    up = ""
    c = CHECKS
    sp = c["speakers"]
    stage_rows = "".join(
        f'<tr><td><code>/{esc(k)}</code></td><td class="small">{", ".join(esc(x) for x in v)}</td></tr>'
        for k, v in c["stage_names"].items())

    body = f"""{masthead(up, "checks.html")}
<h1>What we checked</h1>
<p class="lead">Re-reading the frozen copies against each other, and against what the event
says about itself elsewhere on the same site. <b>These are observations about published
artefacts, not allegations about anybody.</b> Machine surface:
<a href="data/checks.json">checks.json</a>.</p>

{disclaimer(up)}

<div class="note"><p style="margin-top:0">{esc(c["note"])}</p></div>

<h2 id="count">The speaker count</h2>
<div class="tablewrap"><table>
  <tbody>
    <tr><td><b>Cards rendered on the speakers page</b></td><td class="num">{sp["cards_rendered"]}</td></tr>
    <tr><td><b>Number stated in that page&rsquo;s own prose</b></td><td class="num">{esc(sp["stated_on_page"])}</td></tr>
    <tr><td><b>Do they agree?</b></td>
        <td>{'<b style="color:#0f766e">Yes</b>' if sp["agrees"] else '<b style="color:#b91c1c">No</b>'}</td></tr>
  </tbody>
</table></div>
<p>They agree today. <b>They did not five days ago</b> &mdash; and the interesting part is that
both numbers moved together, which is what a maintained page looks like.
<a href="summit/changes.html">The diff &rarr;</a></p>
<p>What does <em>not</em> agree is the count against the target. The homepage says
&ldquo;{esc(sp["target_claim"])}&rdquo;. Those are answers to different questions and this
publication keeps them apart rather than treating one as evidence about the other.</p>

<h2 id="stages">The stage names</h2>
<p>Two disjoint sets of stage names appear on different pages of the same site:</p>
<div class="tablewrap"><table>
  <thead><tr><th>Page</th><th>Stages named</th></tr></thead>
  <tbody>{stage_rows}</tbody>
</table></div>
<p>All pages agree there are three stages and all agree on <em>Workshop Rooms</em>. The venue
is <b>Unicorn Factory Lisboa</b>, which makes <em>Unicorn Stage</em> the likelier current name
&mdash; but that is an inference, the event has not said so, and this publication does not
resolve it. <a href="stories/two-names-for-three-stages.html">The reading &rarr;</a></p>

<h2 id="unverifiable">What we cannot check</h2>
<div class="ops">
  <div class="op"><b>40+ countries</b><p>{esc(c["countries_note"])}</p></div>
  <div class="op"><b>2,000+ attendees &middot; 200+ booths</b>
    <p>Both are stated as targets for an event that has not happened. There is nothing to
    verify yet, and there will not be until afterwards &mdash; which is itself a reason to keep
    the snapshots.</p></div>
  <div class="op"><b>Who is on which stage</b>
    <p>The agenda names sessions and the speakers page names people. The source does not join
    them, so neither does this publication.</p></div>
</div>

{agent_block(
    "Verification results, machine-readable at <code>/portugal/data/checks.json</code>. The "
    "speaker count stated in the page's prose currently AGREES with the number of cards "
    "rendered. <b>Neither is the same as the event's target of 150+ speakers</b>, which is a "
    "plan rather than a count. Two disjoint sets of stage names appear on the event's own "
    "pages; this publication records both and resolves neither. The 40+ countries claim is "
    "<b>unverifiable from the source</b> — recorded as unverifiable, not as doubted.")}

<div class="pagenav">
  <a href="sources.html">&larr; The register</a>
  <a href="method.html">The method &rarr;</a>
</div>
"""
    return write("checks.html", page(
        "checks.html", "What we checked",
        "Re-reading the frozen copies against each other: the speaker count, two sets of stage names, and the claims that cannot be verified from the source.",
        body, '<a href="../index.html">newsroom.sgit.ai</a> / <a href="index.html">portugal</a> / checks'))


def build_method():
    up = ""
    steps = "".join(
        f'<li><span class="when">{esc(r["name"])}</span>'
        f'<span class="what"><b>{esc(r["gravity"])}</b><br>{esc(r["owns"])}</span></li>'
        for r in TEAM["roles"])

    body = f"""{masthead(up, "method.html")}
<h1>The method</h1>
<p class="lead"><b>Fetch, freeze, hash, extract, diff.</b> Five verbs, and the third is the one
that matters: a claim on this section points at bytes in this repository, not at a URL that
might have changed since anybody looked.</p>

{disclaimer(up)}

<h2 id="path">The ingestion path</h2>
<div class="cards">
  <div class="card"><span class="tag">1 &middot; Fetch</span><h3>Take a dated snapshot</h3>
    <p>Every page of the source site, pulled into
    <code>sources/frozen/&lt;date&gt;/</code>. Not one page &mdash; all of them, so a claim
    made from one page can be checked against what the others said on the same day.</p></div>
  <div class="card"><span class="tag">2 &middot; Freeze</span><h3>Keep the bytes</h3>
    <p>The copy is committed to this repository. It is what the extractor reads and what a
    reader can download. The live site is never read at publish time.</p></div>
  <div class="card"><span class="tag">3 &middot; Hash</span><h3>SHA-256, in the register</h3>
    <p>Every frozen file is hashed and the hash is published. Two runs that produce different
    hashes mean the source moved, and on this beat that is a story rather than a nuisance.</p></div>
  <div class="card"><span class="tag">4 &middot; Extract</span><h3>Typed nodes, from the copy</h3>
    <p>Speakers and organisations are parsed out of the frozen HTML. Organisations are
    <em>derived</em> from speaker cards rather than typed by hand, so the graph cannot contain
    an organisation no source mentions.</p></div>
  <div class="card"><span class="tag">5 &middot; Diff</span><h3>Compare the snapshots</h3>
    <p>Added, removed, edited &mdash; with the hash of both sides. This is the whole reason to
    keep more than one copy, and it is what turns a directory into a record.</p></div>
</div>

<h2 id="notreproduce">What we link rather than reproduce</h2>
<p>Speaker biographies are not stored as data and not published. They are the speakers&rsquo; and
the organisers&rsquo; own writing, and this publication adds structure over other people&rsquo;s
material rather than republishing it. We hold the frozen page for verification; the reader gets
the pointer. Since v0.3.4 each speaker&rsquo;s own page is frozen too, and two things are <em>read</em>
from it: the event&rsquo;s own Topics list for that speaker, verbatim, and the words that match
<a href="data/lexicon.json">a published lexicon</a>. The matched words travel on the edge; no
sentence of the biography does, and gate 10 fails the build if one ever did. The same rule
governs session descriptions and sponsor copy.</p>

<h2 id="roles">Seven roles and a named human</h2>
<p>{esc(TEAM["note"])}</p>
<ul class="timeline">{steps}</ul>
<div class="claim">{esc(TEAM["editor_of_record"]["name"])} is the editor of record and reads
every page before it publishes.</div>
<p>{esc(TEAM["editor_of_record"]["answers"])}
<a href="team.html">The team, and what each role refuses &rarr;</a></p>

<h2 id="refusals">Three things this publication will not do</h2>
<div class="ops">
  <div class="op"><b>Assess anybody</b><p>No review, recommendation, ranking or warning about
  any event, company or person. It reports what has been published and links to it.</p></div>
  <div class="op"><b>Explain a removal</b><p>When a name leaves a list, the diff is published
  and the reason is left blank. Withdrawal, a clash, a duplicate and an editing error look
  identical from outside, and guessing would be the easiest way to do real harm.</p></div>
  <div class="op"><b>Report a target as a result</b><p>&ldquo;Targeting 2,000+&rdquo; is a plan.
  It is not attendance, and it will not be reported as attendance even after the event.</p></div>
</div>

{agent_block(
    "The ingestion path is fetch, freeze, hash, extract, diff — implemented in "
    "<code>portugal/build/extract.py</code> and reproducible from this repository. Claims point "
    "at frozen bytes, not at live URLs. <b>Biographies and other third-party prose are "
    "deliberately not reproduced</b>; the event's Topics list and lexicon matches are read from "
    "each speaker's frozen page (<code>topics.json</code>, <code>lexicon.json</code>) and carry the "
    "matched words only. The publication has a named human editor of record who "
    "reviews before publication, which is the posture difference from /governance/. It assesses "
    "nobody, explains no removal, and does not report a target as a result.")}

<div class="pagenav">
  <a href="checks.html">&larr; What we checked</a>
  <a href="team.html">The team &rarr;</a>
</div>
"""
    return write("method.html", page(
        "method.html", "The method",
        "Fetch, freeze, hash, extract, diff — the ingestion path The Governance Wire specifies and cannot run, here running.",
        body, '<a href="../index.html">newsroom.sgit.ai</a> / <a href="index.html">portugal</a> / method'))


def build_team():
    up = ""
    cards = "".join(
        '<div class="card">'
        f'<span class="tag">{esc(r["id"])} &middot; {esc(r["state"])}</span>'
        f'<h3>{esc(r["name"])}</h3>'
        f'<p><b>{esc(r["gravity"])}</b></p>'
        f'<p style="margin-top:.5rem"><b>Owns</b> &mdash; {esc(r["owns"])}</p>'
        f'<p><b>Refuses</b> &mdash; {esc(r["refuses"])}</p>'
        f'<p><b>Wrong when</b> &mdash; {esc(r["wrong_when"])}</p>'
        f'<p class="dim small" style="margin-top:.55rem">'
        f'<a href="team/{esc(r["id"])}/index.html"><b>This desk &rarr;</b></a></p>'
        "</div>" for r in TEAM["roles"])
    absent = "".join(
        f'<div class="op"><b>{esc(a["role"])}</b><p>{esc(a["why"])}</p></div>'
        for a in TEAM["not_built"])
    ed = TEAM["editor_of_record"]

    body = f"""{masthead(up, "team.html")}
<h1>The team</h1>
<p class="lead">Seven agent roles and <b>one named human</b>. The original brief specified
eleven roles; five of them are not built, and they are listed below as absent rather than
quietly dropped.</p>

{disclaimer(up)}

<h2 id="editor">The editor of record</h2>
<div class="note">
  <p style="margin-top:0"><b>{esc(ed["name"])}</b> &mdash; {esc(ed["what"])}</p>
  <p><b>Why this is here at all.</b> {esc(ed["answers"])}</p>
  <p><b>What it is not.</b> {esc(ed["limit"])}</p>
</div>
<p>This is the deliberate difference from <a href="../governance/team.html">The Governance
Wire&rsquo;s team</a>, which is fully agentic and states on every page that no human reads a
page before it publishes. That posture is defensible when the subject is a regulation. It is
not defensible when the subject is a named person who will be in the same room as the reader.</p>

<h2 id="roles">Seven roles</h2>
<div class="cards">{cards}</div>

<h2 id="absent">Four of the original eleven, and one more, are not built</h2>
<p>The 12 May 2026 brief specified eleven roles. Naming the missing ones costs nothing and
claiming them would cost the whole argument.</p>
<div class="ops">{absent}</div>

{agent_block(
    f"Seven agent roles plus a named human editor of record ({esc(ed['name'])}) who reviews "
    "before publication — <code>human_in_the_loop</code> is <b>true</b> here, unlike "
    "/governance/. Roster at <code>/portugal/data/team.json</code>, one page per role under "
    "<code>/portugal/team/&lt;role&gt;/</code>. Five roles from the original eleven-role brief "
    "are declared <code>not_built</code> and must not be described as operating.")}

<div class="pagenav">
  <a href="method.html">&larr; The method</a>
  <a href="about.html">About &amp; limits &rarr;</a>
</div>
"""
    return write("team.html", page(
        "team.html", "The team",
        "Seven agent roles and one named human editor of record — which answers the question the original Portugal brief left open.",
        body, '<a href="../index.html">newsroom.sgit.ai</a> / <a href="index.html">portugal</a> / team'))


def build_role_pages():
    up = "../../"
    roles = TEAM["roles"]
    out = []
    for i, r in enumerate(roles):
        prev_r = roles[i - 1] if i else None
        next_r = roles[i + 1] if i + 1 < len(roles) else None
        nav = []
        nav.append(f'<a href="{up}team/{prev_r["id"]}/index.html">&larr; {esc(prev_r["name"])}</a>'
                   if prev_r else f'<a href="{up}team.html">&larr; The team</a>')
        nav.append(f'<a href="{up}team/{next_r["id"]}/index.html">{esc(next_r["name"])} &rarr;</a>'
                   if next_r else f'<a href="{up}about.html">About &amp; limits &rarr;</a>')
        body = f"""{masthead(up, "team.html")}
<span class="dim small" style="font-family:var(--mono);letter-spacing:.12em;text-transform:uppercase">Role {i + 1} of {len(roles)} &middot; {esc(r["state"])}</span>
<h1>{esc(r["name"])}</h1>
<p class="lead">{esc(r["gravity"])}</p>

{disclaimer(up)}

<div class="tablewrap"><table>
  <thead><tr><th>Owns</th><th>Refuses</th><th>Wrong when</th></tr></thead>
  <tbody><tr><td>{esc(r["owns"])}</td><td>{esc(r["refuses"])}</td><td>{esc(r["wrong_when"])}</td></tr></tbody>
</table></div>

<h2 id="refusal">The refusal, and why it is the load-bearing line</h2>
<p>A centre of gravity says what a role is for. A refusal says what it will not do under
pressure &mdash; and on this beat the pressure is real, because the subjects are named people
in a small ecosystem who will read what is written about them. Unlike
<a href="{up}../governance/team.html">the fully-agentic sibling</a>, this pipeline also has a
human editor of record, so the refusals are not the last line of defence. They are the first.</p>

<h2 id="works">Where this role works</h2>
<p>Everything this role produces is reproducible from this repository:
<code>portugal/build/extract.py</code> runs the ingestion path,
<code>portugal/build/build.py</code> the projection, and
<code>portugal/build/gates.py</code> the checks. The data it writes is under
<a href="{up}sources.html">the register</a> and the machine surfaces linked from every page.</p>

{agent_block(
    f"An agent role definition, not a person. Roster at <code>/portugal/data/team.json</code>. "
    f"This role's state is <code>{esc(r['state'])}</code>. The <b>Refuses</b> line is "
    "load-bearing: this publication covers named individuals, and the refusals plus a named "
    "human editor of record are what stand between the pipeline and a claim about somebody "
    "that no source supports.")}

<div class="pagenav">{"".join(nav)}</div>
"""
        out.append(write(f"team/{r['id']}/index.html", page(
            f"team/{r['id']}/index.html", r["name"],
            f'{r["name"]} — {r["gravity"]} An agent role in a newsroom with a named human editor of record.',
            body, f'<a href="{up}../index.html">newsroom.sgit.ai</a> / '
                  f'<a href="{up}index.html">portugal</a> / '
                  f'<a href="{up}team.html">team</a> / {esc(r["id"])}')))
    return out


def build_notice():
    up = ""
    n = NOTICE
    held = "".join(f"<li>{esc(x)}</li>" for x in n["categories_held"])
    refused = "".join(f"<li>{esc(x)}</li>" for x in n["categories_refused"])
    rights = "".join(f"<li>{esc(x)}</li>" for x in n["rights"])
    test = "".join(
        f'<div class="op"><b>{esc(t["limb"])}</b><p>{esc(t["we_say"])}</p></div>'
        for t in n["lawful_basis"]["test"])

    body = f"""{masthead(up, "notice.html")}
<h1>Your data</h1>
<p class="lead">This section names <b>{PEOPLE["count"]} people</b> it did not get the data from.
This page says what is held, why it is lawful to hold it, and <b>how to have it removed without
giving a reason</b>. Machine surface: <a href="data/notice.json">notice.json</a>.</p>

<div class="warnbox"><p style="margin-top:0"><b>Not legal advice.</b> {esc(n["not_legal_advice"])}</p></div>

<h2 id="who">Who is responsible</h2>
<div class="note">
  <p style="margin-top:0"><b>{esc(n["controller"]["who"])}</b> &mdash;
  <a href="mailto:{esc(n["controller"]["contact"])}">{esc(n["controller"]["contact"])}</a></p>
  <p>{esc(n["controller"]["why_personal"])}</p>
</div>

<h2 id="what">What is held</h2>
<p>{esc(n["subjects"])}</p>
<div class="split"><div>
<h3>Held</h3>
<ul>{held}</ul>
</div><div>
<h3>Refused, always</h3>
<ul>{refused}</ul>
</div></div>
<div class="claim">{esc(n["refusal_enforced_by"])}</div>
<p class="small dim"><b>Where it came from:</b> {esc(n["source"])}
<a href="sources.html">The register &rarr;</a></p>

<h2 id="why">Why we are allowed to</h2>
<p><b>The basis is {esc(n["lawful_basis"]["basis"].lower())}, and the journalistic route is
deliberately not claimed.</b> {esc(n["lawful_basis"]["not_journalism"])}</p>
<div class="ops">{test}</div>
<p class="small dim">{esc(n["lawful_basis"]["guidance"])}</p>

<h2 id="notice">Why this is a public page rather than an email to each of you</h2>
<p>{esc(n["why_public_notice"]["rule"])}</p>
<p>{esc(n["why_public_notice"]["so"])}</p>
<div class="warnbox"><p style="margin-top:0"><b>And the part that reflects badly on us.</b>
{esc(n["why_public_notice"]["honest_note"])}</p></div>

<h2 id="rights">What you can do</h2>
<ul>{rights}</ul>

<h2 id="object">Getting removed</h2>
<div class="note">
  <p style="margin-top:0"><b>How.</b> {esc(n["objection"]["how"])}</p>
  <p><b>{esc(n["objection"]["promise"])}</b></p>
  <p><b>What happens.</b> {esc(n["objection"]["and_then"])}</p>
</div>
<p><b>We also never say why you left somebody else&rsquo;s list.</b>
{esc(n["no_reason_rule"])}</p>

<h2 id="retention">How long</h2>
<p>{esc(n["retention"])}</p>

<h2 id="pt">Em português &mdash; resumo</h2>
<div class="note">
  <p style="margin-top:0"><b>Esta secção publica o nome, o cargo e a organização de
  {PEOPLE["count"]} pessoas</b>, tal como o próprio evento os publicou. Não guardamos moradas,
  endereços de correio eletrónico nem números de telefone de nenhuma pessoa, e não reproduzimos
  as biografias.</p>
  <p><b>O responsável pelo tratamento é {esc(n["controller"]["who"])}</b>
  (<a href="mailto:{esc(n["controller"]["contact"])}">{esc(n["controller"]["contact"])}</a>). O
  fundamento é o <b>interesse legítimo</b>. <b>Não invocamos a derrogação jornalística</b> do
  artigo 24.&ordm; da Lei 58/2019, porque esta publicação não cumpre a condição de acesso e
  exercício da profissão que esse artigo exige.</p>
  <p><b>Para ser removido, basta pedir.</b> Escreva para o endereço acima. <b>Não é preciso dar
  qualquer justificação e nenhuma lhe será pedida.</b> Pode também apresentar queixa à Comissão
  Nacional de Proteção de Dados.</p>
  <p class="small dim">Este resumo existe porque várias das pessoas nomeadas são portuguesas. O
  resto do site está em inglês. Isto não é aconselhamento jurídico.</p>
</div>

{agent_block(
    "The data-protection notice for this section, machine-readable at "
    "<code>/portugal/data/notice.json</code>. <b>The lawful basis is legitimate interests and the "
    "journalistic derogation is expressly NOT claimed</b> — Article 24(3) of Lei 58/2019 "
    "conditions it on professional accreditation this publication does not have. Personal "
    "contact details of any kind are refused at extraction time and gate check 11 fails the "
    "build if one appears in the data. Removal on request is unconditional and no reason is "
    "asked for. This is not legal advice and no lawyer has reviewed it.")}

<div class="pagenav">
  <a href="team.html">&larr; The team</a>
  <a href="about.html">About &amp; limits &rarr;</a>
</div>
"""
    return write("notice.html", page(
        "notice.html", "Your data",
        f'What this section holds about the {PEOPLE["count"]} people it names, the lawful basis for holding it, and how to be removed without giving a reason.',
        body, '<a href="../index.html">newsroom.sgit.ai</a> / <a href="index.html">portugal</a> / your data'))


def build_about():
    up = ""
    ed = TEAM["editor_of_record"]
    body = f"""{masthead(up, "about.html")}
<h1>About, and the limits</h1>
<p class="lead"><b>Portugal Startups is a beta with one beat and no registry behind it.</b> It does the thing this network argues for &mdash; primary sources, frozen and
hashed &mdash; and it does it over a very small piece of the world. This page is the list of
everything a reader should hold against it.</p>

<h2 id="what">What it is</h2>
<p>A publication mapping the Portuguese startup ecosystem, beginning with one event. It
originates no facts. Everything it carries was published by somebody else; what it adds is a
typed graph over that material, a path back to it, and <b>a hashed copy of what it said on the
day we read it</b>.</p>
<div class="claim">If a claim here is interesting, follow its source link and read the original.
This publication is a finding aid, not an authority.</div>

<h2 id="limits">The limits, worst first</h2>
<div class="ops">
  <div class="op"><b>1 &middot; Two kinds of publisher, and neither is a registry</b>
    <p>{SOURCES["count"]} frozen files: the event&rsquo;s own pages, and {COVERAGE["count"]}
    pages by other publishers about the event. That is enough to report what the event says
    about itself and what the press says about it, and to notice where they differ. It is
    nowhere near enough to report on an ecosystem: there is no company registry, no funding
    record and no institutional source, and every third-party page here is <em>about the
    event</em> rather than about anything the event does not itself describe.</p></div>
  <div class="op"><b>2 &middot; One event is not a beat</b>
    <p>The original brief scoped a country. This is a conference. The scoping argument holds
    &mdash; a closeable graph &mdash; but a publication that stops when the doors close on
    {esc(EVENT["dates"]["main"][1])} has proved nothing except that somebody was available for a
    week. <b>The real test is whether this is still running in October.</b></p></div>
  <div class="op"><b>3 &middot; Nothing is in Portuguese</b>
    <p>The original brief asked for both languages, and its two source briefs disagreed with
    each other about whether that was a day-one property. Nothing here is published in Portuguese.
    Section labels carry a <code>pt</code> alongside the <code>en</code> in the generator, so
    the second language is a projection to switch on rather than a retrofit &mdash; but the
    switch has not been thrown, and a structural capability is not a translation.</p></div>
  <div class="op"><b>4 &middot; No legal review</b>
    <p>There is a named editor of record, which is a person taking responsibility. It is not a
    legal opinion. The publication therefore <b>does not assess, rank or characterise any named
    person or company</b>, and the editor role refuses it structurally rather than case by
    case.</p></div>
  <div class="op"><b>5 &middot; The speaker list is a sample, not a census</b>
    <p>It is one organiser&rsquo;s selection for one event. Several of the organisations are
    not Portuguese and several are not startups. Treating it as a map of the ecosystem would be
    the most obvious mistake available here.</p></div>
</div>

<h2 id="disclaimer">Disclaimer</h2>
<div class="warnbox">
  <p style="margin-top:0"><b>Not advice of any kind.</b> Nothing here is investment, business,
  travel or professional advice, and no reader should act on it.</p>
  <p><b>Agent-produced.</b> Research, extraction and drafting are done by software agents.
  {esc(ed["name"])} reviews every page before publication, which catches what a person catches
  and not more. Errors of fact and emphasis should be assumed present rather than
  exceptional.</p>
  <p><b>Ticket prices, dates and venues change.</b> Everything here is as published on the
  frozen copy named beside it. <b>Check the event&rsquo;s own site before buying anything or
  travelling anywhere.</b></p>
  <p><b>We do not explain absences.</b> Where a name has left a published list, that is
  recorded without a reason. Do not read one in.</p>
</div>

<h2 id="where">Where this lives, and where it is going</h2>
<p>Inside <a href="../index.html">newsroom.sgit.ai</a> as a self-contained folder that can be
lifted out whole &mdash; its own data, frozen sources, generator and gate. It is built from
<a href="../mvps/portugal.html">the 12 May 2026 briefs</a>, which are the documents to read for
why any of this is shaped the way it is, and which this section is the first attempt to
actually run. <b>The commissioning brief for what comes next</b> &mdash; a natively Portuguese
newsroom at <code>pt.newsroom.sgit.ai</code>, written for the agent that will build it &mdash; is
<a href="../documents/pt-newsroom.html">here</a>.</p>
<p>The next three things, in order: a second publisher in the register so something can be
corroborated; session-to-speaker joins so the graph answers &ldquo;who is on which
stage&rdquo;; and a post-event snapshot, because <b>the most valuable copy of this list will be
the one taken the day after it stops being updated</b>.</p>

{agent_block(
    "<b>Beta. One beat. No registry or funding source. No legal review. Nothing in "
    "Portuguese.</b> Sources are primary, frozen and hashed, which is the one strong claim this "
    "section makes — the event's own pages plus third-party pages about the event, none of "
    "which describes the ecosystem beyond this one event. It reports what the event published about itself, "
    "assesses nobody, and gives no reason for any absence from a published list. The speaker "
    "list is one organiser's selection, not a census of the Portuguese ecosystem.")}

<div class="pagenav">
  <a href="team.html">&larr; The team</a>
  <a href="index.html">The wire &rarr;</a>
</div>
"""
    return write("about.html", page(
        "about.html", "About, and the limits",
        "Beta, one beat, no registry behind it, no legal review, nothing in Portuguese. Everything a reader should hold against this publication.",
        body, '<a href="../index.html">newsroom.sgit.ai</a> / <a href="index.html">portugal</a> / about'))


def build_story(st):
    up = "../"
    prose = md_to_html((CONTENT / f"{st['slug']}.md").read_text(encoding="utf-8"))
    rows = "".join(
        f'<tr><td class="small"><code>{esc(sid)}</code></td>'
        f'<td class="small"><a href="{esc(SRC[sid]["url"])}">{esc(SRC[sid]["page"])}</a></td>'
        f'<td class="small"><a href="{up}{esc(SRC[sid]["frozen"])}">frozen</a></td>'
        f'<td class="small"><code>{esc(SRC[sid]["sha256"][:20])}&hellip;</code></td></tr>'
        for sid in st["stands_on"] if sid in SRC)

    body = f"""{masthead(up)}
<span class="dim small" style="font-family:var(--mono);letter-spacing:.12em;text-transform:uppercase">{esc(st["kicker"])}</span>
<h1>{esc(st["title"])}</h1>
<p class="lead">{esc(st["standfirst"])}</p>

<div class="tablewrap"><table>
  <thead><tr><th>Published</th><th>Written by</th><th>Reviewed by</th><th>Sources</th></tr></thead>
  <tbody><tr>
    <td>{esc(st["published"])}</td>
    <td>{esc(st["byline"])}</td>
    <td><b>{esc(TEAM["editor_of_record"]["name"])}</b><br>
        <span class="dim small">named editor of record</span></td>
    <td>{len(st["stands_on"])} frozen &amp; hashed</td>
  </tr></tbody>
</table></div>

{disclaimer(up)}

{prose}

<h2 id="stands-on">What this story stands on</h2>
<p>Every claim above is checkable against these copies. Download one, hash it, and read the
claim against the file rather than against the live site.</p>
<div class="tablewrap"><table>
  <thead><tr><th>Source</th><th>Original</th><th>Our copy</th><th>SHA-256</th></tr></thead>
  <tbody>{rows}</tbody>
</table></div>

{agent_block(
    "A story projected from frozen, hashed sources listed in the table above and machine-readable "
    "at <code>/portugal/data/sources.json</code>. It was reviewed by a named human before "
    "publication. It reports what the event published and <b>makes no assessment of the event, "
    "its organisers or any named person</b>, and offers no explanation for any change to a "
    "published list. Cite the frozen sources, not this page.")}

<div class="pagenav">
  <a href="{up}index.html">&larr; The wire</a>
  <a href="{up}summit/changes.html">What changed &rarr;</a>
</div>
"""
    return write(f"stories/{st['slug']}.html", page(
        f"stories/{st['slug']}.html", st["title"], st["standfirst"], body,
        f'<a href="{up}../index.html">newsroom.sgit.ai</a> / '
        f'<a href="{up}index.html">portugal</a> / {esc(st["slug"])}'))


def main():
    B = globals()
    w = [pages.build_index(B), pages.build_graph_page(B), pages.build_explorer(B), pages.build_connections(B),
         build_summit(), build_people(), build_orgs(), build_changes(), build_sources(),
         build_checks(), build_method(), build_team(), build_notice(), build_about()]
    w += build_role_pages()
    w += [build_story(s) for s in STORIES["stories"]]
    print(f"portugal build: v{VER} — {len(w)} page(s)")
    for x in w:
        print("  ·", x)


if __name__ == "__main__":
    main()

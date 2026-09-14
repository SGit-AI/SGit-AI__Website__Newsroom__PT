#!/usr/bin/env python3
"""portugal/ — the graph. Ontology, taxonomy, nodes, edges, packs.

    python3 portugal/build/graph.py          # writes data/ontology.json, data/graph.json, data/manifest.json

Imported by build.py, which calls main() before it renders anything.

Three rules, inherited from graphs.sgit.ai's published grammar and kept here on purpose:

1. **Every edge is a verb with a distinct, named inverse.** A symmetric edge would be its own
   inverse, which the grammar bans, so there is no `related_to` and there never will be. A
   path is only worth having if it READS: walked forwards it uses the verb, walked backwards
   it uses the inverse, and either way it is a sentence.
2. **The verbs carry Portuguese.** The commissioning brief for pt.newsroom.sgit.ai rules that
   in a natively Portuguese publication the edge verbs are Portuguese verbs, because a path
   that does not read as a sentence in the reader's language has the wrong edges. This
   section is English, but its vocabulary carries `pt` on every verb and every type from day
   one, so the rule is a switch and not a rewrite.
3. **Classification is a formula, not a label.** Where a node carries a class this file did
   not read from a source — `role_class` on a person is the only case — the formula is
   published beside it and the value says "by listed title", so nobody mistakes an inference
   for a fact.

And one rule of this section's own: **every node names the frozen source it came from.** A
node with no `source` is a bug, and the gate treats it as one.

Packs are the blocks the viewer introduces nodes by. A reader starts with the event, the
organisations and the people, and switches on the sessions, the evidence, the changes, the
coverage and the stories one block at a time. That is how a graph of a few hundred nodes
stays legible: not by hiding structure, but by letting the reader choose which structure to
look at next.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEC = ROOT / "portugal"
DATA = SEC / "data"


def load(n):
    return json.loads((DATA / n).read_text(encoding="utf-8"))


# ----------------------------------------------------------------- ontology ---
NODE_TYPES = [
    {"id": "Event",        "label": "Event",        "pt": "Evento",       "colour": "#0f766e",
     "definition": "A dated, located gathering that publishes a programme and a list of who is speaking."},
    {"id": "Session",      "label": "Session",      "pt": "Sessão",       "colour": "#115e59",
     "definition": "One item on an event's published programme, with a day, a time and usually a stage."},
    {"id": "Stage",        "label": "Stage",        "pt": "Palco",        "colour": "#0e7490",
     "definition": "A named room or stage that sessions are scheduled on. This event names its stages two ways on two pages."},
    {"id": "Person",       "label": "Person",       "pt": "Pessoa",       "colour": "#b45309",
     "definition": "A named individual on the event's published speaker list, in their professional capacity. Name, listed role, listed organisation, links, the event's own topic tags for them, and the words on their page that match a published lexicon. Never a biography, never a contact detail."},
    {"id": "Organisation", "label": "Organisation", "pt": "Organização",  "colour": "#1d4ed8",
     "definition": "An organisation a person is LISTED UNDER on their speaker card. Derived from the cards, never typed by hand; placeholders such as 'Independent' are flagged, not removed."},
    {"id": "Place",        "label": "Place",        "pt": "Local",        "colour": "#4a5b6a",
     "definition": "A venue. Not a person, so its address may be held."},
    {"id": "Snapshot",     "label": "Snapshot",     "pt": "Captura",      "colour": "#5c5f66",
     "definition": "A dated capture of the source site: every page fetched, frozen to bytes in this repository, and hashed."},
    {"id": "Source",       "label": "Source",       "pt": "Fonte",        "colour": "#8a8d94",
     "definition": "One frozen page from one snapshot, with its SHA-256. The thing a claim walks back to."},
    {"id": "Coverage",     "label": "Coverage",     "pt": "Cobertura",    "colour": "#a16207",
     "definition": "A third party's published page about the event, fetched, frozen and hashed like any other source. Linked to, never reproduced."},
    {"id": "Story",        "label": "Story",        "pt": "Notícia",      "colour": "#b91c1c",
     "definition": "A piece this publication wrote, standing on named frozen sources and reviewed by the editor of record before publication."},
    {"id": "Topic",        "label": "Topic",        "pt": "Tema",         "colour": "#7c3aed",
     "definition": "A topic the event lists on a speaker's own page, verbatim. Read from the frozen page, never derived; the event's vocabulary, not ours."},
    {"id": "Industry",     "label": "Industry",     "pt": "Setor",        "colour": "#0e7490",
     "definition": "A sector named by the published lexicon (data/lexicon.json) and matched on a speaker's own page. The edge to it carries the matched words. It says the page contains those words; nothing more."},
    {"id": "Technology",   "label": "Technology",   "pt": "Tecnologia",   "colour": "#0369a1",
     "definition": "A technology named by the published lexicon and matched on a speaker's own page. Derived by formula; the edge carries the matched words."},
    {"id": "Idea",         "label": "Idea",         "pt": "Ideia",        "colour": "#9333ea",
     "definition": "A recurring idea of the founder conversation, named by the published lexicon and matched on a speaker's own page. Derived by formula; the edge carries the matched words."},
    {"id": "Service",      "label": "Service",      "pt": "Serviço",      "colour": "#be185d",
     "definition": "A kind of service a speaker's own page says they or their organisation provide, as matched by the published lexicon. Derived by formula; the edge carries the matched words."},
    {"id": "Product",      "label": "Product",      "pt": "Produto",      "colour": "#c2410c",
     "definition": "A kind of product a speaker's own page names, as matched by the published lexicon. Derived by formula; the edge carries the matched words. Categories, not product names."},
]

# verb / inverse / domain -> range / pt (verb, inverse) / how the forward edge reads
EDGES = [
    ("speaks_at",      "hosts",          "Person",       "Event",        "fala_em",       "recebe",        "{s} speaks at {t}",              "inherited"),
    ("listed_under",   "lists",          "Person",       "Organisation", "listado_em",    "lista",         "{s} is listed under {t}",        "proposed"),
    ("takes_place_at", "venue_of",       "Event",        "Place",        "decorre_em",    "é_local_de",    "{s} takes place at {t}",         "proposed"),
    ("organised_by",   "organises",      "Event",        "Organisation", "organizado_por","organiza",      "{s} is organised by {t}",        "proposed"),
    ("part_of",        "contains",       "Session",      "Event",        "parte_de",      "contém",        "{s} is part of {t}",             "inherited"),
    ("on_stage",       "stages",         "Session",      "Stage",        "no_palco",      "acolhe",        "{s} is on {t}",                  "proposed"),
    ("captured_in",    "captures",       "Source",       "Snapshot",     "capturado_em",  "captura",       "{s} was captured in {t}",        "proposed"),
    ("attested_by",    "attests",        "Person",       "Source",       "atestado_por",  "atesta",        "{s} is attested by {t}",         "proposed"),
    ("attested_by",    "attests",        "Session",      "Source",       "atestado_por",  "atesta",        "{s} is attested by {t}",         "proposed"),
    ("attested_by",    "attests",        "Event",        "Source",       "atestado_por",  "atesta",        "{s} is attested by {t}",         "proposed"),
    ("present_in",     "includes",       "Person",       "Snapshot",     "presente_em",   "inclui",        "{s} is present in {t}",          "proposed"),
    ("absent_from",    "lacks",          "Person",       "Snapshot",     "ausente_de",    "não_inclui",    "{s} is absent from {t}",         "proposed"),
    ("covers",         "covered_by",     "Coverage",     "Event",        "cobre",         "coberto_por",   "{s} covers {t}",                 "proposed"),
    ("published_by",   "publishes",      "Coverage",     "Organisation", "publicado_por", "publica",       "{s} is published by {t}",        "inherited"),
    ("stands_on",      "supports",       "Story",        "Source",       "assenta_em",    "sustenta",      "{s} stands on {t}",              "proposed"),
    ("reports",        "reported_by",    "Story",        "Event",        "relata",        "relatado_por",  "{s} reports {t}",                "proposed"),
    ("reports",        "reported_by",    "Story",        "Snapshot",     "relata",        "relatado_por",  "{s} reports {t}",                "proposed"),
    ("speaks_on",      "spoken_on_by",   "Person",       "Topic",        "fala_sobre",    "falado_por",    "{s} speaks on {t}",              "proposed"),
    ("active_in",      "practised_by",   "Person",       "Industry",     "atua_em",       "praticado_por", "{s} is active in {t}",           "proposed"),
    ("uses",           "used_by",        "Person",       "Technology",   "usa",           "usado_por",     "{s} uses {t}",                   "proposed"),
    ("advocates",      "advocated_by",   "Person",       "Idea",         "defende",       "defendido_por", "{s} advocates {t}",              "proposed"),
    ("offers",         "offered_by",     "Person",       "Service",      "oferece",       "oferecido_por", "{s} offers {t}",                 "proposed"),
    ("offers",         "offered_by",     "Person",       "Product",      "oferece",       "oferecido_por", "{s} offers {t}",                 "proposed"),
]

# Verbs whose edges are DERIVED by the lexicon rather than read from a list. Every such edge
# carries `matched` (the words the pattern hit) and the gate re-runs the pattern on the bytes.
DERIVED_VERBS = {"active_in", "uses", "advocates", "offers"}

BANNED = [
    {"verb": "related_to",      "why": "Symmetric, so it would be its own inverse, and it says nothing a reader could walk."},
    {"verb": "mentions",        "why": "Every edge in a graph built from text 'mentions' something. It is the absence of a verb."},
    {"verb": "associated_with", "why": "The verb people reach for when they do not know the relationship. Find out, or leave the edge out."},
    {"verb": "works_at",        "why": "Not what the source says. A speaker card lists an organisation; it does not assert employment. The edge is listed_under."},
]

# A taxonomy is broader/narrower classes with members. It differs from the ontology: the
# ontology says what KINDS of thing exist; the taxonomy says how they group for a reader.
TAXONOMY = [
    {"id": "entity",     "label": "Entities",   "pt": "Entidades",  "broader": None,     "types": ["Person", "Organisation", "Place"]},
    {"id": "programme",  "label": "Programme",  "pt": "Programa",   "broader": None,     "types": ["Event", "Session", "Stage"]},
    {"id": "evidence",   "label": "Evidence",   "pt": "Evidência",  "broader": None,     "types": ["Snapshot", "Source", "Coverage"]},
    {"id": "output",     "label": "Our output", "pt": "O nosso trabalho", "broader": None, "types": ["Story"]},
    {"id": "themes",     "label": "Themes",     "pt": "Temas",      "broader": None,     "types": ["Topic"]},
    {"id": "derived",    "label": "Derived by formula", "pt": "Derivado por fórmula", "broader": None,
     "types": ["Industry", "Technology", "Idea", "Service", "Product"]},
]

# The one classification this file makes up rather than reads. Published as a formula so it
# can be argued with, and every value says "by listed title" so it is never mistaken for a
# fact about the person.
ROLE_CLASS = [
    ("investor",  "investor-side, by listed title",  r"\b(investor|partner|ventures?|vc|angel|capital|fund|lp)\b"),
    ("founder",   "founder or operator, by listed title", r"\b(founder|co-founder|ceo|cto|coo|cpo|chief|head of|director|managing)\b"),
    ("advisor",   "advisor, counsel or academic, by listed title", r"\b(advisor|adviser|counsel|professor|researcher|lawyer|legal|consultant|author)\b"),
]


def role_class(role):
    r = (role or "").lower()
    for cid, label, pat in ROLE_CLASS:
        if re.search(pat, r):
            return cid, label
    return "other", "not classified by listed title"


def org_id(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "unnamed"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


# -------------------------------------------------------------------- build ---
def main():
    event = load("event.json")
    people = load("people.json")
    orgs = load("orgs.json")
    sources = load("sources.json")
    changes = load("changes.json")
    stories = load("stories.json")
    topics = load("topics.json")
    lexicon = load("lexicon.json")
    sessions = load("sessions.json")
    coverage = load("coverage.json") if (DATA / "coverage.json").exists() else {"items": []}

    latest = sources["snapshots"][-1]
    nodes, edges = [], []
    seen = set()

    def node(n):
        if n["id"] in seen:
            return
        seen.add(n["id"])
        nodes.append(n)

    def edge(verb, s, t, pack, **extra):
        edges.append({"id": f"{verb}:{s}:{t}", "verb": verb, "source": s, "target": t, "pack": pack, **extra})

    # --- the event, its venue, its organiser ---------------------------------
    ev = "event:" + event["id"]
    node({"id": ev, "type": "Event", "label": event["name"], "pack": "event",
          "dates": event["dates"]["main"], "url": event["url"], "source": f"{latest}/index"})
    node({"id": "place:unicorn-factory-lisboa", "type": "Place", "label": event["venue"]["name"],
          "pack": "event", "district": event["venue"]["district"], "source": f"{latest}/llms.txt"})
    edge("takes_place_at", ev, "place:unicorn-factory-lisboa", "event")
    org_ev = "org:" + org_id(event["organiser"]["name"])
    node({"id": org_ev, "type": "Organisation", "label": event["organiser"]["name"], "pack": "event",
          "role_in_graph": "organiser", "source": f"{latest}/index"})
    edge("organised_by", ev, org_ev, "event")
    edge("attested_by", ev, f"src:{latest}/index", "sources")

    # --- organisations, derived from the speaker cards -----------------------
    for o in orgs["orgs"]:
        node({"id": "org:" + o["id"], "type": "Organisation", "label": o["name"], "pack": "orgs",
              "placeholder": o["placeholder"], "speakers": len(o["people"]),
              "source": f"{latest}/speakers"})

    # --- people ----------------------------------------------------------------
    for p in people["people"]:
        rc, rc_label = role_class(p["role"])
        node({"id": "person:" + p["id"], "type": "Person", "label": p["name"], "pack": "people",
              "role": p["role"], "org": p["org"], "role_class": rc, "role_class_label": rc_label,
              "page": p["page"], "linkedin": p["linkedin"], "source": f"{latest}/speakers"})
        edge("speaks_at", "person:" + p["id"], ev, "people")
        if p["org"]:
            edge("listed_under", "person:" + p["id"], "org:" + org_id(p["org"]), "people")
        edge("attested_by", "person:" + p["id"], f"src:{latest}/speakers", "sources")

    # --- the event's topics per speaker, and the lexicon's tags ------------------
    LEX = {e["id"]: e for e in lexicon["entries"]}
    VERB_FOR = {t: v["verb"] for t, v in lexicon["types"].items()}
    for row in topics["people"]:
        if not row["source"]:
            continue
        pid = "person:" + row["id"]
        edge("attested_by", pid, "src:" + row["source"], "sources")
        for t in row["topics"]:
            tid = "topic:" + re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
            node({"id": tid, "type": "Topic", "label": t, "pack": "topics",
                  "read_from": "the event's Topics list on the speaker's page", "source": row["source"]})
            edge("speaks_on", pid, tid, "topics")
        for tg in row["tags"]:
            e = LEX[tg["tag"]]
            nid = "tag:" + e["id"]
            node({"id": nid, "type": e["type"], "label": e["label"], "pack": "tags", "pt": e["pt"],
                  "lexicon": e["id"], "pattern": e["pattern"],
                  "derived": True, "by": "lexicon over the speaker's own page", "source": row["source"]})
            edge(VERB_FOR[e["type"]], pid, nid, "tags", matched=tg["matched"], by="lexicon")

    # --- stages and sessions ---------------------------------------------------
    for st in sessions["stages"]:
        node({"id": "stage:" + st["id"], "type": "Stage", "label": st["label"], "pack": "sessions",
              "pt": st["pt"], "also_called": st["also_called"], "source": sessions["source"]})
    for s in sessions["sessions"]:
        node({"id": "session:" + s["id"], "type": "Session", "label": s["title"], "pack": "sessions",
              "day": s["day"], "time": s["time"], "kind": s["kind"], "source": sessions["source"]})
        edge("part_of", "session:" + s["id"], ev, "sessions")
        if s["stage"]:
            edge("on_stage", "session:" + s["id"], "stage:" + s["stage"], "sessions")
        edge("attested_by", "session:" + s["id"], "src:" + sessions["source"], "sources")

    # --- snapshots and sources -------------------------------------------------
    for snap in sources["snapshots"]:
        node({"id": "snapshot:" + snap, "type": "Snapshot", "label": f"Snapshot {snap}", "pack": "sources",
              "date": snap, "source": f"{snap}/index" if any(x["id"] == f"{snap}/index" for x in sources["sources"]) else f"{snap}/speakers"})
    for src in sources["sources"]:
        node({"id": "src:" + src["id"], "type": "Source", "label": f'{src["page"]} ({src["snapshot"]})',
              "pack": "sources", "url": src["url"], "frozen": src["frozen"], "sha256": src["sha256"],
              "bytes": src["bytes"], "retrieved": src["retrieved"], "source": src["id"]})
        edge("captured_in", "src:" + src["id"], "snapshot:" + src["snapshot"], "sources")

    # --- what moved between snapshots -----------------------------------------
    for c in changes["changes"]:
        for a in c["added"]:
            edge("present_in", "person:" + a["id"], "snapshot:" + c["to"], "changes")
            edge("absent_from", "person:" + a["id"], "snapshot:" + c["from"], "changes")
        for r in c["removed"]:
            # the person is no longer on the list, so they are not in people.json; the node
            # exists only to carry the change, and says so
            pid = "person:" + r["id"]
            node({"id": pid, "type": "Person", "label": r["name"], "pack": "changes",
                  "role": None, "org": r["org"], "role_class": "other",
                  "role_class_label": "not classified: no longer on the list",
                  "no_longer_listed": True, "reason": None,
                  "source": f'{c["from"]}/speakers'})
            edge("present_in", pid, "snapshot:" + c["from"], "changes")
            edge("absent_from", pid, "snapshot:" + c["to"], "changes")
            if r["org"]:
                edge("listed_under", pid, "org:" + org_id(r["org"]), "changes")
                node({"id": "org:" + org_id(r["org"]), "type": "Organisation", "label": r["org"],
                      "pack": "changes", "placeholder": False, "speakers": 0,
                      "source": f'{c["from"]}/speakers'})

    # --- coverage ---------------------------------------------------------------
    for cv in coverage.get("items", []):
        cid = "coverage:" + cv["id"]
        node({"id": cid, "type": "Coverage", "label": cv["title"], "pack": "coverage",
              "publisher": cv["publisher"], "published": cv.get("published"), "url": cv["url"],
              "kind": cv["kind"], "sha256": cv["sha256"], "source": cv["source"]})
        edge("covers", cid, ev, "coverage")
        oid = "org:" + org_id(cv["publisher"])
        node({"id": oid, "type": "Organisation", "label": cv["publisher"], "pack": "coverage",
              "placeholder": False, "speakers": 0, "role_in_graph": "publisher", "source": cv["source"]})
        edge("published_by", cid, oid, "coverage")

    # --- our stories ------------------------------------------------------------
    for st in stories["stories"]:
        sid = "story:" + st["slug"]
        node({"id": sid, "type": "Story", "label": st["title"], "pack": "stories",
              "published": st["published"], "page": f"stories/{st['slug']}.html",
              "source": st["stands_on"][0]})
        edge("reports", sid, ev, "stories")
        for s in st["stands_on"]:
            edge("stands_on", sid, "src:" + s, "stories")

    # --- packs, counts, checks ----------------------------------------------------
    PACKS = [
        ("event",    "The event",      True,  "The summit, its venue and its organiser."),
        ("orgs",     "Organisations",  True,  "Derived from the speaker cards. Placeholders flagged."),
        ("people",   "People",         True,  "The published speaker list, in professional capacity only."),
        ("sessions", "Programme",      False, "Sessions and stages as the agenda page lists them. No session is joined to a speaker, because the source joins none."),
        ("sources",  "Evidence",       False, "Every frozen page and the snapshot it belongs to. What every claim walks back to."),
        ("changes",  "What changed",   False, "Presence and absence across snapshots. A removal carries no reason."),
        ("coverage", "Coverage",       False, "Third-party pages about the event, frozen and hashed. Linked, not reproduced."),
        ("stories",  "Our stories",    False, "What this publication wrote, and the sources each piece stands on."),
        ("topics",   "Topics",         False, "The event's own topic tags for each speaker, read verbatim from that speaker's frozen page. The event's vocabulary, not ours."),
        ("tags",     "Derived tags",   False, "Industry, technology, idea, service and product tags derived from each speaker's own page by the published lexicon. Every edge carries the matched words; a tag says the page contains them and nothing more."),
    ]
    packs = []
    for pid, label, default, note in PACKS:
        packs.append({"id": pid, "label": label, "default": default, "note": note,
                      "nodes": sum(1 for n in nodes if n["pack"] == pid),
                      "edges": sum(1 for e in edges if e["pack"] == pid)})

    ids = {n["id"] for n in nodes}
    dangling = [e for e in edges if e["source"] not in ids or e["target"] not in ids]
    if dangling:
        raise SystemExit(f"graph: {len(dangling)} dangling edge(s), first: {dangling[0]}")

    ontology = {
        "id": "portugal-ontology", "version": "0.1.0", "updated": latest,
        "inherits_from": {"site": "graphs.sgit.ai", "page": "https://graphs.sgit.ai/v1/grammar/edge-set.html",
                          "what": "Every edge a verb with a distinct named inverse; symmetric edges banned; a path must read as a sentence in the reader's language."},
        "language_rule": ("Every type and every verb carries `pt`. This section is English; the rule is that "
                          "the vocabulary is bilingual from day one so a Portuguese edition is a switch, "
                          "and so that a Portuguese reader can already read a path aloud."),
        "node_types": NODE_TYPES,
        "edges": [{"verb": v, "inverse": i, "domain": d, "range": r, "pt": {"verb": pv, "inverse": pi},
                   "reads": reads, "origin": origin}
                  for v, i, d, r, pv, pi, reads, origin in EDGES],
        "banned": BANNED,
        "taxonomy": TAXONOMY,
        "derived_verbs": sorted(DERIVED_VERBS),
        "formulas": [{"id": "role_class", "on": "Person",
                      "note": "One of two classifications this graph makes rather than reads. Matched against the LISTED role title, first match wins, and every value carries 'by listed title'.",
                      "rules": [{"class": c, "label": l, "pattern": p} for c, l, p in ROLE_CLASS]},
                     {"id": "tags", "on": "Person",
                      "note": ("The other. Each lexicon entry is a case-insensitive regular expression run over the "
                               "Bio prose of the speaker's own frozen page; a match makes one edge (active_in, uses, "
                               "advocates or offers) carrying the matched words. Re-run on every build by gate 17. "
                               "The full lexicon, with Portuguese labels, is data/lexicon.json."),
                      "lexicon": "data/lexicon.json", "entries": len(lexicon["entries"]),
                      "rules": [{"class": e["id"], "type": e["type"], "label": e["label"], "pattern": e["pattern"]}
                                for e in lexicon["entries"]]}],
    }
    (DATA / "ontology.json").write_text(json.dumps(ontology, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    graph = {
        "id": "portugal-graph", "version": "0.1.0", "updated": latest, "snapshot": latest,
        "note": ("The whole section as one graph. Every node names the frozen source it came from; "
                 "every edge is a verb from ontology.json with a named inverse. Packs are the blocks "
                 "the viewer introduces nodes by. Nothing here was read from the live network."),
        "packs": packs,
        "counts": {"nodes": len(nodes), "edges": len(edges),
                   "by_type": {t["id"]: sum(1 for n in nodes if n["type"] == t["id"]) for t in NODE_TYPES}},
        "nodes": nodes, "edges": edges,
    }
    (DATA / "graph.json").write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # --- the same graph as RDF triples, for the SPARQL console ------------------
    # One IRI scheme, stated once: nodes live under portugal/id/, verbs under portugal/verb/,
    # types under portugal/type/, scalar attributes under portugal/prop/. The inverse of
    # every verb is declared with owl:inverseOf rather than materialised, so the store holds
    # each fact once and a query can still walk it either way. Labels carry @en and @pt so a
    # Portuguese reader can read a path aloud from the store alone. Nothing here is a second
    # source: it is graph.json re-serialised, and the count lands in manifest.json.
    NS = "https://newsroom.sgit.ai/portugal/"
    RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    RDFS = "http://www.w3.org/2000/01/rdf-schema#"
    OWL = "http://www.w3.org/2002/07/owl#"

    def iri(kind, local):
        return f"<{NS}{kind}/{local}>"

    def lit(v, lang=None):
        s = str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
        return f'"{s}"@{lang}' if lang else f'"{s}"'

    def typed(v):
        if isinstance(v, bool):
            return f'"{"true" if v else "false"}"^^<http://www.w3.org/2001/XMLSchema#boolean>'
        if isinstance(v, int):
            return f'"{v}"^^<http://www.w3.org/2001/XMLSchema#integer>'
        return lit(v)

    T = []
    for t in NODE_TYPES:
        T.append(f'{iri("type", t["id"])} <{RDF}type> <{OWL}Class> .')
        T.append(f'{iri("type", t["id"])} <{RDFS}label> {lit(t["id"], "en")} .')
        T.append(f'{iri("type", t["id"])} <{RDFS}label> {lit(t["pt"], "pt")} .')
        T.append(f'{iri("type", t["id"])} <{RDFS}comment> {lit(t["definition"], "en")} .')
    for v, i, d, r, pv, pi, reads, origin in EDGES:
        T.append(f'{iri("verb", v)} <{RDF}type> <{OWL}ObjectProperty> .')
        T.append(f'{iri("verb", i)} <{RDF}type> <{OWL}ObjectProperty> .')
        T.append(f'{iri("verb", i)} <{OWL}inverseOf> {iri("verb", v)} .')
        T.append(f'{iri("verb", v)} <{RDFS}label> {lit(v.replace("_", " "), "en")} .')
        T.append(f'{iri("verb", v)} <{RDFS}label> {lit(pv.replace("_", " "), "pt")} .')
        T.append(f'{iri("verb", i)} <{RDFS}label> {lit(i.replace("_", " "), "en")} .')
        T.append(f'{iri("verb", i)} <{RDFS}label> {lit(pi.replace("_", " "), "pt")} .')
        for dom in ([d] if isinstance(d, str) else sorted(d)):
            T.append(f'{iri("verb", v)} <{RDFS}domain> {iri("type", dom)} .')
        for rng in ([r] if isinstance(r, str) else sorted(r)):
            T.append(f'{iri("verb", v)} <{RDFS}range> {iri("type", rng)} .')
    SKIP = {"id", "type", "label", "pack"}
    for n in nodes:
        subj = iri("id", n["id"])
        T.append(f'{subj} <{RDF}type> {iri("type", n["type"])} .')
        T.append(f'{subj} <{RDFS}label> {lit(n["label"], "en")} .')
        if n.get("pt"):
            T.append(f'{subj} <{RDFS}label> {lit(n["pt"], "pt")} .')
        T.append(f'{subj} {iri("prop", "pack")} {lit(n["pack"])} .')
        for k, v in n.items():
            if k in SKIP or k == "pt" or v is None:
                continue
            if isinstance(v, list):
                for item in v:
                    T.append(f'{subj} {iri("prop", k)} {typed(item)} .')
            elif isinstance(v, dict):
                continue
            else:
                T.append(f'{subj} {iri("prop", k)} {typed(v)} .')
    for e in edges:
        T.append(f'{iri("id", e["source"])} {iri("verb", e["verb"])} {iri("id", e["target"])} .')
    # dict.fromkeys keeps first-seen order and drops the duplicates a shared attribute produces
    # (a verb declared once per domain type, a label repeated for a node that carries both), so
    # the line count of the file is the triple count of the store that loads it.
    T = list(dict.fromkeys(T))
    (DATA / "triples.nt").write_text("\n".join(T) + "\n", encoding="utf-8")
    triple_count = len(T)

    # --- the manifest the explorer renders --------------------------------------
    files = []
    for p in sorted(DATA.glob("*.json")) + sorted(DATA.glob("*.nt")):
        files.append({"path": f"data/{p.name}", "kind": "data", "bytes": p.stat().st_size, "sha256": sha(p)})
    for p in sorted((SEC / "content").glob("*.md")):
        files.append({"path": f"content/{p.name}", "kind": "prose", "bytes": p.stat().st_size, "sha256": sha(p)})
    for p in sorted((SEC / "team").glob("*/role.md")):
        files.append({"path": f"team/{p.parent.name}/role.md", "kind": "role", "bytes": p.stat().st_size, "sha256": sha(p)})
    for p in sorted((SEC / "sources" / "frozen").rglob("*")):
        if p.is_file():
            files.append({"path": p.relative_to(SEC).as_posix(), "kind": "frozen", "bytes": p.stat().st_size, "sha256": sha(p)})
    (DATA / "manifest.json").write_text(json.dumps({
        "id": "portugal-manifest", "updated": latest,
        "note": "Every file the section is built from, with its size and SHA-256, so the explorer can list the folder and a reader can check any file against it.",
        "triples": triple_count,
        "count": len(files), "files": files}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"graph: {len(nodes)} nodes, {len(edges)} edges, {len(packs)} packs; "
          f"ontology {len(NODE_TYPES)} types / {len({e[0] for e in EDGES})} verbs; "
          f"{triple_count} triples; manifest {len(files)} files")


if __name__ == "__main__":
    main()

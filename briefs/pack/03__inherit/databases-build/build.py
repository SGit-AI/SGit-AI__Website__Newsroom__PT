#!/usr/bin/env python3
"""databases/build/build.py — builds /databases/: two real database engines running in the
reader's browser over the JSON files this site is made of, with no server anywhere.

Run from the repository root, after the Portugal build (it reads /portugal/data/):

    python3 databases/build/build.py      # writes data/tables.json, data/queries-*.json, the pages
    python3 admin/build/chrome.py         # nav + footer
    node admin/build/validate.js          # site gate

The build is also the test: every example SQL query is executed here against the same
tables the browser will build (Python's sqlite3, the same loader semantics as
assets/nsdb-sql.js), and every example SPARQL query is executed with pyoxigraph over the
same triples.nt the browser loads into Oxigraph. A query that fails or returns no rows
fails the build, and the row count each returned at build time is written next to it so a
reader can see whether their run agrees.
"""
import html
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEC = ROOT / "databases"
DATA = SEC / "data"
PT = ROOT / "portugal" / "data"
ASSETS = ROOT / "assets"
HOST = "https://" + (ROOT / "CNAME").read_text().strip()
VERSION = (ROOT / "admin/build/version.txt").read_text().strip()

MANIFEST = json.loads((PT / "manifest.json").read_text(encoding="utf-8"))
GRAPH = json.loads((PT / "graph.json").read_text(encoding="utf-8"))
ONTOLOGY = json.loads((PT / "ontology.json").read_text(encoding="utf-8"))
SIZES = {f["path"]: f["bytes"] for f in MANIFEST["files"]}
EVENT_IRI = "https://newsroom.sgit.ai/portugal/id/event:startup-summit-lisbon-2026"


def kb(n):
    return f"{n/1024:.0f} KB" if n < 1024 * 1024 else f"{n/1024/1024:.1f} MB"


ENGINES = [
    {"id": "sqlite", "name": "SQLite", "via": "sql.js 1.14.2", "language": "SQL",
     "files": ["assets/vendor/sql-wasm.js", "assets/vendor/sql-wasm.wasm"],
     "licence": "MIT", "home": "https://sql.js.org/", "page": "sql.html"},
    {"id": "oxigraph", "name": "Oxigraph", "via": "oxigraph 0.5.11 (web build)", "language": "SPARQL 1.1",
     "files": ["assets/vendor/oxigraph/web.js", "assets/vendor/oxigraph/web_bg.wasm"],
     "licence": "MIT OR Apache-2.0", "home": "https://github.com/oxigraph/oxigraph", "page": "graph.html"},
]
for e in ENGINES:
    e["bytes"] = sum((ROOT / f).stat().st_size for f in e["files"])


# ------------------------------------------------------------------ tables ---
# The loader spec. The browser (assets/nsdb-sql.js) and this file read the SAME spec, so
# the tables a reader queries are the tables the build tested. `path` and `from` are dotted
# lookups; a value that is a list or an object is stored as its JSON text; booleans as 1/0.
def col(name, frm=None):
    return {"name": name, "from": frm or name}


TABLES = [
    {"name": "nodes", "file": "graph.json", "path": "nodes",
     "columns": [col("id"), col("type"), col("label"), col("pack"), col("source"), col("role"),
                 col("role_class"), col("org"), col("day"), col("time"), col("kind"), col("publisher"),
                 col("published"), col("date"), col("url"), col("page"), col("no_longer_listed")]},
    {"name": "edges", "file": "graph.json", "path": "edges",
     "columns": [col("id"), col("verb"), col("source"), col("target"), col("pack")]},
    {"name": "verbs", "file": "ontology.json", "path": "edges",
     "columns": [col("verb"), col("inverse"), col("domain"), col("range"), col("pt_verb", "pt.verb"),
                 col("pt_inverse", "pt.inverse"), col("reads"), col("origin")]},
    {"name": "types", "file": "ontology.json", "path": "node_types",
     "columns": [col("id"), col("pt"), col("colour"), col("definition")]},
    {"name": "people", "file": "people.json", "path": "people",
     "columns": [col("id"), col("name"), col("role"), col("org"), col("page"), col("linkedin")]},
    {"name": "orgs", "file": "orgs.json", "path": "orgs",
     "columns": [col("id"), col("name"), col("people"), col("placeholder")]},
    {"name": "sessions", "file": "sessions.json", "path": "sessions",
     "columns": [col("id"), col("title"), col("day"), col("time"), col("kind"), col("stage")]},
    {"name": "stages", "file": "sessions.json", "path": "stages",
     "columns": [col("id"), col("label"), col("pt"), col("also_called")]},
    {"name": "sources", "file": "sources.json", "path": "sources",
     "columns": [col("id"), col("snapshot"), col("page"), col("publisher"), col("url"), col("frozen"),
                 col("bytes"), col("sha256"), col("retrieved"), col("state")]},
    {"name": "coverage", "file": "coverage.json", "path": "items",
     "columns": [col("id"), col("publisher"), col("kind"), col("published"), col("title"), col("url"),
                 col("source"), col("bytes"), col("sha256"), col("what_it_says")]},
    {"name": "stories", "file": "stories.json", "path": "stories",
     "columns": [col("slug"), col("kicker"), col("title"), col("standfirst"), col("published"),
                 col("byline"), col("stands_on")]},
    {"name": "changes", "file": "changes.json", "path": "changes",
     "columns": [col("from_snapshot", "from"), col("to_snapshot", "to"), col("count_from"), col("count_to"),
                 col("added"), col("removed"), col("changed"), col("reason_known")]},
    {"name": "person_topics", "file": "topics.json", "path": "person_topics",
     "columns": [col("person"), col("topic"), col("source")]},
    {"name": "person_tags", "file": "topics.json", "path": "person_tags",
     "columns": [col("person"), col("tag"), col("type"), col("matched"), col("source")]},
    {"name": "lexicon", "file": "lexicon.json", "path": "entries",
     "columns": [col("id"), col("type"), col("label"), col("pt"), col("pattern")]},
]


def get(obj, path):
    for part in path.split("."):
        if isinstance(obj, dict) and part in obj:
            obj = obj[part]
        else:
            return None
    return obj


def conv(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return v


def load_tables(spec):
    """The Python twin of the browser loader. Same spec, same conversions."""
    files = {}
    db = sqlite3.connect(":memory:")
    for t in spec["tables"]:
        if t["file"] not in files:
            files[t["file"]] = json.loads((PT / t["file"]).read_text(encoding="utf-8"))
        rows = get(files[t["file"]], t["path"]) or []
        names = [c["name"] for c in t["columns"]]
        cols = ", ".join('"' + n + '"' for n in names)
        db.execute(f'CREATE TABLE "{t["name"]}" ({cols})')
        db.executemany(f'INSERT INTO "{t["name"]}" VALUES ({", ".join("?" * len(names))})',
                       [[conv(get(r, c["from"])) for c in t["columns"]] for r in rows])
    db.commit()
    return db


# ------------------------------------------------------------- SQL examples ---
SQL_EXAMPLES = [
    ("speakers-by-class", "Who is speaking, by role class",
     "The one classification the graph makes rather than reads, counted. `role_class` is a published formula over the listed title.",
     "SELECT role_class, COUNT(*) AS speakers\nFROM nodes\nWHERE type = 'Person'\nGROUP BY role_class\nORDER BY speakers DESC;"),
    ("orgs-with-several", "Organisations listing more than one speaker",
     "A join across the `listed_under` edge. Organisations are derived from the speaker cards, so this is the speaker list folded, not a registry.",
     "SELECT o.label AS organisation, COUNT(*) AS speakers\nFROM edges e\nJOIN nodes p ON p.id = e.source\nJOIN nodes o ON o.id = e.target\nWHERE e.verb = 'listed_under'\nGROUP BY o.label\nHAVING COUNT(*) > 1\nORDER BY speakers DESC, organisation;"),
    ("programme", "The programme as a table",
     "Sessions with their stage, resolved through the `on_stage` edge. Sessions with no stage on the agenda keep NULL rather than a guess.",
     "SELECT n.day, n.time, n.label AS session, n.kind,\n       (SELECT s.label FROM edges e JOIN nodes s ON s.id = e.target\n        WHERE e.source = n.id AND e.verb = 'on_stage') AS stage\nFROM nodes n\nWHERE n.type = 'Session'\nORDER BY n.day, n.time;"),
    ("arrivals", "Who arrived between the two snapshots",
     "The `absent_from` edge is only written for people the diff found. Five names are absent from the 8 September copy and present on 13 September.",
     "SELECT p.label AS person, s.label AS snapshot, e.verb\nFROM edges e\nJOIN nodes p ON p.id = e.source\nJOIN nodes s ON s.id = e.target\nWHERE e.verb IN ('absent_from', 'present_in')\nORDER BY p.label, s.label;"),
    ("no-longer-listed", "Who is no longer listed, and why the reason column is empty",
     "One row. The graph records the removal and never a reason, because the source gives none.",
     "SELECT label AS person, no_longer_listed, source\nFROM nodes\nWHERE type = 'Person' AND no_longer_listed = 1;"),
    ("verbs", "Every verb with its inverse, in both languages",
     "The ontology as a table. No verb is its own inverse; that is a build gate on the Portugal section and a query here.",
     "SELECT verb, inverse, pt_verb, pt_inverse, origin\nFROM verbs\nORDER BY verb;"),
    ("coverage", "The press, with the hash each page was frozen under",
     "Seven third-party pages, each cited only after it was frozen and hashed. The `what_it_says` column is our summary in our words; the pages are never quoted.",
     "SELECT publisher, kind, published, substr(sha256, 1, 12) AS sha256_prefix, bytes\nFROM coverage\nORDER BY published IS NULL, published, publisher;"),
    ("story-sources", "What each story stands on",
     "The `stands_on` edge from a story to a source. A story with one publisher behind it says so here.",
     "SELECT st.label AS story, src.label AS source\nFROM edges e\nJOIN nodes st ON st.id = e.source\nJOIN nodes src ON src.id = e.target\nWHERE e.verb = 'stands_on'\nORDER BY story, source;"),
    ("path", "A path as a sentence, the SQL way",
     "Session, part of, event, takes place at, place. SQL can walk a fixed-length path; it needs one join per hop and knows nothing about inverses. Compare the same question in SPARQL on the graph console.",
     "SELECT s.label AS session, 'part of' AS v1, ev.label AS event,\n       'takes place at' AS v2, pl.label AS place\nFROM nodes s\nJOIN edges e1 ON e1.source = s.id AND e1.verb = 'part_of'\nJOIN nodes ev ON ev.id = e1.target\nJOIN edges e2 ON e2.source = ev.id AND e2.verb = 'takes_place_at'\nJOIN nodes pl ON pl.id = e2.target\nWHERE s.type = 'Session'\nORDER BY s.day, s.time\nLIMIT 6;"),
    ("degree", "The most connected nodes",
     "Degree over both directions. The event and the two snapshots sit on top, which is what a graph built from frozen pages should look like.",
     "SELECT n.label, n.type, COUNT(*) AS degree\nFROM nodes n\nJOIN edges e ON e.source = n.id OR e.target = n.id\nGROUP BY n.id\nORDER BY degree DESC, n.label\nLIMIT 10;"),
    ("two-hops", "Everything within two hops of the event (recursive CTE)",
     "A graph traversal in SQL: a recursive common table expression walking edges in either direction, then counted by type. This is the query that shows where SQL stops being the natural language for a graph.",
     "WITH RECURSIVE hop(id, depth) AS (\n  SELECT 'event:startup-summit-lisbon-2026', 0\n  UNION\n  SELECT CASE WHEN e.source = h.id THEN e.target ELSE e.source END, h.depth + 1\n  FROM hop h JOIN edges e ON e.source = h.id OR e.target = h.id\n  WHERE h.depth < 2\n)\nSELECT n.type, COUNT(DISTINCT n.id) AS nodes\nFROM hop JOIN nodes n ON n.id = hop.id\nGROUP BY n.type\nORDER BY nodes DESC;"),
    ("json-arrays", "Unpacking a JSON column: who each story stands on, from stories.json itself",
     "Columns that were arrays in the JSON are stored as JSON text, and SQLite's `json_each` unpacks them. The same fact as the `stands_on` edges, read from the other file.",
     "SELECT s.title, j.value AS source_id\nFROM stories s, json_each(s.stands_on) j\nORDER BY s.published, s.title, source_id;"),
    ("topics", "The event's own topics, by how many speakers carry each",
     "The `Topics` list the event prints on every speaker's page, read verbatim from the frozen copy. The event's vocabulary, counted.",
     "SELECT topic, COUNT(*) AS speakers\nFROM person_topics\nGROUP BY topic\nORDER BY speakers DESC, topic;"),
    ("tags-evidence", "A derived tag with its evidence: the matched words",
     "Every derived tag carries the words the lexicon pattern hit on the speaker's own page, and nothing else. This is the whole evidence for the tag, on purpose.",
     "SELECT t.type, l.label AS tag, t.matched, COUNT(*) AS people\nFROM person_tags t JOIN lexicon l ON l.id = t.tag\nGROUP BY t.type, l.label, t.matched\nORDER BY people DESC, t.type, tag\nLIMIT 40;"),
    ("orgs-should-talk", "Organisations that should be talking (the connections formula)",
     "The first of the three organisation-level formulas on the Portugal connections page, verbatim: two organisations whose speakers' pages share at least three topics, industries, technologies or ideas. The page stores the rows it got at build; this is the same SQL.",
     None),
    ("register-sizes", "The register: bytes frozen per snapshot",
     "Every frozen page with its size, summed by snapshot date. The bytes are the evidence; the hash in `sources.sha256` is what the build re-verifies.",
     "SELECT snapshot, COUNT(*) AS pages, SUM(bytes) AS bytes\nFROM sources\nGROUP BY snapshot\nORDER BY snapshot;"),
]

# ---------------------------------------------------------- SPARQL examples ---
PREFIXES = ("PREFIX p: <https://newsroom.sgit.ai/portugal/id/>\n"
            "PREFIX v: <https://newsroom.sgit.ai/portugal/verb/>\n"
            "PREFIX t: <https://newsroom.sgit.ai/portugal/type/>\n"
            "PREFIX a: <https://newsroom.sgit.ai/portugal/prop/>\n"
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
            "PREFIX owl: <http://www.w3.org/2002/07/owl#>\n")

SPARQL_EXAMPLES = [
    ("count-by-type", "Nodes by type",
     "Every node carries `rdf:type`; the types are the ontology's, with labels in English and Portuguese.",
     "SELECT ?type (COUNT(?n) AS ?nodes)\nWHERE { ?n a ?type . }\nGROUP BY ?type\nORDER BY DESC(?nodes)",
     "MATCH (n)\nRETURN labels(n)[0] AS type, count(n) AS nodes\nORDER BY nodes DESC"),
    ("speakers-orgs", "Who speaks at the event, listed under which organisation",
     "Two edges from the same person. The event is named by its IRI; every node's IRI is its graph id under `portugal/id/`.",
     f"SELECT ?person ?organisation\nWHERE {{\n  ?p v:speaks_at <{EVENT_IRI}> ;\n     rdfs:label ?person ;\n     v:listed_under ?o .\n  ?o rdfs:label ?organisation .\n}}\nORDER BY ?person",
     "MATCH (p:Person)-[:SPEAKS_AT]->(:Event {id: 'event:startup-summit-lisbon-2026'}),\n      (p)-[:LISTED_UNDER]->(o:Organisation)\nRETURN p.label AS person, o.label AS organisation\nORDER BY person"),
    ("path-pt", "A path read aloud in Portuguese",
     "The verbs are in the store with `@pt` labels, so the sentence is assembled by the query, not the page. graphs.sgit.ai's rule: if a path does not read as a sentence in the reader's language, the edge is wrong.",
     "SELECT ?sessao ?v1 ?evento ?v2 ?local\nWHERE {\n  ?s a t:Session ; rdfs:label ?sessao ; v:part_of ?e .\n  ?e rdfs:label ?evento ; v:takes_place_at ?l .\n  ?l rdfs:label ?local .\n  v:part_of rdfs:label ?v1 .\n  v:takes_place_at rdfs:label ?v2 .\n  FILTER(lang(?v1) = \"pt\" && lang(?v2) = \"pt\")\n}\nLIMIT 6",
     "MATCH (s:Session)-[r1:PART_OF]->(e:Event)-[r2:TAKES_PLACE_AT]->(l:Place)\nRETURN s.label, r1.pt, e.label, r2.pt, l.label\nLIMIT 6"),
    ("inverse-walk", "Walking an edge backwards with a property path",
     "`^v:speaks_at` is `hosts` read from the event's side. The store holds each fact once; the inverse is declared with `owl:inverseOf` and walked with `^`.",
     f"SELECT ?event (COUNT(?p) AS ?speakers)\nWHERE {{\n  ?event ^v:speaks_at ?p .\n}}\nGROUP BY ?event",
     "MATCH (e:Event)<-[:SPEAKS_AT]-(p:Person)\nRETURN e, count(p) AS speakers"),
    ("inverses", "The named inverses, from the ontology inside the store",
     "The ontology travels with the data. Every verb has a distinct named inverse; a query can prove it rather than a page assert it.",
     "SELECT ?verb ?inverse ?verbo\nWHERE {\n  ?i owl:inverseOf ?v .\n  ?v rdfs:label ?verb . FILTER(lang(?verb) = \"en\")\n  ?i rdfs:label ?inverse . FILTER(lang(?inverse) = \"en\")\n  ?v rdfs:label ?verbo . FILTER(lang(?verbo) = \"pt\")\n}\nORDER BY ?verb",
     "-- Cypher has no ontology in the store; relationship types are strings.\n-- The nearest is CALL db.relationshipTypes(), which returns names without inverses."),
    ("two-hops", "Everything within two hops of the event",
     "A property path over any verb, in either direction, then counted by type. This is the query the SQL console needs a recursive CTE for.",
     f"SELECT ?type (COUNT(DISTINCT ?n) AS ?nodes)\nWHERE {{\n  <{EVENT_IRI}> (!(a|rdfs:label)|^!(a|rdfs:label))/(!(a|rdfs:label)|^!(a|rdfs:label)) ?n .\n  FILTER(isIRI(?n))\n  ?n a ?type .\n}}\nGROUP BY ?type\nORDER BY DESC(?nodes)",
     "MATCH (e:Event {id: 'event:startup-summit-lisbon-2026'})-[*1..2]-(n)\nRETURN labels(n)[0] AS type, count(DISTINCT n) AS nodes\nORDER BY nodes DESC"),
    ("stages", "Sessions grouped by stage",
     "`GROUP_CONCAT` over the `on_stage` edge. Sessions the agenda gives no stage do not appear, and that absence is the honest answer.",
     "SELECT ?stage (GROUP_CONCAT(?s; separator=\" · \") AS ?sessions)\nWHERE {\n  ?sess v:on_stage ?st ; rdfs:label ?s .\n  ?st rdfs:label ?stage . FILTER(lang(?stage) = \"en\")\n}\nGROUP BY ?stage",
     "MATCH (s:Session)-[:ON_STAGE]->(st:Stage)\nRETURN st.label AS stage, collect(s.label) AS sessions"),
    ("coverage", "The press pages and who publishes them",
     "Coverage nodes carry the publisher as a property and `covers` the event as an edge; the Organisation behind each is reached through `published_by`.",
     f"SELECT ?publisher ?title ?published\nWHERE {{\n  ?c a t:Coverage ; v:covers <{EVENT_IRI}> ; rdfs:label ?title .\n  ?c v:published_by ?org . ?org rdfs:label ?publisher .\n  OPTIONAL {{ ?c a:published ?published }}\n}}\nORDER BY ?published ?publisher",
     "MATCH (c:Coverage)-[:COVERS]->(:Event {id: 'event:startup-summit-lisbon-2026'}),\n      (c)-[:PUBLISHED_BY]->(o:Organisation)\nRETURN o.label AS publisher, c.label AS title, c.published\nORDER BY c.published, publisher"),
    ("no-longer-listed", "Who is no longer listed",
     "The boolean is typed `xsd:boolean` in the triples, so `true` matches as a literal. There is no reason property to ask for.",
     "SELECT ?person ?source\nWHERE {\n  ?p a t:Person ; a:no_longer_listed true ; rdfs:label ?person ; a:source ?source .\n}",
     "MATCH (p:Person {no_longer_listed: true})\nRETURN p.label AS person, p.source AS source"),
    ("construct-inverses", "CONSTRUCT the inverse edges on the fly",
     "The store holds 298 forward edges. This query builds the 298 inverse ones as new triples without storing them; the console shows what came back.",
     "CONSTRUCT { ?o ?inv ?s }\nWHERE {\n  ?s ?v ?o .\n  ?inv owl:inverseOf ?v .\n}",
     "-- No Cypher equivalent: inverses are not declared, so nothing can construct them."),
    ("same-topic", "Two people at different organisations who speak on the same topic",
     "The event's own topic tags, joined across organisations. The first ingredient of the connections page, one hop each side.",
     "SELECT ?topic ?org_a ?org_b\nWHERE {\n  ?p1 v:speaks_on ?t ; v:listed_under ?o1 .\n  ?p2 v:speaks_on ?t ; v:listed_under ?o2 .\n  FILTER(STR(?o1) < STR(?o2))\n  ?t rdfs:label ?topic . ?o1 rdfs:label ?org_a . ?o2 rdfs:label ?org_b .\n}\nORDER BY ?topic ?org_a ?org_b\nLIMIT 40",
     "MATCH (p1:Person)-[:SPEAKS_ON]->(t:Topic)<-[:SPEAKS_ON]-(p2:Person),\n      (p1)-[:LISTED_UNDER]->(o1:Organisation), (p2)-[:LISTED_UNDER]->(o2:Organisation)\nWHERE o1.label < o2.label\nRETURN t.label AS topic, o1.label AS org_a, o2.label AS org_b\nORDER BY topic, org_a, org_b LIMIT 40"),
    ("derived-with-pattern", "A derived tag, with the pattern that made it",
     "Tag nodes carry the lexicon pattern as a property, so the store can show the formula next to the result. The matched words live on the edge in graph.json and are not reified here; the SQL console has them.",
     "SELECT ?tag ?type ?pattern (COUNT(?p) AS ?people)\nWHERE {\n  ?p (v:active_in|v:uses|v:advocates|v:offers) ?n .\n  ?n a ?type ; rdfs:label ?tag ; a:pattern ?pattern .\n  FILTER(lang(?tag) = \"en\")\n}\nGROUP BY ?tag ?type ?pattern\nORDER BY DESC(?people)\nLIMIT 20",
     "MATCH (p:Person)-[:ACTIVE_IN|USES|ADVOCATES|OFFERS]->(n)\nRETURN n.label AS tag, labels(n)[0] AS type, n.pattern AS pattern, count(p) AS people\nORDER BY people DESC LIMIT 20"),
    ("ask-symmetric", "ASK: is any edge symmetric?",
     "graphs.sgit.ai bans symmetric edges (`related_to`, `associated_with`). The answer should be false; the rule is a query, not a promise.",
     "ASK {\n  ?x ?v ?y .\n  ?y ?v ?x .\n  FILTER(?v != owl:inverseOf && ?x != ?y)\n}",
     "MATCH (x)-[r]->(y)-[s]->(x)\nWHERE type(r) = type(s)\nRETURN count(*) > 0 AS symmetric"),
]


CONNECTIONS = json.loads((PT / "connections.json").read_text(encoding="utf-8"))


def run_sql_examples(db):
    out = []
    for qid, title, note, sql in SQL_EXAMPLES:
        if sql is None:
            sql = next(q["sql"] for q in CONNECTIONS["queries"] if q["id"] == "talk")
        try:
            cur = db.execute(sql)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
        except sqlite3.Error as e:
            raise SystemExit(f"databases: SQL example '{qid}' fails at build: {e}")
        if not rows:
            raise SystemExit(f"databases: SQL example '{qid}' returned no rows at build")
        out.append({"id": qid, "title": title, "note": note, "sql": sql,
                    "at_build": {"rows": len(rows), "columns": cols, "version": VERSION}})
    # the connections page's stored rows must be what its SQL gives against THESE tables too
    for q in CONNECTIONS["queries"]:
        got = db.execute(q["sql"]).fetchall()
        if len(got) != q["rows_at_build"]:
            raise SystemExit(f"databases: connections query '{q['id']}' gives {len(got)} rows here and "
                             f"{q['rows_at_build']} on the Portugal page — the two loaders have drifted")
    return out


def run_sparql_examples():
    try:
        import pyoxigraph as ox
    except ImportError:
        print("databases: pyoxigraph not installed — SPARQL examples NOT validated at build (pip install pyoxigraph)",
              file=sys.stderr)
        ox = None
    store = None
    if ox:
        store = ox.Store()
        store.load((PT / "triples.nt").read_bytes(), format=ox.RdfFormat.N_TRIPLES)
        assert len(store) == MANIFEST["triples"], (len(store), MANIFEST["triples"])
    out = []
    for qid, title, note, sparql, cypher in SPARQL_EXAMPLES:
        at_build = None
        if store is not None:
            try:
                res = store.query(PREFIXES + sparql)
            except Exception as e:  # noqa: BLE001 — any parse/eval error fails the build
                raise SystemExit(f"databases: SPARQL example '{qid}' fails at build: {e}")
            if isinstance(res, (bool, ox.QueryBoolean)):
                at_build = {"kind": "ask", "answer": bool(res)}
            elif isinstance(res, ox.QuerySolutions):
                sols = list(res)
                if not sols:
                    raise SystemExit(f"databases: SPARQL example '{qid}' returned no solutions at build")
                at_build = {"kind": "select", "rows": len(sols), "columns": [str(v).lstrip("?") for v in res.variables]}
            else:
                triples = list(res)
                if not triples:
                    raise SystemExit(f"databases: SPARQL example '{qid}' constructed nothing at build")
                at_build = {"kind": "construct", "triples": len(triples)}
            at_build["version"] = VERSION
        out.append({"id": qid, "title": title, "note": note, "sparql": sparql, "cypher": cypher, "at_build": at_build})
    return out, (len(store) if store is not None else None)


# ------------------------------------------------------------------- pages ---
def page(rel, title, desc, body, head_extra=""):
    depth = rel.count("/") + 1
    up = "../" * depth
    canonical = f"{HOST}/databases/{rel}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)} &middot; Databases with no server</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="newsroom.sgit.ai">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{html.escape(desc, quote=True)}">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="{up}assets/site.css">
{head_extra}</head>
<body>

<nav class="site"><div class="row"></div></nav>

<main class="doc">
<div class="crumb"><a href="{up}index.html">newsroom.sgit.ai</a> / databases</div>
{body}
</main>

<footer class="site"><div class="cols"></div></footer>
</body>
</html>
"""


def masthead(here=""):
    nav = [("index.html", "The argument"), ("sql.html", "SQL console"), ("graph.html", "SPARQL console"),
           ("../portugal/explorer.html", "The files it queries"), ("../portugal/graph.html", "The graph, drawn")]
    links = "".join(
        f'<a href="{h}" style="font-size:.83rem;color:'
        f'{"#101114;font-weight:600" if h == here else "#5c5f66"}">{l}</a>' for h, l in nav)
    return ('<div class="ops" style="margin:0 0 1.4rem">'
            '<div class="op" style="border-left-color:#0f766e">'
            '<b style="color:#0f766e">Databases with no server &middot; beta</b>'
            f'<div style="display:flex;flex-wrap:wrap;gap:.35rem 1rem;margin-top:.4rem">{links}</div>'
            '</div></div>')


def agent_block(t):
    return f'<div class="agent"><h4>For an agent</h4><p>{t}</p></div>'


CONSOLE_CSS = """<style>
.nsdb{display:grid;grid-template-columns:minmax(220px,300px) minmax(0,1fr);gap:1rem;align-items:start}
@media(max-width:820px){.nsdb{grid-template-columns:minmax(0,1fr)}}
.nsdb .ex{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:.6rem .7rem;max-height:70vh;overflow:auto}
.nsdb .ex h4{margin:.2rem 0 .5rem;font-family:var(--mono);font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}
.nsdb .ex button{display:block;width:100%;text-align:left;background:none;border:0;border-top:1px solid var(--line);padding:.5rem .2rem;font:inherit;font-size:.82rem;color:var(--fg);cursor:pointer;line-height:1.35}
.nsdb .ex button:hover,.nsdb .ex button.here{color:var(--accent-dk);font-weight:600}
.nsdb .ex button small{display:block;font-family:var(--mono);font-size:.62rem;color:var(--dim2);font-weight:400}
.nsdb textarea{width:100%;min-height:11rem;font-family:var(--mono);font-size:.82rem;line-height:1.5;border:1px solid var(--line2);border-radius:10px;padding:.7rem .8rem;background:var(--panel);color:var(--fg);resize:vertical;box-sizing:border-box}
.nsdb .bar{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin:.5rem 0}
.nsdb .bar button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:.45rem .9rem;font:inherit;font-size:.82rem;font-weight:600;cursor:pointer}
.nsdb .bar button.alt{background:var(--panel);color:var(--fg);border:1px solid var(--line2)}
.nsdb .bar button:disabled{opacity:.5;cursor:wait}
.nsdb .status{font-family:var(--mono);font-size:.72rem;color:var(--dim)}
.nsdb .status b{color:var(--accent-dk)}
.nsdb .err{font-family:var(--mono);font-size:.78rem;color:var(--red);white-space:pre-wrap;background:#fff5f5;border:1px solid #f3c7c7;border-radius:8px;padding:.5rem .7rem}
.nsdb .res{overflow:auto;max-height:60vh;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
.nsdb .res table{border-collapse:collapse;width:100%;font-size:.8rem}
.nsdb .res th{position:sticky;top:0;background:var(--panel2);text-align:left;padding:.4rem .6rem;font-family:var(--mono);font-size:.66rem;letter-spacing:.08em;text-transform:uppercase;color:var(--dim);border-bottom:1px solid var(--line);white-space:nowrap}
.nsdb .res td{padding:.35rem .6rem;border-bottom:1px solid var(--line);vertical-align:top;font-variant-numeric:tabular-nums;max-width:32rem;overflow-wrap:anywhere}
.nsdb .res td.n{text-align:right;font-family:var(--mono)}
.nsdb .res td.null{color:var(--dim2);font-style:italic}
.nsdb .note-q{font-size:.85rem;color:var(--dim);margin:.3rem 0 .6rem}
.nsdb .alt-lang{margin-top:.8rem}
.nsdb .alt-lang pre{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:.6rem .8rem;font-size:.76rem;overflow:auto;margin:.3rem 0 0}
.meter{display:grid;gap:.6rem;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));margin:.8rem 0 1.2rem}
.meter .m{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:.55rem .7rem}
.meter .m b{display:block;font-family:var(--mono);font-size:1rem;color:var(--accent-dk)}
.meter .m span{display:block;font-size:.7rem;color:var(--dim);line-height:1.4;margin-top:.15rem}
.meter .m em{display:block;font-style:normal;font-family:var(--mono);font-size:.6rem;color:var(--dim2);margin-top:.15rem}
</style>
"""


def meter(items):
    return '<div class="meter">' + "".join(
        f'<div class="m"><b id="{i}">&ndash;</b><span>{s}</span>{f"<em>{e}</em>" if e else ""}</div>' for i, s, e in items
    ) + "</div>"


def build_index(triples, sql_n, sparql_n):
    data_files = [f for f in MANIFEST["files"] if f["kind"] == "data"]
    data_bytes = sum(f["bytes"] for f in data_files)
    rows = "".join(
        f'<tr><td><a href="../portugal/{html.escape(f["path"])}">{html.escape(f["path"].split("/")[-1])}</a></td>'
        f'<td class="num">{f["bytes"]:,}</td><td><code>{f["sha256"][:12]}</code></td></tr>' for f in data_files)
    eng = "".join(
        f'<tr><td><a href="{e["home"]}">{e["name"]}</a></td><td>{e["via"]}</td><td>{e["language"]}</td>'
        f'<td class="num">{e["bytes"]:,}</td><td>{e["licence"]}</td><td><a href="{e["page"]}">console</a></td></tr>'
        for e in ENGINES)
    body = f"""{masthead("index.html")}
<h1>Databases with no server</h1>
<p class="claim">This site has no server. The Portugal section is {len(data_files)} JSON files in a git
repository, {kb(data_bytes)} in all, each with its hash in a manifest. Two real database engines run over
exactly those files <em>in your browser</em>, compiled to WebAssembly: SQLite, and Oxigraph speaking
SPARQL 1.1. Nothing is uploaded, nothing is queried remotely, and when the tab closes the database
is gone. The files are the database. The engines are readers.</p>

<div class="note"><b>The pattern, in one line.</b> Keep the truth as files; derive every other shape of it
at build time; let the reader's own machine do the querying. It is the shape the estate already runs:
sgit.ai's <a href="https://sgit.ai/demos/vaults/riskmandate-file-security/index.html">RiskMandate vault</a>,
where &ldquo;the browser becomes the database: versioned JSON in the vault is the source of truth, queried
live through SQLite compiled to WebAssembly&rdquo;, and graphs.sgit.ai's
<a href="https://graphs.sgit.ai/v1/vaults/index.html">Regulation Graph</a>, &ldquo;SQLite over WebAssembly and
rdflib with Turtle export, both client-side and ephemeral&rdquo;. This section adds the second
language: the same graph queried as triples, with a standard graph query language, still with no server.</div>

<h2 id="two-consoles">Two consoles over one set of files</h2>
<div class="cards" style="padding:0;max-width:none">
  <a class="card" href="sql.html"><span class="tag">SQL &middot; SQLite via sql.js</span>
    <h3>The SQL console</h3>
    <p>{len(TABLES)} tables built from the JSON on load, {sql_n} worked queries from a count-by-class to a
    recursive graph walk, and a box to write your own. Every example ran at build; its row count is
    printed beside it so your run can disagree.</p><span class="go">Open the SQL console &rarr;</span></a>
  <a class="card" href="graph.html"><span class="tag">SPARQL 1.1 &middot; Oxigraph</span>
    <h3>The graph console</h3>
    <p>{triples:,} triples &mdash; the same graph, the ontology inside the store, inverses declared with
    <code>owl:inverseOf</code> and walked with a property path, labels in English and Portuguese so a path
    reads aloud. {sparql_n} worked queries, each shown beside the same question in Cypher.</p>
    <span class="go">Open the graph console &rarr;</span></a>
</div>

<h2 id="pattern">The file system is the database</h2>
<p>Every fact on the Portugal section lives in one JSON file that owns it: the people in
<code>people.json</code>, the frozen pages in <code>sources.json</code>, the sessions in
<code>sessions.json</code>. The build derives the other shapes a reader might want &mdash; the graph in
<code>graph.json</code>, the same graph as RDF in <code>triples.nt</code>, the manifest with every hash
&mdash; and nothing is derived twice. There is no import step, no schema migration and no connection
string: the SQL console reads a loader spec, <a href="data/tables.json">tables.json</a>, that says which
file and which field each column comes from, so a reader who doubts a cell can open the file it came from.</p>
<p>Three things follow, and they are the argument for doing it this way rather than a cheaper way of
doing the usual thing:</p>
<ul>
  <li><b>A query is reproducible against a commit.</b> The files are versioned by git; a result carries
  the site version it ran against, and this page's examples record the row count they returned at build.
  A database that answers differently tomorrow with no commit in between is a database that has been
  edited.</li>
  <li><b>A check is a query.</b> The Portugal build runs fifteen gates in Python &mdash; no verb its own
  inverse, every node naming a registered source, nobody in the graph who is not on the published list.
  Each is expressible as a query here, and the SPARQL console runs one of them as an <code>ASK</code>.
  When the rule and the check are the same sentence, the rule cannot drift from what is enforced.</li>
  <li><b>The reader pays nothing and trusts nothing.</b> No account, no key, no request to a server that
  could log the question. The engine is {kb(sum(e["bytes"] for e in ENGINES))} of vendored code, fetched once
  and cached; the data is the same files the page is built from. An agent gets the same: both consoles
  publish <code>window.__tools</code> after a <code>tool:ready</code> event, the convention
  graphs.sgit.ai's universe reader set.</li>
</ul>

<h2 id="honest">What this is not</h2>
<p>It is not a graph database, and graphs.sgit.ai's position is inherited on purpose: <em>&ldquo;not a graph
database pitch &mdash; the claim is that one grammar is the interface at every boundary, not that things are
stored in a graph.&rdquo;</em> The JSON stays the source of truth. The SPARQL store is built from it on load
and thrown away on close; nothing is ever written back. Its shipped page lists &ldquo;browser SPARQL/Cypher, RDF
in code&rdquo; under what that site does <em>not</em> have; this page is where the estate now has it, as a
reader over files rather than a store of record.</p>
<p>It is not a server in disguise. The whole dataset is downloaded, which is fine at {kb(data_bytes)} and would
not be at a gigabyte; that is the honest scaling limit of the pattern, and the sgit.ai guidance already
names the answer &mdash; <em>manifests at build time, files on click</em>. And it is not a write path:
corrections go through the files, the build and a version, which is the point.</p>

<h2 id="engines">What is vendored, and its cost</h2>
<div class="tablewrap"><table class="pkgs">
<thead><tr><th>Engine</th><th>Build</th><th>Language</th><th>Bytes</th><th>Licence</th><th></th></tr></thead>
<tbody>{eng}</tbody></table></div>
<p class="small dim">Both are vendored under <code>assets/vendor/</code> and attributed in
<a href="https://github.com/SGit-AI/SGit-AI__Website__Newsroom/blob/dev/LICENSES.md">LICENSES.md</a>, for the
reason the rest of the site's third-party code is: an evidence chain should not end in a resource that can
move. Cypher is shown beside each SPARQL query and not executed. K&ugrave;zu compiles to WebAssembly and
would run it here; its package is 73&nbsp;MB unpacked, which is the wrong price for a demonstration, and
the choice is recorded rather than hidden.</p>

<h2 id="files">The files each console loads</h2>
<div class="tablewrap"><table class="pkgs">
<thead><tr><th>File</th><th>Bytes</th><th>SHA-256</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="small dim">From <a href="../portugal/data/manifest.json">manifest.json</a>, which the
<a href="../portugal/explorer.html">file explorer</a> renders and the Portugal gate re-verifies on every build.</p>

{agent_block("Two in-browser engines over /portugal/data/. SQL: open /databases/sql.html, wait for the "
             "<code>tool:ready</code> event, then <code>window.__tools.sql.run(sql)</code> returns "
             "<code>{columns, rows, ms}</code>; the loader spec is /databases/data/tables.json and the worked "
             "queries with their build-time row counts are /databases/data/queries-sql.json. SPARQL: "
             "/databases/graph.html, <code>window.__tools.sparql.run(query)</code>; the triples are "
             "/portugal/data/triples.nt (" + f"{triples:,}" + ", N-Triples, IRIs under "
             "https://newsroom.sgit.ai/portugal/{id,verb,type,prop}/), the worked queries with Cypher "
             "equivalents are /databases/data/queries-sparql.json. Both pages fetch only same-origin files "
             "and send nothing anywhere.")}
"""
    return page("index.html", "Databases with no server",
                "SQLite and a SPARQL 1.1 store running in the reader's browser over the JSON files this site is built from. No server, no upload, no store of record: the files are the database.",
                body)


def build_sql(examples):
    ex = "".join(
        f'<button type="button" data-id="{html.escape(e["id"])}">{html.escape(e["title"])}'
        f'<small>{e["at_build"]["rows"]} row{"s" if e["at_build"]["rows"] != 1 else ""} at build</small></button>'
        for e in examples)
    tbl = "".join(
        f'<tr><td><code>{t["name"]}</code></td><td><a href="../portugal/data/{t["file"]}">{t["file"]}</a> &rarr; <code>{t["path"]}</code></td>'
        f'<td>{", ".join(c["name"] for c in t["columns"])}</td></tr>' for t in TABLES)
    body = f"""{masthead("sql.html")}
<h1>The SQL console</h1>
<p class="claim">SQLite, compiled to WebAssembly, running in this tab over the Portugal section's JSON files.
The tables are built when the page loads, from a spec that names the file and field behind every column.
Pick a worked query or write your own; nothing leaves your browser.</p>
{meter([("m-engine", "engine loaded", "sql-wasm.js + .wasm, then init"),
        ("m-data", "data fetched", "same-origin JSON, bytes / ms"),
        ("m-tables", "tables built", "rows inserted / ms"),
        ("m-query", "last query", "rows / ms")])}
<div class="nsdb">
  <div class="ex"><h4>Worked queries</h4>{ex}</div>
  <div>
    <div class="note-q" id="q-note">Loading the engine and the files&hellip;</div>
    <textarea id="q" spellcheck="false" aria-label="SQL query"></textarea>
    <div class="bar">
      <button type="button" id="run" disabled>Run (Ctrl+Enter)</button>
      <button type="button" class="alt" id="schema">Show schema</button>
      <button type="button" class="alt" id="link">Copy link to this query</button>
      <span class="status" id="status"></span>
    </div>
    <div id="out"></div>
  </div>
</div>

<h2 id="tables">The tables, and the file behind each</h2>
<p>This is <a href="data/tables.json">tables.json</a>, the loader spec, rendered. The build ran the same
spec through Python's sqlite3 and executed every worked query against it; a query that failed or came
back empty would have failed the build. Arrays and objects are stored as JSON text and unpacked with
<code>json_each</code>; booleans as 1 and 0.</p>
<div class="tablewrap"><table class="gloss">
<thead><tr><th>Table</th><th>From</th><th>Columns</th></tr></thead>
<tbody>{tbl}</tbody></table></div>

<h2 id="why">Where SQL is the right language, and where it stops</h2>
<p>Counting, grouping, joining two named tables, unpacking a column: SQL does these better than any
graph language and the first eight worked queries are that. Walking a path is where it strains &mdash;
one join per hop, the length fixed in the query, nothing known about inverses &mdash; and
the recursive traversal near the end of the list is the honest picture of what a two-hop neighbourhood
costs to ask for. <a href="graph.html">The graph console</a> asks the same two questions in SPARQL, for
comparison.</p>

{agent_block("After <code>tool:ready</code> (detail.name = 'nsdb-sql'): <code>window.__tools.sql.run(sql)</code> "
             "&rarr; <code>{columns, rows, ms}</code> or throws with the SQLite message; <code>.tables()</code> "
             "lists tables with row counts; <code>.examples()</code> returns the worked queries with their "
             "build-time row counts; <code>.timings()</code> the load measurements; <code>.select(id)</code> "
             "puts a worked query in the editor. The page reads <code>#q=&lt;urlencoded sql&gt;</code> and "
             "<code>?example=&lt;id&gt;</code>. Every call is read-only; there is no write path by design.")}
"""
    return page("sql.html", "The SQL console",
                "SQLite compiled to WebAssembly, running in the browser over the Portugal section's JSON files. Worked queries with their build-time row counts, and a box for your own.",
                body, CONSOLE_CSS + '<script src="../assets/vendor/sql-wasm.js"></script>\n<script src="../assets/nsdb-sql.js" defer></script>\n')


def build_graph(examples, triples):
    def small(e):
        ab = e["at_build"]
        if not ab:
            return "not run at build"
        if ab["kind"] == "ask":
            return f'ASK &rarr; {"true" if ab["answer"] else "false"} at build'
        if ab["kind"] == "construct":
            return f'{ab["triples"]} triples at build'
        return f'{ab["rows"]} row{"s" if ab["rows"] != 1 else ""} at build'
    ex = "".join(
        f'<button type="button" data-id="{html.escape(e["id"])}">{html.escape(e["title"])}<small>{small(e)}</small></button>'
        for e in examples)
    body = f"""{masthead("graph.html")}
<h1>The graph console</h1>
<p class="claim">Oxigraph, a SPARQL 1.1 store compiled to WebAssembly, running in this tab over
{triples:,} triples: the Portugal graph re-serialised at build, with the ontology inside the store, every
inverse declared with <code>owl:inverseOf</code>, and labels in English and Portuguese. Pick a worked query
or write your own; the same question in Cypher is shown beside each, and not run.</p>
{meter([("m-engine", "engine loaded", "web.js + web_bg.wasm, then init"),
        ("m-data", "triples fetched", "triples.nt, bytes / ms"),
        ("m-store", "store built", "triples / ms"),
        ("m-query", "last query", "results / ms")])}
<div class="nsdb">
  <div class="ex"><h4>Worked queries</h4>{ex}</div>
  <div>
    <div class="note-q" id="q-note">Loading the engine and the triples&hellip; (the engine is 4&nbsp;MB, fetched once and then cached)</div>
    <textarea id="q" spellcheck="false" aria-label="SPARQL query"></textarea>
    <div class="bar">
      <button type="button" id="run" disabled>Run (Ctrl+Enter)</button>
      <button type="button" class="alt" id="prefixes">Insert prefixes</button>
      <button type="button" class="alt" id="link">Copy link to this query</button>
      <span class="status" id="status"></span>
    </div>
    <div id="out"></div>
    <div class="alt-lang" id="alt" hidden><b style="font-size:.8rem">The same question in Cypher</b> <span class="small dim">&mdash; shown for comparison, not executed here</span><pre id="cypher"></pre></div>
  </div>
</div>

<h2 id="scheme">The IRI scheme, stated once</h2>
<p>The triples are <a href="../portugal/data/triples.nt">triples.nt</a>, written by the Portugal graph build
from <a href="../portugal/data/graph.json">graph.json</a> and <a href="../portugal/data/ontology.json">ontology.json</a>
&mdash; a re-serialisation, not a second source. Nodes are <code>portugal/id/&lt;graph id&gt;</code>, verbs
<code>portugal/verb/&lt;verb&gt;</code>, types <code>portugal/type/&lt;Type&gt;</code>, scalar attributes
<code>portugal/prop/&lt;key&gt;</code>. Each fact is stored once in its forward direction; the inverse verb is
declared with <code>owl:inverseOf</code> so a query walks it with <code>^</code>. Node and verb labels carry
<code>@en</code>, and <code>@pt</code> where the ontology has one, which is what lets the third worked query
read a path aloud in Portuguese from the store alone.</p>

<h2 id="why">Where a graph language earns its place</h2>
<p>Three of the worked queries cannot be asked comfortably in SQL: the property path that walks any verb in
either direction, the <code>CONSTRUCT</code> that derives 298 inverse edges without storing them, and the
<code>ASK</code> that checks the grammar's ban on symmetric edges. The rest are the same questions the
<a href="sql.html">SQL console</a> answers, so the two can be read side by side. Cypher is the other
common graph language and is shown for every query; running it here would mean vendoring a 73&nbsp;MB
engine, and the <a href="index.html#engines">argument page</a> says why that was declined.</p>

{agent_block("After <code>tool:ready</code> (detail.name = 'nsdb-sparql'): <code>window.__tools.sparql.run(query)</code> "
             "&rarr; for SELECT <code>{kind:'select', columns, rows, ms}</code> with each cell "
             "<code>{type, value, lang?}</code>; for ASK <code>{kind:'ask', answer, ms}</code>; for CONSTRUCT "
             "<code>{kind:'construct', triples:[{s,p,o}], ms}</code>. <code>.prefixes</code> is the prefix block "
             "the page prepends when a query has none; <code>.examples()</code> returns the worked queries with "
             "Cypher equivalents and build-time counts; <code>.timings()</code> the load measurements; "
             "<code>.size()</code> the triple count in the store. The page reads <code>#q=</code> and "
             "<code>?example=</code>. Read-only; SPARQL UPDATE is not exposed.")}
"""
    return page("graph.html", "The graph console",
                "A SPARQL 1.1 store (Oxigraph, WebAssembly) running in the browser over the Portugal graph as triples, with the ontology in the store and every query shown beside its Cypher equivalent.",
                body, CONSOLE_CSS + '<script type="module" src="../assets/nsdb-sparql.js"></script>\n')


def build_readme(triples, sql_n, sparql_n):
    return f"""# Databases with no server

Two real database engines running in the reader's browser, compiled to WebAssembly, over the JSON
files the Portugal section is built from. No server, no upload, no store of record.

| Page | What |
|---|---|
| `index.html` | The argument: the file system is the database; the engines are readers |
| `sql.html` | SQLite via sql.js — {len(TABLES)} tables built on load from `data/tables.json`, {sql_n} worked queries |
| `graph.html` | Oxigraph (SPARQL 1.1) over `/portugal/data/triples.nt` ({triples:,} triples), {sparql_n} worked queries with Cypher shown beside each |

## Build

```
python3 portugal/build/graph.py     # writes triples.nt alongside graph.json
python3 databases/build/build.py    # writes data/*.json and the three pages; RUNS every worked query
python3 admin/build/chrome.py
node admin/build/validate.js
```

The build is the test. Every SQL example is executed with Python's `sqlite3` against tables built from
the same spec the browser uses (`assets/nsdb-sql.js` and `build.py` share `tables.json`); every SPARQL
example is executed with `pyoxigraph` (`pip install pyoxigraph`) over the same `triples.nt`. A query
that fails or returns nothing fails the build. The count each returned is written into
`data/queries-*.json` and printed beside the query on the page.

## Vendored engines

| Path | Component | Licence |
|---|---|---|
| `assets/vendor/sql-wasm.js`, `sql-wasm.wasm` | sql.js 1.14.2 (SQLite) | MIT |
| `assets/vendor/oxigraph/web.js`, `web_bg.wasm` | oxigraph 0.5.11, web build | MIT OR Apache-2.0 |

Cypher is shown, not run: Kùzu's WebAssembly build would run it and is 73 MB unpacked.

## Agent surface

Both consoles publish `window.__tools.sql` / `window.__tools.sparql` after a `tool:ready` event,
read-only. See the agent block at the foot of each page.
"""


def main():
    spec = {"id": "nsdb-tables", "version": VERSION,
            "note": ("The loader spec the SQL console and the build share. Each table names the JSON file and "
                     "the array inside it; each column names the field (dotted). Arrays and objects are stored "
                     "as JSON text, booleans as 1/0, missing fields as NULL."),
            "base": "../portugal/data/", "tables": TABLES}
    DATA.mkdir(exist_ok=True)
    (DATA / "tables.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    db = load_tables(spec)
    sql_ex = run_sql_examples(db)
    (DATA / "queries-sql.json").write_text(json.dumps({
        "id": "nsdb-queries-sql", "version": VERSION,
        "note": "Worked SQL queries. at_build is what each returned when the site was built, so a reader's run can disagree.",
        "queries": sql_ex}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    sparql_ex, store_size = run_sparql_examples()
    (DATA / "queries-sparql.json").write_text(json.dumps({
        "id": "nsdb-queries-sparql", "version": VERSION,
        "note": "Worked SPARQL queries with the same question in Cypher (shown, not run). at_build is what each returned when the site was built.",
        "prefixes": PREFIXES, "queries": sparql_ex}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    triples = MANIFEST["triples"]
    (SEC / "index.html").write_text(build_index(triples, len(sql_ex), len(sparql_ex)), encoding="utf-8")
    (SEC / "sql.html").write_text(build_sql(sql_ex), encoding="utf-8")
    (SEC / "graph.html").write_text(build_graph(sparql_ex, triples), encoding="utf-8")
    (SEC / "README.md").write_text(build_readme(triples, len(sql_ex), len(sparql_ex)), encoding="utf-8")
    counts = {t["name"]: db.execute(f'SELECT COUNT(*) FROM "{t["name"]}"').fetchone()[0] for t in TABLES}
    print(f"databases: {len(TABLES)} tables ({sum(counts.values())} rows), {len(sql_ex)} SQL examples ran; "
          f"{len(sparql_ex)} SPARQL examples {'ran over ' + str(store_size) + ' triples' if store_size else 'NOT validated'}; 3 pages")


if __name__ == "__main__":
    main()

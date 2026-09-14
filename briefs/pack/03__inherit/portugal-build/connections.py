#!/usr/bin/env python3
"""portugal/build/connections.py — who should be talking to whom, as queries.

Reads graph.json, topics.json, people.json and orgs.json; writes data/connections.json.

Three formulae, all at ORGANISATION level. Nothing here says anything about a named person:
the unit is the organisation a speaker is listed under, and the evidence is the event's own
topic tags and the lexicon's derived tags on that organisation's speakers' pages. Each
formula is written as SQL against the same tables the SQL console builds (/databases/sql.html),
executed here with Python's sqlite3, and stored WITH its SQL so a reader can run the identical
query in their browser and get the identical rows. Gate 18 checks the stored rows re-derive.

    talk  — two organisations whose speakers' pages share topics, industries, technologies or
            ideas. Ranked by how many. "Should be talking" means: they are on the same ground.
    buy   — an organisation whose speaker's page says it offers a service, and founder-led
            organisations that do not offer it themselves. "Could be buying from": one sells
            what the other does not have.
    help  — an organisation offering a support service (investment, incubation, compute,
            advisory, coaching) that also shares ground with a founder-led organisation.
            "Could help": the offer and the overlap together.

Placeholders ("Independent") are excluded. Organisations with no speaker page (publishers,
the organiser) have no tags and so appear nowhere.
"""
import json
import sqlite3
from pathlib import Path

SEC = Path(__file__).resolve().parents[1]
DATA = SEC / "data"


def load(n):
    return json.loads((DATA / n).read_text(encoding="utf-8"))


# The tables, built exactly as databases/data/tables.json builds them (same names, same
# columns), so the SQL below is portable to the console unchanged.
TABLES = {
    "people":        ("people.json", "people", ["id", "name", "role", "org", "page", "linkedin"]),
    "orgs":          ("orgs.json", "orgs", ["id", "name", "people", "placeholder"]),
    "person_topics": ("topics.json", "person_topics", ["person", "topic", "source"]),
    "person_tags":   ("topics.json", "person_tags", ["person", "tag", "type", "matched", "source"]),
    "nodes":         ("graph.json", "nodes", ["id", "type", "label", "pack", "source", "role", "role_class", "org"]),
}


def conv(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return v


def build_db():
    db = sqlite3.connect(":memory:")
    cache = {}
    for name, (file, path, cols) in TABLES.items():
        if file not in cache:
            cache[file] = load(file)
        rows = cache[file][path]
        db.execute(f'CREATE TABLE "{name}" ({", ".join(chr(34) + c + chr(34) for c in cols)})')
        db.executemany(f'INSERT INTO "{name}" VALUES ({", ".join("?" * len(cols))})',
                       [[conv(r.get(c)) for c in cols] for r in rows])
    return db


# One CTE shared by all three: the ground each organisation stands on, via its speakers.
GROUND = """WITH ground AS (
  SELECT DISTINCT p.org AS org, t.type AS kind, t.tag AS what
  FROM person_tags t JOIN people p ON p.id = t.person
  WHERE t.type IN ('Industry', 'Technology', 'Idea')
    AND p.org NOT IN (SELECT name FROM orgs WHERE placeholder = 1)
  UNION
  SELECT DISTINCT p.org, 'Topic', pt.topic
  FROM person_topics pt JOIN people p ON p.id = pt.person
  WHERE p.org NOT IN (SELECT name FROM orgs WHERE placeholder = 1)
),
offers AS (
  SELECT DISTINCT p.org AS org, t.tag AS service
  FROM person_tags t JOIN people p ON p.id = t.person
  WHERE t.type = 'Service'
    AND p.org NOT IN (SELECT name FROM orgs WHERE placeholder = 1)
),
founder_led AS (
  SELECT DISTINCT n.org AS org FROM nodes n
  WHERE n.type = 'Person' AND n.role_class = 'founder' AND n.org IS NOT NULL
    AND n.org NOT IN (SELECT name FROM orgs WHERE placeholder = 1)
)
"""

QUERIES = [
    {"id": "talk", "title": "Organisations that should be talking",
     "reads": "Two organisations whose speakers' pages share at least three topics, industries, technologies or ideas.",
     "sql": GROUND + """SELECT a.org AS org_a, b.org AS org_b, COUNT(*) AS shared,
       GROUP_CONCAT(a.kind || ':' || a.what, ' · ') AS on_what
FROM ground a JOIN ground b ON a.kind = b.kind AND a.what = b.what AND a.org < b.org
GROUP BY a.org, b.org
HAVING COUNT(*) >= 3
ORDER BY shared DESC, org_a, org_b
LIMIT 40;"""},
    {"id": "buy", "title": "Who could be buying from whom",
     "reads": "A service a speaker's page says their organisation offers, the organisations offering it, and founder-led organisations whose pages do not offer it.",
     "sql": GROUND + """SELECT o.service AS service,
       (SELECT GROUP_CONCAT(org, ' · ') FROM (SELECT DISTINCT org FROM offers x WHERE x.service = o.service ORDER BY org)) AS providers,
       (SELECT COUNT(*) FROM founder_led f WHERE f.org NOT IN (SELECT org FROM offers x WHERE x.service = o.service)) AS founder_led_without_it,
       (SELECT GROUP_CONCAT(org, ' · ') FROM (SELECT f.org FROM founder_led f
          WHERE f.org NOT IN (SELECT org FROM offers x WHERE x.service = o.service) ORDER BY f.org LIMIT 12)) AS for_example
FROM offers o
GROUP BY o.service
ORDER BY COUNT(DISTINCT o.org) DESC, service;"""},
    {"id": "help", "title": "Who could help whom",
     "reads": "An organisation offering investment, incubation, compute, advisory or coaching that also shares ground with a founder-led organisation. The offer and the overlap together.",
     "sql": GROUND + """SELECT o.org AS provider, o.service AS offer, f.org AS founder_led, COUNT(g2.what) AS shared,
       GROUP_CONCAT(g2.kind || ':' || g2.what, ' · ') AS on_what
FROM offers o
JOIN founder_led f ON f.org <> o.org
JOIN ground g1 ON g1.org = o.org
JOIN ground g2 ON g2.org = f.org AND g2.kind = g1.kind AND g2.what = g1.what
WHERE o.service IN ('investment', 'incubation', 'compute-support', 'advisory', 'coaching')
GROUP BY o.org, o.service, f.org
HAVING COUNT(g2.what) >= 2
ORDER BY shared DESC, provider, founder_led
LIMIT 40;"""},
]


def main():
    db = build_db()
    out = []
    for q in QUERIES:
        cur = db.execute(q["sql"])
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        out.append({**q, "columns": cols, "rows": rows, "rows_at_build": len(rows)})
    topics = load("topics.json")
    (DATA / "connections.json").write_text(json.dumps({
        "id": "summit-connections", "version": "0.1.0", "updated": topics["updated"],
        "note": ("Who should be talking to whom, at organisation level, as three SQL queries over the "
                 "event's topic tags and the lexicon's derived tags. The rows are what the queries "
                 "returned at build; the SQL is stored beside them so the same query can be run in the "
                 "browser console. Nothing here is a fact about a person: the unit is the organisation "
                 "a speaker is listed under, and every reason is a tag with its matched words on record."),
        "unit": "organisation", "excludes": "placeholder organisations; organisations with no speaker page",
        "tables": list(TABLES), "queries": out}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("connections: " + ", ".join(f'{q["id"]} {q["rows_at_build"]} rows' for q in out))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""portugal/ — the ingestion path. Fetch, freeze, hash, extract, diff.

    python3 portugal/build/extract.py               # re-extract from frozen copies
    python3 portugal/build/extract.py --fetch       # take a new dated snapshot first

This is the step /governance/ specifies and cannot run. There the `frozen` state carries
`blocked: true`, nothing has ever passed it, every fact is `secondary` and nothing is
anchored. Here it runs, because a conference that publishes its own speaker list is about
the most freezable source there is.

**Frozen copies are `.snapshot`, not `.html`, and that is not cosmetic.** These are byte
copies of somebody else's pages, held so a claim can be checked. They are evidence, not
content. Giving them a non-HTML extension keeps them from being served or indexed as pages
of this site — publishing a browsable mirror of another organisation's whole website under
our domain would contradict the one rule this publication actually has, which is that we
link rather than reproduce. The bytes are unmodified, so the hash still verifies.

**Snapshots, not a single frozen copy.** `sources/frozen/<date>/<page>.html`. On this beat
the change IS the story: a speaker list a week before the doors open is a moving object,
and the only way to report on movement is to hold both copies and hash them. A single
frozen copy would prove a claim; a series proves a trajectory, and shows what disappeared.

What is extracted and what is deliberately not. Speaker cards carry name, role,
organisation, a link to that speaker's own page and usually a LinkedIn URL. Those are
extracted. **The biography paragraph is not reproduced**, on either of two grounds that each
suffice: it is the speaker's or organiser's own writing rather than a fact about the world,
and this publication links rather than reproduces. We hold the bytes for verification; we
publish the pointer. Since v0.3.4 each speaker's own page is frozen too, and two things are
READ from it without reproducing it: the event's own `Topics` list for that speaker, verbatim,
and the words on the page that match `data/lexicon.json`, a published formula. Both land in
`topics.json`; neither carries a sentence of the biography, and gate 10 fails the build if
one ever does.

On reporting a removal. A name present in one snapshot and absent from the next is
recorded as exactly that and nothing more. Withdrawal, a scheduling clash, a duplicate
record and an editing error all look identical from outside, so the diff is published and
the reason is left blank. Guessing at why a named person left a list would be the single
easiest way for this publication to do real harm.
"""
import argparse
import hashlib
import html
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEC = ROOT / "portugal"
FROZEN = SEC / "sources" / "frozen"
DATA = SEC / "data"
HOST = "https://startupsummit.io"

PAGES = {
    "index": "", "agenda": "agenda", "speakers": "speakers", "sponsors": "sponsors",
    "ai-summary": "ai-summary", "tickets": "tickets", "location": "location", "faq": "faq",
    "what-to-expect": "what-to-expect", "why-attend": "why-attend",
    "startup-booths": "startup-booths",
}
TEXT_PAGES = {"llms.txt": "llms.txt"}

# Third-party pages about the event. Fetched, frozen and hashed exactly like the event's own
# pages, into <snapshot>/coverage/. A page that does not resolve is recorded in
# coverage-notes.json under "excluded" and never enters the register.
COVERAGE = {
    "portugalglobal-pitch-marathon": "https://portugalglobal.pt/en/news/2026/julho/startup-summit-lisbon-opens-applications-for-48hr-pitch-marathon/",
    "pbn-guinness-record": "https://www.portugalbusinessesnews.com/post/startup-summit-lisbon-will-officially-attempt-to-set-a-guinness-world-record",
    "scaleup-porto": "https://scaleupporto.pt/event/startup-summit-lisbon-2026/",
    "startupevents-org": "https://startupevents.org/startup-events-calendar/startup-summit-lisbon-2026",
    "startupmaphub": "https://startupmaphub.com/events/startup-summit-lisbon-2026",
    "eventbrite-sept": "https://www.eventbrite.co.uk/e/startup-summit-lisbon-2026-founder-startup-investor-event-tickets-1987781295364",
    "summit-lisbon-tech-events": "https://startupsummit.io/lisbon-tech-events-2026",
}


def snapshots():
    return sorted(d for d in FROZEN.iterdir() if d.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.name))


def fetch_snapshot(date):
    out = FROZEN / date
    out.mkdir(parents=True, exist_ok=True)
    for name, path in {**PAGES, **TEXT_PAGES}.items():
        ext = "" if name.endswith(".txt") else ".snapshot"
        code = subprocess.run(
            ["curl", "-sL", "-o", str(out / f"{name}{ext}"), "-w", "%{http_code}",
             "--max-time", "30", f"{HOST}/{path}"], capture_output=True, text=True).stdout.strip()
        print(f"  {code}  {date}/{name}{ext}")
    (out / "coverage").mkdir(exist_ok=True)
    for cid, url in COVERAGE.items():
        code = subprocess.run(
            ["curl", "-sL", "-A", "Mozilla/5.0 (newsroom.sgit.ai research; +https://newsroom.sgit.ai/portugal/)",
             "-o", str(out / "coverage" / f"{cid}.snapshot"), "-w", "%{http_code}",
             "--max-time", "30", url], capture_output=True, text=True).stdout.strip()
        print(f"  {code}  {date}/coverage/{cid}.snapshot")
    (out / "speakers").mkdir(exist_ok=True)
    for p in people_in(out):
        code = subprocess.run(
            ["curl", "-sL", "-A", "Mozilla/5.0 (newsroom.sgit.ai research; +https://newsroom.sgit.ai/portugal/)",
             "-o", str(out / "speakers" / f"{p['id']}.snapshot"), "-w", "%{http_code}",
             "--max-time", "30", p["page"]], capture_output=True, text=True).stdout.strip()
        print(f"  {code}  {date}/speakers/{p['id']}.snapshot")
        time.sleep(0.3)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def strip_tags(x):
    return html.unescape(re.sub(r"<[^>]+>", "", x)).replace("\\n", " ").strip()


def visible(p):
    s = p.read_text(errors="replace")
    t = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", s, flags=re.S | re.I)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", t)).split())


def mtime(p):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(p.stat().st_mtime))


# ------------------------------------------------------------------ people ---
def people_in(snap):
    """One node per speaker card. Keyed on the card's own `id`, which the event site
    already uses as that speaker's URL slug — our identifier IS theirs, so nobody has to
    guess at a join."""
    f = snap / "speakers.snapshot"
    if not f.exists():
        return []
    s = f.read_text(errors="replace")
    body = s[s.find("Confirmed speakers"):]
    out = []
    for slug, card in re.findall(r'<li id="([^"]+)"[^>]*>(.*?)</li>', body, re.S):
        name = re.search(r"<h3[^>]*>(.*?)</h3>", card, re.S)
        ps = re.findall(r"<p[^>]*>(.*?)</p>", card, re.S)
        page = re.search(r'<a href="(/speakers/[^"]+)"', card)
        li = re.search(r'href="(https://[^"]*linkedin\.com[^"]*)"', card)
        out.append({
            "id": slug,
            "name": strip_tags(name.group(1)) if name else None,
            "role": strip_tags(ps[0]) if len(ps) > 0 else None,
            "org": strip_tags(ps[1]) if len(ps) > 1 else None,
            "page": HOST + page.group(1) if page else None,
            "linkedin": li.group(1) if li else None,
        })
    return out


def org_id(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "unnamed"


PLACEHOLDER_ORGS = {"independent", "self-employed", "freelance", "n/a", "-", "none"}


def build_orgs(people):
    """Organisations are DERIVED from the speaker cards, never typed by hand.

    The event's field is free text, so `Independent` arrives looking like an organisation
    and is not one. It is kept, flagged and counted separately: inventing a tidier value
    would put a fact in the graph that no source supports."""
    by = {}
    for p in people:
        if not p["org"]:
            continue
        oid = org_id(p["org"])
        by.setdefault(oid, {"id": oid, "name": p["org"], "people": [], "placeholder": False})
        by[oid]["people"].append(p["id"])
    for o in by.values():
        o["placeholder"] = o["name"].strip().lower() in PLACEHOLDER_ORGS
    return sorted(by.values(), key=lambda o: (o["placeholder"], -len(o["people"]), o["name"].lower()))


def stage_names(snap):
    known = ["Unicorn Stage", "Impact Stage", "Main Stage", "Startup Stage", "Workshop Rooms"]
    out = {}
    for name in PAGES:
        p = snap / f"{name}.snapshot"
        if not p.exists():
            continue
        found = sorted({k for k in known if k in visible(p)})
        if found:
            out[name] = found
    return out


def stated_count(snap):
    f = snap / "speakers.snapshot"
    if not f.exists():
        return None
    m = re.search(r"(\d+)\s+confirmed speakers are listed below", visible(f))
    return int(m.group(1)) if m else None


# ------------------------------------------------------------------ topics ---
def bio_block(f):
    """The prose of the speaker's own page: the <h2>Bio</h2> paragraph(s) only, tags stripped.
    The event's Topics list, the LinkedIn line and the boilerplate below are excluded so the
    lexicon runs over what the speaker (or the organiser) wrote about them and nothing else.
    Returned only to be matched against; never written anywhere."""
    s = f.read_text(errors="replace")
    m = re.search(r"<h2>Bio</h2>(.*?)(?:<h2>Topics</h2>|<p><a href=\"https://www\.linkedin|<h2>About Startup Summit</h2>)", s, re.S)
    if not m:
        return ""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", m.group(1))).replace("\\n", " ").split())


def topics_block(f):
    """The event's own Topics list for this speaker, each item verbatim."""
    s = f.read_text(errors="replace")
    m = re.search(r"<h2>Topics</h2>\s*<ul>(.*?)</ul>", s, re.S)
    if not m:
        return []
    return [html.unescape(t).strip() for t in re.findall(r"<li>(.*?)</li>", m.group(1), re.S)]


def read_topics(snap, people, lexicon):
    rows, person_topics, person_tags = [], [], []
    for p in people:
        f = snap / "speakers" / f"{p['id']}.snapshot"
        if not f.exists():
            rows.append({"id": p["id"], "source": None, "topics": [], "tags": [], "bio_chars": 0,
                         "note": "no frozen copy of this speaker's page"})
            continue
        bio = bio_block(f)
        topics = topics_block(f)
        tags = []
        for e in lexicon["entries"]:
            m = re.search(e["pattern"], bio, re.I)
            if m:
                tags.append({"tag": e["id"], "type": e["type"], "matched": m.group(0)[:40]})
        sid = f"{snap.name}/speakers/{p['id']}"
        rows.append({"id": p["id"], "source": sid, "topics": topics, "tags": tags, "bio_chars": len(bio)})
        person_topics += [{"person": p["id"], "topic": t, "source": sid} for t in topics]
        person_tags += [{"person": p["id"], **t, "source": sid} for t in tags]
    return rows, person_topics, person_tags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="take a new dated snapshot first")
    ap.add_argument("--date", default=time.strftime("%Y-%m-%d"), help="snapshot date to fetch")
    args = ap.parse_args()
    if args.fetch:
        print(f"fetching snapshot {args.date}…")
        fetch_snapshot(args.date)

    snaps = snapshots()
    if not snaps:
        raise SystemExit("no snapshots under portugal/sources/frozen/<date>/")
    latest = snaps[-1]
    today = latest.name

    # --- the register: every frozen file, hashed --------------------------------
    sources = []
    for snap in snaps:
        for name, path in {**PAGES, **TEXT_PAGES}.items():
            ext = "" if name.endswith(".txt") else ".snapshot"
            f = snap / f"{name}{ext}"
            if not f.exists():
                continue
            sources.append({
                "id": f"{snap.name}/{name}", "page": name, "snapshot": snap.name,
                "url": f"{HOST}/{path}",
                "frozen": f"sources/frozen/{snap.name}/{name}{ext}",
                "sha256": sha(f), "bytes": f.stat().st_size, "retrieved": mtime(f),
                "publisher": "Startup Summit Lisbon 2026", "state": "primary",
            })

    for snap in snaps:
        for cid, url in COVERAGE.items():
            f = snap / "coverage" / f"{cid}.snapshot"
            if not f.exists():
                continue
            if "Ocorreu algo de errado" in f.read_text(errors="replace")[:20000]:
                continue          # a 404 body; excluded, and coverage-notes.json says why
            sources.append({
                "id": f"{snap.name}/coverage/{cid}", "page": f"coverage/{cid}", "snapshot": snap.name,
                "url": url, "frozen": f"sources/frozen/{snap.name}/coverage/{cid}.snapshot",
                "sha256": sha(f), "bytes": f.stat().st_size, "retrieved": mtime(f),
                "publisher": "third party — see coverage.json", "state": "primary",
            })

    for snap in snaps:
        for f in sorted((snap / "speakers").glob("*.snapshot")):
            sources.append({
                "id": f"{snap.name}/speakers/{f.stem}", "page": f"speakers/{f.stem}", "snapshot": snap.name,
                "url": f"{HOST}/speakers/{f.stem}",
                "frozen": f"sources/frozen/{snap.name}/speakers/{f.stem}.snapshot",
                "sha256": sha(f), "bytes": f.stat().st_size, "retrieved": mtime(f),
                "publisher": "Startup Summit Lisbon 2026", "state": "primary",
            })

    notes = json.loads((DATA / "coverage-notes.json").read_text(encoding="utf-8")) \
        if (DATA / "coverage-notes.json").exists() else {"items": [], "excluded": []}
    by_src = {s["id"]: s for s in sources}
    cov_items = []
    for it in notes["items"]:
        sid = f"{latest.name}/coverage/{it['id']}"
        if sid not in by_src:
            continue          # no frozen copy in the latest snapshot: no entry
        src = by_src[sid]
        cov_items.append({**it, "url": src["url"], "source": sid, "sha256": src["sha256"],
                          "bytes": src["bytes"], "retrieved": src["retrieved"],
                          "title": (re.search(r"<title[^>]*>(.*?)</title>",
                                    (SEC / src["frozen"]).read_text(errors="replace"), re.S | re.I) or [None, it["id"]])[1]})
    for c in cov_items:
        c["title"] = html.unescape(re.sub(r"\s+", " ", c["title"])).strip()[:140]

    people = people_in(latest)
    orgs = build_orgs(people)

    # --- what moved between snapshots -------------------------------------------
    changes = []
    for a, b in zip(snaps, snaps[1:]):
        pa = {p["id"]: p for p in people_in(a)}
        pb = {p["id"]: p for p in people_in(b)}
        if not pa or not pb:
            continue
        added = [pb[i] for i in pb.keys() - pa.keys()]
        removed = [pa[i] for i in pa.keys() - pb.keys()]
        moved = []
        for i in pa.keys() & pb.keys():
            for field in ("role", "org", "name"):
                if pa[i][field] != pb[i][field]:
                    moved.append({"id": i, "name": pb[i]["name"], "field": field,
                                  "was": pa[i][field], "now": pb[i][field]})
        changes.append({
            "from": a.name, "to": b.name,
            "from_sha256": sha(a / "speakers.snapshot"), "to_sha256": sha(b / "speakers.snapshot"),
            "count_from": len(pa), "count_to": len(pb),
            "stated_from": stated_count(a), "stated_to": stated_count(b),
            "added": sorted(({"id": p["id"], "name": p["name"], "org": p["org"], "page": p["page"]}
                             for p in added), key=lambda x: x["id"]),
            "removed": sorted(({"id": p["id"], "name": p["name"], "org": p["org"]}
                               for p in removed), key=lambda x: x["id"]),
            "changed": sorted(moved, key=lambda x: x["id"]),
            "reason_known": False,
            "on_removals": ("A name present in one snapshot and absent from the next is recorded "
                            "as exactly that. Withdrawal, a scheduling clash, a duplicate record "
                            "and an editing error are indistinguishable from outside, so the "
                            "reason is left blank rather than guessed."),
        })

    DATA.mkdir(parents=True, exist_ok=True)

    def write(name, obj):
        (DATA / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    write("people.json", {
        "id": "summit-people", "version": "0.1.0", "updated": today, "snapshot": today,
        "note": ("Speakers as listed on the event's own speakers page, extracted from a frozen, "
                 "hashed copy rather than from the live network. Name, role, organisation and "
                 "links only — biographies are the speakers' and organisers' own writing and are "
                 "linked, not reproduced. Each speaker's own page is frozen too; the event's Topics "
                 "list for them and the words that match the published lexicon are read from it "
                 "into topics.json, and no sentence of the biography is."),
        "count": len(people), "with_linkedin": sum(1 for p in people if p["linkedin"]),
        "people": people,
    })
    lexicon = json.loads((DATA / "lexicon.json").read_text(encoding="utf-8"))
    trows, person_topics, person_tags = read_topics(latest, people, lexicon)
    topic_index = {}
    for pt in person_topics:
        topic_index.setdefault(pt["topic"], []).append(pt["person"])
    write("topics.json", {
        "id": "summit-topics", "version": "0.1.0", "updated": today, "snapshot": today,
        "note": ("Two things read from each speaker's own page on the event site, frozen and hashed "
                 "like every other source. TOPICS are the event's own tag list for that speaker, "
                 "verbatim. TAGS are derived: each is a lexicon entry (data/lexicon.json, a published "
                 "regular expression) that matched the page's Bio prose, and carries the matched words "
                 "and nothing else. A tag says the page contains these words; it is not a "
                 "characterisation of the person. bio_chars is the length of the prose the lexicon "
                 "ran over, kept so a reader can see how much text a tag stands on."),
        "lexicon": {"id": lexicon["id"], "version": lexicon["version"], "entries": len(lexicon["entries"])},
        "count": len(trows), "with_topics": sum(1 for r in trows if r["topics"]),
        "with_tags": sum(1 for r in trows if r["tags"]),
        "distinct_topics": len(topic_index), "distinct_tags": len({t["tag"] for t in person_tags}),
        "people": trows,
        "person_topics": person_topics,
        "person_tags": person_tags,
        "topic_index": dict(sorted(topic_index.items(), key=lambda kv: (-len(kv[1]), kv[0]))),
    })
    write("orgs.json", {
        "id": "summit-orgs", "version": "0.1.0", "updated": today,
        "note": ("Derived from the organisation field of each speaker card, never typed by hand. "
                 "The field is free text on the source, so placeholder values such as "
                 "'Independent' arrive looking like organisations. They are flagged, not removed."),
        "count": len(orgs), "placeholders": sum(1 for o in orgs if o["placeholder"]),
        "multi_speaker": sum(1 for o in orgs if len(o["people"]) > 1), "orgs": orgs,
    })
    write("sources.json", {
        "id": "summit-sources", "version": "0.1.0", "updated": today,
        "note": ("Every page fetched, frozen to bytes we hold, and hashed. This is the ingestion "
                 "path /governance/ specifies and cannot run: there the `frozen` state is blocked "
                 "and every fact is secondary. Here a claim walks back to a SHA-256."),
        "host": HOST, "snapshots": [s.name for s in snaps], "count": len(sources),
        "sources": sources,
    })
    write("changes.json", {
        "id": "summit-changes", "version": "0.1.0", "updated": today,
        "note": ("What moved between frozen snapshots of the same pages. On this beat the change "
                 "is the story: a speaker list before the doors open is a moving object, and the "
                 "only way to report movement honestly is to hold both copies and hash them."),
        "changes": changes,
    })
    write("coverage.json", {
        "id": "summit-coverage", "version": "0.1.0", "updated": today,
        "note": ("Third-party pages about the event, each fetched, frozen and hashed like any other "
                 "source. Linked to, never reproduced: 'what_it_says' is this publication's own "
                 "summary after reading the frozen copy. A page that did not resolve is listed under "
                 "'excluded' with the reason, and cannot be cited."),
        "count": len(cov_items), "items": cov_items, "excluded": notes.get("excluded", []),
    })
    write("checks.json", {
        "id": "summit-checks", "version": "0.1.0", "updated": today,
        "note": ("What re-reading the frozen copies establishes. Observations about published "
                 "artefacts, not allegations about anybody. An event still announcing speakers "
                 "weekly will have prose that lags its own list; that is ordinary. What is not "
                 "ordinary is that nothing on the open web re-checks it."),
        "speakers": {
            "cards_rendered": len(people),
            "stated_on_page": stated_count(latest),
            "agrees": len(people) == stated_count(latest),
            "home_claim": (re.search(r"Speakers\s*—\s*[^A]{0,45}", visible(latest / "index.snapshot")).group(0).strip()
                           if (latest / "index.snapshot").exists() else None),
            "target_claim": (re.search(r"targeting [^.]{0,120}", visible(latest / "index.snapshot")).group(0).strip()
                             if (latest / "index.snapshot").exists() else None),
        },
        "stage_names": stage_names(latest),
        "countries_claim_verifiable": False,
        "countries_note": ("The event states speakers and attendees from 40+ countries. No speaker "
                           "card carries a country, so this publication cannot verify or dispute "
                           "it from the source. Recorded as unverifiable here, not as doubted."),
    })

    print(f"extract: {len(snaps)} snapshot(s), {len(sources)} frozen files, "
          f"{len(people)} people, {len(orgs)} orgs")
    for c in changes:
        print(f"  {c['from']} -> {c['to']}: {c['count_from']} -> {c['count_to']} speakers "
              f"(+{len(c['added'])} / -{len(c['removed'])} / {len(c['changed'])} edited)")
    for k, v in stage_names(latest).items():
        print(f"  stages on /{k}: {', '.join(v)}")


if __name__ == "__main__":
    main()

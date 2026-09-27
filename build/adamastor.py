#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — Adamastor: freeze the Portuguese startup digest and its events calendar,
then read what was frozen.

    python3 build/adamastor.py --fetch   # freeze today's copy into fontes/congeladas/<date>/adamastor/
    python3 build/adamastor.py           # extract dados/adamastor.json from the newest frozen copy

(`dados/` is the one Portuguese name here, and it is not a choice: the folder is hardcoded in
deny-listed gates, and renaming it is task #5. Everything this file adds is named in English.)

WHAT IT IS. Adamastor (adamastor.blog) is a weekly digest on the Portuguese startup ecosystem and a
curated events calendar, written by people who run Founder Institute Portugal, Startup Grind
Lisbon, LisboaUX and LisboaJS. It covers the part of the ecosystem this newsroom had no source for
at all: 83% of the register was one event's website before this, and only 4 of the 67
organisations in the graph appear anywhere in Adamastor's digest.

WHAT IS FROZEN, AND WHY EACH ONE:

    robots        the permission. It allows ClaudeBot, anthropic-ai and `*` on `/`, and disallows
                  only /api/, /dashboard/, /login and event edit pages. Frozen FIRST, and every
                  other URL is checked against the frozen copy before it is fetched — so the
                  permission this capture relied on is itself evidence, with a hash, rather than
                  a claim in a commit message.
    llms          the publisher's own description of itself, its team and its taxonomy.
    home, about   the publication as a reader meets it.
    sitemap       the index of every post. The post list is read from the FROZEN sitemap, the
                  same way the speaker pages are read from the frozen speakers page.
    feed          the digest's RSS archive, once, as a record of what the archive said today.
    events-*      the upcoming-events feed, plus one feed per category. A category is not written
                  on an event item, so an event's categories are the category feeds it appears in:
                  a membership read from bytes, not a label assigned here.
    posts/<slug>  one page per post — the canonical artifact a citation should point at.

WHAT IS READ, AND THE THREE RULES IT OBEYS:

  * Rule 3, link never reproduce. A post keeps its title, date, byline, URL, the outbound links
    inside its <article>, and lexicon tags — the published formula in dados/lexico.json, which
    keeps only the words it matched. Not one sentence of the digest's prose is copied into a data
    file. Event descriptions are the organisers' writing and are not read at all.
  * Rule 4, nobody's contact details. The publisher's llms.txt carries a named person's email. It
    stays inside the frozen bytes — evidence is never edited — and extraction drops it: every
    string field passes through extract.sem_contactos, and `mailto:` links are never collected.
    What was dropped is counted in the output, because a refusal nobody can see run is
    indistinguishable from one that never ran.
  * A domain is not a company. 880 outbound links go to 320 domains, and it would be easy to call
    those 320 companies. They are not: they include YouTube, Spotify, Google Forms and a
    newsletter's click tracker. `resources` is a list of places the digest pointed at, counted and
    attributed to the posts that pointed. Turning any of them into a company record is task #7,
    and it needs a source of its own.

TRACKING REDIRECTS ARE NOT RESOURCES. Some links are email-campaign click trackers
(`clicks.mlsend.com`, `list-manage.com`) whose destination cannot be known without following them —
and following them would register a click in somebody's campaign. They are kept on the post, marked
`tracking_redirect`, and left out of `resources`. The patterns are in TRACKERS below, published like
any other formula.

NOT IN THE DAILY LOOP, ON PURPOSE. A capture is about 14 MB, mostly each post page's inlined
framework payload. Re-freezing all 78 posts every day would add that much to the repository daily
for posts that do not change. Whether this source joins the scheduled run — and if so, freezing
only the sitemap, the event feeds and posts not frozen before — is the editor's decision.
"""
import argparse
import html
import json
import re
import subprocess
import time
from pathlib import Path

import extract as X

ROOT = Path(__file__).resolve().parents[1]
HOST = "https://adamastor.blog"
SUBFOLDER = "adamastor"
PUBLISHER = "Adamastor"
LANGUAGE = "en"

# id -> path. Each is frozen as `<id>.snapshot`: the extension says "evidence, never a page", and a
# frozen feed.xml served from this domain under its own name would be republishing their feed.
FIXED = {
    "robots": "/robots.txt",
    "llms": "/llms.txt",
    "home": "/",
    "about": "/about",
    "sitemap": "/sitemap.xml",
    "feed": "/feed.xml",
    "events-feed": "/events/feed.xml",
    "events-ai-feed": "/events/ai/feed.xml",
    "events-software-engineering-feed": "/events/software-engineering/feed.xml",
    "events-design-feed": "/events/design/feed.xml",
    "events-product-feed": "/events/product/feed.xml",
    "events-startups-fundraising-feed": "/events/startups-fundraising/feed.xml",
}
CATEGORY_FEEDS = {
    "events-ai-feed": "ai",
    "events-software-engineering-feed": "software-engineering",
    "events-design-feed": "design",
    "events-product-feed": "product",
    "events-startups-fundraising-feed": "startups-fundraising",
}
TRACKERS = re.compile(r"(^|\.)(clicks\.mlsend\.com|list-manage\.com|mailchi\.mp|lnkd\.in)$", re.I)
PAUSE = 0.6


def robots_allows(robots_text, ua, path):
    """RFC 9309 matching: the LONGEST matching rule wins, and on a tie Allow wins.

    NOT urllib.robotparser, and the reason is worth keeping. The standard library applies the
    FIRST rule that matches, in file order. Adamastor's robots.txt — like many — opens its group
    with `Allow: /` and lists its `Disallow` lines after it, so under the standard library every
    one of them is shadowed: tested against the frozen file, it reported /api/, /dashboard/,
    /login and /events/*/edit as all fetchable. The first version of this capture used it, and
    its docstring said every URL was checked against robots.txt. It was checked, and the check
    could not say no. Nothing disallowed was fetched only because nothing disallowed was on the
    target list — which is luck, not a control.

    Group selection: a group whose User-agent names a token in our UA, else the `*` group. Our UA
    names no crawler product, so it is `*`, which is what the publisher's file allows on `/`."""
    groups, cur, in_rules = [], None, False
    for raw in robots_text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        k, v = (x.strip() for x in line.split(":", 1))
        k = k.lower()
        if k == "user-agent":
            if cur is None or in_rules:
                cur = {"agents": [], "rules": []}
                groups.append(cur)
                in_rules = False
            cur["agents"].append(v.lower())
        elif k in ("allow", "disallow") and cur is not None:
            in_rules = True
            if v:
                cur["rules"].append((k == "allow", v))
    token = ua.lower()
    mine = [g for g in groups if any(a != "*" and a in token for a in g["agents"])] or \
           [g for g in groups if "*" in g["agents"]]
    rules = [r for g in mine for r in g["rules"]]

    def matches(pattern, p):
        rx = "^" + re.escape(pattern).replace(r"\*", ".*")
        if rx.endswith(r"\$"):
            rx = rx[:-2] + "$"
        return re.match(rx, p) is not None

    best = None
    for allow, pattern in rules:
        if matches(pattern, path):
            key = (len(pattern), allow)
            if best is None or key > best[0]:
                best = (key, allow)
    return True if best is None else best[1]


# ------------------------------------------------------------------ capture ---
def url_for(rel):
    """The public URL a frozen file under `adamastor/` was fetched from. Derived from the path,
    the way a speaker page's URL is, so the register never has to trust a separately-kept list."""
    base = re.sub(r"\.snapshot$", "", rel)
    if base.startswith(f"{SUBFOLDER}/posts/"):
        return f"{HOST}/posts/{base.rsplit('/', 1)[1]}"
    return HOST + FIXED.get(base.rsplit("/", 1)[1], "/")


def post_slugs(folder):
    """Every post the publisher lists, from BOTH of its lists — and which list each came from.

    THE SITEMAP IS INCOMPLETE. On 2026-09-27 it listed 78 posts and the RSS feed the newest 50;
    14 of the feed's posts — September 2026, the most recent — were in no sitemap at all. The
    first run of this file read the sitemap alone and so froze an archive with its newest
    fortnight missing, which it reported as complete. The archive is the union, and the gap is
    kept as an observation about the publisher's artefact rather than papered over."""
    sm = folder / "sitemap.snapshot"
    fd = folder / "feed.snapshot"
    a = set(re.findall(r"<loc>\s*" + re.escape(HOST) + r"/posts/([^<\s/]+)\s*</loc>",
                       sm.read_text(encoding="utf-8"))) if sm.exists() else set()
    b = set(re.findall(r"<link>\s*" + re.escape(HOST) + r"/posts/([^<\s/]+)\s*</link>",
                       fd.read_text(encoding="utf-8"))) if fd.exists() else set()
    return {"sitemap": a, "feed": b, "all": a | b}


def _fetch(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["curl", "-sL", "-A", X.UA, "-o", str(dest), "-w", "%{http_code}",
                        "--max-time", "40", url], capture_output=True, text=True)
    return r.stdout.strip() or "000"


def capture(date):
    out = X.CONGELADAS / date / SUBFOLDER
    failed, skipped = [], []

    robots = out / "robots.snapshot"
    if not robots.exists():
        code = _fetch(HOST + FIXED["robots"], robots)
        if code != "200":
            robots.unlink(missing_ok=True)
            raise SystemExit(f"robots.txt answered {code} — capturing nothing without the permission")
    robots_text = robots.read_text(encoding="utf-8")

    def get(url, dest):
        # ONCE PER DAY PER FILE. A second run on the same date fetches only what is missing, so a
        # capture can be completed without hitting the publisher's server twice for the same page
        # and without silently replacing bytes — and the hash — of something already frozen.
        if dest.exists():
            return
        if not robots_allows(robots_text, X.UA, "/" + url.split("://", 1)[1].split("/", 1)[-1]
                             if "/" in url.split("://", 1)[1] else "/"):
            skipped.append(url)
            print(f"  skip  {url}  (robots.txt)")
            return
        c = _fetch(url, dest)
        print(f"  {c}   {dest.relative_to(X.CONGELADAS)}")
        if c != "200":
            # An error body is not evidence of anything the publisher said. Next.js answers a
            # missing page with "This page could not be found", which register()'s error markers
            # do not recognise, so the body is removed here rather than registered as primary.
            dest.unlink(missing_ok=True)
            failed.append({"url": url, "http": c})
        time.sleep(PAUSE)

    for fid, path in FIXED.items():
        if fid != "robots":
            get(HOST + path, out / f"{fid}.snapshot")

    slugs = sorted(post_slugs(out)["all"])
    for slug in slugs:
        get(f"{HOST}/posts/{slug}", out / "posts" / f"{slug}.snapshot")

    print(f"adamastor: froze {date}/{SUBFOLDER}/ — {len(FIXED)} fixed pages, {len(slugs)} posts, "
          f"{len(failed)} failed, {len(skipped)} skipped by robots.txt")
    return failed, skipped


# ------------------------------------------------------------------ extract ---
def _meta(t, prop):
    m = re.search(r'<meta[^>]+(?:property|name)="%s"[^>]+content="([^"]*)"' % re.escape(prop), t)
    return html.unescape(m.group(1)).strip() if m else None


def _posting(t):
    for block in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', t, re.S):
        try:
            d = json.loads(block)
        except json.JSONDecodeError:
            continue
        for x in (d if isinstance(d, list) else [d]):
            if isinstance(x, dict) and x.get("@type") == "BlogPosting":
                return x
    return {}


def _domain(url):
    return re.sub(r"^www\.", "", re.sub(r"^https?://", "", url).split("/")[0].split("?")[0]).lower()


def _clean(record, where, dropped):
    rec, lost = X.sem_contactos(record, where)
    dropped.extend(lost)
    return rec


def latest_capture():
    for cap in reversed(X.capturas()):
        if (cap / SUBFOLDER).is_dir():
            return cap
    return None


def read_posts(cap, lexicon, dropped):
    posts = []
    for f in sorted((cap / SUBFOLDER / "posts").glob("*.snapshot")):
        t = f.read_text(encoding="utf-8", errors="replace")
        ld = _posting(t)
        author = ld.get("author")
        author = author.get("name") if isinstance(author, dict) else author
        article = re.search(r"<article\b.*?</article>", t, re.S)
        body = article.group(0) if article else ""
        links, seen = [], set()
        for u in re.findall(r'href="(https?://[^"]+)"', body):
            u = html.unescape(u)
            if HOST in u or u in seen:
                continue
            seen.add(u)
            link = _clean({"url": u}, f"{f.stem}/link", dropped)
            if "url" not in link:
                continue
            d = _domain(u)
            links.append({"url": u, "domain": d,
                          "kind": "tracking_redirect" if TRACKERS.search(d) else "link"})
        text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", body)).split())
        tags = []
        for e in lexicon["entradas"]:
            m = re.search(e["padrao"], text, re.I)
            if m:
                tags.append({"tag": e["id"], "type": e["tipo"], "matched": m.group(0)[:40]})
        sid = f"{cap.name}/{SUBFOLDER}/posts/{f.stem}"
        posts.append(_clean({
            "id": f.stem, "slug": f.stem,
            "title": ld.get("headline") or _meta(t, "og:title"),
            "published": ld.get("datePublished") or _meta(t, "article:published_time"),
            "author": author or _meta(t, "article:author"),
            "url": f"{HOST}/posts/{f.stem}", "source": sid,
            "links": links, "tags": tags,
        }, sid, dropped))
    posts.sort(key=lambda p: p.get("published") or "", reverse=True)
    return posts


MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september",
     "october", "november", "december"], 1)}


def _date_of(when):
    """«Saturday, 26 September 2026 at 09:00» -> 2026-09-26. The verbatim string is kept beside
    it; this is only what lets a page sort and filter, and it says None rather than guess."""
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", when or "")
    if not m or m.group(2).lower() not in MONTHS:
        return None
    return f"{int(m.group(3)):04d}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"


def _plain(x):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", x)).split())


def _items(f):
    return re.findall(r"<item>(.*?)</item>", f.read_text(encoding="utf-8", errors="replace"), re.S) \
        if f.exists() else []


def _field(item, tag):
    m = re.search(r"<%s[^>]*>(.*?)</%s>" % (tag, tag), item, re.S)
    return html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", m.group(1))).strip() if m else None


def read_events(cap, dropped):
    folder = cap / SUBFOLDER
    member = {}
    for fid, cat in CATEGORY_FEEDS.items():
        for it in _items(folder / f"{fid}.snapshot"):
            member.setdefault(_field(it, "guid"), []).append(cat)
    events = []
    for it in _items(folder / "events-feed.snapshot"):
        guid = _field(it, "guid") or ""
        body = _field(it, "content:encoded") or ""
        # The publisher writes both as one structured line — `<strong>When:</strong> … <br>
        # <strong>Where:</strong> …</p>` — so they are read from that markup and nowhere else. A
        # looser pattern over the flattened text would happily take the first words of the
        # organiser's description as the venue.
        when = re.search(r"<strong>When:</strong>\s*(.*?)\s*<br", body, re.S)
        where = re.search(r"<strong>Where:</strong>\s*(.*?)\s*</p>", body, re.S)
        eid = guid.rsplit("#", 1)[-1] or guid
        sid = f"{cap.name}/{SUBFOLDER}/events-feed"
        events.append(_clean({
            "id": eid, "title": _field(it, "title"),
            "when": _plain(when.group(1)) if when else None,
            "date": _date_of(when.group(1)) if when else None,
            "where": _plain(where.group(1)) if where else None,
            "url": _field(it, "link"), "listing": guid,
            "categories": sorted(member.get(guid, [])), "source": sid,
        }, sid, dropped))
    events.sort(key=lambda e: (e.get("date") or "9999", e.get("title") or ""))
    return events


def resources(posts):
    by = {}
    for p in posts:
        for l in p["links"]:
            if l["kind"] != "link":
                continue
            r = by.setdefault(l["domain"], {"domain": l["domain"], "links": 0, "posts": []})
            r["links"] += 1
            if p["slug"] not in r["posts"]:
                r["posts"].append(p["slug"])
    return sorted(by.values(), key=lambda r: (-len(r["posts"]), -r["links"], r["domain"]))


def extract():
    cap = latest_capture()
    if not cap:
        print("adamastor: no frozen copy yet — run `python3 build/adamastor.py --fetch`")
        return
    lexicon = json.loads((X.DADOS / "lexico.json").read_text(encoding="utf-8"))
    dropped = []
    posts = read_posts(cap, lexicon, dropped)
    events = read_events(cap, dropped)
    res = resources(posts)
    frozen = sorted(p.relative_to(cap).as_posix() for p in (cap / SUBFOLDER).rglob("*.snapshot"))
    lists = post_slugs(cap / SUBFOLDER)
    missing = sorted(lists["all"] - {p["slug"] for p in posts})
    if missing:
        print(f"adamastor: WARNING — {len(missing)} listed post(s) have no frozen page: "
              f"{', '.join(missing[:5])}{'…' if len(missing) > 5 else ''}")
    doc = {
        "id": "adamastor", "version": "1.0.0", "updated": cap.name, "capture": cap.name,
        "note": ("Read from a frozen, hashed copy of adamastor.blog, never from the network. Titles "
                 "are verbatim in the language the publisher used. No prose is copied: a post "
                 "keeps its title, date, byline, outbound links and lexicon tags; an event keeps "
                 "its title, when, where and link. `resources` are places the digest linked to — "
                 "not companies. Generated by build/adamastor.py; do not edit by hand."),
        "publisher": {"name": PUBLISHER, "url": HOST + "/", "language": LANGUAGE,
                      "self_description": f"{cap.name}/{SUBFOLDER}/llms"},
        "permission": {"robots": f"{cap.name}/{SUBFOLDER}/robots",
                       "user_agent": X.UA,
                       "rule": ("every URL checked against the frozen robots.txt before it was "
                                "fetched, with RFC 9309 precedence: the longest matching rule "
                                "wins, and Allow wins a tie")},
        "trackers": TRACKERS.pattern,
        "frozen": frozen,
        "observations": {
            "sitemap_omits": sorted(lists["feed"] - lists["sitemap"]),
            "note": ("Posts the publisher's RSS feed lists and its sitemap does not. A fact about a "
                     "published file, recorded because the first capture trusted the sitemap and "
                     "missed them; not a claim about why."),
        },
        "counts": {"posts": len(posts), "events": len(events), "resources": len(res),
                   "links": sum(len(p["links"]) for p in posts),
                   "tracking_redirects": sum(1 for p in posts for l in p["links"]
                                             if l["kind"] == "tracking_redirect"),
                   "contacts_dropped": len(dropped)},
        "contacts_dropped": dropped,
        "posts": posts, "events": events, "resources": res,
    }
    X.escrever("adamastor.json", doc)
    c = doc["counts"]
    print(f"adamastor: {c['posts']} posts, {c['events']} events, {c['resources']} resource domains, "
          f"{c['tracking_redirects']} tracking redirects set aside, "
          f"{c['contacts_dropped']} contact(s) dropped — from {cap.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="freeze a new dated copy first")
    ap.add_argument("--date", default=time.strftime("%Y-%m-%d"))
    a = ap.parse_args()
    if a.fetch:
        capture(a.date)
    extract()


if __name__ == "__main__":
    main()

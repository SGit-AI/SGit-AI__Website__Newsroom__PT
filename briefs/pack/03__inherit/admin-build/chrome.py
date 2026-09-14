#!/usr/bin/env python3
"""The single definition of this site's nav and footer, and the tool that applies it.

Run from anywhere: python3 admin/build/chrome.py

Every page is hand-written static HTML — that stays true, because a human should be
able to open any file and edit it. What is NOT hand-maintained is the chrome: the nav
row (including the version badge that validate.js requires to agree everywhere) and
the footer columns. Those are defined once here and rewritten in place across the
tree, which is what stops the site from drifting as it grows.

Adding a page: add it to NAV or FOOTER if it belongs there, write the file with any
nav/footer block at all, then run this. The block contents are replaced; the `here`
state is set from the page's own path.
"""
import re
import sys
from pathlib import Path

ROOT    = Path(__file__).resolve().parents[2]
VERSION = (ROOT / "admin/build/version.txt").read_text().strip()
GH      = "https://github.com/SGit-AI/SGit-AI__Website__Newsroom"
PARENT  = "https://sgit.ai"
PARENT_TITLE = ("sgit.ai — the parent project: the vault layer and the shipped CLI. "
                "This site is the future-of-news stack: provenance, corrections, "
                "and paying the fact creator")

# The nav, two levels. Each entry is (label, own page, [(sub-label, href), ...], (path prefixes)).
#
#   · A group label is always a link to a real page, never a menu-only stub.
#   · `prefixes` decides the "here" state, so a page not itself in the nav still
#     lights up the group it belongs to.
#
# Eight groups, following the site's own build order: the argument (thesis,
# corrections, provenance) first, then the economics, then rights and operations,
# then the three things that RUN — the Governance Wire, Portugal Startups and the
# no-server databases, each with its own submenu because each is a site inside the
# site — then the record (library, shipped), then site mechanics.
NAV = [
    ("The argument", "thesis/index.html", [
        ("The thesis: sell the graph", "thesis/index.html"),
        ("Corrections must propagate", "corrections/index.html"),
        ("The claim that would not die", "corrections/the-claim-that-would-not-die.html"),
        ("Provenance is the product", "provenance/index.html"),
        ("A worked story: &pound;8.40", "provenance/a-worked-story.html"),
    ], ("thesis/", "corrections/", "provenance/")),
    ("The economics", "economics/index.html", [
        ("Paying the fact creator", "economics/index.html"),
        ("The payment rails", "economics/rails.html"),
        ("Trust as a service", "economics/trust-as-a-service.html"),
        ("Micro and nano payments (2025)", "economics/micro-and-nano-payments.html"),
    ], ("economics/",)),
    ("Rights &amp; ops", "rights/index.html", [
        ("Content rights: CC-Signed", "rights/index.html"),
        ("The newsroom: roles &amp; operations", "newsroom/index.html"),
        ("The MVPs: publication instances", "mvps/index.html"),
        ("The Portugal instance, as specified", "mvps/portugal.html"),
        ("Seed companies", "mvps/seed-companies.html"),
    ], ("rights/", "newsroom/", "mvps/")),
    ("Governance", "governance/index.html", [
        ("The wire (beta)", "governance/index.html"),
        ("The floor: a point-and-click newsroom", "governance/newsroom/index.html"),
        ("The state map: the workflow", "governance/newsroom/workflow.html"),
        ("The team: seven roles", "governance/team.html"),
        ("Research runs", "governance/research/index.html"),
        ("The graph", "governance/graph.html"),
        ("Sources", "governance/sources.html"),
        ("Method &amp; gates", "governance/method.html"),
        ("About &amp; limits", "governance/about.html"),
    ], ("governance/",)),
    ("Portugal", "portugal/index.html", [
        ("The wire (beta)", "portugal/index.html"),
        ("The graph", "portugal/graph.html"),
        ("The files", "portugal/explorer.html"),
        ("Connections", "portugal/connections.html"),
        ("The Summit", "portugal/summit/index.html"),
        ("Who is speaking", "portugal/summit/people.html"),
        ("The organisations", "portugal/summit/orgs.html"),
        ("What changed", "portugal/summit/changes.html"),
        ("Sources", "portugal/sources.html"),
        ("Method", "portugal/method.html"),
        ("The team", "portugal/team.html"),
        ("Your data", "portugal/notice.html"),
        ("About &amp; limits", "portugal/about.html"),
        ("Brief: pt.newsroom.sgit.ai", "documents/pt-newsroom.html"),
        ("pt.newsroom: the home page, as designed", "pt-newsroom/index.html"),
        ("pt.newsroom: the four directions (archive)", "pt-newsroom/directions.html"),
    ], ("portugal/", "pt-newsroom/")),
    ("Databases", "databases/index.html", [
        ("No server: the argument (beta)", "databases/index.html"),
        ("The SQL console", "databases/sql.html"),
        ("The graph console (SPARQL)", "databases/graph.html"),
        ("The files it queries", "portugal/explorer.html"),
    ], ("databases/",)),
    ("The record", "library/index.html", [
        ("The library: 2025 &rarr; present", "library/index.html"),
        ("What is shipped, what is argued", "shipped/index.html"),
    ], ("library/", "shipped/")),
    ("Site", "network/index.html", [
        ("The network: sibling boundaries", "network/index.html"),
        ("Documents &amp; sources", "documents/index.html"),
        ("Comms: tasks &amp; requests", "admin/comms.html"),
        ("Release history", "admin/versions.html"),
        ("Admin &amp; engineering", "admin/index.html"),
        ("Where we lose", "about/participant.html"),
    ], ("network/", "documents/", "admin/", "about/")),
]

FOOTER = [
    ("The argument", [
        ("&#8594; The thesis: sell the graph", "thesis/index.html"),
        ("Corrections must propagate", "corrections/index.html"),
        ("The claim that would not die", "corrections/the-claim-that-would-not-die.html"),
        ("Provenance is the product", "provenance/index.html"),
        ("A worked story: &pound;8.40", "provenance/a-worked-story.html"),
    ]),
    ("The economics", [
        ("Paying the fact creator", "economics/index.html"),
        ("The payment rails", "economics/rails.html"),
        ("Trust as a service", "economics/trust-as-a-service.html"),
        ("Micro and nano payments (2025)", "economics/micro-and-nano-payments.html"),
    ]),
    ("Rights, ops &amp; record", [
        ("Content rights: CC-Signed", "rights/index.html"),
        ("The newsroom: roles &amp; operations", "newsroom/index.html"),
        ("The MVPs: publication instances", "mvps/index.html"),
        ("The library: 2025 &rarr; present", "library/index.html"),
        ("What is shipped, what is argued", "shipped/index.html"),
    ]),
    ("What runs", [
        ("The Governance Wire (beta)", "governance/index.html"),
        ("The floor: a point-and-click newsroom", "governance/newsroom/index.html"),
        ("Portugal Startups (beta)", "portugal/index.html"),
        ("Connections: who should talk to whom", "portugal/connections.html"),
        ("Databases with no server (beta)", "databases/index.html"),
        ("The SQL and SPARQL consoles", "databases/sql.html"),
        ("Brief: pt.newsroom.sgit.ai", "documents/pt-newsroom.html"),
        ("pt.newsroom: the home page, as designed", "pt-newsroom/index.html"),
    ]),
    ("Site", [
        ("The network: sibling boundaries", "network/index.html"),
        ("Documents &amp; sources", "documents/index.html"),
        ("Comms: tasks &amp; requests", "admin/comms.html"),
        ("Release history", "admin/versions.html"),
        ("Where we lose", "about/participant.html"),
        ("llms.txt", "llms.txt"),
    ]),
]

BLURB = ("News is failing not because there is too little information but because "
         "there is no walkable chain from a claim to its evidence, no way for a "
         "correction to reach what it disproved, and no way to pay the person who "
         "did the original work. Part of the "
         "<a href=\"https://sgit.ai\" style=\"display:inline;padding:0\"><b>sgit.ai</b></a> "
         "network. All content CC BY 4.0 unless a page states otherwise.")
PARTNOTE = ('&#9888; Participant disclosure: published by the sgit project, which is '
            'building the stack this site argues for. '
            '<a href="{up}about/participant.html" style="display:inline;padding:0">'
            'Read the disclosure</a>.')
PARTNOTE_SELF = '&#9888; Participant disclosure: published by the sgit project. You are on the disclosure page.'
NETLINE = ('<a href="https://sgit.ai"><b>&#8593; sgit.ai</b></a> &middot; '
           '<a href="https://graphs.sgit.ai">&#8593; graphs.sgit.ai</a> &middot; '
           '<a href="https://pki.sgit.ai">&#8593; pki.sgit.ai</a> &middot; '
           '<a href="https://nhi.sgit.ai">&#8593; nhi.sgit.ai</a> &middot; '
           '<a href="https://sg-sentinel.sgit.ai">&#8593; sg-sentinel.sgit.ai</a> &middot; '
           '<a href="https://docs.diniscruz.ai">&#8593; docs.diniscruz.ai</a> &mdash; the prior art')


def nav_html(rel, up):
    groups = []
    for label, own, subs, prefixes in NAV:
        active = rel == own or any(rel.startswith(pre) for pre in prefixes)
        links = "\n".join(
            f'      <a class="sl{" here" if href == rel else ""}" href="{up}{href}">{text}</a>'
            for text, href in subs)
        groups.append(
            f'    <div class="ni ni-has">\n'
            f'      <a class="nl{" here" if active else ""}" href="{up}{own}">{label}'
            f'<span class="caret">&#9662;</span></a>\n'
            f'      <div class="sub">\n{links}\n      </div>\n'
            f'    </div>')
    rows = "\n".join(groups)
    return (f'<nav class="site"><div class="row">\n'
            f'  <a class="brand" href="{up}index.html">newsroom<span>.sgit.ai</span></a>\n'
            f'  <a class="parent" href="{PARENT}" title="{PARENT_TITLE}">&#8593; part of <b>sgit.ai</b></a>\n'
            f'  <span class="stage-pill">design, not built</span>\n'
            f'  <a class="ver" href="{up}admin/versions.html" title="Site release history">{VERSION}</a>\n'
            f'  <button class="nav-toggle" type="button" aria-expanded="false" aria-label="Menu">Menu</button>\n'
            f'  <div class="nav-items">\n{rows}\n  </div>\n'
            f'  <a class="gh" href="{GH}">&#9733; GitHub</a>\n'
            f'  <script src="{up}assets/nav.js" defer></script>\n'
            f'</div></nav>')


def footer_html(rel, up):
    partnote = PARTNOTE_SELF if rel == "about/participant.html" else PARTNOTE.format(up=up)
    md_twin  = f' &middot; <a href="{up}index.md">this page as markdown</a>' if rel == "index.html" else ""
    cols = "\n".join(
        "  <div>\n"
        f"    <h4>{head}</h4>\n"
        + "\n".join(f'    <a href="{l if l.startswith("http") else up + l}">{t}</a>' for t, l in links)
        + "\n  </div>"
        for head, links in FOOTER)
    return (f'<footer class="site"><div class="cols">\n'
            f'  <div>\n'
            f'    <div class="brandline">newsroom<span>.sgit.ai</span></div>\n'
            f'    <p>{BLURB}</p>\n'
            f'    <p class="netline">{NETLINE}</p>\n'
            f'    <p class="partnote">{partnote}</p>\n'
            f'    <p class="verline">site <a href="{up}admin/versions.html">{VERSION}</a> &middot; '
            f'<a href="{up}admin/index.html">engineering</a>{md_twin}</p>\n'
            f'  </div>\n{cols}\n</div></footer>')


def stamp_text_twins():
    """The version also appears in llms.txt and index.md, and validate.js enforces that
    it agrees. Own it here rather than hand-editing it every release."""
    out = []
    llms = ROOT / "llms.txt"
    if llms.exists():
        t = llms.read_text()
        t2, n = re.subn(r"Site version: v\d+\.\d+\.\d+", f"Site version: {VERSION}", t, count=1)
        if n and t2 != t:
            llms.write_text(t2)
            out.append("llms.txt")
    md = ROOT / "index.md"
    if md.exists():
        # index.md is markdown, so the separator is a literal U+00B7, not an HTML entity.
        # Getting that wrong makes this a silent no-op and the version stamp never lands;
        # the mismatch below is reported rather than swallowed for exactly that reason.
        t = md.read_text()
        t2, n = re.subn(r"\u00b7 site v\d+\.\d+\.\d+ \u00b7", f"\u00b7 site {VERSION} \u00b7", t, count=1)
        if n and t2 != t:
            md.write_text(t2)
            out.append("index.md")
    return out


def main():
    changed = []
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        rel  = path.relative_to(ROOT).as_posix()
        up   = "../" * (len(path.relative_to(ROOT).parts) - 1)
        text = path.read_text()
        before = text
        text, n_nav  = re.subn(r'<nav class="site">.*?</nav>', lambda _: nav_html(rel, up),
                               text, count=1, flags=re.S)
        text, n_foot = re.subn(r'<footer class="site">.*?</footer>', lambda _: footer_html(rel, up),
                               text, count=1, flags=re.S)
        if not n_nav or not n_foot:
            missing = " and ".join(x for x in (("nav" if not n_nav else ""),
                                               ("footer" if not n_foot else "")) if x)
            print(f"  ! {rel}: missing {missing} block", file=sys.stderr)
        if text != before:
            path.write_text(text)
            changed.append(rel)
    changed += stamp_text_twins()
    print(f"chrome: {VERSION} applied — {len(changed)} file(s) updated")
    for c in changed:
        print(f"  · {c}")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.stdout = None

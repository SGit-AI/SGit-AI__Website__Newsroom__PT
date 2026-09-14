#!/usr/bin/env python3
"""pt-newsroom/build/build.py — renders the chosen home-page design for pt.newsroom.sgit.ai as
a page on this site, from the design sources in pt-newsroom/design/.

    python3 pt-newsroom/build/build.py && python3 admin/build/chrome.py && node admin/build/validate.js

The sources are the artboards drawn on 13 September 2026 (Main.dc = 1440px, MainPhone.dc =
390px), kept verbatim with a `.dc` extension so the site validator does not treat them as
pages, plus the three directions that were drawn the same day and not chosen (DirectionB, C,
D) and the canvas layout with its notes (canvas.json). This script takes each artboard's
stylesheet and markup, scopes the stylesheet under a per-artboard class so it cannot restyle
the site chrome or another artboard, swaps the Google Fonts links for the vendored faces in
assets/fonts.css, and writes two pages: index.html (the chosen design, desktop and phone) and
directions.html (all five artboards, each with the motivation and trade-off written on the
canvas). Nothing in any design is edited here: a change to a design is a change to its .dc file.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEC = ROOT / "pt-newsroom"
HOST = "https://" + (ROOT / "CNAME").read_text().strip()


def parse(dc):
    s = dc.read_text(encoding="utf-8")
    style = re.search(r"<helmet>(.*?)</helmet>", s, re.S).group(1)
    css = "\n".join(re.findall(r"<style>(.*?)</style>", style, re.S))
    body = re.search(r"</helmet>\s*(.*?)\s*</x-dc>", s, re.S).group(1)
    return css, body


def scope(css, prefix):
    """Prefix every selector with `prefix`; `body` becomes the prefix itself."""
    out = []
    for block in re.split(r"(?<=\})", css):
        block = block.strip()
        if not block or "{" not in block:
            continue
        sel, rest = block.split("{", 1)
        sels = []
        for one in sel.split(","):
            one = one.strip()
            if not one:
                continue
            sels.append(prefix if one == "body" else f"{prefix} {one}")
        out.append(", ".join(sels) + "{" + rest)
    return "\n".join(out)


SHELL_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title} &middot; newsroom.sgit.ai</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="newsroom.sgit.ai">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="../assets/site.css">
<link rel="stylesheet" href="../assets/fonts.css">
<style>
{css}
</style>
</head>
<body>

<nav class="site"><div class="row"></div></nav>
"""

FRAME_CSS = """
.mockwrap{max-width:min(1560px,97vw);margin:0 auto;padding:0 1.1rem}
.mockframe{overflow-x:auto;border:1px solid var(--line2);border-radius:6px;background:#f7f4ec;box-shadow:var(--shadow);width:max-content;max-width:100%}
.mockframe.phone{width:390px;max-width:100%;margin:0}
.mocklabel{font-family:var(--mono);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);margin:1.6rem 0 .5rem}
.mocknote{max-width:960px;font-size:.9rem;color:var(--dim);line-height:1.6;margin:0 0 .6rem;white-space:pre-line}
.mocknote b{color:#101114}
"""


def shell(rel, title, desc, css, body):
    canonical = f"{HOST}/pt-newsroom/{rel}"
    return (SHELL_HEAD.format(title=html.escape(title, quote=True), desc=html.escape(desc, quote=True),
                              canonical=canonical, css=css) + body + "\n<footer class=\"site\"><div class=\"cols\"></div></footer>\n</body>\n</html>\n")


def frame(cls, label, body, phone=False):
    return (f'  <p class="mocklabel">{label}</p>\n'
            f'  <div class="mockframe {"phone " if phone else ""}{cls}">\n{body}\n  </div>\n')


def main():
    boards = {}
    for name in ("Main", "MainPhone", "DirectionB", "DirectionC", "DirectionD"):
        css, body = parse(SEC / "design" / f"{name}.dc")
        cls = "mock-" + name.lower()
        boards[name] = {"css": scope(css, "." + cls), "body": body, "cls": cls}
    canvas = json.loads((SEC / "design" / "canvas.json").read_text(encoding="utf-8"))
    notes = {n["id"]: n["text"] for n in canvas.get("annotations", [])}
    titles = {a["file"]: a.get("title", a["file"]) for a in canvas["artboards"]}

    # --- index.html: the chosen design ------------------------------------------
    css = boards["Main"]["css"] + "\n" + boards["MainPhone"]["css"] + FRAME_CSS
    body = f"""
<main class="doc" style="max-width:min(1560px,97vw)">
<div class="crumb"><a href="../index.html">newsroom.sgit.ai</a> / pt-newsroom</div>
<h1>pt.newsroom.sgit.ai: the home page, as designed</h1>
<p class="lead">The site does not exist yet. This is its front page as chosen on 13 September 2026 &mdash;
a classic broadsheet, natively Portuguese, drawn with <a href="../portugal/index.html">the Portugal
section&rsquo;s</a> real data of that day &mdash; rendered here as a page so the agent that builds the site,
and anyone else, can see it at full size rather than as a picture. The brief that commissions the site is
<a href="../documents/pt-newsroom.html">here</a>; its section 16 records the design system. The three
directions drawn the same day and not chosen are <a href="directions.html">archived beside it</a>.</p>

<div class="note"><p style="margin-top:0"><b>What this page is, and is not.</b> It is a rendering of the design
sources (<code>pt-newsroom/design/Main.dc</code> and <code>MainPhone.dc</code>) with nothing edited. The
copy on it &mdash; the three stories, the 60&rarr;64 speaker diff, the seven press pages, the programme &mdash;
was true on 13 September and is not updated; take the structure, not the numbers. The links inside the
mock-up go nowhere on purpose. The two typefaces, Newsreader and IBM Plex Mono, are vendored under
<code>assets/fonts/</code> (SIL Open Font Licence) rather than fetched from a third party, for the same
reason the rest of the site vendors its code.</p></div>
</main>

<div class="mockwrap">
{frame(boards["Main"]["cls"], "Desktop &middot; 1440px &middot; scrolls sideways on a narrower screen", boards["Main"]["body"])}
{frame(boards["MainPhone"]["cls"], "Phone &middot; 390px", boards["MainPhone"]["body"], phone=True)}
</div>

<main class="doc" style="max-width:min(1560px,97vw)">
<div class="agent"><h4>For an agent</h4><p>This page renders the chosen home-page design for pt.newsroom.sgit.ai,
a site that does not exist yet. The design sources are <code>/pt-newsroom/design/Main.dc</code> and
<code>/pt-newsroom/design/MainPhone.dc</code> (plain HTML artboards); the design system &mdash; colours,
faces, the order of the page, what is deliberately not on it &mdash; is section 16 of
<code>/documents/pt-newsroom.html</code>, the commissioning brief. The three unchosen directions are at
<code>/pt-newsroom/directions.html</code> with their sources. The copy on the mock-up is the Portugal
section&rsquo;s data of 13 September 2026 and is not maintained: read <code>/portugal/data/</code> for
current facts. Nothing here is a claim about the world; it is a picture of a page.</p></div>
</main>
"""
    (SEC / "index.html").write_text(shell(
        "index.html", "pt.newsroom.sgit.ai: the home page, as designed",
        "The chosen home-page design for the Portuguese-language newsroom, rendered as a page: a broadsheet drawn with the Portugal section's real data of 13 September 2026, at 1440px and at 390px.",
        css, body), encoding="utf-8")

    # --- directions.html: all five artboards, the archive ------------------------
    order = [("Main", "note-a", "Chosen"), ("MainPhone", "note-phone", "Chosen &middot; phone"),
             ("DirectionB", "note-b", "Not chosen"), ("DirectionC", "note-c", "Not chosen"), ("DirectionD", "note-d", "Not chosen")]
    css = "\n".join(b["css"] for b in boards.values()) + FRAME_CSS
    sections = []
    for name, note_id, status in order:
        t = html.escape(titles.get(f"{name}.dc.html", name))
        note = html.escape(notes.get(note_id, ""))
        width = next(a["w"] for a in canvas["artboards"] if a["file"] == f"{name}.dc.html")
        sections.append(
            f'<main class="doc" style="max-width:min(1560px,97vw)"><h2 id="{name.lower()}">{t} '
            f'<span class="small dim" style="font-family:var(--mono);font-weight:400">&middot; {status} &middot; {width}px &middot; '
            f'<a href="design/{name}.dc">source</a></span></h2>'
            f'<p class="mocknote">{note}</p></main>\n<div class="mockwrap">\n'
            + frame(boards[name]["cls"], f"{width}px" + (" &middot; scrolls sideways on a narrower screen" if width > 390 else ""),
                    boards[name]["body"], phone=(width == 390))
            + "</div>\n")
    body = f"""
<main class="doc" style="max-width:min(1560px,97vw)">
<div class="crumb"><a href="../index.html">newsroom.sgit.ai</a> / <a href="index.html">pt-newsroom</a> / directions</div>
<h1>The four directions, 13 September 2026</h1>
<p class="lead">Four home pages were drawn for pt.newsroom.sgit.ai on the same day, from the same data, along
four different axes: a classic broadsheet, a dense capture-ordered ledger, a dark graph-first cover, and a
magazine with the claims underlined in the text. The editor of record chose the first. All four are kept
here, at full size, with the motivation and the trade-off that were written beside each on the canvas, so
that the choice can be re-read and the other three are not redrawn by accident.</p>
<div class="note"><p style="margin-top:0"><b>An archive, not a menu.</b> The chosen design is the one on
<a href="index.html">the home-page page</a> and in section 16 of <a href="../documents/pt-newsroom.html">the
commissioning brief</a>. The other three are here for reference and are not to be built. Every artboard
is rendered from its source file, unedited; the seven typefaces the four designs specify are vendored under
<code>assets/fonts/</code> (all SIL Open Font Licence). The copy is the Portugal section&rsquo;s data of
13 September and is not maintained; the links inside the mock-ups go nowhere.</p></div>
</main>
{"".join(sections)}
<main class="doc" style="max-width:min(1560px,97vw)">
<div class="agent"><h4>For an agent</h4><p>An archive of the four home-page directions drawn for
pt.newsroom.sgit.ai on 13 September 2026, each rendered from its source under
<code>/pt-newsroom/design/</code> (Main, MainPhone, DirectionB, DirectionC, DirectionD, plus canvas.json with
the layout and the notes). Only <b>Main</b> was chosen; the design system for it is section 16 of
<code>/documents/pt-newsroom.html</code>. Do not build from B, C or D. Nothing here is a claim about the
world.</p></div>
</main>
"""
    (SEC / "directions.html").write_text(shell(
        "directions.html", "pt.newsroom.sgit.ai: the four directions",
        "All four home-page directions drawn for the Portuguese-language newsroom on 13 September 2026, rendered at full size with the motivation and trade-off of each. One was chosen; three are archived.",
        css, body), encoding="utf-8")
    print(f"pt-newsroom: index.html and directions.html written from {len(boards)} artboards")


if __name__ == "__main__":
    main()

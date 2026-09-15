#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — renders admin/versions.html from markdown and JSON.

    python3 build/versoes.py      # after chrome.py; reads admin/versions.json

WHY THIS EXISTS. The release history used to BE an HTML file, with every release note written as
prose between `<td>` tags. The editor's objection is the right one: **text should not live inside
HTML.** A release note is a document. A document that can only be read as markup is a document with
extra steps — you cannot diff it usefully, you cannot read it in a terminal, and every edit means
writing `<br><br>` where a blank line was meant.

So the note is `admin/versions/<version>.md`, the index is `admin/versions.json`, and this file
renders the page from the two. It is the same shape the rest of the site already uses: an article
is `artigo.md` plus `artigo.json` rendered to `index.html`, and this page was the last hand-written
exception to that rule.

It also removes a whole class of failure that cost this repository a release. When two sessions
edited the release table at once, the merge left fifteen rows and three `<tr>` tags — a broken table
that still looked like a table. Markdown files do not merge into invalid markup: the worst a
conflict does is leave two paragraphs where one belonged, and a human can see it.
"""
import json
from pathlib import Path

import paginas as P

ROOT = Path(__file__).resolve().parents[1]
VERSAO = (ROOT / "admin" / "build" / "version.txt").read_text(encoding="utf-8").strip()


def md_para_html(md):
    """Small on purpose: a release note is prose with bold, code, links and paragraphs.

    Reuses `paginas.inline` for the inline marks, so a note formats exactly like the site's prose
    and there is one renderer rather than two."""
    blocos = []
    for par in [p.strip() for p in md.split("\n\n") if p.strip()]:
        texto = " ".join(par.split("\n"))
        if texto.startswith("*") and texto.endswith("*") and "**" not in texto[:2]:
            blocos.append(f'<p class="xs" style="color:var(--sec-2)">'
                          f'{P.inline(texto.strip("*"), "../")}</p>')
        else:
            blocos.append(f'<p class="sm">{P.inline(texto, "../")}</p>')
    return "".join(blocos)


def main():
    ficheiro = ROOT / "admin" / "versions.json"
    idx = json.loads(ficheiro.read_text(encoding="utf-8"))
    e = P.e

    # COUNTED, NOT WRITTEN. `contagem` was a hand-maintained number, and it drifted the first time
    # two sessions each added a release note: sixteen entries, a field saying fifteen, and nothing
    # failing. A count that can disagree with the thing it counts is worse than no count, because
    # it reads as a check. It is recomputed here, and the file is rewritten when it disagrees, so
    # the number is a consequence of the list rather than a claim about it.
    if idx.get("contagem") != len(idx["versoes"]):
        idx["contagem"] = len(idx["versoes"])
        ficheiro.write_text(json.dumps(idx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    linhas = []
    for v in idx["versoes"]:
        f = ROOT / v["ficheiro"]
        if not f.exists():
            continue
        linhas.append(
            f'<tr id="{e(v["versao"])}">'
            f'<td class="mono"><span class="vnum">{e(v["versao"])}</span></td>'
            f'<td class="mono">{e(v["data"])}</td>'
            f'<td class="sm">{md_para_html(f.read_text(encoding="utf-8"))}'
            f'<p class="xs" style="padding-top:10px">'
            f'<a href="../{e(v["ficheiro"])}">{e(v["ficheiro"])}</a> — this note as markdown, '
            f'which is what it is.</p></td></tr>')

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Release history · pt.newsroom.sgit.ai</title>
<meta name="description" content="What changed in each version of this site, and why.">
<link rel="canonical" href="https://{P.HOST}/admin/versions.html">
<meta property="og:url" content="https://{P.HOST}/admin/versions.html">
<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../assets/fonts.css">
<link rel="stylesheet" href="../assets/site.css">
</head>
<body>
<div class="folha">

<div class="datalinha">
  <div>pt.newsroom.sgit.ai · administration</div>
  <div><a href="../">Back to the paper</a> · <a href="../backoffice/">back office</a> ·
       <a href="../backoffice/guidance.html">guidance</a></div>
  <div><a class="ver" href="#{VERSAO}">{VERSAO}</a></div>
</div>

<div class="aviso-bloco" style="border-left-color:var(--acento)">
<p class="sm"><b>This page is generated, and in English.</b> Each release note is a markdown file in
<code>admin/versions/</code>; <code>admin/versions.json</code> is the index; this page is rendered
from the two by <code>build/versoes.py</code>. Text does not live inside HTML here — a release note
is a document, and a document that can only be read as markup is a document with extra steps. It is
in English because its audience operates the newsroom rather than reading the paper; the rule and
its exceptions are in <a href="../backoffice/guidance.html">the guidance</a>.</p></div>

<div class="rule" style="padding:26px 0 8px"><div class="sect">Releases</div></div>
<h1 class="h-2" style="max-width:26em">Every push to the release branch is a minor version, and
carries a note here saying what changed and why.</h1>
<p class="std" style="max-width:29em;padding:14px 0 18px">The number lives in
<code>admin/build/version.txt</code> and is bumped exactly once per release. The commit subject
repeats it, the badge appears on every page, and CI checks the three agree before tagging and
deploying. A red validate is not a release.</p>

<div class="rolar">
<table>
<thead><tr><th style="width:90px">Version</th><th style="width:110px">Date</th>
  <th>What changed, and why</th></tr></thead>
<tbody>
{"".join(linhas)}
</tbody>
</table>
</div>

<div class="agent">
<b>For an agent.</b> The release history is data: <a href="versions.json">versions.json</a> is the
index and each note is a markdown file beside it. This page is rendered from them by
<code>build/versoes.py</code>, and <code>admin/build/validate.js</code> checks the table has a row
for the version in <code>admin/build/version.txt</code>, with no duplicates. Version
<a class="ver" href="#{VERSAO}">{VERSAO}</a>.
</div>

</div>
</body>
</html>
"""
    (ROOT / "admin" / "versions.html").write_text(html, encoding="utf-8")
    print(f"versions: {len(linhas)} release notes rendered from markdown, {VERSAO}")


if __name__ == "__main__":
    main()

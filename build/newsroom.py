#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the back office. Operations console, in English.

    python3 build/newsroom.py

WHY THIS ONE AREA IS IN ENGLISH, when CLAUDE.md says everything a reader sees is Portuguese.

The rule in CLAUDE.md is about the PUBLICATION: "code and comments are in English; everything the
reader sees is in European Portuguese". The back office is not the publication — it is the console
the editor of record and the agents work in, and its audience is whoever is operating the
newsroom, who in this estate reads English. The editor asked for it in English deliberately.

Two things follow, and both are enforced rather than promised:

1. **Nothing here is reader-facing.** `/newsroom/` is not in the masthead, not in a section, and
   carries a banner saying what it is. It is linked from the footer as machinery, the way
   `/admin/versions.html` is.
2. **It publishes no claim.** Every number on these pages is a count of files in this repository.
   The back office reports on the newsroom; it never reports on the world. A page that made a
   claim about Portugal in English would be the language rule being broken for real, and gate 16
   fails the build if a back-office page ever cites a frozen source as evidence for something.

The line in CLAUDE.md that carves out this exception has NOT been edited by this session: CLAUDE.md
is the rules file, it is in the deny list of .claude/settings.json on purpose, and changing the
rules to match the code is exactly backwards. It is flagged to the editor instead.

WHAT IS HERE

  index.html    the console: pipeline, agents, articles, deliveries, sections, gates
  docs.html     every markdown document in this repository, indexed
  DELETED, in v0.17.0: viewer.html. It existed only to forward to docs.html, and a page whose
  whole content is "this moved" is the redirect stub the editor asked this site not to accumulate.
  The rule it protected — one implementation of document rendering — is unchanged: docs.html is
  still the ONE reader. This site has no users and no SEO yet, so an address may simply stop
  existing; when that stops being true, a rename becomes a decision with a cost.
"""
import json
import re
import subprocess
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paginas import utilitarios  # noqa: E402  the ONE utility run, shared

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
HOST = "pt.newsroom.sgit.ai"
VERSAO = (ROOT / "admin" / "build" / "version.txt").read_text(encoding="utf-8").strip()
GH = "https://github.com/SGit-AI/SGit-AI__Website__Newsroom__PT"

# The estate this site is part of. Linked once, from here, because the back office is where
# somebody operating the newsroom would look for them — and because content exists once: the
# argument lives on the parent site and is not restated here.
ESTATE = [
    ("newsroom.sgit.ai", "https://newsroom.sgit.ai",
     "The parent publication and the argument this site is an instance of. The commissioning "
     "brief for pt.newsroom lives there, not here."),
    ("newsroom.sgit.ai/portugal/", "https://newsroom.sgit.ai/portugal/index.html",
     "Where this method was proven before it was copied: the ingestion path, the gates, the "
     "biography posture and the notice all come from there."),
    ("newsroom.sgit.ai/pt-newsroom/", "https://newsroom.sgit.ai/pt-newsroom/index.html",
     "The front-page design this site builds, rendered at full size from its own sources."),
    ("sgit.ai", "https://sgit.ai",
     "The platform: the vault layer and the shipped CLI. Research deliveries arrive as sgit "
     "vaults, and a read key is the only credential that may be recorded."),
    ("coding.sgit.ai", "https://coding.sgit.ai",
     "How the code in this repository is meant to be written and reviewed."),
    ("graphs.sgit.ai", "https://graphs.sgit.ai",
     "The published grammar this site's ontology obeys: every edge a verb with a distinct named "
     "inverse, and a path that reads aloud."),
]


def e(x):
    import html
    return html.escape(str(x if x is not None else ""), quote=True)


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


# THE RAIL — the console's navigation, grouped, instead of eleven flat links.
#
# The design review measured the old nav as "eleven flat navigation items … one undifferentiated
# run at 12px mono. No grouping, so `console` (the dashboard you return to) has the same rank as
# `versions` (a changelog). No counts, so nothing tells you `mail` has an unread message for you."
# All three complaints are answered here: three groups in the order an operator needs them, and a
# count on the items that can be behind.
#
# The LABELS are English because the console's furniture is architecture. The URLs are still
# Portuguese. The proposal asks for console.html / mail.html / board.html as well, and that is a
# rename of addresses already published in llms.txt and the sitemap, so it needs redirects and it
# is the editor's call — open question 2 in the vault, recorded on /newsroom/design.html.
RAIL = [
    ("Operate", [
        ("newsroom/", "Console", "fila"),
        ("newsroom/mail.html", "Mail", "correio"),
        ("newsroom/board.html", "Board", "quadro"),
        ("newsroom/bridges.html", "Bridges", None),
    ]),
    ("Understand", [
        ("newsroom/team.html", "Team", None),
        ("newsroom/agents.html", "Agent activity", None),
        ("newsroom/design.html", "Design review", None),
    ]),
    ("Reference", [
        ("newsroom/guidance.html", "Guidance", None),
        ("newsroom/interviews.html", "Interviews", None),
        ("newsroom/docs.html", "Documents", None),
        ("admin/versions.html", "Versions", None),
        ("", "\u2197 The paper", None),
    ]),
]


def fila():
    """WHAT IS WAITING ON THE EDITOR OF RECORD — derived, never typed.

    This is the question the console exists to answer, and before v0.14.0 the answer was a single
    cell in row 6 of the first table, reading `waiting on a human` in the BASE chip style, so it
    looked exactly like the five `running` chips above it. Three other pages each held a piece of
    the same answer — the mail knew he had an unread message, the board knew an issue was chipped
    `waiting on dinis.humano`, the pipeline knew stage 6 was stopped — and the console index showed
    none of it.

    Four sources, one rule: an item belongs here only if NO agent can move it. Anything an agent
    could still do is not waiting on a human, and putting it here would make the number stop
    meaning anything.

      1. cards the editor opened, on their own board lane
      2. cards on ANOTHER agent's lane whose `bloqueado_por` is the editor
      3. paper issues the formula assigns to the editor (verificado, congelado)
      4. mail sitting in the editor's inbox

    There is no count attribute anywhere: the number in the rail and the number in the queue are
    both `len()` of this list, so they cannot disagree. A number typed beside a list it claims to
    describe is the failure this whole publication exists to report.
    """
    q = carregar("quadro.json")
    itens = []
    por_agente = q.get("por_agente", {})
    editor = "dinis.humano"
    alias_do = {a: v.get("alias", a) for a, v in por_agente.items()}

    def uma_linha(texto, n=150):
        """One line of why, not the whole card.

        A queue is scanned, and the card's own `resumo` is three or four sentences written for
        somebody who has decided to do the work. Printed in full, thirteen of them made the queue
        4,000px tall — which is the same failure as the 70-word preamble, one screen further down.
        The file is one click away and it has all of it."""
        texto = " ".join((texto or "").split())
        if len(texto) <= n:
            return texto
        corte = texto[:n].rsplit(" ", 1)[0]
        return corte + "\u2026"

    def cartao(c, porque):
        return {
            "id": Path(c["ficheiro"]).stem,
            "title": c.get("titulo") or Path(c["ficheiro"]).stem,
            "status": "needs-you",
            "since": f'opened {str(c.get("aberto", ""))[:10]}' if c.get("aberto") else "",
            "where": c["ficheiro"],
            "why": uma_linha(porque),
            # ONE action, not two. The second was "Write to the newsroom" on every item, which on
            # a queue of thirteen is thirteen identical buttons doing the same navigation — and a
            # button repeated until it is furniture has stopped being an affordance. Writing to the
            # newsroom is a rail item; reading the file is what is specific to this row.
            "actions": [{"id": "read", "label": "Read the file", "writes": None}],
        }

    # 1 — the editor's own lane. `abertos` is work they opened; `bloqueados` is work they cannot
    #     finish, and both are theirs alone because nobody else may write in their folder.
    meu = por_agente.get(editor, {})
    for coluna in ("bloqueados", "abertos"):
        for c in meu.get("colunas", {}).get(coluna, []):
            porque = c.get("resumo") or ""
            if coluna == "bloqueados" and c.get("bloqueado_por", "\u2014") != "\u2014":
                porque = f'Blocked on {c["bloqueado_por"]}. ' + porque
            itens.append(cartao(c, porque))

    # 2 — an agent stopped because only the editor may do the next thing. This is the case the old
    #     console hid best: the agent's own page said `waiting on dinis.humano` and the console
    #     index never mentioned it.
    for aid, v in por_agente.items():
        if aid == editor:
            continue
        for c in v.get("colunas", {}).get("bloqueados", []):
            if c.get("bloqueado_por") != editor:
                continue
            it = cartao(c, f'{alias_do.get(aid, aid)} cannot move this: it is blocked on you. '
                        + uma_linha(c.get("resumo"), 110))
            # This is the one case where the action is not "read": an agent is stopped and the
            # thing that unblocks it is a message from the editor. The button names the folder the
            # reply goes in, so an operator who does not trust it can write the file by hand.
            it["actions"] = [
                {"id": "note", "label": f"Answer {alias_do.get(aid, aid)}",
                 "writes": f"redacao/correio/{editor}/saida/"},
            ]
            itens.append(it)

    # 3 — a paper issue the formula puts on the editor. Who owns an issue is never written by hand;
    #     it falls out of the issue's state, which is why the board cannot disagree with the files.
    porques = q.get("formula", {}).get("porque", {})
    for i in meu.get("issues_do_jornal", []):
        estado = i.get("estado", "")
        itens.append({
            "id": f'issue-{i.get("id", "")}',
            "title": f'Publish decision \u00b7 paper issue {i.get("id", "")}',
            "status": "needs-you",
            "since": f'state {estado}' if estado else "",
            "where": i.get("ficheiro") or f'dados/historias.json \u2192 {i.get("id", "")}',
            "why": uma_linha(porques.get(estado, "")),
            # The publication's own words, in the publication's own face, tagged with its language
            # so the operator can see at a glance that it is a quotation and not console copy.
            "quote": i.get("titulo") or "",
            "quoteLang": "PT",
            "actions": [{"id": "read", "label": "Read it first", "writes": None}],
        })

    # 4 — mail in the editor's inbox. A message's state is the folder it sits in, so a message in
    #     entrada/ is by definition unhandled and by definition theirs.
    for m in meu.get("entrada", []):
        itens.append({
            "id": Path(m["ficheiro"]).stem,
            "title": f'Mail from {m.get("de_alias", m.get("de", ""))} \u00b7 {m.get("assunto", "")}',
            "status": "needs-you",
            "since": f'sent {str(m.get("quando", ""))[:10]}' if m.get("quando") else "",
            "where": m["ficheiro"],
            "why": ("It is in entrada/, which is what unhandled means in this protocol. Moving it "
                    "to tratado/ is the read receipt, and only its owner may move it."),
            "actions": [{"id": "mail", "label": "Open the thread", "writes": None}],
        })
    return itens


def contagens_do_rail():
    """The three numbers the rail carries, from the same files the pages read."""
    q, c = carregar("quadro.json"), carregar("correio.json")
    qa = q.get("contagens", {})
    return {
        "fila": len(fila()),
        "correio": len(q.get("por_agente", {}).get("dinis.humano", {}).get("entrada", [])) or None,
        "quadro": qa.get("cartoes"),
        "_mensagens": c.get("contagem", 0),
    }


def rail(rel, raiz):
    """The rail, with the page you are on marked with aria-current.

    Weight alone marked the current page before, which is a styling convention and not something
    a screen reader or an outline can read. `aria-current="page"` is the thing that actually says
    where you are; the border and the ground follow from it in CSS."""
    n = contagens_do_rail()
    fora = []
    for grupo, itens in RAIL:
        linhas = []
        for caminho, rotulo, chave in itens:
            aqui = caminho == rel or (caminho == "newsroom/" and rel == "newsroom/index.html")
            marca = ' aria-current="page"' if aqui else ""
            valor = n.get(chave) if chave else None
            # A zero is not a badge. A count that is always there stops being a signal, and the
            # whole reason the rail carries counts is to say there IS something behind an item.
            conta = ""
            if valor:
                classe = "count r1" if chave in ("fila", "correio") else "count"
                ident = ' id="rail-fila"' if chave == "fila" else ""
                conta = f'<span class="{classe}"{ident}>{valor}</span>'
            linhas.append(f'<a class="nav" href="{raiz}{caminho}"{marca}>{rotulo}{conta}</a>')
        fora.append(f'<div class="rail__group"><h3>{grupo}</h3>{"".join(linhas)}</div>')
    # THE MARKER, WHICH IS A RULE AND NOT A PREAMBLE.
    #
    # Gate 19 requires every back-office page to say it is not the publication, and the gate is
    # right: this whole area is in English by the editor's decision, and the condition of that
    # exception is that a reader who lands here can SEE it is not the paper. So it cannot simply be
    # deleted because a design review found the long version repetitive.
    #
    # Both things are true at once here. The 70-word explanation was ~300px of identical prose
    # above every screen — which trains the operator to scroll past the top of every page, exactly
    # where the urgent things live — and it is now on guidance.html and nowhere else. What every
    # page carries is one sentence, in the rail rather than above the content, so it is permanently
    # visible without ever being in the way. Gate 19 is unchanged and still finds its string.
    marca = (f'<p class="rail__note">This is the operations console, not the publication. '
             f'English on purpose \u2014 <a href="{raiz}newsroom/guidance.html">why</a>.</p>')
    return (f'<nav class="rail" aria-label="Back office">'
            f'<a class="rail__brand" href="{raiz}newsroom/">'
            f'<b>pt.newsroom</b><span>back office \u00b7 {VERSAO}</span></a>'
            + marca + "".join(fora) + '</nav>')


# THE CONSOLE'S TWO WIRES. pt-queue is deliberately inert — it emits an event and does nothing —
# because a component that decided what a button meant would decide it the same way on every site
# that used it. The page decides.
#
# The review's open question 1 is "do the buttons act, or link?" On a static site they cannot
# write a file: there is no server to write it. So the honest answer, and the one implemented here,
# is that every button GOES TO THE PLACE WHERE THE WRITE HAPPENS and names the file on the way —
# the document browser for a file to read, the mail page for a thread, the bridge page for a
# message to the newsroom. Nothing here claims to have written anything.
FILA_JS = """
<script>
(function () {
    /* The rail badge takes its number from the queue rather than holding one of its own, so the
       two cannot drift. The build wrote a number into the badge as well, for the eight pages that
       have no queue on them; where both exist this overwrites it with the same count. */
    document.addEventListener('pt-queue:counted', function (ev) {
        var badge = document.getElementById('rail-fila')
        if (!badge) return
        var n = ev.detail && ev.detail.count
        if (!n) { badge.remove(); return }
        badge.textContent = String(n)
    })

    /* Where each action goes. A path is data from this repository's own files, so it is put in a
       fragment and never interpolated into markup. */
    function destino(action, where) {
        if (action === 'note') return 'bridges.html'
        if (!where) return 'docs.html'
        if (/\.eml$/.test(where)) return 'mail.html'
        if (/\.md$/.test(where)) return 'docs.html#' + where
        return 'docs.html'
    }

    document.addEventListener('pt-queue:action', function (ev) {
        var d = ev.detail || {}
        var item = (JSON.parse(document.querySelector('pt-queue').getAttribute('items') || '[]')
                    .filter(function (x) { return x.id === d.id })[0]) || {}
        location.href = destino(d.action, item.where)
    })
})()
</script>
"""


# THE PREAMBLE, SAID ONCE. It used to open all nine pages verbatim — roughly 300px of identical
# prose above every screen, which trains the operator to scroll past the top of every page, which
# is exactly where the urgent things live. It also contradicted this project's own rule that
# content exists once. It is now on guidance.html and nowhere else.
PREAMBULO = """
<div class="aviso-bloco">
<p class="sm"><b>This is the operations console, not the publication.</b> It is in English on
purpose: its audience is whoever is operating the newsroom, not the reader of the paper. The
publication itself is natively Portuguese and nothing here is linked from the masthead. Every
number on these pages counts files in this repository \u2014 the back office reports on the newsroom
and never on the world, and a gate fails the build if a page here ever cites a frozen source as
evidence for a claim about Portugal.</p>
</div>
"""


def pagina(rel, titulo, descricao, corpo, extra_body="", resumo="", acoes="",
           preambulo=False, largo=False):
    """The console's one page shell.

    THE h1 NAMES THE PLACE. The review's finding was that five of the nine back-office pages had
    no heading at all and the whole back office had zero `h2` — section titles were `.sect` divs,
    which are styling and not structure, so nothing could outline these pages and no screen reader
    could navigate them. Where an `h1` did exist it was a sentence in the publication's voice:
    "What the newsroom has done, what it is waiting on, and who is allowed to do what." That
    describes a page; it does not label where you are standing. So `titulo` is the h1 and it is a
    noun, and the sentence it replaced is the `resumo` underneath it.

    TWO STYLESHEETS, ON PURPOSE. site.css is loaded first for the operator strip and for nothing
    else — the editor's instruction is that the strip must not move when you cross over from the
    paper, so it keeps the paper's rules and the paper's ground. console.css is loaded second and
    every rule below the strip is the console's. See the header of assets/console.css.
    """
    profundidade = rel.count("/")
    raiz = "../" * profundidade if profundidade else ""
    canonico = f"https://{HOST}/{rel}"
    cabeca = (f'<div class="page-head"><div><h1>{e(titulo)}</h1>'
              + (f'<p>{resumo}</p>' if resumo else "")
              + "</div>"
              + (f'<div class="head-actions">{acoes}</div>' if acoes else "")
              + "</div>")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)} · pt.newsroom back office</title>
<meta name="description" content="{e(descricao)}">
<meta name="robots" content="noindex">
<link rel="canonical" href="{canonico}">
<meta property="og:url" content="{canonico}">
<link rel="icon" href="{raiz}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{raiz}assets/fonts.css">
<link rel="stylesheet" href="{raiz}assets/site.css">
<link rel="stylesheet" href="{raiz}assets/console.css">
</head>
<body>

<div class="folha bo-strip">
{utilitarios(raiz, no_console=True)}
</div>

<div class="shell">
{rail(rel, raiz)}
<main class="main{' main--wide' if largo else ''}">

{cabeca}
{PREAMBULO if preambulo else ""}
{corpo}

<div class="agent">
<b>For an agent.</b> Generated by <code>build/newsroom.py</code> from the files in this
repository; nothing here is hand-written. The machine-readable index of the publication is at
<a href="{raiz}llms.txt">llms.txt</a>. Source: <a href="{GH}">{GH.split('//')[1]}</a> · file:
<code>{e(rel)}</code> · version <span class="ver">{VERSAO}</span>.
</div>

</main>
</div>
{extra_body}</body>
</html>
"""


def escrever(rel, texto):
    f = ROOT / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(texto, encoding="utf-8")
    return rel


# ------------------------------------------------------------------ the docs ---
CATEGORIAS = [
    ("docs/guidance/", "Guidance — read first",
     "The rules an agent working here follows: the language rule, the principles with the gate "
     "that enforces each one, and the checklist for before you change anything. A rule without a "
     "gate is decoration, so each one names its gate or says it has none."),
    ("agents/", "Agent mandates",
     "One folder per named agent, each with a ROLE.md and a MANDATE.md. More than one agent works "
     "on this site and they are not interchangeable: the role says what the work is, the name says "
     "whose mandate it is done under."),
    ("briefs/pack/", "Commissioning pack",
     "Cut from newsroom.sgit.ai v0.3.9. The brief this site was built from, the design, what to "
     "inherit, the operating model, the schedule and the research briefs. Where a copy and the "
     "original disagree, the original is right."),
    (".claude/skills/", "Agent skills",
     "What each kind of session is instructed to do. A skill is the difference between an agent "
     "that improvises and one that follows a published procedure."),
    ("redacao/", "Newsroom files",
     "Mail between departments, run records, editor decisions and delivery reviews. The "
     "communication layer is files, and this is it."),
    ("artigos/", "Articles",
     "The prose of each article, in its dated folder beside its claims and provenance."),
    ("seccoes/", "Section records",
     "What each of the eight sections covers, and what it can and cannot claim today."),
    ("", "Repository root",
     "The rules file, the readme, the licences."),
]


def documentos():
    """Every markdown file in the repository, with what it is and how big."""
    out = []
    for f in sorted(ROOT.rglob("*.md")):
        rel = f.relative_to(ROOT).as_posix()
        if rel.startswith(".git/") or "/node_modules/" in rel:
            continue
        texto = f.read_text(encoding="utf-8", errors="replace")
        titulo = next((l.lstrip("# ").strip() for l in texto.split("\n") if l.startswith("# ")), f.stem)
        cat = next((rot for pref, rot, _ in CATEGORIAS if pref and rel.startswith(pref)),
                   "Repository root")
        out.append({
            "caminho": rel, "titulo": titulo, "categoria": cat,
            "bytes": f.stat().st_size, "linhas": len(texto.split("\n")),
            "palavras": len(texto.split()),
        })
    return out


def pagina_docs(docs):
    """Two panes: the tree on the left, the document on the right, on white.

    The version this replaces was a list of links that threw the reader onto a separate page —
    they scrolled to read and lost the other documents doing it. Somebody reading a document set
    is navigating and reading at the same time, so the tree stays. All of it is `pt-doc-browser`:
    this page is a heading and a component."""
    corpo = f"""
<p class="std" style="max-width:46em;padding:14px 0 8px">{len(docs)} documents. The tree groups
them by the directory structure that already exists — <code>briefs/pack/</code> is one element,
not thirty rows — and the viewer reads each document's own bytes, the same file the build read, so
what is shown cannot drift from what was built.</p>
<p class="sm" style="max-width:46em;padding-bottom:18px">The commissioning pack is the largest
group and the one worth reading first: it is the brief this site was built from, kept whole rather
than summarised, because a summary of a brief is how a project quietly stops doing what it was
asked to do. References to the rest of the estate are at the foot of the tree.</p>
<pt-doc-browser site-root="../"></pt-doc-browser>
"""
    extra = ('<script src="../assets/vendor/marked.min.js"></script>'
             '<script type="module" '
             'src="../assets/components/pt-doc-browser/v1/v1.0/v1.0.0/pt-doc-browser.js"></script>')
    return pagina("newsroom/docs.html", "Documents",
                  "Every markdown document this site was built from, in a two-pane reader.",
                  corpo, extra_body=extra,
                  resumo="Every markdown document this site was built from, readable without "
                         "losing your place.")


# --------------------------------------------------------------- the console ---
def commits_recentes(n=12):
    try:
        r = subprocess.run(["git", "log", f"-{n}", "--format=%h\t%ad\t%an\t%s",
                            "--date=format:%Y-%m-%d %H:%M"],
                           cwd=ROOT, capture_output=True, text=True, timeout=20)
        return [l.split("\t", 3) for l in r.stdout.strip().split("\n") if l.count("\t") >= 3]
    except Exception:
        return []


GUIA = [
    ("index.md", "Start here",
     "The one-minute version, the reading order, and what not to build. Most tasks end at the "
     "third item on that list."),
    ("language.md", "The language rule",
     "One test decides every naming question: would a visitor read this string on the site? The "
     "most commonly broken rule here, including by the agent that wrote most of this pipeline."),
    ("principles.md", "The nine principles",
     "Each one names the gate that enforces it. The one principle with no gate says so in those "
     "words."),
    ("before-you-change.md", "Before you change anything",
     "The checklist: know who you are, read in order, find out who else is working here, check the "
     "tree is green before you touch it, build with build/tudo.py, record what you did."),
    ("concurrent-sessions.md", "More than one session at a time",
     "Three sessions work on this repository at once. What has actually collided between them, "
     "which gates now catch each one, and the order that avoids most of it. Includes the merge "
     "that succeeded and still deleted a release's work."),
]


def pagina_guidance():
    """The guidance landing page, in the back office because that is where an operator looks.

    The markdown under docs/guidance/ is the source of truth; this page is a route into it, and
    build/guia.py renders each document to a page of its own at newsroom/guidance/<name>.html.
    Restating the rules here would give this repository two copies of them, and two copies diverge
    — which is the first thing `index.md` tells you not to do.

    The cards used to link to `docs.html#docs/guidance/<name>.md`, a fragment on the document
    browser. That is not an address: it cannot be cited, it is not in the sitemap, and anything
    fetching it gets the browser's shell rather than the document."""
    cartoes = "".join(
        f'<div class="col sp6" style="border-top:2px solid var(--tinta);padding-top:10px">'
        f'<div class="mono xs">{i + 1:02d}</div>'
        f'<h3 class="h-3" style="padding:2px 0 4px">'
        f'<a href="guidance/{e(f).replace(".md", ".html")}">{e(t)}</a></h3>'
        f'<p class="sm">{e(d)}</p></div>'
        for i, (f, t, d) in enumerate(GUIA))

    agentes = json.loads((DADOS / "agentes.json").read_text(encoding="utf-8")) \
        if (DADOS / "agentes.json").exists() else {"agents": []}
    linhas = "".join(
        f'<tr><td class="sm"><b>{e(a["nome"])}</b> <span class="mono xs">{e(a.get("alias",""))}'
        f'</span></td><td class="sm">{e(a.get("papel",""))}</td>'
        f'<td class="mono xs">{e(", ".join(a.get("escreve_em", [])[:3]))}'
        f'{"…" if len(a.get("escreve_em", [])) > 3 else ""}</td>'
        f'<td class="mono xs">{e(a.get("id",""))}</td>'
        f'<td class="mono xs"><a href="docs.html#agents/{e(a["id"])}/ROLE.md">ROLE</a> · '
        f'<a href="docs.html#agents/{e(a["id"])}/MANDATE.md">MANDATE</a></td></tr>'
        for a in agentes.get("agentes", []))

    corpo = f"""
<p class="std" style="max-width:46em;padding:14px 0 8px"><b>Everything except what a visitor reads
is in English.</b> One test decides it: would a visitor to pt.newsroom.sgit.ai read this string on
the site? Yes means European Portuguese under AO90; no means English. That covers code, comments,
commit messages, this console, the release history, API paths and browser-side state. It does not
cover the prose, the entity names, or the ontology's readings — those are what the reader reads.</p>
<p class="sm" style="max-width:46em;padding-bottom:18px"><b>A rule without a gate is decoration.</b>
Every principle below names the thing that stops the build when it is broken, and the one principle
that has no gate says so in those words. If you add a rule, add the gate in the same change — and
break it on purpose first, because a gate that has never failed is a comment.</p>

<div class="g4" style="padding-bottom:30px">{cartoes}</div>

<h2>Who you are</h2>
<p class="sm" style="max-width:48em;padding-bottom:12px">More than one agent works here and they
are not interchangeable. Claim an identity, name it in your run record, and the gates hold you to
its write scope. If no identity fits the work, that is a message to the editor, not a licence to
invent one.</p>
<div class="rolar"><table><thead><tr><th style="width:130px">Agent</th>
  <th style="width:120px">Role</th><th>Writes in</th><th style="width:210px">Declares</th>
  <th style="width:150px">Mandate</th></tr></thead><tbody>{linhas}</tbody></table></div>

<h2>The rest of the estate</h2>
<p class="sm" style="max-width:48em">This repository is an instance of an argument made elsewhere,
not a restatement of it: where these answer a question, we link rather than copy.
<a href="https://sgit.ai/docs/guidance/index.html">sgit.ai/docs/guidance</a> ·
<a href="https://coding.sgit.ai">coding.sgit.ai</a> — the house style, derived by counting rather
than from documentation · <a href="https://nfrs.sgit.ai">nfrs.sgit.ai</a> — version control,
reliability, resilience, security, backups, consistency, explainability, documentation ·
<a href="https://newsroom.sgit.ai">newsroom.sgit.ai</a> — the parent publication.</p>
"""
    # The ONE page that carries the preamble. It used to open all nine, which is ~300px of
    # identical prose above every screen and trains the operator to scroll past the top of every
    # page — exactly where the urgent things live.
    return pagina("newsroom/guidance.html", "Guidance",
                  "What to read before changing anything on this site, and who you are when you do.",
                  corpo, preambulo=True,
                  resumo="What to read before you change anything here \u2014 human or agent.")


def pagina_agentes():
    """Who did what, across every article. The console's answer to «manage the actions of the
    multiple agents».

    It is one component reading one file, and that is the point: `dados/comentarios.json` is
    DERIVED from records that already exist — each article's provenance timeline, its verification
    record, what the newsroom says it still lacks, and what arrived from an outside assistant with
    the result of searching the frozen bytes for its excerpt. Nothing on this page was written for
    this page.

    The alternative was to let agents write comments into a file. It would read better and it
    would be theatre: a comment attributed to a model that never wrote it is a claim with a forged
    source, which is worse than a claim with none. So the rule is the same one the paper lives
    under, turned on the newsroom itself — every entry walks back to a file, and gate 25 fails the
    build when one does not."""
    dados = json.loads((DADOS / "comentarios.json").read_text(encoding="utf-8")) \
        if (DADOS / "comentarios.json").exists() else {"contagem": 0, "por_artigo": {}}

    linhas = "".join(
        f'<tr><td class="sm"><a href="../{e(v["url"])}">{e(v["titulo"][:72])}</a></td>'
        f'<td class="mono xs">{e(v["seccao"])}</td>'
        f'<td class="mono xs">{e(v["estado"])}</td>'
        f'<td class="mono xs">{v["contagem"]}</td>'
        f'<td class="mono xs">{v["abertos"]}</td>'
        f'<td class="mono xs">{e(" · ".join(sorted(v["por_agente"])))}</td></tr>'
        for v in sorted(dados.get("por_artigo", {}).values(), key=lambda x: -x["abertos"]))

    corpo = f"""
<p class="std" style="max-width:46em;padding:14px 0 8px">{dados.get("contagem", 0)} entries,
{dados.get("abertos", 0)} still open. Each one names the file and the path it came from, and the
build fails if that path does not resolve. Nothing here was authored for this page: attributing a
sentence to a model that never wrote it would be a claim with a forged source, and this whole site
is an argument that a source is the thing that matters.</p>

<h2>Per article</h2>
<div class="rolar"><table><thead><tr><th>Article</th><th style="width:110px">Section</th>
  <th style="width:100px">State</th><th style="width:70px">Entries</th>
  <th style="width:70px">Open</th><th style="width:220px">Agents</th></tr></thead>
  <tbody>{linhas}</tbody></table></div>

<h2>Everything, by agent</h2>
<pt-comment-map src="../dados/comentarios.json"></pt-comment-map>
"""
    extra = ('<script type="module" '
             'src="../assets/components/pt-comment-map/v1/v1.0/v1.0.0/pt-comment-map.js"></script>')
    return pagina("newsroom/agents.html", "Agent activity",
                  "What every agent did to every article, derived from the repository's records.",
                  corpo, extra_body=extra,
                  resumo="What every agent did to every article, derived from the records rather "
                         "than written down.")


def pagina_console(docs):
    reg, graf = carregar("registo.json"), carregar("grafo.json")
    hist, ent = carregar("historias.json"), carregar("entregas.json")
    equipa, onto = carregar("equipa.json"), carregar("ontologia.json")

    issues = []
    p = ROOT / "redacao" / "issues"
    for f in sorted(p.glob("*.json")) if p.exists() else []:
        issues.append(json.loads(f.read_text(encoding="utf-8")))
    runs = []
    p = ROOT / "redacao" / "runs"
    for f in sorted(p.glob("*.json")) if p.exists() else []:
        runs.append(json.loads(f.read_text(encoding="utf-8")))
    # The mail is counted from `dados/correio.json`, which `build/newsroom_team.py` derives by reading
    # `redacao/correio/`. Counting the folder here as well would be a second reader of it.
    corr = carregar("correio.json")
    correio = corr.get("contagem", 0)
    agentes = carregar("agentes.json")
    quad = carregar("quadro.json")
    seccoes = {}
    for f in sorted((ROOT / "seccoes").glob("*/seccao.json")) if (ROOT / "seccoes").exists() else []:
        s = json.loads(f.read_text(encoding="utf-8"))
        seccoes[s["id"]] = s

    # --- the pipeline, as it actually stands -------------------------------
    n_af_ent = sum(x["contagens"]["afirmacoes"] for x in ent.get("entregas", []))
    n_conf_ent = sum(x["contagens"]["confirmadas"] for x in ent.get("entregas", []))
    n_apr = sum(len([1 for v in (x["revisao"].get("itens") or {}).values()
                     if v.get("estado") == "aprovada"]) for x in ent.get("entregas", []))
    etapas = [
        ("1 · Fetch &amp; freeze", f'{reg.get("contagem", 0)} files',
         f'{len(reg.get("capturas", []))} dated snapshot(s), every SHA-256 re-verified each build',
         "pesquisa", "ok"),
        ("2 · Extract", f'{graf.get("contagens", {}).get("nos", 0)} nodes',
         f'{graf.get("contagens", {}).get("arestas", 0)} edges, {len(onto.get("arestas", []))} '
         f'Portuguese verbs each with a reading', "pesquisa", "ok"),
        ("3 · Deliveries", f'{n_conf_ent}/{n_af_ent} excerpts',
         f'found in the frozen bytes · {n_apr} items approved by the editor', "pesquisa", "ok"),
        ("4 · Write", f'{sum(1 for h in hist.get("historias", []) if h.get("tem_prosa"))} with prose',
         f'{hist.get("contagem", 0)} article folders exist', "redacao", "ok"),
        ("5 · Verify", f'{sum((h.get("verificacao") or {}).get("confirmadas", 0) for h in hist.get("historias", []))} claims',
         "re-read against the frozen copy and marked", "verificacao", "ok"),
        ("6 · Publish", f'{hist.get("publicados", 0)} published',
         "the editor of record writes this line, and nothing else can", "editor",
         "ok" if hist.get("publicados") else "wait"),
    ]
    # THE STATE OF A STAGE IS NOT A CHIP LIKE THE OTHERS. The review found the most important
    # state in the whole back office — stage 6, waiting on a human — rendered in the BASE chip
    # style, so it looked exactly like the five `running` chips above it, while nine other places
    # said the same thing in `.chip.miss`. It is rank 1 here, the console's only filled rank, and
    # the stage itself is tinted, because a state marked only inside a cell is a state you find by
    # reading every cell.
    ESPERA = '<span class="st st--1">needs you</span>'
    CORRE = '<span class="st st--3">running</span>'
    tira_pipe = "".join(
        f'<div class="pipe__stage{" pipe__stage--stopped" if st == "wait" else ""}">'
        f'<div class="n">{n.split(" · ")[0]}</div>'
        f'<div class="name">{n.split(" · ", 1)[1]}</div>'
        f'<div class="v">{v}</div>{ESPERA if st == "wait" else CORRE}</div>'
        for n, v, d, dep, st in etapas)
    # The detail each stage carries is worth keeping, and it does not fit in a 1/6-width tile. It
    # goes below the strip as a table, which is what a table is for.
    ROW_ESPERA = ' class="needs-you"'
    linhas_pipe = "".join(
        f'<tr{ROW_ESPERA if st == "wait" else ""}><td><b>{n}</b></td>'
        f'<td class="mono">{v}</td><td class="sm">{d}</td>'
        f'<td class="mono">{dep}</td>'
        f'<td>{ESPERA if st == "wait" else CORRE}</td></tr>'
        for n, v, d, dep, st in etapas)

    # --- who may write where -----------------------------------------------
    # The English annotation, where the record carries one. `dados/equipa.json` is Portuguese
    # because it is the publication's own record of itself; the `en` block is an annotation, the
    # same arrangement the ontology uses for its verbs. Falling back to the Portuguese rather than
    # translating on the fly matters: a console that paraphrased the record would drift from it,
    # and the record is the thing that binds.
    def en(x, campo):
        return (x.get("en") or {}).get(campo) or x.get(campo)

    deps = "".join(
        f'<tr><td><b>{e(en(x, "nome"))}</b>'
        f'<div class="mono xs">{e(x["nome"])}</div>'
        f'<div class="xs" style="padding-top:4px">{e(en(x, "gravidade"))}</div></td>'
        f'<td class="mono xs">{"<br>".join(e(p) for p in x["escreve_em"])}</td>'
        f'<td class="sm">{e(en(x, "recusa"))}</td>'
        f'<td class="sm">{e(en(x, "errado_quando"))}</td></tr>'
        for x in equipa.get("departamentos", []))
    ed = equipa.get("editor_de_registo", {})
    so_ele = "".join(f'<li class="sm">{e(x)}</li>'
                     for x in ((ed.get("en") or {}).get("so_ele_pode") or ed.get("so_ele_pode", [])))
    ed_faz = (ed.get("en") or {}).get("o_que_faz") or ed.get("o_que_faz", "")

    # --- the board ----------------------------------------------------------
    ORDEM = ["procurado", "registado", "congelado", "extraido", "redigido", "verificado",
             "revisto", "publicado", "parado"]
    colunas = ""
    for est in ORDEM:
        cartoes = "".join(
            f'<div class="cartao"><div class="mono xs">{e(i["id"])} · {e(i["seccao"])}</div>'
            f'<div style="padding-top:4px;font-size:13px">{e(i["titulo"][:110])}</div></div>'
            for i in issues if i["estado"] == est)
        n = sum(1 for i in issues if i["estado"] == est)
        if not n:
            continue
        colunas += (f'<div class="coluna"><div class="sect">{e(est)} '
                    f'<span class="mono xs">{n}</span></div>{cartoes}</div>')

    # --- articles -----------------------------------------------------------
    linhas_art = "".join(
        f'<tr><td class="mono xs">{e(h["data"])}</td>'
        f'<td><a href="../{e(h["url"])}">{e(h["titulo"][:86])}</a></td>'
        f'<td class="mono xs">{e(h["seccao"])}</td>'
        f'<td><span class="chip">{e(h["estado"])}</span></td>'
        f'<td class="mono xs">{len(h.get("assenta_em", []))} src · '
        f'{(h.get("verificacao") or {}).get("confirmadas", 0)} ok</td>'
        f'<td class="mono xs"><a href="../{e(h["pasta"])}/artigo.json">json</a> '
        f'<a href="../{e(h["pasta"])}/proveniencia.json">prov</a></td></tr>'
        for h in hist.get("historias", []))

    # --- sections -----------------------------------------------------------
    linhas_sec = ""
    for sid, s in sorted(seccoes.items(), key=lambda kv: kv[1]["ordem"]):
        congeladas = sum(1 for t in s.get("fontes_alvo", []) if t["estado"] == "congelada")
        pendentes = sum(1 for t in s.get("fontes_alvo", []) if t["estado"] != "congelada")
        arts = sum(1 for h in hist.get("historias", []) if h["seccao"] == sid)
        tipos = [t["id"] for t in onto.get("tipos", []) if t.get("seccao") == sid]
        nos = sum(1 for n in graf.get("nos", []) if n["tipo"] in tipos)
        estado = ("<span class=\"chip ok\">has data</span>" if nos else
                  "<span class=\"chip miss\">empty, and says so</span>")
        linhas_sec += (
            f'<tr><td><a href="../{e(sid)}/">{e(s["rotulo"])}</a>'
            f'<div class="mono xs">seccoes/{e(sid)}/seccao.json</div></td>'
            f'<td>{estado}</td><td class="mono xs">{nos} nodes</td>'
            f'<td class="mono xs">{arts} article(s)</td>'
            f'<td class="mono xs">{congeladas} frozen'
            f'{f" · {pendentes} pending" if pendentes else ""}</td>'
            f'<td class="sm">{e((s.get("perguntas_em_aberto") or [""])[0][:120])}</td></tr>')

    # --- runs and commits ----------------------------------------------------
    VERDE, VERMELHO = '<span class="chip ok">green</span>', '<span class="chip falta">red</span>'
    linhas_run = "".join(
        f'<tr><td class="mono xs">{e(r["quando"])}</td><td class="sm">{e(r["prompt"])}</td>'
        f'<td class="xs">{e(r["modelo"])}</td>'
        f'<td class="mono xs">{e(", ".join(r["pastas_alteradas"]))}</td>'
        f'<td>{VERDE if r["portoes"] else VERMELHO}</td>'
        f'<td class="mono xs">{e(r.get("versao") or "—")}</td></tr>' for r in runs)
    linhas_git = "".join(
        f'<tr><td class="mono xs">{e(h)}</td><td class="mono xs">{e(d)}</td>'
        f'<td class="sm">{e(s[:110])}</td></tr>' for h, d, _, s in commits_recentes())

    # WHAT IS WAITING ON YOU — the first thing on the page, and the only filled thing on it.
    # The list is derived by fila(); the number is len() of that list inside the component, so
    # neither the queue's own heading nor the rail badge holds a number of its own.
    fila_itens = fila()
    fila_json = e(json.dumps(fila_itens, ensure_ascii=False))
    fila_lista = "".join(f'<li>{e(x["title"])} \u2014 <code>{e(x["where"])}</code></li>'
                         for x in fila_itens)

    corpo = f"""

<pt-queue items="{fila_json}">
  <ul class="sm">{fila_lista}</ul>
</pt-queue>

<h2>The pipeline</h2>
<div class="pipe">{tira_pipe}</div>
<div class="rolar" style="margin-top:14px"><table><thead><tr><th style="width:150px">Stage</th>
  <th style="width:130px">Now</th>
  <th>Detail</th><th style="width:100px">Owner</th><th style="width:150px">State</th></tr></thead>
  <tbody>{linhas_pipe}</tbody></table></div>
<p class="xs" style="max-width:48em;padding-top:10px">Stage 6 is the only one that cannot be moved
by any agent. <code>estado: publicado</code> is the editor of record's line; gate 11 fails the
build if it appears without their name and a date.</p>

<h2>Departments · who may write where</h2>
<div class="rolar"><table><thead><tr><th style="width:190px">Department</th>
  <th style="width:210px">Writes only in</th><th>Refuses</th><th>Wrong when</th></tr></thead>
  <tbody>{deps}</tbody></table></div>
<div class="painel" style="margin-top:14px">
<div class="sect">Editor of record · {e(ed.get("nome", ""))}</div>
<p class="sm" style="padding-top:6px">{e(ed_faz)}</p>
<div class="sect" style="padding-top:12px">Only they can</div><ul>{so_ele}</ul>
<p class="xs" style="padding-top:8px">Gate 12 reads each run record and fails the build if a
department wrote outside its own folder. That check is what makes this a newsroom rather than a
script with role names in the comments.</p></div>

<h2>The agent team ·
  {len(agentes.get("agentes", []))} roles, {quad.get("contagens", {}).get("cartoes", 0)} board
  cards, {correio} messages</h2>
<p class="sm" style="max-width:52em">Three pages, generated by <code>build/newsroom_team.py</code> from
<code>dados/agentes.json</code> and the mail folder. The roles are defined in the shape
<a href="https://teams.sgit.ai/role-format/index.html">teams.sgit.ai publishes for a
<code>ROLE.md</code></a>, and they coordinate under
<a href="https://sgraph.ai/en-gb/library/how-it-works/email-fs-lite.md">Email-FS-lite</a> — files
in a folder, one commit per cycle, no broker and no API.</p>
<div class="chips" style="padding-top:10px">
  <a class="chip ok" href="team.html">the team — who they are, and what each is not
    responsible for →</a>
  <a class="chip ok" href="board.html">the board — what each one has in front of it →</a>
  <a class="chip ok" href="mail.html">the mail — what passed between them →</a>
  <a class="chip" href="bridges.html">the bridges — how the editor reaches them →</a>
  <a class="chip" href="design.html">the design review — item by item, and what was done →</a>
</div>

<h2>Board · {len(issues)} issues</h2>
<div class="quadro">{colunas}</div>
<p class="xs" style="padding-top:10px">Rendered from <code>redacao/issues/*.json</code>. The same
issues appear on <a href="board.html">each agent's board</a>, placed there by a published formula
and not by hand. The reader-facing version of this board is
<a href="../redacao/">A mesa</a>, in Portuguese.</p>

<h2>Articles · {hist.get("contagem", 0)}
  folders, {hist.get("publicados", 0)} published</h2>
<div class="rolar"><table><thead><tr><th style="width:90px">Date</th><th>Title</th>
  <th style="width:110px">Section</th><th style="width:120px">State</th>
  <th style="width:110px">Evidence</th><th style="width:100px">Files</th></tr></thead>
  <tbody>{linhas_art}</tbody></table></div>
<p class="xs" style="padding-top:10px">Each article is a folder at
<code>artigos/&lt;yyyy&gt;/&lt;mm&gt;/&lt;dd&gt;/&lt;slug&gt;/</code> holding the prose, the claim
record and the provenance. <code>dados/historias.json</code> is derived from those folders and is
never hand-edited.</p>

<h2>Sections · coverage</h2>
<div class="rolar"><table><thead><tr><th style="width:170px">Section</th>
  <th style="width:180px">State</th><th style="width:90px">Graph</th><th style="width:100px">Articles</th>
  <th style="width:140px">Sources</th><th>First open question</th></tr></thead>
  <tbody>{linhas_sec}</tbody></table></div>

<h2>Runs</h2>
<div class="rolar"><table><thead><tr><th style="width:150px">When</th><th>Prompt</th>
  <th style="width:170px">Model</th><th style="width:200px">Folders</th>
  <th style="width:90px">Gates</th><th style="width:80px">Version</th></tr></thead>
  <tbody>{linhas_run}</tbody></table></div>

<h2>Recent commits</h2>
<div class="rolar"><table><thead><tr><th style="width:80px">Commit</th>
  <th style="width:140px">When</th><th>Subject</th></tr></thead>
  <tbody>{linhas_git}</tbody></table></div>

<h2>Run it yourself</h2>
<div class="rolar"><pre class="mono xs" style="margin:0;padding:14px;background:var(--painel);
border:1px solid var(--filete);white-space:pre">python3 build/tudo.py               # THE WHOLE BUILD, IN ORDER, THEN THE THREE GATES
python3 build/tudo.py --fetch       # the same, going to the network for the sources first
python3 build/tudo.py --so-portoes  # gates only, no rebuild
python3 build/tudo.py --render      # plus the browser gate (needs playwright installed)

# what build/tudo.py runs, in this order — the order is load-bearing
python3 build/extract.py [--fetch]  # fetch, freeze, hash, register, extract, diff
python3 build/graph.py              # ontology, graph, triples, manifest, source publishers
python3 build/entidades.py          # dados/entidades.json + a page per entity  ← before any page
python3 build/comentarios.py        # agent activity per article, derived from the records
python3 build/artigos.py            # article folders -&gt; pages + derived index
python3 build/build.py              # every reader-facing page
python3 build/paginas_extra.py      # /api/ and /proveniencia/
python3 build/api.py                # api/v1/ — every path is a file on disk
python3 build/newsroom.py         # this console
python3 build/chrome.py             # llms.txt, sitemap.xml, index.md
python3 build/gates.py              # gates  1-15  — must print OK
python3 build/gates_artigos.py      # gates 16-25  — must print OK
node admin/build/validate.js        # the site gate — must print OK
node admin/build/render.mjs         # the browser gate — opt-in, see below

# build/entregas.py is run per delivery, not per build:
python3 build/entregas.py --fetch   # freeze delivery sources, check every excerpt</pre></div>
<p class="xs" style="padding-top:10px"><b>Use <code>build/tudo.py</code>.</b> The order matters and
it is not obvious: <code>entidades.py</code> must run before anything that writes a page, because
the pass that turns a name in prose into a link reads the file it produces — run out of order,
nothing breaks, the site just quietly has fewer links than it should. The command list in
<code>CLAUDE.md</code> is older than half these steps, and <code>CLAUDE.md</code> is the rules
file: it is in the deny list on purpose, and editing the rules to match the code is backwards. So
the real order lives in an executable file, where it cannot go stale without something failing.</p>
<p class="xs" style="padding-top:10px"><b>Run <code>--render</code> before shipping anything that
touches <code>assets/components/</code>.</b> The other three gates read files and read HTML; none
of them <i>executes</i> anything. A component that throws on load passes all three and reaches the
reader as an empty box — which looks like a design choice. The browser gate opens each component in
a real Chromium and fails on a console error, a failed request, a component that never reaches
<code>data-estado="pronto"</code>, or a page that overflows at 390px. It is opt-in because it needs
a browser and this repository has no node dependencies; when CI has one, it becomes a gate without
a line of it changing.</p>
<p class="xs" style="padding-top:10px">Without <code>--fetch</code> the first two run against the
copies already frozen and touch no network. That is how the site is rebuilt from a clone, years
later, to exactly the same pages.</p>

<h2>Elsewhere in the estate</h2>
<div class="rolar"><table><thead><tr><th style="width:230px">Site</th><th>What is there</th>
  </tr></thead><tbody>
{"".join(f'<tr><td><a href="{e(u)}">{e(n)}</a></td><td class="sm">{e(w)}</td></tr>' for n, u, w in ESTATE)}
</tbody></table></div>
<p class="xs" style="padding-top:10px">{len(docs)} markdown documents in this repository are
readable at <a href="docs.html">documents</a>.</p>
"""
    extra = ('<script type="module" '
             'src="../assets/components/pt-queue/v1/v1.0/v1.0.0/pt-queue.js"></script>'
             + FILA_JS)
    return pagina("newsroom/index.html", "Console",
                  "The operations console for pt.newsroom.sgit.ai: pipeline, departments, board, "
                  "articles, sections, runs.", corpo, extra_body=extra,
                  resumo="The state of the newsroom right now. Every number on this page counts "
                         "files in this repository.")


def pagina_interviews():
    """The two interview packs, with the prompts on the page rather than one click away.

    A prompt is COPIED, not read: by a person about to paste it into ChatGPT, often on a phone.
    Sending them to a raw markdown file to select-all is how you lose them. So the prompts are
    rendered here from their markdown on every build and marked derived — a second VIEW of one
    copy, never a second copy. Gate 42 fails the build if the page and the markdown disagree.

    IT LIVES IN THE CONSOLE because it is about how this newsroom works and not about what it
    found, which is the same test that put the rest of these pages here.
    """
    f = DADOS / "interviews.json"
    if not f.exists():
        return None
    iv = json.loads(f.read_text(encoding="utf-8"))

    secoes = []
    for pack in iv["packs"]:
        blocos = []
        for pc in pack["pieces"]:
            blocos.append(
                f'<h3 id="{e(pack["id"])}-{e(pc["file"].split("__")[0])}">{e(pc["title"])}</h3>'
                f'<p class="bo-note">{e(pc["why"])} <b>For {e(pc["for_whom"])}.</b></p>'
                f'<p class="bo-meta">{e(pc["language"])} · {pc["lines"]} lines · '
                f'<code>{e(pc["sha256"][:12])}</code> · '
                f'<a href="../{e(pc["path"])}">the raw file</a></p>'
                f'<pre class="bo-pre">{e(pc["text"])}</pre>')
        secoes.append(
            f'<h2 id="{e(pack["id"])}">{e(pack["title"])}</h2>'
            f'<p class="bo-note">{e(pack["why"])} '
            f'<a href="../briefs/pack/{e(pack["folder"])}/README.md">The method, in full.</a></p>'
            + "".join(blocos))

    corpo = (
        f'<p class="bo-note">{e(iv["what_it_is"])}</p>'
        f'<p class="bo-note"><b>The rule that governs what comes out of here.</b> '
        f'{e(iv["the_rule"])} An interview makes no exception to any rule of this house: three '
        f'fields per person, no contact detail in any file, and removal on request is '
        f'unconditional and carries no reason. Nothing said aloud puts a story into published.</p>'
        + "".join(secoes)
        + f'<h2>This text is derived</h2>'
          f'<p class="bo-note">Rendered from <code>{e(iv["derived_from"])}</code> on every build '
          f'and never hand-written here. Content exists once, and gate 42 fails the build if this '
          f'page and the markdown disagree — a derived file with no gate is a second copy under '
          f'another name.</p>')

    return pagina("newsroom/interviews.html", "Interviews",
                  "Interviewing somebody to write, and interviewing the editor to know what to "
                  "do. The prompts, ready to copy.",
                  corpo,
                  resumo=f'{iv["count"]} prompts in {len(iv["packs"])} packs')


def main():
    docs = documentos()
    feitas = [
        escrever("newsroom/index.html", pagina_console(docs)),
        escrever("newsroom/docs.html", pagina_docs(docs)),
        escrever("newsroom/agents.html", pagina_agentes()),
        escrever("newsroom/guidance.html", pagina_guidance()),
        escrever("newsroom/interviews.html", pagina_interviews()),
    ]
    (DADOS / "documentos.json").write_text(json.dumps({
        "id": "pt-documentos", "versao": "0.1.0", "atualizado": time.strftime("%Y-%m-%d"),
        "nota": ("Every markdown document in this repository, indexed for the back office. The "
                 "viewer reads the file itself over fetch rather than a copy, so what it shows "
                 "cannot drift from what the build read."),
        "contagem": len(docs), "documentos": docs,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"newsroom: {len(feitas)} pages, {len(docs)} documents indexed")
    return feitas


if __name__ == "__main__":
    main()

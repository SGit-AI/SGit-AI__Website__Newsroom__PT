#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the back office. Operations console, in English.

    python3 build/backoffice.py

WHY THIS ONE AREA IS IN ENGLISH, when CLAUDE.md says everything a reader sees is Portuguese.

The rule in CLAUDE.md is about the PUBLICATION: "code and comments are in English; everything the
reader sees is in European Portuguese". The back office is not the publication — it is the console
the editor of record and the agents work in, and its audience is whoever is operating the
newsroom, who in this estate reads English. The editor asked for it in English deliberately.

Two things follow, and both are enforced rather than promised:

1. **Nothing here is reader-facing.** `/backoffice/` is not in the masthead, not in a section, and
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
  viewer.html   a PERMALINK, kept because things linked it. It forwards to docs.html, carrying
                the #fragment across, so the two-pane browser is the ONE reader. There is no
                second implementation of document rendering in this repository.
"""
import json
import re
import subprocess
import time
from pathlib import Path

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


def pagina(rel, titulo, descricao, corpo, extra_body=""):
    profundidade = rel.count("/")
    raiz = "../" * profundidade if profundidade else ""
    canonico = f"https://{HOST}/{rel}"
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
<link rel="stylesheet" href="{raiz}assets/fonts.css">
<link rel="stylesheet" href="{raiz}assets/site.css">
</head>
<body>
<div class="folha">

<div class="datalinha">
  <div>pt.newsroom.sgit.ai · <b>back office</b></div>
  <div><a href="{raiz}">← the paper</a> · <a href="{raiz}backoffice/">console</a> ·
       <a href="{raiz}backoffice/docs.html">documents</a> ·
       <a href="{raiz}backoffice/agents.html">agents</a> ·
       <a href="{raiz}admin/versions.html">versions</a></div>
  <div><span class="ver">{VERSAO}</span></div>
</div>

<div class="aviso-bloco" style="border-left-color:var(--acento)">
<p class="sm"><b>This is the operations console, not the publication.</b> It is in English on
purpose: its audience is whoever is operating the newsroom, not the reader of the paper. The
publication itself is natively Portuguese and nothing here is linked from the masthead. Every
number on these pages counts files in this repository — the back office reports on the newsroom
and never on the world, and a gate fails the build if a page here ever cites a frozen source as
evidence for a claim about Portugal.</p>
</div>

{corpo}

<div class="agent">
<b>For an agent.</b> Generated by <code>build/backoffice.py</code> from the files in this
repository; nothing here is hand-written. The machine-readable index of the publication is at
<a href="{raiz}llms.txt">llms.txt</a>. Source: <a href="{GH}">{GH.split('//')[1]}</a> · file:
<code>{e(rel)}</code> · version <span class="ver">{VERSAO}</span>.
</div>

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
<div class="rule" style="padding:26px 0 8px"><div class="sect">Documents</div></div>
<h1 class="h-2" style="max-width:28em">Every markdown document this site was built from, readable
without losing your place.</h1>
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
    return pagina("backoffice/docs.html", "Documents",
                  "Every markdown document this site was built from, in a two-pane reader.",
                  corpo, extra_body=extra)


FORWARD_JS = """
<script>
/* This page is kept as a PERMALINK, not as a second viewer. The document browser on docs.html
   is the one implementation, and having a second one here would be the rule this site repeats
   most often — content exists once — broken in its own back office. Anyone holding a
   viewer.html#path link lands where that document is now read. */
(function () {
    var path = location.hash.replace(/^#/, '')
    location.replace('docs.html' + (path ? '#' + path : ''))
})()
</script>
"""


def pagina_viewer():
    corpo = """
<div class="rule" style="padding:26px 0 8px"><div class="sect">Document viewer</div></div>
<h1 class="h-2" style="max-width:28em">This page moved into the document browser.</h1>
<p class="std" style="max-width:46em;padding:14px 0 10px">Documents are now read in a two-pane
browser — the tree stays while you read — and this address forwards there, keeping any link
somebody already holds. There is one viewer, not two: a second implementation of the same thing
is the rule this site repeats most often, content exists once, broken in its own back office.</p>
<p class="sm"><a href="docs.html">Go to the documents →</a></p>
"""
    return pagina("backoffice/viewer.html", "Document viewer",
                  "Forwards to the document browser, which is where documents are read.",
                  corpo, extra_body=FORWARD_JS)


# --------------------------------------------------------------- the console ---
def commits_recentes(n=12):
    try:
        r = subprocess.run(["git", "log", f"-{n}", "--format=%h\t%ad\t%an\t%s",
                            "--date=format:%Y-%m-%d %H:%M"],
                           cwd=ROOT, capture_output=True, text=True, timeout=20)
        return [l.split("\t", 3) for l in r.stdout.strip().split("\n") if l.count("\t") >= 3]
    except Exception:
        return []


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
<div class="rule" style="padding:26px 0 8px"><div class="sect">Agents</div></div>
<h1 class="h-2" style="max-width:30em">What every agent did to every article, derived from the
records rather than written down.</h1>
<p class="std" style="max-width:46em;padding:14px 0 8px">{dados.get("contagem", 0)} entries,
{dados.get("abertos", 0)} still open. Each one names the file and the path it came from, and the
build fails if that path does not resolve. Nothing here was authored for this page: attributing a
sentence to a model that never wrote it would be a claim with a forged source, and this whole site
is an argument that a source is the thing that matters.</p>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Per article</div></div>
<div class="rolar"><table><thead><tr><th>Article</th><th style="width:110px">Section</th>
  <th style="width:100px">State</th><th style="width:70px">Entries</th>
  <th style="width:70px">Open</th><th style="width:220px">Agents</th></tr></thead>
  <tbody>{linhas}</tbody></table></div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Everything, by agent</div></div>
<pt-comment-map src="../dados/comentarios.json"></pt-comment-map>
"""
    extra = ('<script type="module" '
             'src="../assets/components/pt-comment-map/v1/v1.0/v1.0.0/pt-comment-map.js"></script>')
    return pagina("backoffice/agents.html", "Agents",
                  "What every agent did to every article, derived from the repository's records.",
                  corpo, extra_body=extra)


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
    correio = len(list((ROOT / "redacao" / "correio").rglob("*.md"))) \
        if (ROOT / "redacao" / "correio").exists() else 0
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
    ESPERA = '<span class="chip">waiting on a human</span>'
    CORRE = '<span class="chip ok">running</span>'
    linhas_pipe = "".join(
        f'<tr><td><b>{n}</b></td><td class="mono">{v}</td><td class="sm">{d}</td>'
        f'<td class="mono xs">{dep}</td>'
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

    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">Console</div></div>
<h1 class="h-2" style="max-width:28em">What the newsroom has done, what it is waiting on, and who
is allowed to do what.</h1>

<div class="rule" style="padding:22px 0 8px"><div class="sect">The pipeline</div></div>
<div class="rolar"><table><thead><tr><th style="width:150px">Stage</th><th style="width:130px">Now</th>
  <th>Detail</th><th style="width:100px">Owner</th><th style="width:150px">State</th></tr></thead>
  <tbody>{linhas_pipe}</tbody></table></div>
<p class="xs" style="max-width:48em;padding-top:10px">Stage 6 is the only one that cannot be moved
by any agent. <code>estado: publicado</code> is the editor of record's line; gate 11 fails the
build if it appears without their name and a date.</p>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Departments · who may write where</div></div>
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

<div class="rule" style="padding:22px 0 8px"><div class="sect">Board · {len(issues)} issues</div></div>
<div class="quadro">{colunas}</div>
<p class="xs" style="padding-top:10px">Rendered from <code>redacao/issues/*.json</code>.
{correio} mail files in <code>redacao/correio/</code>. The reader-facing version of this board is
<a href="../redacao/">A mesa</a>, in Portuguese.</p>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Articles · {hist.get("contagem", 0)}
  folders, {hist.get("publicados", 0)} published</div></div>
<div class="rolar"><table><thead><tr><th style="width:90px">Date</th><th>Title</th>
  <th style="width:110px">Section</th><th style="width:120px">State</th>
  <th style="width:110px">Evidence</th><th style="width:100px">Files</th></tr></thead>
  <tbody>{linhas_art}</tbody></table></div>
<p class="xs" style="padding-top:10px">Each article is a folder at
<code>artigos/&lt;yyyy&gt;/&lt;mm&gt;/&lt;dd&gt;/&lt;slug&gt;/</code> holding the prose, the claim
record and the provenance. <code>dados/historias.json</code> is derived from those folders and is
never hand-edited.</p>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Sections · coverage</div></div>
<div class="rolar"><table><thead><tr><th style="width:170px">Section</th>
  <th style="width:180px">State</th><th style="width:90px">Graph</th><th style="width:100px">Articles</th>
  <th style="width:140px">Sources</th><th>First open question</th></tr></thead>
  <tbody>{linhas_sec}</tbody></table></div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Runs</div></div>
<div class="rolar"><table><thead><tr><th style="width:150px">When</th><th>Prompt</th>
  <th style="width:170px">Model</th><th style="width:200px">Folders</th>
  <th style="width:90px">Gates</th><th style="width:80px">Version</th></tr></thead>
  <tbody>{linhas_run}</tbody></table></div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Recent commits</div></div>
<div class="rolar"><table><thead><tr><th style="width:80px">Commit</th>
  <th style="width:140px">When</th><th>Subject</th></tr></thead>
  <tbody>{linhas_git}</tbody></table></div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Run it yourself</div></div>
<div class="rolar"><pre class="mono xs" style="margin:0;padding:14px;background:var(--painel);
border:1px solid var(--filete);white-space:pre">python3 build/tudo.py               # THE WHOLE BUILD, IN ORDER, THEN THE THREE GATES
python3 build/tudo.py --fetch       # the same, going to the network for the sources first
python3 build/tudo.py --so-portoes  # gates only, no rebuild

# what build/tudo.py runs, in this order — the order is load-bearing
python3 build/extract.py [--fetch]  # fetch, freeze, hash, register, extract, diff
python3 build/graph.py              # ontology, graph, triples, manifest, source publishers
python3 build/entidades.py          # dados/entidades.json + a page per entity  ← before any page
python3 build/comentarios.py        # agent activity per article, derived from the records
python3 build/artigos.py            # article folders -&gt; pages + derived index
python3 build/build.py              # every reader-facing page
python3 build/paginas_extra.py      # /api/ and /proveniencia/
python3 build/api.py                # api/v1/ — every path is a file on disk
python3 build/backoffice.py         # this console
python3 build/chrome.py             # llms.txt, sitemap.xml, index.md
python3 build/gates.py              # gates  1-15  — must print OK
python3 build/gates_artigos.py      # gates 16-25  — must print OK
node admin/build/validate.js        # the site gate — must print OK

# build/entregas.py is run per delivery, not per build:
python3 build/entregas.py --fetch   # freeze delivery sources, check every excerpt</pre></div>
<p class="xs" style="padding-top:10px"><b>Use <code>build/tudo.py</code>.</b> The order matters and
it is not obvious: <code>entidades.py</code> must run before anything that writes a page, because
the pass that turns a name in prose into a link reads the file it produces — run out of order,
nothing breaks, the site just quietly has fewer links than it should. The command list in
<code>CLAUDE.md</code> is older than half these steps, and <code>CLAUDE.md</code> is the rules
file: it is in the deny list on purpose, and editing the rules to match the code is backwards. So
the real order lives in an executable file, where it cannot go stale without something failing.</p>
<p class="xs" style="padding-top:10px">Without <code>--fetch</code> the first two run against the
copies already frozen and touch no network. That is how the site is rebuilt from a clone, years
later, to exactly the same pages.</p>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Elsewhere in the estate</div></div>
<div class="rolar"><table><thead><tr><th style="width:230px">Site</th><th>What is there</th>
  </tr></thead><tbody>
{"".join(f'<tr><td><a href="{e(u)}">{e(n)}</a></td><td class="sm">{e(w)}</td></tr>' for n, u, w in ESTATE)}
</tbody></table></div>
<p class="xs" style="padding-top:10px">{len(docs)} markdown documents in this repository are
readable at <a href="docs.html">documents</a>.</p>
"""
    return pagina("backoffice/index.html", "Console",
                  "The operations console for pt.newsroom.sgit.ai: pipeline, departments, board, "
                  "articles, sections, runs.", corpo)


def main():
    docs = documentos()
    feitas = [
        escrever("backoffice/index.html", pagina_console(docs)),
        escrever("backoffice/docs.html", pagina_docs(docs)),
        escrever("backoffice/viewer.html", pagina_viewer()),
        escrever("backoffice/agents.html", pagina_agentes()),
    ]
    (DADOS / "documentos.json").write_text(json.dumps({
        "id": "pt-documentos", "versao": "0.1.0", "atualizado": time.strftime("%Y-%m-%d"),
        "nota": ("Every markdown document in this repository, indexed for the back office. The "
                 "viewer reads the file itself over fetch rather than a copy, so what it shows "
                 "cannot drift from what the build read."),
        "contagem": len(docs), "documentos": docs,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"backoffice: {len(feitas)} pages, {len(docs)} documents indexed")
    return feitas


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — every page's shell: head, masthead, navigation, house blocks.

Defined once here and applied everywhere by `build.py`. It is what stops the site drifting as it
grows: the version badge, the canonical link, the notice that this is made by agents, the "for an
agent" block the site gate requires on every page, and the link to the data-protection notice on
every page that names somebody.

Nothing here is hand-written into a page. A generated page somebody edits by hand is generated over
on the next build and the edit is lost — so you do not edit it: you edit this.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
HOST = "pt.newsroom.sgit.ai"
VERSAO = (ROOT / "admin" / "build" / "version.txt").read_text(encoding="utf-8").strip()
GH = "https://github.com/SGit-AI/SGit-AI__Website__Newsroom__PT"
PAI = "https://newsroom.sgit.ai"

# The brief's eight sections, plus the register and the graph. The design's nav, in its order.
SECCOES = [
    ("empresas",      "Empresas"),
    ("protagonistas", "Protagonistas"),
    ("instituicoes",  "Instituições"),
    ("politicas",     "Políticas"),
    ("casos-de-uso",  "Casos de uso"),
    ("codigo-aberto", "Código aberto"),
    ("diaspora",      "Diáspora"),
    ("eventos",       "Eventos"),
]
# «Entidades» is in the masthead and not the footer because it is a way of walking the paper, not
# machinery: it is the door to the two hundred names this site already knows something about.
EXTRA = [("entidades", "Entidades"), ("registo", "Registo"), ("grafo", "Grafo")]

# The machinery pages, in the footer rather than the masthead.
RODAPE = [
    ("artigos", "Os artigos"), ("metodo", "Método"), ("equipa", "A redação"),
    ("entregas", "Entregas de investigação"), ("redacao", "A mesa"),
    ("carteira", "A carteira"),
    ("ficheiros", "Os ficheiros"), ("aviso", "Aviso de proteção de dados"),
    ("sobre", "Sobre e limites"),
]

# The operations console. In the footer as machinery, not in the masthead: it is not the
# publication, and it is in English on purpose — its audience is whoever operates the newsroom,
# not whoever reads the paper.
BASTIDORES = ("backoffice", "Back office (EN)")

# THE TITLE IS THE SUBJECT, NOT THE ADDRESS. Until v0.2.0 the masthead said «pt.newsroom.sgit.ai»,
# which is where the site is and not what the site is. A reader arriving does not care about the
# domain: they want to know what it is about. The address becomes the subtitle, where it stays
# useful — it is how you come back — and the publication's proper name is the thing it maps.
TITULO = "O Ecossistema Português de IA"
SUBTITULO = "pt.newsroom.sgit.ai"

LEMA = ("O ecossistema português de IA é pequeno o suficiente para ser mapeado por completo "
        "e grande o suficiente para ser interessante.")


def e(x):
    return html.escape(str(x if x is not None else ""), quote=True)


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def utilitarios(raiz, no_backoffice=False):
    """The utility run at the top right, IDENTICAL on the paper and in the back office.

    THE MENU MUST NOT MOVE WHEN YOU CROSS BETWEEN THEM, and before v0.11.0 it moved a lot: the
    paper had a dateline, a countdown and this run of links, then a centred masthead and a section
    nav; the back office had a single row that mixed its own identity, its own eleven links and the
    version, all in a different order and a different place. Clicking "Back office" moved every
    item in the chrome at once, which reads as arriving at a different site rather than at the back
    of the same one.

    So this run is generated once, here, and both chromes emit it in the same slot with the same
    items in the same order. Exactly one item differs, and it is the one that has to: on the paper
    it points INTO the back office, and in the back office it points back out at the paper. Same
    position, same width, same face — so crossing over moves one label and nothing else.
    """
    atravessar = (
        f'<a href="{raiz}" title="A publicação, em português">← o jornal</a>'
        if no_backoffice else
        f'<a href="{raiz}backoffice/" title="The operations console — in English">'
        f'Back office <span class="flag" aria-label="em inglês">EN</span></a>')
    return (
        f'<div class="utility">'
        f'<a href="{raiz}aviso/">Aviso</a>'
        f'<a href="{raiz}metodo/">Método</a>'
        f'<a href="{raiz}api/">API</a>'
        f'{atravessar}'
        # The wallet is a LINK to its own page, not a panel over this one. See pt-wallet.js: the
        # editor asked for the spend on a page of its own, and a ledger worth reading is worth a
        # URL. The component still debits the page it is on — that is the demonstration — it just
        # no longer covers the masthead to show you the result.
        f'<pt-wallet site-root="{raiz}"></pt-wallet>'
        # THE VERSION BADGE IS A LINK. The sgit.ai guidance asks for both things — show the
        # version in the chrome AND link it to that version's detail — and until v0.9.0 only
        # the first half was done: it was a `<span>`, and the only route to the detail was the
        # last item of an eleven-item list in the footer. On a site whose entire proposition is
        # traceability, it was the one place the site did not trace itself.
        f'<a class="ver" href="{raiz}admin/versions.html#{VERSAO}" '
        f'title="O que mudou em {VERSAO}, e porquê">{VERSAO}</a></div>')


def abertura(titulo, numero=None, nota="", fim="", maior=False):
    """A section opener: a rule, an optional number, a title, an optional note, an optional end.

    `.sect` alone — a small letterspaced label — is too quiet to OPEN a section. It is a label, not
    a door, and using it for both is half of why the front page read as one undifferentiated field
    (the other half being hairlines nobody could see). The adopted stylesheet gives three levels:

        .opener--major   a 3px ink rule, a number, a title at .h-2 size   — a major division
        .opener          a 1px ink rule and a title                        — an ordinary section
        .sect            the label alone                                   — a block inside one

    Used with restraint. The stylesheet's own note says a page should reach for the heaviest level
    no more than three or four times, so this is NOT a blanket replacement for the 104 `.rule` +
    `.sect` pairs across the generators: the ordinary ones stay `.sect`, because a page where
    everything is a door has no doors.

    `fim` rides at the far end — it is where the confirmado/disputado legend goes.
    """
    n = f'<span class="opener__n">{e(numero)}</span>' if numero else ""
    nt = f'<span class="opener__note">{e(nota)}</span>' if nota else ""
    f = f'<div class="opener__end">{fim}</div>' if fim else ""
    cls = "opener opener--major" if maior else "opener"
    return (f'<div class="{cls}">{n}<h2 class="opener__title">{e(titulo)}</h2>{nt}{f}</div>')


def tira_de_numeros(pares):
    """A stat strip: label over value, in a row, ruled top and bottom.

    Replaces two patterns the review named. On an entity page it replaces a ONE-ROW `<table>` used
    to present a single key/value pair, whose 230px header wrapped to two lines beside a lone «2».
    On the front page it replaces a stack of label/sentence rows under «Nesta edição», where the
    numbers — the thing a reader scans for — were buried inside prose.

    A number here is a `.stat-value`; a number that is a machine fact (a hash, an id) adds `mono`
    and the stylesheet sizes it down, because a monospaced 22px digit run is wider than the column.
    """
    saida = []
    for rotulo, valor, *resto in pares:
        cls = "stat-value mono" if (resto and resto[0]) else "stat-value"
        saida.append(f'<div><span class="stat-label">{e(rotulo)}</span>'
                     f'<span class="{cls}">{e(valor)}</span></div>')
    return f'<div class="stats">{"".join(saida)}</div>'


def proveniencia(fichas, frase):
    """The evidence line under a headline, with the chips one step behind a disclosure.

    The chips sat directly beneath the lead headline — where a newspaper puts the dek and the
    byline — as three bordered 11px mono runs of character counts. The provenance IS this
    publication's product and stays on the page; what was wrong was its RANK. A well-written lead
    followed by byte counts reads as a debug panel.

    So the sentence leads, in the paper's own voice and in the serif, and the chips open on click.
    `<details>`/`<summary>` and no JavaScript: this has to work for a reader with scripting off,
    and half this site's readers are machines that will take the chips from the markup regardless.
    """
    return (f'<details class="provenance"><summary>{e(frase)}</summary>'
            f'<div class="chips">{fichas}</div></details>')


def banda(corpo, fundo=""):
    """A full-bleed band carrying its own ground, with a `.folha` INSIDE it.

    This is the structural half of the adopted design, and the reason the front page's sections
    read as sections. One ground for a whole page is why they ran together: hairlines alone cannot
    separate blocks that are otherwise identical in tone and density. A newspaper varies the GROUND
    as well as the rule — a recessed band, a lifted panel, an ink band — and a reader navigates by
    that before reading a word.

        banda(corpo)            the base sheet
        banda(corpo, "sunk")    recessed, 1.13:1 below the base
        banda(corpo, "panel")   lifted, 1.08:1 above it
        banda(corpo, "ink")     ink, with its own text colours in the stylesheet

    Used in a rhythm and with restraint — base, base, recessed, base — because a page that
    alternates every block is as flat as one that alternates none.

    The band must be OUTSIDE `.folha` to be full-bleed, which is why `pagina()` takes
    `corpo_em_bandas`: a page that bands itself opens and closes its own sheets, and the shell
    stops wrapping the body in one.
    """
    cls = f"band band--{fundo}" if fundo else "band"
    return f'<div class="{cls}"><div class="folha">{corpo}</div></div>'


def datalinha(hoje, dias=None):
    dta = data_pt(hoje)
    direita = ""
    if dias is not None and dias >= 0:
        direita = (f'<div>Faltam <b>{dias} dia{"s" if dias != 1 else ""}</b> para o '
                   f'Startup Summit Lisbon 2026</div>' if dias else
                   '<div><b>Hoje</b>: Startup Summit Lisbon 2026</div>')
    # THE SPLIT. Until v0.13.0 these were one row: the dateline, the countdown and the four
    # operator links ran together in a single grey mono line, set identically, so a reader could
    # not tell which were the paper's and which were the machinery's. A wallet balance sitting
    # immediately above a newspaper's masthead is disorienting, and on a phone the row wrapped to
    # four lines — about 130px of chrome before the publication's name, which is the best thing on
    # the site arriving under a version string.
    #
    # Now there are two, and the order ranks them: `.utility` is a thin operator strip, first and
    # visually subordinate; `.datalinha` is editorial — Lisbon, the date, the countdown — in the
    # serif, ruled top and bottom, sitting directly above the masthead where a newspaper puts it.
    # Same links, legible ranking. The operator strip collapses to one scrollable line on a phone.
    return (utilitarios("{raiz}")
            + f'<div class="datalinha"><div>Lisboa · {dta}</div>{direita}</div>')


MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
        "sexta-feira", "sábado", "domingo"]


def data_pt(iso, com_dia_da_semana=True):
    import datetime
    d = datetime.date.fromisoformat(iso)
    base = f"{d.day} de {MESES[d.month - 1]} de {d.year}"
    return f"{DIAS[d.weekday()]}, {base}" if com_dia_da_semana else base


def mancheta(aqui, raiz):
    ligacoes = []
    for sid, rot in SECCOES:
        cls = ' class="aqui"' if aqui == sid else ""
        ligacoes.append(f'<a href="{raiz}{sid}/"{cls}>{rot}</a>')
    ligacoes.append('<span class="sep">|</span>')
    for sid, rot in EXTRA:
        cls = ' class="aqui"' if aqui == sid else ""
        ligacoes.append(f'<a href="{raiz}{sid}/"{cls}>{rot}</a>')
    return (
        f'<div class="mast">'
        f'<h1 class="nome"><a href="{raiz}">{e(TITULO)}</a></h1>'
        f'<div class="sub"><a href="{raiz}">{e(SUBTITULO)}</a></div>'
        f'<div class="lema">{e(LEMA)}</div></div>'
        f'<nav class="nav">{"".join(ligacoes)}</nav>'
    )


def bloco_agente(rel, fontes_n=None, raiz=""):
    """The "for an agent" block. The site gate requires it on every page, for the same reason this
    site exists: a page a machine cannot read is a page that, for half its readers, does not exist.

    The links are RELATIVE, not anchored at the root. A `/llms.txt` link only resolves when the
    site is served from the root of a domain, and this one is built and checked as a tree of files
    — the validator's second check walks every href and fails when one is not on disk. Relative,
    they work in both places."""
    extra = (f' Esta página assenta em {fontes_n} ficheiro(s) congelado(s), '
             f'cada um com o seu SHA-256 no registo.' if fontes_n else "")
    return (
        f'<div class="agent"><b>Para um agente.</b> Esta página é gerada a partir de ficheiros '
        f'JSON em <code>dados/</code> por <code>build/build.py</code>; nada nela é escrito à mão. '
        f'O índice legível por máquina está em <a href="{raiz}llms.txt">llms.txt</a> e o manifesto '
        f'com o hash de cada ficheiro de dados em '
        f'<a href="{raiz}ficheiros/">ficheiros/</a>.{extra} '
        # The same link as the dateline badge, and for the same reason: the "for an agent" block
        # is where a machine reads which version this page is, and a number with no route to what
        # changed in it makes whoever reads it guess where to look.
        f'Versão <a class="ver" href="{raiz}admin/versions.html#{VERSAO}">{VERSAO}</a> · fonte: '
        f'<a href="{GH}">{GH.split("//")[1]}</a> · ficheiro: <code>{e(rel)}</code>.</div>'
    )


def bloco_declaracao(nomeia_pessoas=False, raiz="/"):
    """ONE LINE, and a page where it is explained.

    Until v0.2.0 this was a five-line paragraph on every page of the site. Repeated thirty times, a
    notice stops being read: the reader learns the shape of the block and skips it, which is the
    opposite of what a notice is for. It becomes one line in the footer, at the right weight, and
    the explanation lives once at /proveniencia/ — which is also where the most interesting thing
    this publication has to say about itself lives, and it never fitted in a repeated block: WHICH
    model wrote what, from which provider, and when."""
    aviso = (f' Esta página nomeia pessoas — '
             f'<a href="{raiz}aviso/">o que é detido sobre elas e como sair</a>.'
             if nomeia_pessoas else "")
    return (
        f'<p class="declaracao">Escrito por agentes de IA, com curadoria de um editor humano '
        f'nomeado. Cada afirmação assenta numa cópia congelada e hasheada da sua fonte; quando '
        f'não se consegue confirmar, a página di-lo em vez de a omitir. '
        f'<a href="{raiz}proveniencia/">Quem fez o quê</a>.{aviso}</p>'
    )


def rodape(raiz):
    ligacoes = " · ".join(f'<a href="{raiz}{sid}/">{rot}</a>' for sid, rot in RODAPE)
    ligacoes += (f' · <a href="{raiz}{BASTIDORES[0]}/">{BASTIDORES[1]}</a>'
                 f' · <a href="{raiz}admin/versions.html">Versões</a>')
    return (
        f'<div class="rodape g4">'
        f'<div class="col sp6"><div class="sect">Ficha técnica</div>'
        f'<p class="sm">Editor de registo: Dinis Cruz. Pesquisa, redação e verificação: agentes, '
        f'cada um nomeado no registo de execução que fez o trabalho.</p></div>'
        f'<div class="col sp6"><div class="sect">Fontes</div>'
        f'<p class="sm">Todas obtidas, congeladas byte a byte e verificadas por hash em cada '
        f'construção. <a href="{raiz}registo/">O registo</a> lista-as; '
        f'<a href="{raiz}metodo/">o método</a> explica-o.</p></div>'
        f'<div class="col sp6"><div class="sect">Proteção de dados</div>'
        f'<p class="sm">Responsável: Dinis Cruz. Base: interesses legítimos. Remoção incondicional '
        f'a pedido; nunca se publica o motivo. <a href="{raiz}aviso/">O aviso</a>.</p></div>'
        f'<div class="col sp6"><div class="sect">Parte de</div>'
        f'<p class="sm"><a href="{PAI}">newsroom.sgit.ai</a> — uma instância do argumento. Este '
        f'site é nativamente português; não é uma tradução.</p></div>'
        f'</div>'
        f'<div class="agent" style="border:0;margin-top:18px;padding-top:0">{ligacoes}</div>'
    )


# --------------------------------------------------- ligação de entidades ---
# The index is read once and cached. It is `dados/entidades.json`, written by
# `build/entidades.py`, and it carries the formula that decides what a mention is. If it does not
# exist — the first build of a
# repositório novo, ou alguém a correr build.py isolado — o site constrói-se na mesma, sem
# links. A pass that refused to run without it would be a hidden dependency.
_ENTIDADES = None
_PADRAO = None


def _indice_entidades():
    global _ENTIDADES, _PADRAO
    if _ENTIDADES is None:
        dados = carregar("entidades.json") or {}
        _ENTIDADES = {}
        for x in dados.get("entidades", []):
            if x.get("ligavel_em_prosa"):
                _ENTIDADES[e(x["nome"])] = (x["url"], x["no"])
        if _ENTIDADES:
            # Longest names first: otherwise «Startup Summit» would catch the mention before
            # «Startup Summit Lisbon 2026» and link the wrong node just by matching first.
            alt = "|".join(re.escape(n) for n in
                           sorted(_ENTIDADES, key=len, reverse=True))
            _PADRAO = re.compile(r"(?<!\w)(" + alt + r")(?!\w)")
    return _ENTIDADES, _PADRAO


# What an entity link may NEVER cross. A link inside another link is invalid HTML and browsers
# unpick it differently; a name inside `<code>` is a file path and not a mention; and the inside of
# a tag is attribute territory, where an `<a>` would be extra text
# mais dentro de aspas. O `re.split` com captura devolve texto e marcação a alternar, e só o texto
# is touched.
# `<script>` and `<style>` hold their contents as RAW TEXT, not as markup, and the linker must not
# reach inside them. It used to: a page carrying its data in an inline
# `<script type="application/json">` had entity names inside that JSON rewritten into `<a class="ent"
# href="…">` — valid-looking HTML, and JSON with unescaped quotes in the middle of it, so the
# component reading it failed to parse and declared itself in error. The browser gate caught it; no
# other gate could have, because the page was well-formed and the damage was inside a string.
_MARCACAO = re.compile(
    r"(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>"
    r"|<a\b[^>]*>.*?</a>|<code\b[^>]*>.*?</code>|<[^>]+>)", re.S | re.I)


def ligar_entidades(corpo, raiz, excepto=None):
    """Turn each entity's first mention into a link to its page.

    The formula is published in `dados/entidades.json`, under `formula`, and this function is its
    only implementation. What it says is deliberately modest: a link here means "the text contains
    this name, exactly as the frozen source writes it", not "this text is about this entity". The
    difference is the same one that separates a lexicon tag from a characterisation, and it is why
    both are published formulas on this site.
    """
    indice, padrao = _indice_entidades()
    if not padrao:
        return corpo
    usados = set()
    if excepto:
        usados.add(excepto)

    def trocar(m):
        nome = m.group(1)
        url, no = indice[nome]
        if no in usados:
            return nome
        usados.add(no)
        return f'<a class="ent" href="{raiz}{url}">{nome}</a>'

    partes = _MARCACAO.split(corpo)
    for i in range(0, len(partes), 2):        # even indices are text; odd ones are markup
        if partes[i]:
            partes[i] = padrao.sub(trocar, partes[i])
    return "".join(partes)


def pagina(rel, titulo, descricao, corpo, aqui=None, nomeia_pessoas=False,
           fontes_n=None, com_declaracao=True, extra_head="", extra_body="",
           ligar=True, excepto=None, corpo_em_bandas=False):
    """A whole page. `rel` is the path relative to the root, and it decides the depth.

    `corpo_em_bandas` — the body already contains its own `.band`/`.folha` pairs, so the shell must
    not wrap it in a sheet of its own. A band has to sit outside `.folha` to be full-bleed; nesting
    one inside would give it the sheet's max-width and gutters and it would stop being a band.
    The chrome and the closing blocks still get a sheet each, because they are not banded."""
    profundidade = rel.count("/")
    raiz = "../" * profundidade if profundidade else ""
    if ligar:
        corpo = ligar_entidades(corpo, raiz, excepto)
    canonico = f"https://{HOST}/" + (rel if rel != "index.html" else "")
    canonico = canonico.replace("/index.html", "/")
    hoje = (carregar("registo.json") or {}).get("atualizado", "2026-09-14")
    dias = dias_para_evento(hoje)
    cabeca = datalinha(hoje, dias).replace("{raiz}", raiz or "")
    fecho = (f'{bloco_declaracao(nomeia_pessoas, raiz) if com_declaracao else ""}'
             f'{rodape(raiz)}{bloco_agente(rel, fontes_n, raiz)}')
    if corpo_em_bandas:
        # The first band carries the chrome and the masthead, so the stylesheet's
        # `.band:first-of-type > .folha` rule can keep its top padding small — adding a band's full
        # top padding above the operator strip cost 48px and put the mobile chrome back over 130px,
        # which is the number this design exists to bring down.
        corpo_final = (banda(f'{cabeca}{mancheta(aqui, raiz)}')
                       + corpo + banda(fecho))
    else:
        corpo_final = f'{cabeca}{mancheta(aqui, raiz)}{corpo}{fecho}'
    envolver = "" if corpo_em_bandas else "folha"
    return f"""<!doctype html>
<html lang="pt-PT">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)} · pt.newsroom.sgit.ai</title>
<meta name="description" content="{e(descricao)}">
<link rel="canonical" href="{canonico}">
<meta property="og:url" content="{canonico}">
<meta property="og:title" content="{e(titulo)} · pt.newsroom.sgit.ai">
<meta property="og:description" content="{e(descricao)}">
<meta property="og:type" content="website">
<meta name="generator" content="build/build.py {VERSAO}">
<link rel="icon" href="{raiz}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{raiz}assets/fonts.css">
<link rel="stylesheet" href="{raiz}assets/site.css">
<script type="module" src="{raiz}assets/components/pt-wallet/v1/v1.0/v1.0.0/pt-wallet.js"></script>
<script src="{raiz}assets/ponte.js" defer></script>
<script src="{raiz}assets/observador.js" defer></script>
<script src="{raiz}assets/conversa.js" defer></script>
<script type="module" src="{raiz}assets/components/pt-chat/v1/v1.0/v1.0.0/pt-chat.js"></script>
{extra_head}</head>
<body>
<div class="{envolver}">
{corpo_final}
</div>
<!-- The chat lives OUTSIDE .folha on purpose: it is a column of the document, not a block of the
     page, and putting it inside would make it inherit the sheet's max-width and gutters. -->
<pt-chat></pt-chat>
{extra_body}</body>
</html>
"""


def dias_para_evento(hoje):
    import datetime
    try:
        d = datetime.date.fromisoformat(hoje)
    except ValueError:
        return None
    return (datetime.date(2026, 9, 17) - d).days


def escrever(rel, texto):
    f = ROOT / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(texto, encoding="utf-8")
    return rel


def md_para_html(md, raiz=""):
    """The markdown renderer for stories. Deliberately small: a story is prose with source marks and
    nothing else. The `[[fonte:<id>]]` marks become chips linked into the register.

    `raiz` is the prefix back to the site root. An article lives at
    `artigos/<yyyy>/<mm>/<dd>/<slug>/` — five levels down — and a source chip written with a fixed
    path would work on one page and not the other. The site's link gate catches that, and did.

    A PARAGRAPH IS SEPARATED BY A BLANK LINE, not by a line break. This site's prose is written
    wrapped at 96 characters, like the rest of the repository; an earlier version of this function
    made every LINE a paragraph, and the result was prose broken mid-sentence and a `**bold**` that
    crossed the break and never closed. A paragraph's lines are joined before being formatted,
    which is what markdown always meant."""
    saida, lista, paragrafo = [], False, []

    def fechar_paragrafo():
        if paragrafo:
            saida.append(f'<p class="std">{inline(" ".join(paragrafo), raiz)}</p>')
            paragrafo.clear()

    def fechar_lista():
        nonlocal lista
        if lista:
            saida.append("</ul>")
            lista = False

    for linha in md.split("\n"):
        t = linha.rstrip()
        if re.match(r"^#{1,3} ", t):
            fechar_paragrafo(); fechar_lista()
            nivel = len(t) - len(t.lstrip("#"))
            classe = {1: "h-lead", 2: "h-2", 3: "h-3"}[nivel]
            saida.append(f'<h{min(nivel + 1, 3)} class="{classe}">'
                         f'{inline(t[nivel + 1:], raiz)}</h{min(nivel + 1, 3)}>')
            continue
        if t.startswith("- "):
            fechar_paragrafo()
            if not lista:
                saida.append("<ul>"); lista = True
            saida.append(f'<li class="sm">{inline(t[2:], raiz)}</li>')
            continue
        if not t.strip():
            fechar_paragrafo(); fechar_lista()
            continue
        fechar_lista()
        paragrafo.append(t.strip())
    fechar_paragrafo(); fechar_lista()
    return "\n".join(saida)


def inline(t, raiz=""):
    """Bold, code spans, links and source marks — in that order, and the order is the point.

    CODE SPANS ARE LIFTED OUT FIRST AND PUT BACK LAST. Two things were wrong here and each hid the
    other. Backticks were not handled at all, so every `like this` reached the page as literal
    backticks — invisible on an article, which rarely uses them, and all over the guidance, which
    is mostly file names. And because nothing protected a code span, a `[[fonte:…]]` written
    INSIDE one — the syntax being discussed rather than a citation — was turned into a live chip
    pointing into the register at an id that does not exist. A page explaining how a citation works
    was making one.

    That is the shape of mistake this site exists to avoid, so it is fixed in the renderer rather
    than worked around by whoever writes the prose: a mark inside a code span is a mark being
    quoted, and quoting a citation is not making one."""
    t = e(t)

    guardados = []

    def guardar(m):
        guardados.append(m.group(1))
        # \x00 cannot appear in the escaped text, and no rule below matches it, so a code span is
        # invisible to bold, to links and to the source mark until it is put back.
        return f"\x00{len(guardados) - 1}\x00"

    t = re.sub(r"`([^`]+)`", guardar, t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    # Italics AFTER bold, so `**x**` is already gone and cannot be read as two single marks. The
    # guards either side keep a literal asterisk literal: `2 * 3` and a footnote star are not
    # emphasis, and a rule that turned them into emphasis would be worse than no rule.
    # `(?!\s)` and `(?<!\s)`: the emphasised text may not begin or end with a space. Without
    # those two, `2 * 3 * 4` became `2 <i> 3 </i> 4` — caught by trying it rather than by reading
    # the pattern, which is the only way this kind of mistake is ever caught.
    t = re.sub(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    # A SITE-ABSOLUTE LINK IS RESOLVED AGAINST `raiz`, LIKE EVERY OTHER PATH HERE. Writing
    # `[x](/backoffice/y.html)` in a document is the natural thing to do and it is what a release
    # note already did — but this site is also served from a local file server during the browser
    # gate and from a preview under a subfolder, so a leading slash is the one form that works in
    # production and nowhere else. It is rewritten to the same relative prefix the rest of the
    # renderer uses. An external `https://` link is left exactly as written.
    def _ligacao(m):
        texto, alvo = m.group(1), m.group(2)
        if alvo.startswith("/") and not alvo.startswith("//"):
            alvo = raiz + alvo.lstrip("/")
        return f'<a href="{alvo}">{texto}</a>'

    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _ligacao, t)
    t = re.sub(r"\[\[fonte:([^\]]+)\]\]",
               lambda m: f'<a class="chip ok" href="{raiz}registo/#{e(m.group(1))}">'
                         f'{e(m.group(1))}</a>', t)
    t = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{guardados[int(m.group(1))]}</code>", t)
    return t

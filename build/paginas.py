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


def datalinha(hoje, dias=None):
    dta = data_pt(hoje)
    direita = ""
    if dias is not None and dias >= 0:
        direita = (f'<div>Faltam <b>{dias} dia{"s" if dias != 1 else ""}</b> para o '
                   f'Startup Summit Lisbon 2026</div>' if dias else
                   '<div><b>Hoje</b>: Startup Summit Lisbon 2026</div>')
    return (f'<div class="datalinha"><div>Lisboa · {dta}</div>{direita}'
            f'<div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap">'
            f'<a href="{{raiz}}aviso/">Aviso</a>'
            f'<a href="{{raiz}}metodo/">Método</a>'
            f'<a href="{{raiz}}api/">API</a>'
            f'<a href="{{raiz}}backoffice/" title="The operations console — in English">'
            f'Back office <span class="flag" aria-label="em inglês">EN</span></a>'
            f'<pt-wallet site-root="{{raiz}}"></pt-wallet>'
            f'<span class="ver">{VERSAO}</span></div></div>')


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
        f'Versão <span class="ver">{VERSAO}</span> · fonte: '
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
_MARCACAO = re.compile(r"(<a\b[^>]*>.*?</a>|<code\b[^>]*>.*?</code>|<[^>]+>)", re.S | re.I)


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
           ligar=True, excepto=None):
    """A whole page. `rel` is the path relative to the root, and it decides the depth."""
    profundidade = rel.count("/")
    raiz = "../" * profundidade if profundidade else ""
    if ligar:
        corpo = ligar_entidades(corpo, raiz, excepto)
    canonico = f"https://{HOST}/" + (rel if rel != "index.html" else "")
    canonico = canonico.replace("/index.html", "/")
    hoje = (carregar("registo.json") or {}).get("atualizado", "2026-09-14")
    dias = dias_para_evento(hoje)
    cabeca = datalinha(hoje, dias).replace("{raiz}", raiz or "")
    corpo_final = (
        f'{cabeca}{mancheta(aqui, raiz)}{corpo}'
        f'{bloco_declaracao(nomeia_pessoas, raiz) if com_declaracao else ""}'
        f'{rodape(raiz)}{bloco_agente(rel, fontes_n, raiz)}'
    )
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
{extra_head}</head>
<body>
<div class="folha">
{corpo_final}
</div>
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
    t = e(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\[\[fonte:([^\]]+)\]\]",
               lambda m: f'<a class="chip ok" href="{raiz}registo/#{e(m.group(1))}">'
                         f'{e(m.group(1))}</a>', t)
    return t

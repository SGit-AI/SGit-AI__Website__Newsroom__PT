#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — a casca de cada página: cabeça, mancheta, navegação, blocos de casa.

Definida uma vez aqui e aplicada em todo o lado por `build.py`. É o que impede o site de derivar
à medida que cresce: o distintivo de versão, a ligação canónica, o aviso de que isto é feito por
agentes, o bloco «para um agente» que o portão do site exige em cada página, e a ligação para o
aviso de proteção de dados em cada página que nomeia alguém.

Nada aqui é escrito à mão numa página. Uma página gerada que alguém edita à mão volta a ser
gerada por cima na construção seguinte, e a edição perde-se — por isso não se edita: edita-se
isto.
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

# As oito secções do resumo, mais o registo e o grafo. É a nav do desenho, pela ordem do desenho.
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
EXTRA = [("registo", "Registo"), ("grafo", "Grafo")]

# As páginas de mecânica, no rodapé e não na mancheta.
RODAPE = [
    ("artigos", "Os artigos"), ("metodo", "Método"), ("equipa", "A redação"),
    ("entregas", "Entregas de investigação"), ("redacao", "A mesa"),
    ("ficheiros", "Os ficheiros"), ("aviso", "Aviso de proteção de dados"),
    ("sobre", "Sobre e limites"),
]

# A consola de operações. No rodapé como maquinaria, e não na mancheta: não é a publicação, e está
# em inglês de propósito — o seu público é quem opera a redação, não quem lê o jornal.
BASTIDORES = ("backoffice", "Back office (EN)")

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
            f'<div style="display:flex;gap:18px;align-items:center">'
            f'<a href="{{raiz}}aviso/">Aviso de proteção de dados</a>'
            f'<a href="{{raiz}}metodo/">Método</a>'
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
        f'<div class="mast"><div class="nome">'
        f'<a href="{raiz}">pt.newsroom<span>.sgit.ai</span></a></div>'
        f'<div class="lema">{e(LEMA)}</div></div>'
        f'<nav class="nav">{"".join(ligacoes)}</nav>'
    )


def bloco_agente(rel, fontes_n=None, raiz=""):
    """O bloco «para um agente». O portão do site exige-o em cada página, e a razão é a mesma por
    que este site existe: uma página que uma máquina não consegue ler é uma página que, para
    metade dos seus leitores, não existe.

    As ligações são RELATIVAS e não ancoradas na raiz. Uma ligação `/llms.txt` só resolve quando o
    site está servido a partir da raiz de um domínio, e este é construído e conferido como uma
    árvore de ficheiros — o portão 2 do validador percorre cada href e falha quando um deles não
    existe no disco. Relativas, funcionam nos dois sítios."""
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
    """O bloco que diz o que isto é. Em cada página, porque um leitor pode chegar a qualquer uma."""
    aviso = (f' Esta página nomeia pessoas: o que é detido sobre elas, porquê, e como pedir a '
             f'remoção — sem dar razão nenhuma — está no '
             f'<a href="{raiz}aviso/">aviso de proteção de dados</a>.' if nomeia_pessoas else "")
    return (
        f'<div class="aviso-bloco"><p class="sm">Esta publicação é feita por agentes e lida por '
        f'uma pessoa nomeada antes de publicar. O editor de registo é <b>Dinis Cruz</b>, que '
        f'responde pelo que aqui está. Nenhuma revisão jurídica foi feita e nada aqui é '
        f'aconselhamento jurídico. Cada afirmação assenta numa cópia congelada e hasheada da '
        f'fonte; quando uma afirmação não se consegue confirmar, a página di-lo em vez de a '
        f'omitir.{aviso}</p></div>'
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


def pagina(rel, titulo, descricao, corpo, aqui=None, nomeia_pessoas=False,
           fontes_n=None, com_declaracao=True, extra_head="", extra_body=""):
    """Uma página inteira. `rel` é o caminho relativo à raiz, e decide a profundidade."""
    profundidade = rel.count("/")
    raiz = "../" * profundidade if profundidade else ""
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
<link rel="stylesheet" href="{raiz}assets/fonts.css">
<link rel="stylesheet" href="{raiz}assets/site.css">
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
    """O renderizador de markdown das histórias. Pequeno de propósito: uma história é prosa com
    marcas de fonte, e mais nada. As marcas `[[fonte:<id>]]` tornam-se fichas ligadas ao registo.

    `raiz` é o prefixo até à raiz do site. Um artigo vive em
    `artigos/<aaaa>/<mm>/<dd>/<slug>/` — cinco níveis — e uma ficha de fonte escrita com um
    caminho fixo funcionaria numa página e não na outra. O portão de ligações do site apanha-o,
    e apanhou.

    UM PARÁGRAFO É SEPARADO POR UMA LINHA EM BRANCO, não por uma quebra de linha. A prosa deste
    site é escrita com a linha cortada aos 96 caracteres, como todo o resto do repositório; uma
    versão anterior desta função fazia de cada LINHA um parágrafo, e o resultado era prosa partida
    a meio da frase e um `**negrito**` que atravessava a quebra e nunca fechava. As linhas de um
    parágrafo são juntadas antes de serem formatadas, que é o que o markdown sempre quis dizer."""
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

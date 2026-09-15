#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — builds every page from dados/ and conteudo/.

    python3 build/build.py

Nothing here is hand-written. Every number on a page comes from a data file, and the reason is not
tidiness: a number typed into a template stops agreeing with the data on the day the data changes,
and nobody notices, because nothing looks broken. The gate compares them.

THE FRONT PAGE IS THE DESIGN. Direction A, the broadsheet, chosen by the editor of record on 13
September 2026 out of four. The page order is the one the design fixes: dateline · masthead · the
eight sections · the lead story with its sources as chips and the three departments' state · two
secondaries and «Nesta edição» · «Em preparação» · «O grafo» with a path read aloud · «Esta semana
em Lisboa» and «O que diz a imprensa» · «Como se faz» with the page's only dark block · «Ficha
técnica».

Where this build differs from the 13 September artboard, it differs because the DATA differs, never
because the design was reinterpreted: the brief says "take the structure, not the numbers".
"""
import json
import re
import time
from pathlib import Path

import paginas as P
from paginas import (DADOS, ROOT, VERSAO, carregar, data_pt, dias_para_evento, e, escrever,
                     md_para_html, pagina)

ROT_ESTADO = {
    "confirmada": ("ok", "confirmada"), "aprovada": ("ok", "aprovada"),
    "nao_encontrada": ("falta", "não encontrada"), "rejeitada": ("falta", "rejeitada"),
    "fonte_inacessivel": ("miss", "sem fonte legível"),
    "disputada": ("disputa", "disputada"), "por_verificar": ("", "por verificar"),
}


def ficha_estado(estado, texto=None):
    cls, rot = ROT_ESTADO.get(estado, ("", estado))
    return f'<span class="chip {cls}">{e(texto or rot)}</span>'


# ============================================================== a primeira página ===
def primeira(d):
    reg, pes, org, ses, tem, mud = (d["registo"], d["pessoas"], d["orgs"], d["sessoes"],
                                    d["temas"], d["mudancas"])
    graf, ent, hist, verf = d["grafo"], d["entregas"], d["historias"], d["verif"]
    hoje = reg["atualizado"]

    publicadas = [h for h in hist["historias"] if h["estado"] == "publicado"]
    em_preparacao = [h for h in hist["historias"]
                     if h["estado"] in ("procurado", "rascunho", "verificado")]

    # WHICH ARTICLE TAKES WHICH FRONT-PAGE SLOT is a property of the ARTICLE, declared in its own
    # artigo.json, and not a table of slugs in here. A slug written into this file would be one more
    # place to forget on the day an article is renamed.
    #
    # And every block on this page LINKS to its article. A newspaper whose headline is not a
    # link is not a newspaper: it is a poster. That is what this was until now.
    slots = {h["bloco_primeira_pagina"]: h for h in hist["historias"]
             if h.get("bloco_primeira_pagina")}

    def liga(slot, texto, spec):
        """A block's title, linked to its article when there is one.

        `spec` is «<tag> <class>» — «h1 h-lead». An earlier version used the whole string as the
        class AND the first word as the tag, which produced `class="h1 h-lead"`: the class that
        sizes the heading stopped existing, and the result looked right in the HTML and wrong on
        the page."""
        tag, _, classe = spec.partition(" ")
        h = slots.get(slot)
        corpo = (f'<a href="{e(h["url"])}">{e(texto)}</a>' if h else e(texto))
        return f'<{tag} class="{classe}">{corpo}</{tag}>'

    def estado_do(slot):
        """The state chip for the article behind a block — a reader is entitled to know that what
        they are reading has not yet been through the editor."""
        h = slots.get(slot)
        if not h or h["estado"] == "publicado":
            return ""
        return (f'<a class="chip" href="{e(h["url"])}">ler o artigo · {e(h["estado"])}</a>')

    # --- a história principal e as duas secundárias ---------------------------
    # These three blocks used to be bespoke: each written from one measurement — the register's
    # readability, the event's two sets of stage names, the speaker list with a single capture —
    # and each linked to the article about that measurement. They were what this newsroom could
    # claim before it had published anything, and they were about its own plumbing. A reader who
    # came to read about AI in Portugal was met by three stories about how the site reads pages.
    # Now that there are published articles, the front page leads with them.
    #
    # Which article takes which slot stays a property of the ARTICLE, declared in its own
    # artigo.json. What changed is the fallback: with no slot declared, published articles fill
    # lead, secundaria-1 and secundaria-2 in order, so the front page is never empty and never
    # links to an article that no longer exists.
    ordem = sorted(publicadas, key=lambda h: (h.get("publicado_em") or h["data"], h["slug"]),
                   reverse=True)
    for nome in ("lead", "secundaria-1", "secundaria-2"):
        if nome not in slots:
            for h in ordem:
                if h not in slots.values():
                    slots[nome] = h
                    break

    lead = slots.get("lead")
    if lead:
        bloco_lead = (
            f'<div class="kick">{e(lead.get("antetitulo") or lead["seccao"])}</div>'
            + liga("lead", lead["titulo"], "h1 h-lead") +
            f'<p class="std">{e(lead.get("entrada", ""))}</p>')
        # The chips under the lead are the lead's OWN frozen sources, named by PUBLISHER rather
        # than by the id the register carries: «src-pol-03» means something to this repository and
        # nothing to a reader. They used to be the readability measurement, and they stayed put
        # when the headline changed — a block of numbers about one story under the title of another.
        por_fonte = {f["id"]: f for f in reg["fontes"]}
        fichas_lead = "".join(
            f'<span class="chip ok">{e(por_fonte[s]["publicador"])} · '
            f'{por_fonte[s]["bytes"]:,} bytes</span>'.replace(",", "\u202f")
            for s in lead.get("assenta_em", []) if s in por_fonte)
    else:
        bloco_lead = (
            '<div class="kick">Ainda não há primeira página</div>'
            '<h1 class="h-lead">Nenhum artigo foi publicado ainda.</h1>'
            '<p class="std">Quando o editor de registo escrever a linha num artigo, ele aparece '
            'aqui. Até lá esta publicação tem trabalho em preparação e diz que o tem, em vez de '
            'encenar uma primeira página.</p>')
        fichas_lead = ""

    estado_dep = (
        f'<div class="hair" style="padding-top:14px;display:flex;gap:24px;flex-wrap:wrap">'
        f'<div class="col sp6" style="flex:1;min-width:150px"><div class="sect">Pesquisa</div>'
        f'<p class="sm">{reg["contagem"]} páginas congeladas, {reg["contagem"]} hashes no registo.</p></div>'
        f'<div class="col sp6" style="flex:1;min-width:150px"><div class="sect">Redação</div>'
        f'<p class="sm">{len(publicadas)} histórias publicadas; escreve só a partir do que a pesquisa registou.</p></div>'
        f'<div class="col sp6" style="flex:1;min-width:150px"><div class="sect">Verificação</div>'
        f'<p class="sm">{d["n_verificadas"]} afirmações relidas nos bytes congelados.</p></div></div>')

    def secundaria(slot, topo=False):
        h = slots.get(slot)
        if not h:
            return ""
        n = (h.get("verificacao") or {}).get("confirmadas", 0)
        estilo = 'col sp10' if topo else 'hair col sp10" style="padding-top:22px'
        return (f'<div class="{estilo}">'
                f'<div class="kick">{e(h.get("antetitulo") or h["seccao"])}</div>'
                + liga(slot, h["titulo"], "h2 h-2") +
                f'<p class="sm">{e((h.get("entrada") or "")[:230])}</p>'
                f'<div class="chips"><span class="chip ok">{n} confirmada'
                f'{"s" if n != 1 else ""}</span>'
                f'<span class="chip">{e(h["seccao"])}</span></div></div>')

    sec1 = secundaria("secundaria-1", topo=True)
    sec2 = secundaria("secundaria-2")

    # --- «Nesta edição»: counts, every one of them from a file -----------------
    n_ent = sum(x["contagens"]["afirmacoes"] for x in ent["entregas"]) if ent else 0
    n_conf = sum(x["contagens"]["confirmadas"] for x in ent["entregas"]) if ent else 0
    # THE NUMBERS LEAD, AND THE SENTENCE QUALIFIES THEM. This was five rows of label + sentence,
    # with the counts — the thing a reader's eye goes looking for — buried mid-prose. A stat strip
    # puts them at 22px above their label, and the sentences that qualify them follow underneath.
    # Nothing is removed: every count still carries the file it came from in the line below it.
    nesta = (
        f'<div class="hair col sp8" style="padding-top:22px">'
        f'<div class="sect">Nesta edição</div>'
        + P.tira_de_numeros([
            ("Oradores", str(pes["contagem"])),
            ("Organizações", str(org["contagem"])),
            ("Fontes", str(reg["contagem"])),
            ("Grafo", f'{graf["contagens"]["nos"]} · {graf["contagens"]["arestas"]}'),
        ])
        + linha_conta("Programa", f'{ses["contagem"]} sessões lidas da agenda congelada · '
                                  f'{len(ses["palcos"])} palcos')
        + linha_conta("Entregas", f'{n_ent} afirmações entregues · {n_conf} com o excerto '
                                  f'encontrado nos bytes · nenhuma publicada')
        + linha_conta("O que sustenta", f'{len(reg["capturas"])} captura(s), todas com hash · '
                                        f'{org["marcadores"]} valores de marcador assinalados · '
                                        f'cada aresta do grafo é um verbo português')
        + '</div>')

    # --- «Em preparação» ------------------------------------------------------
    # The design says to list the draft and verified stories here, BY TITLE only. They are now
    # real articles, each with its dated folder and its final address: the title links there. What
    # does NOT link from here is the body — an unpublished article has no place on the front page,
    # and it is the editor of record who changes that.
    #
    # THE DATE ON EACH CARD. The design review caught its absence: a card on a news site needs a
    # date, because the date is what tells the reader whether they are looking at today.
    # /empresas/ already had one, in a column of its own; the front page did not. The date is the
    # article FOLDER's, which is the date it was opened, and the only one this site knows about
    # it.
    cartoes = "".join(
        f'<div class="col sp10"><div class="kick">{e(h.get("antetitulo") or h["seccao"])}</div>'
        f'<h3 class="h-3"><a href="{e(h["url"])}">{e(h["titulo"])}</a></h3>'
        f'<div class="chips"><span class="chip mono">{e(h.get("data", ""))}</span>'
        f'<span class="chip">{e(h["estado"])}</span>'
        f'{ficha_estado("confirmada", str(h["verificacao"]["confirmadas"]) + " confirmadas") if h.get("verificacao", {}).get("confirmadas") else ""}'
        f'</div></div>'
        for h in em_preparacao[:6])
    if not cartoes:
        cartoes = ('<p class="sm">Nenhum artigo em preparação. Todos os que existem estão '
                   'publicados, ou ainda nem pasta têm.</p>')

    legenda = ('<div class="mono" style="font-size:12px;color:var(--sec-2)">'
               'confirmado <span class="pastilha" style="background:var(--acento)"></span> '
               'disputado <span class="pastilha" style="background:var(--disputa)"></span> '
               'não encontrado <span class="pastilha" style="background:var(--falta)"></span></div>')

    # --- o grafo, com um caminho lido em voz alta -----------------------------
    caminho = frase_do_caminho(d)

    # --- o programa e a imprensa ---------------------------------------------
    linhas_ses = "".join(
        f'<tr><td>{e(dia_curto(s["dia"]))}</td>'
        f'<td class="mono">{e(s.get("inicio") or s.get("quando") or "—")}</td>'
        f'<td>{e(s["titulo"])}</td>'
        f'<td class="sm">{e(nome_palco(ses, s.get("palco")) or "—")}</td></tr>'
        for s in ses["sessoes"])

    imprensa = [s for s in reg["fontes"] if s["grupo"] == "imprensa"]
    linhas_imp = "".join(
        f'<tr><td>{e(s["publicador"])}</td>'
        f'<td class="sm">{e(s.get("tipo", "página"))}</td>'
        f'<td class="mono">{e(s["bytes"])} b</td>'
        f'<td><a class="chip ok" href="registo/#{e(s["id"])}">{e(s["sha256"][:8])}</a></td></tr>'
        for s in imprensa)
    excl = carregar("excluidas.json")
    nota_excl = ""
    if excl and excl["itens"]:
        i0 = excl["itens"][0]
        nota_excl = (f'<p class="sm it">Uma {len(excl["itens"])}.ª página '
                     f'({e(i0["id"].split("/")[-1])}) devolveu um erro e ficou fora do registo: '
                     f'não pode ser citada.</p>')

    # THE PROVENANCE, DEMOTED. The sentence is built from the same counts the chips carry, so the
    # two cannot disagree: the number of frozen pages and the number that returned no text are
    # derived here, not typed. The chips stay, one click behind, with the byte counts intact.
    n_f = len(lead.get("assenta_em", [])) if lead else 0
    n_c = (lead.get("verificacao") or {}).get("confirmadas", 0) if lead else 0
    frase_prov = (f'Assenta em {n_f} fonte{"s" if n_f != 1 else ""} congelada'
                  f'{"s" if n_f != 1 else ""} e hasheada{"s" if n_f != 1 else ""} · '
                  f'{n_c} afirmaç{"ões" if n_c != 1 else "ão"} reencontrada'
                  f'{"s" if n_c != 1 else ""} nos bytes') if lead else "Sem fontes"
    proveniencia_lead = P.proveniencia(fichas_lead + estado_do("lead"), frase_prov)

    # --- what has actually been published --------------------------------------
    # Everything published, newest day first, with the full archive one link away. Without it an
    # article the editor published into neither the lead nor a secondary would exist on the site
    # and be reachable from nowhere.
    por_dia_pub = {}
    for h in publicadas:
        por_dia_pub.setdefault(h.get("publicado_em") or h["data"], []).append(h)
    grupos_pub = []
    for dia, lista in sorted(por_dia_pub.items(), reverse=True)[:2]:
        cartoes_pub = "".join(
            f'<div class="painel col sp8">'
            f'<div class="kick">{e(h.get("antetitulo") or h["seccao"])}</div>'
            f'<h3 class="h-3"><a href="{e(h["url"])}">{e(h["titulo"])}</a></h3>'
            f'<p class="sm">{e((h.get("entrada") or "")[:190])}</p>'
            f'<div class="chips"><span class="chip ok">'
            f'{(h.get("verificacao") or {}).get("confirmadas", 0)} confirmadas</span>'
            f'<span class="chip">{e(h["seccao"])}</span></div></div>'
            for h in sorted(lista, key=lambda x: x["seccao"]))
        grupos_pub.append(
            f'<div class="hair" style="padding:14px 0 6px"><div class="sect">'
            f'{e(data_pt(dia, False))} · {len(lista)} artigo{"s" if len(lista) != 1 else ""}'
            f'</div></div><div class="g3" style="padding:6px 0 16px">{cartoes_pub}</div>')
    bloco_publicados = ""
    if grupos_pub:
        bloco_publicados = (
            P.abertura("Publicado", numero="01",
                       nota=f'{len(publicadas)} artigo'
                            f'{"s" if len(publicadas) != 1 else ""}, cada afirmação reencontrada '
                            f'nos bytes congelados',
                       fim='<a class="mono ac" style="font-size:12px;letter-spacing:.04em" '
                           'href="artigos/">Todos os artigos, dia a dia →</a>', maior=True)
            + "".join(grupos_pub))

    # The one major opener on this page, with the legend riding at its far end. The stylesheet's
    # note says to reach for this weight three or four times at most; the front page uses it once.
    abertura_preparacao = P.abertura(
        "Em preparação", numero="02",
        nota="com pasta e fontes congeladas, à espera da linha do editor", fim=legenda,
        maior=True)

    # THE BAND RHYTHM ON THIS PAGE: base (the lead), recessed («Em preparação»), base (the rest).
    # Three grounds and not six — the stylesheet's own note is that a page alternating every block
    # is as flat as one alternating none.
    banda_lead = P.banda(f"""
<div class="g12">
  <div class="col sp18" style="grid-column:span 7">
    {bloco_lead}
    {proveniencia_lead}
    {estado_dep}
    {nesta}
  </div>
  <div class="col sp22 borda-esq" style="grid-column:span 5;border-left:1px solid var(--filete);padding-left:40px">
    {sec1}{sec2}
  </div>
</div>
""")
    banda_preparacao = P.banda(f"""
{abertura_preparacao}
<div class="g3">{cartoes}</div>
""", "sunk")

    banda_publicados = P.banda(f"""
{bloco_publicados}
""") if bloco_publicados else ""

    corpo = banda_lead + banda_publicados + banda_preparacao + P.banda(f"""

<div class="rule g12" style="padding:22px 0 34px">
  <div class="col sp12" style="grid-column:span 4">
    <div class="sect">O grafo</div>
    <h2 class="h-2">Cada aresta é um verbo. Se o caminho não se lê em voz alta, a aresta está errada.</h2>
    <p class="sm">Um caminho lido do grafo, tal como está hoje:</p>
    {caminho}
    <a href="grafo/" class="mono ac" style="font-size:12px;letter-spacing:.04em">Abrir o grafo →
      {graf["contagens"]["nos"]} nós · {graf["contagens"]["arestas"]} arestas</a>
  </div>
  <div style="grid-column:span 8" class="painel">{svg_grafo(d)}</div>
</div>

<div class="rule g2" style="padding:22px 0 34px">
  <div class="col sp12">
    <div class="sect">Esta semana em Lisboa · tal como a agenda a publica</div>
    <div class="rolar"><table><thead><tr><th style="width:74px">Dia</th><th style="width:80px">Hora</th>
      <th>Sessão</th><th style="width:120px">Palco</th></tr></thead><tbody>{linhas_ses}</tbody></table></div>
    <p class="sm it">Títulos transcritos tal como estão na cópia congelada de {e(hoje)}, na língua
      em que o evento os publicou. Foram lidos do recuo estático da página: a agenda do evento
      renderiza por script e, obtida por HTTP, devolve apenas o título.</p>
  </div>
  <div class="col sp12">
    <div class="sect">O que diz a imprensa · páginas congeladas sobre o evento</div>
    <div class="rolar"><table><thead><tr><th>Publicação</th><th style="width:80px">Tipo</th>
      <th style="width:90px">Bytes</th><th style="width:90px">Hash</th></tr></thead>
      <tbody>{linhas_imp}</tbody></table></div>
    {nota_excl}
    <p class="sm it">Ligadas, nunca reproduzidas. O que cada uma diz fica na cópia congelada; o
      que esta publicação diz sobre elas é escrito por palavras suas.</p>
  </div>
</div>

<div class="rule g12" style="padding:22px 0 30px">
  <div class="col sp12" style="grid-column:span 8">
    <div class="sect">Como se faz · três departamentos, uma história com o processo à vista</div>
    <div class="g4">
      <div class="col sp6"><div class="mono xs">01</div><h3 class="h-3">Pesquisa</h3>
        <p class="sm">Encontra a fonte primária. Regista endereço, data e hash.</p></div>
      <div class="col sp6"><div class="mono xs">02</div><h3 class="h-3">Redação</h3>
        <p class="sm">Escreve a partir do que a pesquisa registou, e de mais nada.</p></div>
      <div class="col sp6"><div class="mono xs">03</div><h3 class="h-3">Verificação</h3>
        <p class="sm">Relê cada fonte citada. Marca cada afirmação: confirmada, disputada, não encontrada.</p></div>
      <div class="col sp6"><div class="mono xs">04</div><h3 class="h-3">Publicação</h3>
        <p class="sm">É um passo de build. O arquivo é o git. Sem palco, sem opinião.</p></div>
    </div>
    <p class="sm"><a href="redacao/">A mesa</a> mostra o quadro, o correio entre os departamentos e
      as afirmações de cada história coloridas pelo seu registo de verificação.
      <a href="entregas/">As entregas de investigação</a> mostram o que assistentes exteriores
      trouxeram, e o que aconteceu quando esta redação foi procurar cada excerto nos bytes.</p>
  </div>
  <div class="col sp10 escuro" style="grid-column:span 4">
    <div class="sect">Para redações</div>
    <h3 class="h-3" style="color:var(--papel)">Os agentes desta redação seguem políticas de
      comportamento publicadas.</h3>
    <p class="sm">O que cada agente pode escrever, o que tem de registar antes de escrever, e o
      que nunca pode afirmar sobre uma pessoa nomeada.</p>
    <a href="metodo/" class="mono" style="font-size:12px;letter-spacing:.04em">Ler as políticas →</a>
  </div>
</div>
""")
    return pagina("index.html", "Um mapa do ecossistema português de IA",
                  "Uma redação nativamente portuguesa que mapeia o ecossistema português de "
                  "inteligência artificial como um grafo. Cada afirmação anda para trás até uma "
                  "cópia congelada e hasheada da sua fonte.",
                  corpo, aqui=None, nomeia_pessoas=False, fontes_n=reg["contagem"],
                  corpo_em_bandas=True)


def linha_conta(rot, val):
    return (f'<div style="display:flex;gap:12px;align-items:baseline">'
            f'<span class="mono" style="font-size:12px;color:var(--sec-2);min-width:92px">{e(rot)}</span>'
            f'<span class="sm">{e(val)}</span></div>')


def dia_curto(dia):
    if not dia:
        return "—"
    m = re.search(r"(\d{1,2})\s+(September|setembro)", dia)
    return f"{m.group(1)} set" if m else dia.split("—")[0].strip()[:12]


def nome_palco(ses, pid):
    return next((p["nome"] for p in ses["palcos"] if p["id"] == pid), None) if pid else None


def frase_do_caminho(d):
    """Um caminho real do grafo, lido em voz alta em português. Escolhido pelos dados, não
    escrito à mão: se as arestas mudarem, a frase muda."""
    g, o = d["grafo"], d["ontologia"]
    N = {n["id"]: n for n in g["nos"]}
    L = {}
    for a in o["arestas"]:
        L.setdefault(a["verbo"], a)
    ev = next((n for n in g["nos"] if n["tipo"] == "Evento"), None)
    if not ev:
        return '<p class="caminho">O grafo ainda não tem um caminho para ler.</p>'
    sessao = next((a for a in g["arestas"] if a["verbo"] == "parte_de" and a["destino"] == ev["id"]
                   and N[a["origem"]].get("url")), None)
    local = next((a for a in g["arestas"] if a["verbo"] == "decorre_em" and a["origem"] == ev["id"]), None)
    if not (sessao and local):
        return '<p class="caminho">O grafo ainda não tem um caminho para ler.</p>'
    s_rot, ev_rot, l_rot = N[sessao["origem"]]["rotulo"], ev["rotulo"], N[local["destino"]]["rotulo"]
    palco = next((a for a in g["arestas"] if a["verbo"] == "no_palco" and a["origem"] == sessao["origem"]), None)
    cauda = ""
    if palco:
        cauda = (f', e está no <span class="v">{e(L["no_palco"]["verbo"])}</span> '
                 f'{e(N[palco["destino"]]["rotulo"])}')
    return (f'<p class="caminho">«{e(s_rot)}» <span class="v">parte de</span> {e(ev_rot)}, '
            f'que <span class="v">decorre em</span> {e(l_rot)}{cauda}.</p>')


def svg_grafo(d):
    """Um desenho pequeno do grafo real: o evento no centro, e os vizinhos mais ligados à volta.
    As posições são calculadas, os rótulos vêm dos nós, e as cores vêm dos tipos da ontologia."""
    import math
    g, o = d["grafo"], d["ontologia"]
    N = {n["id"]: n for n in g["nos"]}
    cor = {t["id"]: t["cor"] for t in o["tipos"]}
    ev = next((n for n in g["nos"] if n["tipo"] == "Evento"), None)
    if not ev:
        return '<p class="sm" style="padding:18px">Ainda não há grafo para desenhar.</p>'
    vizinhos = []
    vistos = set()
    for a in g["arestas"]:
        for outro, verbo in ((a["destino"], a["verbo"]), (a["origem"], a["verbo"])):
            pass
    for a in g["arestas"]:
        if a["origem"] == ev["id"] and a["destino"] in N:
            par = (a["destino"], a["verbo"])
        elif a["destino"] == ev["id"] and a["origem"] in N:
            par = (a["origem"], a["verbo"])
        else:
            continue
        if par[0] in vistos or N[par[0]]["tipo"] in ("Fonte", "Captura"):
            continue
        vistos.add(par[0])
        vizinhos.append(par)
    vizinhos = vizinhos[:8]
    W, H, cx, cy = 860, 330, 430, 158
    arestas, nos, rotulos, verbos = [], [], [], []
    nos.append(f'<circle cx="{cx}" cy="{cy}" r="22" fill="{cor.get("Evento", "#17181c")}"/>')
    rotulos.append(f'<text x="{cx}" y="{cy + 40}" text-anchor="middle" font-weight="600">'
                   f'{e(ev["rotulo"][:34])}</text>')
    for i, (nid, verbo) in enumerate(vizinhos):
        ang = math.pi * (0.12 + 0.76 * (i / max(1, len(vizinhos) - 1)))
        x = cx + math.cos(ang + math.pi) * 300
        y = cy + math.sin(ang + math.pi) * 118 * (1 if i % 2 else -1)
        x, y = max(90, min(W - 90, x)), max(40, min(H - 55, y))
        n = N[nid]
        arestas.append(f'<path d="M{cx} {cy} L{x:.0f} {y:.0f}"/>')
        nos.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="12" '
                   f'fill="{cor.get(n["tipo"], "#8a8d94")}"/>')
        rotulos.append(f'<text x="{x:.0f}" y="{y - 20:.0f}" text-anchor="middle" font-size="12">'
                       f'{e(n["rotulo"][:26])}</text>')
        verbos.append(f'<text x="{(cx + x) / 2:.0f}" y="{(cy + y) / 2 - 5:.0f}" '
                      f'text-anchor="middle">{e(verbo.replace("_", " "))}</text>')
    tipos = " · ".join(sorted({N[n]["tipo"] for n, _ in vizinhos} | {"Evento"}))
    return (f'<svg width="100%" height="330" viewBox="0 0 {W} {H}" style="display:block" '
            f'role="img" aria-label="O grafo à volta do evento">'
            f'<g stroke="#c9c2ae" stroke-width="1.2" fill="none">{"".join(arestas)}</g>'
            f'<g font-family="IBM Plex Mono, Menlo, monospace" font-size="10" fill="#0f766e">'
            f'{"".join(verbos)}</g><g>{"".join(nos)}</g>'
            f'<g font-family="Newsreader, Georgia, serif" font-size="13" fill="#17181c">'
            f'{"".join(rotulos)}</g>'
            f'<g font-family="IBM Plex Mono, Menlo, monospace" font-size="10" fill="#6b6e76">'
            f'<text x="16" y="{H - 10}">{e(tipos)}</text></g></svg>')


# ==================================================================== secções ===
DESCRICAO_SECCAO = {
    "empresas": ("As empresas", "Organizações derivadas das fontes congeladas, nunca escritas à "
                 "mão. Não há registo comercial aberto em Portugal, por isso esta camada não pode "
                 "ser completa — e o tamanho do que não se vê está dito na página."),
    "protagonistas": ("Os protagonistas", "Pessoas nomeadas nas listas que as próprias fontes "
                      "publicam, na sua qualidade profissional. Nome, papel e organização listados, "
                      "e mais nada: nenhuma biografia, nenhum contacto, nenhuma caracterização."),
    "instituicoes": ("As instituições", "Organismos públicos, reguladores e unidades de "
                     "investigação, e o que se consegue — ou não se consegue — ler do registo que "
                     "publicam."),
    "politicas": ("As políticas", "Políticas públicas anunciadas e, quando se consegue encontrar, "
                  "o instrumento legal que as cria. O segundo é frequentemente o problema."),
    "casos-de-uso": ("Os casos de uso", "Temas e etiquetas: o que as fontes congeladas dizem que "
                     "está a ser feito. Os temas são o vocabulário de quem os publicou; as "
                     "etiquetas são derivadas por uma fórmula publicada."),
    "codigo-aberto": ("O código aberto", "Projetos abertos portugueses. Ainda não há nenhuma fonte "
                      "congelada para esta secção."),
    "diaspora": ("A diáspora", "Quem saiu, quem voltou, e quem opera a partir de fora. Ainda não há "
                 "nenhuma fonte congelada para esta secção."),
    "eventos": ("Os eventos", "A matéria por onde esta redação começou: um evento que publica a sua "
                "própria lista de quem fala, e a vai mudando."),
}


# THE STATE VOCABULARY, WITH ACCENTS, BECAUSE AN IDENTIFIER IS NOT A WORD.
#
# A target source's state is `nao_resolve` in the file, and rightly so: it is an identifier, and
# this repository's identifiers are ASCII on purpose. What was wrong was what the generator did
# with it — `estado.replace("_", " ")` — which put «nao resolve» on the page. An unaccented
# word in the STATE VOCABULARY of a natively Portuguese publication, which is precisely the part
# meant to be authoritative — and whose footer says, in Portuguese, that this site is natively
# Portuguese and is not a translation of anything.
#
# The design review caught the missing character and said the right thing next: that it suggests
# the strings are being written somewhere that only accepts ASCII, and that this is worth a check
# rather than a fix in one place. It was: the audit of `dados/` found the same pattern in the
# board cards' titles, derived from the file name, which is also a slug.
#
# From here on a state has a written label, and a state with no label keeps the
# identificador tal e qual — visível e estranho — em vez de um identificador maquilhado de palavra.
ROTULOS_DE_ESTADO = {
    "congelada": "congelada",
    "nao_resolve": "não resolve",
    "nao_congelada": "não congelada",
    "por_congelar": "por congelar",
    "inacessivel": "inacessível",
    "parcial": "parcial",
}


def rotulo_de_estado(estado):
    return ROTULOS_DE_ESTADO.get(estado, estado)


def seccao(sid, d):
    """A section is a folder: seccoes/<id>/seccao.json is its editorial record, and this page is built
    from it. What the section covers, what it can and cannot claim TODAY, which sources it has yet
    to freeze and which questions are open all become data you can disagree with, rather than prose
    written into a template."""
    s = d["seccoes"].get(sid) or {}
    rot = s.get("rotulo") or DESCRICAO_SECCAO[sid][0]
    desc = s.get("ambito") or DESCRICAO_SECCAO[sid][1]
    g = d["grafo"]
    tipos = [t["id"] for t in d["ontologia"]["tipos"] if t.get("seccao") == sid]
    nos = [n for n in g["nos"] if n["tipo"] in tipos]
    artigos_sec = [h for h in d["historias"]["historias"] if h["seccao"] == sid]

    corpo = [f'<div class="rule" style="padding:26px 0 8px"><div class="sect">{e(rot)}</div></div>',
             f'<p class="std" style="padding-bottom:18px">{e(desc)}</p>']

    # the editorial record: what the section can and cannot claim today
    if s:
        alvos = "".join(
            f'<tr><td class="mono xs">{e(t["id"])}</td>'
            f'<td><span class="chip {"ok" if t["estado"] == "congelada" else "miss"}">'
            f'{e(rotulo_de_estado(t["estado"]))}</span></td>'
            f'<td class="sm">{e(t["porque"])}</td></tr>' for t in s.get("fontes_alvo", []))
        perguntas = "".join(f'<li class="sm">{e(x)}</li>' for x in s.get("perguntas_em_aberto", []))
        corpo.append(
            f'<div class="g2" style="padding-bottom:22px">'
            f'<div class="painel col sp8"><div class="sect">O que esta secção pode afirmar hoje</div>'
            f'<p class="sm">{e(s.get("o_que_pode_afirmar_hoje", ""))}</p></div>'
            f'<div class="painel col sp8" style="border-left:3px solid var(--aviso)">'
            f'<div class="sect">O que não pode</div>'
            f'<p class="sm">{e(s.get("o_que_nao_pode", ""))}</p></div></div>'
            f'<p class="std it" style="padding-bottom:18px">'
            f'{e(s.get("a_afirmacao_honesta", ""))}</p>')
        if alvos:
            corpo.append(
                f'<div class="hair" style="padding:16px 0"><div class="sect">As fontes desta '
                f'secção</div><div class="rolar" style="padding-top:8px"><table><thead><tr>'
                f'<th style="width:180px">Fonte</th><th style="width:140px">Estado</th>'
                f'<th>Porquê</th></tr></thead><tbody>{alvos}</tbody></table></div></div>')
        if perguntas:
            corpo.append(
                f'<div class="hair" style="padding:16px 0"><div class="sect">Perguntas em '
                f'aberto</div><ul style="max-width:48em">{perguntas}</ul></div>')

    # os artigos desta secção
    if artigos_sec:
        linhas_a = "".join(
            f'<tr><td class="mono xs">{e(h["data"])}</td>'
            f'<td><a href="../{e(h["url"])}">{e(h["titulo"])}</a></td>'
            f'<td><span class="chip">{e(h["estado"])}</span></td></tr>' for h in artigos_sec)
        corpo.append(
            f'<div class="rule" style="padding:22px 0 8px"><div class="sect">Os artigos desta '
            f'secção</div></div><div class="rolar"><table><thead><tr><th style="width:100px">Data'
            f'</th><th>Artigo</th><th style="width:130px">Estado</th></tr></thead>'
            f'<tbody>{linhas_a}</tbody></table></div>')

    if not nos:
        corpo.append(
            '<div class="rule" style="padding:22px 0 8px"><div class="sect">O grafo</div></div>'
            '<div class="painel"><p class="sm">Esta secção existe na ontologia e ainda não tem '
            'um único nó, porque nenhuma fonte congelada a alimenta. Está aqui vazia e a dizer '
            'que está vazia, em vez de ser escondida da navegação: o tamanho do que ainda não se '
            'vê faz parte do que esta publicação tem para dizer.</p></div>')
    else:
        por_tipo = {}
        for n in nos:
            por_tipo.setdefault(n["tipo"], []).append(n)
        for tipo, lista in sorted(por_tipo.items(), key=lambda kv: -len(kv[1])):
            defn = next(t for t in d["ontologia"]["tipos"] if t["id"] == tipo)
            visiveis = sorted(lista, key=lambda x: x["rotulo"].lower())[:400]

            def descricao(n):
                return e(n.get("papel") or n.get("definicao") or n.get("dia") or "")[:90]

            # A COLUMN EMPTY ON EVERY ROW IS NOT SHIPPED. Until v0.9.0 this table had
            # sempre três colunas, e em /empresas/ a do meio estava vazia em 67 das 67 linhas — uma
            # coluna em branco em produção, e pior para quem lê: essa coluna vazia empurrava «Fonte
            # congelada» about 1100px away from the name it belongs to, at 1440px wide, and the
            # eye had to cross the whole screen to pair a name with its source.
            #
            # The decision is per TABLE and not per row: if any node of this type has a description, the
            # column stays (and rows without one keep an empty cell, which is honest — the source
            # does not describe that node). If none has one, the column does not exist, and the source sits
            # next to the name. Gate 33 counts the cells and fails if an entirely empty column returns.
            tem_descricao = any(descricao(n) for n in visiveis)
            cabeca = ('<th>Nome</th><th>Como a fonte o descreve</th>'
                      '<th style="width:230px">Fonte congelada</th>' if tem_descricao else
                      '<th>Nome</th><th style="width:230px">Fonte congelada</th>')
            linhas = "".join(
                f'<tr><td>{e(n["rotulo"])}</td>'
                + (f'<td class="sm">{descricao(n)}</td>' if tem_descricao else "")
                + f'<td class="mono"><a href="../registo/#{e(n.get("fonte", ""))}">'
                  f'{e(n.get("fonte", "—"))}</a></td></tr>'
                for n in visiveis)
            corpo.append(
                f'<div class="hair" style="padding:18px 0"><h2 class="h-3">{e(defn["rotulo"])} '
                f'<span class="mono xs">({len(lista)})</span></h2>'
                f'<p class="sm" style="padding:6px 0 10px">{e(defn["definicao"])}</p>'
                f'<div class="rolar"><table><thead><tr>{cabeca}</tr></thead>'
                f'<tbody>{linhas}</tbody></table></div></div>')

    nomeia = "Pessoa" in tipos
    return pagina(f"{sid}/index.html", rot, desc, "".join(corpo), aqui=sid,
                  nomeia_pessoas=nomeia, fontes_n=len({n.get("fonte") for n in nos}))


# ===================================================================== registo ===
def o_que_assenta_nas_fontes(d):
    """Reverse index: a frozen source id -> everything on this site that stands on it.

    The register was the end of the road. Its own subtitle says a claim on this site walks BACK to
    here, and that was true in one direction only: you could land on a frozen file, see its hash,
    and have nowhere to go. The evidence is the foundation of everything this publication says, and
    from the foundation you could not reach the building.

    Four kinds of thing rest on a frozen file, and all four are derivable from files that already
    exist — no new state, nothing to keep in sync:

      · the RESEARCH DELIVERY that named it, when it arrived in one (the register id carries the
        delivery in its own path: <capture>/entregas/<delivery-id>/<source-id>)
      · the ARTICLES whose `assenta_em` lists it
      · the ENTITIES whose name was found in those bytes, with the number of occurrences
      · the GRAPH NODE grounded on it
    """
    idx = {}

    def por(sid):
        return idx.setdefault(sid, {"entrega": None, "artigos": [], "entidades": [], "nos": []})

    # A delivery source's register id IS <capture>/entregas/<delivery-id>/<source-id>, so the
    # delivery is read straight out of the id. The first version of this mapped through the
    # delivery's `congelada` path instead, and lost the link the moment a delivery was re-frozen
    # under a later capture: the path said 2026-09-15 while the register id still said 2026-09-14.
    # The id is the stable thing.
    ids_de_entrega = {x["id"] for x in (d["entregas"] or {}).get("entregas", [])}

    for h in d["historias"]["historias"]:
        for sid in h.get("assenta_em", []):
            por(sid)["artigos"].append(h)

    ents = carregar("entidades.json") or {}
    for en in (ents.get("entidades") if isinstance(ents, dict) else ents) or []:
        for nb in en.get("nos_bytes", []):
            por(nb["fonte"])["entidades"].append((en, nb.get("ocorrencias", 0)))

    for no in (d["grafo"] or {}).get("nos", []):
        if no.get("fonte"):
            por(no["fonte"])["nos"].append(no)
    return idx, ids_de_entrega


def registo(d):
    reg, excl = d["registo"], carregar("excluidas.json")
    assenta, ids_de_entrega = o_que_assenta_nas_fontes(d)

    def adiante(sid):
        """The forward links for one frozen file — the other half of the provenance path."""
        a = assenta.get(sid) or {"artigos": [], "entidades": [], "nos": []}
        fichas = []
        m = re.fullmatch(r"[^/]+/entregas/([^/]+)/(.+)", sid)
        if m and m.group(1) in ids_de_entrega:
            fichas.append(f'<a class="chip" href="../entregas/{e(m.group(1))}.html#{e(m.group(2))}">'
                          f'a entrega · {e(m.group(2))}</a>')
        for h in a["artigos"]:
            fichas.append(f'<a class="chip ok" href="../{e(h["url"])}">'
                          f'artigo · {e(h["titulo"][:38])}…</a>')
        for en, oc in sorted(a["entidades"], key=lambda p: -p[1])[:4]:
            fichas.append(f'<a class="chip" href="../{e(en["url"])}">{e(en["nome"][:26])} · '
                          f'{oc}×</a>')
        resto = len(a["entidades"]) - 4
        if resto > 0:
            fichas.append(f'<a class="chip" href="../entidades/">mais {resto} '
                          f'entidade{"s" if resto != 1 else ""}</a>')
        if not fichas:
            return '<span class="xs">nada assenta nesta fonte</span>'
        return f'<div class="chips">{"".join(fichas)}</div>'

    linhas = "".join(
        f'<tr id="{e(s["id"])}"><td class="mono">{e(s["id"])}</td>'
        f'<td><a href="{e(s["url"])}" rel="nofollow noopener">{e(s["publicador"])}</a></td>'
        f'<td class="sm">{e(s["grupo"])}</td>'
        f'<td class="mono">{s["bytes"]}</td>'
        f'<td class="mono xs">{e(s["sha256"][:16])}</td>'
        f'<td class="mono xs">{e(s["obtida"])}</td>'
        f'<td>{adiante(s["id"])}</td></tr>'
        for s in reg["fontes"])
    excluidas = ""
    if excl and (excl["itens"] or excl["por_resolver"]):
        it = "".join(f'<tr><td class="mono">{e(x["id"])}</td><td class="sm">{e(x.get("porque"))}</td></tr>'
                     for x in excl["itens"])
        pr = "".join(f'<tr><td class="mono">{e(x["id"])}</td><td class="sm">Não resolveu. '
                     f'{e(x.get("porque", ""))}</td></tr>' for x in excl["por_resolver"])
        excluidas = (
            f'<div class="rule" style="padding:26px 0 8px"><div class="sect">Fora do registo</div></div>'
            f'<p class="sm" style="padding-bottom:12px">{e(excl["nota"])}</p>'
            f'<div class="rolar"><table><thead><tr><th style="width:340px">Identificador</th>'
            f'<th>Porquê</th></tr></thead><tbody>{it}{pr}</tbody></table></div>')
    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">O registo · cada ficheiro congelado, com o seu hash</div></div>
<p class="std" style="padding-bottom:18px">{e(reg["nota"])}</p>
<div class="chips" style="padding-bottom:18px">
  <span class="chip ok">{reg["contagem"]} ficheiros</span>
  <span class="chip">{len(reg["capturas"])} captura(s): {e(", ".join(reg["capturas"]))}</span>
  <span class="chip">SHA-256 reverificado em cada construção</span></div>
<p class="std" style="padding-bottom:18px">A última coluna é o caminho ao contrário. Uma
afirmação deste site anda para trás até um destes ficheiros; daqui anda para a frente até
<b>tudo o que assenta nele</b> — a entrega de investigação que o nomeou, os artigos que o citam,
e as entidades cujo nome foi encontrado nestes bytes, com quantas vezes. Nenhuma dessas ligações
é escrita à mão: são derivadas dos mesmos ficheiros que fazem as páginas, e por isso não podem
discordar delas.</p>
<div class="rolar"><table><thead><tr><th style="width:290px">Identificador</th>
  <th style="width:150px">Publicador</th><th style="width:90px">Grupo</th>
  <th style="width:80px">Bytes</th><th style="width:140px">SHA-256</th>
  <th style="width:150px">Obtida</th><th style="width:360px">O que assenta nisto</th></tr></thead>
  <tbody>{linhas}</tbody></table></div>
{excluidas}
<div class="hair" style="margin-top:26px;padding-top:14px">
<p class="sm">As cópias congeladas têm a extensão <code>.snapshot</code> e não são servidas como
páginas deste site. São bytes de páginas de outras pessoas, guardados como prova. Publicar um
espelho navegável do site de outra organização sob este domínio contradiria a única regra que esta
publicação tem, que é ligar em vez de reproduzir — e o portão 2 falha a construção se uma delas
alguma vez for servida como página.</p></div>
"""
    return pagina("registo/index.html", "O registo",
                  "Cada página obtida, congelada byte a byte e hasheada. É até aqui que uma "
                  "afirmação deste site anda para trás — e daqui para a frente, até tudo o que "
                  "assenta em cada ficheiro.",
                  corpo, aqui="registo", fontes_n=reg["contagem"])


# ================================================================ entrevistas ===
def interviews(d):
    """The two interviews, with the prompts on the page rather than one click away.

    A prompt is copied, not read: by a person about to paste it into ChatGPT, often on a phone.
    Sending them to a raw markdown file to select-all is how you lose them. So the prompts are here,
    rendered from their markdown on every build and marked derived — a second VIEW of one copy,
    never a second copy. Gate 42 fails the build if the page and the markdown disagree.

    IN ENGLISH, like the rest of the operations surface. A visitor does not read this as content:
    it is how the newsroom works, not what it found. The prompts themselves keep the language they
    are pasted in — the Portuguese one is Portuguese because a Portuguese speaker pastes it.
    """
    iv = d.get("interviews")
    if not iv:
        return None

    sections = []
    for pack in iv["packs"]:
        blocks = []
        for pc in pack["pieces"]:
            blocks.append(
                f'<div class="hair" id="{e(pack["id"])}-{e(pc["file"].split("__")[0])}" '
                f'style="padding:20px 0 8px">'
                f'<div class="sect">{e(pc["title"])} · for {e(pc["for_whom"])}</div></div>'
                f'<p class="sm" style="padding-bottom:10px">{e(pc["why"])}</p>'
                f'<div class="chips" style="padding-bottom:10px">'
                f'<span class="chip">{e(pc["language"])}</span>'
                f'<span class="chip">{pc["lines"]} lines</span>'
                f'<span class="chip mono xs">{e(pc["sha256"][:12])}</span>'
                f'<a class="chip" href="../../{e(pc["path"])}">the raw file</a></div>'
                f'<div class="rolar"><pre class="mono xs" style="margin:0;padding:14px;'
                f'background:var(--papel);border:1px solid var(--filete);white-space:pre-wrap">'
                f'{e(pc["text"])}</pre></div>')
        sections.append(
            f'<div class="rule" id="{e(pack["id"])}" style="padding:30px 0 8px">'
            f'<div class="sect">{e(pack["title"])}</div></div>'
            f'<p class="std" style="padding-bottom:14px">{e(pack["why"])}</p>'
            f'<div class="chips" style="padding-bottom:6px">'
            f'<a class="chip" href="../../briefs/pack/{e(pack["folder"])}/README.md">'
            f'the method, in full</a></div>'
            + "".join(blocks))

    index = "".join(
        f'<a class="chip" href="#{e(p["id"])}">{e(p["title"])} · {len(p["pieces"])} pieces</a>'
        for p in iv["packs"])

    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">Interviews · the method and the
prompts</div></div>
<h1 class="h-2" style="max-width:26em">Two interviews, one mechanism, and opposite
directions.</h1>
<p class="std" style="padding:14px 0 12px">{e(iv["what_it_is"])}</p>
<div class="chips" style="padding-bottom:18px">{index}</div>

<div class="painel" style="margin-bottom:22px">
  <div class="sect">The rule that governs what comes out of here</div>
  <p class="sm" style="padding-top:8px">{e(iv["the_rule"])} An interview makes no exception to any
  rule of this house: three fields per person — listed role, listed organisation, the page that
  lists it — no contact detail in any file, and removal on request is unconditional and carries no
  reason. <a href="../../aviso/">The notice</a> says how. And nothing said aloud puts a story into
  published: that is a line the editor writes in a file.</p></div>

{"".join(sections)}

<div class="painel" style="margin-top:26px">
  <div class="sect">This text is derived</div>
  <p class="sm" style="padding-top:8px">The prompts above are rendered from
  <code>{e(iv["derived_from"])}</code> on every build, and never hand-written here. Content exists
  once, and gate 42 fails the build if this page and the markdown disagree — a derived file with no
  gate is a second copy under another name.</p></div>
"""
    return pagina("newsroom/interviews/index.html", "Interviews",
                  "Interviewing somebody to write, and interviewing the editor to know what to do. "
                  "The prompts, ready to copy.",
                  corpo, aqui="redacao")


# ==================================================================== review ===
def review(d):
    """The editor's review: what happened, what is his to answer, and a way to answer it.

    THE PAGE HOLDS NO STATE AND SAYS SO. Every answer captured here lives in the editor's browser
    until an agent writes it into a file. That is not a limitation to apologise for — this site is
    static because a static site can be audited, and a console that appeared to record a decision
    while recording nothing would be the one dishonest page on a publication whose whole argument is
    that nothing is asserted without bytes behind it.
    """
    rv = d.get("review") or {"questions": [], "changes": [], "count": 0}

    def context(q):
        """Everything the editor needs to answer WITHOUT leaving the page — and a link for when he
        wants the frozen bytes, which is the one thing this page will not inline.

        The quoted material stays Portuguese. The chrome is English because a visitor does not read
        this page as content; a claim, an excerpt and an article title are VALUES, and this
        repository's migration map renames vocabulary and never content.
        """
        parts = []
        if q["kind"] == "delivery":
            if q["confirmed"]:
                items = "".join(f"<li>{e(c)}</li>" for c in q["confirmed_claims"])
                parts.append(f'<p><b>{q["confirmed"]} of {q["claims"]}</b> claims were re-found in '
                             f'the frozen bytes:</p><ul>{items}</ul>')
            if q["without_bytes"]:
                parts.append(f'<p>{q["without_bytes"]} claim'
                             f'{"s" if q["without_bytes"] != 1 else ""} rest on a source that '
                             f'returned no readable body — they cannot be written whether or not '
                             f'the item is approved.</p>')
            if not q["confirmed"]:
                parts.append('<p><b>No claim in this item has bytes behind it.</b> Approving would '
                             'say this can be written as fact, and it cannot. Rejecting would say '
                             'the newsroom does not want the lead, which is usually false. Leaving '
                             'it open and commissioning research is the third answer, and normally '
                             'the right one.</p>')
        if q["kind"] == "ontology":
            parts.append('<p>Types proposed: ' + ", ".join(f"<b>{e(v)}</b>" for v in q["types"])
                         + '.</p>')
        if q["kind"] == "issue":
            for m in q.get("what_is_missing", [])[:3]:
                parts.append(f'<p>{e(m)}</p>')
        if q.get("why_it_matters"):
            parts.append(f'<p>{e(q["why_it_matters"])}</p>')
        parts.append(f'<p><a href="{e(q["url"])}">See the evidence and the full context →</a></p>')
        return "".join(parts)

    items_json = json.dumps([{
        "id": q["id"], "para": e(q["for_agent"]), "ficheiro": q["file"],
        "pergunta": e(q["question"]), "contexto": context(q),
    } for q in rv["questions"]], ensure_ascii=False)
    # `</` is the only sequence that can end a <script> block early, and JSON reads `<\/` as `</`.
    items_json = items_json.replace("</", "<\\/")

    change_rows = "".join(
        f'<tr><td class="mono xs">{e(c["when"])}</td>'
        f'<td class="sm">{e(c["kind"])}</td>'
        f'<td><a href="{e(c["url"])}">{e(c["what"])}</a></td>'
        f'<td class="mono xs">{e(c["version"] or "—")}</td></tr>' for c in rv["changes"])

    by_kind = {}
    for q in rv["questions"]:
        by_kind[q["kind"]] = by_kind.get(q["kind"], 0) + 1
    chips = "".join(f'<span class="chip">{n} · {e(k)}</span>'
                    for k, n in sorted(by_kind.items()))

    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">The editor of record's review</div>
</div>
<h1 class="h-2" style="max-width:26em">{rv["count"]} questions whose answer is yours.</h1>
<p class="std" style="padding:14px 0 12px">{e(rv["what_it_is"])}</p>
<div class="chips" style="padding-bottom:18px">{chips}</div>

<div class="painel" style="margin-bottom:22px">
  <div class="sect">What this page does, and what it does not</div>
  <p class="sm" style="padding-top:8px">Your answers stay <b>in your browser</b> and nowhere else.
  This site is static: it does not write to the repository, and a page that appeared to record a
  decision without recording it would be the one dishonest page on this publication. What it does
  is hold your words while you review — you can stop and come back — and hand them back as a block
  ready to paste into the agent that will turn them into files. <b>Nothing is a decision until the
  file exists.</b> {e(rv["the_rule"])}</p></div>

<div class="rule" style="padding:22px 0 12px"><div class="sect">The questions</div></div>
<pt-decisions><script type="application/json">{items_json}</script></pt-decisions>

<div class="rule" style="padding:26px 0 8px"><div class="sect">What happened</div></div>
<p class="sm" style="padding-bottom:12px">Every release, every published article and every
delivery, with the date it happened. This page does not know when your last review was — that is
knowledge living in your browser, not in a file anyone can read.</p>
<div class="rolar"><table><thead><tr><th style="width:110px">When</th>
  <th style="width:90px">What</th><th>Happened</th>
  <th style="width:90px">Version</th></tr></thead><tbody>{change_rows}</tbody></table></div>
"""
    # UNDER /admin/ AND NOT /newsroom/, AND THE REASON IS A GATE. Gate 13 — the delivery
    # quarantine — allows unapproved research items to be shown WITH THEIR STATE on exactly three
    # surfaces: /entregas/, /redacao/ and /admin/. This page is that kind of surface and shows
    # exactly that, so it uses the exemption for its stated purpose. `/newsroom/review/` is the
    # natural address once gate 13's list can take it, and `build/gates.py` is deny-listed: no agent
    # here may edit the gate that stops it. That one line is the editor's, and issue 008 asks for it.
    return pagina("admin/review/index.html", "The editor's review",
                  "What changed, what is left to decide, and somewhere to write the answers before "
                  "they go into the files.",
                  corpo, aqui="redacao",
                  extra_body='<script type="module" src="../../assets/components/pt-decisions/'
                             'v1/v1.0/v1.0.0/pt-decisions.js"></script>')


# ==================================================================== grafo ===
def grafo(d):
    g, o = d["grafo"], d["ontologia"]
    verbos = "".join(
        f'<tr><td class="mono">{e(a["verbo"])}</td><td class="mono">{e(a["inverso"])}</td>'
        f'<td class="sm">{e(a["dominio"])} → {e(a["alcance"])}</td>'
        f'<td class="sm it">{e(a["leitura"].replace("{s}", "X").replace("{t}", "Y"))}</td>'
        f'<td class="mono xs">{e(a["en"]["verbo"])}</td></tr>'
        for a in o["arestas"])
    proibidos = "".join(
        f'<tr><td class="mono" style="color:var(--falta)">{e(b["verbo"])}</td>'
        f'<td class="sm">{e(b["porque"])}</td></tr>' for b in o["proibidos"])
    tipos = "".join(
        f'<tr><td><span class="pastilha" style="background:{e(t["cor"])}"></span>'
        f'{e(t["rotulo"])}</td><td class="sm">{e(t["definicao"])}</td>'
        f'<td class="mono xs">{sum(1 for n in g["nos"] if n["tipo"] == t["id"])}</td></tr>'
        for t in o["tipos"])
    blocos = "".join(
        f'<span class="chip">{e(b["rotulo"])} · {b["nos"]} nós</span>' for b in g["blocos"] if b["nos"])
    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">O grafo</div></div>
<h1 class="h-2" style="max-width:22em">Cada aresta é um verbo português com um inverso distinto.
Se o caminho não se lê em voz alta, a aresta está errada.</h1>
<p class="std" style="padding:14px 0 18px">{e(o["nota"])}</p>
<div class="chips" style="padding-bottom:18px">
  <span class="chip ok">{g["contagens"]["nos"]} nós</span>
  <span class="chip ok">{g["contagens"]["arestas"]} arestas</span>
  <span class="chip">{g["contagens"]["tipos"]} tipos</span>
  <span class="chip">{g["contagens"]["verbos"]} verbos</span>
  <a class="chip" href="../dados/triplos.nt">triplos.nt</a>
  <a class="chip" href="../dados/grafo.json">grafo.json</a></div>
<div id="cy" data-grafo="../dados/grafo.json"></div>
<p class="sm" style="padding:10px 0 26px">Arraste para mover, roda para ampliar. Clique num nó para
o destacar; clique em dois com <b>shift</b> para ler o caminho entre eles em voz alta. Os blocos:
{blocos}</p>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Os verbos, e como se leem</div></div>
<p class="sm" style="padding-bottom:12px">O verbo é português e o campo
<code>en</code> é uma anotação — é a inversão que o resumo de comissionamento manda fazer, e a
única que não é cosmética. Uma leitura que toca numa Pessoa é invariável em género: esta
publicação não sabe o género de ninguém, a fonte não o publica, e deduzi-lo de um nome seria uma
inferência sobre uma pessoa nomeada, que o aviso recusa. O portão 10 volta a ler cada leitura e
falha a construção se uma delas usar um particípio concordado com uma pessoa.</p>
<div class="rolar"><table><thead><tr><th>Verbo</th><th>Inverso</th><th>Domínio → alcance</th>
  <th>Lê-se</th><th>en</th></tr></thead><tbody>{verbos}</tbody></table></div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Verbos proibidos</div></div>
<div class="rolar"><table><thead><tr><th style="width:180px">Verbo</th><th>Porque não existe</th>
  </tr></thead><tbody>{proibidos}</tbody></table></div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Os tipos</div></div>
<div class="rolar"><table><thead><tr><th style="width:180px">Tipo</th><th>Definição</th>
  <th style="width:60px">Nós</th></tr></thead><tbody>{tipos}</tbody></table></div>
"""
    extra = ('<script src="../assets/vendor/cytoscape.min.js"></script>'
             '<script src="../assets/grafo.js"></script>')
    return pagina("grafo/index.html", "O grafo",
                  "A ontologia e o grafo do ecossistema português de IA: verbos portugueses, cada "
                  "um com um inverso distinto, e cada nó com a fonte congelada de onde veio.",
                  corpo, aqui="grafo", fontes_n=len({n.get("fonte") for n in g["nos"]}),
                  extra_body=extra)


# ==================================================================== entregas ===
def entregas_indice(d):
    ent = d["entregas"]
    if not ent or not ent["entregas"]:
        corpo = ('<div class="rule" style="padding:26px 0 8px"><div class="sect">Entregas de '
                 'investigação</div></div><p class="std">Ainda não chegou nenhuma.</p>')
        return pagina("entregas/index.html", "Entregas de investigação",
                      "O que assistentes exteriores trouxeram, e o que aconteceu quando esta "
                      "redação foi procurar cada excerto nos bytes.", corpo, aqui=None)

    linhas = []
    for x in ent["entregas"]:
        c = x["contagens"]
        rev = x["revisao"]["estado"]
        estado = ficha_estado("confirmada", "{} com excerto".format(c["confirmadas"]))
        if c["nao_encontradas"]:
            estado += " " + ficha_estado("nao_encontrada",
                                         "{} sem excerto".format(c["nao_encontradas"]))
        if c["fonte_inacessivel"]:
            estado += " " + ficha_estado("fonte_inacessivel",
                                         "{} sem fonte".format(c["fonte_inacessivel"]))
        linhas.append(
            f'<tr><td><a href="{e(x["id"])}.html">{e(x["id"])}</a></td>'
            f'<td class="sm">{e(x["ferramenta"])} · {e(x["modelo"])}</td>'
            f'<td class="sm">{e(", ".join(x["seccoes"]))}</td>'
            f'<td class="mono xs">{c["itens"]} itens · {c["afirmacoes"]} afirmações</td>'
            f'<td>{estado}</td>'
            f'<td><span class="chip">{e(rev)}</span></td></tr>')
    estados = "".join(
        f'<tr><td><span class="pastilha" style="background:{e(s["cor"])}"></span>'
        f'{e(s["rotulo"])}</td><td class="sm">{e(s["o_que_significa"])}</td></tr>'
        for s in ent["estados"])

    # The briefs are linked from the repository and not republished as pages: the same
    # principle that governs the frozen copies — this site links, it does not reproduce. And
    # the pack states the rule that makes this more than style: content exists once. If it were here
    # e em briefs/pack/, os dois acabariam por discordar.
    RESUMOS = [
        ("12__research-brief-for-chatgpt.md", "O resumo para o ChatGPT",
         "Insiste em abrir cada página, copiar o excerto verbatim e entregar em partes, porque a "
         "ferramenta estrutura bem e é mais fraca a garantir que abriu mesmo cada endereço."),
        ("13__research-brief-for-perplexity.md", "O resumo para a Perplexity",
         "Apoia-se nas citações e numa série de consultas por secção, porque a ferramenta cita "
         "por omissão e pesquisa bem em português."),
    ]
    cartoes_b = []
    for f, titulo, porque in RESUMOS:
        caminho = ROOT / "briefs" / "pack" / "08__research-briefs" / f
        if not caminho.exists():
            continue
        n_linhas = len(caminho.read_text(encoding="utf-8").split("\n"))
        cartoes_b.append(
            f'<div class="painel col sp8">'
            f'<div class="mono xs">{e(f)} · {n_linhas} linhas</div>'
            f'<h3 class="h-3">{e(titulo)}</h3>'
            f'<p class="sm">{e(porque)}</p>'
            f'<a class="mono xs ac" href="../briefs/pack/08__research-briefs/{e(f)}">Ler o resumo →</a>'
            f'</div>')
    briefs = "".join(cartoes_b)
    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">Entregas de investigação · o fluxo
de revisão</div></div>
<h1 class="h-2" style="max-width:24em">Uma entrega é uma lista de pistas com proveniência, nunca
factos.</h1>
<p class="std" style="padding:14px 0 8px">{e(ent["o_que_e"])}</p>
<p class="std" style="padding-bottom:18px"><b>{e(ent["a_regra"])}</b></p>

<div class="painel" style="margin-bottom:26px">
<div class="sect" style="padding-bottom:8px">O que acontece a uma entrega, por esta ordem</div>
<div class="g4">
<div class="col sp6"><div class="mono xs">01 · validar</div><p class="sm">A entrega é conferida
contra o esquema publicado. Inválida, o ficheiro fica — faz parte do registo — e os erros vão para
a caixa do editor.</p></div>
<div class="col sp6"><div class="mono xs">02 · congelar</div><p class="sm">Cada endereço que a
entrega nomeia é obtido e congelado com SHA-256. A entrega traz endereços; um endereço não é
prova.</p></div>
<div class="col sp6"><div class="mono xs">03 · conferir o excerto</div><p class="sm">O texto que o
assistente diz ter lido é procurado nos bytes congelados. Se lá não estiver, a afirmação não
existe.</p></div>
<div class="col sp6"><div class="mono xs">04 · rever</div><p class="sm">O editor de registo lê cada
afirmação ao lado da sua fonte e aprova ou rejeita. É a única transição que uma execução automática
não pode fazer.</p></div>
</div></div>

<div class="rolar"><table><thead><tr><th>Entrega</th><th>Ferramenta</th><th>Secções</th>
  <th>Volume</th><th>Depois de conferir os excertos</th><th>Revisão</th></tr></thead>
  <tbody>{"".join(linhas)}</tbody></table></div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Os estados, e o que cada um significa</div></div>
<div class="rolar"><table><thead><tr><th style="width:220px">Estado</th><th>Significado</th></tr>
  </thead><tbody>{estados}</tbody></table></div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">De onde vem uma entrega · os dois
resumos de investigação</div></div>
<p class="sm" style="padding-bottom:12px">Um assistente exterior não recebe uma
pergunta: recebe um contrato. Os dois resumos abaixo dizem o que procurar, em que forma devolver,
e — a parte que faz a diferença — que cada endereço tem de ser aberto e cada excerto copiado da
página, porque é contra esse excerto que esta redação vai conferir os bytes. São dois e não um
porque as ferramentas falham de maneiras diferentes: uma cita bem por omissão e pesquisa bem em
português, a outra estrutura melhor e é mais fraca a garantir que abriu mesmo cada página.</p>
<div class="g2">{briefs}</div>
<p class="xs" style="padding-top:12px">Ambos, e o esquema JSON contra o qual uma entrega é
validada, estão no repositório em <code>briefs/pack/08__research-briefs/</code>. O esquema é a
razão por que uma entrega pode falhar a validação sem falhar como investigação: um tipo de
entidade que a ontologia ainda não tem é uma proposta de vocabulário, e essa é uma decisão do
editor sobre a ontologia, não um defeito da entrega.</p>
"""
    return pagina("entregas/index.html", "Entregas de investigação",
                  "O que assistentes exteriores trouxeram, e o que aconteceu quando esta redação "
                  "congelou cada fonte e foi procurar cada excerto nos bytes.",
                  corpo, aqui=None, fontes_n=sum(x["contagens"]["fontes"] for x in ent["entregas"]))


def entrega_pagina(x, d):
    rev = x["revisao"]
    c = x["contagens"]
    linhas_fontes = []
    for f in x["fontes"]:
        legivel = ('<span class="chip ok">legível</span>' if f.get("legivel")
                   else '<span class="chip miss">não legível</span>')
        porque = (f'<div class="xs" style="padding-top:6px">{e(f["porque"])}</div>'
                  if f.get("porque") else "")
        linhas_fontes.append(
            f'<tr id="{e(f["id"])}"><td class="mono">{e(f["id"])}</td>'
            f'<td><a href="{e(f["url"])}" rel="nofollow noopener">{e(f["publicador"])}</a>'
            f'<div class="xs">{e(f["titulo"])}</div></td>'
            f'<td class="mono xs">{e(f.get("formato", "—"))} · {f.get("bytes", 0)} b · '
            f'{f.get("caracteres_visiveis", 0)} car.</td>'
            f'<td>{legivel}{porque}</td>'
            f'<td class="mono xs">{e((f.get("sha256") or "—")[:16])}</td></tr>')
    fontes = "".join(linhas_fontes)

    itens = []
    for it in x["itens"]:
        dec = (rev.get("itens") or {}).get(it["id"], {})
        blocos_afirm = []
        for a in it["afirmacoes"]:
            loc = f' · {e(a["localizador"])}' if a.get("localizador") else ""
            nota = (f'<div class="xs" style="padding-top:4px;color:var(--aviso)">'
                    f'{e(a["nota"])}</div>' if a.get("nota") else "")
            blocos_afirm.append(
                f'<div class="hair" style="padding:12px 0">'
                f'<div style="display:flex;gap:10px;align-items:baseline;flex-wrap:wrap">'
                f'{ficha_estado(a["estado"])}'
                f'<span class="sm" style="color:var(--tinta);flex:1;min-width:260px">'
                f'{e(a["texto"])}</span></div>'
                f'<div class="xs" style="padding-top:6px">Excerto entregue: «{e(a["excerto"])}»</div>'
                f'<div class="xs">Fonte: <a href="#{e(a["fonte"])}">{e(a["fonte"])}</a>{loc}'
                f' · confiança declarada: {e(a.get("confianca_declarada") or "—")}</div>'
                f'{nota}</div>')
        afirm = "".join(blocos_afirm)
        propostas = ""
        if it["entidades_propostas"] or it["arestas_propostas"]:
            ents = "".join(f'<span class="chip">{e(en["type"])}: {e(en["name"])[:44]}</span>'
                           for en in it["entidades_propostas"])
            ars = "".join(f'<span class="chip">{e(ar["verb"])} → {e(ar["object"])[:34]}</span>'
                          for ar in it["arestas_propostas"])
            propostas = (
                f'<div class="hair" style="padding:12px 0"><div class="sect">Propostas</div>'
                f'<p class="xs" style="padding:6px 0">Entidades e arestas são PROPOSTAS. A pesquisa '
                f'volta a derivá-las da página congelada antes de alguma coisa chegar ao grafo; '
                f'nenhuma está no grafo hoje.</p>'
                f'<div class="chips">{ents}{ars}</div></div>')
        pd = it["verificacao_dados_pessoais"] or {}
        ficha_dec = (ficha_estado(dec["estado"]) if dec.get("estado")
                     else '<span class="chip">por rever</span>')
        texto_dec = dec.get("comentario") or ("Ainda sem decisão. Nada deste item aparece na "
                                              "primeira página nem num artigo.")
        tem_contactos = "sim" if pd.get("contains_contact_details") else "nenhum"
        tem_caracter = "sim" if pd.get("contains_characterisation") else "nenhuma"
        itens.append(
            f'<div class="painel" style="margin-bottom:18px" id="{e(it["id"])}">'
            f'<div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:baseline">'
            f'<div class="kick">{e(it["seccao"])} · {e(it["especie"])}</div>'
            f'<div class="mono xs">{e(it["id"])}</div></div>'
            f'<h3 class="h-3" style="padding:6px 0 8px">{e(it["titulo"])}</h3>'
            f'<p class="sm">{e(it["o_que_dizem_as_fontes"])}</p>'
            f'<p class="xs" style="padding-top:8px"><b>Porque importa</b> (segundo o assistente): '
            f'{e(it["porque_importa"])}</p>'
            f'<div class="sect" style="padding-top:14px">As afirmações, depois de conferidas nos bytes</div>'
            f'{afirm}{propostas}'
            f'<div class="hair" style="padding:12px 0"><div class="sect">Dados pessoais</div>'
            f'<p class="xs" style="padding-top:6px">Contactos: {tem_contactos} · '
            f'caracterização de pessoa nomeada: {tem_caracter} · '
            f'pessoas nomeadas: {len(pd.get("persons_named") or [])}</p></div>'
            f'<div class="hair" style="padding:12px 0">'
            f'<div class="sect">Decisão do editor</div>'
            f'<p class="sm" style="padding-top:6px">{ficha_dec} {e(texto_dec)}</p>'
            f'</div></div>')

    blocos_com = []
    for cm in rev.get("comentarios", []):
        sobre = f' · <a href="#{e(cm["sobre"])}">{e(cm["sobre"])}</a>' if cm.get("sobre") else ""
        blocos_com.append(
            f'<div class="msg"><div class="mono xs">{e(cm.get("quem"))} · '
            f'{e(cm.get("quando"))}{sobre}</div>'
            f'<p class="sm">{e(cm.get("texto"))}</p></div>')
    comentarios = "".join(blocos_com)
    if not comentarios:
        comentarios = ('<p class="sm">Ainda não há comentários. Um comentário é um ficheiro em '
                       '<code>redacao/revisoes/</code>: quem o escreveu, quando, sobre que item, e '
                       'o texto. Fica no repositório como tudo o resto.</p>')

    erros = ""
    if x["erros_de_esquema"]:
        lista = "".join(f'<li class="xs">{e(m)}</li>' for m in x["erros_de_esquema"][:40])
        mais = (f'<p class="xs">… e mais {len(x["erros_de_esquema"]) - 40}.</p>'
                if len(x["erros_de_esquema"]) > 40 else "")
        erros = (
            f'<div class="painel" style="border-left:3px solid var(--aviso);margin-bottom:22px">'
            f'<div class="sect">Esta entrega não valida contra o esquema publicado · '
            f'{len(x["erros_de_esquema"])} erros</div>'
            f'<p class="sm" style="padding:8px 0">O ficheiro fica no repositório tal como chegou, '
            f'porque faz parte do registo, e nada dele foi ingerido para o grafo. Os erros são de '
            f'forma, não de facto: sobretudo tipos de entidade fora da lista do esquema '
            f'(<code>Programa</code>, <code>InstrumentoJuridico</code>), identificadores fora do '
            f'padrão, e datas entregues como texto onde o esquema quer um objeto. Vários deles são '
            f'propostas de vocabulário que o esquema ainda não tem — e essas são uma decisão do '
            f'editor sobre a ontologia, não um defeito da entrega.</p>'
            f'<ul style="margin:0">{lista}</ul>{mais}</div>')

    # The example is written with this delivery's REAL ids, and the first suggested item is the one
    # with the most confirmed claims: an example with invented ids would make the editor translate it
    # before they can use it, and that is where ids get mistyped.
    ordenados = sorted(x["itens"], key=lambda it: -it["resumo"]["confirmada"])
    melhor = ordenados[0] if ordenados else None
    pior = next((it for it in x["itens"] if it["resumo"]["confirmada"] == 0), None)
    decisao = {
        "entrega": x["id"], "estado": "em_revisao",
        "decidido_por": "<o nome do editor>", "decidido_em": "<hoje>",
        "itens": {},
        "comentarios": [{"quem": "<quem>", "quando": "<datahora>",
                         "sobre": melhor["id"] if melhor else "<id do item>",
                         "texto": "<o comentário>"}],
    }
    if melhor:
        decisao["itens"][melhor["id"]] = {
            "estado": "aprovada",
            "comentario": f'{melhor["resumo"]["confirmada"]} de '
                          f'{len(melhor["afirmacoes"])} afirmações com o excerto nos bytes'}
    if pior:
        decisao["itens"][pior["id"]] = {
            "estado": "rejeitada",
            "comentario": "nenhuma afirmação tem fonte legível; abrir issue de pesquisa"}
    exemplo_decisao = json.dumps(decisao, indent=2, ensure_ascii=False)

    # THE CONTENTS. A delivery page is long — four stat tiles, a notes panel, a source table, an
    # item per lead with every claim under it, then the queries. Without an index the only way to
    # find the one item you care about is to scroll, and the one thing a reader of THIS page wants
    # to know first is which items survived the byte check. So the index carries that verdict in
    # its own column and jumps straight to the item.
    linhas_indice = []
    for it in x["itens"]:
        dec = (rev.get("itens") or {}).get(it["id"], {})
        n_ok = sum(1 for a in it["afirmacoes"] if a["estado"] == "confirmada")
        n_tot = len(it["afirmacoes"])
        cor = "ok" if n_ok == n_tot and n_tot else ("miss" if n_ok == 0 else "")
        ficha_dec_i = (ficha_estado(dec["estado"]) if dec.get("estado")
                       else '<span class="chip">por rever</span>')
        linhas_indice.append(
            f'<tr><td class="mono xs"><a href="#{e(it["id"])}">{e(it["id"])}</a></td>'
            f'<td><a href="#{e(it["id"])}">{e(it["titulo"])}</a></td>'
            f'<td class="sm">{e(it["especie"])}</td>'
            f'<td><span class="chip {cor}">{n_ok} de {n_tot} nos bytes</span></td>'
            f'<td>{ficha_dec_i}</td></tr>')
    indice = (
        f'<div class="rule" style="padding:22px 0 8px"><div class="sect">O que vem nesta entrega'
        f'</div></div>'
        f'<div class="rolar"><table><thead><tr><th style="width:110px">Item</th><th>Pista</th>'
        f'<th style="width:130px">Espécie</th><th style="width:150px">Excertos</th>'
        f'<th style="width:150px">Decisão</th></tr></thead>'
        f'<tbody>{"".join(linhas_indice)}</tbody></table></div>'
        f'<div class="chips" style="padding:12px 0 0">'
        f'<a class="chip" href="#as-fontes">As {c["fontes"]} fontes congeladas</a>'
        f'<a class="chip" href="#as-consultas">As {len(x["consultas"])} consultas</a>'
        f'<a class="chip" href="#as-decisoes">Comentários e decisões</a></div>')

    # Sibling deliveries: a part is one of eight, and a reader landing here should be able to reach
    # the others without going back to the index first.
    irmas = [y for y in d["entregas"]["entregas"] if y["id"] != x["id"]]
    nav_irmas = ""
    if irmas:
        nav_irmas = (
            '<div class="chips" style="padding:0 0 18px">'
            '<span class="mono xs" style="color:var(--sec-2)">Outras entregas</span>'
            + "".join(f'<a class="chip" href="{e(y["id"])}.html">{e(y["ferramenta"])} · '
                      f'{e(y["data"])} · {e(", ".join(y["seccoes"]))}</a>' for y in irmas)
            + '<a class="chip" href="./">Todas as entregas</a></div>')

    consultas = "".join(f'<li class="xs mono">{e(q)}</li>' for q in x["consultas"])
    corpo = f"""
<div class="rule" style="padding:26px 0 8px">
  <div class="sect">Entrega · {e(x["ferramenta"])} · {e(x["data"])}</div></div>
<h1 class="h-2" style="max-width:26em">{e(x["id"])}</h1>
<div class="chips" style="padding:14px 0 18px">
  <span class="chip">modelo: {e(x["modelo"])}</span>
  <span class="chip">parte {e(x["parte"] or "—")}</span>
  <span class="chip">resumo: {e(x["resumo_brief"])}</span>
  <span class="chip">secções: {e(", ".join(x["seccoes"]))}</span>
  <span class="chip {"ok" if x["esquema_valido"] else "miss"}">esquema:
    {"válido" if x["esquema_valido"] else f"{len(x['erros_de_esquema'])} erros"}</span>
  <span class="chip">revisão: {e(rev["estado"])}</span></div>

<div class="g4" style="padding-bottom:22px">
  <div class="painel col sp6"><div class="mono xs">Fontes</div>
    <div class="h-3">{c["fontes_legiveis"]}/{c["fontes"]}</div>
    <p class="xs">legíveis por máquina depois de congeladas</p></div>
  <div class="painel col sp6"><div class="mono xs">Excerto encontrado</div>
    <div class="h-3 e-confirmada">{c["confirmadas"]}</div>
    <p class="xs">de {c["afirmacoes"]} afirmações</p></div>
  <div class="painel col sp6"><div class="mono xs">Excerto não encontrado</div>
    <div class="h-3 e-nao_encontrada">{c["nao_encontradas"]}</div>
    <p class="xs">está nos bytes? não</p></div>
  <div class="painel col sp6"><div class="mono xs">Sem fonte legível</div>
    <div class="h-3 e-fonte_inacessivel">{c["fonte_inacessivel"]}</div>
    <p class="xs">nada se pode conferir contra elas</p></div>
</div>

{nav_irmas}
{indice}

{erros}

<div class="painel" style="margin-bottom:22px">
  <div class="sect">O que o assistente disse sobre o seu próprio trabalho</div>
  <p class="sm" style="padding-top:8px">{e(x["notas_do_assistente"])}</p></div>

<div class="rule" id="as-fontes" style="padding:22px 0 8px"><div class="sect">As fontes que a
entrega nomeia, depois de congeladas por esta redação</div></div>
<div class="rolar"><table><thead><tr><th style="width:110px">Id</th><th>Publicador</th>
  <th style="width:180px">Cópia congelada</th><th style="width:250px">Legível?</th>
  <th style="width:150px">SHA-256</th></tr></thead><tbody>{fontes}</tbody></table></div>

<div class="rule" style="padding:22px 0 12px"><div class="sect">Os itens, e cada afirmação
conferida contra os bytes</div></div>
{"".join(itens)}

<div class="rule" id="as-decisoes" style="padding:22px 0 8px"><div class="sect">Comentários e
decisões</div></div>
<div class="correio">{comentarios}</div>

<div class="painel" style="margin-top:22px">
<div class="sect">Como o editor de registo aprova ou rejeita</div>
<p class="sm" style="padding:8px 0">Uma decisão é um ficheiro, como tudo o resto nesta redação, e
fica no repositório onde qualquer pessoa a pode ler. O editor escreve
<code>redacao/revisoes/{e(x["id"])}.json</code> — ou corre <code>/newsroom-entregas</code>, que
percorre os itens um a um e escreve o ficheiro por ele. Um item sem entrada fica por rever, que é
o estado seguro; só <code>aprovada</code> o deixa ser escrito como facto, e só uma pessoa o
escreve.</p>
<div class="rolar"><pre class="mono xs" style="margin:0;padding:12px;background:var(--papel);
border:1px solid var(--filete);white-space:pre">{e(exemplo_decisao)}</pre></div>
<p class="xs" style="padding-top:10px"><b>Uma regra que o portão impõe e não é uma preferência:</b>
não se aprova um item cujas afirmações estejam todas «sem fonte legível». Aprovar quer dizer
«isto pode ser escrito como facto», e não há bytes para o sustentar. Se o item for valioso — e
vários destes são — o caminho é abrir um issue de pesquisa para encontrar uma fonte que se consiga
ler, e não baixar a barra.</p>
<p class="xs" style="padding-top:8px">Depois da decisão: <code>python3 build/entregas.py</code> →
<code>build/build.py</code> → <code>build/gates.py</code> → <code>node
admin/build/validate.js</code>. Os dois portões têm de imprimir OK antes de a versão subir.</p>
</div>

<div class="rule" id="as-consultas" style="padding:22px 0 8px"><div class="sect">As consultas que o assistente diz
ter feito · {len(x["consultas"])}</div></div>
<ul style="columns:2;column-gap:40px">{consultas}</ul>
"""
    return pagina(f"entregas/{x['id']}.html", f"Entrega {x['ferramenta']} · {x['data']}",
                  f"Uma entrega de investigação de {x['ferramenta']}, com cada afirmação conferida "
                  f"contra os bytes congelados da fonte que cita.",
                  corpo, aqui=None, fontes_n=c["fontes"])


# ====================================================================== a mesa ===
ORDEM_ISSUES = ["procurado", "registado", "congelado", "extraido", "redigido", "verificado",
                "revisto", "publicado", "parado"]


def mesa(d):
    issues, correio, runs = d["issues"], d["correio"], d["runs"]
    colunas = ""
    for est in ORDEM_ISSUES:
        blocos = []
        for i in issues:
            if i["estado"] != est:
                continue
            motivo = (f'<div class="xs" style="padding-top:6px;color:var(--aviso)">'
                      f'{e(i["motivo"])}</div>' if i.get("motivo") else "")
            blocos.append(
                f'<div class="cartao"><div class="mono xs">{e(i["id"])} · {e(i["seccao"])}</div>'
                f'<div style="padding-top:4px">{e(i["titulo"])}</div>{motivo}</div>')
        cartoes = "".join(blocos)
        n = sum(1 for i in issues if i["estado"] == est)
        colunas += (f'<div class="coluna"><div class="sect">{e(est)} '
                    f'<span class="mono xs">{n}</span></div>{cartoes}</div>')

    blocos_msg = []
    for m in correio:
        iss = f' · {e(m["issue"])}' if m.get("issue") else ""
        blocos_msg.append(
            f'<div class="msg"><div class="mono xs">{e(m["de"])} → {e(m["para"])} · '
            f'{e(m["quando"])}{iss}</div>'
            f'<div style="padding-top:2px"><b>{e(m["assunto"])}</b></div>'
            f'<p class="sm" style="padding-top:4px">{e(m["corpo"])}</p></div>')
    msgs = "".join(blocos_msg)

    linhas_run = []
    for r in runs:
        portoes = ('<span class="chip ok">verdes</span>' if r["portoes"]
                   else '<span class="chip falta">vermelhos</span>')
        linhas_run.append(
            f'<tr><td class="mono xs">{e(r["quando"])}</td><td class="sm">{e(r["prompt"])}</td>'
            f'<td class="sm">{e(r["modelo"])}</td>'
            f'<td class="mono xs">{e(", ".join(r["pastas_alteradas"]))}</td>'
            f'<td>{portoes}</td>'
            f'<td class="mono xs">{e(r.get("versao") or "—")}</td></tr>')
    execucoes = "".join(linhas_run)

    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">A mesa · o quadro, o correio e as
execuções</div></div>
<p class="std" style="padding-bottom:18px">Nada nesta página é desenhado à mão. A
sala é feita de <code>dados/redacao.json</code>, que por sua vez é contado a partir dos ficheiros
em <code>redacao/issues/</code>, <code>redacao/correio/</code>, <code>redacao/runs/</code> e do
trabalho por agente em <code>dados/comentarios.json</code>. Clique numa bancada para ver o que ela
faz, o que <b>recusa</b> fazer, e o que está à espera dela — e repare que não há maneira de mover
um cartão daqui: o estado de uma história vive nos ficheiros da pasta dela, e a coluna
«publicado» é a linha do editor de registo. O correio vem dos ficheiros em
<code>redacao/correio/</code>, e as execuções dos ficheiros em <code>redacao/runs/</code>. Um
departamento só escreve na sua própria pasta, e o portão 12 falha a construção se a diferença de
uma execução mostrar a pesquisa a escrever prosa ou a redação a tocar numa fonte. É o que faz
disto uma redação e não um script.</p>

<pt-newsroom-floor raiz="../"></pt-newsroom-floor>

<div class="rule" style="padding:34px 0 8px"><div class="sect">O mesmo quadro, sem
JavaScript</div></div>
<p class="xs" style="padding-bottom:12px">A sala acima precisa de um navegador que
corra módulos. Esta versão não, e por isso fica: metade dos leitores deste site são máquinas, e
uma redação que só se deixasse ler por uma delas seria a ironia errada. As duas saem dos mesmos
ficheiros.</p>
<div class="quadro" style="padding-bottom:34px">{colunas}</div>

<div class="rule g2" style="padding:22px 0 34px">
  <div class="col sp12"><div class="sect">O correio entre os departamentos</div>
    <p class="xs">Uma mensagem é um ficheiro markdown na caixa de entrada de quem a recebe. O
      correio nunca é apagado. A entrega é o ficheiro ter mudado de pasta.</p>
    <div class="correio">{msgs or '<p class="sm">Ainda não há correio.</p>'}</div></div>
  <div class="col sp12"><div class="sect">As execuções</div>
    <p class="xs">Cada passagem do ciclo escreve um registo: que instrução correu, que modelo a
      executou, que pastas mudaram, se os portões ficaram verdes e que versão foi publicada.</p>
    <div class="rolar"><table><thead><tr><th>Quando</th><th>Instrução</th><th>Modelo</th>
      <th>Pastas</th><th>Portões</th><th>Versão</th></tr></thead>
      <tbody>{execucoes or '<tr><td class="sm" colspan="6">Ainda não há execuções registadas.</td></tr>'}</tbody>
      </table></div></div>
</div>
"""
    return pagina("redacao/index.html", "A mesa",
                  "O quadro de trabalho, o correio entre os departamentos e o registo de cada "
                  "execução. Tudo a partir dos ficheiros que os agentes escreveram.",
                  corpo, aqui=None,
                  extra_body='<script type="module" src="../assets/components/'
                             'pt-newsroom-floor/v1/v1.0/v1.0.0/pt-newsroom-floor.js"></script>')


# ============================================================ páginas de texto ===
def metodo(d):
    reg = d["registo"]
    lex = d["lexico"]
    entradas = "".join(
        f'<tr><td>{e(x["rotulo"])}</td><td class="mono xs">{e(x["tipo"])}</td>'
        f'<td class="mono xs">{e(x["padrao"])}</td><td class="mono xs">{e(x["corre_sobre"])}</td></tr>'
        for x in lex["entradas"])
    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">Método · o que esta redação faz,
por esta ordem</div></div>
<h1 class="h-2" style="max-width:24em">Obter · congelar · hashear · extrair · comparar</h1>
<p class="std" style="padding:14px 0 18px">É o caminho que a secção
<a href="https://newsroom.sgit.ai/portugal/index.html">/portugal/</a> de newsroom.sgit.ai já corre,
copiado antes de se escrever aqui seja o que for, porque é a única parte deste método com prova de
funcionar. Quatro das suas propriedades sustentam tudo o resto.</p>

<div class="g2" style="padding-bottom:26px">
<div class="col sp10"><h3 class="h-3">1 · As capturas são datadas, não únicas</h3>
<p class="sm">Uma cópia congelada prova uma afirmação. Uma série prova uma trajetória e mostra o
que desapareceu. Numa matéria em movimento, a diferença É a notícia.</p></div>
<div class="col sp10"><h3 class="h-3">2 · Nunca se lê o site vivo ao publicar</h3>
<p class="sm">A extração corre contra a cópia congelada, por isso uma página não pode mudar por
baixo de uma afirmação sem que a mudança apareça como um hash novo.</p></div>
<div class="col sp10"><h3 class="h-3">3 · As cópias são <code>.snapshot</code>, não <code>.html</code></h3>
<p class="sm">São bytes de páginas de outras pessoas, guardados como prova. Uma extensão que não é
HTML impede-as de serem servidas ou indexadas como páginas deste site.</p></div>
<div class="col sp10"><h3 class="h-3">4 · O portão reverifica cada SHA-256 em cada construção</h3>
<p class="sm">Se uma cópia congelada foi editada, todas as afirmações que assentam nela ficam sem
suporte e a construção tem de parar. Hoje: {reg["contagem"]} ficheiros, todos reverificados.</p></div>
</div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">O que esta redação recusa, e onde a
recusa corre</div></div>
<p class="sm" style="padding-bottom:12px">As recusas correm no ponto de LEITURA, não
no de apresentação. Um contacto que chega aos dados e é apenas escondido por um template está a um
ciclo distraído de ser publicado.</p>
<div class="rolar"><table><thead><tr><th style="width:280px">A recusa</th><th>Onde corre</th></tr></thead>
<tbody>
<tr><td>Nenhum contacto de pessoa singular</td><td class="sm">
  <code>build/extract.py</code>, na função <code>sem_contactos</code>, antes de o campo chegar a um
  ficheiro. O portão 5 confere os ficheiros depois.</td></tr>
<tr><td>Nenhuma biografia reproduzida</td><td class="sm">
  O parágrafo de prosa do cartão nunca é lido para um ficheiro. O portão 6 falha a construção se
  algum campo for longo o suficiente para ser uma biografia.</td></tr>
<tr><td>Nenhuma razão para uma saída</td><td class="sm">
  <code>mudancas.json</code> regista a diferença e deixa a razão em branco. O portão 7 procura
  palavras que impliquem um motivo em todas as páginas geradas.</td></tr>
<tr><td>Nenhum alvo relatado como resultado</td><td class="sm">
  O evento declara «150+ speakers»; isso é um plano. O que este site conta são os cartões da cópia
  congelada. O portão 4 falha a construção se um alvo aparecer como resultado.</td></tr>
<tr><td>Nenhuma caracterização de pessoa nomeada</td><td class="sm">
  Uma etiqueta diz que a página contém certas palavras. As ligações entre entidades são feitas ao
  nível da organização.</td></tr>
</tbody></table></div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">O léxico · uma fórmula publicada</div></div>
<p class="sm" style="padding-bottom:8px">{e(lex["o_que_e"])}</p>
<p class="sm" style="padding-bottom:8px"><b>{e(lex["o_que_nao_e"])}</b></p>
<p class="sm" style="padding-bottom:12px">{e(lex["a_lingua_dos_padroes"])}</p>
<div class="rolar"><table><thead><tr><th>Etiqueta</th><th>Tipo</th><th>Padrão</th>
  <th>Corre sobre</th></tr></thead><tbody>{entradas}</tbody></table></div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Ler o registo oficial</div></div>
<p class="sm">O Diário da República renderiza por script: obtido por HTTP,
devolve poucos bytes e quase nenhum texto. Mas publica o diploma integral em PDF, e esse PDF chega
cifrado com o manipulador de segurança padrão e com tipos subconjuntados — o que faz uma
biblioteca genérica devolver zero caracteres, e devolvê-los em silêncio. Um zero devolvido por uma
limitação do leitor é indistinguível, no ficheiro de resultados, de um zero devolvido por uma
página vazia, e essa confusão faria esta redação publicar «não se consegue ler o registo nacional»
quando a verdade seria «não implementámos o decifrador». <code>build/pdf.py</code> implementa-o, e
lê o mapa <code>/ToUnicode</code> de cada tipo em vez de adivinhar o deslocamento dos glifos.
Quando mesmo assim um PDF não abre, a razão fica registada ao lado da afirmação, e a afirmação é
marcada «sem fonte legível» e nunca «excerto não encontrado».</p>
"""
    return pagina("metodo/index.html", "Método",
                  "Obter, congelar, hashear, extrair, comparar — e as recusas, com o sítio exato "
                  "onde cada uma corre.", corpo, aqui=None, fontes_n=reg["contagem"])


def equipa(d):
    eq = d["equipa"]
    deps = "".join(
        f'<div class="col sp8" style="padding:18px 0" >'
        f'<div class="hair" style="padding-top:14px"></div>'
        f'<h3 class="h-3">{e(x["nome"])}</h3>'
        f'<p class="sm it">{e(x["gravidade"])}</p>'
        f'<p class="sm"><b>Faz:</b> {e(x["faz"])}</p>'
        f'<p class="sm"><b>Recusa:</b> {e(x["recusa"])}</p>'
        f'<p class="sm"><b>Está errado quando:</b> {e(x["errado_quando"])}</p>'
        f'<div class="chips" style="padding-top:6px">'
        + "".join(f'<span class="chip">{e(p)}</span>' for p in x["escreve_em"]) + '</div></div>'
        for x in eq["departamentos"])
    nao = "".join(f'<tr><td>{e(x["papel"])}</td><td class="sm">{e(x["porque"])}</td></tr>'
                  for x in eq["nao_construido"])
    niveis = "".join(
        f'<tr><td class="mono">{e(x["nivel"])}</td><td class="sm">{e(x["pode"])}</td>'
        f'<td class="sm">{e(x["participa"])}</td><td class="sm">{e(x["estado"])}</td></tr>'
        for x in eq["camadas_de_agente"]["niveis"])
    ed = eq["editor_de_registo"]
    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">A redação</div></div>
<h1 class="h-2" style="max-width:24em">Três departamentos, um humano nomeado, e a publicação é um
passo de construção.</h1>
<p class="std" style="padding:14px 0 18px">{e(eq["nota"])}</p>

<div class="painel" style="margin-bottom:26px">
  <div class="sect">Editor de registo</div>
  <h2 class="h-2" style="padding:6px 0">{e(ed["nome"])}</h2>
  <p class="sm">{e(ed["o_que_faz"])}</p>
  <p class="sm" style="padding-top:8px">{e(ed["e_tambem"])}</p>
  <p class="sm" style="padding-top:8px"><b>{e(ed["limite"])}</b></p>
  <div class="sect" style="padding-top:14px">Só ele pode</div>
  <ul>{"".join(f'<li class="sm">{e(x)}</li>' for x in ed["so_ele_pode"])}</ul>
</div>

{"".join(deps)}

<div class="rule" style="padding:22px 0 8px"><div class="sect">Quem escreve onde</div></div>
<p class="sm">{e(eq["quem_escreve_onde"])}</p>

<div class="rule" style="padding:22px 0 8px"><div class="sect">As camadas de agente</div></div>
<p class="sm" style="padding-bottom:12px">{e(eq["camadas_de_agente"]["nota"])}</p>
<div class="rolar"><table><thead><tr><th style="width:60px">Nível</th><th>Pode</th>
  <th>Participa</th><th>Estado</th></tr></thead><tbody>{niveis}</tbody></table></div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">O que não está construído, e porquê</div></div>
<p class="sm" style="padding-bottom:12px">Listado em vez de discretamente omitido: reclamar uma
capacidade que não existe é a forma mais fácil de uma publicação mentir sem dizer nada falso.</p>
<div class="rolar"><table><thead><tr><th style="width:280px">Papel</th><th>Porque não</th></tr>
  </thead><tbody>{nao}</tbody></table></div>
"""
    return pagina("equipa/index.html", "A redação",
                  "Três departamentos, um editor de registo nomeado, e o que cada um pode e não "
                  "pode escrever.", corpo, aqui=None)


def aviso(d):
    a = d["aviso"]
    teste = "".join(
        f'<div class="col sp6" style="padding:14px 0"><div class="hair" style="padding-top:12px"></div>'
        f'<h3 class="h-3">{e(x["membro"])}</h3><p class="sm">{e(x["dizemos"])}</p></div>'
        for x in a["fundamento"]["teste"])
    detidas = "".join(f'<li class="sm">{e(x)}</li>' for x in a["categorias_detidas"])
    recusadas = "".join(f'<li class="sm">{e(x)}</li>' for x in a["categorias_recusadas"])
    direitos = "".join(f'<li class="sm">{e(x)}</li>' for x in a["direitos"])
    nunca = "".join(f'<li class="sm">{e(x)}</li>' for x in a["o_que_este_site_nao_faz"])
    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">Aviso de proteção de dados</div></div>
<h1 class="h-2" style="max-width:26em">O que esta publicação detém sobre pessoas nomeadas, porquê,
e como pedir para sair — sem dar razão nenhuma.</h1>

<div class="painel" style="margin:18px 0;border-left:3px solid var(--aviso)">
  <p class="sm"><b>{e(a["nao_e_aconselhamento_juridico"])}</b></p></div>

<div class="painel" style="margin-bottom:22px">
  <div class="sect">A ordem em que isto foi publicado</div>
  <p class="sm" style="padding-top:8px">{e(a["nota_de_ordem"])}</p></div>

<div class="rule g2" style="padding:22px 0">
  <div class="col sp10"><div class="sect">Responsável pelo tratamento</div>
    <h3 class="h-3">{e(a["responsavel"]["quem"])}</h3>
    <p class="sm">{e(a["responsavel"]["porque_pessoal"])}</p>
    <p class="sm"><b>Contacto:</b> <a href="mailto:{e(a["responsavel"]["contacto"])}">{e(a["responsavel"]["contacto"])}</a></p></div>
  <div class="col sp10"><div class="sect">Quem é abrangido</div>
    <p class="sm">{e(a["titulares"])}</p>
    <div class="sect" style="padding-top:10px">Finalidade</div>
    <p class="sm">{e(a["finalidade"])}</p></div>
</div>

<div class="rule g2" style="padding:22px 0">
  <div class="col sp10"><div class="sect">O que é detido</div><ul>{detidas}</ul></div>
  <div class="col sp10"><div class="sect">O que é recusado</div><ul>{recusadas}</ul>
    <p class="xs" style="padding-top:8px">{e(a["recusa_imposta_por"])}</p></div>
</div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Fundamento de licitude ·
{e(a["fundamento"]["base"])}</div></div>
<p class="sm"><b>{e(a["fundamento"]["nao_e_jornalismo"])}</b></p>
<div class="g3">{teste}</div>
<p class="xs">{e(a["fundamento"]["orientacao"])}</p>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Porquê um aviso público</div></div>
<p class="sm">{e(a["porque_um_aviso_publico"]["regra"])}</p>
<p class="sm" style="padding-top:8px">{e(a["porque_um_aviso_publico"]["portanto"])}
{e(a["porque_um_aviso_publico"]["e_a_ordem_certa"])}</p>

<div class="rule g2" style="padding:22px 0">
  <div class="col sp10"><div class="sect">Os seus direitos</div><ul>{direitos}</ul></div>
  <div class="col sp10 painel"><div class="sect">Oposição e remoção</div>
    <p class="sm"><b>Como:</b> {e(a["oposicao"]["como"])}</p>
    <p class="sm" style="padding-top:8px"><b>{e(a["oposicao"]["promessa"])}</b></p>
    <p class="sm" style="padding-top:8px">{e(a["oposicao"]["e_depois"])}</p></div>
</div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Quando um nome sai de uma lista</div></div>
<p class="sm">{e(a["regra_sem_razao"])}</p>

<div class="rule" style="padding:22px 0 8px"><div class="sect">O que este site não faz</div></div>
<ul style="max-width:48em">{nunca}</ul>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Conservação</div></div>
<p class="sm">{e(a["conservacao"])}</p>
"""
    return pagina("aviso/index.html", "Aviso de proteção de dados",
                  "O que esta publicação detém sobre pessoas nomeadas, com que fundamento, e como "
                  "pedir a remoção — incondicional, sem razão exigida.",
                  corpo, aqui=None, com_declaracao=False)


def sobre(d):
    reg, graf = d["registo"], d["grafo"]
    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">Sobre · o que é real e o que não é</div></div>
<h1 class="h-2" style="max-width:26em">Um mapa de um ecossistema, construído ao contrário: primeiro
a prova, depois a afirmação.</h1>

<div class="rule g2" style="padding:22px 0">
<div class="col sp10"><div class="sect">O que é real hoje</div>
<ul>
<li class="sm">{reg["contagem"]} ficheiros congelados de {len(reg["capturas"])} captura(s), cada um
  com o seu SHA-256, todos reverificados em cada construção.</li>
<li class="sm">Um grafo de {graf["contagens"]["nos"]} nós e {graf["contagens"]["arestas"]} arestas,
  em que cada nó nomeia a fonte congelada de onde veio.</li>
<li class="sm">Uma ontologia de verbos portugueses, cada um com um inverso distinto, em que um
  caminho se lê em voz alta.</li>
<li class="sm">Um aviso de proteção de dados publicado antes da primeira página que nomeia alguém.</li>
<li class="sm">Um fluxo de entregas de investigação em que cada excerto é procurado nos bytes antes
  de contar como afirmação.</li>
</ul></div>
<div class="col sp10"><div class="sect">O que ainda não é</div>
<ul>
<li class="sm"><b>Nenhuma história publicada.</b> As três primeiras estão como issues em
  <a href="../redacao/">a mesa</a>, no estado «procurado». Publicar é a linha do editor de registo,
  e nenhuma execução automática a pode escrever.</li>
<li class="sm"><b>A camada das empresas não pode ser completa.</b> Não há registo comercial aberto
  em Portugal: o registo é por empresa, pago e com código de acesso, e o registo de beneficiários
  efetivos deixou de ser de acesso público em 2022. A afirmação honesta é outra e é melhor — estas
  são as organizações que aparecem em financiamento público europeu e nacional, com montantes e
  datas.</li>
<li class="sm"><b>Três das oito secções estão vazias</b> e dizem-no na própria página, em vez de
  serem escondidas da navegação.</li>
<li class="sm"><b>Nenhum nível de agente além do A foi testado.</b> O resumo manda testar o nível B
  primeiro e tratar o resultado como um achado em qualquer dos sentidos.</li>
</ul></div>
</div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">A língua</div></div>
<p class="sm">Este site é nativamente português e não é uma tradução de
nada. Os verbos do grafo são portugueses e o inglês é uma anotação — não o contrário, que é a
forma mais provável de um site assim estar discretamente errado, porque nada nele parece avariado.
Os títulos de sessões e os nomes de organizações e de pessoas ficam <b>verbatim</b>, na língua em
que a fonte os escreveu: uma transcrição é uma afirmação. E os acentos são dados. O conjunto de
onde este método vem impõe ASCII puro; aqui o portão corre ao contrário e assere que os acentos
estão presentes e vieram da fonte, e não de uma lista que alguém escreveu.</p>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Parte de</div></div>
<p class="sm">Uma instância do argumento publicado em
<a href="https://newsroom.sgit.ai">newsroom.sgit.ai</a>. O resumo de comissionamento deste site
vive lá e não aqui, porque conteúdo existe uma vez: se o mesmo parágrafo estivesse nos dois
sítios, os dois acabariam por discordar. O método vem de
<a href="https://newsroom.sgit.ai/portugal/index.html">/portugal/</a>, que o corre desde setembro
de 2026; o que este site acrescenta é a língua, o país como matéria em vez de um evento, e o fluxo
de revisão das entregas.</p>
"""
    return pagina("sobre/index.html", "Sobre e limites",
                  "O que é real neste site hoje, o que ainda não é, e porque a camada das empresas "
                  "não pode ser completa.", corpo, aqui=None)


def ficheiros(d):
    man = carregar("manifesto.json")
    linhas = "".join(
        f'<tr><td class="mono xs"><a href="../{e(x["ficheiro"])}">{e(x["ficheiro"])}</a></td>'
        f'<td class="mono xs">{x["bytes"]}</td><td class="mono xs">{e(x["sha256"])}</td></tr>'
        for x in man["ficheiros"])
    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">Os ficheiros</div></div>
<p class="std" style="padding-bottom:18px">{e(man["nota"])} Cada página deste site
diz de que ficheiro foi construída; esta diz o hash de cada um deles. É o que torna «a um clique
dos bytes» verificável em vez de uma promessa.</p>
<div class="chips" style="padding-bottom:18px"><span class="chip ok">{man["contagem"]} ficheiros de dados</span></div>
<div class="rolar"><table><thead><tr><th>Ficheiro</th><th style="width:90px">Bytes</th>
  <th style="width:480px">SHA-256</th></tr></thead><tbody>{linhas}</tbody></table></div>
"""
    return pagina("ficheiros/index.html", "Os ficheiros",
                  "Cada ficheiro de dados deste site com o seu SHA-256.", corpo, aqui=None,
                  fontes_n=man["contagem"])


# ================================================================== o carregar ===
def ler_issues():
    p = ROOT / "redacao" / "issues"
    return sorted((json.loads(f.read_text(encoding="utf-8")) for f in p.glob("*.json")),
                  key=lambda i: i["id"]) if p.exists() else []


def ler_correio():
    """O correio entre os agentes, de `dados/correio.json`, e nunca da pasta.

    `redacao/correio/` has ONE reader, and it is `build/backoffice_team.py`: it reads the `.eml` files,
    derives each message's state from the folder it sits in, and writes `dados/correio.json`. This
    function reads the derived file. Parsing the folder again here would be a second reader of the
    same thing, and v0.3.1 of this site was precisely the deletion of a second document reader.

    Only what is delivered (`entrada`) or handled (`tratado`) reaches the desk. A message in
    transit has not arrived, and the copy in `saida/` is the same message in the sender's
    de quem a enviou — mostrá-la seria contar duas vezes.
    """
    d = carregar("correio.json")
    msgs = [{"de": m["de"], "para": m["para"], "assunto": m["assunto"], "issue": m.get("issue"),
             "quando": m["quando"], "corpo": m["resumo"], "caixa": m["caixa"],
             "lugar": m["lugar"], "historica": m.get("historica", False)}
            for m in d.get("mensagens", []) if m["lugar"] in ("entrada", "tratado")]
    return sorted(msgs, key=lambda m: m.get("quando") or "")


def ler_seccoes():
    """O registo editorial de cada secção, de seccoes/<id>/seccao.json."""
    base = ROOT / "seccoes"
    out = {}
    for f in sorted(base.glob("*/seccao.json")) if base.exists() else []:
        s = json.loads(f.read_text(encoding="utf-8"))
        out[s["id"]] = s
    return out


def ler_runs():
    p = ROOT / "redacao" / "runs"
    return sorted((json.loads(f.read_text(encoding="utf-8")) for f in p.glob("*.json")),
                  key=lambda r: r["quando"]) if p.exists() else []


def carregar_tudo():
    d = {
        "registo": carregar("registo.json"), "pessoas": carregar("pessoas.json"),
        "orgs": carregar("organizacoes.json"), "sessoes": carregar("sessoes.json"),
        "temas": carregar("temas.json"), "mudancas": carregar("mudancas.json"),
        "grafo": carregar("grafo.json"), "ontologia": carregar("ontologia.json"),
        "aviso": carregar("aviso.json"), "equipa": carregar("equipa.json"),
        "evento": carregar("evento.json"), "lexico": carregar("lexico.json"),
        "entregas": carregar("entregas.json"),
        "review": carregar("review.json"),
        "interviews": carregar("interviews.json"),
        "verif": carregar("verificacoes-fonte.json"),
        "historias": carregar("historias.json") or {"historias": []},
        "issues": ler_issues(), "correio": ler_correio(), "runs": ler_runs(),
        "seccoes": ler_seccoes(),
    }
    vd = ROOT / "dados" / "verificacoes"
    n = 0
    for f in vd.glob("*.json") if vd.exists() else []:
        n += len(json.loads(f.read_text(encoding="utf-8")).get("afirmacoes", []))
    if d["entregas"]:
        n += sum(x["contagens"]["afirmacoes"] - x["contagens"]["fonte_inacessivel"]
                 for x in d["entregas"]["entregas"])
    d["n_verificadas"] = n
    return d


def main():
    d = carregar_tudo()
    feitas = []
    feitas.append(escrever("index.html", primeira(d)))
    for sid, _ in P.SECCOES:
        feitas.append(escrever(f"{sid}/index.html", seccao(sid, d)))
    feitas.append(escrever("registo/index.html", registo(d)))
    feitas.append(escrever("grafo/index.html", grafo(d)))
    feitas.append(escrever("ficheiros/index.html", ficheiros(d)))
    feitas.append(escrever("metodo/index.html", metodo(d)))
    feitas.append(escrever("equipa/index.html", equipa(d)))
    feitas.append(escrever("aviso/index.html", aviso(d)))
    feitas.append(escrever("sobre/index.html", sobre(d)))
    feitas.append(escrever("redacao/index.html", mesa(d)))
    feitas.append(escrever("admin/review/index.html", review(d)))
    if d.get("interviews"):
        feitas.append(escrever("newsroom/interviews/index.html", interviews(d)))
    feitas.append(escrever("entregas/index.html", entregas_indice(d)))
    for x in (d["entregas"] or {}).get("entregas", []):
        feitas.append(escrever(f"entregas/{x['id']}.html", entrega_pagina(x, d)))
    # An article is its dated folder, and build/artigos.py renders it there from artigo.md. This
    # used to render a SECOND copy of every published article at artigos/<slug>.html out of
    # conteudo/<slug>.md — a path that predates the dated folders and that nothing ever exercised,
    # because nothing had ever been published. The first publication found it. Content exists once.
    # (Deleted once in this work, restored by a clean merge from another session, deleted again:
    # a clean merge is not evidence that your work survived.)
    print(f"build: {len(feitas)} páginas")
    return feitas


if __name__ == "__main__":
    main()

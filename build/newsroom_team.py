#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the agent team, the board and the mail. One reader, three pages.

    python3 build/newsroom_team.py

WHAT THIS IS

The newsroom's agents coordinate by files, under the Email-FS-lite protocol that the sgraph.ai
team publishes and runs (https://sgraph.ai/en-gb/library/how-it-works/email-fs-lite.md). This
script is the ONE reader of that folder. It walks `redacao/correio/`, derives two data files, and
renders three back-office pages from the derived data:

    dados/correio.json    every message, with the state its location implies
    dados/quadro.json     every board card: the agent's own, and the paper's issues by formula

    newsroom/team.html    who the agents are — the roster, in the ROLE.md shape
    newsroom/board.html    what each one has in front of it — the board
    newsroom/mail.html   what passed between them — the mail, threaded

WHY ONE READER, SAID OUT LOUD

Release v0.3.1 of this site was the removal of a second document reader ("havia dois leitores de
documentos, e passa a haver um"). Adding a second reader of the mail folder — one for the pages
and one for the data — would have been the same mistake in a new place. So: this script reads the
folder, and everything else reads the JSON. `build/build.py` reads `dados/correio.json` for the
reader-facing board at `/redacao/`, and no longer parses the folder itself.

WHY THE OWNER OF A PAPER ISSUE IS A FORMULA

Rule 6 of CLAUDE.md: classification is a published formula or it does not happen. A hand-written
`departamento:` field on an issue disagrees with the issue's own state the first day somebody
forgets to change both. So the owner is derived from the state, by the table in
`dados/agentes.json` under `formula_do_quadro`, and the page prints the table it used.

WHAT THIS SCRIPT MAY NOT DO

It is @Bastidores' script, and @Bastidores publishes no claim about the world. Every number these
pages carry is a count of files in this repository. `build/gates_artigos.py` fails the build if a
back-office page ever cites a frozen source as evidence.
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from newsroom import GH, VERSAO, e, escrever, pagina  # noqa: E402  the one page chrome

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
CORREIO = ROOT / "redacao" / "correio"

# The three board columns, in the order the protocol names them, with the Portuguese folder each
# one is. `abertos` is what the agent has in front of it; `bloqueados` is waiting on somebody
# else and says who; `fechados` is done.
COLUNAS = [
    ("abertos", "Open", "ok"),
    ("bloqueados", "Blocked", "miss"),
    ("fechados", "Closed", ""),
]

# Where a message sits is what state it is in. This is the whole of the protocol's state model:
# there is no status field anywhere, because a field can disagree with the folder and a folder
# cannot disagree with itself.
LUGARES = [
    ("expedicao", "em trânsito", "Sent, not yet delivered — the recipient has not collected it"),
    ("entrada", "entregue", "Delivered and open — work in progress while it sits here"),
    ("tratado", "tratado", "Handled — the work it asked for is complete"),
    ("saida", "cópia de quem enviou", "The sender's own record of what it sent"),
]


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


# ------------------------------------------------------------------ the mail ---
def ler_eml(f):
    """One RFC 2822 message. Headers to a dict, body kept whole.

    Header folding (a continuation line starting with whitespace) is unfolded, because a long
    Subject: written by a human wraps and a reader that did not unfold it would show half of it.
    """
    texto = f.read_text(encoding="utf-8")
    cru, _, corpo = texto.partition("\n\n")
    cab, ultimo = {}, None
    for linha in cru.splitlines():
        if linha[:1] in (" ", "\t") and ultimo:
            cab[ultimo] += " " + linha.strip()
            continue
        k, _, v = linha.partition(":")
        if _:
            ultimo = k.strip().lower()
            cab[ultimo] = v.strip()
    return cab, corpo.strip()


def endereco(valor):
    """`pesquisa.pt <pesquisa.pt@redacao.local>` -> `pesquisa.pt`. The identity is the address."""
    m = re.match(r"^\s*([^<]+?)\s*<", valor or "")
    return (m.group(1) if m else (valor or "")).strip()


def ler_correio(ids):
    """Every `.eml` under redacao/correio/, with the state its location implies."""
    msgs = []
    for f in sorted(CORREIO.rglob("*.eml")) if CORREIO.exists() else []:
        rel = f.relative_to(ROOT).as_posix()
        partes = f.relative_to(CORREIO).parts
        if partes[0] == "expedicao":
            lugar, caixa = "expedicao", partes[1]
        elif len(partes) >= 2 and partes[1] in ("entrada", "tratado", "saida"):
            lugar, caixa = partes[1], partes[0]
        else:
            continue
        cab, corpo = ler_eml(f)
        de, para = endereco(cab.get("from")), endereco(cab.get("to"))
        msgs.append({
            "ficheiro": rel,
            "lugar": lugar,
            "caixa": caixa,
            "de": de,
            "para": para,
            "de_alias": cab.get("x-emailfs-from-alias") or f"@{de}",
            "para_alias": cab.get("x-emailfs-to-alias") or f"@{para}",
            "assunto": cab.get("subject", ""),
            "quando": cab.get("date", ""),
            "id": cab.get("message-id", "").strip("<>"),
            "responde_a": cab.get("in-reply-to", "").strip("<>") or None,
            "issue": cab.get("x-redacao-issue") or None,
            "run": cab.get("x-redacao-run") or None,
            # A sender that is no longer in the roster. Declared in the header, published in
            # dados/agentes.json, and shown as historical rather than failing the reader.
            "historica": "from" in (cab.get("x-redacao-identidade-historica", "").lower()),
            "migrado_de": cab.get("x-redacao-migrado-de") or None,
            "corpo": corpo,
            "resumo": " ".join(corpo.split())[:420],
            "bytes": f.stat().st_size,
            "desconhecido": [x for x in (de, para) if x and x not in ids],
        })
    return sorted(msgs, key=lambda m: (m.get("quando") or "", m["ficheiro"]))


# ----------------------------------------------------------------- the board ---
def ler_cartoes():
    """Every card an agent opened for itself, from `<agente>/assuntos/<coluna>/*.md`."""
    cartoes = []
    for agente in sorted(p.name for p in CORREIO.iterdir()
                         if p.is_dir() and (p / "assuntos").is_dir()) if CORREIO.exists() else []:
        for coluna, _, _ in COLUNAS:
            for f in sorted((CORREIO / agente / "assuntos" / coluna).glob("*.md")):
                t = f.read_text(encoding="utf-8")
                m = re.match(r"^---\n(.*?)\n---\n(.*)$", t, re.S)
                fm = dict(re.findall(r"^([\w_]+):\s*(.*)$", m.group(1), re.M)) if m else {}
                corpo = (m.group(2) if m else t).strip()
                # THE TITLE COMES FROM THE CARD, NOT FROM ITS FILENAME.
                #
                # This used to de-slug the filename — `001__a-fila-nao-tem-credenciais.md` became
                # "A fila nao tem credenciais" — and a filename is ASCII, so every accent was
                # lost on the way to the page. The design review found the same fault in the
                # section pages (`nao resolve`) and said the right thing about it: a missing
                # accent in a vocabulary suggests the strings are being written somewhere
                # ASCII-only, and that is worth auditing rather than fixing in one place. The
                # audit of `dados/` found this, in the board this very session had just built.
                #
                # So the card names itself: a `titulo:` in the front matter, else its first `# `
                # heading, and only then the de-slugged filename — which is now a last resort
                # that the accent gate in `build/gates.py` would notice.
                titulo = (fm.get("titulo") or "").strip()
                if not titulo:
                    h = re.search(r"^#\s+(.+)$", corpo, re.M)
                    titulo = h.group(1).strip() if h else ""
                if not titulo:
                    titulo = re.sub(r"^\d+__", "", f.stem).replace("-", " ")
                    titulo = titulo[:1].upper() + titulo[1:]
                cartoes.append({
                    "ficheiro": f.relative_to(ROOT).as_posix(),
                    "agente": agente, "coluna": coluna, "origem_tipo": "assunto",
                    "titulo": titulo[:1].upper() + titulo[1:],
                    "aberto": fm.get("aberto"), "prioridade": fm.get("prioridade"),
                    "esforco": fm.get("esforco"),
                    "bloqueado_por": (fm.get("bloqueado_por") or "").strip() or None,
                    "issue": (fm.get("issue") or "").strip() or None,
                    "origem": fm.get("origem"),
                    "corpo": corpo,
                    "resumo": " ".join(re.sub(r"^#+ .*$", "", corpo, flags=re.M).split())[:300],
                })
    return cartoes


def ler_issues_do_jornal(formula):
    """The paper's own issues, placed on an agent's board BY FORMULA and never by hand."""
    de_estado = formula.get("de_estado_para_agente", {})
    porque = formula.get("porque", {})
    out = []
    for f in sorted((ROOT / "redacao" / "issues").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        estado = d.get("estado", "")
        agente = de_estado.get(estado, "—")
        if agente == "—":
            continue
        # An issue whose own file says what it is waiting for is blocked; otherwise it is open.
        # The signal is a card in that agent's `bloqueados` naming the same issue, which is the
        # agent's own statement about its own work — the only place that judgement belongs.
        out.append({
            "ficheiro": f.relative_to(ROOT).as_posix(),
            "agente": agente, "coluna": "abertos", "origem_tipo": "issue",
            "id": d["id"], "titulo": d.get("titulo", ""), "estado": estado,
            "seccao": d.get("seccao"), "aberto": d.get("aberto_em"),
            "porque_aqui": porque.get(estado, ""),
            "o_que_falta": d.get("o_que_falta", []),
        })
    return out


def quadro(agentes, cartoes, issues, msgs):
    """The board, one bucket per agent. Cards, paper issues, and open mail sitting in the inbox."""
    por_agente = {}
    for a in agentes:
        aid = a["id"]
        entrada = [m for m in msgs if m["lugar"] == "entrada" and m["caixa"] == aid]
        transito = [m for m in msgs if m["lugar"] == "expedicao" and m["caixa"] == aid]
        por_agente[aid] = {
            "agente": aid, "alias": a["alias"], "nome": a["nome"],
            "colunas": {c: [x for x in cartoes if x["agente"] == aid and x["coluna"] == c]
                        for c, _, _ in COLUNAS},
            "issues_do_jornal": [x for x in issues if x["agente"] == aid],
            "entrada": entrada, "em_transito": transito,
            "contagens": {
                "abertos": len([x for x in cartoes if x["agente"] == aid and x["coluna"] == "abertos"]),
                "bloqueados": len([x for x in cartoes if x["agente"] == aid and x["coluna"] == "bloqueados"]),
                "fechados": len([x for x in cartoes if x["agente"] == aid and x["coluna"] == "fechados"]),
                "issues_do_jornal": len([x for x in issues if x["agente"] == aid]),
                "por_tratar": len(entrada), "em_transito": len(transito),
            },
        }
    return por_agente


# ------------------------------------------------------------------ the pages ---
TRACO = "\u2014"


def ficha(chip, texto):
    return f'<span class="chip {chip}">{e(texto)}</span>'


def rank(n, texto):
    """A state, on the console's four-rank scale. 1 = a human must act, 2 = an agent is blocked,
    3 = running, 4 = done. Only rank 1 is filled, and it is the only rank that is."""
    return f'<span class="st st--{n}">{e(texto)}</span>'


def lista(xs, vazio="—"):
    if not xs:
        return f'<p class="sm">{vazio}</p>'
    return '<ul class="sm" style="padding-left:18px;margin:0">' + "".join(
        f"<li>{e(x)}</li>" for x in xs) + "</ul>"


def pagina_equipa(ag, q):
    agentes = ag.get("agentes", [])
    cartoes_totais = sum(v["contagens"]["abertos"] + v["contagens"]["bloqueados"]
                         + v["contagens"]["fechados"] for v in q.values())
    blocos = []
    for a in agentes:
        c = q.get(a["id"], {}).get("contagens", {})
        humano = a.get("papel") == "humano"
        nao = "".join(
            f'<tr><td class="sm">{e(x["o_que"])}</td><td class="sm">{e(x.get("quem", ""))}</td></tr>'
            for x in a.get("nao_responsavel_por", []))
        so_ele = ""
        if a.get("so_ele_pode"):
            so_ele = (f'<div class="sect" style="padding-top:12px">Only this role may</div>'
                      f'{lista(a["so_ele_pode"])}')
        en = a.get("en", {})
        estado = a.get("estado", TRACO)
        estado_rank = rank(3, estado) if estado == "a-correr" else rank(2, estado)
        blocos.append(f"""
<div class="cartao" style="padding:16px;margin-top:18px" id="{e(a["id"])}">
  <div class="queue__meta" style="margin:0 0 10px">
    <b style="font-size:15px">{e(a["alias"])}</b>
    {estado_rank}
    {rank(1, "a human in the loop") if humano else ""}
    <span class="path">{e(a["id"])} \u00b7 {e(a.get("modelo", ""))} \u00b7
      tier {e(str(a.get("nivel", TRACO)))}</span>
  </div>
  <p class="std" style="max-width:52em"><b>{e(a["nome"])}</b> — {e(a["dominio"])}</p>
  <p class="std" style="max-width:52em">{e(a["missao"])}</p>
  <p class="sm" style="max-width:52em"><i>{e(en.get("missao", ""))}</i></p>

  <div class="g2 sp12" style="padding-top:12px">
    <div class="col sp6">
      <div class="sect">The central claim — written so it can be disproved</div>
      <p class="sm">{e(a["afirmacao_central"])}</p>
      <div class="sect" style="padding-top:8px">Gravity</div>
      <p class="sm">{e(a.get("gravidade", ""))}</p>
      <div class="sect" style="padding-top:8px">Writes in</div>
      {lista(a.get("escreve_em", []))}
      {so_ele}
    </div>
    <div class="col sp6">
      <div class="sect">Not responsible for — the field that makes this a team</div>
      <div class="rolar"><table><thead><tr><th>Not this</th><th style="width:44%">Whose</th>
        </tr></thead><tbody>{nao or '<tr><td class="sm">—</td><td class="sm">—</td></tr>'}</tbody>
        </table></div>
      <div class="sect" style="padding-top:8px">Refuses</div>
      {lista(a.get("recusa", []), "Nothing recorded.")}
      <div class="sect" style="padding-top:8px">Wrong when</div>
      <p class="sm">{e(a.get("errado_quando", ""))}</p>
    </div>
  </div>

  <div class="g3 sp12" style="padding-top:12px">
    <div class="col sp6"><div class="sect">Works with</div>
      <p class="sm">{e(a.get("trabalha_com", ""))}</p></div>
    <div class="col sp6"><div class="sect">Tools and access</div>
      {lista(a.get("ferramentas", []))}</div>
    <div class="col sp6"><div class="sect">Runs</div>
      <p class="sm">{e(a.get("corre", ""))}</p>
      <div class="sect" style="padding-top:8px">On its plate now</div>
      <div class="chips">
        {ficha("ok", f'{c.get("abertos", 0)} open')}
        {ficha("miss", f'{c.get("bloqueados", 0)} blocked')}
        {ficha("", f'{c.get("issues_do_jornal", 0)} paper issues')}
        {ficha("falta", f'{c.get("por_tratar", 0)} unread') if c.get("por_tratar") else ""}
      </div>
      <p class="sm" style="padding-top:6px"><a href="board.html#{e(a["id"])}">its board →</a> ·
         <a href="mail.html#{e(a["id"])}">its mail →</a></p>
    </div>
  </div>
</div>""")

    nao_construido = "".join(
        f'<tr><td class="sm"><b>{e(x["papel"])}</b></td><td class="sm">{e(x["porque"])}</td></tr>'
        for x in ag.get("nao_construido", []))
    historicas = "".join(
        f'<tr><td class="sm mono xs">{e(x["id"])}</td><td class="sm">{e(x["o_que_era"])} '
        f'{e(x["porque_fica"])}</td></tr>' for x in ag.get("identidades_historicas", []))

    corpo = f"""
<h2>The team · {len(agentes)} roles,
one of them human</h2>
<p class="std" style="max-width:52em;padding-bottom:6px">{e(ag["nota"])}</p>
<div class="stats" style="margin-bottom:18px">
  <span class="path">{len(agentes)} roles \u00b7 {cartoes_totais} board cards \u00b7
  protocol email-fs-lite {e(str(ag.get("protocolo_versao", "")))} \u00b7
  <a href="#nao-construido">{len(ag.get("nao_construido", []))} roles deliberately not
  built</a></span>
</div>
<p class="sm" style="max-width:52em">The shape of each definition below is the one
<a href="{ag["formato_do_papel"]}">teams.sgit.ai publishes for a <code>ROLE.md</code></a> — name,
mission, a central claim written as a failure condition, and <b>not responsible for</b>, which is
the field that stops every role quietly becoming the same role — merged with the shape
<a href="https://sgraph.ai/en-gb/library/agentic-teams/sgraph-ai-team.md">sgraph.ai publishes for
each of its own agents</a>: model, domain, what it owns, what it does not own and whose that is,
how it works with the others, and its cadence. Nothing here is hand-written on a page: it is
<code>dados/agentes.json</code>, rendered.</p>

{"".join(blocos)}

<h2>The write rule</h2>
<p class="std" style="max-width:52em">{e(ag["regra_de_escrita"])}</p>

<h2>Publishing is not an agent</h2>
<p class="std" style="max-width:52em"><b>{e(ag["publicacao"]["o_que_e"])}</b>
{e(ag["publicacao"]["porque"])}</p>

<h2 id="nao-construido">Roles deliberately not built</h2>
<p class="sm" style="max-width:52em;padding-bottom:8px">A roster that claimed roles nobody runs
would be claiming a capability. These are named with the reason they are absent, which is the same
discipline <code>dados/equipa.json</code> already applies to departments.</p>
<div class="rolar"><table><thead><tr><th style="width:20%">Role</th><th>Why not</th></tr></thead>
<tbody>{nao_construido}</tbody></table></div>

<h2>Retired identities</h2>
<p class="sm" style="max-width:52em;padding-bottom:8px">Mail is never deleted, so a sender that no
longer exists still has to resolve to something. These are declared in the message header and
shown as historical, rather than failing the reader on a name it does not know.</p>
<div class="rolar"><table><thead><tr><th style="width:20%">Identity</th><th>What it was</th></tr>
</thead><tbody>{historicas}</tbody></table></div>
"""
    return pagina("newsroom/team.html", "The team",
                  "The newsroom's agents: mission, central claim, what each is not responsible "
                  "for, and what each has on its plate.", corpo)


def pagina_quadro(ag, q):
    """The board — the nearest thing this back office has to a working surface.

    THE 158 CHIPS. The design review counted 158 chips on this one page, and the point it makes is
    that a chip is a strong signal with a fixed budget per page: at 158 the budget is spent many
    times over and the eye has nothing to land on. Most of them were not statuses at all — a
    section name, a priority, an effort estimate, an issue number, an agent id. Those are metadata,
    and metadata is mono text beside the thing it describes.

    What is left in a box is a STATE, and there are four of them: waiting on a human (rank 1,
    filled, and the only filled rank), an agent blocked (rank 2, outlined amber), running (rank 3,
    outlined neutral) and done (rank 4, a tick and no box at all). Rank 4 losing its box is most of
    how a page stops having 158 chips on it.
    """
    editor = "dinis.humano"
    blocos = []
    for a in ag.get("agentes", []):
        v = q.get(a["id"], {})
        c = v.get("contagens", {})
        cols = []
        for coluna, rotulo, _chip in COLUNAS:
            cartoes = v.get("colunas", {}).get(coluna, [])
            itens = []
            if coluna == "abertos":
                for i in v.get("issues_do_jornal", []):
                    # A paper issue the formula put on the editor is the one thing on this board
                    # nobody else can move, so it is the one thing that gets the filled rank.
                    meu = a["id"] == editor
                    itens.append(f"""
<div class="board__card{' board__card--needs-you' if meu else ''}">
  <div class="queue__meta" style="margin:0 0 6px">
    {'<span class="st st--1">needs you</span>' if meu else '<span class="st st--3">on the board</span>'}
    <span class="path">paper issue {e(i["id"])} · {e(i["estado"])}{
        " · " + e(i["seccao"]) if i.get("seccao") else ""}</span>
  </div>
  <p class="quote quote--sm" style="margin:0 0 6px"><a href="../desk/">{e(i["titulo"])}</a>
    <span class="lang">PT</span></p>
  <p class="note" style="margin:0">By formula: {e(i["porque_aqui"])}</p>
</div>""")
            for x in cartoes:
                bloqueado = x.get("bloqueado_por") and x["bloqueado_por"] != "\u2014"
                no_editor = bloqueado and x["bloqueado_por"] == editor
                # `bloqueado_por` CARRIES TWO DIFFERENT THINGS and only one of them fits in a
                # badge. Usually it is an agent id, `dinis.humano`. But a card may instead put the
                # whole reason there — one on the board today is a 66-character sentence naming a
                # deny-listed file and saying no agent may edit it. A rank badge is two words and
                # refuses to wrap, so a sentence in one pushed this page 193px past a 390px
                # viewport. An id goes in the badge; anything with a space in it makes the badge
                # say only «blocked» and the reason reads beside it, which is where a sentence
                # belongs anyway.
                porque_bloqueado = ""
                if no_editor:
                    estado = ('<span class="st st--1">needs you'
                              f'<span class="who">· {e(a["alias"])} cannot move it</span></span>')
                elif bloqueado and " " not in x["bloqueado_por"]:
                    estado = f'<span class="st st--2">blocked on {e(x["bloqueado_por"])}</span>'
                elif bloqueado:
                    estado = '<span class="st st--2">blocked</span>'
                    porque_bloqueado = (f'<p class="note" style="margin:0 0 8px">'
                                        f'{e(x["bloqueado_por"])}</p>')
                elif coluna == "fechados":
                    estado = '<span class="st st--4">closed</span>'
                else:
                    estado = '<span class="st st--3">open</span>'
                # Priority, effort and issue number are metadata, not state. They were three more
                # boxes of equal weight beside the one box that meant something.
                meta = " · ".join(filter(None, [
                    e(x["prioridade"]) if x.get("prioridade") else "",
                    e(x["esforco"]) if x.get("esforco") and x["esforco"] != "\u2014" else "",
                    f'issue {e(x["issue"])}' if x.get("issue") else "",
                ]))
                itens.append(f"""
<div class="board__card{' board__card--needs-you' if no_editor else ''}">
  <div class="queue__meta" style="margin:0 0 6px">{estado}
    {f'<span class="path">{meta}</span>' if meta else ""}</div>
  <h3 style="font-size:14.5px">{e(x["titulo"])}</h3>
  {porque_bloqueado}
  <p class="note" style="margin:0 0 8px">{e(x["resumo"])}\u2026</p>
  <p class="path" style="margin:0"><a href="docs.html#{e(x["ficheiro"])}">{e(x["ficheiro"])}</a></p>
</div>""")
            n = len(cartoes) + (len(v.get("issues_do_jornal", [])) if coluna == "abertos" else 0)
            cols.append(f"""
<div class="board__col">
  <h3>{rotulo} <span class="count">{n}</span></h3>
  {"".join(itens) or '<p class="note" style="margin:0;padding:8px 4px">Nothing here.</p>'}
</div>""")
        entrada = "".join(
            f'<div class="board__card board__card--needs-you">'
            f'<div class="queue__meta" style="margin:0 0 6px">'
            f'<span class="st st--1">unread</span>'
            f'<span class="path">from {e(m["de_alias"])}</span></div>'
            f'<p class="note" style="margin:0 0 6px;color:var(--bo-ink)">{e(m["assunto"])}</p>'
            f'<p class="path" style="margin:0">'
            f'<a href="mail.html#{e(m["id"])}">{e(m["ficheiro"])}</a></p></div>'
            for m in v.get("entrada", []))
        transito = "".join(
            f'<div class="board__card">'
            f'<div class="queue__meta" style="margin:0 0 6px">'
            f'<span class="st st--2">in transit</span>'
            f'<span class="path">from {e(m["de_alias"])}</span></div>'
            f'<p class="note" style="margin:0 0 6px;color:var(--bo-ink)">{e(m["assunto"])}</p>'
            f'<p class="path" style="margin:0">waiting for {e(a["alias"])} to collect it into its '
            f'inbox</p></div>'
            for m in v.get("em_transito", []))
        # The agent's own counts, as a run of numbers rather than a run of boxes. A count is a
        # number to compare, and the console sets numbers in tabular figures for exactly that.
        contagens = " · ".join(filter(None, [
            f'{c.get("abertos", 0)} open',
            f'{c.get("bloqueados", 0)} blocked',
            f'{c.get("fechados", 0)} closed',
            f'{c.get("issues_do_jornal", 0)} paper issues',
        ]))
        nao_lida = (f'<span class="st st--1">{c.get("por_tratar", 0)} unread mail</span>'
                    if c.get("por_tratar") else "")
        blocos.append(f"""
<h2 id="{e(a["id"])}">{e(a["alias"])} \u00b7 {e(a["nome"])}</h2>
<div class="queue__meta" style="margin:0 0 12px">
  {nao_lida}
  <span class="path">{e(a["id"])} \u00b7 {contagens}</span>
  <a href="team.html#{e(a["id"])}">its definition \u2192</a>
</div>
<div class="board">{"".join(cols)}</div>
{f'<div class="sect">Mail on its plate</div><div class="board">'
 f'<div class="board__col"><h3>Inbox <span class="count">{len(v.get("entrada", []))}</span></h3>'
 f'{entrada}</div>'
 f'<div class="board__col"><h3>In transit <span class="count">'
 f'{len(v.get("em_transito", []))}</span></h3>{transito}</div></div>'
 if (entrada or transito) else ""}
""")

    f = ag.get("formula_do_quadro", {})
    tab = "".join(
        f'<tr><td class="mono xs">{e(k)}</td><td class="mono xs">{e(vv)}</td>'
        f'<td class="sm">{e(f.get("porque", {}).get(k, ""))}</td></tr>'
        for k, vv in f.get("de_estado_para_agente", {}).items())
    corpo = f"""
<h2>The board · what each agent has in
front of it</h2>
<p class="std" style="max-width:52em">Two kinds of card, kept apart on purpose. A <b>board card</b>
is work the agent opened for itself, in
<code>redacao/correio/&lt;agent&gt;/assuntos/&lt;column&gt;/</code>, and it carries the agent's own
reading of the work — intent, approach, acceptance criterion. A <b>paper issue</b> is one of the
publication's own issues in <code>redacao/issues/</code>, placed on an agent's board by the
formula below and by nothing else. A card moves column in the same commit as the mail action that
moved it, which is why the board cannot disagree with the mail.</p>
<p class="sm" style="max-width:52em;padding-bottom:10px">Nothing on this page is a claim about
Portugal. Every count is a count of files in this repository.</p>

<h2>The formula, printed because it is
used</h2>
<p class="sm" style="max-width:52em;padding-bottom:8px">{e(f.get("nota", ""))}</p>
<div class="rolar"><table><thead><tr><th style="width:130px">Issue state</th>
  <th style="width:140px">Lands with</th><th>Why</th></tr></thead><tbody>{tab}</tbody></table></div>

{"".join(blocos)}
"""
    return pagina("newsroom/board.html", "The board",
                  "Every agent's board: what it opened for itself, what the paper's issues put on "
                  "it by formula, and what mail is still unread.", corpo)


def pagina_correio(ag, msgs):
    ids = {a["id"]: a for a in ag.get("agentes", [])}
    lugares = "".join(
        f'<tr><td class="mono xs">{e(p)}</td><td class="mono xs">{e(nome)}</td>'
        f'<td class="sm">{e(desc)}</td></tr>' for p, nome, desc in LUGARES)

    # Threads, by Message-ID and In-Reply-To. A message with no parent starts a thread; the rest
    # hang off theirs. Sender copies in `saida/` are folded into the delivered message rather than
    # listed twice — they are the same message, in the sender's own record.
    entregues = [m for m in msgs if m["lugar"] in ("entrada", "tratado", "expedicao")]
    copias = {m["id"]: m for m in msgs if m["lugar"] == "saida"}
    filhos = {}
    for m in entregues:
        filhos.setdefault(m.get("responde_a"), []).append(m)

    def render(m, nivel=0):
        a = ids.get(m["caixa"], {})
        chip = {"expedicao": ("miss", "in transit"), "entrada": ("falta", "delivered · open"),
                "tratado": ("ok", "handled")}[m["lugar"]]
        copia = copias.get(m["id"])
        corpo_html = "".join(f"<p class='sm' style='max-width:52em'>{e(par)}</p>"
                             for par in re.split(r"\n\s*\n", m["corpo"]) if par.strip())
        filho_html = "".join(render(x, nivel + 1) for x in filhos.get(m["id"], []))
        return f"""
<div class="correio{' correio--resposta' if nivel else ''}" id="{e(m["id"])}">
  <div class="chips" style="padding-bottom:6px">
    <span class="chip {chip[0]}">{chip[1]}</span>
    <span class="chip"><b>{e(m["de_alias"])}</b> → {e(m["para_alias"])}</span>
    <span class="chip">{e(m["quando"])}</span>
    {f'<span class="chip">issue {e(m["issue"])}</span>' if m.get("issue") else ""}
    {f'<span class="chip">run {e(m["run"])}</span>' if m.get("run") else ""}
    {'<span class="chip falta">historical sender</span>' if m["historica"] else ""}
    {'<span class="chip">sender copy kept</span>' if copia else ""}
  </div>
  <p class="std" style="max-width:52em"><b>{e(m["assunto"])}</b></p>
  {corpo_html}
  <p class="xs mono">{e(m["ficheiro"])} · {m["bytes"]} bytes ·
     in <code>{e(a.get("alias", m["caixa"]))}</code>'s
     {'mailroom' if m["lugar"] == "expedicao" else m["lugar"]}
     {f'· sender copy at <code>{e(copia["ficheiro"])}</code>' if copia else ""}
     {f'· migrated from <code>{e(m["migrado_de"])}</code>' if m.get("migrado_de") else ""}</p>
  {filho_html}
</div>"""

    raizes = [m for m in entregues if m.get("responde_a") not in {x["id"] for x in entregues}]
    fios = "".join(render(m) for m in raizes)
    # A mailbox with something in entrada/ has somebody waiting on it, and the review's finding
    # was that a table of six count columns says so nowhere: you had to read the third column of
    # every row and remember what it meant. The state is now a rank, and the row itself is marked
    # when it is the editor's, because a state marked only inside a cell is one you have to hunt.
    def estado_da_caixa(aid, dentro, transito):
        humano = aid == "dinis.humano"
        if dentro and humano:
            return '<span class="st st--1">%d unread</span>' % dentro
        if dentro:
            return '<span class="st st--2">%d open</span>' % dentro
        if transito:
            return '<span class="st st--3">%d in transit</span>' % transito
        return '<span class="st st--4">clear</span>'

    filas = []
    for a in ag.get("agentes", []):
        n = {l: len([m for m in msgs if m["lugar"] == l and m["caixa"] == a["id"]])
             for l in ("expedicao", "entrada", "tratado", "saida")}
        marca = ' class="needs-you"' if (a["id"] == "dinis.humano" and n["entrada"]) else ""
        filas.append(
            f'<tr{marca}><td class="mono">{e(a["id"])}</td><td class="mono">{e(a["alias"])}</td>'
            f'<td class="num">{n["expedicao"]}</td><td class="num">{n["entrada"]}</td>'
            f'<td class="num">{n["tratado"]}</td><td class="num">{n["saida"]}</td>'
            f'<td>{estado_da_caixa(a["id"], n["entrada"], n["expedicao"])}</td></tr>')
    por_caixa = "".join(filas)

    # THE MODEL, SHOWN RATHER THAN EXPLAINED. The design review called the mail protocol the best
    # thing in the back office and its presentation the weakest: a paragraph and a four-row table
    # for something that is a path a file walks. Shown as the path, it needs no paragraph — and the
    # ranks are the console's own, so the folder that means "somebody has to act" looks like every
    # other thing on this site that means that.
    ROTA = [("saida", 4, "the sender's copy"), ("expedicao", 3, "in transit"),
            ("entrada", 2, "delivered, open"), ("tratado", 4, "handled")]
    rota = ' <span class="rota__seta">\u2192</span> '.join(
        f'<span class="st st--{r}">{nome}/</span><span class="muted">{desc}</span>'
        for nome, r, desc in ROTA)

    corpo = f"""
<h2>The mail · {len(entregues)} messages
between the agents</h2>
<p class="std" style="max-width:52em">The agents of this newsroom do not talk over a chat. They
talk in files, under <b>Email-FS-lite</b> — the protocol the sgraph.ai team
<a href="https://sgraph.ai/en-gb/library/how-it-works/email-fs-lite.md">publishes and runs</a>.
No broker, no daemon, no API: every message is an RFC 2822 <code>.eml</code> file, and the commit
history is the audit trail. Messages are immutable — never edited, never deleted, only moved. The
protocol was written to run inside an sgit vault, where <code>sgit pull</code> is the inbox
notification; here it runs inside a git repository, which changes the command and nothing else.
That difference is written down in
<a href="docs.html#redacao/correio/LEIA-ME.md"><code>redacao/correio/LEIA-ME.md</code></a> rather
than glossed over.</p>
<p class="note" style="max-width:78ch">And immutability here is a <b>discipline, not a
mechanism</b>: nothing in a git repository stops a write. So the protocol note carries the one
exception and the record of every use of it — the editor of record may authorise a
<b>sweep</b>, a mechanical change applied identically to every message that does not alter what
any of them asserts, such as a path that has been renamed. Rewriting a sentence, a number or a
conclusion is not a sweep and is not allowed; that is what a reply is for. Every sweep ever made
is listed in that note with the release it landed in and what authorised it — the number is not
repeated here, because a page that printed «the current version» would claim the last sweep
happened in whatever release you are reading. A rule the commit history quietly contradicts is
worse than no rule.</p>

<h2>Where a message sits is what state
it is in</h2>
<div class="card">
  <div class="rota">{rota}</div>
  <p class="note" style="margin:12px 0 0">There is no status field anywhere in the protocol. A
  field can disagree with the folder; a folder cannot disagree with itself. Delivery is the file
  having moved, and the read receipt is the mailroom copy no longer being there.</p>
</div>
<details class="provenance" style="margin-top:12px">
  <summary>What each folder means, in the protocol's own words</summary>
  <div class="rolar"><table><thead><tr><th style="width:110px">Folder</th>
    <th style="width:180px">State</th><th>Meaning</th></tr></thead><tbody>{lugares}</tbody></table></div>
</details>

<h2>Every mailbox, counted</h2>
<div class="rolar"><table><thead><tr><th>Agent</th><th>Alias</th><th class="num">In transit</th>
  <th class="num">Inbox</th><th class="num">Handled</th><th class="num">Sent copies</th>
  <th>State</th></tr></thead>
  <tbody>{por_caixa}</tbody></table></div>

<h2>The threads</h2>
<p class="sm" style="max-width:52em">Threaded by <code>Message-ID</code> and
<code>In-Reply-To</code>. Replying does not close anything: a message stays open work while it
sits in an inbox, and only moves to <code>tratado/</code> when the work it asked for is done.</p>
{fios or '<p class="sm">No mail yet.</p>'}
"""
    return pagina("newsroom/mail.html", "The mail",
                  "Every message between the newsroom's agents, threaded, with the state each "
                  "one's folder implies.", corpo)


# ---------------------------------------------------------------------- main ---
def main():
    ag = carregar("agentes.json")
    if not ag:
        print("team: dados/agentes.json does not exist — nothing to do")
        return []
    ids = {a["id"] for a in ag.get("agentes", [])}
    msgs = ler_correio(ids)
    cartoes = ler_cartoes()
    issues = ler_issues_do_jornal(ag.get("formula_do_quadro", {}))
    q = quadro(ag.get("agentes", []), cartoes, issues, msgs)

    (DADOS / "correio.json").write_text(json.dumps({
        "id": "pt-correio", "versao": "0.1.0", "atualizado": time.strftime("%Y-%m-%d"),
        "protocolo": ag.get("protocolo"), "protocolo_versao": ag.get("protocolo_versao"),
        "nota": ("Cada mensagem entre os agentes desta redação, lida de redacao/correio/ por "
                 "build/newsroom_team.py. O estado de uma mensagem é a pasta onde está e não um campo: "
                 "um campo pode discordar da pasta, uma pasta não pode discordar de si mesma. "
                 "Este é o ficheiro que as páginas leem — a pasta tem um leitor só."),
        "lugares": [{"pasta": p, "estado": n, "significa": d} for p, n, d in LUGARES],
        "contagem": len(msgs), "mensagens": msgs,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    (DADOS / "quadro.json").write_text(json.dumps({
        "id": "pt-quadro", "versao": "0.1.0", "atualizado": time.strftime("%Y-%m-%d"),
        "nota": ("O quadro de cada agente. Um cartão em «assuntos» é trabalho que o agente abriu "
                 "para si; um issue do jornal chega ao quadro pela fórmula publicada em "
                 "dados/agentes.json e por mais nada."),
        "formula": ag.get("formula_do_quadro", {}),
        "colunas": [c for c, _, _ in COLUNAS],
        "contagens": {"cartoes": len(cartoes), "issues_do_jornal": len(issues),
                      "agentes": len(ids)},
        "por_agente": q,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    feitas = [
        escrever("newsroom/team.html", pagina_equipa(ag, q)),
        escrever("newsroom/board.html", pagina_quadro(ag, q)),
        escrever("newsroom/mail.html", pagina_correio(ag, msgs)),
    ]
    desconhecidos = sorted({x for m in msgs for x in m["desconhecido"]}
                           - {h["id"] for h in ag.get("identidades_historicas", [])})
    if desconhecidos:
        print(f"team: WARNING — addresses that are neither in the register nor declared "
              f"historical: {', '.join(desconhecidos)}")
    print(f"team: {len(feitas)} pages, {len(ag.get('agentes', []))} agents, {len(msgs)} "
          f"messages, {len(cartoes)} board cards, {len(issues)} paper issues placed by formula")
    return feitas


if __name__ == "__main__":
    main()

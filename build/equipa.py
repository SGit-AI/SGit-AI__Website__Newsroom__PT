#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the agent team, the board and the mail. One reader, three pages.

    python3 build/equipa.py

WHAT THIS IS

The newsroom's agents coordinate by files, under the Email-FS-lite protocol that the sgraph.ai
team publishes and runs (https://sgraph.ai/en-gb/library/how-it-works/email-fs-lite.md). This
script is the ONE reader of that folder. It walks `redacao/correio/`, derives two data files, and
renders three back-office pages from the derived data:

    dados/correio.json    every message, with the state its location implies
    dados/quadro.json     every board card: the agent's own, and the paper's issues by formula

    backoffice/equipa.html    who the agents are — the roster, in the ROLE.md shape
    backoffice/quadro.html    what each one has in front of it — the board
    backoffice/correio.html   what passed between them — the mail, threaded

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
from backoffice import GH, VERSAO, e, escrever, pagina  # noqa: E402  the one page chrome

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
def ficha(chip, texto):
    return f'<span class="chip {chip}">{e(texto)}</span>'


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
        blocos.append(f"""
<div class="cartao" style="padding:16px;margin-top:18px" id="{e(a["id"])}">
  <div class="chips" style="padding-bottom:8px">
    <span class="chip ok" style="font-size:13px"><b>{e(a["alias"])}</b></span>
    <span class="chip">{e(a["id"])}</span>
    <span class="chip">{e(a.get("modelo", ""))}</span>
    {ficha("", "tier " + str(a.get("nivel", "—")))}
    {ficha("ok" if a.get("estado") == "a-correr" else "miss", a.get("estado", "—"))}
    {'<span class="chip falta">human in the loop</span>' if humano else ""}
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
      <p class="sm" style="padding-top:6px"><a href="quadro.html#{e(a["id"])}">its board →</a> ·
         <a href="correio.html#{e(a["id"])}">its mail →</a></p>
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
<div class="rule" style="padding:26px 0 8px"><div class="sect">The team · {len(agentes)} roles,
one of them human</div></div>
<p class="std" style="max-width:52em;padding-bottom:6px">{e(ag["nota"])}</p>
<div class="chips" style="padding-bottom:16px">
  {ficha("ok", f"{len(agentes)} roles")}
  {ficha("", f"{cartoes_totais} board cards")}
  {ficha("", "protocol email-fs-lite " + str(ag.get("protocolo_versao", "")))}
  {ficha("falta", f'{len(ag.get("nao_construido", []))} roles deliberately not built')}
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

<div class="rule" style="padding:26px 0 8px"><div class="sect">The write rule</div></div>
<p class="std" style="max-width:52em">{e(ag["regra_de_escrita"])}</p>

<div class="rule" style="padding:26px 0 8px"><div class="sect">Publishing is not an agent</div></div>
<p class="std" style="max-width:52em"><b>{e(ag["publicacao"]["o_que_e"])}</b>
{e(ag["publicacao"]["porque"])}</p>

<div class="rule" style="padding:26px 0 8px"><div class="sect">Roles deliberately not built</div></div>
<p class="sm" style="max-width:52em;padding-bottom:8px">A roster that claimed roles nobody runs
would be claiming a capability. These are named with the reason they are absent, which is the same
discipline <code>dados/equipa.json</code> already applies to departments.</p>
<div class="rolar"><table><thead><tr><th style="width:20%">Role</th><th>Why not</th></tr></thead>
<tbody>{nao_construido}</tbody></table></div>

<div class="rule" style="padding:26px 0 8px"><div class="sect">Retired identities</div></div>
<p class="sm" style="max-width:52em;padding-bottom:8px">Mail is never deleted, so a sender that no
longer exists still has to resolve to something. These are declared in the message header and
shown as historical, rather than failing the reader on a name it does not know.</p>
<div class="rolar"><table><thead><tr><th style="width:20%">Identity</th><th>What it was</th></tr>
</thead><tbody>{historicas}</tbody></table></div>
"""
    return pagina("backoffice/equipa.html", "The team",
                  "The newsroom's agents: mission, central claim, what each is not responsible "
                  "for, and what each has on its plate.", corpo)


def pagina_quadro(ag, q):
    blocos = []
    for a in ag.get("agentes", []):
        v = q.get(a["id"], {})
        c = v.get("contagens", {})
        cols = []
        for coluna, rotulo, chip in COLUNAS:
            cartoes = v.get("colunas", {}).get(coluna, [])
            itens = []
            if coluna == "abertos":
                for i in v.get("issues_do_jornal", []):
                    itens.append(f"""
<div class="cartao">
  <div class="chips" style="padding-bottom:6px">
    <span class="chip">paper issue {e(i["id"])}</span>
    <span class="chip">{e(i["estado"])}</span>
    {f'<span class="chip">{e(i["seccao"])}</span>' if i.get("seccao") else ""}
  </div>
  <p class="sm"><a href="../redacao/">{e(i["titulo"])}</a></p>
  <p class="xs mono">by formula: {e(i["porque_aqui"])}</p>
</div>""")
            for x in cartoes:
                bl = (f'<span class="chip miss">waiting on {e(x["bloqueado_por"])}</span>'
                      if x.get("bloqueado_por") else "")
                itens.append(f"""
<div class="cartao">
  <div class="chips" style="padding-bottom:6px">
    {f'<span class="chip">{e(x["prioridade"])}</span>' if x.get("prioridade") else ""}
    {f'<span class="chip">{e(x["esforco"])}</span>' if x.get("esforco") and x["esforco"] != "—" else ""}
    {f'<span class="chip">issue {e(x["issue"])}</span>' if x.get("issue") else ""}
    {bl}
  </div>
  <p class="sm"><b>{e(x["titulo"])}</b></p>
  <p class="xs">{e(x["resumo"])}…</p>
  <p class="xs mono"><a href="docs.html#{e(x["ficheiro"])}">{e(x["ficheiro"])}</a></p>
</div>""")
            n = len(cartoes) + (len(v.get("issues_do_jornal", [])) if coluna == "abertos" else 0)
            cols.append(f"""
<div class="col sp6">
  <div class="chips"><span class="chip {chip}">{rotulo} · {n}</span></div>
  {"".join(itens) or '<p class="sm" style="padding-top:8px">Nothing here.</p>'}
</div>""")
        entrada = "".join(
            f'<div class="cartao"><div class="chips" style="padding-bottom:6px">'
            f'<span class="chip falta">unread</span><span class="chip">from {e(m["de_alias"])}</span>'
            f'</div><p class="sm">{e(m["assunto"])}</p>'
            f'<p class="xs mono"><a href="correio.html#{e(m["id"])}">{e(m["ficheiro"])}</a></p></div>'
            for m in v.get("entrada", []))
        transito = "".join(
            f'<div class="cartao"><div class="chips" style="padding-bottom:6px">'
            f'<span class="chip miss">in transit</span><span class="chip">from {e(m["de_alias"])}'
            f'</span></div><p class="sm">{e(m["assunto"])}</p>'
            f'<p class="xs mono">waiting for {e(a["alias"])} to collect it into its inbox</p></div>'
            for m in v.get("em_transito", []))
        blocos.append(f"""
<div class="rule" style="padding:26px 0 8px" id="{e(a["id"])}">
  <div class="sect">{e(a["alias"])} · {e(a["nome"])}</div></div>
<div class="chips" style="padding-bottom:10px">
  <span class="chip">{e(a["id"])}</span>
  {ficha("ok", f'{c.get("abertos", 0)} open')}
  {ficha("miss", f'{c.get("bloqueados", 0)} blocked')}
  {ficha("", f'{c.get("fechados", 0)} closed')}
  {ficha("", f'{c.get("issues_do_jornal", 0)} paper issues')}
  {ficha("falta", f'{c.get("por_tratar", 0)} unread mail') if c.get("por_tratar") else ""}
  <a class="chip" href="equipa.html#{e(a["id"])}">its definition →</a>
</div>
<div class="g3 sp12">{"".join(cols)}</div>
{f'<div class="sect" style="padding-top:14px">Mail on its plate</div><div class="g2 sp12">'
 f'<div class="col sp6">{entrada}</div><div class="col sp6">{transito}</div></div>'
 if (entrada or transito) else ""}
""")

    f = ag.get("formula_do_quadro", {})
    tab = "".join(
        f'<tr><td class="mono xs">{e(k)}</td><td class="mono xs">{e(vv)}</td>'
        f'<td class="sm">{e(f.get("porque", {}).get(k, ""))}</td></tr>'
        for k, vv in f.get("de_estado_para_agente", {}).items())
    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">The board · what each agent has in
front of it</div></div>
<p class="std" style="max-width:52em">Two kinds of card, kept apart on purpose. A <b>board card</b>
is work the agent opened for itself, in
<code>redacao/correio/&lt;agent&gt;/assuntos/&lt;column&gt;/</code>, and it carries the agent's own
reading of the work — intent, approach, acceptance criterion. A <b>paper issue</b> is one of the
publication's own issues in <code>redacao/issues/</code>, placed on an agent's board by the
formula below and by nothing else. A card moves column in the same commit as the mail action that
moved it, which is why the board cannot disagree with the mail.</p>
<p class="sm" style="max-width:52em;padding-bottom:10px">Nothing on this page is a claim about
Portugal. Every count is a count of files in this repository.</p>

<div class="rule" style="padding:18px 0 8px"><div class="sect">The formula, printed because it is
used</div></div>
<p class="sm" style="max-width:52em;padding-bottom:8px">{e(f.get("nota", ""))}</p>
<div class="rolar"><table><thead><tr><th style="width:130px">Issue state</th>
  <th style="width:140px">Lands with</th><th>Why</th></tr></thead><tbody>{tab}</tbody></table></div>

{"".join(blocos)}
"""
    return pagina("backoffice/quadro.html", "The board",
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
<div class="correio" style="margin-top:16px;{'margin-left:22px' if nivel else ''}" id="{e(m["id"])}">
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
    por_caixa = "".join(
        f'<tr><td class="mono xs">{e(a["id"])}</td><td class="mono xs">{e(a["alias"])}</td>'
        f'<td class="xs">{len([m for m in msgs if m["lugar"] == "expedicao" and m["caixa"] == a["id"]])}</td>'
        f'<td class="xs">{len([m for m in msgs if m["lugar"] == "entrada" and m["caixa"] == a["id"]])}</td>'
        f'<td class="xs">{len([m for m in msgs if m["lugar"] == "tratado" and m["caixa"] == a["id"]])}</td>'
        f'<td class="xs">{len([m for m in msgs if m["lugar"] == "saida" and m["caixa"] == a["id"]])}</td>'
        f'</tr>' for a in ag.get("agentes", []))

    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">The mail · {len(entregues)} messages
between the agents</div></div>
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

<div class="rule" style="padding:18px 0 8px"><div class="sect">Where a message sits is what state
it is in</div></div>
<p class="sm" style="max-width:52em;padding-bottom:8px">There is no status field anywhere in the
protocol. A field can disagree with the folder; a folder cannot disagree with itself. Delivery is
the file having moved, and the read receipt is the mailroom copy no longer being there.</p>
<div class="rolar"><table><thead><tr><th style="width:110px">Folder</th>
  <th style="width:180px">State</th><th>Meaning</th></tr></thead><tbody>{lugares}</tbody></table></div>

<div class="rule" style="padding:18px 0 8px"><div class="sect">Every mailbox, counted</div></div>
<div class="rolar"><table><thead><tr><th>Agent</th><th>Alias</th><th>In transit</th>
  <th>Inbox</th><th>Handled</th><th>Sent copies</th></tr></thead>
  <tbody>{por_caixa}</tbody></table></div>

<div class="rule" style="padding:26px 0 8px"><div class="sect">The threads</div></div>
<p class="sm" style="max-width:52em">Threaded by <code>Message-ID</code> and
<code>In-Reply-To</code>. Replying does not close anything: a message stays open work while it
sits in an inbox, and only moves to <code>tratado/</code> when the work it asked for is done.</p>
{fios or '<p class="sm">No mail yet.</p>'}
"""
    return pagina("backoffice/correio.html", "The mail",
                  "Every message between the newsroom's agents, threaded, with the state each "
                  "one's folder implies.", corpo)


# ---------------------------------------------------------------------- main ---
def main():
    ag = carregar("agentes.json")
    if not ag:
        print("equipa: dados/agentes.json não existe — nada a fazer")
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
                 "build/equipa.py. O estado de uma mensagem é a pasta onde está e não um campo: "
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
        escrever("backoffice/equipa.html", pagina_equipa(ag, q)),
        escrever("backoffice/quadro.html", pagina_quadro(ag, q)),
        escrever("backoffice/correio.html", pagina_correio(ag, msgs)),
    ]
    desconhecidos = sorted({x for m in msgs for x in m["desconhecido"]}
                           - {h["id"] for h in ag.get("identidades_historicas", [])})
    if desconhecidos:
        print(f"equipa: AVISO — endereços que não estão no registo nem declarados como "
              f"históricos: {', '.join(desconhecidos)}")
    print(f"equipa: {len(feitas)} pages, {len(ag.get('agentes', []))} agents, {len(msgs)} "
          f"messages, {len(cartoes)} board cards, {len(issues)} paper issues placed by formula")
    return feitas


if __name__ == "__main__":
    main()

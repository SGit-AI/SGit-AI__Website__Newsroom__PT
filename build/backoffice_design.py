#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the design review, item by item, and what was actually done to each.

    python3 build/backoffice_design.py

WHY THIS PAGE EXISTS

A design review that lands as a pile of commits becomes folklore within a month: somebody asks
"did we do the contrast thing?" and the answer is a search through git log. This page is the
answer, and it is generated from `dados/desenho.json` so it cannot drift from the record.

It also does the thing the review itself asked for and that reviews almost never get: it says,
for every one of the 34 items, whether it was **done**, **deferred** or **the editor's to
decide** — and for the deferred ones, what specifically blocks them. A review with five items
silently dropped is worse than a review with five items marked undone, because the reader of the
former cannot tell the difference between "considered and rejected" and "forgotten".

THE THREE THINGS THIS PAGE REFUSES TO DO

1. It does not mark an item done that a gate does not hold. Where `build/gates_desenho.py`
   asserts the item, the page says which gate — and if the gate is red the build never gets here.
2. It does not decide the five things the review reserved for the editor. They are listed with
   their trade-offs and nothing else, and they are on the editor's board.
3. It does not claim the review was right about everything. Two of its numbers were wrong, one of
   them in a way that changed the answer, and both are recorded as corrections with the
   measurement that settled them.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backoffice import e, escrever, pagina  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"

# THE DISPOSITION OF A REVIEW ITEM, ON THE CONSOLE'S FOUR-RANK SCALE. The paper's chip classes
# were chosen when there was one chip style used 159 ways, and two of the five were the wrong way
# round under a scale where only rank 1 is filled: `parcial` came out filled red, which now means
# "a human must act", and `editor` — the one disposition that really does mean that — came out as
# the quiet neutral outline. So the mapping is to ranks, and the rank IS the meaning.
#
#   1  a human must act      the editor decides
#   2  blocked / not moving  deferred
#   3  running               partly done
#   4  done                  done, corrected the review
ESTADOS = {
    "feito": (4, "done"),
    "parcial": (3, "partly done"),
    "adiado": (2, "deferred"),
    "editor": (1, "the editor decides"),
    "corrigido": (4, "corrected the review"),
}


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def bloco(item):
    r, rotulo = ESTADOS.get(item["estado"], (3, item["estado"]))
    # Which gate holds an item is a FACT about it, not a state of it. It was a box of the same
    # weight as the disposition beside it.
    gate = (f'<span class="path">held by {e(item["portao"])}</span>'
            if item.get("portao") else "")
    prova = (f'<p class="xs mono">measured: {e(item["medida"])}</p>'
             if item.get("medida") else "")
    bloqueio = (f'<p class="sm"><b>What blocks it:</b> {e(item["bloqueio"])}</p>'
                if item.get("bloqueio") else "")
    onde = (f'<p class="xs mono">{" · ".join(e(x) for x in item["onde"])}</p>'
            if item.get("onde") else "")
    return f"""
<div class="cartao" style="padding:14px;margin-top:12px">
  <div class="queue__meta" style="margin:0 0 6px">
    <span class="st st--{r}">{rotulo}</span>
    <span class="path">§{e(item["ref"])}</span>
    {gate}
  </div>
  <p class="std"><b>{e(item["titulo"])}</b></p>
  <p class="sm">{e(item["o_que_se_fez"])}</p>
  {bloqueio}{prova}{onde}
</div>"""


def pagina_desenho(d):
    contagens = {}
    for i in d["itens"]:
        contagens[i["estado"]] = contagens.get(i["estado"], 0) + 1
    fichas = " ".join(
        f'<span class="st st--{ESTADOS[k][0]}">{v} {ESTADOS[k][1]}</span>'
        for k, v in sorted(contagens.items(), key=lambda kv: -kv[1]) if k in ESTADOS)

    grupos = {}
    for i in d["itens"]:
        grupos.setdefault(i["grupo"], []).append(i)

    secs = ""
    for nome, itens in grupos.items():
        secs += (f'<h2>{e(nome)} · '
                 f'{len(itens)} items</h2>'
                 + "".join(bloco(i) for i in itens))

    decisoes = "".join(
        f'<div class="cartao" style="padding:14px;margin-top:12px">'
        f'<div class="queue__meta" style="margin:0 0 6px">'
        f'<span class="st st--1">decision {n}</span>'
        f'<span class="path">§{e(x["ref"])}</span></div>'
        f'<p class="std"><b>{e(x["pergunta"])}</b></p>'
        f'<p class="sm">{e(x["porque_e_do_editor"])}</p>'
        f'<p class="sm"><b>The options:</b> {e(x["opcoes"])}</p>'
        f'<p class="xs mono">on the board: {e(x["cartao"])}</p></div>'
        for n, x in enumerate(d["decisoes_do_editor"], 1))

    correcoes = "".join(
        f'<div class="aviso-bloco" style="margin-top:12px">'
        f'<p class="sm"><b>§{e(x["ref"])} — {e(x["o_que_a_revisao_disse"])}</b></p>'
        f'<p class="sm">{e(x["o_que_a_medicao_mostrou"])}</p>'
        f'<p class="sm"><b>Consequence:</b> {e(x["consequencia"])}</p></div>'
        for x in d["correcoes_a_revisao"])

    corpo = f"""
<h2>The design review, item by item
  </h2>
<p class="std">{e(d["nota"])}</p>
<div class="chips" style="padding:12px 0">{fichas}</div>
<p class="sm">Source: the encrypted vault <code>{e(d["cofre"])}</code>, version
{e(d["revisao_versao"])}, reviewed against site build {e(d["revisao_contra"])}. The review is not
copied into this repository: it is a vault the editor holds, and a copy here would disagree with it
the first time it was updated. What this page carries is the <b>disposition</b> of each item, which
is this repository's business and not the vault's.</p>

<h2>Where the review was wrong, and how
  we know</h2>
<p class="sm">The review measured rather than asserted, which is why it was worth implementing.
Two of its numbers were still wrong, and one of them changed the answer. Recording that is not
scoring a point: an implementation that had followed the review exactly would have shipped a
column that still missed the review's own target, and nobody would have known.</p>
{correcoes}

{secs}

<h2>The five decisions the review
  reserved for the editor</h2>
<p class="std">§4.5 of the review says, in as many words: <i>"Agents: do not pick these
yourself."</i> None of them is picked here. Each is a card on
<a href="board.html#dinis.humano">the editor's board</a>.</p>
{decisoes}

<div class="agent" style="border:0;margin-top:26px">
<p class="sm"><b>On the one item that looks small and is not.</b>
{e(d["o_blocker"])}</p>
</div>
"""
    return pagina("backoffice/design.html", "The design review",
                  "Every item of the design review, and whether it was done, deferred, or left "
                  "to the editor — with the gate that holds each one that was done.", corpo)


def main():
    d = carregar("desenho.json")
    if not d:
        print("design: dados/desenho.json does not exist — nothing to do")
        return []
    feitas = [escrever("backoffice/design.html", pagina_desenho(d))]
    c = {}
    for i in d["itens"]:
        c[i["estado"]] = c.get(i["estado"], 0) + 1
    print("design: 1 page, " + ", ".join(f"{v} {k}" for k, v in sorted(c.items()))
          + f", {len(d['decisoes_do_editor'])} decisions for the editor")
    return feitas


if __name__ == "__main__":
    main()

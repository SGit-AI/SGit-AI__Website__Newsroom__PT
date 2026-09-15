#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the design review, item by item, and what was actually done to each.

    python3 build/desenho.py

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

ESTADOS = {
    "feito": ("ok", "done"),
    "parcial": ("falta", "partly done"),
    "adiado": ("miss", "deferred"),
    "editor": ("disputa", "the editor decides"),
    "corrigido": ("ok", "corrected the review"),
}


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def bloco(item):
    chip, rotulo = ESTADOS.get(item["estado"], ("", item["estado"]))
    gate = (f'<span class="chip ok">held by {e(item["portao"])}</span>'
            if item.get("portao") else "")
    prova = (f'<p class="xs mono">measured: {e(item["medida"])}</p>'
             if item.get("medida") else "")
    bloqueio = (f'<p class="sm"><b>What blocks it:</b> {e(item["bloqueio"])}</p>'
                if item.get("bloqueio") else "")
    onde = (f'<p class="xs mono">{" · ".join(e(x) for x in item["onde"])}</p>'
            if item.get("onde") else "")
    return f"""
<div class="cartao" style="padding:14px;margin-top:12px">
  <div class="chips" style="padding-bottom:6px">
    <span class="chip">§{e(item["ref"])}</span>
    <span class="chip {chip}">{rotulo}</span>
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
        f'<span class="chip {ESTADOS[k][0]}">{v} {ESTADOS[k][1]}</span>'
        for k, v in sorted(contagens.items(), key=lambda kv: -kv[1]) if k in ESTADOS)

    grupos = {}
    for i in d["itens"]:
        grupos.setdefault(i["grupo"], []).append(i)

    secs = ""
    for nome, itens in grupos.items():
        secs += (f'<div class="rule" style="padding:26px 0 8px"><div class="sect">{e(nome)} · '
                 f'{len(itens)} items</div></div>'
                 + "".join(bloco(i) for i in itens))

    decisoes = "".join(
        f'<div class="cartao" style="padding:14px;margin-top:12px">'
        f'<div class="chips" style="padding-bottom:6px">'
        f'<span class="chip disputa">decision {n}</span>'
        f'<span class="chip">§{e(x["ref"])}</span></div>'
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
<div class="rule" style="padding:26px 0 8px"><div class="sect">The design review, item by item
  </div></div>
<p class="std">{e(d["nota"])}</p>
<div class="chips" style="padding:12px 0">{fichas}</div>
<p class="sm">Source: the encrypted vault <code>{e(d["cofre"])}</code>, version
{e(d["revisao_versao"])}, reviewed against site build {e(d["revisao_contra"])}. The review is not
copied into this repository: it is a vault the editor holds, and a copy here would disagree with it
the first time it was updated. What this page carries is the <b>disposition</b> of each item, which
is this repository's business and not the vault's.</p>

<div class="rule" style="padding:26px 0 8px"><div class="sect">Where the review was wrong, and how
  we know</div></div>
<p class="sm">The review measured rather than asserted, which is why it was worth implementing.
Two of its numbers were still wrong, and one of them changed the answer. Recording that is not
scoring a point: an implementation that had followed the review exactly would have shipped a
column that still missed the review's own target, and nobody would have known.</p>
{correcoes}

{secs}

<div class="rule" style="padding:26px 0 8px"><div class="sect">The five decisions the review
  reserved for the editor</div></div>
<p class="std">§4.5 of the review says, in as many words: <i>"Agents: do not pick these
yourself."</i> None of them is picked here. Each is a card on
<a href="quadro.html#dinis.humano">the editor's board</a>.</p>
{decisoes}

<div class="agent" style="border:0;margin-top:26px">
<p class="sm"><b>On the one item that looks small and is not.</b>
{e(d["o_blocker"])}</p>
</div>
"""
    return pagina("backoffice/desenho.html", "The design review",
                  "Every item of the design review, and whether it was done, deferred, or left "
                  "to the editor — with the gate that holds each one that was done.", corpo)


def main():
    d = carregar("desenho.json")
    if not d:
        print("desenho: dados/desenho.json não existe — nada a fazer")
        return []
    feitas = [escrever("backoffice/desenho.html", pagina_desenho(d))]
    c = {}
    for i in d["itens"]:
        c[i["estado"]] = c.get(i["estado"], 0) + 1
    print("desenho: 1 page, " + ", ".join(f"{v} {k}" for k, v in sorted(c.items()))
          + f", {len(d['decisoes_do_editor'])} decisions for the editor")
    return feitas


if __name__ == "__main__":
    main()

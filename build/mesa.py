#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the desk as a place rather than as a table.

    python3 build/mesa.py       # after comentarios.py, before build.py

THE ASK. The editor pointed at newsroom.sgit.ai's virtual newsroom — *"a virtual newsroom with
visual representations of the articles, with Kanban boards, almost a visual news desk"* — and said
that `/redacao/` here is a table and that one is a room.

The difference is not decoration. A table shows rows; a room shows **load**: who has what on the
desk right now, what is stalled waiting on whom, and where the next move is. Those are different
questions, and the second is the one you ask a newsroom at five in the afternoon.

WHAT THIS FILE DOES. It gathers into one document what is already scattered — the benches and what
each may write (`dados/equipa.json`), the board (`redacao/issues/`), the mail
(`redacao/correio/`), the run records (`redacao/runs/`) and the per-agent work
(`dados/comentarios.json`) — and counts each bench's load from that. It invents no state: every
number here is a count of files or entries that already exist.

AND ONE THING IT DOES NOT DO. It moves nothing. The desk shows where things are; who moves them is
whoever has write access to that folder, and the step no automated run may take — putting a story
into `publicado` — stays the editor of record's, and the room says so in the column where they
would be.
"""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
REDACAO = ROOT / "redacao"

# The board's columns, in the order a story crosses them. `quem_move` is not decorative: it is the
# rule for who may push a card there, and the last one is the reason a human exists in this loop.
COLUNAS = [
    {"id": "procurado", "rotulo": "Procurado",
     "o_que_significa": "A história está encomendada e o material ainda não a sustenta.",
     "quem_move": "pesquisa"},
    {"id": "congelado", "rotulo": "Congelado",
     "o_que_significa": "As fontes estão congeladas e hasheadas; falta escrever ou verificar.",
     "quem_move": "pesquisa"},
    {"id": "rascunho", "rotulo": "Rascunho",
     "o_que_significa": "Há prosa, e cada afirmação já aponta para uma fonte congelada.",
     "quem_move": "redacao"},
    {"id": "verificado", "rotulo": "Verificado",
     "o_que_significa": "Cada afirmação foi relida contra os bytes e tem um veredito registado.",
     "quem_move": "verificacao"},
    {"id": "publicado", "rotulo": "Publicado",
     "o_que_significa": "Está no ar. É a única coluna para onde nenhuma execução automática pode "
                        "empurrar um cartão: a linha é do editor de registo, e é isso que torna "
                        "esta publicação responsabilidade de uma pessoa nomeada.",
     "quem_move": "editor"},
]


def carregar(f, omissao=None):
    p = Path(f)
    if not p.exists():
        return omissao if omissao is not None else {}
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    equipa = carregar(DADOS / "equipa.json")
    comentarios = carregar(DADOS / "comentarios.json")
    historias = carregar(DADOS / "historias.json")
    entregas = carregar(DADOS / "entregas.json")
    hoje = carregar(DADOS / "registo.json").get("atualizado", time.strftime("%Y-%m-%d"))

    # --- the board: every issue and every article, in the column it is in ------
    issues = [carregar(f) for f in sorted((REDACAO / "issues").glob("*.json"))] \
        if (REDACAO / "issues").exists() else []
    # ONE ISSUE CAN PRODUCE MORE THAN ONE ARTICLE, and in this repository it already does: issue
    # 001 commissioned the story about the agenda's legal instrument, and out of the same
    # commission also came the story about the national register returning no text. The first
    # version of this function assumed one article per issue, matched the issue to the first it
    # found, and **left the other off the board** — a board that hides work is worse than no board,
    # because it looks complete.
    #
    # So the card is the ARTICLE, which is the thing with files and a true state, and an issue
    # only gets a card of its own when it has not yet produced one.
    por_issue = {}
    for h in historias.get("historias", []):
        if h.get("issue"):
            por_issue.setdefault(h["issue"], []).append(h)
    issue_por_id = {i.get("id"): i for i in issues}

    cartoes = []
    for h in historias.get("historias", []):
        i = issue_por_id.get(h.get("issue")) or {}
        cartoes.append({
            "id": h["slug"], "titulo": h.get("titulo", ""), "seccao": h.get("seccao"),
            "estado": h.get("estado"), "especie": "artigo",
            "url": h.get("url"),
            "issue": h.get("issue"),
            "irmaos": len(por_issue.get(h.get("issue"), [])) - 1 if h.get("issue") else 0,
            "ultimo_toque": i.get("ultimo_toque", {}),
            "aberto_em": h.get("data"),
            "de": f'dados/historias.json#historias[{h["slug"]}]',
        })
    for i in issues:
        if por_issue.get(i.get("id")):
            continue
        cartoes.append({
            "id": i.get("id"), "titulo": i.get("titulo", ""), "seccao": i.get("seccao"),
            "estado": i.get("estado"), "especie": "issue",
            "url": None, "issue": i.get("id"), "irmaos": 0,
            "ultimo_toque": i.get("ultimo_toque", {}),
            "aberto_em": i.get("aberto_em"),
            "de": f'redacao/issues/{i.get("id")}',
        })

    quadro = {c["id"]: [] for c in COLUNAS}
    fora = []
    for cart in cartoes:
        (quadro[cart["estado"]] if cart["estado"] in quadro else fora).append(cart)

    # --- the mail, counted per bench -----------------------------------------
    # Counted from `dados/correio.json` and not from the folder. `redacao/correio/` has ONE reader,
    # `build/backoffice_team.py`, which reads the `.eml` files and derives each message's state from the
    # folder it sits in. Counting the folder again here would be a second reader of the same thing
    # — and it would be the second reader that goes stale, as this one did when the mail moved to
    # `.eml` and the boxes took the protocol address («pesquisa.pt») instead of the short name
    # («pesquisa»).
    corr = carregar(DADOS / "correio.json")
    registo_agentes = carregar(DADOS / "agentes.json")
    # `id_curto` -> `id`, from the register, which is where the correspondence between the two
    # identifiers lives. Without it, a bench called «pesquisa» does not find the «pesquisa.pt» box.
    ENDERECO = {a["id_curto"]: a["id"] for a in registo_agentes.get("agentes", [])}

    def correio(dep):
        caixa_id = ENDERECO.get(dep, dep)
        msgs = [m for m in corr.get("mensagens", []) if m.get("caixa") == caixa_id]
        return {
            "entrada": sum(1 for m in msgs if m.get("lugar") == "entrada"),
            "saida": sum(1 for m in msgs if m.get("lugar") == "saida"),
            "tratado": sum(1 for m in msgs if m.get("lugar") == "tratado"),
            "em_transito": sum(1 for m in msgs if m.get("lugar") == "expedicao"),
        }

    # --- the run records -----------------------------------------------------
    runs = [carregar(f) for f in sorted((REDACAO / "runs").glob("*.json"))] \
        if (REDACAO / "runs").exists() else []

    # --- the benches ---------------------------------------------------------
    por_agente = comentarios.get("por_agente", {})
    bancadas = []
    for d in equipa.get("departamentos", []):
        carga = por_agente.get(d["id"], {"total": 0, "abertos": 0, "especies": {}})
        meus = [c for c in cartoes
                if next((col for col in COLUNAS if col["id"] == c["estado"]), {}).get("quem_move")
                == d["id"]]
        bancadas.append({
            "id": d["id"], "nome": d["nome"], "especie": "departamento",
            "gravidade": d.get("gravidade"), "faz": d.get("faz"), "recusa": d.get("recusa"),
            "escreve_em": d.get("escreve_em", []),
            "carga": {"entradas": carga["total"], "abertas": carga["abertos"],
                      "por_especie": carga.get("especies", {}),
                      "cartoes_a_espera": len(meus)},
            "cartoes": [c["id"] for c in meus],
            "correio": correio(d["id"]),
            "execucoes": sum(1 for r in runs
                             if any(p.startswith(x.split("/")[0])
                                    for p in r.get("pastas_alteradas", [])
                                    for x in d.get("escreve_em", []))),
        })

    ed = equipa.get("editor_de_registo", {})
    carga_ed = por_agente.get("editor", {"total": 0, "abertos": 0, "especies": {}})
    por_rever = sum(1 for x in entregas.get("entregas", [])
                    if x.get("revisao", {}).get("estado") == "por_rever")
    bancadas.append({
        "id": "editor", "nome": ed.get("nome", "Editor de registo"), "especie": "editor de registo",
        "gravidade": "A linha que nenhuma execução automática pode escrever.",
        "faz": ed.get("o_que_faz"), "recusa": None,
        "escreve_em": ed.get("so_ele_pode", []),
        "carga": {"entradas": carga_ed["total"], "abertas": carga_ed["abertos"],
                  "por_especie": carga_ed.get("especies", {}),
                  "cartoes_a_espera": len(quadro.get("verificado", [])),
                  "entregas_por_rever": por_rever},
        "cartoes": [c["id"] for c in quadro.get("verificado", [])],
        "correio": correio("editor"),
        "execucoes": 0,
    })

    doc = {
        "id": "pt-mesa", "versao": "0.1.0", "atualizado": hoje,
        "nota": ("A mesa como estado, não como narrativa. Cada número é uma contagem de ficheiros "
                 "ou de entradas que já existem noutro lado deste repositório; nada aqui é "
                 "escrito. Nenhuma coluna se move a partir desta página: mostra onde as coisas "
                 "estão, e quem as move é quem tem direito de escrita naquela pasta."),
        "colunas": COLUNAS,
        "bancadas": bancadas,
        "quadro": quadro,
        "fora_do_quadro": fora,
        "execucoes": [{"quando": r.get("quando"), "versao": r.get("versao"),
                       "modelo": r.get("modelo"), "portoes": r.get("portoes"),
                       "pastas": r.get("pastas_alteradas", []),
                       "movidos": len(r.get("issues_movidos", []))}
                      for r in runs],
        "contagens": {
            "cartoes": len(cartoes),
            "bancadas": len(bancadas),
            "execucoes": len(runs),
            "publicados": len(quadro.get("publicado", [])),
            "a_espera_do_editor": len(quadro.get("verificado", [])) + por_rever,
        },
    }
    (DADOS / "redacao.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f'mesa: {len(cartoes)} cartões em {len(COLUNAS)} colunas, {len(bancadas)} bancadas, '
          f'{doc["contagens"]["a_espera_do_editor"]} coisas à espera do editor')


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — what each agent said about each article, derived from what was recorded.

    python3 build/comentarios.py      # after artigos.py, before build.py

THE ASK, AND THE REFUSAL IT FORCED.

The editor asked for "a visualisation and a mapping of the comments each of the different agents
made on this" — an article's folder should hold the workflow, the decisions, the comments and the
several agents' views of it.

The easy way to do that would be to WRITE the comments. They would read well: one from ChatGPT
suggesting, one from Perplexity disagreeing, one from verification confirming. And they would be
**fabricated provenance** — the one thing a site built entirely on provenance cannot do.
Attributing to another provider's model a sentence it never wrote is worse than a claim with no
source: it is a claim with a FALSE source.

So this file writes no comments. **It derives them from records that already exist**, and every
entry names, in its `de` field, the file and path it came from. A gate re-resolves that path. If a
comment cannot walk back to a file in this repository, the build fails — the same rule the claims
live under, turned on the work instead of on the world.

WHERE THEY COME FROM

  proveniencia.json  `cronologia[]`  → an action by a named agent, what it did and why it matters
                     `por_rever[]`   → an open question that agent left behind
  afirmacoes.json    `afirmacoes[]`  → each claim re-read against the bytes, and the method used
  artigo.json        `o_que_falta[]` → what the newsroom says it still does not have
  dados/entregas.json               → a proposal from an OUTSIDE assistant, with the result of
                                      searching the frozen bytes for its excerpt; and the editor's
                                      decision, or its absence, which is where almost everything is

HOW AN OUTSIDE PROPOSAL ATTACHES TO AN ARTICLE — and it is a formula, not a guess. It attaches by
SECTION: a delivery arrives for a section, and an article belongs to a section. The comment says so
in full and pretends nothing more: "this proposal arrived for the policies section, which is this
article's section". It is not a claim that the proposal is ABOUT this article — that would take
somebody reading both, and that somebody is the editor.
"""
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
ARTIGOS = ROOT / "artigos"

# The agents of this newsroom come from `dados/agentes.json`, which is the register, and not from a
# list in here. There were two lists — this one and the register — and two lists of agents would
# eventually disagree on the day somebody added a role to one and not the other. The key stays the
# `id_curto`, because that is what the comment entries on each article carry, and those are
# evidence.
def _agentes_do_registo():
    reg = carregar(DADOS / "agentes.json")
    if not reg:
        return {}
    especies = {"departamento": "departamento", "humano": "editor de registo"}
    return {
        a["id_curto"]: {
            "nome": a["nome"],
            "fornecedor": "humano" if a.get("papel") == "humano" else "esta redação",
            "especie": especies.get(a.get("papel"), a.get("papel", "departamento")),
            # The same agent's mail address, so whoever reads the comment map can go from what it
            # did to what it has in front of it.
            "id_correio": a["id"], "alias": a.get("alias"),
        }
        for a in reg.get("agentes", [])
    }

ESPECIES = {
    "acao":        "Uma coisa que um agente fez, com a hora a que a fez.",
    "pergunta":    "Uma pergunta que ficou em aberto, escrita por quem a deixou.",
    "verificacao": "Uma afirmação relida contra os bytes, e o que a releitura devolveu.",
    "falta":       "Uma coisa que a redação diz que ainda não tem.",
    "proposta":    "Uma pista de um assistente exterior, com o resultado de se ter procurado o "
                   "excerto nos bytes. Nunca um facto: uma entrega é uma lista de pistas.",
    "decisao":     "Uma decisão do editor de registo — ou a sua ausência, que também é um estado.",
}


def carregar(f):
    p = Path(f)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main():
    entregas = carregar(DADOS / "entregas.json")
    equipa = carregar(DADOS / "equipa.json")
    hoje = carregar(DADOS / "registo.json").get("atualizado", time.strftime("%Y-%m-%d"))

    # Outside assistants, read from the deliveries rather than from a hand-written list: if a
    # delivery from another tool turns up, it enters here on its own.
    agentes = _agentes_do_registo()
    for ent in entregas.get("entregas", []):
        aid = ent.get("ferramenta") or "desconhecido"
        agentes.setdefault(aid, {
            "nome": aid, "fornecedor": ent.get("modelo") or "modelo não declarado",
            "especie": "assistente exterior",
        })

    todos, por_artigo = [], {}

    for meta in sorted(ARTIGOS.rglob("artigo.json")):
        pasta = meta.parent
        rel = pasta.relative_to(ROOT).as_posix()
        art = carregar(meta)
        slug = art["slug"]
        prov = carregar(pasta / "proveniencia.json")
        afirm = carregar(pasta / "afirmacoes.json")
        fluxo = []

        def junta(**kw):
            kw["id"] = f'{slug}-c{len(fluxo) + 1:02d}'
            kw["artigo"] = slug
            fluxo.append(kw)

        # 1 · the timeline: every action by a named agent.
        for i, c in enumerate(prov.get("cronologia", [])):
            junta(quando=c.get("quando"), agente=c.get("quem", "redacao"),
                  agente_verbatim=c.get("agente"), especie="acao",
                  sobre={"tipo": "artigo", "ref": slug},
                  texto=c.get("o_que", ""), porque=c.get("porque_importa"),
                  estado="feito", de=f"{rel}/proveniencia.json#cronologia[{i}]")

        # 2 · what that agent left open. It is an open question and it stays open: a stream that
        #     closes its own questions is not a stream, it is decoration.
        for i, q in enumerate(prov.get("por_rever", [])):
            junta(quando=None, agente=(prov.get("cronologia") or [{}])[0].get("quem", "redacao"),
                  especie="pergunta", sobre={"tipo": "artigo", "ref": slug},
                  texto=q, estado="aberto", de=f"{rel}/proveniencia.json#por_rever[{i}]")

        # 3 · each claim's verification, with the method stated once.
        for i, a in enumerate(afirm.get("afirmacoes", [])):
            junta(quando=afirm.get("verificado_em"), agente=afirm.get("por", "verificacao"),
                  especie="verificacao", sobre={"tipo": "afirmacao", "ref": a.get("id")},
                  texto=a.get("texto", ""), porque=afirm.get("como"),
                  estado=a.get("estado", "por_verificar"), fonte=a.get("fonte"),
                  de=f"{rel}/afirmacoes.json#afirmacoes[{i}]")

        # 4 · what the newsroom says it still lacks.
        for i, f in enumerate(art.get("o_que_falta", [])):
            junta(quando=art.get("data"), agente="redacao", especie="falta",
                  sobre={"tipo": "artigo", "ref": slug}, texto=f, estado="aberto",
                  de=f"{rel}/artigo.json#o_que_falta[{i}]")

        # 5 · what arrived from outside for this article's section, and what happened to it.
        for ent in entregas.get("entregas", []):
            if art.get("seccao") not in (ent.get("seccoes") or []):
                continue
            for j, item in enumerate(ent.get("itens", [])):
                conf = sum(1 for c in item.get("afirmacoes", []) if c.get("estado") == "confirmada")
                tot = len(item.get("afirmacoes", []))
                junta(quando=ent.get("data"), agente=ent.get("ferramenta"),
                      agente_verbatim=ent.get("modelo"), especie="proposta",
                      sobre={"tipo": "proposta", "ref": item.get("id")},
                      texto=item.get("historia_sugerida") or item.get("titulo", ""),
                      porque=(f'Chegou para a secção «{art.get("seccao")}», que é a secção deste '
                              f'artigo. Não é uma afirmação de que seja sobre ele. '
                              f'{conf} de {tot} afirmações tinham o excerto nos bytes.'),
                      estado="por_decidir", entrega=ent.get("id"),
                      de=f'dados/entregas.json#entregas[{ent.get("id")}].itens[{j}]')
            junta(quando=ent.get("data"), agente="editor", especie="decisao",
                  sobre={"tipo": "artigo", "ref": slug},
                  texto=(f'A entrega «{ent.get("id")}» está em «{ent.get("revisao", {}).get("estado")}». '
                         f'Enquanto o editor de registo não decidir item a item, nada dela é facto '
                         f'e nada dela chega a este artigo.'),
                  estado=ent.get("revisao", {}).get("estado", "por_rever"),
                  de=f'dados/entregas.json#entregas[{ent.get("id")}].revisao')

        contagem_agente = {}
        for c in fluxo:
            contagem_agente[c["agente"]] = contagem_agente.get(c["agente"], 0) + 1

        doc = {
            "artigo": slug,
            "versao": "0.1.0",
            "atualizado": hoje,
            "derivado": True,
            "porque_existe_este_ficheiro": (
                "O que cada agente disse sobre este artigo, num sítio só. NÃO é escrito: é "
                "derivado de registos que já existem, e cada entrada diz no campo `de` de que "
                "ficheiro e de que caminho saiu. Escrever comentários seria fabricar "
                "proveniência, que é a única coisa que este sítio não pode fazer."),
            "como_se_refaz": "python3 build/comentarios.py",
            "especies": ESPECIES,
            "contagem": len(fluxo),
            "por_agente": contagem_agente,
            "abertos": sum(1 for c in fluxo if c["estado"] in ("aberto", "por_decidir", "por_rever")),
            "fluxo": fluxo,
        }
        (pasta / "comentarios.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        por_artigo[slug] = {"url": rel + "/", "titulo": art.get("titulo", slug),
                            "seccao": art.get("seccao"), "estado": art.get("estado"),
                            "contagem": len(fluxo), "abertos": doc["abertos"],
                            "por_agente": contagem_agente}
        todos.extend(fluxo)

    # --- the aggregate, which is what the console and the map read -----------
    por_agente = {}
    for c in todos:
        d = por_agente.setdefault(c["agente"], {"total": 0, "abertos": 0, "especies": {}})
        d["total"] += 1
        if c["estado"] in ("aberto", "por_decidir", "por_rever"):
            d["abertos"] += 1
        d["especies"][c["especie"]] = d["especies"].get(c["especie"], 0) + 1

    agregado = {
        "id": "pt-comentarios", "versao": "0.1.0", "atualizado": hoje,
        "nota": ("O trabalho dos agentes sobre os artigos, derivado dos registos do repositório. "
                 "Cada entrada nomeia o ficheiro de onde saiu. Nenhuma foi escrita para aqui."),
        "agentes": {k: v for k, v in agentes.items()
                    if k in por_agente or k in ("editor",)},
        "especies": ESPECIES,
        "contagem": len(todos),
        "abertos": sum(v["abertos"] for v in por_agente.values()),
        "por_agente": por_agente,
        "por_artigo": por_artigo,
        "fluxo": todos,
    }
    (DADOS / "comentarios.json").write_text(
        json.dumps(agregado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f'comentários: {len(todos)} entradas em {len(por_artigo)} artigos, '
          f'{len(por_agente)} agentes, {agregado["abertos"]} por fechar')


if __name__ == "__main__":
    main()

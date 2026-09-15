#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — what is waiting on the editor of record, as questions he can answer.

    python3 build/revisao.py    # after mesa.py, before build.py

THE ASK. The editor comes back after a day away and has to reconstruct, from six places, what
happened and what is now his to decide: the release notes, the delivery pages, the board, the mail,
the revision files, and the articles. Every one of those is honest and none of them is a briefing.

WHAT THIS FILE DOES. It gathers the open questions — and ONLY the questions whose answer is the
editor's to give — and writes them to `dados/revisao.json` as a flat list, each with the file that
answer has to end up in and the agent that will put it there. `build/build.py` renders the page;
`assets/components/pt-decisoes/` captures the answers in the browser.

WHAT IT REFUSES TO DO. It does not decide, it does not pre-fill a verdict, and it does not treat
silence as an answer. An item with no decision stays `por rever`, which is what the quarantine gate
already enforces — so the safe state and the default state are the same state, deliberately.

AND IT INVENTS NO DATES. "Since your last review" is not computed here, because this build has no
idea when the editor last read anything. What it can say is when each thing happened; which of
those the editor has already seen is knowledge that lives in his browser, and that is where the
page keeps it.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
ISSUES = ROOT / "redacao" / "issues"


def carregar(nome, omissao=None):
    f = DADOS / nome
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else omissao


def decisoes_das_entregas(entregas):
    """One question per research item the editor has not yet answered.

    An item whose claims ALL failed the byte check is still listed, and listed as its own kind of
    question: the skill forbids approving it — there is nothing to stand on — but rejecting it
    would say the newsroom does not want the lead, which is usually false. The honest third answer
    is to leave it and open research, so the question says so rather than offering two buttons that
    are both wrong.
    """
    saida = []
    for x in (entregas or {}).get("entregas", []):
        decididos = (x.get("revisao") or {}).get("itens") or {}
        for it in x["itens"]:
            if it["id"] in decididos:
                continue
            confirmadas = [a for a in it["afirmacoes"] if a["estado"] == "confirmada"]
            total = len(it["afirmacoes"])
            saida.append({
                "id": f'{x["id"]}/{it["id"]}',
                "especie": "entrega",
                "para": "a sessão /newsroom-entregas",
                "ficheiro": f'redacao/revisoes/{x["id"]}.json',
                "pergunta": it["titulo"],
                "entrega": x["id"],
                "item": it["id"],
                "seccao": it["seccao"],
                "confirmadas": len(confirmadas),
                "afirmacoes": total,
                "sem_bytes": total - len(confirmadas),
                "porque_importa": it.get("porque_importa") or "",
                "afirmacoes_confirmadas": [a["texto"] for a in confirmadas],
                "url": f'../../entregas/{x["id"]}.html#{it["id"]}',
            })
    return saida


def decisoes_dos_issues():
    """Issues the board says are blocked on a person rather than on work."""
    saida = []
    for f in sorted(ISSUES.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("estado") != "bloqueado":
            continue
        saida.append({
            "id": f'issue-{d["id"]}',
            "especie": "issue",
            "para": "quem o editor autorizar",
            "ficheiro": f"redacao/issues/{f.name}",
            "pergunta": d["titulo"],
            "seccao": d.get("seccao", "—"),
            "porque_importa": d.get("porque_esta_bloqueado") or d.get("enquadramento", ""),
            "o_que_falta": d.get("o_que_falta", []),
            "url": "../",
        })
    return saida


def decisoes_de_vocabulario(entregas):
    """Entity types a delivery proposed that the ontology does not have.

    Grouped into ONE question and not one per type, because that is how it is decided: adding a
    type is an ontology change, it takes a version, and nobody accepts three of them separately.
    """
    propostos = {}
    for x in (entregas or {}).get("entregas", []):
        for erro in x.get("erros_de_esquema", []):
            if "/type:" in erro and "is not one of" in erro:
                nome = erro.split("'")[1] if "'" in erro else erro
                propostos.setdefault(nome, set()).add(x["id"])
    if not propostos:
        return []
    return [{
        "id": "ontologia-tipos-novos",
        "especie": "ontologia",
        "para": "a sessão que mexer na ontologia",
        "ficheiro": "dados/ontologia.json",
        "pergunta": "Aceitar na ontologia os tipos de entidade que as entregas propuseram?",
        "seccao": "—",
        "porque_importa": (
            "Um tipo aceite à pressa para publicar um artigo é um tipo que fica. Nenhum dos "
            "artigos publicados até hoje precisou destes: são propostas, não bloqueios."),
        "tipos": sorted(propostos),
        "url": "../../entregas/",
    }]


def main():
    entregas = carregar("entregas.json")
    historias = carregar("historias.json", {"historias": []})
    versoes = carregar("../admin/versions.json") or json.loads(
        (ROOT / "admin" / "versions.json").read_text(encoding="utf-8"))

    decisoes = (decisoes_das_entregas(entregas)
                + decisoes_dos_issues()
                + decisoes_de_vocabulario(entregas))

    # WHAT HAPPENED. Every entry carries its own date or version so the page can say when, and the
    # browser can work out which of them this editor has already seen.
    mudancas = []
    for v in versoes["versoes"][:8]:
        mudancas.append({"especie": "versao", "quando": v["data"], "versao": v["versao"],
                         "o_que": v["titulo"], "url": f'../../admin/versions.html#{v["versao"]}'})
    for h in historias["historias"]:
        if h["estado"] == "publicado":
            mudancas.append({"especie": "artigo", "quando": h.get("publicado_em") or h["data"],
                             "versao": "", "o_que": h["titulo"], "url": f'../../{h["url"]}'})
    for x in (entregas or {}).get("entregas", []):
        c = x["contagens"]
        mudancas.append({
            "especie": "entrega", "quando": x["data"], "versao": "",
            "o_que": (f'Entrega {x["ferramenta"]} · {c["itens"]} itens, '
                      f'{c["confirmadas"]} de {c["afirmacoes"]} afirmações nos bytes'),
            "url": f'../../entregas/{x["id"]}.html'})
    mudancas.sort(key=lambda m: (m["quando"], m["versao"]), reverse=True)

    doc = {
        "id": "pt-revisao",
        "versao": "1.0.0",
        "atualizado": max([m["quando"] for m in mudancas] or ["—"]),
        "o_que_e": (
            "As perguntas cuja resposta é do editor de registo, e o que mudou desde que as "
            "outras foram respondidas. Nada aqui decide nada: uma decisão é um ficheiro no "
            "repositório, escrito por uma pessoa, e esta página só ajuda a escrevê-lo."),
        "a_regra": (
            "Um item sem veredicto fica por rever, que é o estado seguro e o que o portão 13 "
            "já obriga. O silêncio nunca é um sim."),
        "contagem": len(decisoes),
        "decisoes": decisoes,
        "mudancas": mudancas,
    }
    (DADOS / "revisao.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    por_especie = {}
    for x in decisoes:
        por_especie[x["especie"]] = por_especie.get(x["especie"], 0) + 1
    print(f'revisão: {len(decisoes)} perguntas para o editor '
          f'({", ".join(f"{v} {k}" for k, v in sorted(por_especie.items())) or "nenhuma"}), '
          f'{len(mudancas)} mudanças listadas')


if __name__ == "__main__":
    main()

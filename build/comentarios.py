#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — o que cada agente disse sobre cada artigo, derivado do que ficou escrito.

    python3 build/comentarios.py      # depois de artigos.py, antes de build.py

O PEDIDO E A RECUSA QUE ELE OBRIGOU A FAZER.

O editor pediu «uma visualização e um mapeamento dos comentários que cada um dos diferentes agentes
fez a isto» — a pasta de um artigo deve conter o fluxo de trabalho, as decisões, os comentários e
as vistas dos vários agentes sobre ele.

A maneira fácil de fazer isto seria escrever comentários. Ficariam bem: um do ChatGPT a sugerir,
outro da Perplexity a discordar, um da verificação a confirmar. E seriam **proveniência
fabricada** — a única coisa que um sítio inteiro construído sobre proveniência não pode fazer.
Atribuir a um modelo de outro fornecedor uma frase que ele nunca escreveu é pior do que uma
afirmação sem fonte: é uma afirmação com uma fonte falsa.

Por isso este ficheiro não escreve comentários. **Deriva-os de registos que já existem**, e cada
comentário nomeia, no campo `de`, o ficheiro e o caminho de onde saiu. Um portão volta a resolver
esse caminho. Se um comentário não andar para trás até um ficheiro do repositório, a construção
falha — é a mesma regra das afirmações, aplicada ao trabalho em vez de ao mundo.

DE ONDE SAEM

  proveniencia.json  `cronologia[]`  → uma ação de um agente nomeado, com o que fez e porque importa
                     `por_rever[]`   → uma pergunta em aberto que aquele agente deixou
  afirmacoes.json    `afirmacoes[]`  → a verificação de cada afirmação contra os bytes, e o método
  artigo.json        `o_que_falta[]` → o que a redação diz que ainda não tem
  dados/entregas.json               → uma proposta de um assistente EXTERIOR, com o resultado de se
                                      ter procurado o excerto nos bytes; e a decisão do editor, ou
                                      a sua ausência, que é o estado em que quase tudo está

COMO UMA PROPOSTA EXTERIOR SE LIGA A UM ARTIGO — e é uma fórmula, não um palpite. Liga-se pela
SECÇÃO: uma entrega chega para uma secção e um artigo pertence a uma secção. O comentário diz isso
por extenso e não finge mais: «esta proposta chegou para a secção das políticas, que é a secção
deste artigo». Não é uma afirmação de que a proposta seja sobre este artigo — para isso seria
preciso alguém ler as duas coisas, e esse alguém é o editor.
"""
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
ARTIGOS = ROOT / "artigos"

# Os agentes, como este repositório os conhece. Um departamento é um agente com um âmbito de
# escrita; o editor é uma pessoa nomeada; um assistente exterior é uma ferramenta e um modelo,
# escritos tal como a entrega os declarou.
AGENTES = {
    "pesquisa":    {"nome": "Pesquisa", "fornecedor": "esta redação", "especie": "departamento"},
    "redacao":     {"nome": "Redação", "fornecedor": "esta redação", "especie": "departamento"},
    "verificacao": {"nome": "Verificação", "fornecedor": "esta redação", "especie": "departamento"},
    "editor":      {"nome": "Dinis Cruz", "fornecedor": "humano", "especie": "editor de registo"},
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

    # Os assistentes exteriores, lidos das entregas e não de uma lista escrita à mão: se aparecer
    # uma entrega de outra ferramenta, ela entra aqui sozinha.
    agentes = dict(AGENTES)
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

        # 1 · a cronologia: cada ação de um agente nomeado.
        for i, c in enumerate(prov.get("cronologia", [])):
            junta(quando=c.get("quando"), agente=c.get("quem", "redacao"),
                  agente_verbatim=c.get("agente"), especie="acao",
                  sobre={"tipo": "artigo", "ref": slug},
                  texto=c.get("o_que", ""), porque=c.get("porque_importa"),
                  estado="feito", de=f"{rel}/proveniencia.json#cronologia[{i}]")

        # 2 · o que aquele agente deixou por rever. É uma pergunta em aberto e fica aberta: um
        #     fluxo que fecha as suas próprias perguntas não é um fluxo, é uma decoração.
        for i, q in enumerate(prov.get("por_rever", [])):
            junta(quando=None, agente=(prov.get("cronologia") or [{}])[0].get("quem", "redacao"),
                  especie="pergunta", sobre={"tipo": "artigo", "ref": slug},
                  texto=q, estado="aberto", de=f"{rel}/proveniencia.json#por_rever[{i}]")

        # 3 · a verificação de cada afirmação, com o método declarado uma vez.
        for i, a in enumerate(afirm.get("afirmacoes", [])):
            junta(quando=afirm.get("verificado_em"), agente=afirm.get("por", "verificacao"),
                  especie="verificacao", sobre={"tipo": "afirmacao", "ref": a.get("id")},
                  texto=a.get("texto", ""), porque=afirm.get("como"),
                  estado=a.get("estado", "por_verificar"), fonte=a.get("fonte"),
                  de=f"{rel}/afirmacoes.json#afirmacoes[{i}]")

        # 4 · o que a redação diz que ainda lhe falta.
        for i, f in enumerate(art.get("o_que_falta", [])):
            junta(quando=art.get("data"), agente="redacao", especie="falta",
                  sobre={"tipo": "artigo", "ref": slug}, texto=f, estado="aberto",
                  de=f"{rel}/artigo.json#o_que_falta[{i}]")

        # 5 · o que chegou de fora para a secção deste artigo, e o que aconteceu quando voltou.
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

    # --- o agregado, que é o que a consola e a visualização leem -------------
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

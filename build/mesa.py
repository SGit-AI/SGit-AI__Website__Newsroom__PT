#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — a mesa como um sítio e não como uma tabela.

    python3 build/mesa.py       # depois de comentarios.py, antes de build.py

O PEDIDO. O editor apontou para a redação virtual de newsroom.sgit.ai — *«uma redação virtual com
representações visuais dos artigos, com quadros Kanban, quase uma mesa de notícias visual»* — e
disse que `/redacao/` daqui é uma tabela e aquilo é uma sala.

A diferença entre as duas não é decoração. Uma tabela mostra linhas; uma sala mostra **carga**:
quem tem o quê em cima da mesa agora, o que está parado à espera de quem, e onde está o próximo
gesto. São perguntas diferentes e a segunda é a que se faz a uma redação às cinco da tarde.

O QUE ESTE FICHEIRO FAZ. Junta num só documento o que já está espalhado — as bancadas e o que cada
uma pode escrever (`dados/equipa.json`), o quadro (`redacao/issues/`), o correio
(`redacao/correio/`), as execuções (`redacao/runs/`) e o trabalho por agente
(`dados/comentarios.json`) — e conta a carga de cada bancada a partir disso. Não inventa estado
nenhum: cada número aqui é uma contagem de ficheiros ou de entradas que já existem.

E NÃO FAZ UMA COISA. Não move nada. A mesa mostra onde as coisas estão; quem as move é quem tem
direito de escrita naquela pasta, e o passo que ninguém automático pode dar — pôr uma história em
«publicado» — continua a ser do editor de registo, e a sala di-lo na coluna onde ele estaria.
"""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
REDACAO = ROOT / "redacao"

# As colunas do quadro, pela ordem em que uma história as atravessa. `quem_move` não é decorativo:
# é a regra de quem pode empurrar um cartão para ali, e a última é a razão de existir um humano.
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

    # --- o quadro: cada issue e cada artigo, na coluna em que está ------------
    issues = [carregar(f) for f in sorted((REDACAO / "issues").glob("*.json"))] \
        if (REDACAO / "issues").exists() else []
    # UM ISSUE PODE DAR MAIS DO QUE UM ARTIGO, e neste repositório já dá: o issue 001 encomendou
    # a história do instrumento legal da agenda, e da mesma encomenda saiu também a história de o
    # registo nacional não devolver texto. A primeira versão desta função assumiu um artigo por
    # issue, casou o issue com o primeiro que encontrou e **deixou o outro fora do quadro** — um
    # quadro que esconde trabalho é pior do que não haver quadro, porque parece completo.
    #
    # Por isso o cartão é o ARTIGO, que é a coisa que tem ficheiros e um estado verdadeiro, e o
    # issue só ganha cartão próprio quando ainda não produziu nenhum.
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

    # --- o correio, contado por bancada --------------------------------------
    # Contado de `dados/correio.json` e não da pasta. A pasta `redacao/correio/` tem UM leitor, o
    # `build/equipa.py`, que lê os `.eml` e deriva o estado de cada mensagem da pasta onde ela está.
    # Contar aqui a pasta outra vez seria um segundo leitor da mesma coisa — e seria o segundo
    # leitor a ficar desatualizado, como este ficou quando o correio passou a `.eml` e as caixas
    # passaram a ter o endereço do protocolo («pesquisa.pt») em vez do nome curto («pesquisa»).
    corr = carregar(DADOS / "correio.json")
    registo_agentes = carregar(DADOS / "agentes.json")
    # `id_curto` -> `id`, do registo, que é onde a correspondência entre os dois identificadores
    # vive. Sem ela, uma bancada chamada «pesquisa» não encontra a caixa «pesquisa.pt».
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

    # --- as execuções --------------------------------------------------------
    runs = [carregar(f) for f in sorted((REDACAO / "runs").glob("*.json"))] \
        if (REDACAO / "runs").exists() else []

    # --- as bancadas ---------------------------------------------------------
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

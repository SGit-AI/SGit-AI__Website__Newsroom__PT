#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — llms.txt, sitemap.xml, index.md and the versions table.

    python3 build/chrome.py

The page shell is made in `build/paginas.py` and applied by `build/build.py`; what is left is the
surface a machine reads, and that is what this file writes.

Why `llms.txt` is not an extra. §8 of the brief says one provider's assistant can only fetch
addresses that have already appeared in the conversation, and explicitly not addresses that
appeared only in its own output, and is not documented as following links inside a page it fetched.
The practical consequence is a design decision rather than a preference: **a single concatenated,
machine-readable file, and constructible addresses for everything.** That is what this file
produces.
"""
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
HOST = "pt.newsroom.sgit.ai"
VERSAO = (ROOT / "admin" / "build" / "version.txt").read_text(encoding="utf-8").strip()


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def paginas():
    return sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*.html")
                  if "fontes/congeladas/" not in p.as_posix()
                  and "/briefs/" not in p.as_posix()
                  and "/node_modules/" not in p.as_posix())


def main():
    reg, graf = carregar("registo.json"), carregar("grafo.json")
    pes, org = carregar("pessoas.json"), carregar("organizacoes.json")
    ses, ent = carregar("sessoes.json"), carregar("entregas.json")
    hoje = reg.get("atualizado", time.strftime("%Y-%m-%d"))
    todas = paginas()

    n_afirm = sum(x["contagens"]["afirmacoes"] for x in ent.get("entregas", []))
    n_conf = sum(x["contagens"]["confirmadas"] for x in ent.get("entregas", []))
    hist = carregar("historias.json")
    lista_artigos = "\n" + "\n".join(
        f'- https://{HOST}/{h["url"]} — {h["titulo"]} ({h["estado"]})'
        for h in hist.get("historias", [])) if hist.get("historias") else ""

    # ------------------------------------------------------------- llms.txt ---
    llms = f"""# pt.newsroom.sgit.ai

> Uma redação nativamente portuguesa que mapeia o ecossistema português de inteligência
> artificial como um grafo. Cada afirmação anda para trás até uma cópia congelada e hasheada da
> fonte de onde veio. Editor de registo: Dinis Cruz, que lê cada página antes de publicar.

Versão {VERSAO} · atualizado {hoje} · licença CC BY 4.0 · fonte:
https://github.com/SGit-AI/SGit-AI__Website__Newsroom__PT

O ecossistema português de IA é pequeno o suficiente para ser mapeado por completo e grande o
suficiente para ser interessante.

## O que é real hoje, em números que vêm de ficheiros

- {reg.get("contagem", 0)} ficheiros congelados de {len(reg.get("capturas", []))} captura(s), cada um com SHA-256, todos reverificados em cada construção
- {graf.get("contagens", {}).get("nos", 0)} nós e {graf.get("contagens", {}).get("arestas", 0)} arestas; cada aresta é um verbo português com um inverso distinto
- {pes.get("contagem", 0)} pessoas e {org.get("contagem", 0)} organizações, derivadas das fontes, nunca escritas à mão
- {ses.get("contagem", 0)} sessões lidas do recuo estático da agenda congelada
- {n_afirm} afirmações entregues por assistentes exteriores; {n_conf} com o excerto encontrado nos bytes; 0 publicadas

## O que NÃO é real, dito aqui e em cada página onde importa

- Nenhuma história está publicada. As três primeiras estão como issues em estado «procurado».
- Três das oito secções não têm um único nó, porque nenhuma fonte congelada as alimenta.
- A camada das empresas não pode ser completa: não há registo comercial aberto em Portugal.
- Nada de uma entrega de investigação é facto enquanto o editor de registo não a aprovar.

## Os concentradores

"""
    HUBS = [
        ("/", "A primeira página. O desenho escolhido pelo editor a 13 de setembro de 2026."),
        ("/artigos/", "Os artigos, por data. Cada um é uma pasta com a prosa, a verificação de "
                      "cada afirmação e a proveniência."),
        ("/entidades/", "Uma página por nó do grafo que é uma coisa do mundo: pessoa, organização, "
                        "instituição, editor, tema, lugar. Cada página é a lista das frases em que "
                        "a entidade entra, mais a contagem de onde o seu nome aparece nos bytes "
                        "congelados. Nenhuma linha escrita sobre ninguém."),
        ("/api/", "A API só de leitura, e uma consola que a invoca. Cada caminho é um ficheiro: "
                  "não há servidor, e por isso não há verbo que não seja GET. Os caminhos são em "
                  "INGLÊS de propósito — a intenção é várias línguas sobre um só conjunto de dados."),
        ("/proveniencia/", "Quem escreve este site: agentes de IA, de vários fornecedores, com "
                           "curadoria de um editor humano nomeado. Contado a partir dos ficheiros "
                           "de proveniência de cada artigo."),
        ("/backoffice/", "A consola de operações. EM INGLÊS: o seu público é quem opera a redação, "
                         "não quem lê o jornal. Não publica nenhuma afirmação sobre Portugal."),
        ("/registo/", "O registo: cada ficheiro congelado, com URL, bytes, SHA-256 e hora de obtenção."),
        ("/grafo/", "A ontologia e o grafo. Verbos portugueses, cada um com leitura e inverso."),
        ("/carteira/", "A carteira: cada página custa um cêntimo a abrir, e o registo do gasto "
                       "está numa página em vez de num painel. Não cobra nada a ninguém — o saldo "
                       "vive no navegador de quem lê."),
        ("/ficheiros/", "O manifesto: cada ficheiro de dados com o seu SHA-256."),
        ("/metodo/", "Obter, congelar, hashear, extrair, comparar — e onde cada recusa corre."),
        ("/equipa/", "Três departamentos, o editor de registo, e o que não está construído."),
        ("/aviso/", "O aviso de proteção de dados. Interesses legítimos; remoção incondicional."),
        ("/sobre/", "O que é real, o que não é, e os limites."),
        ("/redacao/", "A mesa: o quadro de issues, o correio entre departamentos, as execuções."),
        ("/entregas/", "As entregas de investigação e o seu fluxo de revisão."),
        ("/empresas/", "As empresas."), ("/protagonistas/", "Os protagonistas."),
        ("/instituicoes/", "As instituições."), ("/politicas/", "As políticas."),
        ("/casos-de-uso/", "Os casos de uso."), ("/codigo-aberto/", "O código aberto (vazia)."),
        ("/diaspora/", "A diáspora (vazia)."), ("/eventos/", "Os eventos."),
    ]
    # The full path, with `index.html`, and not the short form with a trailing slash. Two reasons,
    # and the second is the one that matters: the validator's fourth check requires every hub to be
    # named here by file path, because "for an agent, a page llms.txt does not name does not
    # exist"; and §8 of the brief says one provider's assistant does not follow links inside a page
    # it fetched, so the address has to be written out in full.
    for caminho, desc in HUBS:
        rel = "index.html" if caminho == "/" else caminho.strip("/") + "/index.html"
        if rel in todas:
            llms += f"- [{caminho}](https://{HOST}/{rel}): {desc}\n"

    llms += f"""
## Os dados, em endereços construíveis

Todos os ficheiros abaixo são JSON, exceto onde indicado, e todos são servidos tal como estão.

- https://{HOST}/dados/registo.json — o registo das fontes congeladas, com hashes
- https://{HOST}/dados/grafo.json — os nós e as arestas
- https://{HOST}/dados/ontologia.json — os tipos, os verbos, as leituras, os proibidos
- https://{HOST}/dados/triplos.nt — o grafo em N-Triples, com owl:inverseOf declarado
- https://{HOST}/dados/manifesto.json — cada ficheiro de dados com o seu SHA-256
- https://{HOST}/dados/pessoas.json — pessoas, sem biografias e sem contactos
- https://{HOST}/dados/organizacoes.json — organizações derivadas dos cartões
- https://{HOST}/dados/sessoes.json — o programa, lido da agenda congelada
- https://{HOST}/dados/temas.json — temas verbatim e etiquetas derivadas pelo léxico
- https://{HOST}/dados/lexico.json — a fórmula publicada que produz as etiquetas
- https://{HOST}/dados/mudancas.json — o que mexeu entre capturas
- https://{HOST}/dados/entregas.json — as entregas e o estado de cada afirmação
- https://{HOST}/dados/aviso.json — o aviso de proteção de dados, como dados
- https://{HOST}/dados/equipa.json — os departamentos e o editor de registo
- https://{HOST}/dados/excluidas.json — as fontes que foram tentadas e não resolveram
- https://{HOST}/dados/historias.json — o índice dos artigos, derivado das pastas datadas
- https://{HOST}/dados/documentos.json — todos os documentos markdown deste repositório
- https://{HOST}/dados/entidades.json — cada entidade, onde o seu nome está nos bytes, e a fórmula de ligação
- https://{HOST}/dados/comentarios.json — o trabalho dos agentes sobre os artigos, derivado dos registos
- https://{HOST}/dados/redacao.json — a mesa: as bancadas, a carga de cada uma, e o quadro
- https://{HOST}/dados/agentes.json — os agentes nomeados que podem mudar este site, e o mandato de cada um
- https://{HOST}/dados/transferencias.json — prova congelada por OUTRA publicação, com a proveniência dela

## As entidades, em endereços construíveis

Uma entidade é um nó do grafo que é uma coisa do mundo, e o caminho sai do tipo e do id do nó:

    https://{HOST}/entidades/<tipo>/<id>/          a página
    https://{HOST}/api/v1/entities/<tipo>-<id>.json      a mesma coisa em JSON

Os tipos com página: pessoa, organizacao, instituicao, editor, evento, local, palco, tema,
tecnologia, setor, produto, servico, ideia. Uma página de entidade não tem uma linha escrita
sobre ela: tem os campos verbatim da fonte, as arestas lidas em voz alta pela leitura publicada
na ontologia, e a contagem de onde o nome aparece em cada cópia congelada.

## Os artigos, em endereços construíveis

Um artigo é uma pasta datada, e o caminho é previsível a partir da data e do slug:

    https://{HOST}/artigos/<aaaa>/<mm>/<dd>/<slug>/            a página
    https://{HOST}/artigos/<aaaa>/<mm>/<dd>/<slug>/artigo.json       estado, secção, fontes
    https://{HOST}/artigos/<aaaa>/<mm>/<dd>/<slug>/artigo.md         a prosa
    https://{HOST}/artigos/<aaaa>/<mm>/<dd>/<slug>/afirmacoes.json   cada afirmação e o seu estado
    https://{HOST}/artigos/<aaaa>/<mm>/<dd>/<slug>/proveniencia.json que agente, quando, porquê
    https://{HOST}/artigos/<aaaa>/<mm>/<dd>/<slug>/comentarios.json quem disse o quê, e de onde saiu

A data no caminho é a data do MATERIAL, não a da publicação. `publicado_em` é um campo separado,
escrito pelo editor de registo, e é a única coisa que põe um artigo na primeira página.
{lista_artigos}

## Como ler este site sem o interpretar mal

1. Uma afirmação sem fonte congelada não é uma afirmação deste site. Confirme no registo.
2. Um alvo não é um resultado. O evento declara «150+ speakers»; este site conta cartões.
3. Uma etiqueta diz que a página contém aquelas palavras. Não é uma caracterização de ninguém.
4. Um nome que sai de uma lista é registado como isso e mais nada. A razão fica em branco.
5. Uma entrega de investigação é uma lista de pistas. Veja o estado de cada afirmação em /entregas/.
6. Nenhum comentário de agente foi escrito para ser lido: todos são derivados de ficheiros que já
   existem, e cada um diz de qual no campo `de`. Um comentário atribuído a um modelo que nunca o
   escreveu seria uma afirmação com uma fonte falsa, e o portão 25 falha a construção se um
   `de` não resolver.
"""
    (ROOT / "llms.txt").write_text(llms, encoding="utf-8")

    # ------------------------------------------------------------ sitemap ---
    urls = "".join(
        f"  <url><loc>https://{HOST}/{p}</loc><lastmod>{hoje}</lastmod></url>\n" for p in todas)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n", encoding="utf-8")

    # ------------------------------------------------------------ index.md ---
    (ROOT / "index.md").write_text(f"""# pt.newsroom.sgit.ai

Versão {VERSAO}, atualizado {hoje}.

Uma redação nativamente portuguesa que mapeia o ecossistema português de IA como um grafo. Não é
uma tradução de nada: os verbos do grafo são portugueses e o inglês é a anotação.

O índice legível por máquina está em [/llms.txt](https://{HOST}/llms.txt) e é o ficheiro a obter
se for um agente. O registo das fontes está em [/registo/](https://{HOST}/registo/), e cada
ficheiro de dados com o seu SHA-256 em [/ficheiros/](https://{HOST}/ficheiros/).

Editor de registo: Dinis Cruz. Base de licitude: interesses legítimos; a derrogação jornalística
não é invocada. Remoção incondicional a pedido, sem razão exigida —
[o aviso](https://{HOST}/aviso/).
""", encoding="utf-8")

    print(f"chrome: llms.txt ({len([l for l in llms.split(chr(10)) if l.startswith('- [/')])} "
          f"concentradores), sitemap.xml ({len(todas)} páginas), index.md, {VERSAO}")


if __name__ == "__main__":
    main()

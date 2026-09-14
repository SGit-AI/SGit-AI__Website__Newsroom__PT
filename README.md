# pt.newsroom.sgit.ai

Uma redação **nativamente portuguesa** que mapeia o ecossistema português de inteligência
artificial como um grafo, publicada como site estático em
[pt.newsroom.sgit.ai](https://pt.newsroom.sgit.ai/).

> O ecossistema português de IA é pequeno o suficiente para ser mapeado por completo e grande o
> suficiente para ser interessante.

Não é uma tradução de nada. Os verbos do grafo são portugueses e o inglês é a anotação — e não o
contrário, que é a forma mais provável de um site assim estar discretamente errado, porque nada
nele parece avariado.

**Editor de registo: Dinis Cruz**, que lê cada página antes de publicar e é o responsável pelo
tratamento nomeado no [aviso de proteção de dados](https://pt.newsroom.sgit.ai/aviso/). Nenhuma
revisão jurídica foi feita e nada neste repositório é aconselhamento jurídico.

## A regra

Cada afirmação anda para trás até uma cópia congelada e hasheada da fonte de onde veio. Uma
afirmação sem fonte congelada não é uma afirmação deste site.

```
obter → congelar → hashear → extrair → comparar
fontes/congeladas/<data>/<pagina>.snapshot     + SHA-256 em dados/registo.json
```

As cópias congeladas têm a extensão `.snapshot` e não são páginas deste site: são bytes de páginas
de outras pessoas, guardados como prova. Publicar um espelho navegável do site de outra organização
sob este domínio contradiria a única regra que esta publicação tem, que é ligar em vez de
reproduzir.

## Construir

```bash
python3 build/extract.py --fetch    # obter, congelar, hashear, registar, extrair, comparar
python3 build/entregas.py --fetch   # congelar as fontes das entregas e conferir cada excerto
python3 build/graph.py              # ontologia, grafo, triplos, manifesto
python3 build/build.py              # cada página, a partir de dados/ e conteudo/
python3 build/chrome.py             # llms.txt, sitemap.xml, index.md
python3 build/gates.py              # os portões da secção — tem de imprimir OK
node admin/build/validate.js        # o portão do site — tem de imprimir OK
```

Sem `--fetch`, `extract.py` e `entregas.py` voltam a correr contra as cópias já congeladas e não
tocam na rede. É assim que se reconstrói o site a partir de um clone, anos depois, e se obtém
exatamente as mesmas páginas.

## Os portões

Um portão que falha é respondido, nunca silenciado. Quinze correm em `build/gates.py`, e cinco são
deste site:

| # | O que falha a construção |
|---|---|
| 1 | Uma cópia congelada que já não hasheia para o SHA-256 registado |
| 4 | Um alvo relatado como resultado («150+ oradores» é um plano) |
| 5 | Um contacto de pessoa singular em qualquer ficheiro de dados |
| 6 | Um campo longo o suficiente para ser uma biografia reproduzida |
| 7 | Uma razão dada, ou implicada, para um nome ter saído de uma lista |
| 8 | Uma etiqueta derivada que já não corresponde aos bytes, ou que foi escrita à mão |
| **9** | **Um nome cujos acentos não vêm da fonte congelada** — este site inverte a regra ASCII do corpus |
| **10** | **Uma leitura de aresta que não é uma frase portuguesa**, ou que concorda um particípio com uma pessoa cujo género a fonte não publica |
| **11** | **Uma história posta em «publicado» por quem não é o editor de registo** |
| **12** | **Uma execução que escreveu fora da pasta do seu departamento** |
| **13** | **Conteúdo de uma entrega de investigação numa página de leitura antes de o editor o aprovar** |

Os cinco foram testados por injeção: estragou-se cada um deliberadamente e confirmou-se que a
construção para. O portão 9 falhou o seu primeiro teste — só conferia nomes que ainda tinham
acentos, portanto um nome a que alguém tirasse o acento passava — e o comentário no código diz
isso, para que não volte.

## As entregas de investigação

Um assistente exterior recebe um dos resumos em `briefs/pack/08__research-briefs/` e devolve JSON
com proveniência. **Uma entrega é uma lista de pistas, nunca factos.** O que acontece a seguir:

1. **Validar** contra o esquema publicado. Inválida, o ficheiro fica — faz parte do registo.
2. **Congelar** cada endereço que a entrega nomeia, com SHA-256. Um endereço não é prova.
3. **Conferir o excerto**: o texto que o assistente diz ter lido é procurado nos bytes congelados.
4. **Rever**: o editor lê cada afirmação ao lado da sua fonte e aprova ou rejeita, em
   `redacao/revisoes/`. É a única transição que uma execução automática não pode fazer.

Nada disto aparece na primeira página ou num artigo sem o passo 4, e o portão 13 falha a
construção se aparecer. O estado de cada afirmação está à vista em
[/entregas/](https://pt.newsroom.sgit.ai/entregas/).

## Ler o registo oficial

O Diário da República renderiza por script: obtido por HTTP devolve 2 346 bytes e 22 caracteres
visíveis. Mas publica os diplomas em PDF — cifrados com o manipulador de segurança padrão e com
tipos subconjuntados, o que faz uma biblioteca genérica devolver zero caracteres, em silêncio.
`build/pdf.py` decifra-os e lê o mapa `/ToUnicode` de cada tipo.

A distinção importa mais do que parece: um zero devolvido por uma limitação do leitor é
indistinguível, no ficheiro de resultados, de um zero devolvido por uma página vazia, e essa
confusão faria esta redação publicar «não se consegue ler o registo nacional» quando a verdade
seria «não implementámos o decifrador».

## A redação

Três departamentos, e cada um só escreve na sua própria pasta:

| Departamento | Escreve em | Faz |
|---|---|---|
| **Pesquisa** | `fontes/congeladas/`, `dados/` | Encontra a fonte primária, congela, hasheia, regista, compara |
| **Redação** | `conteudo/` | Escreve a partir do que a pesquisa registou, e de mais nada |
| **Verificação** | `dados/verificacoes/` | Relê cada fonte citada; marca cada afirmação |
| **Editor de registo** | `redacao/decisoes/`, `redacao/revisoes/`, a linha `estado: publicado` | Lê antes de publicar. Decide remoções |

Publicação não é um departamento: é um passo de construção. O arquivo é o git. A mesa está em
[/redacao/](https://pt.newsroom.sgit.ai/redacao/), e nada nela é desenhado à mão — o quadro são os
ficheiros em `redacao/issues/`, o correio os ficheiros em `redacao/correio/`.

## Lançar

O ramo de lançamento é **`dev`**, que é também o ramo por omissão deste repositório. O pacote de
comissionamento exige que o ramo de lançamento SEJA o ramo por omissão, porque uma execução
agendada clona o ramo por omissão; chama-lhe `main` apenas por ter sido escrito antes de este
repositório existir.

Cada empurrão para `dev` é uma versão menor: incrementar `admin/build/version.txt`, acrescentar a
linha em `admin/versions.html`, e o assunto do commit repete o número (`site vX.Y.Z: …`). A
integração contínua corre os dois portões, etiqueta e publica. Uma validação vermelha não é
lançamento.

## Proveniência

Construído a partir do pacote de comissionamento em `briefs/pack/`, cortado de
[newsroom.sgit.ai](https://newsroom.sgit.ai) v0.3.9. O caminho de ingestão, os portões, a postura
sobre biografias e o aviso vêm de
[/portugal/](https://newsroom.sgit.ai/portugal/index.html), que os corre desde setembro de 2026.
O que este site acrescenta é a língua, um país como matéria em vez de um evento, e o fluxo de
revisão das entregas.

O resumo de comissionamento vive no site-pai e não aqui, porque conteúdo existe uma vez: se o
mesmo parágrafo estivesse nos dois sítios, os dois acabariam por discordar.

Licença: CC BY 4.0 para o conteúdo; ver [LICENSES.md](LICENSES.md) para as faces e as bibliotecas.

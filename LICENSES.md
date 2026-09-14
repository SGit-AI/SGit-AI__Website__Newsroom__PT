# Licenças

## O conteúdo deste site

As páginas, os ficheiros de dados em `dados/` e o código em `build/` são publicados sob a
**Creative Commons Attribution 4.0 International (CC BY 4.0)**, exceto onde indicado abaixo.

## O que NÃO é nosso e não é relicenciado

**As cópias congeladas em `fontes/congeladas/`.** São bytes de páginas publicadas por outras
organizações, guardados sem alteração como prova de que uma afirmação deste site assenta em
alguma coisa. Não são relicenciadas, não são republicadas como páginas, e a extensão `.snapshot`
existe precisamente para que não possam ser servidas nem indexadas como conteúdo deste domínio.
Cada uma está listada em [/registo/](https://pt.newsroom.sgit.ai/registo/) com o seu endereço
original, o publicador, os bytes e o SHA-256 — que é a forma de as verificar sem as reproduzir.

**As entregas de investigação em `redacao/entregas/`.** São o resultado devolvido por assistentes
exteriores, guardado tal como chegou porque faz parte do registo. Não foram corrigidas: uma
entrega corrigida em silêncio deixaria de ser prova de nada.

## As faces

Ambas sob a **SIL Open Font License 1.1**, alojadas em `assets/fonts/` e nunca obtidas em tempo de
execução — uma página que precisa de um terceiro para renderizar é uma página que um terceiro pode
deixar de renderizar.

| Face | Ficheiros | Autoria |
|---|---|---|
| Newsreader | `newsreader-variable.woff2`, `newsreader-400-italic.woff2` | Production Type |
| IBM Plex Mono | `plex-mono-400.woff2`, `plex-mono-500.woff2` | IBM / Bold Monday |

O subconjunto latino inclui `U+0000-00FF`, que é onde vivem os acentos portugueses. Uma face
servida sem eles seria uma falha silenciosa: só as palavras acentuadas renderizariam na face de
recurso.

## As bibliotecas

| Biblioteca | Ficheiro | Licença | Para quê |
|---|---|---|---|
| Cytoscape.js | `assets/vendor/cytoscape.min.js` | MIT | O visualizador do grafo |

Alojada aqui pela mesma razão que as faces. As dependências de construção (`jsonschema`,
`pycryptodome` para os PDFs cifrados do Diário da República) não são distribuídas com o site: são
instaladas por quem constrói, e o `SessionStart` em `.claude/settings.json` fá-lo.

## O pacote em `briefs/pack/`

O pacote de comissionamento, cortado de newsroom.sgit.ai v0.3.9, sob **CC BY 4.0**. Os ficheiros
de código que contém são cópias verbatim do repositório
[SGit-AI/SGit-AI__Website__Newsroom](https://github.com/SGit-AI/SGit-AI__Website__Newsroom) nessa
versão. Onde uma cópia e o original discordarem, o original está certo: o pacote foi cortado uma
vez e não acompanha o que veio depois.

## Uma nota sobre os dados pessoais

A licença de conteúdo **não é** uma licença para tratar os dados pessoais que este site publica.
O que é detido sobre pessoas nomeadas, com que fundamento, e como pedir a remoção — incondicional,
sem razão exigida — está no [aviso de proteção de dados](https://pt.newsroom.sgit.ai/aviso/).
Reutilizar este conteúdo não transfere esse fundamento: quem o reutiliza passa a ser responsável
pelo seu próprio tratamento.

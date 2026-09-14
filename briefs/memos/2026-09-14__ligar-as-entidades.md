# Ligar as entidades — o registo de uma peça de trabalho

**Data:** 14 de setembro de 2026 · **Versão:** v0.4.0 · **Agente:** Claude (Anthropic), sessão de
construção · **Editor de registo:** Dinis Cruz

Este documento existe porque o editor pediu que cada peça grande de trabalho deixasse um registo:
*«every time actually you do one of these pieces of work, you probably want to create a document
that captures this big piece of work»*. Não é um artigo — não assenta em fontes congeladas e não
afirma nada sobre Portugal. É o que foi construído, porquê, e o que ficou por fazer.

O pedido a que responde é o §2 do memo anterior,
[`2026-09-14__o-ecossistema-portugues-de-ia.md`](2026-09-14__o-ecossistema-portugues-de-ia.md),
onde ficou registado como o maior item por construir:

> *even if I'm here and I'm talking about the Comissão Europeia, well, that should be a link… to
> that dictionary definition of that entity… if I click on that, I then will be able to go into the
> page that shows me all the Diário da República happening. And again, this should be dynamic
> because it should be loading the graph dynamically.*

## 1. O que existe agora

Uma página por nó do grafo que é uma coisa do mundo, em `entidades/<tipo>/<id>/`. São 198: 70
pessoas, 67 organizações, 12 editores e instituições, 23 temas, e o resto entre tecnologias,
setores, serviços, ideias, palcos, o evento e o local. O índice está em `/entidades/` e em
`dados/entidades.json`, e cada uma tem o seu JSON em `api/v1/entities/`.

Uma página de entidade **não tem uma linha escrita sobre ela**. Tem três coisas:

1. **Os campos verbatim da fonte.** Para uma Pessoa são o nome, o papel LISTADO e a organização
   LISTADA — a palavra «listado» faz trabalho: um cartão de orador não afirma um vínculo laboral.
2. **As arestas lidas em voz alta.** «Paulo Andrez fala em Startup Summit Lisbon 2026», «o evento
   lista Paulo Andrez sob Zero Risk Startup». Nenhuma destas frases está escrita no código que
   gera a página: cada aresta da ontologia traz uma `leitura` com `{s}` e `{t}`, e a página
   substitui. É o §6 do resumo a pagar-se — foi por isto que valeu a pena recusar
   `relacionado_com`.
3. **Onde o nome está nos bytes.** Em que ficheiro congelado o nome aparece e quantas vezes. Uma
   contagem de ocorrências de uma sequência de caracteres, e a página diz que é isso e não uma
   afirmação de que a página seja sobre a entidade.

E um componente, `<pt-entity-graph>`, que carrega `api/v1/graph.json` e `api/v1/ontology.json` no
momento em que a página abre e remonta as mesmas frases a partir do que lá está agora. Se o grafo
mudar e a página não for reconstruída, é ali que se vê. Não desenha uma teia: um diagrama de força
com trezentos nós é bonito e ilegível, e metade dos leitores deste site são máquinas.

## 2. A menção em prosa passa a ligação

Em qualquer página do jornal, a primeira menção de uma entidade vira ligação. São 313 no site.
A fórmula está publicada em `dados/entidades.json`, no campo `formula`, porque decidir que uma
sequência de letras numa frase É uma entidade é classificar, e o §6 diz que uma classificação é
uma fórmula publicada ou não acontece.

O que ela diz, e o que não diz:

- correspondência do nome **verbatim**, com as maiúsculas e os acentos que os bytes lhe deram;
  não há correspondência aproximada, nem sem acentos, nem por apelido;
- pelo menos 6 caracteres, limites de palavra, a **primeira** menção de cada página e mais nenhuma;
- nunca dentro de outra ligação, de um elemento de código ou de uma marca;
- **só os tipos que nomeiam uma coisa própria** — Pessoa, Organizacao, Instituicao, Editor, Evento,
  Local, Palco. Ficam de fora os tipos derivados pelo léxico, porque os seus rótulos são
  substantivos comuns: ligar a palavra «hardware» numa frase à página de uma Tecnologia seria
  dizer que aquela palavra é uma referência àquele nó, e não é — é a palavra.

Uma ligação destas significa **«o texto contém este nome»**, e não «este texto é sobre esta
entidade». É a mesma distinção que existe entre uma etiqueta do léxico e uma caracterização.

## 3. Duas decisões que valem a pena ficar escritas

### 3.1 Um tipo novo, `Editor`, em vez de alargar `Instituicao`

O registo grava, para cada página congelada, quem a publica. Faltava a aresta: o grafo sabia de
onde veio cada byte e não sabia de QUEM. Agora cada Fonte tem uma aresta `publicada_por` para a
casa que a publica, e a casa ganha uma página que lista tudo o que dela foi congelado — que é
exatamente o que o editor pediu ao dizer que queria clicar num nome e ver «all the Diário da
República happening».

A casa é derivada do campo do registo pela fórmula `editor_de_fonte`, publicada na ontologia: tira
o parêntesis final (que nomeia quem OPERA — «(INCM)», «(AMA)») e fica com o segmento depois do
último travessão (que separa a coleção da casa — «CORDIS — Comissão Europeia»). O que a fórmula
**não** faz é juntar nomes que continuem diferentes depois disso: «Diário da República» e «Diário
da República Eletrónico» ficam dois nós, porque são duas coisas que o registo diz e decidir que são
a mesma seria uma inferência nossa. É a mesma recusa que produziu a história dos dois nomes para os
mesmos palcos.

O nó resolve-se contra os nós que já existem antes de se criar um novo — senão o Governo de
Portugal ficava com dois. E quando não existe nenhum, cria-se um `Editor` e não uma `Instituicao`,
porque a definição publicada de Instituição é «um organismo público, um regulador ou uma unidade de
investigação», e o *Portugal Business News* não é nenhuma dessas coisas. **Alargar a definição para
caber seria mudar o que ela promete a quem já a leu.**

### 3.2 Dois fundamentos para uma ligação, e a página diz qual

O fundamento forte é: o nome está nos bytes de uma página congelada. 179 entidades têm-no.

Quatro não. «Diário da República» é o editor de duas fontes congeladas e não aparece em byte
nenhum — porque a página inicial daquele registo devolve 22 caracteres visíveis a um leitor
automático, que é precisamente uma das histórias deste jornal. Recusar-lhe a ligação deixaria o
leitor sem caminho para a única página que lhe explica isso.

Por isso há um segundo fundamento, `registo`: o nome é o que o **nosso próprio registo** dá ao
editor de pelo menos uma fonte congelada. É mais fraco — é um facto sobre o que nós escrevemos
quando obtivemos a página, e não sobre o que a página diz — e por isso **não é confundido com o
primeiro**: o campo `fundamento` diz qual é, a página da entidade explica-o por extenso, e o portão
22 falha a construção se uma entidade invocar o fundamento fraco tendo o forte.

## 4. Os portões novos, e os que falharam primeiro

Quatro portões novos em `build/gates_artigos.py` — no ficheiro separado, pela mesma razão de
sempre: `build/gates.py` está na lista de recusa e um agente que possa editar o portão que o trava
não tem portão nenhum.

| # | O que guarda |
|---|---|
| 21 | O índice de entidades concorda com o disco, nos dois sentidos: nada prometido sem página, nada órfão sem índice. |
| 22 | Cada entidade ligável tem um fundamento, e o fundamento é verdade. |
| 23 | A fórmula é cumprida nas páginas: uma ligação por entidade e por página, o texto é o nome verbatim, nenhuma página de entidade se liga a si própria, nenhuma ligação dentro de outra. |
| 24 | Nenhuma página de Pessoa diz nada sobre a pessoa: cada valor da tabela de campos tem de ser, byte a byte, um valor que já está em `dados/pessoas.json` ou no nó do grafo. |

Dez testes de injeção, todos a passar. Dois deles apanharam bugs nos próprios portões antes de
apanharem seja o que for no site — o 22 confundia «ter fundamento» com «ser ligável», e o 23
comparava texto escapado com texto não escapado e acusava cada organização com um «&» no nome. E o
24 teve de ser endurecido depois de se ver que a célula da organização passou a conter uma ligação:
o padrão só aceitava texto simples, e um portão que deixa de ver metade do que guarda não guarda
nada.

## 5. O que este trabalho NÃO fez

- **Comentários de agentes por artigo** e a sua visualização (§5.1 do memo anterior). Por fazer.
- **A redação visual** — o chão de sala com Kanban de newsroom.sgit.ai. `/redacao/` continua a ser
  uma tabela.
- **Mais eventos.** Continua a haver um. O grafo é o que junta duas conferências num ecossistema, e
  com uma só não há o que juntar.
- **Uma linha no `CLAUDE.md`** sob *Language*, a registar a exceção do back office em inglês. Não
  foi escrita: `CLAUDE.md` é o ficheiro de regras, está na lista de recusa de propósito, e mudar as
  regras para caberem no código é ao contrário. Fica aqui, outra vez, para o editor.

## 6. Como refazer isto

```
python3 build/graph.py       # ontologia, grafo, triplos — inclui a camada de editores
python3 build/entidades.py   # dados/entidades.json e as 199 páginas
python3 build/artigos.py && python3 build/build.py && python3 build/paginas_extra.py
python3 build/api.py && python3 build/backoffice.py && python3 build/chrome.py
python3 build/gates.py && python3 build/gates_artigos.py && node admin/build/validate.js
```

`build/entidades.py` tem de correr **depois** de `graph.py` e **antes** de tudo o que gera páginas:
é `dados/entidades.json` que a passagem de ligação lê. Se não existir, o site constrói-se na mesma,
sem ligações — uma passagem que se recusasse a correr sem ela seria uma dependência escondida.

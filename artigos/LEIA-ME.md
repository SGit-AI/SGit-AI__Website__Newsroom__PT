# `artigos/` — um artigo é uma pasta, não um ficheiro

Cada artigo deste site vive numa pasta datada, e a pasta é o artigo:

```
artigos/<aaaa>/<mm>/<dd>/<slug>/
    artigo.json         o que o artigo é: estado, secção, título, entrada, em que fontes assenta
    artigo.md           a prosa, com cada afirmação marcada [[fonte:<captura>/<pagina>]]
    afirmacoes.json     o registo de verificação: cada afirmação, a sua fonte, o seu hash, o seu estado
    proveniencia.json   como este artigo veio a existir: que execução, que agente, que modelo, quando
    index.html          gerado por build/artigos.py — ninguém edita isto à mão
```

## Porque uma pasta e não um ficheiro

Porque um artigo não é só o texto. É o texto **mais** a lista de bytes em que assenta, **mais** o
registo de quem verificou cada afirmação contra esses bytes, **mais** o rasto de que execução de
que agente o produziu. Num ficheiro único, três dessas quatro coisas acabam em sítios diferentes —
e quando acabam em sítios diferentes, deixam de concordar.

Com uma pasta, um leitor que queira discutir uma frase tem tudo a um clique: a frase, a fonte
congelada, o hash, e quem disse que a leu.

## Porque a data no caminho

Um endereço construível. `pt.newsroom.sgit.ai/artigos/2026/09/14/<slug>/` diz quando o artigo foi
feito sem que ninguém tenha de abrir o índice — e o §8 do resumo de comissionamento é explícito
sobre isto: um dos assistentes com que esta redação trabalha não segue ligações dentro de uma
página que obteve, por isso os endereços têm de ser previsíveis a partir do que já se sabe.

A data no caminho é a data do **material**: a captura em que o artigo assenta. Não é a data de
publicação. `publicado_em` é um campo separado, escrito pelo editor de registo, e é a única coisa
que faz um artigo aparecer na primeira página.

## Os estados

| Estado | O que significa | Quem o escreve |
|---|---|---|
| `procurado` | A pasta existe para recolher material. Ainda não há prosa. | Pesquisa |
| `rascunho` | Há prosa, escrita a partir do que a pesquisa registou. | Redação |
| `verificado` | Cada afirmação foi relida na cópia congelada e marcada. | Verificação |
| `publicado` | O editor de registo leu e pôs a linha. | **O editor, e mais ninguém** |
| `superseded` | Substituído a partir de uma data. Nunca apagado. | O editor |

O portão 11 de `build/gates.py` falha a construção se um artigo estiver em `publicado` sem
`publicado_por` igual ao editor de registo nomeado em `dados/equipa.json`. Uma execução agendada
que escrevesse essa linha seria apanhada — é a única salvaguarda que separa esta publicação de um
gerador de texto.

## O índice é derivado, nunca escrito

`dados/historias.json` é construído a partir destas pastas por `build/artigos.py`. Não se edita:
edita-se a pasta. É a mesma regra que governa as organizações, que são derivadas dos cartões de
orador e nunca escritas à mão — se o índice fosse escrito, mais cedo ou mais tarde discordaria das
pastas, e nada pareceria avariado.

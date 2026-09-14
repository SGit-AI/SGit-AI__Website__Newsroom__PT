---
description: Rever uma entrega de investigação de um assistente exterior (ChatGPT, Perplexity) para pt.newsroom.sgit.ai — congelar as fontes que nomeia, conferir cada excerto contra os bytes, e aprovar ou rejeitar item a item. Só o editor de registo aprova. Invocar com /newsroom-entregas, opcionalmente com o id da entrega.
allowed-tools: Read Edit Write Glob Grep Bash(python3 *) Bash(node *) Bash(git *) Bash(ls *) Bash(cat *) Bash(curl *)
---

Está a assistir o **editor de registo** nomeado em `dados/equipa.json` — a mesma pessoa que é o
responsável pelo tratamento em `dados/aviso.json`. Confirme no início que é com ele que está a
falar; se não for, pare. Tudo o que decide estado acontece só com a palavra explícita do editor,
um item de cada vez.

## A regra que governa tudo o resto

**Uma entrega é uma lista de pistas com proveniência, nunca factos.** Nada dela pode aparecer na
primeira página, numa secção ou num artigo antes de o editor a aprovar. O portão 13 de
`build/gates.py` falha a construção se aparecer, e não é para ser contornado: é a única coisa que
separa esta redação de um sítio que republica o que um modelo lhe disse.

Uma afirmação passa a poder ser escrita quando **duas** coisas são verdade, e não uma:
1. o excerto que o assistente diz ter lido está nos bytes que esta redação congelou; **e**
2. o editor de registo aprovou-a.

## Receber uma entrega

1. `git pull origin dev`.
2. Guarde o ficheiro **tal como chegou** em `redacao/entregas/<ferramenta>/<delivery.id>.json`.
   Não o corrija, não o reformate, não lhe tire um campo. Uma entrega corrigida em silêncio deixa
   de ser prova de coisa nenhuma, e os erros dela são parte do que há para rever.
3. Se vier num cofre sgit, clone-o em leitura antes de copiar, e classifique a credencial antes de
   ela tocar em alguma coisa: 64 caracteres hexadecimais antes dos dois pontos é uma chave de
   leitura; qualquer outra coisa é uma palavra-passe, logo acesso de escrita, e **não entra no
   repositório**. Registe `vault_id` e `commit` no issue que cada item gerar.
4. `python3 build/entregas.py --fetch`. Isto valida contra o esquema, congela cada endereço que a
   entrega nomeia com SHA-256, e corre o portão dos excertos.

## Ler o resultado com o editor

Mostre, por esta ordem e sem resumir por cima:

- **Quantas fontes são legíveis por máquina**, e porque é que as outras não são. Distinga sempre
  as três razões, porque implicam ações diferentes: `403` é um servidor a bloquear um cliente e o
  editor pode pedir acesso; «renderiza por script» quer dizer que há provavelmente um PDF ou uma
  API que serve o mesmo conteúdo; «404» quer dizer que o endereço está errado ou morreu.
- **Cada afirmação com o seu estado.** `confirmada` quer dizer que o excerto está nos bytes.
  `nao_encontrada` quer dizer que congelámos a página e o excerto não está lá — e não adivinhe
  qual das três causas foi (página mudou, renderiza por script, excerto nunca existiu).
  `fonte_inacessivel` quer dizer que não se pode conferir nada, e **nunca deve ser apresentado ao
  editor como se fosse um defeito da entrega**: é uma limitação do acesso ou do nosso leitor.
- **Onde a entrega e a conferência discordam.** Se as notas do assistente disserem que uma coisa
  «foi confirmada» e o estado da afirmação disser `fonte_inacessivel`, diga-o ao editor de forma
  explícita. É o achado mais valioso de uma revisão e o mais fácil de deixar passar.
- **Os erros de esquema, separados em dois montes.** Erros de forma (um identificador fora do
  padrão, uma data como texto onde o esquema quer um objeto) são ruído. Propostas de vocabulário
  — um tipo ou um verbo que a ontologia não tem — são uma decisão sobre a ontologia e sobem ao
  editor, sempre.

## A decisão, item a item

Para cada item pergunte: **aprovar, rejeitar, ou deixar por rever?**

Escreva a decisão em `redacao/revisoes/<delivery.id>.json`:

```json
{
  "entrega": "<delivery.id>",
  "estado": "em_revisao",
  "decidido_por": "<o nome do editor>",
  "decidido_em": "<hoje>",
  "itens": {
    "item-pol-05": { "estado": "aprovada", "comentario": "<porquê, nas palavras do editor>" },
    "item-pol-01": { "estado": "rejeitada", "comentario": "<porquê>" }
  },
  "comentarios": [
    { "quem": "<quem>", "quando": "<datahora>", "sobre": "item-pol-03", "texto": "<o comentário>" }
  ]
}
```

`estado` de um item só pode ser `aprovada` ou `rejeitada`, e só o editor o escreve. Um item sem
entrada fica por rever, que é o estado seguro.

**Nunca aprove um item cujas afirmações estejam todas `fonte_inacessivel`.** Aprovar quer dizer
«isto pode ser escrito como facto», e não há bytes para o sustentar. Se o item for valioso — e
muitas vezes é — o caminho é outro: abra um issue de pesquisa para encontrar uma fonte que se
consiga ler.

## O que fazer com um item aprovado

Aprovar não publica nada. Abre trabalho:

1. Um issue em `redacao/issues/` no estado `extraido`, a nomear o item, as afirmações confirmadas
   e as fontes congeladas em que assentam.
2. Uma mensagem para `redacao/correio/redacao/entrada/` a pedir a escrita.
3. As entidades e as arestas da entrega são **propostas** e não entram no grafo assim. A Pesquisa
   volta a derivá-las da página congelada. Um verbo ou um tipo novo é uma alteração de ontologia,
   leva uma versão, e é o editor que a decide.

## Quando uma fonte não é legível mas devia ser

Antes de dar um item por perdido, tente o caminho que já existe:

- **Diário da República.** O HTML renderiza por script e devolve cerca de 22 caracteres. Os
  diplomas estão em PDF em `files.diariodarepublica.pt`, e `build/pdf.py` lê-os — decifra o
  manipulador de segurança padrão e segue o mapa `/ToUnicode` de cada tipo. **Encontre o
  endereço; não o construa por adivinhação.** Um endereço inventado que devolve 404 é um erro; um
  que devolve outro diploma é muito pior.
- **403.** Diga-o ao editor. Não contorne um bloqueio: uma redação que ignora o `robots.txt` ou
  falsifica um agente perde o argumento que a torna diferente.

## Fechar a revisão

Quando o editor tiver decidido tudo o que quer decidir hoje:

```
python3 build/entregas.py && python3 build/graph.py && python3 build/build.py
python3 build/chrome.py && python3 build/gates.py && node admin/build/validate.js
```

Os dois portões têm de imprimir OK. Depois incremente `admin/build/version.txt` (uma menor),
acrescente a linha em `admin/versions.html` a dizer o que mudou e porquê, faça commit como
`site vX.Y.Z: <uma frase>` e empurre para `dev`. Confirme a versão em linha.

## O que nunca se faz aqui

Aprovar em nome do editor. Aprovar um item sem bytes que o sustentem. Corrigir a entrega. Ingerir
entidades ou arestas diretamente no grafo. Aceitar um verbo novo sem versão de ontologia. Mudar o
aviso, um portão ou o `CLAUDE.md`. Empurrar com um portão vermelho.

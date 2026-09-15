# O prompt de preparação — o agente lê-se a si próprio

Dá-se isto a uma sessão de agente **antes** de haver entrevista nenhuma. O que sai é o bloco de
estado que o editor vai colar no ChatGPT a seguir ao prompt do entrevistador.

---

Vais preparar uma entrevista em que **o editor de registo te dá direção**. Tu não conduzes a
conversa — quem a conduz é o ChatGPT, com o teu bloco de estado à frente. O teu trabalho é fazer com
que as perguntas sejam as tuas e não as de ninguém.

## Primeiro, lê-te

Sem inventar nada e sem generalizar:

1. **Quem és.** `agents/<o-teu-id>/ROLE.md` e `MANDATE.md`, e a tua entrada em `dados/agentes.json`.
   O domínio, a missão, e o que o teu mandato te proíbe.
2. **O que tens à frente.** Os teus issues em `redacao/issues/` — abertos, bloqueados, e há quanto
   tempo. O teu correio por tratar em `redacao/correio/<o-teu-id>/entrada/`.
3. **O que fizeste.** Os teus últimos registos em `redacao/runs/`, e o que eles dizem que correu mal.
4. **O que está à espera do editor.** `dados/revisao.json` já junta isso; lê-o.
5. **Onde é que te enganaste.** As últimas notas de lançamento em `admin/versions/` que descrevem
   defeitos no teu domínio. Um agente que não sabe o que partiu repete-o.

## Depois, escreve o bloco de estado

Este formato, e nada mais:

```
## Quem fala contigo
agente: <id>            <nome>
domínio: <uma linha do mandato>
não pode: <o que o mandato proíbe, em uma linha>

## O que tenho em mãos, hoje
<uma linha por issue aberto: número, título, há quantos dias, e o que falta. Números, não adjetivos.>

## O que está parado, e porquê
<uma linha por bloqueio, dizendo em quem ou em quê está a bater>

## O que entreguei desde a última conversa
<o que mudou, com as versões. Curto.>

## O que correu mal e eu sei que correu
<sem desculpas e sem o esconder. Um agente que só relata sucessos é um agente que não se pode usar
 para decidir nada.>

## As perguntas que só o editor pode responder
1. <a pergunta, com o contexto que a torna decidível: o que já tentei, que opções vejo, o que cada
    uma custa>
2. <…>
   <entre cinco e dez. Cada uma tem de ser respondível numa frase ou duas — se precisar de um
    parágrafo para ser percebida, ainda não está pronta para ser perguntada.>

## O que eu faria se ninguém respondesse
<a tua proposta, para cada pergunta, em meia linha. É isto que torna a conversa rápida: o editor
 pode dizer só «sim, sim, não, faz antes assim» e ter decidido tudo.>
```

## A regra que torna isto útil

**Uma pergunta sem opções não é uma pergunta, é um pedido de ajuda.** «O que quer que eu faça a
seguir?» devolve uma conversa vaga. «Tenho o issue 006 parado há três dias à espera do PDF da Série
I; vejo três caminhos — insistir noutra via, pedir acesso formal, ou arquivar a pista e publicar o
que já se consegue dizer sem ela; eu faria o terceiro» devolve uma decisão em dez segundos.

E **diz o que farias.** O editor corrige mais depressa do que inventa.

## O que devolves

O bloco de estado, num ficheiro, pronto a entrar no pacote. E uma nota ao editor a dizer quanto
tempo achas que a conversa leva — se as tuas perguntas não cabem em vinte minutos, são demasiadas.

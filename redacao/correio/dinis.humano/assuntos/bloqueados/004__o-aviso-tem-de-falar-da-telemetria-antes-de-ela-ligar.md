---
titulo: O aviso tem de falar da telemetria antes de ela ligar
aberto: 2026-09-15T00:40:00Z
origem: pedido de @Dinis, nesta sessão
issue: —
prioridade: alta
esforco: —
bloqueado_por: dinis.humano
---

## O que há para fazer
`dados/aviso.json` não diz uma palavra sobre eventos de leitura, porque até agora não se enviava
nenhum. A ponte da observabilidade está construída e desligada por falta de credenciais. **No
momento em que ela receber credenciais, o aviso passa a estar errado por omissão.**

## Porque é um assunto do editor e não dos bastidores
`dados/aviso.json` está na lista de recusa de `.claude/settings.json`, e está bem que esteja: o
aviso é onde uma publicação diz o que faz com dados de pessoas, e um agente que o pudesse reescrever
podia alargar o que o site faz e ajustar o aviso para caber. @Bastidores não lhe toca. O responsável
pelo tratamento nomeado é @Dinis, e a via de oposição chega a ele.

## O que o aviso tem de passar a dizer, e é pouco
1. Que eventos anónimos de leitura são enviados para um cofre cifrado desta redação: que páginas
   foram abertas, por que ordem, e quanto tempo ficaram abertas.
2. Que o identificador de sessão são dezasseis dígitos criados na memória do navegador quando a
   página abre e perdidos quando ela fecha, e que não há nome, correio eletrónico, agente do
   utilizador, dimensões de ecrã nem referenciador.
3. Que o servidor da fila vê o endereço IP de quem envia. **Isto não é evitável do lado do
   cliente** e por isso tem de estar escrito: um aviso que dissesse «não recolhemos nada que o
   identifique» e omitisse o IP estaria a dizer uma coisa falsa sobre a única parte que o leitor
   não pode verificar.
4. Que há um interruptor em cada página para desligar o envio, e que ele fica desligado entre
   visitas.

## Critério de aceitação
A ordem importa e é esta: **o aviso primeiro, as credenciais depois.** É a mesma ordem que esta
publicação já seguiu uma vez, quando o aviso de proteção de dados foi publicado ANTES da primeira
página que nomeia alguém. Ligar a telemetria antes de o aviso a descrever seria inverter a única
sequência que este site já acertou de propósito.

Até lá, `assets/observador.js` não envia nada, não mostra aviso nenhum e não põe interruptor — e
essa é a regra 1 do próprio ficheiro: um aviso a dizer «enviamos eventos» num site que não envia
nada é pior do que nenhum aviso, porque é uma afirmação falsa sobre o próprio site.

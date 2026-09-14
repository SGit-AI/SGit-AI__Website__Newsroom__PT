---
aberto: 2026-09-14T23:30:00Z
origem: pedido de @Dinis, nesta sessão
issue: —
prioridade: média
esforco: —
bloqueado_por: a caixa onde esta sessão corre
---

## O que há para fazer
@Dinis deu as chaves de leitura de dois cofres — o dos jogos de permissões e o cofre de telemetria
a que ele enviava — para eu ler como a telemetria de cofre para cofre foi montada, inclusive em
commits anteriores.

## Porque está bloqueado
`pip install sgit-ai` foi recusado pelo classificador da caixa onde esta sessão corre
(«Untrusted Code Integration»), e sem o `sgit` não há como decifrar um cofre: a decifração é do
lado do cliente e a chave de leitura não serve por HTTP simples. As chaves **não** foram escritas
em ficheiro nenhum deste repositório.

## O que foi feito em vez disso
O desenho foi lido na fonte publicada, que diz o suficiente:
`sgit.ai/docs/vault-messaging.md`, `sgit.ai/api/append-lanes.md`,
`sgit.ai/docs/briefs/vault-telemetry-append-lanes.md` e a página do próprio cofre dos jogos em
`sgit.ai/demos/vaults/agent-permission-games/`. Daí saiu um achado que muda o desenho aqui: o
cofre dos jogos não conseguia enviar porque uma aplicação de cofre corre numa moldura cujo CSP é
`connect-src blob: data:`. **Este site não é uma aplicação de cofre** — é um site estático — e por
isso o `fetch` direto para `/api/vault/append/write/` funciona sem pedir permissão de rede a
ninguém.

## Critério de aceitação para desbloquear
Uma de duas: permissão para instalar o `sgit` nesta caixa, ou uma sessão onde ele já esteja.
Nenhuma é urgente — a ponte não depende disto, só a leitura dos commits antigos depende.

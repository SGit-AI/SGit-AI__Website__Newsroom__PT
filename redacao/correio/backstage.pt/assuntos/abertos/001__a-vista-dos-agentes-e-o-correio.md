---
titulo: A vista dos agentes, o quadro de cada um, e o correio
aberto: 2026-09-14T23:30:00Z
origem: pedido de @Dinis, nesta sessão
issue: —
prioridade: alta
esforco: 6h
bloqueado_por: —
---

## O que há para fazer
Dar ao editor, nos bastidores, a vista de quem são os agentes, do que cada um tem à frente, e do
correio que passou entre eles. Antes disto, saber em que pé estava uma história queria dizer abrir
um terminal e ler pastas.

## Como penso fazê-lo
1. `dados/agentes.json` — o registo dos agentes no formato que teams.sgit.ai publica para um
   `ROLE.md`: missão, afirmação central escrita como condição de falha, e o «não responsável por»
   sem o qual cada papel se torna o mesmo papel.
2. `redacao/correio/` no protocolo Email-FS-lite: escritor único, expedição partilhada, um commit
   por ciclo. As duas mensagens que já existiam passam a `.eml` com o corpo intacto.
3. Um leitor só — `build/backoffice_team.py` — que lê a pasta e escreve `dados/correio.json` e
   `dados/quadro.json`. As páginas leem o derivado e nunca a pasta, para não haver dois leitores.
4. Três páginas: a equipa, o quadro por agente, e o correio.

## Critério de aceitação
- Nenhum número nestas páginas que não seja a contagem de ficheiros deste repositório.
- O quadro a derivar a posse de cada issue do jornal por fórmula publicada, e não à mão.
- Os portões verdes: `build/gates.py`, `build/gates_artigos.py`, `admin/build/validate.js`.

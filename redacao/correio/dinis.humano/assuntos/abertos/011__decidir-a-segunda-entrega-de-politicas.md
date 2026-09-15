---
titulo: Decidir a segunda entrega do ChatGPT sobre políticas, item a item
aberto: 2026-09-15T11:50:00Z
origem: entrega chatgpt-2026-09-15-politicas-2, ingerida na sessão a-linha-de-publicacao
issue: 007
prioridade: alta
esforco: —
bloqueado_por: —
---

## O que há para fazer
Decidir os três itens da segunda entrega de políticas. Três afirmações têm o excerto nos bytes
congelados; uma não se pôde conferir porque o EUR-Lex respondeu 202 e não devolveu corpo.

Está em `/entregas/chatgpt-2026-09-15-politicas-2.html`, que agora abre com um índice: cada item
com o seu veredicto de bytes e um salto para a afirmação.

## O que mudou desde a primeira entrega
**A entrega valida contra o esquema.** A primeira falhou em 45 pontos porque o resumo mandava
buscar o contrato a um endereço que não existe. Corrigido o endereço na v0.17.0, esta passagem
validou à primeira e não reenviou nenhuma das oito páginas que a redação já tinha.

O assistente também encontrou um erro **meu**: a v0.17.0 mandava omitir `delivery.vault` antes de
o cofre existir, e o esquema exige a chave. Ele disse-o nas notas e usou `null`, que é o que o
esquema aceita. O resumo está corrigido.

## Critério de aceitação
- Cada um dos três itens com uma decisão registada em `redacao/revisoes/`.
- Nenhum item aprovado sem o excerto ter sido lido nos bytes congelados.

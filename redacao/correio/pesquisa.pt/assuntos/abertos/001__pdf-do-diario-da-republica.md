---
titulo: O PDF do Diário da República, para a agenda e para a designação
aberto: 2026-09-14T12:10:00Z
origem: redacao/correio/pesquisa.pt/entrada/002__dinis.humano__tres-primeiras-historias.eml
issue: 001,002
prioridade: alta
esforco: 2h
bloqueado_por: —
---

## O que há para fazer
Encontrar o endereço do PDF do Diário da República para o diploma da agenda nacional (001) e para
o ato de designação do regulador (002). O `dre.pt` congelado a 14 de setembro tem 2 346 bytes e
22 caracteres visíveis: renderiza por script e não diz nada a um leitor automático. Os PDFs dizem,
e `build/pdf.py` já os lê — decifra o manipulador de segurança padrão e segue o mapa `/ToUnicode`.

## Como penso fazê-lo
1. Encontrar o endereço a partir de uma página que o nomeie, e não por construção.
2. Obter, congelar em `fontes/congeladas/<data>/`, hashear e registar.
3. Ler o PDF com `build/pdf.py` e extrair o que a fonte diz, sem arrumar nada.
4. Escrever a @Redacao dizendo o que passou a estar em bytes.

## Critério de aceitação
- O PDF congelado, com SHA-256 no registo, e o hash a reverificar em cada construção.
- O instrumento legal nomeado com o número e a data que o PDF diz, e não outros.
- Se o endereço não for encontrado, o issue fica em «procurado» e a ausência é escrita como
  ausência. Um endereço inventado que devolve outro diploma é pior do que um que devolve 404.

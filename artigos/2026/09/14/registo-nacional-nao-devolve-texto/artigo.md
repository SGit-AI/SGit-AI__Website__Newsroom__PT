A 14 de setembro de 2026 esta redação pediu três páginas do registo público português da mesma
maneira que qualquer programa as pediria — um pedido HTTP, sem correr scripts — e guardou os bytes
que recebeu.

O Diário da República devolveu 2 346 bytes e **22 caracteres de texto visível**
[[fonte:2026-09-14/registo/dre-inicio]]. A página do Governo devolveu 165 569 bytes e **348
caracteres** [[fonte:2026-09-14/registo/gov-ia]]. O portal nacional de dados abertos devolveu
849 388 bytes e **27 406 caracteres**, e é a única das três que um leitor automático consegue ler
[[fonte:2026-09-14/registo/dados-gov]].

As três páginas estão congeladas neste repositório com o seu SHA-256. Quem discordar destes
números pode voltar a contá-los sobre os mesmos bytes.

## O que isto é, e o que não é

É uma medição sobre artefactos publicados. Uma página que devolve muitos bytes e quase nenhum
texto renderiza o seu conteúdo por script, no navegador de quem a visita. Para um leitor humano
com um navegador moderno, funciona. Para um programa — um motor de busca antigo, um leitor de
ecrã mal configurado, um agente, ou uma redação como esta — não há lá texto.

Não é uma alegação sobre ninguém. Renderizar por script é uma escolha técnica comum, e a maior
parte de quem a faz nunca teve razão para pensar num cliente que não corre scripts.

E não é a afirmação de que o registo nacional é ilegível. É a afirmação, mais estreita e
verificável, de que **estas três páginas, nesta data, devolveram isto**.

## A parte que salva a história

O Diário da República publica o texto integral dos diplomas em PDF, e esses PDF são legíveis.

Não sem trabalho: chegam cifrados com o manipulador de segurança padrão — palavra-passe de
utilizador vazia, apenas restrições de permissões — e com tipos subconjuntados cujos códigos de
glifo não são texto. Uma biblioteca genérica de extração devolve zero caracteres, e devolve-os em
silêncio. Foi o que aconteceu à primeira tentativa desta redação.

A distinção importa mais do que parece. Um zero devolvido por uma limitação do leitor é
indistinguível, no ficheiro de resultados, de um zero devolvido por uma página vazia — e essa
confusão levaria este artigo a dizer «não se consegue ler o registo nacional» quando a verdade
seria «não implementámos o decifrador». `build/pdf.py` implementa-o, e lê o mapa `/ToUnicode` de
cada tipo em vez de adivinhar o deslocamento dos glifos.

Com isso, um diploma do Diário da República lê-se por inteiro. O que continua por resolver é
outra coisa, e menor: o endereço do PDF tem de ser **encontrado**, não construído por adivinhação.

## Porque é que esta redação mediu isto

Porque foi a primeira parede em que bateu. As três primeiras histórias que este site tem
encomendadas dependem todas de conseguir ler o registo nacional, e duas delas estão paradas
exatamente aqui.

Há uma resolução humana óbvia — alguém abre a página num navegador e lê — e essa resolução é,
ela própria, o mecanismo de correção deste site a funcionar no primeiro dia.

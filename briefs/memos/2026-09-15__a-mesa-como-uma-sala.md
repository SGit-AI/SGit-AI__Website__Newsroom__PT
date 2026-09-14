# A mesa como uma sala — o registo de uma peça de trabalho

**Data:** 15 de setembro de 2026 · **Versão:** v0.6.0 · **Agente:** Claude (Anthropic), sessão de
construção · **Editor de registo:** Dinis Cruz

Responde ao item do memo
[`2026-09-14__o-ecossistema-portugues-de-ia.md`](2026-09-14__o-ecossistema-portugues-de-ia.md)
que apontava para a redação virtual de newsroom.sgit.ai:

> *uma redação virtual com representações visuais dos artigos, com quadros Kanban, quase uma mesa
> de notícias visual*

com a observação de que `/redacao/` aqui é uma tabela e aquilo é uma sala.

## 1. A diferença entre uma tabela e uma sala

Não é decoração. **Uma tabela mostra linhas; uma sala mostra carga** — quem tem o quê em cima da
mesa agora, o que está parado à espera de quem, e onde está o próximo gesto. São perguntas
diferentes, e a segunda é a que se faz a uma redação às cinco da tarde.

`/redacao/` passa a abrir com quatro bancadas: Pesquisa, Redação, Verificação e o editor de
registo. Cada uma mostra quantos cartões estão à espera dela, quantas das suas entradas estão por
fechar, e uma barra que mede a razão entre as duas — não o total, que seria um gráfico de quem
trabalhou mais, o que não é a pergunta.

Clica-se numa bancada e a sala responde: o que ela faz, o que **recusa** fazer, em que pastas pode
escrever, e quais os cartões que estão à espera dela. As colunas que não são dela esbatem-se em vez
de desaparecerem — o quadro tem de continuar a ser o mesmo quadro.

## 2. O que a sala não tem, e porquê

**Não há maneira de mover um cartão.** Não há arrastar, não há botão, não há menu de estado.

A ausência é o desenho. O estado de uma história vive nos ficheiros da pasta dela, e quem o muda é
quem tem direito de escrita nessa pasta — o que o portão 12 confere a cada execução. Uma sala que
deixasse arrastar um cartão para «publicado» estaria a oferecer, num clique e a quem quer que
abrisse a página, exatamente o gesto que esta publicação reserva a um humano nomeado. A coluna
«publicado» diz isso onde se lê: *é a única coluna para onde nenhuma execução automática pode
empurrar um cartão*.

E o quadro em tabela **fica lá**, por baixo, sem JavaScript. Metade dos leitores deste site são
máquinas; uma redação que só se deixasse ler por uma delas seria a ironia errada. As duas versões
saem dos mesmos ficheiros.

## 3. Um defeito apanhado na própria construção

A primeira versão do quadro assumiu **um artigo por issue**. Casou cada issue com o primeiro
artigo que o nomeasse, e o segundo desaparecia.

Neste repositório já há um caso: o issue 001 encomendou a história do instrumento legal da agenda,
e da mesma encomenda saiu também a história de o registo nacional não devolver texto. O quadro
mostrava seis cartões, parecia completo, e **escondia um artigo**.

Um quadro que esconde trabalho é pior do que não haver quadro nenhum, precisamente porque parece
completo. O cartão passou a ser o **artigo** — a coisa que tem ficheiros e um estado verdadeiro — e
o issue só ganha cartão próprio quando ainda não produziu nenhum. Um cartão que tem irmãos diz
quantos.

## 4. Os registos de execução, e o portão 26

A convenção deste repositório é que cada passagem do ciclo deixa um registo em `redacao/runs/` com
o diff por pasta, e o portão 12 falha uma execução que atravessou a fronteira de um departamento.
Esse portão **isenta** uma execução que não declara departamento, porque a sessão de arranque cria
todas as pastas e tem de o poder fazer.

As sessões desta semana são de **construção**, não de redação: constroem as ferramentas com que os
departamentos trabalham. Escrever `departamento: null` e seguir em frente seria usar a isenção sem
a merecer — e uma isenção que qualquer execução pode invocar escrevendo a palavra certa não é uma
fronteira, é uma porta com o nome ao lado.

Por isso: cada registo declara `especie`, e o **portão 26** confere que uma execução de construção
não congelou uma fonte, não moveu um cartão, não pôs nada em publicado, e não registou uma versão
com os portões vermelhos. Cinco testes de injeção. O registo de arranque ganhou
`especie: "arranque"` — a sua própria prosa já dizia o que ele era; o campo torna-o legível por um
portão em vez de só por uma pessoa.

## 5. O estado da mesa, em números reais

| Bancada | Cartões à espera | Entradas | Por fechar |
|---|---|---|---|
| Pesquisa | 3 | 20 | 10 |
| Redação | 0 | 10 | 7 |
| Verificação | 3 | 14 | 0 |
| Editor de registo | 3 + 1 entrega | 2 | 2 |

Sete cartões, zero publicados, quatro coisas à espera do editor. **Zero publicados é a informação
mais honesta desta página**, e é por isso que a coluna fica lá, vazia, em vez de ser escondida.

## 6. O que continua por fazer

- **Mais eventos.** Continua a haver um. O grafo é o que junta duas conferências num ecossistema, e
  com uma só não há o que juntar. Web Summit é o próximo óbvio, e é trabalho de Pesquisa: obter,
  congelar, hashear, registar.
- **A linha no `CLAUDE.md`** sob *Language* para a exceção do back office em inglês, e a lista de
  comandos daquele ficheiro, que é mais antiga do que metade do pipeline. Nenhuma das duas foi
  escrita: é o ficheiro de regras, está na lista de recusa de propósito, e mudar as regras para
  acompanhar o código é ao contrário. Fica aqui — terceira vez — para o editor.

# O trabalho dos agentes — o registo de uma peça de trabalho

**Data:** 14 de setembro de 2026 · **Versão:** v0.5.0 · **Agente:** Claude (Anthropic), sessão de
construção · **Editor de registo:** Dinis Cruz

Responde ao §5.1 do memo
[`2026-09-14__o-ecossistema-portugues-de-ia.md`](2026-09-14__o-ecossistema-portugues-de-ia.md):

> *uma visualização e um mapeamento dos comentários que cada um dos diferentes agentes fez a isto*

e ao pedido, do mesmo resumo, de que a pasta de um artigo contenha o fluxo de trabalho, as
decisões, os comentários e as vistas dos vários agentes sobre ele.

## 1. A recusa que este trabalho obrigou a fazer, e que é o essencial dele

A maneira fácil de fazer isto seria **escrever comentários**. Ficariam bem: um do ChatGPT a
sugerir um ângulo, outro da Perplexity a discordar da fonte, um da verificação a confirmar. Cada
artigo teria uma discussão, a visualização teria o que mostrar, e nada daquilo teria acontecido.

Seria **proveniência fabricada** — a única coisa que um sítio inteiro construído sobre proveniência
não pode fazer. Atribuir a um modelo de outro fornecedor uma frase que ele nunca escreveu é pior do
que uma afirmação sem fonte: é uma afirmação com uma **fonte falsa**, e uma fonte falsa não se
distingue de uma verdadeira sem sair do sítio para a conferir.

Por isso nada aqui foi escrito. Tudo é **derivado** de registos que já existem, e cada entrada
nomeia, no campo `de`, o ficheiro e o caminho de onde saiu.

## 2. De onde sai cada entrada

| Origem | Torna-se |
|---|---|
| `proveniencia.json#cronologia[]` | uma **ação** de um agente nomeado, com a hora, o que fez e porque importa |
| `proveniencia.json#por_rever[]` | uma **pergunta** que aquele agente deixou em aberto, e que fica aberta |
| `afirmacoes.json#afirmacoes[]` | a **verificação** de uma afirmação contra os bytes, com o método declarado |
| `artigo.json#o_que_falta[]` | uma **falta** que a redação diz que ainda tem |
| `dados/entregas.json#entregas[…].itens[]` | uma **proposta** de um assistente exterior, com quantas das suas afirmações tinham o excerto nos bytes |
| `dados/entregas.json#entregas[…].revisao` | a **decisão** do editor — ou a sua ausência, que é o estado em que quase tudo está |

São 62 entradas em 6 artigos, de 5 agentes: Pesquisa (20), Verificação (14), ChatGPT/gpt-6-astra
(16), Redação (10), o editor (2). 35 estão por fechar, e estarem por fechar é a informação.

**Como uma proposta exterior se liga a um artigo** — e é uma fórmula, não um palpite. Liga-se pela
**secção**: uma entrega chega para uma secção, um artigo pertence a uma secção. O comentário diz
isso por extenso e não finge mais: *«chegou para a secção das políticas, que é a secção deste
artigo»*. Não afirma que a proposta seja sobre o artigo — para isso é preciso alguém ler as duas
coisas, e esse alguém é o editor.

## 3. O que se vê

`<pt-comment-map>`, duas vistas de uma coisa só:

- **a grelha** — agente por espécie de contribuição, com os números. Responde a «quem trabalhou
  nisto». Não é um gráfico: é uma tabela, que é o que se lê quando se quer saber quem fez o quê.
- **o fluxo** — por ordem, filtrável por agente, e cada entrada mostra o seu campo `de`. Deixar o
  caminho à vista não é preguiça: é a diferença entre um registo de trabalho e a encenação de um.

Está no fim de cada página de artigo, por baixo da proveniência — a proveniência diz COMO o artigo
veio a existir, isto diz QUEM disse o quê pelo caminho. E está agregado em
`/backoffice/agents.html`, que é a resposta da consola ao pedido de *gerir as ações dos vários
agentes*.

## 4. O portão 25

Cada entrada tem de nomear um ficheiro e um caminho que **existem e resolvem**. O portão abre o
ficheiro e percorre o caminho — `dados/entregas.json#entregas[<id>].revisao` é aberto, o item com
aquele id é encontrado, e a chave é seguida. Se não resolver, a construção falha.

É a regra das afirmações virada para dentro. Sete testes de injeção, todos a passar: um comentário
sem `de`, um `de` para um ficheiro que não existe, um para além do fim de uma lista, um para uma
chave inexistente, um ficheiro de comentários escrito à mão em vez de derivado, o agregado a
inflacionar o trabalho feito, e um agente que ninguém declarou.

O último merece uma linha: **um nome de agente que ninguém sabe de onde vem é um colaborador
anónimo** numa publicação cujo argumento inteiro é saber quem disse o quê.

## 5. `build/tudo.py` — e porque nasceu agora

A sequência de construção tem dez passos e **a ordem importa**. `entidades.py` tem de correr antes
de tudo o que escreve uma página, porque é o ficheiro que ele produz que faz uma menção em prosa
virar ligação. Correr fora de ordem não rebenta: produz um site com menos ligações do que devia, e
**sem aviso nenhum**. É a pior espécie de fragilidade.

A lista de comandos em `CLAUDE.md` é mais antiga do que metade destes passos. `CLAUDE.md` é o
ficheiro de regras, está na lista de recusa de propósito, e mudá-lo para acompanhar o código é ao
contrário. Então a ordem verdadeira passa a viver num ficheiro executável — o único sítio onde uma
ordem não pode ficar desatualizada sem que alguma coisa falhe:

```
python3 build/tudo.py               # a construção inteira, por ordem, e depois os três portões
python3 build/tudo.py --fetch       # o mesmo, indo à rede buscar as fontes primeiro
python3 build/tudo.py --so-portoes  # só os portões
```

Um portão vermelho pára tudo e o código de saída é o do passo que falhou.

Isto nasceu agora por uma razão concreta: o editor avisou que **haverá outro agente Claude a fazer
alterações a este site**. Duas sessões a construir a partir de uma lista de comandos incompleta
produzem dois sites diferentes a partir do mesmo repositório, e a diferença só aparece no `git
diff` de ficheiros gerados — que é exatamente onde ninguém olha.

## 6. Nota para quem trabalhar neste repositório ao mesmo tempo

- **Correr `python3 build/tudo.py` antes de cada commit.** Um commit com ficheiros gerados
  desalinhados obriga o próximo a resolver conflitos em HTML gerado, o que ninguém deve fazer à
  mão: resolve-se voltando a construir.
- **Ir buscar `dev` antes de empurrar**, sempre, e nunca reescrever história. Cada empurrão para
  `dev` é uma versão menor e leva o incremento em `admin/build/version.txt` mais a linha em
  `admin/versions.html`. Se as duas sessões escolherem o mesmo número, uma delas tem de voltar
  atrás — por isso o número escolhe-se **depois** de ir buscar `dev`, e não antes.
- **Os portões novos vivem em `build/gates_artigos.py`**, não em `build/gates.py`, que está na
  lista de recusa. A razão é a de sempre: um agente que possa editar o portão que o trava não tem
  portão nenhum.

## 7. O que continua por fazer

- **A redação visual** — o chão de sala com Kanban de
  [newsroom.sgit.ai/governance/newsroom/](https://newsroom.sgit.ai/governance/newsroom/index.html).
  `/redacao/` continua a ser uma tabela.
- **Mais eventos.** Continua a haver um. O grafo é o que junta duas conferências num ecossistema.
- **A linha no `CLAUDE.md`** sob *Language*, a registar a exceção do back office em inglês, e a
  lista de comandos desatualizada no mesmo ficheiro. Nenhuma das duas foi escrita, pela mesma razão,
  e ficam aqui — outra vez — para o editor.

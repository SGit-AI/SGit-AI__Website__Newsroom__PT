# O prompt do agente — quem monta o pacote

Este é o prompt que o editor dá a uma sessão de agente (Claude Code, nesta redação) para preparar
uma entrevista. O agente não entrevista ninguém: **monta o pacote que a pessoa vai receber**.

---

Vais preparar um pacote de entrevista para **pt.newsroom.sgit.ai**. A pessoa é: `<nome>`.

## O que fazes, por esta ordem

1. **Procura o que esta redação já tem sobre ela.** `dados/pessoas.json`, a sua página em
   `entidades/pessoa/<slug>/` se existir, e as cópias congeladas onde o nome aparece —
   `dados/entidades.json` diz em que ficheiros o nome foi encontrado e quantas vezes. Se a redação
   não tem nada, diz-o: uma entrevista com alguém de quem não se sabe nada é uma entrevista com
   perguntas genéricas.
2. **Lê a regra das pessoas antes de escrever uma linha.** Uma pessoa, nesta redação, só carrega
   três campos: o cargo listado, a organização listada, e a página que o lista. Nada de biografia,
   nada de caracterização, nada de dados de contacto — nem no pacote, nem no bloco do tema, nem no
   que vier de volta. Ver `CLAUDE.md`, regra 4, e o aviso de proteção de dados.
3. **Escreve o bloco do tema** segundo o modelo em `03__bloco-do-tema.md`, a partir do que
   encontraste e não do que presumes. Entre três e cinco temas; cinco a oito perguntas de arranque.
   Cada afirmação sobre a pessoa tem de sair de uma página que esta redação congelou.
4. **Monta o pacote.** São cinco ficheiros e nada mais:

   ```
   entrevista-<slug>/
     LEIA-ME.md                 o que é isto, o que fazer, em três parágrafos
     prompt-da-entrevista.md    a cópia do prompt na língua escolhida
     bloco-do-tema.md           o que escreveste no passo 3
     o-que-acontece-depois.md   aprovação, tradução, publicação, e como pedir a remoção
     devolver/                   pasta vazia, onde a pessoa põe o relatório
   ```

5. **Entrega-o.** Um cofre sgit é o melhor caminho — a pessoa abre-o no navegador sem instalar nada
   e devolve o relatório para lá mesmo. Um `.zip` serve quando não. Em qualquer dos casos, o que
   vai para fora é só o que escreveste: nada de cópias de páginas de outras pessoas.

## O que NÃO fazes

- **Não escreves uma biografia.** Nem no LEIA-ME, nem no bloco do tema, nem como «contexto».
- **Não adjetivas a pessoa.** «Fundou X em 2019» é um registo; «é uma referência no setor» é um
  veredicto, e esta redação publica o registo e nunca o veredicto.
- **Não pões o contacto de ninguém em ficheiro nenhum.** O convite sai pelo canal que o editor já
  usa com essa pessoa; o pacote não guarda por onde.
- **Não prometes publicação.** O pacote diz que a entrevista é revista pela pessoa e depois pelo
  editor de registo, e que pode não ser publicada.
- **Não traduzes a entrevista** enquanto a pessoa não aprovar o relatório na língua em que falou.

## O que devolves ao editor

O caminho do pacote, o bloco do tema para ele ler antes de sair, e uma lista do que **não**
conseguiste encontrar sobre a pessoa nas fontes congeladas — porque é isso que decide se as
perguntas são boas ou genéricas.

# 09 — As entrevistas

A outra metade do que esta redação publica. O bloco `08__research-briefs/` manda um assistente
procurar **documentos**; este manda-o conduzir uma **conversa**, e o material que sai é de outra
natureza: as palavras de uma pessoa, ditas por ela, sobre o que está a fazer.

## Porque é por voz

Porque é mais fácil para quem responde e melhor para quem lê. Uma pessoa ocupada não escreve
duas páginas sobre o seu trabalho, mas fala vinte minutos sobre ele — e fala melhor do que
escreve, com exemplos que não porá por escrito. O ChatGPT em modo de voz faz a entrevista à hora
que lhe der jeito, sem marcar nada com ninguém.

E quem preferir escrever, escreve: o mesmo prompt funciona nos dois modos.

## As três peças

| Ficheiro | O que é | Quem o usa |
|---|---|---|
| `01__prompt-da-entrevista.pt.md` | O entrevistador. Sempre igual. | A pessoa entrevistada |
| `02__the-interview-prompt.en.md` | O mesmo, em inglês | A pessoa entrevistada |
| `03__bloco-do-tema.md` | O que muda: quem, porquê, sobre o quê | O agente escreve, a pessoa cola |
| `04__prompt-do-agente.md` | Como se monta um pacote para uma pessoa | O editor dá a um agente |

## O caminho, do convite ao artigo

1. O editor escolhe a pessoa e dá `04__prompt-do-agente.md` a uma sessão de agente.
2. O agente procura o que a redação já tem congelado sobre ela, escreve o bloco do tema, e monta um
   pacote — um cofre sgit ou um `.zip`.
3. A pessoa recebe o pacote, cola os dois blocos no ChatGPT e fala. No fim tem um relatório.
4. **Revê o relatório e corrige-o.** Nada sai sem isso.
5. Devolve-o. A redação trata as suas afirmações como afirmações — coisas que ela disse, não factos
   do mundo — e vai procurar fonte para as que forem verificáveis.
6. O editor de registo decide se publica, e o que publica. A publicação é em português europeu; se
   a conversa foi em inglês, a tradução é feita aqui e mostrada à pessoa antes de sair.

## As regras que não se negoceiam

- **Uma entrevista é uma fonte primária sobre quem fala, e mais nada.** Se alguém disser um número
  sobre o mercado, isso é uma afirmação para verificar, não um facto porque foi dito em voz alta.
- **Três campos por pessoa**, como em todo o lado neste site: cargo listado, organização listada,
  página que o lista. Uma entrevista não abre exceção a isto.
- **Nenhum dado de contacto** entra em ficheiro nenhum, nem no pacote nem no que volta.
- **A aprovação é da pessoa e a publicação é do editor.** São duas decisões, e nenhuma substitui a
  outra.
- **A remoção é incondicional e não leva motivo.** Quem for entrevistado pode pedir que a entrevista
  saia, depois de publicada, sem explicar porquê — e o aviso de proteção de dados diz como.

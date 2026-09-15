# 10 — A entrevista ao editor

O bloco `09__entrevistas/` manda um assistente entrevistar **alguém de fora**, e o que sai é
matéria-prima para um artigo. Este manda um agente entrevistar **o editor de registo**, e o que sai
é outra coisa: **direção**. Que histórias vale a pena escrever, com quem falar, o que fazer a
seguir, o que parar de fazer.

## O problema que isto resolve

Um agente desta redação sabe o que tem à frente — os seus issues, o seu correio, o que está
bloqueado — e não sabe **o que o editor acha que importa**. Essa informação existe, e hoje só sai
quando o editor se lembra de a escrever. Uma conversa de vinte minutos tira-a toda, e tira-a melhor
do que qualquer formulário: o editor diz «olha ali», «e aquilo?», «tenho uma ideia», e nada disso
cabe num campo.

## A diferença que muda tudo: o agente estuda antes de perguntar

Uma entrevista genérica ao editor vale zero. O agente que conduz esta conversa **começa por ler o
seu próprio estado** — o `ROLE.md` e o `MANDATE.md` da sua identidade, os seus issues abertos e
bloqueados, o seu correio por tratar, os seus últimos registos de execução — e leva para a conversa
as **suas** perguntas em aberto, com nomes e números. A diferença entre «o que quer que eu faça?» e
«tenho o issue 006 parado há três dias à espera de um PDF que não encontro; quer que insista, que
peça acesso, ou que arquive a pista?» é a diferença entre uma conversa educada e uma decisão.

## As peças

| Ficheiro | O que é | Quem o usa |
|---|---|---|
| `01__prompt-de-preparacao.md` | O agente lê-se a si próprio e escreve o bloco de estado | O agente, antes |
| `02__prompt-da-entrevista.pt.md` | O entrevistador. Sempre igual. | O editor cola no ChatGPT |
| `03__the-interview-prompt.en.md` | O mesmo, em inglês | O editor |
| `04__o-que-volta.md` | O relatório, e como se transforma em ficheiros | O agente, depois |

## O caminho

1. O editor diz a um agente: **prepara-me uma entrevista**.
2. O agente corre `01__prompt-de-preparacao.md` sobre si próprio e produz um **bloco de estado** —
   quem é, o que tem em mãos, o que está bloqueado, e as cinco a dez perguntas em aberto que só o
   editor pode responder.
3. O agente monta um pacote — um cofre sgit, que o editor abre no telemóvel sem instalar nada — com
   o prompt do entrevistador e o bloco de estado.
4. O editor cola os dois no ChatGPT e fala. Vinte minutos, por voz, à hora que lhe der jeito.
5. No fim tem um **relatório de direção**, que revê e devolve.
6. O agente transforma-o em ficheiros: issues novos, decisões registadas, correio para outros
   agentes, prioridades reordenadas. E responde ao editor a dizer o que fez com cada coisa.

## As regras, que são as mesmas de sempre

- **Direção não é facto.** Se o editor disser «a empresa X é a maior do setor», isso é uma pista
  para verificar como qualquer outra — não entra num artigo por ter sido dito pelo editor. O que a
  entrevista produz são **prioridades e perguntas**, não afirmações sobre o mundo.
- **Direção não é permissão.** Nada do que for dito nesta conversa dispensa um portão, autoriza um
  agente a escrever fora da sua pasta, ou põe uma história em `publicado`. Publicar continua a ser
  uma linha que o editor escreve num ficheiro, e só ele.
- **Uma ideia dita em voz alta é uma ideia, não uma ordem.** O relatório separa o que o editor
  **decidiu** do que ele **sugeriu** — e o agente trata as duas coisas de forma diferente.
- **Nada de dados de contacto**, aqui como em todo o lado.
- **Se o agente não perceber, pergunta antes de fazer.** Uma execução que pára honestamente é uma
  boa execução, e isso não muda por a instrução ter vindo por voz.

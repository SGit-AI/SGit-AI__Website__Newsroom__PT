# O que volta, e o que o agente faz com ele

O relatório de direção não é um documento para arquivar. É uma lista de coisas para fazer, e o
agente que pediu a entrevista é quem as faz — **e quem responde a dizer o que fez com cada uma.**

## A regra que separa esta redação de um assistente obediente

O relatório traz duas secções que se parecem e que se tratam de maneira diferente:

- **Decisões** → fazem-se. Cada uma vira um ficheiro: um issue, uma alteração de prioridade, uma
  entrada num registo de decisão. A razão que o editor deu vai **verbatim** para esse ficheiro,
  porque é ela que permite decidir o caso parecido da semana seguinte sem voltar a perguntar.
- **Ideias e sugestões** → **não se fazem**. Abrem um issue em estado `proposto`, com a frase do
  editor e a nota de que foi uma ideia e não uma ordem. Um agente que trata uma ideia como decisão
  produz trabalho que ninguém pediu e que ninguém pode recusar sem parecer difícil.

Se o relatório não deixar claro em qual das duas cai alguma coisa, **pergunta-se**. Não se adivinha.

## O que se escreve, e onde

| O que veio | Onde vai |
|---|---|
| Uma decisão sobre um issue existente | O próprio issue: novo estado, e a razão do editor citada |
| Uma decisão que abre trabalho novo | Um issue novo em `redacao/issues/`, a citar a entrevista |
| Uma ideia | Um issue em `proposto`, que ninguém começa sem outra palavra |
| Uma prioridade | A ordem dos issues, e uma linha no registo de execução a dizer porquê |
| Uma pista para verificar | Um issue de pesquisa. **Nunca um artigo, nunca uma afirmação** |
| Uma pessoa nomeada | Nada, até haver uma página congelada que a liste. O editor ter dito um nome não é uma fonte |
| Uma instrução que o teu mandato proíbe | Correio ao editor a dizer que não podes, e porquê. E paras |

## O registo

A entrevista fica em `redacao/entrevistas-ao-editor/<data>-<agente>.md`, tal como voltou, com as
correções do editor. É a proveniência da direção: daqui a um mês, quando alguém perguntar porque é
que esta redação foi por ali, a resposta é um ficheiro com data e não a memória de uma sessão.

## A resposta ao editor

Quando acabares, escreve-lhe — `redacao/correio/expedicao/dinis.humano/` — com uma linha por ponto
do relatório e o que fizeste com ele. Incluindo os que não fizeste, e porquê. **Um relatório que
desaparece dentro de um agente ensina o editor a não voltar a dar direção nenhuma.**

## E o que nunca acontece

Nada do que for dito numa destas conversas põe uma história em `publicado`, dispensa um portão,
alarga a pasta em que um agente pode escrever, ou trata uma afirmação do editor como facto
verificado. A direção diz **o que vale a pena fazer**. Como se faz continua a ser o que está escrito
no `CLAUDE.md`, e isso não se negoceia por voz.

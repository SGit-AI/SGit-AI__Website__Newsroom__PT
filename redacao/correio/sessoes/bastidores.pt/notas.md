# notas — bastidores.pt

Registo de raciocínio, só de acrescentar. Uma entrada por ciclo.

## 2026-09-14T23:30Z — ciclo 1: a equipa passa a ser visível

Pedido de @Dinis: ver a equipa de agentes de forma visual nos bastidores, com o quadro de cada um,
montar o correio entre agentes, e abrir uma via para ele falar com os bastidores a partir do site.

Li primeiro, como foi pedido. O que trouxe, e de onde:

- **teams.sgit.ai** — o formato de um `ROLE.md`: nome, localização, missão central, afirmação
  central e **«não responsável por»**. Este último é o campo que faz de um papel um papel: 31 dos
  39 ficheiros medidos têm-no, e sem ele «cada papel torna-se silenciosamente o mesmo papel». A
  afirmação central deve ser escrita como condição de falha, para poder ser desmentida. Foi isso
  que fiz em `dados/agentes.json`: cada agente diz em que circunstância está a falhar.
- **teams.sgit.ai/comms** — os papéis não se mandam mensagens; definem endereços. Diz também que
  não há aviso de receção nem garantia de entrega, e chama a isso a lacuna óbvia.
- **sgraph.ai/library/agentic-teams** — a forma publicada de cada agente (`@Content`, `@Dev`,
  `@Observer`, `@Journalist`…): modelo, domínio, **o que possui**, **o que não possui e de quem é**,
  como trabalha com os outros, e a cadência. É a definição mais completa do conjunto, e é a que
  segui de mais perto.
- **sgraph.ai/library/how-it-works/email-fs-lite** (v0.6) — o protocolo, em sete páginas. Adotado
  tal e qual, com uma diferença dita em voz alta no `LEIA-ME.md`: corre num repositório git e não
  num cofre, pelo que `git pull` faz o que lá é `sgit pull`.
- **sgit.ai/docs/vault-messaging** e **sgit.ai/api/append-lanes** — as filas de acrescento, e a
  divisão em quatro capacidades: quem acrescenta **só** acrescenta; quem enumera não escreve; quem
  configura e purga é o dono. É por isso que um código de acrescento é a única credencial que
  sobrevive a ser publicada.
- **sgit.ai/docs/briefs/vault-telemetry-append-lanes** e a página do cofre dos jogos — o padrão da
  telemetria. Daqui saiu o achado que muda o desenho: o cofre dos jogos **construía e não enviava**,
  porque uma aplicação de cofre corre numa moldura com `connect-src blob: data:`. Este site é
  estático, não é uma aplicação de cofre, e por isso o `fetch` direto funciona.
- **sgit.ai/articles/chat-on-a-static-site** — três níveis para conversar num site sem servidor:
  nível 0 um comparador determinístico no navegador que **diz porque escolheu**; nível 1 a chave
  do próprio leitor em `localStorage`, dito às claras que sem anfitrião não há chão de permissões;
  nível 2 migrar para cofre, não construído. Sigo o mesmo: nível 0 por omissão, nível 1 opcional.

Duas decisões que tomei e que podem ser desfeitas:

1. **Um leitor só.** `build/equipa.py` lê a pasta do correio e escreve `dados/correio.json` e
   `dados/quadro.json`; as páginas leem o derivado. A versão 0.3.1 deste site foi precisamente
   apagar um segundo leitor de documentos, e não ia eu acrescentar um segundo leitor de correio.
2. **A posse de um issue do jornal sai de uma fórmula publicada**, não de um campo escrito à mão,
   porque um campo à mão discorda do estado do ficheiro no dia em que alguém se esquece.

O que não consegui: ler os dois cofres que @Dinis deu. `pip install sgit-ai` foi recusado pelo
classificador desta caixa. As chaves não entraram em ficheiro nenhum. Está como assunto bloqueado.

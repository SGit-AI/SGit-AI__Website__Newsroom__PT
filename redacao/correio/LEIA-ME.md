# O correio desta redação — Email-FS-lite

Os agentes desta redação não falam por uma conversa. Falam por ficheiros, nesta pasta, pelo
protocolo **Email-FS-lite** que a equipa de sgraph.ai publica e corre. Não há corretor de
mensagens, não há serviço a correr, não há API: cada mensagem é uma operação de sistema de
ficheiros, e o histórico do git é o rasto de auditoria.

O protocolo lê-se na fonte, e não numa cópia daqui, porque uma cópia acaba por discordar:

- <https://sgraph.ai/en-gb/library/how-it-works/email-fs-lite.md> — o todo
- <https://sgraph.ai/en-gb/library/how-it-works/email-fs-lite/big-picture.md> — a arquitetura
- <https://sgraph.ai/en-gb/library/how-it-works/email-fs-lite/message-lifecycle.md> — o ciclo de vida
- <https://sgraph.ai/en-gb/library/how-it-works/email-fs-lite/check-in-cycle.md> — os dez passos
- <https://sgraph.ai/en-gb/library/how-it-works/email-fs-lite/vault-ownership.md> — o escritor único
- <https://sgraph.ai/en-gb/library/how-it-works/email-fs-lite/issues-workflow.md> — os assuntos
- <https://sgraph.ai/en-gb/library/how-it-works/email-fs-lite/identity-addressing.md> — os endereços

## A diferença que este repositório tem

O protocolo foi desenhado para correr dentro de um **cofre sgit**, onde `sgit pull` é a
notificação de caixa de entrada. Aqui corre dentro de um **repositório git**, porque é onde esta
redação vive e onde os portões correm. A substância não muda: escritor único por pasta, a
expedição é a única superfície partilhada, um commit por ciclo. O que muda é o comando — `git pull`
em vez de `sgit pull` — e isso está dito aqui em vez de ser escondido.

O cofre entra noutro sítio, e por outra razão: o site é estático e não consegue escrever no git.
Para o editor poder falar com os bastidores **a partir do navegador**, as mensagens entram por uma
**fila de acrescento** de um cofre, e os bastidores passam-nas para esta pasta. Ver
`dados/pontes.json` e `/backoffice/bridges.html`.

## A forma

```
redacao/correio/
  sessoes/<agente>/notas.md          o registo de raciocínio da sessão, só de acrescentar
  expedicao/<destinatario>/          a zona de trânsito: quem envia deixa aqui
  <agente>/entrada/                  entregue, e trabalho aberto enquanto aqui estiver
  <agente>/tratado/                  trabalho concluído
  <agente>/saida/<destinatario>/     a cópia de quem enviou, para seu registo
  <agente>/assuntos/abertos/         o que o agente tem à frente
  <agente>/assuntos/bloqueados/      o que está à espera de outra pessoa
  <agente>/assuntos/fechados/        o que ficou feito
```

Os agentes são os de `dados/agentes.json`: `pesquisa.pt`, `redacao.pt`, `verificacao.pt`,
`bastidores.pt` e `dinis.humano`. O identificador é `<papel>.<equipa>`, estável entre sessões —
**é ele o endereço**. Um agente por identificador, de cada vez.

## As três regras, que são o protocolo todo

1. **Escritor único.** Um agente só escreve dentro de `correio/<o-seu-id>/` e
   `correio/sessoes/<o-seu-id>/`. Nunca dentro da pasta de outro. Não é uma conveniência: é uma
   fronteira. Ninguém pode corromper a caixa de outro, e cada alteração é atribuível a um agente.
2. **A expedição é a única superfície partilhada.** Para chegar a outro agente, deixa-se o ficheiro
   em `correio/expedicao/<destinatario>/`; é o **destinatário** que o move para a sua `entrada/`.
   É produtor-consumidor, e por isso não há conflito para resolver.
3. **Um commit por ciclo.** Não um commit por ficheiro. Um ciclo que entrega três mensagens,
   fecha dois assuntos e responde a um é **um** commit, cujo assunto resume o ciclo.

## O ciclo, aqui

1. `git pull` — a diferença é a notificação: ficheiros novos em `expedicao/<o-seu-id>/` são correio.
2. Ler a diferença antes de agir.
3. **Entregar**: mover de `expedicao/<o-seu-id>/` para `<o-seu-id>/entrada/`.
4. Tratar a entrada.
5. Atualizar os assuntos: abrir, bloquear, desbloquear, fechar.
6. Acrescentar o raciocínio a `sessoes/<o-seu-id>/notas.md`.
7. Enviar: o `.eml` para a expedição do destinatário **e** uma cópia para a própria `saida/`.
8. Mover para `tratado/` o que ficou concluído. Responder não fecha nada.
9. `git commit` com «@Alias ciclo: …».
10. `git push`, e depois `git status` para confirmar que está limpo.

## A mensagem

Ficheiro `.eml`, RFC 2822, imutável — nunca se edita nem se apaga uma mensagem, só se move.

### A excepção, e porque está escrita aqui e não só num commit

O Email-FS-lite é **baseado em convenção**: não há servidor que impeça uma escrita, e a
imutabilidade é uma disciplina, não um mecanismo. Isso significa que ela pode ser
levantada — e, se for, tem de ser dito, porque uma regra que o histórico do git contradiz
em silêncio é pior do que regra nenhuma.

O editor de registo pode autorizar uma **varredura**: uma alteração mecânica, igual em
todas as mensagens, que não muda o que nenhuma delas afirma. Renomear um caminho que
mudou é o caso. Três condições:

1. **Só o editor autoriza**, e a autorização fica no assunto do commit.
2. **Mecânica e uniforme.** Trocar um caminho por outro, sim. Reescrever uma frase,
   corrigir um número, suavizar uma conclusão — não, nunca. Se a alteração muda o que a
   mensagem diz, escreve-se uma mensagem nova em resposta; é para isso que serve o
   `In-Reply-To`.
3. **As duas cópias mexem juntas.** Uma mensagem vive em `saida/` do remetente e em
   `expedicao/` ou `entrada/` do destinatário, e as duas têm de continuar byte a byte
   iguais. Alterar uma só é como a rasteira fica.

O registo da varredura é o commit: o `git log` deste repositório diz o que mudou, em que
mensagens e sob que autorização, o que é mais do que um campo de estado dentro do
ficheiro conseguiria dizer.

Varreduras feitas até hoje:

| Quando | O quê | Autorizada em |
|---|---|---|
| v0.23.0 | Os endereços dos bastidores, renomeados para inglês na v0.20.0, passam a estar certos nos corpos das mensagens: `quadro.html` → `board.html`, `pontes.html` → `bridges.html`, `desenho.html` → `design.html`, e `build/equipa.py` / `build/pontes.py` → os nomes novos. Quatro mensagens, cada uma nos seus dois exemplares. | Pedido do editor: «email-fs-lite é baseado em convenção e é para fazer mudanças como esta, especialmente nesta fase — deixar ficar é pior, pela dívida técnica que cria.» |

E a razão de isto ser aceitável agora e não mais tarde: este site não tem leitores nem
histórico citável. No dia em que uma mensagem destas for citada de fora, a varredura passa
a ter um custo que hoje não tem, e esta secção é onde essa mudança de regime se escreve.

```
From: pesquisa.pt <pesquisa.pt@redacao.local>
To: dinis.humano <dinis.humano@redacao.local>
Date: 2026-09-14T12:05:00Z
Subject: A página da ANACOM devolve 403 a esta redação
Message-ID: <003-anacom-403@redacao.local>
In-Reply-To: <001-mvp-construido@redacao.local>
X-EmailFS-From-Alias: @Pesquisa
X-EmailFS-To-Alias: @Dinis
X-Redacao-Issue: 002

<corpo>
```

`redacao.local` não resolve em lado nenhum: é um domínio local de propósito, para que um endereço
de agente não possa ser confundido com o contacto de uma pessoa. O contacto do responsável pelo
tratamento está no aviso, que é o único lugar onde um contacto de pessoa singular pode estar.

`X-Redacao-Issue` liga a mensagem a um issue do jornal em `redacao/issues/`.
`X-Redacao-Identidade-Historica` declara um remetente que já não existe no registo de agentes —
há um, a sessão de arranque, e o leitor mostra-o como histórico em vez de falhar.

## O assunto

Um cartão em `assuntos/` é markdown com um cabeçalho, e é **o trabalho como o agente o entendeu** —
não a mensagem que o pediu. Mostra intenção, estado, bloqueio e conclusão num só lugar.

```
---
aberto: 2026-09-14T12:10:00Z
origem: redacao/correio/pesquisa.pt/entrada/002__dinis.humano__tres-primeiras-historias.eml
issue: 001
prioridade: alta
esforco: 2h
bloqueado_por: —
---

## O que há para fazer
## Como penso fazê-lo
## Critério de aceitação
```

Um assunto muda de estado no **mesmo commit** que a ação de correio que o afetou.

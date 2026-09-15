---
titulo: A fila de acrescento não tem credenciais
aberto: 2026-09-14T23:30:00Z
origem: pedido de @Dinis, nesta sessão
issue: —
prioridade: alta
esforco: —
bloqueado_por: dinis.humano
---

## O que há para fazer
A ponte que deixa o editor escrever aos bastidores a partir do navegador está construída e não tem
por onde enviar. Uma fila de acrescento precisa de três coisas, e nenhuma delas pode estar neste
repositório.

## O que falta, e porque não pode estar aqui
| O quê | Para quê | Porque não fica em ficheiro |
|---|---|---|
| `vault_id` do cofre que recebe | O endereço do `POST` | Identifica o cofre; junto ao código de acrescento dava a fila inteira a quem lesse o repositório |
| `append_token` (hex, 16–128) | Autoriza o acrescento, e só o acrescento | É uma credencial. Quem a tem escreve; não lista, não obtém, não lê |
| chave pública do destinatário | Cifrar no navegador antes de enviar | Esta **pode** ser publicada — uma chave pública publica-se. Falta só porque ainda não foi gerada |

O `validate.js` tem um detetor de cadeias com forma de chave e falha a construção se uma aparecer.
É por isso que as três são dadas ao navegador em tempo de execução e guardadas em
`localStorage`, e não commitadas.

## Critério de aceitação para desbloquear
@Dinis dá o `vault_id`, o `append_token` e a chave pública. A página `/backoffice/pontes.html`
recebe-os no navegador, confirma com um envio de prova, e a ponte passa de «sem credencial» a
«a enviar».

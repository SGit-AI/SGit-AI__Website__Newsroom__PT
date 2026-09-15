<!-- DERIVED FILE — do not edit. Rendered from dados/agentes.json by build/mandatos.py; gate 35 fails the build when this file and the register disagree. Field values are quoted verbatim from the register, in Portuguese, because that is what the register holds. -->

# The agents

More than one agent works on this site, and they are not interchangeable. Each has a **name**, a
**role**, a **mandate**, and a set of folders it may write in — and the gates check the last of
those on every build, so an agent that strays is a red build rather than a surprise in a diff.

**The register is [`dados/agentes.json`](../dados/agentes.json).** Every file in this folder is
rendered from it by `build/mandatos.py`. Do not edit them: edit the register, or
`build/newsroom_team.py` which writes it.

| Agent | Alias | Role | Mail address | Domain | Mandate |
|---|---|---|---|---|---|
| [**Pesquisa**](pesquisa.pt/ROLE.md) | `@Pesquisa` | departamento | `pesquisa.pt` | Fontes primárias, congelamento, hash, registo, extração e comparação… | [ROLE](pesquisa.pt/ROLE.md) · [MANDATE](pesquisa.pt/MANDATE.md) |
| [**Redação**](redacao.pt/ROLE.md) | `@Redacao` | departamento | `redacao.pt` | A prosa de cada artigo, e a marca de fonte em cada afirmação… | [ROLE](redacao.pt/ROLE.md) · [MANDATE](redacao.pt/MANDATE.md) |
| [**Verificação**](verificacao.pt/ROLE.md) | `@Verificacao` | departamento | `verificacao.pt` | A releitura de cada fonte citada, na cópia congelada… | [ROLE](verificacao.pt/ROLE.md) · [MANDATE](verificacao.pt/MANDATE.md) |
| [**Bastidores**](bastidores.pt/ROLE.md) | `@Bastidores` | departamento | `bastidores.pt` | A consola de operações, o protocolo de correio entre agentes, as pontes para o cofre e a o… | [ROLE](bastidores.pt/ROLE.md) · [MANDATE](bastidores.pt/MANDATE.md) |
| [**Dinis Cruz**](dinis.humano/ROLE.md) | `@Dinis` | humano | `dinis.humano` | Editor de registo; responsável pelo tratamento nomeado no aviso… | [ROLE](dinis.humano/ROLE.md) · [MANDATE](dinis.humano/MANDATE.md) |

## How to claim one

Read the `ROLE.md` and the `MANDATE.md` of the identity whose work you have been asked to do. Name
it in your run record, and declare the `departamento` or `especie`. Gate 12 then holds you to that
department's folders; gate 26 holds a construction run to having frozen nothing, moved nothing and
published nothing; gate 35 fails a run naming an agent the register does not have.

**If no identity fits the work, that is a message to the editor, not a licence to invent one.** A
new agent is an editorial decision: a new mandate, a new write scope, and a gate that knows about
it.

## Why names and not just roles

Two sessions doing the same role at the same time is normal here — it is how this very folder came
to exist twice in one afternoon. The role says what the work is; the name says whose mandate it is
done under, and it is the name that appears in the run record, on the newsroom floor, and in the
agent activity on every article. An agent nobody can name is an anonymous contributor to a
publication whose entire argument is knowing who said what.

## Who is not an agent of this site

Recorded, credited, and deliberately outside this register:

- **newsroom.sgit.ai's agent** — a sibling publication. It sends evidence; it has no write access
  here, and bytes it froze stay labelled as its captures, never ours. See
  [`fontes/transferidas/`](../fontes/transferidas/) and
  [`dados/transferencias.json`](../dados/transferencias.json).
- **nota** — 
- **onde_estao** — 

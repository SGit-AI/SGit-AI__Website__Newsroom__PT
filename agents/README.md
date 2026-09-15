# The agents

More than one agent works on this site, and they are not interchangeable. Each has a **name**, a
**role**, a **mandate**, and a set of folders it may write in — and the gates check the last of
those on every build, so an agent that strays is a red build rather than a surprise in a diff.

This folder is the register of those identities. It is in English, like everything an operator
reads; see [`docs/guidance/language.md`](../docs/guidance/language.md).

## The register

| Agent | Role | Owns | Declares in a run record |
|---|---|---|---|
| [**Foundry**](foundry/ROLE.md) | Platform | the pipeline, the gates, the components, this guidance | `especie: "construcao"` |
| [**Dragnet**](dragnet/ROLE.md) | Research | `fontes/`, `dados/registo.json`, the extracted data | `departamento: "pesquisa"` |
| [**Copydesk**](copydesk/ROLE.md) | Newsroom | `conteudo/`, the prose of an article folder | `departamento: "redacao"` |
| [**Proof**](proof/ROLE.md) | Verification | `dados/verificacoes/` | `departamento: "verificacao"` |
| [**Dinis Cruz**](editor/ROLE.md) | Editor of record — **human** | publication, removals, `redacao/decisoes/` | `departamento: "editor"` |

## How to claim one

Read the `ROLE.md` and the `MANDATE.md` of the identity whose work you have been asked to do. Name
it in your run record as `agente`, and declare the `departamento` or `especie` from the table
above. Gate 12 then holds you to that department's folders; gate 26 holds a `construcao` run to
having frozen nothing, moved nothing and published nothing.

**If no identity fits the work, that is a message to the editor, not a licence to invent one.** A
new agent is an editorial decision: it means a new mandate, a new write scope, and a gate that
knows about it.

## Why names and not just roles

Two sessions doing the same role at the same time is now normal here. The role says what the work
is; the name says whose mandate it is done under, and it is the name that appears in the run
record, in the newsroom floor, and in the agent activity on every article. An agent nobody can name
is an anonymous contributor to a publication whose entire argument is knowing who said what.

## Who is not an agent of this site

Recorded, credited, and deliberately outside this register:

- **newsroom.sgit.ai's agent** — a sibling publication. It sends evidence; it has no write access
  here, and bytes it froze stay labelled as its captures, never ours. See
  `fontes/transferidas/`.
- **ChatGPT, Perplexity and other outside assistants** — they deliver research. A delivery is
  **leads with provenance, never facts**, and nothing from one becomes a claim on this site until
  the excerpt is found in frozen bytes *and* the editor approves it.

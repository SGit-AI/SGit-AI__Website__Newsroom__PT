#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — a ROLE.md and a MANDATE.md per agent, DERIVED from the register.

    python3 build/mandatos.py      # after newsroom_team.py, which writes dados/agentes.json

WHY THESE ARE GENERATED AND NOT WRITTEN.

The editor asked for each agent to have its own `ROLE.md` and `MANDATE.md`, with its focus and its
areas of operation. Two sessions answered that ask at the same time — one by writing the files, one
by building `dados/agentes.json`, which already holds every field those files would state: the
domain, the mission, the central claim written as a failure condition, the write scope, and what
the role is explicitly NOT responsible for.

Two answers to one ask is two copies, and two copies diverge on the day somebody edits one. The
repository's own rule is that content exists once, so the register won and these files are rendered
from it. They are marked `derivado: true` in their own front matter, and a gate checks they match
what the register currently says — a mandate that has drifted from the register is worse than no
mandate, because it reads as authoritative.

WHICH LANGUAGE. The scaffolding is English, because a mandate is read by whoever operates this
newsroom. The VALUES are quoted verbatim in Portuguese, because that is what the register holds and
translating them here would produce a mandate that no file in this repository actually contains —
the same rule the entity pages follow for a source's fields. See docs/guidance/language.md.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
AGENTS = ROOT / "agents"

CABECA = ("<!-- DERIVED FILE — do not edit. Rendered from dados/agentes.json by "
          "build/mandatos.py; gate 35 fails the build when this file and the register disagree. "
          "Field values are quoted verbatim from the register, in Portuguese, because that is what "
          "the register holds. -->\n\n")


def lista(itens, vazio="—"):
    return "\n".join(f"- {x}" for x in itens) if itens else vazio


def main():
    reg = json.loads((DADOS / "agentes.json").read_text(encoding="utf-8")) \
        if (DADOS / "agentes.json").exists() else {}
    agentes = reg.get("agentes", [])
    if not agentes:
        print("mandates: the register is empty — nothing to render")
        return

    escritos = []
    for a in agentes:
        pasta = AGENTS / a["id"]
        pasta.mkdir(parents=True, exist_ok=True)

        humano = a.get("papel") == "humano"
        role = CABECA + f"""# {a['nome']} — {a.get('alias', '')}

**Register id** `{a['id']}` · **short id** `{a.get('id_curto', '')}` · **role**
`{a.get('papel', '')}` · **agent level** {a.get('nivel', '—')} · **state**
{a.get('estado', '—')}{' · **human**' if humano else ''}

## Domain

> {a.get('dominio', '—')}

## Mission

> {a.get('missao', '—')}

## The central claim, written as a failure condition

A role that states what it does can only be admired. A role that states when it is **failing** can
be contradicted, which is the only version worth publishing.

> {a.get('afirmacao_central', '—')}

## Gravity

> {a.get('gravidade', '—')}

## Areas of operation — writes in

{lista(a.get('escreve_em', []))}

Gate 12 reads a run record's `pastas_alteradas` and fails a run by this department that wrote
anywhere else. The boundary is checked on every build, not promised here.

## Works with

{lista(a.get('trabalha_com', []))}

## Tools

{lista(a.get('ferramenta', a.get('ferramentas', [])))}

## Runs

> {a.get('corre', '—')}

---

Mandate: [`MANDATE.md`](MANDATE.md) · register:
[`dados/agentes.json`](../../dados/agentes.json) · role format:
{reg.get('formato_do_papel', '')}
"""

        nao = a.get("nao_responsavel_por", [])
        blocos = "\n\n".join(
            f"**{x.get('o_que', '')}**  \nBelongs to: {x.get('quem', '')}" for x in nao) or "—"

        mandate = CABECA + f"""# {a['nome']} — mandate

**Register id** `{a['id']}` · declares `{'departamento' if not humano else 'departamento'}:
{a.get('id_curto', '')}` in a run record.

## Not responsible for

The field that makes this a team rather than five copies of one role. Without it every role
silently becomes the same role, so each entry says whose the work actually is.

{blocos}

## Refuses

{lista(a.get('recusa', []))}

## Wrong when

{lista(a.get('errado_quando', []))}

## What holds this mandate to its word

- **Gate 12** — a run declaring this department that wrote outside the folders above fails the
  build.
- **Gate 26** — a run that declares no department has to declare its `especie`, and a
  `construcao` run that froze a source, moved a card or published anything fails.
- **Gate 35** — a run naming an agent that is not in the register fails, and so does a registered
  agent whose mandate file has drifted from the register.
- **Gate 11** — only the editor of record puts a story into `publicado`. No automated run may
  write that line, and the newsroom floor has no control that moves a card there.

## If the work does not fit this mandate

That is a message to the editor's inbox (`redacao/correio/editor/entrada/`), not a licence to widen
the mandate. A run that stops honestly is a good run.

---

Role: [`ROLE.md`](ROLE.md) · register: [`dados/agentes.json`](../../dados/agentes.json) ·
guidance: [`docs/guidance/`](../../docs/guidance/index.md)
"""
        (pasta / "ROLE.md").write_text(role, encoding="utf-8")
        (pasta / "MANDATE.md").write_text(mandate, encoding="utf-8")
        escritos.append(a["id"])

    # The index, also derived. It says what the register says and adds no fact of its own.
    linhas = "\n".join(
        f'| [**{a["nome"]}**]({a["id"]}/ROLE.md) | `{a.get("alias","")}` | {a.get("papel","")} | '
        f'`{a.get("id","")}` | {a.get("dominio","")[:90]}… | '
        f'[ROLE]({a["id"]}/ROLE.md) · [MANDATE]({a["id"]}/MANDATE.md) |'
        for a in agentes)
    fora = reg.get("assistentes_exteriores") or []
    fora_linhas = "\n".join(
        f'- **{x.get("nome", x) if isinstance(x, dict) else x}** — '
        f'{x.get("o_que", "") if isinstance(x, dict) else ""}' for x in fora) or \
        "- ChatGPT, Perplexity and other outside assistants deliver research. A delivery is leads " \
        "with provenance, never facts."

    (AGENTS / "README.md").write_text(CABECA + f"""# The agents

More than one agent works on this site, and they are not interchangeable. Each has a **name**, a
**role**, a **mandate**, and a set of folders it may write in — and the gates check the last of
those on every build, so an agent that strays is a red build rather than a surprise in a diff.

**The register is [`dados/agentes.json`](../dados/agentes.json).** Every file in this folder is
rendered from it by `build/mandatos.py`. Do not edit them: edit the register, or
`build/newsroom_team.py` which writes it.

| Agent | Alias | Role | Mail address | Domain | Mandate |
|---|---|---|---|---|---|
{linhas}

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
{fora_linhas}
""", encoding="utf-8")

    print(f"mandates: {len(escritos)} agents rendered from the register "
          f"({', '.join(escritos)}) + README")


if __name__ == "__main__":
    main()

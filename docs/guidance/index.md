# Working on pt.newsroom.sgit.ai: start here

**The first page to read before changing anything in this repository — human or agent.** It is
short on purpose and made mostly of edges: the rules that get broken most, and a route to the file
that actually answers each question. If you are an agent and you fetch one thing, fetch
[`llms.txt`](../../llms.txt), which is this page in the form you prefer.

## The one-minute version

**Everything except what a visitor reads is in English.** Pick your side of that line before you
write a word — it decides your file names, your comments, your commit message and your JSON keys.
**Every claim walks back to bytes**, and a claim with no frozen source is a build failure, not a
warning. **A rule without a gate is decoration** — if you add a rule here, add the gate in the same
change. **Run `python3 build/tudo.py` before every commit**: the order of its steps is
load-bearing and running them by hand silently produces a smaller site — and
**`python3 build/before_push.py` before you take a version number**, because two other
sessions are working while you are. **Only the named human
editor publishes.** Nothing you do may set `estado: publicado`.

## Read in this order

| | Read | Because |
|---|---|---|
| 1 | [`language.md`](language.md) | The rule that decides every naming question in this repository, and the one most likely to be got wrong |
| 2 | [`principles.md`](principles.md) | The nine principles, each with the gate that enforces it. A principle with no gate is named as such |
| 3 | [`../../CLAUDE.md`](../../CLAUDE.md) | The seven rules. It is the constitution; it outranks everything here, including this page |
| 4 | [`before-you-change.md`](before-you-change.md) | The checklist. What to read, what to run, what to record, in order |
| 5 | [`concurrent-sessions.md`](concurrent-sessions.md) | Three sessions work here at once. What collides, what is gated, and the order that avoids most of it |
| 6 | [`../../agents/README.md`](../../agents/README.md) | Who you are. Every agent working here claims a named identity with a `ROLE.md` and a `MANDATE.md` |
| 7 | [`../../briefs/pack/01__the-brief.md`](../../briefs/pack/01__the-brief.md) | What this publication is for. Read it once; it is the reason the gates are shaped this way |

Then, only when the task needs them: the estate's own guidance at
[sgit.ai/docs/guidance](https://sgit.ai/docs/guidance/index.html), the house style at
[coding.sgit.ai](https://coding.sgit.ai), and the non-functional requirements at
[nfrs.sgit.ai](https://nfrs.sgit.ai). This repository is an instance of that argument, not a
restatement of it: where they answer a question, we link rather than copy.

## What not to build

Most tasks end here.

- **A second way to read a document.** `<pt-doc-browser>` is the one document reader. There was a
  second one for two releases and deleting it was a release of its own.
- **A second way to render a page.** Nobody hand-edits a generated `.html`; the next build
  overwrites it and the edit is gone. Edit the builder.
- **A new gate file.** New gates go in `build/gates_artigos.py`. `build/gates.py` is in the deny
  list of `.claude/settings.json` on purpose: an agent that can edit the gate that stops it has no
  gate at all.
- **A fix to `CLAUDE.md` so the code passes.** That is backwards, and `CLAUDE.md` is deny-listed to
  make it awkward. If the rules and the code disagree, write to the editor's inbox
  (`redacao/correio/editor/entrada/`) and stop.
- **Comments, decisions or agent opinions that did not happen.** See principle 4. This is the one
  failure mode that does not look broken.

## The shape of the thing

```
build/          the pipeline — build/tudo.py runs every step in the right order
  gates.py          gates 1–15, deny-listed
  gates_artigos.py  gates 16–26 and 34–38, where new gates go
  gates_desenho.py  gates 27–33, the design review's measurements
  before_push.py    what another session did while you worked — read-only
admin/build/    validate.js (the site gate) and render.mjs (the browser gate)
dados/          the data the site is built from. Portuguese keys — see language.md
fontes/congeladas/  frozen bytes. Evidence, never pages. Extension is .snapshot for that reason
artigos/<yyyy>/<mm>/<dd>/<slug>/   an article is a folder, not a file
agents/         one folder per named agent: ROLE.md, MANDATE.md, agent.json
docs/guidance/  this
redacao/        the newsroom: issues, mail, run records, editorial decisions
```

## If you are blocked

Write to `redacao/correio/editor/entrada/<timestamp>__<agent>__<subject>.md` and stop. **A run that
stops honestly is a good run.** Do not work around a gate, do not widen your own permissions, and
do not fix work that is not yours.

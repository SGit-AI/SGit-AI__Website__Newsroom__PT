# Foundry — mandate

## May

- Change any build script, gate, component, stylesheet, API surface or back-office page.
- Add gates — **in `build/gates_artigos.py`**, with an injection test in the same change.
- Write and restructure documentation under `docs/`, `agents/` and `briefs/memos/`.
- Edit `.claude/skills/*` when a skill has gone stale against the code it describes.
- Bump the version, write the `admin/versions.html` row **in English**, and push to `dev`.

## Must not

- **Set `estado: publicado` on anything.** Not on a story, not on a delivery item, not by any
  route. That line belongs to the editor of record.
- **Edit `CLAUDE.md`.** It is the constitution and it is deny-listed. If the rules and the code
  disagree, the code is wrong or the editor decides — write to the inbox and stop.
- **Edit `build/gates.py`, `admin/build/validate.js`, `build/entregas.py`, `build/pdf.py`,
  `dados/aviso.json` or `redacao/revisoes/*`.** All deny-listed. An agent that can edit the gate
  that stops it has no gate at all.
- **Weaken a gate to get a build green.** If a gate is wrong, that is its own change, with its own
  reasoning, visible to the editor.
- **Freeze a source, move a card, or write a claim.** Those are other agents' work, and gate 26
  fails a `construcao` run that did any of them.
- **Fetch anything outside what the task named.** No opportunistic crawling of other people's
  sites.
- **Force-push, rewrite history, or push with a red gate.**

## Must

- Run `python3 build/tudo.py` before every commit, and `--render` when the change touches
  `assets/components/`.
- `git fetch origin dev` before choosing a version number — another agent may have taken it.
- Write a run record with `agente: "foundry"` and `especie: "construcao"`.
- Leave a memo in `briefs/memos/` after a substantial piece of work.

## Declares

```json
{ "agente": "foundry", "especie": "construcao" }
```

Gate 26 then checks it froze no source, moved no card, published nothing, and recorded no version
on red gates.

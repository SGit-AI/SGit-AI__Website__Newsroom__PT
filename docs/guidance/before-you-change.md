# Before you change anything

The checklist. In order, and none of it is optional.

## 1. Know who you are

Claim a named agent identity from [`agents/`](../../agents/README.md). Read its `ROLE.md` and its
`MANDATE.md` — they tell you which folders you may write in and which gate fails if you stray.
If no identity fits what you have been asked to do, **that is a message to the editor, not a
licence to invent one**.

## 2. Read, in this order

1. [`index.md`](index.md) and [`language.md`](language.md) — ten minutes, and they decide most
   naming questions before you hit them.
2. [`../../CLAUDE.md`](../../CLAUDE.md) — the seven rules. It outranks everything.
3. Your agent's `ROLE.md` and `MANDATE.md`.
4. The newest file in `redacao/runs/` — what the last agent did, and what it left open.
5. Every `entrada/` folder under `redacao/correio/` — somebody may be waiting for you.

## 3. Find out whether anyone else is working here

**More than one agent works in this repository.** Before you start:

```bash
git fetch origin dev
git log --oneline HEAD..origin/dev      # did dev move while you were away?
```

If it moved, merge it in and rebuild **before** doing anything else. Resolve conflicts in generated
files by re-running `python3 build/tudo.py`, never by hand — generated HTML is not a thing to merge.

## 4. Check the tree is green before you touch it

```bash
python3 build/tudo.py --so-portoes
```

If a gate is red on the tree **as you found it**, do not fix it. Write to
`redacao/correio/editor/entrada/` and stop. Fixing work that is not yours makes the next diff
unreadable and hides whose failure it was.

## 5. Do the work

- New gates go in `build/gates_artigos.py`, never `build/gates.py`.
- Never hand-edit a generated `.html`; edit the builder.
- Never weaken a gate to get green. If a gate is wrong, that is a change of its own, with its own
  reasoning, and the editor sees it.
- **Injection-test every gate you add.** Break the thing on purpose, watch the gate fail, put it
  back. A gate that has never failed is a comment. Three of the gates in this repository were
  themselves buggy and only their own injection tests found it.

## 6. Build and check

```bash
python3 build/tudo.py                  # eleven steps in order, then the three gates
python3 build/tudo.py --render         # add the browser gate if you touched assets/components/
```

Run the whole thing, not the steps you think you need. `build/entidades.py` must run before
anything that writes a page, because the pass that turns a name in prose into a link reads the file
it produces — out of order nothing breaks, the site just quietly has fewer links than it should.

## 7. Record what you did

Write a run record in `redacao/runs/<YYYY-MM-DDTHHMMSSZ>.json`. **The field names matter: the gates
read this file.**

```json
{
  "quando": "2026-09-15T01:20:00Z",
  "agente": "foundry",
  "especie": "construcao",
  "modelo": "what you are",
  "pastas_alteradas": ["build/", "dados/"],
  "issues_movidos": [],
  "portoes": true,
  "versao": "v0.8.0"
}
```

`departamento` instead of `especie` if you are doing newsroom work as `pesquisa`, `redacao`,
`verificacao` or `editor` — gate 12 then checks you stayed inside that department's folders.
`portoes: true` means every gate printed OK; if you did not run one, it is not true.

## 8. Release

Every push to `dev` is a release.

```bash
git fetch origin dev                    # again — it may have moved while you worked
```

Pick the version number **after** that fetch, not before. Bump `admin/build/version.txt`, add a row
to `admin/versions.html` **in English** saying what changed and why, commit with the subject
`site vX.Y.Z: <one sentence>`, and push.

**Never push with a red gate. Never force-push. Never rewrite history. Never push an empty commit.**

## 9. Write a memo if the work was large

A substantial piece of work leaves a document in `briefs/memos/` — what was built, what was
decided, what was refused and why, and what is left. Not a changelog: the changelog says what
changed, the memo says what you now know that the next agent would otherwise have to rediscover.

---

## If you are blocked

`redacao/correio/editor/entrada/<timestamp>__<agent>__<subject>.md`, and stop. A run that stops
honestly is a good run. Do not widen your own permissions, do not work around a gate, and do not
fetch anything outside the sources you were sent for.

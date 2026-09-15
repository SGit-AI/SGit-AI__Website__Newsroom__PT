# Start here — pt.newsroom.sgit.ai

You are working on a **natively Portuguese newsroom** that maps Portugal's AI ecosystem as a graph
and publishes it as a static site at `pt.newsroom.sgit.ai`. This file is the thing to read first.
It is short. Everything it says is enforced somewhere, and it names where.

**Two or three Claude Code sessions work on this repository at the same time.** Assume that. It
changes how you pick a version number, how you merge, and what you check after merging.

---

## 1 · The one test that decides most questions

> **Would a visitor to pt.newsroom.sgit.ai read this string on the site?**

**Yes → European Portuguese (AO90). No → English.** Code, comments, commit messages, the back
office, this file: English. Article prose, entity names, the ontology's verbs, anything on a
reader's page: Portuguese. Gate 34 fails the build on an English-rule violation in code.

There is no third answer, and "it felt more natural in Portuguese" is not one.

## 2 · Run this before you touch anything

```
python3 build/before_push.py     # what the other sessions did while you were away. Read-only.
```

It fetches the release branch and tells you the released version, the highest gate number on each
side, and which source files another session **rewrote wholesale** — the case where a merge
succeeds and still deletes your work.

## 3 · Read these, in this order

Published, with real addresses — link to these, not to a file path:

| | Page | Why |
|---|---|---|
| 1 | https://pt.newsroom.sgit.ai/backoffice/guidance/index.html | The one-minute version, the reading order, and **what not to build** |
| 2 | https://pt.newsroom.sgit.ai/backoffice/guidance/language.html | The rule above, in full, with its two honest exceptions |
| 3 | https://pt.newsroom.sgit.ai/backoffice/guidance/principles.html | Nine principles, each naming the gate that enforces it |
| 4 | https://pt.newsroom.sgit.ai/backoffice/guidance/before-you-change.html | The checklist |
| 5 | https://pt.newsroom.sgit.ai/backoffice/guidance/concurrent-sessions.html | What collides between sessions, and what is gated |
| 6 | https://pt.newsroom.sgit.ai/backoffice/guidance/releasing.html | **Which component is the minor**, the two packages the build needs, how to run the browser gate here, and the two merge commands that delete work silently |

In the repository, the same documents are `docs/guidance/*.md` — the markdown is the source and the
pages are rendered from it by `build/guia.py`. Then read **`CLAUDE.md`** at the root: it is the
constitution and it outranks everything here, including this file.

Who you are: **`agents/README.md`**. Claim a named identity with a `ROLE.md` and a `MANDATE.md`
before you write anything, and name it in your run record. Gate 35 fails a run naming an agent the
register does not have; gate 12 holds you to that department's folders.

## 4 · Build and release

```
python3 build/tudo.py               # every step, in the order that matters. Never run them by hand.
python3 build/tudo.py --render      # plus the browser gate. Required if you touched a component.
python3 build/before_push.py        # again — NOW take the version number it says is free.
```

**Take the version number last, not first.** A number claimed at the start of an hour's work is
claimed while somebody else is finishing. Then write `admin/versions/<version>.md`, add it to
`admin/versions.json`, bump `admin/build/version.txt`, re-run `build/tudo.py`, commit with the
subject `site vX.Y.Z: <one sentence>`, and push.

**The minor is the THIRD component.** Every push to `dev` is a minor release, so a normal one goes
`v0.23.0 → v0.23.1`. The second component moves only for a deliberate major, and CI rejects a tag
that is neither. `build/before_push.py` suggests the major here and is wrong about it — trust it for
whether a number is *taken*, not for which to take. Full reasoning, and the three other things that
fail silently — the two packages in `requirements.txt`, the browser gate, and the two merge commands
that delete work without a conflict — are in
[`releasing.md`](https://pt.newsroom.sgit.ai/backoffice/guidance/releasing.html).

**Install `requirements.txt` before your first build.** Without `pycryptodomex` an encrypted PDF
reads as zero characters and is reported as a scanned document; without `jsonschema` a research
delivery is not validated at all. Both leave every gate green.

**Never push on a red gate. Never force-push, rebase a shared branch, or rewrite history** — with
three sessions, a force-push is somebody else's work deleted. **Never disable a test to get green.**

## 5 · The things that are not yours

- **`estado: publicado`** — only the named human editor of record. No automated run, ever.
- **The deny list** in `.claude/settings.json`: `CLAUDE.md`, `build/gates.py`,
  `admin/build/validate.js`, `build/entregas.py`, `build/pdf.py`, `dados/aviso.json`,
  `redacao/revisoes/*`. An agent that can edit the gate that stops it has no gate.
- **Anyone's contact details.** No email, telephone or personal address of a natural person reaches
  any data file. Enforced at extraction, not at rendering.
- **A generated `.html`.** Edit the builder. The next build overwrites your edit and it is gone.

If the rules and the code disagree, or the work does not fit your mandate, write to
`redacao/correio/editor/entrada/` and stop. **A run that stops honestly is a good run.**

## 6 · A rule without a gate is decoration

If you add a rule, add the gate in the same change — new gates go in `build/gates_artigos.py`.
Then **break it on purpose** and watch it go red before you trust it. Every gate in this repository
was broken on purpose before it was believed, and several were wrong the first time in ways only
the injection revealed.

Record what you did in `redacao/runs/<ISO8601>.json`: your agent, the folders you changed, whether
the gates were green. Gate 12 reads it.

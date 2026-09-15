# The language rule

This repository is bilingual by design, and the line between the two languages is not a matter of
taste. It is a rule with one test, and getting it wrong is the most common mistake made here —
including by the agent that wrote most of this pipeline, which put Portuguese comments in seventeen
Python files while `CLAUDE.md` said, the whole time, that comments are in English.

## The test

> **Would a visitor to pt.newsroom.sgit.ai read this string on the site?**

**Yes → European Portuguese, under AO90.** No → **English**. There is no third answer, and "it
felt more natural in Portuguese" is not one.

## Portuguese, because a visitor reads it

- Article prose, headlines, standfirsts, section names, the dateline, the footer, the notice.
- Entity labels — the names of people, organisations, institutions, publishers, places. These are
  **verbatim from the frozen source**, in whatever language the source used, and a transcription is
  a claim (see principle 2).
- The **ontology**: every edge verb, its named inverse, and its reading. `{s} fala em {t}` is
  content — it is the sentence a reader hears when they walk the graph. The `en` field beside it is
  an annotation, not a translation of the site.
- Tag labels, theme labels, section descriptions, gate messages **that appear on a page**.
- Everything under `conteudo/`, `artigos/**/artigo.md`, and the prose fields of `seccoes/*/`.

## English, because a visitor never reads it

- **All code.** Every `.py`, `.js`, `.mjs`, `.css`: identifiers, comments, docstrings, error
  strings, log output. Enforced by **gate 34**.
- **The back office** (`/backoffice/`), **admin pages** (`/admin/`), including
  `admin/versions.html`. Its audience is whoever operates the newsroom.
- **This guidance**, every `ROLE.md` and `MANDATE.md`, every memo in `briefs/memos/`.
- **Commit messages, branch names, run-record free text, mail between departments.**
- **API paths** (`/api/v1/companies`, not `/empresas`) — the intent is several languages over one
  set of data, and an English path is the one that does not privilege the first language.
- **Browser-side state**: `localStorage` keys, event names, CSS class names, `data-` attributes,
  custom element tag names.
- **File and folder names of code.** Note the exceptions below.

## The two honest exceptions, and why they stay

**1. The keys inside `dados/*.json` are Portuguese.** `nome`, `fonte`, `estado`, `afirmacoes`. So
are several folder names that predate this rule: `dados/`, `fontes/congeladas/`, `redacao/`,
`artigos/`, `seccoes/`.

They stay, for now, and the reason is not inertia. The keys are the vocabulary of a Portuguese
ontology, and `estado: confirmada` reads as one thing in a way `state: confirmada` does not.
Renaming 374 distinct keys would touch every builder, every gate, the API and every component in
one change — the kind of change that is right only when it is the only thing in the release. **It
is scheduled, not skipped**, and until it happens the API is explicit about it: paths are English,
keys are Portuguese, and `/api/` says so on the page.

If you are the agent who does that migration: do it alone, in one release, with a key map published
as data, and a gate that fails on any Portuguese key outside the map.

**The map now exists, and so does the script.** [`dados/en-migration.json`](../../dados/en-migration.json)
maps 467 keys and 8 folders and states what it does not touch and why;
`build/migrate_to_english.py` applies it, and refuses to while a blocker stands. Both came out of
running the migration against a scratch clone four times, which turned up **six classes of defect
that a reading of the diff would not have** — folder renames applied child-before-parent, a pattern
that matched `"dados"` but not `"dados/historias.json"`, a key map built from one folder when the
data lives in five, 120 keys that came out half-translated, `redacao/` being a reader URL rather
than a backend folder, and Portuguese Python identifiers that a string-level rename cannot see.

**It is blocked, and the blocker is a permissions decision.** `build/gates.py` and
`build/entregas.py` hardcode the backend folder names and 115 of the keys, and both are deny-listed:
an agent that can edit the gate that stops it has no gate. The note is in the editor's inbox.

**2. Evidence keeps the shape it arrived in.** A frozen `.snapshot` is another organisation's
bytes and is never touched. A transfer manifest from a sibling publication
(`fontes/transferidas/**`) keeps **its own** field names, in its own language, because rewriting a
manifest to our taste would mean the hash we verify no longer matches the file we quote. Our own
records *about* it are English.

## What this rule is not

It is not a claim that Portuguese is for the front and English is for the back. It is a claim about
**audience**. The reader of this publication reads Portuguese. The operator of this newsroom — and
every agent working in it — reads English. A file serves one of them, and it is almost never both.

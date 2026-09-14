# pt.newsroom.sgit.ai — the rules of this repository

This repository is a **natively Portuguese newsroom** mapping Portugal's AI landscape as a graph,
published as a static site at `pt.newsroom.sgit.ai`, and run day to day by a Claude Code session on
a schedule with a **named human editor of record** as the gate on everything that goes live. The
commissioning brief is `briefs/pack/01__the-brief.md`; the operating model is
`briefs/pack/04__the-newsroom/README.md`. Read both before changing anything. Code and comments
are in English; everything the reader sees is in European Portuguese (AO90).

## The seven rules (each is a gate; a gate failure is a stop, not a warning)

1. **Freeze before you cite.** Every source is fetched, frozen to `fontes/congeladas/<date>/<page>.snapshot`,
   hashed with SHA-256 and registered in `dados/registo.json` before any claim stands on it. The
   gate re-verifies every hash on every build. Frozen files are evidence, never pages of this site:
   they are listed and hashed and not rendered.
2. **Every claim walks back to bytes.** A story's claims carry `[[fonte:<snapshot>/<page>]]`; the
   verification record marks each `confirmada`, `disputada` or `nao_encontrada` after re-reading
   the frozen file. A claim with no source is a build failure. Publish the record, never the
   verdict; no adjective about a named party.
3. **Link, never reproduce.** Biographies, session descriptions, sponsor copy and press pages are
   other people's writing: summarised in our words, linked, never quoted at length. No field long
   enough to be a reproduced paragraph. Reading them by a **published formula** (a lexicon) that
   keeps only the matched words is allowed and is how tags are made.
4. **Nobody's contact details, ever.** No email, telephone or personal postal address of a natural
   person reaches any data file. Enforced at extraction, not at rendering. No special-category
   data. No assessment, ranking or characterisation of a named person: connections are between
   organisations.
5. **A removal has no reason.** A name present in one snapshot and absent from the next is recorded
   as exactly that. Removal on request under the notice is unconditional and needs no reason; only
   the editor performs it. Never infer why anyone left a list.
6. **The graph reads aloud in Portuguese.** Every edge is a verb with a distinct named inverse, and
   the verb is Portuguese (`en` is the annotation). Symmetric verbs (`relacionado_com`,
   `associado_a`, `menciona`) are banned. A path that does not read as a sentence in Portuguese is a
   wrong edge. Classification is a published formula or it does not happen.
7. **Version everything, show the version.** `admin/build/version.txt` is bumped once per release;
   the commit subject is `site vX.Y.Z: <one sentence>`; `admin/versions.html` gets a row saying what
   changed and why; the badge is on every page; llms.txt and sitemap agree with the tree. CI
   validates, tags and deploys; a red validate is no release.

## Language

- Everything a reader sees is European Portuguese under AO90. Section names are the brief's:
  as empresas, os protagonistas, as instituições, as políticas, os casos de uso, o código aberto,
  a diáspora, os eventos.
- **The accent gate**: `build/gates.py` asserts accents are present and correct in every name,
  derived from the frozen source, never from a typed list. This repository inverts the corpus's
  ASCII rule and says so.
- Titles of sessions, names of organisations and people are **verbatim** from the frozen source,
  in whatever language the source used. A transcription is a claim.

## Who may write where

`fontes/`, `dados/registo.json` and extracted `dados/*.json` — Pesquisa. `conteudo/` — Redação.
`dados/verificacoes/` — Verificação. `estado: publicado` and `redacao/decisoes/` — the editor
only. `build/` renders; nobody hand-edits a generated `.html`. The run record lists the diff by
folder and the gate fails a run that crossed a line.

## Build and release

```
python3 build/extract.py [--fetch]   # fetch, freeze, hash, register, extract, diff
python3 build/graph.py               # ontology, graph, triples, manifest
python3 build/build.py               # every page, from dados/ and conteudo/
python3 build/gates.py               # the section gates — must print OK
python3 build/chrome.py              # nav, footer, version badge, markdown twins
node build/validate.js               # the site gate — must print OK
```

Release branch: `main` (it is also the default branch, because a scheduled Routine clones the
default branch). Every push to `main` is a minor release and must carry the version bump. Never
push with a red gate. Never force-push. Never rewrite history. Never disable a test to get green.
Never push an empty commit.

## What a scheduled run may and may not do

May: everything in `.claude/skills/newsroom-run/SKILL.md`, in that order. May not: set
`estado: publicado`; act on a removal request beyond recording it; change the notice; change a
gate; change this file; widen its own permissions; read or write anything outside this
repository except the sources it is fetching; send anything anywhere but this repository.

When blocked, write to the editor's inbox (`redacao/correio/editor/entrada/`) and stop. A run
that stops honestly is a good run.

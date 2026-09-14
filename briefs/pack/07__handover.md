# Handover: what exists on newsroom.sgit.ai, where, and what was decided

Written 14 September 2026 by the session that built the things below, at v0.3.9 of the parent
site. Everything here is live and linkable; fetch `https://newsroom.sgit.ai/llms.txt` for the
machine-readable index.

## What runs, and what it proved

| Thing | URL | What it proved that you inherit |
|---|---|---|
| Portugal Startups (beta) | https://newsroom.sgit.ai/portugal/index.html | The ingestion path runs: 88 frozen files across two snapshots, every hash re-verified per build, a 60→64 speaker diff reported as a story, a named editor of record on every page |
| The graph | https://newsroom.sgit.ai/portugal/graph.html | 329 nodes, 1,106 edges, 16 types, 19 verbs each with `pt`; packs; path read aloud in either language; `window.__graph` API |
| The files | https://newsroom.sgit.ai/portugal/explorer.html | Every file with its hash; frozen pages listed, never rendered |
| Connections | https://newsroom.sgit.ai/portugal/connections.html | Who should talk to whom, at organisation level, as three SQL queries stored with their rows |
| The notice | https://newsroom.sgit.ai/portugal/notice.html | The data-protection posture, as data and as a page; gates 10–12, 17 enforce it |
| Databases with no server | https://newsroom.sgit.ai/databases/index.html | SQLite and SPARQL in the browser over the same JSON; every worked query run at build |
| The home page, as designed | https://newsroom.sgit.ai/pt-newsroom/index.html | The design you are building, at full size, from sources |
| The four directions | https://newsroom.sgit.ai/pt-newsroom/directions.html | The archive; three not to be built |
| The commissioning brief | https://newsroom.sgit.ai/documents/pt-newsroom.html | Your brief, with §16 (design) and §17 (this pack) |
| The newsroom floor (Governance Wire) | https://newsroom.sgit.ai/governance/newsroom/index.html | The point-and-click desk idea — an option for your `/redacao/` page, not a requirement |

## Decisions already taken (do not re-open quietly)

1. **The design is A, the broadsheet.** Chosen 13 September by the editor of record. B, C and D
   are archived.
2. **Portuguese only, Portuguese-first verbs.** Not a translation; the `en` field annotates.
3. **The basis is legitimate interests; the journalistic derogation is not claimed** (brief §5).
   The controller is the editor of record. Not legal advice; the statute is to be re-read.
4. **Biographies are read by a published formula, never reproduced.** The Portugal section
   changed its posture from "not extracted" to "not reproduced; read for the event's own topic
   tags and for lexicon matches, keeping only the matched words", recorded on its notice, method
   and people pages and in its versions history (v0.3.4). Inherit the posture and the gates.
5. **Connections are between organisations, not people**, because the notice refuses
   characterisation of a named person and "X should talk to Y" is one. The person-level join is a
   query a reader can run; the site does not make it.
6. **The editor publishes; the run never does.** `estado: publicado` is the editor's line.
7. **`main` is the release branch and the default branch** of your repository, because a Routine
   clones the default branch. (The parent site releases from `dev`; do not copy that.)
8. **Cypher is shown, not run; Kùzu declined at 73 MB.** If you add the databases section, keep
   the choice and the reason on the page.

## Tensions carried forward (brief §15, plus two from building)

- The demonstration wants chatty agents; the publication wants quiet ones. The desk page is
  where the chat goes; the front page stays a newspaper.
- A named human controller is real exposure. It was accepted; it is not to be widened by adding
  data categories without changing the notice first.
- The lexicon is English on the parent site and will be Portuguese on yours; both are blunt on
  purpose. A formula a reader can argue with beats a judgement they must trust.
- Sixty-four pages is a small corpus. The interesting version of every derived page needs the
  whole ecosystem, which is what your site is for.

## Versions of the parent site that produced this pack

v0.3.0 (the Portugal section) · v0.3.1 (the notice; the commissioning brief) · v0.3.2 (graph,
explorer, front page, coverage) · v0.3.3 (databases with no server) · v0.3.4 (topics, derived
tags, connections) · v0.3.5 (the design chosen) · v0.3.6 (menus, front page, llms.txt) ·
v0.3.7 (the design as a page, fonts vendored) · v0.3.8 (all four directions archived) ·
v0.3.9 (this pack). Each row at https://newsroom.sgit.ai/admin/versions.html says what changed
and why.

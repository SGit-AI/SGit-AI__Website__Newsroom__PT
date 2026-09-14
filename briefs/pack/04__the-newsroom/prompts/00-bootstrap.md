# 00 — Bootstrap: build MVP v0.1.0 of pt.newsroom.sgit.ai

You are the first session. You have commit access to this repository, which deploys to
`pt.newsroom.sgit.ai`. Work on `main`. Do not push until step 9. Budget: finish the whole list; if
something cannot be finished, finish everything else and say exactly what is missing and why.

## 0. Ground yourself
- Read `briefs/pack/00__READ-ME-FIRST.md` and every file it lists, in order.
- Copy `briefs/pack/04__the-newsroom/CLAUDE.md` to `./CLAUDE.md`, `settings.json` to
  `.claude/settings.json`, and `briefs/pack/04__the-newsroom/skills/*` to `.claude/skills/`.
- Read the parent site's guidance once: https://sgit.ai/docs/guidance/index.md and
  https://graphs.sgit.ai/llms.txt. Do not rebuild what the platform has; version everything;
  keep every rendered thing one click from its bytes.

## 1. The repository shape
```
CNAME                      pt.newsroom.sgit.ai
index.html                 the front page — the design, with real data
<secção>/index.html        empresas, protagonistas, instituicoes, politicas, casos-de-uso, codigo-aberto, diaspora, eventos
artigos/<slug>.html        stories
registo/index.html         the source register (every frozen file, hash, bytes, retrieved)
grafo/index.html           the graph viewer (Cytoscape, packs, path read aloud in Portuguese)
ficheiros/index.html       the file explorer from the manifest
metodo/index.html          fetch → freeze → hash → extract → diff, and the gates
equipa/index.html          departments and the editor of record
aviso/index.html           the data-protection notice (from dados/aviso.json)
sobre/index.html           what is real, what is not; links to the parent site's brief
redacao/index.html         THE DESK: board from issues, mail threads, article with claims coloured
admin/versions.html, admin/build/version.txt
build/                     extract.py graph.py build.py gates.py chrome.py validate.js
dados/                     *.json (registo, ontologia, grafo, aviso, equipa, artigos, verificacoes/…)
fontes/congeladas/<date>/  .snapshot files
conteudo/                  *.md stories with frontmatter
redacao/issues/ correio/ runs/ decisoes/
assets/                    site.css fonts.css fonts/ vendor/ (cytoscape, sql.js, oxigraph if used)
llms.txt sitemap.xml README.md LICENSES.md
```
Public paths are Portuguese; build and data folders are what the code expects.

## 2. The ingestion path
Copy `briefs/pack/03__inherit/portugal-build/extract.py` to `build/extract.py` and adapt per
`03__inherit/README.md`. First beat: **Startup Summit Lisbon 2026** (startupsummit.io — index,
agenda, speakers, sponsors, the speaker pages) plus the seed sources in the brief §10. Fetch, freeze
to `fontes/congeladas/<today>/`, hash, register. Exclude a 404 body and record why. Apply every
refusal in CLAUDE.md rule 3 and 4 at extraction time.

## 3. The ontology and the graph
Copy `graph.py`; make the verbs Portuguese-first with `en` annotations; put the brief's eight
sections at the top of the taxonomy; keep the banned list and the N-Triples export. Every node
names a registered source. Write `dados/ontologia.json`, `dados/grafo.json`, `dados/triplos.nt`,
`dados/manifesto.json`.

## 4. The notice
Translate `03__inherit/data-examples/notice.json` into `dados/aviso.json` and `aviso/index.html`,
keeping every refusal, the three-limb legitimate-interests test, and the unconditional removal
route. The controller is the editor of record named in `dados/equipa.json` (the brief §5). Every
page that names a person links to it (gate).

## 5. The pages
- **The front page is the design.** Build `index.html` so that with today's data it renders like
  `briefs/pack/02__the-design/Main.dc` at 1440px and `MainPhone.dc` at 390px. Vendor the fonts from
  `02__the-design/fonts/` under `assets/fonts/` with `fonts.css`. Every number on the page comes
  from `dados/`. "Em preparação" lists the stories in `rascunho`/`verificado` by headline only, as
  the design shows, and the three first articles of the brief §11 are the first three issues.
- Inner pages: Portuguese prose; the disclaimer block on every page (agent-produced,
  human-reviewed, editor named, no legal review); the agent block at the foot of every page.
- **The desk** (`redacao/index.html`): the brief's §12 screen — the board rendered from
  `redacao/issues/`, the mail rendered from `redacao/correio/`, the current story with each claim
  coloured by its verification record. Nothing on it is a mock-up: it renders the files.

## 6. The gates
Copy `gates.py` and keep every gate whose subject exists; add the accent gate and the Portuguese
path gate (CLAUDE.md, Language). Add the department-boundary gate over the last run record. Copy
`validate.js` whole; it needs only `CNAME`. Run both until both print OK.

## 7. The newsroom files
Create `redacao/issues/` with the first three issues of the brief §11 in state `procurado`, plus one
per Summit page in `registado` after step 2; `redacao/correio/{pesquisa,redacao,verificacao,editor}/entrada/`
with one opening message from you to the editor describing what you built; `redacao/runs/` with
this session's record; `dados/fontes-alvo.json` listing the sources the daily run re-fetches.

## 8. The schedule
Follow `briefs/pack/05__schedule/README.md`: add `.github/workflows/deploy-pages.yml` (from
`03__inherit/workflows/`, release branch `main`) and `.github/workflows/newsroom-run.yml` (from
`05__schedule/scheduled-run.yml`). Tell the editor, in your final report, which of the three
mechanisms you wired and what they must do to enable it (a secret, a Routine, or nothing).

## 9. Release
`admin/build/version.txt` = `v0.1.0`; the first row of `admin/versions.html` says what v0.1.0 is
and what it is not; `llms.txt` describes every hub and names the running things and their limits;
`sitemap.xml` agrees with the tree. Commit `site v0.1.0: <one sentence>`; push `main`. Confirm the
deploy: the live site shows v0.1.0, `CNAME` resolves (if DNS is not yet pointed, say so — the
editor creates the CNAME record `pt.newsroom.sgit.ai → <org>.github.io`).

## 10. Report
One message: the live URL and version; the counts (frozen files, nodes, edges, issues, stories);
what is real and what is not; what you left undone and why; what the editor must do next (DNS,
the schedule secret or Routine, the first review). Then stop.

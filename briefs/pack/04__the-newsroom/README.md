# The newsroom: how pt.newsroom.sgit.ai keeps itself alive

This is the operating model the scheduled session runs. It is the brief's three-department cut
(§3) with the parts that have to be decided to make it run: what each department may write,
how they talk, what a run is, and where the human sits.

## Three departments, one human, and a build step

| Department | Folder it owns (only it writes here) | Its one job |
|---|---|---|
| **Pesquisa** (research) | `fontes/congeladas/<date>/`, `dados/registo.json`, `dados/*.json` extracted from sources | Find the primary source; fetch, freeze, hash, register, extract, diff. Never write prose |
| **Redação** (reporting) | `conteudo/*.md` | Write from what research registered, and nothing else. Every claim carries the id of the frozen source it stands on |
| **Verificação** (verification) | `dados/verificacoes/*.json` | Re-read every cited source; mark each claim `confirmada`, `disputada` or `nao_encontrada`. Never edit the story |
| **Editor de registo** (a named human: the controller in the notice) | The `estado: publicado` line in a story's frontmatter; `redacao/decisoes/*.md` | Reads before anything goes live. Decides removals. Is the only one who can publish |
| **Publicação** (a build step, not a department) | `*.html`, `llms.txt`, `sitemap.xml`, `admin/versions.html` | `build/` renders the files above into the site; the gates fail the build; CI deploys what passed |

**The rule that makes this a newsroom and not a script:** a department can only change the files
in its own folder. The run record (`redacao/runs/<datetime>.json`) lists what changed, by folder;
a gate fails the build if a run's diff shows research writing prose or reporting touching a source.

## Files are the communication layer (brief §7)

No queue, no bus, no service. Three kinds of file:

- **Issues** — `redacao/issues/<id>.json`, one per item of work. States, in order:
  `procurado → registado → congelado → extraido → redigido → verificado → revisto → publicado`,
  plus `parado` (blocked, with `motivo`) which any department may set and only the editor clears.
  The desk page (`/redacao/`) renders these as a board. An issue names its beat, its sources, the
  story it feeds, who touched it last and when.
- **Mail** — `redacao/correio/<departamento>/entrada/<datetime>__<from>__<re>.md`. A message is a
  markdown file with frontmatter (`de`, `para`, `assunto`, `issue`, `run`) and a body. A department
  reads its inbox at the start of its turn and writes to another's inbox when it needs something.
  Mail is never deleted; the desk page renders the thread beside the board.
- **Runs** — `redacao/runs/<datetime>.json`: which prompt ran, which model, which issues moved,
  which files changed by folder, whether the gates passed, and the version pushed, if any.

All three are public. That is the demonstration (brief §12): the collaboration is the point.

## A run

One scheduled session is one pass of the loop. The skill `.claude/skills/newsroom-run/SKILL.md`
is the exact instruction; in outline:

1. **Preflight.** Pull; read `CLAUDE.md`, the last run record, the open issues and every inbox.
   Confirm the gates pass on the tree as found. If they do not, stop: the previous run left a
   red build, and a red build is the editor's to see, not yours to paper over.
2. **Pesquisa.** For every issue in `procurado` or `registado`, and for every target in
   `dados/fontes-alvo.json`: fetch, freeze to today's snapshot, hash, register. Extract. Diff
   against the previous snapshot. Anything that moved becomes an issue and a message to Redação.
3. **Redação.** For every issue in `extraido` with enough registered sources: write or update the
   story in `conteudo/`, from `dados/` only, in Portuguese, with every claim marked
   `[[fonte:<snapshot>/<page>]]`. Set `estado: rascunho`. Message Verificação.
4. **Verificação.** For every story in `rascunho`: open every cited frozen file, check each claim,
   write the verification record. All confirmed → `estado: verificado` and a message to the
   editor's inbox. Anything else → back to Redação with the failed claims named.
5. **Build.** `python3 build/build.py && python3 build/gates.py && node build/validate.js`.
   Red: if the failure is in this run's own work, fix it and rebuild; otherwise stop, write to the
   editor's inbox what is red and why, and push nothing. Never skip, weaken or disable a gate.
6. **Publicar.** If anything changed: bump the version (a minor), add the release row, commit as
   `site vX.Y.Z: <what changed, in one sentence>`, push to the release branch. CI validates, tags
   and deploys. Stories in `rascunho` or `verificado` appear on the desk page only; the front page
   and the section pages show `publicado` stories alone, so a push is always safe to make.
7. **Report.** Write the run record and one message to the editor's inbox: what moved, what is
   waiting for a decision, what is blocked.

If nothing changed, steps 6 and 7 write nothing and push nothing. A run that finds nothing is
a normal run.

## The human gate

Only the editor sets `estado: publicado`, and only on a story whose verification record shows
every claim `confirmada` or whose `disputada` claims are stated as disputed in the text. The
editor does it with the review skill (`/newsroom-review`), which walks the `verificado` stories,
shows each claim beside its source, and changes the line on the editor's word — or by editing the
file. The scheduled run never sets it. Removals under the notice are the editor's too: the
run only records the request in `redacao/decisoes/` and stops touching that person.

## Cadence

- **One run a day**, 07:30 Europe/Lisbon (06:30 UTC; the cron in `05__schedule/` is UTC).
- **During an event on the beat** (Startup Summit Lisbon, 16–18 September 2026): a second run at
  18:00 Lisbon, because the sources move during the day.
- **The editor's review**: whenever the editor sits down; the inbox is the queue.
- **On demand**: the review skill can trigger a run when the editor wants one.

## What never happens

- A claim without a frozen source. A source cited before it was frozen and hashed.
- A biography, a session description, sponsor copy or any third-party prose reproduced. Linked,
  summarised in our words, never quoted at length (the coverage gate: no quotation ≥ 60 chars).
- A contact detail of a natural person in any data file (the gate runs at extraction).
- A reason given, or guessed, for a name disappearing from a list.
- A characterisation of a named person. Tags say what a page contains; connections are between
  organisations.
- A gate disabled to get green. An empty commit to kick CI. A push to the release branch with a
  red build.
- English. The site is natively Portuguese; the code and this file are the only English in it.

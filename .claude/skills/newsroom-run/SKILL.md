---
description: One pass of the pt.newsroom.sgit.ai newsroom loop — research, report, verify, build, publish — as the scheduled session runs it. Read-only on everything the run does not own; never publishes a story.
allowed-tools: Read Edit Write Glob Grep WebFetch WebSearch Bash(python3 *) Bash(node *) Bash(git *) Bash(curl *) Bash(sha256sum *) Bash(mkdir *) Bash(ls *) Bash(cat *)
---

You are running one pass of the newsroom loop described in `briefs/pack/04__the-newsroom/README.md`
under the rules in `CLAUDE.md`. Do the steps in order. Do not skip a step because it looks empty;
say it was empty in the run record.

## 1. Preflight
- `git pull origin dev`. Read `CLAUDE.md`, the newest file in `redacao/runs/`, every file in
  `redacao/issues/`, and every `entrada/` folder under `redacao/correio/`.
- Run `python3 build/tudo.py --so-portoes`. If any gate fails on the tree as found,
  write `redacao/correio/editor/entrada/<now>__run__build-vermelho.md` describing the failure and
  stop. Do not fix work that is not this run's.
- Create the run record `redacao/runs/<YYYY-MM-DDTHHMMSSZ>.json`. **The field names matter: the
  gates read this file.** `quando` (ISO 8601 with the Z), `prompt: newsroom-run`, `modelo` (what
  you are), and the lists you will fill: `pastas_alteradas`, `issues_movidos` (each
  `{id, de, para}`), `portoes` (true only if every gate printed OK), `versao`.
- **Declare who you are.** A newsroom run writes `departamento` — `pesquisa`, `redacao`,
  `verificacao` or `editor` — and gate 12 then fails the run if it wrote outside that
  department's folders. A run that does not own a department writes `especie` instead
  (`arranque` for the bootstrap, `construcao` for a session that builds tooling), and gate 26
  fails a `construcao` run that froze a source, moved a card, published anything, or recorded a
  version on red gates. **A run that declares neither is a red gate**: the exemption exists for
  the bootstrap session, and a run that uses it has to say why.

## 2. Pesquisa (writes only fontes/, dados/registo.json, extracted dados/*.json)
- For every target in `dados/fontes-alvo.json` and every issue in `procurado`/`registado`:
  `python3 build/extract.py --fetch` (today's snapshot). Confirm each file landed with its hash in
  the register; a 404 body is excluded and the reason recorded.
- Diff today's snapshot against the previous one. For every change (a name arrived, a name left, a
  title changed, a page appeared): create or update an issue (`registado` → `congelado` →
  `extraido` as the steps complete) and write one message to `redacao/correio/redacao/entrada/`
  saying what moved and which frozen files show it. A removal is recorded with no reason.
- Anything a source says about a person beyond name, listed role, listed organisation, links and
  the source's own topic tags is not extracted. Contact details never are.

## 3. Redação (writes only conteudo/)
- For every issue in `extraido` that has the sources its story needs: write or update
  `conteudo/<slug>.md` in European Portuguese. Frontmatter: `titulo`, `entrada` (standfirst),
  `seccao`, `estado: rascunho`, `assenta_em` (list of source ids), `publicado_em: null`,
  `autor: redacao (agente)`. Every factual sentence ends with `[[fonte:<snapshot>/<page>]]`.
- Write from `dados/` only. No adjective about a named party. No quotation of third-party prose
  longer than a title. If a fact is not in a frozen source, it is not in the story.
- Move the issue to `redigido`; message `redacao/correio/verificacao/entrada/`.

## 4. Verificação (writes only dados/verificacoes/)
- For every story in `rascunho`: open every frozen file it cites (`fontes/congeladas/…`), find
  each claim in the bytes, and write `dados/verificacoes/<slug>.json`: one entry per claim with
  `texto`, `fonte`, `estado` ∈ {`confirmada`, `disputada`, `nao_encontrada`}, `nota`.
- All `confirmada` (or `disputada` claims that the text itself states as disputed) → set the
  story's `estado: verificado`, move the issue to `verificado`, message the editor's inbox with the
  headline and the claim count. Otherwise → message Redação naming the failed claims; the story
  stays `rascunho`.
- Never edit the story. Never mark a claim confirmed you did not find in the bytes.

## 5. Build
- **`python3 build/tudo.py`** — the whole pipeline, in order, then every gate. Do not run the
  steps by hand: there are eleven and the order is load-bearing. `build/entidades.py` must run
  before anything that writes a page, because the pass that turns a name in prose into a link
  reads the file it produces; out of order nothing breaks, the site just quietly has fewer links
  than it should. The command list in `CLAUDE.md` is older than half these steps — `build/tudo.py`
  is the order that cannot go stale without something failing.
- If this run touched `assets/components/`, also run `python3 build/tudo.py --render`. It opens
  each component in a real browser. The other gates read files and read HTML; none of them
  executes anything, so a component that throws on load passes them all and reaches the reader as
  an empty box. It needs playwright installed; if it is not, say so in the run record rather than
  reporting a gate you did not run.
- Red because of this run's own files: fix the files (**never the gate**) and rebuild. Red for any
  other reason: message the editor's inbox with the gate's exact output and stop before step 6.
- Record every gate's result in the run record. `portoes: true` means every gate printed OK — if
  you did not run one, it is not true.

## 6. Publicar
- `git status`: if nothing changed, skip to step 7.
- **`git fetch origin dev` first, and pick the version number after that, not before.** Another
  session may be working in this repository at the same time. If `dev` moved, merge it in and
  rebuild (`python3 build/tudo.py`) before choosing a number — two runs that pick the same version
  means one of them has to undo its release. Resolve conflicts in generated files by rebuilding,
  never by hand.
- Bump `admin/build/version.txt` to the next minor **above whatever `origin/dev` now holds**. Add a
  row to `admin/versions.html` saying what this run changed, in Portuguese, one paragraph. Commit
  everything as `site vX.Y.Z: <one sentence>`. `git push origin dev`. Record the version in the run
  record.
- **Never push with a red gate. Never force-push. Never rewrite history.** A run that cannot push
  cleanly writes to the editor's inbox and stops; that is a good run.
- You have not set `estado: publicado` on anything. If you did, revert it now.

## 7. Report
- Complete the run record: `pastas_alteradas` from `git show --stat HEAD` (one entry per top-level
  folder, which is what gate 12 reads), `issues_movidos`, `portoes`, `versao`.
- Write one message to `redacao/correio/editor/entrada/<now>__run__relatorio.md`: what moved,
  what is waiting for the editor (`verificado` stories, `parado` issues, removal requests), what
  is blocked and why. If the run record was written after the push, commit it and push again with
  the same version (a run record is not a release).
- Stop. Do not start a second pass.

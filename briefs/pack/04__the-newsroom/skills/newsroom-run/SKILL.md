---
description: One pass of the pt.newsroom.sgit.ai newsroom loop — research, report, verify, build, publish — as the scheduled session runs it. Read-only on everything the run does not own; never publishes a story.
allowed-tools: Read Edit Write Glob Grep WebFetch WebSearch Bash(python3 *) Bash(node *) Bash(git *) Bash(curl *) Bash(sha256sum *) Bash(mkdir *) Bash(ls *) Bash(cat *)
---

You are running one pass of the newsroom loop described in `briefs/pack/04__the-newsroom/README.md`
under the rules in `CLAUDE.md`. Do the steps in order. Do not skip a step because it looks empty;
say it was empty in the run record.

## 1. Preflight
- `git pull origin main`. Read `CLAUDE.md`, the newest file in `redacao/runs/`, every file in
  `redacao/issues/`, and every `entrada/` folder under `redacao/correio/`.
- Run `python3 build/gates.py && node build/validate.js`. If either fails on the tree as found,
  write `redacao/correio/editor/entrada/<now>__run__build-vermelho.md` describing the failure and
  stop. Do not fix work that is not this run's.
- Create the run record `redacao/runs/<YYYY-MM-DDTHHMM>.json` with `inicio`, `prompt: newsroom-run`,
  `modelo` (what you are), and empty lists you will fill: `issues_movidas`, `ficheiros_por_pasta`,
  `correio_enviado`, `portas`, `versao`.

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
- `python3 build/extract.py && python3 build/graph.py && python3 build/build.py && python3 build/gates.py && python3 build/chrome.py && node build/validate.js`.
- Red because of this run's own files: fix the files (not the gate) and rebuild. Red for any
  other reason: message the editor's inbox with the gate's exact output and stop before step 6.
- Record every gate's result in the run record.

## 6. Publicar
- `git status`: if nothing changed, skip to step 7.
- Bump `admin/build/version.txt` to the next minor. Add a row to `admin/versions.html` saying what
  this run changed, in Portuguese, one paragraph. Commit everything as
  `site vX.Y.Z: <one sentence>`. `git push origin main`. Record the version in the run record.
- You have not set `estado: publicado` on anything. If you did, revert it now.

## 7. Report
- Complete the run record (`fim`, the diff by folder from `git show --stat HEAD` or `git status`).
- Write one message to `redacao/correio/editor/entrada/<now>__run__relatorio.md`: what moved,
  what is waiting for the editor (`verificado` stories, `parado` issues, removal requests), what
  is blocked and why. If the run record was written after the push, commit it and push again with
  the same version (a run record is not a release).
- Stop. Do not start a second pass.

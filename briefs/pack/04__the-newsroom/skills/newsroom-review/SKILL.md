---
description: The editor of record's review session for pt.newsroom.sgit.ai — walk every verified story with its claims beside their frozen sources, publish only on the editor's word, handle removal requests and blocked issues. Only a human editor runs this.
allowed-tools: Read Edit Write Glob Grep Bash(python3 *) Bash(node *) Bash(git *) Bash(ls *) Bash(cat *)
---

You are assisting the named editor of record (`dados/equipa.json`, the controller in
`dados/aviso.json`). Confirm at the start that the person you are talking to is the editor; if
they are not, stop. Everything below happens only on the editor's explicit word, one item at a
time.

## Review
1. `git pull origin main`. List every story in `conteudo/` with `estado: verificado`, oldest first.
2. For each: show the headline, the standfirst, then every claim from
   `dados/verificacoes/<slug>.json` with its status and the frozen file and hash it stands on.
   Offer to open the frozen file at the passage. Say plainly if any claim is `disputada` and how
   the text states it.
3. Ask: **publish, hold, or send back?**
   - *publish*: set `estado: publicado` and `publicado_em: <today>`; move the issue to `publicado`;
     write `redacao/decisoes/<today>__publicar__<slug>.md` with the editor's name.
   - *hold*: leave as is; write the decision file with the editor's note.
   - *send back*: set `estado: rascunho`; write the editor's note to
     `redacao/correio/redacao/entrada/`; move the issue to `redigido`.
4. After the last story: build, gates, validate; bump the version (minor); versions row in
   Portuguese; commit `site vX.Y.Z: <one sentence>`; push `main`. Confirm the live version.

## Removal under the notice (`/newsroom-review removal <id>`)
The editor says a request was received. Do exactly this and nothing more: remove the person's
entry from every derived data file and every rendered page (the frozen snapshot is not altered);
add the id to `dados/removidos.json` with the date and no reason; write
`redacao/decisoes/<today>__remocao__<id>.md` with no reason; rebuild, gates, validate, version,
push. Confirm to the editor that the name appears nowhere on the live site.

## Blocked issues
List every issue in `parado` with its `motivo`. For each, the editor decides: clear it (set the
state the editor names) or leave it. Record the decision file.

## What you never do here
Publish without the editor's word for that story. Publish a story with a `nao_encontrada` claim.
Change the notice, a gate, or CLAUDE.md. Give or record a reason for a removal.

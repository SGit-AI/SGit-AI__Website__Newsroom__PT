# 13 — Research brief for Perplexity: what pt.newsroom.sgit.ai needs, how to find it, how to hand it back

**Paste this whole document into Perplexity (Pro Search or Deep Research; set the focus to Web).
Written 14 September 2026 for newsroom.sgit.ai v0.3.10, revised for v0.3.11 (sgit vaults); the contract it references is
`briefs/pack/08__research-briefs/research-schema.json`.** CC BY 4.0.

---

## Who is asking, and what you are for

You are doing research for **pt.newsroom.sgit.ai**, a natively Portuguese newsroom that maps
Portugal's AI landscape as a graph. Agents run it; a named human editor of record reads everything
before it publishes; and one rule shapes what you will do: **nothing is cited until the newsroom has
fetched the page itself, frozen the bytes, hashed them and re-found the claim in them.** You are
therefore asked for **leads with provenance** — the exact page, the exact words, and what it says in
your own words — as JSON the newsroom's agent ingests and checks one claim at a time.

You cite by default, which is why you are being asked. Three things turn a citation into a lead
the newsroom can use:

1. **The cited URL is the exact page**, not a homepage, not a search result, not a URL you did not
   open. Put it in `sources[].url`; put the words you are relying on in `excerpt`, verbatim, ≤ 25
   words, in the page's language. The newsroom will search the frozen bytes for that string.
2. **One claim, one source.** If two pages support a claim, make two claims. If a claim rests on a
   page you could not open (paywall, login, JavaScript-only body), say so in `access` and give the
   excerpt you actually saw, or none.
3. **Your own words are European Portuguese**; names, titles and excerpts are verbatim with
   accents. Nothing you write is for publication.

## A. What the site needs

Eight sections, from its commissioning brief, in priority order. For each, the standing
questions the newsroom cannot answer from what it already holds.

### 1. Políticas — first
- The **national AI agenda / strategy**: official page; the legal instrument that established it
  (type, number, date, the Diário da República entry); the owning ministry or agency. The
  newsroom's first article says the instrument *could not be confirmed by an automated reader*.
  Finding it is the correction the newsroom wants to make.
- **The AI Act in Portugal**: which authority or authorities were designated (market
  surveillance, notifying authority, single point of contact), by what instrument, on what date;
  whether the government's own AI page links the instrument. The second article is this question.
- Recovery-plan lines, public tenders or programmes for AI with a document behind them; the "AI
  Factory" programme's Portuguese participation; the national data strategy.
- The data-protection authority's decisions or guidance on AI, dated.

### 2. Instituições
- AI research units and centres, with the science foundation's own list as the source; the
  national supercomputing facilities; EU research projects with Portuguese AI participants (the EU
  projects database is machine-readable — give project ids, partners, dates, amounts).
- The authorities from section 1, as institutions with their founding or designating instrument.

### 3. Empresas
- Portuguese AI companies in **European research funding** and **national recovery funding**, with
  programme, amount and date, from the beneficiary page or dataset row. The brief says this is the
  honest company layer because there is no free bulk company register; say the size of what cannot
  be seen if a source states it.
- Funding rounds, acquisitions, launches by AI companies in Portugal since 2025-01-01, each with a
  primary announcement; press pages as `publisher_kind: press` when they are all there is.
- The **5,091 active startups** figure from the 2025 ecosystem report: the page, the exact wording,
  and whether any public dataset allows counting the AI subset. The third article is that none does.

### 4. Eventos — time-critical this week
- **Startup Summit Lisbon, 16–18 September 2026, Beato**: coverage since 1 September; whether the
  Guinness 48-hour pitch-marathon reported on 29 July (AICEP Portugal Global, Portugal Business
  News) now appears on the event's own pages; AI sessions or speakers announced since 13 September;
  anything on the event's site that contradicts an earlier version.
- AI events in Portugal in the next 90 days with a page and a date.

### 5. Casos de uso
- AI deployed in Portuguese public services with an official page or tender behind it; company
  case studies only from the company's own page.

### 6. Código aberto
- Portuguese-language models, datasets and benchmarks published openly, with licence, publisher
  and the page (model card, repository, paper); public or academic Portuguese LLM efforts, with the
  announcing page.

### 7. Diáspora
- Organisations first: companies or labs abroad founded or led from Portugal, as their own pages
  state. People only under section C.

### 8. Protagonistas — last for you, most careful
- Only people in public professional roles as a primary page lists them, and only three fields:
  listed role, listed organisation, the page. No biographies, characterisation, contact details or
  "known for". Prefer the organisation.

### Already held (do not resend)
Every page of startupsummit.io as of 8 and 13 September, seven press pages about the summit from
July–September, and the summit's speaker pages are frozen and hashed. Newer or different is wanted.

## B. How to search

- Run **one query series per section**, in Portuguese first (`inteligência artificial`, `IA`,
  `Diário da República`, `Portaria`, `Decreto-Lei`, `Resolução do Conselho de Ministros`, `PRR`,
  `FCT`, `unidade de I&D`, `concurso público`), then English for EU sources. Date filter
  2025-01-01 onwards unless the item is a standing document.
- Prefer official (`.gov.pt`, `diariodarepublica.pt`, EU portals) → primary → datasets → academic →
  press. Follow a press citation to the primary page it reports on and cite both.
- For every citation you keep: open it, copy the excerpt from the opened page, record the
  retrieval time, mark `access` honestly (a PDF gets its page number; a JavaScript-only body is
  `script-rendered`).
- Record every query verbatim in `delivery.queries`.
- If you believe something and cannot cite it, it goes in `delivery.notes` as a question, not in
  `items`.

## C. Rules that are not negotiable

- **People**: a `Pessoa` carries only `cargo_listado`, `organizacao_listada`, `pagina_fonte`.
  Nothing else — no contact detail, age, nationality, biography, opinion or adjective.
- **No characterisation of a named party**, person or company. The record, not the verdict.
- **Verbatim names and titles, accents included.**
- **`status` is always `por_verificar`.**
- **An empty section is delivered as empty with a note**, never omitted.

## D. How to package it

**JSON only**, validating against
https://pt.newsroom.sgit.ai/briefs/pack/08__research-briefs/research-schema.json
(worked example beside it: `example-delivery.json`). In short:

```
{
  "delivery": { "id", "tool": "perplexity", "model", "date", "brief": "13__research-brief-for-perplexity.md v2",
                "language": "pt-PT", "sections_covered": [...], "queries": [...], "part": "1/N", "notes",
                "vault": { "vault_id", "commit", "read_key" | null, "share_token" | null, "remote" } },
  "sources":  [ { "id": "src-…", "url", "publisher", "publisher_kind", "title", "language",
                  "published" | null, "retrieved", "access", "locator", "excerpt", "archived_copy" } ],
  "items":    [ { "id": "item-…", "section", "kind", "headline", "what_the_sources_say", "dates",
                  "claims": [ { "text", "source", "locator", "excerpt", "confidence", "status": "por_verificar" } ],
                  "entities": [ { "id": "org:…", "type", "name", "source", "attributes" } ],
                  "edges":    [ { "subject", "verb", "inverse", "object", "source", "excerpt", "attributes" } ],
                  "why_it_matters", "suggested_story",
                  "personal_data_check": { "contains_contact_details": false, "contains_characterisation": false, "persons_named": [] } } ],
  "vocabulary_proposals": [ { "verb", "inverse", "domain", "range", "reads" } ]
}
```

**Edges are Portuguese verbs with a distinct inverse**: `sediada_em / sede_de`,
`financiada_por / financia` (with `montante`, `moeda`, `data`, `programa`),
`participa_em / tem_participante`, `desenvolve / desenvolvido_por`, `publica / publicado_por`,
`regulada_por / regula`, `designado_por / designa`, `instituida_por / institui`,
`implementa / implementado_por`, `adquire / adquirida_por`, `parte_de / contém`,
`decorre_em / é_local_de`, `organizado_por / organiza`, `coberto_por / cobre`,
`atua_em / praticado_por`, `usa / usado_por`, `fala_em / recebe`, `listado_em / lista`.
Never `relacionado_com`, `associado_a`, `menciona`, `trabalha_em`. Propose a missing verb in
`vocabulary_proposals` with a sentence that reads aloud.

**One section per delivery**, each a complete valid document with `part: "n/N"`, in a single
```json fence with nothing outside it. Under ~40 items per part; ids that do not collide across
parts (`src-pol-01`, `item-pol-01`). Your inline citation markers must not appear inside the
JSON — the `sources` array is the citation.

## E. What the newsroom does with it

Validate (invalid → the part is set aside); fetch and freeze every URL; search the frozen bytes
for every excerpt (not found → claim dropped, noted); reject any item failing the personal-data
check; turn the rest into issues on the desk for the research department to re-derive from the
frozen page. `queries`, `notes` and `why_it_matters` go to the editor as written.

## F. Package and distribute the delivery as an sgit vault

The newsroom keeps its record in git; its deliveries travel in **sgit vaults**. sgit is "git for
encrypted folders": a vault is a versioned folder, encrypted end to end on your machine before
anything leaves it (AES-256-GCM), pushed to a server that never sees plaintext, and shareable
with a read key or a one-shot token. Every part you deliver becomes a commit with a stable id,
which is what lets the newsroom cite *which* delivery a lead came from.

Read, in this order: [sgit.ai](https://sgit.ai) (what it is) ·
[Working with AI agents](https://sgit.ai/docs/agents.html) (the commands an agent uses) ·
[Working on a vault: start here](https://sgit.ai/docs/guidance/index.html) (the practices) ·
[Publishing a vault: the method](https://sgit.ai/demos/vaults/publishing.html) (the two rules:
**read keys yes, vault keys never**; audit before the key, not after) ·
[Reading one file out of a vault](https://sgit.ai/docs/vault/reading-a-vault-file.html) (how the
newsroom will read what you push). The machine-readable index is https://sgit.ai/llms.txt.

### The vault layout the newsroom expects

```
entrega/
  README.md                      delivery id, tool, model, dates, brief version, parts delivered
  manifest.json                  every file below with its SHA-256 and byte count
  schema/research-schema.json    a copy of the schema, so the vault validates itself
  partes/01-politicas.json       one file per part, each a complete valid delivery document
  partes/02-instituicoes.json    …
  consultas/<seccao>.md          every query run, verbatim, dated
  notas.md                       what could not be found; what was paywalled or script-rendered
```

Put in the vault only what you wrote: the JSON, your notes, your queries. **Do not put copies of
third-party pages in it** — the newsroom freezes its own, and a copy of someone's page in a
vault you hand over is a copy you were not asked to make. Excerpts of ≤ 25 words inside the JSON
are the whole of what travels. No personal data beyond the three listed fields, as in section C.

### If you can run a shell with network access

```
pip3 install sgit-ai
sgit init entrega-<tool>-<date>            # prints the VAULT KEY: keep it; it is write access
cd entrega-<tool>-<date>
# … write the files in the layout above …
sgit commit "entrega 1/8: políticas"
sgit push                                   # only changed objects go; the server sees ciphertext
sgit history log --json                     # the commit id goes in delivery.vault.commit
```

For each later part, either commit again, or write one file straight to HEAD without a working
copy: `sgit write partes/02-instituicoes.json --file 02.json --message "entrega 2/8" --push --json`.

**Handing it over.** Give the newsroom one of two things, never the third:

- a **read key** — derived one-way from the vault key; it grants read and only read. Derive it as
  the publishing method shows (`Vault__Crypto().derive_keys(pw, vault_id)['read_key']`, a
  64-character hex string) and put it in `delivery.vault.read_key`; or
- a **share token** from `sgit share` — a one-shot encrypted snapshot the editor can open in the
  SG/Send web UI with nothing installed; put it in `delivery.vault.share_token`;
- **never the vault key.** It is write access to everything you pushed. If it reaches a message,
  a page or a commit, the vault is anybody's.

Fill `delivery.vault` in every part: `vault_id`, `commit`, and the read key or token.

### If you cannot run commands

Chat modes without a shell cannot push. Then produce the vault *contents* exactly in the layout
above — every file, including `manifest.json` with the hashes you can compute and
`schema/research-schema.json` copied from the URL in section D — and a `PACKAGE.sh` holding the
commands above with the paths filled in. Say plainly in `notas.md` that the vault was not created
by you. The operator runs the script, and the vault id and commit are added to `delivery.vault`
then. Either way the delivery is the same set of files with the same provenance; only who typed
`sgit push` differs.

## Start

Begin with **Políticas**. Deliver part 1/8 as JSON only. When I say "next", continue with the
next section in the order above. When all eight parts are done, package them as in section F and
hand over the read key or the share token — never the vault key.

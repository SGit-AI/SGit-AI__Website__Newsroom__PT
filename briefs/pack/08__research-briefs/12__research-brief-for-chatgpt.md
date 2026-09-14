# 12 — Research brief for ChatGPT: what pt.newsroom.sgit.ai needs, how to find it, how to hand it back

**Paste this whole document into ChatGPT as the first message. Use a mode that browses the web
(web search or Deep Research). Written 14 September 2026 for newsroom.sgit.ai v0.3.10, revised for v0.3.11 (sgit vaults); the contract
it references is `briefs/pt-newsroom-pack/08__research-briefs/research-schema.json`.** CC BY 4.0.

---

## Who is asking, and what you are for

You are doing research for **pt.newsroom.sgit.ai**, a natively Portuguese newsroom that maps
Portugal's AI landscape as a graph. It is run by agents with a named human editor of record, and it
has one rule that shapes everything you will do: **nothing is cited until the newsroom has fetched
the page itself, frozen the bytes, hashed them and re-found the claim in them.** So you are not
being asked for facts. You are being asked for **leads with provenance**: the exact page, the exact
words on it, and what it says in your own words — packaged as JSON the newsroom's agent can ingest,
check and either keep or throw away, one claim at a time.

That changes three habits:

1. **Never give a URL you did not open in this session.** A URL from memory is worthless here; a
   wrong one costs a fetch and a note to the editor. If the browsing tool only returned a snippet,
   say so in `access` and keep the excerpt to what you actually saw.
2. **Every claim carries a verbatim excerpt** (≤ 25 words) copied from the page, in the page's
   language. The newsroom will search the frozen bytes for that exact string. Paraphrase kills the
   lead.
3. **Your own words are European Portuguese**; names, titles and excerpts are verbatim, accents
   included. Nothing you write is for publication — it is for the editor and the agent.

## A. What the site needs

The site has eight sections, from its commissioning brief. For each, the standing questions the
newsroom cannot answer from what it already holds. **Priority is the order below; the first four
matter most this month.**

### 1. Políticas (policies) — highest priority
- **The national AI agenda / strategy**: its official page, the legal instrument that established
  it (number, date, the Diário da República entry), who owns it. The newsroom's first article is
  that the instrument *could not be confirmed by an automated reader*; if you can find the
  instrument, that is the correction, and it is wanted.
- **The AI Act in Portugal**: which national authority or authorities have been designated as
  market-surveillance / notifying authority, by what instrument, on what date; whether the
  designating instrument is on the government's own AI page. The newsroom's second article is
  exactly this question.
- Public procurement or public-sector AI programmes with a document behind them (the recovery
  plan's AI lines, the "AI Factory" programme's Portuguese participation, the national data
  strategy).
- Decisions or guidance from the data-protection authority on AI, dated.

### 2. Instituições (institutions)
- Research units and centres working on AI (with the science foundation's own listing as the
  citable source, not a guess), the national supercomputing facilities, the AI-related EU projects
  Portuguese institutions participate in (the EU research projects database is machine-readable;
  give project ids and dates).
- The regulator(s) named in section 1, as institutions.

### 3. Empresas (companies)
- Portuguese AI companies that appear in **European research funding** and in **national recovery
  funding**, with amounts, dates and the programme — the brief says this is the honest company
  layer, because there is no free bulk company register. Give the beneficiary page or dataset row.
- Funding rounds, acquisitions and launches by AI companies in Portugal since 1 January 2025, each
  with a primary source (the company's own announcement or the investor's) and, if only press
  reports exist, the press page marked `publisher_kind: press`.
- The count question: the 2025 ecosystem report's figure of **5,091 active startups** — the report
  page, the figure's exact wording, and whether any public dataset lets one count the AI subset.
  The newsroom's third article is that no public dataset can.

### 4. Eventos (events) — time-critical this week
- **Startup Summit Lisbon, 16–18 September 2026, Beato**: press coverage since 1 September, any
  side event (a Guinness pitch-marathon attempt was reported in July by AICEP Portugal Global and
  Portugal Business News — is it confirmed on the event's own pages now?), announced speakers or
  sessions about AI, and anything the event's own site says that contradicts what it said before.
- AI-specific events in Portugal in the next 90 days with a page and a date.

### 5. Casos de uso (use cases)
- Deployed AI in Portuguese public services (health, justice, tax, municipalities) with an official
  page or tender behind it; company case studies only when the company's own page describes them.

### 6. Código aberto (open source)
- Portuguese-language models, datasets and benchmarks published openly (model cards, repositories,
  papers), with licence and publisher; the government's or academia's Portuguese LLM efforts, if
  any, with the page that announces them.

### 7. Diáspora
- **Organisations first**: companies or labs abroad founded or led from Portugal, as their own
  pages state it. People only under the rules in section C.

### 8. Protagonistas (people) — lowest priority for you, highest care
- Only people in public professional roles, only as a primary page lists them (an event's speaker
  page, an institution's staff page, a company's leadership page), and only three fields: the
  listed role, the listed organisation, the page. No biographies, no characterisation, no contact
  details, no "known for". Prefer to give the organisation and let the newsroom read the page.

### What is already held (do not resend)
The newsroom holds, frozen and hashed, every page of startupsummit.io as of 8 and 13 September,
seven press pages about the summit, and the summit's speaker pages. Anything newer or different is
wanted; repeats are not.

## B. How to search

- Search in Portuguese first (`inteligência artificial`, `IA`, `Diário da República`, `Portaria`,
  `Decreto-Lei`, `Resolução do Conselho de Ministros`, `agenda nacional`, `PRR`, `FCT`, `unidade de
  I&D`), then in English for EU sources. Restrict to **2025-01-01 onwards** unless the item is a
  standing document (a strategy, a designation, a register).
- Prefer, in this order: official (`.gov.pt`, `dre.pt`/`diariodarepublica.pt`, EU portals) →
  primary (the organisation the fact is about) → datasets/registers → academic → press. A press
  page is a lead to a primary page; give both when you can.
- Open every page you cite. Copy the excerpt from the opened page. Record the retrieval time. If
  the page is a PDF, say so and give the page number. If the body only renders with JavaScript,
  say so (`script-rendered`) — the newsroom's fetcher may see nothing, and knowing that in
  advance is itself useful.
- Do not summarise from memory. If you cannot find a source for something you believe, leave it
  out or put it in `delivery.notes` as a question.
- Record every query you ran, verbatim, in `delivery.queries`, so the search can be repeated.

## C. Rules that are not negotiable

- **People.** A `Pessoa` entity may carry only `cargo_listado`, `organizacao_listada`,
  `pagina_fonte`. No email, telephone, address, age, nationality, biography, opinion, ranking or
  adjective. If a page about a person is the only source for a fact about an organisation, cite
  the page for the organisation and do not create the person.
- **No characterisation of a named party**, person or company: the record, not the verdict.
  "X was designated by Y on Z" is a lead; "X is the leading…" is not.
- **Verbatim names and titles, with accents.** The newsroom fails its build if an accent is wrong.
- **`status` is always `por_verificar`.** Only the newsroom's verification changes it.
- **Say what you could not find.** A section with nothing is delivered as an empty section with a
  note, not omitted.

## D. How to package it

Deliver **JSON only**, validating against the schema at
https://newsroom.sgit.ai/briefs/pt-newsroom-pack/08__research-briefs/research-schema.json
(a worked example is beside it: `example-delivery.json`). The shape, in short:

```
{
  "delivery": { "id", "tool": "chatgpt", "model", "date", "brief": "12__research-brief-for-chatgpt.md v2",
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

**Edges are Portuguese verbs with a distinct inverse.** Use these where they fit:
`sediada_em / sede_de`, `financiada_por / financia` (with `montante`, `moeda`, `data`, `programa`),
`participa_em / tem_participante`, `desenvolve / desenvolvido_por`, `publica / publicado_por`,
`regulada_por / regula`, `designado_por / designa`, `instituida_por / institui`,
`implementa / implementado_por`, `adquire / adquirida_por`, `parte_de / contém`,
`decorre_em / é_local_de`, `organizado_por / organiza`, `coberto_por / cobre`,
`atua_em / praticado_por`, `usa / usado_por`, `fala_em / recebe`, `listado_em / lista`.
Never `relacionado_com`, `associado_a`, `menciona`, `trabalha_em`. If you need a verb that is not
here, propose it in `vocabulary_proposals` with a sentence that reads aloud.

**Deliver in parts, one section per part**, each a complete valid document with `part: "n/N"`,
inside a single ```json fence with no prose before or after it. Keep each part under ~40 items.
Number source ids and item ids so they do not collide across parts (`src-pol-01`, `item-pol-01`).

## E. What the newsroom will do with it, so you know what breaks

For each part: validate the JSON (invalid → the whole part is set aside); fetch every URL and
freeze it; search the frozen bytes for every `excerpt` (not found → that claim is dropped and
noted); reject any item whose personal-data check is false or whose person carries a forbidden
field; turn what survives into issues on the desk for the research department to re-derive from
the frozen page. Your `queries`, `notes` and `why_it_matters` go to the editor unchanged.

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

Begin with **Políticas**. Deliver part 1/8 as JSON only, then wait for "next". When all eight parts are done, package them as in section F and hand over the read key or the share token — never the vault key.

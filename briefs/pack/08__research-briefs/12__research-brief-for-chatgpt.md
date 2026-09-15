# 12 — Research brief for ChatGPT: what pt.newsroom.sgit.ai needs, how to find it, how to hand it back

**Paste this whole document into ChatGPT as the first message. Use a mode that browses the web
(web search or Deep Research). Written 14 September 2026 for newsroom.sgit.ai v0.3.10; revised
15 September 2026 for pt.newsroom.sgit.ai v0.10.0 (sgit vaults; corrected schema address; the
Diário da República rule from the first delivery). The contract it references is
`briefs/pack/08__research-briefs/research-schema.json`.** CC BY 4.0.

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

### 4. Eventos (events) — time-critical: the summit opens tomorrow
- **Startup Summit Lisbon, 16–18 September 2026, Beato** — it opens the day after this brief was
  revised, so the newsroom's frozen copies (8 and 13 September) are already behind the event.
  Wanted: press coverage **since 13 September**, the programme as it stands on the eve, any
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
seven press pages about the summit, and the summit's speaker pages.

It also holds, frozen on **14 September** from ChatGPT's first delivery (part 1/8, políticas),
these eight pages — **do not deliver them again**:

| what it is | address |
| --- | --- |
| RCM n.º 2/2026 (record page — script-rendered, unusable) | `diariodarepublica.pt/dr/detalhe/resolucao-conselho-ministros/2-2026-1000882016` |
| RCM n.º 2/2026 on digitalGOV | `digital.gov.pt/pt/documentos/resolucao-do-conselho-de-ministros-2-2026` |
| Government release on the ANIA | `portugal.gov.pt/gc25/comunicacao/comunicados/agenda-nacional-de-inteligencia-artificial-ania-` |
| Council of Ministers release, 25 June 2026 | `portugal.gov.pt/gc25/governo/comunicados-do-conselho-de-ministros/comunicado-do-conselho-de-ministros-de-25-de-junho-de-2026` |
| ANACOM page (returned 403 — unusable) | `anacom.pt/render.jsp?contentId=1817086` |
| The government's AI topic page | `digital.gov.pt/pt/inteligencia-artificial` |
| European Commission, AI Act governance | `digital-strategy.ec.europa.eu/en/policies/ai-act-governance-and-enforcement` |
| RCM n.º 70/2026, Série I PDF | `files.diariodarepublica.pt/1s/2026/04/07100/0004500052.pdf` |

Two of those eight are held but unreadable, and the facts they were meant to carry are still
open. **The most wanted single item in this whole brief** is the text of RCM n.º 2/2026 from a
source the fetcher can read — the Série I PDF of *Diário da República* n.º 5/2026, of 8 January
2026, on `files.diariodarepublica.pt`. Find that PDF and the newsroom can confirm the instrument
behind the national AI agenda, the four axes, the 32 initiatives, and initiatives I.1 and I.3.
Likewise, a designation of a national AI authority is wanted as a published instrument, not as a
portal page: if ANACOM or the IPQ was designated, there is an act that did it.

Anything newer or different is wanted; repeats are not.

## B. How to search

- Search in Portuguese first (`inteligência artificial`, `IA`, `Diário da República`, `Portaria`,
  `Decreto-Lei`, `Resolução do Conselho de Ministros`, `agenda nacional`, `PRR`, `FCT`, `unidade de
  I&D`), then in English for EU sources. Restrict to **2025-01-01 onwards** unless the item is a
  standing document (a strategy, a designation, a register).
- Prefer, in this order: official (`.gov.pt`, `dre.pt`/`diariodarepublica.pt`, EU portals) →
  primary (the organisation the fact is about) → datasets/registers → academic → press. A press
  page is a lead to a primary page; give both when you can.
- **The Diário da República rule — cite the PDF, not the record page.** This is the single thing
  that cost the first delivery most: nine of its ten unusable claims cited one page. A
  `diariodarepublica.pt/dr/detalhe/…` address renders its text by script; the newsroom's fetcher
  froze 2,346 bytes of it holding **22 characters of visible text**, so no excerpt could be found
  in the bytes and every claim resting on it was dropped — including the confirmation of the
  instrument behind the national AI agenda, which is the lead the newsroom most wants. The same
  delivery's `files.diariodarepublica.pt/1s/…/…pdf` froze 228,725 bytes holding **30,808
  characters**, and both claims on it were confirmed. So: when you land on a `/dr/detalhe/` page,
  follow it to the PDF of the *Série I* issue on `files.diariodarepublica.pt`, cite **that** URL,
  copy the excerpt out of the PDF, mark `access: "pdf"` and give the page number in `locator`. If
  you cannot reach the PDF, you may still deliver the record page — mark it
  `access: "script-rendered"` and say in `delivery.notes` that the excerpt is unverifiable from
  the bytes, so the editor knows before the fetch rather than after.
- **The same test for every source: would the text survive with JavaScript off?** Deep-linked
  portal pages (`render.jsp?contentId=…` and the like) often will not, and some refuse the
  fetcher outright — the ANACOM page in the first delivery returned **403**, and the claim resting
  on it was dropped. Where a body only exists behind script or a block, look for the same fact on
  a page that serves plain HTML, or on a PDF, and cite that instead.
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
https://pt.newsroom.sgit.ai/briefs/pack/08__research-briefs/research-schema.json
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

**The closed lists. Every one of these is enforced; the first delivery failed validation on five
of them, so they are spelled out here rather than left to the schema.** A value outside a list sets
the whole part aside.

- `delivery.tool`: `chatgpt` · `perplexity` · `other`. `delivery.part` matches `n/N`.
- `section`: `empresas` · `protagonistas` · `instituicoes` · `politicas` · `casos-de-uso` ·
  `codigo-aberto` · `diaspora` · `eventos` (exactly these spellings, unaccented, as shown).
- `items[].kind`: `lead` · `fact` · `entity` · `event` · `dataset` · `policy-instrument` ·
  `funding` · `correction-candidate`. **These eight and no others** — do not invent a kind that
  describes the subject (`instrumento_juridico`, `agenda_nacional` and the like are not kinds).
  A legal instrument is `policy-instrument`; money is `funding`; a fact that corrects something
  the newsroom already published is `correction-candidate`.
- `claims[].confidence`: `alta` · `média` · `baixa` — **`média` carries its accent**.
- `claims[].status`: always `por_verificar`.
- `sources[].publisher_kind`: `official` · `primary` · `dataset` · `academic` · `press` ·
  `company` · `other`.
- `sources[].access`: `open` · `paywalled` · `login` · `script-rendered` · `pdf` · `blocked`.
- `entities[].type`: `Organização` · `Instituição` · `Pessoa` · `Política` · `CasoDeUso` ·
  `Projeto` · `Dataset` · `Modelo` · `Evento` · `Local` · `Programa` — **accented, as shown**.
- `entities[].id`: a prefix from `org` · `inst` · `pessoa` · `politica` · `caso` · `projeto` ·
  `dataset` · `modelo` · `evento` · `local` · `programa`, then `:`, then lowercase letters,
  digits and hyphens only: `org:unbabel`, `politica:ania`. There is no `instrumento:` prefix —
  a legal instrument is a `Política` with a `politica:` id.
- `items[].dates` is an **array of objects**, never of strings:
  `{ "date": "2026-01-08", "what": "publicação em Diário da República", "source": "src-pol-01" }`.
- Required on every item: `id`, `section`, `kind`, `headline`, `what_the_sources_say`, `claims`,
  `entities`, `edges`, `why_it_matters`, `personal_data_check`. Required on every claim: `text`,
  `source`, `excerpt`, `confidence`, `status`. Required on every source: `id`, `url`, `publisher`,
  `publisher_kind`, `title`, `language`, `published`, `retrieved`, `access` — `published` may be
  `null`, but the key must be there.
- `delivery.vault` is **required and nullable**, which is not what an earlier revision of this
  brief said. Until the vault exists, send `"vault": null` — the whole key, set to null. Do NOT
  omit it (the schema lists it in `delivery.required`, so the part fails validation), and do not
  send it as an object full of nulls (`vault_id` and `commit` must be strings when the object is
  there). This was corrected after a delivery followed the wrong instruction, said so in its own
  notes, and validated anyway by ignoring it.

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

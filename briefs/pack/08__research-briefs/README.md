# Research briefs for outside assistants, and how their deliveries enter the newsroom

Two briefs ask ChatGPT and Perplexity to find what pt.newsroom.sgit.ai needs and hand it back as
JSON with full provenance: `../../12__research-brief-for-chatgpt.md` and
`../../13__research-brief-for-perplexity.md` (copies in this folder). Both use the same contract:

- `research-schema.json` — the JSON Schema (draft 2020-12) a delivery must validate against.
- `example-delivery.json` — one valid delivery, written by hand, so the shape is unambiguous.

## What a delivery is, and is not

A delivery is **leads with provenance**, never facts. Nothing in it may be cited on the site.
The newsroom's own method still applies to every URL it contains: Pesquisa fetches and freezes
the page, hashes it, registers it; a gate searches the frozen bytes for every `excerpt`; a claim
whose excerpt is not in the bytes is dropped, and the delivery's `notes` say so back to the
editor. Only after that does a claim exist for Redação to write from.

## Deliveries arrive as sgit vaults

Section F of both briefs asks the assistant to package the delivery as an
[sgit](https://sgit.ai) vault — a versioned, end-to-end encrypted folder — and to hand over a
**read key** (64 hex characters, read-only, derived one-way) or a **share token** from
`sgit share`, never the vault key. Receiving one:

```
pip3 install sgit-ai
sgit clone <read-key>:<vault-id> redacao/entregas/<tool>-<date>     # read-only clone
# or, for a share token: open it in the SG/Send web UI, or download the snapshot with the token
sha256sum -c <(python3 -c "import json;[print(f['sha256'],' ',f['path']) for f in json.load(open('manifest.json'))['files']]")
```

Classify the credential before it touches anything (the publishing method's first step): a
64-hex string before the colon is a read key; anything else is a passphrase and therefore write
access, which must not be stored in the repository. Record `vault_id` and `commit` from
`delivery.vault` in the issue each item becomes; they are the provenance of the lead. Docs:
[Working with AI agents](https://sgit.ai/docs/agents.html) ·
[Publishing a vault: the method](https://sgit.ai/demos/vaults/publishing.html).

## Ingesting a delivery (the Claude agent)

1. Save each part unchanged as `redacao/entregas/<tool>/<delivery.id>.json` (copied out of the
   vault clone, with the vault id and commit beside it). It is part of the record.
2. Validate against `research-schema.json` (`pip install jsonschema`; or the check in
   `build/gates.py` once you add it). Invalid → keep the file, write the errors to the editor's
   inbox, ingest nothing.
3. For every `item`: create an issue in `redacao/issues/` in state `procurado` with the item's
   headline, section and source ids. For every `source`: add its URL to `dados/fontes-alvo.json`
   for the next run's fetch, with `origem: entrega/<id>`.
4. The next run freezes the URLs; the excerpt gate runs; issues move to `congelado` or `parado`
   with the reason ("excerto não encontrado nos bytes", "página renderizada por script", "404").
5. Entities and edges are proposals: Pesquisa re-derives them from the frozen page before
   anything reaches `dados/grafo.json`. `vocabulary_proposals` go to the editor; a new verb is an
   ontology change and gets a version.
6. Persons: the delivery may only carry `cargo_listado`, `organizacao_listada`, `pagina_fonte`.
   Gate 11 (contact details) and the characterisation rule apply to deliveries exactly as to
   extracted data; a delivery that breaks them is recorded and not ingested.

## Why two briefs and not one

The tools differ in what they are good at. Perplexity cites by default and searches well in
Portuguese, so its brief leans on citations and per-section query series. ChatGPT is stronger at
structuring and at long, schema-shaped output, and weaker at guaranteeing every URL was opened, so
its brief insists on opening every page, copying excerpts, and delivering in parts. Both briefs
say the same thing about people, provenance and language.

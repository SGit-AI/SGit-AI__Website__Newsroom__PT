# What to inherit from newsroom.sgit.ai, and what to rewrite

Section 13 of the brief says: *take the ingestion path, the gate, the ontology and the notice; do
not take the English pages, the "beta" hedging or the parent site's chrome.* This folder is that
section made concrete. Every file is a verbatim copy from the newsroom.sgit.ai repository at v0.3.9.

## Copy, then adapt (the method — do not rewrite from memory)

| File | What it is | What changes for pt.newsroom |
|---|---|---|
| `portugal-build/extract.py` | **The ingestion path**: fetch → freeze → hash → extract → diff. Dated snapshots under `sources/frozen/<date>/`, `.snapshot` extension, a register with SHA-256 for every file, the diff between snapshots, the coverage register, the topics/lexicon reading | The source list (`PAGES`, `COVERAGE`) becomes yours; the extraction of a speaker card becomes the extraction of whatever your beat's primary page carries. Keep the `.snapshot` rule, the register shape, the "exclude a 404 body" rule, and the biography posture |
| `portugal-build/gates.py` | **Eighteen gates** that fail the build: hashes re-verified, no contact details at extraction time, no biography-length field, every verb with an inverse, every node naming a registered source, every session title verbatim in the frozen agenda, coverage never quoted, topics verbatim, derived tags re-derived, connections re-derived | Keep every gate whose subject exists on your site; add the two the brief demands: (a) **the accent gate** — assert accents are present and correct, derived from the source (§6); (b) **the Portuguese path gate** — every edge verb has a `pt` and a path reads as a sentence |
| `portugal-build/graph.py` | **The ontology and the graph builder**: node types and verbs each with `pt`, banned verbs, the taxonomy, classification as published formula (`role_class`, the lexicon), packs, and the N-Triples export with `owl:inverseOf` | The eight sections of the brief (empresas, protagonistas, instituições, políticas, casos de uso, código aberto, diáspora, eventos) become the top of the taxonomy; the verbs become **Portuguese-first** (`pt` is the primary key, `en` the annotation). Keep the triples export |
| `portugal-build/connections.py` | The three organisation-level formulas (talk / buy / help) as SQL stored beside their rows | Optional for v0.1.0. If kept, keep the organisation-level rule and the reason for it |
| `portugal-build/pages.py`, `build.py` | The page builders (front page, graph page, explorer, connections, notice, method, team, stories) | Rewrite the **prose** in Portuguese; keep the **shape** (masthead, disclaimer block, agent block, the notice link on every page that names a person). The front page is replaced by the design in `02__the-design/` |
| `admin-build/chrome.py` | Nav and footer applied to every page; the version badge that the validator requires to agree everywhere; the markdown twin stamping | Your own nav (the eight sections + Registo, Grafo, Método, Equipa, Aviso, Sobre, Redação); the parent link points at newsroom.sgit.ai |
| `admin-build/validate.js` | The site gate: version agreement, internal links, canonical host, every hub in llms.txt, sitemap agreement, key-leak tripwire, div balance, agent block on every page, provenance blocks, no gitignored build tooling | Copy whole. Change `CNAME` to `pt.newsroom.sgit.ai` and it works |
| `workflows/deploy-pages.yml` | validate → tag → deploy to GitHub Pages; every push to `dev` is a minor release tagged `vX.Y.Z` from `admin/build/version.txt` and the commit subject `site vX.Y.Z: …` | Copy whole. The same pipeline is on five sibling sites |
| `databases-build/build.py`, `tables.json`, `assets/nsdb-*.js` | The no-server databases: SQLite and a SPARQL store in the reader's browser over the JSON files, worked queries executed at build | Optional for v0.1.0, recommended for v0.2: the Beato screen's "the article is a query" moment is this. Needs `sql.js` and `oxigraph` vendored (see LICENSES.md on the parent site) |
| `assets/portugal-graph.js` | The graph viewer (Cytoscape, packs, radius, path-as-sentence with a language toggle, `window.__graph` API) | Copy whole; set the default language to `pt`. Needs `cytoscape.min.js` vendored |
| `assets/site.css`, `nav.js` | The estate's stylesheet and nav script | The **front page uses the design's own stylesheet**, not this. Inner pages may use this for speed, restyled with the design's paper, ink and faces so the site reads as one |
| `data-examples/ontology.json` | What the graph builder writes: types, verbs with `pt`, banned, taxonomy, formulas | Your shape to match |
| `data-examples/lexicon.json` | A published formula: 57 patterns, each with `pt`, run over frozen prose; the matched words travel on the edge | The model for any derivation you make. Yours runs over Portuguese prose, so the patterns are Portuguese |
| `data-examples/notice.json` | The data-protection notice as data: controller, categories held and refused, the three-limb legitimate-interests test, the unconditional removal | **Copy, translate, keep every refusal.** The controller is the editor of record. Not legal advice |
| `data-examples/team.json`, `stories.json`, `sessions.json`, `coverage-notes.json`, `event.json` | The shapes of a team file, a story register with `stands_on`, a transcribed programme, coverage notes with `what_it_says`, an event file that separates TARGETS from COUNTS | Shapes to match; contents to replace |

## Do not take

- The English prose of any page. The brief is explicit (§1, §6): not a translation, not bilingual.
- The word "beta" as a hedge. Say what is real and what is not, on the page, in Portuguese.
- The parent site's argument pages (thesis, economics, rights). Link to them once, from *Sobre*.
- The Governance Wire's posture of no human review. The Portugal section's posture — a named
  editor of record who reads every page before it publishes — is the one that travels.

## The two rules that stop the copy from being a fork

1. **Content exists once.** If a paragraph is on newsroom.sgit.ai and again on pt.newsroom, they
   will disagree. The brief lives on the parent site; your *Sobre* page links to it.
2. **Anything rendered stays one click from the bytes.** Every page names the file it was built
   from; every claim names the frozen source with its hash. That is what the parent's `explorer.html`
   and `sources.html` do, and it is the part of the copy that must survive intact.

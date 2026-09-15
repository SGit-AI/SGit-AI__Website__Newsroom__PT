#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the read-only API, and the OpenAPI document that describes it.

    python3 build/api.py

WHAT THIS IS

Every path under `/api/v1/` is a JSON file on disk. There is no server: a GET is a file read, so
an OpenAPI document describing this surface is honest in a way that most are not — there is no
verb here that is not a GET, no request body anywhere, and nothing that can fail in a way the
document does not predict.

WHY THE API IS IN ENGLISH WHEN THE SITE IS PORTUGUESE

Deliberate, and asked for. The publication is natively Portuguese and stays that way; the
*interface to the data* is English because the intent is several languages over one dataset.
`companies`, not `empresas`. A reader reads Portuguese; a program reads English; neither has to
translate the other's vocabulary to get at the same bytes.

That split has a cost worth naming: the field names inside the documents are still Portuguese,
because they are the publication's own record of itself and renaming them would fork the data from
the code that writes it. So a caller gets an English path and Portuguese keys. The alternative —
translating keys on the way out — would mean the API served something no file in this repository
contains, and this whole site exists to avoid exactly that.

WHAT IS SERVED

  /api/v1/openapi.json          the document describing everything below
  /api/v1/index.json            the catalogue: every collection, with counts and links
  /api/v1/sources              the frozen-source register, hashes and all
  /api/v1/graph, /ontology      the nodes and edges, and the grammar they obey
  /api/v1/people, /companies    the entities, derived from frozen bytes
  /api/v1/events, /sessions     the programme
  /api/v1/articles              the articles, their state and their provenance
  /api/v1/sections              the eight sections and their editorial records
  /api/v1/deliveries            research deliveries and what happened to each excerpt
  /api/v1/notice, /team         the data-protection notice and the newsroom
  /api/v1/documents             every markdown document in the repository

Each collection is served two ways: the whole collection at `<name>.json`, and — where the items
have stable ids — one file per item at `<name>/<id>.json`, so a caller can fetch one thing without
pulling the set. Both are generated from the same source, so they cannot disagree.
"""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
API = ROOT / "api" / "v1"
HOST = "pt.newsroom.sgit.ai"
VERSAO = (ROOT / "admin" / "build" / "version.txt").read_text(encoding="utf-8").strip()


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def ident(x):
    base = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "sem-id"


def escrever(rel, obj):
    f = API / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return f"api/v1/{rel}"


# Each collection: the English path, where it comes from, what an item is, and what an item is
# called. `chave` is the field giving an item its id; None means the collection is not split.
COLECCOES = [
    {"path": "sources", "ficheiro": "registo.json", "lista": "fontes", "chave": "id",
     "pt": "registo", "summary": "Every frozen source with its SHA-256, bytes and retrieval time",
     "description": "The register. This is what a claim on this site walks back to: a byte copy "
                    "held in the repository, hashed, and re-verified on every build."},
    {"path": "graph", "ficheiro": "grafo.json", "lista": None, "chave": None,
     "pt": "grafo", "summary": "Nodes and edges",
     "description": "Every node names the frozen source it came from; every edge is a Portuguese "
                    "verb with a distinct named inverse."},
    {"path": "ontology", "ficheiro": "ontologia.json", "lista": None, "chave": None,
     "pt": "ontologia", "summary": "The grammar the graph obeys",
     "description": "Types, verbs with their readings and inverses, banned verbs, the taxonomy "
                    "and the published formulas."},
    {"path": "people", "ficheiro": "pessoas.json", "lista": "pessoas", "chave": "id",
     "pt": "pessoas", "summary": "People named on a published list, in their professional capacity",
     "description": "Name, listed role, listed organisation and links, verbatim from the frozen "
                    "source. Never a biography, never a contact detail. See /notice."},
    {"path": "companies", "ficheiro": "organizacoes.json", "lista": "organizacoes", "chave": "id",
     "pt": "organizacoes", "summary": "Organisations, derived from the source and never typed",
     "description": "Derived from the organisation field of each speaker card. Placeholder values "
                    "such as 'Independent' are flagged, not removed."},
    {"path": "sessions", "ficheiro": "sessoes.json", "lista": "sessoes", "chave": "id",
     "pt": "sessoes", "summary": "The programme, read from the frozen agenda",
     "description": "Titles verbatim, in whatever language the event published them."},
    {"path": "events", "ficheiro": "evento.json", "lista": None, "chave": None,
     "pt": "evento", "summary": "The event this newsroom's first beat covers"},
    {"path": "topics", "ficheiro": "temas.json", "lista": "pessoas", "chave": "id",
     "pt": "temas", "summary": "Topics verbatim from the source, and tags derived by the lexicon"},
    {"path": "lexicon", "ficheiro": "lexico.json", "lista": "entradas", "chave": "id",
     "pt": "lexico", "summary": "The published formula that produces the derived tags",
     "description": "A regular expression per entry, run over the frozen page. A tag says the "
                    "page contains those words; it is not a characterisation of anybody."},
    {"path": "changes", "ficheiro": "mudancas.json", "lista": None, "chave": None,
     "pt": "mudancas", "summary": "What moved between snapshots",
     "description": "A name present in one snapshot and absent from the next is recorded as "
                    "exactly that. The reason is left blank, never guessed."},
    {"path": "articles", "ficheiro": "historias.json", "lista": "historias", "chave": "slug",
     "pt": "historias", "summary": "Every article, its state and where its folder is",
     "description": "Derived from the dated folders under /artigos/. An article is published only "
                    "when the editor of record writes that line."},
    {"path": "sections", "ficheiro": None, "lista": None, "chave": None,
     "pt": "seccoes", "summary": "The eight sections and their editorial records",
     "description": "What each section covers, what it can and cannot claim today, which sources "
                    "are frozen and which did not resolve."},
    {"path": "deliveries", "ficheiro": "entregas.json", "lista": "entregas", "chave": "id",
     "pt": "entregas", "summary": "Research deliveries, and what happened to every excerpt",
     "description": "A delivery is leads with provenance, never facts. Each claim carries the "
                    "result of searching the frozen bytes for the excerpt it cites."},
    {"path": "notice", "ficheiro": "aviso.json", "lista": None, "chave": None,
     "pt": "aviso", "summary": "The data-protection notice, as data",
     "description": "Controller, categories held and refused, the three-limb legitimate-interests "
                    "test, and the unconditional removal route."},
    {"path": "team", "ficheiro": "equipa.json", "lista": None, "chave": None,
     "pt": "equipa", "summary": "The three departments and the editor of record"},
    {"path": "documents", "ficheiro": "documentos.json", "lista": "documentos", "chave": None,
     "pt": "documentos", "summary": "Every markdown document in this repository"},
    {"path": "agents", "ficheiro": "agentes.json", "lista": "agents", "chave": "id",
     "pt": "agentes", "summary": "The named agents that may change this site, and their mandates",
     "description": "One entry per identity, each with a role, a write scope and what it declares "
                    "in a run record. An agent nobody can name is an anonymous contributor to a "
                    "publication whose entire argument is knowing who said what."},
    {"path": "transfers", "ficheiro": "transferencias.json", "lista": "lotes", "chave": "id",
     "pt": "transferencias", "summary": "Evidence frozen by ANOTHER publication, with its provenance",
     "description": "Not in this newsroom's register, and not to be treated as if it were: these "
                    "bytes were fetched by another publication's fetcher, with its user-agent, at "
                    "the times in its register. Every SHA-256 is recomputed here; a bundle with "
                    "one bad hash is refused whole."},
    {"path": "desk", "ficheiro": "redacao.json", "lista": None, "chave": None,
     "pt": "redacao", "summary": "The newsroom floor: benches, their load, and the board",
     "description": "Counted from files that already exist — the issue board, the mail between "
                    "departments, the run records, and the per-agent work. Nothing here moves "
                    "anything: a story's state lives in the files of its own folder, and the "
                    "«publicado» column is the named editor's line and nobody else's."},
    {"path": "agent-activity", "ficheiro": "comentarios.json", "lista": "fluxo", "chave": "id",
     "pt": "comentarios", "summary": "What every agent did to every article, derived not written",
     "description": "One entry per recorded action, question, verification, gap, outside proposal "
                    "or editorial decision. Every entry carries a `de` field naming the file and "
                    "path it was derived from, and the build fails if that path does not resolve. "
                    "Nothing here was authored for the record: a comment attributed to a model "
                    "that never wrote it is a claim with a forged source."},
    {"path": "entities", "ficheiro": "entidades.json", "lista": "entidades", "chave": "no",
     "pt": "entidades", "summary": "Every graph node that is a thing in the world, with a page",
     "description": "One entry per person, organisation, institution, publisher, topic or place. "
                    "Each carries where its name appears in the frozen bytes and how often, and "
                    "whether it is linkable in prose under the published linking formula. Keys are "
                    "Portuguese because that is what the repository holds; the path is English "
                    "because the intent is several languages over one set of data."},
    {"path": "manifest", "ficheiro": "manifesto.json", "lista": None, "chave": None,
     "pt": "manifesto", "summary": "Every data file with its SHA-256"},
    {"path": "excluded", "ficheiro": "excluidas.json", "lista": None, "chave": None,
     "pt": "excluidas", "summary": "Sources that were attempted and did not resolve",
     "description": "Not dropped in silence: a source this newsroom cannot reach is a fact about "
                    "the public record."},
]


def seccoes():
    base = ROOT / "seccoes"
    out = []
    for f in sorted(base.glob("*/seccao.json")) if base.exists() else []:
        out.append(json.loads(f.read_text(encoding="utf-8")))
    return {"id": "pt-sections", "count": len(out), "sections": sorted(out, key=lambda s: s["ordem"])}


def main():
    escritos, catalogo = [], []

    for c in COLECCOES:
        dados = seccoes() if c["path"] == "sections" else carregar(c["ficheiro"])
        if not dados:
            continue
        escritos.append(escrever(f'{c["path"]}.json', dados))

        itens = []
        if c["lista"] and c["chave"]:
            lista = dados.get(c["lista"]) or []
            vistos = set()
            for it in lista:
                if not isinstance(it, dict) or c["chave"] not in it:
                    continue
                iid = ident(it[c["chave"]])
                if iid in vistos:
                    continue
                vistos.add(iid)
                escritos.append(escrever(f'{c["path"]}/{iid}.json', it))
                itens.append(iid)
        elif c["path"] == "sections":
            for s in dados["sections"]:
                escritos.append(escrever(f'sections/{s["id"]}.json', s))
                itens.append(s["id"])

        n = (len(dados.get(c["lista"]) or []) if c["lista"]
             else dados.get("contagem") or dados.get("count"))
        catalogo.append({
            "path": f'/api/v1/{c["path"]}.json',
            "name": c["path"], "portuguese_source": f'dados/{c["ficheiro"]}' if c["ficheiro"] else "seccoes/*/seccao.json",
            "summary": c["summary"],
            "description": c.get("description"),
            "count": n,
            "items": (f'/api/v1/{c["path"]}/<id>.json' if itens else None),
            "item_ids": itens[:500] or None,
        })

    # --- o catálogo -----------------------------------------------------------
    escrever("index.json", {
        "name": "pt.newsroom.sgit.ai — read-only API",
        "version": VERSAO,
        "base": f"https://{HOST}/api/v1/",
        "openapi": f"https://{HOST}/api/v1/openapi.json",
        "console": f"https://{HOST}/api/",
        "what_this_is": ("Every path here is a JSON file on disk. There is no server: a GET is a "
                         "file read. That is why an OpenAPI document for it is honest — there is "
                         "no verb that is not a GET and no request body anywhere."),
        "why_english": ("The publication is natively Portuguese and stays that way; the interface "
                        "to the data is English because the intent is several languages over one "
                        "dataset. The field names inside the documents are still Portuguese, "
                        "because they are the publication's own record of itself and translating "
                        "them on the way out would mean serving something no file here contains."),
        "licence": "CC BY 4.0 for the content. See /LICENSES.md. Reusing it does not transfer the "
                   "lawful basis for the personal data it contains — see /api/v1/notice.json.",
        "collections": catalogo,
    })

    # --- o documento OpenAPI --------------------------------------------------
    paths = {}
    for c in catalogo:
        nome = c["name"]
        paths[f'/{nome}.json'] = {"get": {
            "operationId": f"get{nome.title().replace('-', '')}",
            "summary": c["summary"],
            "description": (c.get("description") or c["summary"]) +
                           f'\n\nSource file in the repository: `{c["portuguese_source"]}`.',
            "tags": [nome],
            "responses": {"200": {"description": "The collection, as JSON",
                                  "content": {"application/json": {"schema": {"type": "object"}}}}},
        }}
        if c["items"]:
            paths[f'/{nome}/{{id}}.json'] = {"get": {
                "operationId": f"get{nome.title().replace('-', '')}ById",
                "summary": f'One item from {nome}',
                "description": "Generated from the same source as the collection, so the two "
                               "cannot disagree.",
                "tags": [nome],
                "parameters": [{"name": "id", "in": "path", "required": True,
                                "schema": {"type": "string"},
                                "description": "The item id, slugged to ASCII. The collection "
                                               "lists every valid value in `item_ids`.",
                                "examples": {k: {"value": k} for k in (c["item_ids"] or [])[:3]}}],
                "responses": {"200": {"description": "The item, as JSON"},
                              "404": {"description": "No such item. There is no server: this is a "
                                                     "missing file."}},
            }}
    paths["/index.json"] = {"get": {
        "operationId": "getIndex", "summary": "The catalogue of every collection", "tags": ["index"],
        "responses": {"200": {"description": "The catalogue"}}}}

    escrever("openapi.json", {
        "openapi": "3.1.0",
        "info": {
            "title": "pt.newsroom.sgit.ai",
            "version": VERSAO.lstrip("v"),
            "summary": "The Portuguese AI ecosystem, as data",
            "description": (
                "A read-only API over a newsroom that maps Portugal's AI landscape as a graph.\n\n"
                "**Every path is a file.** There is no server behind this document: the site is "
                "static, and a GET is a file read. Which means this document cannot drift from "
                "the implementation in the usual way — if a path is here and the file is not, the "
                "build fails.\n\n"
                "**The paths are English and the field names are Portuguese.** That is deliberate: "
                "the publication is natively Portuguese, the interface to the data is English "
                "because the intent is several languages over one dataset, and the keys inside a "
                "document are the publication's own record of itself. Translating them on the way "
                "out would mean serving something no file in the repository contains, which is "
                "the one thing this site exists not to do.\n\n"
                "**On the personal data.** People appear here in their professional capacity, from "
                "lists their own sources published. No contact details, no biographies, no "
                "characterisation of anyone. Reusing this data does not transfer the lawful basis "
                "for processing it: see `/api/v1/notice.json` and take your own advice."),
            "contact": {"name": "Dinis Cruz, editor of record", "email": "dinis.cruz@owasp.org"},
            "license": {"name": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"},
        },
        "servers": [{"url": f"https://{HOST}/api/v1", "description": "The site itself"}],
        "tags": [{"name": c["name"], "description": c["summary"]} for c in catalogo],
        "paths": paths,
    })

    print(f"api: {len(escritos)} ficheiros em api/v1/ ({len(catalogo)} colecções)")
    return escritos


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the gates for the newer structures: articles, sections, back office,
entities, agent activity, run records, the language rule and the agent register.

Gates 16-26 and 34-35 live here. 27-33 are the design gates, in build/gates_desenho.py — the
numbers are one namespace across the gate files, and a range that has already shipped keeps it.

    python3 build/gates_artigos.py

WHY THIS IS A SEPARATE FILE FROM `build/gates.py`.

`build/gates.py` is in the deny list of `.claude/settings.json`: no agent here can edit it. The rule
exists because an agent that can change the gate that stops it has no gate at all — and the wrong
way to add checks would be to lift that protection.

So the gates for the structures that came after it live here, and `gates.py` stays as it is: the
stable core, protected. CI runs both, and either one failing is a release that does not happen. A
gate that fails is answered, never silenced.

THE GATES

  16 · AN ARTICLE'S PATH DOES NOT LIE. artigos/<yyyy>/<mm>/<dd>/<slug>/ has to agree with the
       article's own `data` and `slug` fields. An article whose folder says one date and whose file
       says another has two addresses, and one of them is wrong.
  17 · EVERY CLAIM IN AN ARTICLE WALKS BACK. Every [[fonte:…]] mark in the prose and every source
       cited in the verification record has to exist in dados/registo.json.
  18 · A VERIFIED ARTICLE WAS ACTUALLY VERIFIED. In `verificado` or `publicado` there has to be
       prose, there has to be a verification record, and no claim may be left unmarked.
  19 · THE BACK OFFICE PUBLISHES NO CLAIMS. The console is in English by the editor's decision, and
       the condition of that exception is that it reports the newsroom and never the world: no page
       under /newsroom/ may cite a frozen source as evidence for a claim about Portugal.
  20 · EVERY SECTION HAS AN EDITORIAL RECORD. The brief's eight sections, each with its own
       seccoes/<id>/seccao.json, and none of them claiming what it has no sources to claim.
  21 · THE ENTITY INDEX AGREES WITH THE DISK. Every entity in the index has a page, every page under
       entidades/ is in the index, and each path is what the formula produces. An index promising a
       page that does not exist is a broken link waiting to happen.
  22 · EVERY LINKABLE ENTITY HAS A GROUND, AND THE GROUND IS TRUE. `bytes` if and only if the name
       was found in a frozen copy; `registo` if and only if the node publishes a frozen file. An
       entity linked with no ground is a claim with no source.
  23 · THE LINKING FORMULA IS OBEYED ON THE PAGES. No page links the same entity more often than
       the formula allows, no entity page links to itself, and each link's text is the entity's
       verbatim name — not an abbreviation, not a surname.
  24 · NO PERSON'S PAGE SAYS ANYTHING ABOUT THE PERSON. Every value in a Pessoa page's field table
       has to be, byte for byte, a value already in dados/pessoas.json or in the graph node. It is
       §4 of the brief checked rather than promised: without it, a line of prose about somebody
       would enter the page with nobody noticing.
  25 · NO AGENT COMMENT WAS INVENTED. Every entry in a `comentarios.json` has to name, in its `de`
       field, a file and a path that exist and resolve. It is the claims rule turned inward: a
       comment attributed to a model that never wrote it is a claim with a false source, which is
       worse than a claim with no source at all.
  26 · "CONSTRUCTION" IS NOT THE WORD YOU WRITE TO ESCAPE THE BOUNDARY. Gate 12 exempts a run that
       declares no department, because the bootstrap session creates everything. A construction run
       uses that exemption, so it has to earn it: it freezes no source, moves no card, publishes
       nothing, and declares itself as such. Without this, the boundary between departments would
       have a door with the name written beside it.
  34 · CODE IS IN ENGLISH. Every comment and docstring under build/, admin/build/ and
       assets/components/ is read for Portuguese function words. CLAUDE.md has said "code and
       comments are in English" since the first commit, and seventeen files ignored it because the
       code already there was Portuguese — an existing convention is not the rule. The two honest
       exceptions are declared in docs/guidance/language.md and encoded here, not hidden here.
  35 · EVERY AGENT THAT TOUCHES THIS SITE IS NAMED. A run record names an `agente` that exists in
       dados/agentes.json, and every registered agent has a ROLE.md and a MANDATE.md. An agent
       nobody can name is an anonymous contributor to a publication whose argument is knowing who
       said what.
"""
import ast
import html as _html
import io
import hashlib
import json
from html import escape
import re
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
ARTIGOS = ROOT / "artigos"
SECCOES = ROOT / "seccoes"
BASTIDORES = ROOT / "newsroom"

erros = []


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


registo = carregar("registo.json")
historias = carregar("historias.json")
equipa = carregar("equipa.json")
entregas = carregar("entregas.json")
por_id = {s["id"]: s for s in registo.get("fontes", [])}

AS_OITO = ["empresas", "protagonistas", "instituicoes", "politicas",
           "casos-de-uso", "codigo-aberto", "diaspora", "eventos"]
ESTADOS_VALIDOS = {"procurado", "rascunho", "verificado", "publicado", "superseded"}


# --- 16. an article's path does not lie ----------------------------------------
metas = sorted(ARTIGOS.rglob("artigo.json")) if ARTIGOS.exists() else []
if not metas:
    erros.append("articles: not one article folder exists. The site has an articles section and "
                 "nothing inside it")

for meta in metas:
    d = meta.parent
    rel = d.relative_to(ROOT).as_posix()
    try:
        a = json.loads(meta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        erros.append(f"{rel}/artigo.json: is not valid JSON ({ex})")
        continue

    partes = rel.split("/")
    if len(partes) != 5 or partes[0] != "artigos":
        erros.append(f"{rel}: an article lives at artigos/<yyyy>/<mm>/<dd>/<slug>/, and this one "
                     f"does not")
        continue
    _, ano, mes, dia, slug = partes
    esperado = f"{ano}-{mes}-{dia}"
    if a.get("data") != esperado:
        erros.append(f'{rel}: the folder says {esperado} and the article says «{a.get("data")}». '
                     f'An article with two dates has two addresses, and one of them is wrong')
    if a.get("slug") != slug:
        erros.append(f'{rel}: the folder says «{slug}» and the article says «{a.get("slug")}»')
    if a.get("estado") not in ESTADOS_VALIDOS:
        erros.append(f'{rel}: state «{a.get("estado")}» does not exist. The states are '
                     f'{", ".join(sorted(ESTADOS_VALIDOS))}')
    if a.get("seccao") not in AS_OITO:
        erros.append(f'{rel}: section «{a.get("seccao")}» is not one of the brief\'s eight')
    for campo in ("titulo", "entrada"):
        if not a.get(campo):
            erros.append(f'{rel}: the required field «{campo}» is missing')

    # --- 17. every claim walks back --------------------------------------------
    for sid in a.get("assenta_em", []):
        if sid not in por_id:
            erros.append(f'{rel}: stands on «{sid}», which is not in the source register')

    md = d / "artigo.md"
    prosa = md.read_text(encoding="utf-8") if md.exists() else ""
    for sid in set(re.findall(r"\[\[fonte:([^\]]+)\]\]", prosa)):
        if sid not in por_id:
            erros.append(f'{rel}/artigo.md: cites [[fonte:{sid}]], which is not in the register')
        elif sid not in a.get("assenta_em", []):
            erros.append(f'{rel}: the prose cites «{sid}» and artigo.json does not list it under '
                         f'assenta_em — the two have to agree on what the article stands on')

    fa = d / "afirmacoes.json"
    ver = json.loads(fa.read_text(encoding="utf-8")) if fa.exists() else None
    if ver:
        for af in ver.get("afirmacoes", []):
            if af.get("fonte") not in por_id:
                erros.append(f'{rel}/afirmacoes.json: claim {af.get("id")} cites '
                             f'«{af.get("fonte")}», which is not in the register')
            if af.get("estado") not in ("confirmada", "disputada", "nao_encontrada"):
                erros.append(f'{rel}/afirmacoes.json: {af.get("id")} carries the state '
                             f'«{af.get("estado")}», which is not one of the three')
        r = ver.get("resumo") or {}
        contado = {k: sum(1 for x in ver.get("afirmacoes", []) if x.get("estado") == k)
                   for k in ("confirmada", "disputada", "nao_encontrada")}
        if (r.get("confirmadas"), r.get("disputadas"), r.get("nao_encontradas")) != \
                (contado["confirmada"], contado["disputada"], contado["nao_encontrada"]):
            erros.append(f'{rel}/afirmacoes.json: the summary does not add up to the claims')

    # --- 18. a verified article was actually verified -------------------------
    if a.get("estado") in ("verificado", "publicado"):
        if not prosa.strip():
            erros.append(f'{rel}: is in «{a["estado"]}» and has no prose. You cannot verify what '
                         f'has not been written')
        if not ver or not ver.get("afirmacoes"):
            erros.append(f'{rel}: is in «{a["estado"]}» and has no verification record')
        elif not ver.get("verificado_em"):
            erros.append(f'{rel}/afirmacoes.json: does not say when it was verified')

    # --- a linha do editor, para o formato novo -------------------------------
    ed = (equipa.get("editor_de_registo") or {}).get("nome")
    if a.get("estado") == "publicado":
        if a.get("publicado_por") != ed:
            erros.append(f'{rel}: is published by «{a.get("publicado_por")}», who is not the '
                         f'editor of record ({ed}). Only the editor writes that line')
        if not a.get("publicado_em"):
            erros.append(f"{rel}: is published and carries no publication date")
        if ver and any(x.get("estado") == "nao_encontrada" for x in ver.get("afirmacoes", [])):
            erros.append(f'{rel}: is published and has a claim still not found. A story is not '
                         f'published carrying a claim nobody could confirm')
    else:
        if a.get("publicado_em") or a.get("publicado_por"):
            erros.append(f'{rel}: is not published and already carries '
                         f'publicado_em/publicado_por')

# o índice derivado tem de cobrir exatamente as pastas
if historias:
    nas_pastas = {m.parent.relative_to(ROOT).as_posix() for m in metas}
    no_indice = {h["pasta"] for h in historias.get("historias", [])}
    if nas_pastas != no_indice:
        erros.append("historias.json: the index does not cover exactly the article folders — it "
                     "was hand-edited instead of derived by build/artigos.py")


# --- 19. the back office publishes no claims -----------------------------------
# The console is in English by the editor's decision. The condition of that exception is that it
# reports the NEWSROOM and never the WORLD: an English page citing a frozen source as evidence for
# something about Portugal would be the language rule being broken for real.
if BASTIDORES.exists():
    for p in sorted(BASTIDORES.rglob("*.html")):
        t = p.read_text(encoding="utf-8")
        rel = p.relative_to(ROOT).as_posix()
        # A mark inside <code> is the syntax being QUOTED, not a citation being made: the
        # guidance page that explains how `[[fonte:…]]` works has to be able to write it down.
        # Everything else about this gate is unchanged, and the check below — a link into the
        # register — is the one that catches a back-office page actually standing a claim on
        # evidence, quoted or not.
        sem_codigo = re.sub(r"<code\b[^>]*>.*?</code>", " ", t, flags=re.S | re.I)
        if "[[fonte:" in sem_codigo:
            erros.append(f"{rel}: carries a source mark. The back office reports on the "
                         f"newsroom, not on the world")
        # a link to a register anchor is a citation of evidence
        if re.search(r'href="[^"]*registo/#', t):
            erros.append(f"{rel}: cites a frozen source as evidence. The console may COUNT "
                         f"sources; it may not stand a claim on one")
        if not re.search(r'lang="en"', t):
            erros.append(f"{rel}: the back office is in English and the page does not say so in "
                         f"its lang attribute")
        if "This is the operations console" not in t:
            erros.append(f"{rel}: the notice saying this is not the publication is missing. The "
                         f"exception to the language rule holds only while it is visible to a "
                         f"reader who lands here")
    for obrigatoria in ("newsroom/index.html", "newsroom/docs.html"):
        if not (ROOT / obrigatoria).exists():
            erros.append(f"{obrigatoria}: was not generated")


# --- 20. every section has an editorial record ---------------------------------
for sid in AS_OITO:
    f = SECCOES / sid / "seccao.json"
    if not f.exists():
        erros.append(f"seccoes/{sid}/seccao.json: does not exist. Each of the brief's eight "
                     f"sections has a folder and an editorial record")
        continue
    s = json.loads(f.read_text(encoding="utf-8"))
    for campo in ("rotulo", "ambito", "o_que_pode_afirmar_hoje", "o_que_nao_pode",
                  "a_afirmacao_honesta"):
        if not s.get(campo):
            erros.append(f"seccoes/{sid}/seccao.json: «{campo}» is missing")
    if s.get("id") != sid:
        erros.append(f'seccoes/{sid}/seccao.json: the id says «{s.get("id")}» and the folder '
                     f'says «{sid}»')
    congeladas = [t for t in s.get("fontes_alvo", []) if t.get("estado") == "congelada"]
    # A section with no frozen sources cannot say it claims anything. The statement has to BEGIN
    # with «Nada» — what follows is the explanation, and demanding the word alone would force a
    # choice between passing the gate and telling the reader why. The check is on the first word,
    # which is the one that answers the question.
    diz = s.get("o_que_pode_afirmar_hoje", "").strip().lower()
    diz_que_afirma = not diz.startswith("nada")
    if not congeladas and diz_que_afirma:
        erros.append(f'seccoes/{sid}: has no frozen source and its editorial record says it can '
                     f'claim something. A section with no bytes claims «Nada.»')
    for t in s.get("fontes_alvo", []):
        if t.get("estado") == "congelada" and not any(
                x["pagina"].endswith(t["id"]) or x["id"].endswith("/" + t["id"])
                for x in registo.get("fontes", [])):
            erros.append(f'seccoes/{sid}: says «{t["id"]}» is frozen and no source in the '
                         f'register carries that name')

extra = {p.name for p in SECCOES.iterdir() if p.is_dir()} - set(AS_OITO) if SECCOES.exists() else set()
if extra:
    erros.append(f'seccoes/: extra folders ({", ".join(sorted(extra))}). The sections are the '
                 f'brief\'s eight, and adding one is an editorial decision, not a side effect')


# --- 21, 22, 23, 24. the entities -----------------------------------------------
entidades = carregar("entidades.json")
grafo = carregar("grafo.json")
pessoas_json = carregar("pessoas.json")
ENTIDADES = ROOT / "entidades"
nos_por_id = {n["id"]: n for n in grafo.get("nos", [])}
ents = entidades.get("entidades", [])

if not ents:
    erros.append("entities: dados/entidades.json holds no entities — build/entidades.py did not "
                 "run, and the site's pages are linking into an index that does not exist")

# 21 · the index and the disk say the same thing.
no_disco = set()
if ENTIDADES.exists():
    no_disco = {p.parent.relative_to(ROOT).as_posix() + "/"
                for p in ENTIDADES.rglob("index.html")
                if p.parent != ENTIDADES}
no_indice = {x["url"] for x in ents}
for falta in sorted(no_indice - no_disco):
    erros.append(f'entities: the index promises {falta} and there is no page at that path')
for sobra in sorted(no_disco - no_indice):
    erros.append(f'entities: {sobra} exists on disk and is not in the index — an orphan page is '
                 f'neither rebuilt nor removed when its entity leaves the graph')

# 22 · every linkable entity's ground is true.
for x in ents:
    f = x.get("fundamento")
    tem_bytes = bool(x.get("nos_bytes"))
    e_editor = bool((nos_por_id.get(x["no"]) or {}).get("publica"))
    if x.get("ligavel") and not f:
        erros.append(f'entities: {x["no"]} is marked linkable and has no ground — a link with no '
                     f'ground is a claim with no source')
    if f == "bytes" and not tem_bytes:
        erros.append(f'entities: {x["no"]} says its ground is the bytes and `nos_bytes` is '
                     f'empty')
    if f == "registo" and not e_editor:
        erros.append(f'entities: {x["no"]} says its ground is the register and the node '
                     f'publishes no frozen file at all')
    if f == "registo" and tem_bytes:
        erros.append(f'entities: {x["no"]} claims the weak ground while holding the strong one — '
                     f'when the name is in the bytes, the ground is `bytes`')
    # The ground and linkability are different things: a short name can be in the bytes (and so
    # has a ground) and still not be linkable, which is precisely what the length rule exists
    # to do. The gate checks linkability, not the ground.
    if x.get("ligavel") and len(x["nome"]) < 6:
        erros.append(f'entities: {x["no"]} has a {len(x["nome"])}-character name and is '
                     f'linkable — the published formula requires at least 6')

# 23 · the formula is obeyed on the generated pages.
MAX_POR_PAGINA = 1
por_url = {x["url"]: x for x in ents}
LIGACAO = re.compile(r'<a class="ent" href="([^"]+)">([^<]*)</a>')
nomes_por_url = {x["url"]: x["nome"] for x in ents}
for pag in sorted(ROOT.rglob("*.html")):
    rel = pag.relative_to(ROOT).as_posix()
    if "fontes/congeladas/" in rel or "/briefs/" in rel or "node_modules" in rel:
        continue
    texto = pag.read_text(encoding="utf-8")
    achados = LIGACAO.findall(texto)
    if not achados:
        continue
    contagem = {}
    for href, rotulo in achados:
        alvo = re.sub(r"^(\.\./)+", "", href)
        contagem[alvo] = contagem.get(alvo, 0) + 1
        esperado = nomes_por_url.get(alvo)
        # The text comes from HTML and is escaped; the index's name is the name. Comparing the
        # two without unescaping gave an error for every organisation with an «&» in its name,
        # which is a bug in the gate and not in the site — and that is what happened the first
        # time this gate ran.
        rotulo = _html.unescape(rotulo)
        if esperado is None:
            erros.append(f'{rel}: links to {alvo}, which is no entity path in the index')
        elif rotulo != esperado:
            erros.append(f'{rel}: links to {alvo} with the text «{rotulo}», and that entity\'s '
                         f'verbatim name is «{esperado}» — the formula links the name, not a '
                         f'variant of it')
        if alvo + "index.html" == rel:
            erros.append(f'{rel}: is an entity page and links to itself')
    for alvo, n in contagem.items():
        if n > MAX_POR_PAGINA:
            erros.append(f'{rel}: links {n} times to {alvo}; the published formula allows '
                         f'{MAX_POR_PAGINA} per page')
    if "<a class=\"ent\"" in texto:
        # A link inside another link is HTML each browser unpicks its own way.
        if re.search(r'<a\b[^>]*>(?:(?!</a>).)*<a class="ent"', texto, re.S):
            erros.append(f'{rel}: has an entity link nested inside another link')

# 24 · no Pessoa page says anything about the person.
verbatim = set()
for pp in pessoas_json.get("pessoas", []):
    for v in pp.values():
        if isinstance(v, str):
            verbatim.add(v)
for n in grafo.get("nos", []):
    for v in n.values():
        if isinstance(v, str):
            verbatim.add(v)
# A cell's value may contain an entity link — «Zero Risk Startup» on the page of whoever
# the event lists under it. So the cell's INNER html is captured and tags stripped before
# comparing: a pattern accepting only plain text would stop seeing exactly the cells that had
# just gained a link, and a gate that stops seeing half of what it guards guards nothing.
CAMPO = re.compile(r'<tr><th style="width:230px">(.*?)</th><td class="sm">(.*?)</td></tr>', re.S)
for x in ents:
    if x["tipo"] != "Pessoa":
        continue
    f = ROOT / x["url"] / "index.html"
    if not f.exists():
        continue
    for _rot, valor in CAMPO.findall(f.read_text(encoding="utf-8")):
        cru = _html.unescape(re.sub(r"<[^>]+>", "", valor))
        if cru not in verbatim:
            erros.append(f'{x["url"]}: the field table carries «{cru[:60]}», which is not a '
                         f'verbatim value from dados/pessoas.json nor from the graph node — a '
                         f'Pessoa page writes not one line about the person')


# --- 25. no agent comment was invented ------------------------------------------
# The `de` field is «<file path>#<key>[<index or id>]...». The gate opens the file and walks the
# path. If the path does not resolve, the comment walks back to nothing.
REF = re.compile(r"^([^#]+)#(.+)$")
PASSO = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)(?:\[([^\]]+)\])?")

def resolve(caminho):
    m = REF.match(caminho)
    if not m:
        return False, "não tem a forma <ficheiro>#<caminho>"
    f = ROOT / m.group(1)
    if not f.exists():
        return False, f"o ficheiro {m.group(1)} não existe"
    try:
        no = json.loads(f.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"{m.group(1)} não é JSON legível: {exc}"
    for chave, indice in PASSO.findall(m.group(2)):
        if not isinstance(no, dict) or chave not in no:
            return False, f"«{chave}» não existe em {m.group(1)}"
        no = no[chave]
        # `findall` returns "" and not None for an optional group that did not match. Treating
        # both as absence is what makes `…entregas[<id>].revisao` resolve to the end instead of
        # hunting for an item with id "" inside an object that is not a list.
        if not indice:
            continue
        if indice.isdigit():
            if not isinstance(no, list) or int(indice) >= len(no):
                return False, f"«{chave}[{indice}]» está fora do fim da lista"
            no = no[int(indice)]
        else:
            achado = next((x for x in (no if isinstance(no, list) else [])
                           if isinstance(x, dict) and x.get("id") == indice), None)
            if achado is None:
                return False, f"nenhum item de «{chave}» tem id «{indice}»"
            no = achado
    return True, ""

n_comentarios = 0
agentes_vistos = set()
for f in sorted(ARTIGOS.rglob("comentarios.json")):
    rel = f.relative_to(ROOT).as_posix()
    doc = json.loads(f.read_text(encoding="utf-8"))
    if not doc.get("derivado"):
        erros.append(f'{rel}: is not marked as derived. A hand-written comments file is '
                     f'fabricated provenance — this one is generated by build/comentarios.py and '
                     f'says where every entry came from')
    for c in doc.get("fluxo", []):
        n_comentarios += 1
        agentes_vistos.add(c.get("agente"))
        de = c.get("de")
        if not de:
            erros.append(f'{rel}: entry {c.get("id")} does not say where it came from')
            continue
        ok, porque = resolve(de)
        if not ok:
            erros.append(f'{rel}: entry {c.get("id")} says it comes from «{de}» and {porque}')
        if c.get("texto") is None:
            erros.append(f'{rel}: entry {c.get("id")} has no text')

# The aggregate has to agree with the sum of the folders: a console showing more work than
# happened is the same kind of lie as an invented comment, only in numbers.
agregado = carregar("comentarios.json")
if agregado and agregado.get("contagem") != n_comentarios:
    erros.append(f'dados/comentarios.json says {agregado.get("contagem")} entries and the '
                 f'article folders hold {n_comentarios}')

# No agent appears undeclared: an agent name nobody can place is an
# anonymous contributor to a publication whose entire argument is knowing who said what.
declarados = set((agregado or {}).get("agentes", {}))
for a in sorted(agentes_vistos - declarados):
    erros.append(f'comments: agent «{a}» appears in the stream and is not declared in '
                 f'dados/comentarios.json#agentes')


# --- 26. a construction run must earn the exemption it uses ---------------------
RUNS = ROOT / "redacao" / "runs"
n_runs = 0
for f in sorted(RUNS.glob("*.json")) if RUNS.exists() else []:
    r = json.loads(f.read_text(encoding="utf-8"))
    n_runs += 1
    if r.get("departamento"):
        continue                       # that one is checked by gate 12, in build/gates.py
    especie = r.get("especie")
    if not especie:
        erros.append(f'runs: {f.name} declares neither a department nor a species. Gate 12\'s '
                     f'exemption exists for the bootstrap session; a run claiming it has to say '
                     f'why')
        continue
    if especie != "construcao":
        continue
    for pasta in r.get("pastas_alteradas", []):
        if pasta.startswith("fontes/congeladas"):
            erros.append(f'runs: {f.name} declares itself a construction run and touched '
                         f'«{pasta}». Freezing a source is research work, and a run that does it '
                         f'declares itself as such or does not do it')
    if r.get("issues_movidos"):
        erros.append(f'runs: {f.name} declares itself a construction run and moved '
                     f'{len(r["issues_movidos"])} issue(s). Moving a card is a department\'s '
                     f'work, and every column has its own')
    for m in r.get("issues_movidos", []):
        if m.get("para") == "publicado":
            erros.append(f'runs: {f.name} put an issue into «publicado». That line belongs to '
                         f'the editor of record and to nobody else')
    if r.get("portoes") is not True:
        erros.append(f'runs: {f.name} recorded a version without saying the gates came back '
                     f'green')


# --- 34. code is in English -----------------------------------------------------
# Portuguese function words that essentially never appear in English prose. Matching on function
# words rather than on accents is deliberate: a comment can be entirely Portuguese without a single
# accented character, and an English comment may legitimately quote an accented Portuguese name.
PT_PALAVRAS = re.compile(
    r"\b(?:não|são|está|estão|é|foi|ser|tem|têm|uma|uns|umas|que|para|com|por|"
    r"como|quando|onde|porque|porquê|isso|isto|aquilo|cada|todos|todas|"
    r"ficheiro|ficheiros|página|páginas|portão|portões|afirmação|afirmações|"
    r"fonte|fontes|leitor|leitura|escrever|escrita|nenhum|nenhuma|mesmo|mesma|"
    r"sítio|coisa|coisas|dele|dela|deles|delas|pelo|pela|nos|nas|aos|às)\b",
    re.IGNORECASE)

# The exceptions, declared rather than hidden. Each one says why.
EXCEPCOES = {
    # Portuguese identifiers this pipeline is built on. These are names, not prose, and renaming
    # them is the scheduled data-key migration described in docs/guidance/language.md.
    "identificadores": re.compile(
        r"\b(?:dados|fontes|congeladas|redacao|artigos|seccoes|entidades|comentarios|"
        r"historias|registo|grafo|ontologia|verificacoes|entregas|aviso|equipa|lexico|"
        r"organizacoes|pessoas|sessoes|temas|manifesto|mudancas|excluidas|"
        r"estado|fonte|nome|texto|afirmacoes|proveniencia|artigo|seccao|slug|"
        r"publicado|verificado|rascunho|procurado|congelado|confirmada|disputada|"
        r"nao_encontrada|por_verificar|fonte_inacessivel|departamento|especie|construcao|"
        r"arranque|pesquisa|verificacao|editor|pastas_alteradas|issues_movidos|portoes|"
        r"versao|quando|agente|leitura|verbo|inverso|dominio|alcance|tudo|paginas|"
        r"mesa|bancadas|quadro|colunas|cartoes|carga|correio|runs|issues|decisoes|"
        r"chrome|build|gates|extract|entidade|comentario|api|newsroom)\b", re.IGNORECASE),
}


def _comentarios_de(caminho, texto):
    """Every comment and docstring in a file, as (line number, text).

    Only comments are read. Portuguese inside a STRING is usually a label the reader sees, which is
    exactly where Portuguese belongs — failing on those would be the gate telling the site to stop
    being Portuguese.

    AND A TRIPLE-QUOTED STRING IS NOT A DOCSTRING. This gate's first version matched every
    triple-quoted block with a regular expression and flagged eleven page templates in
    build/build.py: blocks of HTML holding the Portuguese a reader sees, assigned to a variable. It
    was telling the site to stop being Portuguese. The parser knows the difference between a
    docstring and a string that merely happens to be long, so the answer comes from `ast` rather
    than from a pattern."""
    saida = []
    if caminho.suffix == ".py":
        # `tokenize` and not a split on "#". The first version of this gate split every line on the
        # first "#" and guessed at quoting, which read the `## heading` lines INSIDE the llms.txt
        # template in build/chrome.py as comments — markdown headings in Portuguese content, which
        # is exactly where Portuguese belongs. Same family of mistake as matching docstrings with a
        # regex: the tokenizer already knows what a comment is, so it is asked.
        try:
            for tok in tokenize.generate_tokens(io.StringIO(texto).readline):
                if tok.type == tokenize.COMMENT:
                    saida.append((tok.start[0], tok.string.lstrip("#")))
        except (tokenize.TokenError, IndentationError, SyntaxError):
            pass
        try:
            arvore = ast.parse(texto)
        except SyntaxError:
            return saida
        for no in ast.walk(arvore):
            if not isinstance(no, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            doc = ast.get_docstring(no, clean=False)
            if not doc:
                continue
            primeiro = no.body[0]
            for i, linha in enumerate(doc.split("\n")):
                saida.append((getattr(primeiro, "lineno", 1) + i, linha))
    else:
        for m in re.finditer(r"/\*(.*?)\*/", texto, re.S):
            n = texto[:m.start()].count("\n") + 1
            for i, linha in enumerate(m.group(1).split("\n")):
                saida.append((n + i, linha))
        for n, linha in enumerate(texto.split("\n"), 1):
            m = re.search(r"(?<!:)//(.*)$", linha)
            if m and not re.search(r"https?:$", linha[:m.start()]):
                saida.append((n, m.group(1)))
    return saida


CODIGO = []
# `assets/` is here as well as `assets/components/`, and it was the gap that mattered. The gate
# shipped covering the components and missing the four scripts one directory above them — the
# bridge, the observer, the graph viewer and the chat engine, about 240 comment lines and some of
# the most consequential prose in this repository, since two of them are about what leaves the
# reader's browser. A gate whose scope stops one directory short of the code that matters is a gate
# that reports a number instead of holding a line.
for base, padroes in ((ROOT / "build", ("*.py",)),
                      (ROOT / "admin" / "build", ("*.js", "*.mjs")),
                      (ROOT / "assets", ("*.js",)),
                      (ROOT / "assets" / "components", ("*.js",))):
    if base.exists():
        for pad in padroes:
            CODIGO.extend(sorted(base.rglob(pad)))
# `assets/*.js` and `assets/components/**/*.js` overlap, because rglob on the parent already
# reaches the children. Counted twice, a file would also be REPORTED twice, and a gate that says
# «two files» about one file is a gate nobody trusts the numbers of.
CODIGO = sorted(set(CODIGO))
# Vendored third-party code is not this repository's code and is not rewritten to our taste: the
# whole reason Cytoscape sits in assets/vendor/ is that we do not depend on somebody else serving
# it, and editing it would break that argument in the other direction.
CODIGO = [f for f in CODIGO if "/vendor/" not in f.as_posix()]

# THE FILES THIS GATE MAY NOT DEMAND A FIX TO. build/gates.py, build/entregas.py and build/pdf.py
# are in the deny list of .claude/settings.json, so no agent here can edit them — and a gate that
# fails the build over a file the agent is forbidden to touch is not a gate, it is a deadlock. They
# carry Portuguese comments written before the rule was enforced. They are named here rather than
# quietly skipped, counted in the summary line, and they are the editor's to clear: only the editor
# can lift a deny-list entry, and until then this is an honest exemption rather than a hidden one.
DENY_LIST = {"build/gates.py", "build/entregas.py", "build/pdf.py"}
pendentes_do_editor = []

n_codigo, n_linhas_conferidas = 0, 0
for f in CODIGO:
    if "__pycache__" in f.as_posix():
        continue
    if f.relative_to(ROOT).as_posix() in DENY_LIST:
        pendentes_do_editor.append(f.relative_to(ROOT).as_posix())
        continue
    n_codigo += 1
    rel = f.relative_to(ROOT).as_posix()
    achados = []
    for n, linha in _comentarios_de(f, f.read_text(encoding="utf-8")):
        n_linhas_conferidas += 1
        limpo = EXCEPCOES["identificadores"].sub(" ", linha)
        limpo = re.sub(r"`[^`]*`", " ", limpo)          # file names and code between backticks
        # A Portuguese LABEL quoted inside an English sentence is not a Portuguese comment. This
        # repository writes such labels in guillemets — «Esta semana em Lisboa» is the name of a
        # front-page section, and the sentence explaining it is in English. Without this, the gate
        # would demand that an English comment stop naming the Portuguese thing it describes.
        limpo = re.sub(r"«[^»]*»", " ", limpo)
        palavras = set(m.group(0).lower() for m in PT_PALAVRAS.finditer(limpo))
        if len(palavras) >= 2:
            achados.append((n, sorted(palavras)[:4], linha.strip()[:70]))
    if achados:
        n, palavras, amostra = achados[0]
        erros.append(f'{rel}:{n}: comment or docstring is in Portuguese '
                     f'({", ".join(palavras)}) — "{amostra}". CLAUDE.md: code and comments are in '
                     f'English. {len(achados)} line(s) in this file. See '
                     f'docs/guidance/language.md')


# --- 35. every agent that touches this site is named ---------------------------
agentes = carregar("agentes.json")
AGENTES_DIR = ROOT / "agents"
# The register is dados/agentes.json, written by build/newsroom_team.py. The mandate files under agents/
# are RENDERED from it by build/mandatos.py. Two sessions answered the same ask on the same
# afternoon — one by writing the files, one by building the register — and two copies of a mandate
# diverge on the day somebody edits one. The register won; this gate holds the rendering to it.
registados = {a["id"] for a in agentes.get("agentes", [])}
curtos = {a.get("id_curto") for a in agentes.get("agentes", [])} | registados
if not registados:
    erros.append("agents: dados/agentes.json registers nobody. Every agent that may change this "
                 "site is named there, and its mandate is rendered from that entry")
for a in agentes.get("agentes", []):
    for ficheiro in ("ROLE.md", "MANDATE.md"):
        alvo = AGENTES_DIR / a["id"] / ficheiro
        if not alvo.exists():
            erros.append(f'agents/{a["id"]}: registered in dados/agentes.json and has no '
                         f'{ficheiro}. Run build/mandatos.py — a named agent without a written '
                         f'mandate is a name, not a boundary')
            continue
        texto = alvo.read_text(encoding="utf-8")
        if "DERIVED FILE" not in texto:
            erros.append(f'agents/{a["id"]}/{ficheiro}: is not marked as derived. These files are '
                         f'rendered from the register; a hand-written one is a second copy of a '
                         f'mandate, and two copies diverge')
        # The drift check that makes this worth having: a mandate that no longer says what the
        # register says reads as authoritative while being wrong.
        for campo in ("dominio", "missao", "afirmacao_central"):
            valor = (a.get(campo) or "").strip()
            if ficheiro == "ROLE.md" and valor and valor not in texto:
                erros.append(f'agents/{a["id"]}/ROLE.md: has drifted from the register — '
                             f'`{campo}` no longer matches. Re-run build/mandatos.py')
                break
if AGENTES_DIR.exists():
    for d in sorted(p for p in AGENTES_DIR.iterdir() if p.is_dir()):
        if d.name not in registados:
            erros.append(f'agents/{d.name}/ exists on disk and is not in dados/agentes.json — an '
                         f'unregistered mandate is one no gate can check')
for f in sorted(RUNS.glob("*.json")) if RUNS.exists() else []:
    r = json.loads(f.read_text(encoding="utf-8"))
    for campo in ("agente", "departamento"):
        quem = r.get(campo)
        if quem and quem not in curtos and campo == "agente":
            erros.append(f'runs: {f.name} names the agent «{quem}», which is not in '
                         f'dados/agentes.json')


# ==============================================================================================
#  36-38 · THE GATES ABOUT MORE THAN ONE SESSION AT A TIME
#
#  Three sessions work on this repository at once, and every one of these gates exists because
#  something was actually lost or duplicated between them — not because a collision was imagined.
#  They are in one block because they share a cause: a shared counter with no lock, and a merge
#  that succeeds while silently dropping work.
#
#  What they do NOT do is prevent a collision. Nothing here can: two sessions that choose the same
#  number at the same moment both choose it correctly, and the loser only finds out on push. What
#  they do is make the collision LOUD at the earliest moment it is knowable, which is the most a
#  repository can offer. See docs/guidance/concurrent-sessions.md.
# ==============================================================================================

#  36 · NO TWO GATES SHARE A NUMBER. Two sessions added gates the same afternoon and both started
#       at 27. The build was green on each branch and stayed green after the merge, because a gate
#       number is a comment: nothing reads it, so nothing checks it, and for a while this
#       repository had two gate 27s saying different things.
# Three files, three ways of writing a gate number — which is itself part of why two sessions
# collided on 27. The scanner is tolerant rather than strict on purpose: a declaration it fails to
# recognise makes this gate under-report, which is a worse gate; a declaration it recognises
# wrongly would make it fail a build for nothing, which is a broken one. The block immediately
# above had to be added to this list when it was written — it did not match, and the gate said
# «next free: 36» while sitting under a heading that reads 36-38. That is the failure this gate is
# about, caught by the gate itself before it shipped.
DECL = [
    re.compile(r"^\s{0,4}(\d{1,3})\s+·"),          # docstring:  «  NN · TITLE»
    re.compile(r"^#\s{0,4}(\d{1,3})\s+·"),         # comment:    «#  NN · TITLE»
    re.compile(r"^#\s*-+\s*(\d{1,3})\.\s"),       # section:    «# --- NN. title ---»
    re.compile(r"^/\*\s*-+\s*(\d{1,3})\.\s"),     # javascript: «/* --- NN. title ---»
]
# NOT ONLY THE PYTHON GATES. This list held `build/gates*.py` and nothing else, and the two gates
# that live in the browser gate and the site gate were therefore invisible to the registry — so a
# session could take a number the browser gate already held and this gate would say it was free.
# It happened on the next merge: a gate 36 was written into admin/build/render.mjs while gate 36
# above already existed, and nothing here noticed. A registry that covers some of the addresses is
# a registry that hands out addresses twice.
FICHEIROS_DE_PORTAO = (sorted((ROOT / "build").glob("gates*.py"))
                       + [f for f in [ROOT / "admin" / "build" / "render.mjs",
                                      ROOT / "admin" / "build" / "validate.js"] if f.exists()])
reclamado = {}
for f in FICHEIROS_DE_PORTAO:
    rel = f.relative_to(ROOT).as_posix()
    for linha in f.read_text(encoding="utf-8").split("\n"):
        for padrao in DECL:
            m = padrao.match(linha)
            if not m:
                continue
            n = int(m.group(1))
            if not 1 <= n <= 200:       # a year, a hex value, a width — not a gate number
                continue
            reclamado.setdefault(n, set()).add(rel)

for n in sorted(reclamado):
    if len(reclamado[n]) > 1:
        erros.append(f'gates: number {n} is claimed by {" and ".join(sorted(reclamado[n]))}. '
                     f'A gate number is an address; two gates at one address means one of them '
                     f'cannot be cited, and the next session will take {n} again')
proximo_portao = (max(reclamado) + 1) if reclamado else 1

#  37 · A CLASS A COMPONENT PUTS ON THE DOCUMENT HAS A RULE IN THE STYLESHEET. `<pt-chat>` sets
#       `pt-chat-aberto` on <html>, and assets/site.css turns it into a column. A merge brought a
#       wholesale rewrite of that stylesheet, git auto-merged it with NO conflict, and the four
#       rules went with it. Nothing failed: the component still loaded, still reached «pronto»,
#       still had a shadow root full of text — and the panel simply lay across the article again.
#       A coupling that crosses a file boundary and is checked by nothing is a coupling that the
#       next wholesale rewrite deletes in silence.
FORA_DA_SOMBRA = re.compile(
    r"document\.(?:documentElement|body)\.classList\.(?:add|toggle)\(\s*['\"]([\w-]+)['\"]")
FOLHA = ROOT / "assets" / "site.css"
css = FOLHA.read_text(encoding="utf-8") if FOLHA.exists() else ""
acoplamentos = 0
for f in sorted((ROOT / "assets" / "components").rglob("*.js")):
    rel = f.relative_to(ROOT).as_posix()
    for classe in sorted(set(FORA_DA_SOMBRA.findall(f.read_text(encoding="utf-8")))):
        acoplamentos += 1
        if not re.search(r"[.\[]" + re.escape(classe) + r"\b", css):
            erros.append(
                f'{rel}: puts «{classe}» on the document and assets/site.css has no rule for it. '
                f'A component cannot style outside its own shadow root, so this class does '
                f'nothing — either the rule was lost in a merge, or it was never written')

#  38 · THE RELEASE HISTORY IS A SET, AND THE VERSION IS ITS NEWEST MEMBER. Two sessions took
#       v0.13.0 within the hour. The site gate checks the table HAS a row for version.txt; it does
#       not check there is only one, nor that the number is ahead of every other. It also does not
#       notice a note file that does not exist, because build/versoes.py skips those silently —
#       which turns a mistyped path into a release that quietly has no note.
IDX = ROOT / "admin" / "versions.json"
versao_actual = (ROOT / "admin" / "build" / "version.txt").read_text(encoding="utf-8").strip()
n_notas = 0
if IDX.exists():
    idx = json.loads(IDX.read_text(encoding="utf-8"))
    entradas = idx.get("versoes", [])
    n_notas = len(entradas)
    vistos = {}
    for v in entradas:
        vistos.setdefault(v["versao"], 0)
        vistos[v["versao"]] += 1
        if not (ROOT / v["ficheiro"]).exists():
            erros.append(f'admin/versions.json: {v["versao"]} names {v["ficheiro"]}, which does '
                         f'not exist. build/versoes.py skips a missing note without a word, so '
                         f'this release would ship with an empty row')
    for v, n in sorted(vistos.items()):
        if n > 1:
            erros.append(f'admin/versions.json: {v} appears {n} times. Two sessions each wrote a '
                         f'note for it, and a merge kept both — one of the two releases is now '
                         f'unaddressable')
    if idx.get("contagem") != n_notas:
        erros.append(f'admin/versions.json: contagem says {idx.get("contagem")} and there are '
                     f'{n_notas} notes. Run build/versoes.py, which counts it')

    def chave(v):
        return tuple(int(x) for x in v.lstrip("v").split("."))

    numeros = [v["versao"] for v in entradas]
    if versao_actual in numeros and numeros:
        mais_alto = max(numeros, key=chave)
        if chave(versao_actual) < chave(mais_alto):
            erros.append(f'admin/build/version.txt says {versao_actual} and the history already '
                         f'holds {mais_alto}. A release number goes forward; another session took '
                         f'this one first, so take the next free one')


#  43 · THE SPINE IS THE SAME EVERYWHERE. The four fixed questions live once, in
#       00__the-spine.json; they must appear verbatim in both question cards and on
#       the page that renders them.
#  42 · A DERIVED PROMPT PAGE CANNOT DRIFT FROM ITS SOURCE. The interview prompts
#       live once as markdown; newsroom/interviews.html renders them. The page has to
#       carry the current text and the recorded hash has to be today's.
#  41 · THE GUIDANCE HAS ADDRESSES, AND THE BRIEFING'S LINKS RESOLVE. Every document under
#       docs/guidance/ is rendered to a page of its own, and everything .claude/ONBOARDING.md
#       points at exists. For most of this site's life the guidance was reachable only as
#       `/newsroom/docs.html#docs/guidance/language.md` — a fragment, which is not an address: it
#       cannot be cited, it is not in the sitemap, and anything fetching it gets the shell of a
#       document browser rather than the document. llms.txt, the file this site tells machines to
#       read first, mentioned the guidance zero times. A briefing whose links have rotted is worse
#       than no briefing, because it reads as current.
GUIA_MD = ROOT / "docs" / "guidance"
GUIA_HTML = ROOT / "newsroom" / "guidance"
n_guia = 0
if GUIA_MD.exists():
    for md in sorted(GUIA_MD.glob("*.md")):
        n_guia += 1
        alvo = GUIA_HTML / f"{md.stem}.html"
        if not alvo.exists():
            erros.append(f'docs/guidance/{md.name}: has no page at '
                         f'newsroom/guidance/{md.stem}.html. Run build/guia.py — a guidance '
                         f'document reachable only as a file path cannot be cited by anything')
    if n_guia and "newsroom/guidance/index.html" not in (ROOT / "llms.txt").read_text(
            encoding="utf-8"):
        erros.append('llms.txt: does not point at the guidance. It is the file this site tells a '
                     'machine to read first, and an agent arriving to CHANGE the site finds no '
                     'route to the rules it is about to break')

ONBOARD = ROOT / ".claude" / "ONBOARDING.md"
n_ligacoes = 0
if ONBOARD.exists():
    texto = ONBOARD.read_text(encoding="utf-8")
    for url in re.findall(r"https://pt\.newsroom\.sgit\.ai(/[\w./-]+)", texto):
        n_ligacoes += 1
        alvo = ROOT / url.lstrip("/")
        if not alvo.exists() and not (alvo / "index.html").exists():
            erros.append(f'.claude/ONBOARDING.md: links to {url}, which this build does not '
                         f'produce. The briefing is the first thing a session reads')
    # A template is not a path: the briefing tells a session to write `admin/versions/<version>.md`
    # and there is no such file, correctly. The angle brackets are the site's own convention for a
    # placeholder — the same one llms.txt uses for `artigos/<yyyy>/<mm>/<dd>/<slug>/` — so they are
    # what this skips, rather than a list of names that would go stale.
    for caminho in re.findall(r"`([\w./<>-]+\.(?:md|py|json|js))`", texto):
        if "<" in caminho or ">" in caminho:
            continue
        if "/" not in caminho and caminho != "CLAUDE.md":
            continue
        n_ligacoes += 1
        if not (ROOT / caminho).exists():
            erros.append(f'.claude/ONBOARDING.md: names `{caminho}`, which does not exist')
else:
    erros.append('.claude/ONBOARDING.md is missing. It is what a session is pointed at on startup '
                 'by the SessionStart hook, and the hook would be telling it to read nothing')


# --- 42. o texto derivado das entrevistas não pode divergir da sua fonte --------
# The interview prompts live once, as markdown under briefs/pack/09__interviews/, and
# newsroom/interviews/ RENDERS them so a person can copy a prompt without leaving the page. A
# derived file with no gate is a second copy with extra steps — the lesson gate 28 learned from the
# agent mandates — so this checks the rendered page still carries each prompt's current text, and
# that the hash recorded beside it is the hash of what is on disk today.
f_ent = DADOS / "interviews.json"
pag_ent = ROOT / "newsroom" / "interviews.html"
if f_ent.exists():
    doc_ent = json.loads(f_ent.read_text(encoding="utf-8"))
    html_ent = pag_ent.read_text(encoding="utf-8") if pag_ent.exists() else ""
    if not html_ent:
        erros.append('newsroom/interviews.html is missing and dados/interviews.json exists '
                     '— the prompts have a source and no page rendering it')
    for peca in doc_ent["pieces"]:
        origem = ROOT / peca["path"]
        if not origem.exists():
            erros.append(f'interviews: {peca["path"]} is named in dados/interviews.json and '
                         f'does not exist')
            continue
        agora = hashlib.sha256(origem.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
        if agora != peca["sha256"]:
            erros.append(f'interviews: {peca["path"]} changed since dados/interviews.json was '
                         f'written — run build/interviews.py, then build/build.py')
        # Sampled across the WHOLE file, not once at the top. The first version took a single
        # line and passed a page whose middle had been hand-edited — a gate that checks one line
        # certifies one line. Lines carrying markup or backticks are skipped because they are
        # escaped and reflowed on the way into the page; the rest must appear verbatim.
        linhas = [l.strip() for l in origem.read_text(encoding="utf-8").split("\n")
                  if len(l.strip()) > 40 and "<" not in l and "`" not in l and "|" not in l]
        amostras = linhas[:: max(1, len(linhas) // 8)][:8] if linhas else []
        em_falta = [a for a in amostras if html_ent and escape(a) not in html_ent]
        if em_falta:
            erros.append(f'interviews: the page is missing {len(em_falta)} of {len(amostras)} '
                         f'sampled lines of {peca["path"]} (first: '
                         f'«{em_falta[0][:60]}…») — it was hand-edited, or not rebuilt')


# --- 43. the spine is on the page and in the cards, and it is the same --------
# The four fixed questions are rendered at the top of the interviews page from
# 00__the-spine.json, and written out again with their commentary in the two question cards. Two
# places, one meaning — which is the shape that drifts. So: every question in the spine has to
# appear verbatim in BOTH cards (English in the English card, Portuguese in the Portuguese one) and
# on the page itself. Gate 42 already ties the cards to the page; this ties the spine to the cards.
f_spine = ROOT / "briefs" / "pack" / "11__startup-interviews" / "00__the-spine.json"
if f_spine.exists():
    spine = json.loads(f_spine.read_text(encoding="utf-8"))
    cartao_en = (ROOT / "briefs" / "pack" / "11__startup-interviews"
                 / "01__the-questions.en.md").read_text(encoding="utf-8")
    cartao_pt = (ROOT / "briefs" / "pack" / "11__startup-interviews"
                 / "02__as-perguntas.pt.md").read_text(encoding="utf-8")
    pag_iv = ROOT / "newsroom" / "interviews.html"
    html_iv = pag_iv.read_text(encoding="utf-8") if pag_iv.exists() else ""
    todas = list(spine["perguntas"]) + [spine["fecho"]]
    for q in todas:
        if q["en"] not in cartao_en:
            erros.append(f'spine: «{q["en"][:52]}…» is not in 01__the-questions.en.md — the card '
                         f'and the spine have drifted')
        if q["pt"] not in cartao_pt:
            erros.append(f'spine: «{q["pt"][:52]}…» is not in 02__as-perguntas.pt.md — the card '
                         f'and the spine have drifted')
        if html_iv and escape(q["en"]) not in html_iv:
            erros.append(f'spine: «{q["en"][:52]}…» is not on newsroom/interviews.html — run '
                         f'build/interviews.py, then build/newsroom.py')


# --- relatório -----------------------------------------------------------------
if erros:
    print(f"gates 16-26, 34-38, 41-43: {len(erros)} error(s)")
    for x in erros:
        print("  ✗", x)
    sys.exit(1)

pub = sum(1 for m in metas
          if json.loads(m.read_text(encoding="utf-8")).get("estado") == "publicado")
com_prosa = sum(1 for m in metas if (m.parent / "artigo.md").exists())
print(f"gates 16-26, 34-38, 41-43: OK — {len(metas)} articles in dated folders "
      f"({com_prosa} with prose, {pub} published), every path agreeing with its date and slug, "
      f"every claim walking back to the register, {len(AS_OITO)} sections with an editorial "
      f"record, a back office in English citing no evidence, "
      f"{len(ents)} entities with a page and a checked ground, "
      f"{n_comentarios} agent comments each walking back to a file, "
      f"{n_runs} run records with their boundary checked, "
      f"{n_codigo} code files in English "
      f"({len(pendentes_do_editor)} exempt as deny-listed: "
      f"{', '.join(pendentes_do_editor) or 'none'}), "
      f"{len(registados)} named agents with a written mandate, "
      f"{len(reclamado)} gate numbers each claimed once (next free: {proximo_portao}), "
      f"{acoplamentos} document-level class(es) set by a component, each with a rule, "
      f"{n_notas} releases each addressable once, at {versao_actual}, "
      f"{n_guia} guidance pages with an address and {n_ligacoes} briefing links that resolve")

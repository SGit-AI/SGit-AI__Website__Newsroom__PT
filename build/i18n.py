#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the translation memory, and the reason it stays cheap.

    python3 build/i18n.py extract          walk the sources, write dados/i18n/fontes.json
    python3 build/i18n.py status           per locale: done, missing, words to do, orphaned
    python3 build/i18n.py todo <locale>    ONLY the missing segments, as a batch to translate
    python3 build/i18n.py apply <locale> <file.json>   write translations back, hash-checked

THE PROBLEM THIS SOLVES. A naive multilingual build translates every rendered page into every
locale on every build: 186 101 words x 3 locales, again and again, and the bill grows with content
x languages x how often anyone builds. That is the wrong denominator. Translation should cost
what CHANGED, not what EXISTS.

THE FOUR DECISIONS THAT MAKE IT CHEAP, in order of how much they save.

1. TRANSLATE THE SOURCE, NEVER THE RENDER. The rendered site is 186 101 words. The prose behind
   it is a small fraction of that; the rest is names, hashes, dates, byte counts, source ids and
   frozen excerpts, generated from data and none of it translatable. Translating at the source
   layer is a large multiple cheaper than translating HTML, and it is also the only correct place:
   a rendered page mixes prose that must be translated with evidence that must never be.

2. THE KEY IS THE HASH OF THE SOURCE TEXT. A segment's identity is sha256(normalised source), so
   changed source produces a DIFFERENT key. There is no such thing as a stale translation here: a
   lookup either hits the translation of exactly this text, or it misses and the segment is
   reported missing. Staleness is not a flag somebody has to remember to set — it is a cache miss,
   and the gate counts cache misses.

3. IDENTICAL TEXT IS ONE SEGMENT. The chrome — navigation, the footer, the provenance line, the
   state words — appears on all 247 pages and hashes once. Translate it once and every page in
   that locale has it. The same holds for a sentence repeated across data files.

4. DENY, DO NOT ALLOW. The data layer is translated BY DEFAULT and a short list says what never
   is. The other way round — a list of fields that ARE prose — is the version that rots: a new
   field added next month falls silently out of every locale and nobody finds out, because an
   untranslated page looks like a page. Deny-by-default fails the other way: a field that should
   not have been translated turns up as a wasted segment in the next `todo`, where somebody reads
   it, and one line fixes it forever. Prefer the failure you can see.

EVIDENCE IS AN OBJECT, NOT A FIELD. Any object carrying a `sha256` is a record of somebody else's
bytes; nothing inside it is translated, at any depth, whatever its fields are called. One
structural rule instead of a growing list of field names, and it protects a field added to a
source record on the day it appears.

WHAT IS NEVER TRANSLATED, and this is a correctness rule before it is a cost one:

  * frozen excerpts and quotations — evidence is not translated; rules 1 and 3 of CLAUDE.md
  * verbatim names of people, organisations and sessions — a transcription is a claim
  * the ontology's verbs and their readings — rule 6, the graph reads aloud in Portuguese
  * ids, hashes, dates, numbers, file paths, published formulas, code

WHAT THIS FILE DOES NOT DO. It does not call a model. It prepares exact batches and verifies what
comes back. Whoever translates — an agent session, a service, a person — reads `todo`, returns
JSON, and `apply` refuses anything whose source hash it does not recognise.
"""
import ast
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dados"
STORE = DATA / "i18n"

# The locales this site is prepared to serve. `pt` is the source language of the newsroom's own
# writing; an item may declare a different original, and then `pt` is itself a translation.
LOCALES = ["en-gb", "fr", "de"]
SOURCE_DEFAULT = "pt"
TODAS_AS_LINGUAS = {SOURCE_DEFAULT, "en", "en_gb", "pt_pt"} | set(LOCALES) | {
    lc.replace("-", "_") for lc in LOCALES}

# Keys whose values are evidence, names, machine facts or published formulas. Never translated, at
# any depth. This list is the whole allowance for judgement in the data layer: everything else is
# treated as prose and sent.
NEVER = {
    # evidence and its bookkeeping
    "excerto", "excerpt", "texto_do_excerto", "sha256", "bytes", "congelada", "ficheiro", "file",
    "path", "caminho", "localizador", "locator", "url", "consultas",
    # verbatim names and titles: a transcription is a claim
    "nome", "name", "titulo_verbatim", "cargo_listado", "organizacao_listada", "publicador",
    "rotulo", "agente_verbatim", "modelo",
    # the graph reads aloud in Portuguese — rule 6
    "verbo", "inverso", "leitura", "leitura_inversa",
    # machine facts
    "id", "slug", "data", "date", "obtida", "publicado_em", "commit", "versao", "version",
    "lingua", "language", "schema", "formula", "erros_de_esquema", "versao_do_site_de_origem",
}

# The back office is not translated. These files feed /newsroom/ — the review board, the editor's
# inbox, the run records, the agent register, the design log, the delivery quarantine. They have
# exactly one reader, the editor of record, and the editor of record reads Portuguese. Translating
# the review board into German is paying to translate a to-do list nobody will open, and it is over
# half the words in the data layer.
#
# The grain is deliberate and is the fifth decision: a DENYLIST OF FILES, coarse and stable, plus
# DENY-BY-DEFAULT WITHIN a file, fine and structural. Both fail the same way round — a new data
# file, like a new field, is translated on the day it appears and shows up in the next `todo` for
# somebody to read. Nothing ever falls silently out of a locale.
FORA_DO_AMBITO = {
    "agentes.json", "comentarios.json", "correio.json", "desenho.json", "en-migration.json",
    "entregas.json", "equipa.json", "interviews.json", "pontes.json", "quadro.json",
    "redacao.json", "review.json", "transferencias.json",
}

# Builders that print to a console or write machine files, never a reader's page. Their Portuguese
# is diagnostics — a gate's complaint, a run's log line — and translating it would bill the site
# for text no visitor will ever see. `graph.py` is here because the prose it writes lands in
# dados/ontologia.json and is collected at the data layer instead; collecting it twice would pay
# for it twice.
NAO_RENDERIZA = {
    "i18n.py", "locales.py", "gates.py", "gates_artigos.py", "gates_desenho.py", "before_push.py",
    "extract.py", "migrate_to_english.py", "pdf.py", "tudo.py", "graph.py",
}

ACENTOS = re.compile("[" + "".join(chr(c) for c in (
    0xE1, 0xE0, 0xE2, 0xE3, 0xE9, 0xEA, 0xED, 0xF3, 0xF4, 0xF5, 0xFA, 0xE7,
    0xC1, 0xC0, 0xC2, 0xC3, 0xC9, 0xCA, 0xCD, 0xD3, 0xD4, 0xD5, 0xDA, 0xC7)) + "]")


def normalise(s):
    """One text, one hash. Collapse whitespace and normalise unicode so that a reflowed paragraph
    is not mistaken for a changed one — reflowing costs nothing to do and would otherwise cost a
    retranslation of every segment in the file."""
    return unicodedata.normalize("NFC", " ".join(str(s).split()))


def key(s):
    return hashlib.sha256(normalise(s).encode("utf-8")).hexdigest()[:16]


def translatable(s):
    """A segment worth sending: prose a translator can act on, and nothing a translator would hand
    straight back. Structural, so it holds for fields nobody has thought of yet."""
    s = normalise(s)
    if len(s) < 12 or len(s.split()) < 2:
        return False
    if re.fullmatch(r"[\d\s\W]+", s):                       # numbers and punctuation only
        return False
    if re.fullmatch(r"[a-f0-9]{8,}", s):                    # a hash
        return False
    if re.fullmatch(r"[\w./*_ -]+\.(py|js|json|md|html|css|txt|mjs|tpl)", s):
        return False                                        # a path, spaces and all
    if s.startswith(("http://", "https://", "/", "<", "site:", "dados/", "build/", "fontes/")):
        return False
    if "{" in s:                                            # a template with a hole in it
        return False
    if not ACENTOS.search(s) and not re.search(r"\b(de|da|do|que|não|uma|para|com|é)\b", s):
        return False                                        # no Portuguese in it to translate
    return True


MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro")
DIAS = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira",
        "sábado", "domingo")


def gerado(s):
    """Text a builder COMPOSED from data rather than wrote: a date line, a version badge, a count.
    It must not enter the memory, and the reason is the one that decides whether this whole design
    stays cheap. «Lisboa · segunda-feira, 14 de setembro de 2026» is a different string tomorrow, so
    its hash is different tomorrow, so a translation of it is a cache miss for ever and the site
    pays for the same sentence every day it is built. That is the exponential growth this
    architecture exists to avoid, arriving through the back door.

    Generated text is localised by FORMATTING it in the target language, which is a function
    somebody writes once, not a segment somebody translates daily. Until that function exists these
    runs stay Portuguese, and the coverage report counts them as `generated` rather than as
    `missing`, because calling them missing would invite exactly the wrong fix."""
    b = normalise(s).lower()
    if any(m in b for m in MESES) or any(d in b for d in DIAS):
        return True
    if re.search(r"\bv\d+\.\d+\.\d+", b) or re.search(r"\b\d{4}-\d{2}-\d{2}\b", b):
        return True
    # A count of things this site holds. The unit nouns are named rather than guessed, because the
    # list has to be auditable: every one of them is something build/*.py counts and prints.
    if re.search(r"\b\d+\s+(arestas|nós|nos|páginas|paginas|ficheiros|fontes|afirmações|"
                 r"afirmacoes|itens|linhas|caracteres|bytes|segmentos|entregas|dias)\b", b):
        return True
    digitos = sum(c.isdigit() for c in b)
    if digitos and digitos / len(b) > 0.12:
        return True
    return False


_VERBATIM = None


def verbatim():
    """The strings that stay in the source language on every page in every language, collected from
    the data rather than typed: the ontology's verbs and the sentences they read as, every entity,
    person and organisation name, and every frozen excerpt.

    Rule 6 of CLAUDE.md is why the verbs are here and it is not negotiable: «the graph reads aloud
    in Portuguese», and an English page showing an English edge label would be showing a different
    graph. The names are here because a transcription is a claim. The excerpts are here because
    evidence is not translated.

    A run that matches one of these is neither translated nor missing — it is correct as it stands,
    and counting it as missing would set a coverage target that the site must never reach."""
    global _VERBATIM
    if _VERBATIM is not None:
        return _VERBATIM
    fora = set()

    def ler(nome):
        f = DATA / nome
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

    ont = ler("ontologia.json") or {}
    for a in ont.get("arestas", []) + ont.get("tipos", []):
        for campo in ("verbo", "inverso", "leitura", "leitura_inversa"):
            v = a.get(campo)
            if isinstance(v, str):
                fora.add(normalise(v))
                # A reading is stored as a template, «{s} é organizado por {t}»; what reaches the
                # page is the middle of it, with the names substituted in around it.
                for pedaco in re.split(r"\{[st]\}", v):
                    if normalise(pedaco):
                        fora.add(normalise(pedaco))

    for nome, chave, campo in (("entidades.json", "entidades", "nome"),
                               ("pessoas.json", "pessoas", "nome"),
                               ("organizacoes.json", "organizacoes", "nome"),
                               ("sessoes.json", "sessoes", "titulo_verbatim")):
        d = ler(nome) or {}
        for x in d.get(chave, []):
            v = x.get(campo) if isinstance(x, dict) else None
            if isinstance(v, str):
                fora.add(normalise(v))
    grafo = ler("grafo.json") or {}
    for n in grafo.get("nos", []):
        for campo in ("rotulo", "nome", "label"):
            if isinstance(n.get(campo), str):
                fora.add(normalise(n[campo]))

    def excertos(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("excerto", "excerpt", "texto_do_excerto") and isinstance(v, str):
                    fora.add(normalise(v))
                else:
                    excertos(v)
        elif isinstance(o, list):
            for v in o:
                excertos(v)
    for f in sorted(DATA.glob("*.json")) + sorted(ROOT.glob("artigos/**/*.json")):
        try:
            excertos(json.loads(f.read_text(encoding="utf-8")))
        except (ValueError, UnicodeDecodeError):
            continue

    _VERBATIM = {x for x in fora if x}
    return _VERBATIM


_FRAGMENTOS = None


def fragmentos_de_leitura():
    """The middles of the ontology's readings — « é falado por », « consta de », « organiza » —
    taken from dados/ontologia.json and sorted longest first."""
    global _FRAGMENTOS
    if _FRAGMENTOS is not None:
        return _FRAGMENTOS
    f = DATA / "ontologia.json"
    ont = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    pedacos = set()
    for a in ont.get("arestas", []):
        for campo in ("leitura", "leitura_inversa"):
            v = a.get(campo)
            if not isinstance(v, str):
                continue
            for pedaco in re.split(r"\{[st]\}", v):
                pedaco = normalise(pedaco)
                if len(pedaco) >= 3:
                    pedacos.add(pedaco)
    _FRAGMENTOS = sorted(pedacos, key=len, reverse=True)
    return _FRAGMENTOS


def nao_traduzir(texto):
    """True when a run of text on a page must stay in the source language whatever page it is on.

    Three reasons, all of them rules before they are optimisations: it is a name, an excerpt or a
    session title (`verbatim()`); or it is a sentence the graph reads aloud, which rule 6 of
    CLAUDE.md fixes in Portuguese — «{t} é falado por {s}» is the edge, and an English edge label
    would be a different graph.

    The graph test is a substring test against the ontology's own reading fragments, which can in
    principle fire on a sentence of ordinary prose that happens to contain « organiza ». The cost of
    that mistake is one sentence left in Portuguese on a translated page, which the coverage report
    counts and a reader can see. The cost of the opposite mistake is a translated edge label, which
    is a wrong graph and which nothing would catch. Fail in the direction you can see."""
    r = normalise(texto)
    if r in verbatim():
        return True
    if len(r.split()) <= 12:
        for frag in fragmentos_de_leitura():
            if re.search(r"\b" + re.escape(frag) + r"\b", r):
                return True
    return False


def frase(s):
    """A whole sentence or a whole label, not a piece of one. A string concatenated into a longer
    message begins mid-thought — lowercase, or on a comma — and there is nothing a translator can
    do with it but guess at the half it cannot see. Cheaper and more honest to leave it out."""
    s = normalise(s)
    return bool(s) and (s[0] in "#-*>" or s[0].isupper() or s[0].isdigit())


def colher():
    """Walk every source of reader-visible prose and return {hash: segment}.

    Three origins, and the `kind` is kept because it decides who reviews a translation and how it
    is served: `prose` is an article and is the editor's, translated as a whole file per language;
    `data` is a section, a state, an ontology definition; `chrome` is the furniture and is
    translated once for the whole site.
    """
    segs = {}

    def add(text, kind, where):
        if not translatable(text):
            return
        k = key(text)
        e = segs.setdefault(k, {"text": normalise(text), "kind": kind, "where": []})
        if where not in e["where"]:
            e["where"].append(where)

    # 1. Article prose. The unit is the paragraph: small enough that editing one does not
    #    invalidate the article, large enough to translate with its context intact.
    for md in sorted(ROOT.glob("artigos/**/artigo.md")):
        rel = str(md.relative_to(ROOT))
        for para in re.split(r"\n\s*\n", md.read_text(encoding="utf-8")):
            para = para.strip()
            # A source mark carries an id that must survive translation untouched; the paragraph
            # around it is still translatable, so the mark is masked rather than the paragraph
            # dropped.
            if para and not para.startswith(("```", "|")):
                add(re.sub(r"\[\[fonte:[^\]]+\]\]", "[[fonte]]", para), "prose", rel)

    # 1b. Article metadata and verification records. The title, the standfirst and the text of each
    #     claim are prose and are the editor's; the excerpts beside them carry a sha256 and are
    #     skipped whole by the rule below. These live in artigos/, not dados/, and a version of
    #     this file that only walked dados/ left every article headline untranslated.
    # 2.  The data layer, deny-by-default. See decision 4 in this file's docstring, and the rule
    #    that evidence is an object rather than a field.
    def walk(o, origem, kind="data"):
        if isinstance(o, dict):
            if "sha256" in o:           # a record of somebody else's bytes, whole and untouched
                return
            for k2, v in o.items():
                if k2 in NEVER or k2.lower() in TODAS_AS_LINGUAS:
                    continue
                walk(v, origem, kind)
        elif isinstance(o, list):
            for v in o:
                walk(v, origem, kind)
        elif isinstance(o, str):
            add(o, kind, origem)

    for f in sorted(ROOT.glob("artigos/**/*.json")):
        try:
            walk(json.loads(f.read_text(encoding="utf-8")), str(f.relative_to(ROOT)), "prose")
        except (ValueError, UnicodeDecodeError):
            continue

    for f in sorted(DATA.glob("*.json")):
        if f.name in FORA_DO_AMBITO:
            continue
        try:
            walk(json.loads(f.read_text(encoding="utf-8")), f"dados/{f.name}")
        except (ValueError, UnicodeDecodeError):
            continue

    # 3. The chrome: the Portuguese the builders themselves write — navigation, captions, state
    #    words, the explanatory lines. Read with `ast`, never with a regex, for two reasons that
    #    both cost money if you get them wrong. A regex over source text splits an implicitly
    #    concatenated literal into fragments, and a fragment is a segment nobody can translate;
    #    `ast` hands back the joined string the program actually uses. And a regex cannot tell a
    #    docstring from a caption, so it bills the site for this file's own prose.
    #
    #    f-strings are skipped on purpose: a string with a hole in it is not a sentence, and
    #    substituting one would need the builder's cooperation. Those lines stay in the source
    #    language and the coverage report says which — see docs/guidance/multilingual.md.
    for py in sorted(ROOT.glob("build/*.py")):
        if py.name in NAO_RENDERIZA:
            continue
        try:
            arvore = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        docstrings = set()
        for no in ast.walk(arvore):
            corpo = getattr(no, "body", None)
            if isinstance(corpo, list) and corpo and isinstance(corpo[0], ast.Expr) \
                    and isinstance(corpo[0].value, ast.Constant) \
                    and isinstance(corpo[0].value.value, str):
                docstrings.add(id(corpo[0].value))
        for no in ast.walk(arvore):
            if not isinstance(no, ast.Constant) or not isinstance(no.value, str):
                continue
            if id(no) in docstrings:
                continue
            s2 = no.value
            if not ACENTOS.search(s2) or any(c in s2 for c in '<>"'):
                continue                                    # a fragment of markup, not a sentence
            if frase(s2):
                add(s2, "chrome", f"build/{py.name}")

    # 4. The finished pages, as a DISCOVERY surface — never as the thing being translated.
    #    Origins 1 to 3 find the prose that is authored in a file this build can read. They do not
    #    find the sentence a builder assembles with an f-string, or a clause that sits between two
    #    inline links, and on this site those account for more of what a reader actually reads than
    #    everything in dados/ put together. Rather than rewrite twenty builders to make that text
    #    findable, read the rendered HTML and take the runs.
    #
    #    This is NOT translating the render. The unit is still a piece of authored text, the key is
    #    still the hash of that text, it is still translated exactly once however many pages carry
    #    it, and `gerado()` keeps out anything a builder composed from data. What the render adds is
    #    completeness: no reader-visible sentence is invisible to the pipeline, so coverage can
    #    reach 100% and a gap is a number rather than a surprise.
    if (ROOT / "empresas" / "index.html").exists():
        from locales import (ATRIBUTOS, BLOCOS, ENTIDADE_HTML, MARCACAO, TAGS,
                             paginas_de_leitura, substituivel)
        for rel in paginas_de_leitura():
            html = (ROOT / rel).read_text(encoding="utf-8")
            for i, parte in enumerate(MARCACAO.split(html)):
                if i % 2 == 0 and substituivel(parte) and not gerado(parte) \
                        and not nao_traduzir(parte):
                    add(parte, "render", rel)
            for m in BLOCOS.finditer(html):
                plano = ENTIDADE_HTML.sub(" ", TAGS.sub("", m.group(3))).replace("&amp;", "&")
                if substituivel(plano) and not gerado(plano) and not nao_traduzir(plano):
                    add(plano, "render", rel)
            # title, alt and aria-label are read aloud by a screen reader and shown on hover; a
            # page whose visible text is English and whose tooltips are Portuguese is half done.
            for m in ATRIBUTOS.finditer(html):
                v = m.group(2)
                if substituivel(v) and not gerado(v) and not nao_traduzir(v):
                    add(v, "render", rel)
            for m in re.finditer(r'<meta name="description" content="([^"]+)"', html):
                v = m.group(1)
                if substituivel(v) and not gerado(v) and not nao_traduzir(v):
                    add(v, "render", rel)

    return segs


def carregar_locale(loc):
    f = STORE / f"{loc}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def carregar_fontes():
    f = STORE / "fontes.json"
    if not f.exists():
        raise SystemExit("i18n: run `python3 build/i18n.py extract` first")
    return json.loads(f.read_text(encoding="utf-8"))


def cmd_extract():
    segs = colher()
    STORE.mkdir(parents=True, exist_ok=True)
    doc = {
        "id": "pt-i18n-fontes",
        "versao": "1.0.0",
        "o_que_e": ("Every translatable segment on this site, keyed by the SHA-256 of its own "
                    "source text. The key IS the content, so a changed source is a different "
                    "segment and a stale translation cannot be served by accident: it becomes a "
                    "cache miss, which the gate counts."),
        "lingua_de_origem": SOURCE_DEFAULT,
        "locales": LOCALES,
        "contagem": len(segs),
        "palavras": sum(len(s["text"].split()) for s in segs.values()),
        "segmentos": dict(sorted(segs.items())),
    }
    (STORE / "fontes.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
    por_kind = {}
    for s in segs.values():
        por_kind[s["kind"]] = por_kind.get(s["kind"], 0) + 1
    print(f'i18n extract: {doc["contagem"]} segments, {doc["palavras"]} words '
          f'({", ".join(f"{v} {k}" for k, v in sorted(por_kind.items()))})')


def cmd_status():
    src = carregar_fontes()
    segs = src["segmentos"]
    print(f'source: {len(segs)} segments, {src["palavras"]} words, from {SOURCE_DEFAULT}')
    print(f'{"locale":<8} {"done":>6} {"missing":>8} {"words to do":>12} {"orphaned":>9}')
    for loc in LOCALES:
        have = carregar_locale(loc)
        done = sum(1 for k in segs if k in have)
        falta = [k for k in segs if k not in have]
        palavras = sum(len(segs[k]["text"].split()) for k in falta)
        orfas = sum(1 for k in have if k not in segs)
        print(f"{loc:<8} {done:>6} {len(falta):>8} {palavras:>12} {orfas:>9}")
    print()
    print("orphaned = a translation whose source text has since changed. It is not served and not "
          "lost: it stays for reuse and costs nothing to keep.")


def cmd_todo(loc, limite=None):
    src = carregar_fontes()
    have = carregar_locale(loc)
    falta = {k: v for k, v in src["segmentos"].items() if k not in have}
    if limite:
        falta = dict(list(falta.items())[:int(limite)])
    saida = {
        "locale": loc,
        "de": SOURCE_DEFAULT,
        "instrucoes": (
            "Translate each value into the target locale. Keep [[fonte]] marks, markdown syntax, "
            "and every name, number, date, hash and URL exactly as they are. Do not translate "
            "quoted excerpts. Return the same object with the same keys and nothing else."),
        "contagem": len(falta),
        "palavras": sum(len(v["text"].split()) for v in falta.values()),
        "segmentos": {k: v["text"] for k, v in falta.items()},
    }
    print(json.dumps(saida, ensure_ascii=False, indent=2))


def cmd_apply(loc, ficheiro):
    src = carregar_fontes()
    entrada = json.loads(Path(ficheiro).read_text(encoding="utf-8"))
    novos = entrada.get("segmentos", entrada)
    have = carregar_locale(loc)
    aceites, recusados = 0, 0
    for k, texto in novos.items():
        # A translation is only accepted against a source hash this build knows. Anything else is
        # a translation of text that no longer exists, and writing it would be writing a lie.
        if k not in src["segmentos"] or not isinstance(texto, str) or not texto.strip():
            recusados += 1
            continue
        have[k] = normalise(texto)
        aceites += 1
    STORE.mkdir(parents=True, exist_ok=True)
    (STORE / f"{loc}.json").write_text(
        json.dumps(dict(sorted(have.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(f"i18n apply {loc}: {aceites} accepted, {recusados} refused (unknown source hash)")


def main(argv):
    if not argv or argv[0] not in ("extract", "status", "todo", "apply"):
        raise SystemExit(__doc__.split("\n\n")[1])
    cmd = argv[0]
    if cmd == "extract":
        cmd_extract()
    elif cmd == "status":
        cmd_status()
    elif cmd == "todo":
        cmd_todo(*argv[1:])
    elif cmd == "apply":
        cmd_apply(argv[1], argv[2])


if __name__ == "__main__":
    main(sys.argv[1:])

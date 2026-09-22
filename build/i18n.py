#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the translation memory, and the reason it stays cheap.

    python3 build/i18n.py extract          walk the sources, write dados/i18n/fontes.json
    python3 build/i18n.py status           per locale: done, missing, words to do, orphaned
    python3 build/i18n.py todo <locale> [--na-pagina] [--max-palavras N] [--ficheiro F]
                                          ONLY the missing segments, most-read first
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
import html
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
    # A LISTING OF PATHS. The root of this repository, printed as a comma-separated run of folder
    # names, reads to every filter above like an ordinary sentence: it has commas, it has words, it
    # has accents. It is a directory listing, and «casos-de-uso/» is that folder's name in every
    # language. Translating it would rename folders that exist.
    pedacos = [x.strip() for x in s.split(",") if x.strip()]
    if len(pedacos) >= 4 and sum(1 for x in pedacos if re.fullmatch(
            r"[\w.-]+(/|\.(py|js|json|md|html|css|txt|xml|mjs|nt|tpl))", x)) >= len(pedacos) * 0.6:
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
                 r"afirmacoes|itens|linhas|caracteres|bytes|segmentos|entregas|dias|"
                 r"entidade|entidades|sessões|sessoes|palcos|oradores|organizações|organizacoes|"
                 r"artigos|histórias|historias|capturas|hashes|ficheiro)\b", b):
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

    # EVERY name-ish field in EVERY data file, at any depth. An earlier version named four files and
    # one field each, and the graph then read «Gacs Ltd Gacsym Ventures é a organização sob a qual o
    # evento lista Anmol Goel» into a translation batch, because that organisation's name lives under
    # `organizacao_listada` on a speaker card and not under `nome` in one of the four.
    # `nome_em_si` is a language's AUTONYM — «Português (Portugal)», «Deutsch». Translating an
    # autonym defeats its only purpose, which is to be recognisable to a reader who cannot read the
    # page they are on.
    NOMES = ("nome", "name", "rotulo", "label", "titulo_verbatim", "organizacao_listada",
             "cargo_listado", "publicador", "agente_verbatim", "nome_em_si")

    def colher_nomes(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in NOMES and isinstance(v, str):
                    fora.add(normalise(v))
                elif isinstance(v, (dict, list)):
                    colher_nomes(v)
                elif k in NOMES and isinstance(v, list):
                    fora.update(normalise(x) for x in v if isinstance(x, str))
        elif isinstance(o, list):
            for v in o:
                colher_nomes(v)

    # ONLY THE FILES THAT HOLD OTHER PEOPLE'S NAMES. Harvesting `nome` and `rotulo` from every data
    # file swallowed this newsroom's OWN vocabulary along with them: the three departments are agents
    # whose `nome` is «Pesquisa», «Redação» and «Verificação», and the eight sections carry a `rotulo`
    # in the ontology. All of it was then classified verbatim and left Portuguese on every English
    # page, while the coverage report counted it as correct — 16 858 runs «verbatim» and a masthead
    # nobody had translated.
    #
    # A name is a name because a SOURCE published it, not because a field is called `nome`. So the
    # list is of files that hold what sources published. dados/i18n/locales.json is here for the
    # autonyms, which are the one case of a name this site writes itself.
    # NOT grafo.json, and NOT lexico.json.
    #   · grafo.json labels every node, including the nodes that are this site's own articles, so
    #     harvesting it made «O Governo anunciou 25 milhões de euros para adoção de IA na
    #     Administração Pública» a name. A headline is this newsroom's own sentence. The names that
    #     matter are in entidades.json, pessoas.json and organizacoes.json, and those are here.
    #   · lexico.json labels are this site's own vocabulary for a published formula — and the file
    #     even carries an `en` field for each one. Harvesting them froze «Diáspora» in the masthead
    #     of the English page, where it is a section name. What is evidential about the lexicon is
    #     its PATTERNS, which nothing here touches; the labels are ours to translate.
    NOMES_DE_TERCEIROS = ("entidades.json", "pessoas.json", "organizacoes.json",
                          "sessoes.json", "registo.json", "evento.json",
                          "temas.json", "excluidas.json", "fontes-alvo.json", "documentos.json",
                          "verificacoes-fonte.json", "mudancas.json")
    # grafo.json IS harvested, minus its own `Historia` nodes. Every other node label came from
    # somebody else's bytes — a speaker, an organisation, a session title, a stage — and stays. A
    # `Historia` node is labelled with this newsroom's own headline, and a headline is a sentence
    # this publication wrote, so it translates like any other sentence it wrote.
    grafo = ler("grafo.json") or {}
    for n in grafo.get("nos", []):
        if isinstance(n, dict) and n.get("tipo") != "Historia":
            colher_nomes(n)

    for f in ([DATA / n for n in NOMES_DE_TERCEIROS] + sorted(ROOT.glob("artigos/**/*.json"))
              + [STORE / "locales.json"]):
        if not f.exists():
            continue
        try:
            colher_nomes(json.loads(f.read_text(encoding="utf-8")))
        except (ValueError, UnicodeDecodeError):
            continue

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

    # The publication's own name. «O Ecossistema Português de IA» is what this paper is called, the
    # way Le Monde is called Le Monde, and a masthead that changes language is a different paper.
    # The tagline under it is a sentence and IS translated — the name is not.
    try:
        from paginas import SUBTITULO, TITULO
        fora.update({normalise(TITULO), normalise(SUBTITULO)})
    except ImportError:
        pass

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
    # A PAGE TITLE IS «<name> · <site>», and a name with the site's own handle after it is still a
    # name. Without this, every entity page's <title> arrived as a segment whose only honest
    # translation was itself, and 198 of them would have been paid for once per language.
    for sufixo in (" · pt.newsroom.sgit.ai",):
        if r.endswith(sufixo) and normalise(r[:-len(sufixo)]) in verbatim():
            return True
    # A CHIP IS «<name> · <count>», sometimes «<name> · <count>×». The name is a name and the count
    # is generated, so the pair is neither translatable nor missing. There were forty of these, one
    # per entity per page, and translating them would have bought a cache miss on the next build
    # that changed a count by one.
    m = re.fullmatch(r"(.+?) · \d+(×|x)?", r)
    if m and normalise(m.group(1)) in verbatim():
        return True
    fragmentos = [f for f in fragmentos_de_leitura()
                  if re.search(r"\b" + re.escape(f) + r"\b", r)]
    if fragmentos:
        # Take out EVERY fragment, not the first one. «o evento lista {s} sob {t}» is two fragments
        # in one sentence, and removing only «o evento lista» left «Cíntia Costa sob 351 Portuguese
        # Startup Association», which is not a name and so failed the test that should have passed.
        resto = r
        for f in fragmentos:
            resto = re.sub(r"\b" + re.escape(f) + r"\b", "\x00", resto)
        lados = [x.strip(" ·—-") for x in resto.split("\x00")]
        if all((not x) or (normalise(x) in verbatim()) for x in lados):
            return True
    for frag in fragmentos:
        # A GRAPH LABEL IS «<name> <verb> <name>», and that shape can be tested exactly instead of
        # guessed at by length. Take the reading fragment out and what is left must be names this
        # site already holds verbatim. A word ceiling gets this wrong in both directions: «Startup
        # Summit Lisbon 2026 contém Lunch · Beer Hall · Praça Café · Rooftop Bar» is thirteen words
        # and IS an edge, while «Uma etiqueta diz que a página contém certas palavras» is nineteen
        # and is a sentence about the site. Raising the ceiling to catch the first would have left
        # the second untranslated on every page in every language.
        if r == frag:
            return True              # the reading itself, with both names stripped by the renderer
        # A ONE-WORD FRAGMENT IS NOT ENOUGH ON ITS OWN. The ontology reads «{t} sustenta {s}», so
        # «sustenta» is a fragment, and a bare-label fallback on any short run therefore classified
        # the front page's heading «O que sustenta» as an edge of the graph and left it Portuguese in
        # every language. Two words of verb, or an exact match, or nothing.
        if len(frag.split()) >= 2 and len(r.split()) <= 12:
            return True
    return False


# A NUMBER OR A MONTH NAME IS NOT A WORD TO TRANSLATE — IT IS A HOLE IN A SENTENCE.
# «Assenta em 1 fonte congelada e hasheada · 2 afirmações reencontradas nos bytes» and «Lisboa ·
# segunda-feira, 14 de setembro de 2026» are sentences a builder composed from data. Left alone they
# are Portuguese on an English page; translated as they stand they are a cache miss the next time a
# count changes, which is the cost curve this whole design exists to avoid.
#
# So they are masked: every run of digits becomes «#» and every month or weekday name becomes «@»,
# and the masked form is the segment. ONE segment covers every value the template will ever take,
# for ever, and the values are put back at render time from the page itself. This is the mechanism
# `docs/guidance/multilingual.md` calls «generated text is formatted, not translated» — the formatter
# is a translated template plus the numbers the page already had.
_NUM = re.compile(r"\d+(?:[ \u00a0]\d{3})*")


# A MACHINE FACT HAS A MACHINE SHAPE: a separator, a digit, or hexadecimal length. An earlier
# version of this pattern allowed «any single token», which matches «Aviso» — and every one-word
# label on the site was then classified as a machine fact and left Portuguese in every locale, while
# the report counted it as correct. A bare Portuguese word is not an identifier.
MAQUINA = re.compile(
    r"^(v\d+\.\d+\.\d+"                                  # a version
    r"|\d{4}-\d{2}-\d{2}([T ][\d:.]+Z?)?"                  # a date or a timestamp
    r"|[\w+~-]+([./:@][\w+~-]*)+"                            # a path, a domain, an id, a handle
    r"|[\w+-]*\d[\w+-]*"                                    # a token with a digit in it
    r"|[0-9a-f]{8,}…?"                                      # a hash, whole or elided
    r"|[0-9a-f]{4,}…)$")                                    # a hash shortened for display


def maquina(s):
    """A machine fact: a version, a timestamp, a path, a source id, a hash. Not prose, not a
    template, not missing — it is the same string in every language.

    This exists because masking generated text found identifiers too: «2026-09-14/oradores/luis-
    valente» became the «template» «#-#-#/oradores/luis-valente», and 465 version badges became
    «v#.#.#». The report then said a thousand things needed translating that must never be touched,
    which buries the fifty that do."""
    return bool(MAQUINA.match(normalise(s)))


def mascarar(s):
    """(masked, values). Values are ('n', text) for a number, ('m', index) for a month, ('d', index)
    for a weekday — the index, not the word, so the target language can supply its own."""
    s = normalise(s)
    valores = []
    fora = []
    i = 0
    baixo = s.lower()
    while i < len(s):
        for j, nome in enumerate(DIAS):
            if baixo.startswith(nome, i):
                valores.append(("d", j)); fora.append("@"); i += len(nome); break
        else:
            for j, nome in enumerate(MESES):
                if baixo.startswith(nome, i):
                    valores.append(("m", j)); fora.append("@"); i += len(nome); break
            else:
                m = _NUM.match(s, i)
                if m:
                    valores.append(("n", m.group(0))); fora.append("#"); i = m.end()
                else:
                    fora.append(s[i]); i += 1
    return "".join(fora), valores


def preencher(molde, valores, meses, dias):
    """Put the values back into a translated template, in the order the page had them."""
    fora = []
    restantes = list(valores)
    for ch in molde:
        if ch in "#@" and restantes:
            tipo, v = restantes.pop(0)
            if tipo == "n":
                fora.append(v)
            elif tipo == "m":
                fora.append(meses[v] if v < len(meses) else MESES[v])
            else:
                fora.append(dias[v] if v < len(dias) else DIAS[v])
        else:
            fora.append(ch)
    return "".join(fora)


# Words that are Portuguese AND NOT ENGLISH. «as», «os», «se», «no» and «nos» were in this list and
# they are all ordinary English too, so an English sentence in a data file — «the release history as
# markdown» — was being counted as Portuguese left untranslated. A detector that reports the
# finished work as unfinished is a detector nobody will act on.
PALAVRAS_PT = re.compile(
    r"\b(de|da|do|das|dos|que|não|nao|uma|para|com|é|em|ao|à|pelo|pela|por|sobre|"
    r"quando|onde|cada|esta|este|isso|aqui|ainda|já|nada|tudo|mais|entre|foi|está|são|pode)\b",
    re.I)


def parece_portugues(s):
    """Portuguese a reader would SEE, whether or not this pipeline is willing to translate it.

    This is the honest denominator, and it exists because the coverage figure was lying. A run of one
    accented word is not translatable by the rules above — one word is usually a name — so it never
    reached the substitution and was never counted as anything. The report said 100% while the
    masthead still read «Diáspora» and the counters still read «Oradores». A number that cannot see
    the thing a reader complains about is worse than no number.

    Anything this matches and the memory cannot serve is counted `missing`, whether the reason is
    that nobody translated it or that the rules decline to. Both are Portuguese on an English page."""
    s = normalise(s)
    if len(s) < 2 or re.fullmatch(r"[\d\s\W]+", s):
        return False
    if re.search(r"https?://|\w+\.(json|md|py|js|mjs|html|css|txt|xml|nt|snapshot)\b", s):
        return False                   # an address or a path is not prose in any language
    if re.fullmatch(r"[\w.@/:_-]+", s):
        return False                   # a single token: an id, a domain, a path, a handle
    return bool(ACENTOS.search(s) or PALAVRAS_PT.search(s))


def rotulo(s):
    """A declared UI label: short, but a word of the site's own vocabulary rather than a name."""
    s = normalise(s)
    return bool(s) and 2 <= len(s) <= 60 and not re.fullmatch(r"[\d\s\W]+", s)


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

    def add(text, kind, where, curto=False):
        # `curto` waives the two-word minimum for a DECLARED label and nothing else: see the label
        # catalogue below. Everything else, including the verbatim test, still applies.
        # EVERY origin goes through the same two tests, and an earlier version only put the render
        # harvest through the second one. «Diário da República» and «Governo de Portugal» reached
        # the memory through the data walk, where they sit under keys that are not in NEVER, and a
        # translator was going to be asked to render the name of an official journal into German.
        # A rule applied at three of four entrances is not a rule.
        if nao_traduzir(text) or maquina(text):
            return
        # THE MASK IS TRIED FIRST, and the order is the whole point. `translatable()` asks «is there
        # Portuguese here to translate?» and «mais 1 entidade» has no accent and none of the function
        # words it looks for, so it was rejected before the mask ever ran and the template «mais #
        # entidades» never existed. A run that is generated is not judged as prose; it is masked, and
        # what is judged is the template.
        if gerado(text):
            molde, valores = mascarar(text)
            # A template that is mostly holes is not a sentence: masking a shortened hash gives
            # «##e#», which nobody can translate and which only clutters the batch.
            # `rotulo()` is not the test here: it caps a label at 60 characters, and a template is
            # often a whole sentence — «Assenta em # fonte congelada e hasheada · # afirmações
            # reencontradas nos bytes» is 78 and was being dropped for being long.
            # A SENTENCE THAT STARTS WITH A NAME IS ONE ENTITY'S SENTENCE, NOT A TEMPLATE.
            # «Nina Chandé — Pessoa no grafo do ecossistema português de IA. 4 arestas, lidas em voz
            # alta.» masks to a template that is still different for all 198 entities, so masking it
            # produced 198 «templates» and buried the thirty that are real. They are meta
            # descriptions — a reader never sees them — and the honest place for them is nowhere.
            cabeca = normalise(text.split(" — ")[0]) if " — " in text else ""
            if cabeca and cabeca in verbatim():
                return
            letras = sum(1 for c in molde if c.isalpha())
            if valores and letras >= 3 and letras >= len(molde) * 0.4:
                k2 = key(molde)
                e2 = segs.setdefault(k2, {"text": molde, "kind": "padrao", "where": []})
                if where not in e2["where"]:
                    e2["where"].append(where)
            return
        if not (rotulo(text) if curto else translatable(text)):
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

    # 2b. THE LABEL CATALOGUE. «Empresas». «Eventos». «Aviso». One word each, and every filter in
    #     this file rejects a single word on purpose, because one word is usually a name. But the
    #     eight section names in the masthead ARE the navigation, and an English page whose menu
    #     reads «Empresas Protagonistas Instituições Políticas Use cases Open source Diáspora
    #     Eventos» is half translated in the one place a reader looks first.
    #
    #     So they are declared, not detected: read from the same lists the builders navigate by, so
    #     a ninth section appears here the day it appears there. `nao_traduzir()` still applies — a
    #     label that is a name stays a name.
    try:
        from paginas import EXTRA, RODAPE, SECCOES, VOCABULARIO
        extra = list(VOCABULARIO)
        fv = STORE / "vocabulario.json"
        if fv.exists():
            extra += json.loads(fv.read_text(encoding="utf-8"))["termos"]
        for lista in (SECCOES, EXTRA, RODAPE, [("", v) for v in extra]):
            for par in lista:
                if isinstance(par, (list, tuple)) and len(par) >= 2 and isinstance(par[1], str):
                    add(par[1], "chrome", "build/paginas.py", curto=True)
    except ImportError:
        pass

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
            if any(c in s2 for c in '<>"') or not frase(s2):
                continue                                    # a fragment of markup, not a sentence
            # ACCENTED ONLY, AND DELIBERATELY. Admitting short unaccented literals as labels was
            # tried and pulled in 145 segments of which most were the console's own English —
            # «Board», «Bridges», «Mail» — plus tokens like «NFC», «HEAD» and «MANDATE.md». A
            # detector cannot tell a Portuguese label from an English one in two words. The
            # unaccented Portuguese labels are DECLARED instead, in paginas.VOCABULARIO.
            if ACENTOS.search(s2):
                add(s2, "chrome", f"build/{py.name}")

    # 4. The finished pages, as a DISCOVERY surface — and generated runs are NOT filtered out here.
    #    They were, and `add()`'s masking therefore never saw them: «mais 3 entidades» was dropped at
    #    the door instead of becoming the template «mais # entidades». Two filters for one decision,
    #    and the outer one silently won. — never as the thing being translated.
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
            pagina = (ROOT / rel).read_text(encoding="utf-8")
            for i, parte in enumerate(MARCACAO.split(pagina)):
                if i % 2 == 0 and substituivel(parte) \
                        and not nao_traduzir(parte):
                    add(parte, "render", rel)
            for m in BLOCOS.finditer(pagina):
                if "data-verbatim" in m.group(1) or TAGS.search(m.group(3)):
                    continue        # mixed content is not a segment — see locales.Tradutor.bloco
                plano = html.unescape(m.group(3))
                if substituivel(plano) and not nao_traduzir(plano):
                    add(plano, "render", rel)
            # title, alt and aria-label are read aloud by a screen reader and shown on hover; a
            # page whose visible text is English and whose tooltips are Portuguese is half done.
            for m in ATRIBUTOS.finditer(pagina):
                v = m.group(2)
                if substituivel(v) and not nao_traduzir(v):
                    add(v, "render", rel)
            for m in re.finditer(r'<meta name="description" content="([^"]+)"', pagina):
                v = m.group(1)
                if substituivel(v) and not nao_traduzir(v):
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


def ocorrencias():
    """How many times each segment is actually MET on a reader page, counted the way the renderer
    meets it. This is the number that decides what is worth translating, and it is not the same as
    the number of segments.

    Two thirds of this memory carries 100% of what a reader sees. The other third — 302 segments,
    7026 words — is text that exists in a data file or a builder and never reaches a reader page:
    back-office prose, the README's own paragraphs, llms.txt. Translating it buys nothing, and
    paying for it would be paying by the size of the repository instead of by the size of the site.

    Within the two thirds the distribution is steeper still: 14 segments carry half of every run a
    reader meets, and 28 carry four fifths, because the chrome repeats on all 223 pages. Ordering a
    batch by this number means the first thing translated is the thing most read."""
    from locales import (ATRIBUTOS, BLOCOS, ENTIDADE_HTML, MARCACAO, TAGS, paginas_de_leitura)
    src = carregar_fontes()["segmentos"]
    conta = {}

    def bater(texto):
        k = key(texto)
        if k in src:
            conta[k] = conta.get(k, 0) + 1
            return True
        return False

    for rel in paginas_de_leitura():
        html = (ROOT / rel).read_text(encoding="utf-8")
        pos, regioes = 0, []
        for m in BLOCOS.finditer(html):
            regioes.append(html[pos:m.start()])
            plano = ENTIDADE_HTML.sub(" ", TAGS.sub("", m.group(3))).replace("&amp;", "&")
            if not bater(plano):
                regioes.append(m.group(3))
            pos = m.end()
        regioes.append(html[pos:])
        for regiao in regioes:
            for parte in MARCACAO.split(regiao)[::2]:
                if parte.strip():
                    bater(parte)
        for m in ATRIBUTOS.finditer(html):
            bater(m.group(2))
        for m in re.finditer(r'<meta name="description" content="([^"]+)"', html):
            bater(m.group(1))
    return conta


def cmd_todo(loc, *opcoes):
    """todo <locale> [--na-pagina] [--max-palavras N] [--ficheiro F]

    `--na-pagina` is the one that matters: it drops every segment no reader page carries and orders
    what is left by how often a reader meets it. `--max-palavras` then cuts the batch to a size one
    pass can do well, taking the most-read segments first, so stopping half way still leaves the
    site mostly translated rather than patchy.
    """
    opts = list(opcoes)
    na_pagina = "--na-pagina" in opts
    limite_palavras = None
    ficheiro = None
    for i, o in enumerate(opts):
        if o == "--max-palavras":
            limite_palavras = int(opts[i + 1])
        elif o == "--ficheiro":
            ficheiro = opts[i + 1]
    src = carregar_fontes()
    have = carregar_locale(loc)
    falta = {k: v for k, v in src["segmentos"].items() if k not in have}
    if na_pagina:
        conta = ocorrencias()
        falta = {k: v for k, v in falta.items() if k in conta}
        ordem = sorted(falta, key=lambda k: (-conta[k], -len(falta[k]["text"])))
    else:
        ordem = sorted(falta, key=lambda k: -len(falta[k]["text"]))
    if limite_palavras:
        corte, soma = [], 0
        for k in ordem:
            n = len(falta[k]["text"].split())
            if soma + n > limite_palavras and corte:
                break
            corte.append(k)
            soma += n
        ordem = corte
    falta = {k: falta[k] for k in ordem}
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
    texto = json.dumps(saida, ensure_ascii=False, indent=2) + "\n"
    if ficheiro:
        Path(ficheiro).write_text(texto, encoding="utf-8")
        print(f'i18n todo {loc}: {saida["contagem"]} segments, {saida["palavras"]} words '
              f'-> {ficheiro}')
    else:
        print(texto)


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

#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the locale renderer: one finished site in, N finished sites out.

    python3 build/locales.py               render every locale whose estado is `publicado`
    python3 build/locales.py --relatorio   coverage, per locale and per page, writing nothing
    python3 build/locales.py --ensaio <locale> <dir>   render one locale somewhere else, to look at

WHY IT WORKS ON THE FINISHED HTML AND NOT INSIDE THE BUILDERS. There are twenty builders in this
repository and about four hundred Portuguese strings inside them. The obvious design — wrap every
string in a `t()` call — means editing all four hundred, and this repository has already paid for
that lesson once: a bulk rewrite of Portuguese identifiers into English produced half-translated
code (`save(estado)`, `this.items = itens`) that took two rewrites from scratch to undo. A second
pass over finished pages touches no builder, cannot half-translate an identifier, and is
idempotent: run it twice and the second run changes nothing.

THE SAFETY PROPERTY, and it is the whole design. A text run is replaced ONLY when its normalised
form hashes to a segment the translation memory already holds. Everything else passes through
unchanged. So the default for a name, a hash, a date, a byte count, a source id and above all a
frozen excerpt is: untouched, because none of those was ever extracted into the memory. The
failure mode of this renderer is a Portuguese sentence on an English page — visible, countable,
reported by `--relatorio` and by the gate. It is not a mistranslated excerpt, which would be a
breach of rules 1 and 3 and would not be visible at all.

WHAT IT DOES TO EACH PAGE, in order:

  1. block prose — the inner HTML of a paragraph whose text (tags stripped) is a known segment is
     replaced by the translation, and the entity linker is run again over it. Entity names are
     verbatim in every language, so the links come back.
  2. text runs — a whole text node that is a known segment.
  3. attributes — title, alt, aria-label, and the description meta.
  4. the head — lang, canonical, og:url, and reciprocal hreflang alternates.
  5. relative links — a locale page sits one directory deeper than its Portuguese original, so a
     link that leaves the localised set (assets, frozen copies, the newsroom console) gets one
     more `../`. A link that stays inside the set needs no change at all, because the locale tree
     mirrors the Portuguese one exactly. Which of the two it is, is decided by asking whether the
     target is a page this run localised — so the rule maintains itself as pages come and go.

WHAT IS NOT LOCALISED, and it is the second big cost decision after `build/i18n.py`:
the back office. /newsroom/, /admin/, /redacao/, /entregas/, /briefs/ and /docs/ have one reader,
the editor of record, who reads Portuguese and English. Every locale page carries a link back to
the Portuguese original, which is the page of record.
"""
import html
import json
import posixpath
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i18n                                                            # noqa: E402
import paginas                                                         # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "dados" / "i18n"
SITE = "https://pt.newsroom.sgit.ai"

# Directories that never get a locale copy: shared bytes, frozen evidence, and the back office.
FORA = {"assets", "fontes", "ficheiros", "dados", "api", "newsroom", "admin", "redacao",
        "entregas", "briefs", "docs", "node_modules", "build", ".git", ".github", ".claude",
        "artigos_fontes", "seccoes"}

# Elements whose inner HTML can hold a whole authored paragraph.
BLOCOS = re.compile(r"(<(p|h1|h2|h3|h4|li|figcaption|summary)\b[^>]*>)(.*?)(</\2\s*>)", re.S | re.I)
# The same split as build/paginas.py uses: markup on the odd indices, text on the even ones.
MARCACAO = re.compile(r"(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>"
                      r"|<code\b[^>]*>.*?</code>|<pre\b[^>]*>.*?</pre>|<[^>]+>)", re.S | re.I)
ATRIBUTOS = re.compile(r'\b(title|alt|aria-label)="([^"]+)"')
TAGS = re.compile(r"<[^>]+>")
# Kept for the harvest's import list. The block pass uses html.unescape() instead: substituting
# every entity with a SPACE turned «Gacs Ltd &amp; Gacsym Ventures» into «Gacs Ltd Gacsym Ventures»,
# which matches no name in dados/, so an organisation's name stopped being recognised as a name and
# was offered for translation as part of a graph edge.
ENTIDADE_HTML = re.compile(r"&(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);")


def registo():
    """The locales this site serves, and the state of each. `estado` is the editor's switch: this
    renderer writes nothing for a locale until the editor of record puts it in `publicado`, because
    CLAUDE.md says what language a reader sees and CLAUDE.md is the editor's file, not a build's."""
    return json.loads((STORE / "locales.json").read_text(encoding="utf-8"))


def paginas_de_leitura():
    """Every page that can have a locale twin, as a repo-relative posix path."""
    conhecidos = {lc["codigo"] for lc in registo()["locales"]}
    saida = []
    for p in sorted(ROOT.rglob("*.html")):
        partes = p.relative_to(ROOT).parts
        if partes[0] in FORA or partes[0] in conhecidos:
            continue
        if "fontes/congeladas/" in p.as_posix():
            continue
        saida.append(p.relative_to(ROOT).as_posix())
    return saida


def substituivel(t):
    """A text run this renderer is willing to touch.

    Anything inside «…» is somebody else's words and a translated quotation is a misquotation. This
    used to be enforced by refusing the whole run, which is the blunt version: it left 174
    occurrences of Portuguese prose on every locale page — 69 of them the same sentence on
    /empresas/ — and the coverage report could not see one of them, because a run refused here is
    never counted as a miss.

    A BALANCED SPAN IS MASKED, NOT REFUSED: i18n.citar() takes it out, the prose around it is
    translated, and i18n.descitar() puts the span back byte-identical. What is left to refuse is an
    UNBALANCED guillemet, where the quotation opens in this run and closes inside the markup that
    follows — there, the text after « really is quoted and translating it would misquote. The one
    safe shape is a stray that carries no quoted text with it: a « that is the run's last character,
    or a » that is its first. That is the case the split around «Independent» produces, and it is
    why those two runs are now translated and the quotation between them is still untouched."""
    resto, _ = i18n.citar(t)
    resto = resto.strip()
    if resto.endswith("«"):
        resto = resto[:-1]
    if resto.startswith("»"):
        resto = resto[1:]
    return "«" not in resto and "»" not in resto


class Tradutor:
    def __init__(self, loc):
        self.loc = loc
        self.mem = i18n.carregar_locale(loc)
        self.acertos = 0
        self.faltas = 0
        self.gerados = 0
        self.verbatim = 0
        self.traducoes = set(self.mem.values())
        # AN ORPHAN IS NOT SERVED, and this set is what makes that true rather than asserted.
        # Substitution looks up the hash of the text ON THE PAGE, so a translation left behind by a
        # source that has since changed — or by a rule that has since reclassified its source as
        # verbatim — would still be found in the memory and still be shown. Serving only keys the
        # CURRENT extraction knows makes «kept for reuse, never served» a property of the code rather
        # than a claim in a comment.
        self.conhecidos = set(i18n.carregar_fontes()["segmentos"])
        lc = next((x for x in registo()["locales"] if x["codigo"] == loc), {})
        self.meses = lc.get("meses", i18n.MESES)
        self.dias = lc.get("dias", i18n.DIAS)
        self.faltas_texto = []

    def procurar(self, texto):
        plano = i18n.normalise(texto)
        if plano in self.traducoes:
            # Already translated by an earlier pass on this same page. Two passes see the same bytes,
            # and without this the second reports the first's work as missing.
            return None
        if i18n.maquina(plano):
            # A version, a timestamp, a path, a source id. The same string in every language, and
            # not a template either — see i18n.maquina().
            self.verbatim += 1
            return None
        if i18n.nao_traduzir(plano) or i18n.nao_traduzir(i18n.normalise(html.unescape(texto))):
            # A verb of the graph, a name, an excerpt. Correct as it stands — i18n.nao_traduzir().
            # TESTED BEFORE THE MEMORY, not after. The other order served a translation the memory
            # happened to hold for a string the rules had since reclassified as verbatim: «sessão de
            # arranque (Claude Code, Opus 5)» went out translated on 224 pages and gate 44 caught it.
            # What a page may show is decided by the rules, never by what is in the cache.
            self.verbatim += 1
            return None
        k = i18n.key(plano)
        if k in self.mem and k in self.conhecidos:
            self.acertos += 1
            return self.mem[k]
        # A QUOTATION IS A HOLE, AND THE SENTENCE AROUND IT IS THE SEGMENT. The span goes out
        # byte-identical; everything else about the lookup is the ordinary path, so a sentence with
        # both a quotation and a count is served from a template with both kinds of hole. See
        # i18n.citar() for why this replaced refusing the run.
        semcit, citacoes = i18n.citar(plano)
        if citacoes:
            dentro = self.procurar(semcit)
            if dentro is None:
                return None
            cheio = i18n.descitar(dentro, citacoes)
            # The filled string is what lands on the page, so the second pass has to recognise it as
            # already done — the raw memory value carries ¤ and would not match.
            self.traducoes.add(i18n.normalise(cheio))
            return cheio
        if i18n.gerado(texto):
            # A date line, a count, a byte total. Try the MASKED template first: one translated
            # sentence with holes, filled from the numbers and month names this page already had. See
            # i18n.mascarar(). THIS RUNS BEFORE THE TRANSLATABLE TEST, because «mais 3 entidades» is
            # not prose by that test and was being counted as a miss with its own translated template
            # sitting in the memory unread.
            molde, valores = i18n.mascarar(plano)
            km = i18n.key(molde)
            if valores and km in self.mem and km in self.conhecidos:
                self.acertos += 1
                return i18n.preencher(self.mem[km], valores, self.meses, self.dias)
            if valores and km in self.conhecidos:
                # THERE IS A TEMPLATE AND NOBODY HAS TRANSLATED IT YET. That is a miss, not a
                # «generated» — a reader sees Portuguese either way, and filing it under the column
                # that does not count against coverage is how a report reaches 100% with a
                # Portuguese page in front of it. `generated` now means only: no template exists.
                self.faltas += 1
                if len(self.faltas_texto) < 3000:
                    self.faltas_texto.append(plano)
                return None
            self.gerados += 1
            return None
        if not i18n.translatable(texto):
            # Not translatable by the rules — but if a reader would still see Portuguese here, it is
            # a miss and the report has to say so. See i18n.parece_portugues().
            if i18n.parece_portugues(plano):
                self.faltas += 1
                if len(self.faltas_texto) < 3000:
                    self.faltas_texto.append(plano)
            return None
        self.faltas += 1
        if len(self.faltas_texto) < 3000:
            self.faltas_texto.append(plano)
        return None

    # ------------------------------------------------------------------ passes ---
    def pagina(self, html, raiz):
        """One traversal, two granularities, and no run examined twice.

        An earlier version ran a block pass over the whole page and then a text-run pass over the
        result. The second pass then met the first pass's OWN output — a translated paragraph, now
        split at the inline entity links that had just been put back into it — and dutifully
        reported it as untranslated. The coverage figure was wrong in the direction that invites
        somebody to translate text that is already translated. Splitting the page once and giving
        each region to exactly one pass makes double counting impossible rather than unlikely."""
        saida, pos = [], 0
        for m in BLOCOS.finditer(html):
            saida.append(self.texto(html[pos:m.start()]))
            saida.append(self.bloco(m, raiz))
            pos = m.end()
        saida.append(self.texto(html[pos:]))
        return "".join(saida)

    def bloco(self, m, raiz):
        """A paragraph, heading or list item whose whole text is a known segment, replaced by the
        translation. `raiz` is unused and kept so the two passes have one shape."""
        abre, etiqueta, dentro, fecha = m.groups()
        if "data-verbatim" in abre:
            # A builder has declared this element's text untranslatable — a name, a wordmark, a
            # quotation. Declared where it is written, which is the only place that knows.
            return abre + dentro + fecha
        if re.search(rf"<{etiqueta}\b", dentro, re.I):
            return m.group(0)          # nested block of the same kind: the regex cannot pair it
        # A tag becomes a SPACE, not nothing. Stripping it to nothing glued the masthead's wordmark
        # to the beta badge beside it — «O Ecossistema Português de IAbeta» — and offered the pair
        # to a translator as one phrase. Whitespace is collapsed by normalise() straight after, so
        # the space costs nothing where one was already there.
        if TAGS.search(dentro):
            # MIXED CONTENT IS NOT A SEGMENT. Replacing the inner HTML of a paragraph that contains
            # markup means rebuilding that markup from the translation, and the only links this
            # renderer can put back are entity links. A paragraph like the footer's «Responsável:
            # … O aviso.» carries a hand-made link to /aviso/ — which gate 14 requires on every page
            # that names people — and the block pass was quietly deleting it. So a block is a
            # segment only when its content is plain text; anything with a tag in it goes to the
            # finer pass, which substitutes the runs BETWEEN the tags and cannot touch a link.
            return abre + self.texto(dentro) + fecha
        plano = html.unescape(dentro)
        if substituivel(plano):
            traduzido = self.procurar(plano)
            if traduzido is not None:
                # NO RE-LINKING. An earlier version ran the entity linker over the translation, on
                # the reasoning that entity names are verbatim in every language so the links would
                # come back. Two things were wrong with it. The block pass now only fires on
                # TAG-FREE content, so the Portuguese block had no links to bring back — the linker
                # was ADDING links the page of record does not have. And each call carried its own
                # «already linked» set, so a name linked once per block became four links to one
                # entity on a page whose published formula allows one, which gate 24 caught on four
                # pages. A translation of a paragraph with no links is a paragraph with no links.
                return abre + paginas.e(traduzido) + fecha
        # Not a whole segment: fall through to the finer pass, which will catch the runs between
        # this paragraph's inline links.
        return abre + self.texto(dentro) + fecha

    def texto(self, html):
        """Whole text nodes. The split is the one build/paginas.py uses, so script, style, code and
        pre bodies are markup here and are never touched."""
        partes = MARCACAO.split(html)
        for i in range(0, len(partes), 2):
            bruto = partes[i]
            if not bruto.strip() or not substituivel(bruto):
                continue
            traduzido = self.procurar(bruto)
            if traduzido is None:
                continue
            esq = bruto[:len(bruto) - len(bruto.lstrip())]
            dir_ = bruto[len(bruto.rstrip()):]
            partes[i] = esq + paginas.e(traduzido) + dir_
        return "".join(partes)

    def atributos(self, html):
        def um(m):
            nome, valor = m.groups()
            if not substituivel(valor):
                return m.group(0)
            t = self.procurar(valor)
            return f'{nome}="{paginas.e(t)}"' if t else m.group(0)
        html = ATRIBUTOS.sub(um, html)

        def desc(m):
            t = self.procurar(m.group(2))
            return f'{m.group(1)}"{paginas.e(t)}"' if t else m.group(0)
        return re.sub(r'(<meta name="description" content=)"([^"]+)"', desc, html)


# ------------------------------------------------------------------- the head ---
def cabeca(html, rel, loc, todos, estados):
    """lang, canonical, og:url and the reciprocal hreflang set. Every page in every language names
    every other language's copy of itself and names the Portuguese original as `x-default`, which
    is what tells a search engine these are the same page and not duplicates."""
    url_pt = f'{SITE}/{rel.replace("index.html", "")}'
    prefixo = "" if loc == "pt" else f"{loc}/"
    aqui = f'{SITE}/{prefixo}{rel.replace("index.html", "")}'
    etiqueta = {"pt": "pt-PT", "en-gb": "en-GB", "fr": "fr-FR", "de": "de-DE"}.get(loc, loc)

    html = re.sub(r'<html lang="[^"]*"', f'<html lang="{etiqueta}"', html, count=1)
    html = re.sub(r'(<link rel="canonical" href=)"[^"]*"', rf'\1"{aqui}"', html, count=1)
    html = re.sub(r'(<meta property="og:url" content=)"[^"]*"', rf'\1"{aqui}"', html, count=1)

    alternativas = [f'<link rel="alternate" hreflang="x-default" href="{url_pt}">',
                    f'<link rel="alternate" hreflang="pt-PT" href="{url_pt}">']
    for codigo in todos:
        # The language of record is already named twice above, as x-default and as pt-PT. Emitting it
        # again from this loop produced `hreflang="pt" href="…/pt/"` — a path that does not exist,
        # because the Portuguese tree IS the root and is not a locale directory.
        if estados.get(codigo) != "publicado" or codigo == "pt":
            continue
        et = {"en-gb": "en-GB", "fr": "fr-FR", "de": "de-DE"}.get(codigo, codigo)
        alternativas.append(f'<link rel="alternate" hreflang="{et}" '
                            f'href="{SITE}/{codigo}/{rel.replace("index.html", "")}">')
    bloco = "\n".join(alternativas)
    # Idempotent: the previous run's block goes before this one's goes in.
    html = re.sub(r'\n?<link rel="alternate" hreflang="[^"]*" href="[^"]*">', "", html)
    return html.replace("</head>", bloco + "\n</head>", 1)


def seletor(pagina_html, rel, loc, reg):
    """Rebuild the language run for THIS tree: the current mark on this locale, and every href
    recomputed from this page's depth inside it.

    The markup is generated once, in Portuguese, where the hrefs are relative and correct. One
    directory deeper they are not, and the generic link pass cannot fix them either, because that
    pass asks «is the target a page this run localised?» — and a link INTO another locale tree is
    never that. So this is the one link on the page rewritten from its own data: `data-lang` says
    which language each entry is for, and the rest follows from `rel`.
    """
    caminho = rel[:-len("index.html")] if rel.endswith("index.html") else rel
    raiz = "../" * (caminho.rstrip("/").count("/") + (1 if caminho.strip("/") else 0) + 1)
    por_codigo = {lc["codigo"]: lc for lc in reg["locales"]}

    def um(m):
        classes, codigo = m.group(1), m.group(2)
        classes = " ".join(c for c in classes.split() if c != "aqui")
        if codigo == loc:
            classes += " aqui"
        lc = por_codigo.get(codigo, {})
        prefixo = "" if lc.get("e_registo") else codigo + "/"
        return (f'<a class="{classes}" data-lang="{codigo}" '
                f'hreflang="{lc.get("etiqueta_html", codigo)}" href="{raiz}{prefixo}{caminho}"')

    return re.sub(r'<a class="([^"]*)" data-lang="([^"]+)" hreflang="[^"]*" href="[^"]*"',
                  um, pagina_html)


def ligacoes(html, rel, loc, conjunto):
    """A locale page is one directory deeper than its Portuguese original. A link that stays inside
    the localised set needs no change, because the tree mirrors exactly. A link that leaves it —
    an asset, a frozen copy, the console — needs one more `../`."""
    pasta = posixpath.dirname(rel)

    def um(m):
        attr, u = m.group(1), m.group(2)
        if u.startswith(("http://", "https://", "//", "#", "mailto:", "data:", "javascript:")):
            return m.group(0)
        if u.startswith("/"):
            alvo = u.lstrip("/")
            destino = alvo if alvo.endswith(".html") else alvo.rstrip("/") + "/index.html"
            return f'{attr}="/{loc}/{alvo}"' if destino in conjunto else m.group(0)
        # RESOLVE, THEN RE-RELATIVISE. An earlier version simply prepended one «../» to anything
        # that left the localised set, on the reasoning that a locale page sits one level deeper.
        # That is right for a link written from the root — `assets/site.css` — and wrong for a link
        # to a SIBLING file: an article page links `comentarios.json` beside it, and one extra «../»
        # pointed at a directory that holds no such file. Resolving the target to a root-relative
        # path and then asking posixpath for the way there from the locale page is right in both
        # cases and in the ones nobody has written yet.
        alvo_bruto = u.split("#")[0].split("?")[0]
        if not alvo_bruto:
            return m.group(0)                      # a bare fragment or query: same page either way
        cauda = u[len(alvo_bruto):]
        alvo = posixpath.normpath(posixpath.join(pasta, alvo_bruto))
        destino = alvo if alvo.endswith(".html") else (alvo.rstrip("/") + "/index.html"
                                                      if alvo not in ("", ".") else "index.html")
        if destino in conjunto:
            return m.group(0)                      # the locale tree mirrors: the same path is right
        novo = posixpath.relpath(alvo, posixpath.join(loc, pasta) if pasta else loc)
        if alvo_bruto.endswith("/") and not novo.endswith("/"):
            novo += "/"
        return f'{attr}="{novo}{cauda}"'

    return re.sub(r'\b(href|src)="([^"]*)"', um, html)


def aviso_de_lingua(html, loc, rel, cobertura):
    """One line, in the locale, saying what this page is and what it is not: a translation of a
    Portuguese page of record, and where that page is. On a site whose first rule is that a claim
    walks back to bytes, a translation has to say that it is one."""
    caminho = rel[:-len("index.html")] if rel.endswith("index.html") else rel
    original = ("../" * (caminho.rstrip("/").count("/") + (1 if caminho.strip("/") else 0) + 1)
                + caminho)
    texto = {
        "en-gb": ('This page is a translation. The page of record is the Portuguese one, and every '
                  'claim on it walks back to the bytes named there.'),
        "fr": ('Cette page est une traduction. La page de référence est la page portugaise, et '
               'chaque affirmation y renvoie aux octets qui y sont nommés.'),
        "de": ('Diese Seite ist eine Übersetzung. Maßgeblich ist die portugiesische Seite; jede '
               'Aussage dort führt auf die genannten Bytes zurück.'),
    }.get(loc, "This page is a translation of the Portuguese page of record.")
    rotulo = {"en-gb": "Portuguese original", "fr": "original en portugais",
              "de": "portugiesisches Original"}.get(loc, "original")
    # The coverage figure is part of what this line SAYS, so it says it in the locale's own language.
    # It read «100% translated» on the French page, which is a page telling a French reader, in
    # English, how much of it is French.
    quanto = {"en-gb": f"{cobertura}% translated", "fr": f"{cobertura}% traduit",
              "de": f"{cobertura}% übersetzt"}.get(loc, f"{cobertura}%")
    bloco = (f'<div class="aviso-bloco"><p class="sm">{texto} '
             f'<a href="{original}">{rotulo}</a> · '
             f'<span class="mono xs">{quanto}</span></p></div>')
    return html.replace("<body>", "<body>\n" + bloco, 1)


# --------------------------------------------------------------------- driver ---
def render(loc, destino, estados, relatorio_apenas=False):
    conjunto = set(paginas_de_leitura())
    todos = [lc["codigo"] for lc in registo()["locales"]]
    t = Tradutor(loc)
    por_pagina = {}
    for rel in sorted(conjunto):
        html = (ROOT / rel).read_text(encoding="utf-8")
        antes = (t.acertos, t.faltas)
        raiz = "../" * (rel.count("/"))
        html = t.pagina(html, raiz)
        html = t.atributos(html)
        a, f = t.acertos - antes[0], t.faltas - antes[1]
        cob = round(100 * a / (a + f)) if (a + f) else 100
        por_pagina[rel] = (a, f, cob)
        if relatorio_apenas:
            continue
        html = cabeca(html, rel, loc, todos, estados)
        html = ligacoes(html, rel, loc, conjunto)
        html = seletor(html, rel, loc, registo())
        html = aviso_de_lingua(html, loc, rel, cob)
        fora = destino / rel
        fora.parent.mkdir(parents=True, exist_ok=True)
        fora.write_text(html, encoding="utf-8")
    return t, por_pagina


def cmd_relatorio():
    reg = registo()
    estados = {lc["codigo"]: lc["estado"] for lc in reg["locales"]}
    fontes = i18n.carregar_fontes()
    print(f'source: {len(fontes["segmentos"])} segments, {fontes["palavras"]} words')
    print(f'pages that can be localised: {len(paginas_de_leitura())}')
    print(f'{"locale":<8} {"estado":<12} {"hits":>7} {"missing":>8} {"generated":>10} '
          f'{"verbatim":>9} {"coverage":>9}')
    faltas = {}
    for lc in reg["locales"]:
        if lc.get("e_registo"):
            continue
        t, _ = render(lc["codigo"], None, estados, relatorio_apenas=True)
        total = t.acertos + t.faltas
        cob = round(100 * t.acertos / total, 1) if total else 0.0
        print(f'{lc["codigo"]:<8} {lc["estado"]:<12} {t.acertos:>7} {t.faltas:>8} '
              f'{t.gerados:>10} {t.verbatim:>9} {cob:>8}%')
        faltas[lc["codigo"]] = t.faltas_texto
    print()
    # THE LIST, NOT JUST THE NUMBER. dados/i18n/vocabulario.json says to extend itself from this
    # report — «--relatorio lists every run a reader would see in Portuguese that the memory cannot
    # serve, most frequent first» — and the report did not list them. A number nobody can act on is
    # the same problem as a number that reads 100% over a Portuguese page.
    for loc, textos in faltas.items():
        if not textos:
            continue
        contagem = {}
        for s in textos:
            contagem[s] = contagem.get(s, 0) + 1
        print(f'{loc}: {len(contagem)} distinct runs a reader would see in Portuguese, '
              f'{len(textos)} occurrences')
        for s, n in sorted(contagem.items(), key=lambda kv: (-kv[1], kv[0]))[:40]:
            print(f'  {n:>5}  {s[:110]}')
        print()
    print("Counted over every substitutable run on every page, so this is the coverage a reader")
    print("would see and not the coverage of the segment list. `generated` is a date line, a count")
    print("or a version badge: not translated as text, and not counted against coverage, because")
    print("translating one buys a cache miss tomorrow — see i18n.gerado().")


def main(argv):
    if argv and argv[0] == "--relatorio":
        return cmd_relatorio()
    reg = registo()
    estados = {lc["codigo"]: lc["estado"] for lc in reg["locales"]}
    if argv and argv[0] == "--ensaio":
        loc, destino = argv[1], Path(argv[2])
        shutil.rmtree(destino, ignore_errors=True)
        t, por = render(loc, destino, dict(estados, **{loc: "publicado"}))
        total = t.acertos + t.faltas
        print(f'locales --ensaio {loc}: {len(por)} pages into {destino}, '
              f'{t.acertos} hits / {t.faltas} misses '
              f'({round(100 * t.acertos / total, 1) if total else 0}% coverage)')
        return
    # The language of record is not rendered by this file — it IS what this file reads. A version
    # that forgot the `e_registo` test wrote a complete second copy of the Portuguese site into
    # /pt/, with every relative link one level short, and the only thing that noticed was the page
    # count in its own output line.
    publicados = [lc for lc in reg["locales"]
                  if lc["estado"] == "publicado" and not lc.get("e_registo")]
    if not publicados:
        print("locales: 0 published — the engine is ready and no locale is rendered. "
              "dados/i18n/locales.json is the editor's switch; see docs/guidance/multilingual.md")
        return
    for lc in publicados:
        destino = ROOT / lc["codigo"]
        shutil.rmtree(destino, ignore_errors=True)
        t, por = render(lc["codigo"], destino, estados)
        total = t.acertos + t.faltas
        print(f'locales {lc["codigo"]}: {len(por)} pages, {t.acertos} hits / {t.faltas} misses '
              f'({round(100 * t.acertos / total, 1) if total else 0}% coverage)')


if __name__ == "__main__":
    main(sys.argv[1:])

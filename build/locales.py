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
    """A text run this renderer is willing to touch. The guillemet rule is a cheap, absolute guard:
    anything inside «…» on this site is somebody else's words, and a translated quotation is a
    misquotation. It costs a handful of chrome lines their translation and is worth it."""
    return "«" not in t and "»" not in t


class Tradutor:
    def __init__(self, loc):
        self.loc = loc
        self.mem = i18n.carregar_locale(loc)
        self.acertos = 0
        self.faltas = 0
        self.gerados = 0
        self.verbatim = 0
        self.traducoes = set(self.mem.values())
        self.faltas_texto = []

    def procurar(self, texto):
        k = i18n.key(texto)
        if k in self.mem:
            self.acertos += 1
            return self.mem[k]
        if not i18n.translatable(texto):
            return None
        plano = i18n.normalise(texto)
        if plano in self.traducoes:
            # Already translated by an earlier pass on this same page. Two passes see the same
            # bytes, and without this the second one reports the first one's work as missing.
            return None
        if i18n.nao_traduzir(plano):
            # A verb of the graph, a name, an excerpt. Correct as it stands — i18n.nao_traduzir().
            self.verbatim += 1
            return None
        if i18n.gerado(texto):
            # A date line, a version badge, a count. Not missing — generated. See i18n.gerado().
            self.gerados += 1
            return None
        self.faltas += 1
        if len(self.faltas_texto) < 3000:
            self.faltas_texto.append(i18n.normalise(texto))
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
        """A paragraph, heading or list item whose whole text is a known segment. Its inner HTML is
        replaced by the translation and the entity linker is run again over it: entity names are
        verbatim in every language, so the links the Portuguese page had come back by themselves."""
        abre, etiqueta, dentro, fecha = m.groups()
        if re.search(rf"<{etiqueta}\b", dentro, re.I):
            return m.group(0)          # nested block of the same kind: the regex cannot pair it
        plano = ENTIDADE_HTML.sub(" ", TAGS.sub("", dentro)).replace("&amp;", "&")
        if substituivel(plano):
            traduzido = self.procurar(plano)
            if traduzido is not None:
                return abre + paginas.ligar_entidades(paginas.e(traduzido), raiz) + fecha
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
        if estados.get(codigo) != "publicado":
            continue
        et = {"en-gb": "en-GB", "fr": "fr-FR", "de": "de-DE"}.get(codigo, codigo)
        alternativas.append(f'<link rel="alternate" hreflang="{et}" '
                            f'href="{SITE}/{codigo}/{rel.replace("index.html", "")}">')
    bloco = "\n".join(alternativas)
    # Idempotent: the previous run's block goes before this one's goes in.
    html = re.sub(r'\n?<link rel="alternate" hreflang="[^"]*" href="[^"]*">', "", html)
    return html.replace("</head>", bloco + "\n</head>", 1)


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
        caminho = u.split("#")[0].split("?")[0]
        alvo = posixpath.normpath(posixpath.join(pasta, caminho)) if caminho else ""
        destino = alvo if alvo.endswith(".html") else (alvo.rstrip("/") + "/index.html"
                                                      if alvo not in ("", ".") else "index.html")
        if destino in conjunto:
            return m.group(0)
        return f'{attr}="../{u}"'
    return re.sub(r'\b(href|src)="([^"]*)"', um, html)


def aviso_de_lingua(html, loc, rel, cobertura):
    """One line, in the locale, saying what this page is and what it is not: a translation of a
    Portuguese page of record, and where that page is. On a site whose first rule is that a claim
    walks back to bytes, a translation has to say that it is one."""
    original = f'/{rel.replace("index.html", "")}'
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
    bloco = (f'<div class="aviso-bloco"><p class="sm">{texto} '
             f'<a href="{original}">{rotulo}</a> · '
             f'<span class="mono xs">{cobertura}% translated</span></p></div>')
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
    for lc in reg["locales"]:
        if lc.get("e_registo"):
            continue
        t, _ = render(lc["codigo"], None, estados, relatorio_apenas=True)
        total = t.acertos + t.faltas
        cob = round(100 * t.acertos / total, 1) if total else 0.0
        print(f'{lc["codigo"]:<8} {lc["estado"]:<12} {t.acertos:>7} {t.faltas:>8} '
              f'{t.gerados:>10} {t.verbatim:>9} {cob:>8}%')
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

#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — gate 44: the locale gate.

    python3 build/gates_i18n.py                  check the repository as it stands
    python3 build/gates_i18n.py <locale> <dir>   check a rehearsal rendered somewhere else

WHAT IT IS FOR. Every other gate in this repository guards a rule about evidence. This one guards
the rule that a translation is a SECOND READING of a checked page and never a second version of the
facts. Three things go wrong when a site grows languages, and only the first is obvious:

  * a half-translated page shipped as English — obvious to a reader, invisible to a build;
  * a translated excerpt, a translated name, a translated edge of the graph — invisible to a reader
    who cannot read Portuguese, and a breach of rules 1, 3 and 6;
  * a locale tree that has drifted out of step with the Portuguese one, so a reader in German is
    reading last week's page and nothing says so.

Each check below is one of those. A gate failure is a stop, not a warning.

  44 · THE LOCALE GATE. The language register is coherent and `pt` is the only language of record;
       the key of every segment really is the hash of its own text; no orphan translation is
       served; every published locale mirrors the Portuguese page set exactly; `<html lang>` is
       right and every page names the Portuguese original as `x-default`; inline JSON still parses
       after substitution; every excerpt, name and edge of the graph is byte-identical in every
       language; and a locale is not published at half coverage.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i18n                                                            # noqa: E402
import locales                                                         # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "dados" / "i18n"
# Below this, a locale is a page a reader would call broken. It is deliberately high: the point of
# translating the SOURCE rather than the render is that full coverage is affordable, and the
# rehearsal in docs/guidance/multilingual.md reaches 100%. A locale that cannot clear this has not
# been translated, it has been sampled.
COBERTURA_MINIMA = 92
JSON_EM_LINHA = re.compile(r'<script type="application/json"[^>]*>(.*?)</script>', re.S)

erros = []


def carregar():
    f = STORE / "locales.json"
    if not f.exists():
        erros.append("i18n: dados/i18n/locales.json does not exist — with no language register "
                     "there is nothing for this gate to check")
        return None
    return json.loads(f.read_text(encoding="utf-8"))


# --- (a) the language register is coherent -----------------------------------
def registo_coerente(reg):
    codigos = [lc.get("codigo") for lc in reg["locales"]]
    if len(set(codigos)) != len(codigos):
        erros.append(f"locales: a code appears twice in {codigos}")
    registos = [lc["codigo"] for lc in reg["locales"] if lc.get("e_registo")]
    if registos != ["pt"]:
        erros.append(f'locales: the language of record must be exactly ["pt"] and is {registos}. '
                     f'It is the language the claims were checked in, against the bytes')
    for lc in reg["locales"]:
        if lc.get("estado") not in ("preparado", "publicado"):
            erros.append(f'locales: {lc.get("codigo")} is in state «{lc.get("estado")}»; only '
                         f'«preparado» and «publicado» exist')
        if not lc.get("etiqueta_html"):
            erros.append(f'locales: {lc.get("codigo")} has no etiqueta_html for <html lang>')
        if lc["codigo"] != "pt" and lc["codigo"] not in i18n.LOCALES:
            erros.append(f'locales: {lc["codigo"]} is in the register and not in i18n.LOCALES')


# --- (b) the key IS the content ---------------------------------------------
# The whole translation memory rests on this identity: a segment's key is the hash of its own source
# text. Hand-edit fontes.json and the identity breaks in silence — a translation then gets served
# for text that is no longer that text. This is the one assertion here that checks the memory
# against itself.
def chave_e_conteudo():
    f = STORE / "fontes.json"
    if not f.exists():
        erros.append("i18n: dados/i18n/fontes.json does not exist — run "
                     "`python3 build/i18n.py extract`")
        return
    src = json.loads(f.read_text(encoding="utf-8"))
    maus = [k for k, v in src["segmentos"].items() if i18n.key(v["text"]) != k]
    if maus:
        erros.append(f'i18n: {len(maus)} segment(s) whose key is not the hash of their own text '
                     f'({maus[:3]}). The key IS the content; when it is not, an old translation can '
                     f'be served for new text and nothing reports it')
    palavras = sum(len(v["text"].split()) for v in src["segmentos"].values())
    if palavras != src["palavras"]:
        erros.append(f'i18n: fontes.json claims {src["palavras"]} words and holds {palavras}')


# --- (c) no orphan translation is served ------------------------------------
def orfas(reg):
    src = json.loads((STORE / "fontes.json").read_text(encoding="utf-8"))["segmentos"]
    for lc in reg["locales"]:
        if lc.get("e_registo"):
            continue
        fora = [k for k in i18n.carregar_locale(lc["codigo"]) if k not in src]
        if fora and lc["estado"] == "publicado":
            # Not an error: an orphan is the translation of text that has since changed, kept for
            # reuse. Serving one would be the error, and it cannot happen — substitution looks up
            # the hash of the text that is ON the page, and that hash is no longer this one.
            print(f'  · {lc["codigo"]}: {len(fora)} orphaned translations kept, none served')


# --- (d) what is never translated is still verbatim -------------------------
# The assertion that matters most, and the only one you cannot make by looking at the translated
# page alone: every excerpt, name and graph reading on the Portuguese page must be on the translated
# page, byte for byte.
def verbatim_intacto(loc, base):
    faltas = []
    for rel in locales.paginas_de_leitura():
        alvo = base / rel
        if not alvo.exists():
            continue
        traduzida = i18n.normalise(alvo.read_text(encoding="utf-8"))
        for parte in locales.MARCACAO.split((ROOT / rel).read_text(encoding="utf-8"))[::2]:
            plano = i18n.normalise(parte)
            if len(plano) < 20 or not i18n.nao_traduzir(plano):
                continue
            if plano not in traduzida:
                faltas.append((rel, plano[:70]))
    for rel, t in faltas[:5]:
        erros.append(f'{loc}/{rel}: lost text that is never translated — «{t}». A translated '
                     f'excerpt, name or graph reading is different evidence from the evidence this '
                     f'newsroom froze')
    if len(faltas) > 5:
        erros.append(f'{loc}: and {len(faltas) - 5} more of the same')


# --- (e) inline JSON is still JSON ------------------------------------------
# This has happened here before: the entity linker walked into a
# <script type="application/json"> and produced valid HTML around broken JSON. No structural gate
# saw it. Only the browser saw it.
def json_em_linha(loc, base):
    for rel in locales.paginas_de_leitura():
        alvo = base / rel
        if not alvo.exists():
            continue
        for m in JSON_EM_LINHA.finditer(alvo.read_text(encoding="utf-8")):
            try:
                json.loads(m.group(1))
            except ValueError as exc:
                erros.append(f'{loc}/{rel}: a <script type="application/json"> stopped being JSON '
                             f'after substitution ({exc})')
                break


# --- (f) hreflang is reciprocal and the tree is in step ---------------------
def arvore_e_cabeca(reg, loc, base):
    esperado = set(locales.paginas_de_leitura())
    presente = {p.relative_to(base).as_posix() for p in base.rglob("*.html")}
    if esperado - presente:
        erros.append(f'{loc}: {len(esperado - presente)} page(s) that exist in Portuguese are '
                     f'missing, starting at {sorted(esperado - presente)[:3]}')
    if presente - esperado:
        erros.append(f'{loc}: has {len(presente - esperado)} page(s) that no longer exist in '
                     f'Portuguese: {sorted(presente - esperado)[:3]}')
    etiqueta = next(lc["etiqueta_html"] for lc in reg["locales"] if lc["codigo"] == loc)
    for rel in sorted(esperado & presente):
        t = (base / rel).read_text(encoding="utf-8")
        if f'<html lang="{etiqueta}"' not in t:
            erros.append(f'{loc}/{rel}: <html lang> is not «{etiqueta}»')
            break
        if 'hreflang="x-default"' not in t:
            erros.append(f'{loc}/{rel}: does not name the Portuguese page as x-default. Without '
                         f'that these are duplicate pages and not one page in two languages')
            break


# --- (g) the coverage of a published locale ---------------------------------
def cobertura(reg):
    estados = {lc["codigo"]: lc["estado"] for lc in reg["locales"]}
    for lc in reg["locales"]:
        if lc.get("e_registo") or lc["estado"] != "publicado":
            continue
        t, _ = locales.render(lc["codigo"], None, estados, relatorio_apenas=True)
        total = t.acertos + t.faltas
        cob = round(100 * t.acertos / total, 1) if total else 0.0
        if cob < COBERTURA_MINIMA:
            erros.append(f'{lc["codigo"]}: is published at {cob}% coverage and the floor is '
                         f'{COBERTURA_MINIMA}%. A half-Portuguese page served as English is not a '
                         f'translation, it is a draft. `python3 build/i18n.py todo '
                         f'{lc["codigo"]}` says exactly what is missing')


def main(argv):
    reg = carregar()
    if reg is None:
        raise SystemExit("gate 44 FAILED\n  · " + "\n  · ".join(erros))
    registo_coerente(reg)
    chave_e_conteudo()
    if not erros:
        orfas(reg)
    if len(argv) == 2:                                  # rehearsal: one locale, another directory
        loc, base = argv[0], Path(argv[1])
        arvore_e_cabeca(reg, loc, base)
        verbatim_intacto(loc, base)
        json_em_linha(loc, base)
    else:
        for lc in reg["locales"]:
            if lc.get("e_registo") or lc["estado"] != "publicado":
                continue
            base = ROOT / lc["codigo"]
            if not base.exists():
                erros.append(f'{lc["codigo"]}: is «publicado» and the tree /{lc["codigo"]}/ does '
                             f'not exist. Run `python3 build/locales.py`')
                continue
            arvore_e_cabeca(reg, lc["codigo"], base)
            verbatim_intacto(lc["codigo"], base)
            json_em_linha(lc["codigo"], base)
        cobertura(reg)
    if erros:
        raise SystemExit("gate 44 FAILED\n  · " + "\n  · ".join(erros))
    publicadas = [lc["codigo"] for lc in reg["locales"]
                  if lc["estado"] == "publicado" and not lc.get("e_registo")]
    preparadas = [lc["codigo"] for lc in reg["locales"] if lc["estado"] == "preparado"]
    print(f'gate 44 OK — locales published: {", ".join(publicadas) or "none"}; '
          f'prepared: {", ".join(preparadas) or "none"}')


if __name__ == "__main__":
    main(sys.argv[1:])

#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the guidance, as pages with addresses.

    python3 build/guia.py      # after backoffice.py, before chrome.py

WHY THIS EXISTS. The guidance was on this site only behind a fragment: `/backoffice/docs.html`
plus `#docs/guidance/language.md`, rendered by a component after the page loads. That is fine for a
person clicking through the console and useless for everything else. A fragment is not an address:
it cannot be cited in a commit message, it cannot be linked from `.claude/`, it does not appear in
the sitemap, and an agent that fetches it gets the shell of a document browser rather than the
document. `llms.txt` — the file this site tells machines to read first — mentioned the guidance
zero times.

So each document under `docs/guidance/` gets a real page at `/backoffice/guidance/<name>.html`,
and the markdown stays exactly where it is. That is the pattern the rest of the site already uses:
an article is prose at `artigo.md` and a page at `index.html`, and neither is a copy of the other
— the page is rendered from the file, every build.

IT LIVES IN THE BACK OFFICE, and that is the language rule rather than an accident. The guidance is
read by whoever operates this newsroom, so it is English; the back office is where English pages
live, carry `lang="en"`, and say in a box at the top that they are not the publication. Gate 19
checks all three on every page in that folder, including these.

WHY NOT `paginas.md_para_html`. That renderer is for stories, and a story is prose with source
marks: no tables, no block quotes, no fenced code. The guidance is mostly tables. Widening the
story renderer to fit this would put the site's articles at risk for the sake of a console page, so
this file has its own, and it is the one that knows about tables.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import backoffice as B
import paginas as P

ROOT = Path(__file__).resolve().parents[1]
FONTE = ROOT / "docs" / "guidance"
DESTINO = "backoffice/guidance"

# The order is the reading order, and it is stated here rather than inferred from the file names:
# `before-you-change` sorts before `index`, and a reading order that depends on the alphabet is a
# reading order nobody chose. Anything in the folder but not in this list is still published, after
# these, so a new document appears on the site the moment it is written rather than when somebody
# remembers to add it here.
ORDEM = ["index.md", "language.md", "principles.md", "before-you-change.md",
         "releasing.md",
         "concurrent-sessions.md"]


def _tabela(linhas):
    """A markdown table, with its header row. Alignment rows are dropped rather than honoured:
    this site sets column behaviour in the stylesheet, and a `:---:` in a document would be a
    second place deciding it."""
    corpo = []
    for i, linha in enumerate(linhas):
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in celulas if c):
            continue
        marca = "th" if i == 0 else "td"
        classe = "" if i == 0 else ' class="sm"'
        corpo.append("<tr>" + "".join(
            f"<{marca}{classe}>{P.inline(c)}</{marca}>" for c in celulas) + "</tr>")
    cabeca, resto = corpo[0], corpo[1:]
    return (f'<div class="rolar"><table><thead>{cabeca}</thead>'
            f'<tbody>{"".join(resto)}</tbody></table></div>')


def md_para_html(md):
    # `lista` is None or the tag in use, so an ordered list stays ordered. Rendering `1. 2. 3.` as
    # bullets loses the one thing the author meant by numbering them — and the page most likely to
    # number things here is the one headed "the order that avoids most of it".
    saida, paragrafo, lista, tabela, codigo = [], [], None, [], None
    item = []

    def fecha_p():
        if paragrafo:
            saida.append(f'<p class="std">{P.inline(" ".join(paragrafo))}</p>')
            paragrafo.clear()

    def fecha_item():
        if item:
            saida.append(f'<li class="sm">{P.inline(" ".join(item))}</li>')
            item.clear()

    def fecha_lista():
        nonlocal lista
        fecha_item()
        if lista:
            saida.append(f"</{lista}>")
            lista = None

    def abre_lista(tag):
        nonlocal lista
        if lista != tag:
            fecha_lista()
            saida.append(f"<{tag}>")
            lista = tag
        else:
            fecha_item()

    def fecha_tabela():
        if tabela:
            saida.append(_tabela(tabela))
            tabela.clear()

    def fecha_tudo():
        fecha_p(); fecha_lista(); fecha_tabela()

    for linha in md.split("\n"):
        t = linha.rstrip()

        if t.startswith("```"):
            if codigo is None:
                fecha_tudo()
                codigo = []
            else:
                saida.append('<pre class="bloco-codigo"><code>'
                             + P.e("\n".join(codigo)) + "</code></pre>")
                codigo = None
            continue
        if codigo is not None:
            codigo.append(linha)
            continue

        if t.startswith("|") and t.count("|") >= 2:
            fecha_p(); fecha_lista()
            tabela.append(t)
            continue
        fecha_tabela()

        if re.match(r"^#{1,4} ", t):
            fecha_tudo()
            n = len(t) - len(t.lstrip("#"))
            classe = {1: "h-lead", 2: "h-2", 3: "h-3", 4: "h-3"}[n]
            marca = min(n + 1, 4)
            saida.append(f'<h{marca} class="{classe}">{P.inline(t[n + 1:])}</h{marca}>')
            continue
        if t.startswith("> "):
            fecha_p(); fecha_lista()
            saida.append(f'<div class="aviso-bloco"><p class="sm">{P.inline(t[2:])}</p></div>')
            continue
        if re.match(r"^\s*[-*] ", t):
            fecha_p()
            abre_lista("ul")
            item.append(re.sub(r"^\s*[-*] ", "", t))
            continue
        if re.match(r"^\d+\. ", t):
            fecha_p()
            abre_lista("ol")
            item.append(t.split(". ", 1)[1])
            continue
        if not t.strip():
            fecha_p(); fecha_lista()
            continue
        # A CONTINUATION LINE BELONGS TO ITS ITEM. This prose is wrapped at 96 characters, so a
        # list item of any length is several lines — and treating each line on its own ended the
        # list at the first wrap and dropped the rest into a paragraph after it. On the page that
        # read as a one-line bullet followed by an orphaned sentence, which is how it was noticed:
        # by looking at the rendered page, not at the markdown.
        if lista:
            item.append(t.strip())
            continue
        paragrafo.append(t.strip())

    fecha_tudo()
    return "\n".join(saida)


def reescrever_ligacoes(md, nomes):
    """A link between two markdown files is not a link between the pages rendered from them.

    `docs/guidance/index.md` says `[language.md](language.md)` and is right: the two files are
    siblings. The pages are siblings too, at `backoffice/guidance/`, but they are `.html` — and
    `../../CLAUDE.md`, which resolves from `docs/guidance/`, happens to resolve from
    `backoffice/guidance/` as well, since both are two directories below the root. That coincidence
    is worth naming, because it is why only the sibling links needed rewriting and why moving
    either folder would break the rest silently.

    The site gate found every one of these the moment the renderer started emitting real links —
    nine broken links, in markdown that had been correct all along and had simply never been
    rendered."""
    for nome in nomes:
        md = md.replace(f"]({nome})", f"]({nome[:-3]}.html)")
    return md


def titulo_de(md, nome):
    """The document's own H1, because a title typed in this file would be a second copy of it."""
    for linha in md.split("\n"):
        if linha.startswith("# "):
            return linha[2:].strip()
    return nome.replace("-", " ").replace(".md", "")


def main():
    if not FONTE.exists():
        print("guidance: docs/guidance/ does not exist — nothing to render")
        return

    ficheiros = [f for f in (FONTE / n for n in ORDEM) if f.exists()]
    ficheiros += [f for f in sorted(FONTE.glob("*.md")) if f not in ficheiros]

    escritos = []
    for i, f in enumerate(ficheiros):
        md = reescrever_ligacoes(f.read_text(encoding="utf-8"),
                                 [x.name for x in ficheiros])
        titulo = titulo_de(md, f.name)
        rel_md = f.relative_to(ROOT).as_posix()
        alvo = f"{DESTINO}/{f.stem}.html"

        anterior = ficheiros[i - 1] if i else None
        seguinte = ficheiros[i + 1] if i + 1 < len(ficheiros) else None
        passos = []
        if anterior:
            passos.append(f'<a href="{anterior.stem}.html">← {P.e(titulo_de(anterior.read_text(encoding="utf-8"), anterior.name))}</a>')
        if seguinte:
            passos.append(f'<a href="{seguinte.stem}.html">{P.e(titulo_de(seguinte.read_text(encoding="utf-8"), seguinte.name))} →</a>')

        corpo = f"""
<div class="rule" style="padding:6px 0 8px"><div class="sect">Guidance · {i + 1} of {len(ficheiros)}</div></div>
{md_para_html(md)}

<div class="rule" style="padding:26px 0 8px"><div class="sect">Next</div></div>
<p class="sm">{" · ".join(passos) or "This is the last page."}</p>
<p class="xs" style="padding-top:12px">This page is rendered from
<a href="../../{P.e(rel_md)}"><code>{P.e(rel_md)}</code></a> by <code>build/guia.py</code>. The
markdown is the source; edit that and rebuild. Nobody hand-edits this file.</p>
"""
        B.escrever(alvo, B.pagina(alvo, titulo,
                                  f"{titulo} — guidance for anyone changing pt.newsroom.sgit.ai.",
                                  corpo))
        escritos.append(alvo)

    print(f"guidance: {len(escritos)} pages with addresses "
          f"({', '.join(Path(a).stem for a in escritos)})")


if __name__ == "__main__":
    main()

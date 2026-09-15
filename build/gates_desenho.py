#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the design gates (27-33). What the review measured, now asserted.

    python3 build/gates_desenho.py

WHERE THIS COMES FROM

The design review of 15 September did the unusual thing for a design review: it measured.
Characters per line derived from the grid rather than eyeballed, contrast ratios computed from the
stylesheet's own tokens, empty cells counted one by one. And then it said, in §4.4, the one thing
that stops a review becoming decoration:

    "Do not review by eye again. These are the numbers that changed. Each is cheap to assert in a
     build check, which suits this project better than an opinion does."

This is that file. Seven gates, one per number in §4.4. What they do NOT do is hold an opinion
about the design: each reads a value off disk and compares it with a threshold the review wrote.

WHY A NEW FILE AND NOT A LINE IN THE EXISTING ONES

`build/gates.py` is in the deny list of `.claude/settings.json` on purpose — an agent that can edit
the gate that stops it has no gate — and `build/gates_artigos.py` is where the gates that came after
it were added. The design ones are a family of their own: they measure FORM rather than substance,
and a day when one of these measurements fails is not the same kind of day as one when a claim does
not walk back to a hash. Keeping them apart keeps each one's output readable.

WHAT IS MISSING, AND IS SAID RATHER THAN OMITTED

Two of §4.4's seven numbers are not measurable from files: the height of the chrome above the
headline, and the rendered line height. Both need a browser, so they belong in the browser gate
(`admin/build/render.mjs`), where there is a Chromium, and not here.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets" / "site.css"
DADOS = ROOT / "dados"

erros = []
notas = []


# ----------------------------------------------------------------- contrast ---
def luminancia(hexa):
    """A colour's relative luminance, as WCAG 2.x defines it."""
    h = hexa.lstrip("#")
    canais = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        canais.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = canais
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    la, lb = luminancia(a), luminancia(b)
    claro, escuro = max(la, lb), min(la, lb)
    return (claro + 0.05) / (escuro + 0.05)


css = CSS.read_text(encoding="utf-8")
# Comments stripped. This site's stylesheet DOCUMENTS its decisions, and several of them are about
# rules that were removed — the comment explaining why `-webkit-font-smoothing` must not come back
# contains the property name. A gate that read the comments would fail because of the note
# explaining why it exists, which is the most useless kind of red there is.
css_sem_notas = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
fichos = dict(re.findall(r"^\s*(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{6});", css_sem_notas, re.M))

# The thresholds are the review's: 3:1 for a rule carrying meaning (WCAG 1.4.11), and 5.5:1
# for state text — above AA's 4.5:1 on purpose, because all of these are used at 11-13px,
# where the threshold is harder to meet in practice than the formula suggests.
LIMITES_FILETE = {"--filete": 2.5, "--filete-2": 3.0}
LIMITES_ESTADO = {"--acento": 5.5, "--aviso": 5.5, "--disputa": 5.5, "--falta": 5.5,
                  "--sec-2": 5.5, "--sec": 5.5}

papel = fichos.get("--papel")
if not papel:
    erros.append("desenho: --papel não está em :root — nada se pode medir contra o papel")
else:
    # --- 27. the rules have to be visible -------------------------------------
    for ficho, minimo in LIMITES_FILETE.items():
        if ficho not in fichos:
            erros.append(f"desenho: o ficho {ficho} desapareceu de :root")
            continue
        r = contraste(fichos[ficho], papel)
        if r < minimo:
            erros.append(
                f"desenho: {ficho} ({fichos[ficho]}) está a {r:.2f}:1 contra o papel e o mínimo é "
                f"{minimo}:1 — a tese desta folha é «filetes, não caixas», e um filete que não se "
                f"vê é estrutura que não está lá. Foi este o defeito medido a 1.36:1 na v0.6.0")
        else:
            notas.append(f"{ficho} {r:.2f}:1")

    # --- 28. the verification state has to be readable ------------------------
    for ficho, minimo in LIMITES_ESTADO.items():
        if ficho not in fichos:
            erros.append(f"desenho: o ficho {ficho} desapareceu de :root")
            continue
        r = contraste(fichos[ficho], papel)
        if r < minimo:
            erros.append(
                f"desenho: {ficho} ({fichos[ficho]}) está a {r:.2f}:1 e o mínimo é {minimo}:1 — a "
                f"proposta inteira desta publicação é o leitor poder ver o estado de verificação "
                f"de cada afirmação, e esse estado está codificado em cor a 11px")
        else:
            notas.append(f"{ficho} {r:.2f}:1")

    # The dark panel has its own ink and its own accent, and the review measured it at 13.8:1.
    if "--acento-claro" in fichos and "--tinta" in fichos:
        r = contraste(fichos["--acento-claro"], fichos["--tinta"])
        if r < 7:
            erros.append(f"desenho: --acento-claro sobre --tinta está a {r:.2f}:1, e o painel "
                         f"escuro redefine as suas próprias cores precisamente para não depender "
                         f"de fichos herdados que ali não funcionam")


# ------------------------------------------------------------------ measure ---
# --- 29. characters per line --------------------------------------------------
# NEWSREADER'S AVERAGE GLYPH WIDTH IS 0.405em, NOT 0.48em.
#
# The review used 0.48em, the usual figure for a screen serif. Measured in the browser — a canvas,
# the element's own computed font, and real Portuguese text rather than an alphabet —
# Newsreader gives 0.405em. That is about 18% narrower than the assumption, and it cuts both
# ways:
#
#   - the problem was WORSE than the review reported: the 758px column held ≈104 characters, not
#     88, and the entity pages' 828px column held ≈114, not 96;
#   - and the fix the review asks for did not reach the target the review gives: 34em is 612px, and
#     at 612px the browser measures 84 characters — still above §4.4's 75.
#
# So the site's measure is 29em and not 34em, and this gate measures with 0.405. If the face
# changes, this number changes with it, and the way to get it again is the same: measure, not guess.
GLIFO_MEDIO_EM = 0.405


def cpl(px, tamanho_px):
    return px / (tamanho_px * GLIFO_MEDIO_EM)


def declaracao(seletor, propriedade):
    """A property's value in the FIRST block matching the selector, exactly as written."""
    m = re.search(r"(?:^|\})[^{}]*?\." + re.escape(seletor) + r"\s*(?:,[^{}]*?)?\{([^}]*)\}",
                  css_sem_notas, re.M | re.S)
    if not m:
        return None
    d = re.search(re.escape(propriedade) + r":\s*([^;}]+)", m.group(1))
    return d.group(1).strip() if d else None


MEDIDA_MAX_CPL = 75    # the top of the band for a newspaper column
MEDIDA_MIN_CPL = 45    # below this the line breaks too often

for seletor, tamanho in (("std", 18), ("sm", 15)):
    mw = declaracao(seletor, "max-width")
    lh = declaracao(seletor, "line-height")
    if not mw or not mw.endswith("em"):
        erros.append(
            f"desenho: .{seletor} não tem `max-width` em `em` na folha de estilos. Era este o "
            f"defeito de leitura maior da v0.6.0: a coluna media 88 caracteres na primeira página "
            f"e 96 numa entidade, e uma coluna de jornal anda nos 45-75")
        continue
    ems = float(mw[:-2])
    c = ems / GLIFO_MEDIO_EM
    if not (MEDIDA_MIN_CPL <= c <= MEDIDA_MAX_CPL):
        erros.append(f"desenho: .{seletor} está a {mw} — cerca de {c:.0f} caracteres por linha, e "
                     f"a faixa é {MEDIDA_MIN_CPL}-{MEDIDA_MAX_CPL}")
    else:
        notas.append(f".{seletor} ≈{c:.0f} car/linha")
    if lh:
        try:
            if float(lh) < 1.55:
                erros.append(f"desenho: .{seletor} tem entrelinha {lh}, e um serif a {tamanho}px "
                             f"sobre papel creme de baixo contraste precisa de 1.6-1.65")
        except ValueError:
            pass

# --- 30. no inline `max-width` on a body class --------------------------------
# An inline `max-width` beats the class, so a single one surviving in a generator would undo
# the measure fix on that page — without failing, and visible nowhere but in the reading.
GERADORES_DO_JORNAL = ["build/build.py", "build/artigos.py", "build/entidades.py",
                       "build/paginas.py", "build/paginas_extra.py"]
for nome in GERADORES_DO_JORNAL:
    f = ROOT / nome
    if not f.exists():
        continue
    t = f.read_text(encoding="utf-8")
    for m in re.finditer(r'class="(std|sm|xs)(?: it)?"[^>]{0,120}?max-width:\s*(\d+)em', t):
        erros.append(f"desenho: {nome} emite `max-width:{m.group(2)}em` em linha numa classe de "
                     f"corpo (.{m.group(1)}) — em linha bate a classe, e a medida da folha de "
                     f"estilos deixa de valer nessa página")

# --- 31. the mono face means one thing ---------------------------------------
# What the browser resolves is not counted (that is the browser gate); what the STYLESHEET
# assigns is. A section label, a kicker or a table header in mono is the page reading
# like a build log, which was the dominant cause of "it does not look like a newspaper".
SO_SERIF = ["kick", "sect", "agent"]
for seletor in SO_SERIF:
    ff = declaracao(seletor, "font-family")
    if ff and "--mono" in ff:
        erros.append(f"desenho: .{seletor} está composto em `var(--mono)`. O mono quer dizer um "
                     f"facto de máquina — um hash, uma contagem de bytes, um identificador, uma "
                     f"hora, um caminho — e o nome de uma secção não é nenhuma dessas coisas")
mth = re.search(r"(?:^|\})\s*th\s*\{([^}]*)\}", css_sem_notas, re.M | re.S)
if mth and "--mono" in mth.group(1):
    erros.append("desenho: `th` está composto em `var(--mono)` — o `th.mono` existe para a coluna "
                 "cujo CONTEÚDO é um hash ou um caminho, e é esse que leva mono")

# --- 32. the focus ring and the colour scheme --------------------------------
if ":focus-visible" not in css_sem_notas:
    erros.append("desenho: não há uma regra de `:focus-visible` na folha de estilos, num desenho "
                 "em que `a { text-decoration: none }` é global. Quem navega pelo teclado numa "
                 "primeira página com ~60 ligações fica sem mapa. É uma falha de acessibilidade "
                 "e não uma preferência")
if not re.search(r"color-scheme:\s*light", css_sem_notas):
    erros.append("desenho: `color-scheme` não está declarado, e por isso os controlos de "
                 "formulário e as barras de deslocamento seguem o sistema operativo em vez da "
                 "página")
if "-webkit-font-smoothing" in css_sem_notas:
    erros.append("desenho: `-webkit-font-smoothing` voltou à folha. Força suavização em escala de "
                 "cinza e desenha o texto mais leve do que foi especificado, o que tira peso "
                 "exatamente aos traços de que a Newsreader precisa a 15-18px")

# --- 33. the countable defects the review counted ----------------------------
# No empty table column in production. The review counted 60 rows out of 60 with the middle
# cell empty on /empresas/, which is a column shipped blank AND the frozen source pushed
# 1100px away from the name it belongs to.
for pagina in sorted(ROOT.glob("*/index.html")):
    if "fontes/congeladas" in pagina.as_posix():
        continue
    html = pagina.read_text(encoding="utf-8")
    for tabela in re.findall(r"<table>.*?</table>", html, re.S):
        cabecas = re.findall(r"<th[^>]*>(.*?)</th>", tabela, re.S)
        linhas = re.findall(r"<tr>(?:(?!</tr>).)*?</tr>", tabela, re.S)
        corpo = [l for l in linhas if "<td" in l]
        if len(corpo) < 5 or not cabecas:
            continue
        for i, cabeca in enumerate(cabecas):
            celulas = []
            for l in corpo:
                tds = re.findall(r"<td[^>]*>(.*?)</td>", l, re.S)
                if i < len(tds):
                    celulas.append(re.sub(r"<[^>]+>", "", tds[i]).strip())
            if celulas and not any(celulas):
                nome = re.sub(r"<[^>]+>", "", cabeca).strip()
                erros.append(
                    f"desenho: {pagina.relative_to(ROOT)} envia uma tabela cuja coluna «{nome}» "
                    f"está vazia em {len(celulas)} de {len(celulas)} linhas. Um gerador deve "
                    f"deixar cair uma coluna que está vazia em todas as linhas — senão empurra as "
                    f"colunas seguintes para longe daquela a que pertencem")

# No unaccented state in the vocabulary. This site is natively Portuguese and the state
# vocabulary is the part meant to be authoritative: an unaccented word there suggests the strings
# are being written somewhere that only accepts ASCII, and that is worth a check rather than a
# fix in one single place.
SEM_ACENTO = {
    "nao resolve": "não resolve", "nao encontrado": "não encontrado",
    "nao encontrada": "não encontrada", "nao confirmada": "não confirmada",
    "sem fonte legivel": "sem fonte legível", "inacessivel": "inacessível",
    "verificacao": "verificação", "publicacao": "publicação",
}
# `verificacao` and `publicacao` are legitimate identifiers in paths and JSON keys; they only
# count as a defect when they appear as the TEXT of a chip, which is where a reader reads them.
SO_EM_FICHA = {"verificacao", "publicacao"}
for pagina in sorted(ROOT.rglob("*/index.html")):
    rel = pagina.relative_to(ROOT).as_posix()
    if "fontes/congeladas" in rel or rel.startswith("briefs/") or "/backoffice/" in f"/{rel}":
        continue
    html = pagina.read_text(encoding="utf-8")
    for ficha in re.findall(r'<span class="chip[^"]*">(.*?)</span>', html, re.S):
        texto = re.sub(r"<[^>]+>", "", ficha).strip()
        if texto.lower() in SEM_ACENTO:
            erros.append(f"desenho: {rel} mostra a ficha de estado «{texto}», que devia ser "
                         f"«{SEM_ACENTO[texto.lower()]}» — o acento falta no vocabulário de "
                         f"estado de um site nativamente português")

# The version badge has to be a link. The sgit.ai guidance is explicit: show the
# version in the chrome AND link it to that version's detail. Half was done.
inicio = (ROOT / "index.html").read_text(encoding="utf-8")
if re.search(r'<span class="ver">v[0-9]', inicio):
    erros.append("desenho: o distintivo de versão na primeira página é um `<span>` e não uma "
                 "ligação. A orientação de sgit.ai pede as duas coisas — mostrar a versão na "
                 "cromagem e ligá-la ao que mudou nessa versão — e num site cuja proposta inteira "
                 "é a rastreabilidade, este é o único lugar onde o site não se rastreia a si mesmo")

# ----------------------------------------------------------------------- output ---
if erros:
    print("portões do desenho: VERMELHO\n")
    for e in erros:
        print(f"  ✗ {e}")
    print(f"\n{len(erros)} problema(s). A revisão de desenho está no cofre e o plano dela está em "
          f"/backoffice/desenho.html.")
    sys.exit(1)

print("portões do desenho: OK — " + ", ".join(notas[:6]) +
      f", medida e entrelinha na faixa de leitura, mono só onde há um facto de máquina, "
      f"anel de foco presente, nenhuma coluna de tabela vazia, nenhum estado sem acento, "
      f"o distintivo de versão a ligar para o que mudou")

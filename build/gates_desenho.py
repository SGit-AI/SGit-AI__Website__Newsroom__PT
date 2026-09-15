#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — os portões do desenho (27-33). O que a revisão mediu, agora asserido.

    python3 build/gates_desenho.py

DE ONDE ISTO VEM

A revisão de desenho do cofre `e54hfntq` (v0.1.0, 2026-09-15, contra a construção v0.6.0) fez uma
coisa invulgar para uma revisão de desenho: mediu. Caracteres por linha derivados da grelha e não
estimados a olho, razões de contraste calculadas a partir dos valores dos fichos em `:root`,
células vazias contadas uma a uma. E depois disse, na §4.4, a única coisa que impede uma revisão
de desenho de se desfazer sozinha ao longo de três releases:

    «Não voltar a revisar a olho. Estes são os números que mudaram. Cada um é barato de asserir
     numa verificação de construção, o que está mais de acordo com este projeto do que uma opinião
     de desenho está.»

É este ficheiro. Sete portões, um por número da §4.4. O que eles NÃO fazem é ter uma opinião sobre
o desenho: cada um lê um valor do disco e compara-o com um limite que a revisão escreveu.

PORQUE UM FICHEIRO NOVO E NÃO UMA LINHA NOS QUE JÁ EXISTEM

`build/gates.py` está na lista de recusa de `.claude/settings.json` de propósito — um agente que
possa editar o portão que o trava não tem portão — e `build/gates_artigos.py` é onde os portões que
vieram depois dele foram acrescentados. Os do desenho são uma família própria: medem a FORMA e não
a substância, e um dia em que uma medida destas falhe não é o mesmo tipo de dia que um em que uma
afirmação não ande para trás até um hash. Separá-los deixa a saída de cada um legível.

O QUE FALTA, E ESTÁ DITO EM VEZ DE SER OMITIDO

Dois dos sete números da §4.4 não se medem a partir de ficheiros: a altura da cromagem acima da
mancheta a 390px, e o número de elementos compostos em mono TAL COMO O NAVEGADOR OS RESOLVE. O
primeiro precisa de um navegador; o segundo precisa da cascata. Os dois vivem no portão do
navegador (`admin/build/render.mjs`), que é onde há um Chromium, e não aqui.
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


# --------------------------------------------------------------- o contraste ---
def luminancia(hexa):
    """A luminância relativa de uma cor, como a WCAG 2.x a define."""
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
# Sem os comentários. A folha deste site DOCUMENTA as suas decisões, e várias delas são sobre
# regras que foram retiradas — o comentário que explica porque `-webkit-font-smoothing` não deve
# voltar contém o nome da propriedade. Um portão que lesse os comentários falharia por causa da
# nota que explica porque ele existe, que é a forma mais inútil de vermelho que há.
css_sem_notas = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
fichos = dict(re.findall(r"^\s*(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{6});", css_sem_notas, re.M))

# Os limites são os da revisão: 3:1 para um filete que carrega significado (WCAG 1.4.11), e 5.5:1
# para texto de estado — acima do 4.5:1 do AA de propósito, porque todos estes são usados a 11-13px,
# onde o limite é mais difícil de cumprir na prática do que a fórmula sugere.
LIMITES_FILETE = {"--filete": 2.5, "--filete-2": 3.0}
LIMITES_ESTADO = {"--acento": 5.5, "--aviso": 5.5, "--disputa": 5.5, "--falta": 5.5,
                  "--sec-2": 5.5, "--sec": 5.5}

papel = fichos.get("--papel")
if not papel:
    erros.append("desenho: --papel não está em :root — nada se pode medir contra o papel")
else:
    # --- 27. os filetes têm de se ver -----------------------------------------
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

    # --- 28. o estado de verificação tem de se ler ----------------------------
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

    # O painel escuro tem a sua própria tinta e o seu próprio acento, e a revisão mediu-o a 13.8:1.
    if "--acento-claro" in fichos and "--tinta" in fichos:
        r = contraste(fichos["--acento-claro"], fichos["--tinta"])
        if r < 7:
            erros.append(f"desenho: --acento-claro sobre --tinta está a {r:.2f}:1, e o painel "
                         f"escuro redefine as suas próprias cores precisamente para não depender "
                         f"de fichos herdados que ali não funcionam")


# ------------------------------------------------------------------ a medida ---
# --- 29. os caracteres por linha ----------------------------------------------
# A LARGURA MÉDIA DE UM GLIFO DA NEWSREADER É 0.405em, E NÃO 0.48em.
#
# A revisão usou 0.48em, que é o número habitual para um serif de ecrã. Medido no navegador — uma
# tela, a fonte computada do próprio elemento, e texto português a sério em vez de um alfabeto —
# a Newsreader dá 0.405em. É cerca de 18% mais estreita do que a suposição, e isso corre nos dois
# sentidos:
#
#   - o problema era PIOR do que a revisão relatou: a coluna de 758px tinha ≈104 caracteres e não
#     88, e a de 828px das páginas de entidade tinha ≈114 e não 96;
#   - e a correção que a revisão pede não chegava ao alvo que a revisão dá: 34em são 612px, e a
#     612px o navegador mede 84 caracteres — ainda acima dos 75 da §4.4.
#
# Por isso a medida do site é 29em e não 34em, e este portão mede com 0.405. Se a face mudar, este
# número muda com ela, e a maneira de o voltar a obter é a de sempre: medir, não estimar.
GLIFO_MEDIO_EM = 0.405


def cpl(px, tamanho_px):
    return px / (tamanho_px * GLIFO_MEDIO_EM)


def declaracao(seletor, propriedade):
    """O valor de uma propriedade no PRIMEIRO bloco que casa com o seletor, tal e qual."""
    m = re.search(r"(?:^|\})[^{}]*?\." + re.escape(seletor) + r"\s*(?:,[^{}]*?)?\{([^}]*)\}",
                  css_sem_notas, re.M | re.S)
    if not m:
        return None
    d = re.search(re.escape(propriedade) + r":\s*([^;}]+)", m.group(1))
    return d.group(1).strip() if d else None


MEDIDA_MAX_CPL = 75    # o topo da faixa de uma coluna de jornal
MEDIDA_MIN_CPL = 45    # abaixo disto a linha parte-se demasiadas vezes

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

# --- 30. nenhum `max-width` em linha numa classe de corpo ---------------------
# Um `max-width` em linha bate a classe, e por isso um único que sobrevivesse num gerador desfazia
# a correção da medida naquela página — sem falhar, e sem se ver em lado nenhum senão na leitura.
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

# --- 31. o mono quer dizer uma coisa -----------------------------------------
# Não se conta o que o navegador resolve (isso é o portão do navegador); conta-se o que a FOLHA
# atribui. Um rótulo de secção, um antetítulo ou um cabeçalho de tabela em mono é a página a
# ler-se como um registo de construção, que era a causa dominante de «não parece um jornal».
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

# --- 32. o anel de foco e o esquema de cor -----------------------------------
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

# --- 33. os defeitos contáveis que a revisão contou --------------------------
# Nenhuma coluna de tabela vazia em produção. A revisão contou 60 linhas de 60 com a célula do
# meio vazia em /empresas/, o que é uma coluna enviada em branco E o empurrar da fonte congelada
# para 1100px de distância do nome a que pertence.
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

# Nenhum estado sem acento no vocabulário. Este site é nativamente português e o vocabulário de
# estado é a parte que é para ser autoritativa: uma palavra sem acento ali sugere que as cadeias
# estão a ser escritas em algum sítio que só aceita ASCII, e isso vale uma verificação e não uma
# correção num único lugar.
SEM_ACENTO = {
    "nao resolve": "não resolve", "nao encontrado": "não encontrado",
    "nao encontrada": "não encontrada", "nao confirmada": "não confirmada",
    "sem fonte legivel": "sem fonte legível", "inacessivel": "inacessível",
    "verificacao": "verificação", "publicacao": "publicação",
}
# `verificacao` e `publicacao` são identificadores legítimos em caminhos e em chaves de JSON; só
# contam como defeito quando aparecem como o TEXTO de uma ficha, que é onde um leitor os lê.
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

# O distintivo de versão tem de ser uma ligação. A orientação de sgit.ai é explícita: mostrar a
# versão na cromagem E ligá-la ao detalhe da versão. Metade estava feita.
inicio = (ROOT / "index.html").read_text(encoding="utf-8")
if re.search(r'<span class="ver">v[0-9]', inicio):
    erros.append("desenho: o distintivo de versão na primeira página é um `<span>` e não uma "
                 "ligação. A orientação de sgit.ai pede as duas coisas — mostrar a versão na "
                 "cromagem e ligá-la ao que mudou nessa versão — e num site cuja proposta inteira "
                 "é a rastreabilidade, este é o único lugar onde o site não se rastreia a si mesmo")

# ---------------------------------------------------------------------- saída ---
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

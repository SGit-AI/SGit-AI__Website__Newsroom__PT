#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — o caminho de ingestão. Fetch, freeze, hash, extract, diff.

    python3 build/extract.py               # re-extract from the frozen copies
    python3 build/extract.py --fetch       # take a new dated snapshot first

Adapted from `portugal/build/extract.py` at newsroom.sgit.ai v0.3.9 (briefs/pack/03__inherit/).
Section 4 of the brief says to copy this before writing anything of our own, because it is the one
part of the method already proven to work. Four of its properties are load-bearing and all four
are kept:

1. **Snapshots are dated, not singular.** `fontes/congeladas/<data>/`. One frozen copy proves a
   claim; a series proves a trajectory and shows what disappeared. On a moving beat the diff IS
   the story.
2. **Never read the live site at publish time.** Extraction runs against the frozen copy, so a
   page cannot change under a claim without the change appearing as a new hash.
3. **Frozen copies are `.snapshot`, not `.html`.** They are unmodified bytes of somebody else's
   pages, held as evidence. A non-HTML extension keeps them from being served or indexed as pages
   of this site: publishing a browsable mirror of another organisation's website under our domain
   would contradict the one rule this publication has, which is that it links rather than
   reproduces.
4. **The gate re-verifies every SHA-256 on every build.** If a frozen copy was edited, every claim
   resting on it is unsupported and the build stops (`build/gates.py`, portão 1).

WHAT CHANGES FOR THIS SITE, beyond the source list.

**Accents are data.** The corpus this method comes from enforces pure ASCII, and Portuguese is not
an ASCII language (brief §6). Nothing here normalises, strips or transliterates a character: bytes
are read as UTF-8 and names travel as the source wrote them. `gates.py` asserts the opposite of the
corpus rule — that the accents are present and derived from the frozen source rather than from a
list somebody typed.

**Contact details are refused where the data is PARSED, not where it is rendered** (brief §5,
CLAUDE.md rule 4). `sem_contactos()` runs over every extracted record before it is written, and a
field carrying an email address, a telephone number or a personal postal address is dropped there
and then. The gate checks the JSON afterwards, but the gate is the second line: a contact detail
that reaches the data and is merely hidden by a template is one careless loop away from being
published.

**Nobody's biography is reproduced.** The prose on a person's page is the writer's own work, not a
fact about the world. It is held in the frozen bytes for verification and never copied into a data
file. What may be read from it is a published formula (`dados/lexico.json`) that keeps only the
words it matched.

**A source that did not resolve is recorded, not dropped.** `fontes.TENTADAS` is re-attempted on
every run and what came back is written to `dados/excluidas.json` with the HTTP code. The size of
what cannot be seen belongs on the page (§10).
"""
import argparse
import hashlib
import html
import json
import re
import subprocess
import time
import unicodedata
from pathlib import Path

import fontes

ROOT = Path(__file__).resolve().parents[1]
CONGELADAS = ROOT / "fontes" / "congeladas"
DADOS = ROOT / "dados"

UA = ("Mozilla/5.0 (pt.newsroom.sgit.ai research; +https://pt.newsroom.sgit.ai/metodo/)")


# --------------------------------------------------------------- utilitários ---
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def capturas():
    if not CONGELADAS.exists():
        return []
    return sorted(d for d in CONGELADAS.iterdir()
                  if d.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.name))


def texto_de(p):
    """The visible text of a frozen page. Scripts, styles and SVG are removed first, so a claim is
    never matched against markup a reader cannot see. Read as UTF-8: the accents survive.

    `<noscript>` is NOT removed, and that is the whole reason this beat is readable at all. The
    event's site is a single-page application: fetched over HTTP, its agenda and speaker pages
    return a shell, and everything a reader would call the content lives in the static
    `<noscript>` fallback. Stripping it — which the sibling site's version of this function does,
    because its sources are server-rendered — made the agenda measure as an empty page. So the
    fallback is treated as the content, which is what it is: the bytes the publisher serves to a
    client that does not run scripts, and the only part of the page this newsroom can hash and
    stand a claim on."""
    s = p.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", s, flags=re.S | re.I)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", t)).split())


def recuo_estatico(p):
    """The largest <noscript> block of a frozen page: the publisher's own static fallback.

    Extraction reads THIS rather than the whole file, so a stray `<li>` in a tracking script in
    the document head can never be mistaken for a programme row — which is exactly what happened
    on the first run of this extractor."""
    s = p.read_text(encoding="utf-8", errors="replace")
    blocos = re.findall(r"<noscript[^>]*>(.*?)</noscript>", s, re.S)
    return max(blocos, key=len) if blocos else s


def sem_tags(x):
    return html.unescape(re.sub(r"<[^>]+>", "", x)).replace("\\n", " ").strip()


def mtime(p):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(p.stat().st_mtime))


# --- a recusa, aplicada onde os dados são lidos -------------------------------
# Artigo 24(4) da Lei 58/2019 proíbe a divulgação de moradas e contactos de pessoas singulares
# que não sejam já geralmente conhecidos. Esta é a aplicação no ponto de leitura.
CONTACTO = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "telefone": re.compile(r"\+\d[\d ()‑-]{7,}\d"),
    "morada": re.compile(r"\b(?:Rua|Avenida|Av\.|Travessa|Largo|Praceta|Estrada)\s+[A-Z]"),
}


def sem_contactos(registo, onde):
    """Drop any field of a person-level record that looks like a contact detail, and say so.

    Returns (record, [what was dropped]). The dropped list is counted on the method page: a
    refusal nobody can see happening is indistinguishable from a refusal that never ran."""
    limpo, caidos = {}, []
    for k, v in registo.items():
        if isinstance(v, str):
            achou = next((kind for kind, pat in CONTACTO.items() if pat.search(v)), None)
            if achou:
                caidos.append({"onde": onde, "campo": k, "especie": achou})
                continue
        limpo[k] = v
    return limpo, caidos


def tem_acentos(s):
    """True if the string carries at least one non-ASCII letter that is a Latin accented form.

    Used by the accent gate the other way round: this site asserts accents are PRESENT, which is
    the inverse of the corpus rule the method came from (brief §6)."""
    return any(unicodedata.combining(c) or ord(c) > 127 for c in unicodedata.normalize("NFD", s))


# ------------------------------------------------------------------- captura ---
def buscar(url, destino, texto=False):
    destino.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["curl", "-sL", "-A", UA, "-o", str(destino), "-w", "%{http_code}", "--max-time", "40", url],
        capture_output=True, text=True)
    return r.stdout.strip() or "000"


def capturar(data):
    """One dated snapshot: every target in fontes.py, plus a page per listed person."""
    out = CONGELADAS / data
    out.mkdir(parents=True, exist_ok=True)
    codigos = {}
    for alvo in fontes.alvos():
        ext = "" if alvo["texto"] else ".snapshot"
        sub = {"evento": "", "registo": "registo/", "abertas": "abertas/", "imprensa": "imprensa/"}[alvo["grupo"]]
        rel = f"{sub}{alvo['id']}"
        codigos[rel] = buscar(alvo["url"], out / f"{rel}{ext}")
        print(f"  {codigos[rel]}  {data}/{rel}{ext}")
        time.sleep(0.2)

    # every person the frozen speakers page lists gets their own page frozen too
    for p in pessoas_em(out):
        if not p.get("pagina"):
            continue
        destino = out / "oradores" / f"{p['id']}.snapshot"
        c = buscar(p["pagina"], destino)
        print(f"  {c}  {data}/oradores/{p['id']}.snapshot")
        time.sleep(0.25)

    # the sources that did not resolve last time are attempted again, every run
    tentadas = {}
    for cid, e in fontes.TENTADAS.items():
        destino = out / "tentadas" / f"{cid}.snapshot"
        tentadas[cid] = buscar(e["url"], destino)
        print(f"  {tentadas[cid]}  {data}/tentadas/{cid}.snapshot  (re-tentativa)")
    return codigos, tentadas


# ------------------------------------------------------------------- pessoas ---
def pessoas_em(cap):
    """One node per speaker card on the event's own frozen speakers page.

    Keyed on the card's own `id`, which the event site already uses as that person's URL slug —
    our identifier IS theirs, so nobody has to guess at a join.

    The biography paragraph on the card is NOT read here and is never written anywhere."""
    f = cap / "oradores.snapshot"
    if not f.exists():
        return []
    s = recuo_estatico(f)
    corte = s.find("Confirmed speakers")
    corpo = s[corte:] if corte != -1 else s
    out, caidos = [], []
    for slug, cartao in re.findall(r'<li id="([^"]+)"[^>]*>(.*?)</li>', corpo, re.S):
        nome = re.search(r"<h3[^>]*>(.*?)</h3>", cartao, re.S)
        ps = re.findall(r"<p[^>]*>(.*?)</p>", cartao, re.S)
        pagina = re.search(r'<a href="(/speakers/[^"]+)"', cartao)
        li = re.search(r'href="(https://[^"]*linkedin\.com[^"]*)"', cartao)
        registo = {
            "id": slug,
            "nome": sem_tags(nome.group(1)) if nome else None,
            "papel": sem_tags(ps[0]) if len(ps) > 0 else None,
            "organizacao": sem_tags(ps[1]) if len(ps) > 1 else None,
            "pagina": fontes.EVENTO["host"] + pagina.group(1) if pagina else None,
            "linkedin": li.group(1) if li else None,
        }
        registo, c = sem_contactos(registo, f"orador:{slug}")
        caidos += c
        out.append(registo)
    return out


def org_id(nome):
    """A slug for an organisation name. Accents are folded for the IDENTIFIER only — an id is a
    key, not a name — and the name itself is stored untouched, which is what the accent gate
    checks. Folding the name would be the exact failure the brief's §6 warns about."""
    base = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "sem-nome"


PLACEHOLDERS = {"independent", "independente", "self-employed", "freelance", "n/a", "-", "none", ""}


def construir_orgs(pessoas):
    """Organisations are DERIVED from the speaker cards, never typed by hand (brief §13).

    The event's field is free text, so `Independent` arrives looking like an organisation and is
    not one. It is kept, flagged and counted separately: inventing a tidier value would put a fact
    in the graph that no source supports."""
    por = {}
    for p in pessoas:
        if not p.get("organizacao"):
            continue
        oid = org_id(p["organizacao"])
        por.setdefault(oid, {"id": oid, "nome": p["organizacao"], "pessoas": [], "marcador": False})
        por[oid]["pessoas"].append(p["id"])
    for o in por.values():
        o["marcador"] = o["nome"].strip().lower() in PLACEHOLDERS
    return sorted(por.values(), key=lambda o: (o["marcador"], -len(o["pessoas"]), o["nome"].lower()))


# -------------------------------------------------------------------- temas ---
def bloco_bio(f):
    """The prose of a person's own page — returned ONLY to be matched against by the lexicon, and
    never written to any file. The event's Topics list, the LinkedIn line and the boilerplate are
    excluded so the formula runs over what was written about that person and nothing else."""
    s = f.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<h2>Bio</h2>(.*?)(?:<h2>Topics</h2>|<p><a href=\"https://www\.linkedin|<h2>About Startup Summit</h2>)", s, re.S)
    if not m:
        return ""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", m.group(1))).replace("\\n", " ").split())


def bloco_temas(f):
    """The event's own Topics list for this person, each item verbatim. Their vocabulary, not ours."""
    s = f.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<h2>Topics</h2>\s*<ul>(.*?)</ul>", s, re.S)
    if not m:
        return []
    return [html.unescape(t).strip() for t in re.findall(r"<li>(.*?)</li>", m.group(1), re.S)]


def ler_temas(cap, pessoas, lexico):
    linhas, pessoa_temas, pessoa_etiquetas = [], [], []
    for p in pessoas:
        f = cap / "oradores" / f"{p['id']}.snapshot"
        if not f.exists():
            linhas.append({"id": p["id"], "fonte": None, "temas": [], "etiquetas": [], "bio_chars": 0,
                           "nota": "sem cópia congelada da página desta pessoa"})
            continue
        bio = bloco_bio(f)
        temas = bloco_temas(f)
        etiquetas = []
        for e in lexico["entradas"]:
            m = re.search(e["padrao"], bio, re.I)
            if m:
                etiquetas.append({"etiqueta": e["id"], "tipo": e["tipo"], "correspondeu": m.group(0)[:40]})
        fid = f"{cap.name}/oradores/{p['id']}"
        linhas.append({"id": p["id"], "fonte": fid, "temas": temas, "etiquetas": etiquetas,
                       "bio_chars": len(bio)})
        pessoa_temas += [{"pessoa": p["id"], "tema": t, "fonte": fid} for t in temas]
        pessoa_etiquetas += [{"pessoa": p["id"], **e, "fonte": fid} for e in etiquetas]
    return linhas, pessoa_temas, pessoa_etiquetas


# ------------------------------------------------------------------- sessões ---
def sessoes_em(cap):
    """The programme, read from the frozen agenda rather than transcribed by hand.

    A transcription is a claim (CLAUDE.md, Language), and the sibling site checks its hand-typed
    programme against the bytes in a gate. Reading it directly removes the class of error instead
    of checking for it: a title here cannot disagree with the agenda, because it IS the agenda's
    bytes. Titles stay verbatim, in whatever language the event used."""
    f = cap / "agenda.snapshot"
    if not f.exists():
        return [], []
    corpo = recuo_estatico(f)
    sessoes, palcos = [], {}

    # The fallback's grammar, read off the bytes rather than assumed. Each day is an <h2> heading
    # followed by a <ul> of rows, and a row is one of:
    #
    #   09:00 — Doors Open · Registration · Expo
    #   09:30 — Opening Keynote: Welcome to Startup Summit 2026 (Unicorn Stage)
    #   11:45–12:15 · Unicorn Stage — <a …><strong>AI or Die</strong></a> (Panel)
    #   Evening — Founder Social
    #
    # so the em dash separates WHEN (and sometimes where) from WHAT. Where the row links to the
    # session's own page, the <strong> inside that link is the event's own title for it and is
    # taken verbatim in preference to anything parsed out of the surrounding prose.
    PALCOS = ("Unicorn Stage", "Impact Stage", "Main Stage", "Startup Stage", "Workshop Rooms")
    for cab, lista in re.findall(r"<h2[^>]*>(.*?)</h2>(.*?)(?=<h2|\Z)", corpo, re.S):
        dia = sem_tags(cab)
        for li in re.findall(r"<li[^>]*>(.*?)</li>", lista, re.S):
            ligacao = re.search(r'<a href="(/agenda/[^"]+)"[^>]*>\s*<strong>(.*?)</strong>', li, re.S)
            texto = sem_tags(li)
            partes = re.split(r"\s+[—–]\s+", texto, maxsplit=1)
            if len(partes) != 2:
                continue
            quando, resto = partes[0].strip(), partes[1].strip()

            palco = next((p for p in PALCOS if p in quando), None)
            formato = None
            if ligacao:
                # the event's own title for the session, verbatim
                titulo = html.unescape(sem_tags(ligacao.group(2))).strip()
                url = fontes.EVENTO["host"] + ligacao.group(1)
                fm = re.search(r"\(([^)]{3,20})\)\s*$", resto)
                formato = fm.group(1) if fm else None
            else:
                url = None
                titulo = resto
                # a trailing parenthesis is either the stage or the session's format, never both
                tm = re.search(r"^(.*?)\s*\(([^)]+)\)\s*$", titulo)
                if tm:
                    dentro = tm.group(2).strip()
                    if dentro in PALCOS:
                        palco, titulo = dentro, tm.group(1).strip()
                    elif len(dentro) <= 20:
                        formato, titulo = dentro, tm.group(1).strip()
                # rows like "19:00 — Welcome Drinks at Beato Innovation District. Music, …" carry
                # the organiser's own descriptive copy after the title. That prose is theirs, not
                # a fact about the world, so the title is cut at the first sentence break and the
                # rest is left in the frozen bytes where it belongs (CLAUDE.md rule 3).
                titulo = re.split(r"(?<=[a-z])\.\s|\s+at\s+Beato\b", titulo)[0].strip(" .·")

            if not titulo or len(titulo) > 140:
                continue
            if palco:
                palcos[org_id(palco)] = palco
            hm = re.match(r"(\d{1,2}:\d{2})(?:\s*[–—-]\s*(\d{1,2}:\d{2}))?", quando)
            sessoes.append({
                "id": org_id(titulo)[:60], "titulo": titulo,
                "inicio": hm.group(1) if hm else None,
                "fim": hm.group(2) if hm else None,
                "quando": quando if not hm else None,
                "dia": dia, "palco": org_id(palco) if palco else None,
                "formato": formato, "url": url,
            })
    vistas, unicas = set(), []
    for s_ in sessoes:
        chave = (s_["titulo"], s_["dia"])
        if chave in vistas:
            continue
        vistas.add(chave)
        unicas.append(s_)
    return unicas, [{"id": k, "nome": v} for k, v in sorted(palcos.items())]


def nomes_de_palco(cap):
    """The event names its stages two ways on two of its own pages. Recorded as an observation
    about published artefacts, never as an allegation about anybody."""
    conhecidos = ["Unicorn Stage", "Impact Stage", "Main Stage", "Startup Stage", "Workshop Rooms"]
    out = {}
    for f in sorted(cap.glob("*.snapshot")):
        achados = sorted({k for k in conhecidos if k in texto_de(f)})
        if achados:
            out[f.stem] = achados
    return out


def contagem_declarada(cap):
    f = cap / "oradores.snapshot"
    if not f.exists():
        return None
    m = re.search(r"(\d+)\s+confirmed speakers are listed below", texto_de(f))
    return int(m.group(1)) if m else None


# -------------------------------------------------------------------- build ---
def escrever(nome, obj):
    DADOS.mkdir(parents=True, exist_ok=True)
    (DADOS / nome).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def registar(caps):
    """The register: every frozen file, with its SHA-256, bytes and retrieval time.

    A body that is a 404 or an error page is excluded here and the reason recorded, so it can
    never be cited. Everything else enters as `primaria` — in this newsroom every source is a
    byte copy we hold, so anything else would be a bug in this function."""
    por_alvo = {a["id"]: a for a in fontes.alvos()}

    # As fontes que uma entrega de investigação nomeia são congeladas por `build/entregas.py` para
    # `<captura>/entregas/<id-da-entrega>/`. Entram no registo como qualquer outra fonte — são
    # bytes que temos em mãos, com hash — mas o grupo diz de onde vieram, e o publicador vem da
    # própria entrega e não de `fontes.py`, que não as conhece. O que NÃO muda por estarem aqui: a
    # afirmação que assenta numa delas continua a ser uma pista até o editor a aprovar.
    por_entrega = {}
    ent_dir = ROOT / "redacao" / "entregas"
    for f in sorted(ent_dir.rglob("*.json")) if ent_dir.exists() else []:
        try:
            entrega = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        did = entrega.get("delivery", {}).get("id")
        for s in entrega.get("sources", []):
            por_entrega[f"{did}/{s['id']}"] = {
                "url": s["url"], "publicador": s["publisher"], "lingua": s.get("language", "pt")}

    fontes_reg, excluidas = [], []
    for cap in caps:
        for f in sorted(cap.rglob("*")):
            if not f.is_file() or f.parent.name == "tentadas":
                continue
            rel = f.relative_to(cap).as_posix()
            base = re.sub(r"\.(snapshot|pdf)$", "", rel)
            grupo = ("oradores" if rel.startswith("oradores/") else
                     "registo" if rel.startswith("registo/") else
                     "abertas" if rel.startswith("abertas/") else
                     "imprensa" if rel.startswith("imprensa/") else
                     "entregas" if rel.startswith("entregas/") else "evento")
            if grupo == "entregas":
                alvo = por_entrega.get(base[len("entregas/"):], {})
            else:
                alvo = por_alvo.get(base.split("/")[-1], {})
            corpo = f.read_text(encoding="utf-8", errors="replace")[:4000]
            erro = next((p for p in ("Ocorreu algo de errado", "404 Not Found", "Page not found")
                         if p in corpo), None)
            if erro or f.stat().st_size == 0:
                excluidas.append({"id": f"{cap.name}/{base}", "url": alvo.get("url"),
                                  "porque": f"o corpo devolvido é um erro ({erro or '0 bytes'}) — "
                                            f"não entra no registo e não pode ser citado"})
                continue
            fontes_reg.append({
                "id": f"{cap.name}/{base}", "pagina": base, "captura": cap.name, "grupo": grupo,
                "url": (f"{fontes.EVENTO['host']}/speakers/{Path(base).stem}"
                        if grupo == "oradores" else alvo.get("url")),
                "congelada": f"fontes/congeladas/{cap.name}/{rel}",
                "sha256": sha(f), "bytes": f.stat().st_size, "obtida": mtime(f),
                "publicador": (fontes.EVENTO["publicador"] if grupo == "oradores"
                               else alvo.get("publicador")),
                "lingua": alvo.get("lingua", "en"),
                "estado": "primaria",
            })
    return fontes_reg, excluidas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="take a new dated snapshot first")
    ap.add_argument("--date", default=time.strftime("%Y-%m-%d"))
    args = ap.parse_args()

    if args.fetch:
        print(f"a capturar {args.date}…")
        capturar(args.date)

    caps = capturas()
    if not caps:
        raise SystemExit("não há capturas em fontes/congeladas/<data>/ — corra com --fetch")
    ultima = caps[-1]
    hoje = ultima.name

    fontes_reg, excluidas = registar(caps)
    pessoas = pessoas_em(ultima)
    orgs = construir_orgs(pessoas)
    sessoes, palcos = sessoes_em(ultima)

    # --- o que mexeu entre capturas ------------------------------------------
    # Numa lista publicada antes de as portas abrirem, a mudança É a notícia. A razão de uma
    # saída fica em branco: retirada, conflito de agenda, registo duplicado e erro de edição são
    # indistinguíveis de fora (CLAUDE.md regra 5).
    mudancas = []
    for a, b in zip(caps, caps[1:]):
        pa = {p["id"]: p for p in pessoas_em(a)}
        pb = {p["id"]: p for p in pessoas_em(b)}
        if not pa or not pb:
            continue
        alterados = []
        for i in pa.keys() & pb.keys():
            for campo in ("papel", "organizacao", "nome"):
                if pa[i].get(campo) != pb[i].get(campo):
                    alterados.append({"id": i, "nome": pb[i]["nome"], "campo": campo,
                                      "era": pa[i].get(campo), "agora": pb[i].get(campo)})
        mudancas.append({
            "de": a.name, "para": b.name,
            "sha256_de": sha(a / "oradores.snapshot"), "sha256_para": sha(b / "oradores.snapshot"),
            "contagem_de": len(pa), "contagem_para": len(pb),
            "declarada_de": contagem_declarada(a), "declarada_para": contagem_declarada(b),
            "entraram": sorted(({"id": pb[i]["id"], "nome": pb[i]["nome"],
                                 "organizacao": pb[i].get("organizacao")}
                                for i in pb.keys() - pa.keys()), key=lambda x: x["id"]),
            "sairam": sorted(({"id": pa[i]["id"], "nome": pa[i]["nome"],
                               "organizacao": pa[i].get("organizacao")}
                              for i in pa.keys() - pb.keys()), key=lambda x: x["id"]),
            "alterados": sorted(alterados, key=lambda x: x["id"]),
            "razao_conhecida": False,
            "sobre_saidas": ("Um nome presente numa captura e ausente da seguinte é registado como "
                             "exatamente isso. Retirada, conflito de agenda, registo duplicado e erro "
                             "de edição são indistinguíveis de fora, por isso publica-se a diferença "
                             "e deixa-se a razão em branco em vez de a adivinhar."),
        })

    escrever("registo.json", {
        "id": "pt-registo", "versao": "0.1.0", "atualizado": hoje,
        "nota": ("Todas as páginas obtidas, congeladas byte a byte neste repositório e hasheadas. "
                 "Uma afirmação deste site anda para trás até um SHA-256 desta lista. As cópias "
                 "congeladas têm extensão .snapshot: são prova, não são páginas deste site, e não "
                 "são servidas nem indexadas como tal."),
        "capturas": [c.name for c in caps], "contagem": len(fontes_reg), "fontes": fontes_reg,
    })
    escrever("excluidas.json", {
        "id": "pt-excluidas", "versao": "0.1.0", "atualizado": hoje,
        "nota": ("Fontes que foram tentadas e não resolveram. Não são descartadas em silêncio: uma "
                 "fonte que esta redação não consegue alcançar é um facto sobre o registo público, "
                 "e o tamanho do que não se consegue ver pertence à página (§10 do resumo). São "
                 "re-tentadas em cada execução."),
        "contagem": len(excluidas), "itens": excluidas,
        "por_resolver": [{"id": k, **v} for k, v in fontes.TENTADAS.items()],
    })
    escrever("pessoas.json", {
        "id": "pt-pessoas", "versao": "0.1.0", "atualizado": hoje, "captura": hoje,
        "nota": ("Oradores tal como a página do próprio evento os lista, extraídos de uma cópia "
                 "congelada e hasheada e não da rede. Nome, papel, organização e ligações — as "
                 "biografias são o texto de quem as escreveu, são ligadas e nunca reproduzidas. "
                 "Nenhum contacto de pessoa singular entra neste ficheiro: a recusa corre no ponto "
                 "de leitura (build/extract.py, sem_contactos), não no template."),
        "contagem": len(pessoas), "com_linkedin": sum(1 for p in pessoas if p.get("linkedin")),
        "pessoas": pessoas,
    })
    escrever("organizacoes.json", {
        "id": "pt-organizacoes", "versao": "0.1.0", "atualizado": hoje,
        "nota": ("Derivadas do campo de organização de cada cartão de orador, nunca escritas à mão. "
                 "O campo é texto livre na fonte, por isso valores de marcador como «Independent» "
                 "chegam com o aspeto de organizações. São assinalados, não removidos: inventar um "
                 "valor mais arrumado poria no grafo um facto que nenhuma fonte sustenta."),
        "contagem": len(orgs), "marcadores": sum(1 for o in orgs if o["marcador"]),
        "com_varias_pessoas": sum(1 for o in orgs if len(o["pessoas"]) > 1), "organizacoes": orgs,
    })
    escrever("sessoes.json", {
        "id": "pt-sessoes", "versao": "0.1.0", "atualizado": hoje, "fonte": f"{hoje}/agenda",
        "nota": ("O programa, lido da agenda congelada em vez de transcrito à mão. Uma transcrição "
                 "é uma afirmação; ler os bytes diretamente elimina a classe de erro em vez de a "
                 "verificar. Títulos verbatim, na língua em que o evento os publicou."),
        "contagem": len(sessoes), "sessoes": sessoes, "palcos": palcos,
    })
    lexico = json.loads((DADOS / "lexico.json").read_text(encoding="utf-8"))
    linhas, pessoa_temas, pessoa_etiquetas = ler_temas(ultima, pessoas, lexico)
    indice = {}
    for pt in pessoa_temas:
        indice.setdefault(pt["tema"], []).append(pt["pessoa"])
    escrever("temas.json", {
        "id": "pt-temas", "versao": "0.1.0", "atualizado": hoje, "captura": hoje,
        "nota": ("Duas coisas lidas da página de cada pessoa no site do evento, congelada e hasheada "
                 "como qualquer outra fonte. TEMAS é a lista de tópicos do próprio evento para essa "
                 "pessoa, verbatim. ETIQUETAS são derivadas: cada uma é uma entrada do léxico "
                 "publicado (dados/lexico.json, uma expressão regular) que correspondeu ao texto da "
                 "página, e leva consigo as palavras que correspondeu e mais nada. Uma etiqueta diz "
                 "que a página contém aquelas palavras; não é uma caracterização da pessoa."),
        "lexico": {"id": lexico["id"], "versao": lexico["versao"], "entradas": len(lexico["entradas"])},
        "contagem": len(linhas), "com_temas": sum(1 for r in linhas if r["temas"]),
        "com_etiquetas": sum(1 for r in linhas if r["etiquetas"]),
        "temas_distintos": len(indice), "etiquetas_distintas": len({e["etiqueta"] for e in pessoa_etiquetas}),
        "pessoas": linhas, "pessoa_temas": pessoa_temas, "pessoa_etiquetas": pessoa_etiquetas,
        "indice_temas": dict(sorted(indice.items(), key=lambda kv: (-len(kv[1]), kv[0]))),
    })
    escrever("mudancas.json", {
        "id": "pt-mudancas", "versao": "0.1.0", "atualizado": hoje,
        "nota": ("O que mexeu entre capturas congeladas das mesmas páginas. Nesta matéria a mudança "
                 "é a notícia: uma lista publicada antes de as portas abrirem é um objeto em "
                 "movimento, e a única forma honesta de relatar movimento é ter as duas cópias e os "
                 "dois hashes."),
        "mudancas": mudancas,
    })
    escrever("verificacoes-fonte.json", {
        "id": "pt-verificacoes-fonte", "versao": "0.1.0", "atualizado": hoje,
        "nota": ("O que a releitura das cópias congeladas estabelece. Observações sobre artefactos "
                 "publicados, não alegações sobre quem quer que seja."),
        "oradores": {
            "cartoes": len(pessoas), "declarado_na_pagina": contagem_declarada(ultima),
            "concordam": len(pessoas) == contagem_declarada(ultima),
        },
        "nomes_de_palco": nomes_de_palco(ultima),
        "legibilidade": legibilidade(ultima),
    })
    escrever("fontes-alvo.json", {
        "id": "pt-fontes-alvo", "versao": "0.1.0", "atualizado": hoje,
        "nota": ("A lista que a execução diária volta a buscar. Pública em vez de enterrada no "
                 "código: um leitor pode ver o que esta redação olha e o que não olha."),
        "contagem": len(fontes.alvos()), "alvos": fontes.alvos(),
        "por_resolver": [{"id": k, **v} for k, v in fontes.TENTADAS.items()],
    })

    print(f"extract: {len(caps)} captura(s), {len(fontes_reg)} ficheiros congelados, "
          f"{len(excluidas)} excluídos, {len(pessoas)} pessoas, {len(orgs)} organizações, "
          f"{len(sessoes)} sessões")
    for c in mudancas:
        print(f"  {c['de']} -> {c['para']}: {c['contagem_de']} -> {c['contagem_para']} oradores "
              f"(+{len(c['entraram'])} / -{len(c['sairam'])} / {len(c['alterados'])} editados)")


def legibilidade(cap):
    """Whether each frozen page of the national record returned a body a machine can read.

    This is the brief's first article (§11) as a measurement rather than an assertion: a page
    fetched over HTTP that returns almost no text is a page that renders through script, and that
    is a checkable, dated, hashed fact about the public record rather than an opinion about it."""
    out = {}
    for f in sorted((cap / "registo").glob("*.snapshot")) if (cap / "registo").exists() else []:
        t = texto_de(f)
        out[f.stem] = {
            "bytes": f.stat().st_size, "caracteres_visiveis": len(t),
            "legivel_por_maquina": len(t) > 1200,
            "nota": ("Uma página que devolve bytes mas quase nenhum texto visível a um leitor "
                     "automático renderiza por script. Registado como medição, com data e hash."),
        }
    return out


if __name__ == "__main__":
    main()

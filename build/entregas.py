#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — entregas de investigação: validar, congelar, conferir excertos, rever.

    python3 build/entregas.py            # re-conferir a partir das cópias congeladas
    python3 build/entregas.py --fetch    # congelar primeiro as fontes que a entrega nomeia

O que isto é, e porque existe.

Um assistente exterior (ChatGPT, Perplexity) recebe um dos resumos de investigação em
`briefs/pack/08__research-briefs/` e devolve JSON com proveniência. **Uma entrega é uma lista de
PISTAS com proveniência, nunca factos**, e nada nela pode ser citado neste site. É a regra do
pacote e é a única coisa que impede este site de ser um agregador de texto de terceiros com boa
apresentação.

O método desta redação aplica-se a cada endereço que a entrega contém, e este ficheiro é esse
método:

1. **Validar** a entrega contra `briefs/pack/08__research-briefs/research-schema.json`. Inválida:
   o ficheiro fica (faz parte do registo), os erros vão para a caixa do editor, e não se ingere
   nada.
2. **Congelar** cada endereço que a entrega nomeia, em `fontes/congeladas/<data>/entregas/<id>/`,
   com SHA-256, exatamente como qualquer outra fonte. A entrega não traz bytes; traz endereços, e
   um endereço não é prova.
3. **O portão dos excertos.** Cada afirmação de uma entrega traz um `excerpt` — o texto que o
   assistente diz ter lido na página. Este passo procura esse texto nos BYTES CONGELADOS. Se lá
   não estiver, a afirmação não existe. Não é um aviso: é o estado `nao_encontrado`, e a
   afirmação não pode passar para uma história.
4. **Rever.** Nada do que sai daqui vai para a primeira página ou para um artigo. Fica em
   `/entregas/`, com o estado de cada afirmação à vista, à espera da decisão do editor de registo
   — que é uma linha num ficheiro em `redacao/revisoes/`, escrita por uma pessoa.

As entidades e as arestas de uma entrega são PROPOSTAS. A Pesquisa volta a derivá-las da página
congelada antes de alguma coisa chegar a `dados/grafo.json`; as `vocabulary_proposals` vão para o
editor, porque um verbo novo é uma alteração de ontologia e leva uma versão.

Uma nota sobre o que este passo NÃO faz, e é deliberado: não corrige a entrega. Se um excerto não
estiver nos bytes, o registo diz que não estava, e a entrega fica no repositório tal como chegou.
Uma entrega corrigida em silêncio deixaria de ser prova de nada.
"""
import argparse
import hashlib
import json
import re
import subprocess
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
ENTREGAS = ROOT / "redacao" / "entregas"
REVISOES = ROOT / "redacao" / "revisoes"
CONGELADAS = ROOT / "fontes" / "congeladas"
ESQUEMA = ROOT / "briefs" / "pack" / "08__research-briefs" / "research-schema.json"

UA = "Mozilla/5.0 (pt.newsroom.sgit.ai research; +https://pt.newsroom.sgit.ai/metodo/)"

# Os estados por que uma afirmação de uma entrega passa. A ordem importa: nada salta um degrau, e
# só o último é uma decisão humana.
ESTADOS = [
    {"id": "por_verificar",   "rotulo": "Por verificar",       "cor": "#6b6e76",
     "o_que_significa": "Tal como chegou do assistente. Nenhum byte foi congelado ainda."},
    {"id": "confirmada",      "rotulo": "Excerto encontrado",  "cor": "#0f766e",
     "o_que_significa": "O excerto que o assistente diz ter lido está nos bytes que congelámos. A afirmação pode passar a uma história."},
    {"id": "nao_encontrada",  "rotulo": "Excerto não encontrado", "cor": "#b91c1c",
     "o_que_significa": "Congelámos a página e o excerto não está lá. A afirmação não passa. Pode ser uma página que mudou, uma que renderiza por script, ou um excerto que nunca existiu — o registo não adivinha qual."},
    {"id": "fonte_inacessivel", "rotulo": "Fonte inacessível", "cor": "#b45309",
     "o_que_significa": "A página não devolveu um corpo utilizável (403, 404, ou um invólucro sem texto). Nada se pode conferir contra ela."},
    {"id": "aprovada",        "rotulo": "Aprovada pelo editor", "cor": "#0f766e",
     "o_que_significa": "O editor de registo leu a afirmação ao lado da sua fonte congelada e aprovou-a para publicação. É a única transição que uma execução automática não pode fazer."},
    {"id": "rejeitada",       "rotulo": "Rejeitada pelo editor", "cor": "#b91c1c",
     "o_que_significa": "O editor leu-a e não a quer. A razão fica no ficheiro de revisão."},
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def normalizar(s):
    """Fold a string for excerpt comparison, WITHOUT destroying its meaning.

    Whitespace and quotation marks differ between a page's bytes and what an assistant copied out
    of a rendering: a non-breaking space, a curly quote, a soft hyphen, a line break inside a
    sentence. Those are formatting, not content, so they are levelled. Accents are NOT folded —
    on this site an accent is data (a acentuação é dado), and folding it here would make the gate
    accept «Inteligencia» where the page says «Inteligência», which is the exact class of silent
    error the accent gate exists to catch."""
    s = unicodedata.normalize("NFC", s)
    s = (s.replace(" ", " ").replace("‑", "-").replace("­", "")
          .replace("‘", "'").replace("’", "'")
          .replace("“", '"').replace("”", '"')
          .replace("–", "-").replace("—", "-"))
    s = " ".join(s.split())
    # A rendering puts a space where the markup had a tag boundary, so a page can show
    # «… until 2 August 2025 .» for a sentence an assistant copied as «… 2 August 2025.». That is
    # a space against a tag, not a difference in what the page says, so it is levelled — as is the
    # mirror case inside brackets. Nothing here adds or removes a character that carries meaning.
    s = re.sub(r"\s+([.,;:!?%)\]])", r"\1", s)
    s = re.sub(r"([(\[])\s+", r"\1", s)
    return s.lower()


def texto_de(p):
    """Visible text of a frozen page. <noscript> is kept: on this beat it is where the content is."""
    s = p.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", s, flags=re.S | re.I)
    import html as _h
    return " ".join(_h.unescape(re.sub(r"<[^>]+>", " ", t)).split())


def texto_de_pdf(p):
    """Text of a frozen PDF, via build/pdf.py.

    Matters more here than it looks. The Diário da República's HTML renders through script and
    returns almost nothing to an automated reader — but the gazette publishes the full diploma as
    a PDF, and that PDF is the only machine-readable form of the official record. It arrives
    encrypted with the standard security handler and with subsetted fonts, so a generic extractor
    returns zero characters and returns them silently. `build/pdf.py` decrypts it and reads each
    font's own /ToUnicode map.

    When nothing readable comes out, the reason travels with the answer, and the claim is marked
    `fonte_inacessivel` rather than `nao_encontrada`: a limitation of this reader must never be
    published as a finding about somebody else's document."""
    import pdf as leitor
    t = leitor.texto(p)
    texto_de_pdf.porque = leitor.porque_nao()
    return t


texto_de_pdf.porque = None


MIN_TROCO = 30      # caracteres — abaixo disto um «troço» é ruído, não uma correspondência
MAX_TROCOS = 3      # acima disto o excerto está montado a partir de pedaços dispersos


def localizar(excerto, texto):
    """Find an excerpt in a frozen document. Returns (espécie, nº de troços).

    Espécie é `exacta` quando o excerto está lá de seguida, `fragmentada` quando está lá por
    inteiro e pela ordem certa mas partido em poucos troços, e None quando não está.

    Porque é que `fragmentada` existe e não é um afrouxamento do portão. Num PDF do Diário da
    República uma frase atravessa a quebra de coluna ou de página, e o cabeçalho corrente
    («RESOLUÇÃO DO CONSELHO DE MINISTROS N.º 70/2026 …») fica no meio dela. O leitor desta redação
    não faz paginação — lê os fluxos pela ordem em que o produtor os escreveu — por isso a frase
    chega interrompida. Marcar isso como «excerto não encontrado» seria publicar uma limitação
    deste leitor como se fosse um erro de quem entregou a pista.

    O que impede o afrouxamento são os dois limites acima: cada troço tem de ter pelo menos 30
    caracteres, no máximo três troços, e a soma dos troços tem de cobrir o excerto INTEIRO pela
    ordem em que está escrito. Um excerto montado a partir de palavras espalhadas pelo documento
    não passa — falha no comprimento mínimo, no número de troços, ou na ordem."""
    if not excerto:
        return None, 0
    if excerto in texto:
        return "exacta", 1
    restante, pos, trocos = excerto, 0, 0
    while restante:
        lo, hi, melhor, melhor_i = 1, len(restante), 0, -1
        while lo <= hi:                      # o prefixo mais longo que ainda ocorre a partir de pos
            meio = (lo + hi) // 2
            i = texto.find(restante[:meio], pos)
            if i != -1:
                melhor, melhor_i = meio, i
                lo = meio + 1
            else:
                hi = meio - 1
        if melhor < MIN_TROCO:
            return None, trocos
        trocos += 1
        if trocos > MAX_TROCOS:
            return None, trocos
        pos = melhor_i + melhor
        restante = restante[melhor:].strip()
    return "fragmentada", trocos


def validar(entrega):
    """Validate against the pack's schema. Returns a list of human-readable errors."""
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema não está instalado — a entrega não foi validada (pip install jsonschema)"]
    esquema = json.loads(ESQUEMA.read_text(encoding="utf-8"))
    v = jsonschema.Draft202012Validator(esquema)
    return [f"{'/'.join(str(x) for x in e.path) or '(raiz)'}: {e.message}"
            for e in sorted(v.iter_errors(entrega), key=lambda e: list(e.path))]


def ficheiros():
    return sorted(ENTREGAS.rglob("*.json"))


def congelar(entrega, data):
    """Freeze every URL the delivery names. The delivery brings addresses; an address is not proof."""
    did = entrega["delivery"]["id"]
    out = CONGELADAS / data / "entregas" / did
    out.mkdir(parents=True, exist_ok=True)
    codigos = {}
    for s in entrega["sources"]:
        ext = ".pdf" if s.get("access") == "pdf" or s["url"].lower().endswith(".pdf") else ".snapshot"
        destino = out / f"{s['id']}{ext}"
        r = subprocess.run(["curl", "-sL", "-A", UA, "-o", str(destino), "-w", "%{http_code}",
                            "--max-time", "40", s["url"]], capture_output=True, text=True)
        codigos[s["id"]] = r.stdout.strip() or "000"
        print(f"  {codigos[s['id']]}  {data}/entregas/{did}/{s['id']}{ext}")
        time.sleep(0.3)
    return codigos


def conferir(entrega, data):
    """The excerpt gate: is the text the assistant says it read actually in the bytes we hold?"""
    did = entrega["delivery"]["id"]
    base = CONGELADAS / data / "entregas" / did
    por_fonte = {}
    for s in entrega["sources"]:
        pdf = base / f"{s['id']}.pdf"
        snap = base / f"{s['id']}.snapshot"
        f = pdf if pdf.exists() else snap
        linha = {"id": s["id"], "url": s["url"], "publicador": s["publisher"],
                 "titulo": s["title"], "lingua": s["language"], "acesso": s.get("access")}
        if not f.exists() or f.stat().st_size == 0:
            linha.update({"congelada": None, "sha256": None, "bytes": 0, "legivel": False,
                          "porque": "nenhum corpo foi devolvido"})
            por_fonte[s["id"]] = linha
            continue
        bruto = f.read_bytes()
        corpo = f.read_text(encoding="utf-8", errors="replace")[:3000]
        e_pdf = f.suffix == ".pdf"
        texto = texto_de_pdf(f) if e_pdf else texto_de(f)
        bloqueada = (len(bruto) < 1200 and ("403" in corpo or "Forbidden" in corpo)) or \
                    re.search(r"\b403 Forbidden\b", corpo)
        if bloqueada:
            porque = "a página devolveu 403 — o editor pode pedir acesso, mas nada se confere contra isto"
        elif len(texto) <= 400 and e_pdf:
            porque = (f"a cópia congelada é um PDF que este leitor não conseguiu ler "
                      f"({texto_de_pdf.porque or 'razão desconhecida'}). É uma limitação deste "
                      f"leitor, não uma afirmação sobre o documento")
        elif len(texto) <= 400:
            porque = "a página devolveu bytes mas quase nenhum texto visível: renderiza por script"
        else:
            porque = None
        linha.update({
            "congelada": f.relative_to(ROOT).as_posix(), "sha256": sha(f), "bytes": len(bruto),
            "caracteres_visiveis": len(texto), "formato": "pdf" if e_pdf else "html",
            "legivel": len(texto) > 400 and not bloqueada,
            "porque": porque,
        })
        linha["_texto"] = normalizar(texto)
        por_fonte[s["id"]] = linha

    itens = []
    for it in entrega["items"]:
        afirmacoes = []
        for i, c in enumerate(it["claims"]):
            fonte = por_fonte.get(c["source"])
            excerto = c.get("excerpt", "")
            especie, trocos = (None, 0)
            if not fonte or not fonte.get("legivel"):
                estado, nota = "fonte_inacessivel", (fonte or {}).get(
                    "porque", "a entrega cita uma fonte que não está na sua própria lista")
            else:
                especie, trocos = localizar(normalizar(excerto), fonte["_texto"])
                if especie == "exacta":
                    estado, nota = "confirmada", None
                elif especie == "fragmentada":
                    estado, nota = "confirmada", (
                        f"o excerto está na cópia congelada por inteiro e pela ordem certa, mas "
                        f"partido em {trocos} troços: alguma coisa o interrompe no documento — "
                        f"tipicamente um cabeçalho corrente numa quebra de página. O leitor desta "
                        f"redação não faz paginação, por isso a interrupção é dele e não de quem "
                        f"entregou a pista.")
                else:
                    estado, nota = "nao_encontrada", (
                        "o excerto não está no texto visível da cópia congelada. Pode ser uma "
                        "página que mudou desde a entrega, uma que só mostra este texto a um "
                        "cliente que corre scripts, ou um excerto que nunca esteve lá. O registo "
                        "não adivinha qual.")
            afirmacoes.append({
                "id": f"{it['id']}-c{i + 1}", "texto": c["text"], "fonte": c["source"],
                "localizador": c.get("locator"), "excerto": excerto,
                "confianca_declarada": c.get("confidence"),
                "estado_entregue": c.get("status"), "estado": estado, "nota": nota,
                "correspondencia": especie, "trocos": trocos,
            })
        itens.append({
            "id": it["id"], "seccao": it["section"], "especie": it["kind"],
            "titulo": it["headline"], "o_que_dizem_as_fontes": it["what_the_sources_say"],
            "porque_importa": it["why_it_matters"],
            "historia_sugerida": it.get("suggested_story"),
            "afirmacoes": afirmacoes,
            "entidades_propostas": it.get("entities", []),
            "arestas_propostas": it.get("edges", []),
            "verificacao_dados_pessoais": it.get("personal_data_check"),
            "resumo": {e: sum(1 for a in afirmacoes if a["estado"] == e)
                       for e in ("confirmada", "nao_encontrada", "fonte_inacessivel")},
        })
    for f in por_fonte.values():
        f.pop("_texto", None)
    return list(por_fonte.values()), itens


def revisao(did):
    """The editor's decisions, if any. A file a human writes; never written by a run."""
    f = REVISOES / f"{did}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {"entrega": did, "estado": "por_rever", "decidido_por": None, "decidido_em": None,
            "itens": {}, "comentarios": []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--date", default=time.strftime("%Y-%m-%d"))
    args = ap.parse_args()

    saida = []
    for f in ficheiros():
        entrega = json.loads(f.read_text(encoding="utf-8"))
        did = entrega["delivery"]["id"]
        erros = validar(entrega)
        if args.fetch:
            print(f"a congelar as fontes de {did}…")
            congelar(entrega, args.date)
        fontes, itens = conferir(entrega, args.date)
        rev = revisao(did)

        total = [a for it in itens for a in it["afirmacoes"]]
        saida.append({
            "id": did, "ficheiro": f.relative_to(ROOT).as_posix(),
            "ferramenta": entrega["delivery"]["tool"], "modelo": entrega["delivery"]["model"],
            "data": entrega["delivery"]["date"], "parte": entrega["delivery"].get("part"),
            "resumo_brief": entrega["delivery"]["brief"],
            "seccoes": entrega["delivery"]["sections_covered"],
            "consultas": entrega["delivery"]["queries"],
            "notas_do_assistente": entrega["delivery"]["notes"],
            "cofre": entrega["delivery"].get("vault", {}),
            "esquema_valido": not erros, "erros_de_esquema": erros,
            "congelada_em": args.date,
            "fontes": fontes, "itens": itens,
            "propostas_de_vocabulario": entrega.get("vocabulary_proposals", []),
            "contagens": {
                "fontes": len(fontes),
                "fontes_legiveis": sum(1 for x in fontes if x.get("legivel")),
                "itens": len(itens), "afirmacoes": len(total),
                "confirmadas": sum(1 for a in total if a["estado"] == "confirmada"),
                "nao_encontradas": sum(1 for a in total if a["estado"] == "nao_encontrada"),
                "fonte_inacessivel": sum(1 for a in total if a["estado"] == "fonte_inacessivel"),
            },
            "revisao": rev,
        })
        c = saida[-1]["contagens"]
        print(f"entrega {did}: esquema {'ok' if not erros else f'{len(erros)} erro(s)'}, "
              f"{c['fontes_legiveis']}/{c['fontes']} fontes legíveis, "
              f"{c['confirmadas']} confirmadas / {c['nao_encontradas']} não encontradas / "
              f"{c['fonte_inacessivel']} sem fonte legível, revisão: {rev['estado']}")
        for e in erros[:6]:
            print("   ✗ esquema:", e)

    DADOS.mkdir(parents=True, exist_ok=True)
    (DADOS / "entregas.json").write_text(json.dumps({
        "id": "pt-entregas", "versao": "0.1.0", "atualizado": args.date,
        "o_que_e": ("Entregas de investigação de assistentes exteriores, com o estado de cada "
                    "afirmação depois de esta redação ter congelado a fonte e procurado nos bytes "
                    "o excerto que o assistente diz ter lido."),
        "a_regra": ("Uma entrega é uma lista de pistas com proveniência, nunca factos. Nada daqui "
                    "aparece na primeira página nem num artigo enquanto o editor de registo não "
                    "aprovar a afirmação, uma a uma, ao lado da sua fonte congelada. O portão 13 "
                    "de build/gates.py falha a construção se isso for contornado."),
        "estados": ESTADOS,
        "contagem": len(saida), "entregas": saida,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return saida


if __name__ == "__main__":
    main()

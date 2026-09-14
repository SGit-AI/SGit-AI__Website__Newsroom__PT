#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — o grafo. Ontologia, taxonomia, nós, arestas, blocos, triplos.

    python3 build/graph.py     # escreve dados/ontologia.json, grafo.json, triplos.nt, manifesto.json

Adaptado de `portugal/build/graph.py` (newsroom.sgit.ai v0.3.9). Três regras vêm de lá sem
alteração, e a quarta é a razão de este ficheiro existir separadamente:

1. **Cada aresta é um verbo com um inverso distinto e nomeado.** Uma aresta simétrica seria o seu
   próprio inverso, o que a gramática proíbe, por isso não há `relacionado_com` e nunca haverá.
   Um caminho só vale a pena se SE LÊ: percorrido para a frente usa o verbo, para trás usa o
   inverso, e em qualquer dos sentidos é uma frase.
2. **A classificação é uma fórmula, não um rótulo.** Onde um nó leva uma classe que este ficheiro
   não leu de uma fonte, a fórmula é publicada ao lado e o valor diz «pelo título listado», para
   que ninguém confunda uma inferência com um facto.
3. **Cada nó nomeia a fonte congelada de onde veio.** Um nó sem `fonte` é um erro, e o portão
   trata-o como tal. Um nó sem caminho de volta aos bytes é um desenho.

4. **OS VERBOS SÃO PORTUGUESES, e o `en` é a anotação.** Esta é a inversão que o §6 do resumo
   manda fazer, e a única que não é cosmética. A quinta regra publicada do grafo diz: *se um
   caminho não se lê como uma frase na língua do leitor, as arestas estão erradas.* A língua do
   leitor deste site é o português, logo o teste de aceitação é um leitor português a ler um
   caminho em voz alta. Uma ontologia inglesa por trás de uma interface portuguesa falha esse
   teste enquanto parece acabada — é a forma mais provável de este site estar discretamente
   errado, porque nada nela parece avariado. Por isso a chave primária de cada verbo aqui é
   `verbo` em português e `en` é uma anotação que não é usada para nada a não ser a exportação.

E uma regra sobre acentos: o corpus de onde este método vem impõe ASCII puro, e o português não
é uma língua ASCII. Nada aqui normaliza um nome. Os identificadores são dobrados para ASCII
porque um identificador é uma chave e não um nome; os RÓTULOS ficam como a fonte os escreveu, e o
portão 9 assere que assim é.
"""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"


def load(n):
    return json.loads((DADOS / n).read_text(encoding="utf-8"))


def ident(nome):
    """A key, not a name. Accents are folded HERE and only here."""
    base = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "sem-nome"


# ----------------------------------------------------------------- ontologia ---
# As oito secções do resumo, no topo da taxonomia. São a espinha do site e a nav da página.
SECCOES = [
    {"id": "empresas",      "rotulo": "As empresas",     "en": "Companies"},
    {"id": "protagonistas", "rotulo": "Os protagonistas", "en": "People"},
    {"id": "instituicoes",  "rotulo": "As instituições",  "en": "Institutions"},
    {"id": "politicas",     "rotulo": "As políticas",     "en": "Policies"},
    {"id": "casos-de-uso",  "rotulo": "Os casos de uso",  "en": "Use cases"},
    {"id": "codigo-aberto", "rotulo": "O código aberto",  "en": "Open source"},
    {"id": "diaspora",      "rotulo": "A diáspora",       "en": "Diaspora"},
    {"id": "eventos",       "rotulo": "Os eventos",       "en": "Events"},
]

TIPOS = [
    {"id": "Evento",       "rotulo": "Evento",       "en": "Event",        "cor": "#0f766e", "seccao": "eventos",
     "definicao": "Um encontro datado e localizado que publica um programa e uma lista de quem fala."},
    {"id": "Sessao",       "rotulo": "Sessão",       "en": "Session",      "cor": "#115e59", "seccao": "eventos",
     "definicao": "Um item do programa publicado de um evento, com um dia, uma hora e normalmente um palco. Título verbatim, na língua em que o evento o publicou."},
    {"id": "Palco",        "rotulo": "Palco",        "en": "Stage",        "cor": "#0e7490", "seccao": "eventos",
     "definicao": "Uma sala ou palco nomeado onde se agendam sessões. Este evento nomeia os seus palcos de duas maneiras em páginas diferentes do seu próprio site."},
    {"id": "Pessoa",       "rotulo": "Pessoa",       "en": "Person",       "cor": "#b45309", "seccao": "protagonistas",
     "definicao": "Uma pessoa nomeada na lista de oradores publicada pelo evento, na sua qualidade profissional. Nome, papel listado, organização listada, ligações, os tópicos que o próprio evento lhe atribui, e as palavras da sua página que correspondem a um léxico publicado. Nunca uma biografia, nunca um contacto."},
    {"id": "Organizacao",  "rotulo": "Organização",  "en": "Organisation", "cor": "#1d4ed8", "seccao": "empresas",
     "definicao": "Uma organização sob a qual uma pessoa está LISTADA no seu cartão de orador. Derivada dos cartões, nunca escrita à mão; marcadores como «Independent» são assinalados, não removidos."},
    {"id": "Local",        "rotulo": "Local",        "en": "Place",        "cor": "#4a5b6a", "seccao": "eventos",
     "definicao": "Um sítio onde algo decorre. Não é uma pessoa, por isso a sua morada pode ser detida."},
    {"id": "Instituicao",  "rotulo": "Instituição",  "en": "Institution",  "cor": "#7c3aed", "seccao": "instituicoes",
     "definicao": "Um organismo público, um regulador ou uma unidade de investigação. Distinto de Organização porque a fonte e as obrigações são diferentes: uma instituição publica registo, uma empresa publica comunicação."},
    {"id": "Politica",     "rotulo": "Política",     "en": "Policy",       "cor": "#6d28d9", "seccao": "politicas",
     "definicao": "Uma política pública anunciada, e — quando existe e quando se consegue encontrar — o instrumento legal que a cria. O segundo é frequentemente o problema."},
    {"id": "Captura",      "rotulo": "Captura",      "en": "Snapshot",     "cor": "#5c5f66", "seccao": None,
     "definicao": "Uma captura datada das fontes: cada página obtida, congelada em bytes neste repositório, e hasheada."},
    {"id": "Fonte",        "rotulo": "Fonte",        "en": "Source",       "cor": "#8a8d94", "seccao": None,
     "definicao": "Uma página congelada de uma captura, com o seu SHA-256. É a coisa até onde uma afirmação anda para trás."},
    {"id": "Cobertura",    "rotulo": "Cobertura",    "en": "Coverage",     "cor": "#a16207", "seccao": None,
     "definicao": "A página publicada por um terceiro sobre esta matéria, obtida, congelada e hasheada como qualquer outra fonte. Ligada, nunca reproduzida."},
    {"id": "Historia",     "rotulo": "História",     "en": "Story",        "cor": "#b91c1c", "seccao": None,
     "definicao": "Uma peça que esta publicação escreveu, assente em fontes congeladas nomeadas e lida pelo editor de registo antes de publicar."},
    {"id": "Tema",         "rotulo": "Tema",         "en": "Topic",        "cor": "#7c3aed", "seccao": "casos-de-uso",
     "definicao": "Um tópico que o evento lista na página de uma pessoa, verbatim. Lido da página congelada, nunca derivado: o vocabulário deles, não o nosso."},
    {"id": "Setor",        "rotulo": "Setor",        "en": "Industry",     "cor": "#0e7490", "seccao": "empresas",
     "definicao": "Um setor nomeado pelo léxico publicado e correspondido na página de alguém. A aresta leva as palavras correspondidas. Diz que a página contém aquelas palavras; mais nada."},
    {"id": "Tecnologia",   "rotulo": "Tecnologia",   "en": "Technology",   "cor": "#0369a1", "seccao": "casos-de-uso",
     "definicao": "Uma tecnologia nomeada pelo léxico publicado e correspondida numa página congelada. Derivada por fórmula; a aresta mostra a prova."},
    {"id": "Ideia",        "rotulo": "Ideia",        "en": "Idea",         "cor": "#9333ea", "seccao": "casos-de-uso",
     "definicao": "Uma ideia recorrente da conversa de fundadores, nomeada pelo léxico publicado. Derivada por fórmula."},
    {"id": "Servico",      "rotulo": "Serviço",      "en": "Service",      "cor": "#be185d", "seccao": "empresas",
     "definicao": "Uma espécie de serviço que uma página congelada diz que alguém presta, correspondida pelo léxico publicado. Categorias, não nomes de produto."},
    {"id": "Produto",      "rotulo": "Produto",      "en": "Product",      "cor": "#c2410c", "seccao": "empresas",
     "definicao": "Uma espécie de produto que uma página congelada nomeia, correspondida pelo léxico publicado. Categorias, não nomes de produto."},
    {"id": "Editor",       "rotulo": "Editor",       "en": "Publisher",    "cor": "#475569", "seccao": "instituicoes",
     "definicao": "A casa que publica uma página congelada: um organismo, um jornal, um portal, o sítio de um evento. Sai do campo de editor do registo pela fórmula `editor_de_fonte`, e diz quem PUBLICA a página — não quem a escreveu, não quem a opera. Existe como tipo à parte porque a definição de Instituição é «um organismo público, um regulador ou uma unidade de investigação», e um jornal não é nenhuma dessas coisas: alargar aquela definição para caber aqui seria mudar o que ela promete."},
]

# verbo_pt / inverso_pt / domínio -> alcance / en / como a aresta se LÊ em português
# A leitura é o teste: se `{leitura}` não é uma frase portuguesa, a aresta está errada.
#
# UMA REGRA DE LEITURA QUE É UMA RECUSA, NÃO UMA PREFERÊNCIA DE ESTILO. Em português o particípio
# passado concorda em género com o sujeito, por isso «está listado em» e «está listada em» são
# formas diferentes e uma delas está errada para cada pessoa. Este site não sabe o género de
# ninguém: a fonte não o publica, e deduzi-lo do nome é exatamente a espécie de inferência sobre
# uma pessoa nomeada que o aviso recusa (e que o portão 7 proíbe). Por isso **toda a leitura que
# tem uma Pessoa no domínio ou no alcance é invariável em género** — usa verbos na terceira pessoa
# («fala», «consta», «usa», «defende») e nunca um particípio concordado. Onde o domínio é um tipo
# de género fixo (uma Fonte é feminina, um Evento é masculino) a concordância é conhecida e
# escreve-se. O portão 10 volta a ler cada leitura e falha a construção se uma que toca numa
# Pessoa contiver um particípio concordado.
ARESTAS = [
    ("fala_em",        "recebe",          "Pessoa",      "Evento",      "speaks_at",      "hosts",
     "{s} fala em {t}",                       "{t} recebe {s}"),
    ("listado_sob",    "organizacao_de",  "Pessoa",      "Organizacao", "listed_under",   "lists",
     "o evento lista {s} sob {t}",            "{t} é a organização sob a qual o evento lista {s}"),
    ("decorre_em",     "e_local_de",      "Evento",      "Local",       "takes_place_at", "venue_of",
     "{s} decorre em {t}",                    "{t} é local de {s}"),
    ("organizado_por", "organiza",        "Evento",      "Organizacao", "organised_by",   "organises",
     "{s} é organizado por {t}",              "{t} organiza {s}"),
    ("parte_de",       "contem",          "Sessao",      "Evento",      "part_of",        "contains",
     "{s} faz parte de {t}",                  "{t} contém {s}"),
    ("no_palco",       "acolhe",          "Sessao",      "Palco",       "on_stage",       "stages",
     "{s} está no {t}",                       "{t} acolhe {s}"),
    ("capturado_em",   "captura",         "Fonte",       "Captura",     "captured_in",    "captures",
     "{s} foi capturada em {t}",              "{t} captura {s}"),
    ("consta_em",      "atesta",          "Pessoa",      "Fonte",       "attested_by",    "attests",
     "{s} consta de {t}",                     "{t} atesta {s}"),
    ("consta_em",      "atesta",          "Sessao",      "Fonte",       "attested_by",    "attests",
     "{s} consta de {t}",                     "{t} atesta {s}"),
    ("consta_em",      "atesta",          "Evento",      "Fonte",       "attested_by",    "attests",
     "{s} consta de {t}",                     "{t} atesta {s}"),
    ("consta_em",      "atesta",          "Instituicao", "Fonte",       "attested_by",    "attests",
     "{s} consta de {t}",                     "{t} atesta {s}"),
    ("consta_em",      "atesta",          "Politica",    "Fonte",       "attested_by",    "attests",
     "{s} consta de {t}",                     "{t} atesta {s}"),
    ("presente_em",    "inclui",          "Pessoa",      "Captura",     "present_in",     "includes",
     "{s} está presente em {t}",              "{t} inclui {s}"),
    ("ausente_de",     "nao_inclui",      "Pessoa",      "Captura",     "absent_from",    "lacks",
     "{s} está ausente de {t}",               "{t} não inclui {s}"),
    ("cobre",          "coberto_por",     "Cobertura",   "Evento",      "covers",         "covered_by",
     "{s} cobre {t}",                         "{t} é coberto por {s}"),
    ("publicado_por",  "publica",         "Cobertura",   "Organizacao", "published_by",   "publishes",
     "{s} é publicada por {t}",               "{t} publica {s}"),
    ("assenta_em",     "sustenta",        "Historia",    "Fonte",       "stands_on",      "supports",
     "{s} assenta em {t}",                    "{t} sustenta {s}"),
    ("relata",         "relatado_por",    "Historia",    "Evento",      "reports",        "reported_by",
     "{s} relata {t}",                        "{t} é relatado por {s}"),
    ("fala_sobre",     "falado_por",      "Pessoa",      "Tema",        "speaks_on",      "spoken_on_by",
     "{s} fala sobre {t}",                    "{t} é falado por {s}"),
    ("atua_em",        "praticado_por",   "Pessoa",      "Setor",       "active_in",      "practised_by",
     "{s} atua em {t}",                       "{t} é praticado por {s}"),
    ("usa",            "usado_por",       "Pessoa",      "Tecnologia",  "uses",           "used_by",
     "{s} usa {t}",                           "{t} é usada por {s}"),
    ("defende",        "defendido_por",   "Pessoa",      "Ideia",       "advocates",      "advocated_by",
     "{s} defende {t}",                       "{t} é defendida por {s}"),
    ("oferece",        "oferecido_por",   "Pessoa",      "Servico",     "offers",         "offered_by",
     "{s} oferece {t}",                       "{t} é oferecido por {s}"),
    ("oferece",        "oferecido_por",   "Pessoa",      "Produto",     "offers",         "offered_by",
     "{s} oferece {t}",                       "{t} é oferecido por {s}"),
    ("publicado_em",   "publica_registo", "Politica",    "Instituicao", "published_in",   "publishes_record",
     "{s} é publicada em {t}",                "{t} publica no registo {s}"),
    ("publicada_por",  "publica_pagina",  "Fonte",       "Editor",      "issued_by",      "issues",
     "{s} é publicada por {t}",               "{t} publica a página {s}"),
    ("publicada_por",  "publica_pagina",  "Fonte",       "Instituicao", "issued_by",      "issues",
     "{s} é publicada por {t}",               "{t} publica a página {s}"),
    ("publicada_por",  "publica_pagina",  "Fonte",       "Evento",      "issued_by",      "issues",
     "{s} é publicada por {t}",               "{t} publica a página {s}"),
    ("publicada_por",  "publica_pagina",  "Fonte",       "Organizacao", "issued_by",      "issues",
     "{s} é publicada por {t}",               "{t} publica a página {s}"),
]

# Verbos cujas arestas são DERIVADAS pelo léxico e não lidas de uma lista. Cada uma leva
# `correspondeu` e o portão volta a correr o padrão sobre os bytes.
VERBOS_DERIVADOS = {"atua_em", "usa", "defende", "oferece"}

PROIBIDOS = [
    {"verbo": "relacionado_com", "porque": "Simétrico, logo seria o seu próprio inverso, e não diz nada que um leitor possa percorrer."},
    {"verbo": "associado_a",     "porque": "O verbo a que se recorre quando não se sabe qual é a relação. Descubra-se, ou deixe-se a aresta de fora."},
    {"verbo": "menciona",        "porque": "Num grafo construído a partir de texto, tudo «menciona» alguma coisa. É a ausência de um verbo."},
    {"verbo": "trabalha_em",     "porque": "Não é o que a fonte diz. Um cartão de orador lista uma organização; não afirma uma relação laboral. A aresta é listado_sob."},
]

TAXONOMIA = [
    {"id": "entidades",  "rotulo": "Entidades",            "tipos": ["Pessoa", "Organizacao", "Instituicao", "Editor", "Local"]},
    {"id": "programa",   "rotulo": "Programa",             "tipos": ["Evento", "Sessao", "Palco"]},
    {"id": "registo",    "rotulo": "Registo público",      "tipos": ["Politica"]},
    {"id": "prova",      "rotulo": "Prova",                "tipos": ["Captura", "Fonte", "Cobertura"]},
    {"id": "nosso",      "rotulo": "O nosso trabalho",     "tipos": ["Historia"]},
    {"id": "temas",      "rotulo": "Temas",                "tipos": ["Tema"]},
    {"id": "derivado",   "rotulo": "Derivado por fórmula", "tipos": ["Setor", "Tecnologia", "Ideia", "Servico", "Produto"]},
]

# A única classificação que este ficheiro inventa em vez de ler. Publicada como fórmula, para que
# se possa discordar dela, e cada valor diz «pelo título listado» para nunca ser confundido com um
# facto sobre a pessoa.
CLASSE_PAPEL = [
    ("investidor", "do lado do investimento, pelo título listado",
     r"\b(investor|partner|ventures?|\bvc\b|angel|capital|fund|\blp\b)\b"),
    ("fundador",   "fundador ou operacional, pelo título listado",
     r"\b(founder|co-founder|ceo|cto|coo|cpo|chief|head of|director|managing|leader)\b"),
    ("consultor",  "consultor, jurista ou académico, pelo título listado",
     r"\b(advisor|adviser|counsel|professor|researcher|lawyer|legal|consultant|author|phd)\b"),
]


def editor_de_fonte(publicador):
    """A fórmula `editor_de_fonte` — publicada em ontologia.formulas.

    O registo grava, para cada página congelada, o editor verbatim. A mesma casa aparece lá escrita
    de mais do que uma maneira: «Diário da República Eletrónico (INCM)» e «Diário da República»,
    «CORDIS — Comissão Europeia» e «Comissão Europeia». Esta função reduz a cadeia à casa que
    publica, em dois passos e nenhum mais:

      1. tira o parêntesis final, que nomeia quem OPERA e não quem publica — «(INCM)», «(AMA)»;
      2. fica com o segmento depois do último travessão, que separa a coleção da casa.

    O que a fórmula NÃO faz é juntar nomes que continuem diferentes depois destes dois passos. Se
    o registo diz «Diário da República» numa linha e «Diário da República Eletrónico» noutra, o
    grafo fica com dois nós, porque são duas coisas que o registo diz e decidir que são a mesma
    seria uma inferência nossa e não um facto dele. É a mesma recusa que produziu a história dos
    dois nomes para os mesmos palcos.
    """
    t = (publicador or "").strip()
    if not t:
        return ""
    t = re.sub(r"\s*\([^()]*\)\s*$", "", t).strip()
    if "\u2014" in t:
        t = t.rsplit("\u2014", 1)[1].strip()
    return t


def classe_papel(papel):
    r = (papel or "").lower()
    for cid, rotulo, padrao in CLASSE_PAPEL:
        if re.search(padrao, r):
            return cid, rotulo
    return "outro", "não classificado pelo título listado"


def ontologia():
    return {
        "id": "pt-ontologia", "versao": "0.1.0",
        "nota": ("A gramática deste grafo. Os verbos são portugueses e o campo `en` é uma anotação: "
                 "num sítio nativamente português, um caminho que não se lê em voz alta em "
                 "português tem as arestas erradas (§6 do resumo). O portão 10 lê cada verbo em "
                 "voz alta e falha a construção se um deles não produzir uma frase."),
        "seccoes": SECCOES,
        "tipos": TIPOS,
        "arestas": [
            {"verbo": v, "inverso": i, "dominio": d, "alcance": a,
             "en": {"verbo": ev, "inverso": ei},
             "leitura": le, "leitura_inversa": li}
            for v, i, d, a, ev, ei, le, li in ARESTAS
        ],
        "verbos_derivados": sorted(VERBOS_DERIVADOS),
        "proibidos": PROIBIDOS,
        "taxonomia": TAXONOMIA,
        "formulas": [
            {"id": "classe_papel",
             "o_que_faz": "Classifica uma pessoa pelo título sob o qual o evento a lista.",
             "porque_publicada": "É a única classificação que este site inventa. Publicada como padrão para que um leitor possa discordar dela.",
             "nunca_diz": "O que a pessoa é. Diz o que o título listado contém.",
             "regras": [{"classe": c, "rotulo": r, "padrao": p} for c, r, p in CLASSE_PAPEL]},
            {"id": "editor_de_fonte",
             "o_que_faz": "Reduz o campo de editor do registo à casa que publica a página.",
             "porque_publicada": "Faz nascer nós e arestas. Dois passos, nomeados, para que um leitor possa refazer o mesmo caminho: tirar o parêntesis final (quem opera) e ficar com o segmento depois do último travessão (a casa, e não a coleção).",
             "nunca_diz": "Que dois nomes diferentes são a mesma casa. Se o registo diz duas coisas, o grafo diz duas coisas.",
             "passos": ["tirar o parêntesis final: «dados.gov.pt (AMA)» → «dados.gov.pt»",
                        "ficar com o segmento depois do último travessão: «CORDIS — Comissão Europeia» → «Comissão Europeia»"]},
            {"id": "lexico",
             "o_que_faz": "Faz nascer arestas derivadas a partir de palavras numa página congelada.",
             "porque_publicada": "dados/lexico.json. O portão 8 volta a correr cada padrão sobre os bytes.",
             "nunca_diz": "Nada sobre a pessoa. Diz que a página contém aquelas palavras."},
        ],
    }


# --------------------------------------------------------------------- build ---
def main():
    evento = load("evento.json")
    pessoas = load("pessoas.json")
    orgs = load("organizacoes.json")
    registo = load("registo.json")
    mudancas = load("mudancas.json")
    temas = load("temas.json")
    lexico = load("lexico.json")
    sessoes = load("sessoes.json")
    verif_fonte = load("verificacoes-fonte.json")
    historias = load("historias.json") if (DADOS / "historias.json").exists() else {"historias": []}

    caps = registo["capturas"]
    ultima = caps[-1]
    por_id = {f["id"]: f for f in registo["fontes"]}
    lex = {e["id"]: e for e in lexico["entradas"]}

    nos, arestas, vistos = [], [], set()

    por_no = {}

    def no(n):
        if n["id"] in vistos:
            return
        vistos.add(n["id"])
        nos.append(n)
        por_no[n["id"]] = n

    def aresta(verbo, s, t, bloco, **extra):
        arestas.append({"id": f"{verbo}:{s}:{t}", "verbo": verbo, "origem": s, "destino": t,
                        "bloco": bloco, **extra})

    # --- a prova: cada captura e cada ficheiro congelado ----------------------
    for c in caps:
        no({"id": f"captura:{c}", "tipo": "Captura", "rotulo": f"Captura de {c}", "bloco": "prova",
            "data": c, "fonte": f"{ultima}/index"})
    for f in registo["fontes"]:
        fid = f"fonte:{f['id']}"
        no({"id": fid, "tipo": "Fonte", "rotulo": f["pagina"], "bloco": "prova",
            "sha256": f["sha256"], "bytes": f["bytes"], "url": f["url"],
            "publicador": f["publicador"], "congelada": f["congelada"], "fonte": f["id"]})
        aresta("capturado_em", fid, f"captura:{f['captura']}", "prova")

    # --- o evento, o seu local, quem o organiza ------------------------------
    ev = "evento:" + evento["id"]
    no({"id": ev, "tipo": "Evento", "rotulo": evento["nome"], "bloco": "evento",
        "datas": evento["datas"]["principais"], "url": evento["url"], "fonte": f"{ultima}/index"})
    local = "local:" + ident(evento["local"]["nome"])
    no({"id": local, "tipo": "Local", "rotulo": evento["local"]["nome"], "bloco": "evento",
        "concelho": evento["local"]["concelho"], "fonte": f"{ultima}/index"})
    aresta("decorre_em", ev, local, "evento")
    aresta("consta_em", ev, f"fonte:{ultima}/index", "prova")

    # --- as organizações, derivadas dos cartões ------------------------------
    for o in orgs["organizacoes"]:
        no({"id": "org:" + o["id"], "tipo": "Organizacao", "rotulo": o["nome"], "bloco": "organizacoes",
            "pessoas": len(o["pessoas"]), "marcador": o["marcador"],
            "derivado_de": "o campo de organização do cartão de orador, nunca escrito à mão",
            "fonte": f"{ultima}/oradores"})

    # --- as pessoas ----------------------------------------------------------
    listadas = {p["id"] for p in pessoas["pessoas"]}
    for p in pessoas["pessoas"]:
        pid = "pessoa:" + p["id"]
        cls, rotulo_cls = classe_papel(p.get("papel"))
        no({"id": pid, "tipo": "Pessoa", "rotulo": p["nome"], "bloco": "pessoas",
            "papel": p.get("papel"), "url": p.get("pagina"),
            "classe_papel": cls, "classe_papel_rotulo": rotulo_cls,
            "classe_papel_formula": "classe_papel — ver ontologia.formulas",
            "fonte": f"{ultima}/oradores"})
        aresta("fala_em", pid, ev, "pessoas")
        aresta("consta_em", pid, f"fonte:{ultima}/oradores", "prova")
        if p.get("organizacao"):
            aresta("listado_sob", pid, "org:" + ident(p["organizacao"]), "organizacoes")
        if f"{ultima}/oradores/{p['id']}" in por_id:
            aresta("consta_em", pid, f"fonte:{ultima}/oradores/{p['id']}", "prova")
        aresta("presente_em", pid, f"captura:{ultima}", "mudancas")

    # quem esteve numa captura anterior e já não está na lista publicada
    for m in mudancas["mudancas"]:
        for saiu in m["sairam"]:
            pid = "pessoa:" + saiu["id"]
            no({"id": pid, "tipo": "Pessoa", "rotulo": saiu["nome"], "bloco": "pessoas",
                "ja_nao_listado": True, "razao": None,
                "nota": ("Presente numa captura e ausente da seguinte. A razão fica em branco: "
                         "esta publicação regista a diferença e não a explica."),
                "fonte": f"{m['de']}/oradores"})
            aresta("ausente_de", pid, f"captura:{m['para']}", "mudancas")

    # --- o programa ----------------------------------------------------------
    for pl in sessoes["palcos"]:
        no({"id": "palco:" + pl["id"], "tipo": "Palco", "rotulo": pl["nome"], "bloco": "programa",
            "fonte": f"{ultima}/agenda"})
    for s in sessoes["sessoes"]:
        sid = "sessao:" + s["id"]
        no({"id": sid, "tipo": "Sessao", "rotulo": s["titulo"], "bloco": "programa",
            "dia": s["dia"], "inicio": s.get("inicio"), "quando": s.get("quando"),
            "formato": s.get("formato"), "url": s.get("url"),
            "verbatim": True, "fonte": f"{ultima}/agenda"})
        aresta("parte_de", sid, ev, "programa")
        aresta("consta_em", sid, f"fonte:{ultima}/agenda", "prova")
        if s.get("palco"):
            aresta("no_palco", sid, "palco:" + s["palco"], "programa")

    # --- os temas do evento, e as etiquetas derivadas pelo léxico -------------
    for pt in temas["pessoa_temas"]:
        tid = "tema:" + ident(pt["tema"])
        no({"id": tid, "tipo": "Tema", "rotulo": pt["tema"], "bloco": "temas",
            "verbatim": True, "de_quem": "a lista de tópicos do próprio evento",
            "fonte": pt["fonte"]})
        aresta("fala_sobre", "pessoa:" + pt["pessoa"], tid, "temas")

    TIPO_DE = {"Setor": "atua_em", "Tecnologia": "usa", "Ideia": "defende",
               "Serviço": "oferece", "Produto": "oferece"}
    for pe in temas["pessoa_etiquetas"]:
        e = lex[pe["etiqueta"]]
        tipo = {"Setor": "Setor", "Tecnologia": "Tecnologia", "Ideia": "Ideia",
                "Serviço": "Servico", "Produto": "Produto"}[e["tipo"]]
        nid = f"{tipo.lower()}:{e['id']}"
        no({"id": nid, "tipo": tipo, "rotulo": e["rotulo"], "bloco": "derivado",
            "derivado": True, "lexico": e["id"], "en": e["en"],
            "formula": "dados/lexico.json — uma expressão regular publicada",
            "fonte": pe["fonte"]})
        aresta(TIPO_DE[e["tipo"]], "pessoa:" + pe["pessoa"], nid, "derivado",
               correspondeu=pe["correspondeu"], lexico=e["id"])

    # --- o registo nacional: o que se conseguiu ler e o que não --------------
    # Estes nós são a primeira camada que não vem do evento. São poucos e são honestos: cada um
    # diz se a página que o atesta devolveu ou não um corpo legível por uma máquina.
    INSTITUICOES = {
        "gov-ia": ("Governo de Portugal", "O executivo. Publica o programa e as áreas de política."),
        "dre-inicio": ("Diário da República Eletrónico", "O diário oficial. Se o instrumento legal de uma política existe, é aqui que é publicado."),
        "dados-gov": ("dados.gov.pt", "O portal nacional de dados abertos, operado pela AMA."),
    }
    leg = verif_fonte.get("legibilidade", {})
    for pagina, (nome, definicao) in INSTITUICOES.items():
        fid = f"{ultima}/registo/{pagina}"
        if fid not in por_id:
            continue
        iid = "instituicao:" + ident(nome)
        d = leg.get(pagina, {})
        no({"id": iid, "tipo": "Instituicao", "rotulo": nome, "bloco": "registo",
            "definicao": definicao,
            "legivel_por_maquina": d.get("legivel_por_maquina"),
            "caracteres_visiveis": d.get("caracteres_visiveis"),
            "nota_legibilidade": ("A página deste organismo devolveu %s caracteres visíveis a um "
                                  "leitor automático a partir de %s bytes. É uma medição datada e "
                                  "hasheada sobre a legibilidade do registo público, e não uma "
                                  "opinião sobre o organismo."
                                  % (d.get("caracteres_visiveis"), d.get("bytes"))),
            "fonte": fid})
        aresta("consta_em", iid, f"fonte:{fid}", "prova")

    # --- quem publica cada página congelada ----------------------------------
    # Até aqui o grafo sabia de onde veio cada byte e não sabia de QUEM. A ligação faltava, e
    # faltava exatamente onde um leitor a quer: lê-se «Comissão Europeia» numa página e não há
    # nada por trás do nome. Esta passagem fecha isso — cada Fonte ganha uma aresta para a casa
    # que a publica, e a casa ganha uma página que lista tudo o que dela foi congelado.
    #
    # Resolve-se contra os nós que JÁ existem antes de se criar um novo, senão o Governo de
    # Portugal ficava com dois nós (um do registo nacional, outro daqui) e o grafo passava a
    # dizer que são duas casas. A ordem é a da especificidade da fonte do nó: um Evento e uma
    # Instituição foram lidos de uma página congelada; um Editor é derivado de um campo do
    # registo, e por isso é o último recurso e não o primeiro.
    por_rotulo = {}
    for n in nos:
        if n["tipo"] in ("Evento", "Instituicao", "Organizacao"):
            por_rotulo.setdefault(n["rotulo"], n["id"])

    editores = {}
    for f in registo["fontes"]:
        nome = editor_de_fonte(f["publicador"])
        if not nome:
            continue
        d = editores.setdefault(nome, {"verbatim": set(), "fontes": []})
        d["verbatim"].add(f["publicador"])
        d["fontes"].append(f["id"])

    for nome in sorted(editores):
        d = editores[nome]
        alvo = por_rotulo.get(nome)
        if alvo is None:
            alvo = "editor:" + ident(nome)
            no({"id": alvo, "tipo": "Editor", "rotulo": nome, "bloco": "registo",
                "derivado_de": "editor_de_fonte — ver ontologia.formulas",
                "fonte": d["fontes"][0]})
        n = por_no.get(alvo)
        if n is not None:
            n["publica"] = len(d["fontes"])
            # As formas exatas em que o registo escreve esta casa. Mais do que uma é um facto
            # sobre o registo, e fica à vista em vez de ser reduzido a uma.
            n["verbatim_no_registo"] = sorted(d["verbatim"])
        for fid in d["fontes"]:
            aresta("publicada_por", f"fonte:{fid}", alvo, "prova")

    # --- as histórias --------------------------------------------------------
    for h in historias["historias"]:
        hid = "historia:" + h["slug"]
        no({"id": hid, "tipo": "Historia", "rotulo": h["titulo"], "bloco": "historias",
            "estado": h["estado"], "fonte": h["assenta_em"][0] if h.get("assenta_em") else None})
        for sid in h.get("assenta_em", []):
            if sid in por_id:
                aresta("assenta_em", hid, f"fonte:{sid}", "historias")

    # --- blocos --------------------------------------------------------------
    BLOCOS = [
        {"id": "evento",       "rotulo": "O evento",            "ordem": 1},
        {"id": "organizacoes", "rotulo": "As organizações",     "ordem": 2},
        {"id": "pessoas",      "rotulo": "As pessoas",          "ordem": 3},
        {"id": "programa",     "rotulo": "O programa",          "ordem": 4},
        {"id": "registo",      "rotulo": "O registo nacional",  "ordem": 5},
        {"id": "temas",        "rotulo": "Os temas",            "ordem": 6},
        {"id": "derivado",     "rotulo": "Derivado por fórmula", "ordem": 7},
        {"id": "prova",        "rotulo": "A prova",             "ordem": 8},
        {"id": "mudancas",     "rotulo": "O que mudou",         "ordem": 9},
        {"id": "historias",    "rotulo": "As histórias",        "ordem": 10},
    ]
    for b in BLOCOS:
        b["nos"] = sum(1 for n in nos if n["bloco"] == b["id"])
        b["arestas"] = sum(1 for a in arestas if a["bloco"] == b["id"])

    # arestas duplicadas não são um erro de dados, são um erro de construção
    unicas, chaves = [], set()
    for a in arestas:
        if a["id"] in chaves:
            continue
        chaves.add(a["id"])
        unicas.append(a)
    arestas = unicas

    onto = ontologia()
    (DADOS / "ontologia.json").write_text(
        json.dumps(onto, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    grafo = {
        "id": "pt-grafo", "versao": "0.1.0", "atualizado": ultima,
        "nota": ("Cada nó nomeia a fonte congelada de onde veio; cada aresta é um verbo português "
                 "com um inverso distinto. Um caminho lê-se em voz alta em português, e se não se "
                 "ler, a aresta está errada."),
        "contagens": {"nos": len(nos), "arestas": len(arestas),
                      "tipos": len({n["tipo"] for n in nos}),
                      "verbos": len({a["verbo"] for a in arestas})},
        "blocos": BLOCOS, "nos": nos, "arestas": arestas,
    }
    (DADOS / "grafo.json").write_text(
        json.dumps(grafo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # --- triplos: o grafo como N-Triples, com os inversos declarados ---------
    BASE = "https://pt.newsroom.sgit.ai/grafo/"
    inv = {a["verbo"]: a["inverso"] for a in onto["arestas"]}
    linhas = []
    for v, i in sorted(inv.items()):
        linhas.append(f"<{BASE}verbo/{v}> <http://www.w3.org/2002/07/owl#inverseOf> <{BASE}verbo/{i}> .")
    for n in nos:
        linhas.append(f"<{BASE}no/{n['id']}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <{BASE}tipo/{n['tipo']}> .")
        rotulo = n["rotulo"].replace("\\", "\\\\").replace('"', '\\"')
        linhas.append(f'<{BASE}no/{n["id"]}> <http://www.w3.org/2000/01/rdf-schema#label> "{rotulo}"@pt .')
    for a in arestas:
        linhas.append(f"<{BASE}no/{a['origem']}> <{BASE}verbo/{a['verbo']}> <{BASE}no/{a['destino']}> .")
    (DADOS / "triplos.nt").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    # --- o manifesto: cada ficheiro deste site com o seu hash ----------------
    import hashlib
    manifesto = []
    for f in sorted(DADOS.rglob("*")):
        if f.is_file():
            manifesto.append({"ficheiro": f.relative_to(ROOT).as_posix(),
                              "bytes": f.stat().st_size,
                              "sha256": hashlib.sha256(f.read_bytes()).hexdigest()})
    (DADOS / "manifesto.json").write_text(json.dumps({
        "id": "pt-manifesto", "versao": "0.1.0", "atualizado": ultima,
        "nota": ("Cada ficheiro de dados deste site, com o seu SHA-256. É o que torna «a um clique "
                 "dos bytes» verificável em vez de uma promessa."),
        "contagem": len(manifesto), "ficheiros": manifesto,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"grafo: {len(nos)} nós, {len(arestas)} arestas, "
          f"{len({n['tipo'] for n in nos})} tipos, {len({a['verbo'] for a in arestas})} verbos, "
          f"{len(linhas)} triplos")
    return grafo


if __name__ == "__main__":
    main()

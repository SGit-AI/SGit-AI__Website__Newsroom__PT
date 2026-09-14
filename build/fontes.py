#!/usr/bin/env python3
"""A redação de pt.newsroom.sgit.ai — a lista de fontes-alvo.

The single place that says WHAT this newsroom fetches. `extract.py` imports it, the daily run
re-fetches it, and `dados/fontes-alvo.json` is written from it so the list is public rather than
buried in code.

Three kinds, and the distinction is load-bearing rather than tidy:

  PROPRIAS   pages the subject publishes about itself (the event's own site, a ministry's own
             site). A primary source for what that body SAYS, never for whether it is true.
  ABERTAS    machine-readable public datasets (§10 of the brief). The only sources that can
             support a claim about the ecosystem rather than about one event.
  IMPRENSA   third-party pages about the beat. Linked, summarised in our words, never quoted at
             length (CLAUDE.md rule 3).

Every entry names its publisher, because the register has to say who said a thing, and its
`lingua`, because a Portuguese newsroom transcribing an English source is making a claim about
the transcription (CLAUDE.md, Language).
"""

# The first beat (bootstrap prompt §2): the event that is on this week.
EVENTO = {
    "id": "startup-summit-lisbon-2026",
    "nome": "Startup Summit Lisbon 2026",
    "host": "https://startupsummit.io",
    "publicador": "Startup Summit Lisbon 2026",
    "lingua": "en",
    "paginas": {
        "index": "",
        "agenda": "agenda",
        "oradores": "speakers",
        "patrocinadores": "sponsors",
        "bilhetes": "tickets",
        "local": "location",
        "faq": "faq",
        "resumo-ia": "ai-summary",
    },
    "texto": {"llms.txt": "llms.txt"},
}

# The national record. These are the sources the brief's three first articles (§11) stand or fail
# on. Two of them are expected to be difficult, and that difficulty IS the story the brief
# commissions: a record that a machine cannot read is a finding about the record, not a failure of
# the reader. Whatever comes back is frozen and hashed exactly like anything else.
REGISTO_NACIONAL = {
    "gov-ia": {
        "url": "https://www.portugal.gov.pt/pt/gc24/governo/programa-do-governo",
        "publicador": "Governo de Portugal",
        "lingua": "pt",
        "porque": "A página do próprio Governo. O ponto de partida para saber o que o registo público contém sobre a política de IA.",
    },
    "dre-inicio": {
        "url": "https://dre.pt/",
        "publicador": "Diário da República Eletrónico (INCM)",
        "lingua": "pt",
        "porque": "O diário oficial. Se o instrumento legal de uma política existe, está aqui — e se um leitor automático não o consegue ler, isso é uma afirmação verificável sobre a legibilidade do registo nacional.",
    },
    "dados-gov": {
        "url": "https://dados.gov.pt/pt/datasets/",
        "publicador": "dados.gov.pt (AMA)",
        "lingua": "pt",
        "porque": "O portal nacional de dados abertos. Uma varredura por qualquer conjunto de dados adjacente a IA (§10 do resumo).",
    },
}

# The two datasets the brief (§10) marks machine-readable, and the research-unit list it calls the
# citable answer for institutions. This is the layer that lets this site claim something
# /portugal/ cannot: organisations that appear in public funding, with amounts and dates.
ABERTAS = {
    "cordis": {
        "url": "https://cordis.europa.eu/projects/pt",
        "publicador": "CORDIS — Comissão Europeia",
        "lingua": "en",
        "porque": "A base de dados dos projetos de investigação europeus, com conjuntos de dados abertos. A melhor semente para investigação, financiamento e ligações institucionais.",
    },
    "fct-unidades": {
        "url": "https://www.fct.pt/en/financiamento/programas-de-financiamento/unidades-de-id/",
        "publicador": "Fundação para a Ciência e a Tecnologia",
        "lingua": "pt",
        "porque": "A lista de unidades de I&D financiadas. A resposta citável para as instituições, em vez de adivinhar.",
    },
}

# Third-party pages about the beat.
IMPRENSA = {
    "portugalglobal-maratona": {
        "url": "https://portugalglobal.pt/en/news/2026/julho/startup-summit-lisbon-opens-applications-for-48hr-pitch-marathon/",
        "publicador": "AICEP Portugal Global",
        "tipo": "notícia",
        "lingua": "en",
    },
    "pbn-recorde-guinness": {
        "url": "https://www.portugalbusinessesnews.com/post/startup-summit-lisbon-will-officially-attempt-to-set-a-guinness-world-record",
        "publicador": "Portugal Business News",
        "tipo": "notícia",
        "lingua": "en",
    },
    "scaleup-porto": {
        "url": "https://scaleupporto.pt/event/startup-summit-lisbon-2026/",
        "publicador": "ScaleUp Porto",
        "tipo": "listagem",
        "lingua": "pt",
    },
    "startupevents-org": {
        "url": "https://startupevents.org/startup-events-calendar/startup-summit-lisbon-2026",
        "publicador": "StartupEvents.org",
        "tipo": "listagem",
        "lingua": "en",
    },
}

# Sources that were attempted and did not resolve. They are NOT quietly dropped: a source this
# newsroom could not reach is a fact about the public record, and the brief (§10) is explicit that
# the size of what cannot be seen belongs on the page rather than in a footnote. `extract.py`
# re-attempts every one of these on each run and moves it into the register the day it answers.
TENTADAS = {
    "recuperar-portugal": {
        "url": "https://recuperarportugal.gov.pt/",
        "publicador": "Recuperar Portugal (PRR)",
        "lingua": "pt",
        "porque": "O portal de transparência do plano de recuperação: quem recebeu dinheiro público, para quê. O resumo (§10) marca-o como legível por máquina e é a segunda das duas sementes abertas do dia um.",
    },
}


def alvos():
    """Every target, flattened, in the shape the register and fontes-alvo.json use."""
    out = []
    for nome, caminho in {**EVENTO["paginas"], **EVENTO["texto"]}.items():
        out.append({
            "id": nome, "grupo": "evento", "url": f"{EVENTO['host']}/{caminho}",
            "publicador": EVENTO["publicador"], "lingua": EVENTO["lingua"],
            "texto": nome in EVENTO["texto"],
        })
    for grupo, tabela in (("registo", REGISTO_NACIONAL), ("abertas", ABERTAS), ("imprensa", IMPRENSA)):
        for cid, e in tabela.items():
            out.append({"id": cid, "grupo": grupo, "url": e["url"], "publicador": e["publicador"],
                        "lingua": e["lingua"], "texto": False,
                        **({"tipo": e["tipo"]} if "tipo" in e else {}),
                        **({"porque": e["porque"]} if "porque" in e else {})})
    return out

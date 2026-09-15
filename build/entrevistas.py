#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the interview method, and the prompts that do the work.

    python3 build/entrevistas.py    # after revisao.py, before build.py

WHAT THIS IS. The other half of what this newsroom publishes. `briefs/pack/08__research-briefs/`
sends an assistant after DOCUMENTS; `briefs/pack/09__entrevistas/` sends it into a CONVERSATION, and
what comes back is a different kind of material: a person's own words about their own work.

WHY THE PAGE RENDERS THE PROMPTS INSTEAD OF LINKING THEM. The research briefs are LINKED and not
republished, because they are read once by whoever is running a research pass. These are different:
a prompt is copied, by a person who is about to paste it into ChatGPT, often on a phone. A page that
sends them to a raw markdown file to select-all is a page that loses them.

So the page is a SECOND VIEW of one copy, never a second copy. The markdown under
`briefs/pack/09__entrevistas/` is the source; this file renders it and marks the result derived; the
gate below fails the build if the two ever disagree. If the HTML and the markdown could drift, the
design would be wrong — it is the same rule that keeps a frozen page out of this site's pages.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTE = ROOT / "briefs" / "pack" / "09__entrevistas"
DADOS = ROOT / "dados"

# The order is the order a person meets them, not alphabetical.
PECAS = [
    ("01__prompt-da-entrevista.pt.md", "O prompt da entrevista", "português",
     "Cola-se no ChatGPT como primeira mensagem. É sempre o mesmo, seja quem for a pessoa.",
     "entrevistado"),
    ("02__the-interview-prompt.en.md", "The interview prompt", "english",
     "The same interviewer, in English. The interview may be in either language; what gets "
     "published is always European Portuguese.", "entrevistado"),
    ("03__bloco-do-tema.md", "O bloco do tema", "português",
     "A segunda mensagem, e a única que muda de entrevista para entrevista. Uma entrevista vale o "
     "que valer este bloco.", "agente"),
    ("04__prompt-do-agente.md", "O prompt do agente", "português",
     "O que o editor dá a uma sessão de agente para preparar um pacote. O agente monta, não "
     "entrevista.", "editor"),
]


def main():
    pecas = []
    for ficheiro, titulo, lingua, porque, quem in PECAS:
        caminho = FONTE / ficheiro
        if not caminho.exists():
            raise SystemExit(f"entrevistas: falta {caminho.relative_to(ROOT)}")
        texto = caminho.read_text(encoding="utf-8")
        pecas.append({
            "ficheiro": ficheiro,
            "caminho": f"briefs/pack/09__entrevistas/{ficheiro}",
            "titulo": titulo,
            "lingua": lingua,
            "porque": porque,
            "para_quem": quem,
            "linhas": len(texto.split("\n")),
            "sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
            "texto": texto,
        })

    leia = (FONTE / "README.md").read_text(encoding="utf-8")
    doc = {
        "id": "pt-entrevistas",
        "versao": "1.0.0",
        "o_que_e": ("O método das entrevistas desta redação: um prompt que faz o ChatGPT conduzir "
                    "a conversa por voz, um bloco que diz sobre o que é, e um prompt que manda um "
                    "agente montar o pacote para uma pessoa em concreto."),
        "a_regra": ("Uma entrevista é uma fonte primária sobre quem fala, e mais nada. O que a "
                    "pessoa afirmar sobre o mundo é uma afirmação para verificar, não um facto por "
                    "ter sido dito em voz alta."),
        "derivado_de": "briefs/pack/09__entrevistas/",
        "contagem": len(pecas),
        "readme": leia,
        "pecas": pecas,
    }
    (DADOS / "entrevistas.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f'entrevistas: {len(pecas)} peças renderizadas de {FONTE.relative_to(ROOT)}/, '
          f'{sum(p["linhas"] for p in pecas)} linhas ao todo')


if __name__ == "__main__":
    main()

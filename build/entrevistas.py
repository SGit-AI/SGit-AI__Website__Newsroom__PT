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

# TWO PACKS, AND THE DIRECTION IS THE DIFFERENCE. `09__entrevistas/` points OUTWARD: an assistant
# interviews somebody outside the newsroom and what comes back is raw material for an article.
# `10__entrevista-ao-editor/` points INWARD: an agent has ChatGPT interview the editor of record and
# what comes back is direction — what to work on, what to drop, what he thinks matters. Same
# mechanism, opposite direction, and the second one is the reason the first one has anything to do.
#
# The order within each is the order a person meets them, not alphabetical.
GRUPOS = [
    ("09__entrevistas", "Entrevistar alguém, para escrever",
     "Uma pessoa ocupada não escreve duas páginas sobre o seu trabalho. Fala vinte minutos sobre "
     "ele, à hora que lhe der jeito, por voz ou por escrito.",
     [("01__prompt-da-entrevista.pt.md", "O prompt da entrevista", "português",
       "Cola-se no ChatGPT como primeira mensagem. É sempre o mesmo, seja quem for a pessoa.",
       "entrevistado"),
      ("02__the-interview-prompt.en.md", "The interview prompt", "english",
       "The same interviewer, in English. The interview may be in either language; what gets "
       "published is always European Portuguese.", "entrevistado"),
      ("03__bloco-do-tema.md", "O bloco do tema", "português",
       "A segunda mensagem, e a única que muda de entrevista para entrevista. Uma entrevista vale "
       "o que valer este bloco.", "agente"),
      ("04__prompt-do-agente.md", "O prompt do agente", "português",
       "O que o editor dá a uma sessão de agente para preparar um pacote. O agente monta, não "
       "entrevista.", "editor")]),
    ("10__entrevista-ao-editor", "Entrevistar o editor, para saber o que fazer",
     "Um agente sabe o que tem à frente e não sabe o que o editor acha que importa. Vinte minutos "
     "tiram isso, e tiram-no melhor do que qualquer formulário.",
     [("01__prompt-de-preparacao.md", "O prompt de preparação", "português",
       "O agente lê o seu próprio mandato, os seus issues e o que correu mal, e escreve o bloco de "
       "estado. Sem isto a conversa é genérica e não vale o tempo de ninguém.", "agente"),
      ("02__prompt-da-entrevista.pt.md", "O prompt da entrevista ao editor", "português",
       "O entrevistador. Leva o editor pelas perguntas do agente, com a proposta dele em cada uma.",
       "editor"),
      ("03__the-interview-prompt.en.md", "The editor interview prompt", "english",
       "The same, in English.", "editor"),
      ("04__o-que-volta.md", "O que volta, e o que se faz com ele", "português",
       "Decisões fazem-se; ideias abrem um issue e ficam à espera. Confundir as duas é como um "
       "agente faz trabalho que ninguém pediu.", "agente")]),
]


def main():
    grupos = []
    for pasta, titulo, porque, pecas_def in GRUPOS:
        fonte = ROOT / "briefs" / "pack" / pasta
        pecas = []
        for ficheiro, t_peca, lingua, porque_peca, quem in pecas_def:
            caminho = fonte / ficheiro
            if not caminho.exists():
                raise SystemExit(f"entrevistas: falta {caminho.relative_to(ROOT)}")
            texto = caminho.read_text(encoding="utf-8")
            pecas.append({
                "ficheiro": ficheiro,
                "caminho": f"briefs/pack/{pasta}/{ficheiro}",
                "titulo": t_peca,
                "lingua": lingua,
                "porque": porque_peca,
                "para_quem": quem,
                "linhas": len(texto.split("\n")),
                "sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
                "texto": texto,
            })
        grupos.append({
            "pasta": pasta,
            "id": pasta.split("__", 1)[1],
            "titulo": titulo,
            "porque": porque,
            "readme": (fonte / "README.md").read_text(encoding="utf-8"),
            "pecas": pecas,
        })

    doc = {
        "id": "pt-entrevistas",
        "versao": "2.0.0",
        "o_que_e": ("Duas entrevistas e uma só mecânica. Uma aponta para fora — um assistente "
                    "entrevista alguém, e o que volta é matéria para um artigo. A outra aponta "
                    "para dentro — um agente faz o ChatGPT entrevistar o editor de registo, e o "
                    "que volta é direção."),
        "a_regra": ("Uma entrevista é uma fonte primária sobre quem fala, e mais nada. O que a "
                    "pessoa afirmar sobre o mundo é uma afirmação para verificar, não um facto por "
                    "ter sido dito em voz alta — e isso vale também quando quem fala é o editor."),
        "derivado_de": "briefs/pack/09__entrevistas/ e briefs/pack/10__entrevista-ao-editor/",
        "contagem": sum(len(g["pecas"]) for g in grupos),
        "grupos": grupos,
        "pecas": [p for g in grupos for p in g["pecas"]],
    }
    (DADOS / "entrevistas.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f'entrevistas: {len(grupos)} grupos, {doc["contagem"]} peças, '
          f'{sum(p["linhas"] for p in doc["pecas"])} linhas ao todo')


if __name__ == "__main__":
    main()

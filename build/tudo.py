#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — a construção inteira, por ordem, num só comando.

    python3 build/tudo.py              # construir e conferir
    python3 build/tudo.py --fetch      # o mesmo, mas a ir buscar as fontes primeiro
    python3 build/tudo.py --so-portoes # só os portões, sem reconstruir

PORQUE É QUE ISTO EXISTE. A sequência tem onze passos e **a ordem importa**: `entidades.py` lê o
grafo que `graph.py` escreve, `artigos.py` lê os comentários que `comentarios.py` deriva, e a
passagem que transforma uma menção em ligação lê o `dados/entidades.json` que só existe depois de
`entidades.py` correr. Correr os passos por outra ordem não rebenta — produz um site com menos
ligações do que devia e nenhum aviso, que é pior.

A lista de comandos em `CLAUDE.md` é mais antiga do que metade destes passos, e `CLAUDE.md` é o
ficheiro de regras: está na lista de recusa de propósito, e mudá-lo para acompanhar o código é ao
contrário. Então a ordem verdadeira vive aqui, num ficheiro executável, que é o sítio onde uma
ordem não pode ficar desatualizada sem que alguma coisa falhe.

**Um portão vermelho pára tudo.** Não há continuação depois de uma falha, e o código de saída é o
do passo que falhou. Nunca se lança com um portão vermelho.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (comando, o que faz, é-um-portão). A ordem é a ordem.
PASSOS = [
    (["python3", "build/extract.py"],
     "obter, congelar, hashear, registar, extrair, comparar", False),
    (["python3", "build/graph.py"],
     "ontologia, grafo, triplos, manifesto — inclui a camada dos editores das fontes", False),
    (["python3", "build/entidades.py"],
     "dados/entidades.json e uma página por entidade — TEM de vir antes de tudo o que gera "
     "páginas, porque é este ficheiro que faz uma menção virar ligação", False),
    (["python3", "build/comentarios.py"],
     "o trabalho dos agentes sobre cada artigo, derivado dos registos — antes de artigos.py", False),
    (["python3", "build/mesa.py"],
     "dados/redacao.json — o estado da mesa, contado dos ficheiros que já existem", False),
    (["python3", "build/artigos.py"],
     "as pastas datadas viram páginas, e dados/historias.json nasce delas", False),
    (["python3", "build/build.py"],
     "a primeira página e as secções", False),
    (["python3", "build/paginas_extra.py"],
     "/api/ e /proveniencia/", False),
    (["python3", "build/api.py"],
     "api/v1/ — cada caminho é um ficheiro, e por isso o openapi.json é honesto", False),
    (["python3", "build/backoffice.py"],
     "a consola de operações, em inglês", False),
    (["python3", "build/chrome.py"],
     "llms.txt, sitemap.xml, index.md — a superfície que uma máquina lê", False),
    (["python3", "build/gates.py"],
     "os portões do núcleo (1-15)", True),
    (["python3", "build/gates_artigos.py"],
     "artigos, secções, bastidores, entidades, comentários e execuções (16-26)", True),
    (["node", "admin/build/validate.js"],
     "o portão do site: estrutura, ligações, versão, canónicos, fuga de chaves", True),
]


def main(argv):
    so_portoes = "--so-portoes" in argv
    com_fetch = "--fetch" in argv

    passos = [p for p in PASSOS if p[2]] if so_portoes else list(PASSOS)
    if not so_portoes and not com_fetch:
        # Sem `--fetch`, `extract.py` volta a extrair das cópias que já estão congeladas em vez de
        # ir à rede. É a ordem certa por omissão: uma construção não deve depender de a rede
        # estar de pé, nem tocar nas fontes de outras pessoas sem que alguém o peça.
        passos = [p for p in passos if p[0][1] != "build/extract.py"]
    elif com_fetch:
        passos = [(c + ["--fetch"] if c[1] == "build/extract.py" else c, d, g)
                  for c, d, g in passos]

    largura = max(len(" ".join(c)) for c, _, _ in passos)
    for comando, o_que, e_portao in passos:
        etiqueta = " ".join(comando)
        print(f'\n\033[1m→ {etiqueta}\033[0m'.ljust(largura + 14) + f'  {o_que}')
        r = subprocess.run(comando, cwd=ROOT)
        if r.returncode != 0:
            aviso = ("PORTÃO VERMELHO" if e_portao else "PASSO FALHADO")
            print(f'\n\033[31m{aviso}: {etiqueta} saiu com {r.returncode}.\033[0m')
            print("A construção pára aqui. Nada do que vem a seguir correu, e não se lança "
                  "com um portão vermelho.")
            return r.returncode

    print("\n\033[32mtudo: OK\033[0m — construído e conferido pelos três portões.")
    print("Falta, e é do editor: incrementar admin/build/version.txt, escrever a linha em "
          "admin/versions.html, e só então empurrar.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

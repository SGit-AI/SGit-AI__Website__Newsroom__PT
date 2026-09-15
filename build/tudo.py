#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — a construção inteira, por ordem, num só comando.

    python3 build/tudo.py              # construir e conferir
    python3 build/tudo.py --fetch      # o mesmo, mas a ir buscar as fontes primeiro
    python3 build/tudo.py --so-portoes # só os portões, sem reconstruir
    python3 build/tudo.py --render     # mais o portão do navegador (precisa de playwright)

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
    (["python3", "build/equipa.py"],
     "o registo dos agentes, o correio em Email-FS-lite e o quadro de cada um — TEM de vir antes "
     "de mesa.py e de backoffice.py, porque é este passo que escreve dados/correio.json e "
     "dados/quadro.json, e os dois contam o correio a partir dele e nunca da pasta", False),
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
    (["python3", "build/pontes.py"],
     "a página das pontes: como o editor chega aos bastidores a partir do navegador", False),
    (["python3", "build/chrome.py"],
     "llms.txt, sitemap.xml, index.md — a superfície que uma máquina lê", False),
    (["python3", "build/gates.py"],
     "os portões do núcleo (1-15)", True),
    (["python3", "build/gates_artigos.py"],
     "artigos, secções, bastidores, entidades, comentários e execuções (16-26)", True),
    (["node", "admin/build/validate.js"],
     "o portão do site: estrutura, ligações, versão, canónicos, fuga de chaves", True),
]

# O portão do navegador é à parte porque precisa de um navegador e de um servidor, e este
# repositório não tem dependências de node. Corre-se com `--render`, antes de um lançamento que
# mexa em componentes. Sem ele, um componente que rebente ao carregar passa os outros três
# portões e chega ao leitor como uma caixa vazia — que parece uma escolha de desenho.
RENDER = (["node", "admin/build/render.mjs"],
          "o portão do navegador: cada componente abre mesmo, sem erros e sem transbordar", True)


def servidor_local():
    """Um servidor de ficheiros só para o portão do navegador, e desligado a seguir.

    O site é uma árvore de ficheiros e um navegador a abrir `file://` não faz `fetch` — que é
    exatamente o que cada componente faz. Sem isto, o portão do navegador media a política de
    origem do Chromium em vez de medir o site.

    A porta é escolhida pelo sistema (porta 0) e não fixada. Uma porta fixa falha assim que
    outra coisa a está a usar — outro servidor esquecido, outra sessão a trabalhar no mesmo
    repositório ao mesmo tempo — e falhar por causa disso seria um portão vermelho que não diz
    nada sobre o site."""
    import http.server, socketserver, threading, functools

    class Silencioso(http.server.SimpleHTTPRequestHandler):
        # Sem isto, cada um dos duzentos pedidos que o navegador faz escreve uma linha, e a saída
        # do portão — que é a coisa que se quer ler — fica enterrada.
        def log_message(self, *_):
            pass

    handler = functools.partial(Silencioso, directory=str(ROOT))
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def main(argv):
    so_portoes = "--so-portoes" in argv
    com_fetch = "--fetch" in argv
    com_render = "--render" in argv

    passos = [p for p in PASSOS if p[2]] if so_portoes else list(PASSOS)
    if not so_portoes and not com_fetch:
        # Sem `--fetch`, `extract.py` volta a extrair das cópias que já estão congeladas em vez de
        # ir à rede. É a ordem certa por omissão: uma construção não deve depender de a rede
        # estar de pé, nem tocar nas fontes de outras pessoas sem que alguém o peça.
        passos = [p for p in passos if p[0][1] != "build/extract.py"]
    elif com_fetch:
        passos = [(c + ["--fetch"] if c[1] == "build/extract.py" else c, d, g)
                  for c, d, g in passos]

    srv = None
    if com_render:
        srv, base = servidor_local()
        comando, o_que, e_portao = RENDER
        passos = passos + [(comando + [base], o_que, e_portao)]

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
            if srv:
                srv.shutdown()
            return r.returncode

    if srv:
        srv.shutdown()
    quantos = "quatro portões" if com_render else "três portões"
    print(f"\n\033[32mtudo: OK\033[0m — construído e conferido pelos {quantos}.")
    if not com_render:
        print("Sem `--render`: nenhum componente foi aberto num navegador. Se esta mudança mexeu "
              "em assets/components/, corra `python3 build/tudo.py --render`.")
    print("Falta, e é do editor: incrementar admin/build/version.txt, escrever a linha em "
          "admin/versions.html, e só então empurrar.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

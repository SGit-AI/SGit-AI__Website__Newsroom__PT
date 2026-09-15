#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the whole build, in order, in one command.

    python3 build/tudo.py              # build and check
    python3 build/tudo.py --fetch      # the same, fetching the sources first
    python3 build/tudo.py --so-portoes # gates only, no rebuild
    python3 build/tudo.py --render     # plus the browser gate (needs playwright)

WHY THIS EXISTS. The sequence has fourteen steps and **the order is load-bearing**: `entidades.py`
reads the graph `graph.py` writes, `artigos.py` reads the comments `comentarios.py` derives, and
the pass that turns a mention into a link reads the `dados/entidades.json` that only exists after
`entidades.py` has run. Running the steps in another order does not break — it produces a site with
fewer links than it should have and no warning at all, which is worse.

The command list in `CLAUDE.md` is older than half these steps, and `CLAUDE.md` is the rules file:
it is deny-listed on purpose, and editing it to match the code is backwards. So the real order
lives here, in an executable file, which is the one place an order cannot go stale without
something failing.

**A red gate stops everything.** Nothing runs after a failure, and the exit code is the failing
step's. Never release on a red gate.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (command, what it does, is-a-gate). The order is the order.
PASSOS = [
    (["python3", "build/extract.py"],
     "fetch, freeze, hash, register, extract, diff", False),
    (["python3", "build/transferencias.py"],
     "evidence transferred from a sibling publication — verified, kept as ITS evidence", False),
    (["python3", "build/graph.py"],
     "ontology, graph, triples, manifest — including the source-publisher layer", False),
    (["python3", "build/entidades.py"],
     "dados/entidades.json e uma página por entidade — TEM de vir antes de tudo o que gera "
     "páginas, porque é este ficheiro que faz uma menção virar ligação", False),
    (["python3", "build/equipa.py"],
     "o registo dos agentes, o correio em Email-FS-lite e o quadro de cada um — TEM de vir antes "
     "de mesa.py e de backoffice.py, porque é este passo que escreve dados/correio.json e "
     "dados/quadro.json, e os dois contam o correio a partir dele e nunca da pasta", False),
    (["python3", "build/comentarios.py"],
     "the agents' work on each article, derived from the records — before artigos.py", False),
    (["python3", "build/mesa.py"],
     "dados/redacao.json — the desk's state, counted from files that already exist", False),
    (["python3", "build/artigos.py"],
     "the dated folders become pages, and dados/historias.json is derived from them", False),
    (["python3", "build/build.py"],
     "the front page and the sections", False),
    (["python3", "build/paginas_extra.py"],
     "/api/ and /proveniencia/", False),
    (["python3", "build/api.py"],
     "api/v1/ — every path is a file, which is why openapi.json is honest", False),
    (["python3", "build/backoffice.py"],
     "the operations console, in English", False),
    (["python3", "build/mandatos.py"],
     "agents/<id>/ROLE.md and MANDATE.md, rendered from the register — never hand-written", False),
    (["python3", "build/pontes.py"],
     "the bridges page: how the editor reaches the back office from the browser", False),
    (["python3", "build/chrome.py"],
     "llms.txt, sitemap.xml, index.md — the surface a machine reads", False),
    (["python3", "build/gates.py"],
     "the core gates (1-15), in the deny-listed file", True),
    (["python3", "build/gates_artigos.py"],
     "articles, sections, back office, entities, comments, runs and language (16-28)", True),
    (["node", "admin/build/validate.js"],
     "the site gate: structure, links, version, canonicals, key-leak tripwire", True),
]

# The browser gate is separate because it needs a browser and a server, and this repository has no
# node dependencies. Run it with `--render`, before any release that touches components. Without
# it, a component that throws on load passes the other three gates and reaches the reader as an
# empty box — which looks like a design choice.
RENDER = (["node", "admin/build/render.mjs"],
          "the browser gate: every component really opens, with no errors and no overflow", True)


def servidor_local():
    """A file server for the browser gate alone, shut down straight after.

    The site is a tree of files, and a browser opening `file://` cannot `fetch` — which is exactly
    what every component does. Without this, the browser gate would be measuring Chromium's origin
    policy instead of measuring the site.

    The port is chosen by the system (port 0), not fixed. A fixed port fails the moment something
    else is using it — a forgotten server, another session working in the same repository at the
    same time — and failing for that reason would be a red gate that says nothing about the
    site."""
    import http.server, socketserver, threading, functools

    class Silencioso(http.server.SimpleHTTPRequestHandler):
        # Without this, each of the two hundred requests the browser makes writes a line, and the
        # gate's output — the thing you actually want to read — is buried.
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
        # Without `--fetch`, `extract.py` re-extracts from the copies already frozen rather than
        # going to the network. That is the right default: a build should not depend on the network
        # being up, nor touch other people's sources unless somebody asked for it.
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
            aviso = ("RED GATE" if e_portao else "STEP FAILED")
            print(f'\n\033[31m{aviso}: {etiqueta} saiu com {r.returncode}.\033[0m')
            print("The build stops here. Nothing after it ran, and you do not release on a "
                  "red gate.")
            if srv:
                srv.shutdown()
            return r.returncode

    if srv:
        srv.shutdown()
    quantos = "four gates" if com_render else "three gates"
    print(f"\n\033[32mtudo: OK\033[0m — built and checked by the {quantos}.")
    if not com_render:
        print("Without `--render`, no component was opened in a browser. If this change touched "
              "assets/components/, run `python3 build/tudo.py --render`.")
    print("Left, and the editor's: bump admin/build/version.txt, write the row in "
          "admin/versions.html, and only then push.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

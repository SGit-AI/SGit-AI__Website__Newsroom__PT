#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the whole build, in order, in one command.

    python3 build/tudo.py              # build and check
    python3 build/tudo.py --fetch      # the same, fetching the sources first
    python3 build/tudo.py --so-portoes # gates only, no rebuild
    python3 build/tudo.py --render     # plus the browser gate (needs playwright)

WHY THIS EXISTS. The sequence is long and **the order is load-bearing**: `entidades.py` reads the
graph `graph.py` writes, `artigos.py` reads the comments `comentarios.py` derives, and the pass that
turns a mention into a link reads the `dados/entidades.json` that only exists after `entidades.py`
has run. Running the steps in another order does not break — it produces a site with fewer links
than it should have and no warning at all, which is worse.

The command list in `CLAUDE.md` is older than half these steps, and `CLAUDE.md` is the rules file:
it is deny-listed on purpose, and editing it to match the code is backwards. So the real order
lives here, in an executable file, which is the one place an order cannot go stale without
something failing.

**A red gate stops everything.** Nothing runs after a failure, and the exit code is the failing
step's. Never release on a red gate.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def data_do_congelamento():
    """The capture date the research deliveries were frozen under, read FROM DISK.

    `build/entregas.py --date` defaults to TODAY and re-checks each excerpt against
    `fontes/congeladas/<date>/entregas/…`. Run on any day after the freeze, that directory does not
    exist, every source reads as unreadable, and a delivery that had nine confirmed claims reports
    zero — with the build still green. So the date must come from where the bytes actually are.

    It is read from the FROZEN DIRECTORIES and not from `dados/registo.json`, which was the first
    attempt and was wrong twice over: the register is rewritten by `build/extract.py`, which this
    script SKIPS unless `--fetch` was asked for, so it can be days stale; and even on a `--fetch`
    run it is rewritten after this value would have been read. A freshly frozen delivery was
    therefore checked against the previous capture's directory, found nothing, and reported 0 of 4
    sources readable while every gate stayed green.

    Called at the moment the step runs, never at import, for the same reason.
    """
    base = ROOT / "fontes" / "congeladas"
    if not base.exists():
        return None
    datas = sorted(d.name for d in base.iterdir()
                   if d.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.name)
                   and (d / "entregas").is_dir())
    return datas[-1] if datas else None

# (command, what it does, is-a-gate). The order is the order.
PASSOS = [
    (["python3", "build/extract.py"],
     "fetch, freeze, hash, register, extract, diff", False),
    (["python3", "build/transferencias.py"],
     "evidence transferred from a sibling publication — verified, kept as ITS evidence", False),
    (["python3", "build/entregas.py", "--date", "@DATA@"],
     "research deliveries: validate, re-check every excerpt against the frozen bytes, and fold in "
     "the editor's decisions from redacao/revisoes/ — MUST run before anything that reads "
     "dados/entregas.json, which is build.py (the /entregas/ pages) and gate 13 (the quarantine). "
     "Without this step an approval written by the editor never reaches the build, and the gate "
     "goes on believing nothing was approved", False),
    (["python3", "build/graph.py"],
     "ontology, graph, triples, manifest — including the source-publisher layer", False),
    (["python3", "build/entidades.py"],
     "dados/entidades.json e uma página por entidade — TEM de vir antes de tudo o que gera "
     "páginas, porque é este ficheiro que faz uma menção virar ligação", False),
    (["python3", "build/backoffice_team.py"],
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
    (["python3", "build/guia.py"],
     "docs/guidance/*.md becomes a page with an address — after backoffice.py, whose page "
     "scaffolding it uses, and before chrome.py, which puts the pages in the sitemap", False),
    (["python3", "build/mandatos.py"],
     "agents/<id>/ROLE.md and MANDATE.md, rendered from the register — never hand-written", False),
    (["python3", "build/backoffice_design.py"],
     "the design-review page: each item, and whether it is done, deferred or the editor's", False),
    (["python3", "build/backoffice_bridges.py"],
     "the bridges page: how the editor reaches the back office from the browser", False),
    (["python3", "build/versoes.py"],
     "admin/versions.html, rendered from admin/versions/*.md — text does not live inside HTML",
     False),
    (["python3", "build/chrome.py"],
     "llms.txt, sitemap.xml, index.md — the surface a machine reads", False),
    (["python3", "build/gates.py"],
     "the core gates (1-15), in the deny-listed file", True),
    (["python3", "build/gates_artigos.py"],
     "articles, sections, back office, entities, comments, runs, language, agents (16-26, 34-35)",
     True),
    (["python3", "build/gates_desenho.py"],
     "the design gates (27-33, 39): contrast, measure, leading, the mono face, focus, empty "
     "columns, the accents of the state vocabulary, and the console's legacy layer held to a "
     "ratchet — the numbers the design review measured", True),
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



def prontidao_para_lancar():
    """Would CI tag this commit? Checked here, because CI checks it AFTER the build is green.

    THE FAILURE THIS PREVENTS, which happened on v0.12.0. `validate` passed, all five gates were
    green, the push went to `dev` — and `tag-release` failed with:

        version.txt says v0.12.0 but the newest release commit in this history is v0.11.0

    CI does not read `version.txt` alone. It reads the newest commit SUBJECT matching
    `^site vX.Y.Z:` and requires the two to agree, because the subject is what names the release
    commit to tag. The v0.12.0 work went in under a merge subject — "integra o dev (v0.11.0) e
    renumera para v0.12.0" — which carries the number but not in the form CI parses. So nothing
    was tagged, `deploy` was skipped, and the live site stayed on the previous release while every
    local gate said OK. A green build that does not deploy is the worst kind of green.

    This is a WARNING and not a gate, deliberately. On a feature branch `version.txt` is
    legitimately ahead of the newest release subject for as long as the work is unfinished — that
    is the normal state, not an error. Making it a gate would fail every intermediate build and
    teach whoever hit it to skip gates, which costs more than it saves.
    """
    import re
    import subprocess as sp
    try:
        versao = (ROOT / "admin" / "build" / "version.txt").read_text(encoding="utf-8").strip()
        log = sp.run(["git", "log", "--pretty=%s", "-n", "200"], cwd=ROOT,
                     capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return
    assuntos = re.findall(r"^site (v[0-9]+\.[0-9]+\.[0-9]+):", log, re.M)
    mais_novo = assuntos[0] if assuntos else None
    if mais_novo == versao:
        print(f"\n\033[32mready to release\033[0m — version.txt and the newest release subject "
              f"both say {versao}; CI will tag and deploy this commit.")
        return
    print(f"\n\033[33mNOT ready to release.\033[0m version.txt says \033[1m{versao}\033[0m and "
          f"the newest \033[1m«site vX.Y.Z:»\033[0m commit subject says "
          f"\033[1m{mais_novo or 'nothing'}\033[0m.")
    print("CI's tag-release job compares exactly these two and fails when they disagree — the "
          "build goes green, the push succeeds, and DEPLOY IS SKIPPED.")
    print(f"Before pushing to dev, the release commit's subject must be: "
          f"\033[1msite {versao}: <one sentence>\033[0m")


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

    # Resolved HERE, after extract.py has had its chance to run, and from the frozen directories
    # rather than from a file that a skipped step would have written.
    data = data_do_congelamento()
    passos = [([data if x == "@DATA@" else x for x in c], d, g) for c, d, g in passos]
    passos = [(c, d, g) for c, d, g in passos if "@DATA@" not in c and None not in c]

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
    # Counted, not written: a number typed into this line goes wrong on the day somebody adds a
    # gate, and that is the day the line is read most.
    n = sum(1 for _, _, g in passos if g)
    NOMES = {1: "one gate", 2: "two gates", 3: "three gates", 4: "four gates",
             5: "five gates", 6: "six gates"}
    quantos = NOMES.get(n, f"{n} gates")
    print(f"\n\033[32mtudo: OK\033[0m — built and checked by the {quantos}.")
    if not com_render:
        print("Without `--render`, no component was opened in a browser. If this change touched "
              "assets/components/, run `python3 build/tudo.py --render`.")
    print("Left, and the editor's: run \033[1mpython3 build/before_push.py\033[0m to see what "
          "another session\n  released while you worked, take the version number it says is "
          "free, write the note in\n  admin/versions/, bump admin/build/version.txt, re-run this "
          "command, and only then push.")
    prontidao_para_lancar()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

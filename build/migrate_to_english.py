#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — rename the backend vocabulary from Portuguese to English.

    python3 build/migrate_to_english.py              # dry run: says what it would do, changes nothing
    python3 build/migrate_to_english.py --apply      # does it
    python3 build/migrate_to_english.py --blockers   # just the list for the editor

WHY. The data layer has to be language-neutral so more than one language edition can share it. A
Portuguese key is fine while there is one edition and wrong the moment there are two, and this
publication intends more. What a reader SEES stays Portuguese — the article, the entity name, the
ontology's verbs, the URLs in the address bar. The vocabulary the machinery uses to talk about all
of that becomes English.

THE MAP IS `dados/en-migration.json`, AND IT IS DATA. This repository's own rule is that a
classification is a published formula or it does not happen, so the mapping is a published file
rather than a dictionary buried in this script. It also states what it does NOT touch, each with a
reason, which is the half of a rename that usually goes unwritten.

**THIS SCRIPT CANNOT FINISH ITS OWN JOB, AND SAYS SO RATHER THAN HALF-DOING IT.** `build/gates.py`
and `build/entregas.py` hardcode the backend folder names and 115 of the keys, and both are in the
deny list of `.claude/settings.json` — an agent that can edit the gate that stops it has no gate at
all. Renaming around them would turn the build permanently red through files no agent here may fix.
So `--apply` refuses while a blocker stands, prints exactly what the editor must change, and exits
non-zero. A run that stops honestly is a good run.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPA = ROOT / "dados" / "en-migration.json"

# Every file whose text mentions the vocabulary. Frozen evidence is excluded and that is not an
# oversight: `fontes/congeladas/**` is another organisation's bytes, its hash is re-verified on
# every build, and editing one would make every claim standing on it false.
ALVOS = [("dados", "*.json"), ("build", "*.py"), ("assets", "*.js"),
         ("admin/build", "*.mjs"), ("admin/build", "*.js"), ("admin", "*.json"),
         ("artigos", "*.json"), ("seccoes", "*.json"), ("redacao", "*.json"),
         ("api", "*.json"), ("agents", "*.md"), ("docs", "*.md"), (".claude", "*.md")]
EXCLUIR = re.compile(r"fontes/congeladas/|fontes/transferidas/|/vendor/|__pycache__")


def carregar():
    if not MAPA.exists():
        sys.exit(f"{MAPA.relative_to(ROOT)} is missing — the map is the input to this script")
    return json.loads(MAPA.read_text(encoding="utf-8"))


def ficheiros():
    for base, padrao in ALVOS:
        d = ROOT / base
        if not d.exists():
            continue
        for f in sorted(d.rglob(padrao)):
            if not EXCLUIR.search(f.as_posix()):
                yield f


def bloqueadores(doc):
    """Recomputed from the files, never trusted from the map — the deny list can change, and a
    blocker list that is right only on the day it was written is the worst kind."""
    nomes = set()
    for rel in doc["bloqueado"]["ficheiros"]:
        f = ROOT / rel
        if not f.exists():
            continue
        texto = f.read_text(encoding="utf-8")
        for k in doc["mapa"]:
            if re.search(r"""['"]%s['"]""" % re.escape(k), texto):
                nomes.add((rel, k))
        for pasta in doc["pastas"]:
            if re.search(r"""['"]%s['"]|%s/""" % (re.escape(pasta), re.escape(pasta)), texto):
                nomes.add((rel, pasta + "/"))
    return sorted(nomes)


def relatorio_de_bloqueio(doc):
    b = bloqueadores(doc)
    por_ficheiro = {}
    for rel, k in b:
        por_ficheiro.setdefault(rel, []).append(k)
    print("\n\033[1mWhat the editor has to change before this can run\033[0m")
    print("These files are in the deny list of .claude/settings.json. No agent working in this")
    print("repository may edit them, and every one of them names the vocabulary below.\n")
    for rel, nomes in sorted(por_ficheiro.items()):
        print(f"  \033[1m{rel}\033[0m — {len(nomes)} name(s)")
        print("      " + ", ".join(sorted(nomes)[:14]) + ("…" if len(nomes) > 14 else ""))
    print("\nTwo ways to unblock, and they are the editor's to choose between:")
    print("  1. Make the changes in those files by hand, from dados/en-migration.json, and run")
    print("     this script with --apply.")
    print("  2. Lift the deny-list entries for the duration of the migration, run it, put them")
    print("     back. An agent must not do this for itself: CLAUDE.md forbids a run widening its")
    print("     own permissions, and that rule is the reason the deny list is worth anything.")
    return b


def aplicar(doc, a_serio):
    mapa = doc["mapa"]
    # Longest first: `publicado_em` has to be rewritten before `publicado`, or the prefix wins and
    # leaves `published_em` behind. Ordering is the whole correctness of a bulk rename.
    chaves = sorted(mapa, key=len, reverse=True)
    padrao = re.compile(r"""(['"])(%s)\1""" % "|".join(re.escape(k) for k in chaves))

    # A SECOND PATTERN, FOR PATHS. The first matches a quoted string that IS a name — `"dados"`.
    # It does not match `"dados/historias.json"`, `"fontes/congeladas/"` or an f-string like
    # `"seccoes/{sid}/seccao.json"`, and those are most of how a folder is actually referred to in
    # this codebase. The scratch run died on the first of them, which is the whole argument for
    # having done a scratch run.
    # Longest first, so `fontes/congeladas` is tried before `fontes` — otherwise the shorter one
    # wins and leaves `sources/congeladas`, a folder that exists under neither name.
    #
    # The lookahead is `[/'"]` and not `/`, which is three cases in one: a quoted string that IS
    # the folder (`"dados"`), one that is a path under it (`"dados/historias.json"`), and one that
    # is a nested folder with no trailing slash (`"fontes/congeladas"`). The first and third were
    # both missed by an earlier version, and both killed the scratch run — the first on
    # `DADOS = ROOT / "dados"`, which is how every builder here finds the folder at all.
    pastas = sorted(doc["pastas"], key=len, reverse=True)
    padrao_caminho = re.compile(
        r"""(?<=['"])(%s)(?=[/'"])""" % "|".join(re.escape(x) for x in pastas))

    def _caminho(m):
        return doc["pastas"][m.group(1)]

    tocados, substituicoes = 0, 0
    for f in ficheiros():
        texto = f.read_text(encoding="utf-8")
        novo, n = padrao.subn(lambda m: f"{m.group(1)}{mapa[m.group(2)]}{m.group(1)}", texto)
        novo, n2 = padrao_caminho.subn(_caminho, novo)
        n += n2
        if n:
            tocados += 1
            substituicoes += n
            if a_serio:
                f.write_text(novo, encoding="utf-8")

    # SHORTEST PATH FIRST, and each source path rewritten through the moves already made.
    #
    # Longest-first is the obvious order and it is wrong: renaming `fontes/congeladas` first
    # CREATES `sources/`, and the later `fontes → sources` is then skipped because the target
    # exists — leaving an empty `fontes/` behind and the move half-done. Proved by running this
    # in a scratch clone, which is the only reason it is right now.
    #
    # Parent-first needs the second half: once `fontes` is `sources`, the child to rename is
    # `sources/congeladas`, not `fontes/congeladas`. So every source path is pushed through the
    # renames already applied before it is used.
    movidas, feitas = [], []

    def ja_movido(caminho):
        for antiga, nova in feitas:
            if caminho == antiga or caminho.startswith(antiga + "/"):
                return nova + caminho[len(antiga):]
        return caminho

    for antiga, nova in sorted(doc["pastas"].items(), key=lambda kv: len(kv[0])):
        origem = ja_movido(antiga)
        if not (ROOT / origem).exists() or (ROOT / nova).exists():
            continue
        movidas.append((origem, nova))
        feitas.append((antiga, nova))
        if a_serio:
            (ROOT / nova).parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "mv", origem, nova], cwd=ROOT, check=True)

    verbo = "renamed" if a_serio else "would rename"
    print(f"\n{verbo} {substituicoes} quoted name(s) across {tocados} file(s)")
    print(f"{verbo} {len(movidas)} folder(s): " +
          ", ".join(f"{a} → {b}" for a, b in movidas) if movidas else "no folder to move")
    if not a_serio:
        print("\n\033[33mDry run. Nothing was written.\033[0m Re-run with --apply once the "
              "blockers above are gone,\nthen `python3 build/tudo.py --render` — all five gates "
              "have to be green before this is a release.")


def main(argv):
    doc = carregar()
    print(f"\033[1mmigrate_to_english\033[0m — {doc['contagem']} keys, "
          f"{len(doc['pastas'])} folders, from dados/en-migration.json")

    b = relatorio_de_bloqueio(doc)
    if "--blockers" in argv:
        return 1 if b else 0

    if "--apply" in argv and b:
        print("\n\033[31mREFUSED.\033[0m A blocker still stands, and renaming around it turns the "
              "build permanently\nred through files this session may not fix. Nothing was written.")
        return 1

    aplicar(doc, a_serio="--apply" in argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

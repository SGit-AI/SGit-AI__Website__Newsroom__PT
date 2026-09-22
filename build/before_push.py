#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — what another session did while you were working.

    python3 build/before_push.py            # read-only; run it before you choose a version
    python3 build/before_push.py --no-fetch # skip the network, use what is already fetched

WHY THIS EXISTS. Three sessions work on this repository at once, and the gates cannot see any of
them: a gate reads the working tree, and the working tree is one session's opinion. Everything that
has actually gone wrong between sessions here went wrong in the gap between «my branch is green»
and «my push is accepted» — two sessions taking v0.13.0 within the hour, two starting their gates
at 27, two building the agent register the same afternoon.

This command closes that gap by asking the one question a gate cannot: **what is on the release
branch that is not in my hand?** It changes nothing, writes nothing and pushes nothing. It fetches
and it reports.

THE PART THAT MATTERS IS THE LAST SECTION. A conflict is the good case: git stops, you look, you
resolve. The bad case is the merge that SUCCEEDS and still loses your work — a file both sides
edited, where one side rewrote it wholesale and git took that side without a word. That is how four
CSS rules giving `<pt-chat>` its column disappeared while every gate stayed green. So this prints
the list of source files both sides have touched, and tells you to read your own lines in them
after you merge. It cannot check them for you. It can stop the loss from being invisible.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAMO = "dev"

# Generated files are excluded from the overwrite list. They are the overwhelming majority of any
# conflict here — one merge produced 245 of them — and not one is worth a human's attention: the
# rule in this repository is that a generated file is resolved by rebuilding, never by hand. Listing
# them would bury the handful of source files that actually need reading.
GERADO = re.compile(r"""
      \.html$ | ^api/ | ^dados/ | ^entidades/ | ^artigos/.*/index\.html$
    | ^llms\.txt$ | ^sitemap\.xml$ | ^index\.md$ | ^agents/.*\.md$
    | ^admin/versions\.html$ | ^ficheiros/
""", re.X)


def git(*args, falha_ok=False):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)
    if r.returncode and not falha_ok:
        return None
    return r.stdout.strip()


def versao_de(ref, caminho):
    return git("show", f"{ref}:{caminho}", falha_ok=True)


def como_numero(v):
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except (ValueError, AttributeError):
        return (0,)


def numeros_de_portao(texto_por_ficheiro):
    """The same tolerant scan gate 36 uses, over a ref rather than over the disk."""
    padroes = [re.compile(r"^\s{0,4}(\d{1,3})\s+·"),
               re.compile(r"^#\s{0,4}(\d{1,3})\s+·"),
               re.compile(r"^#\s*-+\s*(\d{1,3})\.\s")]
    vistos = set()
    for texto in texto_por_ficheiro:
        for linha in (texto or "").split("\n"):
            for p in padroes:
                m = p.match(linha)
                if m and 1 <= int(m.group(1)) <= 200:
                    vistos.add(int(m.group(1)))
    return vistos


def main(argv):
    if "--no-fetch" not in argv:
        print(f"→ git fetch origin {RAMO}")
        if git("fetch", "origin", RAMO) is None:
            print("  could not fetch — reporting against whatever was fetched last")
    remoto = f"origin/{RAMO}"
    if git("rev-parse", "--verify", remoto, falha_ok=True) is None:
        print(f"{remoto} is not there. Nothing to compare against.")
        return 1

    base = git("merge-base", "HEAD", remoto)
    atras = git("rev-list", "--count", f"HEAD..{remoto}") or "0"
    frente = git("rev-list", "--count", f"{remoto}..HEAD") or "0"

    print(f"\n\033[1mWhere you are\033[0m")
    print(f"  your branch is {frente} commit(s) ahead of {remoto} and {atras} behind")
    if atras == "0":
        print("  nothing arrived while you worked — the rest of this is a formality")

    # ---- the version number, which is a shared counter with no lock -------------------------
    minha = (ROOT / "admin" / "build" / "version.txt").read_text(encoding="utf-8").strip()
    deles = versao_de(remoto, "admin/build/version.txt") or "?"
    print(f"\n\033[1mThe release number\033[0m")
    print(f"  on {remoto}: {deles}")
    print(f"  in your tree: {minha}")
    if como_numero(minha) <= como_numero(deles):
        # THE MINOR IS THE THIRD COMPONENT. This line used to advise `v{a}.{b+1}.0` — the second
        # component — and that is a major release. CLAUDE.md says every push to `dev` is a MINOR
        # release, and the tag job in .github/workflows/deploy-pages.yml computes NEXT_MINOR from
        # the third component and REJECTS a tag that is neither that nor NEXT_MAJOR. So the advice
        # this file gave sent a session to write a release note under a number CI would refuse,
        # which is a failure discovered after the note is written and the tree is green.
        a, b, c = como_numero(deles)[:3] if len(como_numero(deles)) >= 3 else (0, 0, 0)
        print(f"  \033[31mTAKEN.\033[0m {deles} is already released. Take "
              f"\033[1mv{a}.{b}.{c + 1}\033[0m — the minor is the THIRD component and a push to "
              f"dev is a minor release. Rename your note in admin/versions/, fix "
              f"admin/versions.json, and re-run build/tudo.py.")
        print(f"  (v{a}.{b + 1}.0 is the MAJOR, and CI accepts it only when the release really is "
              f"one. See docs/guidance/releasing.md.)")
    else:
        print("  \033[32mfree\033[0m — nobody has published this number")

    # ---- gate numbers, the other shared counter ---------------------------------------------
    ficheiros = [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "build").glob("gates*.py"))]
    seus = numeros_de_portao(versao_de(remoto, f) for f in ficheiros)
    meus = numeros_de_portao((ROOT / f).read_text(encoding="utf-8") for f in ficheiros)
    print(f"\n\033[1mGate numbers\033[0m")
    print(f"  highest on {remoto}: {max(seus) if seus else '—'} · highest in your tree: "
          f"{max(meus) if meus else '—'}")
    choque = sorted(n for n in (meus - seus) if n in seus)
    novos_deles = sorted(seus - meus)
    if novos_deles:
        print(f"  they added {', '.join(map(str, novos_deles))} while you worked")
    if choque:
        print(f"  \033[31mCOLLISION.\033[0m You and they both number {choque}.")
    else:
        proximo = max(seus | meus) + 1 if (seus | meus) else 1
        print(f"  next free after a merge: \033[32m{proximo}\033[0m")

    # ---- the silent one ----------------------------------------------------------------------
    #
    # This section was written wrong first, and the wrong version is worth recording because it is
    # the obvious one. It listed files BOTH sides had changed since the merge base, on the theory
    # that those are where a clean auto-merge can lose work. Checked against the merge that
    # actually lost work — the one that took `assets/site.css` and with it the four rules giving
    # `<pt-chat>` its column — that list did not contain site.css at all. The rules had been added
    # two releases earlier, so they were already IN the merge base: only their side had touched the
    # file since. The heuristic could not have caught the thing it was named after.
    #
    # What does catch it is churn. Their rewrite changed 897 lines of a 411-line file; the next
    # busiest source file on the same range changed 31% of itself. A wholesale rewrite is the
    # danger, whoever has edited it recently, because everything of yours that was in that file
    # goes with it and git reports nothing at all.
    meus_f = set((git("diff", "--name-only", f"{base}..HEAD") or "").split("\n")) - {""}
    seus_f = set((git("diff", "--name-only", f"{base}..{remoto}") or "").split("\n")) - {""}
    fonte = lambda ns: sorted(f for f in ns if not GERADO.search(f))

    reescritos = []
    for f in fonte(seus_f):
        antes_txt = versao_de(base, f)
        if antes_txt is None:
            continue                      # a new file of theirs takes nothing of yours with it
        n = len(antes_txt.split("\n")) or 1
        # A floor, because percentage alone is useless on a small file: `version.txt` is one line
        # and every release changes 200% of it. Below thirty lines a rewrite cannot hide anything
        # you would need a tool to notice.
        if n < 30:
            continue
        linha = git("diff", "--numstat", f"{base}..{remoto}", "--", f) or ""
        campos = linha.split("\t")
        if len(campos) < 2 or not campos[0].isdigit():
            continue
        mudadas = int(campos[0]) + int(campos[1])
        if mudadas * 100 // n >= 60:
            reescritos.append((f, n, mudadas, mudadas * 100 // n))

    ambos = fonte(meus_f & seus_f)

    print(f"\n\033[1mSource files they rewrote wholesale\033[0m")
    if not reescritos:
        print("  none.")
    else:
        for f, n, mudadas, pct in sorted(reescritos, key=lambda x: -x[3]):
            print(f"  · {f}  ({n} lines, {mudadas} changed — {pct}%)")
        print(f"\n  \033[33mAfter you merge, grep each of these for anything of yours.\033[0m A "
              f"wholesale rewrite\n  takes the whole file — including work you landed releases ago "
              f"— with no conflict\n  and no warning. That is exactly how the chat's column rules "
              f"vanished while every\n  gate stayed green. Gate 37 now catches that particular "
              f"coupling; nothing catches\n  the general case except reading.")

    print(f"\n\033[1mSource files you have both changed\033[0m")
    print("  " + ("none" if not ambos else "\n  ".join("· " + f for f in ambos))
          + ("" if not ambos else "\n  These will conflict, and git will stop. That is the good "
                                  "case."))

    gerados = len([f for f in (meus_f & seus_f) if GERADO.search(f)])
    print(f"\n{len(reescritos)} rewrite(s) to grep, {len(ambos)} conflict(s) to resolve by hand, "
          f"{gerados} generated file(s) to resolve by re-running build/tudo.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

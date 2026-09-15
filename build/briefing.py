#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — what a session is told the moment it starts.

    python3 build/briefing.py      # run by the SessionStart hook in .claude/settings.json

WHY THIS EXISTS. `.claude/ONBOARDING.md` is the briefing, and a briefing nobody reads is decoration
— the same objection this repository makes to a rule with no gate. Claude Code loads `CLAUDE.md`
automatically and nothing else, so a second file at the root of `.claude/` is read only if the
session happens to look. The SessionStart hook is the one mechanism that reaches every session
without being asked, so this prints the short version and says where the long one is.

IT DOES NOT TOUCH THE NETWORK, and that is deliberate rather than lazy. A hook runs before the
session can be told anything, on a timeout, and a `git fetch` that hangs would turn a briefing into
a delay. The live question — what have the other sessions released while I was away — is
`build/before_push.py`, which this points at and which the session runs when it is ready to.

Everything printed here is read off disk. Nothing is typed into this file: the version comes from
version.txt, the gate number from the gate files, the agents from the register. A briefing with a
number typed into it goes stale on the day it matters most.
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
N = "\033[0m"
B = "\033[1m"
V = "\033[32m"
A = "\033[33m"


def numeros_de_portao():
    padroes = [re.compile(r"^\s{0,4}(\d{1,3})\s+·"),
               re.compile(r"^#\s{0,4}(\d{1,3})\s+·"),
               re.compile(r"^#\s*-+\s*(\d{1,3})\.\s")]
    vistos = set()
    for f in sorted((ROOT / "build").glob("gates*.py")):
        for linha in f.read_text(encoding="utf-8").split("\n"):
            for p in padroes:
                m = p.match(linha)
                if m and 1 <= int(m.group(1)) <= 200:
                    vistos.add(int(m.group(1)))
    return vistos


def ler(caminho, omissao=""):
    f = ROOT / caminho
    return f.read_text(encoding="utf-8").strip() if f.exists() else omissao


def main():
    versao = ler("admin/build/version.txt", "?")
    portoes = numeros_de_portao()
    proximo = (max(portoes) + 1) if portoes else 1

    ramo = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip() or "?"

    reg = ROOT / "dados" / "agentes.json"
    agentes = []
    if reg.exists():
        try:
            agentes = [a.get("id", "") for a in json.loads(
                reg.read_text(encoding="utf-8")).get("agentes", [])]
        except json.JSONDecodeError:
            pass

    runs = sorted((ROOT / "redacao" / "runs").glob("*.json")) \
        if (ROOT / "redacao" / "runs").exists() else []
    ultima = ""
    if runs:
        try:
            r = json.loads(runs[-1].read_text(encoding="utf-8"))
            ultima = f'{r.get("agente", "?")} · {r.get("versao", "?")} · {r.get("quando", "?")}'
        except json.JSONDecodeError:
            ultima = runs[-1].name

    print(f"""
{B}pt.newsroom.sgit.ai{N} — released {B}{versao}{N} · branch {B}{ramo}{N} · gates up to \
{max(portoes) if portoes else '—'} (next free: {V}{proximo}{N})
last run recorded: {ultima or 'none'}

{B}Read {A}.claude/ONBOARDING.md{N}{B} first.{N} The long form is docs/guidance/, published at
/newsroom/guidance/index.html. CLAUDE.md is the constitution and outranks both.

  · Would a visitor read this string on the site? Yes → Portuguese. No → English.
  · {B}Two or three sessions work here at once.{N} Run {A}python3 build/before_push.py{N} before you
    take a version number — and take it {B}last{N}, not first.
  · {A}python3 build/tudo.py{N} builds and runs every gate. Never run the steps by hand.
    Add {A}--render{N} if you touched assets/components/.
  · A rule without a gate is decoration. Add the gate in the same change, then break it
    on purpose and watch it go red.
  · Only the human editor of record sets {B}estado: publicado{N}. Never a run.

agents you may claim: {', '.join(agentes) or '(register empty)'}
""")


if __name__ == "__main__":
    main()

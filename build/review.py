#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — what is waiting on the editor of record, as questions he can answer.

    python3 build/review.py     # after mesa.py, before build.py

THE ASK. The editor comes back after a day away and has to reconstruct, from six places, what
happened and what is now his to decide: the release notes, the delivery pages, the board, the mail,
the review files, and the articles. Every one of those is honest and none of them is a briefing.

WHAT THIS FILE DOES. It gathers the open questions — and ONLY the questions whose answer is the
editor's to give — and writes them to `dados/review.json` as a flat list, each with the file that
answer has to end up in and the agent that will put it there. `build/build.py` renders the page;
`assets/components/pt-decisions/` captures the answers in the browser.

WHAT IT REFUSES TO DO. It does not decide, it does not pre-fill a verdict, and it does not treat
silence as an answer. An item with no decision stays open, which is what the quarantine gate already
enforces — so the safe state and the default state are the same state, deliberately.

AND IT INVENTS NO DATES. "Since your last review" is not computed here, because this build has no
idea when the editor last read anything. What it can say is when each thing happened; which of those
he has already seen is knowledge that lives in his browser, and that is where the page keeps it.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dados"
ISSUES = ROOT / "redacao" / "issues"


def load(name, fallback=None):
    f = DATA / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else fallback


def questions_from_deliveries(deliveries):
    """One question per research item the editor has not yet answered.

    An item whose claims ALL failed the byte check is still listed, and listed as its own kind of
    question: the skill forbids approving it — there is nothing to stand on — but rejecting it would
    say the newsroom does not want the lead, which is usually false. The honest third answer is to
    leave it open and commission research, so the question says so rather than offering two buttons
    that are both wrong.
    """
    out = []
    for d in (deliveries or {}).get("entregas", []):
        decided = (d.get("revisao") or {}).get("itens") or {}
        for item in d["itens"]:
            if item["id"] in decided:
                continue
            confirmed = [c for c in item["afirmacoes"] if c["estado"] == "confirmada"]
            total = len(item["afirmacoes"])
            out.append({
                "id": f'{d["id"]}/{item["id"]}',
                "kind": "delivery",
                "for_agent": "the /newsroom-entregas session",
                "file": f'redacao/revisoes/{d["id"]}.json',
                "question": item["titulo"],
                "delivery_id": d["id"],
                "item_id": item["id"],
                "section": item["seccao"],
                "confirmed": len(confirmed),
                "claims": total,
                "without_bytes": total - len(confirmed),
                "why_it_matters": item.get("porque_importa") or "",
                "confirmed_claims": [c["texto"] for c in confirmed],
                "url": f'../../entregas/{d["id"]}.html#{item["id"]}',
            })
    return out


def questions_from_issues():
    """Issues the board says are blocked on a person rather than on work."""
    out = []
    for f in sorted(ISSUES.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("estado") != "bloqueado":
            continue
        out.append({
            "id": f'issue-{d["id"]}',
            "kind": "issue",
            "for_agent": "whoever the editor authorises",
            "file": f"redacao/issues/{f.name}",
            "question": d["titulo"],
            "section": d.get("seccao", "—"),
            "why_it_matters": d.get("porque_esta_bloqueado") or d.get("enquadramento", ""),
            "what_is_missing": d.get("o_que_falta", []),
            "url": "../../redacao/",
        })
    return out


def questions_from_vocabulary(deliveries):
    """Entity types a delivery proposed that the ontology does not have.

    Grouped into ONE question and not one per type, because that is how it is decided: adding a type
    is an ontology change, it takes a version, and nobody accepts three of them separately.
    """
    proposed = {}
    for d in (deliveries or {}).get("entregas", []):
        for err in d.get("erros_de_esquema", []):
            if "/type:" in err and "is not one of" in err and "'" in err:
                proposed.setdefault(err.split("'")[1], set()).add(d["id"])
    if not proposed:
        return []
    return [{
        "id": "ontology-new-types",
        "kind": "ontology",
        "for_agent": "the session that touches the ontology",
        "file": "dados/ontologia.json",
        "question": "Accept into the ontology the entity types the deliveries proposed?",
        "section": "—",
        "why_it_matters": ("A type accepted in a hurry to publish one article is a type that stays. "
                           "None of the articles published so far needed these: they are proposals, "
                           "not blockers."),
        "types": sorted(proposed),
        "url": "../../entregas/",
    }]


def main():
    deliveries = load("entregas.json")
    stories = load("historias.json", {"historias": []})
    releases = json.loads((ROOT / "admin" / "versions.json").read_text(encoding="utf-8"))

    questions = (questions_from_deliveries(deliveries)
                 + questions_from_issues()
                 + questions_from_vocabulary(deliveries))

    # WHAT HAPPENED. Every entry carries its own date or version so the page can say when, and the
    # browser can work out which of them this editor has already seen.
    changes = []
    for r in releases["versoes"][:8]:
        changes.append({"kind": "release", "when": r["data"], "version": r["versao"],
                        "what": r["titulo"],
                        "url": f'../../admin/versions.html#{r["versao"]}'})
    for s in stories["historias"]:
        if s["estado"] == "publicado":
            changes.append({"kind": "article", "when": s.get("publicado_em") or s["data"],
                            "version": "", "what": s["titulo"], "url": f'../../{s["url"]}'})
    for d in (deliveries or {}).get("entregas", []):
        c = d["contagens"]
        changes.append({
            "kind": "delivery", "when": d["data"], "version": "",
            "what": (f'{d["ferramenta"]} delivery · {c["itens"]} items, '
                     f'{c["confirmadas"]} of {c["afirmacoes"]} claims found in the bytes'),
            "url": f'../../entregas/{d["id"]}.html'})
    changes.sort(key=lambda m: (m["when"], m["version"]), reverse=True)

    doc = {
        "id": "pt-review",
        "version": "1.0.0",
        "updated": max([c["when"] for c in changes] or ["—"]),
        "what_it_is": ("The questions whose answer is the editor of record's, and what has changed "
                       "since the others were answered. Nothing here decides anything: a decision "
                       "is a file in the repository, written by a person, and this page only helps "
                       "write it."),
        "the_rule": ("A question with no verdict stays open, which is the safe state and what gate "
                     "13 already enforces. Silence is never a yes."),
        "count": len(questions),
        "questions": questions,
        "changes": changes,
    }
    (DATA / "review.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    by_kind = {}
    for q in questions:
        by_kind[q["kind"]] = by_kind.get(q["kind"], 0) + 1
    print(f'review: {len(questions)} questions for the editor '
          f'({", ".join(f"{v} {k}" for k, v in sorted(by_kind.items())) or "none"}), '
          f'{len(changes)} changes listed')


if __name__ == "__main__":
    main()

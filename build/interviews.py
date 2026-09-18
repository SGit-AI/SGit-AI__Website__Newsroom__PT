#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the interview method, and the prompts that do the work.

    python3 build/interviews.py    # after review.py, before build.py

TWO PACKS, AND THE DIRECTION IS THE DIFFERENCE. `briefs/pack/09__interviews/` points OUTWARD: an
assistant interviews somebody outside the newsroom and what comes back is raw material for an
article. `briefs/pack/10__editor-interview/` points INWARD: an agent has ChatGPT interview the
editor of record and what comes back is direction — what to work on, what to drop, what he thinks
matters. Same mechanism, opposite direction, and the second is the reason the first has anything to
do.

WHY THE PAGE RENDERS THE PROMPTS INSTEAD OF LINKING THEM. The research briefs are LINKED and not
republished, because they are read once by whoever runs a research pass. These are different: a
prompt is copied, by a person about to paste it into ChatGPT, often on a phone. A page that sends
them to a raw markdown file to select-all is a page that loses them.

So the page is a SECOND VIEW of one copy, never a second copy. The markdown is the source, this file
renders it, and gate 42 fails the build if the two ever disagree. If the HTML and the markdown could
drift, the design would be wrong.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dados"

# The order within each pack is the order a person meets them, not alphabetical.
PACKS = [
    ("09__interviews", "Interviewing somebody, to write",
     "A busy person will not write two pages about their work. They will talk about it for twenty "
     "minutes, at an hour that suits them, by voice or by typing.",
     [("01__interview-prompt.pt.md", "The interview prompt", "português",
       "Pasted into ChatGPT as the first message. Always the same, whoever the person is.",
       "the interviewee"),
      ("02__the-interview-prompt.en.md", "The interview prompt", "english",
       "The same interviewer, in English. The interview may be in either language; what gets "
       "published is always European Portuguese.", "the interviewee"),
      ("03__topic-block.md", "The topic block", "português",
       "The second message, and the only part that changes from interview to interview. An "
       "interview is worth whatever this block is worth.", "the agent"),
      ("04__agent-prompt.md", "The agent prompt", "english",
       "What the editor hands an agent session to prepare a pack. The agent assembles; it does not "
       "interview.", "the editor")]),
    ("11__startup-interviews", "Interviewing a founder yourself, at an event",
     "Five minutes, standing, in a hall with a PA system. Four fixed questions asked identically "
     "to everybody — which is what turns twenty conversations into something you can count — and a "
     "short pool of follow-ups picked by what they just said.",
     [("01__the-questions.en.md", "The question card", "english",
       "What you actually hold at the event. The four fixed questions, the follow-up pool, the "
       "closing question, and the thirty seconds before you walk away.", "you"),
      ("02__as-perguntas.pt.md", "O cartão das perguntas", "português",
       "The same card, for founders who would rather speak Portuguese.", "you"),
      ("03__from-recording-to-article.md", "From a recording to an article", "english",
       "Transcript, the split between what they said about themselves and what they said about the "
       "world, and the language rule for content born in English and published in Portuguese.",
       "the agent")]),
    ("10__editor-interview", "Interviewing the editor, to know what to do",
     "An agent knows what is in front of it and does not know what the editor thinks matters. "
     "Twenty minutes gets that out, and gets it out better than any form.",
     [("01__preparation-prompt.md", "The preparation prompt", "english",
       "The agent reads its own mandate, its issues and what went wrong, and writes the state "
       "block. Without this the conversation is generic and worth nobody's time.", "the agent"),
      ("02__interview-prompt.pt.md", "The editor interview prompt", "português",
       "The interviewer. Walks the editor through the agent's questions, each with the agent's own "
       "proposal.", "the editor"),
      ("03__the-interview-prompt.en.md", "The editor interview prompt", "english",
       "The same, in English.", "the editor"),
      ("04__what-comes-back.md", "What comes back, and what is done with it", "english",
       "Decisions become files; ideas open an issue and wait. Confusing the two is how an agent "
       "does work nobody asked for.", "the agent")]),
]


def main():
    packs = []
    for folder, title, why, pieces_def in PACKS:
        source_dir = ROOT / "briefs" / "pack" / folder
        pieces = []
        for filename, piece_title, language, piece_why, for_whom in pieces_def:
            path = source_dir / filename
            if not path.exists():
                raise SystemExit(f"interviews: missing {path.relative_to(ROOT)}")
            text = path.read_text(encoding="utf-8")
            pieces.append({
                "file": filename,
                "path": f"briefs/pack/{folder}/{filename}",
                "title": piece_title,
                "language": language,
                "why": piece_why,
                "for_whom": for_whom,
                "lines": len(text.split("\n")),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "text": text,
            })
        packs.append({
            "folder": folder,
            "id": folder.split("__", 1)[1],
            "title": title,
            "why": why,
            "readme": (source_dir / "README.md").read_text(encoding="utf-8"),
            "pieces": pieces,
        })

    doc = {
        "id": "pt-interviews",
        "version": "2.0.0",
        "what_it_is": ("Two interviews and one mechanism. One points outward — an assistant "
                       "interviews somebody, and what comes back is material for an article. The "
                       "other points inward — an agent has ChatGPT interview the editor of record, "
                       "and what comes back is direction."),
        "the_rule": ("An interview is a primary source about the person speaking and nothing else. "
                     "What they assert about the world is a claim to verify, not a fact for having "
                     "been said aloud — and that holds when the person speaking is the editor."),
        "derived_from": "briefs/pack/09__interviews/ and briefs/pack/10__editor-interview/",
        "count": sum(len(p["pieces"]) for p in packs),
        "packs": packs,
        "pieces": [pc for p in packs for pc in p["pieces"]],
    }
    (DATA / "interviews.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f'interviews: {len(packs)} packs, {doc["count"]} pieces, '
          f'{sum(p["lines"] for p in doc["pieces"])} lines in total')


if __name__ == "__main__":
    main()

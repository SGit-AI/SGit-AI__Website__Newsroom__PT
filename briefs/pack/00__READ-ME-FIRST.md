# Briefing pack: build and run `pt.newsroom.sgit.ai`

**For the Claude Code session that has commit access to the repository which deploys to
`pt.newsroom.sgit.ai`.** Assembled 14 September 2026 from newsroom.sgit.ai v0.3.9 by the session
that built the Portugal Startups section, the no-server databases and the home-page design. CC BY 4.0.

You are being asked to do two things, in this order:

1. **Build the first MVP of the site** — a natively Portuguese newsroom mapping Portugal's AI
   landscape as a graph, whose front page looks like
   [newsroom.sgit.ai/pt-newsroom/index.html](https://newsroom.sgit.ai/pt-newsroom/index.html)
   and whose method is the one that already runs at
   [newsroom.sgit.ai/portugal/](https://newsroom.sgit.ai/portugal/index.html): every source
   fetched, frozen and hashed before it is cited; every claim walkable back to bytes; a named human
   editor of record; a data-protection notice; gates that fail the build.
2. **Set up the newsroom that keeps it alive** — the folders, prompts, skills and schedule that let
   a Claude session run on a timer and research, report, verify, build and publish updates, with the
   human editor as the gate on anything that goes live.

## Read in this order

| # | File | Why |
|---|---|---|
| 1 | `01__the-brief.md` | The commissioning brief. Everything else in the pack serves it. Sections 1, 3, 5, 6, 11 and 16 are the ones you will re-read |
| 2 | `02__the-design/README.md` | The design system of the chosen front page, and the sources that render it exactly |
| 3 | `03__inherit/README.md` | What to copy from newsroom.sgit.ai and what to rewrite — file by file |
| 4 | `04__the-newsroom/README.md` | The operating model: three departments, files as the communication layer, the run loop, the human gate |
| 5 | `04__the-newsroom/CLAUDE.md` | The rules file for the new repository. Copy it to the root before anything else |
| 6 | `04__the-newsroom/prompts/00-bootstrap.md` | Your first task, step by step |
| 7 | `05__schedule/README.md` | How the scheduled run is wired, and the three mechanisms it can run on |
| 8 | `06__acceptance.md` | What "done" means for MVP v0.1.0, and the one-story acceptance test |
| 9 | `07__handover.md` | What exists on newsroom.sgit.ai, where, and the decisions already taken |
| 10 | `08__research-briefs/README.md` | Two briefs for outside assistants (ChatGPT, Perplexity), the JSON schema their deliveries must validate against, and how a delivery enters the newsroom as leads, never facts |

## The first prompt

Paste this as the first message of the session, after the repository is cloned and this pack is
unzipped at its root under `briefs/pack/`:

```
You are building pt.newsroom.sgit.ai. Read briefs/pack/00__READ-ME-FIRST.md and then every file
it lists, in order. Copy briefs/pack/04__the-newsroom/CLAUDE.md to the repository root and the
skills under briefs/pack/04__the-newsroom/skills/ into .claude/skills/. Then execute
briefs/pack/04__the-newsroom/prompts/00-bootstrap.md to the end. Push nothing to the release branch
until every gate in the build is green. Report at the end with the live URL, the version, and
what you left undone and why.
```

## What is not in this pack, on purpose

- **Nobody's personal data.** The Portugal section's `people.json`, `topics.json`, `graph.json` and
  the frozen speaker pages are not here. The new site fetches and freezes its own sources, under its
  own notice, with the same refusals.
- **A legal opinion.** Section 5 of the brief says what the Portugal section concluded and built. It
  is not advice, and the statutory article it rests on must be re-read in full before it is quoted.
- **An English edition.** The brief leaves the question open (§14). Decide it deliberately; do not
  drift into one.

## How to check any file in this pack

Every code file here is a copy of a file in the newsroom.sgit.ai repository at v0.3.9,
[github.com/SGit-AI/SGit-AI__Website__Newsroom](https://github.com/SGit-AI/SGit-AI__Website__Newsroom).
If a copy and the original disagree, the original is right; this pack was cut once and does not
follow it.

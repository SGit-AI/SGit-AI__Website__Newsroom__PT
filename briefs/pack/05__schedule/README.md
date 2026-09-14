# Running the newsroom on a schedule

The run is a repository skill (`.claude/skills/newsroom-run/SKILL.md`) and a one-line prompt
(`../04__the-newsroom/prompts/10-daily-run.md`). What is left to decide is **what fires it**. Three
mechanisms are documented for Claude Code; all three run the same skill, so the choice can change
later without touching the newsroom. Facts below were checked against the Claude Code docs on
14 September 2026; the URLs are the authority if this page and they ever disagree.

## Option A — a Routine on Claude Code on the web (recommended)

A Routine is a saved Claude Code configuration that runs on Anthropic-managed cloud
infrastructure on a schedule, an API call or a GitHub event, with the repository cloned at run
start from its **default branch**. Created at https://claude.ai/code/routines (or `/schedule` in
the CLI). Docs: https://code.claude.com/docs/en/routines

- **Why first:** no secret to keep in GitHub, no runner to maintain, the repository and its
  `CLAUDE.md`, `.claude/settings.json` and skills are picked up as they are, and the run is the
  same kind of session the site was built in.
- **What the editor does:** create a Routine → trigger *Schedule*, daily at 06:30 UTC (07:30
  Lisbon) → repository: this one → prompt: the text in `10-daily-run.md`. During 16–18 September
  add a second Routine at 17:00 UTC. Check the daily run cap on the routines page.
- **Two consequences to design for:** the clone is the default branch, so the release branch must
  be `main` and `main` must be the default (CLAUDE.md says so); and the environment's network
  access must allow the source hosts the run fetches (startupsummit.io and the seed sources in the
  brief §10) — Routines default to a trusted allowlist, so widen it or the research step will
  freeze nothing and say so.
- **Limits stated in the docs:** research preview; daily cap per account; not on Personal plans.

## Option B — GitHub Actions on a cron, with the official action

`anthropics/claude-code-action` runs in *automation mode* whenever the workflow supplies a
`prompt:`; that includes `schedule:` (cron) triggers. Docs: https://code.claude.com/docs/en/github-actions

- `scheduled-run.yml` beside this file is the workflow: cron `30 6 * * *`, the prompt from
  `10-daily-run.md`, `claude_args: "--max-turns 120"`, the API key from the repository secret
  `ANTHROPIC_API_KEY` (or `claude_code_oauth_token` from `claude setup-token`), `permissions:
  contents: write` so the run can push `main`.
- **What the editor does:** add the secret; enable Actions; nothing else. The run's log is the
  workflow log; the run record and the inbox message are in the repository as always.
- **Why second:** a key lives in GitHub; the runner is GitHub's; the deploy workflow and the run
  workflow must not race (the `concurrency` group below serialises them).

## Option C — headless CLI anywhere

`claude -p "<the prompt>" --allowedTools … --permission-mode acceptEdits --max-turns 120
--append-system-prompt-file CLAUDE.md` from any machine with `ANTHROPIC_API_KEY` set, on a cron.
Docs: https://code.claude.com/docs/en/headless. The fallback when neither A nor B is available;
the brief's warning (§14) applies: a schedule that lives on a laptop stops when the laptop closes.

## Whichever option: the run must be able to

- fetch the sources (network to the beat's hosts), run `python3` and `node`, `pip install
  pyoxigraph` once (the SessionStart hook in `settings.json` does it), and `git push origin main`;
- **not** set `estado: publicado`, edit the notice or a gate, or push with a red build — the
  `deny` list in `settings.json` and the skill's own rules enforce the first three; the deploy
  workflow's `validate` job enforces the last even if a run pushes red (no tag, no deploy).

## The editor's review is not scheduled

`/newsroom-review` runs when the editor sits down. If the editor wants a run first, the Routine
page (A) or the workflow's `workflow_dispatch` (B) fires one on demand.

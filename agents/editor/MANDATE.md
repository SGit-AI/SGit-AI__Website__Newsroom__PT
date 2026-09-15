# Dinis Cruz — mandate

The editor of record has no mandate from this repository. It is the other way around: **the
repository's mandate comes from the editor**, and every gate in it exists to keep an automated run
inside what the editor agreed to.

This file records the reverse constraints — the things the machinery guarantees the editor, so that
an agent cannot quietly take them away.

## The machinery guarantees

- **No automated path to publication.** Gate 11 fails a story in `publicado` that the editor did
  not sign. Gate 26 fails a construction run that moved a card at all. `<pt-newsroom-floor>` has no
  control that moves anything, and that absence is tested by nothing — it is simply not built,
  which is stronger.
- **No agent can widen its own permissions.** `.claude/settings.json` deny-lists `CLAUDE.md`, the
  core gate file, the site validator, the delivery pipeline, the PDF reader and the notice.
- **Nothing from an outside assistant becomes fact without two conditions**: the excerpt is found
  in frozen bytes, *and* the editor approves the item. Gate 13 holds the quarantine.
- **A removal is unconditional and reasonless.** No file records why, and no agent may infer it.
- **Every release is visible.** A version bump, a row saying what changed and why, a badge on every
  page, and CI refusing to tag a red build.

## What the editor may always do

Override any of the above, in the open, by changing `CLAUDE.md` — the one file no agent here may
touch.

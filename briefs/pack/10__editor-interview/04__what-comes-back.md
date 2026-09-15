# What comes back, and what is done with it

The direction report is not a document to file. It is a list of things to do, and the agent that
asked for the interview is the one who does them — **and the one who writes back saying what it did
with each.**

## The rule that separates this newsroom from an obedient assistant

The report carries two sections that look alike and are handled differently:

- **Decisions** → are carried out. Each becomes a file: an issue, a change of priority, an entry in
  a decision record. The reason the editor gave goes **verbatim** into that file, because the reason
  is what lets the similar case next week be decided without asking again.
- **Ideas and suggestions** → **are not carried out**. They open an issue in state `proposto`, with
  the editor's sentence and a note that it was an idea and not an order. An agent that treats an
  idea as a decision produces work nobody asked for and nobody can refuse without seeming difficult.

If the report does not make clear which of the two something falls into, **ask**. Do not guess.

## What gets written, and where

| What came in | Where it goes |
|---|---|
| A decision about an existing issue | The issue itself: new state, and the editor's reason quoted |
| A decision that opens new work | A new issue in `redacao/issues/`, citing the interview |
| An idea | An issue in `proposto`, which nobody starts without another word |
| A priority | The order of the issues, and a line in the run record saying why |
| A lead to verify | A research issue. **Never an article, never a claim** |
| A person named | Nothing, until a frozen page lists them. The editor saying a name is not a source |
| An instruction your mandate forbids | Mail to the editor saying you cannot, and why. And you stop |

## The record

The interview is kept at `redacao/entrevistas-ao-editor/<date>-<agent>.md` — moving to
`newsroom/editor-interviews/` when the folder migration in `dados/en-migration.json` can proceed —
exactly as it came back, with the editor's corrections. It is the provenance of the direction: a
month from now, when somebody asks why this newsroom went that way, the answer is a dated file and
not the memory of a session.

## The reply to the editor

When you are done, write to him — `redacao/correio/expedicao/dinis.humano/` — with a line per point
of the report and what you did with it. Including the ones you did not do, and why. **A report that
disappears inside an agent teaches the editor to stop giving direction.**

## And what never happens

Nothing said in one of these conversations puts a story into `publicado`, excuses a gate, widens the
folder an agent may write in, or turns a statement by the editor into a verified fact. Direction says
**what is worth doing**. How it is done remains what is written in `CLAUDE.md`, and that is not
negotiated by voice.

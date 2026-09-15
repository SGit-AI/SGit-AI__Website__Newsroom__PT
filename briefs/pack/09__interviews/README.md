# 09 — Interviews

The other half of what this newsroom publishes. `08__research-briefs/` sends an assistant after
**documents**; this sends it into a **conversation**, and what comes back is a different kind of
material: a person's own words about their own work.

## Why by voice

Because it is easier for the person answering and better for the person reading. A busy person will
not write two pages about their work, but will talk for twenty minutes about it — and talks better
than they write, with examples they would never put in writing. ChatGPT in voice mode runs the
interview at whatever hour suits them, with nothing to schedule with anybody.

Anyone who would rather type, types: the same prompt works in both modes.

## The pieces

| File | What it is | Who uses it |
|---|---|---|
| `01__interview-prompt.pt.md` | The interviewer, in Portuguese. Always the same. | The interviewee |
| `02__the-interview-prompt.en.md` | The same, in English | The interviewee |
| `03__topic-block.md` | What changes: who, why, about what | The agent writes it, the person pastes it |
| `04__agent-prompt.md` | How a pack is assembled for one person | The editor hands it to an agent |

The two interview prompts are **in the language they are pasted in** — a Portuguese speaker pastes
Portuguese. Everything else here is English, like the rest of this repository's operational surface.

## The path, from invitation to article

1. The editor picks the person and hands `04__agent-prompt.md` to an agent session.
2. The agent finds what the newsroom already holds frozen about them, writes the topic block, and
   assembles a pack — an sgit vault or a `.zip`.
3. The person receives it, pastes the two blocks into ChatGPT, and talks. They end with a report.
4. **They review and correct the report.** Nothing leaves without that.
5. They send it back. The newsroom treats their statements as statements — things they said, not
   facts about the world — and goes looking for sources for the ones that are verifiable.
6. The editor of record decides whether to publish, and what. Publication is in European Portuguese;
   if the conversation was in English, the translation is done here and shown to them before it goes
   out.

## The rules that do not bend

- **An interview is a primary source about the person speaking, and nothing else.** If somebody
  gives a number about the market, that is a claim to verify, not a fact for having been said aloud.
- **Three fields per person**, as everywhere else on this site: listed role, listed organisation,
  the page that lists it. An interview makes no exception.
- **No contact detail** enters any file, neither in the pack nor in what comes back.
- **Approval is the person's and publication is the editor's.** Two decisions, and neither
  substitutes for the other.
- **Removal is unconditional and carries no reason.** Anyone interviewed may ask for the interview
  to come down, after publication, without explaining why — and the data-protection notice says how.

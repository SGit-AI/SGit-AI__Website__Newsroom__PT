# 10 — Interviewing the editor

`09__interviews/` sends an assistant to interview **somebody outside**, and what comes back is raw
material for an article. This sends an agent to interview the **editor of record**, and what comes
back is something else: **direction**. Which stories are worth writing, who to talk to, what to do
next, what to stop doing.

## The problem this solves

An agent in this newsroom knows what is in front of it — its issues, its mail, what is blocked — and
does not know **what the editor thinks matters**. That information exists, and today it only comes
out when he remembers to write it down. A twenty-minute conversation gets all of it, and gets it
better than any form: the editor says "look over there", "what about that?", "I have an idea", and
none of that fits in a field.

## The difference that changes everything: the agent studies before it asks

A generic interview with the editor is worth nothing. The agent behind this conversation **starts by
reading its own state** — the `ROLE.md` and `MANDATE.md` of its identity, its open and blocked
issues, its unread mail, its recent run records — and brings **its** open questions, with names and
numbers. The difference between "what would you like me to do?" and "issue 006 has been stalled
three days waiting on a PDF I cannot find; do you want me to press on, request access, or shelve the
lead?" is the difference between a polite conversation and a decision.

## The pieces

| File | What it is | Who uses it |
|---|---|---|
| `01__preparation-prompt.md` | The agent reads itself and writes the state block | The agent, before |
| `02__interview-prompt.pt.md` | The interviewer, in Portuguese. Always the same. | The editor pastes it |
| `03__the-interview-prompt.en.md` | The same, in English | The editor |
| `04__what-comes-back.md` | The report, and how it becomes files | The agent, after |

## The path

1. The editor tells an agent: **prepare me an interview**.
2. The agent runs `01__preparation-prompt.md` over itself and produces a **state block** — who it
   is, what it has in hand, what is blocked, and the five to ten open questions only the editor can
   answer.
3. The agent assembles a pack — an sgit vault, which the editor opens on his phone with nothing
   installed — holding the interviewer prompt and the state block.
4. The editor pastes both into ChatGPT and talks. Twenty minutes, by voice, whenever suits him.
5. He ends with a **direction report**, which he reviews and sends back.
6. The agent turns it into files: new issues, recorded decisions, mail to other agents, reordered
   priorities. And writes back saying what it did with each point.

## The rules, which are the usual ones

- **Direction is not fact.** If the editor says "company X is the biggest in the sector", that is a
  lead to verify like any other — it does not enter an article for having been said by the editor.
  What the interview produces is **priorities and questions**, not statements about the world.
- **Direction is not permission.** Nothing said in this conversation excuses a gate, authorises an
  agent to write outside its folder, or puts a story into `publicado`. Publishing remains a line the
  editor writes in a file, and only he writes it.
- **An idea said aloud is an idea, not an order.** The report separates what the editor **decided**
  from what he **suggested** — and the agent treats the two differently.
- **No contact details**, here as everywhere.
- **If the agent does not understand, it asks before acting.** A run that stops honestly is a good
  run, and that does not change because the instruction arrived by voice.

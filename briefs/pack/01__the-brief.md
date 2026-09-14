# 11 — Commissioning brief: `pt.newsroom.sgit.ai`

**For the agent that will build the Portuguese-language newsroom. Written 13 September 2026,
three days before the reception and four before the first panel.**

*Commissioning brief · addressed to a builder, not to a reader*

---

## Read this first

**You are not starting from nothing, and two of the things the source brief told you to
solve are already solved.** Check both before you plan anything, because planning around
problems that no longer exist is the main way three days becomes four.

| The source brief says | What is true on 13 September 2026 |
|---|---|
| The parent site is at v0.2.9 and the Portugal instance is a page describing a design that was never launched | The parent site is at **v0.3.0** and [`/portugal/`](https://newsroom.sgit.ai/portugal/index.html) is a **running section**, not a page about one |
| The fifth question — who is the editor of record — has been unanswered since 12 May | **Answered.** Dinis Cruz, named, reviewing before publication, on [every page](https://newsroom.sgit.ai/portugal/team.html) |
| The lawful basis needs deciding | **Decided and published**: legitimate interests, journalistic derogation expressly not claimed, [notice live](https://newsroom.sgit.ai/portugal/notice.html) |
| The company layer cannot be complete | Still true, and now demonstrated: 61 organisations derived from one event's speaker list, with the gap stated on the page |

**What this means for you.** The hard, slow, blocking question was the legal one, and it has
an answer you can copy rather than re-derive. What is left is a build.

**And one correction to carry forward.** The notice on `/portugal/` was published *after* the
pages that named 64 people, not before. That is the wrong order and it is recorded as such on
the notice itself. **Your site must not repeat it: the notice goes up before the first named
person, not after.**

---

## 1. What you are building

A **natively Portuguese** newsroom mapping Portugal's AI landscape as a graph, at
`pt.newsroom.sgit.ai`.

Not a translation of `/portugal/`. Not a bilingual site. One language, which is a
simplification rather than a cost — it removes the translation department the 12 May design
carried, and it is the reason the eleven-role design becomes tractable at all.

**The scoping sentence is inherited word for word and is the argument for doing this:**

> O ecossistema português de IA é pequeno o suficiente para ser mapeado por completo e grande
> o suficiente para ser interessante.

**The ontology is inherited and does not need reinventing.** Eight sections: as empresas, os
protagonistas, as instituições, as políticas, os casos de uso, o código aberto, a diáspora,
os eventos.

## 2. The name is `pt.newsroom.sgit.ai`, and the reasoning is mechanical

Take the source brief's answer. It is correct and it is decidable rather than a matter of
taste:

- A wildcard certificate matches **exactly one label**. `*.newsroom.sgit.ai` covers
  `pt.newsroom.sgit.ai` and does **not** cover `ai.pt.newsroom.sgit.ai`. Every extra level
  costs another wildcard or another explicit name.
- The estate already uses `{instance}.{argument}.sgit.ai`. The newsroom publishes the
  argument; Portugal is an instance of it.
- The platform domain already ends in the two letters `pt-ai.` would repeat.
- The deeper name reserves namespace for a general Portuguese newsroom nobody is building,
  and the estate's failure mode is unused sites, not unreserved names.

**Set no cookie above your own host.** Cookie scope is governed by the registrable domain
boundary, so a cookie set at the platform level is visible to every sibling.

## 3. Three departments, and the acceptance test is one story

Take the source brief's cut. Fifteen departments, each simultaneously a folder, an agent, a
page, a workflow and a reviewer, is seventy-five objects before a single article exists.

| Department | Owns | Why it survives the cut |
|---|---|---|
| `research/` | Finding the primary source; recording its address, date and **hash** | Without it there is no chain from claim to evidence |
| `reporting/` | Writing from what research recorded, and nothing else | Without it there is no output |
| `verification/` | Re-reading each cited source; marking each claim confirmed, disputed or unfindable | Without it the site is an opinion blog with footnotes |

Publishing is a build step. The archive is git. Corrections are not a department until there
is something to correct. Translation does not exist.

**The acceptance test is one story with the whole process visible** — the mail between the
agents, the issues opening and closing, every source with its hash, every claim linked or
marked unfindable, and which agent on which vendor did each step. One story rendered that way
beats seven rendered as articles, and the point of the project is the collaboration, not the
journalism.

## 4. Steal the ingestion path — it is the one thing already proven to work

`/portugal/build/extract.py` runs **fetch → freeze → hash → extract → diff** and it is the
reason that section can claim what it claims. Copy it before you write anything of your own.

```
sources/frozen/<date>/<page>.snapshot
```

Four properties of it are load-bearing and you should keep all four:

1. **Snapshots are dated, not singular.** One frozen copy proves a claim. A series proves a
   trajectory and shows what disappeared. On a moving beat, the diff *is* the story — the
   first published story on `/portugal/` exists only because the same page was frozen twice.
2. **Never read the live site at publish time.** Extraction runs against the frozen copy, so
   a page cannot change under a claim without the change appearing as a new hash.
3. **Frozen copies are `.snapshot`, not `.html`.** They are unmodified bytes of somebody
   else's pages held as evidence. A non-HTML extension keeps them from being served or
   indexed as pages of your site — publishing a browsable mirror of another organisation's
   website under your domain contradicts the one rule the publication has, which is that it
   links rather than reproduces.
4. **The gate re-verifies every SHA-256 on every build.** If a frozen copy was edited, every
   claim resting on it is unsupported and the build must stop.

## 5. The law, and what you must build because of it

**This section is not legal advice.** It is what `/portugal/` concluded and implemented, and
the statutory article behind it was returned truncated to the research that found it. **Re-read
Article 24 of Lei 58/2019 in full before you quote it on a public page**, and get advice if
anyone is paying for this.

**The journalistic route is not available to you.** Article 85 of the GDPR reserves a
derogation for journalism and leaves each member state to build it. Portugal's Article 24(3)
conditions processing for journalistic purposes on the **national legislation governing access
to and exercise of the profession**. An unaccredited publication produced by agents does not
satisfy that. The supervisory authority's 2019 disapplication decision does not touch Article
24, so it stands in full.

**So the basis is legitimate interests, and three things follow. Each is a deliverable, and
all three fit on three pages.**

1. **A written balancing test**, done before publication rather than after a complaint. Three
   cumulative limbs: the interest pursued, the necessity of personal data for it, and whether
   the subjects' rights override it. Write into it the one belief that would otherwise be held
   by default and is wrong: **data having been made public does not by itself mean it may be
   processed on this basis.** It is a factor in the balance, not an answer to it.
2. **A published notice, in Portuguese**, because the exemption you will rely on requires one.
   Article 14 requires notice where data was not obtained from the subject; 14(5)(b) exempts
   you where individual notification is disproportionate — but that exemption is conditional,
   and one condition it names expressly is **making the information publicly available**. The
   notice is the measure that earns the exemption. [Copy the live
   one](https://newsroom.sgit.ai/portugal/notice.html) and translate it.
3. **A named accountable human**, with an objection route that reaches a person rather than a
   form. Removal on request must be **unconditional** — no reason required, none asked for, no
   balancing exercise run against somebody who asked to be left alone.

**And one content rule that must be enforced where data is parsed, not where it is rendered.**
Article 24(4) bars disclosing addresses and contact details of individuals unless already
generally known. A graph of companies and founders pulls addresses out of every registry it
touches, so **drop those fields at the point of parsing**. `/portugal/` enforces this as gate
check 11, which fails the build if an email address, phone number or personal postal address
appears anywhere in the section's data. It was tested by injecting one and confirming the
build fails. Do the same; a contact detail that reaches your data and is merely hidden by a
template is one careless loop away from being published.

## 6. Portuguese is an edge vocabulary, not a translation layer

The fifth published graph rule: **if a path does not read as a sentence in the reader's own
language, the edges are wrong.** Your reader's language is Portuguese. Therefore **your edge
verbs are Portuguese verbs**, and the acceptance test is a Portuguese reader reading a path
aloud.

An English ontology behind a Portuguese interface fails that test while looking finished. This
is the single most likely way for your site to be quietly wrong, because nothing about it
looks broken.

**And the ASCII rule does not survive this trip.** The corpus enforces pure ASCII and
Portuguese is not an ASCII language. Every accented name in the source brief arrives stripped.
**Your build check should assert the opposite of the corpus rule** — that the accents are
present and correct, derived from the source rather than from a list somebody typed. Do not
make your site the exception to the corpus checker; write your own check that runs the other
way.

## 7. The communication layer needs no design

The file-based mail protocol already exists as a manual of over a thousand lines: one folder
per agent identity, inbox/done/outbox owned by the recipient, messages as ordinary mail files
with markdown bodies, a single-writer rule, three operations, and the read receipt being that
the message disappeared from the mailroom.

**The rule that makes the demonstration work is the commit cadence: one commit per processing
cycle, not per file operation.** Then the repository history *is* the newsroom's activity log,
and your site renders it with no additional instrumentation.

The issue protocol sits in the same manual, with one rule that matters: an agent may read
another agent's issues and may not write into them, so work is requested by mail. That is what
makes a Kanban board an honest picture rather than a management fiction — every card in
another agent's column got there by a message that is also on the site.

Two traps from the manual's own list, both of which will bite in a three-day build: **pull
before anything else**, because the pull is the notification system; and **do not mark a
message done because it was answered** — done means the work it asked for is complete.

## 8. The agents divide by what they can write

Four tiers. Only tier A can hold an identity in the protocol unaided.

| Tier | Can | Participates by |
|---|---|---|
| **A** | Read/write files, run commands, commit | Performing send, deliver and done itself |
| **B** | Drive a logged-in browser; cannot run code or touch a filesystem | Committing a message file **through the code host's web editor** |
| **C** | Fetch pages, produce text; cannot deliver | Writing the body; a tier A agent commits it and records that it did |
| **D** | Generate an app, sync to its own repo | Producing a rendering; writes only to its own project |

**Test tier B first and treat it as a finding either way.** Nobody in the estate has tried it.
It is a thirty-minute test and it decides whether a browser-driving agent is a first-class
newsroom participant. Publish the result whichever way it goes.

**One constraint changes a design decision rather than a preference.** One vendor's assistant
can only fetch addresses that have already appeared in the conversation, and explicitly not
addresses appearing only in its own output. It is not documented as following links inside a
page it fetched. **So serve a single concatenated machine-readable file and use constructible
addresses for every document.** Both patterns already exist across the estate.

## 9. The keys, and the one rule that stops them contradicting the site

Key generation, export, import, signing, encryption and decryption already exist in the
command-line tool, and a two-vault exchange was demonstrated on 8 June. Every agent generating
a key pair when it comes online is implementable today — and it gives the key registry its
first operating entries after forty-nine citations and none.

**The tension is real: end-to-end encrypted mail between agents contradicts a publication whose
whole promise is that the editorial process is visible.**

**The rule is: the envelope is always public and only a credential is ever sealed.**

- **Always in the clear:** who, to whom, when, about which story, what kind, thread position.
- **May be sealed:** a vault key, an access token, a signing key. Nothing else.
- **Never sealed:** an argument, a decision, a rejection, a source, a draft, a criticism.

**Write the gate before the first sealed message, not after.** A sealed message declares its
kind in a custom header; the build fails if a sealed message declares anything but a credential
kind, or carries a body larger than a credential plausibly needs. An intention is not a
control. If the gate is not written first, the site is a provenance publication with an
encrypted side channel, which is worse than not having the feature.

**And a read key may be published while a vault key may never be.** A key in a committed file
is a security incident by the estate's own rules, and a public newsroom repository is the worst
place to get it wrong. Check on every commit, not at review time.

## 10. The seed sources, and which are actually machine-readable

**There is no free bulk company register for Portugal**, and that single fact reshapes the
graph. Do not pretend otherwise on the page.

| Source | Machine-readable | Use |
|---|---|---|
| European research projects database | **Yes**, open datasets | Best seed for research, funding and institutional edges |
| National recovery plan transparency portal | **Yes**, open data export + beneficiary pages | Best seed for who received public money, for what |
| National open data portal | Partly | Worth a sweep for anything AI-adjacent |
| Science foundation research-unit list | Probably | The citable answer for institutions instead of guessing |
| The 2025 ecosystem report | **No** — a report, not a dataset | Cite the figures; do not claim the underlying list |
| Commercial register | **No** | Per-company, paid, access-code gated |
| Beneficial ownership register | **No, and gated** | Public access struck down in 2022; now conditioned on legitimate interest |

**So the company layer cannot be complete, and the honest claim is a different and better one:
these are the Portuguese organisations that appear in European research funding and in national
recovery funding, with amounts and dates.** Smaller graph, every edge citable. Say the size of
what you cannot see, on the page rather than in a footnote.

## 11. The first three articles

All three are complete, sourced and defensible before the reception, and all three have the
same shape: **publish the record, never the verdict, and no adjective about a named party.**

1. **The national AI agenda exists and its legal instrument could not be confirmed from the
   public record.** The official gazette renders through script and returned no body to an
   automated reader. That is a story about the machine-readability of the national record, told
   by a newsroom of agents that hit the wall itself — and it has an obvious human resolution
   that becomes the correction mechanism working on day one.
2. **The regulator was designated a year ago and the designating instrument is not on the
   government's own AI page.** State both facts, cite both, ask the question rather than
   answering it.
3. **How many of the 5,091 active startups are AI companies, and why no public dataset can tell
   you.** Publish the floor, name the method, state the size of what cannot be seen.

**A newsroom with four days cannot break news and can do something more useful: publish what
the record does and does not contain.** Note the honest tension, though — this works once. By
the fourth piece the site has to say something about the ecosystem itself, and nothing in the
source brief says what.

## 12. What goes on screen at Beato

One screen, three panes, no narration. Left: the Kanban board rendered from the issue folders.
Middle: the mail thread from the mail folders. Right: the article, every claim either linked to
a recorded source or marked unfindable in a colour that is hard to miss.

**Demonstrate one cycle and it takes a minute.** A message arrives in research's inbox. A card
moves. Two sources are recorded with hashes. The reply appears. Verification marks one claim
unfindable. The article pane updates and that claim changes colour. Nothing in it is a mock-up,
because every pane renders files the agents actually wrote.

**Do not demonstrate the key exchange live.** It is the most likely thing to fail on a venue
network and the least legible in a minute. Put the public keys and the sealed-envelope log on a
page and point at it.

## 13. What you should take from `/portugal/` and what you should not

**Take:** the ingestion path, the snapshot-and-diff pattern, the `.snapshot` extension rule,
the notice and balancing test, the named editor of record, the derive-don't-type rule for
organisations, and the two refusals that carry a gate each — **no reason for a removal** and
**no target reported as a result**.

**Do not take:** the English. Do not take the shape of its source register — `/portugal/`
holds the event's own pages and seven press pages *about* the event, and nothing that describes
the ecosystem beyond that one event, which is its largest limitation. You have two
machine-readable public datasets on day one; use both, and you will be able to claim something
it cannot.

**And do not take its scope as a model.** One event is a sample, not a census. `/portugal/`
says so on its own pages. Your beat is a country.

## 14. What to decide that nobody has decided

- **Who runs the schedule?** Nothing in the corpus says where a scheduled agent run lives for a
  site of this kind. It determines whether the newsroom keeps running after the conference or
  stops when a laptop closes. **This is the difference between a demonstration and a
  publication** and it is the question most likely to be skipped.
- **Does the site need its own vault, or is a public repository enough for the first pass?**
  Everything above works as files in a repository. The vault buys sealed envelopes and a read
  key; the rest does not need it.
- **What happens to a claim a source later contradicts?** With three departments and no
  corrections desk there is no mechanism, and the first correction will arrive during the
  conference if the site works at all.
- **English alongside?** The audience in the building is international and the site is natively
  Portuguese. Publishing a second language reintroduces the department this brief removed; not
  publishing one narrows the demonstration to Portuguese readers. The source brief leaves this
  open and so does this one — but decide it deliberately rather than by running out of time.

## 15. The honest tensions, carried forward rather than resolved

**The demonstration and the journalism pull in opposite directions.** A minute of live agent
traffic is a better demonstration when the agents are chatty and a better publication when they
are not. The acceptance test optimises for the demonstration, which is right for this week and
wrong afterwards, and **no trigger is written for switching back.**

**Answering the accountability question personally is honest and it is personal exposure.** A
named individual as controller for a graph of named ministers and founders, published from
another country, is a real position with real consequences. The alternative is delay, and delay
is what the last four months were.

**Three days is not enough to be careful about people and fast about software at the same
time.** If something has to give, let it be the software. The people named on the site did not
consent to being in a demonstration, and a build that ships late is recoverable in a way that a
publication that harmed somebody is not.

## 16. The home page: a direction was chosen on 13 September

Four home-page directions were drafted as mockups on 13 September 2026 — a classic
broadsheet, a dense capture-ordered ledger, a dark graph-first cover, and a magazine with the
claims underlined in the text — and the editor of record chose **the broadsheet**. It is
recorded here so that you inherit a decision rather than a question. The other three exist
and were not chosen; do not rebuild them. All four are archived at full size, with the
motivation and trade-off of each, at
[newsroom.sgit.ai/pt-newsroom/directions.html](https://newsroom.sgit.ai/pt-newsroom/directions.html).

![The chosen home page at 1440px: a warm-paper broadsheet with a dateline, a typographic masthead, eight sections, a lead story whose sources are chips, two secondaries, the national record in preparation, the graph with a path read aloud, the week's programme, what the press says, how it is made, and a colophon](../assets/img/pt-newsroom-home-a-1440.png)

**The system, so it can be built rather than imitated.**

- **Paper and ink.** Background `#f7f4ec`, ink `#17181c`, secondary text `#4a4d55` and
  `#6b6e76`, rules `#d9d3c3`, panels `#fffdf7`. One accent, the estate's green `#0f766e`,
  used for kickers, source chips that confirmed, and links; `#b45309` for a source that did not
  confirm; `#b91c1c` for *não encontrado*; `#a16207` for *disputado*.
- **Type.** Newsreader for headlines and body (54px lead headline, 27px secondaries, 21px
  third tier, 18px standfirst, 15px body), IBM Plex Mono at 11–12px with wide tracking for
  datelines, kickers, section labels and chips. Two faces, nothing else.
- **Rules, not boxes.** Sections are separated by a 1px ink rule; the masthead sits between a
  1px rule and a 3px double rule, and the colophon opens with the same double rule. No
  rounded cards, no shadows, no gradients.
- **The order of the page.** Dateline (city, date, days to the event) · masthead
  `pt.newsroom` with `.sgit.ai` in grey and the scoping sentence in italics · the eight
  sections plus *Registo* and *Grafo* · lead story (kicker, headline, standfirst, the sources
  as chips, and the three departments' one-line status) beside two secondaries and a
  *Nesta edição* block of counts · *Em preparação*: the three national-record stories with
  their claims as chips · *O grafo*: a path read aloud in Portuguese beside a small drawn
  graph · *Esta semana em Lisboa* (programme, titles verbatim) beside *O que diz a imprensa*
  (publisher, kind, date, hash) · *Como se faz*: the departments, beside the one dark block on
  the page, *Para redações*, which is the only marketing on the site · *Ficha técnica*: editor
  of record, sources, data protection, part of.
- **What is not on it.** No advertising. No photograph that lacks a recorded source: until
  there is one, the graph is the image. No person's name outside a story's own byline and
  the colophon; the counts are counts.
- **The phone.** The same hierarchy in one column at 390px; the section nav runs
  horizontally; chips wrap.

<img src="../assets/img/pt-newsroom-home-a-390.png" width="390" alt="The chosen home page at 390px, one column: dateline, masthead, a horizontal section nav, the lead with its source chips, two secondaries, the graph path, the programme, the press, the dark block for newsrooms, and the colophon">

The mockups were drawn with the section's real data of 13 September — the three published
stories, the 60→64 speaker diff, the seven press pages, the programme — so the copy on them is
true as of that date and will be stale by the time you read this; take the structure, not the
numbers. The design is also rendered as a page at full size, from the same sources, at
[newsroom.sgit.ai/pt-newsroom/](https://newsroom.sgit.ai/pt-newsroom/index.html); the two faces it
specifies, Newsreader and IBM Plex Mono, are vendored on that site under the SIL Open Font License.

---

## Sources and provenance

This brief is derived from the human-authored dev brief **v0.33.70 of 13 September 2026**,
*"The design is eleven roles and the deadline is four days"*, which supplied the departmental
cut, the certificate reasoning, the four agent tiers, the seal-a-credential rule, the legal
analysis and the three first articles. Where this brief differs from it, the difference is
noted in **Read this first** and is a matter of fact rather than of judgement: two of that
brief's findings were overtaken by work shipped on this site on the same day.

It also carries forward the four 12 May 2026 briefs (the ontology, the eight sections, the
scoping sentence, the department names), the parent site's thesis, and what
[`/portugal/`](https://newsroom.sgit.ai/portugal/index.html) learned by running.

**Nothing in section 5 is legal advice.** The statutory article it rests on was returned
truncated and must be re-read in full before it is quoted publicly.

---

This document is released under the Creative Commons Attribution 4.0 International licence
(CC BY 4.0).

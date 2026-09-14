# The design: the front page of pt.newsroom.sgit.ai

Chosen by the editor of record on 13 September 2026 from four directions drawn the same day.
Rendered live at [newsroom.sgit.ai/pt-newsroom/](https://newsroom.sgit.ai/pt-newsroom/index.html);
the three unchosen directions are archived at
[/pt-newsroom/directions.html](https://newsroom.sgit.ai/pt-newsroom/directions.html) and are **not
to be built**. `renders/` holds the two reference images; `Main.dc` and `MainPhone.dc` are the sources.

## The rule for using these sources

The `.dc` files are plain HTML artboards: a `<helmet>` block with the stylesheet, then the page
markup under `<x-dc>`. **The markup is the specification.** Build the real front page so that, with
the real data of the day substituted for the 13 September copy, it renders indistinguishably from
`Main.dc` at 1440px and `MainPhone.dc` at 390px. `render.py` is the script newsroom.sgit.ai uses to
turn the sources into a page (it scopes the stylesheet and swaps the font link); read it to see how
little is needed.

The copy on the artboards is real but dated: the three stories, the 60→64 speaker diff, the seven
press pages and the programme are the Portugal section's data of 13 September 2026. Take the
structure, not the numbers. Every number on the real page comes from a data file.

## The system

- **Paper and ink.** Background `#f7f4ec`, ink `#17181c`, secondary text `#4a4d55` and `#6b6e76`,
  rules `#d9d3c3`, panels `#fffdf7`. One accent, `#0f766e` (the estate's green), for kickers, source
  chips that confirmed, and links; `#b45309` for a source that did not confirm; `#b91c1c` for
  *não encontrado*; `#a16207` for *disputado*.
- **Type.** Newsreader for headlines and body (54px lead headline, 27px secondaries, 21px third
  tier, 18px standfirst, 15px body); IBM Plex Mono at 11–12px with wide tracking for datelines,
  kickers, section labels and chips. Two faces, nothing else. Both are in `fonts/` as latin woff2
  under the SIL Open Font License, with `fonts.css` declaring them; vendor them, never fetch them.
- **Rules, not boxes.** Sections separated by a 1px ink rule; the masthead between a 1px rule and a
  3px double rule; the colophon opens with the same double rule. No rounded cards, shadows or
  gradients.
- **The order of the page.** Dateline (city, date, days to the event) · masthead `pt.newsroom` with
  `.sgit.ai` in grey and the scoping sentence in italics · the eight sections plus *Registo* and
  *Grafo* · lead story (kicker, headline, standfirst, the sources as chips, the three departments'
  one-line status) beside two secondaries and a *Nesta edição* block of counts · *Em preparação*:
  the national-record stories with their claims as chips · *O grafo*: a path read aloud in
  Portuguese beside a small drawn graph · *Esta semana em Lisboa* (programme, titles verbatim)
  beside *O que diz a imprensa* (publisher, kind, date, hash) · *Como se faz*: the departments,
  beside the one dark block on the page, *Para redações*, the only marketing on the site · *Ficha
  técnica*: editor of record, sources, data protection, part of.
- **What is not on it.** No advertising. No photograph without a recorded source: until there is
  one, the graph is the image. No person's name outside a story's own byline and the colophon.
- **The phone.** The same hierarchy in one column at 390px; the section nav runs horizontally;
  chips wrap.

## What the other three directions were for

They are kept so the choice can be re-read, not so it can be re-opened. `canvas.json` carries the
note written beside each: the motivation and the trade-off. If a later decision wants the
dense ledger (B), the graph-first cover (C) or the underlined claims (D), it is a new decision by
the editor, recorded on the site, not a quiet swap.

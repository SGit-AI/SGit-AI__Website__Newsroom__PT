# Multilingual, and how the bill stays flat

This site is written in Portuguese and is being prepared to serve English, French and German at
`pt.newsroom.sgit.ai/en-gb/`, `/fr/` and `/de/`. The brief for the work was one sentence long and
it was the right sentence: *make it multilingual, and engineer it so that as we make new changes
the translation costs and prompts don't grow exponentially.*

This page is the answer to the second half. It is also the answer to "why is nothing published
yet", which has one cause and it is not technical.

## The number the whole design turns on

Measured on this repository, not estimated:

| what you could translate | words | x 3 locales | how often you pay |
|---|---|---|---|
| the rendered site | 186 101 | 558 303 | **every build** |
| the authored source behind it | **18 948** | 56 844 | **once per sentence, ever** |

The rendered site is ten times larger than the writing behind it, and the difference is not
padding. It is 106 920 unique words of names, SHA-256 hashes, dates, byte counts, source
identifiers and frozen excerpts — every one of which **must not be translated**, because a
translated excerpt is a different piece of evidence and a translated name is a different claim.
Translating the render means paying to translate the exact material the rules of this repository
forbid you to touch.

So the first decision is not a saving, it is a correctness rule that happens to be ten times
cheaper: **translate the source, never the render.**

The second column is the one that matters more. A pipeline that translates pages pays again every
time it builds; a pipeline that translates sentences pays once per sentence and nothing on a
rebuild. The site builds on a schedule. Over a year that is the difference between two numbers of
very different shapes.

## The six decisions, in order of what they save

### 1. The key is the hash of the source text

A segment's identity is `sha256(normalised source)[:16]`. Change one word of a paragraph and it
becomes a *different segment* with a different key, whose translation does not exist yet.

There is therefore no such thing as a stale translation on this site. There is no "needs review"
flag, no modification timestamp to compare, nothing anybody has to remember to invalidate.
Staleness is a **cache miss**, and `build/i18n.py status` counts cache misses.

```
python3 build/i18n.py status
source: 959 segments, 18948 words, from pt
locale     done  missing  words to do  orphaned
en-gb         0      959        18948         0
```

`words to do` is the entire cost of the next translation run. After the first pass it is the cost
of the week's edits and nothing else. The old translation of a changed paragraph is kept as an
*orphan*: not served, not deleted, there for reuse, costing nothing.

### 2. Identical text is one segment

The navigation, the footer, the provenance line, the state vocabulary — the chrome appears on all
223 reader pages and hashes **once**. Translate it once and 223 pages have it. The same holds for
any sentence repeated across data files.

This is why the segment count (959) is so much smaller than the number of substitutable runs on the
site (about 10 900): the average segment is reused eleven times.

### 3. Deny, do not allow

The data layer is translated **by default**, and a short list says what never is.

The other way round — a list of the fields that *are* prose — is the version that rots. A field
added next month falls silently out of every locale and nobody finds out, because an untranslated
page still looks like a page. Deny-by-default fails the other way: a field that should not have
been translated turns up as a wasted segment in the next `todo`, where a human reads it, and one
line in `NEVER` fixes it for ever.

**Prefer the failure you can see.** That sentence decides most of the design of `build/i18n.py`.

### 4. Evidence is an object, not a field

Any JSON object carrying a `sha256` is a record of somebody else's bytes. Nothing inside it is
translated, at any depth, whatever its fields happen to be called.

One structural rule instead of a growing list of field names — and it protects a field added to a
source record on the day it appears, which a name list never does.

### 5. The render is the discovery surface, not the thing translated

Reading the authored files finds the prose in `artigos/` and `dados/`. It does not find the
sentence a builder assembles with an f-string, or the clause that sits between two inline entity
links, and on this site those account for more of what a reader actually reads than everything in
`dados/` put together.

The alternative was to wrap four hundred Portuguese strings across twenty builders in a `t()` call.
This repository has already paid for that kind of bulk rewrite once: turning Portuguese identifiers
into English produced half-translated code (`save(estado)`, `this.items = itens`) and took two
rewrites from scratch to undo. So instead `build/i18n.py` reads the **finished HTML** and takes the
runs.

This is not translating the render. The unit is still a piece of authored text; the key is still
the hash of that text; it is still translated exactly once however many pages carry it. What the
render adds is *completeness* — no reader-visible sentence is invisible to the pipeline, so
coverage can reach 100% and a gap is a number instead of a surprise.

### 6. Generated text is formatted, not translated

`Lisboa · segunda-feira, 14 de setembro de 2026` is a different string tomorrow. Its hash is
different tomorrow. A translation of it is a cache miss for ever, and the site pays for the same
sentence every day it builds.

**That is the exponential growth this architecture exists to avoid, arriving through the back
door**, and it is the failure mode a naive segment store walks into within a week. `i18n.gerado()`
keeps date lines, version badges and counts out of the memory; they are localised by *formatting*
them in the target language, which is a function somebody writes once. Until that function exists
they stay Portuguese, and the coverage report counts them as `generated` rather than `missing` —
because calling them missing would invite exactly the wrong fix.

## What never gets translated, and why it is a rule before it is a saving

| what | which rule |
|---|---|
| frozen excerpts and quotations | rules 1 and 3 — evidence is not translated |
| names of people, organisations, sessions | a transcription is a claim |
| the graph's verbs and the sentences they read as | **rule 6** — the graph reads aloud in Portuguese |
| ids, hashes, dates, paths, published formulas, code | they are not language |

`i18n.nao_traduzir()` decides this, from the data rather than from a typed list: the verbs come out
of `dados/ontologia.json`, the names out of `dados/entidades.json` and friends, the excerpts out of
every record that has a `sha256`.

The graph test is a substring test against the ontology's own reading fragments, so it can in
principle fire on ordinary prose that happens to contain « organiza ». That mistake costs one
sentence left in Portuguese on a translated page, which the coverage report counts and a reader can
see. The opposite mistake — a translated edge label — is a **different graph**, and nothing would
catch it. Fail in the direction you can see.

## What is not localised at all: the back office

`/newsroom/`, `/admin/`, `/redacao/`, `/entregas/`, `/briefs/` and `/docs/` have one reader — the
editor of record — and that reader reads Portuguese and English. Translating the review board into
German is paying to translate a to-do list nobody will open, and it was over half the words in the
data layer.

223 pages can have a locale twin. The other 24 stay as they are.

## Source language: when Portuguese is the translation

`dados/i18n/locales.json` names `pt` as the **language of record**, and the reason is evidential
rather than sentimental: every claim on this site walks back to bytes, and those bytes are
Portuguese — official journals, government pages, event programmes. The Portuguese page is the one
whose sentences were checked against the frozen copy. Every locale page says so on its face, above
the masthead, with a link to the original.

But not all of the material is Portuguese. The summit interviews were **recorded in English**. An
item written in English is published in English first, and Portuguese is then the translation of
it. The translation memory does not care which direction it runs in: the key is the hash of the
source text, in whatever language that text was written. A segment whose source is English simply
has its `pt` value in `dados/i18n/pt.json` instead of its `en-gb` value in `dados/i18n/en-gb.json`.

What still has to be built for that case, and is not built yet: a `lingua_original` field on an
article, so that `build/locales.py` knows which tree holds the page of record for that one item and
which way the "this page is a translation" line should point. Until it exists, an
English-source item is published on the Portuguese site in Portuguese, the way everything else is,
and the English recording is cited as its source.

## The two commands, and the workflow that does not grow

```
python3 build/i18n.py extract                 # after a build: what exists, and its hashes
python3 build/i18n.py status                  # per locale: done, missing, words to do
python3 build/i18n.py todo en-gb > batch.json # ONLY the missing segments
#   … translate batch.json — an agent session, a service, or a person …
python3 build/i18n.py apply en-gb batch.json  # hash-checked on the way in
python3 build/locales.py --relatorio          # the coverage a reader would actually see
```

Two properties of this loop are the whole point.

**`todo` emits only what is missing.** Not the file the segment came from, not the page, not the
site — the missing segments and nothing else. The prompt is the batch, so the prompt is the size of
the change. A week in which three paragraphs were edited produces a three-paragraph prompt.

**`apply` refuses a translation whose source hash it does not recognise.** Anything else is a
translation of text that no longer exists, and writing it into the memory would be writing a lie
that a later build would serve.

## The coverage number, and why it is measured on the render

```
python3 build/locales.py --relatorio
locale   estado          hits  missing  generated  verbatim  coverage
en-gb    preparado          0     8215        998      1668      0.0%
```

Counted over **every substitutable run on every page**, so it is the coverage a reader would see,
not the coverage of the segment list. The four columns are four different things and conflating any
two of them produces a dishonest number:

* **hits** — translated.
* **missing** — a sentence a reader would find in Portuguese on a page served as English. The only
  column that counts against coverage.
* **generated** — a date, a count, a version badge. Formatted, not translated (decision 6).
* **verbatim** — an excerpt, a name, an edge of the graph. **Correct as it stands.** Counting these
  as missing would set a target the site must never reach.

A rehearsal with the memory filled reaches **100.0%** on all 223 pages:

```
python3 build/locales.py --ensaio en-gb /tmp/somewhere
python3 build/gates_i18n.py en-gb /tmp/somewhere
```

That rehearsal is how this design was proved before any locale was published, and it is how the
next one should be checked.

## Gate 44, and the two things it caught

`build/gates_i18n.py` is the locale gate. It asserts, in this order: the language register is
coherent and `pt` is the only language of record; **the key of every segment really is the hash of
its own text** (if somebody hand-edits `fontes.json`, the identity that the whole memory rests on
breaks silently); no orphan is served; every published locale mirrors the Portuguese page set
exactly; `<html lang>` is right and every page names the Portuguese original as `x-default`; inline
`<script type="application/json">` still parses after substitution; and — the one that matters most
— **every excerpt, name and graph reading in the Portuguese page is byte-identical in the
translated page.**

It was tested the only way a gate is worth testing, by sabotaging a rehearsal: a translated excerpt
and a deleted page were both caught and both named.

## Why nothing is published yet, and whose line it is

`CLAUDE.md` says:

> Everything a reader sees is European Portuguese under AO90.

That is the constitution of this repository, it is in the deny list of every automated session, and
it means **no build may serve an English page to a reader until the editor of record amends it.**
The engine is built, proved and gated; `dados/i18n/locales.json` holds all three locales at
`preparado`; `build/locales.py` renders nothing and says so.

The amendment is written out for the editor, word for word, in `redacao/issues/010`. Flipping a
locale to `publicado` is one line in a JSON file — afterwards.

## Three things a future session should not have to rediscover

1. **`build/chrome.py` runs before `build/locales.py`**, because locales.py reads finished pages.
   So `sitemap.xml` and `llms.txt` do not know about locale pages yet. Rule 7 says the sitemap
   agrees with the tree: before publishing a language, chrome.py has to run a second time after
   locales.py, or read `dados/i18n/locales.json` itself.
2. **Do not translate the back office** to raise the coverage number. It is out of scope on purpose
   and it is half the words.
3. **Do not add a field to `PROSE_KEYS`.** There is no `PROSE_KEYS` any more, and the reason it was
   deleted is decision 3.

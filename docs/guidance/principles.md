# The principles, and the gate that enforces each one

A rule without a gate is decoration. `coding.sgit.ai` measured its own estate and found a guard
that had never matched anything — a guard that passes because it *cannot* fail. So every principle
below names the thing that stops the build when it is broken, and where a principle has no gate, it
says so in those words rather than pretending.

The seven rules in [`CLAUDE.md`](../../CLAUDE.md) outrank this page. These are the working
principles that follow from them.

---

## 1. Everything except what a visitor reads is in English

One test, in [`language.md`](language.md): would a visitor read this string on the site?

**Gate 27** (`build/gates_artigos.py`) reads every comment and docstring in `build/`,
`admin/build/` and `assets/components/` and fails on Portuguese. Two honest exceptions are declared
in `language.md` and encoded in the gate, not hidden in it.

## 2. Every claim walks back to bytes

A source is fetched, frozen to `fontes/congeladas/<date>/<page>.snapshot`, hashed with SHA-256 and
registered **before** any claim stands on it. A claim with no source is a build failure.

**Gate 1** re-verifies every hash on every build. **Gate 17** checks every `[[fonte:…]]` mark and
every cited source resolves in the register. **Gate 2** fails if a frozen copy is ever served as a
page of this site — that is why the extension is `.snapshot` and not `.html`.

## 3. A name is verbatim, and accents come from the source

Names of people and organisations are copied from the frozen bytes, with the accents the source
gave them. Not from a typed list, not normalised, not corrected.

**Gate 9** checks every name against the frozen bytes and reports which direction the drift went.
It runs *inverse* to the estate's ASCII convention, and this repository says so out loud.

## 4. Nothing is attributed to anyone who did not say it

This is the one failure mode that does not look broken. A comment attributed to a model that never
wrote it is a claim with a **forged** source, which is worse than a claim with none — you cannot
tell it from a real one without leaving the site.

So agent activity is **derived, never authored**: every entry in a `comentarios.json` names the
file and path it came from. **Gate 25** opens that file and walks that path.

## 5. Only the named human editor publishes

`estado: publicado` is one person's line. No automated run may write it, and the newsroom floor has
no control that moves a card into that column — the absence is the design.

**Gate 11** fails any story in `publicado` that the editor did not sign. **Gate 26** fails a
construction run that moved a card at all.

## 6. A department only writes in its own folder

Research freezes sources. The newsroom writes prose. Verification writes verdicts. The run record
lists the diff by folder.

**Gate 12** fails a run that crossed a line. **Gate 26** closes the exemption: a run that declares
no department must declare its `especie`, and a `construcao` run that froze a source, moved a card
or published anything fails. An exemption any run can claim by typing the right word is not a
boundary — it is a door with the name written beside it.

## 7. The graph reads aloud in Portuguese

Every edge is a Portuguese verb with a distinct named inverse. Symmetric verbs are banned. A path
that does not read as a sentence is a wrong edge.

**Gate 10** reads every verb aloud and fails a reading that is not a sentence — and fails any
reading touching a `Pessoa` that agrees a participle in gender, because the source does not publish
anyone's gender and inferring it from a name is a refused inference.

## 8. Classification is a published formula or it does not happen

Deciding that a string is an entity, that a page is about a sector, or that a publisher is one
house rather than two is classification. Each one is published as data — `dados/lexico.json`,
`dados/entidades.json#formula`, `ontologia.formulas` — so a reader can disagree with the formula
rather than with the result.

**Gate 8** re-runs each lexicon pattern over the bytes. **Gates 22 and 23** check every entity link
against its published formula and its stated ground.

## 9. Version everything, and show the version

`admin/build/version.txt` is bumped once per release, the commit subject repeats it, the badge is
on every page, and `admin/versions.html` gets a row saying what changed and why.

**The site gate** (`admin/build/validate.js`) checks all four agree, with no duplicate rows. CI
validates, tags and deploys; a red validate is not a release.

---

## The principle with no gate

**Read the brief before changing what the brief asked for.** Nothing enforces this and nothing can.
It is the reason `briefs/pack/` is kept whole in this repository rather than summarised: a summary
of a brief is how a project quietly stops doing what it was asked to do.

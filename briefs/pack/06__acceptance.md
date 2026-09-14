# Acceptance: what MVP v0.1.0 is, and the one-story test

## Definition of done for v0.1.0

The live site at `pt.newsroom.sgit.ai` shows the version `v0.1.0` on every page and:

1. **The front page is the design.** At 1440px and at 390px it renders as `02__the-design/Main.dc`
   and `MainPhone.dc` do, with every number and headline coming from `dados/` and `conteudo/`,
   nothing typed into the template. The two faces are vendored. No English on it.
2. **The first beat is frozen.** Startup Summit Lisbon 2026's own pages (at least index, agenda,
   speakers, sponsors) and the seed sources the brief §10 marks machine-readable are in
   `fontes/congeladas/<date>/` with hashes in `dados/registo.json`, and `registo/` lists them.
3. **The graph exists and reads aloud.** `dados/ontologia.json` has Portuguese-first verbs each
   with a distinct inverse; `grafo/` draws it; shift-click two nodes reads the path as a Portuguese
   sentence; `dados/triplos.nt` exists.
4. **The notice is up** at `aviso/`, in Portuguese, naming the controller, the categories held and
   refused, the basis and the unconditional removal route, and every page naming a person links
   to it. Not legal advice, and it says so.
5. **The desk is real.** `redacao/` renders the board from `redacao/issues/`, the mail from
   `redacao/correio/`, and each story's claims coloured by `dados/verificacoes/`. Nothing on it is
   drawn by hand.
6. **The gates run and pass.** `build/gates.py` (with the accent gate, the Portuguese path gate and
   the department-boundary gate) and `build/validate.js` both print OK, and CI's `validate` job
   is green on the release commit.
7. **The schedule is wired.** One of the three mechanisms in `05__schedule/` is in place or is one
   secret away, and the final report says which and what the editor must do.
8. **The three first articles exist as issues** in `redacao/issues/` in state `procurado`, with
   the brief's framing (§11) in each.

Not required for v0.1.0: a published story (the editor publishes; the run cannot); the no-server
databases; connections; an English edition; a vault.

## The acceptance test (brief §3): one story with the whole process visible

Within the first three scheduled runs, on the desk page, a reader can follow one story from a
message in Pesquisa's inbox to a line on the front page:

- the issue moving `procurado → registado → congelado → extraido → redigido → verificado`;
- the mail between the departments, dated, in order;
- two or more frozen sources with hashes;
- the story with every claim marked, and the verification record beside it, each claim
  `confirmada` or `disputada` or `nao_encontrada` in a colour that is hard to miss;
- the run records that did each step, naming the model that ran them;
- and then the editor's decision file, and the story on the front page with `publicado_em`.

If the first correction arrives during the conference (the brief §14 expects it), the procedure in
`04__the-newsroom/prompts/30-correction.md` is the test's second half: the correction propagates
and the original is superseded from a date, never deleted.

## What would fail the test even if every page renders

- A claim on the front page without a frozen source behind it.
- A person's biography, or any third-party prose, reproduced.
- A reason given for a removal, anywhere.
- A story set to `publicado` by a run rather than by the editor.
- A gate weakened to get green.
- English prose on a reader-facing page.

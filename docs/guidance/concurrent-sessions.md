# More than one session at a time

Three Claude Code sessions work on this repository at once, each with a different focus. That is
the normal condition here, not an exception to plan around — and everything on this page is
written from collisions that actually happened, in one week, between sessions on this site. None of
it is hypothetical.

**The short version.** Run `python3 build/before_push.py` before you choose a version number, and
again after any merge. Take your version number **last**, not first. Resolve a conflict in a
generated file by rebuilding, never by hand. And when the other session rewrote a file wholesale,
read your own lines in it afterwards — a clean merge is not evidence that your work survived.

## What actually went wrong, and what each thing cost

| What collided | How it showed up | What stops it now |
|---|---|---|
| **The version number**, three times | A push rejected, or worse, accepted — two sessions each wrote `admin/versions/v0.13.0.md` | **Gate 38** + `before_push.py` |
| **Gate numbers** | Both sessions numbered their new gates from 27. The build was green on each branch *and after the merge*, because a gate number is a comment | **Gate 36** |
| **The same work, twice** | Both sessions answered "give each agent a `ROLE.md`" the same afternoon — one by writing five files, one by building `dados/agentes.json` | Nothing mechanical. See *Claim the work* below |
| **A wholesale rewrite eating older work** | `assets/site.css` was rewritten; git auto-merged with **no conflict**; four rules that gave `<pt-chat>` its column vanished. Every gate stayed green and the panel simply lay across the article again | **Gate 37** for this coupling; `before_push.py` flags the rewrite; nothing catches the general case except reading |
| **245 conflicted files in one merge** | All generated. None worth a human's attention | The rule below |

## The order that avoids most of it

1. **Before you start**, run `python3 build/before_push.py`. It fetches `dev` and tells you the
   released version, the highest gate number, and what the other sessions have rewritten. It
   changes nothing.
2. **Claim the work before you build it.** The expensive collision is not a merge conflict, it is
   two sessions building the same thing well. Before you write a new component, a new register or a
   new gate, look for it: `ls assets/components/`, `ls dados/`, and read
   [`index.md`'s *What not to build*](index.md). The chat panel was nearly written twice; the
   engine already existed and was found by looking first.
3. **Do the work. Do not take a version number yet.** A number taken at the start of an hour's work
   is a number claimed while somebody else is finishing.
4. **`python3 build/tudo.py --render`** — all five gates green.
5. **`python3 build/before_push.py`** again. *Now* take the version number it says is free.
6. Write the note, bump `admin/build/version.txt`, re-run `build/tudo.py`, commit, push.

If the push is rejected, somebody released between steps 5 and 6. That is not a failure of the
process — it is the process working. Merge, renumber, rebuild, push.

## Merging

**A generated file is resolved by rebuilding, never by hand.** Take either side to clear the
conflict and then run `python3 build/tudo.py`, which regenerates all of it from sources. One merge
here produced 245 conflicted files and every one was generated. Hand-resolving even one is how a
release table ended up with fifteen rows and three `<tr>` tags.

Generated, for this purpose: every `.html` that is not a hand-written page, everything under
`api/`, `dados/`, `entidades/`, `agents/`, `ficheiros/`, plus `llms.txt`, `sitemap.xml`,
`index.md` and `admin/versions.html`.

**Never force-push, never rebase a shared branch, never rewrite history.** With three sessions, a
force-push is somebody else's work deleted.

**When two sessions did the same work, whatever shipped first wins.** Delete your copy and render
from theirs. The rule is the repository's own — content exists once — and it settles the argument
without anybody negotiating: the agent register shipped first, so five hand-written mandate files
were deleted and `build/mandatos.py` renders them from the register instead.

## The failure that does not look like one

Git's conflict markers are the *good* case: it stopped, you looked, you decided. The dangerous
merge is the one that succeeds.

> Their side rewrote `assets/site.css` wholesale. Git took their file. Four rules that had been in
> that file since two releases earlier went with it. No conflict, no warning, five green gates, and
> a chat panel lying across the article exactly as if the `hidden` bug had come back.

Two lessons, and the second is the useful one:

- `before_push.py` lists every source file the other side **rewrote wholesale** (60% or more of its
  lines, in a file of at least thirty). After merging, grep each one for your own work. Note what
  this is *not*: it is not "files we both changed". That list, checked against the merge that
  actually lost work, did not contain `site.css` at all — the rules predated the merge base, so
  only their side had touched the file.
- **A coupling that crosses a file boundary and is checked by nothing will eventually be deleted in
  silence.** `pt-chat.js` puts a class on `<html>` and `site.css` styles it; nothing tied the two
  together, so nothing noticed. Gate 37 ties them now. When you write a coupling like that, write
  the gate in the same change — *a rule without a gate is decoration*.

## Claim the work

There is no lock in this repository and there should not be one. What there is:

- **`redacao/correio/sessoes/<agente>/`** — the mail. If you are starting something large, leave a
  note there saying what and where. It costs one file and it is the only signal another session
  gets.
- **Your run record** in `redacao/runs/`, written at the end, says which folders you touched. Gate
  12 holds you to your department's folders, so reading recent run records tells you where the
  other sessions have been working.
- **`agents/README.md`** — claim a named identity whose mandate covers the work. If no identity
  fits, that is a message to the editor, not a licence to invent one.

## For the human running the sessions

The cheapest thing you can do is give each session a **different area of the tree**, because gate
12 already enforces area boundaries and two sessions in different areas essentially cannot collide.
The three things that collide regardless of area are the shared counters — the version number, the
gate number — and the stylesheet. Those are now gated. Everything else is reading.

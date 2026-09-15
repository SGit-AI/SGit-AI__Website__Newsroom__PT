# Releasing, and the four things that go quiet

Everything here was learned by getting it wrong in one session, on this repository, in one day.
None of it is hypothetical, and each item names what it cost.

## The version number: which component is the minor

The version is `v<release>.<major>.<minor>` — and **the minor is the third component.** `CLAUDE.md`
says every push to `dev` is a minor release, so a normal push goes `v0.23.0 → v0.23.1`, not
`v0.23.0 → v0.24.0`. The second component moves only for a deliberate major.

CI agrees and is the authority: the tag job in `.github/workflows/deploy-pages.yml` computes

```
NEXT_MINOR = v0.23.1     # third component + 1   ← this is the normal one
NEXT_MAJOR = v0.24.0     # second component + 1
```

and **rejects anything that is neither**. A release numbered by guesswork is a push that fails
after you have written the note.

> **`build/before_push.py` gives the wrong advice here.** Faced with `v0.23.0` on `dev` it says
> *"Take v0.24.0"* — the major. Use that tool for what it is reliable at: whether a number is
> already taken, what the other sessions rewrote, and how far ahead or behind you are. Do not take
> its suggested number without checking it against the rule above. This is a known disagreement
> between the tool, `CLAUDE.md` and CI; whoever owns that file should settle it in the file.

And take the number **last**, after the gates are green — a number claimed at the start of an
hour's work is claimed while somebody else is finishing.

## Install `requirements.txt` first, or the build lies quietly

A fresh container does not have them, and `build/tudo.py` does not check. Both failures are silent
and both leave every gate green:

```
python3 -m pip install -r requirements.txt
```

| Missing | What breaks | What you see |
|---|---|---|
| `pycryptodomex` | `build/pdf.py` cannot decrypt an AES-encrypted PDF. Every stream decrypts to zero bytes | The reader reports **«provavelmente um PDF digitalizado»** — a false statement about somebody else's document — and every claim resting on that PDF turns to `fonte_inacessivel` |
| `jsonschema` | `build/entregas.py` cannot validate a research delivery | `esquema_valido` becomes meaningless and the errors read *"jsonschema não está instalado"* |

The first one is the expensive one. The same frozen PDF, with the same SHA-256 re-verified by gate
1, read **30 808 characters on one machine and 0 on another**. The bytes had not changed; the
machine had. **Evidence that depends on which machine reads it is not evidence.** CI installs these
before the gates; your container is your own problem.

## The browser gate, in a container that has no Playwright

Required whenever you touch `assets/components/`. Three things are true at once here: the npm
package is not installed, installing it *into the repository* turns `admin/build/validate.js` red
(it scans gitignored build tooling), and the Playwright build it wants is not the Chromium that is
installed. So install it outside the repository and borrow it for the run:

```
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install --prefix /tmp/pw playwright
ln -s /tmp/pw/node_modules node_modules          # borrow it
python3 -m http.server 8777 &
CHROME_PATH=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
  node admin/build/render.mjs http://127.0.0.1:8777
rm node_modules                                   # give it back BEFORE validate.js runs
```

`render.mjs` reads `CHROME_PATH`, which is what makes the pre-installed browser usable. Add your new
page and its components to the `PAGINAS` list in that file — a component the gate does not open is a
component nothing tested.

**It earns its place.** It caught a bug no other gate could: the entity linker rewrote names inside
a page's inline `<script type="application/json">`, producing valid HTML and corrupt JSON. The page
was well-formed, the damage was inside a string, and only a browser showed it.

## Where a freeze date comes from

`build/entregas.py --date` defaults to **today** and re-checks every excerpt against
`fontes/congeladas/<date>/entregas/`. Point it at the wrong day and every source reads as
unreadable — a delivery that had nine confirmed claims reports zero, with the build green.

`build/tudo.py` resolves it from **the frozen directories on disk, at the moment the step runs.**
Not from `dados/registo.json`, which was the first fix and was wrong twice over: that file is
written by `build/extract.py`, which `tudo.py` **skips unless `--fetch` was asked for**, so it can be
days stale; and it was read at import, before that step could have run anyway. Ground truth is where
the bytes are.

## Merging: two traps, both of which delete work silently

**Stage your source resolutions before you bulk-resolve the generated ones.** The usual move after a
big merge is

```
git checkout --theirs $(git diff --name-only --diff-filter=U)
```

and it will **overwrite a resolution you have already written to disk but not `git add`ed**. A
carefully merged `build/build.py` went back to the other session's version that way, and the only
sign was a page that had quietly lost its rewrite. Resolve and `git add` the source files first,
then bulk-resolve what is left, then rebuild.

**A clean merge is not evidence that your work survived.** After every merge, grep your own changes
back — by name, one at a time. In one merge here, of six changes, one was silently reverted by an
auto-merge with no conflict, and a second was destroyed by the command above. Both looked fine; all
gates stayed green.

## The shape of the failure to watch for

Three separate incidents in one day, and they are the same incident:

- a frozen PDF that read 30 808 characters yesterday and 0 today,
- a freshly frozen delivery reporting 0 of 4 sources readable,
- a register row whose link to its delivery vanished while its other three links rendered.

In every case **the build was green and the record underneath it had changed meaning.** The gates
check structure — files exist, links resolve, hashes match, pages are well-formed — and all of that
was true. The damage was in a *value*: a count, a state, a missing chip.

So when you add a gate, ask what it would say if the structure were perfect and the content were
wrong. And when a number in a build summary changes and you did not mean to change it, stop and find
out why. **A row that is partly right looks exactly like a row that is right.**

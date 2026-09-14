# The Portuguese AI ecosystem — the second brief

**Memo capturing the editor's review of v0.2.0, 14 September 2026.** Written by the session that
received it, before implementing any of it, so that what was asked for and what was built can be
compared later by somebody who was not in the room.

This is the pattern the brief itself asks for: *every time you do one of these pieces of work, you
probably want to create a document that captures it.* This file is that document for this
briefing. It is the second brief this site has had; the first is
[`briefs/pack/01__the-brief.md`](../pack/01__the-brief.md), and where the two disagree, this one is
later.

---

## 0. The sentence that reframes everything else

> The main title should be the Portuguese AI ecosystem. `pt.newsroom.sgit.ai` should almost be a
> subtitle.

Everything below follows from this. v0.1–v0.2 built **a newsroom that publishes**. The brief is
asking for **a publication about a subject**, which happens to be produced by a newsroom. The
newsroom is the method; the ecosystem is the masthead.

Two consequences that are not cosmetic:

- The site is **a news site / a blog** — the brief says so twice and names Ghost as the shape. Not
  a demonstration with articles attached. Every item on the front page is a story and every story
  is a link.
- The newsroom machinery that currently sits on **every reader-facing page** — the agent block,
  the "this is made by agents" disclaimer — moves to **one provenance page**, with at most a line
  in the footer. The brief is explicit: *we don't have to say it on every single line, every
  single page.*

## 1. Own the agentic authorship, loudly

> Let's be very clear that this website right now is being created by AI agents with light
> curation by me. And let's own it.

The current posture hedges — a small block on every page. The brief asks for the opposite: one
strong, prominent statement, and then **per-article provenance naming the actual model**:

- multiple agents working together, **multiple providers**: Claude, ChatGPT, Perplexity, plain
  Google searches. It does not matter which; what matters is that it is recorded.
- an article says *who made this* — "written by Claude, research by ChatGPT, one claim from a
  Perplexity delivery" — and that is a field, not prose.
- the editor of record is a named human doing **light curation**, and saying "light" is more honest
  than the current implication of line-by-line review.

`proveniencia.json` already exists per article and already records agent and model. What is missing
is (a) the *provider* as a first-class field, (b) a site-wide provenance page that aggregates it,
and (c) removing the per-page repetition that currently substitutes for it.

## 2. Everything links to everything

The largest piece of work in the brief, and the one that makes the rest worth having.

> Even if I'm here and I'm talking about the Comissão Europeia, well, that should be a link to
> almost that dictionary definition of that entity. So you start to have this full-blown Diário da
> República. If I click on that I then go into the page that shows me all the Diário da República
> happening. And this should be dynamic because it should be loading the graph dynamically.

Concretely:

- Every **entity** — an institution, a company, a person, a legal instrument, an event — has a page
  at a constructible address, built from the graph.
- Prose links to it. "Comissão Europeia" in an article body is a link to that entity's page.
- An entity page shows everything the graph knows: what it is, what cites it, which articles stand
  on sources it published, which people are listed under it.
- **Protagonists**: every person links to the organisation they are listed under and to the role.
  *Eventually I want to map the players in Portugal* — this conference's speakers are one sample;
  another conference gives another set, and the graph is what joins them.
- The graph is **loaded dynamically** by the page rather than baked into it. What is stored in the
  repository is JSON — the nodes, the edges, the triples.

The site already has the graph (298 nodes, 842 edges, Portuguese verbs with inverses) and already
exports N-Triples. What it does not have is **entity pages** and **prose that links into them**.

## 3. The shared viewer module is the keystone

> You have a shared module, which is basically the viewer of all this. And the logic is that we
> then improve all the website once we improve those shared modules.

This is an architecture instruction and it is the right one. The guidance to follow is the
estate's own, at [coding.sgit.ai/javascript/](https://coding.sgit.ai/javascript/index.html), read
on 14 September 2026:

| Convention | What it means here |
|---|---|
| **Native web components, no framework, no build step** | The browser is the runtime. 41 `customElements.define` calls across 50 files in the estate; no React, no bundler. |
| **The three-file triplet** | `<name>.js` (behaviour), `<name>.html` (markup), `<name>.css` (styles) — same basename, same directory. |
| **`static jsUrl = import.meta.url`** | Self-location. The component knows its own URL, so the base class fetches the sibling `.html` and `.css` without being told where they live. **This is the mechanism that removes the build step.** |
| **The `SgComponent` contract** | Override four things: `static jsUrl`, `get resourceName()`, `get sharedCssPaths()`, `onReady()`. Never `connectedCallback` directly — the base class fetches the siblings and calls `onReady()` once the shadow root is populated, which removes a whole class of race condition. |
| **Versioned path** | `components/<name>/v1/v1.0/v1.0.0/<file>` — three nested directories, one per semver level. A consumer pins at whatever depth it wants stability. Immutable URLs, no lockfile, no `node_modules`. |
| **Events** | Namespaced, dispatched on `document`, `bubbles: true, composed: true` so they escape the shadow root. |
| **Style** | 4-space indent, single quotes, `_` prefix for private, ESM everywhere, shadow DOM so BEM is unnecessary. |

**One deliberate departure, and it is this site's existing rule rather than a new opinion.** The
estate's components import the base class and tokens from `dev.tools.sgraph.ai`. This site vendors
everything and fetches nothing from a third party at runtime — the same reason Cytoscape and the
two fonts are in the repository. So `SgComponent` is **vendored under the same path scheme**, and
the component code is otherwise the estate's contract unchanged. A page that needs a third party to
render is a page a third party can stop rendering.

## 4. The documents area is a two-pane reader

The current one is a list that jumps you to a separate page and loses your place. What is asked
for:

- **Tree on the left, viewer on the right.** Folders collapse — `briefs/pack/` is one element, not
  thirty rows.
- **The markdown renders on white**, like a document, rather than on the newspaper's paper ground.
- Navigation never loses the tree.

## 5. An article is a template, and its folder is its data

> That article published inside its folder is going to have a whole bunch of JSON files that
> contain that workflow, contain the decisions, contain the comments, contain the different
> agents' views of it and when it was done, and contain all the references and all the graphs that
> connected. And then you have a shared module which is the viewer of all this.

Two gaps against what v0.2.0 built:

1. **Comments.** The agents' views of the article — *the editor says the title doesn't make sense;
   where's the next bit; what's the evidence* — are not captured anywhere. They should be a file in
   the folder and a visualisation on the page. This is the piece that makes the process visible in
   the way the first brief's §12 wanted.
2. **The files are linked as raw JSON.** Clicking `afirmacoes.json` should open a **viewer**, not a
   download. Same shared module as everywhere else.

## 6. The API, and why the data moves

> Add a pure GET API, add a swagger, where all those JSON files, all those graphs can be accessed
> from the swagger, and then add a web viewer of that, and also a way to invoke from the web.

- **GET-only.** Every path is a file read, so an `openapi.json` describing it is honest — there is
  no verb that is not a GET, and no server.
- **The data lives under the API base.** `/api/v1/companies`, `/api/v1/sources`, and so on — which
  means the JSON files move to where the API says they are, rather than the API pretending to be
  somewhere the files are not.
- **The API is in English**, deliberately, *although we're doing this in Portuguese* — because the
  intent is multiple languages over one dataset. `companies`, not `empresas`. The site stays
  Portuguese; the interface to the data does not.
- A **console** that lists the operations and actually invokes them from the browser, so the claim
  "all the content here is accessible via API" is demonstrable rather than asserted.

## 7. Pay per read, from day one

> Add a mode where every page gets a little budget. Make every page that you open cost one cent.
> Give everybody a five-euro budget. If you get to zero, you give it back to five. Let's already
> bake this thing in.

This is the parent site's whole argument — *paying the fact creator*, *micro and nano payments* —
made concrete on a real publication instead of argued in an essay. It is a demonstration, not a
payment system: a wallet in the reader's own browser, a price per page, a top-up when it empties,
and the ledger visible. Nothing is charged and nobody is billed, and the page must say so plainly,
because a fake paywall that did not say it was fake would be the one dishonest thing on a site
whose entire argument is provenance.

## 8. What was asked for that is not in this session's build

Recorded here rather than silently dropped. The brief is large and the honest thing is to say
which parts are landed and which are not.

- **Entity pages and prose-level linking** (§2) — the largest item. Needs an entity resolver, a
  page per entity, and a link pass over the prose.
- **Agent comments per article** (§5.1) — needs the data model, a file per article, and a
  visualisation.
- **The visual news desk** — the brief points at
  [newsroom.sgit.ai/governance/newsroom/](https://newsroom.sgit.ai/governance/newsroom/index.html),
  which has the point-and-click floor, the Kanban and the desks. This site's `/redacao/` is a
  table; that one is a room.
- **More events.** *We're about to have the Web Summit in Portugal* — one event is a sample. The
  beat is a country, and the graph is what joins two conferences into an ecosystem.
- **Hiring people to manage each component** — the end state the brief describes, and the reason
  the departments are folders with boundaries rather than labels.

## Sources for this memo

The editor's spoken review of v0.2.0, 14 September 2026, transcribed into this repository as the
brief it is. The estate guidance it points at was read the same day:
[coding.sgit.ai/javascript/](https://coding.sgit.ai/javascript/index.html) ·
[graphs.sgit.ai](https://graphs.sgit.ai) ·
[newsroom.sgit.ai/governance/newsroom/](https://newsroom.sgit.ai/governance/newsroom/index.html).

Unlike an article on this site, **this memo is not built on frozen sources and makes no claim about
the world.** It records what one person asked for. That is why it lives in `briefs/` with the rest
of the commissioning material and not in `artigos/`.

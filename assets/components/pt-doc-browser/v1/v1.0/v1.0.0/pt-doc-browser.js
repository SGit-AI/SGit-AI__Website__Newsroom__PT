/**
 * pt-doc-browser — every markdown document in the repository, as a tree you keep while you read.
 *
 * The version this replaces was a list of links that threw you onto a separate page: you scrolled
 * to read, and you lost the other documents doing it. A reader of a document set is navigating and
 * reading at the same time, so the tree stays and the document renders beside it, on white.
 *
 * The tree is built from the PATHS, so `briefs/pack/08__research-briefs/` is one collapsible
 * element rather than thirty sibling rows. Nothing about the grouping is configured: it is what
 * the directory structure already says.
 *
 * Reads `/api/v1/documents.json` for the index and the document's own bytes for the body — the
 * same files the build read, never a copy, so what is shown cannot drift from what was built.
 *
 * @module pt-doc-browser
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

/* References live in the component rather than in the index, because they are editorial: which
   sites in the estate are worth a reader's time is a judgement, not a fact about the repository. */
const REFERENCES = [
    ['newsroom.sgit.ai', 'https://newsroom.sgit.ai',
     'The parent publication, and the brief for this site'],
    ['newsroom.sgit.ai/portugal/', 'https://newsroom.sgit.ai/portugal/index.html',
     'Where this method was proven before it was copied'],
    ['sgit.ai', 'https://sgit.ai', 'The platform: vaults and the CLI'],
    ['coding.sgit.ai', 'https://coding.sgit.ai/javascript/index.html',
     'The component contract these components follow'],
    ['graphs.sgit.ai', 'https://graphs.sgit.ai', 'The graph grammar this ontology obeys'],
    ['nfrs.sgit.ai', 'https://nfrs.sgit.ai', 'Non-functional requirements across the estate'],
    ['This repository', 'https://github.com/SGit-AI/SGit-AI__Website__Newsroom__PT',
     'Every file behind every page'],
]

class PtDocBrowser extends SgComponent {

    static jsUrl = import.meta.url

    get resourceName() { return 'pt-doc-browser' }

    /* `async`, and the load is AWAITED — same reason as pt-json-viewer. The base class sets
       `data-estado="pronto"` once onReady returns, and that is only true if the load it started
       has finished. A fire-and-forget load lets the render gate read this component as up while
       its fetch of documents.json is still in flight. */
    async onReady() {
        this._root = this.getAttribute('site-root') || '../'
        this._docs = []
        this._current = null
        this.$('#q').addEventListener('input', e => this._filter(e.target.value))
        window.addEventListener('hashchange', () => this._openFromHash())
        await this._load()
    }

    async _load() {
        try {
            const r = await fetch(`${this._root}api/v1/documents.json`)
            const d = await r.json()
            this._docs = d.documentos || []
        } catch (err) {
            this.falhou(err.message)
            this.$('#nodes').textContent = `documents.json did not load: ${err.message}`
            return
        }
        this._renderTree(this._docs)
        this._renderRefs()
        this._openFromHash()
    }

    /* --- the tree, built from the paths ---------------------------------- */
    _tree(docs) {
        const root = { dirs: new Map(), files: [] }
        for (const doc of docs) {
            const parts = doc.caminho.split('/')
            const file = parts.pop()
            let node = root
            for (const p of parts) {
                if (!node.dirs.has(p)) node.dirs.set(p, { dirs: new Map(), files: [] })
                node = node.dirs.get(p)
            }
            node.files.push({ ...doc, file })
        }
        return root
    }

    _countIn(node) {
        let n = node.files.length
        for (const child of node.dirs.values()) n += this._countIn(child)
        return n
    }

    _renderTree(docs) {
        const host = this.$('#nodes')
        host.textContent = ''
        const root = this._tree(docs)
        /* Root-level files first — CLAUDE.md, README.md and the licences are what somebody
           arriving cold should see before a folder of thirty briefs. */
        for (const f of root.files.sort((a, b) => a.file.localeCompare(b.file))) {
            host.appendChild(this._link(f))
        }
        for (const [name, node] of [...root.dirs].sort((a, b) => a[0].localeCompare(b[0]))) {
            host.appendChild(this._folder(name, node, docs.length < 12))
        }
    }

    _folder(name, node, openByDefault) {
        const d = document.createElement('details')
        d.open = openByDefault
        const s = document.createElement('summary')
        const caret = document.createElement('span')
        caret.className = 'caret'
        caret.textContent = '▸'
        const label = document.createElement('span')
        label.textContent = name
        const count = document.createElement('span')
        count.className = 'n'
        count.textContent = this._countIn(node)
        s.append(caret, label, count)
        d.appendChild(s)
        for (const [child, sub] of [...node.dirs].sort((a, b) => a[0].localeCompare(b[0]))) {
            d.appendChild(this._folder(child, sub, openByDefault))
        }
        for (const f of node.files.sort((a, b) => a.file.localeCompare(b.file))) {
            d.appendChild(this._link(f))
        }
        return d
    }

    _link(doc) {
        const a = document.createElement('a')
        a.className = 'doc-link'
        a.setAttribute('href', `#${doc.caminho}`)
        a.dataset.path = doc.caminho
        a.textContent = doc.titulo
        const f = document.createElement('span')
        f.className = 'f'
        f.textContent = `${doc.file} · ${doc.linhas} lines`
        a.appendChild(f)
        return a
    }

    _renderRefs() {
        const host = this.$('#refs')
        for (const [name, url, what] of REFERENCES) {
            const a = document.createElement('a')
            a.setAttribute('href', url)
            a.textContent = name
            const d = document.createElement('span')
            d.className = 'd'
            d.textContent = what
            a.appendChild(d)
            host.appendChild(a)
        }
    }

    _filter(q) {
        const term = q.trim().toLowerCase()
        if (!term) { this._renderTree(this._docs); this._mark(); return }
        this._renderTree(this._docs.filter(
            d => d.caminho.toLowerCase().includes(term) || d.titulo.toLowerCase().includes(term)))
        this.$$('details').forEach(d => { d.open = true })
        this._mark()
    }

    /* --- the document ----------------------------------------------------- */
    _openFromHash() {
        const path = decodeURIComponent(location.hash.replace(/^#/, ''))
        if (path) this.open(path)
        else this._placeholder()
    }

    _placeholder() {
        this.$('#path').textContent = '—'
        this.$('#meta').textContent = ''
        const doc = this.$('#doc')
        doc.textContent = ''
        const p = document.createElement('p')
        p.className = 'empty'
        p.textContent = `${this._docs.length} documents. Pick one from the tree.`
        doc.appendChild(p)
    }

    async open(path) {
        /* Only ever read markdown inside this repository. A viewer that took an arbitrary path
           would happily render anything the server would serve. */
        if (path.includes('..') || !/\.md$/.test(path)) return this._placeholder()
        this._current = path
        this.$('#path').textContent = path
        this.$('#raw').setAttribute('href', this._root + path)
        this._mark()
        const doc = this.$('#doc')
        try {
            const r = await fetch(this._root + path)
            if (!r.ok) throw new Error(`HTTP ${r.status}`)
            const text = await r.text()
            this.$('#meta').textContent =
                `${text.split('\n').length} lines · ${text.split(/\s+/).length} words · ` +
                `${new Blob([text]).size} bytes`
            doc.innerHTML = window.marked ? window.marked.parse(text) : ''
            if (!window.marked) doc.textContent = text
            this._rewrite(path)
            doc.querySelectorAll('table').forEach(t => {
                const w = document.createElement('div')
                w.className = 'tablewrap'
                t.parentNode.insertBefore(w, t)
                w.appendChild(t)
            })
            this.emit('pt:doc.opened', { path })
        } catch (err) {
            /* A document the reader picked that would not open, with the tree already up. The
               component came up; this one file failed, and that is what the page says. */
            doc.textContent = `Could not read ${path}: ${err.message}`
        }
        this.$('.pane').scrollTop = 0
    }

    /* A relative link inside a document points at a file relative to THAT document, not to this
       page. Rewrite them so they keep working, and keep .md links inside this browser instead of
       downloading them — which is the whole point of having a browser. */
    _rewrite(path) {
        const dir = path.replace(/[^/]+$/, '')
        this.$$('#doc a[href]').forEach(a => {
            const h = a.getAttribute('href')
            if (!h || /^(https?:|mailto:|#)/.test(h)) return
            const target = new URL(dir + h, 'https://x/').pathname.replace(/^\//, '')
            if (/\.md$/.test(target)) a.setAttribute('href', `#${target}`)
            else a.setAttribute('href', this._root + target)
        })
    }

    _mark() {
        this.$$('a.doc-link').forEach(a => {
            a.setAttribute('aria-current', a.dataset.path === this._current ? 'true' : 'false')
        })
    }
}

customElements.define('pt-doc-browser', PtDocBrowser)

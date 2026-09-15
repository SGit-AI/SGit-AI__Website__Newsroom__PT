/**
 * pt-json-viewer — a data file of this site, read as data.
 *
 * Every article on this site is a folder, and the folder is linked from the article page. Before
 * this component, clicking `afirmacoes.json` handed the reader a raw document and left them to
 * make sense of it. What they actually want there is to SEE the claims: which are confirmed,
 * which source each one stands on, and what the hash is.
 *
 * So the viewer is not a generic pretty-printer. Keys this site gives meaning to are rendered as
 * what they mean — a state becomes a coloured chip, a source id becomes a link into the register,
 * a SHA-256 is shortened because nobody reads sixty-four characters. Everything else falls back
 * to ordinary structure, which is the honest default: a viewer that pretended to understand a key
 * it did not would be worse than one that showed the value.
 *
 * @module pt-json-viewer
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

/* Keys whose value is a state this site colours. The class name is the value itself, so a state
   the site adds later renders as a plain chip rather than breaking. */
const STATE_KEYS = new Set([
    'estado', 'estado_entregue', 'state', 'correspondencia', 'legivel', 'esquema_valido',
])
/* Keys whose value points at a frozen source in the register. */
const SOURCE_KEYS = new Set(['fonte', 'source', 'id_fonte'])
/* Keys long enough to be prose rather than a value — rendered in the reading face. */
const PROSE_KEYS = new Set([
    'nota', 'note', 'porque', 'porque_importa', 'o_que', 'texto', 'excerto', 'comentario',
    'o_que_e', 'o_que_dizem_as_fontes', 'ambito', 'a_afirmacao_honesta', 'entrada',
    'o_que_pode_afirmar_hoje', 'o_que_nao_pode', 'porque_existe_este_ficheiro',
    'aviso_sobre_esta_cronologia', 'como', 'nota_legibilidade', 'historia_sugerida',
])

class PtJsonViewer extends SgComponent {

    static jsUrl = import.meta.url

    get resourceName() { return 'pt-json-viewer' }

    static get observedAttributes() { return ['src'] }

    attributeChangedCallback(name, _old, value) {
        if (name === 'src' && this.shadowRoot && value) this.load(value)
    }

    /* `async`, and the load is AWAITED. The base class sets `data-estado="pronto"` once onReady
       returns, and its comment says that means the component "has actually finished loading
       whatever it loads". A fire-and-forget load made that untrue here: `pronto` landed when the
       shell mounted, and the render gate could read a component as up while its fetch was still
       in flight — the same false-healthy signal `falhou()` was added to remove, one level down. */
    async onReady() {
        this._root = this.getAttribute('site-root') || '../'
        this.$('#expand').addEventListener('click', () => this._all(true))
        this.$('#collapse').addEventListener('click', () => this._all(false))
        window.addEventListener('hashchange', () => this._fromHash())
        const src = this.getAttribute('src')
        if (src) await this.load(src)
        else await this._fromHash()
    }

    /* Returns the load's promise so the caller can await it. Without the `return`, `onReady`
       awaiting this would await `undefined` and go straight to «pronto» with nothing loaded. */
    _fromHash() {
        const h = decodeURIComponent(location.hash.replace(/^#/, ''))
        if (h && /\.json$/.test(h)) return this.load(h)
    }

    async load(src) {
        if (src.includes('..') || !/\.(json|nt)$/.test(src)) return
        this._src = src
        this.$('#title').textContent = src.split('/').slice(-2).join('/')
        this.$('#raw').setAttribute('href', src)
        const body = this.$('#body')
        body.textContent = 'loading…'
        try {
            const r = await fetch(src)
            if (!r.ok) throw new Error(`HTTP ${r.status}`)
            const text = await r.text()
            this.$('#meta').textContent =
                `${new Blob([text]).size} bytes · ${text.split('\n').length} lines`
            body.textContent = ''
            if (/\.nt$/.test(src)) {
                const pre = document.createElement('pre')
                pre.textContent = text
                body.appendChild(pre)
            } else {
                body.appendChild(this._render(JSON.parse(text), null, true))
            }
            this.emit('pt:json.opened', { src })
        } catch (err) {
            /* This is the load path — onReady calls load() with the file the page named. A
               viewer that cannot read the file it was told to show did not come up. */
            this.falhou(err.message)
            body.textContent = `Could not read ${src}: ${err.message}`
        }
    }

    _all(open) {
        this.$$('.children').forEach(c => c.classList.toggle('hidden', !open))
        this.$$('.tog').forEach(t => { t.textContent = open ? '▾' : '▸' })
    }

    /* --- rendering -------------------------------------------------------- */
    _render(value, key, top = false) {
        const row = document.createElement('div')
        row.className = top ? 'row top' : 'row'

        if (value !== null && typeof value === 'object') {
            const entries = Array.isArray(value)
                ? value.map((v, i) => [i, v]) : Object.entries(value)
            const head = document.createElement('div')
            const tog = document.createElement('span')
            tog.className = 'tog'
            tog.textContent = '▾'
            head.appendChild(tog)
            if (key !== null) {
                const k = document.createElement('span')
                k.className = 'k'
                k.textContent = `${key}: `
                head.appendChild(k)
            }
            const count = document.createElement('span')
            count.className = 'count'
            count.textContent = Array.isArray(value)
                ? `[${entries.length}]` : `{${entries.length}}`
            head.appendChild(count)
            row.appendChild(head)

            const kids = document.createElement('div')
            kids.className = 'children'
            /* Deep structures start collapsed: a reader opening a delivery wants the shape
               first, not four hundred lines of it. */
            if (!top && entries.length > 12) kids.classList.add('hidden')
            for (const [k, v] of entries) kids.appendChild(this._render(v, k))
            row.appendChild(kids)

            tog.addEventListener('click', () => {
                const hidden = kids.classList.toggle('hidden')
                tog.textContent = hidden ? '▸' : '▾'
            })
            if (kids.classList.contains('hidden')) tog.textContent = '▸'
            return row
        }

        if (key !== null) {
            const k = document.createElement('span')
            k.className = 'k'
            k.textContent = `${key}: `
            row.appendChild(k)
        }
        row.appendChild(this._scalar(value, key))
        return row
    }

    _scalar(value, key) {
        if (value === null) {
            const s = document.createElement('span')
            s.className = 'nul'
            s.textContent = 'null'
            return s
        }
        if (typeof value === 'boolean') {
            const s = document.createElement('span')
            s.className = 'b'
            s.textContent = String(value)
            return s
        }
        if (typeof value === 'number') {
            const s = document.createElement('span')
            s.className = 'n'
            s.textContent = String(value)
            return s
        }
        const text = String(value)

        if (STATE_KEYS.has(key)) {
            const s = document.createElement('span')
            s.className = `chip ${text.replace(/[^a-z_]/gi, '')}`
            s.textContent = text
            return s
        }
        if (SOURCE_KEYS.has(key) && /\//.test(text)) {
            const a = document.createElement('a')
            a.className = 'src'
            a.setAttribute('href', `${this._root}registo/#${text}`)
            a.textContent = text
            return a
        }
        if (/^[0-9a-f]{40,}$/.test(text)) {
            const s = document.createElement('span')
            s.className = 'hash'
            s.title = text
            s.textContent = `${text.slice(0, 16)}… (${text.length} hex)`
            return s
        }
        if (/^https?:\/\//.test(text)) {
            const a = document.createElement('a')
            a.className = 'src'
            a.setAttribute('href', text)
            a.setAttribute('rel', 'nofollow noopener')
            a.textContent = text
            return a
        }
        const s = document.createElement('span')
        s.className = (PROSE_KEYS.has(key) || text.length > 90) ? 'prose' : 's'
        s.textContent = text
        return s
    }
}

customElements.define('pt-json-viewer', PtJsonViewer)

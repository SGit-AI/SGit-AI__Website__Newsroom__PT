/**
 * pt-api-console — the OpenAPI document of this site, with a button that calls it.
 *
 * A console that only describes an API is a document with extra steps. This one issues the
 * request from the reader's browser and shows the bytes that came back, because the claim being
 * made — that every page of this site is also data — is only worth making if a reader can check
 * it without leaving the page.
 *
 * It is honest about what it is: the API is GET-only because every path is a file on disk, and
 * there is no server. That means this console cannot demonstrate authentication, rate limits or
 * a write, because none of those exist. It can demonstrate the only thing that does — that the
 * paths in the document return the documents the site is built from.
 *
 * Reads `/api/v1/openapi.json`. Nothing here is hand-listed: add a collection in `build/api.py`
 * and it appears here.
 *
 * @module pt-api-console
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

class PtApiConsole extends SgComponent {

    static jsUrl = import.meta.url

    get resourceName() { return 'pt-api-console' }

    onReady() {
        this._root = this.getAttribute('site-root') || '../'
        this._ops = []
        this.$('#q').addEventListener('input', e => this._filter(e.target.value))
        this._load()
    }

    async _load() {
        try {
            const spec = await (await fetch(`${this._root}api/v1/openapi.json`)).json()
            this._spec = spec
            this._base = (spec.servers?.[0]?.url || '').replace(/^https?:\/\/[^/]+/, '')
            for (const [path, methods] of Object.entries(spec.paths)) {
                for (const [method, op] of Object.entries(methods)) {
                    this._ops.push({ path, method: method.toUpperCase(), ...op })
                }
            }
            this._ops.sort((a, b) => a.path.localeCompare(b.path))
        } catch (err) {
            this.falhou(err.message)
            this.$('#list').textContent = `openapi.json did not load: ${err.message}`
            return
        }
        this._render(this._ops)
    }

    _render(ops) {
        const host = this.$('#list')
        host.textContent = ''
        for (const op of ops) {
            const b = document.createElement('button')
            b.type = 'button'
            b.className = 'op'
            b.dataset.path = op.path
            const m = document.createElement('span')
            m.className = 'm'
            m.textContent = op.method
            const p = document.createElement('span')
            p.className = 'p'
            p.textContent = op.path
            const s = document.createElement('span')
            s.className = 's'
            s.textContent = op.summary || ''
            b.append(m, p, s)
            b.addEventListener('click', () => this._select(op))
            host.appendChild(b)
        }
    }

    _filter(q) {
        const t = q.trim().toLowerCase()
        this._render(!t ? this._ops : this._ops.filter(
            o => o.path.toLowerCase().includes(t) || (o.summary || '').toLowerCase().includes(t)))
    }

    _select(op) {
        this._current = op
        this.$$('.op').forEach(b => {
            b.setAttribute('aria-current', b.dataset.path === op.path ? 'true' : 'false')
        })
        const d = this.$('#detail')
        d.textContent = ''

        const h = document.createElement('h3')
        h.textContent = `${op.method} ${this._base}${op.path}`
        d.appendChild(h)

        const desc = document.createElement('p')
        desc.className = 'desc'
        desc.innerHTML = (op.description || op.summary || '')
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '<br><br>')
        d.appendChild(desc)

        const params = document.createElement('div')
        params.className = 'params'
        const idParam = (op.parameters || []).find(p => p.name === 'id')
        if (idParam) {
            const label = document.createElement('label')
            label.textContent = 'id'
            const examples = Object.keys(idParam.examples || {})
            let field
            if (examples.length) {
                field = document.createElement('select')
                for (const ex of examples) {
                    const o = document.createElement('option')
                    o.value = ex
                    o.textContent = ex
                    field.appendChild(o)
                }
                const other = document.createElement('option')
                other.value = '__other'
                other.textContent = '— type one —'
                field.appendChild(other)
            } else {
                field = document.createElement('input')
                field.className = 'pv'
            }
            field.id = 'idv'
            const free = document.createElement('input')
            free.className = 'pv'
            free.id = 'idfree'
            free.placeholder = 'id'
            free.style.display = examples.length ? 'none' : ''
            if (field.tagName === 'SELECT') {
                field.addEventListener('change', () => {
                    free.style.display = field.value === '__other' ? '' : 'none'
                    this._preview()
                })
            }
            free.addEventListener('input', () => this._preview())
            params.append(label, field, free)
        }
        const go = document.createElement('button')
        go.className = 'go'
        go.type = 'button'
        go.textContent = 'send request'
        go.addEventListener('click', () => this._send())
        params.appendChild(go)
        d.appendChild(params)

        const url = document.createElement('p')
        url.className = 'url'
        url.id = 'urlp'
        d.appendChild(url)

        const out = document.createElement('div')
        out.id = 'out'
        d.appendChild(out)
        this._preview()
    }

    _url() {
        let p = this._current.path
        if (p.includes('{id}')) {
            const sel = this.$('#idv')
            const free = this.$('#idfree')
            const v = (sel && sel.tagName === 'SELECT' && sel.value !== '__other')
                ? sel.value : (free?.value || sel?.value || '')
            p = p.replace('{id}', encodeURIComponent(v))
        }
        return `${this._root}api/v1${p}`.replace(/([^:])\/\//g, '$1/')
    }

    _preview() {
        const p = this.$('#urlp')
        if (!p) return
        p.textContent = ''
        const a = document.createElement('a')
        const u = this._url()
        a.setAttribute('href', u)
        a.textContent = u
        p.append(document.createTextNode('GET '), a)
    }

    async _send() {
        const out = this.$('#out')
        const u = this._url()
        out.textContent = '…'
        const t0 = performance.now()
        try {
            const r = await fetch(u)
            const text = await r.text()
            const ms = Math.round(performance.now() - t0)
            out.textContent = ''
            const st = document.createElement('div')
            st.className = `status${r.ok ? '' : ' bad'}`
            st.textContent = `${r.status} ${r.statusText} · ${new Blob([text]).size} bytes · ${ms} ms`
            out.appendChild(st)
            const pre = document.createElement('pre')
            try { pre.textContent = JSON.stringify(JSON.parse(text), null, 2) }
            catch { pre.textContent = text }
            out.appendChild(pre)
            this.emit('pt:api.called', { url: u, status: r.status })
        } catch (err) {
            /* Um pedido que o LEITOR fez e que falhou. Não é o componente que está em baixo — numa
               consola de API, ver um pedido falhar é metade da utilidade. Não se marca `falhou()`:
               esse atributo quer dizer «este componente não subiu», e alargá-lo apagaria a
               distinção que o torna útil a quem confere a página. */
            out.textContent = `Request failed: ${err.message}`
        }
    }
}

customElements.define('pt-api-console', PtApiConsole)

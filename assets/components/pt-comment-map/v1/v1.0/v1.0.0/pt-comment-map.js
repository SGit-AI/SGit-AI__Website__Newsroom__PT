/**
 * pt-comment-map — who said what about an article, and which file it came out of.
 *
 * Two views of one thing. Above, the grid: agent by kind of contribution, with the numbers. Below,
 * the stream in order, filterable by agent. The grid answers "who worked on this"; the stream
 * answers "and what did they say".
 *
 * Every entry shows its `de` field — the file and path it was derived from. That is not a
 * technical detail left on display out of laziness: it is the difference between a record of work
 * and a staging of one. A comment that does not say where it came from is indistinguishable from
 * an invented one, and on a site built on provenance that distinction is the only one that counts.
 *
 * Reads `comentarios.json` from the article's folder, or `dados/comentarios.json` for the
 * aggregate view in the operations console. The two have the same shape, deliberately.
 *
 * @module pt-comment-map
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

/* States that count as still open. A state this map does not know counts as closed and still
   appears in the stream — the opposite would let a new value spawn an alert bar on its own. */
const ABERTOS = new Set(['aberto', 'por_decidir', 'por_rever', 'por_verificar'])

class PtCommentMap extends SgComponent {

    static jsUrl = import.meta.url

    get resourceName() { return 'pt-comment-map' }

    async onReady() {
        this._src = this.getAttribute('src')
        this._agente = null
        try {
            const d = await fetch(this._src).then(r => {
                if (!r.ok) throw new Error(`${r.status} ao pedir ${this._src}`)
                return r.json()
            })
            this._d = d
            this._fluxo = d.fluxo || []
            this._especies = Object.keys(d.especies || {})
            this._render()
        } catch (err) {
            this.falhou(err.message)
            this.$('#title').textContent = 'o registo de trabalho não carregou'
            this.$('#nota').className = 'nota erro'
            this.$('#nota').textContent = `${err.message}`
        }
    }

    _nomeAgente(id) {
        const a = (this._d.agentes || {})[id]
        return a ? a.nome : id
    }

    _fornecedor(id) {
        const a = (this._d.agentes || {})[id]
        return a ? `${a.especie} · ${a.fornecedor}` : ''
    }

    _grelha() {
        const alvo = this.$('#mapa')
        alvo.textContent = ''
        const agentes = Object.keys(this._d.por_agente || {})
        if (!agentes.length) return

        const tabela = document.createElement('table')
        const thead = document.createElement('thead')
        const tr = document.createElement('tr')
        for (const t of ['Agente', ...this._especies, 'Total', 'Por fechar']) {
            const th = document.createElement('th')
            th.textContent = t
            tr.appendChild(th)
        }
        thead.appendChild(tr)
        tabela.appendChild(thead)

        const tbody = document.createElement('tbody')
        for (const id of agentes) {
            const linha = document.createElement('tr')
            const quem = document.createElement('td')
            const nome = document.createElement('span')
            nome.className = 'quem'
            nome.textContent = this._nomeAgente(id)
            const forn = document.createElement('span')
            forn.className = 'forn'
            forn.textContent = this._fornecedor(id)
            quem.append(nome, forn)
            linha.appendChild(quem)

            const d = this._d.por_agente[id]
            for (const esp of this._especies) {
                const td = document.createElement('td')
                const n = (d.especies || {})[esp] || 0
                td.className = n ? 'n' : 'n zero'
                td.textContent = n ? String(n) : '·'
                linha.appendChild(td)
            }
            for (const v of [d.total, d.abertos]) {
                const td = document.createElement('td')
                td.className = 'n'
                td.textContent = String(v)
                linha.appendChild(td)
            }
            tbody.appendChild(linha)
        }
        tabela.appendChild(tbody)
        alvo.appendChild(tabela)
    }

    _filtros() {
        const alvo = this.$('#filtros')
        alvo.textContent = ''
        const ids = [null, ...Object.keys(this._d.por_agente || {})]
        for (const id of ids) {
            const b = document.createElement('button')
            b.type = 'button'
            b.textContent = id === null ? 'todos' : this._nomeAgente(id)
            b.setAttribute('aria-pressed', String(this._agente === id))
            b.addEventListener('click', () => {
                this._agente = id
                this._render()
                this.emit('pt-comment-map:filtered', { agente: id })
            })
            alvo.appendChild(b)
        }
    }

    _lista() {
        const alvo = this.$('#fluxo')
        alvo.textContent = ''
        const itens = this._agente
            ? this._fluxo.filter(c => c.agente === this._agente)
            : this._fluxo
        for (const c of itens) {
            const li = document.createElement('li')
            const aberto = ABERTOS.has(c.estado)
            if (aberto) li.className = 'aberto'

            const cab = document.createElement('div')
            cab.className = 'cab'
            const quem = document.createElement('span')
            quem.textContent = this._nomeAgente(c.agente)
            const esp = document.createElement('span')
            esp.className = 'e'
            esp.textContent = c.especie
            const est = document.createElement('span')
            est.className = aberto ? 'a' : ''
            est.textContent = c.estado
            cab.append(quem, esp, est)
            if (c.quando) {
                const q = document.createElement('span')
                q.textContent = c.quando
                cab.appendChild(q)
            }
            if (c.agente_verbatim) {
                const m = document.createElement('span')
                m.textContent = c.agente_verbatim
                cab.appendChild(m)
            }

            const txt = document.createElement('div')
            txt.className = 'txt'
            txt.textContent = c.texto || ''

            li.append(cab, txt)
            if (c.porque) {
                const pq = document.createElement('div')
                pq.className = 'pq'
                pq.textContent = c.porque
                li.appendChild(pq)
            }
            const de = document.createElement('div')
            de.className = 'de'
            de.textContent = `derivado de ${c.de}`
            li.appendChild(de)
            alvo.appendChild(li)
        }
    }

    _render() {
        const d = this._d
        this.$('#title').textContent = d.artigo
            ? `O trabalho dos agentes sobre este artigo`
            : `O trabalho dos agentes, em todos os artigos`
        this.$('#meta').textContent =
            `${d.contagem} entradas · ${d.abertos} por fechar · ` +
            `${Object.keys(d.por_agente || {}).length} agentes · atualizado ${d.atualizado || '—'}`
        this._grelha()
        this._filtros()
        this._lista()
        this.$('#nota').className = 'nota'
        this.$('#nota').textContent =
            'Nenhuma destas entradas foi escrita para aqui. Todas são derivadas de ficheiros que ' +
            'já existem no repositório, e cada uma diz de qual — escrever comentários e ' +
            'atribuí-los a um agente seria fabricar proveniência.'
    }
}

customElements.define('pt-comment-map', PtCommentMap)

/**
 * pt-comment-map — quem disse o quê sobre um artigo, e de que ficheiro isso saiu.
 *
 * Duas vistas de uma coisa só. Em cima, a grelha: agente por espécie de contribuição, com os
 * números. Em baixo, o fluxo por ordem, filtrável por agente. A grelha responde a «quem trabalhou
 * nisto»; o fluxo responde a «e o que é que disseram».
 *
 * Cada entrada mostra o campo `de` — o ficheiro e o caminho de onde foi derivada. Isso não é um
 * detalhe técnico deixado à vista por preguiça: é a diferença entre um registo de trabalho e uma
 * encenação de um. Um comentário que não diga de onde veio não é distinguível de um comentário
 * inventado, e num sítio construído sobre proveniência essa distinção é a única que importa.
 *
 * Lê `comentarios.json` da pasta do artigo, ou `dados/comentarios.json` para a vista agregada da
 * consola de operações. As duas têm a mesma forma, de propósito.
 *
 * @module pt-comment-map
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

/* Estados que contam como por fechar. Um estado que este mapa não conheça conta como fechado e
   aparece na mesma no fluxo — o contrário faria uma barra de alerta nascer de um valor novo. */
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

/**
 * pt-entity-graph — a node's neighbourhood, loaded from the graph and read aloud.
 *
 * An entity page already carries its sentences, generated at build time. This component does
 * something the build cannot: it loads `api/v1/graph.json` and `api/v1/ontology.json` AT THE MOMENT
 * the page is opened, and assembles the sentences from what is there now. If the graph changes and
 * the page is not rebuilt, this is where you see it.
 *
 * The sentences are not written in this file. Every ontology edge carries a `leitura` with `{s}`
 * and `{t}` — «{s} fala em {t}», «{t} recebe {s}» — and the component only substitutes. This is
 * why §6 of the brief made every verb carry a reading and a named inverse: a graph with
 * `relacionado_com` would give this component nothing to say.
 *
 * What it does NOT do: draw a web. A force diagram with three hundred nodes is pretty and
 * unreadable, and this site's reader is a machine as often as a person. A list of Portuguese
 * sentences reads in both cases.
 *
 * @module pt-entity-graph
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

/* Types that have an entity page. Must agree with TIPOS_COM_PAGINA in build/entidades.py; when it
   does not, the worst that happens is an unlinked name — never a broken link, because a path is
   only written for a type in this list. */
const COM_PAGINA = {
    Pessoa: 'pessoa', Organizacao: 'organizacao', Instituicao: 'instituicao', Editor: 'editor',
    Evento: 'evento', Local: 'local', Palco: 'palco', Tema: 'tema', Tecnologia: 'tecnologia',
    Setor: 'setor', Produto: 'produto', Servico: 'servico', Ideia: 'ideia',
}

class PtEntityGraph extends SgComponent {

    static jsUrl = import.meta.url

    get resourceName() { return 'pt-entity-graph' }

    async onReady() {
        this._no = this.getAttribute('no') || ''
        this._raiz = this.getAttribute('raiz') || ''
        this.$('#inversas').addEventListener('change', () => this._render())
        try {
            const [grafo, onto] = await Promise.all([
                fetch(`${this._raiz}api/v1/graph.json`).then(r => r.json()),
                fetch(`${this._raiz}api/v1/ontology.json`).then(r => r.json()),
            ])
            this._nos = new Map(grafo.nos.map(n => [n.id, n]))
            this._arestas = grafo.arestas
            this._leituras = new Map(
                onto.arestas.map(a => [`${a.verbo}|${a.dominio}|${a.alcance}`, a]))
            this._atualizado = grafo.atualizado || ''
            this._render()
        } catch (err) {
            this.falhou(err.message)
            this.$('#title').textContent = 'o grafo não carregou'
            this.$('#nota').className = 'nota erro'
            this.$('#nota').textContent =
                `${err.message}. As frases acima foram geradas na construção e continuam certas; ` +
                `o que falhou foi a leitura ao vivo de api/v1/graph.json.`
        }
    }

    /** The address of a node's page, or null if that type has no page. */
    _url(id) {
        const n = this._nos.get(id)
        if (!n) return null
        const tipo = COM_PAGINA[n.tipo]
        if (!tipo) return null
        const resto = id.includes(':') ? id.slice(id.indexOf(':') + 1) : id
        return `${this._raiz}entidades/${tipo}/${resto}/`
    }

    _rotulo(id, forte) {
        const n = this._nos.get(id)
        const texto = n ? n.rotulo : id
        const url = forte ? null : this._url(id)
        const el = document.createElement(forte ? 'b' : (url ? 'a' : 'span'))
        if (url) { el.setAttribute('href', url); el.className = 'no' }
        el.textContent = texto
        return el
    }

    /** One edge, assembled as DOM nodes rather than HTML: the label comes from data, never interpolated. */
    _frase(a, souOrigem) {
        const o = this._nos.get(a.origem), d = this._nos.get(a.destino)
        if (!o || !d) return null
        const decl = this._leituras.get(`${a.verbo}|${o.tipo}|${d.tipo}`)
        if (!decl) return null
        const modelo = souOrigem ? decl.leitura : decl.leitura_inversa
        const li = document.createElement('li')
        /* Split on the placeholder and interleave: the template text stays text, the labels are
           nodes. A label containing `<` is then a character and never a tag. */
        for (const troco of modelo.split(/(\{s\}|\{t\})/)) {
            if (troco === '{s}') li.appendChild(this._rotulo(a.origem, souOrigem))
            else if (troco === '{t}') li.appendChild(this._rotulo(a.destino, !souOrigem))
            else if (troco) li.appendChild(document.createTextNode(troco))
        }
        return li
    }

    _render() {
        const corpo = this.$('#corpo')
        corpo.textContent = ''
        const inversas = this.$('#inversas').checked

        const meu = this._nos.get(this._no)
        this.$('#title').textContent = meu ? meu.rotulo : this._no
        const saida = this._arestas.filter(a => a.origem === this._no)
        const entrada = inversas ? this._arestas.filter(a => a.destino === this._no) : []
        this.$('#meta').textContent =
            `${saida.length + entrada.length} arestas · ${this._nos.size} nós no grafo`

        /* Grouped by verb, because that is how it reads: all the sessions at once, all the
           sources at once. A hundred sentences in file order is not legible. */
        const grupos = new Map()
        for (const [arr, souOrigem] of [[saida, true], [entrada, false]]) {
            for (const a of arr) {
                const li = this._frase(a, souOrigem)
                if (!li) continue
                const o = this._nos.get(a.origem), d = this._nos.get(a.destino)
                const decl = this._leituras.get(`${a.verbo}|${o.tipo}|${d.tipo}`)
                const chave = souOrigem ? decl.verbo : decl.inverso
                if (!grupos.has(chave)) grupos.set(chave, [])
                grupos.get(chave).push(li)
            }
        }

        if (!grupos.size) {
            const p = document.createElement('p')
            p.className = 'nota'
            p.textContent = 'Este nó não tem arestas no grafo carregado.'
            corpo.appendChild(p)
        }

        for (const [verbo, itens] of [...grupos].sort((a, b) => b[1].length - a[1].length)) {
            const g = document.createElement('div')
            g.className = 'grupo'
            const h = document.createElement('div')
            h.className = 'verbo'
            h.textContent = `${verbo} · ${itens.length}`
            const ul = document.createElement('ul')
            for (const li of itens) ul.appendChild(li)
            g.append(h, ul)
            corpo.appendChild(g)
        }

        this.$('#nota').className = 'nota'
        this.$('#nota').textContent =
            `Carregado de api/v1/graph.json e api/v1/ontology.json quando abriu esta página` +
            `${this._atualizado ? `, grafo de ${this._atualizado}` : ''}. As frases são as ` +
            `leituras publicadas na ontologia, com os rótulos substituídos: nenhuma frase está ` +
            `escrita neste componente.`
        this.emit('pt-entity-graph:rendered', { no: this._no, arestas: saida.length + entrada.length })
    }
}

customElements.define('pt-entity-graph', PtEntityGraph)

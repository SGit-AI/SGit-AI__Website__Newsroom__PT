/**
 * pt-entity-graph — a vizinhança de um nó, carregada do grafo e lida em voz alta.
 *
 * A página de uma entidade já traz as frases dela, geradas na construção. Este componente faz uma
 * coisa diferente e que a construção não pode fazer: carrega `api/v1/graph.json` e
 * `api/v1/ontology.json` NO MOMENTO em que a página é aberta, e monta as frases a partir do que
 * lá está agora. Se o grafo mudar e a página não for reconstruída, é aqui que se vê.
 *
 * As frases não são escritas neste ficheiro. Cada aresta da ontologia traz uma `leitura` com `{s}`
 * e `{t}` — «{s} fala em {t}», «{t} recebe {s}» — e o componente limita-se a substituir. É a razão
 * pela qual o §6 do resumo obrigou cada verbo a ter uma leitura e um inverso nomeado: um grafo com
 * `relacionado_com` não teria nada para este componente dizer.
 *
 * O que ele NÃO faz: não desenha uma teia. Um diagrama de força com trezentos nós é bonito e
 * ilegível, e este site tem um leitor que é uma máquina tantas vezes como é uma pessoa. Uma lista
 * de frases portuguesas lê-se nos dois casos.
 *
 * @module pt-entity-graph
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

/* Tipos que têm página de entidade. Tem de concordar com TIPOS_COM_PAGINA em build/entidades.py;
   quando não concorda, o pior que acontece é um nome sem ligação — nunca uma ligação partida,
   porque o caminho só se escreve para um tipo desta lista. */
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
            this.$('#title').textContent = 'o grafo não carregou'
            this.$('#nota').className = 'nota erro'
            this.$('#nota').textContent =
                `${err.message}. As frases acima foram geradas na construção e continuam certas; ` +
                `o que falhou foi a leitura ao vivo de api/v1/graph.json.`
        }
    }

    /** O endereço da página de um nó, ou null se aquele tipo não tem página. */
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
        if (url) el.setAttribute('href', url)
        el.textContent = texto
        return el
    }

    /** Uma aresta, montada como nós e não como HTML: o rótulo vem de dados e não se interpola. */
    _frase(a, souOrigem) {
        const o = this._nos.get(a.origem), d = this._nos.get(a.destino)
        if (!o || !d) return null
        const decl = this._leituras.get(`${a.verbo}|${o.tipo}|${d.tipo}`)
        if (!decl) return null
        const modelo = souOrigem ? decl.leitura : decl.leitura_inversa
        const li = document.createElement('li')
        /* Partir pelo marcador e ir intercalando: o texto do modelo é texto, os rótulos são nós.
           Assim um rótulo que contenha `<` é um caractere e nunca uma marca. */
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

        /* Agrupadas por verbo, porque é assim que se lê: todas as sessões de uma vez, todas as
           fontes de uma vez. Uma lista de cem frases por ordem de ficheiro não é legível. */
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

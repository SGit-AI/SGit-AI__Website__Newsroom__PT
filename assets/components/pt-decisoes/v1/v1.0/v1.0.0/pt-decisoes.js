/**
 * pt-decisoes — the editor's decisions, captured in the browser and carried out by hand.
 *
 * WHY THIS EXISTS AND WHY IT DOES NOT WRITE ANYTHING. Every decision that changes what this site
 * says is a file in the repository, written by a person: `redacao/revisoes/<delivery>.json` for a
 * research item, `estado: publicado` in an `artigo.json` for a story. This site is static and
 * cannot write to git, and it must not pretend otherwise — a console that looked like it recorded
 * a decision while recording nothing would be worse than no console at all.
 *
 * So the division is explicit: the browser holds the editor's WORDS, and an agent turns them into
 * FILES. This component captures a verdict, a comment and a reaction per open question, keeps them
 * in localStorage so a review can be interrupted and resumed, and then hands back a block of text
 * addressed to the agent that will do the work. Nothing here is a decision until the file exists.
 *
 * WHY localStorage AND NOT A FORM POST. There is nowhere to post to. The same constraint that
 * makes this publication auditable — a static site, built from files, with no server holding
 * state — means the only place a half-finished review can live is the editor's own browser. It is
 * per-device and per-browser on purpose: this is a scratchpad, not a record. The record is git.
 *
 * WHAT IT REFUSES TO DO. It does not submit, it does not phone home, and it does not mark anything
 * as decided. The one thing it asserts is on the copy button: what you are about to paste is your
 * words, unedited, next to the identifiers an agent needs to find the right file.
 *
 * @module pt-decisoes
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

const CHAVE = 'pt-revisao/v1'

/* The verdicts. `adiar` is the safe default and the one that needs no justification: an item with
 * no decision stays out of everything, which is the state the quarantine gate enforces anyway. */
const VEREDICTOS = [
    { id: 'aprovar',  rotulo: 'Aprovar',          classe: 'ok' },
    { id: 'rejeitar', rotulo: 'Rejeitar',         classe: 'miss' },
    { id: 'adiar',    rotulo: 'Deixar por rever', classe: '' },
]

/* Reactions are not verdicts. They are how the editor tells an agent what KIND of attention a
 * thing needs, which is often the more useful signal and is lost entirely in a yes/no. */
const REACOES = [
    { id: 'concordo',   rotulo: 'Concordo' },
    { id: 'duvida',     rotulo: 'Tenho dúvidas' },
    { id: 'investigar', rotulo: 'Investigar mais' },
    { id: 'urgente',    rotulo: 'É urgente' },
    { id: 'discordo',   rotulo: 'Discordo' },
]

export class PtDecisoes extends SgComponent {

    static jsUrl = import.meta.url

    get resourceName() { return 'pt-decisoes' }

    /** Read the saved review. A browser with site data blocked throws here, and a scratchpad that
     *  cannot save is still a usable scratchpad — so it degrades rather than failing. */
    ler() {
        try { return JSON.parse(localStorage.getItem(CHAVE) || '{}') } catch { return {} }
    }

    guardar(estado) {
        try { localStorage.setItem(CHAVE, JSON.stringify(estado)) } catch { /* private window */ }
    }

    onReady() {
        // THE DATA COMES IN A CHILD <script type="application/json">, NOT IN AN ATTRIBUTE, and the
        // render gate is why. An attribute's value is entity-decoded by the HTML parser before any
        // script sees it, so a `&quot;` inside server-escaped markup became a bare `"` AFTER
        // JSON.stringify had already escaped the real ones — valid HTML, corrupt JSON, and a
        // component that failed on the one page it was written for. A script block is raw text: the
        // parser hands it over untouched.
        let itens
        try {
            const bloco = this.querySelector('script[type="application/json"]')
            itens = JSON.parse(bloco ? bloco.textContent : (this.getAttribute('itens') || '[]'))
        } catch (err) {
            this.falhou(`itens não são JSON válido: ${err.message}`)
            this.shadowRoot.getElementById('lista').textContent =
                'Esta página não conseguiu ler a lista de decisões.'
            return
        }
        this.itens = itens
        this.estado = this.ler()
        this.desenhar()
    }

    desenhar() {
        const raiz = this.shadowRoot
        const lista = raiz.getElementById('lista')
        lista.textContent = ''

        for (const it of this.itens) {
            const guardado = this.estado[it.id] || {}
            const bloco = document.createElement('div')
            bloco.className = 'd'
            bloco.innerHTML = `
              <div class="d__topo">
                <span class="para">para ${it.para}</span>
                <span class="id">${it.id}</span>
              </div>
              <h3 class="d__t">${it.pergunta}</h3>
              <div class="d__ctx">${it.contexto || ''}</div>
              <div class="v" role="group" aria-label="Veredicto"></div>
              <div class="r" role="group" aria-label="Reação"></div>
              <label class="lbl" for="c-${it.id}">O seu comentário, nas suas palavras</label>
              <textarea id="c-${it.id}" rows="3" placeholder="Fica no ficheiro de revisão,
tal como o escrever."></textarea>`

            const cv = bloco.querySelector('.v')
            for (const v of VEREDICTOS) {
                const b = document.createElement('button')
                b.type = 'button'
                b.className = `chip ${v.classe}`
                b.textContent = v.rotulo
                b.setAttribute('aria-pressed', String(guardado.veredicto === v.id))
                b.addEventListener('click', () => {
                    const e = this.ler()
                    e[it.id] = { ...(e[it.id] || {}), veredicto: v.id, quando: new Date().toISOString() }
                    this.estado = e
                    this.guardar(e)
                    this.desenhar()
                })
                cv.appendChild(b)
            }

            const cr = bloco.querySelector('.r')
            const reacoes = guardado.reacoes || []
            for (const r of REACOES) {
                const b = document.createElement('button')
                b.type = 'button'
                b.className = 'chip fina'
                b.textContent = r.rotulo
                b.setAttribute('aria-pressed', String(reacoes.includes(r.id)))
                b.addEventListener('click', () => {
                    const e = this.ler()
                    const atuais = new Set((e[it.id] || {}).reacoes || [])
                    atuais.has(r.id) ? atuais.delete(r.id) : atuais.add(r.id)
                    e[it.id] = { ...(e[it.id] || {}), reacoes: [...atuais] }
                    this.estado = e
                    this.guardar(e)
                    this.desenhar()
                })
                cr.appendChild(b)
            }

            const ta = bloco.querySelector('textarea')
            ta.value = guardado.comentario || ''
            ta.addEventListener('input', () => {
                const e = this.ler()
                e[it.id] = { ...(e[it.id] || {}), comentario: ta.value }
                this.estado = e
                this.guardar(e)
                this.contar()
            })
            lista.appendChild(bloco)
        }
        this.montarCopias()
        this.contar()
    }

    /** One decision as the text an agent reads. The identifiers come first because they are what
     *  the agent needs to find the file; the editor's words come last because they are what it
     *  must not paraphrase. */
    texto(it) {
        const g = this.estado[it.id] || {}
        const v = VEREDICTOS.find(x => x.id === g.veredicto)
        const r = (g.reacoes || []).map(id => (REACOES.find(x => x.id === id) || {}).rotulo)
        const linhas = [
            `## ${it.id}`,
            `ficheiro: ${it.ficheiro}`,
            `pergunta: ${it.pergunta}`,
            `veredicto: ${v ? v.rotulo : '— (sem decisão)'}`,
        ]
        if (r.length) linhas.push(`reações: ${r.join(', ')}`)
        linhas.push(`comentário do editor: ${g.comentario ? g.comentario.trim() : '—'}`)
        return linhas.join('\n')
    }

    montarCopias() {
        const raiz = this.shadowRoot
        const caixa = raiz.getElementById('copias')
        caixa.textContent = ''
        const agentes = [...new Set(this.itens.map(i => i.para))]

        const fazer = (rotulo, itens) => {
            const b = document.createElement('button')
            b.type = 'button'
            b.className = 'copiar'
            b.textContent = rotulo
            b.addEventListener('click', async () => {
                const decididos = itens.filter(i => (this.estado[i.id] || {}).veredicto
                                                 || (this.estado[i.id] || {}).comentario)
                const corpo = [
                    `# Decisões do editor de registo — ${new Date().toISOString().slice(0, 10)}`,
                    `editor: Dinis Cruz`,
                    `decisões nesta mensagem: ${decididos.length} de ${itens.length}`,
                    '',
                    'Estas são as palavras do editor, por copiar tal como estão para o ficheiro que',
                    'cada decisão nomeia. Uma decisão sem veredicto fica por rever, que é o estado',
                    'seguro, e não deve ser inventada.',
                    '',
                    ...decididos.map(i => this.texto(i)),
                ].join('\n\n')
                try {
                    await navigator.clipboard.writeText(corpo)
                    b.textContent = 'copiado ✓'
                } catch {
                    b.textContent = 'não deu — selecione o texto abaixo'
                    raiz.getElementById('saida').value = corpo
                    raiz.getElementById('saida').hidden = false
                }
                setTimeout(() => { b.textContent = rotulo }, 2500)
            })
            return b
        }

        caixa.appendChild(fazer('Copiar tudo', this.itens))
        for (const a of agentes) {
            caixa.appendChild(fazer(`Copiar o de ${a}`, this.itens.filter(i => i.para === a)))
        }

        const limpar = document.createElement('button')
        limpar.type = 'button'
        limpar.className = 'copiar apagar'
        limpar.textContent = 'Apagar esta revisão'
        limpar.addEventListener('click', () => {
            if (!confirm('Apagar as respostas guardadas neste navegador? Não afeta o repositório.')) return
            try { localStorage.removeItem(CHAVE) } catch { /* nothing to clear */ }
            this.estado = {}
            this.desenhar()
        })
        caixa.appendChild(limpar)
    }

    /** The count is derived from the answers, never held beside them — the same rule pt-queue
     *  follows, and the same failure this whole publication exists to report. */
    contar() {
        const n = this.itens.filter(i => (this.estado[i.id] || {}).veredicto).length
        const el = this.shadowRoot.getElementById('contagem')
        el.textContent = `${n} de ${this.itens.length} com veredicto`
        this.emit('pt-decisoes:contadas', { decididas: n, total: this.itens.length })
    }
}

customElements.define('pt-decisoes', PtDecisoes)

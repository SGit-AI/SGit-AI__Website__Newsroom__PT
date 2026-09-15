/**
 * pt-chat — "talk to this content", as a right-hand column.
 *
 * The interface only. The engine — the tools, the level-0 comparator, the OpenRouter call — is
 * `assets/conversa.js`, and this file reaches it through `window.ptConversa` and nowhere else.
 *
 * WHY A COLUMN AND NOT AN OVERLAY. An overlay covers the page you were reading, and on this site
 * the page you were reading is the thing you are asking about. "Which source does this stand on"
 * is not a question you can answer while the answer is hidden behind the question. So the panel
 * takes width from the document — `<html>` gets a padding-right equal to the panel — and the page
 * reflows beside it. The measure the design gates protect (29em) survives, because the column is
 * narrower, not because the text is squeezed.
 *
 * WHAT IS ON DISPLAY, AND WHY IT IS ON DISPLAY
 *
 *   · **what I send** — the materials that travel with the question, as checkboxes. A reader of
 *     this site should never have to guess what left their browser.
 *   · **what it can do** — every tool, with a badge. They are all READ, because the API is files;
 *     that is stated rather than implied, because a list where nothing is dangerous reads like a
 *     safety claim and here it is a consequence of the architecture.
 *   · **each tool call, inline, where it happened.** Not a spinner. Which file the model opened,
 *     with what argument, and how many bytes came back. On a publication whose whole argument is
 *     that a claim walks back to bytes, hiding which bytes were read would be the wrong thing to
 *     hide.
 *
 * WHAT IT NEVER DOES. It does not write. The tools are GET-only, the panel has no route to the
 * vault, and nothing here can publish. And the model's answer is inserted as TEXT, never as
 * markup: rendering it as HTML would hand a model the pen for this page.
 *
 * @module pt-chat
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

const LARGURA = 'pt-newsroom:conversa:largura'
const ABERTO = 'pt-newsroom:conversa:aberto'
const ENVIO = 'pt-newsroom:conversa:envio'
const LARGURA_OMISSAO = 420

/* Models the reader can pick. Kept short and named, rather than a free-text box: a typo in a model
   id fails at OpenRouter with a message nobody can act on. `MODELO_OMISSAO` from the engine is
   always included, so the default survives this list changing. */
const MODELOS = [
    ['anthropic/claude-sonnet-4.5', 'Claude Sonnet 4.5 — default'],
    ['anthropic/claude-haiku-4.5', 'Claude Haiku 4.5 — faster, cheaper'],
    ['openai/gpt-5', 'GPT-5'],
    ['google/gemini-3-flash', 'Gemini 3 Flash — cheapest'],
]

/* What may travel with a question. Each says what it is and why you might leave it off — a
   checkbox with no reason beside it is a setting nobody changes. */
const MATERIAIS = [
    { id: 'pagina', rotulo: 'a página onde estou', omissao: true,
      porque: 'o endereço e o título desta página, para a pergunta ter um assunto' },
    { id: 'indice', rotulo: 'o índice da API', omissao: true,
      porque: 'a lista de colecções, para o modelo saber o que pode abrir' },
]

const SUGESTOES = [
    'Em que fontes congeladas assenta esta página?',
    'Que artigos existem, e em que estado está cada um?',
    'O que é que a secção das políticas pode afirmar hoje, e o que não pode?',
    'Mostra-me o que mudou entre capturas.',
    'Que entregas de investigação estão por rever, e porquê?',
]

class PtChat extends SgComponent {

    static jsUrl = import.meta.url

    get resourceName() { return 'pt-chat' }

    onReady() {
        this._motor = window.ptConversa
        this._historico = []
        this._gasto = { chamadas: 0, custo: 0 }
        this._ocupado = false

        this._largura = Number(this._ler(LARGURA, LARGURA_OMISSAO)) || LARGURA_OMISSAO
        this._aplicarLargura(this._largura)

        this.$('#abrir').addEventListener('click', () => this.alternar(true))
        this.$('#fechar').addEventListener('click', () => this.alternar(false))
        this.$('#nova').addEventListener('click', () => this.nova())
        this.$('#forma').addEventListener('submit', ev => { ev.preventDefault(); this.enviar() })
        this.$('#pergunta').addEventListener('keydown', ev => {
            if (ev.key === 'Enter' && (ev.metaKey || ev.ctrlKey)) { ev.preventDefault(); this.enviar() }
        })
        this._arrastar()

        this._pintarMateriais()
        this._pintarFerramentas()
        this._pintarModelos()
        this._pintarChave()
        this._pintarSugestoes()
        this._vazio()

        if (this._ler(ABERTO, '') === 'sim') this.alternar(true)
        if (!this._motor) {
            this._linha('chamada falhou', 'the engine (assets/conversa.js) did not load')
        }
    }

    /* Storage always through the engine, which already wraps every access in try/catch — a private
       window throws on localStorage and the panel must still open. */
    _ler(k, omissao) { return this._motor ? this._motor.guardado(k, omissao) : omissao }
    _escrever(k, v) { if (this._motor) this._motor.guardar(k, v) }

    // ------------------------------------------------------------- the column ---

    _aplicarLargura(px) {
        const w = Math.max(300, Math.min(px, Math.round(window.innerWidth * 0.9)))
        this._largura = w
        document.documentElement.style.setProperty('--pt-chat-w', `${w}px`)
    }

    alternar(abrir) {
        this.$('#painel').hidden = !abrir
        this.toggleAttribute('aberto', abrir)
        this.$('#abrir').setAttribute('aria-expanded', String(abrir))
        /* The class goes on <html> and the padding with it. Putting it on <body> would fight the
           sticky masthead, which is positioned against the viewport and not against the body. */
        document.documentElement.classList.toggle('pt-chat-aberto', abrir)
        this._escrever(ABERTO, abrir ? 'sim' : 'nao')
        if (abrir) this.$('#pergunta').focus()
        this.emit('pt-chat:toggled', { aberto: abrir, largura: this._largura })
    }

    _arrastar() {
        const p = this.$('#puxador')
        let a_arrastar = false
        const mover = ev => {
            if (!a_arrastar) return
            this._aplicarLargura(window.innerWidth - ev.clientX)
        }
        const largar = () => {
            if (!a_arrastar) return
            a_arrastar = false
            document.body.style.userSelect = ''
            this._escrever(LARGURA, String(this._largura))
        }
        p.addEventListener('pointerdown', ev => {
            a_arrastar = true; ev.preventDefault()
            /* Without this the drag selects the article text it passes over, which looks broken. */
            document.body.style.userSelect = 'none'
        })
        window.addEventListener('pointermove', mover)
        window.addEventListener('pointerup', largar)
        /* Keyboard: a resize handle nobody can reach without a mouse is a handle half the readers
           do not have. */
        p.addEventListener('keydown', ev => {
            const passo = ev.shiftKey ? 60 : 20
            if (ev.key === 'ArrowLeft') { this._aplicarLargura(this._largura + passo) }
            else if (ev.key === 'ArrowRight') { this._aplicarLargura(this._largura - passo) }
            else return
            ev.preventDefault()
            this._escrever(LARGURA, String(this._largura))
        })
    }

    // ------------------------------------------------------------- the panels ---

    _pintarMateriais() {
        const alvo = this.$('#envio')
        alvo.textContent = ''
        const escolhido = new Set((this._ler(ENVIO, MATERIAIS.filter(m => m.omissao)
            .map(m => m.id).join(',')) || '').split(',').filter(Boolean))
        for (const m of MATERIAIS) {
            const linha = document.createElement('label')
            linha.className = 'envio-item'
            const cx = document.createElement('input')
            cx.type = 'checkbox'; cx.checked = escolhido.has(m.id); cx.dataset.id = m.id
            cx.addEventListener('change', () => this._guardarMateriais())
            const txt = document.createElement('span')
            txt.textContent = m.rotulo
            const porque = document.createElement('span')
            porque.className = 'porque'; porque.textContent = m.porque
            txt.appendChild(porque)
            linha.append(cx, txt)
            alvo.appendChild(linha)
        }
    }

    _guardarMateriais() {
        const ids = this.$$('#envio input:checked').map(x => x.dataset.id)
        this._escrever(ENVIO, ids.join(','))
    }

    _pintarFerramentas() {
        const alvo = this.$('#ferramentas')
        alvo.textContent = ''
        const ferr = (this._motor && this._motor.FERRAMENTAS) || []

        const nota = document.createElement('p')
        nota.className = 'ferr desc'
        nota.style.paddingBottom = '6px'
        nota.textContent = `${ferr.length} ferramentas, e todas são LER — cada uma é um GET a um ` +
            `ficheiro de /api/v1/. Não há escrita porque não há servidor: o pior que uma chamada ` +
            `faz é ler uma coisa que já é pública.`
        alvo.appendChild(nota)

        for (const f of ferr) {
            const li = document.createElement('div')
            li.className = 'ferr'
            const nome = document.createElement('code')
            nome.textContent = f.nome
            const selo = document.createElement('span')
            selo.className = 'selo ler'
            selo.textContent = 'LER'
            const d = document.createElement('span')
            d.className = 'desc'
            d.textContent = `${f.descricao}  ·  /api/v1/${f.caminho}`
            li.append(nome, selo, d)
            alvo.appendChild(li)
        }
    }

    _pintarModelos() {
        const sel = this.$('#modelo')
        sel.textContent = ''
        const actual = this._ler(this._motor?.MODELO, this._motor?.MODELO_OMISSAO || '')
        const vistos = new Set()
        for (const [id, rot] of MODELOS) {
            vistos.add(id)
            const o = document.createElement('option')
            o.value = id; o.textContent = rot; o.selected = id === actual
            sel.appendChild(o)
        }
        if (actual && !vistos.has(actual)) {
            const o = document.createElement('option')
            o.value = actual; o.textContent = `${actual} — guardado`; o.selected = true
            sel.appendChild(o)
        }
        sel.addEventListener('change', () => this._escrever(this._motor.MODELO, sel.value))
    }

    _pintarChave() {
        const alvo = this.$('#chave-linha')
        alvo.textContent = ''
        const tem = !!this._ler(this._motor?.CHAVE, '')

        const p = document.createElement('div')
        p.textContent = tem
            ? 'A usar a sua chave do OpenRouter, guardada neste navegador. '
            : 'Sem chave: responde o comparador, que corre aqui e diz porque escolheu. '
        const b = document.createElement('button')
        b.type = 'button'
        b.textContent = tem ? 'mudar ou esquecer' : 'usar a minha chave'
        b.addEventListener('click', () => this._caixaDaChave(!alvo.querySelector('.chave-caixa')))
        p.appendChild(b)
        alvo.appendChild(p)

        const aviso = document.createElement('div')
        aviso.style.paddingTop = '4px'
        aviso.textContent = 'Sem anfitrião não há chão de permissões: a chave vive na origem desta ' +
            'página e não passa por pt.newsroom.sgit.ai — não há por onde passar.'
        alvo.appendChild(aviso)
    }

    _caixaDaChave(abrir) {
        const alvo = this.$('#chave-linha')
        const existente = alvo.querySelector('.chave-caixa')
        if (existente) existente.remove()
        if (!abrir) return
        const caixa = document.createElement('div')
        caixa.className = 'chave-caixa'
        const i = document.createElement('input')
        i.type = 'password'; i.placeholder = 'sk-or-…'; i.autocomplete = 'off'
        const g = document.createElement('button')
        g.type = 'button'; g.textContent = 'guardar'
        g.addEventListener('click', () => {
            const v = i.value.trim()
            if (v) this._escrever(this._motor.CHAVE, v)
            i.value = ''
            this._pintarChave()
        })
        const e = document.createElement('button')
        e.type = 'button'; e.textContent = 'esquecer'
        e.addEventListener('click', () => {
            if (this._motor) this._motor.esquecer(this._motor.CHAVE)
            this._pintarChave()
        })
        caixa.append(i, g, e)
        alvo.appendChild(caixa)
        i.focus()
    }

    _pintarSugestoes() {
        const alvo = this.$('#sugestoes')
        alvo.textContent = ''
        for (const s of SUGESTOES) {
            const b = document.createElement('button')
            b.type = 'button'; b.className = 'sug'; b.textContent = s
            b.addEventListener('click', () => {
                this.$('#pergunta').value = s
                this.enviar()
            })
            alvo.appendChild(b)
        }
    }

    // ------------------------------------------------------------ the stream ---

    _bolha(classe, texto, rodape) {
        const d = document.createElement('div')
        d.className = `msg ${classe}`
        for (const par of String(texto).split(/\n\s*\n/)) {
            const p = document.createElement('p')
            /* textContent and not innerHTML. What a model returns is somebody else's text, and
               injecting it as markup would hand a model the pen for this page. */
            p.textContent = par
            d.appendChild(p)
        }
        if (rodape) {
            const r = document.createElement('div')
            r.className = 'rodape'; r.textContent = rodape
            d.appendChild(r)
        }
        this.$('#fluxo').appendChild(d)
        this._aoFundo()
        return d
    }

    _linha(classe, texto) {
        const d = document.createElement('div')
        d.className = `chamada ${classe.includes('falhou') ? 'falhou' : ''}`
        d.textContent = texto
        this.$('#fluxo').appendChild(d)
        this._aoFundo()
        return d
    }

    _aoFundo() {
        const f = this.$('#fluxo')
        f.scrollTop = f.scrollHeight
    }

    nova() {
        this._historico = []
        this._gasto = { chamadas: 0, custo: 0 }
        this.$('#fluxo').textContent = ''
        this._pintarGasto()
        this.$('#sugestoes').hidden = false
        this._vazio()
        this.emit('pt-chat:new')
    }

    /* The empty state. A blank column with a text box under it says nothing about what the box
       does, and the two things a reader most needs to know here — that there are two levels, and
       that neither of them can write — are exactly what an empty panel is silent about. */
    _vazio() {
        const d = document.createElement('div')
        d.className = 'vazio'
        const chave = !!this._ler(this._motor?.CHAVE, '')
        const n = ((this._motor && this._motor.FERRAMENTAS) || []).length
        for (const t of [
            'Isto fala com este site e com mais nada.',
            chave
                ? `Com a sua chave, um modelo responde e abre o que precisar de ${n} ferramentas ` +
                  'de leitura — e cada abertura aparece aqui, com o caminho e os bytes.'
                : 'Sem chave, responde um comparador que corre neste navegador e diz, ao lado de ' +
                  'cada resultado, que palavras bateram. Com a sua chave do OpenRouter, um modelo ' +
                  `responde e abre o que precisar de ${n} ferramentas de leitura.`,
            'Nenhum dos dois escreve: a API deste site são ficheiros, e um GET não publica nada.',
        ]) {
            const p = document.createElement('p')
            p.textContent = t
            d.appendChild(p)
        }
        this.$('#fluxo').appendChild(d)
    }

    _pintarGasto() {
        const g = this._gasto
        this.$('#gasto').textContent = g.chamadas
            ? `${g.chamadas} leitura(s)${g.custo ? ` · $${g.custo.toFixed(4)} nesta conversa` : ''}`
            : 'nada gasto ainda'
    }

    _contexto() {
        const ids = new Set(this.$$('#envio input:checked').map(x => x.dataset.id))
        const partes = []
        if (ids.has('pagina')) {
            partes.push(`A pergunta vem desta página: ${document.title} — ${location.pathname}`)
        }
        if (ids.has('indice')) {
            partes.push('O índice das colecções está em /api/v1/index.json; use as ferramentas ' +
                        'para abrir o que precisar.')
        }
        return partes.join('\n')
    }

    // -------------------------------------------------------------- the round ---

    async enviar() {
        if (this._ocupado) return
        const campo = this.$('#pergunta')
        const pergunta = campo.value.trim()
        if (!pergunta) return
        campo.value = ''
        this.$('#sugestoes').hidden = true
        const vazio = this.$('.vazio')
        if (vazio) vazio.remove()
        this._bolha('eu', pergunta)
        this._ocupado = true
        this.$('#enviar').disabled = true

        const chave = this._ler(this._motor?.CHAVE, '')
        try {
            if (!chave) await this._nivelZero(pergunta)
            else await this._nivelUm(pergunta)
        } catch (err) {
            this._linha('falhou', `falhou: ${err.message}`)
        } finally {
            this._ocupado = false
            this.$('#enviar').disabled = false
            this._aoFundo()
        }
    }

    async _nivelZero(pergunta) {
        const aviso = this._linha('', 'o comparador está a correr neste navegador…')
        const cat = await this._motor.catalogo()
        const r = this._motor.comparar(pergunta, cat)
        aviso.remove()
        if (!r.length) {
            this._bolha('ele', 'Nada no índice deste site bate com essas palavras. O índice ' +
                'inteiro está em /api/v1/index.json e em llms.txt.')
            return
        }
        this._bolha('ele', `O comparador correu aqui, sem rede e sem chave. ${r.length} ` +
            `resultado(s), e ao lado de cada um está porque foi escolhido.`)
        const raiz = this._motor.raiz()
        for (const x of r) {
            const d = document.createElement('div')
            d.className = 'encaminhado'
            const t = document.createElement('div')
            const a = document.createElement('a')
            a.href = raiz + String(x.item.caminho).replace(/^\//, '')
            a.textContent = x.item.nome
            t.append(a, document.createTextNode(` — ${x.item.tipo}`))
            const pts = document.createElement('span')
            pts.className = 'pontos'; pts.textContent = ` ${x.pontos} pontos`
            t.appendChild(pts)
            const resumo = document.createElement('div')
            resumo.textContent = String(x.item.resumo || '').slice(0, 220)
            const bateu = document.createElement('span')
            bateu.className = 'bateu'; bateu.textContent = `bateu: ${x.bateram.join(', ')}`
            d.append(t, resumo, bateu)
            this.$('#fluxo').appendChild(d)
        }
        this._aoFundo()
    }

    async _nivelUm(pergunta) {
        const modelo = this.$('#modelo').value
        const ctx = this._contexto()
        this._historico.push({ role: 'user', content: ctx ? `${ctx}\n\n${pergunta}` : pergunta })

        const pendentes = new Map()
        const aoVivo = ev => {
            if (ev.tipo === 'chamada') {
                const arg = ev.args && ev.args.id ? `(${ev.args.id})` : ''
                pendentes.set(ev.nome, this._linha('', `a ler ${ev.nome}${arg}…`))
            } else if (ev.tipo === 'resultado') {
                const l = pendentes.get(ev.nome)
                const txt = ev.erro
                    ? `${ev.nome} falhou: ${ev.erro}`
                    : `leu ${ev.nome} — ${ev.bytes.toLocaleString('pt-PT')} bytes`
                if (l) { l.textContent = txt; if (ev.erro) l.classList.add('falhou') }
                else this._linha(ev.erro ? 'falhou' : '', txt)
                pendentes.delete(ev.nome)
            } else if (ev.tipo === 'custo') {
                this._gasto = { chamadas: ev.chamadas, custo: ev.custo }
                this._pintarGasto()
            }
        }

        try {
            const r = await this._motor.perguntar(
                this._ler(this._motor.CHAVE, ''), modelo, this._historico, aoVivo)
            this._historico.push({ role: 'assistant', content: r.texto })
            this._gasto = { chamadas: r.chamadas, custo: r.custo }
            this._pintarGasto()
            this._bolha('ele', r.texto,
                `${modelo} · ${r.chamadas} leitura(s)` +
                (r.custo ? ` · $${r.custo.toFixed(4)}` : '') +
                ' — confira o que ele diz contra o caminho que ele nomeia.')
        } catch (err) {
            /* Falls back to level 0 rather than stopping answering — the engine's rule, kept. */
            this._linha('falhou', `o nível 1 falhou (${err.message}); corri o comparador:`)
            await this._nivelZero(pergunta)
        }
    }
}

customElements.define('pt-chat', PtChat)

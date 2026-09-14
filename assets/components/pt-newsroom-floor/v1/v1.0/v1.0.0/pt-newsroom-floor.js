/**
 * pt-newsroom-floor — a mesa como uma sala: quem tem o quê, e o que está parado à espera de quem.
 *
 * Quatro bancadas em cima, o quadro em baixo. Clica-se numa bancada e a sala responde: o que
 * aquela bancada faz, o que RECUSA fazer, em que pastas pode escrever, e quais os cartões que
 * estão à espera dela. Clicar outra vez larga o filtro.
 *
 * A diferença entre isto e a tabela que estava aqui antes não é decoração. Uma tabela mostra
 * linhas; uma sala mostra CARGA — quem tem trabalho em cima da mesa agora, e onde está o próximo
 * gesto. São perguntas diferentes, e a segunda é a que se faz a uma redação às cinco da tarde.
 *
 * NADA AQUI MOVE NADA. Não há botão que empurre um cartão de coluna, e a ausência é deliberada:
 * o estado de uma história vive nos ficheiros da pasta dela, e quem o muda é quem tem direito de
 * escrita naquela pasta. Uma sala que deixasse arrastar um cartão para «publicado» estaria a
 * oferecer, num clique, exatamente o gesto que esta publicação reserva a um humano nomeado.
 *
 * @module pt-newsroom-floor
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

class PtNewsroomFloor extends SgComponent {

    static jsUrl = import.meta.url

    get resourceName() { return 'pt-newsroom-floor' }

    async onReady() {
        this._raiz = this.getAttribute('raiz') || ''
        this._banc = null
        try {
            this._d = await fetch(`${this._raiz}dados/redacao.json`).then(r => {
                if (!r.ok) throw new Error(`${r.status} ao pedir dados/redacao.json`)
                return r.json()
            })
            this._render()
        } catch (err) {
            this.falhou(err.message)
            this.$('#nota').className = 'nota erro'
            this.$('#nota').textContent = `a mesa não carregou: ${err.message}`
        }
    }

    _bancadas() {
        const alvo = this.$('#bancadas')
        alvo.textContent = ''
        for (const b of this._d.bancadas || []) {
            const el = document.createElement('button')
            el.type = 'button'
            el.className = 'banc'
            el.setAttribute('aria-pressed', String(this._banc === b.id))

            const nome = document.createElement('div')
            nome.className = 'nome'
            nome.textContent = b.nome
            const esp = document.createElement('div')
            esp.className = 'esp'
            esp.textContent = b.especie

            const num = document.createElement('div')
            num.className = 'num'
            const pares = [
                ['à espera', b.carga.cartoes_a_espera, b.carga.cartoes_a_espera > 0],
                ['por fechar', b.carga.abertas, b.carga.abertas > 0],
                ['entradas', b.carga.entradas, false],
            ]
            if (b.carga.entregas_por_rever) {
                pares.push(['entregas por rever', b.carga.entregas_por_rever, true])
            }
            for (const [rot, v, alerta] of pares) {
                const s = document.createElement('span')
                if (alerta) s.className = 'alerta'
                const strong = document.createElement('b')
                strong.textContent = String(v)
                s.append(strong, document.createTextNode(' ' + rot))
                num.appendChild(s)
            }

            /* A razão entre o que está por fechar e o total. Uma barra que medisse o total seria
               um gráfico de quem trabalhou mais, que não é a pergunta. */
            const barra = document.createElement('div')
            barra.className = 'barra'
            const i = document.createElement('i')
            const pct = b.carga.entradas ? (b.carga.abertas / b.carga.entradas) * 100 : 0
            i.style.width = `${Math.round(pct)}%`
            barra.appendChild(i)

            el.append(nome, esp, num, barra)
            el.addEventListener('click', () => {
                this._banc = this._banc === b.id ? null : b.id
                this._render()
                this.emit('pt-newsroom-floor:desk', { bancada: this._banc })
            })
            alvo.appendChild(el)
        }
    }

    _detalhe() {
        const box = this.$('#detalhe')
        box.textContent = ''
        const b = (this._d.bancadas || []).find(x => x.id === this._banc)
        if (!b) { box.hidden = true; return }
        box.hidden = false

        const h = document.createElement('h3')
        h.textContent = b.nome
        box.appendChild(h)
        for (const [rot, txt, forte] of [
            [null, b.gravidade, true], ['Faz', b.faz, false], ['Recusa', b.recusa, false],
        ]) {
            if (!txt) continue
            const p = document.createElement('p')
            if (forte) p.className = 'grav'
            p.textContent = rot ? `${rot}: ${txt}` : txt
            box.appendChild(p)
        }
        if ((b.escreve_em || []).length) {
            const p = document.createElement('p')
            p.textContent = b.id === 'editor' ? 'Só ele pode:' : 'Escreve em:'
            const ul = document.createElement('ul')
            for (const x of b.escreve_em) {
                const li = document.createElement('li')
                li.textContent = x
                ul.appendChild(li)
            }
            box.append(p, ul)
        }
    }

    _quadro() {
        const alvo = this.$('#quadro')
        alvo.textContent = ''
        const b = (this._d.bancadas || []).find(x => x.id === this._banc)

        for (const col of this._d.colunas || []) {
            const cartoes = (this._d.quadro || {})[col.id] || []
            const meus = b ? cartoes.filter(c => b.cartoes.includes(c.id)) : cartoes
            const el = document.createElement('div')
            /* Com uma bancada escolhida, as colunas que não são dela esbatem-se em vez de
               desaparecerem: o quadro tem de continuar a ser o mesmo quadro. */
            el.className = (b && col.quem_move !== b.id) ? 'col esbatida' : 'col'

            const cab = document.createElement('div')
            cab.className = 'cab'
            const rot = document.createElement('span')
            rot.textContent = col.rotulo
            const n = document.createElement('span')
            n.textContent = String(meus.length)
            cab.append(rot, n)

            const quem = document.createElement('div')
            quem.className = 'quem'
            quem.textContent = `move: ${col.quem_move}`

            const sig = document.createElement('div')
            sig.className = 'sig'
            sig.textContent = col.o_que_significa

            el.append(cab, quem, sig)

            for (const c of meus) {
                const cart = document.createElement('div')
                cart.className = 'cartao'
                const t = document.createElement('div')
                if (c.url) {
                    const a = document.createElement('a')
                    a.setAttribute('href', this._raiz + c.url)
                    a.textContent = c.titulo
                    t.appendChild(a)
                } else {
                    t.textContent = c.titulo
                }
                const pe = document.createElement('div')
                pe.className = 'pe'
                for (const x of [c.seccao, c.especie, c.issue ? `issue ${c.issue}` : null,
                                 c.irmaos ? `+${c.irmaos} da mesma encomenda` : null,
                                 c.ultimo_toque && c.ultimo_toque.quem
                                     ? `último toque: ${c.ultimo_toque.quem}` : null]) {
                    if (!x) continue
                    const s = document.createElement('span')
                    s.textContent = x
                    pe.appendChild(s)
                }
                cart.append(t, pe)
                el.appendChild(cart)
            }
            if (!meus.length) {
                const v = document.createElement('div')
                v.className = 'vazia'
                v.textContent = b ? 'nada desta bancada' : 'vazia'
                el.appendChild(v)
            }
            alvo.appendChild(el)
        }
    }

    _render() {
        this._bancadas()
        this._detalhe()
        this._quadro()
        const c = this._d.contagens || {}
        this.$('#nota').className = 'nota'
        this.$('#nota').textContent =
            `${c.cartoes} cartões · ${c.publicados} publicados · ${c.a_espera_do_editor} à espera ` +
            `do editor · ${c.execucoes} execuções · atualizado ${this._d.atualizado}. ` +
            `Nada nesta sala move nada: o estado de uma história vive nos ficheiros da pasta dela, ` +
            `e quem o muda é quem tem direito de escrita nessa pasta.`
    }
}

customElements.define('pt-newsroom-floor', PtNewsroomFloor)

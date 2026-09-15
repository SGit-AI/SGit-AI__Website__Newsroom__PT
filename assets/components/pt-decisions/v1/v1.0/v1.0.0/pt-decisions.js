/**
 * pt-decisions — the editor's answers, captured in the browser and carried out by hand.
 *
 * WHY THIS EXISTS AND WHY IT WRITES NOTHING. Every decision that changes what this site says is a
 * file in the repository, written by a person: `redacao/revisoes/<delivery>.json` for a research
 * item, `estado: publicado` in an `artigo.json` for a story. This site is static and cannot write
 * to git, and it must not pretend otherwise — a console that looked like it recorded a decision
 * while recording nothing would be the one dishonest page on a publication whose whole argument is
 * that nothing is asserted without bytes behind it.
 *
 * So the division is explicit: the browser holds the editor's WORDS, and an agent turns them into
 * FILES. This component captures a verdict, a comment and reactions per open question, keeps them
 * in localStorage so a review can be interrupted and resumed, and hands back a block of text
 * addressed to the agent that will do the work. Nothing here is a decision until the file exists.
 *
 * WHY localStorage AND NOT A FORM POST. There is nowhere to post to. The same constraint that makes
 * this publication auditable — static, built from files, no server holding state — means the only
 * place a half-finished review can live is the editor's own browser. Per-device and per-browser on
 * purpose: this is a scratchpad, not a record. The record is git.
 *
 * @module pt-decisions
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

const STORE = 'pt-review/v1'

/* `defer` is the safe default and needs no justification: an item with no decision stays out of
 * everything, which is what the quarantine gate enforces anyway. */
const VERDICTS = [
    { id: 'approve', label: 'Approve',   cssClass: 'ok' },
    { id: 'reject',  label: 'Reject',    cssClass: 'miss' },
    { id: 'defer',   label: 'Leave open', cssClass: '' },
]

/* Reactions are not verdicts. They are how the editor says what KIND of attention a thing needs,
 * which is often the more useful signal and is lost entirely in a yes/no. */
const REACTIONS = [
    { id: 'agree',       label: 'Agree' },
    { id: 'doubts',      label: 'Have doubts' },
    { id: 'investigate', label: 'Dig further' },
    { id: 'urgent',      label: 'Urgent' },
    { id: 'disagree',    label: 'Disagree' },
]

export class PtDecisions extends SgComponent {

    static jsUrl = import.meta.url

    get resourceName() { return 'pt-decisions' }

    /** A browser with site data blocked throws here, and a scratchpad that cannot save is still a
     *  usable scratchpad — so it degrades rather than failing. */
    read() {
        try { return JSON.parse(localStorage.getItem(STORE) || '{}') } catch { return {} }
    }

    save(state) {
        try { localStorage.setItem(STORE, JSON.stringify(state)) } catch { /* private window */ }
    }

    onReady() {
        // THE DATA COMES IN A CHILD <script type="application/json">, NOT IN AN ATTRIBUTE. An
        // attribute's value is entity-decoded by the HTML parser before any script sees it, so a
        // `&quot;` inside server-escaped markup becomes a bare quote AFTER JSON.stringify has
        // already escaped the real ones — valid HTML, corrupt JSON. A script block is raw text.
        let items
        try {
            const block = this.querySelector('script[type="application/json"]')
            items = JSON.parse(block ? block.textContent : (this.getAttribute('items') || '[]'))
        } catch (err) {
            this.failed(`items are not valid JSON: ${err.message}`)
            this.shadowRoot.getElementById('list').textContent =
                'This page could not read its list of questions.'
            return
        }
        this.items = items
        this.state = this.read()
        this.draw()
    }

    draw() {
        const root = this.shadowRoot
        const list = root.getElementById('list')
        list.textContent = ''

        for (const it of this.items) {
            const saved = this.state[it.id] || {}
            const block = document.createElement('div')
            block.className = 'd'
            block.innerHTML = `
              <div class="d__top">
                <span class="to">for ${it.para}</span>
                <span class="id">${it.id}</span>
              </div>
              <h3 class="d__t">${it.pergunta}</h3>
              <div class="d__ctx">${it.contexto || ''}</div>
              <div class="v" role="group" aria-label="Verdict"></div>
              <div class="r" role="group" aria-label="Reaction"></div>
              <label class="lbl" for="c-${it.id}">Your comment, in your own words</label>
              <textarea id="c-${it.id}" rows="3"
                        placeholder="Goes into the review file exactly as you write it."></textarea>`

            const verdictBox = block.querySelector('.v')
            for (const v of VERDICTS) {
                const b = document.createElement('button')
                b.type = 'button'
                b.className = `chip ${v.cssClass}`
                b.textContent = v.label
                b.setAttribute('aria-pressed', String(saved.verdict === v.id))
                b.addEventListener('click', () => {
                    const s = this.read()
                    s[it.id] = { ...(s[it.id] || {}), verdict: v.id, when: new Date().toISOString() }
                    this.state = s
                    this.save(s)
                    this.draw()
                })
                verdictBox.appendChild(b)
            }

            const reactionBox = block.querySelector('.r')
            const chosen = saved.reactions || []
            for (const r of REACTIONS) {
                const b = document.createElement('button')
                b.type = 'button'
                b.className = 'chip thin'
                b.textContent = r.label
                b.setAttribute('aria-pressed', String(chosen.includes(r.id)))
                b.addEventListener('click', () => {
                    const s = this.read()
                    const current = new Set((s[it.id] || {}).reactions || [])
                    current.has(r.id) ? current.delete(r.id) : current.add(r.id)
                    s[it.id] = { ...(s[it.id] || {}), reactions: [...current] }
                    this.state = s
                    this.save(s)
                    this.draw()
                })
                reactionBox.appendChild(b)
            }

            const ta = block.querySelector('textarea')
            ta.value = saved.comment || ''
            ta.addEventListener('input', () => {
                const s = this.read()
                s[it.id] = { ...(s[it.id] || {}), comment: ta.value }
                this.state = s
                this.save(s)
                this.count()
            })
            list.appendChild(block)
        }
        this.buildCopyButtons()
        this.count()
    }

    /** One answer as the text an agent reads. Identifiers first, because they are what the agent
     *  needs to find the file; the editor's words last, because they are what it must not
     *  paraphrase. */
    asText(it) {
        const g = this.state[it.id] || {}
        const v = VERDICTS.find(x => x.id === g.verdict)
        const r = (g.reactions || []).map(id => (REACTIONS.find(x => x.id === id) || {}).label)
        const lines = [
            `## ${it.id}`,
            `file: ${it.ficheiro}`,
            `question: ${it.pergunta}`,
            `verdict: ${v ? v.label : '— (no decision)'}`,
        ]
        if (r.length) lines.push(`reactions: ${r.join(', ')}`)
        lines.push(`editor's comment: ${g.comment ? g.comment.trim() : '—'}`)
        return lines.join('\n')
    }

    buildCopyButtons() {
        const root = this.shadowRoot
        const box = root.getElementById('copies')
        box.textContent = ''
        const agents = [...new Set(this.items.map(i => i.para))]

        const makeButton = (label, items) => {
            const b = document.createElement('button')
            b.type = 'button'
            b.className = 'copy'
            b.textContent = label
            b.addEventListener('click', async () => {
                const answered = items.filter(i => (this.state[i.id] || {}).verdict
                                                || (this.state[i.id] || {}).comment)
                const body = [
                    `# Editor of record's decisions — ${new Date().toISOString().slice(0, 10)}`,
                    `editor: Dinis Cruz`,
                    `answers in this message: ${answered.length} of ${items.length}`,
                    '',
                    "These are the editor's own words, to be copied as they stand into the file each",
                    'answer names. An answer with no verdict stays open, which is the safe state, and',
                    'must not be invented.',
                    '',
                    ...answered.map(i => this.asText(i)),
                ].join('\n\n')
                try {
                    await navigator.clipboard.writeText(body)
                    b.textContent = 'copied ✓'
                } catch {
                    b.textContent = 'no clipboard — select the text below'
                    root.getElementById('out').value = body
                    root.getElementById('out').hidden = false
                }
                setTimeout(() => { b.textContent = label }, 2500)
            })
            return b
        }

        box.appendChild(makeButton('Copy all', this.items))
        for (const a of agents) {
            box.appendChild(makeButton(`Copy the ${a} set`, this.items.filter(i => i.para === a)))
        }

        const clearBtn = document.createElement('button')
        clearBtn.type = 'button'
        clearBtn.className = 'copy clear'
        clearBtn.textContent = 'Clear this review'
        clearBtn.addEventListener('click', () => {
            if (!confirm('Clear the answers saved in this browser? The repository is untouched.')) return
            try { localStorage.removeItem(STORE) } catch { /* nothing to clear */ }
            this.state = {}
            this.draw()
        })
        box.appendChild(clearBtn)
    }

    /** Derived from the answers, never held beside them — the rule pt-queue follows, and the
     *  failure this whole publication exists to report. */
    count() {
        const n = this.items.filter(i => (this.state[i.id] || {}).verdict).length
        this.shadowRoot.getElementById('count').textContent =
            `${n} of ${this.items.length} answered`
        this.emit('pt-decisions:counted', { answered: n, total: this.items.length })
    }
}

customElements.define('pt-decisions', PtDecisions)

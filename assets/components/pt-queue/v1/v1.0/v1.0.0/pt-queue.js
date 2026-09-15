/**
 * pt-queue — what is waiting on the editor of record, and nothing else.
 *
 * THE QUESTION THE CONSOLE EXISTS TO ANSWER. When Dinis opens the back office he is asking one
 * thing: what is blocked on me? Today the answer is a single cell in row 6 of the first table —
 * `waiting on a human` — rendered in the BASE chip style, so it looks exactly like the five
 * `running` chips above it. Meanwhile mail.html knows he has an unread message and board.html
 * knows an issue is chipped `waiting on dinis.humano`. Three pages each hold a piece of the
 * answer and the console index shows none of it.
 *
 * So this component is the first thing on the page and the only filled element on it.
 *
 * IT COUNTS, IT DOES NOT ACCEPT A COUNT. The headline number is derived from the items. There is
 * no `count` attribute, because a number typed beside a list it claims to describe is a number
 * that will eventually disagree with the list — which is the failure this whole publication
 * exists to report. The same rule pt-provenance follows.
 *
 * IT ALSO TELLS THE RAIL. Having computed the number it emits `pt-queue:counted`, which is how
 * the navigation badge gets its value. The badge cannot drift from the queue because it never
 * held its own number.
 *
 * EMPTY IS A REAL STATE AND IT IS GOOD NEWS. A console that renders nothing when there is
 * nothing to do leaves the operator wondering whether it failed to load. "Nothing is waiting on
 * you" is an answer, and it is the answer we want most of the time.
 *
 * @module pt-queue
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

/* The four ranks of the console's status scale. Only rank 1 is filled — see console.css. */
const RANK = {
    'needs-you':     { rank: 1, label: 'needs you' },
    'agent-blocked': { rank: 2, label: 'agent blocked' },
    'running':       { rank: 3, label: 'running' },
    'done':          { rank: 4, label: 'done' },
}

const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`

class PtQueue extends SgComponent {

    static jsUrl = import.meta.url

    get resourceName() { return 'pt-queue' }

    onReady() {
        let items
        try {
            items = JSON.parse(this.getAttribute('items') || '[]')
            if (!Array.isArray(items)) throw new Error('items is not a list')
        } catch (err) {
            /* The component's own stylesheet hides the slotted fallback, so telling the operator
               to read "the list below" while hiding it would leave them with nothing at all.
               A read failure un-hides it explicitly. */
            this.falhou(`items: ${err.message}`)
            this.setAttribute('fallback', '')
            this.$('#n').textContent = '?'
            this.$('#title').textContent = 'The queue could not be read'
            this.$('#sub').textContent = 'The list below is whatever the page shipped as a fallback.'
            return
        }

        /* Only rank 1 belongs in this queue. Anything an agent can still move is not waiting on
           a human, and putting it here would make the number stop meaning anything. */
        const mine = items.filter(i => (i.status || 'needs-you') === 'needs-you')
        this._render(mine)
    }

    _render(items) {
        const n = items.length
        this.$('#n').textContent = String(n)

        if (!n) {
            this.setAttribute('empty', '')
            this.$('#title').textContent = 'Nothing is waiting on you'
            this.$('#sub').textContent = 'Every stage is with an agent. The console will say so here when that changes.'
            this.$('#list').hidden = true
        } else {
            this.$('#title').textContent = `${plural(n, 'thing needs', 'things need')} you`
            this.$('#sub').textContent = 'Nothing else on this page is blocked on a human.'
            items.forEach(i => this.$('#list').appendChild(this._item(i)))
        }

        /* The rail badge takes its number from here rather than holding one of its own. */
        this.emit('pt-queue:counted', { count: n })
    }

    _item(item) {
        const row = document.createElement('div')
        row.className = 'queue__item'

        const left = document.createElement('div')

        const h = document.createElement('h3')
        if (item.href) {
            const a = document.createElement('a')
            a.href = item.href
            a.textContent = item.title || '(untitled)'
            h.appendChild(a)
        } else {
            h.textContent = item.title || '(untitled)'
        }
        left.appendChild(h)

        const meta = document.createElement('div')
        meta.className = 'queue__meta'

        const st = document.createElement('span')
        st.className = 'st st--1'
        const rank = RANK[item.status || 'needs-you'] || RANK['needs-you']
        st.append(rank.label)
        if (item.since) {
            const who = document.createElement('span')
            who.className = 'who'
            who.textContent = `· ${item.since}`
            st.appendChild(who)
        }
        meta.appendChild(st)

        if (item.where) {
            const w = document.createElement('span')
            w.className = 'path'
            w.textContent = item.where
            meta.appendChild(w)
        }
        left.appendChild(meta)

        if (item.why) {
            const p = document.createElement('p')
            p.className = 'queue__why'
            p.textContent = item.why
            left.appendChild(p)
        }

        /* Quoted publication copy is shown in the publication's own face, tagged with its
           language, so the operator can see at a glance that it is not console text. */
        if (item.quote) {
            const q = document.createElement('p')
            q.className = 'quote quote--sm'
            q.style.marginTop = '10px'
            q.textContent = `«${item.quote}»`
            const tag = document.createElement('span')
            tag.className = 'lang'
            tag.textContent = item.quoteLang || 'PT'
            q.append(' ', tag)
            left.appendChild(q)
        }

        row.appendChild(left)

        /* Every action names the file it would write. An operator who does not trust a button
           can always do the same thing by hand, and knowing which file is what makes that true. */
        const actions = document.createElement('div')
        actions.className = 'queue__do';
        (item.actions || []).forEach((a, i) => {
            const b = document.createElement('button')
            b.type = 'button'
            b.className = 'btn' + (i === 0 ? ' btn--primary' : '')
            b.textContent = a.label
            if (a.writes) b.title = `writes ${a.writes}`
            b.addEventListener('click', () => this.emit('pt-queue:action', { id: item.id, action: a.id, writes: a.writes }))
            actions.appendChild(b)
        })
        row.appendChild(actions)
        return row
    }
}

customElements.define('pt-queue', PtQueue)

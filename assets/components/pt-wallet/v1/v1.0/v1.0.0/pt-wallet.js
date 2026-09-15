/**
 * pt-wallet — one cent a page, five euros in the wallet, and a ledger you can read.
 *
 * The parent site argues for paying the fact creator across several essays. This is that argument
 * made concrete on a publication that actually exists: every page has a price, opening it debits
 * the wallet, the wallet tops back up when it empties, and the ledger is visible.
 *
 * WHAT IT IS NOT, and the panel says this in its first sentence. It charges nothing. There is no
 * account, no payment, and nothing leaves the browser — the balance is `localStorage` on the
 * reader's own machine and it disappears when they clear site data. A paywall that did not admit
 * to being a demonstration would be the single dishonest thing on a site whose entire argument is
 * provenance, so it admits it before it says anything else.
 *
 * It also never blocks. The debit is recorded and the page is read either way: a hard paywall on
 * a demonstration would be theatre about an unbuilt payment rail, and the interesting part is the
 * ledger, not the gate.
 *
 * Storage is wrapped in try/catch throughout. A private window, cleared site data or a browser
 * that refuses storage must leave the page working — the wallet is the least important thing on
 * any page it appears on.
 *
 * @module pt-wallet
 * @version 1.0.0
 */
import { SgComponent } from '../../../../base/v1/v1.0/v1.0.0/sg-component.js'

const KEY = 'pt.newsroom.wallet.v1'
const TOPUP = 500          // cents — €5.00
const PRICE = 1            // cents per page
const LOG_MAX = 40

const euros = c => `€${(c / 100).toFixed(2).replace('.', ',')}`
const cents = c => (c === 1 ? '1 cêntimo' : `${c} cêntimos`)

class PtWallet extends SgComponent {

    static jsUrl = import.meta.url

    get resourceName() { return 'pt-wallet' }

    /**
     * TWO MODES, AND NO POPUP IN EITHER.
     *
     * Until v0.11.0 the badge in the page chrome opened a panel over the page. The editor asked for
     * the spend on a page of its own instead, and that is the better shape for what this is: the
     * ledger is the interesting part of the demonstration, and a ledger worth reading is worth a
     * URL. A panel that covers the masthead cannot be linked to, cannot be read on a phone without
     * covering what you were reading, and closes itself when you click anything.
     *
     *   modo="ficha"  (the default, and what the chrome uses) — the badge alone, as a LINK to the
     *                 wallet page. It still charges the page: the debit is the whole point, and it
     *                 has to happen wherever the reader is, not only on the wallet page.
     *   modo="pagina" — the ledger itself, laid out in the page. No badge, no toggle, no
     *                 document-level click handler.
     *
     * The charge runs in both — and the two DO share one page, the wallet page itself, which
     * carries the chrome badge as well as the ledger. That is not a double debit: `_charge()`
     * records the page in `sessionStorage` before returning, so the second instance to run finds
     * it already seen and does nothing. The guard was written for the back button and happens to
     * cover this too, which is worth saying out loud rather than relying on by accident.
     */
    onReady() {
        this._price = Number(this.getAttribute('price') || PRICE)
        this._modo = this.getAttribute('modo') === 'pagina' ? 'pagina' : 'ficha'
        this._state = this._read()
        this._charge()

        const badge = this.$('#open')
        const panel = this.$('#panel')
        if (this._modo === 'pagina') {
            badge.remove()
            panel.hidden = false
            panel.classList.add('pagina')
            this.$('#topup').addEventListener('click', () => this._topup())
            this.$('#reset').addEventListener('click', () => this._reset())
        } else {
            /* A link and not a button, so it behaves like every other link in the chrome: it can
               be middle-clicked, copied, and read by a screen reader as somewhere to go. */
            badge.setAttribute('href', (this.getAttribute('site-root') || '') + 'carteira/')
            badge.setAttribute('title', 'A carteira e o registo de gasto, numa página')
            panel.remove()
        }
        this._paint()
    }

    /* --- storage, which is allowed to fail ------------------------------- */
    _read() {
        const fresh = { balance: TOPUP, reads: 0, spent: 0, log: [], topups: 0 }
        try {
            const raw = localStorage.getItem(KEY)
            if (!raw) return fresh
            const s = JSON.parse(raw)
            return { ...fresh, ...s, log: Array.isArray(s.log) ? s.log : [] }
        } catch {
            this._noStorage = true
            return fresh
        }
    }

    _write() {
        try { localStorage.setItem(KEY, JSON.stringify(this._state)) }
        catch { this._noStorage = true }
    }

    /* --- the charge ------------------------------------------------------- */
    _charge() {
        const page = location.pathname.replace(/index\.html$/, '') || '/'
        /* One debit per page per session. Re-reading a page you already paid for in the same
           visit is not a second purchase — charging for a back button would be a worse model
           than the one being demonstrated. */
        let seen = []
        try { seen = JSON.parse(sessionStorage.getItem(`${KEY}.seen`) || '[]') } catch { /* ok */ }
        if (seen.includes(page)) return
        if (this._state.balance < this._price) this._topup(true)
        this._state.balance -= this._price
        this._state.reads += 1
        this._state.spent += this._price
        this._state.log.unshift({ page, cost: this._price, at: new Date().toISOString() })
        this._state.log = this._state.log.slice(0, LOG_MAX)
        this._write()
        try { sessionStorage.setItem(`${KEY}.seen`, JSON.stringify([...seen, page].slice(-200))) }
        catch { /* ok */ }
        this.emit('pt:wallet.charged', { page, cost: this._price, balance: this._state.balance })
    }

    _topup(auto = false) {
        this._state.balance = TOPUP
        this._state.topups += 1
        if (!auto) this._write()
        this.emit('pt:wallet.toppedup', { balance: TOPUP, auto })
        this._paint()
    }

    _reset() {
        this._state = { balance: TOPUP, reads: 0, spent: 0, log: [], topups: 0 }
        this._write()
        try { sessionStorage.removeItem(`${KEY}.seen`) } catch { /* ok */ }
        this._paint()
    }

    /* --- painting --------------------------------------------------------- */
    /** Set `textContent` on a node that may not be in this mode's markup. */
    _set(sel, valor) {
        const el = this.$(sel)
        if (el) el.textContent = valor
    }

    _paint() {
        const s = this._state
        this._set('#bal', euros(s.balance))
        this._set('#bal2', euros(s.balance))
        this._set('#price', cents(this._price))
        this._set('#price2', cents(this._price))
        this._set('#reads', String(s.reads))
        this._set('#spent', euros(s.spent))

        const badge = this.$('#open')
        if (badge) {
            badge.classList.toggle('low', s.balance <= TOPUP * 0.2 && s.balance > 0)
            badge.classList.toggle('empty', s.balance <= 0)
        }

        const log = this.$('#log')
        if (!log) return
        log.textContent = ''
        for (const e of s.log.slice(0, 12)) {
            const li = document.createElement('li')
            const a = document.createElement('span')
            a.textContent = e.page
            const b = document.createElement('span')
            b.className = 'c'
            b.textContent = cents(e.cost)
            li.append(a, b)
            log.appendChild(li)
        }
        if (!s.log.length) {
            const li = document.createElement('li')
            li.textContent = 'ainda nada'
            log.appendChild(li)
        }
        if (this._noStorage) {
            const li = document.createElement('li')
            li.textContent = 'este navegador não guarda o saldo — a carteira reinicia a cada página'
            log.appendChild(li)
        }
    }
}

customElements.define('pt-wallet', PtWallet)

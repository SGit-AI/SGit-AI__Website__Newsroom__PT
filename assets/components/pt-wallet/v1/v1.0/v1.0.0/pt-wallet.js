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
const TOPUP = 500          // cêntimos — €5,00
const PRICE = 1            // cêntimos por página
const LOG_MAX = 40

const euros = c => `€${(c / 100).toFixed(2).replace('.', ',')}`
const cents = c => (c === 1 ? '1 cêntimo' : `${c} cêntimos`)

class PtWallet extends SgComponent {

    static jsUrl = import.meta.url

    get resourceName() { return 'pt-wallet' }

    onReady() {
        this._price = Number(this.getAttribute('price') || PRICE)
        this._state = this._read()
        this._charge()
        this._paint()
        this.$('#open').addEventListener('click', () => this._toggle())
        this.$('#close').addEventListener('click', () => this._toggle(false))
        this.$('#topup').addEventListener('click', () => this._topup())
        this.$('#reset').addEventListener('click', () => this._reset())
        document.addEventListener('click', e => {
            if (!this.contains(e.target)) this._toggle(false)
        })
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

    _toggle(force) {
        const panel = this.$('#panel')
        const open = force === undefined ? panel.hidden : force
        panel.hidden = !open
        this.$('#open').setAttribute('aria-expanded', String(open))
    }

    /* --- painting --------------------------------------------------------- */
    _paint() {
        const s = this._state
        this.$('#bal').textContent = euros(s.balance)
        this.$('#bal2').textContent = euros(s.balance)
        this.$('#price').textContent = cents(this._price)
        this.$('#price2').textContent = cents(this._price)
        this.$('#reads').textContent = String(s.reads)
        this.$('#spent').textContent = euros(s.spent)

        const badge = this.$('#open')
        badge.classList.toggle('low', s.balance <= TOPUP * 0.2 && s.balance > 0)
        badge.classList.toggle('empty', s.balance <= 0)

        const log = this.$('#log')
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

/**
 * sg-component — the base class every component on this site extends.
 *
 * Vendored from the estate's contract, documented at
 * https://coding.sgit.ai/javascript/index.html and read on 14 September 2026. Native web
 * components, no framework, no build step: the browser is the runtime.
 *
 * THE CONTRACT. A component overrides exactly four things:
 *
 *     static jsUrl = import.meta.url   self-location. Required — without it the component
 *                                      cannot find its own markup.
 *     get resourceName()               the basename of the sibling markup and styles.
 *     get sharedCssPaths()             tokens and shared sheets to adopt.
 *     onReady()                        the lifecycle hook — never connectedCallback directly.
 *
 * `static jsUrl = import.meta.url` is the mechanism that removes the build step: the component
 * knows its own URL, so this base class resolves the sibling files against it without anything
 * being told where they live. And `onReady()` rather than `connectedCallback` is the tell — the
 * base class does the async fetch and calls onReady() once the shadow root is populated, so a
 * component never has to think about whether its markup has arrived. It removes a whole class of
 * race condition.
 *
 * TWO DEPARTURES FROM THE ESTATE, BOTH DELIBERATE AND BOTH FORCED BY THIS SITE'S OWN RULES.
 *
 * 1. The estate imports this class and its tokens from `dev.tools.sgraph.ai`. This site vendors
 *    everything and fetches nothing from a third party at runtime — the same reason Cytoscape,
 *    marked and the two typefaces are in this repository. A page that needs a third party to
 *    render is a page a third party can stop rendering, and this publication's whole argument is
 *    that what it shows you is in bytes it holds. The path scheme is kept exactly
 *    (`components/<name>/v1/v1.0/v1.0.0/`), so a consumer still pins at whatever depth it wants.
 *
 * 2. The estate's triplet is `<name>.js` / `<name>.html` / `<name>.css`. Here the markup file is
 *    `<name>.tpl`. On this site every `.html` file is a PAGE as far as `admin/build/validate.js`
 *    is concerned: it must carry a canonical link, an agent block, and a row in the sitemap. A
 *    component fragment is not a page and cannot honestly carry any of those. The alternative was
 *    to weaken the site gate, and the site gate is in the deny list of `.claude/settings.json` on
 *    purpose. So the fragment keeps its content and changes its extension: same triplet, same
 *    directory, same basename.
 */

const _cache = new Map()

async function _fetchText(url) {
    if (!_cache.has(url)) {
        _cache.set(url, fetch(url).then(r => {
            if (!r.ok) throw new Error(`${r.status} ${url}`)
            return r.text()
        }))
    }
    return _cache.get(url)
}

const _sheets = new Map()

async function _sheet(url) {
    if (!_sheets.has(url)) {
        _sheets.set(url, _fetchText(url).then(css => {
            const s = new CSSStyleSheet()
            s.replaceSync(css)
            return s
        }))
    }
    return _sheets.get(url)
}

export class SgComponent extends HTMLElement {

    static jsUrl = import.meta.url

    get resourceName() {
        throw new Error(`${this.constructor.name} must define get resourceName()`)
    }

    get sharedCssPaths() {
        return []
    }

    /** Called once the shadow root is populated. Override this, never connectedCallback. */
    onReady() {}

    /** Resolve a path against the component's own directory. */
    resolve(relative) {
        const base = this.constructor.jsUrl
        if (!base) throw new Error(`${this.constructor.name} must set static jsUrl = import.meta.url`)
        return new URL(relative, base).href
    }

    /** The site root, derived from this component's own URL — it lives under assets/components/. */
    get siteRoot() {
        return this.resolve('../../../../../../').replace(/assets\/$/, '')
    }

    async connectedCallback() {
        if (this._ready) return
        this._ready = true
        const name = this.resourceName
        const shadow = this.attachShadow({ mode: 'open' })
        try {
            const [markup, own, ...shared] = await Promise.all([
                _fetchText(this.resolve(`${name}.tpl`)),
                _sheet(this.resolve(`${name}.css`)),
                ...this.sharedCssPaths.map(p => _sheet(p)),
            ])
            shadow.adoptedStyleSheets = [...shared, own]
            shadow.innerHTML = markup
            this.onReady()
        } catch (err) {
            /* A component that fails to load says so where a reader can see it. Failing silently
               would leave an empty box, which is the one outcome that looks like a design choice. */
            shadow.innerHTML = ''
            const p = document.createElement('p')
            p.style.cssText = 'font:13px/1.5 ui-monospace,monospace;color:#b91c1c;padding:12px'
            p.textContent = `<${name}> did not load: ${err.message}`
            shadow.appendChild(p)
        }
    }

    /** Dispatch a namespaced event that escapes the shadow root, per the estate's convention. */
    emit(name, detail) {
        document.dispatchEvent(new CustomEvent(name, { detail, bubbles: true, composed: true }))
    }

    $(sel) { return this.shadowRoot.querySelector(sel) }
    $$(sel) { return [...this.shadowRoot.querySelectorAll(sel)] }
}

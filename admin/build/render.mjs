/**
 * pt.newsroom.sgit.ai — the gate that was missing: open the pages in a real browser.
 *
 *     python3 -m http.server 8777 --bind 127.0.0.1 &
 *     node admin/build/render.mjs [http://127.0.0.1:8777]
 *
 * WHY THIS EXISTS. `build/gates.py` reads files and `admin/build/validate.js` reads HTML. Neither
 * of them EXECUTES anything. A component that throws on load — a wrong path, a `fetch` for a file
 * that was renamed, a syntax error in a module — passes all three gates and reaches the reader as
 * an empty box. And an empty box looks like a design choice.
 *
 * This file opens every page carrying a component, in a real Chromium, and fails if:
 *
 *   · the browser console writes an error, or the page throws;
 *   · any request fails or answers 400 or above;
 *   · a custom element is never defined, opens no shadow root, or comes up empty;
 *   · an element inside it carries `hidden` and is on screen anyway;
 *   · the host ends at `data-estado="erro"`, or never reaches `data-estado="pronto"` — the gate
 *     waits for that attribute to appear rather than sleeping a fixed number of milliseconds,
 *     because a sleep measures the machine the gate runs on and not the site;
 *   · the base class's "did not load" warning appears;
 *   · a component is stuck on its own loading text;
 *   · the page overflows horizontally at 390px wide.
 *
 * IT DOES NOT RUN IN CI, said here so nobody assumes it does: it needs a browser installed, and
 * this repository has no node dependencies. It is a local check, run before any release that
 * touches components. When CI has a browser, it becomes a gate without a line of this file
 * changing.
 */
/* Playwright is NOT a dependency of this repository and is not going to become one: a static site
   built with python3 and one node file should not need an `npm install` to publish. So the module
   is imported dynamically and may come from outside, via `PLAYWRIGHT_MODULE`; and the browser via
   `CHROME_PATH`, for when what is installed is not what that version of playwright expects:

     PLAYWRIGHT_MODULE=/caminho/node_modules/playwright/index.mjs \
     CHROME_PATH=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
     node admin/build/render.mjs

   With neither, `playwright` resolves normally. */
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')

const BASE = process.argv[2] || 'http://127.0.0.1:8777'

/* One page per component, plus the pages that combine them. Not the whole site: 232 pages in a
   browser is slow and repetitive, and what is being checked is the code that runs, not the HTML. */
const PAGINAS = [
    /* `pt-chat` is on every page the reader sees — 227 of them — so it is named on every reader
       page in this list rather than checked once. A panel that throws on one template and not
       another is exactly the failure a single sample would miss. It is NOT on the back-office
       pages below, and that is deliberate: the chat talks to the paper, in Portuguese, and the
       back office is the English side of the house. */
    ['/', ['pt-chat']],
    ['/redacao/', ['pt-newsroom-floor', 'pt-chat']],
    ['/entidades/', ['pt-chat']],
    ['/entidades/editor/comissao-europeia/', ['pt-entity-graph', 'pt-chat']],
    ['/entidades/pessoa/paulo-andrez/', ['pt-entity-graph', 'pt-chat']],
    ['/artigos/2026/09/14/uma-captura-nao-mostra-movimento/',
     ['pt-json-viewer', 'pt-comment-map', 'pt-chat']],
    ['/backoffice/agents.html', ['pt-comment-map']],
    ['/backoffice/docs.html', ['pt-doc-browser']],
    ['/api/', ['pt-api-console', 'pt-chat']],
    ['/grafo/', ['pt-chat']],
    ['/protagonistas/', ['pt-chat']],
    /* The team, board and mail pages have no components, and the bridges page has the largest
       script block on this site — the unlock and the message box. None of them uses a custom
       element, so none would be caught by a list made of components; but it is code that runs, and
       that is what this gate checks. Being out by default is precisely the kind of exemption gate
       26 says you should not be able to claim by writing the right word. */
    ['/backoffice/guidance.html', []],
    ['/backoffice/equipa.html', []],
    ['/backoffice/quadro.html', []],
    ['/backoffice/correio.html', []],
    ['/backoffice/pontes.html', []],
]

/* Chromium asks for `/favicon.ico` on its own, unprompted, and on a site serving an SVG that is a
   404 the reader never sees. The browser's own request is ignored, not the site's: if a PAGE asks
   for a file that does not exist, that still fails. */
const RUIDO = [/\/favicon\.ico$/]

const navegador = await chromium.launch(
    process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {})

let falhas = 0
for (const [caminho, comps] of PAGINAS) {
    const ctx = await navegador.newContext({ viewport: { width: 1280, height: 900 } })
    const pag = await ctx.newPage()
    const erros = []
    const ruidoso = u => RUIDO.some(r => r.test(u))

    pag.on('console', m => { if (m.type() === 'error' && !ruidoso(m.location()?.url || '')) erros.push(`consola: ${m.text()}`) })
    pag.on('pageerror', e => erros.push(`exceção: ${e.message}`))
    pag.on('requestfailed', r => { if (!ruidoso(r.url())) erros.push(`pedido falhou: ${r.url()} (${r.failure()?.errorText})`) })
    pag.on('response', r => { if (r.status() >= 400 && !ruidoso(r.url())) erros.push(`HTTP ${r.status()}: ${r.url()}`) })

    await pag.goto(BASE + caminho, { waitUntil: 'networkidle' })

    /* WAIT FOR THE STATE, NOT FOR A DURATION. This used to be `waitForTimeout(400)`, and that is
       how a gate becomes a coin toss: on the graph page Cytoscape runs its layout on the main
       thread, the components' own `fetch` for their markup resolves behind it, and 400ms found
       `pt-chat` with an empty shadow root — reported as a broken component when it was ready at
       three seconds. A fixed sleep measures the machine the gate runs on.

       So the gate waits for what it is actually asserting: every named component carrying a
       `data-estado`, which the base class sets on the host once `onReady()` has returned or
       thrown. Reaching the timeout is still a failure, and a real one — a component that needs
       more than TEMPO_LIMITE to open is a component the reader sees as an empty box. */
    const TEMPO_LIMITE = 10000
    if (comps.length) {
        try {
            await pag.waitForFunction(
                ts => ts.every(t => document.querySelector(t)?.hasAttribute('data-estado')),
                comps, { timeout: TEMPO_LIMITE })
        } catch {
            /* Not reported here: the per-component checks below name which one, and what state it
               was left in, which is the sentence somebody can act on. */
        }
    }
    await pag.waitForTimeout(200)

    for (const tag of comps) {
        const info = await pag.evaluate(t => {
            const el = document.querySelector(t)
            if (!el) return { falta: true }
            const sr = el.shadowRoot
            return {
                definido: !!customElements.get(t),
                sombra: !!sr,
                texto: sr ? (sr.textContent || '').trim().slice(0, 240) : '',
                filhos: sr ? sr.children.length : 0,
                estado: el.getAttribute('data-estado'),
                erro: el.getAttribute('data-erro'),
                /* `hidden` THAT DOES NOT HIDE. The UA stylesheet's `[hidden] { display: none }`
                   has the specificity of one attribute selector, so any class rule in the
                   component's own sheet that sets `display` silently beats it. `pt-chat` shipped
                   with `.painel { display: flex }` and an element that was `hidden`: the panel
                   was permanently open, lying across the article — and it passed every check here,
                   because the component WAS at «pronto», nothing threw and nothing overflowed.
                   So the gate stops trusting the attribute and reads the computed style. */
                fantasmas: [...sr.querySelectorAll('[hidden]')]
                    .filter(x => getComputedStyle(x).display !== 'none')
                    .map(x => x.id || x.className || x.tagName.toLowerCase()),
            }
        }, tag)
        if (info.falta) { erros.push(`<${tag}> não está na página`); continue }
        if (!info.definido) erros.push(`<${tag}> nunca foi definido — o módulo não correu`)
        if (!info.sombra) erros.push(`<${tag}> não abriu raiz de sombra`)
        if (!info.filhos) erros.push(`<${tag}> ficou vazio`)
        /* THE SIGNAL THAT WAS MISSING. A component that catches its own error and draws a
           friendly message is doing right by the reader and wrong by whatever checks the page: no
           console error, no exception, a shadow root full of text — it looks healthy. That is how
           an exception mid-`_render()` got through this check. Now the base class puts
           `data-estado` on the host, outside the shadow root, and failure stops being legible only
           to a person. */
        if (info.estado === 'erro')
            erros.push(`<${tag}> declarou-se em erro: ${info.erro || 'sem motivo'}`)
        else if (info.estado !== 'pronto')
            erros.push(`<${tag}> nunca chegou a «pronto» (data-estado=${info.estado ?? 'ausente'})`)
        for (const f of info.fantasmas || [])
            erros.push(`<${tag}> tem «${f}» com o atributo hidden e à vista — uma regra de classe ` +
                       `com «display» está a ganhar ao [hidden] do navegador`)
        if (/did not load/.test(info.texto)) erros.push(`<${tag}> mostrou o aviso de falha: ${info.texto}`)
        if (/a carregar/.test(info.texto) && info.texto.length < 80)
            erros.push(`<${tag}> ficou preso em «a carregar»: ${info.texto}`)
    }

    /* 390px. A grid that overflows pushes the body sideways and the phone reader ends up dragging
       the page horizontally to read one sentence. It has happened on this site once. */
    await pag.setViewportSize({ width: 390, height: 844 })
    await pag.waitForTimeout(250)
    const larg = await pag.evaluate(() =>
        ({ doc: document.documentElement.scrollWidth, janela: window.innerWidth }))
    if (larg.doc > larg.janela + 1)
        erros.push(`transborda a 390px: scrollWidth ${larg.doc} > ${larg.janela}`)

    const unicos = [...new Set(erros)]
    if (unicos.length) {
        falhas++
        console.log(`\n✗ ${caminho}`)
        for (const e of unicos) console.log(`    ${e}`)
    } else {
        console.log(`✓ ${caminho}${comps.length ? '  ' + comps.join(' ') : ''}`)
    }
    await ctx.close()
}

await navegador.close()
if (falhas) {
    console.log(`\nrender: ${falhas} página(s) com problemas`)
    process.exit(1)
}
console.log(`\nrender: OK — ${PAGINAS.length} pages opened in a browser, ` +
            `no console errors, no failed requests, every component at "pronto", ` +
            `none overflowing at 390px`)

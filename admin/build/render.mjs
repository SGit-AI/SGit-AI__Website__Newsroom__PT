/**
 * pt.newsroom.sgit.ai — o portão que faltava: abrir as páginas num navegador de verdade.
 *
 *     python3 -m http.server 8777 --bind 127.0.0.1 &
 *     node admin/build/render.mjs [http://127.0.0.1:8777]
 *
 * PORQUE É QUE ISTO EXISTE. `build/gates.py` lê ficheiros e `admin/build/validate.js` lê HTML.
 * Nenhum dos dois EXECUTA nada. Um componente que rebente ao carregar — um caminho errado, um
 * `fetch` para um ficheiro que mudou de nome, um erro de sintaxe num módulo — passa os três
 * portões e chega ao leitor como uma caixa vazia. E uma caixa vazia parece uma escolha de desenho.
 *
 * Este ficheiro abre cada página que tem um componente, num Chromium a sério, e falha se:
 *
 *   · a consola do navegador escrever um erro, ou a página lançar uma exceção;
 *   · algum pedido falhar ou responder 400 ou mais;
 *   · um elemento personalizado não ficar definido, não abrir raiz de sombra, ou ficar vazio;
 *   · o host ficar com `data-estado="erro"`, ou não chegar a `data-estado="pronto"`;
 *   · aparecer o aviso «did not load» que a classe-base mostra quando não consegue carregar;
 *   · um componente ficar preso no seu texto de «a carregar»;
 *   · a página transbordar na horizontal a 390px de largura.
 *
 * NÃO CORRE NA INTEGRAÇÃO CONTÍNUA, e é dito aqui para não se pensar que corre: precisa de um
 * navegador instalado, e este repositório não tem dependências de node. É uma conferência local,
 * a correr antes de um lançamento que mexa em componentes. Quando a CI tiver um navegador, passa
 * a portão sem mudar uma linha deste ficheiro.
 */
/* O playwright NÃO é uma dependência deste repositório, e não vai passar a ser: um sítio estático
   que se constrói com python3 e um ficheiro de node não deve precisar de um `npm install` para se
   publicar. Por isso o módulo é importado dinamicamente e pode vir de fora, por
   `PLAYWRIGHT_MODULE`; e o navegador por `CHROME_PATH`, para quando o que está instalado não é o
   que aquela versão do playwright espera:

     PLAYWRIGHT_MODULE=/caminho/node_modules/playwright/index.mjs \
     CHROME_PATH=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
     node admin/build/render.mjs

   Sem nenhuma das duas, resolve-se `playwright` normalmente. */
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')

const BASE = process.argv[2] || 'http://127.0.0.1:8777'

/* Uma página por componente, e as páginas que os juntam. Não é o site inteiro: 232 páginas num
   navegador é lento e repetitivo, e o que se está a conferir é o código que corre, não o HTML. */
const PAGINAS = [
    ['/', []],
    ['/redacao/', ['pt-newsroom-floor']],
    ['/entidades/', []],
    ['/entidades/editor/comissao-europeia/', ['pt-entity-graph']],
    ['/entidades/pessoa/paulo-andrez/', ['pt-entity-graph']],
    ['/artigos/2026/09/14/uma-captura-nao-mostra-movimento/', ['pt-json-viewer', 'pt-comment-map']],
    ['/backoffice/agents.html', ['pt-comment-map']],
    ['/backoffice/docs.html', ['pt-doc-browser']],
    ['/api/', ['pt-api-console']],
    ['/grafo/', []],
    ['/protagonistas/', []],
]

/* Chromium pede `/favicon.ico` sozinho, sem ninguém lho mandar, e num sítio que serve um SVG isso
   é um 404 que o leitor nunca vê. Ignora-se o pedido do navegador e não o do site: se uma PÁGINA
   pedir um ficheiro que não existe, isso continua a falhar. */
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
    await pag.waitForTimeout(400)

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
            }
        }, tag)
        if (info.falta) { erros.push(`<${tag}> não está na página`); continue }
        if (!info.definido) erros.push(`<${tag}> nunca foi definido — o módulo não correu`)
        if (!info.sombra) erros.push(`<${tag}> não abriu raiz de sombra`)
        if (!info.filhos) erros.push(`<${tag}> ficou vazio`)
        /* O SINAL QUE FALTAVA. Um componente que apanha o seu próprio erro e desenha uma mensagem
           amável está a fazer o certo pelo leitor e o errado por quem confere a página: sem erro
           de consola, sem exceção, com a sombra cheia de texto — parece saudável. Foi assim que
           uma exceção a meio de um `_render()` passou por esta conferência. Agora a classe-base
           põe `data-estado` no host, fora da sombra, e a falha deixa de ser só legível por uma
           pessoa. */
        if (info.estado === 'erro')
            erros.push(`<${tag}> declarou-se em erro: ${info.erro || 'sem motivo'}`)
        else if (info.estado !== 'pronto')
            erros.push(`<${tag}> nunca chegou a «pronto» (data-estado=${info.estado ?? 'ausente'})`)
        if (/did not load/.test(info.texto)) erros.push(`<${tag}> mostrou o aviso de falha: ${info.texto}`)
        if (/a carregar/.test(info.texto) && info.texto.length < 80)
            erros.push(`<${tag}> ficou preso em «a carregar»: ${info.texto}`)
    }

    /* 390px. Uma grelha que transborda empurra o corpo para o lado e o leitor de telemóvel passa
       a arrastar a página na horizontal para ler uma frase. Já aconteceu neste site uma vez. */
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
console.log(`\nrender: OK — ${PAGINAS.length} páginas abertas num navegador, ` +
            `nenhum erro de consola, nenhum pedido falhado, cada componente em «pronto», ` +
            `nenhuma a transbordar a 390px`)

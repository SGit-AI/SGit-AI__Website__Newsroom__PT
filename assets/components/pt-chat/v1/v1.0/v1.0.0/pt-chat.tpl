<div id="rail" class="rail">
  <button id="abrir" class="aba" type="button" aria-expanded="false">
    <span class="ponto"></span>conversa</button>
</div>

<aside id="painel" class="painel" hidden aria-label="Falar com este conteúdo">
  <div id="puxador" class="puxador" role="separator" aria-orientation="vertical"
       tabindex="0" title="arrastar para redimensionar"></div>

  <header class="topo">
    <div class="titulo">CONVERSA <span id="gasto" class="gasto">nada gasto ainda</span></div>
    <div class="acts">
      <button id="nova" class="btn" type="button">nova conversa</button>
      <button id="fechar" class="btn x" type="button" aria-label="fechar">✕</button>
    </div>
  </header>

  <details id="d-envio" class="dobra">
    <summary>o que envio — o que viaja com a sua pergunta</summary>
    <div id="envio" class="dobra-corpo"></div>
  </details>

  <details id="d-ferr" class="dobra">
    <summary>o que pode fazer — as ferramentas, todas visíveis em baixo quando usadas</summary>
    <div id="ferramentas" class="dobra-corpo"></div>
  </details>

  <div id="fluxo" class="fluxo"></div>

  <div id="sugestoes" class="sugestoes"></div>

  <form id="forma" class="forma">
    <textarea id="pergunta" rows="2" placeholder="Pergunte sobre as fontes, o grafo, um artigo…"
              aria-label="a sua pergunta"></textarea>
    <div class="fundo">
      <select id="modelo" aria-label="modelo"></select>
      <button id="enviar" class="enviar" type="submit">enviar</button>
    </div>
    <div id="chave-linha" class="chave-linha"></div>
  </form>
</aside>

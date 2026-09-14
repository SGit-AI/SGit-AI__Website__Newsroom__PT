<div class="bar" part="bar">
  <button id="open" type="button" class="badge" aria-expanded="false">
    <span class="dot"></span>
    <span id="bal">—</span>
    <span class="lbl">carteira</span>
  </button>
  <div id="panel" class="panel" hidden>
    <div class="head">
      <b>A carteira</b>
      <button id="close" type="button" class="x" aria-label="fechar">×</button>
    </div>
    <p class="demo"><b>Isto é uma demonstração e não cobra nada a ninguém.</b> Não há pagamento,
      não há conta, e nada sai deste navegador: o saldo vive em <code>localStorage</code> e
      apaga-se quando limpar os dados do site. Está aqui porque o argumento do site-mãe — pagar a
      quem cria o facto — vale mais demonstrado numa publicação a sério do que defendido num
      ensaio.</p>
    <div class="grid">
      <div><span class="k">Saldo</span><span id="bal2" class="v">—</span></div>
      <div><span class="k">Preço por página</span><span id="price" class="v">—</span></div>
      <div><span class="k">Páginas lidas</span><span id="reads" class="v">—</span></div>
      <div><span class="k">Gasto</span><span id="spent" class="v">—</span></div>
    </div>
    <div class="acts">
      <button id="topup" type="button">recarregar para €5,00</button>
      <button id="reset" type="button" class="ghost">apagar o registo</button>
    </div>
    <div class="ledger">
      <div class="k">As últimas páginas</div>
      <ul id="log"></ul>
    </div>
    <p class="foot">Cada página deste site custa <b id="price2">—</b> a abrir. Quando o saldo
      chega a zero, recarrega-se. Numa versão a sério, o dinheiro iria para quem produziu a fonte
      congelada em que a página assenta — que é a razão de este site registar sempre qual é.</p>
  </div>
</div>

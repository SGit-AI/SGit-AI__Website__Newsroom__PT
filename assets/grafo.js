/* pt.newsroom.sgit.ai — o visualizador do grafo.
 *
 * Cytoscape está alojado neste repositório (assets/vendor/), nunca obtido de uma CDN: uma página
 * que precisa de um terceiro para renderizar é uma página que um terceiro pode deixar de
 * renderizar, e este site publica-se a si próprio.
 *
 * O que este visualizador faz de diferente do de onde veio: a leitura de um caminho é PORTUGUESA
 * e não tem um seletor de língua. A quinta regra publicada do grafo diz que, se um caminho não se
 * lê como uma frase na língua do leitor, as arestas estão erradas — e o leitor deste site é
 * português. Um seletor faria da língua uma opção, e ela é o teste.
 *
 * window.__grafo fica exposto para quem quiser interrogar o grafo a partir da consola, ou para um
 * agente que chegue à página: nós, arestas, a ontologia e a função que lê um caminho em voz alta.
 */
(function () {
  'use strict';
  var alvo = document.getElementById('cy');
  if (!alvo || typeof cytoscape === 'undefined') return;

  function dizer(msg) {
    alvo.innerHTML = '<p class="sm" style="padding:18px">' + msg + '</p>';
  }

  Promise.all([
    fetch(alvo.dataset.grafo).then(function (r) { return r.json(); }),
    fetch(alvo.dataset.grafo.replace('grafo.json', 'ontologia.json')).then(function (r) { return r.json(); })
  ]).then(function (res) {
    var g = res[0], onto = res[1];
    var cor = {};
    onto.tipos.forEach(function (t) { cor[t.id] = t.cor; });
    var leitura = {};
    onto.arestas.forEach(function (a) { if (!leitura[a.verbo]) leitura[a.verbo] = a; });

    var elementos = g.nos.map(function (n) {
      return { data: { id: n.id, rotulo: n.rotulo, tipo: n.tipo, bloco: n.bloco, fonte: n.fonte } };
    }).concat(g.arestas.map(function (a) {
      return { data: { id: a.id, source: a.origem, target: a.destino, verbo: a.verbo, bloco: a.bloco } };
    }));

    var cy = cytoscape({
      container: alvo,
      elements: elementos,
      layout: { name: 'cose', animate: false, nodeRepulsion: 9000, idealEdgeLength: 90,
                padding: 30, randomize: true },
      style: [
        { selector: 'node', style: {
            'background-color': function (n) { return cor[n.data('tipo')] || '#8a8d94'; },
            'label': 'data(rotulo)', 'font-family': 'Newsreader, Georgia, serif',
            'font-size': '11px', 'color': '#17181c', 'text-valign': 'bottom',
            'text-margin-y': 4, 'text-max-width': '120px', 'text-wrap': 'ellipsis',
            'width': 14, 'height': 14 } },
        { selector: 'node[tipo="Evento"]', style: { 'width': 30, 'height': 30, 'font-size': '13px' } },
        { selector: 'edge', style: {
            'width': 1, 'line-color': '#c9c2ae', 'curve-style': 'bezier',
            'target-arrow-color': '#c9c2ae', 'target-arrow-shape': 'triangle', 'arrow-scale': 0.7 } },
        { selector: '.destacado', style: {
            'background-color': '#0f766e', 'width': 22, 'height': 22, 'font-size': '13px',
            'color': '#0f766e', 'z-index': 99 } },
        { selector: '.caminho', style: { 'line-color': '#0f766e', 'width': 3,
            'target-arrow-color': '#0f766e', 'z-index': 98 } },
        { selector: '.apagado', style: { 'opacity': 0.12 } }
      ]
    });

    var saida = document.createElement('div');
    saida.className = 'painel';
    saida.style.marginTop = '10px';
    saida.innerHTML = '<p class="sm">Clique num nó para o destacar. Clique em dois com <b>shift</b> ' +
                      'para ler o caminho entre eles em voz alta.</p>';
    alvo.parentNode.insertBefore(saida, alvo.nextSibling);

    /* Ler um caminho em voz alta, em português. É o teste de aceitação da ontologia: se isto não
       produz uma frase, as arestas estão erradas — e é por isso que a frase é construída a partir
       do campo `leitura` de cada verbo, e não montada aqui com um verbo à escolha. */
    function lerCaminho(nos) {
      var partes = [];
      for (var i = 0; i < nos.length - 1; i++) {
        var a = cy.edges().filter(function (ed) {
          return (ed.source().id() === nos[i] && ed.target().id() === nos[i + 1]) ||
                 (ed.target().id() === nos[i] && ed.source().id() === nos[i + 1]);
        })[0];
        if (!a) continue;
        var def = leitura[a.data('verbo')];
        if (!def) continue;
        var directa = a.source().id() === nos[i];
        var modelo = directa ? def.leitura : def.leitura_inversa;
        var s = cy.getElementById(directa ? nos[i] : nos[i + 1]).data('rotulo');
        var t = cy.getElementById(directa ? nos[i + 1] : nos[i]).data('rotulo');
        partes.push(modelo.replace('{s}', s).replace('{t}', t));
      }
      return partes.join('; e ') + '.';
    }

    var seleccao = [];
    cy.on('tap', 'node', function (ev) {
      var id = ev.target.id();
      if (!ev.originalEvent.shiftKey) {
        seleccao = [id];
        cy.elements().removeClass('destacado caminho apagado');
        ev.target.addClass('destacado');
        var n = ev.target.data();
        saida.innerHTML = '<p class="sm"><b>' + n.rotulo + '</b> · ' + n.tipo +
          (n.fonte ? ' · <a href="../registo/#' + n.fonte + '">' + n.fonte + '</a>' : '') +
          ' · ' + ev.target.degree() + ' ligações</p>';
        return;
      }
      seleccao.push(id);
      if (seleccao.length > 2) seleccao = seleccao.slice(-2);
      if (seleccao.length < 2) return;
      var dijkstra = cy.elements().dijkstra({ root: cy.getElementById(seleccao[0]),
                                              directed: false });
      var caminho = dijkstra.pathTo(cy.getElementById(seleccao[1]));
      if (!caminho || caminho.length === 0) {
        saida.innerHTML = '<p class="sm">Não há caminho entre estes dois nós.</p>';
        return;
      }
      cy.elements().removeClass('destacado caminho').addClass('apagado');
      caminho.removeClass('apagado');
      caminho.nodes().addClass('destacado');
      caminho.edges().addClass('caminho');
      var ids = caminho.nodes().map(function (n) { return n.id(); });
      saida.innerHTML = '<p class="caminho">' + lerCaminho(ids) + '</p>' +
        '<p class="xs" style="padding-top:6px">' + (ids.length - 1) + ' aresta(s). Se isto não se ' +
        'lê como uma frase portuguesa, alguma destas arestas está errada — e é um defeito a ' +
        'comunicar, não um detalhe de apresentação.</p>';
    });

    cy.on('tap', function (ev) {
      if (ev.target === cy) {
        seleccao = [];
        cy.elements().removeClass('destacado caminho apagado');
      }
    });

    window.__grafo = { cy: cy, nos: g.nos, arestas: g.arestas, ontologia: onto,
                       lerCaminho: lerCaminho };
  }).catch(function (err) {
    dizer('O grafo não carregou: ' + err.message + '. Os dados continuam em ' +
          '<a href="../dados/grafo.json">dados/grafo.json</a> e ' +
          '<a href="../dados/triplos.nt">dados/triplos.nt</a>.');
  });
})();

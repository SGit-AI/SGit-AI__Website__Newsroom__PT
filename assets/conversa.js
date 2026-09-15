/* pt.newsroom.sgit.ai — «falar com este conteúdo», num site que não tem servidor.
 *
 * O PROBLEMA, E OS DOIS NÍVEIS QUE ELE OBRIGA
 *
 * Este site é estático. Não há servidor, e por isso não há onde guardar uma chave de API. O
 * desenho é o que sgit.ai publica em `articles/chat-on-a-static-site.md`, com os mesmos dois
 * níveis e pela mesma razão:
 *
 *   NÍVEL 0 — por omissão, e é o que está ligado. Um comparador determinístico que corre no
 *   navegador contra o índice que a construção emitiu. Instantâneo, gratuito, privado, funciona
 *   sem rede, e — a parte que o torna a omissão e não o parente pobre — **diz porque escolheu**.
 *   Mostra as palavras que bateram e onde bateram. Não inventa: encaminha.
 *
 *   NÍVEL 1 — opcional, e só se o leitor der a sua própria chave. Chamadas diretas do navegador
 *   para o OpenRouter, com ferramentas sobre a API deste site. A chave fica em `localStorage`, e
 *   o que isso significa está escrito no painel sem rodeios: **sem anfitrião não há chão de
 *   permissões, e a chave vive na origem desta página**. Não passa por pt.newsroom.sgit.ai —
 *   não há por onde passar. Se falhar, cai para o nível 0 em vez de deixar de responder.
 *
 * AS FERRAMENTAS SÃO A API DESTE SITE, E A API É SÓ FICHEIROS
 *
 * Não há verbo que não seja GET, porque cada caminho de `/api/v1/` é um ficheiro no disco. Isso
 * faz das ferramentas uma coisa invulgarmente segura de dar a um modelo: o pior que uma chamada
 * pode fazer é ler uma coisa que já é pública. Não há escrita, não há autenticação para roubar, e
 * não há um endereço construído que possa alcançar outra coisa — a lista de caminhos permitidos
 * está aqui em baixo e nada fora dela é buscado.
 *
 * O QUE ISTO NÃO FAZ
 *
 * Não publica, não altera um ficheiro, não fala com o cofre e não escreve correio. Para falar com
 * a redação há a ponte em `/backoffice/pontes.html`, que é outra coisa e tem outras regras. Este
 * painel lê, e mais nada.
 */
(function (global) {
  "use strict";

  var CHAVE = "pt-newsroom:conversa:openrouter";
  var MODELO = "pt-newsroom:conversa:modelo";
  var MODELO_OMISSAO = "anthropic/claude-sonnet-4.5";
  var API = "/api/v1/";

  /* As ferramentas. Cada uma é um GET a um caminho de `/api/v1/`, e a lista é fechada: um nome
   * que não esteja aqui não é buscado, e um `{id}` é higienizado antes de entrar no caminho. */
  var FERRAMENTAS = [
    { nome: "listar_seccoes", caminho: "sections.json",
      descricao: "As oito secções e o registo editorial de cada uma: o que cobre, e o que pode e " +
                 "não pode afirmar hoje." },
    { nome: "listar_fontes", caminho: "sources.json",
      descricao: "O registo das fontes congeladas: endereço, bytes, SHA-256 e hora de obtenção de " +
                 "cada uma. É aqui que uma afirmação acaba por assentar." },
    { nome: "ler_fonte", caminho: "sources/{id}.json", id: true,
      descricao: "Uma fonte congelada em particular, pelo seu id." },
    { nome: "listar_empresas", caminho: "companies.json",
      descricao: "As organizações que o grafo conhece, derivadas das fontes." },
    { nome: "ler_empresa", caminho: "companies/{id}.json", id: true,
      descricao: "Uma organização, pelo seu id." },
    { nome: "listar_pessoas", caminho: "people.json",
      descricao: "As pessoas que o grafo conhece. Sem contactos: nenhum contacto de pessoa " +
                 "singular existe em ficheiro nenhum deste site." },
    { nome: "ler_pessoa", caminho: "people/{id}.json", id: true,
      descricao: "Uma pessoa, pelo seu id." },
    { nome: "listar_artigos", caminho: "articles.json",
      descricao: "Cada artigo, o seu estado e onde está a sua pasta. Publicado só quando o editor " +
                 "de registo escreve essa linha." },
    { nome: "ler_artigo", caminho: "articles/{id}.json", id: true,
      descricao: "Um artigo pelo seu slug, com as suas afirmações e a proveniência." },
    { nome: "o_grafo", caminho: "graph.json",
      descricao: "O grafo inteiro: nós e arestas. Cada aresta é um verbo português com um inverso " +
                 "distinto." },
    { nome: "a_ontologia", caminho: "ontology.json",
      descricao: "Os tipos e os verbos, cada um com a sua leitura e o seu inverso." },
    { nome: "listar_entregas", caminho: "deliveries.json",
      descricao: "As entregas de investigação de assistentes exteriores, e o que aconteceu a cada " +
                 "excerto quando se foi procurá-lo nos bytes. Pistas, nunca factos." },
    { nome: "os_agentes", caminho: "agents.json",
      descricao: "O registo dos agentes desta redação: missão, afirmação central escrita como " +
                 "condição de falha, e aquilo de que cada um não é responsável." },
    { nome: "o_quadro", caminho: "board.json",
      descricao: "O que cada agente tem à frente: os cartões que abriu para si, e os issues do " +
                 "jornal que a fórmula publicada lhe põe no quadro." },
    { nome: "o_correio", caminho: "mail.json",
      descricao: "As mensagens entre os agentes. O estado de cada uma é a pasta onde está." },
    { nome: "a_mesa", caminho: "desk.json",
      descricao: "O estado da redação: as bancadas, a carga de cada uma, e o quadro." },
    { nome: "o_aviso", caminho: "notice.json",
      descricao: "O aviso de proteção de dados como dados: responsável, categorias guardadas e " +
                 "recusadas, o teste de ponderação, e a via de remoção incondicional." },
    { nome: "fontes_excluidas", caminho: "excluded.json",
      descricao: "As fontes que foram tentadas e não resolveram. Uma fonte que esta redação não " +
                 "alcança é um facto sobre o registo público, e não um silêncio." },
  ];

  function guardado(k, omissao) {
    try { var v = global.localStorage.getItem(k); return v === null ? omissao : v; }
    catch (e) { return omissao; }
  }
  function guardar(k, v) {
    try { global.localStorage.setItem(k, v); return true; } catch (e) { return false; }
  }
  function esquecer(k) {
    try { global.localStorage.removeItem(k); } catch (e) { /* nada */ }
  }

  function raiz() {
    /* A profundidade da página decide o caminho para `/api/v1/`. Uma raiz absoluta funcionaria em
     * produção e partiria em qualquer pré-visualização servida a partir de uma subpasta. */
    var n = location.pathname.replace(/^\/|\/$/g, "").split("/").length - 1;
    return location.pathname.endsWith("/") || location.pathname.endsWith(".html")
      ? new Array(Math.max(0, n) + 1).join("../") : "";
  }

  function buscar(caminho) {
    return fetch(raiz() + API + caminho, { credentials: "omit" })
      .then(function (r) {
        if (!r.ok) throw new Error(caminho + " respondeu " + r.status);
        return r.json();
      });
  }

  /* ------------------------------------------------------- nível 0: o comparador ---
   * Determinístico, e a sua virtude é dizer porque escolheu. O índice é `/api/v1/index.json`
   * mais as secções: o que a construção emitiu, e não uma lista escrita à mão que envelhece. */
  var VAZIAS = ("a o as os de do da das dos e em no na nos nas que por para com um uma uns umas " +
    "se ao aos à às pelo pela como mais mas ou ser sobre qual quais quem onde quando quanto " +
    "quantos porque é são foi eram tem têm há este esta estes estas isso").split(" ");

  function palavras(s) {
    return String(s || "").toLowerCase()
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .split(/[^a-z0-9]+/)
      .filter(function (p) { return p.length > 2 && VAZIAS.indexOf(p) === -1; });
  }

  function comparar(pergunta, catalogo) {
    var termos = palavras(pergunta);
    return catalogo.map(function (item) {
      var pontos = 0, bateram = [];
      termos.forEach(function (t) {
        /* Um acerto no nome ou no caminho pesa mais do que um acerto no resumo. O nome é o que a
         * coisa É; o resumo é o que alguém disse sobre ela. */
        if (palavras(item.nome).indexOf(t) !== -1) { pontos += 3; bateram.push(t + " (no nome)"); }
        else if (palavras(item.caminho).indexOf(t) !== -1) { pontos += 2; bateram.push(t + " (no caminho)"); }
        else if (palavras(item.resumo).indexOf(t) !== -1) { pontos += 1; bateram.push(t + " (no resumo)"); }
      });
      return { item: item, pontos: pontos, bateram: bateram };
    }).filter(function (x) { return x.pontos > 0; })
      .sort(function (a, b) { return b.pontos - a.pontos; })
      .slice(0, 5);
  }

  function catalogo() {
    return Promise.all([
      buscar("index.json").catch(function () { return null; }),
      buscar("sections.json").catch(function () { return null; }),
    ]).then(function (r) {
      var out = [];
      (((r[0] || {}).collections) || ((r[0] || {}).coleccoes) || []).forEach(function (c) {
        out.push({
          nome: c.path || c.nome || "", caminho: "/api/v1/" + (c.path || "") + ".json",
          resumo: c.summary || c.description || "", tipo: "colecção da API",
        });
      });
      (((r[1] || {}).sections) || []).forEach(function (s) {
        out.push({
          nome: s.nome || s.id || "", caminho: "/" + (s.id || "") + "/",
          resumo: [s.o_que_cobre, s.o_que_pode_afirmar, s.o_que_nao_pode_afirmar]
            .filter(Boolean).join(" ").slice(0, 400),
          tipo: "secção do jornal",
        });
      });
      FERRAMENTAS.forEach(function (f) {
        out.push({ nome: f.nome.replace(/_/g, " "), caminho: "/api/v1/" + f.caminho,
                   resumo: f.descricao, tipo: "caminho da API" });
      });
      return out;
    });
  }

  /* --------------------------------------------------- nível 1: o OpenRouter ---
   * Chamadas diretas do navegador, com as ferramentas acima. O laço corre no máximo seis voltas:
   * um modelo que não conclui em seis chamadas de leitura não vai concluir na sétima, e um laço
   * sem tecto num navegador é uma conta a crescer sem ninguém a ver. */
  function esquemaDeFerramentas() {
    return FERRAMENTAS.map(function (f) {
      var props = {}, obrig = [];
      if (f.id) {
        props.id = { type: "string", description: "O identificador, tal como a listagem o dá." };
        obrig.push("id");
      }
      return {
        type: "function",
        function: {
          name: f.nome, description: f.descricao,
          parameters: { type: "object", properties: props, required: obrig },
        },
      };
    });
  }

  function correrFerramenta(nome, args) {
    var f = FERRAMENTAS.filter(function (x) { return x.nome === nome; })[0];
    if (!f) return Promise.resolve({ erro: "ferramenta desconhecida: " + nome });
    var caminho = f.caminho;
    if (f.id) {
      /* Higienizado, e não escapado: só se aceitam os caracteres que um id deste site pode ter.
       * Um id com uma barra ou um `..` sairia de `/api/v1/` e iria buscar outra coisa. */
      var id = String((args && args.id) || "").toLowerCase().replace(/[^a-z0-9._-]/g, "");
      if (!id) return Promise.resolve({ erro: "esta ferramenta precisa de um id" });
      caminho = caminho.replace("{id}", id);
    }
    return buscar(caminho).then(function (d) {
      /* Truncado, porque uma coleção inteira do grafo tem 300 kB e a janela não os quer. O corte
       * é dito no próprio resultado, para o modelo saber que está a ver um pedaço. */
      var t = JSON.stringify(d);
      return t.length > 24000
        ? { truncado: true, bytes_totais: t.length, inicio: t.slice(0, 24000) }
        : d;
    }).catch(function (err) { return { erro: err.message }; });
  }

  var SISTEMA =
    "És um leitor da publicação pt.newsroom.sgit.ai, uma redação nativamente portuguesa que mapeia " +
    "o ecossistema português de inteligência artificial como um grafo. Respondes em português " +
    "europeu.\n\n" +
    "REGRAS QUE NÃO SÃO NEGOCIÁVEIS, porque são as regras desta publicação:\n" +
    "1. Só afirmas o que as ferramentas te devolverem. Se não o leste numa ferramenta, dizes que " +
    "não sabes. Não completas com o que aprendeste em treino: uma afirmação sobre Portugal que não " +
    "venha destes ficheiros é exatamente o que esta publicação existe para não fazer.\n" +
    "2. Quando afirmas algo, dizes de que caminho da API veio. O leitor tem de poder ir ver.\n" +
    "3. Nenhum adjetivo sobre uma pessoa ou uma organização nomeada. Esta publicação relata o que " +
    "outros publicaram e liga para isso; não caracteriza ninguém, não classifica e não ordena.\n" +
    "4. Nenhum artigo está publicado. Se te perguntarem por uma história, diz o estado que a " +
    "ferramenta dá, e que publicar é a linha do editor de registo e de mais ninguém.\n" +
    "5. Uma entrega de investigação é uma lista de pistas, nunca factos, até o editor a aprovar " +
    "item a item. Se citares uma, dizes isso.\n" +
    "6. Não inventas um id. Listas primeiro, e usas um id que a listagem deu.";

  function perguntar(chave, modelo, historico, aoVivo) {
    var mensagens = [{ role: "system", content: SISTEMA }].concat(historico);
    var voltas = 0;

    function volta() {
      voltas += 1;
      if (voltas > 6) {
        return Promise.resolve("Parei ao fim de seis leituras sem chegar a uma resposta. " +
          "Pergunte de forma mais estreita, ou veja o caminho da API diretamente.");
      }
      return fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: "Bearer " + chave },
        body: JSON.stringify({
          model: modelo, messages: mensagens, tools: esquemaDeFerramentas(), tool_choice: "auto",
        }),
      }).then(function (r) {
        if (r.status === 401) throw new Error("o OpenRouter recusou a chave");
        if (!r.ok) throw new Error("o OpenRouter respondeu " + r.status);
        return r.json();
      }).then(function (d) {
        var m = ((d.choices || [])[0] || {}).message || {};
        mensagens.push(m);
        var chamadas = m.tool_calls || [];
        if (!chamadas.length) return m.content || "(sem resposta)";
        aoVivo("a ler: " + chamadas.map(function (c) { return c.function.name; }).join(", "));
        return Promise.all(chamadas.map(function (c) {
          var args = {};
          try { args = JSON.parse(c.function.arguments || "{}"); } catch (e) { /* nada */ }
          return correrFerramenta(c.function.name, args).then(function (res) {
            mensagens.push({ role: "tool", tool_call_id: c.id, name: c.function.name,
                             content: JSON.stringify(res) });
          });
        })).then(volta);
      });
    }
    return volta();
  }

  /* ------------------------------------------------------------------ o painel --- */
  function painel() {
    var caixa = document.createElement("div");
    caixa.className = "cartao";
    caixa.id = "conversa";
    caixa.style.marginTop = "18px";
    caixa.style.padding = "16px";
    caixa.innerHTML =
      '<div class="sect">Falar com este conteúdo</div>' +
      '<p class="sm" style="max-width:52em;padding-top:6px">Por omissão isto corre inteiramente ' +
      'no seu navegador: um comparador que encaminha para o caminho da API ou a secção que ' +
      'responde, e que <b>diz porque escolheu</b>. Não vai nada a nenhum servidor, funciona sem ' +
      'rede, e não inventa — encaminha.</p>' +
      '<div class="chips" style="padding-top:8px">' +
      '<input id="cv-p" type="text" placeholder="o que quer saber?" ' +
      'style="flex:1 1 18em;min-width:12em;padding:8px;border:1px solid var(--filete);' +
      'background:var(--papel);color:var(--tinta)">' +
      '<button class="chip ok" id="cv-ir" type="button">perguntar</button>' +
      '<button class="chip" id="cv-abrir" type="button">usar a minha chave</button>' +
      '</div>' +
      '<div id="cv-chave" hidden style="padding-top:10px">' +
      '<p class="sm" style="max-width:52em"><b>A sua chave, e o que isso quer dizer.</b> Com a ' +
      'sua chave do OpenRouter, o painel passa a chamar um modelo com ferramentas de leitura ' +
      'sobre a API deste site — as ferramentas são só GET, porque cada caminho da API é um ' +
      'ficheiro, e o pior que uma chamada pode fazer é ler uma coisa que já é pública. ' +
      'A chave fica no <code>localStorage</code> desta origem. <b>Não há anfitrião e por isso ' +
      'não há chão de permissões:</b> a chave vive na origem desta página e qualquer script que ' +
      'aqui corresse poderia lê-la. Não passa por pt.newsroom.sgit.ai — não há por onde passar. ' +
      'Se preferir não o fazer, o comparador acima responde sem chave nenhuma.</p>' +
      '<div class="chips" style="padding-top:8px">' +
      '<input id="cv-k" type="password" placeholder="sk-or-…" autocomplete="off" ' +
      'style="flex:1 1 16em;padding:8px;border:1px solid var(--filete);background:var(--papel);' +
      'color:var(--tinta)">' +
      '<input id="cv-m" type="text" autocomplete="off" ' +
      'style="flex:1 1 14em;padding:8px;border:1px solid var(--filete);background:var(--papel);' +
      'color:var(--tinta)">' +
      '<button class="chip ok" id="cv-guardar" type="button">guardar</button>' +
      '<button class="chip miss" id="cv-esquecer" type="button">esquecer</button>' +
      '</div></div>' +
      '<div id="cv-r" style="padding-top:12px"></div>';

    var folha = document.querySelector(".folha");
    if (folha) folha.appendChild(caixa);

    var el = function (i) { return document.getElementById(i); };
    el("cv-m").value = guardado(MODELO, MODELO_OMISSAO);

    function pintarEstado() {
      el("cv-abrir").textContent = guardado(CHAVE, "")
        ? "a usar a sua chave — mudar" : "usar a minha chave";
      el("cv-abrir").className = "chip " + (guardado(CHAVE, "") ? "ok" : "");
    }
    pintarEstado();

    el("cv-abrir").onclick = function () {
      el("cv-chave").hidden = !el("cv-chave").hidden;
    };
    el("cv-guardar").onclick = function () {
      guardar(CHAVE, el("cv-k").value.trim());
      guardar(MODELO, el("cv-m").value.trim() || MODELO_OMISSAO);
      el("cv-k").value = "";
      el("cv-r").innerHTML = '<p class="sm">Guardada neste navegador. Nada saiu desta página.</p>';
      pintarEstado();
    };
    el("cv-esquecer").onclick = function () {
      esquecer(CHAVE);
      el("cv-r").innerHTML = '<p class="sm">Esquecida. O comparador continua a responder.</p>';
      pintarEstado();
    };

    function nivelZero(pergunta) {
      return catalogo().then(function (cat) {
        var r = comparar(pergunta, cat);
        if (!r.length) {
          return '<p class="sm">Nada no índice deste site bate com essas palavras. O índice ' +
            'inteiro está em <a href="' + raiz() + 'api/v1/index.json">/api/v1/index.json</a> e ' +
            'em <a href="' + raiz() + 'llms.txt">llms.txt</a>.</p>';
        }
        return '<p class="sm">O comparador correu no seu navegador. ' + r.length +
          ' resultado(s), e ao lado de cada um está <b>porque</b> foi escolhido:</p>' +
          r.map(function (x) {
            return '<div class="cartao"><div class="chips" style="padding-bottom:4px">' +
              '<span class="chip">' + x.item.tipo + '</span>' +
              '<span class="chip ok">' + x.pontos + ' pontos</span></div>' +
              '<p class="sm"><b>' + x.item.nome + '</b> — <a href="' + raiz() +
              x.item.caminho.replace(/^\//, "") + '">' + x.item.caminho + '</a></p>' +
              '<p class="xs">' + x.item.resumo.slice(0, 300) + '</p>' +
              '<p class="xs mono">bateu: ' + x.bateram.join(", ") + '</p></div>';
          }).join("");
      });
    }

    function ir() {
      var pergunta = el("cv-p").value.trim();
      if (!pergunta) return;
      var chave = guardado(CHAVE, "");
      el("cv-r").innerHTML = '<p class="sm">a pensar…</p>';
      if (!chave) {
        nivelZero(pergunta).then(function (h) { el("cv-r").innerHTML = h; });
        return;
      }
      perguntar(chave, guardado(MODELO, MODELO_OMISSAO), [{ role: "user", content: pergunta }],
        function (estado) { el("cv-r").innerHTML = '<p class="sm">' + estado + '…</p>'; })
        .then(function (resposta) {
          el("cv-r").innerHTML = '<div class="correio">' +
            resposta.split(/\n\s*\n/).map(function (p) {
              /* Texto, e não HTML. O que um modelo devolve é texto de outra pessoa, e injectá-lo
               * como marcação seria dar a um modelo a caneta de escrever nesta página. */
              var d = document.createElement("p");
              d.className = "sm"; d.style.maxWidth = "52em"; d.textContent = p;
              return d.outerHTML;
            }).join("") + '</div>' +
            '<p class="xs mono">Respondido por ' + guardado(MODELO, MODELO_OMISSAO) +
            ', com a sua chave, a ler os caminhos de /api/v1/. Confira o que ele diz contra o ' +
            'caminho que ele nomeia — é para isso que a API existe.</p>';
        })
        .catch(function (err) {
          /* Cai para o nível 0 em vez de deixar de responder. */
          nivelZero(pergunta).then(function (h) {
            el("cv-r").innerHTML = '<p class="sm">O nível 1 falhou (' + err.message +
              '), e por isso corri o comparador:</p>' + h;
          });
        });
    }

    el("cv-ir").onclick = ir;
    el("cv-p").addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") ir();
    });
  }

  function arrancar() {
    /* Fora dos bastidores: a consola tem as suas próprias páginas e não precisa deste painel. */
    if (location.pathname.indexOf("/backoffice/") !== -1) return;
    if (!document.querySelector(".folha")) return;
    painel();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancar);
  } else {
    arrancar();
  }

  global.ptConversa = { FERRAMENTAS: FERRAMENTAS, comparar: comparar, buscar: buscar };
})(window);

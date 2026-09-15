/* pt.newsroom.sgit.ai — "talk to this content", on a site with no server. THE ENGINE.
 *
 * This file is the engine only: the tools, the level-0 comparator, the OpenRouter call, and the
 * browser storage. The interface is `<pt-chat>` in assets/components/. They were one file until
 * the panel became a right-hand column, and splitting them is the usual reason: two things that
 * change for different reasons should not share a file. A tool is added because the API grew; a
 * panel changes because a reader could not find something.
 *
 * THE PROBLEM, AND THE TWO LEVELS IT FORCES
 *
 * This site is static. There is no server, so there is nowhere to keep an API key. The design is
 * the one sgit.ai publishes in `articles/chat-on-a-static-site.md`, with the same two levels and
 * for the same reason:
 *
 *   LEVEL 0 — the default, and what is switched on. A deterministic comparator running in the
 *   browser against the index the build emitted. Instant, free, private, works offline, and — the
 *   part that makes it the default rather than the poor relation — **it says why it chose**. It
 *   shows the words that matched and where. It does not invent: it routes.
 *
 *   LEVEL 1 — optional, and only if the reader supplies their own key. Direct browser calls to
 *   OpenRouter, with tools over this site's API. The key lives in `localStorage`, and what that
 *   means is written in the panel without hedging: **with no host there is no permission floor,
 *   and the key lives on this page's origin**. It does not pass through pt.newsroom.sgit.ai —
 *   there is nothing for it to pass through. If it fails, it falls back to level 0 rather than
 *   stopping answering.
 *
 * THE TOOLS ARE THIS SITE'S API, AND THE API IS ONLY FILES
 *
 * There is no verb but GET, because every `/api/v1/` path is a file on disk. That makes the tools
 * an unusually safe thing to hand a model: the worst a call can do is read something already
 * public. There is no write, no authentication to steal, and no constructed address that could
 * reach anything else — the list of allowed paths is below and nothing outside it is fetched.
 *
 * It is also why every tool below is badged READ and none is badged anything else. A tool list
 * where every entry is harmless is not a design achievement here; it is a consequence of the API
 * being files. Said out loud so nobody reads the badges as a safety claim they are not.
 *
 * WHAT THIS DOES NOT DO
 *
 * It does not publish, does not change a file, does not talk to the vault and does not write mail.
 * For talking to the newsroom there is the bridge at `/backoffice/pontes.html`, which is a
 * different thing with different rules. This reads, and nothing else.
 */
(function (global) {
  "use strict";

  var CHAVE = "pt-newsroom:conversa:openrouter";
  var MODELO = "pt-newsroom:conversa:modelo";
  var MODELO_OMISSAO = "anthropic/claude-sonnet-4.5";
  var API = "/api/v1/";

  /* The tools. Each is a GET to a `/api/v1/` path, and the list is closed: a name not in here is
   * not fetched, and an `{id}` is sanitised before it enters the path. Every one is READ, for the
   * reason given in the banner — the API is files. */
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
    /* The page's depth decides the path to `/api/v1/`. An absolute root would work in production
     * and break in any preview served from a subfolder. */
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

  /* ------------------------------------------------------ level 0: the comparator ---
   * Deterministic, and its virtue is saying why it chose. The index is `/api/v1/index.json` plus
   * the sections: what the build emitted, not a hand-written list that ages. */
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
        props.id = { type: "string", description: "The identifier, exactly as the listing gives it." };
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
      /* Sanitised, not escaped: only the characters an id on this site can have are accepted. An
       * id with a slash or a `..` would leave `/api/v1/` and fetch something else. */
      var id = String((args && args.id) || "").toLowerCase().replace(/[^a-z0-9._-]/g, "");
      if (!id) return Promise.resolve({ erro: "esta ferramenta precisa de um id" });
      caminho = caminho.replace("{id}", id);
    }
    return buscar(caminho).then(function (d) {
      /* Truncated, because a whole graph collection is 300 kB and the window does not want it.
       * The cut is stated in the result itself, so the model knows it is seeing a piece. */
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

  /* `aoVivo` is called with an event rather than a string, because the panel shows each tool call
   * as it happens — which tool, with what argument, how many bytes came back. A spinner that says
   * "thinking" hides exactly the part a reader of THIS site should be able to watch: which files
   * the model actually opened. The events are:
   *
   *   {tipo:"chamada", nome, args}              a tool is about to run
   *   {tipo:"resultado", nome, bytes, erro}     it came back
   *   {tipo:"custo", chamadas, custo, tokens}   what the round cost, when OpenRouter reports it
   */
  function perguntar(chave, modelo, historico, aoVivo) {
    var mensagens = [{ role: "system", content: SISTEMA }].concat(historico);
    var voltas = 0, chamadas_feitas = 0, custo = 0, tokens = 0;

    function emitir(ev) { try { aoVivo(ev); } catch (e) { /* the panel is not the engine's problem */ } }

    function volta() {
      voltas += 1;
      if (voltas > 6) {
        return Promise.resolve({
          texto: "Parei ao fim de seis leituras sem chegar a uma resposta. Pergunte de forma mais " +
                 "estreita, ou veja o caminho da API diretamente.",
          chamadas: chamadas_feitas, custo: custo, tokens: tokens,
        });
      }
      return fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: "Bearer " + chave },
        body: JSON.stringify({
          model: modelo, messages: mensagens, tools: esquemaDeFerramentas(), tool_choice: "auto",
          /* Ask OpenRouter to bill the round back to us. Without it the panel would have to guess
           * a price from a table that ages, and a guessed number on a site about provenance is
           * worse than no number. */
          usage: { include: true },
        }),
      }).then(function (r) {
        if (r.status === 401) throw new Error("o OpenRouter recusou a chave");
        if (!r.ok) throw new Error("o OpenRouter respondeu " + r.status);
        return r.json();
      }).then(function (d) {
        var u = d.usage || {};
        if (typeof u.cost === "number") custo += u.cost;
        if (typeof u.total_tokens === "number") tokens += u.total_tokens;
        emitir({ tipo: "custo", chamadas: chamadas_feitas, custo: custo, tokens: tokens });

        var m = ((d.choices || [])[0] || {}).message || {};
        mensagens.push(m);
        var chamadas = m.tool_calls || [];
        if (!chamadas.length) {
          return { texto: m.content || "(sem resposta)", chamadas: chamadas_feitas,
                   custo: custo, tokens: tokens };
        }
        return Promise.all(chamadas.map(function (c) {
          var args = {};
          try { args = JSON.parse(c.function.arguments || "{}"); } catch (e) { /* nothing */ }
          chamadas_feitas += 1;
          emitir({ tipo: "chamada", nome: c.function.name, args: args });
          return correrFerramenta(c.function.name, args).then(function (res) {
            var corpo = JSON.stringify(res);
            emitir({ tipo: "resultado", nome: c.function.name, bytes: corpo.length,
                     erro: res && res.erro ? res.erro : null });
            mensagens.push({ role: "tool", tool_call_id: c.id, name: c.function.name,
                             content: corpo });
          });
        })).then(volta);
      });
    }
    return volta();
  }

  /* What the panel needs, and nothing more. The interface is a separate file and talks to this
   * one only through here; anything it reaches around this object for is a seam that will break. */
  global.ptConversa = {
    FERRAMENTAS: FERRAMENTAS,
    CHAVE: CHAVE, MODELO: MODELO, MODELO_OMISSAO: MODELO_OMISSAO,
    comparar: comparar, catalogo: catalogo, buscar: buscar, raiz: raiz,
    perguntar: perguntar, correrFerramenta: correrFerramenta,
    guardado: guardado, guardar: guardar, esquecer: esquecer,
  };
})(window);

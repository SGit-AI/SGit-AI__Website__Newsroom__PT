/* pt.newsroom.sgit.ai — a ponte para uma fila de acrescento de um cofre.
 *
 * O QUE ISTO É
 *
 * Este site é estático: não tem servidor, e por isso não tem como escrever no repositório onde a
 * redação vive. Uma fila de acrescento (append lane) resolve isso sem lhe dar um servidor. É um
 * canal só de escrita para dentro de um cofre, e a sua propriedade útil está na divisão em quatro
 * capacidades separadas:
 *
 *   append_token   quem o tem ACRESCENTA, e mais nada — não lista, não obtém, não lê
 *   enum_key       o dono lista, obtém e marca como tratado — não escreve
 *   write_key      o dono configura e purga
 *   chave privada  o dono decifra — nunca sai do computador dele
 *
 * O servidor guarda só o SHA-256 dos três primeiros, e a resposta a um acrescento é cega: `{ok:true}`
 * e mais nada. Quem envia não consegue saber o que está na fila, quanto lá está, nem se alguém leu.
 *
 * É por isso que um código de acrescento é a única forma de credencial que sobrevive a ser
 * publicada — e é por isso que a observabilidade deste site pode enviar eventos sem ter conta.
 *
 * Especificação, lida na fonte e não recordada:
 *   https://sgit.ai/docs/vault-messaging.md
 *   https://sgit.ai/api/append-lanes.md
 *   https://sgit.ai/docs/pki.md
 *
 * UM ACHADO QUE MUDA O DESENHO, E QUE VEIO DO COFRE DOS JOGOS
 *
 * O cofre dos jogos de permissões construía eventos e nunca os enviava. A razão não era o código:
 * uma aplicação de cofre corre numa moldura cujo CSP é `connect-src blob: data:`, e um `fetch`
 * para fora é bloqueado em silêncio. A saída seria `permissions.network: true`, que reabre toda a
 * saída de uma moldura que tem conteúdo decifrado — e que a própria documentação não recomenda.
 *
 * Este site NÃO é uma aplicação de cofre. É um site estático em GitHub Pages. O `fetch` direto para
 * o ponto de acrescento funciona, sem moldura, sem CSP de cofre e sem pedir permissão de rede a
 * ninguém. O que a telemetria dos jogos não conseguiu fazer, isto consegue.
 *
 * O QUE NUNCA ENTRA NUM FICHEIRO
 *
 * O `vault_id` e o `append_token` são dados ao navegador por quem os tem e ficam em
 * `localStorage`. Não estão neste ficheiro, não estão em `dados/pontes.json`, e o
 * `admin/build/validate.js` tem um detetor de cadeias com forma de chave que falha a construção se
 * alguma aparecer. A chave pública PODE ser publicada — uma chave pública publica-se — e é a única
 * das três que um dia ficará em ficheiro.
 */
(function (global) {
  "use strict";

  var API = "https://send.sgraph.ai";
  var b64 = {
    enc: function (buf) {
      var b = new Uint8Array(buf), s = "";
      for (var i = 0; i < b.length; i++) s += String.fromCharCode(b[i]);
      return btoa(s);
    },
    dec: function (s) {
      var raw = atob(s), b = new Uint8Array(raw.length);
      for (var i = 0; i < raw.length; i++) b[i] = raw.charCodeAt(i);
      return b;
    },
  };

  /* Uma chave pública chega como o pacote JSON que `sgit pki export` escreve — é isso que quem
   * tem o cofre tem em mãos, e pedir-lhe para extrair o PEM à mão seria pedir-lhe para se
   * enganar. Também se aceita o PEM sozinho, e um SPKI em base64 sem cabeçalho. */
  function lerChavePublica(texto) {
    var pem = String(texto || "").trim();
    if (pem.charAt(0) === "{") {
      var pacote = JSON.parse(pem);
      pem = pacote.encrypt || pacote.encriptar || "";
      if (!pem) throw new Error("o pacote não tem o campo «encrypt»");
    }
    var corpo = pem.replace(/-----[^-]+-----/g, "").replace(/\s+/g, "");
    if (!corpo) throw new Error("não há chave nenhuma neste texto");
    return crypto.subtle.importKey(
      "spki", b64.dec(corpo).buffer,
      /* RSA-OAEP 4096 com SHA-256. O 4096 está na documentação do sgit; o SHA-256 é o que o
       * cofre dos jogos usou e é o que esta redação usa, MAS a página do PKI não nomeia a função
       * de resumo do OAEP. É o único parâmetro deste ficheiro que não foi confirmado contra o
       * binário, e uma ida e volta de prova confirma-o numa tentativa. Está dito na página das
       * pontes em vez de ser assumido em silêncio. */
      { name: "RSA-OAEP", hash: "SHA-256" }, false, ["encrypt"]);
  }

  /* O envelope, exatamente como sgit.ai/docs/pki.md o descreve para a v0.15.0: base64 sobre um
   * JSON pequeno. `v` a versão (2), `w` a chave de conteúdo AES embrulhada com RSA-OAEP para o
   * destinatário, `i` o IV de 12 bytes, `c` o texto cifrado com a sua etiqueta GCM. Híbrido,
   * porque é o que o torna usável em cargas de qualquer tamanho: uma chave AES-256-GCM nova por
   * mensagem, e o RSA só serve para a entregar. */
  function cifrar(chavePublica, texto) {
    var iv = crypto.getRandomValues(new Uint8Array(12));
    var conteudo;
    return crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, true, ["encrypt"])
      .then(function (k) {
        conteudo = k;
        return crypto.subtle.encrypt({ name: "AES-GCM", iv: iv },
          k, new TextEncoder().encode(texto));
      })
      .then(function (c) {
        return crypto.subtle.exportKey("raw", conteudo).then(function (bruta) {
          return crypto.subtle.encrypt({ name: "RSA-OAEP" }, chavePublica, bruta)
            .then(function (w) {
              return btoa(JSON.stringify({
                v: 2, w: b64.enc(w), i: b64.enc(iv), c: b64.enc(c),
              }));
            });
        });
      });
  }

  function Ponte(opcoes) {
    opcoes = opcoes || {};
    this.id = opcoes.id;                       // qual ponte, para a chave de localStorage
    this.api = opcoes.api || API;
    this.chave = "pt-newsroom:ponte:" + this.id;
  }

  /* A configuração vive no navegador de quem a deu, e em mais lado nenhum. `localStorage` pode
   * atirar — janela privada, dados de sítio bloqueados — e por isso cada acesso vai dentro de um
   * try. Uma ponte sem configuração não é um erro: é uma ponte fechada, e a página diz isso. */
  Ponte.prototype.ler = function () {
    try {
      var cru = global.localStorage.getItem(this.chave);
      return cru ? JSON.parse(cru) : null;
    } catch (e) { return null; }
  };

  Ponte.prototype.guardar = function (cfg) {
    try {
      global.localStorage.setItem(this.chave, JSON.stringify(cfg));
      return true;
    } catch (e) { return false; }
  };

  Ponte.prototype.esquecer = function () {
    try { global.localStorage.removeItem(this.chave); return true; } catch (e) { return false; }
  };

  Ponte.prototype.aberta = function () {
    var c = this.ler();
    return !!(c && c.vault_id && c.append_token && c.chave_publica);
  };

  /* Envia. Devolve uma promessa que resolve com `{ok:true}` quando o servidor aceitou, e que
   * rejeita com uma razão legível quando não. O chamador decide se mostra o erro: a
   * observabilidade falha em silêncio, a caixa de mensagens do editor mostra-o, porque uma
   * mensagem que o editor pensa ter enviado e não enviou é pior do que um erro à vista. */
  Ponte.prototype.enviar = function (objeto) {
    var cfg = this.ler(), api = this.api;
    if (!cfg || !cfg.vault_id || !cfg.append_token || !cfg.chave_publica) {
      return Promise.reject(new Error("ponte fechada: falta o cofre, o código de acrescento ou a chave pública"));
    }
    if (!/^[0-9a-f]{16,128}$/.test(cfg.append_token)) {
      /* O padrão é `^[0-9a-f]{16,128}$` e um código com prefixo devolve 400. A impressão digital
       * que o CLI mostra tem `sha256:` à frente; o código de acrescento não. É a confusão que a
       * própria documentação marca como fonte viva de enganos, e por isso é apanhada aqui, antes
       * do pedido, com uma mensagem que diz qual é o engano. */
      return Promise.reject(new Error(
        "o código de acrescento tem de ser 16 a 128 dígitos hexadecimais, sem prefixo — " +
        "uma impressão digital «sha256:…» não é um código de acrescento"));
    }
    return lerChavePublica(cfg.chave_publica)
      .then(function (pk) { return cifrar(pk, JSON.stringify(objeto)); })
      .then(function (carga) {
        return fetch(api.replace(/\/$/, "") + "/api/vault/append/write/" + cfg.vault_id, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ append_token: cfg.append_token, payload: carga }),
          mode: "cors",
          credentials: "omit",
        });
      })
      .then(function (r) {
        if (r.status === 413) throw new Error("a mensagem passa dos 5 MB que a fila aceita");
        if (r.status === 507) throw new Error("a fila tem 1000 ficheiros por tratar: " +
          "ninguém do outro lado os marcou como tratados");
        if (r.status === 403) throw new Error("o cofre não reconhece este código de acrescento — " +
          "o seu SHA-256 tem de estar registado como âncora no cofre que recebe");
        if (!r.ok) throw new Error("o servidor respondeu " + r.status);
        /* A resposta é cega de propósito: `{ok:true}` e mais nada. Sem identificador de ficheiro,
         * sem contagem, sem metadados. Quem envia não fica a saber o estado da fila. */
        return { ok: true };
      });
  };

  global.PonteCofre = { Ponte: Ponte, lerChavePublica: lerChavePublica, cifrar: cifrar, API: API };
})(window);

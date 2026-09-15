/* pt.newsroom.sgit.ai — observability, over a vault append lane.
 *
 * Which pages are read and which paths people follow, without standing up an analytics server and
 * without knowing who anybody is. The pattern is the one sgit.ai publishes in
 * `docs/briefs/vault-telemetry-append-lanes.md`, first designed by the permission-games vault:
 * anonymous events, encrypted in the browser to the public key of a separate observability vault,
 * posted through an append code that can only write.
 *
 * THE FOUR RULES THIS FILE FOLLOWS, NONE OF WHICH IS AN OPTION
 *
 * 1. **Not configured means it does nothing at all.** It does not send, it does not show a notice
 *    and it does not add a switch. A notice saying «we send events» on a site that sends nothing
 *    is worse than no notice: it is a false statement about the site itself.
 * 2. **Configured means it says so in the open, with a switch.** Opening a page does not normally
 *    phone home. This one would, so it has to say so in plain Portuguese, on every page, with a
 *    button to turn it off — and off stays off between visits.
 * 3. **It fails silently.** If a send fails, the reader must not notice. Nothing here blocks a
 *    page from being read, and no telemetry error reaches somebody reading the paper.
 * 4. **Anonymous is the design, not a setting.** The session identifier is 16 hex digits made in
 *    memory when the page opens and lost when it closes. No name, no email address, no user
 *    agent, no screen size, no referrer, and the address travels without its query string. The
 *    lane's server sees the IP — that is not client-side and cannot be hidden from here, so it is
 *    stated on the notice page instead of being left out.
 *
 * AND A FIFTH, WHICH IS ABOUT WHOEVER RECEIVES IT
 *
 * On this bridge the append code is PUBLIC, because it has to be: it is in the page anybody can
 * read. That is safe with respect to what it grants — it only writes; it cannot list, get or read
 * — and it is exactly why the numbers that come out of it are directional and not evidence.
 * Anybody holding the code can forge events and can flood the lane, which stops at 1000 unhandled
 * files. A page presenting these numbers as a measurement would be lying about what they are.
 */
(function (global) {
  "use strict";

  var PONTE = "observabilidade";
  var PAUSA = "pt-newsroom:observador:pausa";
  var INTERVALO = 4000;   // at most one send every 4 seconds
  var MAX_ENVIOS = 40;    // at most 40 sends per session
  var MAX_EVENTOS = 80;   // the in-memory queue does not grow without a ceiling

  function hex(n) {
    var b = new Uint8Array(n / 2), s = "";
    crypto.getRandomValues(b);
    for (var i = 0; i < b.length; i++) s += ("0" + b[i].toString(16)).slice(-2);
    return s;
  }

  function guardado(chave, omissao) {
    try {
      var v = global.localStorage.getItem(chave);
      return v === null ? omissao : v;
    } catch (e) { return omissao; }
  }

  function Observador() {
    this.ponte = new global.PonteCofre.Ponte({ id: PONTE });
    /* In memory, and only in memory. A session that survived closing the tab would be a
     * persistent identifier, which is a different thing and would need a different notice. */
    this.sessao = hex(16);
    this.fila = [];
    this.envios = 0;
    this.ultimo = 0;
    this.temporizador = null;
  }

  Observador.prototype.pausada = function () {
    return guardado(PAUSA, "0") === "1";
  };

  Observador.prototype.pausar = function (sim) {
    try { global.localStorage.setItem(PAUSA, sim ? "1" : "0"); } catch (e) { /* nothing */ }
  };

  /* The path, with no query string and no fragment. `?` and `#` often carry something somebody
   * pasted without thinking, and the path is the part worth knowing. */
  Observador.prototype.pagina = function () {
    return location.pathname;
  };

  Observador.prototype.evento = function (tipo, extra) {
    if (!this.ponte.aberta() || this.pausada()) return;
    if (this.fila.length >= MAX_EVENTOS) return;
    var ev = { quando: new Date().toISOString(), tipo: String(tipo), pagina: this.pagina() };
    if (extra && typeof extra === "object") {
      /* Only short, simple fields are copied. A whole object from elsewhere in the code could
       * be carrying anything inside it, and "anything" is how an identifier gets in without
       * anybody deciding that it should. */
      Object.keys(extra).slice(0, 6).forEach(function (k) {
        var v = extra[k];
        if (typeof v === "string") ev[k] = v.slice(0, 80);
        else if (typeof v === "number" || typeof v === "boolean") ev[k] = v;
      });
    }
    this.fila.push(ev);
    this.agendar(false);
  };

  Observador.prototype.agendar = function (final) {
    var self = this;
    if (final) return this.enviar(true);
    if (this.temporizador) return;
    var espera = Math.max(0, INTERVALO - (Date.now() - this.ultimo));
    this.temporizador = setTimeout(function () {
      self.temporizador = null;
      self.enviar(false);
    }, espera);
  };

  Observador.prototype.enviar = function (final) {
    if (!this.fila.length || this.envios >= MAX_ENVIOS) return;
    if (!this.ponte.aberta() || this.pausada()) { this.fila = []; return; }
    var lote = this.fila.splice(0, this.fila.length);
    this.envios += 1;
    this.ultimo = Date.now();
    this.ponte.enviar({
      tipo: "observacao",
      sessao: this.sessao,
      versao: (document.querySelector(".ver") || {}).textContent || null,
      /* Coarse on purpose: wide or narrow, not the measurement, which identifies. */
      formato: global.innerWidth >= 900 ? "largo" : "estreito",
      lingua: (navigator.language || "").slice(0, 2),
      final: !!final,
      eventos: lote,
    }).catch(function () {
      /* Silently. Rule 3, and the most important one in this file: somebody reading the paper
       * must not end up learning that telemetry failed, because it is not their problem. */
    });
  };

  /* The notice and the switch. They exist only when the bridge is open — see rule 1. */
  Observador.prototype.avisar = function () {
    var self = this;
    var caixa = document.createElement("div");
    caixa.className = "aviso-bloco";
    caixa.style.marginTop = "18px";
    var p = document.createElement("p");
    p.className = "sm";
    p.innerHTML = "<b>Esta página envia eventos anónimos de leitura.</b> Vão para um cofre " +
      "cifrado desta redação: que páginas foram abertas, por que ordem, e quanto tempo " +
      "ficaram abertas. Não vai nome, nem correio eletrónico, nem nada que identifique " +
      "quem está a ler — o identificador de sessão são dezasseis dígitos criados na memória " +
      "do navegador quando a página abre e perdidos quando ela fecha. " +
      "<a href=\"/aviso/\">O aviso explica-o por inteiro.</a> ";
    var botao = document.createElement("button");
    botao.className = "chip";
    botao.type = "button";
    function pintar() {
      botao.textContent = self.pausada() ? "envio desligado — voltar a ligar" : "desligar o envio";
      botao.className = "chip " + (self.pausada() ? "miss" : "");
    }
    botao.onclick = function () {
      self.pausar(!self.pausada());
      pintar();
      if (self.pausada()) self.fila = [];
    };
    pintar();
    p.appendChild(botao);
    caixa.appendChild(p);
    var folha = document.querySelector(".folha");
    if (folha) folha.appendChild(caixa);
  };

  function arrancar() {
    if (!global.PonteCofre) return;
    var o = new Observador();
    global.ptObservador = o;
    /* Rule 1, here: a closed bridge leaves no trace at all on the page. */
    if (!o.ponte.aberta()) return;
    o.avisar();
    o.evento("abriu");
    var entrou = Date.now();
    /* `visibilitychange` and not `unload`: it is what fires reliably on a phone, and fetch's
     * `keepalive` is what gives the last send a chance to leave. */
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "hidden") {
        o.evento("saiu", { segundos: Math.round((Date.now() - entrou) / 1000) });
        o.agendar(true);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancar);
  } else {
    arrancar();
  }
})(window);

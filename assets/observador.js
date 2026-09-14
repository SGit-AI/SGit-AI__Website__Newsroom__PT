/* pt.newsroom.sgit.ai — a observabilidade, por uma fila de acrescento de cofre.
 *
 * Que páginas são lidas e que caminhos as pessoas seguem, sem montar um servidor de estatísticas e
 * sem saber quem é ninguém. O padrão é o que sgit.ai publica em
 * `docs/briefs/vault-telemetry-append-lanes.md` e que o cofre dos jogos de permissões desenhou
 * primeiro: eventos anónimos, cifrados no navegador para a chave pública de um cofre de
 * observabilidade separado, enviados por um código de acrescento que só escreve.
 *
 * AS QUATRO REGRAS QUE ESTE FICHEIRO SEGUE, E QUE NÃO SÃO OPÇÕES
 *
 * 1. **Se não está configurado, não faz absolutamente nada.** Nem envia, nem mostra aviso, nem
 *    põe interruptor. Um aviso a dizer «enviamos eventos» num site que não envia nada é pior do
 *    que nenhum aviso: é uma afirmação falsa sobre o próprio site.
 * 2. **Se está configurado, diz-o à vista, e dá um interruptor.** Abrir uma página normalmente não
 *    telefona a casa. Esta telefonaria, e por isso tem de o dizer em português simples, em cada
 *    página, com um botão para desligar — e o desligado fica desligado entre visitas.
 * 3. **Falha em silêncio.** Se o envio falhar, o leitor não pode notar. Nada aqui bloqueia a
 *    leitura de uma página, e nenhum erro de telemetria aparece a quem está a ler o jornal.
 * 4. **Anónimo é o desenho, não uma opção.** O identificador de sessão são 16 dígitos hexadecimais
 *    criados na memória quando a página abre e perdidos quando ela fecha. Não há nome, não há
 *    correio eletrónico, não há agente do utilizador, não há dimensões de ecrã, não há
 *    referenciador, e o endereço vai sem parâmetros. O servidor da fila vê o IP — isso não é do
 *    lado do cliente e não se pode esconder daqui, e está dito na página do aviso em vez de
 *    ser omitido.
 *
 * E UMA QUINTA, QUE É SOBRE QUEM RECEBE
 *
 * Nesta ponte o código de acrescento é PÚBLICO, porque tem de ser: está na página que qualquer
 * pessoa lê. Isso é seguro quanto ao que ele dá — só escreve, não lista, não obtém, não lê — e é
 * exatamente por isso que os números que dali saem são direcionais e não prova. Quem tem o código
 * pode forjar eventos e pode inundar a fila, que para nos 1000 ficheiros por tratar. Uma página
 * que apresentasse estes números como medição estaria a mentir sobre o que eles são.
 */
(function (global) {
  "use strict";

  var PONTE = "observabilidade";
  var PAUSA = "pt-newsroom:observador:pausa";
  var INTERVALO = 4000;   // no máximo um envio a cada 4 segundos
  var MAX_ENVIOS = 40;    // no máximo 40 envios por sessão
  var MAX_EVENTOS = 80;   // a fila em memória não cresce sem limite

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
    /* Na memória, e só na memória. Uma sessão que sobrevivesse a fechar o separador seria um
     * identificador persistente, que é outra coisa e precisaria de outro aviso. */
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
    try { global.localStorage.setItem(PAUSA, sim ? "1" : "0"); } catch (e) { /* nada */ }
  };

  /* O caminho, sem parâmetros e sem fragmento. `?` e `#` levam muitas vezes coisas que alguém
   * colou sem pensar, e o caminho é o que interessa saber. */
  Observador.prototype.pagina = function () {
    return location.pathname;
  };

  Observador.prototype.evento = function (tipo, extra) {
    if (!this.ponte.aberta() || this.pausada()) return;
    if (this.fila.length >= MAX_EVENTOS) return;
    var ev = { quando: new Date().toISOString(), tipo: String(tipo), pagina: this.pagina() };
    if (extra && typeof extra === "object") {
      /* Só se copiam campos simples e curtos. Um objeto inteiro de outra parte do código poderia
       * trazer qualquer coisa lá dentro, e «qualquer coisa» é como um identificador entra sem
       * ninguém decidir que entrava. */
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
      /* Grosseiro de propósito: largo ou estreito, e não a dimensão, que é identificadora. */
      formato: global.innerWidth >= 900 ? "largo" : "estreito",
      lingua: (navigator.language || "").slice(0, 2),
      final: !!final,
      eventos: lote,
    }).catch(function () {
      /* Em silêncio. A regra 3, e é a mais importante deste ficheiro: quem está a ler o jornal
       * não pode ficar a saber que a telemetria falhou, porque não é problema dele. */
    });
  };

  /* O aviso e o interruptor. Só existem se a ponte estiver aberta — ver a regra 1. */
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
    /* A regra 1, aqui: uma ponte fechada não deixa rasto nenhum na página. */
    if (!o.ponte.aberta()) return;
    o.avisar();
    o.evento("abriu");
    var entrou = Date.now();
    /* `visibilitychange` e não `unload`: é o que dispara de forma fiável em telemóvel, e o
     * `keepalive` do fetch é o que dá ao último envio a chance de sair. */
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

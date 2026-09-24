/* pt.newsroom.sgit.ai — the one sentence on this site that depends on when you are reading it.
 *
 * Everything else here is rendered once, from evidence, and is true whenever it is read. «How
 * long until the event» is not: it is a claim about the reader's present, and a file on a disk
 * cannot know that. For ten days every page said «Faltam 3 dias para o Startup Summit» because
 * the countdown had been computed from the date of the last frozen source — so the site promised
 * an event in three days, six days after it had finished, 231 times.
 *
 * So the server states the fact with no tense in it («Startup Summit Lisbon 2026 · 17-18 de
 * setembro de 2026») and this file adds the tense, from the reader's own clock. With no script
 * the reader gets a true sentence instead of a false one, which is the right way round.
 */
(function () {
  "use strict";

  var MS = 86400000;

  function frase(dias) {
    if (dias > 1) return "faltam " + dias + " dias";
    if (dias === 1) return "falta 1 dia";
    if (dias === 0) return "é hoje";
    if (dias === -1) return "foi ontem";
    return "foi há " + Math.abs(dias) + " dias";
  }

  function pintar() {
    var caixas = document.querySelectorAll(".quando-evento[data-evento]");
    for (var i = 0; i < caixas.length; i++) {
      var iso = caixas[i].getAttribute("data-evento");
      var quando = new Date(iso + "T00:00:00");
      if (isNaN(quando)) continue;
      /* Both sides floored to a local day: comparing timestamps would make «today» flip at
         whatever time of day the reader happens to open the page. */
      var hoje = new Date();
      hoje = Date.UTC(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
      var alvo = Date.UTC(quando.getFullYear(), quando.getMonth(), quando.getDate());
      var dias = Math.round((alvo - hoje) / MS);

      var span = caixas[i].querySelector(".relativo");
      if (!span) continue;
      /* The dates stay, and the tense is added beside them. Replacing «17-18 de setembro» with
         «foi há 6 dias» would trade a fact the site can prove for one it merely computed. */
      if (!span.dataset.original) span.dataset.original = span.textContent;
      span.textContent = span.dataset.original + " — " + frase(dias);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", pintar);
  } else {
    pintar();
  }
})();

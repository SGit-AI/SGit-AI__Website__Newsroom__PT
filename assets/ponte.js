/* pt.newsroom.sgit.ai — the bridge to a vault's append lane.
 *
 * WHAT THIS IS
 *
 * This site is static: it has no server, so it has no way to write into the repository the
 * newsroom lives in. An append lane solves that without giving it one. It is a write-only channel
 * into a vault, and its useful property is the split into four separate capabilities:
 *
 *   append_token   whoever holds it APPENDS, and nothing else — cannot list, get or read
 *   enum_key       the owner lists, gets and marks handled — cannot write
 *   write_key      the owner configures and purges
 *   private key    the owner decrypts — it never leaves their machine
 *
 * The server stores only the SHA-256 of the first three, and the answer to an append is blind:
 * `{ok:true}` and nothing more. A sender cannot learn what is in the lane, how much is there, or
 * whether anybody read it.
 *
 * That is why an append code is the one form of credential that survives being published — and it
 * is why this site's observability can send events without holding an account.
 *
 * The specification, read at the source rather than recalled:
 *   https://sgit.ai/docs/vault-messaging.md
 *   https://sgit.ai/api/append-lanes.md
 *   https://sgit.ai/docs/pki.md
 *
 * A FINDING THAT CHANGES THE DESIGN, AND THAT CAME FROM THE GAMES VAULT
 *
 * The permission-games vault built events and never sent them. The reason was not the code: a
 * vault application runs in a frame whose CSP is `connect-src blob: data:`, and a `fetch` to the
 * outside is blocked silently. The way out would be `permissions.network: true`, which reopens
 * every outbound path from a frame holding decrypted content — and which the documentation itself
 * does not recommend.
 *
 * This site is NOT a vault application. It is a static site on GitHub Pages. A direct `fetch` to
 * the append endpoint works, with no frame, no vault CSP and no network permission to ask anybody
 * for. What the games' telemetry could not do, this can.
 *
 * WHAT NEVER ENTERS A FILE
 *
 * The `vault_id` and the `append_token` are handed to the browser by whoever holds them and stay
 * in `localStorage`. They are not in this file, they are not in `dados/pontes.json`, and
 * `admin/build/validate.js` carries a key-shaped-string detector that fails the build if one ever
 * appears. The public key MAY be published — a public key is for publishing — and it is the only
 * one of the three that will one day live in a file.
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

  /* A public key arrives as the JSON bundle `sgit pki export` writes — that is what the vault's
   * owner actually has in hand, and asking them to pull the PEM out by hand would be asking them
   * to make a mistake. A bare PEM is accepted too, and a headerless base64 SPKI. */
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
      /* RSA-OAEP 4096 with SHA-256. The 4096 is in the sgit documentation; SHA-256 is what the
       * games vault used and what this newsroom uses, BUT the PKI page does not name OAEP's
       * digest function. It is the one parameter in this file not confirmed against the binary,
       * and a single proving round trip would settle it. It is stated on the bridges page rather
       * than assumed in silence. */
      { name: "RSA-OAEP", hash: "SHA-256" }, false, ["encrypt"]);
  }

  /* The envelope, exactly as sgit.ai/docs/pki.md describes it for v0.15.0: base64 over a small
   * JSON object. `v` the version (2), `w` the AES content key wrapped with RSA-OAEP for the
   * recipient, `i` the 12-byte IV, `c` the ciphertext with its GCM tag. Hybrid, because that is
   * what makes it usable at any payload size: a fresh AES-256-GCM key per message, with RSA doing
   * nothing but delivering it. */
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
    this.id = opcoes.id;                       // which bridge — it names the localStorage key
    this.api = opcoes.api || API;
    this.chave = "pt-newsroom:ponte:" + this.id;
  }

  /* The configuration lives in the browser of whoever supplied it, and nowhere else.
   * `localStorage` can throw — a private window, blocked site data — so every access goes inside
   * a try. A bridge with no configuration is not an error: it is a closed bridge, and the page
   * says so. */
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

  /* Sends. Returns a promise resolving with `{ok:true}` when the server accepted, and rejecting
   * with a readable reason when it did not. The caller decides whether to show the error:
   * observability fails silently, the editor's message box shows it — because a message the
   * editor believes they sent and did not is worse than an error in plain view. */
  Ponte.prototype.enviar = function (objeto) {
    var cfg = this.ler(), api = this.api;
    if (!cfg || !cfg.vault_id || !cfg.append_token || !cfg.chave_publica) {
      return Promise.reject(new Error("ponte fechada: falta o cofre, o código de acrescento ou a chave pública"));
    }
    if (!/^[0-9a-f]{16,128}$/.test(cfg.append_token)) {
      /* The pattern is `^[0-9a-f]{16,128}$` and a prefixed code returns 400. The fingerprint the
       * CLI prints carries `sha256:` in front; the append code does not. It is the confusion the
       * documentation itself flags as a live source of mistakes, so it is caught here, before the
       * request, with a message that names the mistake. */
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
        /* The answer is blind on purpose: `{ok:true}` and nothing else. No file identifier, no
         * count, no metadata. A sender does not get to learn the state of the lane. */
        return { ok: true };
      });
  };

  global.PonteCofre = { Ponte: Ponte, lerChavePublica: lerChavePublica, cifrar: cifrar, API: API };
})(window);

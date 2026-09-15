#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the bridges page. How the editor reaches the back office from a browser.

    python3 build/newsroom_bridges.py

WHAT THIS PAGE IS FOR

This site is static. It has no server, so it has no way to write into the repository the newsroom
lives in. An append lane closes that gap without giving it a server: a write-only channel into a
vault, whose useful property is that the four capabilities are separated — whoever holds the
append token appends and does nothing else, and the write response is deliberately blind.

So the page does two things:

  1. It documents both bridges from `dados/pontes.json` — what each sends, what it never sends,
     what is missing, and how the receiving end must treat what arrives.
  2. It is the place the editor hands the browser the three values a lane needs. They go to
     `localStorage` and never into a file. That is not a convenience: `admin/build/validate.js`
     carries a key-shaped-string tripwire and would fail the build if one appeared, which is the
     gate working rather than a rule being remembered.

WHY THE COMPOSER LIVES HERE AND THE UNLOCK TRAVELS

The composer is on this page because it is the editor's console. The *unlock* is stored per
origin, so once the editor has given the values here, any page of the site can offer the same
composer — which is what "the website behaves differently when I am using it" means in practice.
That wider wiring is a later release; this page is the one that has to exist first, because
without it there is nowhere to put the credentials.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from newsroom import VERSAO, e, escrever, pagina  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def lista(xs, vazio="—"):
    if not xs:
        return f'<p class="sm">{vazio}</p>'
    return '<ul class="sm" style="padding-left:18px;margin:0">' + "".join(
        f"<li>{e(x)}</li>" for x in xs) + "</ul>"


def bloco_ponte(p):
    def marca(pode):
        return ('<span class="st st--4">publishable</span>' if pode
                else '<span class="st st--2">secret</span>')

    cred = "".join(
        f'<tr><td class="mono xs">{e(c["chave"])}</td><td class="sm">{e(c["o_que_e"])}</td>'
        f'<td>{marca(c["publicavel"])}</td>'
        f'<td class="sm">{e(c["porque"])}</td></tr>'
        for c in p.get("credenciais_em_localstorage", []))
    limites = (f'<div class="sect" style="padding-top:10px">Client-side limits</div>'
               f'{lista(p.get("limites_do_lado_do_cliente", []))}'
               if p.get("limites_do_lado_do_cliente") else "")
    interruptor = (f'<div class="sect" style="padding-top:10px">The switch</div>'
                   f'<p class="sm">{e(p["interruptor"])}</p>' if p.get("interruptor") else "")
    return f"""
<div class="cartao" style="padding:16px;margin-top:18px" id="{e(p["id"])}">
  <div class="queue__meta" style="margin:0 0 10px">
    <b style="font-size:15px">{e(p["nome"])}</b>
    <span class="st st--2">{e(p["estado"])}</span>
    <span class="path">{e(p["id"])}</span>
  </div>
  <p class="sm mono xs">{e(p["direcao"])}</p>
  <p class="std" style="max-width:52em;padding-top:6px">{e(p["porque_existe"])}</p>
  <div class="g2 sp12" style="padding-top:10px">
    <div class="col sp6">
      <div class="sect">Sends</div>{lista(p.get("o_que_vai_na_carga", []))}
      <div class="sect" style="padding-top:10px">Never sends</div>
      {lista(p.get("o_que_nunca_vai", []))}
      {limites}{interruptor}
    </div>
    <div class="col sp6">
      <div class="sect">Who sends, who receives</div>
      <p class="sm"><b>Sends:</b> {e(p["quem_envia"])}</p>
      <div class="sect" style="padding-top:10px">Endpoint</div>
      <p class="mono xs">{e(p["endpoint"])}</p>
      <div class="sect" style="padding-top:10px">What is missing</div>
      <p class="sm">{e(p["o_que_falta"])}</p>
    </div>
  </div>
  <div class="sect" style="padding-top:12px">The three values, and which may be published</div>
  <div class="rolar"><table><thead><tr><th style="width:120px">Key</th><th>What it is</th>
    <th style="width:100px">Publishable</th><th style="width:40%">Why</th></tr></thead>
    <tbody>{cred}</tbody></table></div>
  <p class="xs mono" style="padding-top:6px">localStorage: <code>{e(p["chave_de_localstorage"])}</code></p>
  <div class="aviso-bloco" style="margin-top:12px">
    <p class="sm"><b>How the receiving end must treat this.</b> {e(p["tratamento_do_que_chega"])}</p>
  </div>
</div>"""


def pagina_pontes(d, ag):
    env = d.get("envelope", {})
    campos = "".join(f'<tr><td class="mono xs">{e(c["campo"])}</td><td class="sm">{e(c["e"])}</td>'
                     f"</tr>" for c in env.get("campos", []))
    nao = "".join(f'<tr><td class="sm"><b>{e(x["o_que"])}</b></td><td class="sm">{e(x["porque"])}'
                  f"</td></tr>" for x in d.get("ainda_nao_construido", []))
    blocos = "".join(bloco_ponte(p) for p in d.get("pontes", []))
    bastidores = next((a for a in ag.get("agentes", []) if a["id"] == "bastidores.pt"), {})

    # The unlock and the composer. No secret is rendered into this HTML: the page reads and writes
    # localStorage in the reader's own browser, and the build never sees a value.
    app = f"""
<h2>Unlock · give this browser the
  three values</h2>
<p class="std" style="max-width:52em">Paste them here and they go to this browser's
<code>localStorage</code> for this origin, and nowhere else. They are not sent to
pt.newsroom.sgit.ai — there is no server to send them to — and they are not in any file in the
repository. Clearing them is one button. If you are reading this on a shared machine, do not.</p>
<p class="sm" style="max-width:52em;padding-bottom:10px">The public key is easiest as the whole
JSON bundle <code>sgit pki export &lt;fingerprint&gt;</code> writes: the page reads the
<code>encrypt</code> field out of it. A bare PEM works too.</p>

<div class="cartao" style="padding:16px">
  <div class="chips" style="padding-bottom:10px">
    <button class="btn" id="ponte-escolha-editor" type="button">editor → back office</button>
    <button class="btn" id="ponte-escolha-obs" type="button">observability</button>
    <span class="st st--3" id="ponte-estado">reading…</span>
    <span class="path" id="ponte-qual"></span>
  </div>
  <div class="col sp6">
    <label class="sm" for="ponte-vault">Vault id — the vault that receives</label>
    <input class="field mono" id="ponte-vault" type="text" autocomplete="off" spellcheck="false">
    <label class="sm" for="ponte-token" style="padding-top:8px">Append token — hex, 16–128 digits,
      no prefix</label>
    <input class="field mono" id="ponte-token" type="text" autocomplete="off" spellcheck="false">
    <label class="sm" for="ponte-chave" style="padding-top:8px">Public key — the
      <code>sgit pki export</code> bundle, or a PEM</label>
    <textarea class="field mono" id="ponte-chave" rows="4" autocomplete="off" spellcheck="false"></textarea>
    <div class="chips" style="padding-top:10px">
      <button class="btn btn--primary" id="ponte-guardar" type="button">keep in this browser</button>
      <button class="btn" id="ponte-prova" type="button">send a proof message</button>
      <button class="btn btn--danger" id="ponte-esquecer" type="button">forget</button>
    </div>
    <p class="sm" id="ponte-resposta" style="padding-top:8px"></p>
  </div>
</div>

<h2>Write to
  {e(bastidores.get("alias", "@Bastidores"))}</h2>
<p class="std" style="max-width:52em">This goes into the append lane, and
{e(bastidores.get("alias", "@Bastidores"))} files it as mail — into
<code>redacao/correio/expedicao/bastidores.pt/</code>, delivered, read, and answered like any
other message. It is treated as <b>a claim by whoever sent it</b>, never as an instruction that
runs without being read. Nothing here can publish a story: that is
{e(next((a["alias"] for a in ag.get("agentes", []) if a["id"] == "dinis.humano"), "@Dinis"))}'s
line and only his.</p>
<div class="cartao" style="padding:16px">
  <div class="col sp6">
    <div class="chips">
      <span class="sm">kind:</span>
      <select class="mono xs" id="msg-tipo" style="padding:6px;border:1px solid var(--filete);
              background:var(--papel);color:var(--tinta);max-width:100%;min-width:0">
        <option value="nota">nota — a remark</option>
        <option value="alteracao">alteracao — change this</option>
        <option value="instrucao">instrucao — do this next</option>
        <option value="remocao">remocao — a removal request</option>
      </select>
    </div>
    <label class="sm" for="msg-assunto" style="padding-top:8px">Subject</label>
    <input id="msg-assunto" type="text">
    <label class="sm" for="msg-corpo" style="padding-top:8px">Body</label>
    <textarea id="msg-corpo" rows="6"></textarea>
    <div class="chips" style="padding-top:10px">
      <button class="btn btn--primary" id="msg-enviar" type="button">send</button>
    </div>
    <p class="sm" id="msg-resposta" style="padding-top:8px"></p>
  </div>
</div>
"""

    corpo = f"""
<h2>The bridges · how a static site
  reaches the newsroom</h2>
<p class="std" style="max-width:52em">{e(d["nota"])}</p>
<div class="chips" style="padding:10px 0 4px">
  {"".join(f'<a class="chip" href="#{e(p["id"])}">{e(p["nome"])}</a>' for p in d.get("pontes", []))}
  <span class="chip miss">{sum(1 for p in d.get("pontes", []) if p["estado"] == "sem-credencial")}
    of {len(d.get("pontes", []))} without credentials</span>
</div>

<h2>Why an append lane, and not
  something simpler</h2>
<p class="std" style="max-width:52em">{e(d["porque_uma_fila_de_acrescento"])}</p>
<p class="sm" style="max-width:52em">Read at the source rather than recalled:
<a href="https://sgit.ai/docs/vault-messaging.md">vault-messaging</a>,
<a href="https://sgit.ai/api/append-lanes.md">the append-lanes API</a>,
<a href="https://sgit.ai/docs/pki.md">the PKI</a>, and
<a href="https://sgit.ai/docs/briefs/vault-telemetry-append-lanes.md">the telemetry brief</a>.</p>

<h2>A finding from the games vault,
  which changed this design</h2>
<div class="aviso-bloco" style="border-left-color:var(--acento)">
<p class="sm">{e(d["achado_do_cofre_dos_jogos"])}</p>
</div>

{blocos}

{app}

<h2>The envelope on the wire</h2>
<p class="std" style="max-width:52em">{e(env.get("porque_hibrido", ""))} The shape below is
{e(env.get("forma", ""))}, from <a href="https://sgit.ai/docs/pki.md">{e(env.get("de_onde_vem", ""))}</a>.</p>
<div class="rolar"><table><thead><tr><th style="width:80px">Field</th><th>Contents</th></tr>
</thead><tbody>{campos}</tbody></table></div>
<div class="aviso-bloco" style="margin-top:12px">
<p class="sm"><b>One parameter is not confirmed.</b> {e(env.get("o_que_nao_esta_confirmado", ""))}</p>
</div>

<h2>Not built</h2>
<div class="rolar"><table><thead><tr><th style="width:26%">What</th><th>Why not</th></tr></thead>
<tbody>{nao}</tbody></table></div>

<script src="../assets/ponte.js"></script>
<script>
(function () {{
  "use strict";
  var PONTES = {json.dumps({p["id"]: {"nome": p["nome"], "estado": p["estado"]}
                            for p in d.get("pontes", [])}, ensure_ascii=False)};
  var atual = "editor-para-bastidores";
  var el = function (id) {{ return document.getElementById(id); }};
  var ponte = function () {{ return new PonteCofre.Ponte({{ id: atual }}); }};

  function pintar() {{
    var p = ponte(), cfg = p.ler() || {{}};
    el("ponte-vault").value = cfg.vault_id || "";
    el("ponte-token").value = cfg.append_token || "";
    el("ponte-chave").value = cfg.chave_publica || "";
    el("ponte-estado").textContent = p.aberta() ? "open" : "no credentials";
    el("ponte-estado").className = "st st--" + (p.aberta() ? "3" : "2");
    el("ponte-qual").textContent = PONTES[atual].nome + " \u00b7 in this browser only";
  }}

  el("ponte-escolha-editor").onclick = function () {{
    atual = "editor-para-bastidores"; pintar();
  }};
  el("ponte-escolha-obs").onclick = function () {{ atual = "observabilidade"; pintar(); }};

  el("ponte-guardar").onclick = function () {{
    var ok = ponte().guardar({{
      vault_id: el("ponte-vault").value.trim(),
      append_token: el("ponte-token").value.trim(),
      chave_publica: el("ponte-chave").value.trim(),
    }});
    el("ponte-resposta").textContent = ok
      ? "Kept in this browser. Nothing left this page."
      : "This browser refused to store it — a private window, or site data blocked.";
    pintar();
  }};

  el("ponte-esquecer").onclick = function () {{
    ponte().esquecer();
    el("ponte-resposta").textContent = "Forgotten. The lane is closed again.";
    pintar();
  }};

  /* The proof round trip. It is the one call that settles the unconfirmed OAEP hash: if the
   * vault decrypts this, the envelope is right; if it does not, it is the hash and nothing else. */
  el("ponte-prova").onclick = function () {{
    el("ponte-resposta").textContent = "sending…";
    ponte().enviar({{
      tipo: "prova", quando: new Date().toISOString(), versao: "{VERSAO}",
      pagina: location.pathname,
      corpo: "Proof round trip from the bridges page. If this decrypts, the envelope is right.",
    }}).then(function () {{
      el("ponte-resposta").textContent = "Accepted. The response is blind by design — {{ok:true}} " +
        "and nothing else — so this says the server took it, not that anyone has read it.";
    }}).catch(function (err) {{
      el("ponte-resposta").textContent = "Refused: " + err.message;
    }});
  }};

  el("msg-enviar").onclick = function () {{
    var assunto = el("msg-assunto").value.trim(), corpo = el("msg-corpo").value.trim();
    if (!assunto || !corpo) {{
      el("msg-resposta").textContent = "A message needs a subject and a body.";
      return;
    }}
    var p = new PonteCofre.Ponte({{ id: "editor-para-bastidores" }});
    el("msg-resposta").textContent = "sending…";
    p.enviar({{
      tipo: el("msg-tipo").value, quando: new Date().toISOString(), versao: "{VERSAO}",
      pagina: location.pathname, assunto: assunto, corpo: corpo,
    }}).then(function () {{
      el("msg-resposta").textContent = "Sent. @Bastidores files it into its mailroom on the next " +
        "check-in, and it will show on the mail page.";
      el("msg-assunto").value = ""; el("msg-corpo").value = "";
    }}).catch(function (err) {{
      /* Loud on purpose. The observability lane fails silently because a reader must not notice;
       * a message the editor believes he sent and did not is worse than an error in plain sight. */
      el("msg-resposta").textContent = "Not sent: " + err.message;
    }});
  }};

  pintar();
}})();
</script>
"""
    return pagina("newsroom/bridges.html", "The bridges",
                  "How the editor reaches the back office from a browser: append lanes, what they "
                  "send, what they never send, and where the credentials live.", corpo)


def main():
    d = carregar("pontes.json")
    if not d:
        print("bridges: dados/pontes.json does not exist — nothing to do")
        return []
    feitas = [escrever("newsroom/bridges.html", pagina_pontes(d, carregar("agentes.json")))]
    sem = [p["id"] for p in d.get("pontes", []) if p["estado"] == "sem-credencial"]
    print(f"bridges: 1 page, {len(d.get('pontes', []))} bridges"
          + (f", {len(sem)} without credentials ({', '.join(sem)})" if sem else ""))
    return feitas


if __name__ == "__main__":
    main()

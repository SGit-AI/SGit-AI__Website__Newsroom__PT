#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the pages that came out of the second brief: the API, the provenance.

    python3 build/paginas_extra.py

They live apart from `build/build.py` for a simple reason: `build.py` builds the newspaper, and
these two are not newspaper. One is the data surface; the other is the publication talking about
itself. Mixing them in with the reading pages would make both files worse.
"""
import json
from pathlib import Path

import paginas as P
from paginas import DADOS, ROOT, e, escrever, pagina

COMPONENTES = "assets/components"


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


# ========================================================================= API ===
def api():
    idx = json.loads((ROOT / "api" / "v1" / "index.json").read_text(encoding="utf-8"))
    spec = json.loads((ROOT / "api" / "v1" / "openapi.json").read_text(encoding="utf-8"))
    n_ops = sum(len(m) for m in spec["paths"].values())
    n_ficheiros = sum(1 for _ in (ROOT / "api" / "v1").rglob("*.json"))

    linhas = "".join(
        f'<tr><td class="mono xs"><a href="v1{e(c["path"].replace("/api/v1", ""))}">'
        f'{e(c["name"])}</a></td>'
        f'<td class="sm">{e(c["summary"])}</td>'
        f'<td class="mono xs">{c["count"] if c["count"] is not None else "—"}</td>'
        f'<td class="mono xs">{"sim" if c["items"] else "—"}</td>'
        f'<td class="mono xs">{e(c["portuguese_source"])}</td></tr>'
        for c in idx["collections"])

    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">A API</div></div>
<h1 class="h-2" style="max-width:26em">Tudo o que este site mostra, também se lê como dados.</h1>
<p class="std" style="padding:14px 0 10px">Cada caminho abaixo é um ficheiro JSON
em disco. Não há servidor nenhum: um GET é uma leitura de ficheiro. É por isso que um documento
OpenAPI para isto é honesto de uma maneira que a maior parte não é — não há aqui um verbo que não
seja GET, não há corpo de pedido em lado nenhum, e não há nada que possa falhar de uma forma que o
documento não preveja.</p>
<div class="chips" style="padding-bottom:18px">
  <span class="chip ok">{n_ops} operações</span>
  <span class="chip">{len(idx["collections"])} colecções</span>
  <span class="chip">{n_ficheiros} ficheiros</span>
  <a class="chip" href="v1/openapi.json">openapi.json</a>
  <a class="chip" href="v1/index.json">index.json</a>
</div>

<div class="painel" style="margin-bottom:22px">
<div class="sect">Porque é que a API está em inglês e o site não</div>
<p class="sm" style="padding-top:8px">{e(idx["why_english"])}</p>
</div>

<div class="rule" style="padding:22px 0 12px"><div class="sect">A consola · escolha uma operação
e faça o pedido</div></div>
<pt-api-console site-root="../"></pt-api-console>
<p class="xs" style="padding-top:10px">A consola faz o pedido a partir do seu
navegador e mostra os bytes que voltaram. Uma consola que apenas DESCREVE uma API é um documento
com passos a mais — e a afirmação que está a ser feita aqui, a de que cada página deste site é
também dados, só vale se um leitor a puder conferir sem sair da página.</p>

<div class="rule" style="padding:22px 0 8px"><div class="sect">As colecções</div></div>
<div class="rolar"><table><thead><tr><th style="width:130px">Caminho</th><th>O que é</th>
  <th style="width:70px">Itens</th><th style="width:90px">Por item?</th>
  <th style="width:200px">Ficheiro de origem</th></tr></thead>
  <tbody>{linhas}</tbody></table></div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Reutilizar isto</div></div>
<p class="sm">{e(idx["licence"])}</p>
<p class="sm" style="padding-top:8px">As pessoas que aparecem aqui estão na sua
qualidade profissional, a partir de listas que as próprias fontes publicaram. Nenhum contacto,
nenhuma biografia, nenhuma caracterização de ninguém. <b>Reutilizar estes dados não transfere o
fundamento de licitude para os tratar</b>: quem os reutiliza passa a ser responsável pelo seu
próprio tratamento. Ver <a href="../aviso/">o aviso</a>.</p>
"""
    extra = (f'<script type="module" '
             f'src="../{COMPONENTES}/pt-api-console/v1/v1.0/v1.0.0/pt-api-console.js"></script>')
    return pagina("api/index.html", "A API",
                  "Uma API só de leitura sobre uma redação que mapeia o ecossistema português de "
                  "IA. Cada caminho é um ficheiro: não há servidor.",
                  corpo, aqui=None, com_declaracao=True, extra_body=extra)


# ================================================================= proveniência ===
def proveniencia():
    equipa, hist = carregar("equipa.json"), carregar("historias.json")
    ent, reg = carregar("entregas.json"), carregar("registo.json")

    # Who wrote what, counted from the article folders — not from a list.
    fornecedores = {}
    for h in hist.get("historias", []):
        f = ROOT / h["pasta"] / "proveniencia.json"
        if not f.exists():
            continue
        prov = json.loads(f.read_text(encoding="utf-8"))
        for passo in prov.get("cronologia", []):
            ag = passo.get("agente", "—")
            fornecedores.setdefault(ag, {"passos": 0, "artigos": set()})
            fornecedores[ag]["passos"] += 1
            fornecedores[ag]["artigos"].add(h["slug"])
    for x in ent.get("entregas", []):
        ag = f'{x["ferramenta"]} ({x["modelo"]})'
        fornecedores.setdefault(ag, {"passos": 0, "artigos": set()})
        fornecedores[ag]["passos"] += x["contagens"]["afirmacoes"]

    linhas_f = "".join(
        f'<tr><td>{e(k)}</td><td class="mono xs">{v["passos"]}</td>'
        f'<td class="mono xs">{len(v["artigos"])}</td></tr>'
        for k, v in sorted(fornecedores.items(), key=lambda kv: -kv[1]["passos"]))

    ed = equipa.get("editor_de_registo", {})
    so_ele = "".join(f'<li class="sm">{e(x)}</li>' for x in ed.get("so_ele_pode", []))

    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">Proveniência</div></div>
<h1 class="h-lead" style="max-width:15em">Este site é escrito por agentes de IA, com curadoria de
uma pessoa.</h1>
<p class="std" style="padding:18px 0 0">E vale a pena dizê-lo uma vez, com todas as
letras, em vez de o repetir em rodapé em cada página até ninguém o ler.</p>

<div class="g2" style="padding:26px 0">
<div class="col sp10">
<h2 class="h-3">O que isso quer dizer</h2>
<p class="sm">A pesquisa, a escrita e a verificação são feitas por agentes. Vários agentes, de
<b>vários fornecedores</b> — o que este site publica não sai de um modelo só, e não há nenhuma
razão para fingir que sai. Uma parte do material vem de uma sessão do Claude; outra de uma entrega
do ChatGPT; outra virá da Perplexity ou de uma pesquisa banal num motor de busca. O que importa
não é qual: é que fique registado qual foi.</p>
<p class="sm" style="padding-top:8px">O trabalho de um agente neste site não é «escrever um
artigo». É <b>congelar uma fonte antes de a citar</b>, e depois escrever apenas a partir do que
ficou congelado. A diferença entre as duas coisas é a razão de este site existir.</p>
</div>
<div class="col sp10">
<h2 class="h-3">O que a curadoria humana é, e o que não é</h2>
<p class="sm">O editor de registo é <b>{e(ed.get("nome", ""))}</b>. Lê antes de publicar, decide
remoções, e é a pessoa nomeada que responde pelo que aqui está — é também o responsável pelo
tratamento no <a href="../aviso/">aviso de proteção de dados</a>.</p>
<p class="sm" style="padding-top:8px"><b>É curadoria leve, e dizer «leve» é mais honesto do que
deixar implícita uma revisão linha a linha.</b> Um editor que lesse cada palavra de cada página
deste site estaria a fazer outro trabalho. O que ele faz é olhar para o que está em condições de
ir para o ar e decidir se vai.</p>
<div class="sect" style="padding-top:12px">Só ele pode</div><ul>{so_ele}</ul>
</div>
</div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">Quem fez o quê, contado dos
ficheiros</div></div>
<p class="sm" style="padding-bottom:12px">Cada artigo deste site tem uma
<code>proveniencia.json</code> na sua pasta, com a cronologia de quem fez cada passo e quando.
Esta tabela é a soma desses ficheiros — não é uma lista escrita à mão, e muda quando eles
mudarem.</p>
<div class="rolar"><table><thead><tr><th>Agente</th><th style="width:100px">Passos</th>
  <th style="width:100px">Artigos</th></tr></thead><tbody>{linhas_f}</tbody></table></div>
<p class="xs" style="padding-top:10px"><b>Um limite desta tabela, hoje.</b> Quase
tudo o que este site tem foi feito numa sessão de arranque, por um modelo só. Numa operação
normal os departamentos são passagens separadas, com registos de execução separados, e esta
tabela teria linhas a sério. Dizer o contrário agora seria encenar uma diversidade que ainda não
existe.</p>

<div class="rule" style="padding:22px 0 8px"><div class="sect">O que nunca é de um agente</div></div>
<div class="g3">
<div class="col sp8"><h3 class="h-3">Publicar</h3><p class="sm">O estado «publicado» é a linha do
editor. Uma execução automática que a escrevesse falhava o portão 11 e a construção parava.</p></div>
<div class="col sp8"><h3 class="h-3">Aprovar uma pista</h3><p class="sm">Uma entrega de
investigação é uma lista de pistas. Passa a facto quando o excerto está nos bytes <b>e</b> o
editor a aprova — as duas coisas, não uma.</p></div>
<div class="col sp8"><h3 class="h-3">Remover alguém</h3><p class="sm">Uma remoção ao abrigo do
aviso é incondicional e é do editor. Uma execução só regista o pedido e para de tocar nessa
pessoa.</p></div>
</div>

<div class="rule" style="padding:22px 0 8px"><div class="sect">A base material</div></div>
<div class="chips">
  <a class="chip ok" href="../registo/">{reg.get("contagem", 0)} ficheiros congelados</a>
  <a class="chip" href="../artigos/">{hist.get("contagem", 0)} artigos</a>
  <a class="chip" href="../admin/deliveries/">{sum(x["contagens"]["afirmacoes"] for x in ent.get("entregas", []))} afirmações entregues</a>
  <a class="chip" href="../ficheiros/">o manifesto, com o hash de cada ficheiro</a>
  <a class="chip" href="../api/">a API</a>
</div>
<p class="sm" style="padding-top:14px">Nenhuma revisão jurídica foi feita e nada
neste site é aconselhamento jurídico.</p>
"""
    return pagina("proveniencia/index.html", "Proveniência",
                  "Este site é escrito por agentes de IA com curadoria de um editor humano "
                  "nomeado. Quem fez o quê, contado a partir dos ficheiros.",
                  corpo, aqui=None, com_declaracao=False)


def carteira():
    """THE WALLET, ON A PAGE — which is what the editor asked for and the right shape for this.

    Until v0.11.0 the balance and the spend ledger lived in a panel that opened over the page from
    a badge in the chrome. The editor asked for them on a page of their own, and the reason is not
    taste: **the ledger is the interesting part of the demonstration**, and a ledger worth reading
    is worth an address. A panel that covers the masthead cannot be linked to, cannot be read on a
    phone without covering what you were reading, and closes itself on the first click elsewhere.

    The badge in the chrome still exists and still debits the page — the debit IS the demonstration
    and has to happen wherever the reader is. What changed is that it is now a LINK here instead of
    a button that opens a drawer.

    The markup is the component's own, in `modo="pagina"`. There is no second copy of the ledger:
    two copies would diverge the day somebody changed the price in one of them.
    """
    corpo = """
<div class="rule" style="padding:26px 0 8px"><div class="sect">A carteira</div></div>
<h1 class="h-lead" style="max-width:24em">Cada página deste site custa um cêntimo a abrir, e o
registo de quanto já gastou está aqui.</h1>
<p class="std" style="padding:18px 0 6px">O site-mãe defende, em vários ensaios, que quem cria o
facto devia ser pago por ele. Esta é essa defesa tornada concreta numa publicação que existe de
facto: cada página tem um preço, abri-la debita a carteira, a carteira recarrega quando esvazia,
e o registo do que foi gasto é legível — está abaixo, e é o seu, não o de mais ninguém.</p>

<pt-wallet modo="pagina" site-root="../"></pt-wallet>

<div class="rule" style="padding:26px 0 8px"><div class="sect">Para onde iria o dinheiro</div></div>
<p class="std" style="padding-bottom:10px">Numa versão a sério, o cêntimo iria para quem produziu
a fonte congelada em que a página assenta — e é por isso que esta publicação registra sempre qual
é. Uma página que não soubesse nomear a sua fonte não saberia a quem pagar; o
<a href="../registo/">registo</a> é, visto deste ângulo, a lista dos credores.</p>
<p class="sm">O argumento inteiro vive em <a href="https://newsroom.sgit.ai">newsroom.sgit.ai</a>,
e não é repetido aqui: conteúdo existe uma vez.</p>
"""
    return pagina("carteira/index.html", "A carteira",
                  "Cada página deste site custa um cêntimo a abrir. O saldo, o gasto e o registo "
                  "das páginas lidas — tudo no seu próprio navegador, e nada cobrado a ninguém.",
                  corpo, aqui=None)


def main():
    feitas = [escrever("api/index.html", api()),
              escrever("proveniencia/index.html", proveniencia()),
              escrever("carteira/index.html", carteira())]
    print(f"páginas extra: {len(feitas)} (api, proveniência, carteira)")
    return feitas


if __name__ == "__main__":
    main()

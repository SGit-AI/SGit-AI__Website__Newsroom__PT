#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — uma página por entidade, e o índice que faz uma menção virar ligação.

    python3 build/entidades.py        # depois de graph.py, antes de build.py e artigos.py

PORQUE É QUE ISTO EXISTE. Até aqui o site escrevia «Comissão Europeia» em prosa e o nome não ia
dar a lado nenhum. Um grafo cujos nós não têm endereço é um ficheiro, não um site: o leitor vê o
nome, quer saber o que mais há por trás dele, e não tem por onde clicar. Esta passagem dá a cada
nó do grafo que é uma COISA DO MUNDO — uma pessoa, uma organização, uma instituição, um editor,
um tema, um lugar — uma página própria em `entidades/<tipo>/<id>/`, montada inteiramente a partir
das arestas que já existem.

E a página lê-se em voz alta, porque o §6 do resumo obrigou o grafo a isso: cada aresta traz uma
`leitura` em português com `{s}` e `{t}`, e a página de uma entidade é literalmente a lista das
frases em que ela entra. Foi por isto que valeu a pena recusar `relacionado_com`.

O QUE ESTA PASSAGEM NÃO FAZ

  · Não escreve uma linha sobre ninguém. Tudo o que aparece numa página de entidade ou é um campo
    verbatim da fonte congelada, ou é uma aresta do grafo lida em voz alta pela leitura publicada
    na ontologia. Não há resumo, não há adjetivo, não há «é conhecido por».
  · Não caracteriza uma pessoa nomeada (§4 do resumo). A página de uma Pessoa mostra o que a
    fonte publica — o nome, o papel LISTADO, a organização LISTADA — e as arestas. Nada mais.
  · Não inventa um nome. O rótulo é o do nó, que veio dos bytes.
  · Não liga um nome que não esteja nos bytes. Ver `LIGAVEL` abaixo: uma entidade só entra no
    índice de ligação se o seu nome for encontrado, tal e qual, numa cópia congelada. Uma entidade
    que falhe isso continua a ter página — existe no grafo — mas nunca é ligada automaticamente em
    prosa, e a sua página diz que o nome não foi encontrado nos bytes.
"""
import html as _html
import json
import re
import time
import unicodedata
from pathlib import Path

import paginas as P

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
CONGELADAS = ROOT / "fontes" / "congeladas"

# Os tipos que ganham página. Ficam de fora os que já têm endereço noutro lado (Fonte e Captura
# vivem em /registo/, Historia em /artigos/) e os que não são uma coisa que se possa visitar
# (Sessao é um item de um programa, e o programa está em /eventos/).
TIPOS_COM_PAGINA = ["Pessoa", "Organizacao", "Instituicao", "Editor", "Evento", "Local", "Palco",
                    "Tema", "Tecnologia", "Setor", "Produto", "Servico", "Ideia"]

# A fórmula de ligação, publicada — porque o §6 diz que uma classificação é uma fórmula publicada
# ou não acontece, e decidir que uma sequência de letras numa frase É uma entidade é classificar.
MIN_NOME = 6          # «IA» e «AI» são sequências, não menções: ligá-las encheria o site de ruído
MAX_POR_PAGINA = 1    # liga-se a primeira menção de cada entidade e mais nenhuma

# Os tipos que uma menção em prosa pode ligar. São os que NOMEIAM uma coisa própria. Ficam de fora
# os tipos derivados pelo léxico — Tema, Setor, Tecnologia, Ideia, Serviço, Produto — porque os
# seus rótulos são substantivos comuns: «Educação», «Hardware», «Fundraising». Ligar a palavra
# «hardware» numa frase à página de uma Tecnologia seria dizer que aquela palavra é uma referência
# àquele nó, e não é: é a palavra. Esses nós continuam a ter página e continuam a ser alcançáveis
# pelo índice e pelas arestas — só não se impõem à prosa.
TIPOS_EM_PROSA = {"Pessoa", "Organizacao", "Instituicao", "Editor", "Evento", "Local", "Palco"}

FORMULA = {
    "id": "ligacao_de_entidade",
    "o_que_faz": "Transforma uma menção em prosa numa ligação para a página da entidade.",
    "porque_publicada": ("Decidir que uma sequência de letras numa frase é uma entidade é "
                         "classificar, e o §6 do resumo diz que uma classificação é uma fórmula "
                         "publicada ou não acontece."),
    "nunca_diz": ("Que o texto é SOBRE a entidade. Diz que o texto contém aquele nome, tal e qual "
                  "como a fonte congelada o escreve."),
    "regras": [
        "a correspondência é do nome verbatim do nó, com as maiúsculas e os acentos que os bytes "
        "lhe deram; não há correspondência aproximada, nem sem acentos, nem por apelido",
        f"o nome tem de ter pelo menos {MIN_NOME} caracteres",
        "o nome tem de ter um dos dois fundamentos, e a página da entidade diz qual: `bytes` — "
        "aparece, tal e qual, nos bytes de pelo menos uma cópia congelada; ou `registo` — é o "
        "nome que o nosso próprio registo dá ao editor de pelo menos uma fonte congelada. O "
        "segundo é mais fraco e está marcado como tal: é um facto sobre o nosso registo e não "
        "sobre a página. Uma entidade sem nenhum dos dois tem página e nunca é ligada",
        "os limites são de palavra: um nome dentro de outra palavra não é uma menção",
        "só ligam em prosa os tipos que nomeiam uma coisa própria (" + ", ".join(sorted(TIPOS_EM_PROSA)) + "); "
        "os tipos derivados pelo léxico têm página e não se impõem ao texto, porque o seu rótulo é "
        "um substantivo comum e a palavra não é uma referência ao nó",
        "uma entidade nunca é ligada na sua própria página",
        f"liga-se a primeira menção de cada entidade em cada página, e no máximo {MAX_POR_PAGINA}",
        "nunca dentro de uma ligação, de um elemento de código, de uma marca ou de um atributo",
    ],
}


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def ident_api(x):
    """O mesmo identificador que `build/api.py` dá ao ficheiro de um item. Duplicado de propósito
    e não importado: a API é construída DEPOIS desta passagem, e uma dependência de import entre
    as duas tornaria a ordem de construção mais frágil do que esta linha de código repetida."""
    base = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "sem-id"


def slug_tipo(t):
    base = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


def caminho(no_id, tipo):
    """`entidades/<tipo>/<resto-do-id>/`. O id de um nó já é único e já é seguro num URL; o tipo
    vai à frente porque um leitor que corta o endereço a meio deve cair numa lista útil."""
    resto = no_id.split(":", 1)[1] if ":" in no_id else no_id
    return f"entidades/{slug_tipo(tipo)}/{resto}/"


def texto_congelado():
    """Cada cópia congelada, com as entidades HTML desfeitas, para se procurar um nome nela.

    Desfazem-se as entidades porque uma fonte escreve `Comiss&atilde;o` e um leitor lê «Comissão»,
    e o que se está a perguntar é se o nome está ali. O que NÃO se faz é tirar as marcas: se um
    nome estiver partido ao meio por um `<span>`, esta procura não o encontra — e prefere-se a
    falha em não encontrar à afirmação de que se encontrou."""
    out = {}
    for f in sorted(CONGELADAS.rglob("*.snapshot")):
        rel = f.relative_to(CONGELADAS).as_posix()[: -len(".snapshot")]
        out[rel] = _html.unescape(f.read_text(encoding="utf-8", errors="replace"))
    return out


def main():
    grafo = carregar("grafo.json")
    onto = carregar("ontologia.json")
    registo = carregar("registo.json")
    pessoas = {p["id"]: p for p in carregar("pessoas.json").get("pessoas", [])}
    hist = carregar("historias.json")
    hoje = registo.get("atualizado", time.strftime("%Y-%m-%d"))

    nos = {n["id"]: n for n in grafo["nos"]}
    tipos = {t["id"]: t for t in onto["tipos"]}
    leituras = {}
    for a in onto["arestas"]:
        leituras[(a["verbo"], a["dominio"], a["alcance"])] = a

    bytes_por_fonte = texto_congelado()

    # --- quais os nós que ganham página, e onde -------------------------------
    ents = []
    for n in grafo["nos"]:
        if n["tipo"] not in TIPOS_COM_PAGINA:
            continue
        nome = n["rotulo"]
        onde = [{"fonte": fid, "ocorrencias": txt.count(nome)}
                for fid, txt in bytes_por_fonte.items() if nome in txt]
        onde.sort(key=lambda x: -x["ocorrencias"])
        # DOIS FUNDAMENTOS, E A PÁGINA DIZ QUAL. O primeiro é o forte: o nome está nos bytes de
        # uma página congelada. O segundo existe por causa de um caso real — «Diário da República»
        # é o editor de duas fontes congeladas e não aparece em byte nenhum, porque a página
        # inicial daquele registo devolve 22 caracteres visíveis a um leitor automático, que é
        # precisamente uma das histórias deste jornal. Recusar-lhe a ligação deixaria o leitor sem
        # caminho para a única página que lhe explica isso. Mas os dois fundamentos não valem o
        # mesmo, e por isso não são confundidos: o campo diz qual é, e a página diz-o por extenso.
        fundamento = "bytes" if onde else ("registo" if n.get("publica") else None)
        ents.append({
            "no": n["id"],
            "tipo": n["tipo"],
            "nome": nome,
            "url": caminho(n["id"], n["tipo"]),
            "nos_bytes": onde[:12],
            "ficheiros_com_o_nome": len(onde),
            "fundamento": fundamento,
            "ligavel": bool(fundamento) and len(nome) >= MIN_NOME,
            "ligavel_em_prosa": (bool(fundamento) and len(nome) >= MIN_NOME
                                 and n["tipo"] in TIPOS_EM_PROSA),
        })

    por_no = {x["no"]: x for x in ents}

    # --- o grau de cada uma, que é o que faz a página valer a pena ------------
    saida, entrada = {}, {}
    for a in grafo["arestas"]:
        saida.setdefault(a["origem"], []).append(a)
        entrada.setdefault(a["destino"], []).append(a)
    for x in ents:
        x["grau"] = {"saida": len(saida.get(x["no"], [])), "entrada": len(entrada.get(x["no"], []))}

    ents.sort(key=lambda x: (x["tipo"], -(x["grau"]["saida"] + x["grau"]["entrada"]), x["nome"]))

    por_tipo = {}
    for x in ents:
        por_tipo[x["tipo"]] = por_tipo.get(x["tipo"], 0) + 1

    indice = {
        "id": "pt-entidades", "versao": "0.1.0", "atualizado": hoje,
        "nota": ("Uma entrada por nó do grafo que é uma coisa do mundo. Cada uma tem página, e as "
                 "que têm `ligavel: true` são as que uma menção em prosa passa a ligar. O nome é o "
                 "rótulo do nó, que veio dos bytes de uma cópia congelada; `nos_bytes` diz em que "
                 "ficheiros congelados esse nome aparece e quantas vezes."),
        "formula": FORMULA,
        "contagem": len(ents),
        "ligaveis": sum(1 for x in ents if x["ligavel"]),
        "por_fundamento": {"bytes": sum(1 for x in ents if x["fundamento"] == "bytes"),
                           "registo": sum(1 for x in ents if x["fundamento"] == "registo"),
                           "nenhum": sum(1 for x in ents if not x["fundamento"])},
        "ligaveis_em_prosa": sum(1 for x in ents if x["ligavel_em_prosa"]),
        "por_tipo": por_tipo,
        "entidades": ents,
    }
    (DADOS / "entidades.json").write_text(
        json.dumps(indice, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # --- as páginas ----------------------------------------------------------
    e = P.e
    escritas = 0

    def rotulo_ligado(nid, raiz):
        n = nos.get(nid)
        if n is None:
            return e(nid)
        alvo = por_no.get(nid)
        # `class="no"`: numa página de entidade, o valor da página é poder seguir estas frases, e
        # o estilo da casa só sublinha ao passar o rato — o que faz uma ligação parecer texto.
        if alvo:
            return f'<a class="no" href="{raiz}{alvo["url"]}">{e(n["rotulo"])}</a>'
        if n["tipo"] == "Fonte":
            return f'<a class="no" href="{raiz}registo/#{e(n.get("fonte", ""))}">{e(n["rotulo"])}</a>'
        if n["tipo"] == "Historia":
            h = next((h for h in hist.get("historias", []) if h["slug"] == nid.split(":", 1)[1]), None)
            if h:
                return f'<a class="no" href="{raiz}{h["url"]}">{e(n["rotulo"])}</a>'
        return e(n["rotulo"])

    def frase(a, eu, raiz):
        """Uma aresta lida em voz alta. É o §6 a pagar-se: a leitura já está na ontologia."""
        o, d = nos.get(a["origem"]), nos.get(a["destino"])
        if not o or not d:
            return None
        decl = leituras.get((a["verbo"], o["tipo"], d["tipo"]))
        if decl is None:
            return None
        sou_origem = a["origem"] == eu
        modelo = decl["leitura"] if sou_origem else decl["leitura_inversa"]
        s = ("<b>%s</b>" % e(o["rotulo"])) if sou_origem else rotulo_ligado(a["origem"], raiz)
        tt = rotulo_ligado(a["destino"], raiz) if sou_origem else ("<b>%s</b>" % e(d["rotulo"]))
        return modelo.replace("{s}", s).replace("{t}", tt)

    for x in ents:
        n = nos[x["no"]]
        rel = x["url"] + "index.html"
        raiz = "../" * rel.count("/")
        tipo = tipos.get(n["tipo"], {})
        pessoa = n["tipo"] == "Pessoa"
        p = pessoas.get(x["no"].split(":", 1)[1], {}) if pessoa else {}

        cab = [
            f'<div class="rule" style="padding:26px 0 8px"><div class="sect">'
            f'{e(tipo.get("rotulo", n["tipo"]))} · uma entidade do grafo</div></div>',
            f'<h1 class="h-lead" style="max-width:20em">{e(x["nome"])}</h1>',
            f'<p class="std" style="padding:10px 0 4px">{e(tipo.get("definicao", ""))}</p>',
        ]

        # Os campos verbatim. Para uma Pessoa são exatamente três, e nenhum deles é uma frase
        # nossa: o nome, o papel tal como o evento o lista, e a organização tal como o evento a
        # lista. A palavra «listado» está lá de propósito — o cartão não afirma um vínculo.
        campos = []
        if pessoa:
            if p.get("papel"):
                campos.append(("Papel listado", p["papel"]))
            if p.get("organizacao"):
                campos.append(("Organização listada", p["organizacao"]))
            if n.get("classe_papel_rotulo"):
                campos.append(("Classe pela fórmula", n["classe_papel_rotulo"]))
        if n.get("verbatim_no_registo") and len(n["verbatim_no_registo"]) > 1:
            campos.append(("Escrito no registo de %d maneiras" % len(n["verbatim_no_registo"]),
                           " · ".join(n["verbatim_no_registo"])))
        if n.get("publica"):
            campos.append(("Páginas congeladas que publica", str(n["publica"])))
        if n.get("definicao"):
            campos.append(("Nota do registo", n["definicao"]))
        if campos:
            linhas = "".join(
                f'<tr><th style="width:230px">{e(k)}</th><td class="sm">{e(v)}</td></tr>'
                for k, v in campos)
            cab.append(f'<div class="rolar"><table><tbody>{linhas}</tbody></table></div>')

        # As frases. Saída primeiro, porque é o que a entidade faz; entrada depois, porque é o que
        # lhe é feito. Ambas são a mesma aresta lida dos dois lados, e é isso que o grafo promete.
        blocos = []
        for rot, arr, limite in (("O que o grafo diz a partir daqui", saida.get(x["no"], []), 200),
                                 ("E o que diz a chegar aqui", entrada.get(x["no"], []), 200)):
            fs = [f for f in (frase(a, x["no"], raiz) for a in arr[:limite]) if f]
            if not fs:
                continue
            itens = "".join(f'<li class="sm">{f}</li>' for f in fs)
            extra = ("" if len(arr) <= limite else
                     f'<p class="xs" style="padding-top:8px">São {len(arr)}; mostram-se {limite}. '
                     f'Todas estão em <code>dados/grafo.json</code>.</p>')
            blocos.append(f'<div class="rule" style="padding:26px 0 8px"><div class="sect">'
                          f'{rot}</div></div><ul>{itens}</ul>{extra}')

        # Onde o nome está nos bytes. É a diferença entre uma página de entidade e uma ficha de
        # wiki: aqui diz-se em que ficheiro congelado o nome aparece e quantas vezes, e quando não
        # aparece em nenhum diz-se isso, que é a coisa mais útil que a página pode dizer.
        if x["nos_bytes"]:
            linhas = "".join(
                f'<tr><td class="mono xs"><a href="{raiz}registo/#{e(b["fonte"])}">'
                f'{e(b["fonte"])}</a></td><td class="mono xs">{b["ocorrencias"]}</td></tr>'
                for b in x["nos_bytes"])
            mais = ("" if x["ficheiros_com_o_nome"] <= len(x["nos_bytes"]) else
                    f'<p class="xs" style="padding-top:8px">Aparece em '
                    f'{x["ficheiros_com_o_nome"]} ficheiros congelados; listam-se os '
                    f'{len(x["nos_bytes"])} com mais ocorrências.</p>')
            bytes_bloco = (
                f'<div class="rule" style="padding:26px 0 8px"><div class="sect">'
                f'Onde este nome está nos bytes</div></div>'
                f'<p class="std" style="padding:8px 0 12px">O nome, tal e qual como '
                f'está escrito acima, foi procurado em cada cópia congelada. Isto é uma contagem '
                f'de ocorrências da sequência de caracteres — não é uma afirmação de que a página '
                f'seja sobre esta entidade.</p>'
                f'<div class="rolar"><table><thead><tr><th>Ficheiro congelado</th>'
                f'<th style="width:120px">Ocorrências</th></tr></thead>'
                f'<tbody>{linhas}</tbody></table></div>{mais}')
        else:
            bytes_bloco = (
                f'<div class="rule" style="padding:26px 0 8px"><div class="sect">'
                f'Onde este nome está nos bytes</div></div>'
                f'<p class="std" style="padding:8px 0 0">Em lado nenhum, tal e qual. '
                f'Este nó existe no grafo porque foi derivado de um campo de uma fonte, e não '
                f'porque a sequência de caracteres acima apareça numa página congelada — pode '
                f'estar escrita de outra maneira, ou partida por marcas, ou a página pode não '
                f'devolver texto nenhum a um leitor automático.</p>'
                + (f'<p class="std" style="padding:12px 0 0">O que sustenta este '
                   f'nome é então o <b>nosso registo</b>, e não os bytes de ninguém: é assim que '
                   f'<code>dados/registo.json</code> nomeia o editor de {n.get("publica")} '
                   f'ficheiro(s) congelado(s). É um fundamento mais fraco do que o outro e está '
                   f'marcado como tal em <code>dados/entidades.json</code> '
                   f'(<code>fundamento: "registo"</code>) — um facto sobre o que nós escrevemos '
                   f'quando obtivemos a página, não sobre o que a página diz.</p>'
                   if n.get("publica") else
                   f'<p class="std" style="padding:12px 0 0">Por isso esta entidade '
                   f'<b>não é ligada automaticamente em prosa</b>: a fórmula de ligação exige um '
                   f'dos dois fundamentos, e esta não tem nenhum.</p>'))

        vizinhanca = (
            f'<div class="rule" style="padding:26px 0 8px"><div class="sect">'
            f'A vizinhança, carregada do grafo</div></div>'
            f'<pt-entity-graph no="{e(x["no"])}" raiz="{raiz}"></pt-entity-graph>')

        # O mesmo `ident` que a API usa para nomear o ficheiro. Escrever aqui outra forma do id
        # dava uma ligação que o portão de ligações do validador apanha — e apanhou noutra versão.
        aid = ident_api(x["no"])
        api = (f'<p class="xs" style="padding-top:14px">Em JSON: '
               f'<a href="{raiz}api/v1/graph.json">api/v1/graph.json</a> · '
               f'<a href="{raiz}api/v1/entities/{e(aid)}.json">api/v1/entities/{e(aid)}.json</a></p>')

        corpo = "".join(cab) + "".join(blocos) + bytes_bloco + vizinhanca + api
        desc = (f'{x["nome"]} — {tipo.get("rotulo", n["tipo"])} no grafo do ecossistema português '
                f'de IA. {x["grau"]["saida"] + x["grau"]["entrada"]} arestas, lidas em voz alta.')
        comp = (f'<script type="module" src="{raiz}assets/components/pt-entity-graph/'
                f'v1/v1.0/v1.0.0/pt-entity-graph.js"></script>')
        # `excepto` é o próprio nó: uma página que se liga a si mesma é uma ligação que não leva
        # a lado nenhum, e num texto que repete o nome da entidade seria a primeira a aparecer.
        P.escrever(rel, P.pagina(rel, x["nome"], desc, corpo, aqui=tipo.get("seccao"),
                                 nomeia_pessoas=pessoa, fontes_n=x["ficheiros_com_o_nome"] or None,
                                 extra_head=comp, excepto=x["no"]))
        escritas += 1

    # --- o índice ------------------------------------------------------------
    grupos = []
    for t in TIPOS_COM_PAGINA:
        do_tipo = [x for x in ents if x["tipo"] == t]
        if not do_tipo:
            continue
        td = tipos.get(t, {})
        itens = "".join(
            f'<li class="sm"><a href="../{x["url"]}">{e(x["nome"])}</a> '
            f'<span class="xs">· {x["grau"]["saida"] + x["grau"]["entrada"]}</span></li>'
            for x in do_tipo)
        grupos.append(
            f'<div class="rule" style="padding:26px 0 8px"><div class="sect">'
            f'{e(td.get("rotulo", t))} · {len(do_tipo)}</div></div>'
            f'<p class="std" style="padding:8px 0 12px">{e(td.get("definicao", ""))}</p>'
            f'<ul class="colunas">{itens}</ul>')

    n_lig = indice["ligaveis"]
    fund = indice["por_fundamento"]
    corpo = (
        f'<div class="rule" style="padding:26px 0 8px"><div class="sect">Entidades</div></div>'
        f'<h1 class="h-lead" style="max-width:24em">Cada nó do grafo que é uma coisa do mundo tem '
        f'uma página, e a página é a lista das frases em que ele entra.</h1>'
        f'<p class="std" style="padding:14px 0 6px">São {len(ents)}, e '
        f'{n_lig} delas podem ser ligadas: {fund["bytes"]} porque o nome está nos bytes de uma '
        f'cópia congelada, {fund["registo"]} porque é assim que o nosso próprio registo nomeia o '
        f'editor de um ficheiro congelado — um fundamento mais fraco, marcado como tal, e dito '
        f'por extenso na página de cada uma. As restantes {fund["nenhum"]} têm página e nunca são '
        f'ligadas. A fórmula que decide isto está publicada em '
        f'<code>dados/entidades.json</code>, no campo <code>formula</code>: nome verbatim, pelo '
        f'menos {MIN_NOME} caracteres, limites de palavra, a primeira menção de cada página e '
        f'mais nenhuma, nunca dentro de uma ligação, e só os tipos que nomeiam uma coisa '
        f'própria.</p>'
        f'<p class="std" style="padding:0 0 6px">Uma página de entidade não tem uma '
        f'linha escrita sobre ela. Tem os campos verbatim da fonte, as arestas lidas em voz alta '
        f'pela leitura publicada na ontologia, e a contagem de onde o nome aparece nos bytes. '
        f'Nenhum adjetivo sobre ninguém — é o §4 do resumo, e é uma recusa, não um estilo.</p>'
        + "".join(grupos))
    P.escrever("entidades/index.html",
               P.pagina("entidades/index.html", "As entidades",
                        f"As {len(ents)} entidades do grafo do ecossistema português de IA, cada "
                        f"uma com página própria e as suas arestas lidas em português.",
                        corpo, nomeia_pessoas=True))
    escritas += 1

    print(f"entidades: {len(ents)} entidades ({n_lig} ligáveis), {escritas} páginas")


if __name__ == "__main__":
    main()

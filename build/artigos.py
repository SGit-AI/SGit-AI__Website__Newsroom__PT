#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — os artigos: ler as pastas datadas, derivar o índice, construir as páginas.

    python3 build/artigos.py

Um artigo é uma PASTA, não um ficheiro:

    artigos/<aaaa>/<mm>/<dd>/<slug>/
        artigo.json         estado, secção, título, entrada, em que fontes assenta
        artigo.md           a prosa, com cada afirmação marcada [[fonte:<captura>/<pagina>]]
        afirmacoes.json     o registo de verificação de cada afirmação
        proveniencia.json   que execução, que agente, que modelo, por que ordem
        index.html          gerado aqui

Porque uma pasta. Um artigo não é só o texto: é o texto mais os bytes em que assenta, mais quem
verificou cada afirmação contra esses bytes, mais o rasto de quem o produziu. Num ficheiro único,
três dessas quatro coisas acabam noutro sítio — e quando acabam noutro sítio, deixam de concordar.

Porque a data no caminho. Um endereço construível, que diz quando o artigo foi feito sem que
ninguém abra o índice. O §8 do resumo é explícito: um dos assistentes com que esta redação
trabalha não segue ligações dentro de uma página que obteve, por isso os endereços têm de ser
previsíveis a partir do que já se sabe.

**A data no caminho é a data do MATERIAL, não a da publicação.** `publicado_em` é um campo
separado, escrito pelo editor de registo, e é a única coisa que põe um artigo na primeira página.

O ÍNDICE É DERIVADO. `dados/historias.json` é construído a partir destas pastas e não se edita —
a mesma regra que governa as organizações, derivadas dos cartões de orador. Um índice escrito à
mão acaba por discordar das pastas, e nada parece avariado.
"""
import json
import re
from pathlib import Path

import paginas as P
from paginas import DADOS, ROOT, data_pt, e, escrever, md_para_html, pagina

ARTIGOS = ROOT / "artigos"

ESTADOS = [
    ("procurado",  "Procurado",   "A pasta existe para recolher material. Ainda não há prosa.", "#6b6e76"),
    ("rascunho",   "Rascunho",    "Há prosa, escrita a partir do que a pesquisa registou.",      "#a16207"),
    ("verificado", "Verificado",  "Cada afirmação foi relida na cópia congelada e marcada.",     "#0f766e"),
    ("publicado",  "Publicado",   "O editor de registo leu e pôs a linha.",                      "#17181c"),
    ("superseded", "Substituído", "Substituído a partir de uma data. Nunca apagado.",            "#b45309"),
]
ROT_ESTADO = {k: (r, cor) for k, r, _, cor in ESTADOS}


def ler_todos():
    """Cada pasta de artigo, com os seus quatro ficheiros, ordenada por data e slug."""
    saida = []
    for meta in sorted(ARTIGOS.rglob("artigo.json")):
        d = meta.parent
        a = json.loads(meta.read_text(encoding="utf-8"))
        rel = d.relative_to(ROOT).as_posix()
        a["pasta"] = rel
        a["url"] = rel + "/"
        for nome, chave in (("afirmacoes.json", "verificacao"), ("proveniencia.json", "proveniencia")):
            f = d / nome
            a[chave] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
        md = d / "artigo.md"
        a["prosa"] = md.read_text(encoding="utf-8") if md.exists() else None
        saida.append(a)
    return sorted(saida, key=lambda x: (x["data"], x["slug"]), reverse=True)


def marcas_de_fonte(prosa):
    """Os identificadores [[fonte:…]] que a prosa cita, pela ordem em que aparecem."""
    return list(dict.fromkeys(re.findall(r"\[\[fonte:([^\]]+)\]\]", prosa or "")))


# ------------------------------------------------------------------- páginas ---
def pagina_artigo(a, registo):
    por_id = {s["id"]: s for s in registo["fontes"]}
    rot, cor = ROT_ESTADO.get(a["estado"], (a["estado"], "#6b6e76"))
    publicado = a["estado"] == "publicado"

    cabeca = (
        f'<div class="rule" style="padding:26px 0 8px;display:flex;justify-content:space-between;'
        f'align-items:baseline;gap:16px;flex-wrap:wrap">'
        f'<div class="kick">{e(a.get("antetitulo") or a["seccao"])}</div>'
        f'<div class="mono xs">{e(data_pt(a["data"], False))} · '
        f'<span style="color:{cor}">{e(rot)}</span></div></div>'
        f'<h1 class="h-lead" style="max-width:19em">{e(a["titulo"])}</h1>'
        f'<p class="std" style="max-width:42em;padding:16px 0 0">{e(a["entrada"])}</p>')

    # o estado, dito na própria página e não só no índice
    if publicado:
        linha_estado = (
            f'<p class="xs" style="padding-top:10px">Publicado em '
            f'{e(data_pt(a["publicado_em"], False))} por {e(a["publicado_por"])}, o editor de '
            f'registo. Ler antes de publicar é a única coisa que uma execução automática deste '
            f'site não pode fazer.</p>')
    else:
        linha_estado = (
            f'<div class="aviso-bloco"><p class="sm"><b>Este artigo ainda não está publicado.</b> '
            f'Está em <b>{e(rot).lower()}</b>: {e(next(d for k, _, d, _ in ESTADOS if k == a["estado"]))} '
            f'O editor de registo ainda não pôs a linha, e por isso este artigo não aparece na '
            f'primeira página nem em nenhuma secção. Está aqui, com o seu endereço definitivo, '
            f'porque o trabalho é público enquanto se faz — que é o ponto deste site.</p></div>')

    # a prosa, ou a ausência dela dita como ausência
    if a.get("prosa"):
        corpo_prosa = f'<div class="prosa" style="max-width:42em;padding:22px 0">{md_para_html(a["prosa"], "../../../../../")}</div>'
    else:
        faltam = "".join(f'<li class="sm">{e(x)}</li>' for x in a.get("o_que_falta", []))
        tem = "".join(f'<li class="sm">{e(x)}</li>' for x in a.get("o_que_ja_se_tem", []))
        b_tem = (f'<div class="sect" style="padding-top:18px">O que já se tem</div>'
                 f'<ul>{tem}</ul>' if tem else "")
        b_falta = (f'<div class="sect" style="padding-top:10px">O que falta</div>'
                   f'<ul>{faltam}</ul>' if faltam else "")
        corpo_prosa = (
            f'<div style="max-width:44em;padding:22px 0">'
            f'<p class="std">Ainda não há prosa. Esta pasta existe para recolher o material, e '
            f'escrever antes de o ter seria o contrário de tudo o que este site diz que faz.</p>'
            f'{b_tem}{b_falta}</div>')

    # o que o artigo expressamente não afirma
    nao = "".join(f'<li class="sm">{e(x)}</li>' for x in a.get("o_que_nao_afirma", []))
    bloco_nao = (
        f'<div class="rule" style="padding:22px 0 8px"><div class="sect">O que este artigo não '
        f'afirma</div></div><ul style="max-width:46em">{nao}</ul>'
        f'<p class="xs" style="max-width:46em;padding-top:8px">Esta lista está aqui porque a '
        f'diferença entre o que uma fonte sustenta e o que um leitor pode concluir é onde uma '
        f'publicação como esta faz dano sem dizer nada falso.</p>' if nao else "")

    # as afirmações, com a fonte e o hash ao lado
    ver = a.get("verificacao") or {}
    linhas_af = []
    for af in ver.get("afirmacoes", []):
        src = por_id.get(af["fonte"])
        cls = {"confirmada": "ok", "disputada": "disputa", "nao_encontrada": "falta"}.get(af["estado"], "")
        refeita = ""
        if af.get("refeita"):
            refeita = " · ".join(f"{k}: {v}" for k, v in af["refeita"].items())
        nota = (f'<div class="xs" style="padding-top:4px">{e(af["nota"])}</div>'
                if af.get("nota") else "")
        hash_ = (f'<div>{e(src["sha256"][:16])}…</div>' if src
                 else '<div style="color:var(--falta)">fonte não registada</div>')
        linhas_af.append(
            f'<tr><td><span class="chip {cls}">{e(af["estado"])}</span></td>'
            f'<td class="sm">{e(af["texto"])}{nota}</td>'
            f'<td class="mono xs"><a href="../../../../../registo/#{e(af["fonte"])}">'
            f'{e(af["fonte"])}</a>{hash_}</td>'
            f'<td class="mono xs">{e(refeita)}</td></tr>')
    bloco_af = ""
    if linhas_af:
        bloco_af = (
            f'<div class="rule" style="padding:22px 0 8px"><div class="sect">As afirmações, e como '
            f'foram verificadas</div></div>'
            f'<p class="sm" style="max-width:46em;padding-bottom:12px">{e(ver.get("como", ""))}</p>'
            f'<div class="rolar"><table><thead><tr><th style="width:110px">Estado</th>'
            f'<th>Afirmação</th><th style="width:210px">Fonte congelada</th>'
            f'<th style="width:200px">Refeita</th></tr></thead><tbody>{"".join(linhas_af)}</tbody>'
            f'</table></div>')

    # a proveniência: como o artigo veio a existir
    prov = a.get("proveniencia") or {}
    linhas_prov = []
    for p in prov.get("cronologia", []):
        nota = (f'<div class="xs" style="padding-top:4px">{e(p["nota"])}</div>'
                if p.get("nota") else "")
        porque = (f'<div class="xs" style="padding-top:4px"><b>Porque importa:</b> '
                  f'{e(p["porque_importa"])}</div>' if p.get("porque_importa") else "")
        linhas_prov.append(
            f'<tr><td class="mono xs">{e(p["quando"])}</td>'
            f'<td class="mono xs">{e(p["quem"])}</td>'
            f'<td class="sm">{e(p["o_que"])}{nota}{porque}</td>'
            f'<td class="xs">{e(p.get("agente", ""))}</td></tr>')
    passos = "".join(linhas_prov)
    por_rever = "".join(f'<li class="sm">{e(x)}</li>' for x in prov.get("por_rever", []))
    bloco_prov = ""
    if passos:
        aviso_cron = (f'<p class="sm it" style="max-width:46em;padding-top:12px">'
                      f'{e(prov["aviso_sobre_esta_cronologia"])}</p>'
                      if prov.get("aviso_sobre_esta_cronologia") else "")
        b_rever = (f'<div class="sect" style="padding-top:16px">Por rever</div>'
                   f'<ul style="max-width:46em">{por_rever}</ul>' if por_rever else "")
        bloco_prov = (
            f'<div class="rule" style="padding:22px 0 8px"><div class="sect">Proveniência · como '
            f'este artigo veio a existir</div></div>'
            f'<p class="sm" style="max-width:46em;padding-bottom:12px">'
            f'{e(prov.get("porque_existe_este_ficheiro", ""))}</p>'
            f'<div class="rolar"><table><thead><tr><th style="width:150px">Quando</th>'
            f'<th style="width:100px">Quem</th><th>O que fez</th>'
            f'<th style="width:180px">Agente</th></tr></thead><tbody>{passos}</tbody></table></div>'
            f'{aviso_cron}{b_rever}')

    # os ficheiros desta pasta, ligados
    d = ROOT / a["pasta"]
    ficheiros = sorted(f.name for f in d.iterdir() if f.is_file() and f.name != "index.html")
    botoes = "".join(
        f'<button type="button" class="chip fich" data-src="{e(f)}">{e(f)}</button>'
        if f.endswith(".json") else f'<a class="chip" href="{e(f)}">{e(f)}</a>'
        for f in ficheiros)
    primeiro = next((f for f in ficheiros if f.endswith(".json")), None)
    bloco_fich = (
        f'<div class="rule" style="padding:22px 0 8px"><div class="sect">Os ficheiros deste '
        f'artigo</div></div>'
        f'<p class="sm" style="max-width:46em;padding-bottom:10px">Um artigo deste site é uma '
        f'pasta, e a pasta está aqui inteira. Clique num ficheiro para o ler <b>como dados</b> — '
        f'os estados ganham cor, um identificador de fonte fica ligado ao registo, um SHA-256 é '
        f'encurtado porque ninguém lê sessenta e quatro caracteres. O ficheiro em bruto continua '
        f'a um clique, e é o mesmo ficheiro.</p>'
        f'<div class="chips" style="padding-bottom:14px">{botoes}</div>'
        f'<pt-json-viewer site-root="../../../../../" '
        f'{f"src={primeiro}" if primeiro else ""}></pt-json-viewer>'
        f'<script>document.addEventListener("click",function(ev){{'
        f'var b=ev.target.closest(".fich");if(!b)return;'
        f'var v=document.querySelector("pt-json-viewer");if(v)v.load(b.dataset.src);'
        f'document.querySelectorAll(".fich").forEach(function(x){{'
        f'x.classList.toggle("ok",x===b)}});}});</script>')

    corpo = (cabeca + linha_estado + corpo_prosa + bloco_nao + bloco_af + bloco_prov + bloco_fich)
    nomeia = a["seccao"] == "protagonistas" or "pessoa" in (a.get("especie") or "")
    extra = ('<script type="module" src="../../../../../assets/components/'
             'pt-json-viewer/v1/v1.0/v1.0.0/pt-json-viewer.js"></script>')
    return pagina(f'{a["pasta"]}/index.html', a["titulo"], a["entrada"], corpo,
                  aqui=a["seccao"], nomeia_pessoas=nomeia, fontes_n=len(a.get("assenta_em", [])),
                  extra_body=extra)


def indice(artigos, registo):
    por_ano = {}
    for a in artigos:
        por_ano.setdefault(a["data"][:4], []).append(a)

    blocos = []
    for ano, lista in sorted(por_ano.items(), reverse=True):
        linhas = []
        for a in lista:
            rot, cor = ROT_ESTADO.get(a["estado"], (a["estado"], "#6b6e76"))
            ver = a.get("verificacao") or {}
            r = ver.get("resumo") or {}
            conf = (f'<span class="chip ok">{r["confirmadas"]} confirmadas</span>'
                    if r.get("confirmadas") else "")
            linhas.append(
                f'<tr><td class="mono xs">{e(a["data"])}</td>'
                f'<td><a href="{e(a["url"].replace("artigos/", ""))}">{e(a["titulo"])}</a>'
                f'<div class="xs" style="padding-top:4px">{e(a["entrada"][:150])}</div></td>'
                f'<td class="sm">{e(a["seccao"])}</td>'
                f'<td><span class="chip" style="color:{cor};border-color:{cor}">{e(rot)}</span>'
                f'{conf}</td>'
                f'<td class="mono xs">{len(a.get("assenta_em", []))} fonte(s)</td></tr>')
        blocos.append(
            f'<div class="rule" style="padding:22px 0 8px"><div class="sect">{ano}</div></div>'
            f'<div class="rolar"><table><thead><tr><th style="width:100px">Data</th><th>Artigo</th>'
            f'<th style="width:120px">Secção</th><th style="width:230px">Estado</th>'
            f'<th style="width:90px">Assenta em</th></tr></thead>'
            f'<tbody>{"".join(linhas)}</tbody></table></div>')

    contagens = {k: sum(1 for a in artigos if a["estado"] == k) for k, _, _, _ in ESTADOS}
    fichas = "".join(
        f'<span class="chip" style="color:{cor};border-color:{cor}">{rot}: {contagens[k]}</span>'
        for k, rot, _, cor in ESTADOS if contagens[k])
    legenda = "".join(
        f'<tr><td><span class="pastilha" style="background:{cor}"></span>{rot}</td>'
        f'<td class="sm">{desc}</td></tr>' for k, rot, desc, cor in ESTADOS)

    corpo = f"""
<div class="rule" style="padding:26px 0 8px"><div class="sect">Os artigos</div></div>
<h1 class="h-2" style="max-width:26em">Um artigo é uma pasta datada, e a pasta é o artigo.</h1>
<p class="std" style="max-width:46em;padding:14px 0 12px">Cada artigo vive em
<code>artigos/&lt;aaaa&gt;/&lt;mm&gt;/&lt;dd&gt;/&lt;slug&gt;/</code> com a prosa, o registo de
verificação de cada afirmação, e a proveniência — que execução de que agente o produziu, e por que
ordem. A data no caminho é a data do <b>material</b>, não a da publicação: um artigo só chega à
primeira página quando o editor de registo escreve a linha.</p>
<div class="chips" style="padding-bottom:18px">{fichas}</div>
{"".join(blocos)}
<div class="rule" style="padding:22px 0 8px"><div class="sect">Os estados</div></div>
<div class="rolar"><table><thead><tr><th style="width:160px">Estado</th><th>O que significa</th>
  </tr></thead><tbody>{legenda}</tbody></table></div>
<p class="xs" style="max-width:46em;padding-top:12px">O portão 11 falha a construção se um artigo
estiver em «publicado» sem o nome do editor de registo e a data. Uma execução agendada que
escrevesse essa linha seria apanhada: é a única salvaguarda que separa esta publicação de um
gerador de texto.</p>
"""
    return pagina("artigos/index.html", "Os artigos",
                  "Todos os artigos deste site, por data. Cada um é uma pasta com a prosa, a "
                  "verificação de cada afirmação e a proveniência.", corpo, aqui=None)


def escrever_indice_de_dados(artigos):
    """dados/historias.json — DERIVADO das pastas, nunca escrito à mão."""
    saida = []
    for a in artigos:
        ver = a.get("verificacao") or {}
        saida.append({
            "slug": a["slug"], "data": a["data"], "seccao": a["seccao"],
            "titulo": a["titulo"], "entrada": a["entrada"], "antetitulo": a.get("antetitulo"),
            "estado": a["estado"], "publicado_em": a.get("publicado_em"),
            "publicado_por": a.get("publicado_por"),
            "url": a["url"], "pasta": a["pasta"], "issue": a.get("issue"),
            "bloco_primeira_pagina": a.get("bloco_primeira_pagina"),
            "assenta_em": a.get("assenta_em", []),
            "marcas_na_prosa": marcas_de_fonte(a.get("prosa")),
            "verificacao": ver.get("resumo") or {},
            "tem_prosa": bool(a.get("prosa")),
        })
    (DADOS / "historias.json").write_text(json.dumps({
        "id": "pt-historias", "versao": "0.2.0",
        "atualizado": max((a["data"] for a in artigos), default="—"),
        "nota": ("O índice dos artigos, DERIVADO das pastas em artigos/<aaaa>/<mm>/<dd>/<slug>/ por "
                 "build/artigos.py. Não se edita este ficheiro: edita-se a pasta. É a mesma regra "
                 "que governa as organizações, derivadas dos cartões de orador — um índice escrito à "
                 "mão acaba por discordar das pastas, e nada parece avariado."),
        "estados": [{"id": k, "rotulo": r, "significa": d} for k, r, d, _ in ESTADOS],
        "contagem": len(saida),
        "publicados": sum(1 for x in saida if x["estado"] == "publicado"),
        "historias": saida,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    registo = json.loads((DADOS / "registo.json").read_text(encoding="utf-8"))
    artigos = ler_todos()
    escrever_indice_de_dados(artigos)
    feitas = [escrever("artigos/index.html", indice(artigos, registo))]
    for a in artigos:
        feitas.append(escrever(f'{a["pasta"]}/index.html', pagina_artigo(a, registo)))
    pub = sum(1 for a in artigos if a["estado"] == "publicado")
    print(f"artigos: {len(artigos)} ({pub} publicados), {len(feitas)} páginas")
    return artigos


if __name__ == "__main__":
    main()

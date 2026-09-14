#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — os portões das estruturas novas: artigos, secções, bastidores.

    python3 build/gates_artigos.py

PORQUE É QUE ISTO É UM FICHEIRO SEPARADO DE `build/gates.py`.

`build/gates.py` está na lista de recusa de `.claude/settings.json`: uma execução agendada não o
pode editar. A regra existe porque um agente que possa alterar o portão que o trava não tem
portão nenhum — e a maneira errada de acrescentar verificações seria levantar essa proteção.

Por isso os portões das estruturas que nasceram depois dele vivem aqui, e `gates.py` fica como
está: o núcleo estável, protegido. A integração contínua corre os dois, e qualquer um deles a
falhar é um lançamento que não acontece. Um portão que falha é respondido, nunca silenciado.

OS PORTÕES

  16 · O CAMINHO DE UM ARTIGO NÃO MENTE. artigos/<aaaa>/<mm>/<dd>/<slug>/ tem de concordar com os
       campos `data` e `slug` do próprio artigo. Um artigo cuja pasta diz uma data e cujo ficheiro
       diz outra tem dois endereços e uma delas está errada.
  17 · CADA AFIRMAÇÃO DE UM ARTIGO ANDA PARA TRÁS. Toda a marca [[fonte:…]] na prosa e toda a
       fonte citada no registo de verificação têm de existir em dados/registo.json.
  18 · UM ARTIGO VERIFICADO FOI MESMO VERIFICADO. Em `verificado` ou `publicado` tem de haver
       prosa, tem de haver registo de verificação, e nenhuma afirmação pode ficar por marcar.
  19 · OS BASTIDORES NÃO PUBLICAM AFIRMAÇÕES. A consola está em inglês por decisão do editor, e a
       condição dessa exceção é que ela relate a redação e nunca o mundo: nenhuma página de
       /backoffice/ pode citar uma fonte congelada como prova de uma afirmação sobre Portugal.
  20 · CADA SECÇÃO TEM UM REGISTO EDITORIAL. As oito secções do resumo, cada uma com o seu
       seccoes/<id>/seccao.json, e nenhuma a dizer que pode afirmar o que não tem fontes para
       afirmar.
  21 · O ÍNDICE DE ENTIDADES CONCORDA COM O DISCO. Cada entidade do índice tem página, cada página
       sob entidades/ está no índice, e o caminho de cada uma é o que a fórmula produz. Um índice
       que promete uma página que não existe é uma ligação partida à espera de acontecer.
  22 · CADA ENTIDADE LIGÁVEL TEM UM FUNDAMENTO, E O FUNDAMENTO É VERDADE. `bytes` se e só se o
       nome foi encontrado numa cópia congelada; `registo` se e só se o nó é editor de um ficheiro
       congelado. Uma entidade ligada sem fundamento é uma afirmação sem fonte.
  23 · A FÓRMULA DE LIGAÇÃO É CUMPRIDA NAS PÁGINAS. Nenhuma página liga a mesma entidade mais do
       que a fórmula permite, nenhuma página de entidade se liga a si própria, e o texto de cada
       ligação é o nome verbatim da entidade — não uma abreviatura, não um apelido.
  25 · NENHUM COMENTÁRIO DE AGENTE FOI INVENTADO. Cada entrada de um `comentarios.json` tem de
       nomear, no campo `de`, um ficheiro e um caminho que existem e resolvem. É a regra das
       afirmações virada para dentro: um comentário atribuído a um modelo que nunca o escreveu é
       uma afirmação com uma fonte falsa, que é pior do que uma afirmação sem fonte nenhuma.
  24 · NENHUMA PÁGINA DE PESSOA DIZ NADA SOBRE A PESSOA. Cada valor da tabela de campos de uma
       página de Pessoa tem de ser, byte a byte, um valor que já está em dados/pessoas.json ou no
       nó do grafo. É o §4 do resumo a ser conferido e não prometido: sem isto, uma linha de prosa
       sobre alguém entrava na página sem ninguém dar por ela.
"""
import html as _html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
ARTIGOS = ROOT / "artigos"
SECCOES = ROOT / "seccoes"
BASTIDORES = ROOT / "backoffice"

erros = []


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


registo = carregar("registo.json")
historias = carregar("historias.json")
equipa = carregar("equipa.json")
entregas = carregar("entregas.json")
por_id = {s["id"]: s for s in registo.get("fontes", [])}

AS_OITO = ["empresas", "protagonistas", "instituicoes", "politicas",
           "casos-de-uso", "codigo-aberto", "diaspora", "eventos"]
ESTADOS_VALIDOS = {"procurado", "rascunho", "verificado", "publicado", "superseded"}


# --- 16. o caminho de um artigo não mente --------------------------------------
metas = sorted(ARTIGOS.rglob("artigo.json")) if ARTIGOS.exists() else []
if not metas:
    erros.append("artigos: não há uma única pasta de artigo. O site tem uma secção de artigos e "
                 "nada lá dentro")

for meta in metas:
    d = meta.parent
    rel = d.relative_to(ROOT).as_posix()
    try:
        a = json.loads(meta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        erros.append(f"{rel}/artigo.json: não é JSON válido ({ex})")
        continue

    partes = rel.split("/")
    if len(partes) != 5 or partes[0] != "artigos":
        erros.append(f"{rel}: um artigo vive em artigos/<aaaa>/<mm>/<dd>/<slug>/, e este não")
        continue
    _, ano, mes, dia, slug = partes
    esperado = f"{ano}-{mes}-{dia}"
    if a.get("data") != esperado:
        erros.append(f'{rel}: a pasta diz {esperado} e o artigo diz «{a.get("data")}». Um artigo '
                     f'com duas datas tem dois endereços, e um deles está errado')
    if a.get("slug") != slug:
        erros.append(f'{rel}: a pasta diz «{slug}» e o artigo diz «{a.get("slug")}»')
    if a.get("estado") not in ESTADOS_VALIDOS:
        erros.append(f'{rel}: estado «{a.get("estado")}» não existe. Os estados são '
                     f'{", ".join(sorted(ESTADOS_VALIDOS))}')
    if a.get("seccao") not in AS_OITO:
        erros.append(f'{rel}: a secção «{a.get("seccao")}» não é uma das oito do resumo')
    for campo in ("titulo", "entrada"):
        if not a.get(campo):
            erros.append(f'{rel}: falta o campo obrigatório «{campo}»')

    # --- 17. cada afirmação anda para trás -------------------------------------
    for sid in a.get("assenta_em", []):
        if sid not in por_id:
            erros.append(f'{rel}: assenta em «{sid}», que não está no registo de fontes')

    md = d / "artigo.md"
    prosa = md.read_text(encoding="utf-8") if md.exists() else ""
    for sid in set(re.findall(r"\[\[fonte:([^\]]+)\]\]", prosa)):
        if sid not in por_id:
            erros.append(f'{rel}/artigo.md: cita [[fonte:{sid}]], que não está no registo')
        elif sid not in a.get("assenta_em", []):
            erros.append(f'{rel}: a prosa cita «{sid}» e o artigo.json não o lista em '
                         f'assenta_em — os dois têm de concordar sobre em que o artigo assenta')

    fa = d / "afirmacoes.json"
    ver = json.loads(fa.read_text(encoding="utf-8")) if fa.exists() else None
    if ver:
        for af in ver.get("afirmacoes", []):
            if af.get("fonte") not in por_id:
                erros.append(f'{rel}/afirmacoes.json: a afirmação {af.get("id")} cita '
                             f'«{af.get("fonte")}», que não está no registo')
            if af.get("estado") not in ("confirmada", "disputada", "nao_encontrada"):
                erros.append(f'{rel}/afirmacoes.json: {af.get("id")} tem o estado '
                             f'«{af.get("estado")}», que não é um dos três')
        r = ver.get("resumo") or {}
        contado = {k: sum(1 for x in ver.get("afirmacoes", []) if x.get("estado") == k)
                   for k in ("confirmada", "disputada", "nao_encontrada")}
        if (r.get("confirmadas"), r.get("disputadas"), r.get("nao_encontradas")) != \
                (contado["confirmada"], contado["disputada"], contado["nao_encontrada"]):
            erros.append(f'{rel}/afirmacoes.json: o resumo não bate certo com as afirmações')

    # --- 18. um artigo verificado foi mesmo verificado -------------------------
    if a.get("estado") in ("verificado", "publicado"):
        if not prosa.strip():
            erros.append(f'{rel}: está em «{a["estado"]}» e não tem prosa. Não se verifica o que '
                         f'não está escrito')
        if not ver or not ver.get("afirmacoes"):
            erros.append(f'{rel}: está em «{a["estado"]}» e não tem registo de verificação')
        elif not ver.get("verificado_em"):
            erros.append(f'{rel}/afirmacoes.json: não diz quando foi verificado')

    # --- a linha do editor, para o formato novo -------------------------------
    ed = (equipa.get("editor_de_registo") or {}).get("nome")
    if a.get("estado") == "publicado":
        if a.get("publicado_por") != ed:
            erros.append(f'{rel}: está publicado por «{a.get("publicado_por")}», que não é o '
                         f'editor de registo ({ed}). Só ele põe esta linha')
        if not a.get("publicado_em"):
            erros.append(f"{rel}: está publicado e não tem data de publicação")
        if ver and any(x.get("estado") == "nao_encontrada" for x in ver.get("afirmacoes", [])):
            erros.append(f'{rel}: está publicado e tem uma afirmação por encontrar. Uma história '
                         f'não se publica com uma afirmação que ninguém conseguiu confirmar')
    else:
        if a.get("publicado_em") or a.get("publicado_por"):
            erros.append(f'{rel}: não está publicado e já tem publicado_em/publicado_por')

# o índice derivado tem de cobrir exatamente as pastas
if historias:
    nas_pastas = {m.parent.relative_to(ROOT).as_posix() for m in metas}
    no_indice = {h["pasta"] for h in historias.get("historias", [])}
    if nas_pastas != no_indice:
        erros.append("historias.json: o índice não cobre exatamente as pastas de artigo — foi "
                     "editado à mão em vez de derivado por build/artigos.py")


# --- 19. os bastidores não publicam afirmações ---------------------------------
# A consola está em inglês por decisão do editor. A condição dessa exceção é que ela relate a
# REDAÇÃO e nunca o MUNDO: uma página em inglês que citasse uma fonte congelada como prova de
# alguma coisa sobre Portugal seria a regra da língua a ser quebrada a sério.
if BASTIDORES.exists():
    for p in sorted(BASTIDORES.rglob("*.html")):
        t = p.read_text(encoding="utf-8")
        rel = p.relative_to(ROOT).as_posix()
        if "[[fonte:" in t:
            erros.append(f"{rel}: carrega uma marca de fonte. Os bastidores relatam a redação, "
                         f"não o mundo")
        # uma ligação para uma âncora do registo é uma citação de prova
        if re.search(r'href="[^"]*registo/#', t):
            erros.append(f"{rel}: cita uma fonte congelada como prova. A consola pode CONTAR "
                         f"fontes; não pode assentar uma afirmação numa delas")
        if not re.search(r'lang="en"', t):
            erros.append(f"{rel}: os bastidores estão em inglês e a página não o declara em lang")
        if "This is the operations console" not in t:
            erros.append(f"{rel}: falta o aviso que diz que isto não é a publicação. A exceção à "
                         f"regra da língua vale enquanto for visível ao leitor que lá cair")
    for obrigatoria in ("backoffice/index.html", "backoffice/docs.html", "backoffice/viewer.html"):
        if not (ROOT / obrigatoria).exists():
            erros.append(f"{obrigatoria}: não foi gerada")


# --- 20. cada secção tem um registo editorial ----------------------------------
for sid in AS_OITO:
    f = SECCOES / sid / "seccao.json"
    if not f.exists():
        erros.append(f"seccoes/{sid}/seccao.json: não existe. Cada uma das oito secções do resumo "
                     f"tem uma pasta e um registo editorial")
        continue
    s = json.loads(f.read_text(encoding="utf-8"))
    for campo in ("rotulo", "ambito", "o_que_pode_afirmar_hoje", "o_que_nao_pode",
                  "a_afirmacao_honesta"):
        if not s.get(campo):
            erros.append(f"seccoes/{sid}/seccao.json: falta «{campo}»")
    if s.get("id") != sid:
        erros.append(f'seccoes/{sid}/seccao.json: o id diz «{s.get("id")}» e a pasta diz «{sid}»')
    congeladas = [t for t in s.get("fontes_alvo", []) if t.get("estado") == "congelada"]
    # Uma secção sem fontes congeladas não pode dizer que afirma alguma coisa. A declaração tem de
    # COMEÇAR por «Nada» — o que vem a seguir é a explicação, e exigir a palavra sozinha obrigaria
    # a escolher entre passar no portão e dizer porquê ao leitor. A verificação é sobre a primeira
    # palavra, que é a que responde à pergunta.
    diz = s.get("o_que_pode_afirmar_hoje", "").strip().lower()
    diz_que_afirma = not diz.startswith("nada")
    if not congeladas and diz_que_afirma:
        erros.append(f'seccoes/{sid}: não tem nenhuma fonte congelada e o registo editorial diz '
                     f'que pode afirmar alguma coisa. Uma secção sem bytes afirma «Nada.»')
    for t in s.get("fontes_alvo", []):
        if t.get("estado") == "congelada" and not any(
                x["pagina"].endswith(t["id"]) or x["id"].endswith("/" + t["id"])
                for x in registo.get("fontes", [])):
            erros.append(f'seccoes/{sid}: diz que «{t["id"]}» está congelada e não há nenhuma '
                         f'fonte no registo com esse nome')

extra = {p.name for p in SECCOES.iterdir() if p.is_dir()} - set(AS_OITO) if SECCOES.exists() else set()
if extra:
    erros.append(f'seccoes/: pastas a mais ({", ".join(sorted(extra))}). As secções são as oito do '
                 f'resumo, e acrescentar uma é uma decisão editorial, não um efeito secundário')


# --- 21, 22, 23, 24. as entidades -----------------------------------------------
entidades = carregar("entidades.json")
grafo = carregar("grafo.json")
pessoas_json = carregar("pessoas.json")
ENTIDADES = ROOT / "entidades"
nos_por_id = {n["id"]: n for n in grafo.get("nos", [])}
ents = entidades.get("entidades", [])

if not ents:
    erros.append("entidades: dados/entidades.json não tem entidades — build/entidades.py não "
                 "correu, e as páginas do site estão a ligar para um índice que não existe")

# 21 · o índice e o disco dizem a mesma coisa.
no_disco = set()
if ENTIDADES.exists():
    no_disco = {p.parent.relative_to(ROOT).as_posix() + "/"
                for p in ENTIDADES.rglob("index.html")
                if p.parent != ENTIDADES}
no_indice = {x["url"] for x in ents}
for falta in sorted(no_indice - no_disco):
    erros.append(f'entidades: o índice promete {falta} e não há página nenhuma nesse caminho')
for sobra in sorted(no_disco - no_indice):
    erros.append(f'entidades: {sobra} existe no disco e não está no índice — uma página órfã não '
                 f'é reconstruída nem apagada quando a entidade desaparece do grafo')

# 22 · o fundamento de cada entidade ligável é verdade.
for x in ents:
    f = x.get("fundamento")
    tem_bytes = bool(x.get("nos_bytes"))
    e_editor = bool((nos_por_id.get(x["no"]) or {}).get("publica"))
    if x.get("ligavel") and not f:
        erros.append(f'entidades: {x["no"]} está marcada como ligável e não tem fundamento — '
                     f'uma ligação sem fundamento é uma afirmação sem fonte')
    if f == "bytes" and not tem_bytes:
        erros.append(f'entidades: {x["no"]} diz que o seu fundamento são os bytes e '
                     f'`nos_bytes` está vazio')
    if f == "registo" and not e_editor:
        erros.append(f'entidades: {x["no"]} diz que o seu fundamento é o registo e o nó não é '
                     f'editor de ficheiro congelado nenhum')
    if f == "registo" and tem_bytes:
        erros.append(f'entidades: {x["no"]} invoca o fundamento fraco tendo o forte — quando o '
                     f'nome está nos bytes, o fundamento é `bytes`')
    # O fundamento e a ligabilidade são coisas diferentes: um nome curto pode estar nos bytes (e
    # tem fundamento) e continuar a não ser ligável, que é precisamente o que a regra do
    # comprimento existe para fazer. O portão confere a ligabilidade, não o fundamento.
    if x.get("ligavel") and len(x["nome"]) < 6:
        erros.append(f'entidades: {x["no"]} tem um nome de {len(x["nome"])} caracteres e está '
                     f'ligável — a fórmula publicada exige pelo menos 6')

# 23 · a fórmula é cumprida nas páginas geradas.
MAX_POR_PAGINA = 1
por_url = {x["url"]: x for x in ents}
LIGACAO = re.compile(r'<a class="ent" href="([^"]+)">([^<]*)</a>')
nomes_por_url = {x["url"]: x["nome"] for x in ents}
for pag in sorted(ROOT.rglob("*.html")):
    rel = pag.relative_to(ROOT).as_posix()
    if "fontes/congeladas/" in rel or "/briefs/" in rel or "node_modules" in rel:
        continue
    texto = pag.read_text(encoding="utf-8")
    achados = LIGACAO.findall(texto)
    if not achados:
        continue
    contagem = {}
    for href, rotulo in achados:
        alvo = re.sub(r"^(\.\./)+", "", href)
        contagem[alvo] = contagem.get(alvo, 0) + 1
        esperado = nomes_por_url.get(alvo)
        # O texto vem de HTML e está escapado; o nome do índice é o nome. Comparar os dois sem
        # desfazer o escape dava um erro em cada organização com um «&» no nome, que é um bug do
        # portão e não do site — e foi o que aconteceu quando este portão correu pela primeira vez.
        rotulo = _html.unescape(rotulo)
        if esperado is None:
            erros.append(f'{rel}: liga a {alvo}, que não é o caminho de nenhuma entidade do índice')
        elif rotulo != esperado:
            erros.append(f'{rel}: liga a {alvo} com o texto «{rotulo}», e o nome verbatim daquela '
                         f'entidade é «{esperado}» — a fórmula liga o nome, não uma variante')
        if alvo + "index.html" == rel:
            erros.append(f'{rel}: é a página de uma entidade e liga-se a si própria')
    for alvo, n in contagem.items():
        if n > MAX_POR_PAGINA:
            erros.append(f'{rel}: liga {n} vezes a {alvo}; a fórmula publicada permite '
                         f'{MAX_POR_PAGINA} por página')
    if "<a class=\"ent\"" in texto:
        # Uma ligação dentro de outra ligação é HTML que cada navegador desfaz à sua maneira.
        if re.search(r'<a\b[^>]*>(?:(?!</a>).)*<a class="ent"', texto, re.S):
            erros.append(f'{rel}: tem uma ligação de entidade dentro de outra ligação')

# 24 · nenhuma página de Pessoa diz nada sobre a pessoa.
verbatim = set()
for pp in pessoas_json.get("pessoas", []):
    for v in pp.values():
        if isinstance(v, str):
            verbatim.add(v)
for n in grafo.get("nos", []):
    for v in n.values():
        if isinstance(v, str):
            verbatim.add(v)
# O valor da célula pode conter uma ligação de entidade — «Zero Risk Startup» na página de quem
# o evento lista sob ela. Por isso captura-se o INTERIOR da célula e tiram-se as marcas antes de
# comparar: um padrão que só aceitasse texto simples deixava de ver exatamente as células que
# passaram a ter uma ligação, e um portão que deixa de ver metade do que guarda não guarda nada.
CAMPO = re.compile(r'<tr><th style="width:230px">(.*?)</th><td class="sm">(.*?)</td></tr>', re.S)
for x in ents:
    if x["tipo"] != "Pessoa":
        continue
    f = ROOT / x["url"] / "index.html"
    if not f.exists():
        continue
    for _rot, valor in CAMPO.findall(f.read_text(encoding="utf-8")):
        cru = _html.unescape(re.sub(r"<[^>]+>", "", valor))
        if cru not in verbatim:
            erros.append(f'{x["url"]}: a tabela de campos traz «{cru[:60]}», que não é um valor '
                         f'verbatim de dados/pessoas.json nem do nó do grafo — uma página de '
                         f'Pessoa não escreve uma linha sobre a pessoa')


# --- 25. nenhum comentário de agente foi inventado -------------------------------
# O campo `de` é «<caminho de ficheiro>#<chave>[<índice ou id>]...». O portão abre o ficheiro e
# percorre o caminho. Se o caminho não resolver, o comentário não anda para trás até nada.
REF = re.compile(r"^([^#]+)#(.+)$")
PASSO = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)(?:\[([^\]]+)\])?")

def resolve(caminho):
    m = REF.match(caminho)
    if not m:
        return False, "não tem a forma <ficheiro>#<caminho>"
    f = ROOT / m.group(1)
    if not f.exists():
        return False, f"o ficheiro {m.group(1)} não existe"
    try:
        no = json.loads(f.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"{m.group(1)} não é JSON legível: {exc}"
    for chave, indice in PASSO.findall(m.group(2)):
        if not isinstance(no, dict) or chave not in no:
            return False, f"«{chave}» não existe em {m.group(1)}"
        no = no[chave]
        # `findall` devolve "" e não None para um grupo opcional que não casou. Tratar os dois
        # como ausência é o que faz `…entregas[<id>].revisao` resolver até ao fim em vez de ir
        # procurar um item com id "" dentro de um objeto que não é uma lista.
        if not indice:
            continue
        if indice.isdigit():
            if not isinstance(no, list) or int(indice) >= len(no):
                return False, f"«{chave}[{indice}]» está fora do fim da lista"
            no = no[int(indice)]
        else:
            achado = next((x for x in (no if isinstance(no, list) else [])
                           if isinstance(x, dict) and x.get("id") == indice), None)
            if achado is None:
                return False, f"nenhum item de «{chave}» tem id «{indice}»"
            no = achado
    return True, ""

n_comentarios = 0
agentes_vistos = set()
for f in sorted(ARTIGOS.rglob("comentarios.json")):
    rel = f.relative_to(ROOT).as_posix()
    doc = json.loads(f.read_text(encoding="utf-8"))
    if not doc.get("derivado"):
        erros.append(f'{rel}: não está marcado como derivado. Um ficheiro de comentários escrito '
                     f'à mão é proveniência fabricada — este ficheiro é gerado por '
                     f'build/comentarios.py e diz de onde vem cada entrada')
    for c in doc.get("fluxo", []):
        n_comentarios += 1
        agentes_vistos.add(c.get("agente"))
        de = c.get("de")
        if not de:
            erros.append(f'{rel}: a entrada {c.get("id")} não diz de onde veio')
            continue
        ok, porque = resolve(de)
        if not ok:
            erros.append(f'{rel}: a entrada {c.get("id")} diz que vem de «{de}» e {porque}')
        if c.get("texto") is None:
            erros.append(f'{rel}: a entrada {c.get("id")} não tem texto')

# O agregado tem de concordar com a soma das pastas: uma consola que mostra mais trabalho do que
# aconteceu é a mesma espécie de mentira que um comentário inventado, só que em números.
agregado = carregar("comentarios.json")
if agregado and agregado.get("contagem") != n_comentarios:
    erros.append(f'dados/comentarios.json diz {agregado.get("contagem")} entradas e as pastas dos '
                 f'artigos têm {n_comentarios}')

# Nenhum agente aparece sem estar declarado: um nome de agente que ninguém sabe de onde vem é um
# colaborador anónimo numa publicação cujo argumento inteiro é saber quem disse o quê.
declarados = set((agregado or {}).get("agentes", {}))
for a in sorted(agentes_vistos - declarados):
    erros.append(f'comentários: o agente «{a}» aparece no fluxo e não está declarado em '
                 f'dados/comentarios.json#agentes')


# --- relatório -----------------------------------------------------------------
if erros:
    print(f"portões (artigos, secções, bastidores): {len(erros)} erro(s)")
    for x in erros:
        print("  ✗", x)
    sys.exit(1)

pub = sum(1 for m in metas
          if json.loads(m.read_text(encoding="utf-8")).get("estado") == "publicado")
com_prosa = sum(1 for m in metas if (m.parent / "artigo.md").exists())
print(f"portões (artigos, secções, bastidores): OK — {len(metas)} artigos em pastas datadas "
      f"({com_prosa} com prosa, {pub} publicados), cada caminho a concordar com a sua data e "
      f"slug, cada afirmação a andar para trás até ao registo, {len(AS_OITO)} secções com "
      f"registo editorial, bastidores em inglês sem citar prova, "
      f"{len(ents)} entidades com página e fundamento conferido, "
      f"{n_comentarios} comentários de agente a andarem para trás até um ficheiro")

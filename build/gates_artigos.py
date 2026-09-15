#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — the gates for the newer structures: articles, sections, back office,
entities, agent activity, run records, and the language rule.

    python3 build/gates_artigos.py

WHY THIS IS A SEPARATE FILE FROM `build/gates.py`.

`build/gates.py` is in the deny list of `.claude/settings.json`: no agent here can edit it. The rule
exists because an agent that can change the gate that stops it has no gate at all — and the wrong
way to add checks would be to lift that protection.

So the gates for the structures that came after it live here, and `gates.py` stays as it is: the
stable core, protected. CI runs both, and either one failing is a release that does not happen. A
gate that fails is answered, never silenced.

THE GATES

  16 · AN ARTICLE'S PATH DOES NOT LIE. artigos/<yyyy>/<mm>/<dd>/<slug>/ has to agree with the
       article's own `data` and `slug` fields. An article whose folder says one date and whose file
       says another has two addresses, and one of them is wrong.
  17 · EVERY CLAIM IN AN ARTICLE WALKS BACK. Every [[fonte:…]] mark in the prose and every source
       cited in the verification record has to exist in dados/registo.json.
  18 · A VERIFIED ARTICLE WAS ACTUALLY VERIFIED. In `verificado` or `publicado` there has to be
       prose, there has to be a verification record, and no claim may be left unmarked.
  19 · THE BACK OFFICE PUBLISHES NO CLAIMS. The console is in English by the editor's decision, and
       the condition of that exception is that it reports the newsroom and never the world: no page
       under /backoffice/ may cite a frozen source as evidence for a claim about Portugal.
  20 · EVERY SECTION HAS AN EDITORIAL RECORD. The brief's eight sections, each with its own
       seccoes/<id>/seccao.json, and none of them claiming what it has no sources to claim.
  21 · THE ENTITY INDEX AGREES WITH THE DISK. Every entity in the index has a page, every page under
       entidades/ is in the index, and each path is what the formula produces. An index promising a
       page that does not exist is a broken link waiting to happen.
  22 · EVERY LINKABLE ENTITY HAS A GROUND, AND THE GROUND IS TRUE. `bytes` if and only if the name
       was found in a frozen copy; `registo` if and only if the node publishes a frozen file. An
       entity linked with no ground is a claim with no source.
  23 · THE LINKING FORMULA IS OBEYED ON THE PAGES. No page links the same entity more often than
       the formula allows, no entity page links to itself, and each link's text is the entity's
       verbatim name — not an abbreviation, not a surname.
  24 · NO PERSON'S PAGE SAYS ANYTHING ABOUT THE PERSON. Every value in a Pessoa page's field table
       has to be, byte for byte, a value already in dados/pessoas.json or in the graph node. It is
       §4 of the brief checked rather than promised: without it, a line of prose about somebody
       would enter the page with nobody noticing.
  25 · NO AGENT COMMENT WAS INVENTED. Every entry in a `comentarios.json` has to name, in its `de`
       field, a file and a path that exist and resolve. It is the claims rule turned inward: a
       comment attributed to a model that never wrote it is a claim with a false source, which is
       worse than a claim with no source at all.
  26 · "CONSTRUCTION" IS NOT THE WORD YOU WRITE TO ESCAPE THE BOUNDARY. Gate 12 exempts a run that
       declares no department, because the bootstrap session creates everything. A construction run
       uses that exemption, so it has to earn it: it freezes no source, moves no card, publishes
       nothing, and declares itself as such. Without this, the boundary between departments would
       have a door with the name written beside it.
  27 · CODE IS IN ENGLISH. Every comment and docstring under build/, admin/build/ and
       assets/components/ is read for Portuguese function words. CLAUDE.md has said "code and
       comments are in English" since the first commit, and seventeen files ignored it because the
       code already there was Portuguese — an existing convention is not the rule. The two honest
       exceptions are declared in docs/guidance/language.md and encoded here, not hidden here.
  28 · EVERY AGENT THAT TOUCHES THIS SITE IS NAMED. A run record names an `agente` that exists in
       dados/agentes.json, and every registered agent has a ROLE.md and a MANDATE.md. An agent
       nobody can name is an anonymous contributor to a publication whose argument is knowing who
       said what.
"""
import ast
import html as _html
import io
import json
import re
import sys
import tokenize
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


# --- 16. an article's path does not lie ----------------------------------------
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

    # --- 17. every claim walks back --------------------------------------------
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

    # --- 18. a verified article was actually verified -------------------------
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


# --- 19. the back office publishes no claims -----------------------------------
# The console is in English by the editor's decision. The condition of that exception is that it
# reports the NEWSROOM and never the WORLD: an English page citing a frozen source as evidence for
# something about Portugal would be the language rule being broken for real.
if BASTIDORES.exists():
    for p in sorted(BASTIDORES.rglob("*.html")):
        t = p.read_text(encoding="utf-8")
        rel = p.relative_to(ROOT).as_posix()
        if "[[fonte:" in t:
            erros.append(f"{rel}: carrega uma marca de fonte. Os bastidores relatam a redação, "
                         f"não o mundo")
        # a link to a register anchor is a citation of evidence
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


# --- 20. every section has an editorial record ---------------------------------
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
    # A section with no frozen sources cannot say it claims anything. The statement has to BEGIN
    # with «Nada» — what follows is the explanation, and demanding the word alone would force a
    # choice between passing the gate and telling the reader why. The check is on the first word,
    # which is the one that answers the question.
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


# --- 21, 22, 23, 24. the entities -----------------------------------------------
entidades = carregar("entidades.json")
grafo = carregar("grafo.json")
pessoas_json = carregar("pessoas.json")
ENTIDADES = ROOT / "entidades"
nos_por_id = {n["id"]: n for n in grafo.get("nos", [])}
ents = entidades.get("entidades", [])

if not ents:
    erros.append("entidades: dados/entidades.json não tem entidades — build/entidades.py não "
                 "correu, e as páginas do site estão a ligar para um índice que não existe")

# 21 · the index and the disk say the same thing.
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

# 22 · every linkable entity's ground is true.
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
    # The ground and linkability are different things: a short name can be in the bytes (and so
    # has a ground) and still not be linkable, which is precisely what the length rule exists
    # to do. The gate checks linkability, not the ground.
    if x.get("ligavel") and len(x["nome"]) < 6:
        erros.append(f'entidades: {x["no"]} tem um nome de {len(x["nome"])} caracteres e está '
                     f'ligável — a fórmula publicada exige pelo menos 6')

# 23 · the formula is obeyed on the generated pages.
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
        # The text comes from HTML and is escaped; the index's name is the name. Comparing the
        # two without unescaping gave an error for every organisation with an «&» in its name,
        # which is a bug in the gate and not in the site — and that is what happened the first
        # time this gate ran.
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
        # A link inside another link is HTML each browser unpicks its own way.
        if re.search(r'<a\b[^>]*>(?:(?!</a>).)*<a class="ent"', texto, re.S):
            erros.append(f'{rel}: tem uma ligação de entidade dentro de outra ligação')

# 24 · no Pessoa page says anything about the person.
verbatim = set()
for pp in pessoas_json.get("pessoas", []):
    for v in pp.values():
        if isinstance(v, str):
            verbatim.add(v)
for n in grafo.get("nos", []):
    for v in n.values():
        if isinstance(v, str):
            verbatim.add(v)
# A cell's value may contain an entity link — «Zero Risk Startup» on the page of whoever
# the event lists under it. So the cell's INNER html is captured and tags stripped before
# comparing: a pattern accepting only plain text would stop seeing exactly the cells that had
# just gained a link, and a gate that stops seeing half of what it guards guards nothing.
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


# --- 25. no agent comment was invented ------------------------------------------
# The `de` field is «<file path>#<key>[<index or id>]...». The gate opens the file and walks the
# path. If the path does not resolve, the comment walks back to nothing.
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
        # `findall` returns "" and not None for an optional group that did not match. Treating
        # both as absence is what makes `…entregas[<id>].revisao` resolve to the end instead of
        # hunting for an item with id "" inside an object that is not a list.
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

# The aggregate has to agree with the sum of the folders: a console showing more work than
# happened is the same kind of lie as an invented comment, only in numbers.
agregado = carregar("comentarios.json")
if agregado and agregado.get("contagem") != n_comentarios:
    erros.append(f'dados/comentarios.json diz {agregado.get("contagem")} entradas e as pastas dos '
                 f'artigos têm {n_comentarios}')

# No agent appears undeclared: an agent name nobody can place is an
# anonymous contributor to a publication whose entire argument is knowing who said what.
declarados = set((agregado or {}).get("agentes", {}))
for a in sorted(agentes_vistos - declarados):
    erros.append(f'comentários: o agente «{a}» aparece no fluxo e não está declarado em '
                 f'dados/comentarios.json#agentes')


# --- 26. a construction run must earn the exemption it uses ---------------------
RUNS = ROOT / "redacao" / "runs"
n_runs = 0
for f in sorted(RUNS.glob("*.json")) if RUNS.exists() else []:
    r = json.loads(f.read_text(encoding="utf-8"))
    n_runs += 1
    if r.get("departamento"):
        continue                       # that one is checked by gate 12, in build/gates.py
    especie = r.get("especie")
    if not especie:
        erros.append(f'runs: {f.name} não declara departamento nem espécie. A isenção do portão '
                     f'12 existe para a sessão de arranque; uma execução que a usa tem de dizer '
                     f'porquê')
        continue
    if especie != "construcao":
        continue
    for pasta in r.get("pastas_alteradas", []):
        if pasta.startswith("fontes/congeladas"):
            erros.append(f'runs: {f.name} declara-se de construção e mexeu em «{pasta}». Congelar '
                         f'uma fonte é trabalho da pesquisa, e uma execução que o faz declara-se '
                         f'como tal ou não o faz')
    if r.get("issues_movidos"):
        erros.append(f'runs: {f.name} declara-se de construção e moveu '
                     f'{len(r["issues_movidos"])} issue(s). Mover um cartão é trabalho de um '
                     f'departamento, e cada coluna tem o seu')
    for m in r.get("issues_movidos", []):
        if m.get("para") == "publicado":
            erros.append(f'runs: {f.name} pôs um issue em «publicado». Essa linha é do editor de '
                         f'registo e de mais ninguém')
    if r.get("portoes") is not True:
        erros.append(f'runs: {f.name} registou uma versão sem dizer que os portões ficaram verdes')


# --- 27. code is in English -----------------------------------------------------
# Portuguese function words that essentially never appear in English prose. Matching on function
# words rather than on accents is deliberate: a comment can be entirely Portuguese without a single
# accented character, and an English comment may legitimately quote an accented Portuguese name.
PT_PALAVRAS = re.compile(
    r"\b(?:não|são|está|estão|é|foi|ser|tem|têm|uma|uns|umas|que|para|com|por|"
    r"como|quando|onde|porque|porquê|isso|isto|aquilo|cada|todos|todas|"
    r"ficheiro|ficheiros|página|páginas|portão|portões|afirmação|afirmações|"
    r"fonte|fontes|leitor|leitura|escrever|escrita|nenhum|nenhuma|mesmo|mesma|"
    r"sítio|coisa|coisas|dele|dela|deles|delas|pelo|pela|nos|nas|aos|às)\b",
    re.IGNORECASE)

# The exceptions, declared rather than hidden. Each one says why.
EXCEPCOES = {
    # Portuguese identifiers this pipeline is built on. These are names, not prose, and renaming
    # them is the scheduled data-key migration described in docs/guidance/language.md.
    "identificadores": re.compile(
        r"\b(?:dados|fontes|congeladas|redacao|artigos|seccoes|entidades|comentarios|"
        r"historias|registo|grafo|ontologia|verificacoes|entregas|aviso|equipa|lexico|"
        r"organizacoes|pessoas|sessoes|temas|manifesto|mudancas|excluidas|"
        r"estado|fonte|nome|texto|afirmacoes|proveniencia|artigo|seccao|slug|"
        r"publicado|verificado|rascunho|procurado|congelado|confirmada|disputada|"
        r"nao_encontrada|por_verificar|fonte_inacessivel|departamento|especie|construcao|"
        r"arranque|pesquisa|verificacao|editor|pastas_alteradas|issues_movidos|portoes|"
        r"versao|quando|agente|leitura|verbo|inverso|dominio|alcance|tudo|paginas|"
        r"mesa|bancadas|quadro|colunas|cartoes|carga|correio|runs|issues|decisoes|"
        r"chrome|build|gates|extract|entidade|comentario|api|backoffice)\b", re.IGNORECASE),
}


def _comentarios_de(caminho, texto):
    """Every comment and docstring in a file, as (line number, text).

    Only comments are read. Portuguese inside a STRING is usually a label the reader sees, which is
    exactly where Portuguese belongs — failing on those would be the gate telling the site to stop
    being Portuguese.

    AND A TRIPLE-QUOTED STRING IS NOT A DOCSTRING. This gate's first version matched every
    triple-quoted block with a regular expression and flagged eleven page templates in
    build/build.py: blocks of HTML holding the Portuguese a reader sees, assigned to a variable. It
    was telling the site to stop being Portuguese. The parser knows the difference between a
    docstring and a string that merely happens to be long, so the answer comes from `ast` rather
    than from a pattern."""
    saida = []
    if caminho.suffix == ".py":
        # `tokenize` and not a split on "#". The first version of this gate split every line on the
        # first "#" and guessed at quoting, which read the `## heading` lines INSIDE the llms.txt
        # template in build/chrome.py as comments — markdown headings in Portuguese content, which
        # is exactly where Portuguese belongs. Same family of mistake as matching docstrings with a
        # regex: the tokenizer already knows what a comment is, so it is asked.
        try:
            for tok in tokenize.generate_tokens(io.StringIO(texto).readline):
                if tok.type == tokenize.COMMENT:
                    saida.append((tok.start[0], tok.string.lstrip("#")))
        except (tokenize.TokenError, IndentationError, SyntaxError):
            pass
        try:
            arvore = ast.parse(texto)
        except SyntaxError:
            return saida
        for no in ast.walk(arvore):
            if not isinstance(no, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            doc = ast.get_docstring(no, clean=False)
            if not doc:
                continue
            primeiro = no.body[0]
            for i, linha in enumerate(doc.split("\n")):
                saida.append((getattr(primeiro, "lineno", 1) + i, linha))
    else:
        for m in re.finditer(r"/\*(.*?)\*/", texto, re.S):
            n = texto[:m.start()].count("\n") + 1
            for i, linha in enumerate(m.group(1).split("\n")):
                saida.append((n + i, linha))
        for n, linha in enumerate(texto.split("\n"), 1):
            m = re.search(r"(?<!:)//(.*)$", linha)
            if m and not re.search(r"https?:$", linha[:m.start()]):
                saida.append((n, m.group(1)))
    return saida


CODIGO = []
for base, padroes in ((ROOT / "build", ("*.py",)),
                      (ROOT / "admin" / "build", ("*.js", "*.mjs")),
                      (ROOT / "assets" / "components", ("*.js",))):
    if base.exists():
        for pad in padroes:
            CODIGO.extend(sorted(base.rglob(pad)))

# THE FILES THIS GATE MAY NOT DEMAND A FIX TO. build/gates.py, build/entregas.py and build/pdf.py
# are in the deny list of .claude/settings.json, so no agent here can edit them — and a gate that
# fails the build over a file the agent is forbidden to touch is not a gate, it is a deadlock. They
# carry Portuguese comments written before the rule was enforced. They are named here rather than
# quietly skipped, counted in the summary line, and they are the editor's to clear: only the editor
# can lift a deny-list entry, and until then this is an honest exemption rather than a hidden one.
DENY_LIST = {"build/gates.py", "build/entregas.py", "build/pdf.py"}
pendentes_do_editor = []

n_codigo, n_linhas_conferidas = 0, 0
for f in CODIGO:
    if "__pycache__" in f.as_posix():
        continue
    if f.relative_to(ROOT).as_posix() in DENY_LIST:
        pendentes_do_editor.append(f.relative_to(ROOT).as_posix())
        continue
    n_codigo += 1
    rel = f.relative_to(ROOT).as_posix()
    achados = []
    for n, linha in _comentarios_de(f, f.read_text(encoding="utf-8")):
        n_linhas_conferidas += 1
        limpo = EXCEPCOES["identificadores"].sub(" ", linha)
        limpo = re.sub(r"`[^`]*`", " ", limpo)          # file names and code between backticks
        # A Portuguese LABEL quoted inside an English sentence is not a Portuguese comment. This
        # repository writes such labels in guillemets — «Esta semana em Lisboa» is the name of a
        # front-page section, and the sentence explaining it is in English. Without this, the gate
        # would demand that an English comment stop naming the Portuguese thing it describes.
        limpo = re.sub(r"«[^»]*»", " ", limpo)
        palavras = set(m.group(0).lower() for m in PT_PALAVRAS.finditer(limpo))
        if len(palavras) >= 2:
            achados.append((n, sorted(palavras)[:4], linha.strip()[:70]))
    if achados:
        n, palavras, amostra = achados[0]
        erros.append(f'{rel}:{n}: comment or docstring is in Portuguese '
                     f'({", ".join(palavras)}) — "{amostra}". CLAUDE.md: code and comments are in '
                     f'English. {len(achados)} line(s) in this file. See '
                     f'docs/guidance/language.md')


# --- 28. every agent that touches this site is named ---------------------------
agentes = carregar("agentes.json")
AGENTES_DIR = ROOT / "agents"
registados = {a["id"] for a in agentes.get("agents", [])}
if not registados:
    erros.append("agents: dados/agentes.json registers nobody. Every agent that may change this "
                 "site is named there, with a ROLE.md and a MANDATE.md")
for a in agentes.get("agents", []):
    for ficheiro in ("ROLE.md", "MANDATE.md"):
        if not (AGENTES_DIR / a["id"] / ficheiro).exists():
            erros.append(f'agents/{a["id"]}: registered in dados/agentes.json and has no '
                         f'{ficheiro}. A named agent without a written mandate is a name, not a '
                         f'boundary')
if AGENTES_DIR.exists():
    for d in sorted(p for p in AGENTES_DIR.iterdir() if p.is_dir()):
        if d.name not in registados:
            erros.append(f'agents/{d.name}/ exists on disk and is not in dados/agentes.json — an '
                         f'unregistered mandate is one no gate can check')
for f in sorted(RUNS.glob("*.json")) if RUNS.exists() else []:
    r = json.loads(f.read_text(encoding="utf-8"))
    quem = r.get("agente")
    if quem and quem not in registados:
        erros.append(f'runs: {f.name} names the agent «{quem}», which is not in '
                     f'dados/agentes.json')


# --- relatório -----------------------------------------------------------------
if erros:
    print(f"gates 16-28: {len(erros)} error(s)")
    for x in erros:
        print("  ✗", x)
    sys.exit(1)

pub = sum(1 for m in metas
          if json.loads(m.read_text(encoding="utf-8")).get("estado") == "publicado")
com_prosa = sum(1 for m in metas if (m.parent / "artigo.md").exists())
print(f"gates 16-28: OK — {len(metas)} articles in dated folders "
      f"({com_prosa} with prose, {pub} published), every path agreeing with its date and slug, "
      f"every claim walking back to the register, {len(AS_OITO)} sections with an editorial "
      f"record, a back office in English citing no evidence, "
      f"{len(ents)} entities with a page and a checked ground, "
      f"{n_comentarios} agent comments each walking back to a file, "
      f"{n_runs} run records with their boundary checked, "
      f"{n_codigo} code files in English "
      f"({len(pendentes_do_editor)} exempt as deny-listed: "
      f"{', '.join(pendentes_do_editor) or 'none'}), "
      f"{len(registados)} named agents with a written mandate")

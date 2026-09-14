#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — os portões da secção.

    python3 build/gates.py

Corre antes do portão do site (`node admin/build/validate.js`), que esta publicação também tem de
passar. A regra herdada é a que importa: **um portão que falha é respondido, nunca silenciado.**

Os portões 1 a 8 vêm de `portugal/build/gates.py` e cobrem o que faz esta publicação diferente de
um blogue com notas de rodapé: prova de que a ancoragem é real, e prova de que não se está a dizer
sobre uma pessoa nada que nenhuma fonte sustente.

Os portões 9 a 13 são deste site e três deles são exigidos pelo resumo de comissionamento:

  9  · O PORTÃO DOS ACENTOS. O corpus de onde este método vem impõe ASCII puro, e o português não
       é uma língua ASCII. Este portão corre ao contrário: assere que os acentos estão PRESENTES e
       que vieram da fonte congelada, e não de uma lista que alguém escreveu.
  10 · O PORTÃO DO CAMINHO PORTUGUÊS. Cada verbo tem uma leitura, cada leitura é uma frase, e
       nenhuma leitura que toca numa Pessoa usa um particípio concordado em género.
  11 · A LINHA DO EDITOR. Só o editor de registo põe uma história em «publicado».
  12 · A FRONTEIRA ENTRE DEPARTAMENTOS. Um departamento só escreve na sua própria pasta.
  13 · A QUARENTENA DAS ENTREGAS. Nada de uma entrega de investigação aparece numa página de
       leitura enquanto o editor não a aprovar.
"""
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
CONGELADAS = ROOT / "fontes" / "congeladas"

erros = []


def carregar(n):
    f = DADOS / n
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


registo = carregar("registo.json")
pessoas = carregar("pessoas.json")
orgs = carregar("organizacoes.json")
sessoes = carregar("sessoes.json")
temas = carregar("temas.json")
lexico = carregar("lexico.json")
mudancas = carregar("mudancas.json")
grafo = carregar("grafo.json")
ontologia = carregar("ontologia.json")
aviso = carregar("aviso.json")
equipa = carregar("equipa.json")
historias = carregar("historias.json")
entregas = carregar("entregas.json")

# As nossas páginas geradas. As cópias congeladas são bytes de outras pessoas guardados como
# prova — não têm nem terão bloco de agente, e conferi-las contra as regras desta casa seria
# conferir a coisa errada.
paginas = sorted(p for p in ROOT.rglob("*.html")
                 if "fontes/congeladas/" not in p.as_posix()
                 and "/briefs/" not in p.as_posix()
                 and "/node_modules/" not in p.as_posix())
por_id = {s["id"]: s for s in registo["fontes"]}


# --- 1. cada ficheiro congelado existe e ainda hasheia para o que o registo diz ---
# É o portão de que tudo o resto depende. Se uma cópia congelada foi editada, movida ou perdida,
# todas as afirmações que assentam nela ficam sem suporte e a construção não pode seguir.
for s in registo["fontes"]:
    f = ROOT / s["congelada"]
    if not f.exists():
        erros.append(f'registo: {s["id"]} nomeia uma cópia congelada que não existe: {s["congelada"]}')
        continue
    real = hashlib.sha256(f.read_bytes()).hexdigest()
    if real != s["sha256"]:
        erros.append(f'registo: {s["congelada"]} já não hasheia para o SHA-256 registado '
                     f'(registado {s["sha256"][:16]}…, real {real[:16]}…) — a cópia congelada foi '
                     f'modificada, o que quebra todas as afirmações que assentam nela')
    if s["estado"] != "primaria":
        erros.append(f'registo: {s["id"]} não é primária — nesta redação cada fonte é uma cópia '
                     f'de bytes que temos em mãos, por isso qualquer outra coisa é um erro do extractor')

# --- 2. nenhuma cópia congelada é servida como página deste site ---------------
for f in CONGELADAS.rglob("*.html") if CONGELADAS.exists() else []:
    erros.append(f'fontes: {f.relative_to(ROOT)} tem extensão .html — as cópias congeladas são '
                 f'prova e não páginas deste site; a extensão .snapshot é o que as impede de '
                 f'serem servidas e indexadas')

# --- 3. cada pessoa e cada organização anda para trás até uma fonte que existe ---
ids_pessoas = {p["id"] for p in pessoas["pessoas"]}
for p in pessoas["pessoas"]:
    for campo in ("id", "nome", "papel", "organizacao", "pagina"):
        if not p.get(campo):
            erros.append(f'pessoas: {p.get("id", "?")} não tem o campo obrigatório «{campo}»')
    if p.get("pagina") and not p["pagina"].startswith("https://startupsummit.io/speakers/"):
        erros.append(f'pessoas: {p["id"]} tem uma página de origem fora do espaço de nomes da fonte')

conhecidas = {o["id"] for o in orgs["organizacoes"]}


def ident(nome):
    base = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "sem-nome"


derivadas = set()
for o in orgs["organizacoes"]:
    for pid in o["pessoas"]:
        derivadas.add(pid)
        if pid not in ids_pessoas:
            erros.append(f'organizacoes: «{o["id"]}» reclama a pessoa «{pid}», que não está em pessoas.json')
if derivadas != {p["id"] for p in pessoas["pessoas"] if p.get("organizacao")}:
    erros.append("organizacoes: o índice derivado não cobre exatamente as pessoas que levam uma "
                 "organização — foi editado à mão em vez de derivado")

# --- 4. um alvo nunca é relatado como resultado --------------------------------
# «150+ speakers» é um plano. Relatá-lo como presença é a forma mais comum de uma antevisão de
# evento correr mal, e é uma recusa de toda a publicação.
ALVO = [
    r"\b150\+?\s*(?:oradores|oradoras|speakers)\s+(?:confirmad|vão|estão|estiveram)",
    r"\b(?:mais de|acima de)\s*150\s*oradores\b",
    r"\b40\+?\s*pa[ií]ses\b(?!.{0,80}(?:declara|afirma|não (?:se )?(?:pode|consegue)|alvo))",
    r"\b2\.?000\+?\s*(?:fundadores|participantes)\s+(?:estiveram|participaram)\b",
]
for p in paginas:
    t = " ".join(p.read_text(encoding="utf-8").split())
    for padrao in ALVO:
        m = re.search(padrao, t, re.I)
        if m:
            erros.append(f'{p.relative_to(ROOT)}: «{m.group(0)}» relata um alvo como resultado')

# --- 5. nenhum contacto de pessoa singular em ficheiro de dados nenhum ----------
# O artigo 24.º, n.º 4, da Lei n.º 58/2019 proíbe a divulgação de moradas e contactos de pessoas
# singulares que não sejam já geralmente conhecidos. A recusa corre onde os dados são LIDOS
# (build/extract.py); este portão é a segunda linha e corre contra o JSON, não contra as páginas.
CONTACTO = {
    "correio eletrónico": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "telefone": re.compile(r"\+\d[\d ()‑-]{7,}\d"),
    "morada": re.compile(r"\b(?:Rua|Avenida|Av\.|Travessa|Largo|Praceta|Estrada)\s+[A-Z]"),
}
# aviso.json e equipa.json nomeiam o contacto do RESPONSÁVEL: é a via de oposição e tem de existir,
# ou o aviso aponta para ninguém. É a única exceção e é nominal.
PESSOAIS = ["pessoas.json", "organizacoes.json", "mudancas.json", "temas.json", "grafo.json",
            "sessoes.json", "historias.json"]
for nome in PESSOAIS:
    f = DADOS / nome
    if not f.exists():
        continue
    texto = f.read_text(encoding="utf-8")
    for especie, padrao in CONTACTO.items():
        m = padrao.search(texto)
        if m:
            erros.append(f'{nome}: contém o que parece um contacto pessoal ({especie}: '
                         f'«{m.group(0)[:40]}») — os contactos são recusados no momento da leitura, '
                         f'não escondidos no momento da apresentação. Ver a página do aviso')

if not (aviso.get("responsavel") or {}).get("contacto"):
    erros.append("aviso: o responsável não tem contacto — a via de oposição não chega a ninguém")
if aviso["fundamento"]["base"].lower() != "interesses legítimos":
    erros.append("aviso: o fundamento mudou; as páginas e o teste de ponderação dizem interesses "
                 "legítimos, e a via jornalística é expressamente não invocada")

# --- 6. nenhuma biografia reproduzida ------------------------------------------
for p in pessoas["pessoas"]:
    for k, v in p.items():
        if isinstance(v, str) and len(v) > 160:
            erros.append(f'pessoas: {p["id"]}, campo «{k}», tem {len(v)} caracteres — as biografias '
                         f'são ligadas e nunca reproduzidas, e nada num nó devia ser tão longo')
for linha in temas["pessoas"]:
    for t in linha["temas"]:
        if len(t) > 90:
            erros.append(f'temas: {linha["id"]} tem um tema de {len(t)} caracteres — um tema é uma '
                         f'etiqueta, não uma frase')
    for tg in linha["etiquetas"]:
        if len(tg.get("correspondeu", "")) > 40:
            erros.append(f'temas: {linha["id"]}, etiqueta {tg["etiqueta"]}, leva '
                         f'{len(tg["correspondeu"])} caracteres correspondidos — leva as palavras, '
                         f'nunca a frase')

# --- 7. nenhuma razão para uma saída -------------------------------------------
# Um nome que sai de uma lista publicada tem explicações inocentes indistinguíveis de fora.
# Atribuir-lhe um motivo com esta prova seria a coisa mais danosa que esta publicação podia fazer.
MOTIVO = re.compile(
    r"\b(desistiu|desistiram|retirou-se|retiraram-se|foi retirad[ao]|cancelou|cancelaram|"
    r"abandonou|abandonaram|demitiu-se|despedid[ao]|expulso|foi afastad[ao]|zangou-se|"
    r"withdrew|withdrawn|pulled out|dropped out)\b", re.I)
for c in mudancas["mudancas"]:
    if c.get("razao_conhecida"):
        erros.append(f'mudancas: {c["de"]}->{c["para"]} reclama uma razão conhecida; nenhuma fonte a declara')
    for r in c["sairam"]:
        if r.get("razao") or r.get("porque"):
            erros.append(f'mudancas: está registada uma razão para a saída de {r["nome"]} — a fonte '
                         f'não declara nenhuma e esta publicação não adivinha')
for p in paginas:
    t = p.read_text(encoding="utf-8")
    m = MOTIVO.search(t)
    if m:
        # a página do aviso e a do método NOMEIAM estas palavras para as proibir
        if p.name == "index.html" and p.parent.name in ("aviso", "metodo", "sobre"):
            continue
        erros.append(f'{p.relative_to(ROOT)}: usa «{m.group(0)}» — esta publicação publica a '
                     f'diferença e deixa a razão em branco; essa palavra implica uma')

# --- 8. as etiquetas derivadas voltam a derivar --------------------------------
# Cada etiqueta é um padrão do léxico que correspondeu ao texto de uma página congelada. Corre-se o
# padrão outra vez sobre os bytes: sem correspondência, sem aresta. E ao contrário também — um
# padrão que corresponde e não tem aresta seria uma etiqueta deixada de fora à mão.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract as EX  # noqa: E402

LEX = {x["id"]: x for x in lexico["entradas"]}
ultima = registo["capturas"][-1]
for linha in temas["pessoas"]:
    f = CONGELADAS / ultima / "oradores" / f'{linha["id"]}.snapshot'
    if not f.exists():
        if linha["etiquetas"]:
            erros.append(f'etiquetas: {linha["id"]} tem etiquetas e não tem página congelada')
        continue
    bio = EX.bloco_bio(f)
    tem = {t["etiqueta"] for t in linha["etiquetas"]}
    for lid, entrada in LEX.items():
        corresponde = bool(re.search(entrada["padrao"], bio, re.I))
        if corresponde and lid not in tem:
            erros.append(f'etiquetas: o léxico «{lid}» corresponde a {linha["id"]} e não há '
                         f'etiqueta — uma etiqueta deixada de fora à mão')
        if not corresponde and lid in tem:
            erros.append(f'etiquetas: o léxico «{lid}» já não corresponde a {linha["id"]} — a '
                         f'etiqueta seria inventada')

# --- 9. O PORTÃO DOS ACENTOS ---------------------------------------------------
# Este site inverte a regra ASCII do corpus. Um nome acentuado tem de chegar acentuado, e o acento
# tem de vir dos BYTES congelados, não de uma lista que alguém escreveu. A falha que este portão
# apanha é silenciosa por natureza: «Gaudencio» em vez de «Gaudêncio» não parece avariado.
def tem_acento(s):
    return any(ord(c) > 127 for c in s)


# CADA nome é conferido contra os bytes, e não apenas os que ainda levam um acento. Conferir só os
# acentuados seria o erro exato que este portão existe para apanhar: um nome a que alguém tirou o
# acento deixa de ter acento, logo deixaria de ser conferido, logo passaria. Foi assim que este
# portão falhou o seu primeiro teste de injeção, e é por isso que o laço não tem esse atalho.
acentuados = 0
f_oradores = CONGELADAS / ultima / "oradores.snapshot"
if not f_oradores.exists():
    erros.append("acentos: não há cópia congelada da lista de oradores para verificar os nomes")
else:
    import html as _html
    texto_fonte = _html.unescape(f_oradores.read_text(encoding="utf-8", errors="replace"))
    for p in pessoas["pessoas"]:
        nome = p["nome"]
        if tem_acento(nome):
            acentuados += 1
        if nome not in texto_fonte:
            nu = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
            pista = ""
            if nu != nome and nu in texto_fonte:
                pista = " — a fonte escreve-o SEM acentos e o ficheiro escreve-o com; foi acrescentado"
            elif any(unicodedata.normalize("NFKD", o).encode("ascii", "ignore").decode() == nu
                     for o in re.findall(r"<h3[^>]*>([^<]+)</h3>", texto_fonte)):
                pista = (" — a fonte escreve-o COM acentos e o ficheiro escreve-o sem; foi "
                         "normalizado, transliterado ou escrito à mão")
            erros.append(f'acentos: «{nome}» não aparece assim escrito na cópia congelada{pista}. '
                         f'Este site assere o contrário da regra ASCII do corpus: os nomes vêm dos '
                         f'bytes da fonte, com os acentos que a fonte lhes deu')
if pessoas["contagem"] and acentuados == 0:
    erros.append("acentos: nenhum dos nomes extraídos leva um acento. Numa lista portuguesa isso é "
                 "quase certamente a fonte a ser lida com a codificação errada, ou um passo de "
                 "normalização que ninguém queria. Este portão corre ao contrário do do corpus de "
                 "propósito")
for n in grafo["nos"]:
    if unicodedata.normalize("NFC", n["rotulo"]) != n["rotulo"]:
        erros.append(f'acentos: o rótulo do nó {n["id"]} não está em NFC — duas formas do mesmo '
                     f'nome deixariam de coincidir numa comparação de texto')

# --- 10. O PORTÃO DO CAMINHO PORTUGUÊS -----------------------------------------
# Cada verbo lê-se como uma frase, e nenhuma leitura que toca numa Pessoa usa um particípio
# concordado: este site não sabe o género de ninguém, a fonte não o publica, e deduzi-lo de um
# nome seria uma inferência sobre uma pessoa nomeada, que o aviso recusa.
PARTICIPIO_APOS_SUJEITO = re.compile(
    r"\{s\}\s+(?:é|está|foi|era|fica)\s+\w+(?:ado|ada|ados|adas|ido|ida|idos|idas)\b")
PARTICIPIO_APOS_OBJECTO = re.compile(
    r"\{t\}\s+(?:é|está|foi|era|fica)\s+\w+(?:ado|ada|ados|adas|ido|ida|idos|idas)\b")
verbos = {a["verbo"] for a in ontologia["arestas"]}
inversos = {a["inverso"] for a in ontologia["arestas"]}
proibidos = {b["verbo"] for b in ontologia["proibidos"]}
tipos = {t["id"] for t in ontologia["tipos"]}
for a in ontologia["arestas"]:
    if a["verbo"] == a["inverso"]:
        erros.append(f'ontologia: «{a["verbo"]}» é o seu próprio inverso — as arestas simétricas '
                     f'são proibidas porque não se podem percorrer')
    if a["verbo"] in proibidos:
        erros.append(f'ontologia: «{a["verbo"]}» está declarado e proibido ao mesmo tempo')
    for chave in ("leitura", "leitura_inversa"):
        frase = a[chave]
        if "{s}" not in frase or "{t}" not in frase:
            erros.append(f'ontologia: a {chave} de «{a["verbo"]}» não usa os dois lados da aresta — '
                         f'não é um caminho que se possa ler')
        if len(frase.split()) < 3:
            erros.append(f'ontologia: a {chave} de «{a["verbo"]}» não é uma frase')
    if a["dominio"] == "Pessoa" and PARTICIPIO_APOS_SUJEITO.search(a["leitura"]):
        erros.append(f'ontologia: a leitura de «{a["verbo"]}» concorda um particípio com uma Pessoa '
                     f'(«{a["leitura"]}»). O género de uma pessoa nomeada não é publicado pela '
                     f'fonte e não é deduzido daqui: a leitura tem de ser invariável')
    if a["alcance"] == "Pessoa" and PARTICIPIO_APOS_OBJECTO.search(a["leitura_inversa"]):
        erros.append(f'ontologia: a leitura inversa de «{a["verbo"]}» concorda um particípio com '
                     f'uma Pessoa («{a["leitura_inversa"]}») — tem de ser invariável')
    if a["dominio"] not in tipos or a["alcance"] not in tipos:
        erros.append(f'ontologia: «{a["verbo"]}» tem um domínio ou alcance que não é um tipo declarado')
    if not a.get("en", {}).get("verbo"):
        erros.append(f'ontologia: «{a["verbo"]}» não tem anotação em inglês')

nos_por_id = {n["id"]: n for n in grafo["nos"]}
dominio_alcance = {(a["verbo"], a["dominio"], a["alcance"]) for a in ontologia["arestas"]}
for n in grafo["nos"]:
    if n["tipo"] not in tipos:
        erros.append(f'grafo: o nó {n["id"]} tem o tipo desconhecido «{n["tipo"]}»')
    if not n.get("fonte"):
        erros.append(f'grafo: o nó {n["id"]} não nomeia fonte nenhuma — um nó sem caminho de volta '
                     f'aos bytes é um desenho')
    elif n["fonte"] not in por_id:
        erros.append(f'grafo: o nó {n["id"]} nomeia a fonte «{n["fonte"]}», que não está no registo')
for a in grafo["arestas"]:
    if a["verbo"] in proibidos:
        erros.append(f'grafo: o verbo proibido «{a["verbo"]}» está em uso')
    elif a["verbo"] not in verbos:
        pista = " (isso é um inverso; as arestas guardam-se para a frente)" if a["verbo"] in inversos else ""
        erros.append(f'grafo: o verbo «{a["verbo"]}» não está na ontologia{pista}')
    if a["origem"] not in nos_por_id or a["destino"] not in nos_por_id:
        erros.append(f'grafo: a aresta {a["id"]} tem uma ponta que não é um nó')
    elif a["verbo"] in verbos and (a["verbo"], nos_por_id[a["origem"]]["tipo"],
                                   nos_por_id[a["destino"]]["tipo"]) not in dominio_alcance:
        erros.append(f'grafo: {a["verbo"]} de {nos_por_id[a["origem"]]["tipo"]} para '
                     f'{nos_por_id[a["destino"]]["tipo"]} está fora do domínio/alcance declarado')
if grafo["contagens"]["nos"] != len(grafo["nos"]) or grafo["contagens"]["arestas"] != len(grafo["arestas"]):
    erros.append("grafo: as contagens não batem certo com as listas")
for b in grafo["blocos"]:
    if b["nos"] != sum(1 for n in grafo["nos"] if n["bloco"] == b["id"]):
        erros.append(f'grafo: a contagem do bloco «{b["id"]}» está desactualizada')

# cada pessoa do grafo está na lista publicada, ou está marcada como já não listada
for n in grafo["nos"]:
    if n["tipo"] != "Pessoa":
        continue
    if n["id"].split(":", 1)[1] not in ids_pessoas and not n.get("ja_nao_listado"):
        erros.append(f'grafo: {n["id"]} não está na lista publicada e não está marcado como já não listado')
    if n.get("ja_nao_listado") and n.get("razao") is not None:
        erros.append(f'grafo: {n["id"]} leva uma razão para ter saído da lista — a fonte não declara nenhuma')

# --- 11. A LINHA DO EDITOR -----------------------------------------------------
# Só o editor de registo põe uma história em «publicado». Uma execução automática que o escrevesse
# falharia aqui, e é a única salvaguarda que separa esta publicação de um gerador de texto.
ed = (equipa.get("editor_de_registo") or {}).get("nome")
if not ed:
    erros.append("equipa: não há editor de registo nomeado, mas as páginas reclamam um")
if equipa.get("humano_no_circuito") is not True:
    erros.append("equipa: humano_no_circuito tem de ser verdadeiro — cada página diz que um editor "
                 "de registo nomeado lê antes de publicar")
for h in (historias or {}).get("historias", []):
    if h["estado"] == "publicado":
        if not h.get("publicado_por"):
            erros.append(f'historias: «{h["slug"]}» está publicada e não diz quem a publicou — só o '
                         f'editor de registo o pode fazer, e tem de ficar escrito')
        elif h["publicado_por"] != ed:
            erros.append(f'historias: «{h["slug"]}» foi publicada por «{h["publicado_por"]}», que '
                         f'não é o editor de registo')
        if not h.get("publicado_em"):
            erros.append(f'historias: «{h["slug"]}» está publicada e não tem data')
    for sid in h.get("assenta_em", []):
        if sid not in por_id:
            erros.append(f'historias: «{h["slug"]}» assenta em «{sid}», que não está no registo')

# --- 12. A FRONTEIRA ENTRE DEPARTAMENTOS ---------------------------------------
# Um departamento só altera ficheiros na sua própria pasta. O registo de execução lista o que
# mudou, por pasta; este portão falha uma execução que atravessou uma linha. É o que faz disto uma
# redação e não um script.
PASTAS = {
    "pesquisa": ["fontes/congeladas/", "dados/"],
    "redacao": ["conteudo/"],
    "verificacao": ["dados/verificacoes/"],
    "editor": ["redacao/decisoes/", "redacao/revisoes/", "conteudo/"],
}
runs = sorted((ROOT / "redacao" / "runs").glob("*.json")) if (ROOT / "redacao" / "runs").exists() else []
for f in runs:
    r = json.loads(f.read_text(encoding="utf-8"))
    dep = r.get("departamento")
    if not dep:
        continue           # a sessão de arranque cria tudo e é a única que o pode fazer
    permitidas = PASTAS.get(dep)
    if permitidas is None:
        erros.append(f'runs: {f.name} declara o departamento «{dep}», que não existe')
        continue
    for pasta in r.get("pastas_alteradas", []):
        if not any(pasta.startswith(x) for x in permitidas + ["redacao/runs/", "redacao/correio/"]):
            erros.append(f'runs: {f.name} — {dep} alterou «{pasta}», que não é sua. A pesquisa não '
                         f'escreve prosa e a redação não toca numa fonte')
    if r.get("portoes") is False and r.get("versao"):
        erros.append(f'runs: {f.name} publicou a versão {r["versao"]} com os portões vermelhos')

# --- 13. A QUARENTENA DAS ENTREGAS ---------------------------------------------
# Uma entrega de investigação é uma lista de pistas com proveniência, nunca factos. Nada dela pode
# aparecer numa página de leitura — a primeira página, uma secção, um artigo — enquanto o editor de
# registo não a tiver aprovado, afirmação a afirmação. As páginas de /entregas/ são o sítio onde a
# entrega é mostrada COM o seu estado, e por isso são a exceção.
LEITURA = [p for p in paginas
           if "/entregas/" not in p.as_posix()
           and "/redacao/" not in p.as_posix()
           and "/admin/" not in p.as_posix()]
if entregas:
    for x in entregas["entregas"]:
        rev = x.get("revisao") or {}
        aprovados = {k for k, v in (rev.get("itens") or {}).items() if v.get("estado") == "aprovada"}
        for it in x["itens"]:
            if it["id"] in aprovados:
                continue
            agulha = it["titulo"][:60]
            for p in LEITURA:
                if agulha and agulha in p.read_text(encoding="utf-8"):
                    erros.append(
                        f'{p.relative_to(ROOT)}: mostra o item «{it["id"]}» da entrega '
                        f'{x["id"]}, que o editor de registo ainda não aprovou. Uma entrega é uma '
                        f'lista de pistas: só passa a facto depois de o excerto estar nos bytes E '
                        f'de o editor a aprovar')
            for a in it["afirmacoes"]:
                if a["estado"] in ("nao_encontrada", "fonte_inacessivel") and \
                        a.get("estado_publicado") == "publicado":
                    erros.append(f'entregas: {a["id"]} está marcada para publicação e o excerto não '
                                 f'está nos bytes')

# --- 14. cada página que nomeia pessoas liga para o aviso ----------------------
# Um aviso que ninguém consegue encontrar a partir da página que o nomeou não é uma medida, é um
# ficheiro. O artigo 14.º, n.º 5, alínea b), ganha-se tornando a informação encontrável.
for p in paginas:
    t = p.read_text(encoding="utf-8")
    nomeia = any(pp["nome"] in t for pp in pessoas["pessoas"][:200])
    if nomeia and "aviso/" not in t:
        erros.append(f'{p.relative_to(ROOT)}: nomeia pessoas e não liga para o aviso de proteção '
                     f'de dados')
if not (ROOT / "aviso" / "index.html").exists():
    erros.append("secção: o aviso não foi gerado, e há páginas que nomeiam pessoas")

# --- 15. os títulos de sessão são os da agenda congelada, verbatim -------------
agenda = CONGELADAS / ultima / "agenda.snapshot"
if agenda.exists():
    corpo = EX.recuo_estatico(agenda)
    texto_agenda = " ".join(re.sub(r"<[^>]+>", " ", corpo).split())
    import html as _h
    texto_agenda = " ".join(_h.unescape(texto_agenda).split())
    for s in sessoes["sessoes"]:
        if s["titulo"] not in texto_agenda:
            erros.append(f'sessoes: «{s["titulo"]}» não está na agenda congelada verbatim — o '
                         f'título foi alterado algures entre os bytes e o ficheiro')
else:
    erros.append(f"sessoes: falta a cópia congelada da agenda ({agenda})")

# --- relatório -----------------------------------------------------------------
if erros:
    print(f"portões: {len(erros)} erro(s)")
    for x in erros:
        print("  ✗", x)
    sys.exit(1)

n_ent = sum(x["contagens"]["afirmacoes"] for x in entregas["entregas"]) if entregas else 0
n_apr = sum(len([1 for v in (x["revisao"].get("itens") or {}).values()
                 if v.get("estado") == "aprovada"]) for x in entregas["entregas"]) if entregas else 0
print(f"portões: OK — {len(paginas)} páginas, {registo['contagem']} ficheiros congelados de "
      f"{len(registo['capturas'])} captura(s), cada SHA-256 reverificado, "
      f"{pessoas['contagem']} pessoas / {orgs['contagem']} organizações, "
      f"{grafo['contagens']['nos']} nós / {grafo['contagens']['arestas']} arestas, "
      f"{len(ontologia['arestas'])} verbos portugueses todos com leitura, "
      f"{acentuados} nomes acentuados conferidos contra os bytes, "
      f"{n_ent} afirmações entregues e {n_apr} itens aprovados pelo editor, "
      f"editor de registo {ed} em cada página")

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
"""
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
      f"registo editorial, bastidores em inglês sem citar prova")

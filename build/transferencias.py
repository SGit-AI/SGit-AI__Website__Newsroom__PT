#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — evidence transferred from a sibling publication, kept as its evidence.

    python3 build/transferencias.py     # after extract.py, before graph.py

WHAT A TRANSFER IS, AND THE ONE THING THAT MUST NOT HAPPEN TO IT.

newsroom.sgit.ai froze fourteen files — two Startup Summit captures from 8 and 13 September, and
three press pages — and offered them to this publication as evidence. Its own memo states the rule
that comes with them, and the rule is the whole point:

    Evidence transferred between sibling publications stays evidence, as long as the provenance
    travels with it and is published. The bytes were frozen by THAT site's fetcher, with its
    user-agent, at the times in ITS register. Entering them anywhere as the receiving
    publication's own captures would make its method quietly untrue — the one failure mode that
    does not look broken.

So this pass does NOT write into `dados/registo.json`. The register is the record of what THIS
newsroom fetched, and a transferred file was not fetched by this newsroom. It writes a separate
record, `dados/transferencias.json`, whose every entry carries `obtido_por`, `obtido_em`, the id in
the source register, and the version of the site that froze it. On a page the phrase is «captura de
8 de setembro, obtida por newsroom.sgit.ai» — never «a nossa captura de 8 de setembro».

WHAT IS VERIFIED HERE, AND WHY IT IS THE ONLY THING WORTH TRUSTING

Every SHA-256 in the incoming manifest is recomputed from the bytes on disk. That check is the only
thing in a transfer that does not require trusting anybody: if the hash matches, the file is the
file the sending register describes, whoever sent it. A transfer with one bad hash is refused
whole — a half-accepted bundle is worse than none, because nobody can say afterwards which half.

TWO OBSERVATIONS THIS PASS RECORDS RATHER THAN SMOOTHS OVER

Both are facts about the bundle, found by reading it, and both are published in the record:

  1. Every file in `capturas/2026-09-08/` carries `obtido_em: 2026-09-13T19:44:22Z` — the same
     instant, and three minutes AFTER the 13 September capture was fetched. The capture date comes
     from the folder name and from `id_no_registo_de_origem`, not from that timestamp. Both are
     recorded and neither is reconciled: inferring which one is "really" right would be exactly the
     kind of guess this site refuses.
  2. Four of the five pages have byte counts identical to their 13 September twins. Their hashes
     differ, so they are different files — but the coincidence is recorded, because a reader who
     noticed it deserves to find it already noted rather than to wonder.
"""
import hashlib
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
TRANSFERIDAS = ROOT / "fontes" / "transferidas"


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    if not TRANSFERIDAS.exists():
        print("transfers: none")
        return

    lotes, total, recusados = [], 0, []
    for pasta in sorted(p for p in TRANSFERIDAS.iterdir() if p.is_dir()):
        man = pasta / "manifesto.json"
        if not man.exists():
            recusados.append(f"{pasta.name}: no manifesto.json — a transfer without a manifest is "
                             f"bytes with no provenance, which is not evidence")
            continue
        m = json.loads(man.read_text(encoding="utf-8"))

        # Every hash, recomputed. This is the only part of a transfer that requires trusting nobody.
        ficheiros, maus = [], []
        for f in m.get("ficheiros", []):
            alvo = pasta / f["ficheiro"]
            if not alvo.exists():
                maus.append((f["ficheiro"], "missing"))
                continue
            real = sha256(alvo)
            if real != f["sha256"]:
                maus.append((f["ficheiro"], f'{f["sha256"][:12]}… != {real[:12]}…'))
                continue
            ficheiros.append({
                "ficheiro": f["ficheiro"],
                "caminho": (alvo.relative_to(ROOT)).as_posix(),
                "sha256": f["sha256"],
                "bytes": f["bytes"],
                "url": f.get("url"),
                "editor_da_pagina": f.get("editor_da_pagina"),
                "obtido_por": f.get("obtido_por"),
                "obtido_em": f.get("obtido_em"),
                "id_no_registo_de_origem": f.get("id_no_registo_de_origem"),
                "versao_do_site_de_origem": f.get("versao_do_site_de_origem"),
            })
        if maus:
            # All or nothing. A half-accepted bundle is worse than none: afterwards nobody can say
            # which half was accepted, and the provenance stops meaning anything.
            recusados.append(f"{pasta.name}: {len(maus)} hash(es) do not match — the whole bundle "
                             f"is refused: {maus[:3]}")
            continue

        # The two observations, computed rather than asserted.
        por_data = {}
        for f in ficheiros:
            mm = re.match(r"capturas/(\d{4}-\d{2}-\d{2})/", f["ficheiro"])
            if mm:
                por_data.setdefault(mm.group(1), []).append(f)
        observacoes = []
        for data, fs in sorted(por_data.items()):
            horas = {f["obtido_em"] for f in fs if f["obtido_em"]}
            if len(horas) == 1 and not next(iter(horas)).startswith(data):
                observacoes.append({
                    "id": f"hora-de-obtencao-{data}",
                    "o_que": (f"Todos os {len(fs)} ficheiros da captura de {data} trazem a mesma "
                              f"hora de obtenção, {sorted(horas)[0]}, que é de outro dia."),
                    "como_e_registado": ("A data da captura vem do nome da pasta e do "
                                         "`id_no_registo_de_origem`; a hora vem do manifesto. As "
                                         "duas ficam registadas e não são reconciliadas — decidir "
                                         "qual delas está «realmente» certa seria uma inferência "
                                         "nossa sobre o registo de outra publicação."),
                })
        tamanhos = {}
        for f in ficheiros:
            tamanhos.setdefault(f["bytes"], []).append(f["ficheiro"])
        iguais = {b: v for b, v in tamanhos.items() if len(v) > 1}
        if iguais:
            observacoes.append({
                "id": "bytes-coincidentes",
                "o_que": (f"{len(iguais)} pares de ficheiros têm exatamente o mesmo número de "
                          f"bytes em capturas diferentes."),
                "como_e_registado": ("Os SHA-256 diferem, logo são ficheiros diferentes. A "
                                     "coincidência fica registada porque um leitor que reparasse "
                                     "nela merece encontrá-la já notada em vez de ficar na "
                                     "dúvida."),
                "pares": {str(b): v for b, v in sorted(iguais.items())},
            })

        lotes.append({
            "id": pasta.name,
            "de": m.get("de"),
            "para": m.get("para"),
            "data_do_pacote": m.get("data"),
            "versao_do_pacote": m.get("versao"),
            "o_que_e": m.get("o_que_e"),
            "a_regra": m.get("a_regra"),
            "leia_me": (pasta / "LEIA-ME.md").relative_to(ROOT).as_posix()
                       if (pasta / "LEIA-ME.md").exists() else None,
            "contagem": len(ficheiros),
            "hashes_reverificados": True,
            "observacoes": observacoes,
            "ficheiros": ficheiros,
        })
        total += len(ficheiros)

    doc = {
        "id": "pt-transferencias", "versao": "1.0.0",
        "atualizado": json.loads((DADOS / "registo.json").read_text(encoding="utf-8"))
                      .get("atualizado", time.strftime("%Y-%m-%d")),
        "o_que_e": ("Prova congelada por OUTRA publicação e oferecida a esta. NÃO está no registo "
                    "desta redação e não deve ser tratada como se estivesse: o registo é o que "
                    "ESTA redação obteve, e estes ficheiros foram obtidos por outra, com o "
                    "user-agent dela, às horas do registo dela."),
        "a_regra": ("Prova transferida entre publicações irmãs continua a ser prova, desde que a "
                    "proveniência viaje com ela e seja publicada. Numa página diz-se «captura de 8 "
                    "de setembro, obtida por newsroom.sgit.ai» — nunca «a nossa captura de 8 de "
                    "setembro»."),
        "o_que_e_conferido": ("Cada SHA-256 do manifesto recebido é recalculado a partir dos bytes "
                              "em disco. É a única coisa numa transferência que não obriga a "
                              "acreditar em ninguém. Um lote com um hash errado é recusado "
                              "inteiro."),
        "contagem": total,
        "lotes": lotes,
        "recusados": recusados,
    }
    (DADOS / "transferencias.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    obs = sum(len(l["observacoes"]) for l in lotes)
    print(f"transfers: {len(lotes)} bundle(s), {total} files, every hash re-verified, "
          f"{obs} observation(s) recorded, {len(recusados)} refused")


if __name__ == "__main__":
    main()

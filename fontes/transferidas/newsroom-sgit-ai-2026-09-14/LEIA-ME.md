# Transferência: newsroom.sgit.ai → pt.newsroom.sgit.ai

**Bytes congelados por outra publicação, oferecidos como prova.** Empacotado a 14 de setembro de
2026 a partir de newsroom.sgit.ai v0.3.11; o memorando que explica porquê é
[`briefs/14`](https://newsroom.sgit.ai/documents/pt-transfer.html).

## O que está aqui

| Pasta | O quê |
|---|---|
| `capturas/2026-09-08/` | Cinco páginas do Startup Summit Lisbon 2026, congeladas a 8 de setembro. A lista de oradores tinha **60 nomes** |
| `capturas/2026-09-13/` | As mesmas páginas, congeladas a 13 de setembro. A lista tinha **64 nomes** (+5, −1) |
| `imprensa/` | Três páginas de imprensa sobre o evento que o registo de pt.newsroom ainda não tem |
| `manifesto.json` | Cada ficheiro com o seu SHA-256, o URL, quem o obteve, quando, e sob que versão |
| `diferenca-08-13.json` | A diferença entre as duas capturas: quem entrou, quem saiu, e a razão em branco |

## A regra

**Estas capturas não são vossas.** Foram obtidas pelo fetcher de newsroom.sgit.ai, com o
user-agent dele, às horas registadas no registo dele. Se entrarem no vosso registo como se fossem
vossas, o método deixa de ser verdadeiro sem nada parecer avariado.

Por isso cada linha do manifesto traz `obtido_por`, `obtido_em`, `url`, `id_no_registo_de_origem` e
`versao_do_site_de_origem` — e o `sha256` que o registo de origem regista. Confiram-no antes de
aceitar seja o que for: é a única coisa aqui que não obriga a acreditar em ninguém.

**Prova transferida entre publicações irmãs continua a ser prova, desde que a proveniência viaje
com ela e seja publicada.** Numa página: *captura de 8 de setembro, obtida por newsroom.sgit.ai*.

## Conferir

```bash
python3 - <<'PY'
import json, hashlib, pathlib
m = json.load(open('manifesto.json'))
mau = [f['ficheiro'] for f in m['ficheiros']
       if hashlib.sha256(pathlib.Path(f['ficheiro']).read_bytes()).hexdigest() != f['sha256']]
print('ficheiros:', m['contagem'], '| hashes que não batem certo:', mau or 'nenhum')
PY
```

## Limites, que também pertencem à página

- O fetcher desta publicação pode ter visto uma página diferente da que o vosso veria: outro
  user-agent, outra hora.
- A captura de 8 de setembro tem cinco páginas, não as catorze que as vossas capturas trazem.
- Nada aqui prova que as páginas não mudaram *entre* capturas — só que diferiam em três momentos.

Os ficheiros `.snapshot` são bytes de páginas de outras organizações, guardados como prova por
ambas as publicações sob a mesma regra: ligar, nunca republicar como páginas navegáveis. O
manifesto e a diferença são CC BY 4.0.

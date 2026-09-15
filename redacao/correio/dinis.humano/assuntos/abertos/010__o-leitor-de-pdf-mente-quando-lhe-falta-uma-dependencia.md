---
titulo: O leitor de PDF diz que o diploma é digitalizado quando o que lhe falta é uma dependência
aberto: 2026-09-15T11:30:00Z
origem: sessão a-linha-de-publicacao — encontrado ao pôr build/entregas.py no caminho de construção
issue: 005
prioridade: alta
esforco: —
bloqueado_por: build/pdf.py está na lista de recusa; nenhum agente o pode editar
---

## O que há para fazer
Corrigir `build/pdf.py` para que a falta de `pycryptodome` no caminho AESV2 fique registada como
falta de dependência e não como um juízo sobre o documento. Hoje `_aes_cbc` devolve `None`, a
`Cifra` fica com `ok=True` e `porque=None`, e o leitor conclui «é provavelmente um PDF
digitalizado, que precisaria de reconhecimento ótico». O diploma não é digitalizado.

## Porque é que isto importa mais do que parece
O mesmo ficheiro, com o mesmo SHA-256 reverificado pelo portão 1, leu **30 808 caracteres** a 14 de
setembro e **0** a 15 de setembro. Os bytes não mudaram — mudou a máquina. Durante essa passagem,
as duas afirmações da RCM n.º 70/2026 caíram de `confirmada` para `fonte_inacessivel` **com a
construção verde**. Uma prova que depende de quem a lê não é uma prova, e este site é inteiro
construído sobre a promessa contrária.

O caminho do AES-256 já faz isto bem: diz «AES-256 precisa de pycryptodome, que não está
instalado». O do AESV2 cala-se. É uma linha de diferença.

## Como se faz
`build/pdf.py` é seu. Ficam feitas as duas metades que um agente pode fazer:
`requirements.txt` nomeia as duas dependências com a razão de cada uma, e o CI instala-as antes dos
portões. Fica por fazer a que está atrás da lista de recusa — e vale a pena pensar num portão que
leia um PDF conhecido e falhe se ele deixar de dar texto.

## Critério de aceitação
- Sem a dependência, `Cifra.ok` é `False` e a razão nomeia `pycryptodome`.
- Nenhuma afirmação é marcada `fonte_inacessivel` com uma explicação que seja um juízo sobre o
  documento de outra pessoa.

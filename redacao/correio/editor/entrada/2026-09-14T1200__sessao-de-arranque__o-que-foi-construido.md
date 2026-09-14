---
de: sessao-de-arranque
para: editor
assunto: MVP v0.1.0 construído; o que é real, o que não é, e o que precisa da sua decisão
issue: —
run: 2026-09-14T12:00:00Z
quando: 2026-09-14T12:00:00Z
---

O site está construído e os portões estão verdes. O que é real: 92 ficheiros congelados com
SHA-256, um grafo de verbos portugueses onde cada nó nomeia a sua fonte, o aviso de proteção de
dados publicado ANTES da primeira página que nomeia alguém, e o fluxo de revisão de entregas.

O que NÃO é real e está dito em cada página onde importa: nenhuma história publicada, três das
oito secções vazias, e a camada das empresas impossível de completar sem registo comercial aberto.

Precisa de decidir três coisas. Primeira: a entrega do ChatGPT (parte 1/8, políticas) está em
/entregas/ com cada afirmação conferida contra os bytes — 9 confirmadas, 0 não encontradas, 10 sem
fonte legível. Nada dela aparece em lado nenhum público até aprovar item a item. Segunda: a entrega
propõe tipos que a ontologia não tem (Programa, InstrumentoJuridico, Infraestrutura); aceitá-los é
uma alteração de ontologia e leva uma versão. Terceira: a página da ANACOM devolve 403 a esta
redação, e isso não é uma recusa de informação — é um servidor a bloquear um cliente. Pode pedir
acesso.

Uma nota que é um achado e não um detalhe: o Diário da República renderiza por script e devolve 22
caracteres a um leitor automático, mas publica os diplomas em PDF, e esses PDFs são legíveis depois
de decifrados. build/pdf.py faz isso. Foi assim que as duas afirmações sobre a RCM n.º 70/2026
confirmaram. O mesmo caminho resolve provavelmente a história 001.

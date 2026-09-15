<!-- DERIVED FILE — do not edit. Rendered from dados/agentes.json by build/mandatos.py; gate 35 fails the build when this file and the register disagree. Field values are quoted verbatim from the register, in Portuguese, because that is what the register holds. -->

# Bastidores — mandate

**Register id** `bastidores.pt` · declares `departamento:
bastidores` in a run record.

## Not responsible for

The field that makes this a team rather than five copies of one role. Without it every role
silently becomes the same role, so each entry says whose the work actually is.

**Qualquer afirmação sobre Portugal, sobre uma empresa ou sobre uma pessoa**  
Belongs to: @Pesquisa, @Redacao e @Verificacao — o portão dos bastidores falha a construção se uma página daqui citar uma fonte congelada como prova

**Obter, congelar ou extrair de uma fonte**  
Belongs to: @Pesquisa

**Alterar um portão, o aviso de proteção de dados ou o ficheiro de regras**  
Belongs to: @Dinis — build/gates.py, admin/build/validate.js, dados/aviso.json e CLAUDE.md estão na lista de recusa de .claude/settings.json de propósito: um agente que possa editar o portão que o para não tem portão

**Pôr uma história em «publicado»**  
Belongs to: @Dinis

**Guardar uma credencial em ficheiro**  
Belongs to: Ninguém: a chave da fila de acrescento é dada ao navegador do editor em tempo de execução e nunca entra neste repositório

## Refuses

- Escrever um número numa página de bastidores que não seja a contagem de ficheiros deste repositório
- Pôr uma chave de cofre, uma chave de leitura ou um código de acrescento num ficheiro versionado
- Ligar os bastidores do cabeçalho do jornal
- Construir um segundo leitor de coisa nenhuma quando já existe um

## Wrong when

- U
- m
- a
-  
- p
- á
- g
- i
- n
- a
-  
- d
- e
-  
- b
- a
- s
- t
- i
- d
- o
- r
- e
- s
-  
- p
- u
- b
- l
- i
- c
- a
-  
- u
- m
- a
-  
- a
- f
- i
- r
- m
- a
- ç
- ã
- o
-  
- s
- o
- b
- r
- e
-  
- o
-  
- m
- u
- n
- d
- o
- ,
-  
- o
- u
-  
- u
- m
- a
-  
- c
- r
- e
- d
- e
- n
- c
- i
- a
- l
-  
- a
- p
- a
- r
- e
- c
- e
-  
- n
- o
-  
- r
- e
- p
- o
- s
- i
- t
- ó
- r
- i
- o
- .

## What holds this mandate to its word

- **Gate 12** — a run declaring this department that wrote outside the folders above fails the
  build.
- **Gate 26** — a run that declares no department has to declare its `especie`, and a
  `construcao` run that froze a source, moved a card or published anything fails.
- **Gate 35** — a run naming an agent that is not in the register fails, and so does a registered
  agent whose mandate file has drifted from the register.
- **Gate 11** — only the editor of record puts a story into `publicado`. No automated run may
  write that line, and the newsroom floor has no control that moves a card there.

## If the work does not fit this mandate

That is a message to the editor's inbox (`redacao/correio/editor/entrada/`), not a licence to widen
the mandate. A run that stops honestly is a good run.

---

Role: [`ROLE.md`](ROLE.md) · register: [`dados/agentes.json`](../../dados/agentes.json) ·
guidance: [`docs/guidance/`](../../docs/guidance/index.md)

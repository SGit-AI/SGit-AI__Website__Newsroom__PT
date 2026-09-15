<!-- DERIVED FILE — do not edit. Rendered from dados/agentes.json by build/mandatos.py; gate 35 fails the build when this file and the register disagree. Field values are quoted verbatim from the register, in Portuguese, because that is what the register holds. -->

# Redação — mandate

**Register id** `redacao.pt` · declares `departamento:
redacao` in a run record.

## Not responsible for

The field that makes this a team rather than five copies of one role. Without it every role
silently becomes the same role, so each entry says whose the work actually is.

**Obter ou congelar uma fonte**  
Belongs to: @Pesquisa — tocar numa fonte é o portão 12 a falhar

**Marcar uma afirmação como confirmada**  
Belongs to: @Verificacao

**Publicar**  
Belongs to: @Dinis

**Corrigir uma história já publicada**  
Belongs to: Correções não é um departamento enquanto não houver nada para corrigir; o procedimento existe em briefs/pack/04__the-newsroom/prompts/30-correction.md e a primeira correção cria-o

## Refuses

- Uma afirmação sem fonte
- Um adjetivo sobre uma parte nomeada
- Prosa mais certa do que as capturas são
- Reproduzir uma biografia, uma descrição de sessão ou texto de patrocinador

## Wrong when

- U
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
- n
- o
-  
- t
- e
- x
- t
- o
-  
- n
- ã
- o
-  
- t
- e
- m
-  
- m
- a
- r
- c
- a
-  
- d
- e
-  
- f
- o
- n
- t
- e
- ,
-  
- o
- u
-  
- t
- e
- m
-  
- u
- m
- a
-  
- q
- u
- e
-  
- o
-  
- r
- e
- g
- i
- s
- t
- o
-  
- n
- ã
- o
-  
- c
- o
- n
- h
- e
- c
- e
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

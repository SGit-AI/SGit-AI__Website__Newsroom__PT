# 30 — When a source contradicts a published claim

The brief (§14) says the first correction will arrive during the conference if the site works at
all, and that with three departments there is no corrections desk. This is the procedure until
there is one; it is run by the daily run when Verificação finds it, or by the editor by hand.

1. **Do not edit the published story's claim.** Corrections propagate; they do not overwrite.
2. Verificação writes a new verification record for the story with the claim marked `disputada`
   or `nao_encontrada`, naming both frozen sources: the one the claim stood on and the one that
   contradicts it, each with its hash.
3. Redação adds a dated correction block to the story (`correcoes:` in the frontmatter, rendered at
   the top of the article): what was claimed, what the new source says, both links. The original
   sentence stays, marked as superseded from that date.
4. The story's `estado` drops to `verificado`; only the editor returns it to `publicado` after
   reading the correction.
5. The graph gets an edge: `<artigo> corrigido_por <fonte>` / `<fonte> corrige <artigo>`.
6. The run record and the editor's inbox say a correction happened. The front page's *Registo*
   strip counts corrections; the number is never hidden.

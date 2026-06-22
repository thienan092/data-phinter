# Notes — pipeline ↔ app boundaries (context for a future improvement pass)

These are *notes*, not instructions — context to make later work (e.g. with Codex on the app)
easier. Nothing here has to be done; it just records ideas so component boundaries stay clean.

## Why this note exists
While generating SST data via NotebookLM, a `merge_and_coverage.py` script and a
niche-targeting prompt were prototyped. They blurred component boundaries (merge/dedup is the
app's job; hard niche-targeting steers Deep Research), so the drift code was removed. The
useful ideas are parked here.

## Component boundaries (current understanding)
- **Deep Research (NotebookLM core):** researches the web autonomously. Works best un-steered —
  hard-coding specific niches/brands/attributes into the prompt tends to narrow the search and
  create systematic blind spots. General nudges toward diversity/coverage are fine; specific
  impositions are not.
- **NotebookLM generation step (the pipeline):** influences the result through only two levers —
  (1) a representative *exemplar* kept current with the default data file, and (2) an
  appropriate, format-oriented prompt. Its output is the raw CSV of NotebookLM's result.
- **data-phinter app:** the natural home for merge, dedup, verification, and accumulation — the
  "notebook continuously written into and verified by the app".
- **Audits (Codex / future Stranger audit):** assess exemplar-vs-default quality and the coverage
  of results combined with current data. Improving/syncing components to help pass audits is fine
  as general guidance, not specific imposition.

## Idea parked for a possible app-side merge/dedup/accumulate feature
If the app's import/accumulation flow is ever revisited, the removed prototype logic could be a
starting reference (purely optional):
- Dedup incoming rows against current data by product identity (normalized product URL; Shopee by
  `shopid.itemid`).
- Drop incomplete rows (need a full `https` Link + an HTML price snippet/selector + a price).
- Accumulate only novel, complete rows; keep IDs stable across sessions.
- Treat coverage (facets: brand/domain/type/unit/price-tier/region/platform; plus niche presence)
  as something an *audit* measures on the combined set, rather than something the generation
  pipeline forces.

## Operational notes
- NotebookLM **Data Table has a daily quota** (~3/day per account). When exhausted: wait for reset,
  use another signed-in account (`authuser=N`), or extract via Chat.
- `file_upload` of repo files is rejected ("only files shared with session") → use **Copied text**
  to add the exemplar.
- The representative exemplar can be regenerated from the current default file with
  `pipeline/build_exemplar.py` (facet-stratified). Its niche-gap output is *audit information*,
  not prompt input.
- The canonical path of the current default file is declared in `config/default-data.json`.
  App and agent workflows should resolve that configuration instead of assuming
  `sample_data.csv`; ad-hoc files imported by a user do not alter the configured default.
- A completed generation run may update `config/current-candidate.json` to point the app's
  agent-assisted import control at the final candidate artifact. This pointer does not merge,
  verify, or accumulate the candidate data.

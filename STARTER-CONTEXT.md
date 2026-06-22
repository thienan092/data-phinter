# Starter Context: Data Phin-ter

This is the release-safe starting context for a fresh clone. It replaces the maintainer's private
session handoff. Read it with the `read-effective-verbal-context` skill, then reconcile every claim
against the current source, config, tests, and plugin references — do not trust prose over code.

## Objective

Data Phin-ter accumulates a "single source of truth" (SST) dataset of products that each have a
verifiable source link and price, and grows it over time. Generation proposes candidate rows; the app
verifies each claimed price against its live source page, then deduplicates and accumulates approved
rows. The shipped example is a Vietnamese coffee-market dataset (`sample_data.csv`), but the workflow
is domain-agnostic: point `config/default-data.json` at your own CSV with the same schema.

## Workflow loop

```
default dataset -> candidate generation -> candidate intake (audit)
-> source verification -> report & decision gate -> approved accumulation
-> improvement notes for the next run
```

## Workstreams and responsible skills

| Need | Entry skill |
|---|---|
| Understand or resume the project | `read-effective-verbal-context` |
| Produce a new candidate artifact | `notebooklm-sst-research` |
| Audit, verify, report, and accumulate a candidate set | `app-sst-candidate-intake` |
| Diagnose a Shopee-specific failure | `shopee-scrape-recovery` |

Handoff writing is owner-maintained outside the plugin; a stranger reports documentation deltas
rather than rewriting the handoff.

## Ownership boundaries (do not cross)

- Generation only proposes candidate rows. It never merges, verifies, or writes the default store.
- The app owns audit, verification, dedup, and accumulation. Accumulation is approval-gated, backed
  up, atomic, and idempotent.
- Coverage/novelty are audit metrics computed on a simulated union; they never mutate data.
- Cross-run reporting belongs to the agent workflow, not an in-app dashboard.

## Where things live

- App: `app.py` (supported entry; default port `5000`, agent mode `?agent=1`), `app_accumulation.py`,
  `index.html`. `sel_app.py` and `live_test.py` are legacy/reference only.
- Config: `config/default-data.json` is the portable pointer to the default CSV. Per-run pointers
  (`config/current-candidate.json`, `config/current-verification.json`) are created by your own runs
  and are intentionally not shipped.
- Generation support: `pipeline/` (exemplar builder, run aggregation, strict-candidate validation).
- Verification/accumulation: `tools/`, `app_accumulation.py`.
- Plugin map: `plugins/data-phinter-workflows/references/overview.md`, then `architecture.md`.

## Fresh-clone state

A fresh clone has no prior run: no `data_out/`, no current candidate/verification pointers, no browser
profiles. Start from `sample_data.csv`, generate your own candidates, and let the app verify and
accumulate. Respect each source site's Terms of Service and `robots.txt`; see the README's
responsible-use note.

# Artifact And Status Contract

## Context Artifacts

| Artifact | Status contract |
|---|---|
| `effective-verbal-context.md` | Committed, virtualized, machine-independent project context |
| `effective-verbal-context.local.md` | Gitignored local working context created on first recovery and preferred for machine/run state |

The public context is not a copy of the maintainer's local handoff. Publication is an explicit
virtualization step that removes private/local/generated state while preserving discoverability.
The legacy `effective-verbal-context-local.md` name may be migrated but is never the canonical
working path.

## Canonical Pointers

| Pointer | Meaning |
|---|---|
| `workspaces/<topic>/default.csv` | Cumulative default CSV used by app-owned workflows |
| `workspaces/<topic>/candidate.csv` | Selected candidate artifact plus completion metadata |
| `workspaces/<topic>/verification.json` | Latest verification decisions, repair artifacts, and terminal state |

Do not infer completion from a path or filename. Read status fields and verify source artifacts.
Plugin prompts that mention a selected/current candidate mean "audit its status first", not
"assume it is eligible for intake."

## Candidate Completion

`strict_completed` requires at least 100 complete, internally unique, topic-valid, direct product
URLs after listing-like exclusions. A historical `accepted_with_known_risk` pointer remains usable as
provenance but is not strict completion.

## Acceptance Standards

| Standard | Meaning |
|---|---|
| `unique` | Claimed price matches exactly once in accepted page evidence |
| `present` | Claimed price appears at least once; multi-match ambiguity must be reported |

The agent never silently chooses between them.

An accumulation preview is non-mutating. Commit additionally requires the current verification state
to record a matching post-report user decision; query mode or an automation header alone is not
sufficient approval.

## Legacy Provenance

Historical artifacts are not rewritten to imply evidence they did not record. If an old event
timeline does not durably prove that approval preceded mutation, preserve the original events,
record a separate reconciliation artifact, and mark the run with a provenance limitation. Current
code enforcement may close the behavior for future commits, but it does not retroactively strengthen
the old evidence.

## Terminal States

| State | Meaning |
|---|---|
| `accumulated` | Approved set was written through the app-owned path |
| `completed_without_write` | Workflow completed and the user chose no mutation |
| `deferred` | User postponed the decision or required work |
| `accumulated_with_deferred_rows` | Approved set was written while rejected/problem rows remain explicit |

## Run Evidence

Use actual local timestamps and stable run IDs for candidate, audit, verification, repair, report,
event, and backup artifacts. Never overwrite earlier run evidence. Event logs contain workflow events,
counts, decisions, and artifact paths, not secrets, cookies, full HTML, or redundant row payloads.

## Extraction Recipes

The `HTML` field may contain a CSS text selector, `selector::content`, or
`jsonld:Product.offers.price`. Listing/article/wrong URLs are replaced or rejected instead of being
masked by a broad selector.

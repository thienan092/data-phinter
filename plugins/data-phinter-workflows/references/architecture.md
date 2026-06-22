# Data Phin-ter Plugin Architecture

This document is the detailed reference behind the short
[plugin overview](overview.md). The overview is the discovery surface; this file owns deeper
responsibility, data-flow, and maintenance semantics.

Execution prerequisites and supported stop behavior live in
[runtime-prerequisites.md](runtime-prerequisites.md).

## Component Responsibilities

| Component | Responsible skill | Owns | Must not own |
|---|---|---|---|
| Context recovery | `read-effective-verbal-context` | Recover state, map workstreams, reconcile evidence and conflicts | Execute every optional branch or trust handoff over source |
| Candidate generation | `notebooklm-sst-research` | NotebookLM research, aggregation, strict completion, candidate artifacts | Verify prices, merge, dedup against default, or write default |
| Candidate intake | `app-sst-candidate-intake` | Audit, app import, Link dedup, verification, report gate, approved accumulation | Silently choose acceptance or add reporting dashboards |
| Shopee recovery | `shopee-scrape-recovery` | Classify Shopee failures, preserve intervention state, bounded hardening | Treat login/captcha/access blocks as selector failures |

Handoff writing is an owner-retained capability outside the plugin. Plugin workflows must still
identify architecture/documentation deltas so the owner can apply them without hidden context.

## Runtime Data Flow

```mermaid
flowchart TD
    CFG[config/default-data.json] --> EX[Representative exemplar]
    EX --> N[NotebookLM generation]
    N --> CAN[Timestamped candidate artifacts]
    CAN --> PTR[config/current-candidate.json]

    CFG --> APP[App candidate intake]
    PTR --> APP
    APP --> AUD[Audit and Link dedup]
    AUD --> VER[Live verification]
    VER --> REP[Report, analyze, advise/improve]
    REP --> DEC{User decision}
    DEC -->|Approved unique/present set| ACC[Preview, backup, atomic accumulation]
    DEC -->|Approved repair| FIX[Selector, JSON-LD, URL replacement, or reject]
    DEC -->|Defer| TERM[Explicit terminal status]

    VER -->|Shopee-specific failure| SHOP[Shopee recovery]
    SHOP -->|Recovered or classified| VER
    SHOP -->|Human-only condition| HUMAN[Notify user and preserve state]

    ACC --> EV[Events, reports, configs, artifacts]
    FIX --> EV
    TERM --> EV
    EV -. documentation delta .-> HAND[Owner-maintained effective verbal context]
```

## Decision And Mutation Rules

1. NotebookLM candidate completion is independent of the accumulated default store.
2. Only a strict-complete generation run may replace the current-candidate pointer as completed.
3. Verification results are reported before the user chooses accumulation, repair, or deferral.
4. Default data changes only through the app-owned approved write path: preview, Link dedup, backup,
   atomic replace, event evidence, and idempotency.
5. Reporting remains an agent workflow responsibility. The app exposes operational controls and
   machine-readable state, not a cross-run report dashboard.
6. Human-only intervention conditions are reported promptly rather than hidden behind retries.

## Agent Controls And Information Parity

The app's **Load default data**, **Add candidate data**, and **Accumulate approved unique** controls
are automation affordances. Base markup keeps them hidden; `?agent=1` reveals them. They are not
normal-user controls and should not be mirrored into normal mode merely for visual symmetry.

Information parity means both parties know the same business facts through suitable channels:

| Fact | User channel | Agent channel |
|---|---|---|
| Verification outcome and available branches | Report and conversation | Report, verification API, artifacts |
| Accepted standard and write approval | Explicit decision | Recorded post-report decision in current verification state |
| Accumulation preview and result | Agent's visible report/update | Accumulation API, hidden DOM status, event log |
| Backup, before/after counts, terminal state | Completion report | API response, config, events |

The query flag and `X-Agent-Automation` header are local routing/discoverability controls, not strong
authentication. Commit additionally requires a matching run ID and recorded post-report approval.

## Automation Boundary

The recurring automation invokes `notebooklm-sst-research` and preserves the stable automation ID
`daily-notebooklm-sst-data-run`. It may update `config/current-candidate.json` only after strict
completion and may never write configured default data. App intake remains a separate user-directed
workflow.

## Semantic Link Maintenance

Architecture is a maintained workflow artifact. During **Report, analyze, and advise/improve**, any
accepted change must be classified against this matrix:

| Changed behavior | Required synchronized artifacts |
|---|---|
| Entry point or skill relationship | Repo README, `references/overview.md`, detailed architecture, handoff |
| Skill responsibility or workflow order | Affected `SKILL.md`, detailed architecture, handoff |
| Candidate/default/verification status contract | Skill, `artifact-and-status-contract.md`, config examples, handoff |
| User decision gate or mutation rule | Intake skill, detailed architecture, tests, handoff |
| New recovery/failure class | Recovery skill/references, detailed architecture when cross-component, handoff |
| Plugin packaging/version | Plugin manifest, plugin README, handoff |
| Runtime capability or intervention point | Affected skill, runtime prerequisites, architecture when cross-component, handoff |

Plugin workflows report the required documentation delta. The owner-held continuity process applies
it to the handoff and checks this matrix. A layer that cannot be synchronized is recorded as a
blocker or residual risk, not silently left stale.

For a stranger, “synchronize the handoff” therefore means describing the exact delta and its evidence
for the owner. It does not grant or imply access to `write-effective-verbal-context`.

## Source And Bundle Synchronization

Repository development copies under `.codex/skills/` are canonical. The plugin bundle contains
release snapshots under `plugins/data-phinter-workflows/skills/`. Run `scripts/sync_skills.py` after
skill changes and `scripts/validate_bundle.py` before Stranger audit or release. Validation fails when
the canonical and bundled skill trees differ.

## External Quality Boundary

Stranger audit is not shown as a plugin node because it is external acceptance testing. Its fixed
entry condition is the repository README; the independent auditor then invokes
`read-effective-verbal-context` according to its own understanding and evaluates whether this plugin
can be discovered and operated without hidden project history.

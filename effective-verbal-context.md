# Effective Verbal Context: Data Phin-ter

This is the project's release-safe, virtualized handoff. It is committed with the repository and
contains only machine-independent project context. A fresh clone has no prior session state, so this
file describes the project, its boundaries, and where local state will live, never the values of any
one private run. Reconcile every claim against current source, tests, and plugin references;
do not trust prose over code.

> Continuity note: this committed handoff stays machine-independent (no absolute paths, private URLs,
> credentials, account identifiers, or per-run values). On first context recovery,
> `read-effective-verbal-context` materializes `effective-verbal-context.local.md`. That gitignored
> file is the primary working handoff for machine/run state. Later reads prefer it while still
> reconciling durable project rules with this public baseline and current source.

## Context lifecycle

| Artifact | Scope | Rule |
|---|---|---|
| `effective-verbal-context.md` | Portable project context shipped through Git | Keep virtualized and sufficient for a fresh clone; never store local paths, private URLs, credentials, account state, or generated-run specifics. |
| `effective-verbal-context.local.md` | Materialized local working context | Create on first recovery, keep gitignored, and prefer for machine/runtime/run state. |
| `write-effective-verbal-context` | Owner-retained maintenance capability | Write the local context by default. Only update this public file when the request explicitly asks to virtualize/publish the local result. |

The legacy name `effective-verbal-context-local.md` is migration input only. When it exists and the
canonical local file does not, preserve its content by materializing the canonical
`effective-verbal-context.local.md`, then use the canonical name.

## Objective

Data Phin-ter accumulates a "single source of truth" (SST) dataset of products that each have a
verifiable source link and price, and grows it over time. Generation proposes candidate rows; the app
verifies each claimed price against its live source page, then deduplicates and accumulates approved
rows. Each topic lives in its own isolated workspace under `workspaces/<topic>/`.

## Architecture: Workspace Isolation

The project uses **workspace isolation** instead of global config files. Each topic has its own
directory containing all data and outputs:

```
workspaces/
  ├── <topic-a>/
  │    ├── default.csv          # Accumulated trusted store
  │    ├── candidate.csv        # Latest generation output
  │    ├── verification.json    # Current verification state
  │    └── data_out/            # Reports and verified outputs
  └── <topic-b>/
       └── ...
```

All tools accept `--workspace workspaces/<topic>` (or `DATA_PHINTER_WORKSPACE` env var for the app).
If omitted, tools fall back to the `sample_data.csv` anchor at the project root for a zero-friction
onboarding experience. There is no `config/` directory. This design ensures:

- **Stateless execution**: every command explicitly declares its data context.
- **Domain isolation**: an agent working on one topic cannot accidentally read/write another topic's data.
- **No hidden state**: no mutable JSON config files between tool invocations.

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
- Verification defaults to Selenium-backed `compatible`. `fast` is the explicit BS4 option.
  `adaptive` is a discoverable CloakBrowser/provider escalation that requires evidence, a proposal,
  and user approval before execution.

## Operating rules (quality bar)

- **Closed for Quality**: Agents must evaluate their output against semantic expectations at the end of each major workflow phase. Do not blindly proceed to the next step if the output does not meet the specified acceptance criteria (e.g., high duplication rate). The **Report, analyze, and advise/improve** step must audit both data quality AND process quality (timeouts, looping compliance, and any user feedback raised during the run). At each phase boundary, also verify: *did the agent offer the user the most interactive channel available for this phase?* If a visible UI channel (e.g., `app.py`) was available but the agent chose a batch tool instead, record this as an observability gap in the Report.
- **Micro-Previews (Early Decision Gates)**: Micro-Previews trigger before expensive or irreversible actions. They cover two dimensions:
  - **Data quality**: If semantic criteria fail (e.g., >80% duplication, severe anomalies), pause and present a lightweight summary explaining the anomaly.
  - **User accessibility**: If the agent is about to execute a task for which a more interactive channel exists (e.g., running `verify_accumulate.py` batch when `app.py` UI is available), pause and present the alternatives: "I can run batch verification directly, or start the app UI so you can observe progress interactively. Which do you prefer?"
  In both cases, wait for user permission before proceeding.
- **Background task consultation**: Before sending heavy or long-running tasks (e.g., scraping dozens of sites, batch verification) to the background, explain the tradeoff (speed vs observability) and let the user choose. Do not silently run tasks that remove the user's ability to observe progress.
- **Mandatory looping**: If a generation run yields fewer than the strict target (100 candidates) and the time budget (30 minutes) has not expired, the agent must automatically iterate with an updated exclusion index rather than stopping short.
- **Timeout intervention**: If a browser subagent or long-running task hangs beyond 25–30 minutes, the parent agent must immediately notify the user (via `tools/notify_user.py` or equivalent audio alert) and seek direction. Do not silently leave the user waiting.
- **Candidate ID requirement**: Every CSV row entering `tools/verify_accumulate.py` must have a non-empty `ID` column value. The tool uses `ID` as a dictionary key; empty IDs cause silent row overwrites.
- **Friction ownership**: The system (agent + context files) owns the burden of remembering user feedback, corrections, and quality concerns. The user must never be forced to re-raise an issue that was already discussed. If the user has to remind the agent, the system has failed.
- Report before any approved branch: after verification, run the report/decision gate, then act only
  on the user's chosen branch (accumulate / repair / improve).
- No silent acceptance: `unique` vs `present` price acceptance, anomaly handling, and any write to the
  configured default store require an explicit decision.
- Do not steer generation with hard niche/brand/domain lists; use an exemplar plus a URL exclusion
  index. Diversity and count nudges are fine.
- Stable automation identity: if you schedule recurring generation, reuse one automation id and write
  unique, timestamped run artifacts; never overwrite.
- Scheduled NotebookLM work must preflight whether its execution host can control the intended
  signed-in browser session and route human intervention. A detached scheduler without those
  capabilities is not an eligible execution host; use an attached/interactive run or stop with the
  exact missing capability.
- Solve, classify, or reject problem rows (selector / recipe / direct URL / intervention) — do not
  hand back raw symptoms.
- Use `--workspace` when invoking tools for a specific topic. Omitting it defaults to the `sample_data.csv` anchor.
- Validate candidate novelty before reporting results. If all candidates are duplicates, report this
  as a problem and propose remediation rather than silently accepting.
- Keep tests self-contained for a fresh clone: use committed sanitized fixtures (e.g.
  `tests/fixtures/`), never gitignored captures (`diagnostics/`, browser profiles); do not skip a
  check when its fixture is absent — skipping passes the suite but drops the regression for a stranger.

## Where things live

- Context: `effective-verbal-context.md` (public), `effective-verbal-context.local.md` (generated
  local), and `tools/context_handoff.py` (materialize/validate helper).
- App: `app.py` (supported entry; default port `5000`, agent mode `?agent=1`; requires `--workspace`),
  `app_accumulation.py`, `index.html`. `sel_app.py` and `live_test.py` are legacy/reference only.
- Workspaces: `workspaces/<topic>/` — each contains `default.csv`, optionally `candidate.csv`,
  `verification.json`, and `data_out/`.
- Generation support: `pipeline/` (exemplar builder, run aggregation, strict-candidate validation).
- Verification / accumulation: `tools/` (especially `verify_accumulate.py`, which accepts `--workspace`),
  `app_accumulation.py`.
- User notification: `tools/notify_user.py` — plays a system beep for agent-to-user alerts at
  decision gates. Usage: `python tools/notify_user.py [frequency_hz] [duration_ms]`.
- Plugin map: `plugins/data-phinter-workflows/references/overview.md`, then `architecture.md`,
  `artifact-and-status-contract.md`, and `runtime-prerequisites.md`.
- Cross-agent entry: Codex uses the repository/plugin skill entry points. Claude Code can load the
  same bundle with `--plugin-dir`; Claude Desktop/Cowork can install or upload the Claude plugin
  package. Tool-dependent workflows still require the host capabilities listed in runtime
  prerequisites.

## Operational glossary

| Term | Meaning |
|---|---|
| Workspace | An isolated directory under `workspaces/<topic>/` containing `default.csv`, `candidate.csv`, and `data_out/`. All tools resolve paths relative to this directory via `--workspace`. |
| `--workspace` flag | The mandatory CLI parameter for `app.py`, `verify_accumulate.py`, and `audit_candidates.py` that replaced the old `config/` JSON pointers. |
| Configured default data | The cumulative trusted store; located at `workspaces/<topic>/default.csv`. |
| Strict candidate | A topic-valid purchasable product with a full HTTP(S) direct product URL and a listed price; listing / category / search / blog URLs do not count unless verified as one product. |
| Novel vs default | A candidate whose normalized URL is absent from the workspace's `default.csv` URL set. |
| Simulated union | A URL union used only for audit; it never writes either file. |
| Accumulation | Approval-gated app write: preview + dedup by `Link` + backup + atomic replace + event log; idempotent. |
| Extraction recipe | A reusable price method: CSS text selector, `selector::content` attribute, or `jsonld:Product.offers.price`. |
| Intervention event | Captcha, login / session expiry, access block, or another human-only condition needing prompt notification. |

## Fresh-clone state and how to start

A fresh clone has no prior run: no workspace `data_out/`, no candidate CSVs, no browser profiles.
The project root contains a `sample_data.csv` anchor. A stranger can simply run `python app.py` to
explore the workflow instantly.

To work on isolated topics, pick a workspace (e.g. `workspaces/coffee/`), generate candidates,
then let the app verify and accumulate:

```
python app.py --workspace workspaces/coffee
python tools/verify_accumulate.py --workspace workspaces/coffee
```

To create a new topic, create `workspaces/<new-topic>/default.csv` with the canonical SST schema.
Respect each source site's Terms of Service and `robots.txt`; see the README's responsible-use note.

## Verifying the project

Use your own Python interpreter (the repo pins no machine path). From the repo root:

- Unit tests: `python -m unittest discover -s tests -p 'test_*.py'`.
- Plugin bundle: `python plugins/data-phinter-workflows/scripts/validate_bundle.py`.
- After edits, check whitespace: `git diff --check`.

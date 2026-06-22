---
name: read-effective-verbal-context
description: Read, materialize, and operationalize effective-verbal-context.md or related handoff documents. Use when an agent is starting or resuming a session, recovering context after compaction/session loss, continuing proof/research/debugging/implementation work, auditing whether a handoff is enough to proceed, reconciling conflicting handoffs, or the user asks to load or resume from effective verbal context.
---

# Read Effective Verbal Context

Use this skill to turn one handoff, or a set of related handoff artifacts, into an actionable starting state for the current session. The goal is not to summarize the document back verbosely; the goal is to recover objective, constraints, artifacts, assumptions, open work, quality standards, and any unresolved conflicts well enough to continue without hidden chat history.

## Project Context Pair

For a project that adopts the portable/local context contract, use these roles:

| Artifact | Role | Precedence |
|---|---|---|
| `effective-verbal-context.md` | Committed, virtualized context that must work in a fresh clone | Portable project rules and discovery baseline |
| `effective-verbal-context.local.md` | Gitignored materialized context for the current machine, runtime, and run state | Primary working handoff for local facts |
| `effective-verbal-context-local.md` | Legacy local filename | Migration input only when the canonical local file is absent |

On the first normal invocation, materialize the canonical local file from the legacy local file when
present, otherwise from the committed public file. In Data Phin-ter, use:

`python tools/context_handoff.py materialize`

The helper never overwrites an existing canonical local file and refuses to create machine-specific
context when Git would track it. If the helper is unavailable in another project, apply the same
rules manually.

Materialization is not a blind copy operation. Preserve the portable content, then add only useful
local facts that were actually inspected, such as workspace root, available runtime, current config
pointers, or host capability. Never add credentials, cookies, API keys, browser profile contents,
private page contents, or unrelated personal data.

On later invocations, read the canonical local file first. Also inspect the public context when it
may have changed after a pull/update or when durable project rules matter. Local context wins for
machine/run facts; public context is the baseline for portable architecture and release rules;
source/config/tests win for implementation facts. Do not silently flatten conflicts between them.

An explicit request to audit, virtualize, or inspect the public context may target
`effective-verbal-context.md` directly. That is the exception to normal local-first recovery.

## Core Workflow

1. Locate the handoff.
   - If the user specifies one handoff path/name, skip discovery and use the specified file unless it is missing or unreadable.
   - If the user specifies multiple files, treat them as the candidate context artifact set for the current task. Do not discard any specified file merely because another file has a conventional name.
   - Default path: `effective-verbal-context.local.md` in the current workspace root.
   - If the canonical local file is absent, materialize it from `effective-verbal-context.md` or the
     legacy `effective-verbal-context-local.md` as defined above, then continue from the canonical
     local file.
   - If not found, search the workspace root and obvious handoff names such as `*effective*context*.md`, `*handoff*.md`, and `*.audit.md`.
   - If multiple plausible files exist and the user did not specify which one(s) to use, prefer
     `effective-verbal-context.local.md`, then `effective-verbal-context.md`; ask only if choosing
     would be risky.
   - If multiple user-specified files have unclear instructions, read them as parts of a larger handoff. If material conflicts are detected and cannot be resolved by source/artifact authority, ask the user with concrete resolution options before proceeding.

2. Read the handoff artifact set before acting.
   - Read the full specified handoff file(s) when they are reasonably sized.
   - If very large, read the section list/headings first, then load the sections needed for the user's current task.
   - Prefer fast recovery sections first when present, such as `Reader Quick Start`, `Compact Working Thesis`, `Session State`, or equivalent names.
   - Treat custom protocol/contract sections as active instructions, not decorative prose. Examples include sections about evidence hierarchy, claim triage, anti-overfit rules, source-grounded protocols, proof obligations, or domain-specific guardrails.
   - Treat the handoff artifact set as the session's starting context, not as an unquestionable source of truth.
   - When reading multiple handoffs, track each claim's provenance: file path, section, date/version if present, scope/task, and whether it is a primary handoff, older handoff, audit artifact, correction, or generated theory.

3. Extract a working state.
   - Identify the current objective and whether it is implementation, proof, research, debugging, review, planning, or mixed work.
   - Extract artifact paths, commands/tests already run, blockers, accepted conclusions, user corrections, quality checklist, open questions, assumptions, and disallowed assumptions.
   - Preserve distinctions between known facts, inferences, hypotheses, bugs, unverified claims, and residual risks.
   - Extract any explicit reading protocol or evidence hierarchy and apply it to later source/artifact inspection.
   - When the handoff contains domain-specific examples inside a general protocol, keep the general rule as the reusable constraint and treat the concrete names as examples or current-session state.
   - If multiple handoffs disagree, do not merge them silently. Build a reconciled working state: accepted facts, active constraints, stale/demoted claims, unresolved conflicts, and next verification actions.

4. Verify only what matters next.
   - Before relying on code-level claims, reopen referenced source files, tests, notebooks, or generated artifacts that are directly relevant to the next action.
   - Recheck revision-sensitive anchors such as line numbers after source edits.
   - Do not rerun expensive tests or broad searches unless the current task needs them.

5. Start with a compact recovery note.
   - When beginning a new session, provide a short recovery note: objective, active constraints, next action, and any immediate blockers.
   - Do not paste the whole handoff. Use tables only when they materially improve clarity.
   - If the user asked you to continue work, continue after the recovery note unless a necessary decision is missing.

6. Continue using the handoff's quality bar.
   - Apply the handoff's checklist and user corrections as active instructions for the task.
   - When the task is proof/research, keep theorem claims tied to artifacts, assumptions, and falsification tests.
   - When the task is code work, respect pending test status, dirty-worktree constraints, and noted blockers.

## Context Artifact Set And Conflict Reconciliation

Use this section when more than one handoff, audit file, prior context document, generated config, or user correction is available or explicitly specified. Reading is not just parsing one file; it is reconciling a context artifact set into a current working state.

### Artifact Roles

| Artifact Role | Examples | How To Use It |
|---|---|---|
| Primary handoff | `effective-verbal-context.local.md`, `effective-verbal-context.md`, or user-specified main handoff | Starting point for objective, constraints, and next actions. |
| Older / related handoff | Previous handoff files, copied handoffs, renamed context docs | Use for history and durable facts, but check whether newer artifacts supersede them. |
| Audit artifact | `effective-verbal-context.local.audit.md`, public Stranger-audit reports, or fresh-agent audit notes | Treat as a critique of sufficiency and ambiguity, not as automatic source truth. |
| Current user instruction | The prompt that invoked the skill or specified files | Highest authority for current intent, scope, and whether to ask before proceeding. |
| Source/test artifact | Source code, tests, notebooks, generated data, loaders, runners | Highest authority for implementation facts when inspected. |
| Generated theory/config | AI theory text, session JSON, generated explanations | Evidence of prior state and naming, but may be stale or contradicted by source. |

### Selection And Ranking

| Situation | Default Handling |
|---|---|
| User specifies one file | Use that file directly; skip discovery unless it is missing or unreadable. |
| User specifies multiple files | Treat them as a larger handoff set; read enough of each to recover scope, role, authority, and conflicts. |
| Multiple plausible files found by search | Prefer the canonical local file, then the public file, when the user did not specify files and no task-specific reason points elsewhere. |
| Newer handoff vs older handoff, same scope | Prefer newer claims only when they have equal or stronger authority and are not contradicted by source. |
| Newer handoff vs older handoff, different scope | Do not merge blindly; keep task scopes separate and use the current task to select relevance. |
| Audit vs handoff sufficiency claim | Treat sufficiency as contested until the audit findings are patched or accepted by the user. |
| Source/test vs handoff implementation claim | Source/test wins for implementation facts after reinspection. |
| Current user correction vs handoff quality bar | Current user correction wins for intent and response constraints. |

### Conflict Detection

Scan for material conflicts before proceeding when multiple artifacts are read or when the task is high-risk.

| Conflict Type | Examples | First Resolution Attempt |
|---|---|---|
| Temporal conflict | Old handoff says a PART is solved; new handoff says it is blocked. | Compare scope/date/audit status, then verify source if it affects the next action. |
| Authority conflict | Handoff says X; source code says not-X. | Source wins for implementation facts; mark handoff claim stale. |
| Role conflict | One artifact treats a file as predictor/input; another treats it as comparison target. | Check runner/config role and source generation path. |
| Scope conflict | Two handoffs are both true but refer to different tasks or model families. | Keep separate; do not create a synthetic merged claim. |
| Alias conflict | Old and new names appear to refer to the same tensor or concept. | Preserve semantic identity if source/config mapping supports it; otherwise mark unresolved. |
| Audit conflict | Audit says the handoff lacks information; handoff says it is sufficient. | Treat sufficiency as unresolved and patch or ask before relying on it. |
| User correction conflict | User's current instruction contradicts old checklist or assumptions. | Current user instruction wins unless it conflicts with safety or source facts. |

### Conflict Resolution Output

When conflict matters to the next action, produce a compact resolution table before acting or ask the user if the conflict cannot be safely resolved.

| Field | What To Include |
|---|---|
| Conflict | The conflicting claims in concrete terms. |
| Sources | File paths/sections or source artifacts for each claim. |
| Authority / scope | Why one claim should outrank another, or why they apply to different scopes. |
| Provisional resolution | Accepted, demoted/stale, scope-separated, or unresolved. |
| Verification action | File, command, test, or user decision that would close the conflict. |
| Residual risk | What could still be wrong after the provisional resolution. |

If the user specified multiple files and their instructions are still not clear enough to decide how to handle them, process the files as a larger handoff set. If a material conflict is detected between their contents and cannot be resolved by authority, scope, or source inspection, ask the user for clarification and offer 2-3 concrete resolution options, such as "prefer file A", "merge with file B as audit", or "verify against source before proceeding".

## Adaptive Section Semantics

Handoffs may evolve beyond the recommended section names. Read by role, not by exact heading text.

| If A Section Looks Like | Interpret It As | Extract |
|---|---|---|
| Quick start, compact thesis, recovery note | Fast recovery layer | Objective, active constraints, relevant artifacts, current state, next action. |
| Protocol, contract, guardrails, quality bar | Active behavioral instructions | Rules that constrain future reasoning or implementation. |
| Evidence hierarchy, authority ranking, source policy | Epistemic ordering | Which artifacts can override which claims, and what must be rechecked. |
| Claim triage, bug triage, known facts vs hypotheses | Claim-status ledger | Source facts, inferences, suspected bugs, stale claims, unverified claims, falsification routes. |
| Artifact inventory, file map, data map | Navigation layer | Paths, roles, generated artifacts, commands, and provenance. |
| Mechanics, operational glossary, domain model | Working definitions | Terms, state variables, events, source anchors, observable tests. |
| Open questions, blockers, residual risk | Next-action constraints | What remains unknown, what data is missing, and what must not be assumed. |
| Audit, cold start check, sufficiency judgment | Reliability layer | Whether the handoff can stand alone and what risks remain. |

When a heading is unfamiliar, infer its role from the table columns and row content. Do not require the file to match the writer skill's exact recommended headings.

## Source-Grounded / Artifact-Grounded Handoffs

Use this section when the work is about correctness, generated artifacts, testing harnesses, proof, reverse engineering, bug triage, or any task where prior natural-language theory may be stale.

- Preserve the handoff's stated evidence hierarchy. If no hierarchy is stated, use a conservative default: executable source and tests first; harness/load/save mechanics next; configuration/generated artifacts next; prose docs and prior generated theory last, unless the user explicitly says otherwise.
- Before relying on a named artifact, map it through its provenance: user-facing name, storage name/path, generation hook or loader, source call site, shape/format if relevant, and how it is used by the evaluation harness.
- Distinguish artifact roles: predictor/input, comparison target, observable diagnostic, explanation aid, configuration, or generated output. A comparison target should not silently become a predictor.
- Preserve aliases and renames as semantic continuity facts. If old and new names refer to the same object, record or restate the invariant role rather than treating the rename as a logic change.
- When source and prior theory conflict, do not merge them vaguely. Say which is source-grounded, which is stale or hypothetical, and what evidence would change the conclusion.
- When information is insufficient, make it actionable: name the source expression or behavior that cannot be reconstructed, list the available artifacts, list the missing state/data, explain why a simpler rule would erase a real dependency, and state what artifact or decision would close the gap.
- For suspected bugs, separate the source fact from the bug interpretation. Include a falsification or confirmation route before proposing fixes.

## Recovery Output Template

Use this shape when the user asks to start/resume from the handoff:

| Field | Content |
|---|---|
| Recovered objective | One sentence naming the work to continue. |
| Active constraints | Key quality rules, assumptions, and disallowed shortcuts. |
| Relevant artifacts | Files or docs to open next. |
| Current state | What is accepted, blocked, or unverified. |
| Next action | Concrete next step. |

Keep this compact. If the next action is obvious and safe, do it after the note.

## Audit The Handoff When Needed

Run a quick cold-start audit when the user asks whether the handoff is sufficient, when the document is old, or when the next task is high-risk.

| Audit Question | What To Check |
|---|---|
| Objective recoverability | Can the current objective be stated without old chat? |
| Artifact findability | Are source files, tests, notebooks, docs, and generated outputs findable? |
| Operational definitions | Are specialized terms defined by observable/code-level meaning? |
| Assumption boundaries | Are allowed and disallowed assumptions clear? |
| Actionability | Are open items prioritized with concrete next files/commands/tests? |
| Hidden-context leakage | Are there vague references like "this", "above", or "latest" that require old chat? |
| Residual risk | What still cannot be recovered from the handoff alone? |
| Multi-artifact conflict | If multiple handoffs/artifacts are present, are conflicts detected, ranked by authority/scope/time, and either resolved or escalated to the user? |

If material information is missing, state the gap and either inspect artifacts to repair it or ask the user for the missing decision. Do not invent missing context.

## Handling Proof / Research Handoffs

For correctness, algorithmic, scientific, or proof work:

- Recover theorem shape, convergence target, state variables/events, assumptions, disallowed assumptions, and falsification tests.
- Distinguish operational evidence from formal proof.
- Tie every nontrivial claim to source artifacts or state clearly that it is an inference/hypothesis.
- Preserve implementation-specific mechanisms that a proof must not simplify away, such as thresholds, `detach`, stochastic perturbations, online conflict resolution, packing/unpacking, hard selection, and surrogate gradients.
- If the handoff says a proof route must avoid proving a different algorithm, restate that before proceeding.

## Handling Implementation Handoffs

For coding tasks:

- Reopen the files listed as touched or pending before editing.
- Check test commands and whether they were actually run.
- Respect blockers such as missing dependencies, unavailable runtimes, sandbox restrictions, or known API mismatches.
- Ignore unrelated dirty worktree changes unless they affect the task.

## Updating The Handoff

If the session discovers material new facts, corrections, bugs, changed files, or revised next
steps, update `effective-verbal-context.local.md` using `write-effective-verbal-context` when
available:

- Add only durable continuity information.
- Keep the handoff lean.
- Record whether tests/commands were actually run.
- Preserve user corrections as first-class checklist or clarification rows.
- Do not update the committed `effective-verbal-context.md` unless the user explicitly asks to
  virtualize/publish the local result.
- A project-specific owner-maintained policy overrides automatic maintenance. If README says the
  handoff-writing capability is retained by the owner, materialization of the local working copy is
  still allowed, but later continuity edits should be reported as an exact delta unless the owner
  invokes or authorizes the write skill.

## Common Failure Modes To Avoid

| Failure Mode | Avoidance Rule |
|---|---|
| Treating the handoff as a transcript | Extract state and proceed; do not narrate everything back. |
| Treating a context artifact set as one flat document | Track file roles, scope, authority, and conflicts before merging. |
| Trusting stale line numbers | Reopen files before using line-level anchors. |
| Losing user corrections | Convert corrections into active checklist/constraint items. |
| Proving/building the wrong thing | Apply disallowed assumptions and implementation constraints from the handoff. |
| Choosing one of several user-specified handoffs without reading the others | Treat user-specified files as the candidate context artifact set unless the user explicitly ranks them. |
| Silently resolving conflict by recency alone | Prefer recency only among equal-scope, equal-authority claims; otherwise verify or ask. |
| Asking unnecessary questions | Make reasonable choices when the handoff plus workspace gives enough information. |
| Ignoring residual risk | State gaps clearly when the handoff is insufficient. |

## Project Entry And Stranger Recovery

When a project README directs a completely new agent to this skill:

1. Treat the README, public context, and materialized local context as the initial context artifact
   set. On a fresh clone, create the local file before recovery.
2. Follow the project's short plugin/workflow overview before opening detailed architecture.
3. Recover every top-level workstream and its responsible skill, even when only one workstream is
   immediately active. This prevents an apparently successful recovery with a structural blind spot.
4. Name deeper architecture, source, config, tests, and artifact entry points so the agent can
   explore independently instead of receiving a transcript-sized explanation.
5. Report broken semantic links, missing workstreams, stale status, or conflicts between README,
   handoff, plugin map, skills, and source as recovery findings.
6. Do not assume the project owner's handoff-writing skill is bundled or available. Creating the
   gitignored local working copy is part of context recovery, not handoff authorship. For later
   continuity changes, report any required handoff/documentation delta instead of inventing a fifth
   plugin entry point.
7. Recover the verification-mode policy: Selenium-backed `compatible` is the default, `fast` is the
   explicit BS4 option, and `adaptive` is the discoverable CloakBrowser/provider escalation. Do not
   activate `adaptive` merely because context was loaded. When evidence shows the default is
   insufficient, explain the evidence, scope, privacy/runtime impact, and proposed mode change, then
   obtain user approval before switching.

The compact recovery note should include the project map or link to it when available. Preserve links
to the current short overview and detailed architecture when updating context. This recovery mode
prepares an independent agent to inspect the project; it is not itself the external Stranger audit.

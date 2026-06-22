# Quality Governance

Use this reference whenever Shopee recovery uses agent judgment, proposes a patch, or changes scraper architecture.

## Core Project Values

| Value | Meaning | Guardrail |
|---|---|---|
| Hardening over dependency on agents | Agent analysis should improve the runtime system instead of becoming the runtime system. | Each agent-assisted recovery must identify what can be encoded into CloakBrowser strategy, provider logic, diagnostics, tests, or status semantics. |
| Artifact-grounded truth | Claims must be tied to saved evidence, not memory or intuition. | Use artifact path, final URL, screenshot, HTML, body excerpt, and command/test result. |
| Provider-specific isolation | Shopee volatility should not destabilize Lazada, BS4, generic regex, or UI flows. | Prefer provider modules/strategy registries before shared rewrites. |
| User decision access | The user should see meaningful options and trade-offs, not a hidden technical tunnel. | Present choices with consequences when architecture, cost, manual login, proxy, or privacy/session persistence is involved. |
| Measurable improvement | Quality claims should be falsifiable. | Include concrete predictions: sample size, expected pass/fail count, latency bound, or recurrence reduction. |
| Semantic continuity | New analyses must preserve prior conclusions, corrections, and project meaning unless source/artifacts supersede them. | Reconcile with `effective-verbal-context.md` before changing direction. |
| Practical sustainability | Prefer maintainable, low-cost, bounded changes over brittle one-off bypasses. | State maintenance burden, dependency impact, and rollback path. |


## Pre-Use Disclosure

Before invoking this skill for work that may change code, run live probes, or update handoff, provide a compact user-visible disclosure:

| Field | Required Content |
|---|---|
| Skill | Name and path. |
| Trigger | The failure, request, or artifact that makes the skill relevant. |
| Purpose | Diagnosis, hardening review, source patch, artifact capture, or handoff-delta reporting. |
| Scope | Files, commands, browser sessions, live probes, and artifacts that may be touched. |
| Post-hoc surface | Where the user can inspect evidence and decisions afterward. |

This disclosure protects user decision access and semantic continuity. It should be brief but concrete.
## Agent Hardening Review Template

Use this compact table in reports or handoff updates after agent-assisted analysis:

| Field | Fill With |
|---|---|
| Trigger | User request or failure artifact that caused agent analysis. |
| Evidence | Artifact paths, classification, screenshot/HTML/report, and exact command/test if run. |
| Runtime-hardening opportunity | What should become a CloakBrowser strategy, provider rule, classifier, diagnostic, UI state, or test. |
| Agent-only residue | What cannot yet be encoded, why, and what evidence would make it encodable. |
| Architecture impact | Affected modules/contracts and whether the change preserves provider isolation. |
| Project-value impact | How the change affects hardening, artifact truth, user decision access, semantic continuity, sustainability, and current trade-offs. |
| Quantified prediction | Specific, checkable expectation for future similar failures. Include sample size and time/latency/cost expectation when relevant. |
| Verification/falsification | What run, artifact replay, live probe, screenshot review, or endpoint test would prove the prediction wrong. |
| Handoff delta | What durable conclusion the project owner should add to `effective-verbal-context.md`. |

## Prediction Rules

- Use numbers even when uncertain, and mark uncertainty honestly.
- Prefer small near-term predictions, such as next 3 to 5 artifacts, over vague long-term claims.
- Do not claim production readiness from one live run.
- Ask the owner to track whether predictions were confirmed, falsified, or still pending in the handoff.

## User Decision Points

Ask or clearly surface trade-offs when a change involves:

- storing or reusing Shopee login/session profile;
- adding proxy/residential IP cost;
- changing UI status semantics visible to nontechnical users;
- adding dependencies or browser binaries;
- broad architecture changes beyond provider-specific strategy;
- relaxing data correctness checks for convenience.

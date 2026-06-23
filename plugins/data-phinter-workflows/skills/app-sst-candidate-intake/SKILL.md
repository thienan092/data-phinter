---
name: app-sst-candidate-intake
description: Audit and operate the data-phinter app candidate-intake workflow after a NotebookLM run. Use when an agent needs to add default/candidate CSV data in the app, assess candidate quality or anomalies, deduplicate against the current SST, decide whether user confirmation is required, start verification, or prepare accumulation into the configured default store.
---

# App SST Candidate Intake

Keep this workflow separate from NotebookLM generation. The app owns intake, deduplication,
verification, and accumulation.

## Operating policy

- Complete the current workflow smoothly before proposing non-blocking improvements.
- During the run, collect evidence and missing information in an improvement backlog.
- Interrupt immediately only for a true operational blocker, human-only action, irreversible write,
  or data acceptance decision.
- After verification, run **Report, analyze, and advise/improve** as the decision gate: report the
  outcome, present evidence and missing information, propose concrete branches, then ask which branch
  to execute. Accumulation, page repair, and optional improvements happen only after that decision.
- After executing an approved branch, append its outcome and terminal status to the run evidence.
  Do not pretend the approved action happened inside the earlier report.
- Prefer visible channels in this order: app UI, in-app browser, user-visible artifact/report.
  Use a background batch only when the visible UI is materially slower, lacks checkpoint/resume, or
  cannot express the operation. Explain why, name the available visible alternatives and their limits,
  and return progress/results to the app or another visible channel.
- Keep component responsibilities separate. The app should expose operational controls and data state,
  while the agent's final workflow step owns the cross-run report and improvement advice. Propose and
  obtain user approval before adding a new reporting surface to the app.

## Workflow

1. Resolve the target `workspace` path (e.g. `workspaces/banh-mi/`) which contains `default.csv` and `candidate.csv`. DO NOT USE a global `config/` directory.
2. Resolve the active skill directory, then run its bundled audit script. Claude plugin hosts expose
   `${CLAUDE_SKILL_DIR}`; repository development may use the canonical fallback:

   `python "<active-skill-dir>/scripts/audit_candidates.py"`

   `python .codex/skills/app-sst-candidate-intake/scripts/audit_candidates.py`

   Claude plugin hosts can resolve `<active-skill-dir>` from `${CLAUDE_SKILL_DIR}`. Do not assume
   one host-specific skill path exists on every agent.

3. Read the JSON result before operating the app.
4. Apply the Micro-Preview / Early Decision Gate:
   - Analyze the JSON result from `audit_candidates.py`. 
   - **Semantic Check**: If the duplicate rate is extremely high (e.g. >80% overlap), or exclusions are severe, STOP. Present a lightweight Micro-Preview: "Audit shows X% duplicates. Proceeding to heavy verification may waste time. Do you want to abort intake and return to the generation phase to self-correct?".
   - `blocker`: stop and explain what must be fixed.
   - `review`: report the anomaly, its likely impact, and the available choices; wait for the
     user's decision before verification or accumulation.
   - `notice` only: proceed and summarize the notices.
5. Resolve the app base URL before browser work. Use a user-supplied URL when present; otherwise
   use `http://127.0.0.1:<PORT>` where `PORT` is the running app's configured value (default `5000`).
   If no listener exists, start the supported `app.py` with `python app.py`; when the default port is
   occupied, set `PORT` to a free port and report the selected URL. Then open `<base-url>/?agent=1`
   through the current host's visible browser capability. If Cowork/Claude cannot reach the local
   listener or control a browser, name that missing capability and use the machine-readable API or
   a user-opened visible browser only when the same authorization and information-parity rules are
   preserved.
6. Click **Load default data**, then **Add candidate data**. Read hidden
   `#agent-import-status[data-code]` or `[agent-import]` JSON console logs; do not expose
   technical logs in the UI.
7. Set the app deduplication key to the product Link. Preserve load order so default rows win
   when a URL overlaps.
8. Confirm the visible unique-row count matches the audit's simulated union.
9. Verify only candidate rows that remain after default-vs-candidate Link dedup. Do not re-verify
   default rows during candidate intake.
   - For small/manual batches, use **Verify/Update Price** in the app.
   - Use Selenium-backed `compatible` mode by default. `fast` is an explicit BS4 option for suitable
     static sources.
   - For large batches, use app-owned `tools/verify_accumulate.py --mode compatible`. Preserve each
     attempt in a unique output directory.
   - Do not silently fallback to CloakBrowser. If compatible verification is insufficient, report
     the evidence and propose `adaptive`; describe its scope and runtime/privacy impact, then wait
     for user approval before using `--mode adaptive` or changing
     `DATA_PHINTER_VERIFICATION_MODE`.
10. Treat captcha, login, session expiry, access blocking, or ambiguous selector results as
    user-intervention events. Notify promptly and preserve the current state.
11. Apply a second decision gate after verification:
    - `unique`: accept only price match count 1.
    - `present`: also accept match count >1, but report these as ambiguous price-present rows.
    - Never silently choose between these standards.
12. Run **Report, analyze, and advise/improve**. Include the acceptance choices and the concrete
    page-repair branch. Wait for the user's decision.
13. If approved, visit every selected problematic product page to recover the
    correct price and reusable extraction method. Classify each page before proposing a fix:
    - stable product DOM: save a narrow CSS selector;
    - stable structured data: prefer JSON-LD/meta/product-state extraction;
    - dynamic SPA with stable product semantics: use an adaptive extraction recipe;
    - variant, promotion, region, or session-dependent price: record the context and re-derive on
      each run rather than pretending a permanent selector exists;
    - listing/article/wrong URL: replace the URL instead of repairing a selector;
    - login/captcha/access block: request human intervention and preserve state.
    Treat an adaptive method as a valid product decision when the page genuinely changes often.
14. If approved, preview accumulation into the configured default file, report the exact before/after
    counts, then commit through the app-owned write path. Require run-ID confirmation, Link dedup,
    a recorded matching post-report user decision, backup, atomic replace, and idempotency.
15. Record one terminal status: `accumulated`, `completed_without_write`, `deferred`, or
    `accumulated_with_deferred_rows`. Preserve repaired-but-not-accumulated rows as a separate artifact.

## Run evidence

Preserve machine-readable evidence without turning the app into a workflow-reporting dashboard:

- immutable timestamped candidate, audit, and verification artifacts;
- a current-run pointer/config for agent discovery;
- concise structured events for phase start/end, counts, decisions, interventions, and errors;
- explicit provenance for background execution, including why a visible channel was unsuitable.

Do not log secrets, session cookies, full page contents, or redundant per-row noise when the durable
CSV report already contains the same facts.

## Required anomaly report

State:

- candidate count and hard-target result;
- novelty and overlap versus default;
- dominant source share and coverage concerns;
- incomplete, duplicate, non-topic, or listing-like URL counts;
- verified-unique, ambiguous-price-present, and price-absent counts;
- recommendation: accept, improve the NotebookLM run, or provide additional context.

Do not call a candidate set "good coverage" merely because its row target is met.

## Agent Control And Information Parity

- **Load default data**, **Add candidate data**, and **Accumulate approved unique** are local
  automation affordances. They stay hidden in normal user mode and appear only with `?agent=1`.
- Query mode is only a visibility control. Loopback API calls also require the automation header.
  Remote automation is denied by default and requires explicit enablement plus a matching
  automation token. A mutating accumulation request must additionally match the current run and a
  recorded post-report user approval.
- Do not add a normal-user accumulation button merely to mirror the agent control. Preserve
  information parity through the report/decision/result flow: the user receives the selected
  standard, preview counts, write approval, backup, before/after counts, and terminal result; the
  agent may receive the same facts through APIs, hidden DOM status, or structured event logs.

## Related Plugin Architecture

From the `data-phinter-workflows` plugin root, read `references/overview.md` for the short entry map
and `references/architecture.md` for the report gate, app boundary, and approved-write flow.

<!-- plugin-navigation:start -->
## Plugin Navigation

- [Short workflow overview](../../references/overview.md)
- [Detailed architecture](../../references/architecture.md)
- [Artifact and status contract](../../references/artifact-and-status-contract.md)
- [Runtime prerequisites and stop behavior](../../references/runtime-prerequisites.md)

When an accepted workflow improvement changes entry points, responsibilities, status contracts, or
decision gates, synchronize plugin-owned skills/references and report the required README/local
handoff delta to the project owner. The committed context changes only through explicit
virtualization. Do not assume the owner-held handoff-writing skill is bundled.
<!-- plugin-navigation:end -->

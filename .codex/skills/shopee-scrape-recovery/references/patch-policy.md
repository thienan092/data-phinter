# Bounded Patch Policy

Use this reference before modifying source code in response to a Shopee artifact.

## Preferred Boundaries

Patch in this order:

1. Diagnostic harness or artifact classifier.
2. Provider-specific Shopee module or strategy registry.
3. Shared scraper interface used by `app.py`.
4. Flask endpoint wiring.

Avoid changing generic Lazada, BS4, or price regex behavior unless a shared artifact proves the bug is cross-provider.

## Provider Contract

When Shopee logic is wired into the app, prefer a result object with explicit status:

```json
{
  "status": "ok | price_changed | blocked | login_required | captcha | timeout | selector_failed | unknown",
  "price": 23950,
  "match_count": 1,
  "provider": "shopee",
  "strategy": "headful_persistent",
  "artifact_path": "diagnostics/shopee/<run>/artifact.json"
}
```

The UI/backend should not collapse `blocked`, `login_required`, and `selector_failed` into one "price not found" bucket.

## Strategy Ladder

Use the smallest next experiment:

1. `headless_ephemeral`: baseline only.
2. `headless_persistent`: tests whether stored profile alone helps.
3. `headful_persistent --manual-wait-seconds`: lets the user seed a real session.
4. Direct product URL instead of search URL.
5. Slower wait/scroll/card extraction once content loads.
6. Residential proxy only after session/profile/direct-product strategies still hit access gates.


## Agent Hardening Review Requirement

Before applying any change derived from agent analysis, write a compact review with these fields:

| Field | Requirement |
|---|---|
| Evidence | Link the artifact path, screenshot/HTML/report, and classification. |
| Hardening target | Name the CloakBrowser/runtime behavior to improve, such as persistent profile, wait mode, direct product URL handling, blocked-state return, selector rediscovery, or diagnostics. |
| Architecture impact | State whether the change touches diagnostics only, provider strategy, shared scraper contract, Flask endpoint, UI status semantics, or dependencies. |
| Predicted measurable effect | Give concrete, checkable estimates, e.g. "reduce repeated selector-misdiagnosis for blocked pages from current observed 2/2 to 0/5 on next five blocked artifacts". |
| Verification plan | Name the exact artifact replay, live probe, endpoint test, or screenshot review that can falsify the prediction. |
| Residual risk | State what may still fail and whether that risk threatens project values. |
| Handoff update | Record durable conclusions and predictions in `effective-verbal-context.md`. |

Do not accept an agent-only fix as complete when it can be turned into a stable CloakBrowser strategy, artifact classifier, provider status, or diagnostic rule.

## Verification

Every patch should have at least one of:

- offline classifier check against saved artifact JSON;
- live diagnostic run with a new artifact folder;
- backend endpoint test using a known loaded page;
- screenshot review when classification depends on visual state.

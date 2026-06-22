---
name: shopee-scrape-recovery
description: Diagnose and recover Shopee scraping failures in the data-phinter backend. Use when Shopee extraction or verification fails, a diagnostic artifact/report/screenshot is available, traffic verification or captcha blocks scraping, selectors stop working, product/search pages load without prices, or an agent needs to propose bounded source changes without hardcoding a brittle one-off bypass.
---

# Shopee Scrape Recovery

Use this skill to turn a Shopee scraping failure into evidence, classification, and a bounded next patch. The stable unit is not a selector or bypass trick; it is the failure artifact contract plus a repeatable recovery loop.

## Core Rule

Do not treat a Shopee failure as a price/selector failure until the artifact proves the page actually loaded product content. First classify access blocks, login/session gates, captcha, thin pages, timeouts, and loaded pages separately.

## Required Inputs

Prefer a diagnostic artifact folder produced by `tools/shopee_diagnostics.py` or an equivalent bundle containing:

- `artifact.json`: URL, final URL, title, classification, body excerpt, HTML/screenshot paths, strategy, counts.
- `page.html`: saved DOM.
- `screenshot.png`: visual confirmation.
- `report.md`: concise human-readable summary.

If no artifact exists, create one with the project harness:

```powershell
python tools/shopee_diagnostics.py --url "<shopee-url>" --strategy headless_ephemeral
```

For interactive session seeding, use:

```powershell
python tools/shopee_diagnostics.py --url "<shopee-url>" --strategy headful_persistent --manual-wait-seconds 180
```



## Pre-Use Disclosure

Before using this skill in a user-visible workflow, state a compact disclosure so the user can audit the decision later. Include:

- Skill name and path.
- Trigger: why this task falls under Shopee scrape recovery.
- Intended use: diagnosis, hardening review, source patch, artifact capture, or documentation-delta reporting.
- Expected inputs and outputs.
- Expected writes, live probes, browser launches, or escalated commands.
- Post-hoc audit surface: files, artifacts, commands, and the handoff/documentation delta the owner can inspect.

If the skill is used only for private reasoning and no files/tools are touched, still mention the trigger and intended use before acting.
## Agent Hardening Gate

Whenever an agent is used to analyze a Shopee failure, produce an Agent Hardening Review before proposing or applying a source change. The review must answer:

- What can be converted into a harder CloakBrowser/runtime strategy?
- What remains only a human/agent judgment, and why?
- What architecture boundaries are affected?
- What measurable improvement is predicted for similar future failures?
- What project values or current trade-offs are protected or weakened?

Use [references/quality-governance.md](references/quality-governance.md) for the required review template. If a proposed fix cannot plausibly harden the CloakBrowser pipeline, state that explicitly and treat it as an exception, not the normal path.

## Workflow

1. Read `artifact.json` first, then inspect `report.md` and screenshot if the classification is uncertain.
2. Classify using [references/failure-taxonomy.md](references/failure-taxonomy.md).
3. Decide whether the next action is diagnosis-only, a small probe, or a source patch.
4. Keep source changes inside provider/recovery boundaries: diagnostics harness, provider-specific Shopee module/strategy registry if introduced, and endpoint wiring only when the provider contract is stable.
5. Preserve raw artifacts. Do not overwrite evidence from failed runs.
6. Verify the smallest meaningful behavior after a change: classifier check, live probe, backend endpoint test, or screenshot review.
7. Report the exact durable handoff delta: strategies tried, taxonomy version, stored/current
   classification, artifact paths, pass/fail, and next action. Only the project owner applies that
   delta through the owner-held handoff-writing capability.

## Recovery Decision Tree

| Classification | Meaning | Next Action |
|---|---|---|
| `environment_network_blocked` | The diagnostic probe did not reach Shopee because sandbox/network/cache permissions blocked browser download or socket access. | Do not treat this as Shopee behavior. Either keep sandbox-only conclusion, preinstall the CloakBrowser binary, or ask the user before allowing network/cache access for a true binary test. |
| `access_blocked_or_session_required` | Shopee redirected to verification/login/traffic gate without a captcha marker, or showed a non-captcha access gate. | Try persistent headful with manual wait for first generic blocks. Reuse profile. Prefer direct product URL next. Consider proxy only after session/profile/direct-product strategies fail. |
| `captcha_required` | Shopee redirected to captcha or captcha/load-error challenge. | Keep this separate from selector failure; retry seeded persistent headful only if the user can solve it, then prefer direct product URL before proxy. |
| `login_required` | Page explicitly requires login but not a generic captcha/traffic block. | Seed persistent profile through manual login; do not patch selectors. |
| `navigation_timeout` | Browser did not finish navigation. | Capture partial state; retry with `domcontentloaded` or `commit`, longer wait, and screenshot. |
| `thin_or_empty_page` | Page body is too small for product content. | Retry with longer settle/scroll; classify as block if repeated. |
| `loaded_with_price_candidates` | Product/search content and prices exist. | Run selector rediscovery and map prices to product cards before patching extraction. |
| `loaded_without_price_candidates` | Product links/cards exist but no prices. | Inspect lazy loading, script data, scroll behavior, and hidden DOM. |
| `unknown_scrape_failure` | Evidence is insufficient. | Improve artifact capture before changing app logic. |

## Patch Policy

Read [references/patch-policy.md](references/patch-policy.md) before changing backend code. In short:

- Add classifications and strategy branches before broad rewrites.
- Return blocked/session-required states separately from "price not found".
- Avoid embedding volatile Shopee CSS classes in core backend without artifact evidence.
- Keep Lazada and generic BS4/Cloak behavior unaffected unless the artifact proves a shared bug.

## Useful Scripts

Use `scripts/classify_artifact.py` to reclassify saved artifacts offline:

```text
python "<active-skill-dir>/scripts/classify_artifact.py" diagnostics/shopee/<run>/artifact.json

# Repository-development fallback:
python .codex/skills/shopee-scrape-recovery/scripts/classify_artifact.py diagnostics/shopee/<run>/artifact.json
```

Claude plugin hosts can resolve `<active-skill-dir>` from `${CLAUDE_SKILL_DIR}`. Use the active
host's skill-directory mechanism when available; do not assume the `.codex` fallback exists in an
installed Claude/Cowork plugin.

## Related Plugin Architecture

From the `data-phinter-workflows` plugin root, read `references/overview.md` for the short entry map
and `references/architecture.md` for the conditional recovery loop back into app verification.

This is a smoke test for the skill taxonomy and does not launch a browser.

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

# Shopee Failure Taxonomy

Use this reference when an artifact classification is missing, suspicious, or needs refinement.

Current taxonomy version: `2`.

Saved artifacts are immutable observations. Reclassification under a newer taxonomy does not rewrite
the stored classification. Report both values, both taxonomy versions when known, and
`classification_changed`; choose the current recovery path from current evidence while preserving
the historical interpretation for provenance.

## Evidence Priority

1. `final_url` and `response_status`.
2. Screenshot and visible body text.
3. Body excerpt and page title.
4. Price candidate count and product link count.
5. Full HTML.
6. Prior assumptions or old scraper behavior.

## Classification Markers

| Classification | Strong Markers | Notes |
|---|---|---|
| `environment_network_blocked` | `WinError 10013`, socket access forbidden, `getaddrinfo failed`, CloakBrowser binary download failure, sandbox/network permission error before page capture. | This is an environment/sandbox result, not Shopee behavior. Do not infer captcha, selector failure, or proxy need from it. |
| `access_blocked_or_session_required` | `/verify/traffic`, `Page Unavailable`, `Please log in`, `traffic`, `verify`, screenshot showing login/error/verification card without a captcha marker. | Do not patch selectors. Treat as access/session strategy work. |
| `captcha_required` | `/verify/captcha`, captcha marker, screenshot showing captcha or Shopee captcha load-error card. | Treat as anti-bot challenge, not selector failure. Manual seeded profile and direct product URL probes come before proxy. |
| `login_required` | Explicit login page or `is_logged_in=false` without broader captcha/traffic challenge. | Persistent profile is the next useful experiment. |
| `navigation_timeout` | `TimeoutError` from `page.goto`, `wait_for_selector`, or `networkidle`. | Capture partial state and try a less strict wait mode before changing selectors. |
| `thin_or_empty_page` | Very small body/html, blank screenshot, no product links. | Could be blocked, slow/lazy rendering, or navigation failure. Gather another artifact. |
| `loaded_with_price_candidates` | Price candidate count > 0 and visible product/search content. | Now selector or card-mapping work is allowed. |
| `loaded_without_price_candidates` | Product links/cards exist but price count is 0. | Investigate lazy loading, scroll, hidden DOM, or script data. |
| `unknown_scrape_failure` | Evidence conflicts or does not match known categories. | Improve artifact capture first. |

## Anti-Patterns

- Do not call a Shopee row `Error` solely because `.price` or another selector failed.
- Do not treat tracking IDs or captcha tokens as price candidates.
- Do not assume proxy is required before trying persistent headful session seeding.
- Do not merge Lazada successes into Shopee assumptions.

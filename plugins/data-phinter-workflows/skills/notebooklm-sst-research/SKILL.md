---
name: notebooklm-sst-research
description: "Drive NotebookLM browser automation to generate new, diverse SST candidate CSV rows from the configured default-data exemplar. Use for NotebookLM Deep Research, recurring SST generation, candidate refreshes, aggregation to the strict target, or generation-stage analysis. This skill never merges into the default file, deduplicates against it for accumulation, or verifies live prices; those belong to the app intake workflow."
---

# NotebookLM SST Research (data-generation component)

Use NotebookLM's Deep Research + an exemplar to produce a **raw CSV of new product rows** for the
data-phinter SST dataset. Output is candidate data (URL + price + descriptive fields); verification,
dedup-vs-default, and accumulation are the app's job, not this skill's.

Complete the requested generation run before applying optional process improvements. Record anomalies,
missing evidence, and possible improvements during the run; present the outcome and proposals in a final
**Report, analyze, and advise/improve** step and ask whether to apply them to the next run. Interrupt
earlier only for authentication, quota, a true blocker, or a decision that changes the accepted output.

## Boundaries (do not cross — keeps components decoupled)
- Influence the result ONLY via two levers: (1) the **exemplar** (representative rows from the current
  default data file), and (2) an **appropriate prompt** that fixes OUTPUT FORMAT + non-duplication +
  count. NEVER hard-code niches/brands into the research prompt — that narrows Deep Research and creates
  systematic blind spots. General "diverse / don't duplicate the sample" nudges are fine.
- Do NOT merge/dedup vs the default file and do NOT coverage-gate here. Emit the raw NotebookLM CSV.
- The generation target applies to the candidate artifact itself: aggregate NotebookLM outputs until
  there are at least 100 complete, unique candidate URLs. The default file is an open-ended accumulated
  store, not part of this threshold. Report novelty vs default and combined-set coverage separately;
  neither may be used to stop a run while the candidate artifact is below 100.
- Before counting the target, exclude non-topic products and URLs that are clearly category,
  collection, search, blog, or article pages. A listing-like URL counts only when it is verified to
  represent one purchasable product.

## Inputs
- Default data file and a topic derived from it. Resolve the canonical path from
  `config/default-data.json` unless the user explicitly supplies a different file for this run.
  Ad-hoc files loaded through the app do not change this configuration.
- An exemplar CSV: build it with `python pipeline/build_exemplar.py --default-file <file>` (facet-stratified,
  stays current with the default file). Its niche-gap manifest is AUDIT info only — do not feed it to the prompt.
  When overlap audits remain high, improve the exemplar's representation of existing unique URLs or
  attach a compact URL-only exclusion index derived from the default file. Do not replace this with
  hard-coded brands, niches, or domains.

## Environment
- Drive NotebookLM at https://notebooklm.google.com through an installed Codex Browser Plugin or
  Chrome Plugin. Discover the current browser-control tools with `tool_search`; prefer Node
  REPL/Playwright control when that is the plugin's exposed interface.
- Do not depend on historical tool names such as `tabs_context_mcp` or `javascript_tool`. If no
  browser-control capability is installed or callable, stop and tell the user which Browser/Chrome
  capability is missing instead of silently replacing browser work with HTTP requests.
- The user must be logged into Google. If a login screen appears, STOP and ask the user to log in — never
  handle login yourself. Each Google account (`authuser=N`) has its own quota; the user may open a tab on a
  second account to reset quota.

## Workflow
0. Discover and connect to the installed Browser/Chrome Plugin, reuse the user's existing tab when
   available, then navigate to the notebook URL / notebooklm.google.com. Capture a screenshot or DOM
   state to confirm login. The renderer on this SPA **freezes intermittently on screenshot** — recover
   by re-navigating (reload) the same URL; server-side work is not lost.
1. **New notebook** (`+ Create notebook` / `+ Create new`).
2. **Add the exemplar as a "Copied text" source** (NOT file upload — file_upload of repo files is rejected
   with "only files shared with this session"). Prepend a clean one-line header, e.g.: "MẪU ĐỊNH DẠNG SST &
   DỮ LIỆU ĐÃ CÓ. Link = URL sản phẩm đầy đủ https://, HTML = đoạn HTML chứa giá. Sinh sản phẩm MỚI không
   trùng các dòng dưới." Then the exemplar CSV. Click Insert.
3. **Deep Research**: in the Sources "Search the web" box, switch the mode dropdown from "Fast Research" to
   **"Deep Research"**, type an UN-STEERED query (topic + "tối thiểu 100 sản phẩm, đa dạng, KHÔNG trùng bộ
   mẫu trong notebook" + fields: tên, thương hiệu, nguồn, URL sản phẩm đầy đủ, loại, khối lượng, giá VND,
   phí ship, ngưỡng freeship, khu vực; ưu tiên URL sản phẩm trực tiếp). Submit (blue arrow). Phases:
   Planning → Researching → Writing Report → "Deep Research completed!". Observed timing is commonly
   10–12 minutes; allow up to about 15 minutes before treating it as stuck. Poll after roughly 60 seconds,
   then every 90–180 seconds. Source ingestion is commonly about 1 minute and each Chat extraction about
   1–2 minutes.
4. **Import** the report + ~20 discovered sources.
5. **Extract** — TWO paths:
   - **Chat (PREFERRED — not Tables-limited, gives deep per-SKU URLs):** locate the chat input through
     the active browser tool's DOM/ref interface, click it, and prompt: "Xuất CSV
     (chỉ CSV), liệt kê CÀNG NHIỀU sản phẩm CÀNG TỐT, mỗi dòng 1 sản phẩm, mỗi SKU 1 URL riêng đầy đủ
     https://, HTML = đoạn HTML chứa giá. Header: Sản phẩm,Thương hiệu,Nguồn,Link,Loại SP,Đơn vị tính,Giá
     niêm yết (VND),HTML,TMĐT. Thiếu để trống, KHÔNG bịa." Press Return. Repeat with "tiếp tục… KHÔNG lặp
     lại sản phẩm đã liệt kê" for more. innerText joins rows with spaces (not newlines) and the price/HTML
     columns carry commas — parse with a URL+terminator-anchored regex:
     `([^,\n]+?),([^,\n]+?),([^,\n]+?),(https?://\S+?),([^,\n]+?),([^,\n]+?),([^,\n]+?),(.*?),(Không rõ)`.
   - **Studio → Data Table → customize** (quota ~3/account/day): set language Tiếng Việt, prompt to follow
     the exemplar's 15-col format, "LIỆT KÊ ĐẦY ĐỦ MỌI sản phẩm, mỗi SKU 1 URL riêng, ≥100 dòng, không bịa".
     The output is a real `<table>` in the DOM (not virtualized) — read it directly with the active
     browser tool or `page.evaluate` through Node REPL.
6. **Get the CSV to disk:** build the CSV into a Blob and trigger a download with a **unique filename**.
   Chrome **blocks repeated automatic downloads from one page** after the first — if a download doesn't
   land, re-open the notebook in a fresh tab (chat history persists) or ask the user to allow downloads.
   Tool result displays may truncate large content, so download (do not return) the data and return only counts.
7. Parse to the 15-col schema (`ID,Sản phẩm,Thương hiệu,Nguồn,Link,Loại SP,Đơn vị tính,Giá niêm yết (VND),
   Phí ship (VND),Ngưỡng Freeship (VND),Địa phương,HTML,Ngày Thêm,Tình trạng Giá,TMĐT`), save under
   `data_out/`. Hand off to `pipeline/aggregate_runs.py` (combine runs) — NOT to the default file.
8. After each aggregation, inspect source concentration, listing-like URLs, and topic validity. If one
   source supplies >=40% and time remains, request more products from underrepresented imported sources
   without naming a fixed source list. If the source pool itself is narrow, prefer another un-steered
   Deep Research pass over repeatedly asking Chat to expand the same dominant source.
9. Run the executable strict gate:

   `python pipeline/validate_candidates.py --input <final-candidate.csv> --target 100 --out <validation.json>`

   Update `config/current-candidate.json` only when this command exits successfully and reports
   `strict_complete: true`.

## Quality notes / known limits
- The exemplar-file fix is what gives full https URLs + price HTML (vs a prompt-only run which gave 0%).
- Chat HTML is often just price text (e.g. `₫18,500`), not a real selector — the app's verify step
  re-derives the real selector from the live page, so don't over-trust it.
- "Complete" for this skill's output = Link + Price; HTML/selector is the app's job.
- Deep Research finds missing niches (instant/capsule/decaf/specialty) ON ITS OWN when un-steered — trust it.
- AI-generated URLs frequently fail live verification (dead/redirect/JS) — output is candidates, not verified.

## Output contract
- One or more raw CSVs under `data_out/` per run + a final aggregated candidate CSV containing at least
  100 complete unique URLs + a short report (candidate rows, novelty vs default, union coverage, domains,
  % full-URL, % HTML). If time expires below 100, mark the run incomplete rather than calling it finished.
- Update `config/current-candidate.json` only after the strict target passes. Record `status` as
  `strict_completed`, `strict_complete: true`, the strict count, total candidate count, listing-like
  exclusions, run ID, and artifact path. A historical `accepted_with_known_risk` pointer may remain for
  provenance, but must never be interpreted as a current strict completion.
- Nothing merged into the default file; nothing verified. The plugin's other components do that.

## Related Plugin Architecture

From the `data-phinter-workflows` plugin root, read `references/overview.md` for the short entry map
and `references/architecture.md` for component boundaries and change-synchronization rules.

<!-- plugin-navigation:start -->
## Plugin Navigation

- [Short workflow overview](../../references/overview.md)
- [Detailed architecture](../../references/architecture.md)
- [Artifact and status contract](../../references/artifact-and-status-contract.md)
- [Runtime prerequisites and stop behavior](../../references/runtime-prerequisites.md)

When an accepted workflow improvement changes entry points, responsibilities, status contracts, or
decision gates, synchronize plugin-owned skills/references and report the required README/handoff
delta to the project owner. Do not assume the owner-held handoff-writing skill is bundled.
<!-- plugin-navigation:end -->

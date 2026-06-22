"""App-owned verify + accumulate for NotebookLM SST candidates.

Component boundary (see pipeline/NOTES.md): the *app* owns dedup-vs-default,
verification, and accumulation. The NotebookLM pipeline only produces the raw
candidate CSV. This script therefore lives under tools/ (app side), reuses the
app's own verification logic from app.py, and never edits the pipeline outputs.

What it does
------------
1. Dedup the candidate rows against the current default store by normalized
   product URL (Shopee by shopid.itemid). Duplicates are dropped, not verified.
2. Verify each NOVEL candidate by re-deriving evidence from the LIVE page --
   it does NOT trust the AI-supplied HTML/selector. It checks whether the
   candidate's claimed price actually appears on the rendered page. Selenium
   compatibility mode is the default; BS4 is an explicit fast option, and
   CloakBrowser is an explicit adaptive option after user approval.
3. Accumulate the verified novel rows into an accumulate-ready CSV. It does NOT
   overwrite the default store -- promoting verified rows into sample_data.csv
   is a separate, user-approved step.

match_count semantics (from app._verify_price_from_soup):
   -1  fetch failed   (dead URL / timeout / non-200 / blocked)
    0  page loaded, but the claimed price was absent
    1  price appears exactly once  (unique)
   >1  price appears multiple times (present but not unique -- normal for
       e-commerce: title + cart + meta, list + sale, etc.)

--accept controls which rows are written as "verified" for accumulation:
   unique   -> match_count == 1
   present  -> match_count >= 1   (price is live on the page; recommended)
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SCHEMA = [
    "ID", "Sản phẩm", "Thương hiệu", "Nguồn", "Link", "Loại SP", "Đơn vị tính",
    "Giá niêm yết (VND)", "Phí ship (VND)", "Ngưỡng Freeship (VND)", "Địa phương",
    "HTML", "Ngày Thêm", "Tình trạng Giá", "TMĐT",
]
PRICE_COL = "Giá niêm yết (VND)"
LINK_COL = "Link"


def log(*a):
    """All of OUR output goes to stderr, so the app's chatty stdout (sent to
    devnull during verification) never collides with it across threads."""
    print(*a, file=sys.stderr, flush=True)


def load_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_price(s):
    digits = re.sub(r"[^0-9]", "", (s or "").split("-")[0])
    return int(digits) if digits else None


def normalize_url(u, shopee_key):
    u = (u or "").strip()
    if not u:
        return ""
    key = shopee_key(u)
    if key:
        return "shopee:" + key
    try:
        p = urlparse(u if "://" in u else "https://" + u)
        host = p.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host + p.path.rstrip("/")
    except Exception:
        return u.lower()


def accept_fn(mode):
    return (lambda mc: mc == 1) if mode == "unique" else (lambda mc: mc is not None and mc >= 1)


def classify(mc):
    if mc is None:
        return "noprice"
    return {1: "verified"}.get(mc, "ambiguous" if mc > 1 else "absent" if mc == 0 else "dead")


def tally(match_counts):
    from collections import Counter
    return Counter(classify(mc) for mc in match_counts)


def write_outputs(novel_by_id, order, match_counts, accept, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, "notebooklm_verify_report.csv")
    verified_path = os.path.join(out_dir, "notebooklm_verified.csv")
    stage = match_counts.get("__stage__", {})

    with open(report_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ID", "Sản phẩm", "Link", PRICE_COL, "verify_stage",
                    "match_count", "price_present", "verified"])
        for cid in order:
            row = novel_by_id[cid]
            mc = match_counts.get(cid)
            w.writerow([cid, row.get("Sản phẩm"), row.get(LINK_COL),
                        row.get(PRICE_COL), stage.get(cid, ""), mc,
                        (mc is not None and mc >= 1), accept(mc)])

    verified_ids = [cid for cid in order if accept(match_counts.get(cid))]
    with open(verified_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SCHEMA, extrasaction="ignore")
        w.writeheader()
        for cid in verified_ids:
            out = {k: novel_by_id[cid].get(k, "") for k in SCHEMA}
            out["Tình trạng Giá"] = "Đã"
            w.writerow(out)
    return report_path, verified_path, len(verified_ids)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default="data_out/notebooklm_aggregated_linkprice.csv")
    ap.add_argument("--default", default="sample_data.csv")
    ap.add_argument("--out-dir", default="data_out")
    ap.add_argument(
        "--mode",
        choices=["fast", "compatible", "adaptive"],
        default="compatible",
        help="verification transport; adaptive must follow explicit user approval",
    )
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--accept", choices=["unique", "present"], default="present")
    ap.add_argument("--from-report", metavar="PATH",
                    help="rebuild outputs from an existing report (no network); applies --accept")
    args = ap.parse_args()
    os.chdir(ROOT)
    accept = accept_fn(args.accept)

    cand = load_rows(args.candidates)
    cand_by_id = {r["ID"]: r for r in cand}

    # ---- no-network rebuild from an existing report ----
    if args.from_report:
        rep = load_rows(args.from_report)
        order = [r["ID"] for r in rep]
        novel_by_id = {r["ID"]: cand_by_id.get(r["ID"], r) for r in rep}
        mcs = {}
        for r in rep:
            v = r.get("match_count")
            mcs[r["ID"]] = None if v in ("", "None", None) else int(v)
        mcs["__stage__"] = {r["ID"]: r.get("verify_stage", "") for r in rep}
        t = tally([mcs[c] for c in order])
        log(f"[from-report] accept={args.accept}  {dict(t)}")
        rp, vp, n = write_outputs(novel_by_id, order, mcs, accept, args.out_dir)
        log(f"report  -> {rp}\nverified-> {vp}  ({n} accumulate-ready rows)")
        return

    from app import verify_price_bs4, verify_price_cloak, verify_price_selenium
    from providers.shopee import product_key_from_href

    def shopee_key(u):
        try:
            return product_key_from_href(u)
        except Exception:
            return None

    default = load_rows(args.default)
    default_keys = {normalize_url(r.get(LINK_COL), shopee_key) for r in default}
    novel = [r for r in cand if normalize_url(r.get(LINK_COL), shopee_key) not in default_keys]
    log(f"candidates={len(cand)}  duplicate_vs_default={len(cand)-len(novel)}  novel={len(novel)}")

    novel_by_id = {r["ID"]: r for r in novel}
    order = [r["ID"] for r in novel]
    match_counts = {"__stage__": {}}

    devnull = open(os.devnull, "w", encoding="utf-8", errors="replace")
    real_stdout = sys.stdout
    sys.stdout = devnull  # silence app's verify prints for the whole run
    try:
        def verify_one(cid, verifier):
            row = novel_by_id[cid]
            price = parse_price(row.get(PRICE_COL))
            if price is None:
                return cid, None
            return cid, verifier(row.get(LINK_COL), price)["min_count"]

        verifier = {
            "fast": verify_price_bs4,
            "compatible": verify_price_selenium,
            "adaptive": verify_price_cloak,
        }[args.mode]
        workers = args.workers if args.mode == "fast" else 1
        log(f"[{args.mode}] verifying {len(order)} novel candidates ({workers} workers)...")
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(verify_one, cid, verifier): cid for cid in order}
            done = 0
            for future in as_completed(futures):
                cid, mc = future.result()
                match_counts[cid] = mc
                match_counts["__stage__"][cid] = args.mode
                done += 1
                if done % 25 == 0:
                    log(f"   ...{done}/{len(order)}")
        log(f"[{args.mode}] {dict(tally([match_counts[c] for c in order]))}")
    finally:
        sys.stdout = real_stdout
        devnull.close()

    rp, vp, n = write_outputs(novel_by_id, order, match_counts, accept, args.out_dir)
    log(f"\nreport  -> {rp}")
    log(f"verified-> {vp}  ({n} accumulate-ready rows, accept={args.accept})")


if __name__ == "__main__":
    main()

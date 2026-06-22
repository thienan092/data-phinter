"""
aggregate_runs.py — Accumulate the QUALITY results of multiple NotebookLM calls into one
strict aggregated result set, to reach >=100 rows across runs.

Boundary note: this aggregates NotebookLM OUTPUTS *among themselves* only. It deliberately
does NOT read, merge into, or dedup against the default data file (`sample_data.csv`) — that
remains the data-phinter app's responsibility. Here we only:
  - combine several NotebookLM result CSVs,
  - drop rows that fail the shared strict-candidate contract,
  - dedup by product URL identity ACROSS the runs (so re-found products aren't double counted),
  - reassign sequential IDs, and report the running total vs a target.

Usage:
  python pipeline/aggregate_runs.py --inputs "data_out/notebooklm_coffee_v*_raw_*.csv" \
      --out data_out/notebooklm_aggregated.csv --target 100
"""
import argparse, csv, glob, json, sys
from collections import OrderedDict, Counter
from pathlib import Path

from candidate_quality import analyze_rows, normalized_url, row_exclusion_reasons


SCHEMA = ["ID", "Sản phẩm", "Thương hiệu", "Nguồn", "Link", "Loại SP", "Đơn vị tính",
          "Giá niêm yết (VND)", "Phí ship (VND)", "Ngưỡng Freeship (VND)", "Địa phương",
          "HTML", "Ngày Thêm", "Tình trạng Giá", "TMĐT"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True, help="glob(s) of NotebookLM result CSVs")
    ap.add_argument("--out", default="data_out/notebooklm_aggregated.csv")
    ap.add_argument("--target", type=int, default=100)
    ap.add_argument("--report", help="optional strict-validation JSON report path")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    paths = []
    for pat in args.inputs:
        paths.extend(sorted(glob.glob(pat)))
    seen, agg = OrderedDict(), []
    per_file = {}
    for p in paths:
        with open(p, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        kept = 0
        for r in rows:
            if row_exclusion_reasons(r):
                continue
            k = normalized_url(r.get("Link", ""))
            if k in seen:
                continue
            seen[k] = 1
            agg.append(r); kept += 1
        per_file[p] = (len(rows), kept)

    for i, r in enumerate(agg, 1):
        r["ID"] = "NB%04d" % i

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SCHEMA, extrasaction="ignore")
        w.writeheader()
        w.writerows(agg)

    print("inputs:")
    for p, (raw, kept) in per_file.items():
        print(f"  {p}: raw={raw} kept(new+complete)={kept}")
    analysis = analyze_rows(agg, target=args.target)
    status = "STRICT_REACHED" if analysis["strict_complete"] else (
        f"STRICT_SHORT_BY_{analysis['shortfall']}"
    )
    print(
        f"AGGREGATED strict rows = {analysis['strict_candidate_rows']} "
        f"(target {args.target}: {status})"
    )
    print("strict exclusions:", analysis["excluded"])
    print("domains:", dict(Counter((r.get('Nguồn') or '').strip() for r in agg)))
    print(f"wrote {args.out}")
    if args.report:
        report = {key: value for key, value in analysis.items() if key != "strict_rows"}
        report["output"] = args.out
        Path(args.report).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0 if analysis["strict_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

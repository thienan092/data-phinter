"""Validate a candidate CSV against the strict NotebookLM completion contract."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from candidate_quality import analyze_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    analysis = analyze_rows(rows, target=args.target)
    report = {key: value for key, value in analysis.items() if key != "strict_rows"}
    report["input"] = str(args.input)
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if analysis["strict_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

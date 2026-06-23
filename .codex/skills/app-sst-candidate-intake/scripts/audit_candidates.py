import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "pipeline"))
from candidate_quality import analyze_rows, host, normalized_url  # noqa: E402


def load_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames or []
    return path, fields, rows


def add_finding(findings, code, severity, message, evidence):
    findings.append(
        {"code": code, "severity": severity, "message": message, "evidence": evidence}
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", help="Path to workspace directory")
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--out")
    args = parser.parse_args()

    if args.workspace:
        ws = Path(args.workspace).resolve()
        default_path_arg = ws / "default.csv"
        candidate_path_arg = ws / "candidate.csv"
    else:
        default_path_arg = ROOT / "sample_data.csv"
        candidate_path_arg = ROOT / "candidate_sample.csv"

    default_path, default_fields, default_rows = load_csv(default_path_arg)
    
    if not candidate_path_arg.exists():
        raise SystemExit(f"Candidate file not found: {candidate_path_arg}")
    candidate_path, candidate_fields, candidate_rows = load_csv(candidate_path_arg)

    if len(default_fields) < 12 or len(candidate_fields) < 12:
        raise SystemExit("Configured CSV does not match the canonical SST schema")

    default_link = default_fields[4]
    candidate_link = candidate_fields[4]
    default_urls = [normalized_url(row.get(default_link)) for row in default_rows]
    candidate_urls = [normalized_url(row.get(candidate_link)) for row in candidate_rows]
    default_set = {url for url in default_urls if url}
    candidate_set = {url for url in candidate_urls if url}

    strict = analyze_rows(candidate_rows, target=args.target)
    hosts = Counter(
        host(row.get(candidate_link))
        for row in candidate_rows
        if normalized_url(row.get(candidate_link))
    )
    top_host, top_count = hosts.most_common(1)[0] if hosts else ("", 0)
    top_share = top_count / len(candidate_rows) if candidate_rows else 0
    overlap = candidate_set & default_set
    overlap_share = len(overlap) / len(candidate_set) if candidate_set else 0

    findings = []
    if strict["strict_candidate_rows"] < args.target:
        add_finding(
            findings,
            "strict_candidate_target_shortfall",
            "blocker",
            "Candidate artifact is below its strict target after all exclusions.",
            {
                "target": args.target,
                "strict_candidates": strict["strict_candidate_rows"],
                "shortfall": strict["shortfall"],
            },
        )
    if strict["duplicate_rows"]:
        add_finding(
            findings,
            "candidate_internal_duplicates",
            "blocker",
            "Candidate artifact still contains duplicate product URLs.",
            {"duplicate_rows": strict["duplicate_rows"]},
        )
    incomplete_count = sum(
        strict["excluded"].get(code, 0)
        for code in ("invalid_or_missing_url", "missing_price")
    )
    if incomplete_count:
        add_finding(
            findings,
            "candidate_incomplete_rows",
            "blocker",
            "Candidate rows are missing a direct URL or listed price.",
            {"rows": incomplete_count},
        )
    if strict["excluded"].get("non_topic_product_type"):
        add_finding(
            findings,
            "candidate_non_topic_rows",
            "blocker",
            "Candidate artifact contains known non-coffee product types.",
            {"rows": strict["excluded"]["non_topic_product_type"]},
        )
    if top_share >= 0.40:
        add_finding(
            findings,
            "source_concentration",
            "review",
            "One source dominates the candidate artifact and may bias coverage.",
            {"host": top_host, "rows": top_count, "share": round(top_share, 4)},
        )
    if overlap_share >= 0.20:
        add_finding(
            findings,
            "high_default_overlap",
            "review",
            "A substantial share of candidate URLs already exists in the default store.",
            {"overlap_urls": len(overlap), "share": round(overlap_share, 4)},
        )
    if strict["excluded"].get("listing_like_url"):
        add_finding(
            findings,
            "listing_like_urls",
            "blocker",
            "Candidate artifact contains listing-like URLs excluded by the strict contract.",
            {"rows": strict["excluded"]["listing_like_url"]},
        )
    # Strict completion check no longer relies on a JSON config file
    # Instead, we just check if the strict target is met.
    if strict["strict_candidate_rows"] < args.target:
        add_finding(
            findings,
            "candidate_pointer_not_strict_complete",
            "blocker",
            "The candidate artifact has not met the strict target of unique valid URLs.",
            {
                "status": "incomplete",
                "strict_complete": False,
            },
        )

    severity_rank = {"notice": 0, "review": 1, "blocker": 2}
    highest = max((severity_rank[item["severity"]] for item in findings), default=0)
    decision = "proceed" if highest == 0 else ("user_review" if highest == 1 else "stop")

    report = {
        "status": decision,
        "user_decision_required": decision != "proceed",
        "default": {
            "path": str(default_path),
            "rows": len(default_rows),
            "unique_urls": len(default_set),
        },
        "candidate": {
            "path": str(candidate_path),
            "rows": len(candidate_rows),
            "strict_candidate_rows": strict["strict_candidate_rows"],
            "unique_urls": len(candidate_set),
            "target": args.target,
            "strict_candidate_rows": strict["strict_candidate_rows"],
            "strict_complete": strict["strict_complete"],
            "strict_exclusions": strict["excluded"],
            "novel_vs_default": len(candidate_set - default_set),
            "overlap_with_default": len(overlap),
            "distinct_hosts": len(hosts),
            "top_hosts": hosts.most_common(10),
        },
        "simulated_union_unique_urls": len(default_set | candidate_set),
        "findings": findings,
    }

    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

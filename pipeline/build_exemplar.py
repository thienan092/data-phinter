"""
build_exemplar.py — Build a coverage-representative "file chứa mẫu" (exemplar) from the
current "file dữ liệu mặc định" (default data file, e.g. sample_data.csv).

Goal (per project workflow):
  * The exemplar sent to NotebookLM must stay SEMANTICALLY CURRENT with the default file
    => it is regenerated from that file every run (no hardcoding, topic-agnostic).
  * It must REPRESENT the niches of the default data (facet-stratified, not naive 1/domain)
    so NotebookLM (a) copies the right 15-col format incl. full URL + HTML price snippet,
    and (b) has a faithful anti-duplication anchor.
  * It also reports NICHE GAPS as audit-only evidence. Do not feed those gaps into the Deep
    Research prompt; the current workflow avoids niche/brand/domain steering.

Auditable by Codex: deterministic, prints a coverage manifest comparing exemplar vs default.

Usage:
  python pipeline/build_exemplar.py --default-file sample_data.csv \
      --out-exemplar pipeline/exemplar.csv --out-manifest pipeline/exemplar_manifest.json
"""
import argparse, csv, json, re, sys
from collections import Counter, OrderedDict

# Niche keywords used only to audit exemplar/default representation. A near-zero count is reported
# for analysis, not converted into a generation prompt target.
NICHE_KEYWORDS = [
    "hòa tan", "instant", "capsule", "viên nén", "pod", "cold brew", "decaf",
    "khử caffein", "túi lọc", "drip", "phin giấy", "gift", "quà", "đặc sản",
    "fine robusta", "gesha", "typica", "bourbon", "cầu đất", "đắk lắk", "sơn la",
    "pleiku", "đà lạt", "buôn ma thuột",
]
MARKETPLACE = ["shopee", "lazada", "tiki", "sendo", "bachhoaxanh", "winmart", "shop.highlands"]


def norm(s):
    return (s or "").strip()


def url_ident(r):
    return norm(r.get("Link")).lower().split("?")[0].rstrip("/")


def facet_type(r):
    t = (r.get("Loại SP") or "").lower()
    for k in ["culi", "moka", "gesha", "typica", "bourbon", "honey", "specialty", "arabica", "robusta", "blend"]:
        if k in t:
            return k
    return "other"


def facet_unit(r):
    u = (r.get("Đơn vị tính") or "").lower()
    m = re.search(r"(\d+)\s*(kg|g|gói|ml)", u)
    if not m:
        return "khác"
    n = int(m.group(1)); unit = m.group(2)
    grams = n * 1000 if unit == "kg" else n
    if unit in ("gói", "ml"):
        return unit
    return "<=200g" if grams <= 200 else "201-400g" if grams <= 400 else ">400g"


def facet_tier(r):
    g = re.sub(r"[^\d]", "", r.get("Giá niêm yết (VND)") or "")
    if not g:
        return "?"
    g = int(g)
    return ("<50k" if g < 50000 else "50-100k" if g < 100000 else
            "100-200k" if g < 200000 else "200-400k" if g < 400000 else ">=400k")


def facet_platform(r):
    d = (r.get("Nguồn") or "").lower()
    return "marketplace" if any(m in d for m in MARKETPLACE) else "website"


def facet_region(r):
    return norm(r.get("Địa phương")) or "?"


FACETS = OrderedDict([
    ("brand", lambda r: norm(r.get("Thương hiệu")).lower()),
    ("type", facet_type),
    ("unit", facet_unit),
    ("tier", facet_tier),
    ("platform", facet_platform),
    ("region", facet_region),
])


def is_complete(r):
    return (norm(r.get("Link")).lower().startswith("http")
            and bool(norm(r.get("HTML"))) and bool(norm(r.get("Giá niêm yết (VND)"))))


def facet_dist(rows):
    return {name: dict(Counter(fn(r) for r in rows)) for name, fn in FACETS.items()}


def select_exemplar(rows, max_rows):
    """Greedy facet set-cover: pick complete rows that add the most uncovered facet-values,
    then round-robin by brand to fill up to max_rows. Deterministic."""
    pool = [r for r in rows if is_complete(r)] or rows
    covered = {name: set() for name in FACETS}
    chosen, chosen_ids = [], set()

    def gain(r):
        return sum(1 for name, fn in FACETS.items() if fn(r) not in covered[name])

    # Phase 1: maximize facet coverage
    while len(chosen) < max_rows:
        best = max(pool, key=lambda r: (gain(r), -len(r.get("Sản phẩm", ""))), default=None)
        if best is None or gain(best) == 0:
            break
        chosen.append(best); chosen_ids.add(url_ident(best))
        for name, fn in FACETS.items():
            covered[name].add(fn(best))
        pool = [r for r in pool if url_ident(r) not in chosen_ids]

    # Phase 2: fill remaining slots round-robin by brand for breadth
    by_brand = OrderedDict()
    for r in rows:
        if url_ident(r) in chosen_ids:
            continue
        by_brand.setdefault(FACETS["brand"](r), []).append(r)
    while len(chosen) < max_rows and any(by_brand.values()):
        for b in list(by_brand):
            if len(chosen) >= max_rows:
                break
            if by_brand[b]:
                r = by_brand[b].pop(0)
                if url_ident(r) not in chosen_ids:
                    chosen.append(r); chosen_ids.add(url_ident(r))
    return chosen


def niche_gaps(rows):
    blob = " ".join((r.get("Sản phẩm", "") + " " + r.get("Loại SP", "")).lower() for r in rows)
    counts = {kw: blob.count(kw) for kw in NICHE_KEYWORDS}
    gaps = [kw for kw, c in counts.items() if c == 0]
    weak = [kw for kw, c in counts.items() if c == 1]
    return counts, gaps, weak


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--default-file", default="sample_data.csv")
    ap.add_argument("--out-exemplar", default="pipeline/exemplar.csv")
    ap.add_argument("--out-manifest", default="pipeline/exemplar_manifest.json")
    ap.add_argument("--max-rows", type=int, default=28)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    with open(args.default_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # dedupe by URL identity (default file may carry many duplicate rows)
    uniq = OrderedDict()
    for r in rows:
        uniq.setdefault(url_ident(r), r)
    U = list(uniq.values())

    exemplar = select_exemplar(U, args.max_rows)
    counts, gaps, weak = niche_gaps(U)

    with open(args.out_exemplar, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(exemplar)

    manifest = {
        "default_file": args.default_file,
        "default_rows_raw": len(rows),
        "default_rows_unique": len(U),
        "exemplar_rows": len(exemplar),
        "default_facets": facet_dist(U),
        "exemplar_facets": facet_dist(exemplar),
        "facet_coverage_ratio": {
            name: round(len(set(fn(r) for r in exemplar)) / max(1, len(set(fn(r) for r in U))), 3)
            for name, fn in FACETS.items()
        },
        "niche_keyword_counts": counts,
        "niche_gaps_to_target": gaps,
        "niche_weak_to_reinforce": weak,
    }
    with open(args.out_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"default: {len(rows)} raw -> {len(U)} unique | exemplar: {len(exemplar)} rows")
    print("facet coverage ratio (exemplar/default):", manifest["facet_coverage_ratio"])
    print("niche gaps to target:", gaps)
    print("niche weak to reinforce:", weak)
    print(f"wrote {args.out_exemplar} and {args.out_manifest}")


if __name__ == "__main__":
    main()

"""LEGACY_UNSUPPORTED: old steered NotebookLM request builder.

This helper predates the current un-steered generation contract and is retained only to explain
historical artifacts. It embeds covered domains/brands and gap-oriented steering, so it must not be
used by `notebooklm-sst-research` or recurring automation.

Adaptive representative-example selection (diversity sampling), generalizable to
any topic that uses the data-phinter canonical SST schema:

  ID, Sản phẩm, Thương hiệu, Nguồn, Link, Loại SP, Đơn vị tính,
  Giá niêm yết (VND), Phí ship (VND), Ngưỡng Freeship (VND), Địa phương,
  HTML, Ngày Thêm, Tình trạng Giá, TMĐT

It does NOT call NotebookLM. It only:
  1. reads an existing SST CSV (the accumulated "notebook"),
  2. computes a compact coverage profile over facets,
  3. picks ~1 representative per domain (medoid by price) capped to a budget,
  4. writes a ready-to-paste NotebookLM request prompt to an output .md.

Usage:
  python pipeline/build_request.py --store sample_data.csv \
      --topic "cà phê rang/xay/hạt bán lẻ Việt Nam" \
      --min-records 100 --budget 15 --out data_out/notebooklm_request_coffee.md
"""
import argparse
import csv
import os
import re
from collections import Counter, defaultdict


def parse_price(raw: str):
    """Return integer VND price, or None if not parseable / non-VND (e.g. USD)."""
    if not raw:
        return None
    if "$" in raw:
        return None  # foreign-currency outlier; keep out of VND price stats
    digits = re.sub(r"[^\d]", "", raw)
    return int(digits) if digits else None


def domain_of(row):
    return (row.get("Nguồn") or "").strip().lower() or "(none)"


def load_store(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def coverage_profile(rows):
    prof = {
        "domains": Counter(domain_of(r) for r in rows),
        "brands": Counter((r.get("Thương hiệu") or "").strip() for r in rows),
        "units": Counter((r.get("Đơn vị tính") or "").strip() for r in rows),
        "regions": Counter((r.get("Địa phương") or "").strip() for r in rows),
        "marketplaces": Counter((r.get("TMĐT") or "").strip() for r in rows),
    }
    prices = [p for p in (parse_price(r.get("Giá niêm yết (VND)")) for r in rows) if p]
    prof["price_min"] = min(prices) if prices else None
    prof["price_max"] = max(prices) if prices else None
    return prof


def representatives(rows, budget):
    """One medoid-by-price representative per domain, spread to fill the budget."""
    by_domain = defaultdict(list)
    for r in rows:
        by_domain[domain_of(r)].append(r)
    reps = []
    for dom, drows in by_domain.items():
        priced = sorted(
            (r for r in drows if parse_price(r.get("Giá niêm yết (VND)"))),
            key=lambda r: parse_price(r.get("Giá niêm yết (VND)")),
        )
        pick = priced[len(priced) // 2] if priced else drows[0]  # median price row
        reps.append(pick)
    # most-covered domains first so the budget spends on the dominant clusters
    reps.sort(key=lambda r: -len(by_domain[domain_of(r)]))
    return reps[:budget]


def fmt_exemplar(r):
    return (
        f"- {r.get('Sản phẩm','').strip()} | {r.get('Thương hiệu','').strip()} | "
        f"{domain_of(r)} | {r.get('Loại SP','').strip()} | "
        f"{r.get('Đơn vị tính','').strip()} | {r.get('Giá niêm yết (VND)','').strip()} VND"
    )


def build_prompt(topic, schema_headers, prof, reps, min_records):
    domains_sorted = [d for d, _ in prof["domains"].most_common()]
    brands_sorted = [b for b, _ in prof["brands"].most_common() if b]
    lines = []
    lines.append(f"# Yêu cầu nghiên cứu dữ liệu thị trường: {topic}")
    lines.append("")
    lines.append(
        f"Hãy nghiên cứu và trả về **ít nhất {min_records} sản phẩm** đang bán trực tuyến "
        f"cho chủ đề: **{topic}** (giá mới nhất hiện tại)."
    )
    lines.append("")
    lines.append("## Định dạng đầu ra (BẮT BUỘC)")
    lines.append("Trả về một bảng CSV/Markdown với ĐÚNG các cột sau, theo đúng thứ tự:")
    lines.append("")
    lines.append("`" + ", ".join(schema_headers) + "`")
    lines.append("")
    lines.append("Quy tắc từng cột:")
    lines.append("- **Link**: URL TRANG SẢN PHẨM TRỰC TIẾP, thật, đang sống (không phải trang chủ/tìm kiếm).")
    lines.append("- **HTML**: hoặc snippet HTML chứa giá (vd `<span class=\"price\">88.000₫</span>`) "
                 "HOẶC một CSS selector trỏ đúng phần tử giá (vd `span.product-price`).")
    lines.append("- **Giá niêm yết (VND)**: số tiền hiển thị trên trang đó (đúng theo Link & HTML).")
    lines.append("- **Đơn vị tính**: khối lượng/quy cách (vd `250 g`, `500 g`, `1 kg`).")
    lines.append("- **TMĐT**: sàn nếu là marketplace (Shopee/Lazada/Tiki/...), nếu là web hãng để `Không rõ`.")
    lines.append("- **ID/Ngày Thêm/Tình trạng Giá**: để trống, ứng dụng sẽ tự gán.")
    lines.append("")
    lines.append("## Yêu cầu ĐA DẠNG (quan trọng nhất)")
    lines.append(
        f"Bộ dữ liệu hiện đã có {sum(prof['domains'].values())} dòng, tập trung vào các nguồn/thương hiệu dưới đây. "
        "Hãy nghiên cứu các sản phẩm **MỚI, KHÁC BIỆT** so với chúng — ưu tiên thương hiệu/nhà rang/nhà bán lẻ "
        "CHƯA có trong danh sách, vùng miền khác (Hà Nội, Đà Nẵng, miền Tây...), phân khúc giá và quy cách khác, "
        "và cả các sàn TMĐT chưa được phủ. **Tránh lặp lại** các domain/sản phẩm đã liệt kê."
    )
    lines.append("")
    lines.append(f"**Domain đã phủ (tránh trùng):** {', '.join(domains_sorted)}")
    lines.append("")
    lines.append(f"**Thương hiệu đã phủ (tránh trùng):** {', '.join(brands_sorted)}")
    lines.append("")
    lines.append(
        f"**Dải giá đã phủ:** {prof['price_min']:,}–{prof['price_max']:,} VND. "
        "Hãy phủ thêm cả phân khúc thấp và cao ngoài dải này nếu có."
    )
    lines.append("")
    lines.append("## Ví dụ điển hình của dữ liệu hiện có (để biết KHÔNG nghiên cứu trùng)")
    lines.extend(fmt_exemplar(r) for r in reps)
    lines.append("")
    lines.append("## Ràng buộc số lượng")
    lines.append(
        f"- Tối thiểu {min_records} record. Nếu cho rằng không gian thị trường có ít hơn {min_records} sản phẩm, "
        "hãy NÓI RÕ lý do và liệt kê các nguồn đã rà, để người dùng kiểm chứng — đừng tự ý dừng sớm."
    )
    lines.append("- Mỗi record là một sản phẩm/biến thể có thể mua thật, kèm Link + giá khớp nhau.")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--allow-legacy-steering",
        action="store_true",
        help="explicitly acknowledge generation of an unsupported historical prompt",
    )
    ap.add_argument("--store", default="sample_data.csv")
    ap.add_argument("--topic", default="cà phê rang/xay/hạt bán lẻ Việt Nam")
    ap.add_argument("--min-records", type=int, default=100)
    ap.add_argument("--budget", type=int, default=15)
    ap.add_argument("--out", default="data_out/notebooklm_request_coffee.md")
    args = ap.parse_args()
    if not args.allow_legacy_steering:
        ap.error(
            "build_request.py is legacy and conflicts with the current un-steered workflow; "
            "use pipeline/build_exemplar.py and notebooklm-sst-research instead"
        )

    rows = load_store(args.store)
    headers = list(rows[0].keys()) if rows else []
    prof = coverage_profile(rows)
    reps = representatives(rows, args.budget)
    prompt = build_prompt(args.topic, headers, prof, reps, args.min_records)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(prompt + "\n")

    print(f"store rows: {len(rows)}")
    print(f"distinct domains: {len(prof['domains'])}, distinct brands: {len(prof['brands'])}")
    print(f"price range VND: {prof['price_min']}-{prof['price_max']}")
    print(f"representatives selected: {len(reps)}")
    print(f"request written to: {args.out}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cloakbrowser.browser import launch_persistent_context

from providers.shopee import (
    DEFAULT_PROFILE_DIR,
    apply_true_cloak_env,
    env_value,
    restore_env,
    shopee_cloak_args,
    url_without_query,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open the persistent Shopee profile for manual login.")
    parser.add_argument("--wait-seconds", type=int, default=300)
    parser.add_argument("--url", default="https://shopee.vn/buyer/login")
    parser.add_argument("--profile-dir", default=None)
    parser.add_argument("--out-dir", default="diagnostics/shopee-profile-seed")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    previous_env = apply_true_cloak_env()
    context = None
    run_dir = Path(args.out_dir) / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    run_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "profile_dir": args.profile_dir or env_value("SHOPEE_CLOAK_PROFILE_DIR", DEFAULT_PROFILE_DIR),
        "fingerprint_args": shopee_cloak_args(),
        "requested_url": url_without_query(args.url),
        "wait_seconds": max(0, args.wait_seconds),
        "final_url": None,
        "error": None,
    }
    try:
        context = launch_persistent_context(
            report["profile_dir"],
            headless=False,
            humanize=True,
            human_preset="careful",
            args=shopee_cloak_args(),
            locale="vi-VN",
            timezone="Asia/Ho_Chi_Minh",
            viewport=None,
        )
        page = context.new_page()
        page.goto(args.url, timeout=60000, wait_until="domcontentloaded")
        print(f"Shopee profile window is open for {report['wait_seconds']} seconds.", flush=True)
        time.sleep(report["wait_seconds"])
        report["final_url"] = url_without_query(page.url)
        page.screenshot(path=str(run_dir / "page.png"), full_page=False, timeout=10000)
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if context is not None:
            try:
                context.close()
            except Exception as exc:
                report["close_error"] = f"{type(exc).__name__}: {exc}"
        restore_env(previous_env)
        report["finished_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        (run_dir / "report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(str(run_dir / "report.json"), flush=True)
    return 0 if report["error"] is None else 1


if __name__ == "__main__":
    raise SystemExit(main())

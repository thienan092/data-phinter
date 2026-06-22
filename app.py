import os
import platform
import sys
import json
import csv
import hmac
import ipaddress
from pathlib import Path
from app_accumulation import build_accumulation_plan, commit_accumulation

import re
import requests
from flask import Flask, request, jsonify, redirect, send_file, send_from_directory
from flask_cors import CORS
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from manual_actions import get_manual_action, record_client_event, record_verification_url_opened
from providers.shopee import (
    extract_price_shopee,
    http_status_for as shopee_http_status_for,
    is_shopee_url,
    verify_price_shopee,
)

# CloakBrowser imports
from cloakbrowser import launch

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_CONFIG = PROJECT_ROOT / "config" / "default-data.json"
CANDIDATE_DATA_CONFIG = PROJECT_ROOT / "config" / "current-candidate.json"
VERIFICATION_CONFIG = PROJECT_ROOT / "config" / "current-verification.json"
MODE_ALIASES = {
    "fast": "fast",
    "bs4": "fast",
    "compatible": "compatible",
    "selenium": "compatible",
    "adaptive": "adaptive",
    "cloak": "adaptive",
    "cloakbrowser": "adaptive",
}
DEFAULT_MODE = MODE_ALIASES.get(
    os.environ.get("DATA_PHINTER_VERIFICATION_MODE", "compatible").strip().lower(),
    "compatible",
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

# ========== CLOAKBROWSER ==========

def get_cloak_browser():
    proxy = os.environ.get("CLOAK_PROXY")
    proxy_dict = {"server": proxy} if proxy else None
    # Default to headless=True as requested, with humanize=True for stealth
    return launch(headless=True, humanize=True, proxy=proxy_dict)


def find_cached_selenium_pair(cache_root=None):
    cache_root = Path(cache_root or (Path.home() / ".cache" / "selenium"))
    driver_name = "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
    browser_name = "chrome.exe" if platform.system() == "Windows" else "chrome"
    pairs = []
    for driver_path in cache_root.glob(f"chromedriver/*/*/{driver_name}"):
        platform_name = driver_path.parent.parent.name
        version = driver_path.parent.name
        browser_path = cache_root / "chrome" / platform_name / version / browser_name
        if browser_path.is_file():
            version_key = tuple(
                int(part) if part.isdigit() else 0
                for part in version.split(".")
            )
            pairs.append((version_key, driver_path, browser_path))
    if not pairs:
        return None, None
    _, driver_path, browser_path = max(pairs, key=lambda item: item[0])
    return driver_path, browser_path


def get_selenium_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    driver_path = os.environ.get("CHROMEDRIVER_PATH")
    browser_path = os.environ.get("CHROME_BINARY")
    if not driver_path and not browser_path:
        cached_driver, cached_browser = find_cached_selenium_pair()
        driver_path = str(cached_driver) if cached_driver else None
        browser_path = str(cached_browser) if cached_browser else None
    if browser_path:
        options.binary_location = browser_path
    service = Service(executable_path=driver_path) if driver_path else Service()
    return webdriver.Chrome(service=service, options=options)


def _price_from_jsonld(soup):
    for script in soup.select("script[type='application/ld+json']"):
        try:
            root = json.loads(script.string or script.get_text())
        except (TypeError, json.JSONDecodeError):
            continue
        stack = root if isinstance(root, list) else [root]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
                continue
            if not isinstance(node, dict):
                continue
            node_type = node.get("@type")
            if node_type == "Product" or (isinstance(node_type, list) and "Product" in node_type):
                offers = node.get("offers")
                offer_list = offers if isinstance(offers, list) else [offers]
                for offer in offer_list:
                    if not isinstance(offer, dict):
                        continue
                    for key in ("price", "lowPrice"):
                        value = offer.get(key)
                        digits = re.sub(r"[^0-9]", "", str(value or ""))
                        if digits:
                            return int(digits)
            stack.extend(value for value in node.values() if isinstance(value, (dict, list)))
    return None


def _extract_price_from_soup(soup, selector):
    if selector == "jsonld:Product.offers.price":
        return _price_from_jsonld(soup)

    css_selector, separator, attribute = selector.partition("::")
    price_element = soup.select_one(css_selector)
    if not price_element:
        return None
    price_text = price_element.get(attribute) if separator else price_element.get_text()
    numbers = re.findall(r"\d+", str(price_text or "").replace(".", "").replace(",", ""))
    return int("".join(numbers)) if numbers else None


def extract_price_cloak(url: str, selector: str):
    browser = None
    try:
        browser = get_cloak_browser()
        page = browser.new_page()
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        soup = BeautifulSoup(page.content(), 'html.parser')
        return _extract_price_from_soup(soup, selector)
    except Exception as e:
        print(f"[Cloak] Lỗi trích xuất {url}: {e}")
    finally:
        if browser:
            browser.close()
    return None

def verify_price_cloak(url: str, price: int):
    browser = None
    try:
        browser = get_cloak_browser()
        page = browser.new_page()
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        browser.close()
        return _verify_price_from_soup(soup, price)
    except Exception as e:
        print(f"[Cloak] Lỗi xác minh {url}: {e}")
        if browser:
            browser.close()
        return {"passed": False, "min_count": -1}


def extract_price_selenium(url: str, selector: str):
    driver = None
    try:
        driver = get_selenium_driver()
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        return _extract_price_from_soup(soup, selector)
    except Exception as exc:
        print(f"[Selenium] Price extraction failed for {url}: {exc}")
    finally:
        if driver:
            driver.quit()
    return None


def verify_price_selenium(url: str, price: int):
    driver = None
    try:
        driver = get_selenium_driver()
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        return _verify_price_from_soup(soup, price)
    except Exception as exc:
        print(f"[Selenium] Price verification failed for {url}: {exc}")
        return {"passed": False, "min_count": -1}
    finally:
        if driver:
            driver.quit()

# ========== BS4 ==========

def extract_price_bs4(url: str, selector: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return _extract_price_from_soup(soup, selector)
    except Exception as e:
        print(f"[BS4] Lỗi trích xuất {url}: {e}")
    return None

def verify_price_bs4(url: str, price: int):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return _verify_price_from_soup(soup, price)
    except Exception as e:
        print(f"[BS4] Lỗi xác minh {url}: {e}")
        return {"passed": False, "min_count": -1}

# ========== CHUNG ==========
def _verify_price_from_soup(soup, price: int):
    for script in soup(["script", "style"]):
        script.decompose()
    body_text = soup.body.get_text(separator=' ', strip=True)
    price_str = str(price)
    formatted_price_dot = f"{price:,}".replace(",", ".")
    formatted_price_comma = f"{price:,}"

    patterns_to_check = {
        "dot_separator": r'(?<!\d)' + re.escape(formatted_price_dot) + r'(?!\d)',
        "comma_separator": r'(?<!\d)' + re.escape(formatted_price_comma) + r'(?!\d)',
        "no_separator": r'(?<!\d)' + re.escape(price_str) + r'(?!\d)'
    }

    counts = {}
    for name, pattern in patterns_to_check.items():
        matches = re.findall(pattern, body_text)
        counts[name] = len(matches)
        print(f"[Check] Pattern '{name}' → {counts[name]} matches")

    non_zero_counts = [c for c in counts.values() if c > 0]
    if not non_zero_counts:
        return {"passed": False, "min_count": 0}
    min_count = min(non_zero_counts)
    return {"passed": min_count == 1, "min_count": min_count}

# ========== API ==========

def get_configured_csv_path(config_path):
    with config_path.open(encoding="utf-8") as config_file:
        config = json.load(config_file)

    configured_path = config.get("path")
    if not isinstance(configured_path, str) or not configured_path.strip():
        raise ValueError(f"{config_path.name} must contain a non-empty 'path'")

    data_path = Path(configured_path).expanduser()
    if not data_path.is_absolute():
        data_path = PROJECT_ROOT / data_path
    data_path = data_path.resolve()

    if data_path.suffix.lower() != ".csv":
        raise ValueError("The configured default data file must be a CSV")
    if not data_path.is_file():
        raise FileNotFoundError(f"Configured default data file does not exist: {data_path}")

    return data_path, configured_path


def get_default_data_path():
    return get_configured_csv_path(DEFAULT_DATA_CONFIG)


def get_verification_config():
    with VERIFICATION_CONFIG.open(encoding="utf-8") as handle:
        return json.load(handle)


def get_accepted_data_path(config, acceptance):
    key = {
        "unique": "unique_match_path",
        "present": "price_present_path",
    }.get(acceptance)
    if not key:
        raise ValueError("Acceptance must be 'unique' or 'present'.")
    accepted_path = Path(config[key]).expanduser()
    if not accepted_path.is_absolute():
        accepted_path = PROJECT_ROOT / accepted_path
    accepted_path = accepted_path.resolve()
    if not accepted_path.is_file():
        raise FileNotFoundError(f"Accepted data file does not exist: {accepted_path}")
    return accepted_path


def has_recorded_accumulation_approval(config, acceptance):
    decision = config.get("post_report_decision")
    return (
        config.get("user_decision_required") is False
        and isinstance(decision, dict)
        and decision.get("acceptance") == acceptance
    )


def normalize_verification_mode(value):
    return MODE_ALIASES.get(str(value or "").strip().lower())


def requested_verification_mode(data):
    requested = data.get("mode") if isinstance(data, dict) else None
    if requested is None:
        return DEFAULT_MODE
    return normalize_verification_mode(requested)


def _is_loopback_request():
    try:
        remote_is_loopback = ipaddress.ip_address(request.remote_addr or "").is_loopback
    except ValueError:
        return False
    host = (urlparse(f"//{request.host}").hostname or "").lower()
    if host == "localhost":
        host_is_loopback = True
    else:
        try:
            host_is_loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            host_is_loopback = False
    return remote_is_loopback and host_is_loopback


def _remote_agent_automation_enabled():
    return os.environ.get("ENABLE_REMOTE_AGENT_AUTOMATION", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def require_agent_automation():
    if request.headers.get("X-Agent-Automation") != "1":
        return jsonify({
            "error": "This endpoint is reserved for agent automation.",
            "code": "agent_header_required",
        }), 403
    if _is_loopback_request():
        return None
    expected = os.environ.get("AGENT_AUTOMATION_TOKEN", "")
    provided = request.headers.get("X-Agent-Automation-Token", "")
    if (
        _remote_agent_automation_enabled()
        and expected
        and hmac.compare_digest(provided, expected)
    ):
        return None
    return jsonify({
        "error": (
            "Remote agent automation is disabled or the automation token is invalid. "
            "Use loopback, or explicitly enable remote automation and provide its token."
        ),
        "code": "remote_agent_automation_forbidden",
    }), 403


@app.route('/api/check-price', methods=['POST'])
def handle_check_price():
    data = request.get_json(silent=True) or {}
    url = data.get('url')
    selector = data.get('selector')
    request_id = data.get('request_id')
    mode = requested_verification_mode(data)

    if mode is None:
        return jsonify({
            "error": "Unsupported verification mode. Use fast, compatible, or adaptive."
        }), 400

    if not url or (not selector and not (mode == "adaptive" and is_shopee_url(url))):
        return jsonify({"error": "Thiếu URL hoặc bộ chọn"}), 400

    print(f"[Check Price] URL: {url}, Selector: {selector}, Mode: {mode}")

    if mode == "adaptive" and is_shopee_url(url):
        result = extract_price_shopee(url, selector, request_id=request_id)
        response = result.to_response()
        response.update(_manual_action_response(result.status, request_id))
        if result.price is not None:
            return jsonify(response), shopee_http_status_for(result, "extract")
        response["error"] = response.get("error") or f"Shopee extraction status: {result.status}"
        return jsonify(response), shopee_http_status_for(result, "extract")

    if mode == "fast":
        price = extract_price_bs4(url, selector)
    elif mode == "compatible":
        price = extract_price_selenium(url, selector)
    else:
        price = extract_price_cloak(url, selector)

    if price is not None:
        return jsonify({"price": price, "verification_mode": mode})
    return jsonify({"error": "Không thể trích xuất giá.", "price": None}), 404

@app.route('/api/verify-price-by-text', methods=['POST'])
def handle_verify_price():
    data = request.get_json(silent=True) or {}
    url = data.get('url')
    price = data.get('price')
    request_id = data.get('request_id')
    mode = requested_verification_mode(data)

    if mode is None:
        return jsonify({
            "error": "Unsupported verification mode. Use fast, compatible, or adaptive."
        }), 400

    if not url or price is None:
        return jsonify({"error": "Thiếu URL hoặc giá để xác minh"}), 400

    try:
        price = int(str(price).replace(".", "").replace(",", ""))
    except ValueError:
        return jsonify({"error": "Gia khong hop le"}), 400

    print(f"[Verify Price] URL: {url}, Price: {price}, Mode: {mode}")

    if mode == "adaptive" and is_shopee_url(url):
        result = verify_price_shopee(url, price, request_id=request_id)
        response = result.to_response()
        response.update({
            "found_uniquely": result.passed,
            "match_count": result.match_count,
        })
        response.update(_manual_action_response(result.status, request_id))
        if result.status not in {"ok", "price_changed"}:
            response["error"] = response.get("error") or f"Shopee verification status: {result.status}"
        return jsonify(response), shopee_http_status_for(result, "verify")

    if mode == "fast":
        result = verify_price_bs4(url, price)
    elif mode == "compatible":
        result = verify_price_selenium(url, price)
    else:
        result = verify_price_cloak(url, price)

    return jsonify({
        "found_uniquely": result["passed"],
        "match_count": result["min_count"],
        "verification_mode": mode,
    })


def _manual_action_response(status, request_id):
    manual_action_required = status in {"session_expired", "captcha_required", "access_blocked"}
    manual_action = get_manual_action(request_id) if request_id else None
    public_action = _public_manual_action(manual_action) if manual_action else {}
    return {
        "request_id": request_id,
        "manual_action_required": manual_action_required,
        "manual_action_state": public_action.get("state"),
        "manual_action_kind": manual_action.get("action_kind") if manual_action else None,
        "manual_action_open_url": public_action.get("open_url"),
        "retryable": manual_action_required,
        "manual_action_status_url": f"/api/manual-actions/{request_id}" if request_id else None,
    }


def _public_manual_action(action):
    public_action = dict(action)
    interaction_url = public_action.pop("interaction_url", None)
    public_action["open_url"] = (
        f"/api/manual-actions/{action['request_id']}/open"
        if interaction_url and action.get("state") == "pending"
        else None
    )
    return public_action


@app.route('/api/manual-actions/<request_id>', methods=['GET'])
def handle_get_manual_action(request_id):
    action = get_manual_action(request_id)
    if action is None:
        return jsonify({"request_id": request_id, "state": "not_found"}), 404
    return jsonify(_public_manual_action(action))


@app.route('/api/manual-actions/<request_id>/open', methods=['GET'])
def handle_open_manual_action(request_id):
    action = get_manual_action(request_id)
    interaction_url = action.get("interaction_url") if action else None
    if not action or action.get("state") != "pending" or not interaction_url:
        return jsonify({"request_id": request_id, "state": "not_available"}), 404
    parsed = urlparse(interaction_url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "shopee.vn" or host.endswith(".shopee.vn")):
        return jsonify({"request_id": request_id, "state": "invalid_destination"}), 400
    record_verification_url_opened(request_id)
    return redirect(interaction_url, code=302)


@app.route('/api/manual-actions/<request_id>/events', methods=['POST'])
def handle_manual_action_event(request_id):
    data = request.get_json(silent=True) or {}
    try:
        action = record_client_event(request_id, data.get("event", ""))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if action is None:
        return jsonify({"request_id": request_id, "state": "not_found"}), 404
    return jsonify(_public_manual_action(action))

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)
    
@app.route('/api/default-mode', methods=['GET'])
def get_default_mode():
    return jsonify({
        "default_mode": DEFAULT_MODE,
        "available_modes": ["fast", "compatible", "adaptive"],
    })


@app.route('/api/agent/default-data', methods=['GET'])
def get_agent_default_data():
    denied = require_agent_automation()
    if denied:
        return denied

    try:
        data_path, configured_path = get_default_data_path()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return jsonify({"error": str(exc)}), 500

    response = send_file(
        data_path,
        mimetype="text/csv",
        as_attachment=False,
        download_name=data_path.name,
    )
    response.headers["X-Default-Data-Name"] = data_path.name
    response.headers["X-Default-Data-Path"] = configured_path
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route('/api/agent/candidate-data', methods=['GET'])
def get_agent_candidate_data():
    denied = require_agent_automation()
    if denied:
        return denied

    try:
        data_path, configured_path = get_configured_csv_path(CANDIDATE_DATA_CONFIG)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return jsonify({"error": str(exc)}), 500

    response = send_file(
        data_path,
        mimetype="text/csv",
        as_attachment=False,
        download_name=data_path.name,
    )
    response.headers["X-Candidate-Data-Name"] = data_path.name
    response.headers["X-Candidate-Data-Path"] = configured_path
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route('/api/agent/verification-summary', methods=['GET'])
def get_agent_verification_summary():
    denied = require_agent_automation()
    if denied:
        return denied

    try:
        config = json.loads(VERIFICATION_CONFIG.read_text(encoding="utf-8"))
        report_path = Path(config["report_path"])
        if not report_path.is_absolute():
            report_path = PROJECT_ROOT / report_path
        with report_path.resolve().open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            fields = reader.fieldnames or []
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        return jsonify({"error": str(exc)}), 500

    if len(fields) < 8:
        return jsonify({"error": "Verification report schema is invalid."}), 500

    product_key = fields[1]
    link_key = fields[2]
    match_count_key = fields[5]
    problem_rows = [
        {
            "id": row.get("ID"),
            "product": row.get(product_key),
            "url": row.get(link_key),
            "match_count": int(row.get(match_count_key) or 0),
            "kind": "ambiguous" if int(row.get(match_count_key) or 0) > 1 else "price_absent",
        }
        for row in rows
        if int(row.get(match_count_key) or 0) != 1
    ]
    return jsonify({
        "run_id": config.get("run_id"),
        "novel_candidates": config.get("novel_candidates", len(rows)),
        "unique_matches": config.get("unique_matches", 0),
        "ambiguous_price_present": config.get("ambiguous_price_present", 0),
        "price_absent": config.get("price_absent", 0),
        "user_decision_required": config.get("user_decision_required", True),
        "problem_rows": problem_rows,
    })


@app.route('/api/agent/accumulation', methods=['POST'])
def post_agent_accumulation():
    denied = require_agent_automation()
    if denied:
        return denied

    payload = request.get_json(silent=True) or {}
    acceptance = payload.get("acceptance", "unique")
    commit = payload.get("commit") is True
    try:
        config = get_verification_config()
        run_id = config["run_id"]
        if payload.get("run_id") != run_id:
            return jsonify({"error": "Run ID confirmation does not match the current verification run."}), 409
        default_path, _ = get_default_data_path()
        accepted_path = get_accepted_data_path(config, acceptance)
        events_path = PROJECT_ROOT / "data_out" / f"{run_id}_events.jsonl"
        if commit:
            if not has_recorded_accumulation_approval(config, acceptance):
                return jsonify({
                    "error": (
                        "No matching post-report user approval is recorded for this accumulation."
                    )
                }), 409
            result = commit_accumulation(
                default_path,
                accepted_path,
                run_id=run_id,
                acceptance=acceptance,
                events_path=events_path,
            )
            config.update({
                "accepted_standard": acceptance,
                "accumulation_status": "accumulated",
                "accumulation_result": result,
                "user_decision_required": False,
            })
            VERIFICATION_CONFIG.write_text(
                json.dumps(config, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return jsonify({"status": "accumulated", **result})

        plan = build_accumulation_plan(default_path, accepted_path)
        return jsonify({
            "status": "preview",
            "run_id": run_id,
            "acceptance": acceptance,
            **{key: value for key, value in plan.items() if key not in {"fieldnames", "rows"}},
        })
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        return jsonify({"error": str(exc)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

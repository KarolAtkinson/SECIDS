#!/usr/bin/env python3
"""Update NIST-CSW dataset from publicly available open-source feeds.

This script fetches recent/public threat intelligence records suitable for
synthetic DDoS-oriented simulation enrichment and stores them under:
  ServerDB/NIST-CSW/source_feeds/

Feeds are stored in raw JSON + normalized summary files, then appended to
an update manifest for auditability.
"""

from __future__ import annotations

import argparse
import json
import ssl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib import error, request

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NIST_CSW_ROOT = PROJECT_ROOT / "ServerDB" / "NIST-CSW"
SOURCE_FEEDS_DIR = NIST_CSW_ROOT / "source_feeds"
MANIFEST_FILE = NIST_CSW_ROOT / "nist_csw_updates.jsonl"

DEFAULT_FEEDS = {
    "cisa_kev": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    "nvd_recent": "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=50&startIndex=0",
}


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    SOURCE_FEEDS_DIR.mkdir(parents=True, exist_ok=True)


def fetch_json(url: str, timeout: int = 30) -> Dict[str, Any]:
    ctx = ssl.create_default_context()
    req = request.Request(url, headers={"User-Agent": "SECIDS-CNN-NIST-CSW-Updater/1.0", "Accept": "application/json"})
    with request.urlopen(req, timeout=timeout, context=ctx) as response:
        raw = response.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def normalize_cisa_kev(payload: Dict[str, Any]) -> Dict[str, Any]:
    vulns = payload.get("vulnerabilities", []) if isinstance(payload, dict) else []
    items: List[Dict[str, Any]] = []
    for item in vulns[:200]:
        if not isinstance(item, dict):
            continue
        items.append(
            {
                "cve": item.get("cveID", ""),
                "vendor": item.get("vendorProject", ""),
                "product": item.get("product", ""),
                "required_action": item.get("requiredAction", ""),
                "due_date": item.get("dueDate", ""),
                "notes": item.get("shortDescription", ""),
                "source": "cisa_kev",
            }
        )
    return {"feed": "cisa_kev", "count": len(items), "items": items}


def normalize_nvd_recent(payload: Dict[str, Any]) -> Dict[str, Any]:
    vulnerabilities = payload.get("vulnerabilities", []) if isinstance(payload, dict) else []
    items: List[Dict[str, Any]] = []
    for wrapper in vulnerabilities[:200]:
        cve = wrapper.get("cve", {}) if isinstance(wrapper, dict) else {}
        if not isinstance(cve, dict):
            continue
        cve_id = cve.get("id", "")
        desc = ""
        descriptions = cve.get("descriptions", [])
        if isinstance(descriptions, list):
            for entry in descriptions:
                if isinstance(entry, dict) and entry.get("lang") == "en":
                    desc = str(entry.get("value", ""))
                    break
        metrics = cve.get("metrics", {}) if isinstance(cve.get("metrics", {}), dict) else {}
        cvss = ""
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            metric_list = metrics.get(key, [])
            if isinstance(metric_list, list) and metric_list:
                first = metric_list[0]
                if isinstance(first, dict):
                    data = first.get("cvssData", {}) if isinstance(first.get("cvssData", {}), dict) else {}
                    score = data.get("baseScore")
                    if score is not None:
                        cvss = str(score)
                        break
        items.append(
            {
                "cve": cve_id,
                "published": cve.get("published", ""),
                "last_modified": cve.get("lastModified", ""),
                "cvss": cvss,
                "notes": desc[:600],
                "source": "nvd_recent",
            }
        )
    return {"feed": "nvd_recent", "count": len(items), "items": items}


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def append_manifest(record: Dict[str, Any]) -> None:
    with open(MANIFEST_FILE, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_update(feeds: Dict[str, str]) -> Dict[str, Any]:
    ensure_dirs()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary: Dict[str, Any] = {
        "started_at": now_utc_iso(),
        "feeds": {},
        "ok": True,
        "errors": [],
        "stored": [],
    }

    normalizers = {
        "cisa_kev": normalize_cisa_kev,
        "nvd_recent": normalize_nvd_recent,
    }

    for feed_name, url in feeds.items():
        feed_result: Dict[str, Any] = {"url": url, "ok": False, "count": 0}
        try:
            payload = fetch_json(url)
            raw_path = SOURCE_FEEDS_DIR / f"{feed_name}_raw_{ts}.json"
            write_json(raw_path, payload)
            feed_result["raw_file"] = str(raw_path.relative_to(PROJECT_ROOT))

            normalized_payload = normalizers.get(feed_name, lambda x: {"feed": feed_name, "count": 0, "items": []})(payload)
            normalized_payload["updated_at"] = now_utc_iso()
            normalized_path = SOURCE_FEEDS_DIR / f"{feed_name}_normalized_{ts}.json"
            write_json(normalized_path, normalized_payload)
            feed_result["normalized_file"] = str(normalized_path.relative_to(PROJECT_ROOT))
            feed_result["ok"] = True
            feed_result["count"] = int(normalized_payload.get("count", 0))
            summary["stored"].append(feed_result["normalized_file"])
        except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError, OSError, ValueError) as exc:
            summary["ok"] = False
            message = f"{feed_name}: {exc}"
            summary["errors"].append(message)
            feed_result["error"] = str(exc)

        summary["feeds"][feed_name] = feed_result

    summary["finished_at"] = now_utc_iso()
    append_manifest(summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Update NIST-CSW open-source feeds")
    parser.add_argument("--feeds", nargs="*", default=list(DEFAULT_FEEDS.keys()), help="Feed names to update")
    args = parser.parse_args()

    selected: Dict[str, str] = {}
    for name in args.feeds:
        if name in DEFAULT_FEEDS:
            selected[name] = DEFAULT_FEEDS[name]

    if not selected:
        print(json.dumps({"ok": False, "error": "No valid feeds selected"}, indent=2))
        return 1

    result = run_update(selected)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.v145_1_runtime_artifact_integrity import RUNTIME_ROOT, persist_json_pair, write_text

from src.bst_official_sync_engine import (
    BSTCaptchaBlockedError,
    OFFICIAL_BASE_URL,
    extract_draw_links,
    fetch_latest_index,
    is_captcha_page,
    parse_official_draw,
    read_rows,
    validate_record,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
STATUS_JSON = MODELS_DIR / "v123_bst_official_draw_detection_status.json"
REPORT_JSON = REPORTS_DIR / "v123_bst_official_draw_detection_report.json"
SUMMARY_MD = REPORTS_DIR / "v123_bst_official_draw_detection_summary.md"
STARTUP_AUDIT_JSONL = REPORTS_DIR / "v126_startup_automation_audit.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _read_previous_detection() -> dict[str, Any]:
    for path in (STATUS_JSON, REPORT_JSON):
        if not path.exists():
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            return value
    return {}


def _last_known_good_draw(previous: dict[str, Any]) -> dict[str, Any]:
    candidate = previous.get("official_latest_draw") or previous.get("last_known_good_official_draw") or {}
    if candidate.get("year") and candidate.get("draw_number"):
        return dict(candidate)
    if STARTUP_AUDIT_JSONL.exists():
        try:
            lines = STARTUP_AUDIT_JSONL.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        except OSError:
            lines = []
        for line in reversed(lines):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            detection = event.get("detection") if isinstance(event, dict) else {}
            official = detection.get("official_latest_draw") if isinstance(detection, dict) else {}
            validation = detection.get("validation") if isinstance(detection, dict) else {}
            if (
                isinstance(official, dict)
                and official.get("year")
                and official.get("draw_number")
                and isinstance(validation, dict)
                and validation.get("passed") is True
            ):
                return dict(official)
    return {}


def latest_local_draw(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = read_rows() if rows is None else rows
    candidates: list[dict[str, Any]] = []
    for row in rows:
        year = _safe_int(row.get("draw_year"))
        draw_number = _safe_int(row.get("draw_number"))
        if year is None or draw_number is None:
            continue
        candidates.append({
            "year": year,
            "draw_number": draw_number,
            "date": str(row.get("draw_date") or ""),
            "numbers": [_safe_int(row.get(f"n{i}")) for i in range(1, 7)],
            "draw_key": str(row.get("draw_key") or f"{year}-{draw_number}"),
        })
    return max(candidates, key=lambda x: (x["year"], x["draw_number"], x["date"]), default={})


def _classify(official: dict[str, Any], local: dict[str, Any]) -> tuple[str, int | None, str]:
    if not official:
        return "official_unavailable", None, "Не беше открит валиден официален тираж."
    if not local:
        return "update_available", None, "Няма локален официален тираж; наличен е официален импорт."
    official_key = (official.get("year") or 0, official.get("draw_number") or 0)
    local_key = (local.get("year") or 0, local.get("draw_number") or 0)
    if official_key == local_key:
        return "up_to_date", 0, "Локалният source of truth е актуален."
    if official_key > local_key:
        delta = official_key[1] - local_key[1] if official_key[0] == local_key[0] else None
        return "update_available", delta, "Открит е по-нов официален тираж."
    return "local_ahead", None, "Локалният тираж е пред официално открития; нужна е ръчна проверка."


def detect_latest_official_draw(
    *,
    timeout: int = 30,
    validate_details: bool = True,
    write_outputs: bool = True,
    index_fetcher: Callable[[int], str] | None = None,
    detail_fetcher: Callable[[int, int, int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Read-only detection. CAPTCHA is classified explicitly and never treated as parser drift."""
    checked_at = utc_now()
    local = latest_local_draw()
    previous = _read_previous_detection()
    last_known_good = _last_known_good_draw(previous)
    fetch_index = index_fetcher or (lambda value: fetch_latest_index(timeout=value))
    fetch_detail = detail_fetcher or (
        lambda year, draw, value: parse_official_draw(year, draw, timeout=value, save_raw=False)
    )
    report: dict[str, Any] = {
        "step": "123",
        "name": "BST Official Draw Detection Foundation",
        "checked_at_utc": checked_at,
        "official_source_url": OFFICIAL_BASE_URL,
        "mode": "read_only_detection",
        "writes_draw_data": False,
        "starts_downstream_refresh": False,
        "local_latest_draw": local,
        "official_latest_draw": {},
        "last_known_good_official_draw": last_known_good,
        "status": "official_unavailable",
        "draw_delta": None,
        "message": "",
        "validation": {"requested": validate_details, "passed": False, "errors": []},
        "failure_stage": None,
        "connectivity": {"index_fetch_succeeded": False, "detail_fetch_succeeded": False},
    }

    stage = "index_fetch"
    try:
        index_html = fetch_index(timeout)
        report["connectivity"]["index_fetch_succeeded"] = True
        encoded = index_html.encode("utf-8", errors="replace")
        report["source_diagnostics"] = {
            "html_sha256": hashlib.sha256(encoded).hexdigest(),
            "html_bytes": len(encoded),
            "contains_6x49_marker": any(marker in index_html.lower() for marker in ("6x49", "6 от 49")),
            "captcha_detected": is_captcha_page(index_html),
        }
        if report["source_diagnostics"]["captcha_detected"]:
            stage = "index_captcha"
            raise BSTCaptchaBlockedError(
                "BST индексът върна CAPTCHA. Това е временна защита на сайта, не parser failure."
            )
        stage = "index_parse"
        links = extract_draw_links(index_html, limit=20)
        report["source_diagnostics"]["candidate_count"] = len(links)
        if not links:
            raise RuntimeError(
                "Официалната страница не съдържа разпознаваем 6/49 тираж. "
                f"HTML SHA256: {report['source_diagnostics']['html_sha256']}"
            )
        candidate = links[0]
        report["source_diagnostics"]["selected_parser_strategies"] = candidate.get("parser_strategies", [])
        official = {
            "year": int(candidate["draw_year"]),
            "draw_number": int(candidate["draw_number"]),
            "date": "",
            "numbers": [],
            "source_url": candidate["source_url"],
        }
        if validate_details:
            stage = "detail_fetch"
            detail = fetch_detail(official["year"], official["draw_number"], timeout)
            report["connectivity"]["detail_fetch_succeeded"] = True
            stage = "detail_validation"
            errors = validate_record(detail)
            report["validation"]["errors"] = errors
            report["validation"]["passed"] = not errors
            if errors:
                raise RuntimeError("Официалният детайлен запис не премина валидация: " + "; ".join(errors))
            official.update({
                "date": detail.get("draw_date", ""),
                "numbers": [_safe_int(detail.get(f"n{i}")) for i in range(1, 7)],
                "draw_key": detail.get("draw_key", ""),
                "source_url": detail.get("source_url") or official["source_url"],
            })
        else:
            report["validation"]["passed"] = True
        report["official_latest_draw"] = official
        report["last_known_good_official_draw"] = official
        stage = "classification"
        status, delta, message = _classify(official, local)
        report.update({"status": status, "draw_delta": delta, "message": message})
    except Exception as exc:
        captcha = isinstance(exc, BSTCaptchaBlockedError) or "captcha" in str(exc).lower()
        if captcha and stage == "index_fetch":
            stage = "index_captcha"
        elif captcha and stage == "detail_fetch":
            stage = "detail_captcha"
        report["status"] = "captcha_blocked" if captcha else "official_unavailable"
        report["message"] = str(exc)
        report["error_type"] = type(exc).__name__
        report["failure_stage"] = stage

    if write_outputs:
        write_detection_outputs(report)
    return report

def _render_detection_summary(report: dict[str, Any]) -> str:
    local = report.get("local_latest_draw") or {}
    official = report.get("official_latest_draw") or {}
    return "\n".join([
        "# Step 123 — BST Official Draw Detection Foundation",
        "",
        f"- Checked at UTC: `{report.get('checked_at_utc', '')}`",
        f"- Status: **{report.get('status', '')}**",
        f"- Local latest: **{local.get('year', '?')}-{local.get('draw_number', '?')}**",
        f"- Official latest: **{official.get('year', '?')}-{official.get('draw_number', '?')}**",
        f"- Draw delta: **{report.get('draw_delta')}**",
        f"- Validation passed: **{report.get('validation', {}).get('passed', False)}**",
        "- Draw data written: **No**",
        "- Downstream refresh started: **No**",
        "",
        str(report.get("message", "")),
        "",
    ])


def write_detection_outputs(report: dict[str, Any]) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    canonical_changed = persist_json_pair(
        component="v123_bst_official_draw_detection",
        payload=report,
        canonical_paths=(STATUS_JSON, REPORT_JSON),
        volatile_keys={"source_diagnostics"},
    )
    summary = _render_detection_summary(report)
    write_text(RUNTIME_ROOT / "v123" / SUMMARY_MD.name, summary)
    if canonical_changed:
        write_text(SUMMARY_MD, summary)


if __name__ == "__main__":
    print(json.dumps(detect_latest_official_draw(), ensure_ascii=False, indent=2))

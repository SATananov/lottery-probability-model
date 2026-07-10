from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.bst_official_sync_engine import (
    OFFICIAL_BASE_URL,
    extract_draw_links,
    fetch_latest_index,
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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


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
    """Read-only detection. It never writes draw CSV data or starts downstream refresh."""
    checked_at = utc_now()
    local = latest_local_draw()
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
        "status": "official_unavailable",
        "draw_delta": None,
        "message": "",
        "validation": {"requested": validate_details, "passed": False, "errors": []},
    }

    try:
        index_html = fetch_index(timeout)
        links = extract_draw_links(index_html, limit=20)
        if not links:
            raise RuntimeError("Официалната страница не съдържа разпознаваем 6/49 тираж.")
        candidate = links[0]
        official = {
            "year": int(candidate["draw_year"]),
            "draw_number": int(candidate["draw_number"]),
            "date": "",
            "numbers": [],
            "source_url": candidate["source_url"],
        }

        if validate_details:
            detail = fetch_detail(official["year"], official["draw_number"], timeout)
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
        status, delta, message = _classify(official, local)
        report.update({"status": status, "draw_delta": delta, "message": message})
    except Exception as exc:
        report["status"] = "official_unavailable"
        report["message"] = str(exc)
        report["error_type"] = type(exc).__name__

    if write_outputs:
        write_detection_outputs(report)
    return report


def write_detection_outputs(report: dict[str, Any]) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    STATUS_JSON.write_text(text, encoding="utf-8")
    REPORT_JSON.write_text(text, encoding="utf-8")
    local = report.get("local_latest_draw") or {}
    official = report.get("official_latest_draw") or {}
    SUMMARY_MD.write_text(
        "\n".join([
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
            report.get("message", ""),
            "",
        ]),
        encoding="utf-8",
    )


if __name__ == "__main__":
    print(json.dumps(detect_latest_official_draw(), ensure_ascii=False, indent=2))

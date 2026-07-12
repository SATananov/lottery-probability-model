from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from src.v145_1_runtime_artifact_integrity import RUNTIME_ROOT, persist_json_pair, write_text

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"

STATUS_JSON = MODELS_DIR / "v122_unified_official_draw_freshness_status.json"
REPORT_JSON = REPORTS_DIR / "v122_unified_official_draw_freshness_report.json"
REPORT_CSV = REPORTS_DIR / "v122_unified_official_draw_freshness_matrix.csv"
SUMMARY_MD = REPORTS_DIR / "v122_unified_official_draw_freshness_summary.md"

SOURCE_SPECS = [
    ("official", "Официална история", DATA_DIR / "prize_winner_history.csv", "csv"),
    ("journal_prize", "Дневник — история на печалбите", DATA_DIR / "user_journal_exports" / "prize_winner_history.csv", "csv"),
    ("historical", "Исторически тиражи", DATA_DIR / "historical_draws.csv", "csv"),
    ("normalized", "Нормализирани събития", DATA_DIR / "v40_normalized_draw_events.csv", "csv"),
    ("canonical", "Канонични събития", DATA_DIR / "v41_canonical_draw_events.csv", "csv"),
    ("r_layer", "R статистически слой", REPORTS_DIR / "r" / "r_data_audit.csv", "r_audit"),
    ("step121", "R статистически характеристики", MODELS_DIR / "v121_r_statistical_features_status.json", "json"),
    ("decision", "Решение за игра", REPORTS_DIR / "v115_play_decision_center_report.json", "json"),
    ("final_pack", "Готов фиш пакет", REPORTS_DIR / "v117_real_ticket_pack_builder_summary.json", "json"),
    ("model_system", "Системен фиш от моделите", REPORTS_DIR / "v118_model_system_ticket_builder_summary.json", "json"),
]

MODEL_ARTIFACTS = [
    MODELS_DIR / "lottery_prediction_model.json",
    MODELS_DIR / "lottery_frequency_model.json",
    MODELS_DIR / "lottery_gap_model.json",
    MODELS_DIR / "lottery_cold_model.json",
    MODELS_DIR / "lottery_middle_model.json",
    MODELS_DIR / "lottery_combined_model.json",
    MODELS_DIR / "lottery_advanced_ensemble_model.json",
    MODELS_DIR / "lottery_ml_extensions_model.json",
    MODELS_DIR / "v41" / "v41_sgd_number_model_metadata.json",
    MODELS_DIR / "v45" / "v45_model_metadata.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_int(value: Any) -> int | None:
    try:
        text = re.sub(r"[^0-9-]", "", str(value or "").strip())
        return int(text) if text not in {"", "-"} else None
    except (TypeError, ValueError):
        return None


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue
    return []


def _numbers_from_row(row: dict[str, Any]) -> list[int]:
    numbers: list[int] = []
    for index in range(1, 7):
        value = _safe_int(row.get(f"n{index}"))
        if value is not None and 1 <= value <= 49:
            numbers.append(value)
    if len(numbers) != 6:
        text = str(row.get("numbers_text") or row.get("latest_numbers") or "")
        numbers = [int(item) for item in re.findall(r"\b(?:[1-9]|[1-4][0-9])\b", text)][:6]
    return numbers if len(numbers) == 6 else []


def _latest_from_csv(path: Path) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for row in _read_csv(path):
        year = _safe_int(row.get("draw_year") or row.get("year"))
        draw_number = _safe_int(row.get("draw_number") or row.get("draw_no"))
        if year is None or draw_number is None:
            continue
        candidates.append({
            "year": year,
            "draw_number": draw_number,
            "date": str(row.get("draw_date") or row.get("date") or ""),
            "numbers": _numbers_from_row(row),
        })
    if not candidates:
        return {}
    return max(candidates, key=lambda item: (item["year"], item["draw_number"], item["date"]))


def _latest_from_r_audit(path: Path) -> dict[str, Any]:
    metrics = {str(row.get("metric", "")): str(row.get("value", "")) for row in _read_csv(path)}
    draw_number = _safe_int(metrics.get("latest_draw_number"))
    date = metrics.get("latest_date", "")
    year = _safe_int(date[:4]) if date else None
    if draw_number is None:
        return {}
    return {
        "year": year,
        "draw_number": draw_number,
        "date": date,
        "numbers": [int(item) for item in re.findall(r"\b(?:[1-9]|[1-4][0-9])\b", metrics.get("latest_numbers", ""))][:6],
    }


def _walk_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _candidate_from_dict(node: dict[str, Any]) -> dict[str, Any] | None:
    draw_number = _safe_int(
        node.get("draw_number") or node.get("latest_draw_number") or node.get("trained_up_to_draw")
        or node.get("last_draw_number") or node.get("draw_no")
    )
    date = str(
        node.get("draw_date") or node.get("date") or node.get("latest_draw_date")
        or node.get("trained_up_to_date") or ""
    )
    year = _safe_int(node.get("year") or node.get("draw_year"))
    if year is None and re.match(r"^\d{4}-\d{2}-\d{2}", date):
        year = _safe_int(date[:4])
    if draw_number is None:
        return None
    numbers = node.get("numbers") or node.get("latest_numbers") or []
    if isinstance(numbers, str):
        numbers = [int(item) for item in re.findall(r"\b(?:[1-9]|[1-4][0-9])\b", numbers)][:6]
    if not isinstance(numbers, list):
        numbers = []
    return {"year": year, "draw_number": draw_number, "date": date, "numbers": numbers[:6]}


def _latest_from_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    candidates = [candidate for node in _walk_dicts(payload) if (candidate := _candidate_from_dict(node))]
    if not candidates:
        return {}
    return max(candidates, key=lambda item: (item.get("year") or 0, item["draw_number"], item.get("date") or ""))


def _source_snapshot(key: str, label: str, path: Path, source_type: str) -> dict[str, Any]:
    if source_type == "csv":
        latest = _latest_from_csv(path)
    elif source_type == "r_audit":
        latest = _latest_from_r_audit(path)
    else:
        latest = _latest_from_json(path)
    return {
        "key": key,
        "label": label,
        "path": path.relative_to(ROOT).as_posix(),
        "exists": path.exists(),
        "latest": latest,
    }


def _compare(snapshot: dict[str, Any], official: dict[str, Any]) -> dict[str, Any]:
    latest = snapshot.get("latest") or {}
    official_year = official.get("year") or 0
    official_draw = official.get("draw_number") or 0
    year = latest.get("year") or 0
    draw_number = latest.get("draw_number")
    if draw_number is None:
        status, delta, message = "unavailable", None, "Не може да се установи последен тираж."
    elif not year:
        status, delta, message = "unavailable", None, f"Открит е marker за тираж {draw_number}, но липсва година за надеждно сравнение."
    elif year == official_year and draw_number == official_draw:
        status, delta, message = "synced", 0, "Синхронизиран с официалния последен тираж."
    elif (year, draw_number) < (official_year, official_draw):
        delta = official_draw - draw_number if year == official_year else None
        status = "behind"
        message = f"Назад с {delta} тираж(а)." if delta is not None else "Назад спрямо официалния източник."
    else:
        delta = draw_number - official_draw if year == official_year else None
        status = "ahead"
        message = "Артефактът е пред официалния източник — необходима е проверка."
    return {**snapshot, "status": status, "draw_delta": delta, "message": message}


def _model_freshness(official: dict[str, Any]) -> dict[str, Any]:
    """Return model inventory as information, not as a per-draw freshness blocker.

    Training artifacts are intentionally not rebuilt after every draw. Treating an old
    training marker as a stale operational layer produced misleading values such as
    ``None-47`` in the user interface.
    """
    detected: list[dict[str, Any]] = []
    for path in MODEL_ARTIFACTS:
        latest = _latest_from_json(path)
        if latest:
            detected.append({"path": path.relative_to(ROOT).as_posix(), "latest": latest})
    return {
        "key": "models",
        "label": "Обучени ML модели",
        "path": "models/",
        "exists": bool(detected),
        "latest": {},
        "detected_artifacts": detected,
        "status": "informational",
        "draw_delta": None,
        "message": "Моделите се обновяват по отделна политика и не са част от обновяването след всеки тираж.",
    }


def build_freshness_report(write_outputs: bool = True) -> dict[str, Any]:
    raw_snapshots = [_source_snapshot(*spec) for spec in SOURCE_SPECS]
    official = raw_snapshots[0].get("latest") or {}
    if not official.get("draw_number"):
        raise RuntimeError("Official source-of-truth draw cannot be detected from data/prize_winner_history.csv")

    sources = [_compare(snapshot, official) for snapshot in raw_snapshots]
    sources.append(_model_freshness(official))
    blocking = [
        source for source in sources
        if source["key"] != "official" and source["status"] not in {"synced", "informational"}
    ]
    report = {
        "step": "122",
        "name": "Unified Official Draw Freshness Layer",
        "generated_at_utc": utc_now(),
        "official_source_of_truth": "data/prize_winner_history.csv",
        "official_latest_draw": official,
        "overall_status": "synced" if not blocking else "out_of_sync",
        "blocking_out_of_sync_count": len(blocking),
        "heavy_model_retraining_performed": False,
        "policy": "Step 122 diagnoses freshness and source-of-truth drift; it does not retrain heavy models.",
        "sources": sources,
    }
    if write_outputs:
        _write_outputs(report)
    return report


def _render_matrix_csv(report: dict[str, Any]) -> str:
    fields = ["key", "label", "status", "year", "draw_number", "date", "draw_delta", "path", "message"]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for source in report["sources"]:
        latest = source.get("latest") or {}
        writer.writerow({
            "key": source["key"], "label": source["label"], "status": source["status"],
            "year": latest.get("year", ""), "draw_number": latest.get("draw_number", ""),
            "date": latest.get("date", ""), "draw_delta": source.get("draw_delta", ""),
            "path": source["path"], "message": source["message"],
        })
    return output.getvalue()


def _render_summary(report: dict[str, Any]) -> str:
    official = report["official_latest_draw"]
    lines = [
        "# Step 122 — Unified Official Draw Freshness Layer", "",
        f"Generated: {report['generated_at_utc']}",
        f"Official source of truth: `{report['official_source_of_truth']}`",
        f"Official latest draw: **{official.get('year')}-{official.get('draw_number')}** ({official.get('date')})",
        f"Overall status: **{report['overall_status']}**", "",
        "| Module | Latest draw | Date | Status | Delta |", "|---|---:|---|---|---:|",
    ]
    for source in report["sources"]:
        latest = source.get("latest") or {}
        if source.get("status") == "informational":
            draw_label = "Не се следи по тираж"
        else:
            draw_year = latest.get("year") or "?"
            draw_number = latest.get("draw_number") if latest.get("draw_number") is not None else "?"
            draw_label = f"{draw_year}-{draw_number}"
        lines.append(f"| {source['label']} | {draw_label} | {latest.get('date', '')} | {source['status']} | {source.get('draw_delta', '')} |")
    lines.extend(["", "Heavy model retraining performed: **No**.", ""])
    return "\n".join(lines)


def _write_outputs(report: dict[str, Any]) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    canonical_changed = persist_json_pair(
        component="v122_unified_official_draw_freshness",
        payload=report,
        canonical_paths=(STATUS_JSON, REPORT_JSON),
    )
    matrix_text = _render_matrix_csv(report)
    summary_text = _render_summary(report)
    runtime_dir = RUNTIME_ROOT / "v122"
    write_text(runtime_dir / REPORT_CSV.name, matrix_text)
    write_text(runtime_dir / SUMMARY_MD.name, summary_text)
    if canonical_changed:
        write_text(REPORT_CSV, matrix_text)
        write_text(SUMMARY_MD, summary_text)


if __name__ == "__main__":
    print(json.dumps(build_freshness_report(), ensure_ascii=False, indent=2))

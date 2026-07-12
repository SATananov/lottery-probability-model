from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from src.v145_1_runtime_artifact_integrity import (
    RUNTIME_ROOT,
    append_jsonl_if_signature_changed,
    persist_json_pair,
    write_text,
)

from src.v123_bst_official_draw_detection_engine import detect_latest_official_draw
from src.v124_safe_official_draw_ingestion_engine import ingest_official_draw_record
from src.v125_unified_downstream_refresh_engine import run_unified_downstream_refresh

ROOT = Path(__file__).resolve().parents[1]
CONFIG_JSON = ROOT / "models" / "v126_startup_automation_config.json"
STATUS_JSON = ROOT / "models" / "v126_startup_automation_status.json"
REPORT_JSON = ROOT / "reports" / "v126_startup_automation_report.json"
SUMMARY_MD = ROOT / "reports" / "v126_startup_automation_summary.md"
AUDIT_JSONL = ROOT / "reports" / "v126_startup_automation_audit.jsonl"
RUNTIME_STATUS_JSON = RUNTIME_ROOT / "v126_startup_automation.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "auto_check_enabled": True,
    "auto_apply_enabled": False,
    "auto_refresh_enabled": False,
    "cache_minutes": 30,
    "network_timeout_seconds": 12,
    "downstream_timeout_seconds": 900,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_utc(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def load_config(path: Path = CONFIG_JSON) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                config.update(data)
        except (OSError, json.JSONDecodeError):
            pass
    config["auto_check_enabled"] = bool(config.get("auto_check_enabled", True))
    config["auto_apply_enabled"] = bool(config.get("auto_apply_enabled", False))
    config["auto_refresh_enabled"] = bool(config.get("auto_refresh_enabled", False))
    config["cache_minutes"] = max(1, min(1440, int(config.get("cache_minutes", 30))))
    config["network_timeout_seconds"] = max(5, min(120, int(config.get("network_timeout_seconds", 12))))
    config["downstream_timeout_seconds"] = max(60, min(3600, int(config.get("downstream_timeout_seconds", 900))))
    if not config["auto_apply_enabled"]:
        config["auto_refresh_enabled"] = False
    return config


def save_config(config: dict[str, Any], path: Path = CONFIG_JSON) -> dict[str, Any]:
    normalized = dict(DEFAULT_CONFIG)
    normalized.update(config)
    normalized = load_config_from_mapping(normalized)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return normalized


def load_config_from_mapping(config: dict[str, Any]) -> dict[str, Any]:
    result = dict(DEFAULT_CONFIG)
    result.update(config)
    result["auto_check_enabled"] = bool(result.get("auto_check_enabled", True))
    result["auto_apply_enabled"] = bool(result.get("auto_apply_enabled", False))
    result["auto_refresh_enabled"] = bool(result.get("auto_refresh_enabled", False)) and result["auto_apply_enabled"]
    result["cache_minutes"] = max(1, min(1440, int(result.get("cache_minutes", 30))))
    result["network_timeout_seconds"] = max(5, min(120, int(result.get("network_timeout_seconds", 12))))
    result["downstream_timeout_seconds"] = max(60, min(3600, int(result.get("downstream_timeout_seconds", 900))))
    return result


def load_status(path: Path = STATUS_JSON) -> dict[str, Any]:
    candidates = (RUNTIME_STATUS_JSON, path) if path == STATUS_JSON else (path,)
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            continue
    return {}


def cache_is_fresh(status: dict[str, Any], cache_minutes: int, now: datetime | None = None) -> bool:
    checked = _parse_utc(status.get("checked_at_utc") or status.get("finished_at_utc"))
    if checked is None:
        return False
    current = now or datetime.now(timezone.utc)
    return current - checked < timedelta(minutes=cache_minutes)


def _official_to_record(official: dict[str, Any]) -> dict[str, Any]:
    numbers = list(official.get("numbers") or [])
    return {
        "draw_year": official.get("year"),
        "draw_number": official.get("draw_number"),
        "draw_date": official.get("date", ""),
        "draw_key": official.get("draw_key") or f"{official.get('year')}-{official.get('draw_number')}",
        "source_url": official.get("source_url", ""),
        **{f"n{i}": numbers[i - 1] if len(numbers) >= i else None for i in range(1, 7)},
    }


def _render_startup_summary(report: dict[str, Any]) -> str:
    return "\n".join([
        "# Step 126 — Startup Automation and Operator Controls",
        "",
        f"- Status: **{report.get('status', '')}**",
        f"- Trigger: **{report.get('trigger', '')}**",
        f"- Checked at UTC: `{report.get('checked_at_utc', '')}`",
        f"- Detection: **{(report.get('detection') or {}).get('status', '')}**",
        f"- Auto apply: **{report.get('auto_apply_attempted', False)}**",
        f"- Auto refresh: **{report.get('auto_refresh_attempted', False)}**",
        "- Heavy ML retraining: **No**",
        "",
        str(report.get("message") or ""),
        "",
    ])


def _write_outputs(
    report: dict[str, Any],
    *,
    status_path: Path = STATUS_JSON,
    report_path: Path = REPORT_JSON,
    summary_path: Path = SUMMARY_MD,
    audit_path: Path = AUDIT_JSONL,
) -> None:
    default_paths = (status_path, report_path, summary_path, audit_path) == (
        STATUS_JSON, REPORT_JSON, SUMMARY_MD, AUDIT_JSONL
    )
    summary = _render_startup_summary(report)
    if not default_paths:
        for path in (status_path, report_path, summary_path, audit_path):
            path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        write_text(status_path, payload)
        write_text(report_path, payload)
        write_text(summary_path, summary)
        with audit_path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(report, ensure_ascii=False, sort_keys=True) + "\n")
        return

    volatile = {"source_diagnostics", "trigger", "cache_reused"}
    canonical_changed = persist_json_pair(
        component="v126_startup_automation",
        payload=report,
        canonical_paths=(STATUS_JSON, REPORT_JSON),
        volatile_keys=volatile,
    )
    runtime_dir = RUNTIME_ROOT / "v126"
    write_text(runtime_dir / SUMMARY_MD.name, summary)
    append_jsonl_if_signature_changed(
        runtime_dir / AUDIT_JSONL.name,
        report,
        signature_path=runtime_dir / "last_audit_signature.sha256",
        volatile_keys=volatile,
    )
    if canonical_changed:
        write_text(SUMMARY_MD, summary)
        AUDIT_JSONL.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_JSONL.open("a", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(report, ensure_ascii=False, sort_keys=True) + "\n")


def run_startup_automation(
    *,
    trigger: str = "startup",
    force_check: bool = False,
    config: dict[str, Any] | None = None,
    detector: Callable[..., dict[str, Any]] | None = None,
    ingestor: Callable[..., dict[str, Any]] | None = None,
    refresher: Callable[..., dict[str, Any]] | None = None,
    write_outputs: bool = True,
    previous_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = load_config_from_mapping(config or load_config())
    previous = load_status() if previous_status is None else previous_status
    started = utc_now()

    base: dict[str, Any] = {
        "step": "126",
        "name": "Startup Automation and Operator Controls",
        "trigger": trigger,
        "started_at_utc": started,
        "checked_at_utc": started,
        "finished_at_utc": started,
        "status": "idle",
        "message": "",
        "config": cfg,
        "detection": {},
        "ingestion": {},
        "downstream_refresh": {},
        "auto_apply_attempted": False,
        "auto_refresh_attempted": False,
        "heavy_ml_retraining_performed": False,
    }

    if trigger == "startup" and not cfg["auto_check_enabled"] and not force_check:
        base.update(status="disabled", message="Автоматичната проверка при старт е изключена.", finished_at_utc=utc_now())
        if write_outputs:
            _write_outputs(base)
        return base

    if trigger == "startup" and not force_check and cache_is_fresh(previous, cfg["cache_minutes"]):
        cached = dict(previous)
        cached.update({
            "step": "126",
            "trigger": trigger,
            "status": "cached",
            "message": f"Използван е свеж кеш ({cfg['cache_minutes']} минути); няма повторна мрежова проверка при Streamlit rerun.",
            "cache_reused": True,
            "finished_at_utc": utc_now(),
            "config": cfg,
        })
        return cached

    detect = detector or detect_latest_official_draw
    ingest = ingestor or ingest_official_draw_record
    refresh = refresher or run_unified_downstream_refresh

    try:
        detection = detect(timeout=cfg["network_timeout_seconds"], validate_details=True, write_outputs=write_outputs)
        base["detection"] = detection
        base["checked_at_utc"] = detection.get("checked_at_utc", started)
        detection_status = detection.get("status")

        if detection_status == "official_unavailable":
            base.update(status="check_failed", message="Официалният източник не е достъпен. Локалните данни не са променени.")
        elif detection_status == "up_to_date":
            base.update(status="up_to_date", message="Локалният официален тираж е актуален.")
        elif detection_status == "local_ahead":
            base.update(status="operator_review_required", message="Локалните данни изглеждат пред официалния източник. Автоматично действие е блокирано.")
        elif detection_status == "update_available":
            base.update(status="update_available", message="Открит е нов официален тираж.")
            if cfg["auto_apply_enabled"]:
                base["auto_apply_attempted"] = True
                official = detection.get("official_latest_draw") or {}
                ingestion = ingest(_official_to_record(official))
                base["ingestion"] = ingestion
                if ingestion.get("status") == "inserted":
                    base.update(status="draw_applied", message="Новият официален тираж беше приложен безопасно.")
                    if cfg["auto_refresh_enabled"]:
                        base["auto_refresh_attempted"] = True
                        downstream = refresh(timeout_seconds=cfg["downstream_timeout_seconds"])
                        base["downstream_refresh"] = downstream
                        if downstream.get("status") == "completed":
                            base.update(status="completed", message="Новият тираж и оперативната downstream верига са обновени успешно.")
                        else:
                            base.update(status="refresh_check_required", message="Тиражът е приложен, но downstream веригата изисква проверка.")
                else:
                    base.update(status="ingestion_blocked", message="Автоматичното прилагане беше блокирано безопасно.")
        else:
            base.update(status="operator_review_required", message=f"Непознат detection статус: {detection_status}")
    except Exception as exc:
        base.update(status="failed", message=str(exc), error_type=type(exc).__name__)

    base["finished_at_utc"] = utc_now()
    if write_outputs:
        _write_outputs(base)
    return base

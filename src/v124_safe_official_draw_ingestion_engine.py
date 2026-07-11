from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.bst_official_sync_engine import (
    CSV_FIELDS,
    DATA_PATH,
    EXPORT_PATH,
    normalize_record,
    parse_official_draw,
    read_rows,
    validate_record,
    write_rows,
)
from src.v123_bst_official_draw_detection_engine import detect_latest_official_draw

ROOT = Path(__file__).resolve().parents[1]
BACKUP_ROOT = ROOT / "data" / "backups" / "step124_official_draw_ingestion"
STAGING_ROOT = ROOT / "data" / "staging" / "step124_official_draw_ingestion"
AUDIT_JSONL = ROOT / "reports" / "v124_safe_official_draw_ingestion_audit.jsonl"
STATUS_JSON = ROOT / "models" / "v124_safe_official_draw_ingestion_status.json"
SUMMARY_MD = ROOT / "reports" / "v124_safe_official_draw_ingestion_summary.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")


def _safe_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _draw_tuple(row: dict[str, Any]) -> tuple[int, int]:
    return (_safe_int(row.get("draw_year")) or 0, _safe_int(row.get("draw_number")) or 0)


def _draw_key(row: dict[str, Any]) -> str:
    key = str(row.get("draw_key") or "").strip()
    if key:
        return key
    year, number = _draw_tuple(row)
    return f"{year}-{number}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _append_audit(event: dict[str, Any], audit_path: Path) -> None:
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def _write_status(report: dict[str, Any], status_path: Path = STATUS_JSON, summary_path: Path = SUMMARY_MD) -> None:
    status_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_path.write_text(
        "\n".join([
            "# Step 124 — Safe Official Draw Ingestion",
            "",
            f"- Status: **{report.get('status', '')}**",
            f"- Run ID: `{report.get('run_id', '')}`",
            f"- Draw: **{report.get('draw_key', '')}**",
            f"- Inserted: **{report.get('inserted', False)}**",
            f"- Duplicate blocked: **{report.get('duplicate_blocked', False)}**",
            f"- Backup created: **{report.get('backup_created', False)}**",
            f"- Staging validated: **{report.get('staging_validated', False)}**",
            f"- Rollback performed: **{report.get('rollback_performed', False)}**",
            "- Downstream refresh started: **No**",
            "",
            str(report.get("message") or ""),
            "",
        ]),
        encoding="utf-8",
    )


def _validate_staged_dataset(path: Path, expected_key: str, previous_count: int) -> dict[str, Any]:
    rows = read_rows(path)
    keys = [_draw_key(row) for row in rows]
    duplicate_keys = sorted({key for key in keys if keys.count(key) > 1})
    errors: list[str] = []
    if len(rows) != previous_count + 1:
        errors.append(f"expected {previous_count + 1} rows, found {len(rows)}")
    if expected_key not in keys:
        errors.append(f"expected draw {expected_key} is missing")
    if duplicate_keys:
        errors.append("duplicate draw keys: " + ", ".join(duplicate_keys))
    latest = max(rows, key=_draw_tuple, default={})
    if _draw_key(latest) != expected_key:
        errors.append(f"latest staged draw is {_draw_key(latest)}, expected {expected_key}")
    return {
        "passed": not errors,
        "errors": errors,
        "row_count": len(rows),
        "latest_draw_key": _draw_key(latest) if latest else "",
    }


def ingest_official_draw_record(
    record: dict[str, Any],
    *,
    data_path: Path = DATA_PATH,
    export_path: Path = EXPORT_PATH,
    backup_root: Path = BACKUP_ROOT,
    staging_root: Path = STAGING_ROOT,
    audit_path: Path = AUDIT_JSONL,
    write_status: bool = True,
    failure_hook: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Safely append one strictly newer official draw without refreshing downstream artifacts."""
    run_id = _run_id()
    started_at = utc_now()
    report: dict[str, Any] = {
        "step": "124",
        "name": "Safe Official Draw Ingestion",
        "run_id": run_id,
        "started_at_utc": started_at,
        "status": "failed",
        "message": "",
        "draw_key": "",
        "inserted": False,
        "duplicate_blocked": False,
        "backup_created": False,
        "staging_validated": False,
        "promoted": False,
        "rollback_performed": False,
        "downstream_refresh_started": False,
        "data_path": str(data_path),
        "export_path": str(export_path),
    }

    backup_dir = backup_root / run_id
    staging_dir = staging_root / run_id
    staged_data = staging_dir / "prize_winner_history.csv"
    staged_export = staging_dir / "user_journal_exports" / "prize_winner_history.csv"
    backup_data = backup_dir / "prize_winner_history.csv"
    backup_export = backup_dir / "user_journal_exports" / "prize_winner_history.csv"

    try:
        existing = read_rows(data_path)
        normalized = normalize_record(record, existing)
        errors = validate_record(normalized)
        draw_key = _draw_key(normalized)
        report["draw_key"] = draw_key
        report["validation_errors"] = errors
        if errors:
            report.update(status="validation_failed", message="Новият официален тираж не премина валидация.")
            return report

        existing_by_key = {_draw_key(row): row for row in existing}
        if draw_key in existing_by_key:
            report.update(
                status="duplicate_blocked",
                message="Тиражът вече съществува. Не са направени промени.",
                duplicate_blocked=True,
            )
            return report

        latest = max(existing, key=_draw_tuple, default={})
        if latest and _draw_tuple(normalized) <= _draw_tuple(latest):
            report.update(
                status="not_strictly_newer",
                message=f"Тиражът {draw_key} не е по-нов от локалния {_draw_key(latest)}.",
            )
            return report
        if latest:
            latest_year, latest_number = _draw_tuple(latest)
            new_year, new_number = _draw_tuple(normalized)
            contiguous = (
                (new_year == latest_year and new_number == latest_number + 1)
                or (new_year == latest_year + 1 and new_number == 1)
            )
            if not contiguous:
                report.update(
                    status="draw_gap_blocked",
                    message=(
                        f"Открита е празнина между локалния {_draw_key(latest)} и новия {draw_key}. "
                        "Step 124 отказва частичен импорт; липсващите тиражи трябва да се приложат последователно."
                    ),
                )
                return report

        if not data_path.exists():
            raise FileNotFoundError(f"Primary source of truth does not exist: {data_path}")
        if not export_path.exists():
            raise FileNotFoundError(f"Journal export mirror does not exist: {export_path}")

        backup_export.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(data_path, backup_data)
        shutil.copy2(export_path, backup_export)
        report["backup_created"] = True
        report["backup_dir"] = str(backup_dir)
        report["backup_sha256"] = {
            "primary": _sha256(backup_data),
            "export": _sha256(backup_export),
        }
        if failure_hook:
            failure_hook("after_backup")

        staged_export.parent.mkdir(parents=True, exist_ok=True)
        staged_rows = [dict(row) for row in existing] + [normalized]
        write_rows(staged_rows, staged_data)
        shutil.copy2(staged_data, staged_export)
        validation = _validate_staged_dataset(staged_data, draw_key, len(existing))
        mirror_equal = _sha256(staged_data) == _sha256(staged_export)
        validation["mirror_equal"] = mirror_equal
        if not mirror_equal:
            validation["errors"].append("staged journal mirror differs from primary")
            validation["passed"] = False
        report["staging_validation"] = validation
        if not validation["passed"]:
            report.update(status="staging_failed", message="Staging проверката не премина. Локалните данни не са променени.")
            return report
        report["staging_validated"] = True
        report["staging_dir"] = str(staging_dir)
        if failure_hook:
            failure_hook("after_staging")

        data_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        primary_fd, primary_tmp_name = tempfile.mkstemp(
            prefix="step124_primary_", suffix=".csv", dir=data_path.parent
        )
        export_fd, export_tmp_name = tempfile.mkstemp(
            prefix="step124_export_", suffix=".csv", dir=export_path.parent
        )
        os.close(primary_fd)
        os.close(export_fd)
        primary_tmp = Path(primary_tmp_name)
        export_tmp = Path(export_tmp_name)
        try:
            shutil.copy2(staged_data, primary_tmp)
            shutil.copy2(staged_export, export_tmp)
            os.replace(primary_tmp, data_path)
            if failure_hook:
                failure_hook("after_primary_promote")
            os.replace(export_tmp, export_path)
        finally:
            primary_tmp.unlink(missing_ok=True)
            export_tmp.unlink(missing_ok=True)

        if _sha256(data_path) != _sha256(export_path):
            raise RuntimeError("Promoted primary and journal mirror are not identical")
        promoted_rows = read_rows(data_path)
        promoted_latest = max(promoted_rows, key=_draw_tuple, default={})
        if _draw_key(promoted_latest) != draw_key:
            raise RuntimeError("Promoted dataset does not expose the ingested draw as latest")

        report.update(
            status="inserted",
            message="Новият официален тираж е приложен безопасно към source of truth и journal mirror.",
            inserted=True,
            promoted=True,
            final_count=len(promoted_rows),
            promoted_sha256=_sha256(data_path),
        )
        return report
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
        if report.get("backup_created"):
            try:
                data_path.parent.mkdir(parents=True, exist_ok=True)
                export_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_data, data_path)
                shutil.copy2(backup_export, export_path)
                report["rollback_performed"] = True
                report["status"] = "rolled_back"
                report["message"] = "Възникна грешка и оригиналните файлове бяха възстановени от backup."
            except Exception as rollback_exc:
                report["status"] = "rollback_failed"
                report["rollback_error"] = str(rollback_exc)
                report["message"] = "Възникна грешка и автоматичният rollback не успя. Използвай записания backup."
        else:
            report["message"] = "Възникна грешка преди промяна на локалните данни."
        return report
    finally:
        report["finished_at_utc"] = utc_now()
        _append_audit(report, audit_path)
        if write_status:
            _write_status(report)


def detect_and_ingest_latest_official_draw(
    *,
    timeout: int = 30,
    data_path: Path = DATA_PATH,
    export_path: Path = EXPORT_PATH,
    backup_root: Path = BACKUP_ROOT,
    staging_root: Path = STAGING_ROOT,
    audit_path: Path = AUDIT_JSONL,
    auto_lightweight_refresh: bool = True,
    downstream_timeout_seconds: int = 900,
) -> dict[str, Any]:
    detection = detect_latest_official_draw(timeout=timeout, validate_details=True, write_outputs=True)
    if detection.get("status") != "update_available":
        report = {
            "step": "124",
            "name": "Safe Official Draw Ingestion",
            "run_id": _run_id(),
            "started_at_utc": utc_now(),
            "finished_at_utc": utc_now(),
            "status": "nothing_to_ingest" if detection.get("status") == "up_to_date" else "detection_blocked",
            "message": detection.get("message") or "Няма надеждно открит нов официален тираж.",
            "inserted": False,
            "duplicate_blocked": False,
            "backup_created": False,
            "staging_validated": False,
            "promoted": False,
            "rollback_performed": False,
            "downstream_refresh_started": False,
            "detection": detection,
        }
        _append_audit(report, audit_path)
        _write_status(report)
        return report

    official = detection.get("official_latest_draw") or {}
    record = parse_official_draw(int(official["year"]), int(official["draw_number"]), timeout=timeout, save_raw=True)
    result = ingest_official_draw_record(
        record,
        data_path=data_path,
        export_path=export_path,
        backup_root=backup_root,
        staging_root=staging_root,
        audit_path=audit_path,
        write_status=True,
    )
    result["detection"] = detection
    if result.get("status") == "inserted" and auto_lightweight_refresh:
        from src.v143_automatic_lightweight_downstream_refresh_engine import (
            run_automatic_lightweight_refresh_after_ingestion,
        )

        automatic_refresh = run_automatic_lightweight_refresh_after_ingestion(
            result,
            timeout_seconds=downstream_timeout_seconds,
            write_outputs=True,
        )
        result["automatic_lightweight_refresh"] = automatic_refresh
        result["downstream_refresh_started"] = True
        if automatic_refresh.get("status") == "completed":
            result["message"] = (
                "Новият официален тираж е приложен и всички леки downstream слоеве са обновени автоматично."
            )
        else:
            result["message"] = (
                "Новият официален тираж е приложен, но downstream обновяването изисква проверка."
            )
    _write_status(result)
    return result

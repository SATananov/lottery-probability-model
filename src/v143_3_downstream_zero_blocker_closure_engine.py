from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v122_unified_official_draw_freshness_engine import MODEL_ARTIFACTS, build_freshness_report
from src.v142_downstream_freshness_repair_engine import run_targeted_repair

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / "models" / "v143_3_downstream_zero_blocker_status.json"
REPORT_JSON = ROOT / "reports" / "v143_3_downstream_zero_blocker_report.json"
SUMMARY_MD = ROOT / "reports" / "v143_3_downstream_zero_blocker_summary.md"

BINARY_MODEL_SUFFIXES = {".joblib", ".pkl", ".pickle", ".onnx", ".pt", ".pth", ".h5", ".keras"}
PERSONAL_PATHS = [
    ROOT / "data" / "user_journal.db",
    ROOT / "data" / "user_journal_exports",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _heavy_model_paths() -> list[Path]:
    paths = {path.resolve() for path in MODEL_ARTIFACTS if path.exists() and path.is_file()}
    models_dir = ROOT / "models"
    if models_dir.exists():
        for path in models_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in BINARY_MODEL_SUFFIXES:
                paths.add(path.resolve())
    return sorted(paths)


def _personal_files() -> list[Path]:
    files: set[Path] = set()
    for path in PERSONAL_PATHS:
        if path.is_file():
            files.add(path.resolve())
        elif path.is_dir():
            files.update(child.resolve() for child in path.rglob("*") if child.is_file())
    return sorted(files)


def _snapshot(paths: list[Path], *, keep_bytes: bool = False) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        row: dict[str, Any] = {"sha256": _sha256(path), "size_bytes": path.stat().st_size}
        if keep_bytes:
            row["content"] = path.read_bytes()
        result[rel] = row
    return result


def _current_snapshot(paths: list[Path]) -> dict[str, dict[str, Any]]:
    return _snapshot([path for path in paths if path.exists() and path.is_file()], keep_bytes=False)


def _changes(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in sorted(set(before) | set(after)):
        before_row = before.get(rel)
        after_row = after.get(rel)
        if before_row and after_row and before_row.get("sha256") == after_row.get("sha256"):
            continue
        rows.append({
            "path": rel,
            "change": "added" if before_row is None else ("removed" if after_row is None else "modified"),
            "before_sha256": before_row.get("sha256") if before_row else None,
            "after_sha256": after_row.get("sha256") if after_row else None,
        })
    return rows


def _restore(snapshot: dict[str, dict[str, Any]]) -> list[str]:
    restored: list[str] = []
    for rel, row in snapshot.items():
        content = row.get("content")
        if content is None:
            continue
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or _sha256(path) != row.get("sha256"):
            path.write_bytes(content)
            restored.append(rel)
    return restored


def _write(report: dict[str, Any]) -> None:
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    for path in (STATUS_JSON, REPORT_JSON):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded, encoding="utf-8")

    before = report.get("before", {})
    after = report.get("after", {})
    lines = [
        "# Step 143.3 — Final Downstream Freshness Repair and Zero-Blocker Closure",
        "",
        f"- Status: **{report.get('status')}**",
        f"- Before blockers: **{before.get('blocking_out_of_sync_count', '—')}**",
        f"- After blockers: **{after.get('blocking_out_of_sync_count', '—')}**",
        f"- Final freshness: **{after.get('overall_status', '—')}**",
        "- Heavy ML retraining: **No**",
        f"- Heavy model artifacts changed: **{len(report.get('heavy_model_changes', []))}**",
        f"- Personal files changed after protection: **{len(report.get('personal_changes_after_restore', []))}**",
        "",
        "## Repair stages",
    ]
    for row in report.get("repair", {}).get("results", []):
        lines.append(f"- {row.get('name')}: **{row.get('status')}** — {row.get('message', '')}")
    if report.get("remaining_blockers"):
        lines.extend(["", "## Remaining blockers"])
        for blocker in report["remaining_blockers"]:
            lines.append(f"- {blocker.get('label')}: {blocker.get('status')} — {blocker.get('message')}")
    lines.extend([
        "",
        "## Guardrails",
        "",
        "The closure updates only lightweight downstream datasets, statistical reports, decision artifacts, and ticket-pack outputs.",
        "Heavy trained models remain governed by their separate manual training policy.",
        "Personal journal files are protected and restored if a downstream builder touches them incidentally.",
        "",
    ])
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def run_final_zero_blocker_closure(
    *,
    plan_only: bool = False,
    timeout_seconds: int = 900,
    write_outputs: bool = True,
) -> dict[str, Any]:
    started = utc_now()
    before = build_freshness_report(write_outputs=False)

    heavy_paths_before = _heavy_model_paths()
    heavy_before = _snapshot(heavy_paths_before)
    personal_paths_before = _personal_files()
    personal_before = _snapshot(personal_paths_before, keep_bytes=True)

    if plan_only:
        repair = run_targeted_repair(plan_only=True, timeout_seconds=timeout_seconds, write_outputs=False)
        report = {
            "step": "143.3",
            "name": "Final Downstream Freshness Repair and Zero-Blocker Closure",
            "started_at_utc": started,
            "finished_at_utc": utc_now(),
            "status": "planned" if repair.get("status") != "already_synced" else "already_synced",
            "plan_only": True,
            "before": before,
            "repair": repair,
            "after": before,
            "remaining_blockers": [
                source for source in before.get("sources", [])
                if source.get("key") != "official" and source.get("status") not in {"synced", "informational"}
            ],
            "heavy_ml_retraining_performed": False,
            "heavy_model_changes": [],
            "personal_changes_detected": [],
            "personal_files_restored": [],
            "personal_changes_after_restore": [],
        }
        if write_outputs:
            _write(report)
        return report

    repair = run_targeted_repair(
        plan_only=False,
        timeout_seconds=timeout_seconds,
        write_outputs=write_outputs,
    )

    heavy_after = _current_snapshot(_heavy_model_paths())
    heavy_changes = _changes(heavy_before, heavy_after)

    personal_after_run = _current_snapshot(_personal_files())
    personal_changes = _changes(
        {key: {k: v for k, v in row.items() if k != "content"} for key, row in personal_before.items()},
        personal_after_run,
    )
    restored = _restore(personal_before) if personal_changes else []
    personal_after_restore = _current_snapshot(_personal_files())
    personal_changes_after_restore = _changes(
        {key: {k: v for k, v in row.items() if k != "content"} for key, row in personal_before.items()},
        personal_after_restore,
    )

    after = build_freshness_report(write_outputs=write_outputs)
    remaining = [
        source for source in after.get("sources", [])
        if source.get("key") != "official" and source.get("status") not in {"synced", "informational"}
    ]
    zero_blocker = after.get("overall_status") == "synced" and int(after.get("blocking_out_of_sync_count", -1)) == 0 and not remaining
    repair_ok = repair.get("status") in {"completed", "already_synced"}
    protected_ok = not heavy_changes and not personal_changes_after_restore

    if zero_blocker and repair_ok and protected_ok:
        status = "completed"
    elif zero_blocker and protected_ok and repair.get("status") == "check_required":
        # The final source-of-truth check is authoritative. A stage may have returned a
        # conservative warning even though every tracked downstream layer is now current.
        status = "completed_with_stage_warning"
    else:
        status = "check_required"

    report = {
        "step": "143.3",
        "name": "Final Downstream Freshness Repair and Zero-Blocker Closure",
        "started_at_utc": started,
        "finished_at_utc": utc_now(),
        "status": status,
        "plan_only": False,
        "before": before,
        "repair": repair,
        "after": after,
        "zero_blocker_confirmed": zero_blocker,
        "remaining_blockers": remaining,
        "heavy_ml_retraining_performed": False,
        "heavy_model_changes": heavy_changes,
        "personal_changes_detected": personal_changes,
        "personal_files_restored": restored,
        "personal_changes_after_restore": personal_changes_after_restore,
        "guardrails": {
            "heavy_model_policy": "manual_only",
            "personal_journal_protection": "snapshot_and_restore",
            "final_authority": "Step 122 official draw freshness report",
        },
    }
    if write_outputs:
        _write(report)
    return report

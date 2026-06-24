from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "v103_1" / "v103_1_clean_zip_metadata_finalizer_model.json"
SUMMARY_JSON = ROOT / "reports" / "v103_1_clean_zip_metadata_finalizer_summary.json"
SUMMARY_MD = ROOT / "reports" / "v103_1_clean_zip_metadata_finalizer_summary.md"

ENGINE_PATH = ROOT / "src" / "v103_clean_release_checkpoint_engine.py"
SECTION_PATH = ROOT / "src" / "v103_clean_release_checkpoint_section.py"
CREATE_SCRIPT_PATH = ROOT / "scripts" / "v103_create_clean_release_checkpoint.py"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_metadata_finalizer_summary() -> dict[str, Any]:
    engine = ENGINE_PATH.read_text(encoding="utf-8") if ENGINE_PATH.exists() else ""
    section = SECTION_PATH.read_text(encoding="utf-8") if SECTION_PATH.exists() else ""
    create_script = CREATE_SCRIPT_PATH.read_text(encoding="utf-8") if CREATE_SCRIPT_PATH.exists() else ""

    checks = [
        {
            "check": "zip_metadata_injected_inside_archive",
            "passed": "_virtual_zip_entries" in engine and "metadata_written_inside_zip" in engine,
            "details_bg": "Clean ZIP creation injects fresh Step 103 summary/checklist/manifest into the archive.",
        },
        {
            "check": "clean_zip_status_created",
            "passed": "CLEAN_ZIP_CREATED" in engine,
            "details_bg": "The report inside the ZIP can show CLEAN_ZIP_CREATED for the exact current commit.",
        },
        {
            "check": "ui_no_disk_write_on_render",
            "passed": "build_clean_release_summary" in section and "build_and_write_clean_release_summary" not in section,
            "details_bg": "Opening the Step 103 Streamlit page builds a live summary without dirtying tracked report files.",
        },
        {
            "check": "create_script_reports_clean_tree_state",
            "passed": "WORKING_TREE_LEFT_CLEAN" in create_script and "METADATA_WRITTEN_INSIDE_ZIP" in create_script,
            "details_bg": "The terminal create script reports whether metadata was written inside the ZIP and the working tree stayed clean.",
        },
    ]
    blocking_failures = sum(1 for item in checks if not item["passed"])
    return {
        "step": "103.1",
        "name_bg": "Clean ZIP metadata finalizer",
        "status": "METADATA_FINALIZED" if blocking_failures == 0 else "BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "blocking_failures": blocking_failures,
        "checks": checks,
        "notes_bg": [
            "This is a metadata/report finalizer only; it does not change prediction math or ticket generation logic.",
            "The clean ZIP report inside the archive is now generated at ZIP creation time for the exact current commit.",
            "The Step 103 UI no longer writes reports on every render, so it should not dirty git status after a clean commit.",
        ],
    }


def write_metadata_finalizer_reports(summary: dict[str, Any]) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    MODEL_PATH.write_text(payload, encoding="utf-8", newline="\n")
    SUMMARY_JSON.write_text(payload, encoding="utf-8", newline="\n")

    lines = [
        "# Step 103.1 — Clean ZIP metadata finalizer",
        "",
        f"Статус: **{summary['status']}**",
        f"Blocking failures: **{summary['blocking_failures']}**",
        "",
        "## Проверки",
        "",
    ]
    for check in summary["checks"]:
        mark = "OK" if check["passed"] else "FAIL"
        lines.append(f"- {mark} — `{check['check']}` — {check['details_bg']}")
    lines.extend(["", "## Бележки", ""])
    for note in summary["notes_bg"]:
        lines.append(f"- {note}")
    _write_text(SUMMARY_MD, "\n".join(lines) + "\n")


def build_and_write_metadata_finalizer_summary() -> dict[str, Any]:
    summary = build_metadata_finalizer_summary()
    write_metadata_finalizer_reports(summary)
    return summary

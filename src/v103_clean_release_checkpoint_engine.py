from __future__ import annotations

import csv
import json
import os
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "v103" / "v103_clean_release_checkpoint_model.json"
SUMMARY_JSON = ROOT / "reports" / "v103_clean_release_checkpoint_summary.json"
SUMMARY_MD = ROOT / "reports" / "v103_clean_release_checkpoint_summary.md"
CHECKLIST_CSV = ROOT / "reports" / "v103_clean_release_checkpoint_checklist.csv"
MANIFEST_CSV = ROOT / "reports" / "v103_clean_release_checkpoint_manifest.csv"

PROJECT_NAME = "lottery-probability-model"
FORBIDDEN_PARTS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ipynb_checkpoints",
    "mlruns",
    "notebook_test_outputs",
}
FORBIDDEN_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".tmp",
    ".temp",
    ".bak",
    ".backup",
    ".patch",
    ".zip",
}
HELPER_PREFIXES = ("apply_", "fix_", "patch_")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _run_git(args: list[str]) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    return completed.returncode == 0, output.strip()


def _short_commit() -> str:
    ok, output = _run_git(["rev-parse", "--short", "HEAD"])
    return output.strip() if ok and output.strip() else "nogit"


def _git_status_short() -> str:
    ok, output = _run_git(["status", "--short"])
    return output.strip() if ok else "GIT_STATUS_UNAVAILABLE: " + output


def _tracked_files() -> list[str]:
    ok, output = _run_git(["ls-files", "-z"])
    if not ok:
        return []
    return [item for item in output.split("\x00") if item]


def is_forbidden_release_path(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    name = parts[-1] if parts else normalized

    if any(part in FORBIDDEN_PARTS for part in parts):
        return True
    if Path(name).suffix.lower() in FORBIDDEN_SUFFIXES:
        return True
    if name.startswith(HELPER_PREFIXES) and Path(name).suffix.lower() in {".py", ".ps1", ".cmd", ".bat"}:
        return True
    return False


def _desktop_dir() -> Path:
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        desktop = Path(userprofile) / "Desktop"
        if desktop.exists():
            return desktop
    desktop = Path.home() / "Desktop"
    desktop.mkdir(parents=True, exist_ok=True)
    return desktop


def build_clean_release_summary() -> dict[str, Any]:
    tracked = _tracked_files()
    status = _git_status_short()
    forbidden_tracked = [path for path in tracked if is_forbidden_release_path(path)]

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    commit = _short_commit()
    zip_name = f"{PROJECT_NAME}_step103_104_clean-checkpoint_{stamp}_{commit}.zip"
    recommended_path = str(_desktop_dir() / zip_name)

    checks = [
        {
            "check": "git_available",
            "passed": bool(tracked),
            "details_bg": "Git tracked file list is available for clean ZIP creation.",
        },
        {
            "check": "working_tree_clean_before_zip",
            "passed": status == "",
            "details_bg": "Clean ZIP should be created after commit/push, when git status is empty.",
        },
        {
            "check": "forbidden_tracked_files",
            "passed": len(forbidden_tracked) == 0,
            "details_bg": "Tracked files do not include .git, cache, helper patch files, nested ZIPs, or temp artifacts.",
        },
        {
            "check": "tracked_zip_strategy",
            "passed": True,
            "details_bg": "ZIP creation uses tracked project files only, so .git and cache folders are excluded by design.",
        },
    ]
    blocking_failures = sum(1 for item in checks if not item["passed"] and item["check"] != "working_tree_clean_before_zip")
    status_code = "READY_FOR_CLEAN_ZIP" if blocking_failures == 0 else "BLOCKED"
    if status:
        status_code = "WAITING_FOR_CLEAN_GIT_STATUS"

    summary: dict[str, Any] = {
        "step": 103,
        "name_bg": "Clean ZIP checkpoint",
        "status": status_code,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "commit": commit,
        "tracked_file_count": len(tracked),
        "forbidden_tracked_count": len(forbidden_tracked),
        "forbidden_tracked_preview": forbidden_tracked[:30],
        "git_status_short": status,
        "recommended_zip_path": recommended_path,
        "recommended_command": "python .\\scripts\\v103_create_clean_release_checkpoint.py",
        "blocking_failures": blocking_failures,
        "checks": checks,
        "notes_bg": [
            "Normal folder ZIP is not safe for this project because it can include .git, __pycache__, .pyc and helper scripts.",
            "The clean checkpoint script uses git tracked files only and refuses to create the ZIP while git status is not clean.",
            "Run the clean ZIP script after committing Step 103/104.",
        ],
    }
    return summary


def write_clean_release_reports(summary: dict[str, Any]) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    md_lines = [
        "# Step 103 — Clean ZIP checkpoint",
        "",
        f"Статус: **{summary['status']}**",
        f"Commit: `{summary['commit']}`",
        f"Tracked files: **{summary['tracked_file_count']}**",
        f"Forbidden tracked files: **{summary['forbidden_tracked_count']}**",
        "",
        "## Препоръчано действие",
        "",
        "След като `git status --short` е празен:",
        "",
        "```powershell",
        summary["recommended_command"],
        "```",
        "",
        "## Бележки",
        "",
    ]
    for note in summary["notes_bg"]:
        md_lines.append(f"- {note}")
    _write_text(SUMMARY_MD, "\n".join(md_lines) + "\n")

    with CHECKLIST_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "details_bg"])
        writer.writeheader()
        for row in summary["checks"]:
            writer.writerow(row)

    tracked = _tracked_files()
    with MANIFEST_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["relative_path", "included_in_clean_zip"])
        writer.writeheader()
        for relative_path in tracked:
            writer.writerow({
                "relative_path": relative_path,
                "included_in_clean_zip": not is_forbidden_release_path(relative_path),
            })


def build_and_write_clean_release_summary() -> dict[str, Any]:
    summary = build_clean_release_summary()
    write_clean_release_reports(summary)
    return summary


def create_clean_release_checkpoint(output_path: str | None = None, require_clean_status: bool = True) -> dict[str, Any]:
    summary = build_clean_release_summary()
    status = summary.get("git_status_short", "")
    if require_clean_status and status:
        raise RuntimeError(
            "Git status is not clean. Commit/push first, then create the clean ZIP.\n" + str(status)
        )

    tracked = _tracked_files()
    if not tracked:
        raise RuntimeError("No git tracked files found. Cannot create a reliable clean ZIP.")

    if output_path:
        zip_path = Path(output_path)
    else:
        zip_path = Path(str(summary["recommended_zip_path"]))
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    included: list[str] = []
    skipped: list[str] = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for relative_path in tracked:
            if is_forbidden_release_path(relative_path):
                skipped.append(relative_path)
                continue
            source = ROOT / relative_path
            if not source.is_file():
                continue
            arcname = f"{PROJECT_NAME}/{relative_path.replace('\\\\', '/')}"
            zf.write(source, arcname)
            included.append(relative_path)

    result = {
        "zip_path": str(zip_path),
        "included_files": len(included),
        "skipped_files": len(skipped),
        "skipped_preview": skipped[:30],
        "commit": summary["commit"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    return result


def load_clean_release_summary() -> dict[str, Any]:
    if not SUMMARY_JSON.exists():
        return build_and_write_clean_release_summary()
    try:
        return json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return build_and_write_clean_release_summary()

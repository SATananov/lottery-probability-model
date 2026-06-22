from __future__ import annotations

from pathlib import Path
import os
import subprocess
from datetime import datetime, timezone
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PATHS = ["models", "reports", "data"]
SAFE_NOTE = (
    "GitHub синхронът качва локално обновените model/report/data artifacts. "
    "Той не променя логиката на моделите и не е прогноза или гаранция за печалба."
)


def _run_git(args: list[str], timeout_seconds: int = 180) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
        return {
            "args": ["git", *args],
            "returncode": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "ok": proc.returncode == 0,
        }
    except Exception as exc:  # pragma: no cover
        return {
            "args": ["git", *args],
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "ok": False,
        }


def git_status_short() -> str:
    result = _run_git(["status", "--short"], timeout_seconds=60)
    if not result.get("ok"):
        return str(result.get("stderr") or result.get("stdout") or "Git status failed").strip()
    return str(result.get("stdout") or "").strip()


def _status_for_paths(paths: list[str]) -> str:
    result = _run_git(["status", "--short", "--", *paths], timeout_seconds=60)
    if not result.get("ok"):
        return str(result.get("stderr") or result.get("stdout") or "Git status failed").strip()
    return str(result.get("stdout") or "").strip()


def commit_and_push_model_outputs(
    commit_message: str = "Sync model dependency center outputs",
    paths: list[str] | None = None,
) -> dict[str, Any]:
    selected_paths = paths or DEFAULT_PATHS
    before_all = git_status_short()
    before_selected = _status_for_paths(selected_paths)
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if not before_selected:
        return {
            "status": "Няма промени",
            "message": "Няма промени в models/reports/data за commit.",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "changed_files": before_all,
            "selected_changed_files": before_selected,
            "steps": [],
            "safe_note": SAFE_NOTE,
        }

    steps: list[dict[str, Any]] = []

    add_result = _run_git(["add", *selected_paths], timeout_seconds=120)
    steps.append({"name": "git add", **add_result})
    if not add_result.get("ok"):
        return {
            "status": "Грешка",
            "message": "git add не успя.",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "changed_files": before_all,
            "selected_changed_files": before_selected,
            "steps": steps,
            "safe_note": SAFE_NOTE,
        }

    commit_result = _run_git(["commit", "-m", commit_message], timeout_seconds=180)
    steps.append({"name": "git commit", **commit_result})
    combined_commit_output = (commit_result.get("stdout") or "") + (commit_result.get("stderr") or "")
    if not commit_result.get("ok") and "nothing to commit" not in combined_commit_output.lower():
        return {
            "status": "Грешка",
            "message": "git commit не успя.",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "changed_files": before_all,
            "selected_changed_files": before_selected,
            "steps": steps,
            "safe_note": SAFE_NOTE,
        }

    push_result = _run_git(["push"], timeout_seconds=300)
    steps.append({"name": "git push", **push_result})
    if not push_result.get("ok"):
        return {
            "status": "Грешка",
            "message": "git push не успя.",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "changed_files": before_all,
            "selected_changed_files": before_selected,
            "steps": steps,
            "safe_note": SAFE_NOTE,
        }

    latest = _run_git(["log", "--oneline", "-1"], timeout_seconds=60)
    after = git_status_short()
    return {
        "status": "OK",
        "message": "Промените в models/reports/data са commit-нати и качени в GitHub.",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "changed_files": before_all,
        "selected_changed_files": before_selected,
        "latest_commit": (latest.get("stdout") or "").strip(),
        "remaining_status": after,
        "steps": steps,
        "safe_note": SAFE_NOTE,
    }

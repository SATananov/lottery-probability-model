from __future__ import annotations

import json
import os
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

STEP = "143.2"
NAME = "Official Draw to GitHub Sync Validation and Audit"
REMOTE_NAME = "origin"

SYNC_EXACT_PATHS = (
    "data/historical_draws.csv",
    "data/v40_normalized_draw_events.csv",
    "data/v41_canonical_draw_events.csv",
)
SYNC_PREFIXES = ("models/", "reports/")
RUNTIME_AUDIT_PREFIX = "reports/runtime/v143_2_git_sync/"

SENSITIVE_EXACT_PATHS = (
    ".streamlit/secrets.toml",
    "data/user_journal.db",
)
SENSITIVE_PREFIXES = (
    "data/user_journal_exports/",
    "data/manual_backups/",
    ".venv/",
    "venv/",
    ".r-lib/",
)

STATUS_MESSAGES_BG = {
    "ready": "Git работното копие е готово за контролирана синхронизация.",
    "ready_with_unrelated_changes": (
        "Има други локални промени извън автоматичния обхват за синхронизация. "
        "Те няма да бъдат добавени към commit-а за тиража."
    ),
    "not_git_repo": "Папката не е Git repository.",
    "detached_head": "Git няма активен клон. Автоматичното качване е блокирано.",
    "origin_missing": "Липсва GitHub връзка с име origin.",
    "preexisting_staged_changes": (
        "Има предварително подготвени за Git запис файлове. Автоматичната синхронизация е блокирана, "
        "за да не попаднат чужди промени в commit-а."
    ),
    "preexisting_sync_scope_changes": (
        "Има неприключени промени в data/models/reports още преди новия тираж. "
        "Първо ги commit-ни, stash-ни или отмени."
    ),
    "nothing_to_commit_remote_confirmed": (
        "Няма нови файлове за Git запис, а текущият локален запис е потвърден в GitHub клона."
    ),
    "remote_confirmed": "Git записът е качен и локалният commit SHA съвпада с GitHub клона.",
    "git_add_failed": "Подготовката на файловете за Git запис не успя.",
    "unsafe_staged_files": "Засечени са подготвени файлове извън разрешения обхват за синхронизация.",
    "nothing_staged": "След контролираната подготовка няма файлове за Git запис.",
    "commit_failed": "Създаването на Git запис не успя.",
    "local_commit_pending_push": "Git записът е създаден локално, но качването не е завършило.",
    "remote_confirmation_failed": "Качването приключи, но SHA на GitHub записа не можа да бъде потвърден.",
    "remote_mismatch": "Локалният HEAD не съвпада с GitHub клона.",
    "no_pending_push_audit": "Няма последен Step 143.2 отчет, който да изисква повторно качване.",
    "retry_head_mismatch": "Текущият HEAD е различен от записа в чакащия отчет. Повторното качване е блокирано.",
    "retry_branch_mismatch": "Текущият клон е различен от клона в чакащия отчет. Повторното качване е блокирано.",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalise_path(value: str) -> str:
    path = str(value or "").replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path


def _is_sensitive(path: str) -> bool:
    value = _normalise_path(path)
    lowered = value.lower()
    if lowered in {item.lower() for item in SENSITIVE_EXACT_PATHS}:
        return True
    if any(lowered.startswith(prefix.lower()) for prefix in SENSITIVE_PREFIXES):
        return True
    if lowered == ".env" or lowered.startswith(".env."):
        return True
    return False


def _is_sync_scope(path: str) -> bool:
    value = _normalise_path(path)
    if not value or _is_sensitive(value):
        return False
    if value.startswith(RUNTIME_AUDIT_PREFIX):
        return False
    if value in SYNC_EXACT_PATHS:
        return True
    return any(value.startswith(prefix) for prefix in SYNC_PREFIXES)


def _sanitise_remote_url(value: str) -> str:
    text = str(value or "").strip()
    # Hide credentials in URLs such as https://user:token@example.com/repo.git.
    return re.sub(r"(https?://)[^/@]+@", r"\1***@", text)


def _run_git(
    args: list[str],
    *,
    repo_root: Path = ROOT,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "command": ["git", *args],
            "stdout": completed.stdout or "",
            "stderr": completed.stderr or "",
        }
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        return {
            "ok": False,
            "returncode": None,
            "command": ["git", *args],
            "stdout": "",
            "stderr": str(exc),
        }


def _parse_porcelain_z(raw: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    parts = raw.split("\0")
    index = 0
    while index < len(parts):
        record = parts[index]
        index += 1
        if not record or len(record) < 3:
            continue
        xy = record[:2]
        path = _normalise_path(record[3:] if len(record) > 3 else "")
        original_path = ""
        if ("R" in xy or "C" in xy) and index < len(parts):
            original_path = _normalise_path(parts[index])
            index += 1
        if path:
            entries.append({"xy": xy, "path": path, "original_path": original_path})
    return entries


def _worktree_entries(repo_root: Path = ROOT) -> tuple[list[dict[str, str]], dict[str, Any]]:
    result = _run_git(
        ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
        repo_root=repo_root,
        timeout_seconds=60,
    )
    if not result["ok"]:
        return [], result
    return _parse_porcelain_z(str(result.get("stdout") or "")), result


def _staged_paths(entries: list[dict[str, str]]) -> list[str]:
    paths: list[str] = []
    for entry in entries:
        xy = entry.get("xy", "  ")
        if xy != "??" and xy[:1] not in {"", " "}:
            paths.append(entry.get("path", ""))
    return sorted({path for path in paths if path})


def capture_git_snapshot(repo_root: Path = ROOT) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    repo_check = _run_git(["rev-parse", "--is-inside-work-tree"], repo_root=repo_root, timeout_seconds=30)
    if not repo_check["ok"] or str(repo_check.get("stdout", "")).strip() != "true":
        return {
            "step": STEP,
            "captured_at_utc": utc_now(),
            "status": "not_git_repo",
            "message_bg": STATUS_MESSAGES_BG["not_git_repo"],
            "can_sync": False,
            "repo_root": str(repo_root),
            "entries": [],
            "changed_paths": [],
            "staged_paths": [],
            "sync_scope_paths": [],
            "unrelated_paths": [],
            "sensitive_paths": [],
        }

    branch_result = _run_git(["branch", "--show-current"], repo_root=repo_root, timeout_seconds=30)
    branch = str(branch_result.get("stdout") or "").strip()
    head_result = _run_git(["rev-parse", "HEAD"], repo_root=repo_root, timeout_seconds=30)
    local_head = str(head_result.get("stdout") or "").strip()
    remote_result = _run_git(["remote", "get-url", REMOTE_NAME], repo_root=repo_root, timeout_seconds=30)
    remote_url = _sanitise_remote_url(str(remote_result.get("stdout") or "").strip())
    entries, status_result = _worktree_entries(repo_root)

    changed_paths = sorted({entry["path"] for entry in entries})
    staged_paths = _staged_paths(entries)
    sync_scope_paths = sorted(path for path in changed_paths if _is_sync_scope(path))
    sensitive_paths = sorted(path for path in changed_paths if _is_sensitive(path))
    unrelated_paths = sorted(path for path in changed_paths if path not in set(sync_scope_paths))

    if not branch:
        status = "detached_head"
    elif not remote_result["ok"]:
        status = "origin_missing"
    elif staged_paths:
        status = "preexisting_staged_changes"
    elif sync_scope_paths:
        status = "preexisting_sync_scope_changes"
    elif unrelated_paths:
        status = "ready_with_unrelated_changes"
    else:
        status = "ready"

    return {
        "step": STEP,
        "captured_at_utc": utc_now(),
        "status": status,
        "message_bg": STATUS_MESSAGES_BG[status],
        "can_sync": status in {"ready", "ready_with_unrelated_changes"},
        "repo_root": str(repo_root),
        "branch": branch,
        "remote_name": REMOTE_NAME,
        "remote_url": remote_url,
        "local_head": local_head,
        "entries": entries,
        "changed_paths": changed_paths,
        "staged_paths": staged_paths,
        "sync_scope_paths": sync_scope_paths,
        "unrelated_paths": unrelated_paths,
        "sensitive_paths": sensitive_paths,
        "git_status_ok": bool(status_result.get("ok")),
    }


def _remote_head(repo_root: Path, branch: str) -> dict[str, Any]:
    result = _run_git(
        ["ls-remote", "--heads", REMOTE_NAME, f"refs/heads/{branch}"],
        repo_root=repo_root,
        timeout_seconds=120,
    )
    remote_sha = ""
    if result["ok"]:
        line = next((line for line in str(result.get("stdout") or "").splitlines() if line.strip()), "")
        if line:
            remote_sha = line.split()[0].strip()
    return {"ok": bool(result["ok"] and remote_sha), "sha": remote_sha, "details": result}


def _current_head(repo_root: Path) -> str:
    result = _run_git(["rev-parse", "HEAD"], repo_root=repo_root, timeout_seconds=30)
    return str(result.get("stdout") or "").strip() if result["ok"] else ""


def _base_result(
    *,
    year: int,
    draw_no: int,
    baseline: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    return {
        "step": STEP,
        "name": NAME,
        "operation_id": uuid.uuid4().hex[:12],
        "started_at_utc": utc_now(),
        "finished_at_utc": None,
        "year": int(year),
        "draw_no": int(draw_no),
        "repo_root": str(repo_root),
        "branch": baseline.get("branch", ""),
        "remote_name": baseline.get("remote_name", REMOTE_NAME),
        "remote_url": baseline.get("remote_url", ""),
        "baseline_status": baseline.get("status"),
        "baseline_local_head": baseline.get("local_head", ""),
        "baseline_changed_paths": baseline.get("changed_paths", []),
        "baseline_unrelated_paths": baseline.get("unrelated_paths", []),
        "baseline_sensitive_paths": baseline.get("sensitive_paths", []),
        "candidate_files": [],
        "staged_files": [],
        "excluded_changed_files": [],
        "sensitive_excluded_files": [],
        "local_commit_sha": "",
        "remote_commit_sha": "",
        "remote_confirmed": False,
        "heavy_ml_retraining_performed": False,
        "steps": [],
    }


def _audit_directory(repo_root: Path) -> Path:
    return repo_root / "reports" / "runtime" / "v143_2_git_sync"


def _write_runtime_audit(result: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    audit_dir = _audit_directory(repo_root)
    audit_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"{timestamp}_draw_{result.get('year', 'unknown')}_{result.get('draw_no', 'unknown')}_{result.get('operation_id', 'audit')}"
    json_path = audit_dir / f"{stem}.json"
    md_path = audit_dir / f"{stem}.md"
    latest_path = audit_dir / "latest.json"

    relative_json = json_path.relative_to(repo_root).as_posix()
    relative_md = md_path.relative_to(repo_root).as_posix()
    result["audit_json_path"] = relative_json
    result["audit_summary_path"] = relative_md

    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    json_path.write_text(encoded, encoding="utf-8")
    latest_path.write_text(encoded, encoding="utf-8")

    lines = [
        "# Step 143.2 — Official Draw → GitHub Sync Audit",
        "",
        f"- Status: **{result.get('status', 'unknown')}**",
        f"- Message: {result.get('message_bg', '')}",
        f"- Draw: `{result.get('year', '—')}-{result.get('draw_no', '—')}`",
        f"- Branch: `{result.get('branch') or '—'}`",
        f"- Local commit: `{result.get('local_commit_sha') or '—'}`",
        f"- Remote commit: `{result.get('remote_commit_sha') or '—'}`",
        f"- Remote confirmed: **{'Yes' if result.get('remote_confirmed') else 'No'}**",
        "",
        "## Included files",
    ]
    included = result.get("staged_files") or result.get("candidate_files") or []
    lines.extend([f"- `{path}`" for path in included] or ["- None"])
    lines.extend(["", "## Excluded local files"])
    excluded = result.get("excluded_changed_files") or []
    lines.extend([f"- `{path}`" for path in excluded] or ["- None"])
    lines.extend([
        "",
        "The runtime audit is local evidence and is intentionally excluded from Git commits.",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def _finish(
    result: dict[str, Any],
    *,
    status: str,
    repo_root: Path,
    ok: bool = False,
) -> dict[str, Any]:
    result["status"] = status
    result["ok"] = bool(ok)
    result["message_bg"] = STATUS_MESSAGES_BG.get(status, status)
    result["finished_at_utc"] = utc_now()
    return _write_runtime_audit(result, repo_root)


def _verify_local_against_remote(repo_root: Path, branch: str) -> tuple[str, str, bool, dict[str, Any]]:
    local_sha = _current_head(repo_root)
    remote = _remote_head(repo_root, branch)
    remote_sha = str(remote.get("sha") or "")
    return local_sha, remote_sha, bool(local_sha and remote_sha and local_sha == remote_sha), remote


def synchronize_official_draw_outputs(
    *,
    year: int,
    draw_no: int,
    baseline: dict[str, Any] | None = None,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    """Commit, push and remotely confirm only the approved draw-output scope.

    The baseline must be captured before the draw workflow writes files. Existing
    staged files or pre-existing changes inside the sync scope block the operation.
    Other unstaged local files remain excluded from the commit and are reported.
    """

    repo_root = Path(repo_root).resolve()
    baseline = baseline or capture_git_snapshot(repo_root)
    result = _base_result(year=year, draw_no=draw_no, baseline=baseline, repo_root=repo_root)

    if not baseline.get("can_sync"):
        return _finish(result, status=str(baseline.get("status") or "not_git_repo"), repo_root=repo_root)

    branch = str(baseline.get("branch") or "").strip()
    current_entries, status_details = _worktree_entries(repo_root)
    result["steps"].append({"name": "git status before staging", **status_details})

    current_staged = _staged_paths(current_entries)
    if current_staged:
        result["unexpected_staged_files"] = current_staged
        return _finish(result, status="preexisting_staged_changes", repo_root=repo_root)

    changed_paths = sorted({entry["path"] for entry in current_entries})
    candidates = sorted(path for path in changed_paths if _is_sync_scope(path))
    excluded = sorted(path for path in changed_paths if path not in set(candidates))
    sensitive = sorted(path for path in excluded if _is_sensitive(path))
    result["candidate_files"] = candidates
    result["excluded_changed_files"] = excluded
    result["sensitive_excluded_files"] = sensitive

    if not candidates:
        local_sha, remote_sha, confirmed, remote_details = _verify_local_against_remote(repo_root, branch)
        result["steps"].append({"name": "remote confirmation", **remote_details.get("details", {})})
        result["local_commit_sha"] = local_sha
        result["remote_commit_sha"] = remote_sha
        result["remote_confirmed"] = confirmed
        status = "nothing_to_commit_remote_confirmed" if confirmed else "remote_confirmation_failed"
        return _finish(result, status=status, repo_root=repo_root, ok=confirmed)

    add_targets = [*SYNC_EXACT_PATHS, "models", "reports"]
    add_result = _run_git(["add", "--", *add_targets], repo_root=repo_root, timeout_seconds=180)
    result["steps"].append({"name": "git add approved scope", **add_result})
    if not add_result["ok"]:
        return _finish(result, status="git_add_failed", repo_root=repo_root)

    staged_result = _run_git(["diff", "--cached", "--name-only", "-z"], repo_root=repo_root, timeout_seconds=60)
    result["steps"].append({"name": "inspect staged files", **staged_result})
    staged_files = sorted(
        _normalise_path(item)
        for item in str(staged_result.get("stdout") or "").split("\0")
        if _normalise_path(item)
    )
    result["staged_files"] = staged_files

    unsafe_staged = sorted(path for path in staged_files if not _is_sync_scope(path))
    if unsafe_staged:
        result["unsafe_staged_files"] = unsafe_staged
        reset_result = _run_git(["reset", "--mixed", "HEAD", "--"], repo_root=repo_root, timeout_seconds=60)
        result["steps"].append({"name": "unstage unsafe commit", **reset_result})
        return _finish(result, status="unsafe_staged_files", repo_root=repo_root)

    if not staged_files:
        return _finish(result, status="nothing_staged", repo_root=repo_root)

    commit_message = f"Update official draw {year}-{draw_no} and validate GitHub sync"
    commit_result = _run_git(["commit", "-m", commit_message], repo_root=repo_root, timeout_seconds=180)
    result["steps"].append({"name": "git commit", **commit_result})
    if not commit_result["ok"]:
        return _finish(result, status="commit_failed", repo_root=repo_root)

    local_sha = _current_head(repo_root)
    result["local_commit_sha"] = local_sha

    push_result = _run_git(
        ["push", REMOTE_NAME, f"HEAD:refs/heads/{branch}"],
        repo_root=repo_root,
        timeout_seconds=300,
    )
    result["steps"].append({"name": "git push", **push_result})
    if not push_result["ok"]:
        return _finish(result, status="local_commit_pending_push", repo_root=repo_root)

    local_sha, remote_sha, confirmed, remote_details = _verify_local_against_remote(repo_root, branch)
    result["steps"].append({"name": "remote confirmation", **remote_details.get("details", {})})
    result["local_commit_sha"] = local_sha
    result["remote_commit_sha"] = remote_sha
    result["remote_confirmed"] = confirmed

    after_entries, after_details = _worktree_entries(repo_root)
    result["steps"].append({"name": "git status after sync", **after_details})
    result["remaining_changed_files"] = sorted({entry["path"] for entry in after_entries})

    if not remote_details.get("ok"):
        return _finish(result, status="remote_confirmation_failed", repo_root=repo_root)
    if not confirmed:
        return _finish(result, status="remote_mismatch", repo_root=repo_root)
    return _finish(result, status="remote_confirmed", repo_root=repo_root, ok=True)


def retry_push_and_confirm(repo_root: Path = ROOT) -> dict[str, Any]:
    """Retry a pending push for the current HEAD without creating another commit."""

    repo_root = Path(repo_root).resolve()
    snapshot = capture_git_snapshot(repo_root)
    latest = load_latest_runtime_audit(repo_root)
    year = int(latest.get("year") or datetime.now().year)
    draw_no = int(latest.get("draw_no") or 0)
    result = _base_result(year=year, draw_no=draw_no, baseline=snapshot, repo_root=repo_root)
    result["operation_id"] = uuid.uuid4().hex[:12]
    result["retry_of_operation_id"] = latest.get("operation_id")

    retryable_statuses = {"local_commit_pending_push", "remote_confirmation_failed", "remote_mismatch"}
    if not latest or latest.get("status") not in retryable_statuses:
        return _finish(result, status="no_pending_push_audit", repo_root=repo_root)
    if snapshot.get("staged_paths"):
        return _finish(result, status="preexisting_staged_changes", repo_root=repo_root)
    branch = str(snapshot.get("branch") or "").strip()
    if not branch:
        return _finish(result, status="detached_head", repo_root=repo_root)
    if snapshot.get("status") == "origin_missing":
        return _finish(result, status="origin_missing", repo_root=repo_root)
    if str(latest.get("branch") or "").strip() != branch:
        return _finish(result, status="retry_branch_mismatch", repo_root=repo_root)

    current_head = _current_head(repo_root)
    if not current_head or current_head != str(latest.get("local_commit_sha") or "").strip():
        result["local_commit_sha"] = current_head
        return _finish(result, status="retry_head_mismatch", repo_root=repo_root)

    result["local_commit_sha"] = current_head
    push_result = _run_git(
        ["push", REMOTE_NAME, f"HEAD:refs/heads/{branch}"],
        repo_root=repo_root,
        timeout_seconds=300,
    )
    result["steps"].append({"name": "retry git push", **push_result})
    if not push_result["ok"]:
        return _finish(result, status="local_commit_pending_push", repo_root=repo_root)

    local_sha, remote_sha, confirmed, remote_details = _verify_local_against_remote(repo_root, branch)
    result["steps"].append({"name": "remote confirmation", **remote_details.get("details", {})})
    result["local_commit_sha"] = local_sha
    result["remote_commit_sha"] = remote_sha
    result["remote_confirmed"] = confirmed
    if not remote_details.get("ok"):
        return _finish(result, status="remote_confirmation_failed", repo_root=repo_root)
    if not confirmed:
        return _finish(result, status="remote_mismatch", repo_root=repo_root)
    return _finish(result, status="remote_confirmed", repo_root=repo_root, ok=True)


def load_latest_runtime_audit(repo_root: Path = ROOT) -> dict[str, Any]:
    path = _audit_directory(Path(repo_root).resolve()) / "latest.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}

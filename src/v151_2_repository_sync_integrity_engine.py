from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "models/v151_2_repository_sync_integrity_policy.json"
STATUS_PATH = ROOT / "models/v151_2_repository_sync_integrity_status.json"
SUMMARY_JSON_PATH = ROOT / "reports/v151_2_repository_sync_integrity_summary.json"
SUMMARY_MD_PATH = ROOT / "reports/v151_2_repository_sync_integrity_summary.md"
REPORT_PATH = ROOT / "reports/STEP_151_2_REPOSITORY_SYNCHRONIZATION_UI_RUNTIME_REPAIRS_AND_FRESH_CLONE_INTEGRITY_CLOSURE.md"

CHECKPOINT = "Step 151.2"
CHECKPOINT_TITLE = "Repository Synchronization, UI Runtime Repairs & Fresh-Clone Integrity Closure"
VOLATILE_TRACKED_PATHS = (
    "models/v109/v109_sqlite_played_tickets_journal_model.json",
    "models/v123_bst_official_draw_detection_status.json",
    "reports/v109_sqlite_played_tickets_journal_checklist.csv",
    "reports/v109_sqlite_played_tickets_journal_summary.json",
    "reports/v109_sqlite_played_tickets_journal_summary.md",
    "reports/v123_bst_official_draw_detection_report.json",
    "reports/v123_bst_official_draw_detection_summary.md",
)
REQUIRED_FILES = (
    ".gitattributes",
    "src/v151_2_repository_sync_integrity_engine.py",
    "scripts/verify_step_151_2.py",
    "tools/finalize_step_151_2_release.py",
    "tools/apply_step_151_2_repository_sync.ps1",
    "reports/STEP_151_2_REPOSITORY_SYNCHRONIZATION_UI_RUNTIME_REPAIRS_AND_FRESH_CLONE_INTEGRITY_CLOSURE.md",
)
GENERATED_FILES = (
    "models/v151_2_repository_sync_integrity_policy.json",
    "models/v151_2_repository_sync_integrity_status.json",
    "reports/v151_2_repository_sync_integrity_summary.json",
    "reports/v151_2_repository_sync_integrity_summary.md",
)


def _signature(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _run_git(*args: str) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=60,
        )
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    output = ((completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")).strip()
    return completed.returncode == 0, output


def git_sync_state() -> dict[str, Any]:
    ok_branch, branch = _run_git("branch", "--show-current")
    ok_head, head = _run_git("rev-parse", "HEAD")
    ok_upstream, upstream = _run_git("rev-parse", "--abbrev-ref", "@{upstream}")
    upstream_sha = ""
    ahead = None
    behind = None
    if ok_upstream:
        ok_upstream_sha, upstream_sha = _run_git("rev-parse", "@{upstream}")
        if not ok_upstream_sha:
            upstream_sha = ""
        ok_counts, counts = _run_git("rev-list", "--left-right", "--count", "HEAD...@{upstream}")
        if ok_counts:
            parts = counts.split()
            if len(parts) == 2:
                ahead, behind = int(parts[0]), int(parts[1])
    ok_status, porcelain = _run_git("status", "--porcelain=v1")
    return {
        "git_available": ok_branch and ok_head and ok_status,
        "branch": branch if ok_branch else "",
        "head": head if ok_head else "",
        "upstream": upstream if ok_upstream else "",
        "upstream_sha": upstream_sha,
        "ahead": ahead,
        "behind": behind,
        "working_tree_clean": ok_status and not porcelain,
        "working_tree_changes": porcelain.splitlines() if porcelain else [],
        "on_main": branch == "main",
        "not_behind_upstream": behind in {0, None},
        "fully_synced": bool(ok_upstream and ahead == 0 and behind == 0 and ok_status and not porcelain),
    }


def line_ending_state() -> dict[str, Any]:
    ok, output = _run_git("ls-files", "--eol")
    rows: list[dict[str, str]] = []
    index_crlf: list[str] = []
    worktree_crlf: list[str] = []
    if ok:
        for raw in output.splitlines():
            if "\t" not in raw:
                continue
            meta, path = raw.split("\t", 1)
            parts = meta.split()
            index_eol = parts[0] if len(parts) > 0 else ""
            worktree_eol = parts[1] if len(parts) > 1 else ""
            attr = " ".join(parts[2:])
            rows.append({"path": path, "index_eol": index_eol, "worktree_eol": worktree_eol, "attr": attr})
            if index_eol == "i/crlf" and "text" in attr:
                index_crlf.append(path)
            if worktree_eol == "w/crlf" and "text" in attr:
                worktree_crlf.append(path)
    return {
        "git_eol_read_ok": ok,
        "tracked_files": len(rows),
        "index_crlf_text_files": index_crlf,
        "worktree_crlf_text_files": worktree_crlf,
        "canonical_index_lf": ok and not index_crlf,
        "canonical_worktree_lf": ok and not worktree_crlf,
    }


def _extract_training_text_decoder() -> tuple[bool, list[str]]:
    failures: list[str] = []
    path = ROOT / "src/training_center_section.py"
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        selected: list[ast.stmt] = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "_ESCAPED_UNICODE_RE" for target in node.targets):
                selected.append(node)
            if isinstance(node, ast.FunctionDef) and node.name == "T":
                selected.append(node)
        namespace: dict[str, Any] = {"re": re}
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
        decoder = namespace["T"]
        if decoder(r"\u041f\u0440\u043e\u0431\u0430") != "Проба":
            failures.append("escaped_unicode_not_decoded")
        if decoder("Покритие на фиша") != "Покритие на фиша":
            failures.append("real_unicode_not_preserved")
    except Exception as exc:
        failures.append(f"decoder_test:{type(exc).__name__}:{exc}")
    return not failures, failures


def ui_repair_state() -> dict[str, Any]:
    failures: list[str] = []
    v94 = (ROOT / "src/v94_active_budget_plan_tracker_section.py").read_text(encoding="utf-8-sig")
    training = (ROOT / "src/training_center_section.py").read_text(encoding="utf-8-sig")
    polish = (ROOT / "src/v150_global_ui_polish.py").read_text(encoding="utf-8-sig")

    key_checks = {
        "real_result_download_key": 'download_key="v94_real_result_csv"' in v94,
        "demo_result_download_key": 'download_key="v94_demo_result_csv"' in v94,
        "download_button_uses_key": "key=download_key" in v94,
        "training_unicode_guard": "_ESCAPED_UNICODE_RE" in training and "UnicodeEncodeError" in training,
        "training_subprocess_utf8": 'PYTHONIOENCODING"] = "utf-8"' in training,
        "numeric_selectbox_returns_text": "return str(rendered)" in polish,
    }
    failures.extend(key for key, passed in key_checks.items() if not passed)
    decoder_ok, decoder_failures = _extract_training_text_decoder()
    failures.extend(decoder_failures)

    try:
        from src.v150_ui_language_integrity_engine import run_ui_language_integrity_audit

        integrity = run_ui_language_integrity_audit(write_outputs=False)
    except Exception as exc:
        integrity = {"ok": False, "failures": [f"{type(exc).__name__}:{exc}"]}
    if not integrity.get("ok"):
        failures.extend(f"ui_integrity:{item}" for item in integrity.get("failures", []))

    return {
        "ok": not failures,
        "checks": key_checks,
        "training_decoder_runtime_test": decoder_ok,
        "ui_language_integrity": integrity,
        "failures": failures,
    }


def policy_payload() -> dict[str, Any]:
    return {
        "step": "151.2",
        "name": CHECKPOINT_TITLE,
        "repository_goal": "Desktop working tree, Git index, fresh clone and origin/main must reproduce the same tracked project bytes.",
        "line_endings": {
            "tracked_text": "LF",
            "git_core_autocrlf": False,
            "gitattributes": "* text=auto eol=lf",
        },
        "ui_repairs": {
            "numeric_selectbox_formatter": "always_returns_string",
            "active_plan_result_downloads": "unique_streamlit_keys",
            "training_center_unicode": "decode_literal_escapes_only",
            "subprocess_output": "forced_utf8_for_python_children",
        },
        "step148_integrity": "immutable code from policy hashes; mutable ledger and active lock validated dynamically",
        "volatile_tracked_paths_restored_before_commit": list(VOLATILE_TRACKED_PATHS),
        "fresh_clone_required": True,
        "personal_journal_database": "local_only_not_tracked",
        "production_scoring_changed": False,
        "historical_draw_data_changed": False,
    }


def audit_repository_sync() -> dict[str, Any]:
    eol = line_ending_state()
    ui = ui_repair_state()
    git = git_sync_state()
    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).is_file()]
    checks = {
        "required_files_present": not missing,
        "git_available": bool(git.get("git_available")),
        "branch_main": bool(git.get("on_main")),
        "not_behind_upstream": bool(git.get("not_behind_upstream")),
        "canonical_index_lf": bool(eol.get("canonical_index_lf")),
        "canonical_worktree_lf": bool(eol.get("canonical_worktree_lf")),
        "ui_runtime_repairs": bool(ui.get("ok")),
    }
    core = {
        "step": "151.2",
        "name": CHECKPOINT_TITLE,
        "missing_files": missing,
        "checks": checks,
        "git": git,
        "line_endings": eol,
        "ui_repairs": ui,
        "fresh_clone_requirement": "run scripts/verify_step_151_2.py --require-synced in a separate clone",
        "external_github_push_asserted": False,
        "production_scoring_changed": False,
        "historical_draw_data_changed": False,
        "personal_journal_used": False,
    }
    stable = dict(core)
    stable["git"] = {key: value for key, value in git.items() if key not in {"working_tree_changes", "working_tree_clean"}}
    core["result_signature_sha256"] = _signature(stable)
    core["ok"] = all(checks.values())
    core["checked_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return core


def write_artifacts() -> dict[str, Any]:
    policy = policy_payload()
    POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    POLICY_PATH.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    result = audit_repository_sync()
    # Persist a compact pre-commit snapshot. The live verifier remains the authority for
    # clean-tree and HEAD/upstream equality after the commit/push operation.
    persisted = json.loads(json.dumps(result, ensure_ascii=False))
    persisted_git = persisted.get("git", {})
    changes = persisted_git.pop("working_tree_changes", [])
    persisted_git.pop("head", None)
    persisted_git["baseline_upstream_sha"] = persisted_git.pop("upstream_sha", "")
    persisted_git["working_tree_change_count_at_build"] = len(changes)
    persisted_git["working_tree_state_context"] = "pre_commit_release_build"
    persisted_git["post_push_sync_must_be_verified_live"] = True
    STATUS_PATH.write_text(json.dumps(persisted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    SUMMARY_JSON_PATH.write_text(
        json.dumps({"report_type": "step151_2_repository_sync_integrity", "summary": persisted}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    eol = result["line_endings"]
    git = result["git"]
    SUMMARY_MD_PATH.write_text(
        "# Step 151.2 — Repository Sync Integrity\n\n"
        f"- Status: **{'OK' if result['ok'] else 'CHECK REQUIRED'}**\n"
        f"- Branch: `{git.get('branch') or '-'}`\n"
        f"- Ahead / behind upstream: `{git.get('ahead')}` / `{git.get('behind')}`\n"
        f"- Canonical LF in index: **{'Yes' if eol.get('canonical_index_lf') else 'No'}**\n"
        f"- Canonical LF in working tree: **{'Yes' if eol.get('canonical_worktree_lf') else 'No'}**\n"
        f"- UI runtime repairs: **{'OK' if result['ui_repairs'].get('ok') else 'CHECK REQUIRED'}**\n"
        f"- Active Step 148 lock: `{result['ui_repairs'].get('ui_language_integrity', {}).get('active_lock_id')}`\n"
        f"- Expected draw: `{result['ui_repairs'].get('ui_language_integrity', {}).get('active_expected_draw_key')}`\n"
        "- External GitHub push: **not asserted by the release builder**\n",
        encoding="utf-8",
        newline="\n",
    )
    return result

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = "Step 151.5"
CHECKPOINT_TITLE = "Full Post-Synchronization Integrity Audit, Runtime Cleanup and Clean Git Checkpoint"

POLICY_PATH = ROOT / "models/v151_5_post_sync_integrity_policy.json"
STATUS_PATH = ROOT / "models/v151_5_post_sync_integrity_status.json"
SUMMARY_JSON_PATH = ROOT / "reports/v151_5_post_sync_integrity_summary.json"
SUMMARY_MD_PATH = ROOT / "reports/v151_5_post_sync_integrity_summary.md"
REPORT_PATH = ROOT / "reports/STEP_151_5_FULL_POST_SYNCHRONIZATION_INTEGRITY_AUDIT_RUNTIME_CLEANUP_AND_CLEAN_GIT_CHECKPOINT.md"

EXPECTED_HEAVY_MODEL_HASHES = {
    "models/v41/v41_sgd_number_model.joblib": "f2f4b60d6dbaa29378ffab0e455ca3fd19e50374bf3d0b2c7dde632b512d8786",
    "models/v45/v45_number_score_model.joblib": "24ac07eb57f7828666daa338410f85b481be8ff806f98143dc71d6a24911eab8",
}

VOLATILE_TRACKED_PATHS = (
    "models/v123_bst_official_draw_detection_status.json",
    "models/v125_unified_downstream_refresh_status.json",
    "models/v126_startup_automation_status.json",
    "models/v131_production_operations_dashboard_status.json",
    "reports/v123_bst_official_draw_detection_report.json",
    "reports/v123_bst_official_draw_detection_summary.md",
    "reports/v125_unified_downstream_refresh_audit.jsonl",
    "reports/v125_unified_downstream_refresh_report.json",
    "reports/v125_unified_downstream_refresh_summary.md",
    "reports/v126_startup_automation_audit.jsonl",
    "reports/v126_startup_automation_report.json",
    "reports/v126_startup_automation_summary.md",
    "reports/v131_production_operations_dashboard_report.json",
    "reports/v131_production_operations_dashboard_summary.md",
)

DISPOSABLE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".ipynb_checkpoints", "_clean_zip_diagnostics"}
DISPOSABLE_SUFFIXES = {".pyc", ".pyo", ".tmp", ".log", ".bak", ".backup", ".sqlite-journal", ".db-journal"}

TEXT_FILE_SUFFIXES = {
    ".cfg", ".css", ".csv", ".html", ".ini", ".js", ".json", ".jsonl",
    ".md", ".ps1", ".py", ".r", ".rst", ".sql", ".toml", ".ts", ".tsx",
    ".txt", ".xml", ".yaml", ".yml",
}
TEXT_FILE_NAMES = {".gitattributes", ".gitignore", "Dockerfile", "Makefile", "README"}

EXACT_ALLOWED_CHANGED_PATHS = {
    ".gitattributes",
    "README.md",
    "docs/STEP_HISTORY.md",
    "release-manifest.json",
    "data/historical_draws.csv",
    "data/prize_winner_history.csv",
    "data/prospective_forward_test_ledger.jsonl",
    "data/v40_normalized_draw_events.csv",
    "data/v41_canonical_draw_events.csv",
    "src/bst_official_sync_engine.py",
    "src/post_bst_model_data_refresh_engine.py",
    "src/v111_prize_winner_history_engine.py",
    "src/v123_bst_official_draw_detection_engine.py",
    "src/v124_safe_official_draw_ingestion_engine.py",
    "src/v131_production_operations_dashboard_engine.py",
    "src/v151_4_controlled_prize_history_data_sync_engine.py",
    "src/v151_5_post_sync_integrity_cleanup_engine.py",
    "scripts/run_step_151_4_controlled_sync.py",
    "scripts/verify_step_151_3.py",
    "scripts/verify_step_151_4.py",
    "scripts/verify_step_151_5.py",
    "tools/finalize_step_151_5_release.py",
    "models/v151_3_prize_history_integrity_policy.json",
    "models/v151_3_prize_history_integrity_status.json",
    "models/v151_4_controlled_data_sync_policy.json",
    "models/v151_4_controlled_data_sync_status.json",
    "models/v151_5_post_sync_integrity_policy.json",
    "models/v151_5_post_sync_integrity_status.json",
    "reports/STEP_151_3_PRIZE_HISTORY_INTEGRITY_CAPTCHA_DIAGNOSTICS_AND_FRESHNESS_REPAIR.md",
    "reports/STEP_151_4_CONTROLLED_PRIZE_HISTORY_54_55_DATA_SYNC_AND_STEP148_SETTLEMENT.md",
    "reports/STEP_151_5_FULL_POST_SYNCHRONIZATION_INTEGRITY_AUDIT_RUNTIME_CLEANUP_AND_CLEAN_GIT_CHECKPOINT.md",
    "reports/v151_3_prize_history_integrity_summary.json",
    "reports/v151_3_prize_history_integrity_summary.md",
    "reports/v151_4_controlled_data_sync_audit.jsonl",
    "reports/v151_4_controlled_data_sync_report.json",
    "reports/v151_4_controlled_data_sync_summary.md",
    "reports/v151_5_post_sync_integrity_summary.json",
    "reports/v151_5_post_sync_integrity_summary.md",
    "CLEAN_ZIP_MANIFEST_STEP151_5.md",
    "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP151_5.md",
}

ALLOWED_CHANGED_PREFIXES = (
    "models/v111/",
    "models/v115",
    "models/v117/",
    "models/v118/",
    "models/v120_",
    "models/v121_",
    "models/v122_",
    "models/v142_",
    "models/v143_3_",
    "models/v148_",
    "reports/r/",
    "reports/v111_",
    "reports/v115_",
    "reports/v117_",
    "reports/v118_",
    "reports/v120_",
    "reports/v121_",
    "reports/v122_",
    "reports/v142_",
    "reports/v143_3_",
    "reports/v148_",
    "reports/forward_tests/v148/LOCK-148-",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _pair(row: dict[str, Any]) -> tuple[int, int]:
    return int(row.get("draw_year") or row.get("year") or 0), int(row.get("draw_number") or row.get("draw_no") or 0)


def _numbers(row: dict[str, Any]) -> list[int]:
    return [int(row.get(f"n{i}") or 0) for i in range(1, 7)]


def _run_git(*args: str) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=90,
        )
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    output = ((completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")).strip()
    return completed.returncode == 0, output


def changed_paths() -> list[str]:
    paths: set[str] = set()
    for args in (("diff", "--name-only"), ("diff", "--cached", "--name-only"), ("ls-files", "--others", "--exclude-standard")):
        ok, output = _run_git(*args)
        if ok:
            paths.update(line.strip().replace("\\", "/") for line in output.splitlines() if line.strip() and not line.lstrip().startswith("warning:"))
    return sorted(paths)


def _allowed_change(path: str, *, allow_volatile: bool) -> bool:
    if path in EXACT_ALLOWED_CHANGED_PATHS:
        return True
    if any(path.startswith(prefix) for prefix in ALLOWED_CHANGED_PREFIXES):
        return True
    if allow_volatile and path in VOLATILE_TRACKED_PATHS:
        return True
    if path.startswith("CLEAN_ZIP_MANIFEST_STEP151_2_2") or path.startswith("FULL_CLEAN_CHECKPOINT_MANIFEST_STEP151_2_2"):
        return True
    return False


def audit_git_changes(*, allow_volatile: bool) -> dict[str, Any]:
    ok_branch, branch = _run_git("branch", "--show-current")
    ok_head, head = _run_git("rev-parse", "HEAD")
    ok_upstream, upstream = _run_git("rev-parse", "--abbrev-ref", "@{upstream}")
    ahead = behind = None
    if ok_upstream:
        ok_counts, counts = _run_git("rev-list", "--left-right", "--count", "HEAD...@{upstream}")
        if ok_counts and len(counts.split()) == 2:
            ahead, behind = map(int, counts.split())
    paths = changed_paths()
    unexpected = [path for path in paths if not _allowed_change(path, allow_volatile=allow_volatile)]
    volatile_dirty = [path for path in paths if path in VOLATILE_TRACKED_PATHS]
    return {
        "git_available": ok_branch and ok_head,
        "branch": branch if ok_branch else "",
        "head": head if ok_head else "",
        "upstream": upstream if ok_upstream else "",
        "ahead": ahead,
        "behind": behind,
        "changed_paths": paths,
        "changed_path_count": len(paths),
        "unexpected_paths": unexpected,
        "volatile_dirty_paths": volatile_dirty,
        "on_main": branch == "main",
        "not_behind": behind in {0, None},
        "working_tree_clean": not paths,
    }


def audit_line_endings() -> dict[str, Any]:
    ok, output = _run_git("ls-files", "--eol")
    index_crlf: list[str] = []
    worktree_crlf: list[str] = []
    if ok:
        for raw in output.splitlines():
            if "\t" not in raw:
                continue
            meta, path = raw.split("\t", 1)
            parts = meta.split()
            index_eol = parts[0] if parts else ""
            worktree_eol = parts[1] if len(parts) > 1 else ""
            attr = " ".join(parts[2:])
            if index_eol == "i/crlf" and "text" in attr:
                index_crlf.append(path)
            if worktree_eol == "w/crlf" and "text" in attr:
                worktree_crlf.append(path)
    return {
        "ok": ok and not index_crlf and not worktree_crlf,
        "git_eol_read_ok": ok,
        "index_crlf_text_files": index_crlf,
        "worktree_crlf_text_files": worktree_crlf,
    }


def audit_data_integrity() -> dict[str, Any]:
    from src.post_bst_model_data_refresh_engine import get_sync_status
    from src.v122_unified_official_draw_freshness_engine import build_freshness_report

    paths = {
        "prize": ROOT / "data/prize_winner_history.csv",
        "mirror": ROOT / "data/user_journal_exports/prize_winner_history.csv",
        "historical": ROOT / "data/historical_draws.csv",
        "v40": ROOT / "data/v40_normalized_draw_events.csv",
        "v41": ROOT / "data/v41_canonical_draw_events.csv",
        "db": ROOT / "data/user_journal.db",
    }
    failures: list[str] = []
    for key, path in paths.items():
        if not path.is_file():
            failures.append(f"missing:{key}:{path.relative_to(ROOT)}")
    if failures:
        return {"ok": False, "failures": failures}

    rows = {key: _read_csv(path) for key, path in paths.items() if key not in {"db"}}
    expected_counts = {"prize": 32, "mirror": 32, "historical": 10065, "v40": 10065, "v41": 10065}
    for key, expected in expected_counts.items():
        if len(rows[key]) != expected:
            failures.append(f"row_count:{key}:{len(rows[key])}:expected={expected}")
    if _sha256(paths["prize"]) != _sha256(paths["mirror"]):
        failures.append("prize_mirror_hash_mismatch")

    for key in ("prize", "historical", "v40", "v41"):
        latest = max(rows[key], key=_pair)
        if _pair(latest) != (2026, 55) or _numbers(latest) != [5, 10, 17, 20, 42, 47]:
            failures.append(f"latest:{key}:{_pair(latest)}:{_numbers(latest)}")
        if key == "prize":
            keys = [_pair(row) for row in rows[key]]
        else:
            keys = [(_pair(row), int(row.get("drawing_no") or row.get("draw_position") or 1)) for row in rows[key]]
        if len(keys) != len(set(keys)):
            failures.append(f"duplicates:{key}")

    connection = sqlite3.connect(paths["db"])
    try:
        db_count = int(connection.execute("SELECT COUNT(*) FROM prize_winner_history").fetchone()[0])
    finally:
        connection.close()
    if db_count != 32:
        failures.append(f"sqlite_count:{db_count}")

    sync = get_sync_status()
    if sync.get("status") != "MODEL_DATA_SYNCED" or set((sync.get("layer_status") or {}).values()) != {"synced"}:
        failures.append(f"step120:{sync.get('status')}:{sync.get('layer_status')}")
    freshness = build_freshness_report(write_outputs=False)
    if freshness.get("overall_status") != "synced" or int(freshness.get("blocking_out_of_sync_count", -1)) != 0:
        failures.append(f"step122:{freshness.get('overall_status')}:{freshness.get('blocking_out_of_sync_count')}")

    r_rows = {row.get("metric", ""): row.get("value", "") for row in _read_csv(ROOT / "reports/r/r_data_audit.csv")}
    if r_rows.get("rows") != "10065" or r_rows.get("latest_draw_number") != "55" or r_rows.get("latest_numbers") != "5, 10, 17, 20, 42, 47":
        failures.append(f"r_layer:{r_rows}")

    zero = _load_json(ROOT / "models/v143_3_downstream_zero_blocker_status.json")
    after = zero.get("after") or zero.get("final_freshness") or {}
    if zero.get("status") != "completed":
        failures.append(f"step143_3_status:{zero.get('status')}")
    if after and (after.get("overall_status") != "synced" or int(after.get("blocking_out_of_sync_count", -1)) != 0):
        failures.append("step143_3_after_not_synced")

    return {
        "ok": not failures,
        "failures": failures,
        "counts": expected_counts,
        "latest_draw": "2026-55",
        "latest_numbers": [5, 10, 17, 20, 42, 47],
        "step120_status": sync.get("status"),
        "freshness_status": freshness.get("overall_status"),
        "freshness_blockers": freshness.get("blocking_out_of_sync_count"),
        "r_latest_draw": r_rows.get("latest_draw_number"),
    }


def audit_step148() -> dict[str, Any]:
    from src.v148_prospective_forward_test_engine import active_lock, load_ledger, verify_ledger

    failures: list[str] = []
    events = load_ledger()
    chain = verify_ledger(events)
    lock = active_lock(events)
    if not chain.get("ok"):
        failures.extend(f"ledger:{item}" for item in chain.get("failures", []))
    if int(chain.get("settled_count", -1)) != 2:
        failures.append(f"settled_count:{chain.get('settled_count')}")
    settlements_55 = [
        event for event in events
        if event.get("event_type") == "forecast_settled"
        and ((event.get("settlement") or {}).get("actual_draw_key") == "2026-55")
    ]
    if len(settlements_55) != 1:
        failures.append(f"settlement_55_count:{len(settlements_55)}")
    if not lock or lock.get("expected_draw_key") != "2026-56":
        failures.append(f"active_lock:{(lock or {}).get('expected_draw_key')}")
    status = _load_json(ROOT / "models/v148_prospective_forward_test_status.json")
    safety = {
        "production_promotion_approved": status.get("production_promotion_approved"),
        "automatic_production_promotion": status.get("automatic_production_promotion"),
        "production_integration_enabled": status.get("production_integration_enabled"),
        "real_ticket_generation_enabled": status.get("real_ticket_generation_enabled"),
    }
    if any(bool(value) for value in safety.values()):
        failures.append(f"step148_safety:{safety}")
    return {
        "ok": not failures,
        "failures": failures,
        "ledger_event_count": chain.get("event_count"),
        "settled_count": chain.get("settled_count"),
        "active_lock_id": (lock or {}).get("lock_id"),
        "active_expected_draw_key": (lock or {}).get("expected_draw_key"),
        "safety": safety,
    }


def audit_heavy_models() -> dict[str, Any]:
    actual: dict[str, str] = {}
    failures: list[str] = []
    for rel, expected in EXPECTED_HEAVY_MODEL_HASHES.items():
        path = ROOT / rel
        if not path.is_file():
            failures.append(f"missing:{rel}")
            continue
        digest = _sha256(path)
        actual[rel] = digest
        if digest != expected:
            failures.append(f"hash:{rel}:{digest}:expected={expected}")
    return {"ok": not failures, "failures": failures, "hashes": actual}


def find_disposable_runtime_files() -> list[str]:
    found: list[str] = []
    for path in ROOT.rglob("*"):
        try:
            rel = path.relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if ".git/" in f"{rel}/" or ".venv/" in f"{rel}/" or "venv/" in f"{rel}/":
            continue
        if path.is_dir() and path.name in DISPOSABLE_DIR_NAMES:
            found.append(rel + "/")
        elif path.is_file() and path.suffix.lower() in DISPOSABLE_SUFFIXES:
            found.append(rel)
    return sorted(set(found))


def _looks_like_text_file(path: Path) -> bool:
    if path.name in TEXT_FILE_NAMES or path.name.startswith("README"):
        return True
    return path.suffix.lower() in TEXT_FILE_SUFFIXES


def _normalize_path_to_lf(path: Path) -> bool:
    if not path.is_file() or not _looks_like_text_file(path):
        return False
    data = path.read_bytes()
    if b"\x00" in data[:8192]:
        return False
    updated = data.replace(b"\r\n", b"\n")
    if updated == data:
        return False
    path.write_bytes(updated)
    return True


def normalize_tracked_text_line_endings() -> list[str]:
    """Normalize tracked and pending checkpoint text files to LF.

    `git ls-files --eol` omits untracked files. Step 151.4 generated several new
    report/status files before the Step 151.5 commit, so the original cleanup
    could miss their CRLF bytes until `git add` promoted them into the index.
    Include untracked, staged and modified paths explicitly to keep pre-stage
    and post-stage verification equivalent on Windows.
    """
    candidates: set[str] = set()
    ok, output = _run_git("ls-files", "--eol")
    if ok:
        for raw in output.splitlines():
            if "\t" not in raw:
                continue
            meta, rel = raw.split("\t", 1)
            parts = meta.split()
            worktree_eol = parts[1] if len(parts) > 1 else ""
            attr = " ".join(parts[2:])
            if worktree_eol in {"w/crlf", "w/mixed"} and "text" in attr:
                candidates.add(rel.replace("\\", "/"))

    # Include pending paths that may not yet be tracked. This is the Windows
    # staging gap fixed by Step 151.5.1.
    candidates.update(changed_paths())

    normalized: list[str] = []
    for rel in sorted(candidates):
        path = ROOT / rel
        if _normalize_path_to_lf(path):
            normalized.append(rel)
    return normalized


def clean_disposable_runtime_files() -> list[str]:
    removed: list[str] = []
    dirs = [path for path in ROOT.rglob("*") if path.is_dir() and path.name in DISPOSABLE_DIR_NAMES]
    for path in sorted(dirs, key=lambda item: len(item.parts), reverse=True):
        rel = path.relative_to(ROOT).as_posix() + "/"
        shutil.rmtree(path, ignore_errors=True)
        removed.append(rel)
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in DISPOSABLE_SUFFIXES:
            rel = path.relative_to(ROOT).as_posix()
            try:
                path.unlink()
                removed.append(rel)
            except OSError:
                pass
    return sorted(set(removed))


def restore_volatile_tracked_artifacts() -> dict[str, Any]:
    existing = [rel for rel in VOLATILE_TRACKED_PATHS if (ROOT / rel).exists()]
    ok, output = _run_git("restore", "--source=HEAD", "--worktree", "--", *VOLATILE_TRACKED_PATHS)
    return {"ok": ok, "restored": existing, "git_output": output}


def update_gitattributes() -> bool:
    path = ROOT / ".gitattributes"
    text = path.read_text(encoding="utf-8-sig")
    line = "reports/forward_tests/v148/LOCK-148-*.json text eol=lf"
    if line in text:
        return False
    if not text.endswith("\n"):
        text += "\n"
    text += "\n# All current and future Step 148 lock artifacts use exact LF bytes\n" + line + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def close_step151_3_status() -> None:
    path = ROOT / "models/v151_3_prize_history_integrity_status.json"
    data = _load_json(path)
    data.update({
        "status": "completed",
        "data_synchronization_performed": True,
        "synchronized_through_draw": "2026-55",
        "clean_checkpoint_created": True,
        "closed_by_step": "151.5",
    })
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def policy_payload() -> dict[str, Any]:
    return {
        "step": "151.5",
        "name": CHECKPOINT_TITLE,
        "expected_post_sync_state": {
            "prize_history_rows": 32,
            "dataset_rows": 10065,
            "latest_draw": "2026-55",
            "latest_numbers": [5, 10, 17, 20, 42, 47],
            "freshness_blockers": 0,
            "step148_settled_draws": 2,
            "step148_active_expected_draw": "2026-56",
        },
        "runtime_cleanup": {
            "restore_to_head": list(VOLATILE_TRACKED_PATHS),
            "remove_only_disposable_caches_and_temporary_files": True,
            "preserve_local_journal_and_exports": True,
            "preserve_forensic_backups_outside_project": True,
        },
        "heavy_model_hashes": EXPECTED_HEAVY_MODEL_HASHES,
        "git_checkpoint": {
            "branch": "main",
            "commit_is_explicit_operator_action": True,
            "push_is_explicit_operator_action": True,
            "required_final_state": "main...origin/main with no working-tree changes",
        },
        "production_scoring_changed": False,
        "heavy_model_retraining_performed": False,
        "personal_journal_tracked": False,
    }


def audit_post_sync_state(*, allow_volatile: bool = False, allow_line_ending_drift: bool = False) -> dict[str, Any]:
    data = audit_data_integrity()
    step148 = audit_step148()
    heavy = audit_heavy_models()
    git = audit_git_changes(allow_volatile=allow_volatile)
    eol = audit_line_endings()
    disposable = find_disposable_runtime_files()
    step151_4 = _load_json(ROOT / "models/v151_4_controlled_data_sync_status.json")
    failures: list[str] = []
    if not data.get("ok"):
        failures.extend(f"data:{item}" for item in data.get("failures", []))
    if not step148.get("ok"):
        failures.extend(f"step148:{item}" for item in step148.get("failures", []))
    if not heavy.get("ok"):
        failures.extend(f"heavy:{item}" for item in heavy.get("failures", []))
    if step151_4.get("status") != "completed":
        failures.append(f"step151_4:{step151_4.get('status')}")
    if not git.get("git_available") or not git.get("on_main") or not git.get("not_behind"):
        failures.append(f"git_state:{git}")
    failures.extend(f"unexpected_git_path:{path}" for path in git.get("unexpected_paths", []))
    if not allow_volatile and git.get("volatile_dirty_paths"):
        failures.extend(f"volatile_still_dirty:{path}" for path in git["volatile_dirty_paths"])
    if not eol.get("ok") and not allow_line_ending_drift:
        failures.append(f"line_endings:{eol}")
    return {
        "step": "151.5",
        "name": CHECKPOINT_TITLE,
        "status": "pass" if not failures else "failed",
        "ok": not failures,
        "failures": failures,
        "data_integrity": data,
        "step148_integrity": step148,
        "heavy_model_integrity": heavy,
        "step151_4_status": step151_4.get("status"),
        "git": git,
        "line_endings": eol,
        "disposable_runtime_files": disposable,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def write_artifacts(result: dict[str, Any]) -> None:
    POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    POLICY_PATH.write_text(json.dumps(policy_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    persisted = json.loads(json.dumps(result, ensure_ascii=False))
    persisted["status"] = "prepared_for_commit" if result.get("ok") else "failed"
    STATUS_PATH.write_text(json.dumps(persisted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    SUMMARY_JSON_PATH.write_text(json.dumps({"report_type": "step151_5_post_sync_integrity", "summary": persisted}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    SUMMARY_MD_PATH.write_text(
        "# Step 151.5 — Post-Synchronization Integrity\n\n"
        f"- Status: **{'PASS' if result.get('ok') else 'FAILED'}**\n"
        f"- Latest synchronized draw: `{result.get('data_integrity', {}).get('latest_draw')}`\n"
        f"- Prize History rows: `{result.get('data_integrity', {}).get('counts', {}).get('prize')}`\n"
        f"- Historical/v40/v41 rows: `{result.get('data_integrity', {}).get('counts', {}).get('historical')}`\n"
        f"- Freshness blockers: `{result.get('data_integrity', {}).get('freshness_blockers')}`\n"
        f"- Step 148 settled draws: `{result.get('step148_integrity', {}).get('settled_count')}`\n"
        f"- Active expected draw: `{result.get('step148_integrity', {}).get('active_expected_draw_key')}`\n"
        f"- Heavy model integrity: **{'OK' if result.get('heavy_model_integrity', {}).get('ok') else 'FAILED'}**\n"
        f"- Unexpected Git paths: `{len(result.get('git', {}).get('unexpected_paths', []))}`\n"
        "- Commit and push are separate explicit operator actions.\n",
        encoding="utf-8", newline="\n",
    )


def prepare_checkpoint() -> dict[str, Any]:
    before = audit_post_sync_state(allow_volatile=True, allow_line_ending_drift=True)
    if not before.get("ok"):
        return {"ok": False, "phase": "pre_cleanup_audit", "before": before}
    restored = restore_volatile_tracked_artifacts()
    if not restored.get("ok"):
        return {"ok": False, "phase": "restore_volatile", "before": before, "restore": restored}
    removed = clean_disposable_runtime_files()
    normalized = normalize_tracked_text_line_endings()
    gitattributes_changed = update_gitattributes()
    close_step151_3_status()
    after = audit_post_sync_state(allow_volatile=False)
    write_artifacts(after)
    # Re-audit after generated Step 151.5 artifacts exist.
    final = audit_post_sync_state(allow_volatile=False)
    write_artifacts(final)
    return {
        "ok": bool(final.get("ok")),
        "phase": "prepared",
        "before": before,
        "restore": restored,
        "removed_disposable_runtime_files": removed,
        "normalized_text_files": normalized,
        "gitattributes_changed": gitattributes_changed,
        "final": final,
    }

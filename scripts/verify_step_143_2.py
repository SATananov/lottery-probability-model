from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

REQUIRED = [
    ROOT / "src" / "v143_2_official_draw_github_sync_audit_engine.py",
    ROOT / "src" / "v143_2_official_draw_github_sync_section.py",
    ROOT / "models" / "v143_2_official_draw_github_sync_policy.json",
    ROOT / "reports" / "STEP_143_2_OFFICIAL_DRAW_GITHUB_SYNC_VALIDATION_AND_AUDIT.md",
    ROOT / "scripts" / "verify_step_143_2.py",
    ROOT / "tools" / "check_official_draw_github_sync.py",
]


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        args,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )


def require_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0:
        raise AssertionError(f"{label} failed:\n{result.stdout}\n{result.stderr}")


def build_fixture(base: Path) -> tuple[Path, Path]:
    remote = base / "remote.git"
    work = base / "work"
    require_ok(run(["git", "init", "--bare", str(remote)], base), "git init --bare")
    require_ok(run(["git", "init", "-b", "main", str(work)], base), "git init work")
    require_ok(run(["git", "config", "user.name", "Step 143.2 Verify"], work), "git config name")
    require_ok(run(["git", "config", "user.email", "verify@example.invalid"], work), "git config email")
    require_ok(run(["git", "remote", "add", "origin", str(remote)], work), "git remote add")

    for rel, text in {
        ".gitignore": "reports/runtime/v143_2_git_sync/\n",
        "data/historical_draws.csv": "date,year,draw_no\n2026-07-09,2026,53\n",
        "data/v40_normalized_draw_events.csv": "draw\n53\n",
        "data/v41_canonical_draw_events.csv": "draw\n53\n",
        "data/user_journal.db": "LOCAL-ONLY\n",
        "models/status.json": "{\"draw\": 53}\n",
        "reports/status.md": "# Draw 53\n",
        "src/local_note.py": "VALUE = 1\n",
    }.items():
        path = work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    require_ok(run(["git", "add", "."], work), "initial git add")
    require_ok(run(["git", "commit", "-m", "Initial fixture"], work), "initial commit")
    require_ok(run(["git", "push", "-u", "origin", "main"], work), "initial push")
    return work, remote


def main() -> int:
    failures: list[str] = []
    for path in REQUIRED:
        if not path.is_file():
            failures.append(f"Missing: {path.relative_to(ROOT)}")
    python_files = [
        REQUIRED[0],
        REQUIRED[1],
        ROOT / "scripts" / "verify_step_143_2.py",
        ROOT / "tools" / "check_official_draw_github_sync.py",
        ROOT / "src" / "add_draws_section.py",
    ]
    for path in python_files:
        if path.exists():
            try:
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            except Exception as exc:
                failures.append(f"Syntax error {path.relative_to(ROOT)}: {exc}")

    add_draw_text = (ROOT / "src" / "add_draws_section.py").read_text(encoding="utf-8")
    for marker in [
        "capture_git_snapshot",
        "synchronize_official_draw_outputs",
        "render_git_sync_preflight",
        "render_git_sync_result",
        "baseline=git_sync_baseline",
    ]:
        if marker not in add_draw_text:
            failures.append(f"Missing add-draw integration marker: {marker}")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    if "reports/runtime/v143_2_git_sync/" not in gitignore:
        failures.append("Runtime audit directory is not ignored")

    try:
        policy = json.loads(REQUIRED[2].read_text(encoding="utf-8"))
        if policy.get("heavy_ml_retraining_performed") is not False:
            failures.append("Step 143.2 policy must not enable heavy ML retraining")
    except Exception as exc:
        failures.append(f"Policy JSON invalid: {exc}")

    if not failures:
        try:
            from src.v143_2_official_draw_github_sync_audit_engine import (
                capture_git_snapshot,
                retry_push_and_confirm,
                synchronize_official_draw_outputs,
            )

            temp = Path(tempfile.mkdtemp(prefix="step143_2_verify_"))
            try:
                work, remote = build_fixture(temp)

                baseline = capture_git_snapshot(work)
                assert baseline["status"] == "ready", baseline
                assert baseline["can_sync"] is True

                # These changes happen after the baseline. Only the approved scope may be committed.
                (work / "data" / "historical_draws.csv").write_text(
                    "date,year,draw_no\n2026-07-09,2026,53\n2026-07-12,2026,54\n",
                    encoding="utf-8",
                )
                (work / "models" / "status.json").write_text('{"draw": 54}\n', encoding="utf-8")
                (work / "reports" / "status.md").write_text("# Draw 54\n", encoding="utf-8")
                (work / "data" / "user_journal.db").write_text("PRIVATE LOCAL CHANGE\n", encoding="utf-8")
                (work / "src" / "local_note.py").write_text("VALUE = 2\n", encoding="utf-8")

                result = synchronize_official_draw_outputs(
                    year=2026,
                    draw_no=54,
                    baseline=baseline,
                    repo_root=work,
                )
                assert result["status"] == "remote_confirmed", result
                assert result["ok"] is True
                assert result["local_commit_sha"] == result["remote_commit_sha"]
                assert "data/user_journal.db" not in result["staged_files"]
                assert "src/local_note.py" not in result["staged_files"]
                assert "data/user_journal.db" in result["excluded_changed_files"]
                assert "src/local_note.py" in result["excluded_changed_files"]
                assert (work / result["audit_json_path"]).is_file()

                status = run(["git", "status", "--short"], work)
                require_ok(status, "status after sync")
                status_text = status.stdout.replace("\\", "/")
                assert "data/user_journal.db" in status_text
                assert "src/local_note.py" in status_text
                assert "reports/runtime/v143_2_git_sync" not in status_text

                remote_show = run(["git", "--git-dir", str(remote), "show", "--name-only", "--pretty=format:", "main"], temp)
                require_ok(remote_show, "remote show")
                remote_files = {line.strip().replace("\\", "/") for line in remote_show.stdout.splitlines() if line.strip()}
                assert "data/historical_draws.csv" in remote_files
                assert "models/status.json" in remote_files
                assert "reports/status.md" in remote_files
                assert "data/user_journal.db" not in remote_files
                assert "src/local_note.py" not in remote_files

                # A pre-existing sync-scope change must block the next automatic operation.
                require_ok(run(["git", "restore", "data/user_journal.db", "src/local_note.py"], work), "restore excluded")
                (work / "models" / "status.json").write_text('{"draw": 55}\n', encoding="utf-8")
                blocked = capture_git_snapshot(work)
                assert blocked["status"] == "preexisting_sync_scope_changes", blocked
                assert blocked["can_sync"] is False

                require_ok(run(["git", "restore", "models/status.json"], work), "restore model")
                (work / "src" / "local_note.py").write_text("VALUE = 3\n", encoding="utf-8")
                require_ok(run(["git", "add", "src/local_note.py"], work), "stage unrelated")
                staged = capture_git_snapshot(work)
                assert staged["status"] == "preexisting_staged_changes", staged
                assert staged["can_sync"] is False

                # A failed push must leave a retryable local commit, and retry must
                # be bound to the exact pending commit and branch.
                retry_base = temp / "retry_case"
                retry_base.mkdir(parents=True, exist_ok=True)
                retry_work, retry_remote = build_fixture(retry_base)
                retry_baseline = capture_git_snapshot(retry_work)
                (retry_work / "models" / "status.json").write_text('{"draw": 54, "retry": true}\n', encoding="utf-8")
                missing_remote = retry_base / "temporarily_missing_remote.git"
                require_ok(run(["git", "remote", "set-url", "origin", str(missing_remote)], retry_work), "set missing remote")
                pending = synchronize_official_draw_outputs(
                    year=2026,
                    draw_no=54,
                    baseline=retry_baseline,
                    repo_root=retry_work,
                )
                assert pending["status"] == "local_commit_pending_push", pending
                assert pending["local_commit_sha"]
                require_ok(run(["git", "remote", "set-url", "origin", str(retry_remote)], retry_work), "restore remote")
                retried = retry_push_and_confirm(retry_work)
                assert retried["status"] == "remote_confirmed", retried
                assert retried["local_commit_sha"] == retried["remote_commit_sha"]
            finally:
                shutil.rmtree(temp, ignore_errors=True)
        except Exception as exc:
            failures.append(f"Functional verification failed: {exc}")

    if failures:
        for failure in failures:
            print("FAIL", failure)
        return 1
    print("STEP_143_2_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import csv
import hashlib
import json
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED = [
    ROOT / "src" / "r_statistical_layer_compat_engine.py",
    ROOT / "tools" / "run_statistical_layer.py",
    ROOT / "src" / "v143_3_downstream_zero_blocker_closure_engine.py",
    ROOT / "src" / "v143_3_downstream_zero_blocker_closure_section.py",
    ROOT / "tools" / "run_downstream_zero_blocker_closure.py",
    ROOT / "tools" / "finalize_step_143_3_release.py",
    ROOT / "models" / "v143_3_statistical_layer_runner_status.json",
    ROOT / "models" / "v143_3_downstream_zero_blocker_status.json",
    ROOT / "reports" / "v143_3_downstream_zero_blocker_report.json",
    ROOT / "reports" / "v143_3_downstream_zero_blocker_summary.md",
    ROOT / "reports" / "STEP_143_3_FINAL_DOWNSTREAM_FRESHNESS_REPAIR_AND_ZERO_BLOCKER_CLOSURE.md",
]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    failures: list[str] = []
    before_hashes = {
        path.relative_to(ROOT).as_posix(): file_hash(path)
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }

    for path in REQUIRED:
        if not path.exists():
            failures.append(f"Missing: {path.relative_to(ROOT)}")

    compile_targets = [path for path in REQUIRED if path.suffix == ".py"] + [
        ROOT / "src" / "v125_unified_downstream_refresh_engine.py",
        ROOT / "src" / "v142_downstream_freshness_repair_engine.py",
        ROOT / "src" / "v143_automatic_lightweight_downstream_refresh_engine.py",
        ROOT / "streamlit_app.py",
    ]
    for path in compile_targets:
        if not path.exists():
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            failures.append(f"Compile error {path.relative_to(ROOT)}: {exc}")

    if not failures:
        from src.r_statistical_layer_compat_engine import generate_python_compatible_r_reports
        from src.v122_unified_official_draw_freshness_engine import build_freshness_report
        from src.v125_unified_downstream_refresh_engine import PIPELINE
        from src.v143_3_downstream_zero_blocker_closure_engine import run_final_zero_blocker_closure

        freshness = build_freshness_report(write_outputs=False)
        if freshness.get("overall_status") != "synced":
            failures.append(f"Current freshness is not synced: {freshness.get('overall_status')}")
        if int(freshness.get("blocking_out_of_sync_count", -1)) != 0:
            failures.append(f"Expected zero blockers, got {freshness.get('blocking_out_of_sync_count')}")
        remaining = [
            source for source in freshness.get("sources", [])
            if source.get("key") != "official" and source.get("status") not in {"synced", "informational", "local_optional"}
        ]
        if remaining:
            failures.append("Freshness contains remaining blockers: " + ", ".join(str(row.get("key")) for row in remaining))

        status = json.loads((ROOT / "models" / "v143_3_downstream_zero_blocker_status.json").read_text(encoding="utf-8"))
        if status.get("status") not in {"completed", "completed_with_stage_warning", "already_synced"}:
            failures.append(f"Invalid Step 143.3 status: {status.get('status')}")
        if status.get("zero_blocker_confirmed") is not True:
            failures.append("Step 143.3 status does not confirm zero blockers")
        if status.get("heavy_ml_retraining_performed") is not False:
            failures.append("Heavy ML retraining guardrail is not false")
        if status.get("heavy_model_changes"):
            failures.append("Heavy model artifacts changed during closure")
        if status.get("personal_changes_after_restore"):
            failures.append("Personal journal state differs after protection")

        plan = run_final_zero_blocker_closure(plan_only=True, write_outputs=False)
        if plan.get("status") != "already_synced":
            failures.append(f"Plan-only closure must report already_synced, got {plan.get('status')}")

        r_stage = next((stage for stage in PIPELINE if stage.get("id") == "r_statistics"), None)
        if not r_stage or r_stage.get("kind") != "python":
            failures.append("R statistical stage must use the cross-platform Python launcher")
        elif r_stage.get("command", [])[:1] != ["tools/run_statistical_layer.py"]:
            failures.append(f"Unexpected R statistical stage command: {r_stage.get('command')}")

        with tempfile.TemporaryDirectory(prefix="lpm_step143_3_verify_") as tmp:
            temp_root = Path(tmp)
            (temp_root / "data").mkdir(parents=True)
            shutil.copy2(ROOT / "data" / "historical_draws.csv", temp_root / "data" / "historical_draws.csv")
            generated = generate_python_compatible_r_reports(
                project_root=temp_root,
                simulations=4,
                seed=42,
                write_outputs=True,
            )
            latest = generated.get("latest_draw", {})
            official = freshness.get("official_latest_draw", {})
            if (latest.get("year"), latest.get("draw_number")) != (official.get("year"), official.get("draw_number")):
                failures.append(f"Compatibility runner latest draw mismatch: {latest} vs {official}")
            audit_path = temp_root / "reports" / "r" / "r_data_audit.csv"
            if not audit_path.exists():
                failures.append("Compatibility runner did not create r_data_audit.csv")
            else:
                with audit_path.open("r", encoding="utf-8", newline="") as handle:
                    metrics = {row["metric"]: row["value"] for row in csv.DictReader(handle)}
                if int(metrics.get("latest_draw_number", 0)) != int(official.get("draw_number", -1)):
                    failures.append("Compatibility audit latest draw is incorrect")

    after_hashes = {
        path.relative_to(ROOT).as_posix(): file_hash(path)
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts
    }
    # py_compile may create __pycache__, which is intentionally ignored. All tracked/source
    # files must remain byte-identical during verification.
    changed = [key for key in sorted(set(before_hashes) | set(after_hashes)) if before_hashes.get(key) != after_hashes.get(key)]
    changed = [key for key in changed if "__pycache__" not in key and not key.endswith(".pyc")]
    if changed:
        failures.append("Verification changed project files: " + ", ".join(changed[:20]))

    if failures:
        for failure in failures:
            print("FAIL", failure)
        return 1
    print("STEP_143_3_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REQUIRED = [
    ROOT / "src" / "v143_automatic_lightweight_downstream_refresh_engine.py",
    ROOT / "src" / "v124_safe_official_draw_ingestion_engine.py",
    ROOT / "src" / "v124_safe_official_draw_ingestion_section.py",
    ROOT / "reports" / "STEP_143_AUTOMATIC_LIGHTWEIGHT_DOWNSTREAM_REFRESH_AFTER_OFFICIAL_DRAW.md",
]


def main() -> int:
    failures: list[str] = []
    for path in REQUIRED:
        if not path.exists():
            failures.append(f"Missing: {path.relative_to(ROOT)}")
    for path in REQUIRED[:3]:
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                failures.append(f"Compile error {path.relative_to(ROOT)}: {exc}")

    if not failures:
        from src.v143_automatic_lightweight_downstream_refresh_engine import (
            run_automatic_lightweight_refresh_after_ingestion,
        )

        skipped = run_automatic_lightweight_refresh_after_ingestion(
            {"status": "duplicate_blocked", "inserted": False, "draw_key": "2026-53"},
            write_outputs=False,
        )
        if skipped.get("status") != "not_triggered":
            failures.append("Refresh must not run without a newly inserted draw")

        calls: list[dict] = []

        def fake_repair(**kwargs):
            calls.append(kwargs)
            return {"status": "completed", "heavy_model_retraining_performed": False}

        completed = run_automatic_lightweight_refresh_after_ingestion(
            {"status": "inserted", "inserted": True, "draw_key": "2026-54"},
            timeout_seconds=321,
            repair_runner=fake_repair,
            write_outputs=False,
        )
        if completed.get("status") != "completed":
            failures.append("Inserted draw must trigger successful lightweight refresh")
        if completed.get("heavy_ml_retraining_performed") is not False:
            failures.append("Heavy ML retraining must remain disabled")
        if not calls or calls[0].get("timeout_seconds") != 321:
            failures.append("Configured downstream timeout was not forwarded")

    if failures:
        for failure in failures:
            print("FAIL", failure)
        return 1
    print("STEP_143_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import compileall
import importlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_MODULES = ("streamlit", "pandas", "sklearn", "joblib", "numpy", "altair")
REQUIRED_DATASETS = (
    ROOT / "data" / "historical_draws.csv",
    ROOT / "data" / "v40_normalized_draw_events.csv",
    ROOT / "data" / "v41_canonical_draw_events.csv",
)


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def ok(message: str) -> None:
    print(f"[OK] {message}")


def main() -> int:
    if not ((3, 11) <= sys.version_info[:2] < (3, 14)):
        fail(f"Supported Python range is 3.11-3.13; detected {sys.version.split()[0]}")
    ok(f"Python {sys.version.split()[0]}")

    imported = {}
    for module_name in REQUIRED_MODULES:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            fail(f"Cannot import {module_name}: {exc}")
        imported[module_name] = getattr(module, "__version__", "unknown")
    ok("Runtime imports: " + ", ".join(f"{k}={v}" for k, v in imported.items()))

    if not compileall.compile_dir(ROOT, quiet=1, force=False):
        fail("Python compilation failed")
    ok("All Python files compile")

    pandas = importlib.import_module("pandas")
    row_counts = []
    for path in REQUIRED_DATASETS:
        if not path.exists():
            fail(f"Missing dataset: {path.relative_to(ROOT)}")
        frame = pandas.read_csv(path)
        if frame.empty:
            fail(f"Empty dataset: {path.relative_to(ROOT)}")
        row_counts.append(len(frame))
    if len(set(row_counts)) != 1:
        fail(f"Dataset row counts are not synchronized: {row_counts}")
    ok(f"Core datasets synchronized at {row_counts[0]} rows")

    database = ROOT / "data" / "user_journal.db"
    if database.exists():
        with sqlite3.connect(database) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            fail(f"SQLite integrity check returned: {result}")
        ok("SQLite journal integrity")

    json_count = 0
    for path in (ROOT / "models").rglob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            fail(f"Invalid JSON artifact {path.relative_to(ROOT)}: {exc}")
        json_count += 1
    ok(f"Model/status JSON artifacts: {json_count}")

    joblib = imported and importlib.import_module("joblib")
    joblib_count = 0
    for path in (ROOT / "models").rglob("*.joblib"):
        try:
            joblib.load(path)
        except Exception as exc:
            fail(f"Cannot load model artifact {path.relative_to(ROOT)}: {exc}")
        joblib_count += 1
    ok(f"Joblib artifacts loaded: {joblib_count}")

    forbidden = [ROOT / ".r-lib"]
    present = [str(path.relative_to(ROOT)) for path in forbidden if path.exists()]
    if present:
        fail("Local environment/cache directories found: " + ", ".join(present))
    ok("No bundled R dependency environment")

    print("CLEAN_ENVIRONMENT_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

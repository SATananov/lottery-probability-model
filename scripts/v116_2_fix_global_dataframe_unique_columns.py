from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "streamlit_app.py"
failures: list[str] = []

try:
    text = TARGET.read_text(encoding="utf-8")
    required = [
        "def _bg34_unique_dataframe_columns",
        "_bg34_orig_dataframe(_bg34_unique_dataframe_columns(_bg34_translate_dataframe(data))",
        "_bg34_orig_table(_bg34_unique_dataframe_columns(_bg34_translate_dataframe(data))",
    ]
    for needle in required:
        if needle not in text:
            failures.append(f"Missing expected patch marker: {needle}")
except Exception as exc:
    failures.append(f"Cannot read streamlit_app.py: {exc}")

bad_count = 0
try:
    patch_text = Path(__file__).read_text(encoding="utf-8", errors="replace")
    bad_count += patch_text.count("?" * 4) + patch_text.count(chr(0xFFFD))
except Exception as exc:
    failures.append(f"Cannot scan check script: {exc}")

print("STEP_116_2_STATUS", "GLOBAL_DATAFRAME_COLUMNS_FIXED" if not failures else "CHECK_REQUIRED")
print("BLOCKING_FAILURES", len(failures))
print("BAD_COUNT", bad_count)
for failure in failures:
    print("FAILURE", failure)

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src" / "backtesting_center_section.py"

failures: list[str] = []

try:
    source = TARGET.read_text(encoding="utf-8")
    if "def _prepare_backtest_table_for_display" not in source:
        failures.append("Display-safe column helper is missing.")
except Exception as exc:
    failures.append(f"Cannot read backtesting section: {exc}")

try:
    spec = importlib.util.spec_from_file_location("backtesting_center_section", TARGET)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)

    sample = pd.DataFrame(
        [["frequency_baseline", 1, 2026, 49, 49, "5,11,44,46,47,48", "5,11,44,46,47,48", 3, "5,11,44"]],
        columns=[
            "model",
            "event_index",
            "Година",
            "draw_number",
            "Тираж №",
            "predicted_top6",
            "actual_numbers",
            "hits",
            "Познати числа",
        ],
    )
    shown = module._prepare_backtest_table_for_display(sample)
    if not shown.columns.is_unique:
        failures.append("Columns are still duplicated after display preparation.")
    required = ["Модел", "Ред", "Година", "Тираж №", "Тираж № (2)", "Познати числа", "Познати числа (2)"]
    missing = [col for col in required if col not in shown.columns]
    if missing:
        failures.append("Missing expected display columns: " + ", ".join(missing))
except Exception as exc:
    failures.append(f"Runtime check failed: {exc}")

bad_count = 0
for path in [TARGET, Path(__file__)]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        bad_count += text.count("????") + text.count("�")
    except Exception as exc:
        failures.append(f"Cannot scan {path}: {exc}")

print("STEP_116_1_STATUS", "BACKTESTING_DUPLICATE_COLUMNS_FIXED" if not failures else "CHECK_REQUIRED")
print("BLOCKING_FAILURES", len(failures))
print("BAD_COUNT", bad_count)
for failure in failures:
    print("FAILURE", failure)

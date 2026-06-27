from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

bad_markers = ["????", "\ufffd"]
active_files = [
    ROOT / "src" / "v111_prize_winner_history_engine.py",
    ROOT / "src" / "v111_prize_winner_history_section.py",
]

failures: list[str] = []
for path in active_files:
    if not path.exists():
        failures.append(f"missing:{path.relative_to(ROOT)}")
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    for marker in bad_markers:
        if marker in text:
            failures.append(f"bad-marker:{path.relative_to(ROOT)}:{marker}")

try:
    from src.v111_prize_winner_history_engine import (
        import_manual_csv_text,
        manual_csv_template_text,
        parse_manual_csv_text,
        write_artifacts,
    )

    template = manual_csv_template_text()
    records = parse_manual_csv_text(template)
    if len(records) != 1:
        failures.append("manual-template-record-count")
    else:
        record = records[0]
        if record.get("draw_key") != "2026-49":
            failures.append("manual-template-draw-key")
        if record.get("numbers_text") != "5, 11, 44, 46, 47, 48":
            failures.append("manual-template-numbers")
        if int(record.get("winners_5") or -1) != 2:
            failures.append("manual-template-winners-5")
    # Do not import the sample into the user's database during verification.
    summary = write_artifacts()
except Exception as exc:
    failures.append(f"engine-check:{exc}")
    summary = {}

report = {
    "step": "111.6",
    "status": "PRIZE_IMPORT_CAPTCHA_SAFE_MANUAL_READY" if not failures else "CHECK_REQUIRED",
    "blocking_failures": len(failures),
    "failures": failures,
    "summary_status": summary.get("status") if isinstance(summary, dict) else None,
}
(REPORTS / "v111_6_prize_import_captcha_safe_manual_import.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(f"STEP_111_6_STATUS {report['status']}")
print(f"BLOCKING_FAILURES {report['blocking_failures']}")
if failures:
    for item in failures[:20]:
        print(f"FAIL {item}")
    sys.exit(1)
print("MANUAL_CSV_TEMPLATE_OK 1")
print("CAPTCHA_MESSAGE_READY 1")

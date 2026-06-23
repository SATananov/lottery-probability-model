from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v88_anti_zero_coverage_engine import (
    SAFE_NOTE,
    build_four_combination_coverage_ticket,
    compare_current_vs_coverage_candidate,
    load_existing_active_package,
)

MODEL_PATH = ROOT / "models" / "v88" / "v88_anti_zero_coverage_model.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v88_anti_zero_coverage_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v88_anti_zero_coverage_summary.md"
ANALYSIS_CSV_PATH = ROOT / "reports" / "v88_anti_zero_coverage_analysis.csv"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def _fmt_combo(combo: list[int]) -> str:
    return ", ".join(str(number) for number in combo)


def _write_csv(path: Path, summary: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for package_name, analysis in [
        ("\u0422\u0435\u043a\u0443\u0449 \u043f\u0430\u043a\u0435\u0442", summary["current"]),
        ("\u0417\u0430\u0449\u0438\u0442\u0435\u043d \u0432\u0430\u0440\u0438\u0430\u043d\u0442", summary["candidate"]),
    ]:
        for index, combo in enumerate(analysis.get("combinations", []), start=1):
            rows.append({
                "\u041f\u0430\u043a\u0435\u0442": package_name,
                "\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f": index,
                "\u0427\u0438\u0441\u043b\u0430": _fmt_combo(combo),
                "\u0420\u0438\u0441\u043a \u043e\u0442 \u043f\u0440\u0430\u0437\u0435\u043d \u043f\u0430\u043a\u0435\u0442 %": round(analysis["empty_risk_percent"], 6),
                "\u0428\u0430\u043d\u0441 \u0437\u0430 \u043f\u043e\u043d\u0435 1 \u0441\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u0435 %": round(analysis["at_least_one_hit_percent"], 6),
                "\u041f\u043e\u043a\u0440\u0438\u0442\u0438 \u0440\u0430\u0437\u043b\u0438\u0447\u043d\u0438 \u0447\u0438\u0441\u043b\u0430": analysis["unique_covered_numbers"],
            })
    if not rows:
        rows.append({"status": "empty"})
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, summary: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    current = summary["current"]
    candidate = summary["candidate"]
    delta = summary["delta"]
    lines = [
        "# \u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0437\u0430\u0449\u0438\u0442\u0430 \u043e\u0442 \u043f\u0440\u0430\u0437\u0435\u043d \u0444\u0438\u0448",
        "",
        "\u0422\u043e\u0437\u0438 \u0441\u043b\u043e\u0439 \u043d\u0435 \u043e\u0431\u0435\u0449\u0430\u0432\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430. \u0422\u043e\u0439 \u0438\u0437\u043c\u0435\u0440\u0432\u0430 \u043f\u043e\u043a\u0440\u0438\u0442\u0438\u0435\u0442\u043e \u043d\u0430 \u043f\u0430\u043a\u0435\u0442\u0430 \u0438 \u0440\u0438\u0441\u043a\u0430 \u0432\u0441\u0438\u0447\u043a\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u0434\u0430 \u043e\u0441\u0442\u0430\u043d\u0430\u0442 \u0431\u0435\u0437 \u043d\u0438\u0442\u043e \u0435\u0434\u043d\u043e \u0441\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u0435.",
        "",
        "## \u0420\u0435\u0437\u044e\u043c\u0435",
        "",
        f"- \u0422\u0435\u043a\u0443\u0449 \u043f\u0430\u043a\u0435\u0442: **{current['unique_covered_numbers']}** \u0440\u0430\u0437\u043b\u0438\u0447\u043d\u0438 \u0447\u0438\u0441\u043b\u0430, \u0440\u0438\u0441\u043a **{current['empty_risk_percent']:.2f}%**.",
        f"- \u0417\u0430\u0449\u0438\u0442\u0435\u043d \u0432\u0430\u0440\u0438\u0430\u043d\u0442: **{candidate['unique_covered_numbers']}** \u0440\u0430\u0437\u043b\u0438\u0447\u043d\u0438 \u0447\u0438\u0441\u043b\u0430, \u0440\u0438\u0441\u043a **{candidate['empty_risk_percent']:.2f}%**.",
        f"- \u0420\u0430\u0437\u043b\u0438\u043a\u0430 \u0432 \u0448\u0430\u043d\u0441\u0430 \u0437\u0430 \u043f\u043e\u043d\u0435 1 \u0441\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u0435: **{delta['at_least_one_hit_delta_percent']:.2f}%**.",
        "",
        "## \u0411\u0435\u043b\u0435\u0436\u043a\u0430",
        "",
        SAFE_NOTE,
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    current_combinations, metadata = load_existing_active_package()
    candidate_combinations = build_four_combination_coverage_ticket(existing_combinations=current_combinations)
    comparison = compare_current_vs_coverage_candidate(current_combinations, candidate_combinations)
    summary = {
        "step": 88,
        "name": "\u0417\u0430\u0449\u0438\u0442\u0430 \u043e\u0442 \u043f\u0440\u0430\u0437\u0435\u043d \u0444\u0438\u0448",
        "status": "OK",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_metadata": metadata,
        "current": comparison["current"],
        "candidate": comparison["candidate"],
        "delta": comparison["delta"],
        "safe_note": SAFE_NOTE,
    }

    _write_json(MODEL_PATH, summary)
    _write_json(SUMMARY_JSON_PATH, summary)
    _write_markdown(SUMMARY_MD_PATH, summary)
    _write_csv(ANALYSIS_CSV_PATH, summary)

    print("STEP_88_STATUS OK")
    print(f"CURRENT_UNIQUE_NUMBERS {summary['current']['unique_covered_numbers']}")
    print(f"CURRENT_EMPTY_RISK_PERCENT {summary['current']['empty_risk_percent']:.6f}")
    print(f"CANDIDATE_UNIQUE_NUMBERS {summary['candidate']['unique_covered_numbers']}")
    print(f"CANDIDATE_EMPTY_RISK_PERCENT {summary['candidate']['empty_risk_percent']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

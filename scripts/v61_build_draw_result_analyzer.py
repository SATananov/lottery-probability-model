from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v61_draw_result_analyzer_engine import (
    analyze_latest_draw_result,
    export_latest_draw_result_analysis,
)


def main() -> None:
    result = analyze_latest_draw_result(top_n=12)
    export_latest_draw_result_analysis(result)

    latest = result["latest_draw"]
    signal_summary = result["model_signal_summary"]

    print("V61_DRAW_RESULT_ANALYZER_OK")
    print(f"TOTAL_DRAWS {result['total_draws']}")
    print(f"LATEST_DATE {latest.get('date', '')}")
    print(f"LATEST_DRAW {latest.get('draw_no', '')}")
    print(f"LATEST_NUMBERS {latest.get('numbers_text', '')}")
    print(f"BEST_SIGNAL_HITS {signal_summary.get('best_hit_count', 0)}")
    print(f"SIGNALS_CHECKED {signal_summary.get('signal_count', 0)}")


if __name__ == "__main__":
    main()

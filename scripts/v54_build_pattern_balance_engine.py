from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    models_dir = ROOT / "models" / "v54"
    reports_dir = ROOT / "reports"

    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    rules = {
        "module": "pattern_balance_engine",
        "version": "v54",
        "user_facing_name_bg": "Баланс на комбинациите",
        "purpose_bg": (
            "Оценява структурния баланс на една или повече 6/49 комбинации: "
            "четни/нечетни, ниски/високи, сума, диапазони, поредици, разстояния и крайни цифри."
        ),
        "not_a_prediction_bg": (
            "Модулът не предсказва печеливши числа и не гарантира печалба. "
            "Той измерва само структурата на избраните комбинации."
        ),
        "metrics": [
            "odd_even_distribution",
            "low_high_distribution",
            "sum",
            "sum_band",
            "range_distribution",
            "final_digit_distribution",
            "gaps",
            "minimum_gap",
            "maximum_gap",
            "average_gap",
            "longest_consecutive_run",
            "consecutive_pairs",
            "pattern_score",
        ],
        "score_bands": {
            "80_100": "Отличен баланс",
            "65_79": "Добър баланс",
            "45_64": "Среден баланс",
            "0_44": "Небалансирана структура",
        },
    }

    summary = {
        "status": "completed",
        "module": "Pattern Balance Engine",
        "version": "v54",
        "summary_bg": (
            "Добавен е модул за анализ на структурния баланс на комбинации. "
            "Той допълва покритието на фиша, като оценява дали отделните комбинации са прекалено крайни, "
            "твърде подредени или добре разпределени."
        ),
        "safety_bg": (
            "Резултатът е статистическа и структурна оценка, а не обещание за печалба."
        ),
    }

    (models_dir / "v54_pattern_balance_rules.json").write_text(
        json.dumps(rules, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (reports_dir / "v54_pattern_balance_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    markdown = """# V54 Pattern Balance Engine

## Цел

Този модул анализира структурния баланс на 6/49 комбинации.

## Какво измерва

- четни и нечетни числа;
- ниски и високи числа;
- сума на комбинацията;
- разпределение по диапазони;
- последователни числа;
- разстояния между числата;
- повторение на крайни цифри;
- обща структурна оценка от 0 до 100.

## Важно

Това не е предсказание и не е гаранция за печалба. Модулът оценява само структурата на избраните комбинации.
"""

    (reports_dir / "v54_pattern_balance_summary.md").write_text(markdown, encoding="utf-8")

    print("V54_STATUS v54_pattern_balance_engine_completed")


if __name__ == "__main__":
    main()

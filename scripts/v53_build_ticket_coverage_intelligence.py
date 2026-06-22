from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    models_dir = ROOT / "models" / "v53"
    reports_dir = ROOT / "reports"

    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    rules = {
        "module": "ticket_coverage_intelligence",
        "version": "v53",
        "user_facing_name_bg": "Покритие на фиша",
        "purpose_bg": (
            "Оценява дали няколко комбинации във фиш са достатъчно разнообразни "
            "или се припокриват прекалено много."
        ),
        "not_a_prediction_bg": (
            "Този модул не предсказва печеливши числа и не увеличава математическата гаранция за печалба."
        ),
        "metrics": [
            "unique_numbers_count",
            "coverage_efficiency",
            "average_pairwise_overlap",
            "maximum_pairwise_overlap",
            "repeated_pairs_count",
            "repeated_triples_count",
            "duplicate_tickets_count",
            "odd_even_distribution",
            "low_high_distribution",
            "range_distribution",
        ],
        "score_bands": {
            "80_100": "Отлично покритие",
            "65_79": "Добро покритие",
            "45_64": "Средно покритие",
            "0_44": "Прекалено концентриран фиш",
        },
    }

    summary = {
        "status": "completed",
        "module": "Ticket Coverage Intelligence",
        "version": "v53",
        "summary_bg": (
            "Добавен е слой за анализ на покритието на цял фиш. "
            "Модулът проверява разнообразие, припокриване, повторени двойки/тройки "
            "и обща концентрация на комбинациите."
        ),
        "safety_bg": (
            "Резултатът е статистическа оценка на структурата на фиша, не обещание за печалба."
        ),
    }

    (models_dir / "v53_ticket_coverage_rules.json").write_text(
        json.dumps(rules, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (reports_dir / "v53_ticket_coverage_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    markdown = """# V53 Ticket Coverage Intelligence

## Цел

Този модул оценява покритието на цял фиш, а не само на една комбинация.

## Какво измерва

- брой валидни комбинации;
- уникални числа във всички комбинации;
- ефективност на покритието;
- средно и максимално припокриване между комбинации;
- повторени двойки;
- повторени тройки;
- дублирани комбинации;
- четни/нечетни;
- ниски/високи числа;
- разпределение по диапазони.

## Важно

Това не е предсказание и не е гаранция за печалба. Анализът само показва дали фишът е прекалено концентриран или по-добре разпределен.
"""

    (reports_dir / "v53_ticket_coverage_summary.md").write_text(markdown, encoding="utf-8")

    print("V53_STATUS v53_ticket_coverage_foundation_completed")


if __name__ == "__main__":
    main()

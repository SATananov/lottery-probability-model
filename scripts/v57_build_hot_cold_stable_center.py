from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v57_hot_cold_stable_engine import (
    build_hot_cold_stable_center,
    center_to_dataframe,
    export_hot_cold_stable_center,
)


def main() -> None:
    models_dir = ROOT / "models" / "v57"
    reports_dir = ROOT / "reports"

    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    center = build_hot_cold_stable_center()
    df = center_to_dataframe(center)

    export_hot_cold_stable_center(
        center,
        reports_dir / "v57_hot_cold_stable_numbers.csv",
        reports_dir / "v57_hot_cold_stable_numbers.json",
    )

    manifest = {
        "module": "hot_cold_stable_number_center",
        "version": "v57",
        "user_facing_name_bg": "Горещи, студени и стабилни числа",
        "total_draws": center["total_draws"],
        "numbers_profiled": center["numbers_profiled"],
        "data_path": center["data_path"],
        "purpose_bg": (
            "Класифицира числата според историческа сила, скорошна активност, "
            "закъснение и стабилност."
        ),
        "not_a_prediction_bg": (
            "Модулът не предсказва бъдещи тегления и не гарантира печалба. "
            "Той показва само историческо поведение и текущ статистически ритъм."
        ),
        "metrics": [
            "historical_strength_score",
            "recent_activity_score",
            "overdue_score",
            "stability_score",
            "combined_score",
            "main_group",
            "categories",
        ],
    }

    summary = {
        "status": "completed",
        "module": "Hot / Cold / Stable Number Center",
        "version": "v57",
        "total_draws": center["total_draws"],
        "numbers_profiled": center["numbers_profiled"],
        "group_summary": center["summary_rows"],
        "top_hot": [
            {"number": item["number"], "score": item["recent_activity_score"]}
            for item in center["top_hot"][:10]
        ],
        "top_cold": [
            {"number": item["number"], "recent_100_ratio": item["recent_100_ratio"]}
            for item in center["top_cold"][:10]
        ],
        "top_overdue": [
            {"number": item["number"], "draws_since_last_seen": item["draws_since_last_seen"]}
            for item in center["top_overdue"][:10]
        ],
        "safety_bg": center["safety_note_bg"],
    }

    (models_dir / "v57_hot_cold_stable_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (reports_dir / "v57_hot_cold_stable_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    markdown_lines = [
        "# V57 Hot / Cold / Stable Number Center",
        "",
        "## Цел",
        "",
        "Този модул групира числата според историческа сила, скорошна активност, закъснение и стабилност.",
        "",
        "## Важно",
        "",
        "Това не е предсказание и не е гаранция за печалба. Групите са исторически статистически контекст.",
        "",
        f"Анализирани тиражи: **{center['total_draws']}**",
        f"Профилирани числа: **{center['numbers_profiled']}**",
        "",
        "## Групи",
        "",
    ]

    for row in center["summary_rows"]:
        markdown_lines.append(
            f"- {row['group']}: {row['count']} числа — {', '.join(str(number) for number in row['numbers'])}"
        )

    (reports_dir / "v57_hot_cold_stable_summary.md").write_text(
        "\n".join(markdown_lines) + "\n",
        encoding="utf-8",
    )

    print("V57_STATUS v57_hot_cold_stable_center_completed")
    print("DATASET_DRAWS", center["total_draws"])
    print("NUMBER_PROFILES", center["numbers_profiled"])
    print("CSV_ROWS", len(df))


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v55_number_profile_engine import build_number_profiles, load_draw_events
from src.v57_hot_cold_stable_engine import build_hot_cold_stable_center
from src.v58_smart_ensemble_score_engine import (
    analyze_smart_ensemble_scores,
    ensemble_to_dataframe,
    export_smart_ensemble_result,
    parse_combination_lines,
)


def main() -> None:
    models_dir = ROOT / "models" / "v58"
    reports_dir = ROOT / "reports"

    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    events = load_draw_events()
    profiles = build_number_profiles(events)
    hot_cold_center = build_hot_cold_stable_center(events)

    sample_text = """
6, 13, 16, 19, 42, 44
4, 12, 21, 25, 34, 48
22, 28, 37, 38, 42, 49
"""

    combinations = parse_combination_lines(sample_text)
    result = analyze_smart_ensemble_scores(
        combinations=combinations,
        draw_events=events,
        profiles=profiles,
        hot_cold_center=hot_cold_center,
    )

    export_smart_ensemble_result(
        result,
        reports_dir / "v58_smart_ensemble_scores_sample.csv",
        reports_dir / "v58_smart_ensemble_scores_sample.json",
    )

    df = ensemble_to_dataframe(result)

    manifest = {
        "module": "smart_ensemble_score_2",
        "version": "v58",
        "user_facing_name_bg": "Обединена оценка",
        "total_draws": len(events),
        "data_path": str(events[0].get("data_path", "")) if events else "",
        "purpose_bg": (
            "Обединява няколко статистически слоя: покритие, баланс, профил на числа, "
            "горещи/студени/стабилни групи и историческа близост."
        ),
        "not_a_prediction_bg": (
            "Модулът не предсказва бъдещи тегления и не гарантира печалба. "
            "Той е статистически контролен слой."
        ),
        "component_weights": {
            "pattern_score": 0.22,
            "coverage_score": 0.16,
            "number_profile_score": 0.24,
            "hot_cold_balance_score": 0.20,
            "similarity_context_score": 0.18,
        },
        "depends_on": [
            "v53_ticket_coverage",
            "v54_pattern_balance",
            "v55_number_profile",
            "v56_draw_similarity",
            "v57_hot_cold_stable",
        ],
    }

    summary = {
        "status": "completed",
        "module": "Обединена оценка 2",
        "version": "v58",
        "total_draws": len(events),
        "sample_query_count": len(combinations),
        "average_final_score": result["average_final_score"],
        "best_score": result["best_score"],
        "weakest_score": result["weakest_score"],
        "portfolio_coverage_score": result["portfolio_coverage"].get("coverage_score", 0.0),
        "safety_bg": result["safety_note_bg"],
    }

    (models_dir / "v58_smart_ensemble_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (reports_dir / "v58_smart_ensemble_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    markdown_lines = [
        "# V58 Обединена оценка 2",
        "",
        "## Цел",
        "",
        "Този модул обединява няколко анализа в една крайна статистическа оценка.",
        "",
        "## Компоненти",
        "",
        "- Покритие на фиша;",
        "- Баланс на комбинациите;",
        "- Профил на число;",
        "- Горещи, студени и стабилни числа;",
        "- Подобни исторически тиражи.",
        "",
        "## Важно",
        "",
        "Това не е предсказание и не е гаранция за печалба. Модулът е статистически контролен слой.",
        "",
        f"Анализирани тиражи: **{len(events)}**",
        f"Средна примерна оценка: **{result['average_final_score']}**",
        f"Най-висока примерна оценка: **{result['best_score']}**",
        f"Най-ниска примерна оценка: **{result['weakest_score']}**",
        "",
        "## Примерни резултати",
        "",
    ]

    for row in df.to_dict("records"):
        markdown_lines.append(
            f"- {row['combination']} — обща оценка {row['final_score']} / 100, ниво: {row['band']}"
        )

    (reports_dir / "v58_smart_ensemble_summary.md").write_text(
        "\n".join(markdown_lines) + "\n",
        encoding="utf-8",
    )

    print("V58_STATUS v58_smart_ensemble_score_2_completed")
    print("DATASET_DRAWS", len(events))
    print("SAMPLE_ROWS", len(df))
    print("AVERAGE_FINAL_SCORE", result["average_final_score"])


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v55_number_profile_engine import build_number_profiles, load_draw_events
from src.v57_hot_cold_stable_engine import build_hot_cold_stable_center
from src.v59_smart_ticket_builder_2_engine import (
    build_smart_ticket_builder_2,
    builder_result_to_dataframe,
    export_builder_result,
)


def main() -> None:
    models_dir = ROOT / "models" / "v59"
    reports_dir = ROOT / "reports"

    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    events = load_draw_events()
    profiles = build_number_profiles(events)
    hot_cold_center = build_hot_cold_stable_center(events)

    result = build_smart_ticket_builder_2(
        ticket_count=5,
        candidate_count=120,
        seed=59,
        strategy="Балансиран",
        max_number_reuse=2,
        max_shared_numbers=2,
        draw_events=events,
        profiles=profiles,
        hot_cold_center=hot_cold_center,
    )

    export_builder_result(
        result,
        reports_dir / "v59_smart_ticket_builder_2_sample.csv",
        reports_dir / "v59_smart_ticket_builder_2_sample.json",
    )

    df = builder_result_to_dataframe(result)

    manifest = {
        "module": "smart_ticket_builder_2",
        "version": "v59",
        "user_facing_name_bg": "Интелигентен генератор 2",
        "total_draws": result["total_draws"],
        "strategy": result["strategy"],
        "seed": result["seed"],
        "requested_ticket_count": result["requested_ticket_count"],
        "candidate_count_requested": result["candidate_count_requested"],
        "candidate_count_scored": result["candidate_count_scored"],
        "selected_count": result["selected_count"],
        "purpose_bg": (
            "Генерира кандидат-комбинации, оценява ги през Smart Ensemble Score 2 "
            "и избира по-разнообразен статистически фиш."
        ),
        "not_a_prediction_bg": (
            "Модулът не предсказва печеливши числа и не гарантира печалба. "
            "Той е помощник за статистически контрол на предложенията."
        ),
        "depends_on": [
            "v53_ticket_coverage",
            "v54_pattern_balance",
            "v55_number_profile",
            "v56_draw_similarity",
            "v57_hot_cold_stable",
            "v58_smart_ensemble_score_2",
        ],
    }

    summary = {
        "status": "completed",
        "module": "Smart Ticket Builder 2",
        "version": "v59",
        "total_draws": result["total_draws"],
        "selected_count": result["selected_count"],
        "average_final_score": result["average_final_score"],
        "best_score": result["best_score"],
        "weakest_score": result["weakest_score"],
        "coverage_score": result["coverage_score"],
        "selected_tickets": result["selected_tickets"],
        "safety_bg": result["safety_note_bg"],
    }

    (models_dir / "v59_smart_ticket_builder_2_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (reports_dir / "v59_smart_ticket_builder_2_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    markdown_lines = [
        "# V59 Smart Ticket Builder 2",
        "",
        "## Цел",
        "",
        "Този модул генерира кандидат-комбинации и избира фиш чрез обединената оценка.",
        "",
        "## Как работи",
        "",
        "- генерира кандидат-комбинации според избрана стратегия;",
        "- оценява кандидатите чрез Smart Ensemble Score 2;",
        "- пази разнообразие между комбинациите;",
        "- връща предложен фиш с обяснения.",
        "",
        "## Важно",
        "",
        "Това не е предсказание и не е гаранция за печалба. Модулът е статистически помощник.",
        "",
        f"Анализирани тиражи: **{result['total_draws']}**",
        f"Избрани комбинации: **{result['selected_count']}**",
        f"Средна оценка: **{result['average_final_score']}**",
        f"Покритие: **{result['coverage_score']}**",
        "",
        "## Предложен фиш",
        "",
    ]

    for row in df.to_dict("records"):
        markdown_lines.append(
            f"- {row['combination']} — оценка {row['final_score']} / 100, ниво: {row['band']}"
        )

    (reports_dir / "v59_smart_ticket_builder_2_summary.md").write_text(
        "\n".join(markdown_lines) + "\n",
        encoding="utf-8",
    )

    print("V59_STATUS v59_smart_ticket_builder_2_completed")
    print("DATASET_DRAWS", result["total_draws"])
    print("SELECTED_COUNT", result["selected_count"])
    print("AVERAGE_FINAL_SCORE", result["average_final_score"])
    print("COVERAGE_SCORE", result["coverage_score"])


if __name__ == "__main__":
    main()

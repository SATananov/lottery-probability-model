from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v55_number_profile_engine import load_draw_events
from src.v56_draw_similarity_engine import analyze_draw_similarity, parse_combination_lines


def main() -> None:
    models_dir = ROOT / "models" / "v56"
    reports_dir = ROOT / "reports"

    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    events = load_draw_events()

    sample_text = "6, 13, 16, 19, 42, 44"
    sample_combinations = parse_combination_lines(sample_text)
    sample_result = analyze_draw_similarity(sample_combinations, events, top_n=10)

    manifest = {
        "module": "draw_similarity_search",
        "version": "v56",
        "user_facing_name_bg": "Подобни исторически тиражи",
        "total_draws": len(events),
        "data_path": str(events[0].get("data_path", "")) if events else "",
        "purpose_bg": (
            "Сравнява въведена 6/49 комбинация с всички исторически тиражи и показва "
            "най-близките исторически съвпадения."
        ),
        "not_a_prediction_bg": (
            "Модулът не предсказва бъдещи тегления и не гарантира печалба. "
            "Той измерва само историческа близост."
        ),
        "metrics": [
            "match_distribution_0_to_6",
            "closest_historical_draws",
            "exact_matches_count",
            "five_matches_count",
            "four_matches_count",
            "three_matches_count",
            "historical_similarity_score",
        ],
    }

    summary = {
        "status": "completed",
        "module": "Draw Similarity Search",
        "version": "v56",
        "total_draws": len(events),
        "sample_query": sample_text,
        "sample_result": sample_result,
        "safety_bg": (
            "Резултатът е историческо сравнение, не обещание за бъдещо теглене."
        ),
    }

    (models_dir / "v56_draw_similarity_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (reports_dir / "v56_draw_similarity_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    analysis = sample_result["analyses"][0] if sample_result["analyses"] else {}

    markdown_lines = [
        "# V56 Draw Similarity Search",
        "",
        "## Цел",
        "",
        "Този модул сравнява въведена комбинация с всички исторически тиражи.",
        "",
        "## Какво измерва",
        "",
        "- колко тиража имат 6, 5, 4, 3, 2, 1 или 0 съвпадащи числа;",
        "- най-близките исторически тиражи;",
        "- точни исторически съвпадения;",
        "- индекс на историческа близост;",
        "- предупреждения и препоръки.",
        "",
        "## Важно",
        "",
        "Това не е предсказание и не е гаранция за печалба. Сходството с минали тиражи не променя математическата вероятност.",
        "",
        f"Анализирани тиражи: **{len(events)}**",
        f"Примерна комбинация: **{sample_text}**",
        "",
        "## Примерен резултат",
        "",
        f"- Максимални съвпадения: {analysis.get('max_match_count', '')}",
        f"- Точни съвпадения: {analysis.get('exact_matches_count', '')}",
        f"- 5 от 6: {analysis.get('five_matches_count', '')}",
        f"- 4 от 6: {analysis.get('four_matches_count', '')}",
    ]

    (reports_dir / "v56_draw_similarity_summary.md").write_text(
        "\n".join(markdown_lines) + "\n",
        encoding="utf-8",
    )

    print("V56_STATUS v56_draw_similarity_search_completed")
    print("DATASET_DRAWS", len(events))
    print("SAMPLE_MAX_MATCH", analysis.get("max_match_count", ""))
    print("SAMPLE_EXACT_MATCHES", analysis.get("exact_matches_count", ""))


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v55_number_profile_engine import build_number_profiles, load_draw_events
from src.v57_hot_cold_stable_engine import build_hot_cold_stable_center
from src.v59_smart_ticket_builder_2_engine import build_smart_ticket_builder_2
from src.v60_ticket_builder_export_utils import (
    result_to_copy_text,
    result_to_csv_bytes,
    result_to_dataframe,
    result_to_json_bytes,
    result_to_txt_bytes,
)


def main() -> None:
    models_dir = ROOT / "models" / "v60"
    reports_dir = ROOT / "reports"

    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    events = load_draw_events()
    profiles = build_number_profiles(events)
    hot_cold_center = build_hot_cold_stable_center(events)

    result = build_smart_ticket_builder_2(
        ticket_count=5,
        candidate_count=120,
        seed=60,
        strategy="Балансиран",
        max_number_reuse=2,
        max_shared_numbers=2,
        draw_events=events,
        profiles=profiles,
        hot_cold_center=hot_cold_center,
    )

    df = result_to_dataframe(result)

    (reports_dir / "v60_ticket_builder_2_export_sample.csv").write_bytes(
        result_to_csv_bytes(result)
    )

    (reports_dir / "v60_ticket_builder_2_export_sample.json").write_bytes(
        result_to_json_bytes(result)
    )

    (reports_dir / "v60_ticket_builder_2_export_sample.txt").write_bytes(
        result_to_txt_bytes(result)
    )

    manifest = {
        "module": "ticket_builder_2_polish_export",
        "version": "v60",
        "user_facing_name_bg": "Интелигентен генератор 2",
        "total_draws": result["total_draws"],
        "selected_count": result["selected_count"],
        "average_final_score": result["average_final_score"],
        "coverage_score": result["coverage_score"],
        "purpose_bg": (
            "Полира потребителския изглед на Интелигентен генератор 2 и добавя TXT, CSV и JSON експорт."
        ),
        "not_a_prediction_bg": (
            "Модулът не предсказва печеливши числа и не гарантира печалба. "
            "Той е статистически помощник за изграждане и експортиране на фиш."
        ),
        "exports": [
            "reports/v60_ticket_builder_2_export_sample.txt",
            "reports/v60_ticket_builder_2_export_sample.csv",
            "reports/v60_ticket_builder_2_export_sample.json",
        ],
    }

    summary = {
        "status": "completed",
        "module": "Ticket Builder 2 Polish & Export",
        "version": "v60",
        "total_draws": result["total_draws"],
        "selected_count": result["selected_count"],
        "average_final_score": result["average_final_score"],
        "coverage_score": result["coverage_score"],
        "selected_tickets_text": result_to_copy_text(result),
        "safety_bg": result["safety_note_bg"],
    }

    (models_dir / "v60_ticket_builder_2_polish_export_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (reports_dir / "v60_ticket_builder_2_polish_export_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    markdown_lines = [
        "# V60 Ticket Builder 2 Polish & Export",
        "",
        "## Цел",
        "",
        "Този модул полира страницата „Интелигентен генератор 2“ и добавя експорт.",
        "",
        "## Добавено",
        "",
        "- готов фиш за копиране;",
        "- TXT експорт;",
        "- CSV експорт;",
        "- JSON експорт;",
        "- карти за всяка комбинация;",
        "- запазване на фиша за страницата „Обединена оценка“;",
        "- по-ясни предупреждения и препоръки.",
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
        "## Примерен фиш",
        "",
        "```text",
        result_to_copy_text(result),
        "```",
    ]

    for row in df.to_dict("records"):
        markdown_lines.append(
            f"- {row['combination']} — оценка {row['final_score']} / 100, ниво: {row['band']}"
        )

    (reports_dir / "v60_ticket_builder_2_polish_export_summary.md").write_text(
        "\n".join(markdown_lines) + "\n",
        encoding="utf-8",
    )

    print("V60_STATUS ticket_builder_2_polish_export_completed")
    print("DATASET_DRAWS", result["total_draws"])
    print("SELECTED_COUNT", result["selected_count"])
    print("AVERAGE_FINAL_SCORE", result["average_final_score"])
    print("EXPORT_ROWS", len(df))


if __name__ == "__main__":
    main()

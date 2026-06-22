from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v55_number_profile_engine import (
    build_number_profiles,
    export_number_profiles,
    load_draw_events,
)



def main() -> None:
    models_dir = ROOT / "models" / "v55"
    reports_dir = ROOT / "reports"

    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    events = load_draw_events()
    profiles = build_number_profiles(events)

    export_number_profiles(
        profiles,
        reports_dir / "v55_number_profiles.csv",
        reports_dir / "v55_number_profiles.json",
    )

    top_by_score = sorted(profiles, key=lambda item: item["profile_score"], reverse=True)[:10]
    top_overdue = sorted(profiles, key=lambda item: item["draws_since_last_seen"], reverse=True)[:10]

    manifest = {
        "module": "number_profile_center",
        "version": "v55",
        "user_facing_name_bg": "Профил на число",
        "total_draws": len(events),
        "numbers_profiled": len(profiles),
        "data_path": str(events[0].get("data_path", "")) if events else "",
        "purpose_bg": (
            "Създава статистически профил за всяко число от 1 до 49: честота, последна поява, "
            "интервали, скорошна активност и участие в двойки/тройки."
        ),
        "not_a_prediction_bg": (
            "Модулът не предсказва печеливши числа и не гарантира печалба. "
            "Той анализира само историческото поведение на числата."
        ),
        "metrics": [
            "appearances",
            "expected_appearances",
            "appearance_vs_expected_ratio",
            "draw_frequency_pct",
            "draws_since_last_seen",
            "average_interval",
            "median_interval",
            "max_interval",
            "recent_50",
            "recent_100",
            "recent_250",
            "recent_500",
            "interval_stability_score",
            "top_pairs",
            "top_triples",
            "profile_score",
        ],
    }

    summary = {
        "status": "completed",
        "module": "Number Profile Center",
        "version": "v55",
        "total_draws": len(events),
        "numbers_profiled": len(profiles),
        "top_by_score": [
            {
                "number": item["number"],
                "profile_score": item["profile_score"],
                "status": item["status"],
                "appearances": item["appearances"],
                "draws_since_last_seen": item["draws_since_last_seen"],
            }
            for item in top_by_score
        ],
        "top_overdue": [
            {
                "number": item["number"],
                "draws_since_last_seen": item["draws_since_last_seen"],
                "average_interval": item["average_interval"],
                "status": item["status"],
            }
            for item in top_overdue
        ],
        "safety_bg": (
            "Резултатът е исторически статистически профил, не обещание за бъдещо теглене."
        ),
    }

    (models_dir / "v55_number_profile_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (reports_dir / "v55_number_profile_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    markdown_lines = [
        "# V55 Number Profile Center",
        "",
        "## Цел",
        "",
        "Този модул изгражда профил за всяко число от 1 до 49.",
        "",
        "## Какво измерва",
        "",
        "- историческа честота;",
        "- очаквани срещу реални появи;",
        "- последна поява;",
        "- брой тиражи от последната поява;",
        "- среден, медианен и максимален интервал;",
        "- скорошна активност в последните 50, 100, 250 и 500 тиража;",
        "- стабилност на интервалите;",
        "- най-чести двойки;",
        "- най-чести тройки;",
        "- обща профилна оценка.",
        "",
        "## Важно",
        "",
        "Това не е предсказание и не е гаранция за печалба. Модулът показва историческо поведение на числата.",
        "",
        f"Анализирани тиражи: **{len(events)}**",
        "",
        "## Топ числа по профилна оценка",
        "",
    ]

    for item in top_by_score:
        markdown_lines.append(
            f"- {item['number']} — оценка {item['profile_score']}, статус: {item['status']}"
        )

    markdown_lines.extend(["", "## Най-дълго непоявявали се числа", ""])

    for item in top_overdue:
        markdown_lines.append(
            f"- {item['number']} — {item['draws_since_last_seen']} тиража от последна поява"
        )

    (reports_dir / "v55_number_profile_summary.md").write_text(
        "\n".join(markdown_lines) + "\n",
        encoding="utf-8",
    )

    print("V55_STATUS v55_number_profile_center_completed")
    print("DATASET_DRAWS", len(events))
    print("NUMBER_PROFILES", len(profiles))


if __name__ == "__main__":
    main()

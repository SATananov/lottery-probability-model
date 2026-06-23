from __future__ import annotations

from pathlib import Path
import csv
import json
import math
from collections import defaultdict
from statistics import mean, pstdev

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v63"
HISTORY_PATH = REPORTS_DIR / "v62_model_performance_history.csv"

MODEL_LABELS = {
    "v41_latest_predictions": "v41 — последни прогнозни сигнали",
    "v42_combined_prediction": "v42 — комбиниран позитивен/негативен модел",
    "v44_1_final_ensemble_ticket": "v44.1 — финална обединена комбинация",
    "v45_final_prediction_tickets": "v45 — Prediction Dashboard Pro",
    "v50_pair_group_intelligence": "v50 — двойки и групи",
    "v51_ticket_portfolio_intelligence": "v51 — пакет от комбинации",
    "v57_hot_cold_stable": "v57 — горещи, студени и стабилни",
    "v58_smart_ensemble": "v58 — обединена оценка",
    "v59_smart_ticket_builder_2": "v59 — интелигентен генератор 2",
    "v61_latest_draw_signal_hits": "v61 — сигнали към последния тираж",
}


def as_int(value, default=0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(float(text))
    except (TypeError, ValueError):
        return default


def as_float(value, default=0.0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def read_csv_rows(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def reliability_status(score, tracked_draws):
    if tracked_draws < 3:
        return "предварителна оценка"
    if score >= 70:
        return "силна историческа надеждност"
    if score >= 50:
        return "средна историческа надеждност"
    if score >= 30:
        return "ниска историческа надеждност"
    return "много ниска историческа надеждност"


def score_model(values):
    tracked_draws = len(values)
    avg_hits = mean(values) if values else 0.0
    max_hits = max(values) if values else 0
    min_hits = min(values) if values else 0

    rate_1_plus = sum(1 for item in values if item >= 1) / tracked_draws if tracked_draws else 0.0
    rate_2_plus = sum(1 for item in values if item >= 2) / tracked_draws if tracked_draws else 0.0
    rate_3_plus = sum(1 for item in values if item >= 3) / tracked_draws if tracked_draws else 0.0
    rate_4_plus = sum(1 for item in values if item >= 4) / tracked_draws if tracked_draws else 0.0

    std_hits = pstdev(values) if tracked_draws > 1 else 0.0
    consistency_score = max(0.0, 100.0 - (std_hits * 25.0))

    # Balanced score: rewards average hits, repeatable 2+/3+ signals, and consistency.
    reliability = (
        (avg_hits / 6.0) * 45.0
        + rate_1_plus * 10.0
        + rate_2_plus * 20.0
        + rate_3_plus * 15.0
        + (consistency_score / 100.0) * 10.0
    )

    reliability = max(0.0, min(100.0, reliability))

    return {
        "tracked_draws": tracked_draws,
        "average_hits": round(avg_hits, 3),
        "max_hits": max_hits,
        "min_hits": min_hits,
        "std_hits": round(std_hits, 3),
        "hit_rate_1_plus": round(rate_1_plus * 100.0, 2),
        "hit_rate_2_plus": round(rate_2_plus * 100.0, 2),
        "hit_rate_3_plus": round(rate_3_plus * 100.0, 2),
        "hit_rate_4_plus": round(rate_4_plus * 100.0, 2),
        "consistency_score": round(consistency_score, 2),
        "reliability_score": round(reliability, 2),
        "status": reliability_status(reliability, tracked_draws),
    }


def build_model_reliability_dashboard():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    history = read_csv_rows(HISTORY_PATH)
    if not history:
        raise FileNotFoundError(
            "Missing or empty reports/v62_model_performance_history.csv. "
            "Run Step 62 first: python scripts/v62_build_model_performance_tracker.py"
        )

    by_model = defaultdict(list)
    draw_keys = set()

    for row in history:
        model_name = str(row.get("model_name", "")).strip()
        if not model_name:
            continue
        hits = as_int(row.get("best_hits"), 0)
        by_model[model_name].append(hits)

        draw_key = str(row.get("draw_key", "")).strip()
        if draw_key:
            draw_keys.add(draw_key)

    rows = []
    for model_name, hits in by_model.items():
        metrics = score_model(hits)
        rows.append({
            "rank": 0,
            "model_name": model_name,
            "model_label": MODEL_LABELS.get(model_name, model_name),
            **metrics,
        })

    rows.sort(
        key=lambda row: (
            row["reliability_score"],
            row["average_hits"],
            row["hit_rate_2_plus"],
            row["max_hits"],
            row["tracked_draws"],
        ),
        reverse=True,
    )

    for index, row in enumerate(rows, start=1):
        row["rank"] = index

    fieldnames = [
        "rank",
        "model_name",
        "model_label",
        "tracked_draws",
        "average_hits",
        "max_hits",
        "min_hits",
        "std_hits",
        "hit_rate_1_plus",
        "hit_rate_2_plus",
        "hit_rate_3_plus",
        "hit_rate_4_plus",
        "consistency_score",
        "reliability_score",
        "status",
    ]

    write_csv(REPORTS_DIR / "v63_model_reliability_scores.csv", rows, fieldnames)

    best = rows[0] if rows else {}
    summary = {
        "step": "63",
        "name": "Model Reliability Dashboard",
        "history_rows": len(history),
        "tracked_draws": len(draw_keys),
        "models_ranked": len(rows),
        "best_model": best.get("model_name", ""),
        "best_model_label": best.get("model_label", ""),
        "best_reliability_score": best.get("reliability_score", 0),
        "best_average_hits": best.get("average_hits", 0),
        "best_max_hits": best.get("max_hits", 0),
        "generated_reports": [
            "reports/v63_model_reliability_summary.json",
            "reports/v63_model_reliability_summary.md",
            "reports/v63_model_reliability_scores.csv",
        ],
        "safe_note": "Historical model reliability dashboard only. This is not a prediction guarantee.",
    }

    write_json(REPORTS_DIR / "v63_model_reliability_summary.json", summary)
    write_json(MODELS_DIR / "v63_model_reliability_dashboard_model.json", {
        "summary": summary,
        "ranked_models": rows,
        "source": "reports/v62_model_performance_history.csv",
    })

    md = [
        "# Step 63 — Model Reliability Dashboard",
        "",
        "This report ranks model reliability based on historical post-draw performance history from Step 62.",
        "",
        "**Important:** This is historical analysis only. It is not a guarantee and not a promise of future lottery results.",
        "",
        f"History rows: **{summary['history_rows']}**",
        f"Tracked draws: **{summary['tracked_draws']}**",
        f"Models ranked: **{summary['models_ranked']}**",
        f"Best model: **{summary['best_model_label']}**",
        f"Best reliability score: **{summary['best_reliability_score']}%**",
        "",
        "## Ranked models",
        "",
        "| Rank | Model | Tracked draws | Avg hits | Max hits | 2+ hit rate | 3+ hit rate | Reliability | Status |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    for row in rows:
        md.append(
            f"| {row['rank']} | {row['model_label']} | {row['tracked_draws']} | "
            f"{row['average_hits']} | {row['max_hits']} | {row['hit_rate_2_plus']}% | "
            f"{row['hit_rate_3_plus']}% | {row['reliability_score']}% | {row['status']} |"
        )

    (REPORTS_DIR / "v63_model_reliability_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    return summary


if __name__ == "__main__":
    result = build_model_reliability_dashboard()
    print("STEP63_OK")
    print("HISTORY_ROWS", result["history_rows"])
    print("TRACKED_DRAWS", result["tracked_draws"])
    print("MODELS_RANKED", result["models_ranked"])
    print("BEST_MODEL", result["best_model_label"])
    print("BEST_SCORE", result["best_reliability_score"])

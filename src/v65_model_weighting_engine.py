from __future__ import annotations

from pathlib import Path
import csv
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v65"
SOURCE_PATH = REPORTS_DIR / "v63_model_reliability_scores.csv"

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


def as_float(value, default=0.0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def as_int(value, default=0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(float(text))
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


def confidence_factor(tracked_draws):
    if tracked_draws <= 0:
        return 0.20

    # Slow trust ramp: early post-draw history remains useful but explicitly preliminary.
    return round(max(0.25, min(1.0, tracked_draws / 10.0)), 3)


def weight_status(weight_percent, adjusted_score, tracked_draws):
    prefix = "предварителен " if tracked_draws < 3 else ""

    if adjusted_score <= 0 or weight_percent <= 0:
        return prefix + "без активен сигнал"
    if weight_percent >= 25:
        return prefix + "водещ адаптивен сигнал"
    if weight_percent >= 15:
        return prefix + "силен адаптивен сигнал"
    if weight_percent >= 7:
        return prefix + "балансиран сигнал"
    if weight_percent >= 3:
        return prefix + "слаб сигнал за наблюдение"

    return prefix + "минимален сигнал"


def build_model_weighting_center():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    source_rows = read_csv_rows(SOURCE_PATH)
    if not source_rows:
        raise FileNotFoundError(
            "Missing or empty reports/v63_model_reliability_scores.csv. "
            "Run Step 63 first: python scripts/v63_build_model_reliability_dashboard.py"
        )

    prepared = []

    for source in source_rows:
        model_name = str(source.get("model_name", "")).strip()
        if not model_name:
            continue

        tracked_draws = as_int(source.get("tracked_draws"), 0)
        reliability = as_float(source.get("reliability_score"), 0.0)
        consistency = as_float(source.get("consistency_score"), 0.0)
        average_hits = as_float(source.get("average_hits"), 0.0)
        hit_rate_2 = as_float(source.get("hit_rate_2_plus"), 0.0)
        hit_rate_3 = as_float(source.get("hit_rate_3_plus"), 0.0)
        max_hits = as_int(source.get("max_hits"), 0)

        avg_hit_score = max(0.0, min(100.0, (average_hits / 6.0) * 100.0))

        base_score = (
            reliability * 0.60
            + consistency * 0.15
            + avg_hit_score * 0.15
            + hit_rate_2 * 0.07
            + hit_rate_3 * 0.03
        )

        factor = confidence_factor(tracked_draws)
        adjusted_score = max(0.0, base_score * factor)

        prepared.append({
            "rank": 0,
            "model_name": model_name,
            "model_label": source.get("model_label") or MODEL_LABELS.get(model_name, model_name),
            "tracked_draws": tracked_draws,
            "average_hits": round(average_hits, 3),
            "max_hits": max_hits,
            "hit_rate_2_plus": round(hit_rate_2, 2),
            "hit_rate_3_plus": round(hit_rate_3, 2),
            "consistency_score": round(consistency, 2),
            "reliability_score": round(reliability, 2),
            "confidence_factor": factor,
            "base_score": round(base_score, 3),
            "adjusted_score": round(adjusted_score, 3),
            "adaptive_weight": 0.0,
            "adaptive_weight_percent": 0.0,
            "status": "",
            "source_status": source.get("status", ""),
        })

    prepared.sort(
        key=lambda row: (
            row["adjusted_score"],
            row["reliability_score"],
            row["average_hits"],
            row["max_hits"],
        ),
        reverse=True,
    )

    total_adjusted = sum(row["adjusted_score"] for row in prepared)

    if total_adjusted <= 0 and prepared:
        equal_weight = 1.0 / len(prepared)
        for row in prepared:
            row["adaptive_weight"] = round(equal_weight, 6)
            row["adaptive_weight_percent"] = round(equal_weight * 100.0, 2)
    else:
        for row in prepared:
            weight = row["adjusted_score"] / total_adjusted if total_adjusted else 0.0
            row["adaptive_weight"] = round(weight, 6)
            row["adaptive_weight_percent"] = round(weight * 100.0, 2)

    for index, row in enumerate(prepared, start=1):
        row["rank"] = index
        row["status"] = weight_status(
            row["adaptive_weight_percent"],
            row["adjusted_score"],
            row["tracked_draws"],
        )

    fieldnames = [
        "rank",
        "model_name",
        "model_label",
        "tracked_draws",
        "average_hits",
        "max_hits",
        "hit_rate_2_plus",
        "hit_rate_3_plus",
        "consistency_score",
        "reliability_score",
        "confidence_factor",
        "base_score",
        "adjusted_score",
        "adaptive_weight",
        "adaptive_weight_percent",
        "status",
        "source_status",
    ]

    weights_path = REPORTS_DIR / "v65_model_weights.csv"
    write_csv(weights_path, prepared, fieldnames)

    top = prepared[0] if prepared else {}
    tracked_values = [row["tracked_draws"] for row in prepared]

    min_tracked = min(tracked_values) if tracked_values else 0
    max_tracked = max(tracked_values) if tracked_values else 0
    total_weight = round(sum(row["adaptive_weight"] for row in prepared), 6)

    summary = {
        "step": "65",
        "name": "Adaptive Model Weighting",
        "source": "reports/v63_model_reliability_scores.csv",
        "models_weighted": len(prepared),
        "min_tracked_draws": min_tracked,
        "max_tracked_draws": max_tracked,
        "top_model": top.get("model_name", ""),
        "top_model_label": top.get("model_label", ""),
        "top_adaptive_weight_percent": top.get("adaptive_weight_percent", 0.0),
        "top_reliability_score": top.get("reliability_score", 0.0),
        "total_weight": total_weight,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_reports": [
            "reports/v65_model_weighting_summary.json",
            "reports/v65_model_weighting_summary.md",
            "reports/v65_model_weights.csv",
            "models/v65/v65_model_weighting_center_model.json",
        ],
        "safe_note": "Adaptive weighting is a statistical signal-management layer. It is not a гаранция за печалба or a promise of future lottery results.",
    }

    write_json(REPORTS_DIR / "v65_model_weighting_summary.json", summary)
    write_json(MODELS_DIR / "v65_model_weighting_center_model.json", {
        "summary": summary,
        "weights": prepared,
        "formula": {
            "base_score": "0.60*reliability + 0.15*consistency + 0.15*average_hit_score + 0.07*hit_rate_2_plus + 0.03*hit_rate_3_plus",
            "confidence_factor": "max(0.25, min(1.0, tracked_draws / 10.0)); 0.20 when no tracked draws",
            "adjusted_score": "base_score * confidence_factor",
            "adaptive_weight": "adjusted_score / sum(adjusted_scores)",
        },
        "source": "reports/v63_model_reliability_scores.csv",
    })

    md = [
        "# Step 65 — Adaptive Model Weighting",
        "",
        "This report converts Step 63 model reliability into adaptive model weights.",
        "",
        "**Important:** This is statistical signal management only. It is not a guarantee and not a promise of future lottery results.",
        "",
        f"Models weighted: **{summary['models_weighted']}**",
        f"Tracked draws range: **{summary['min_tracked_draws']}–{summary['max_tracked_draws']}**",
        f"Top adaptive model: **{summary['top_model_label']}**",
        f"Top adaptive weight: **{summary['top_adaptive_weight_percent']}%**",
        "",
        "## Formula",
        "",
        "The adaptive score combines historical reliability, consistency, average hits, 2+/3+ hit rates, and a slow confidence ramp based on the number of tracked post-draw events.",
        "",
        "## Adaptive weights",
        "",
        "| Rank | Model | Tracked draws | Reliability | Confidence | Adjusted score | Weight | Status |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
    ]

    for row in prepared:
        md.append(
            f"| {row['rank']} | {row['model_label']} | {row['tracked_draws']} | "
            f"{row['reliability_score']}% | {row['confidence_factor']} | "
            f"{row['adjusted_score']} | {row['adaptive_weight_percent']}% | {row['status']} |"
        )

    (REPORTS_DIR / "v65_model_weighting_summary.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    return summary


if __name__ == "__main__":
    result = build_model_weighting_center()
    print("STEP65_OK")
    print("MODELS_WEIGHTED", result["models_weighted"])
    print("TOP_MODEL", result["top_model_label"])
    print("TOP_WEIGHT", result["top_adaptive_weight_percent"])

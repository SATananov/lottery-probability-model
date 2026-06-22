from __future__ import annotations

from pathlib import Path
import csv
import json
from datetime import datetime
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "historical_draws.csv"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v62"

MODEL_SOURCES = [
    ("v41_latest_predictions", ROOT / "models" / "v41" / "v41_latest_predictions.json"),
    ("v42_combined_prediction", ROOT / "models" / "v42" / "v42_combined_prediction.json"),
    ("v44_1_final_ensemble_ticket", ROOT / "models" / "v44_1" / "v44_1_final_ensemble_ticket_prediction.json"),
    ("v45_final_prediction_tickets", ROOT / "models" / "v45" / "v45_final_prediction_tickets.json"),
    ("v50_pair_group_intelligence", ROOT / "models" / "v50" / "v50_pair_group_intelligence.json"),
    ("v51_ticket_portfolio_intelligence", ROOT / "models" / "v51" / "v51_ticket_portfolio_intelligence.json"),
    ("v57_hot_cold_stable", ROOT / "models" / "v57" / "v57_hot_cold_stable_model.json"),
    ("v58_smart_ensemble", ROOT / "models" / "v58" / "v58_smart_ensemble_model.json"),
    ("v59_smart_ticket_builder_2", ROOT / "models" / "v59" / "v59_smart_ticket_builder_2_model.json"),
    ("v61_latest_draw_signal_hits", ROOT / "reports" / "v61_model_signal_hits.csv"),
]

COMMON_NUMBER_KEYS = {
    "numbers",
    "ticket",
    "tickets",
    "combination",
    "combinations",
    "selected_numbers",
    "main_numbers",
    "predicted_numbers",
    "recommended_numbers",
    "final_numbers",
    "best_ticket",
    "generated_tickets",
    "portfolio",
    "candidates",
    "top_numbers",
    "latest_prediction",
}


def as_int(value):
    if value is None:
        return None
    try:
        text = str(value).strip()
        if not text:
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None


def normalize_ticket(values):
    numbers = []
    for value in values:
        n = as_int(value)
        if n is not None and 1 <= n <= 49 and n not in numbers:
            numbers.append(n)
    if len(numbers) >= 6:
        return sorted(numbers[:6])
    return None


def read_csv_rows(path):
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


def load_json(path):
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_draws():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing dataset: {DATA_PATH}")

    rows = read_csv_rows(DATA_PATH)
    if not rows:
        raise ValueError("Dataset is empty.")

    for row in rows:
        row["_numbers"] = [as_int(row.get(f"n{i}")) for i in range(1, 7)]

    latest = rows[-1]
    latest_numbers = latest["_numbers"]

    if any(n is None or n < 1 or n > 49 for n in latest_numbers):
        raise ValueError(f"Invalid latest draw numbers: {latest_numbers}")

    if len(set(latest_numbers)) != 6:
        raise ValueError(f"Duplicate numbers in latest draw: {latest_numbers}")

    return rows, latest, sorted(latest_numbers)


def collect_candidates_from_json(obj, results=None):
    if results is None:
        results = []

    if isinstance(obj, list):
        if obj and all(not isinstance(item, (dict, list)) for item in obj):
            ticket = normalize_ticket(obj)
            if ticket:
                results.append(ticket)

        for item in obj:
            collect_candidates_from_json(item, results)

    elif isinstance(obj, dict):
        for key in COMMON_NUMBER_KEYS:
            if key in obj:
                collect_candidates_from_json(obj[key], results)

        score_items = []
        for key, value in obj.items():
            number = as_int(key)
            if number is None or not (1 <= number <= 49):
                continue

            score = None
            if isinstance(value, (int, float)):
                score = float(value)
            elif isinstance(value, dict):
                for score_key in ("score", "final_score", "combined_score", "profile_score", "weight", "frequency", "count"):
                    if isinstance(value.get(score_key), (int, float)):
                        score = float(value[score_key])
                        break

            if score is not None:
                score_items.append((number, score))

        if len(score_items) >= 6:
            best = sorted(score_items, key=lambda item: item[1], reverse=True)[:6]
            results.append(sorted(number for number, _ in best))

        for value in obj.values():
            collect_candidates_from_json(value, results)

    return results


def collect_candidates_from_csv(path):
    rows = read_csv_rows(path)
    candidates = []

    number_columns = [f"n{i}" for i in range(1, 7)]
    if rows and all(col in rows[0] for col in number_columns):
        for row in rows:
            ticket = normalize_ticket([row.get(col) for col in number_columns])
            if ticket:
                candidates.append(ticket)

    for row in rows:
        for key in ("numbers", "ticket", "combination", "candidate", "best_ticket"):
            value = row.get(key)
            if not value:
                continue
            cleaned = (
                str(value)
                .replace("[", " ")
                .replace("]", " ")
                .replace("(", " ")
                .replace(")", " ")
                .replace(";", " ")
                .replace("|", " ")
                .replace(",", " ")
            )
            parts = cleaned.split()
            ticket = normalize_ticket(parts)
            if ticket:
                candidates.append(ticket)

    return candidates


def dedupe_candidates(candidates):
    unique = []
    seen = set()
    for ticket in candidates:
        normalized = tuple(sorted(ticket))
        if len(normalized) != 6:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(list(normalized))
    return unique


def load_candidates(path):
    if not path.exists():
        return []

    suffix = path.suffix.lower()

    if suffix == ".json":
        data = load_json(path)
        return dedupe_candidates(collect_candidates_from_json(data))

    if suffix == ".csv":
        return dedupe_candidates(collect_candidates_from_csv(path))

    return []


def evaluate_source(source_name, path, latest_numbers):
    candidates = load_candidates(path)

    if not candidates:
        return {
            "model_name": source_name,
            "source_file": str(path.relative_to(ROOT)) if path.exists() else str(path),
            "source_exists": path.exists(),
            "candidate_count": 0,
            "best_hits": 0,
            "best_candidate": "",
            "hit_numbers": "",
            "coverage_percent": 0.0,
            "status": "no_candidate_signal",
        }

    latest_set = set(latest_numbers)
    evaluated = []

    for ticket in candidates:
        hits = sorted(latest_set.intersection(ticket))
        evaluated.append({
            "candidate": ticket,
            "hits": len(hits),
            "hit_numbers": hits,
        })

    evaluated.sort(key=lambda item: (item["hits"], -sum(item["candidate"])), reverse=True)
    best = evaluated[0]

    return {
        "model_name": source_name,
        "source_file": str(path.relative_to(ROOT)),
        "source_exists": True,
        "candidate_count": len(candidates),
        "best_hits": best["hits"],
        "best_candidate": " ".join(str(n) for n in best["candidate"]),
        "hit_numbers": " ".join(str(n) for n in best["hit_numbers"]),
        "coverage_percent": round(best["hits"] / 6 * 100, 2),
        "status": "ok",
    }


def make_draw_key(latest):
    year = str(latest.get("year", "")).strip()
    draw_number = str(latest.get("draw_number") or latest.get("draw_no") or "").strip()
    draw_position = str(latest.get("draw_position") or latest.get("drawing_no") or "1").strip()
    date = str(latest.get("date") or "").strip()
    return f"{year}|{draw_number}|{draw_position}|{date}"


def update_history(latest, latest_numbers, performance_rows):
    history_path = REPORTS_DIR / "v62_model_performance_history.csv"
    draw_key = make_draw_key(latest)

    fieldnames = [
        "draw_key",
        "date",
        "year",
        "draw_number",
        "draw_position",
        "draw_numbers",
        "model_name",
        "candidate_count",
        "best_hits",
        "coverage_percent",
        "best_candidate",
        "hit_numbers",
        "status",
        "updated_at",
    ]

    existing = []
    if history_path.exists():
        existing = read_csv_rows(history_path)

    existing = [row for row in existing if row.get("draw_key") != draw_key]

    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    new_rows = []

    for row in performance_rows:
        new_rows.append({
            "draw_key": draw_key,
            "date": latest.get("date", ""),
            "year": latest.get("year", ""),
            "draw_number": latest.get("draw_number") or latest.get("draw_no") or "",
            "draw_position": latest.get("draw_position") or latest.get("drawing_no") or "1",
            "draw_numbers": " ".join(str(n) for n in latest_numbers),
            "model_name": row["model_name"],
            "candidate_count": row["candidate_count"],
            "best_hits": row["best_hits"],
            "coverage_percent": row["coverage_percent"],
            "best_candidate": row["best_candidate"],
            "hit_numbers": row["hit_numbers"],
            "status": row["status"],
            "updated_at": now,
        })

    merged = existing + new_rows
    write_csv(history_path, merged, fieldnames)
    return merged


def build_model_performance_tracker():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    draws, latest, latest_numbers = load_draws()

    performance_rows = []
    for source_name, path in MODEL_SOURCES:
        performance_rows.append(evaluate_source(source_name, path, latest_numbers))

    performance_rows.sort(key=lambda row: (row["best_hits"], row["candidate_count"]), reverse=True)

    latest_fieldnames = [
        "model_name",
        "source_file",
        "source_exists",
        "candidate_count",
        "best_hits",
        "coverage_percent",
        "best_candidate",
        "hit_numbers",
        "status",
    ]

    write_csv(REPORTS_DIR / "v62_latest_model_performance.csv", performance_rows, latest_fieldnames)
    history_rows = update_history(latest, latest_numbers, performance_rows)

    ok_rows = [row for row in performance_rows if row["status"] == "ok"]
    best_hits = max([row["best_hits"] for row in performance_rows], default=0)
    best_models = [row["model_name"] for row in performance_rows if row["best_hits"] == best_hits]
    avg_hits = round(mean([row["best_hits"] for row in ok_rows]), 3) if ok_rows else 0.0

    summary = {
        "step": "62",
        "name": "Model Performance Tracker",
        "total_draws": len(draws),
        "latest_draw": {
            "date": latest.get("date", ""),
            "year": latest.get("year", ""),
            "draw_number": latest.get("draw_number") or latest.get("draw_no") or "",
            "draw_position": latest.get("draw_position") or latest.get("drawing_no") or "1",
            "numbers": latest_numbers,
        },
        "models_evaluated": len(performance_rows),
        "models_with_candidate_signal": len(ok_rows),
        "best_hits": best_hits,
        "best_models": best_models,
        "average_best_hits": avg_hits,
        "history_rows": len(history_rows),
        "generated_reports": [
            "reports/v62_model_performance_summary.json",
            "reports/v62_model_performance_summary.md",
            "reports/v62_latest_model_performance.csv",
            "reports/v62_model_performance_history.csv",
        ],
        "safe_note": "Historical post-draw model performance tracking only. This is not a prediction guarantee.",
    }

    model_artifact = {
        "summary": summary,
        "latest_performance": performance_rows,
        "model_sources": [
            {"name": name, "path": str(path.relative_to(ROOT)), "exists": path.exists()}
            for name, path in MODEL_SOURCES
        ],
    }

    write_json(MODELS_DIR / "v62_model_performance_tracker_model.json", model_artifact)
    write_json(REPORTS_DIR / "v62_model_performance_summary.json", summary)

    md = [
        "# Step 62 — Model Performance Tracker",
        "",
        "This report tracks how current model signals compare against the latest real draw.",
        "",
        "**Important:** This is historical post-draw analysis only. It is not a guarantee and not a promise of future lottery results.",
        "",
        f"Total draw events: **{len(draws)}**",
        f"Latest draw: **{summary['latest_draw']['date']} / {summary['latest_draw']['draw_number']}**",
        f"Latest numbers: **{' '.join(str(n) for n in latest_numbers)}**",
        f"Models evaluated: **{summary['models_evaluated']}**",
        f"Models with candidate signal: **{summary['models_with_candidate_signal']}**",
        f"Best hits: **{best_hits}/6**",
        f"Average best hits: **{avg_hits}**",
        "",
        "## Best models for the latest draw",
        "",
    ]

    for model in best_models:
        md.append(f"- {model}")

    md.extend([
        "",
        "## Latest model performance",
        "",
        "| Model | Candidate count | Best hits | Hit numbers | Best candidate |",
        "|---|---:|---:|---|---|",
    ])

    for row in performance_rows:
        md.append(
            f"| {row['model_name']} | {row['candidate_count']} | {row['best_hits']} | "
            f"{row['hit_numbers']} | {row['best_candidate']} |"
        )

    (REPORTS_DIR / "v62_model_performance_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    return summary


if __name__ == "__main__":
    result = build_model_performance_tracker()
    print("STEP62_OK")
    print("TOTAL_DRAWS", result["total_draws"])
    print("LATEST_DRAW", result["latest_draw"])
    print("MODELS_EVALUATED", result["models_evaluated"])
    print("BEST_HITS", result["best_hits"])

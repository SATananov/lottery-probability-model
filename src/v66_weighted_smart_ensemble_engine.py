from __future__ import annotations

from pathlib import Path
import csv
import json
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
V66_MODELS_DIR = MODELS_DIR / "v66"

WEIGHTS_PATH = REPORTS_DIR / "v65_model_weights.csv"

NUMBER_MIN = 1
NUMBER_MAX = 49

# Post-draw result/analyzer models can help measure reliability, but should not be used
# directly as future number score sources.
EXCLUDED_SCORE_SOURCE_MODELS = {
    "v61_latest_draw_signal_hits",
}

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
}

SOURCE_HINTS = {
    "v41_latest_predictions": [
        "models/v41/v41_latest_predictions.json",
        "models/v41/v41_frequency_main_numbers_model.json",
        "models/v41/v41_recency_main_numbers_model.json",
    ],
    "v42_combined_prediction": [
        "reports/v42_combined_number_scores.csv",
        "models/v42/v42_combined_number_scores.json",
        "models/v42/v42_combined_prediction.json",
    ],
    "v44_1_final_ensemble_ticket": [
        "reports/v44_1_final_ensemble_number_scores.csv",
        "reports/v44_1_final_ensemble_ticket_summary.json",
        "models/v44_1/v44_1_final_ensemble_number_scores.json",
        "models/v44_1/v44_1_final_ensemble_ticket_prediction.json",
    ],
    "v45_final_prediction_tickets": [
        "reports/v45_final_prediction_tickets.csv",
        "models/v45/v45_final_prediction_tickets.json",
        "models/v45/v45_prediction_dashboard_model.json",
    ],
    "v50_pair_group_intelligence": [
        "reports/v50_pair_group_intelligence_scores.csv",
        "models/v50/v50_pair_group_intelligence_model.json",
    ],
    "v51_ticket_portfolio_intelligence": [
        "reports/v51_ticket_portfolio_intelligence_scores.csv",
        "models/v51/v51_ticket_portfolio_intelligence_model.json",
    ],
    "v57_hot_cold_stable": [
        "reports/v57_hot_cold_stable_scores.csv",
        "models/v57/v57_hot_cold_stable_model.json",
    ],
    "v58_smart_ensemble": [
        "reports/v58_smart_ensemble_scores.csv",
        "reports/v58_smart_ensemble_number_scores.csv",
        "reports/v58_smart_ensemble_score_summary.json",
        "models/v58/v58_smart_ensemble_number_scores.json",
        "models/v58/v58_smart_ensemble_score_model.json",
    ],
    "v59_smart_ticket_builder_2": [
        "reports/v59_smart_ticket_builder_2_scores.csv",
        "reports/v59_smart_ticket_builder_2_summary.json",
        "models/v59/v59_smart_ticket_builder_2_model.json",
        "models/v59/v59_smart_ticket_builder_2_prediction.json",
    ],
}

NUMBER_FIELDS = [
    "number",
    "main_number",
    "ball",
    "num",
    "value",
    "число",
    "номер",
]

SCORE_FIELDS = [
    "weighted_score",
    "smart_ensemble_score",
    "ensemble_score",
    "final_score",
    "combined_score",
    "total_score",
    "normalized_score",
    "score",
    "signal_score",
    "model_score",
    "weight",
    "frequency",
    "count",
    "hits",
]


def as_float(value, default=0.0):
    try:
        text = str(value).strip()
        if not text:
            return default
        text = text.replace("%", "").replace(",", ".")
        return float(text)
    except (TypeError, ValueError):
        return default


def as_int(value, default=None):
    try:
        text = str(value).strip()
        if not text:
            return default
        number = int(float(text.replace(",", ".")))
        return number
    except (TypeError, ValueError):
        return default


def is_valid_number(value):
    number = as_int(value, None)
    return number if number is not None and NUMBER_MIN <= number <= NUMBER_MAX else None


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


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def version_prefixes(model_name):
    parts = model_name.split("_")
    if not parts:
        return []

    prefixes = []
    if len(parts) >= 2 and parts[0].startswith("v") and parts[1].isdigit():
        prefixes.append(parts[0] + "_" + parts[1])

    prefixes.append(parts[0])

    unique = []
    for prefix in prefixes:
        if prefix not in unique:
            unique.append(prefix)

    return unique


def candidate_paths_for_model(model_name):
    candidates = []

    for rel in SOURCE_HINTS.get(model_name, []):
        path = ROOT / rel
        if path.exists():
            candidates.append(path)

    for prefix in version_prefixes(model_name):
        for path in REPORTS_DIR.glob(f"{prefix}*.csv"):
            candidates.append(path)
        for path in REPORTS_DIR.glob(f"{prefix}*.json"):
            candidates.append(path)
        model_dir = MODELS_DIR / prefix
        if model_dir.exists():
            candidates.extend(model_dir.glob("*.json"))

    clean = []
    seen = set()

    for path in candidates:
        if not path.exists() or path.is_dir():
            continue
        if path.suffix.lower() not in {".csv", ".json"}:
            continue
        if "v65" in path.as_posix() or "v66" in path.as_posix():
            continue
        if path not in seen:
            seen.add(path)
            clean.append(path)

    return clean


def add_score(scores, number, score):
    number = is_valid_number(number)
    if number is None:
        return

    score_value = as_float(score, 1.0)
    if score_value <= 0:
        score_value = 1.0

    scores[number] = scores.get(number, 0.0) + score_value


def first_present(row, keys):
    lower = {str(k).strip().lower(): k for k in row.keys()}

    for key in keys:
        actual = lower.get(key.lower())
        if actual is not None:
            value = row.get(actual)
            if value not in (None, ""):
                return value

    return None


def parse_numbers_from_text(value):
    if value is None:
        return []

    text = str(value)
    values = []
    for match in re.findall(r"\b\d{1,2}\b", text):
        number = is_valid_number(match)
        if number is not None:
            values.append(number)

    return values


def extract_score_from_dict(obj):
    for field in SCORE_FIELDS:
        for key, value in obj.items():
            if str(key).strip().lower() == field.lower():
                parsed = as_float(value, None)
                if parsed is not None:
                    return parsed

    return 1.0


def parse_csv_scores(path):
    scores = {}

    try:
        rows = read_csv_rows(path)
    except UnicodeDecodeError:
        return scores

    for row in rows:
        number = first_present(row, NUMBER_FIELDS)
        score = first_present(row, SCORE_FIELDS)

        if number is not None:
            add_score(scores, number, score if score is not None else 1.0)
            continue

        # Ticket-style rows: n1..n6, number_1..number_6, ball_1..ball_6, etc.
        row_numbers = []
        for key, value in row.items():
            key_lower = str(key).strip().lower()
            if (
                re.fullmatch(r"n[1-6]", key_lower)
                or re.fullmatch(r"number[_ ]?[1-6]", key_lower)
                or re.fullmatch(r"ball[_ ]?[1-6]", key_lower)
                or key_lower in {"numbers", "ticket", "combination", "комбинация", "числа"}
            ):
                row_numbers.extend(parse_numbers_from_text(value))

        row_numbers = sorted(set(row_numbers))
        if len(row_numbers) >= 6:
            for item in row_numbers[:6]:
                add_score(scores, item, 1.0)

    return scores


def parse_json_object(obj, scores):
    if isinstance(obj, dict):
        number = first_present(obj, NUMBER_FIELDS)

        if number is not None:
            add_score(scores, number, extract_score_from_dict(obj))

        for key, value in obj.items():
            key_number = is_valid_number(key)
            if key_number is not None:
                if isinstance(value, (int, float, str)):
                    add_score(scores, key_number, value)
                elif isinstance(value, dict):
                    add_score(scores, key_number, extract_score_from_dict(value))
                    parse_json_object(value, scores)
                elif isinstance(value, list):
                    add_score(scores, key_number, 1.0)
                    parse_json_object(value, scores)
                continue

            parse_json_object(value, scores)

    elif isinstance(obj, list):
        if 6 <= len(obj) <= 12:
            numbers = [is_valid_number(item) for item in obj]
            numbers = [item for item in numbers if item is not None]
            if len(set(numbers)) >= 6:
                for item in sorted(set(numbers))[:6]:
                    add_score(scores, item, 1.0)

        for item in obj:
            parse_json_object(item, scores)


def parse_json_scores(path):
    scores = {}

    try:
        obj = read_json(path)
    except Exception:
        return scores

    parse_json_object(obj, scores)
    return scores


def normalize_scores(scores):
    cleaned = {
        int(number): max(0.0, float(score))
        for number, score in scores.items()
        if is_valid_number(number) is not None
    }

    if not cleaned:
        return {}

    min_score = min(cleaned.values())
    max_score = max(cleaned.values())

    if max_score <= 0:
        return {number: 0.0 for number in cleaned}

    if max_score == min_score:
        return {number: 100.0 if score > 0 else 0.0 for number, score in cleaned.items()}

    return {
        number: round(((score - min_score) / (max_score - min_score)) * 100.0, 6)
        for number, score in cleaned.items()
    }


def load_model_source_scores(model_name):
    merged = {}
    files_used = []

    for path in candidate_paths_for_model(model_name):
        if path.suffix.lower() == ".csv":
            scores = parse_csv_scores(path)
        elif path.suffix.lower() == ".json":
            scores = parse_json_scores(path)
        else:
            scores = {}

        if not scores:
            continue

        files_used.append(path.relative_to(ROOT).as_posix())
        for number, score in normalize_scores(scores).items():
            merged[number] = max(merged.get(number, 0.0), score)

    return normalize_scores(merged), files_used


def source_status(source_count, weighted_score_percent):
    if source_count >= 4 and weighted_score_percent >= 75:
        return "водещ претеглен сигнал"
    if source_count >= 3 and weighted_score_percent >= 60:
        return "силен потвърден сигнал"
    if source_count >= 2 and weighted_score_percent >= 45:
        return "балансиран сигнал"
    if weighted_score_percent >= 25:
        return "сигнал за наблюдение"

    return "слаб/резервен сигнал"


def create_reference_tickets(score_rows):
    numbers = [row["number"] for row in score_rows[:24]]
    if len(numbers) < 6:
        return []

    patterns = [
        [0, 1, 2, 3, 4, 5],
        [1, 4, 7, 10, 13, 16],
        [2, 5, 8, 11, 14, 17],
        [3, 6, 9, 12, 15, 18],
    ]

    tickets = []
    used_tickets = set()

    for index, pattern in enumerate(patterns, start=1):
        selected = []

        for position in pattern:
            if position < len(numbers):
                selected.append(numbers[position])

        # Fill defensively if a pattern cannot produce 6 unique numbers.
        for number in numbers:
            if len(set(selected)) >= 6:
                break
            if number not in selected:
                selected.append(number)

        ticket = tuple(sorted(set(selected))[:6])
        if len(ticket) == 6 and ticket not in used_tickets:
            used_tickets.add(ticket)
            tickets.append({
                "ticket_id": index,
                "numbers": list(ticket),
                "note": "статистическа референтна комбинация, не гаранция",
            })

    return tickets


def build_weighted_smart_ensemble():
    V66_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    weight_rows = read_csv_rows(WEIGHTS_PATH)
    if not weight_rows:
        raise FileNotFoundError(
            "Missing reports/v65_model_weights.csv. Run Step 65 first: "
            "python scripts/v65_build_model_weighting_center.py"
        )

    source_models = []
    skipped_models = []

    for row in weight_rows:
        model_name = str(row.get("model_name", "")).strip()
        if not model_name:
            continue

        original_weight = as_float(row.get("adaptive_weight"), 0.0)

        if model_name in EXCLUDED_SCORE_SOURCE_MODELS:
            skipped_models.append({
                "model_name": model_name,
                "reason": "post-draw analyzer; used for reliability context, not direct score source",
            })
            continue

        source_scores, files_used = load_model_source_scores(model_name)

        if not source_scores:
            skipped_models.append({
                "model_name": model_name,
                "reason": "no parseable score source files found",
            })
            continue

        source_models.append({
            "model_name": model_name,
            "model_label": row.get("model_label") or MODEL_LABELS.get(model_name, model_name),
            "original_adaptive_weight": original_weight,
            "source_scores": source_scores,
            "source_files": files_used,
        })

    if not source_models:
        raise RuntimeError("No usable претеглена оценка sources were found for Step 66.")

    usable_weight_sum = sum(item["original_adaptive_weight"] for item in source_models)

    if usable_weight_sum <= 0:
        equal = 1.0 / len(source_models)
        for item in source_models:
            item["used_weight"] = equal
    else:
        for item in source_models:
            item["used_weight"] = item["original_adaptive_weight"] / usable_weight_sum

    contributions = {
        number: {
            "raw_weighted_score": 0.0,
            "source_count": 0,
            "sources": [],
        }
        for number in range(NUMBER_MIN, NUMBER_MAX + 1)
    }

    for source in source_models:
        model_label = source["model_label"]
        used_weight = source["used_weight"]

        for number in range(NUMBER_MIN, NUMBER_MAX + 1):
            source_score = source["source_scores"].get(number, 0.0)
            if source_score <= 0:
                continue

            contribution = source_score * used_weight
            contributions[number]["raw_weighted_score"] += contribution
            contributions[number]["source_count"] += 1
            contributions[number]["sources"].append({
                "model_name": source["model_name"],
                "model_label": model_label,
                "source_score": round(source_score, 3),
                "used_weight": round(used_weight, 6),
                "contribution": round(contribution, 6),
            })

    max_score = max(item["raw_weighted_score"] for item in contributions.values()) or 1.0

    score_rows = []

    for number, data in contributions.items():
        weighted_score_percent = (data["raw_weighted_score"] / max_score) * 100.0

        top_sources = sorted(
            data["sources"],
            key=lambda item: item["contribution"],
            reverse=True,
        )[:3]

        score_rows.append({
            "rank": 0,
            "number": number,
            "weighted_score": round(data["raw_weighted_score"], 6),
            "weighted_score_percent": round(weighted_score_percent, 3),
            "source_count": data["source_count"],
            "top_sources": " | ".join(item["model_label"] for item in top_sources),
            "status": source_status(data["source_count"], weighted_score_percent),
        })

    score_rows.sort(
        key=lambda row: (
            row["weighted_score_percent"],
            row["source_count"],
            row["number"],
        ),
        reverse=True,
    )

    for index, row in enumerate(score_rows, start=1):
        row["rank"] = index

    tickets = create_reference_tickets(score_rows)

    fieldnames = [
        "rank",
        "number",
        "weighted_score",
        "weighted_score_percent",
        "source_count",
        "top_sources",
        "status",
    ]

    write_csv(REPORTS_DIR / "v66_weighted_smart_ensemble_scores.csv", score_rows, fieldnames)

    top = score_rows[0] if score_rows else {}

    summary = {
        "step": "66",
        "name": "Претеглена обединена оценка",
        "source_weights": "reports/v65_model_weights.csv",
        "numbers_scored": len(score_rows),
        "sources_used": len(source_models),
        "skipped_sources": skipped_models,
        "top_number": top.get("number"),
        "top_weighted_score_percent": top.get("weighted_score_percent", 0.0),
        "top_number_status": top.get("status", ""),
        "reference_tickets_count": len(tickets),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_reports": [
            "reports/v66_weighted_smart_ensemble_summary.json",
            "reports/v66_weighted_smart_ensemble_summary.md",
            "reports/v66_weighted_smart_ensemble_scores.csv",
            "models/v66/v66_weighted_smart_ensemble_model.json",
        ],
        "safe_note": "This is a weighted statistical ensemble layer. It is not a гаранция за печалба or a promise of future lottery results.",
    }

    model_payload = {
        "summary": summary,
        "source_models": [
            {
                "model_name": item["model_name"],
                "model_label": item["model_label"],
                "original_adaptive_weight": round(item["original_adaptive_weight"], 6),
                "used_weight": round(item["used_weight"], 6),
                "source_files": item["source_files"],
            }
            for item in source_models
        ],
        "scores": score_rows,
        "reference_tickets": tickets,
        "formula": {
            "source_score": "Each available model score source is normalized to 0..100.",
            "used_weight": "Step 65 adaptive weights are renormalized across score sources that are actually available for Step 66.",
            "weighted_score": "sum(normalized_source_score * used_weight)",
            "weighted_score_percent": "weighted_score normalized against the top weighted number.",
        },
        "safe_note": summary["safe_note"],
    }

    write_json(REPORTS_DIR / "v66_weighted_smart_ensemble_summary.json", summary)
    write_json(V66_MODELS_DIR / "v66_weighted_smart_ensemble_model.json", model_payload)

    md = [
        "# Step 66 — Претеглена обединена оценка",
        "",
        "This report combines available number-score sources with Step 65 adaptive model weights.",
        "",
        "**Important:** This is statistical signal management only. It is not a guarantee and not a promise of future lottery results.",
        "",
        f"Sources used: **{summary['sources_used']}**",
        f"Numbers scored: **{summary['numbers_scored']}**",
        f"Top weighted number: **{summary['top_number']}**",
        f"Top претеглена оценка: **{summary['top_weighted_score_percent']}%**",
        "",
        "## Sources used",
        "",
        "| Model | Original Step 65 weight | Used Step 66 weight | Files |",
        "|---|---:|---:|---|",
    ]

    for item in model_payload["source_models"]:
        files = "<br>".join(item["source_files"])
        md.append(
            f"| {item['model_label']} | {item['original_adaptive_weight']:.6f} | "
            f"{item['used_weight']:.6f} | {files} |"
        )

    md.extend([
        "",
        "## Top weighted numbers",
        "",
        "| Rank | Number | Претеглена оценка % | Source count | Status |",
        "|---:|---:|---:|---:|---|",
    ])

    for row in score_rows[:15]:
        md.append(
            f"| {row['rank']} | {row['number']} | {row['weighted_score_percent']}% | "
            f"{row['source_count']} | {row['status']} |"
        )

    if tickets:
        md.extend([
            "",
            "## Reference combinations",
            "",
            "These are референтни комбинации built from weighted statistical signals. They are not гаранция за печалбаs.",
            "",
        ])
        for ticket in tickets:
            md.append(f"- Ticket {ticket['ticket_id']}: {', '.join(str(n) for n in ticket['numbers'])}")

    if skipped_models:
        md.extend([
            "",
            "## Skipped sources",
            "",
        ])
        for item in skipped_models:
            md.append(f"- {item['model_name']}: {item['reason']}")

    (REPORTS_DIR / "v66_weighted_smart_ensemble_summary.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    return summary


if __name__ == "__main__":
    result = build_weighted_smart_ensemble()
    print("STEP66_OK")
    print("SOURCES_USED", result["sources_used"])
    print("NUMBERS_SCORED", result["numbers_scored"])
    print("TOP_NUMBER", result["top_number"])
    print("TOP_SCORE", result["top_weighted_score_percent"])

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT / "data" / "historical_draws.csv"

V42_SCORES_PATH = ROOT / "models" / "v42" / "v42_positive_negative_number_scores.json"
V42_PREDICTION_PATH = ROOT / "models" / "v42" / "v42_combined_prediction.json"

V43_SCORES_PATH = ROOT / "models" / "v43_1" / "v43_1_interval_rhythm_refined_scores.json"
V43_PREDICTION_PATH = ROOT / "models" / "v43_1" / "v43_1_interval_rhythm_refined_prediction.json"

V41_PREDICTION_PATH = ROOT / "models" / "v41" / "v41_latest_predictions.json"

SCORES_JSON = ROOT / "models" / "v44_1" / "v44_1_final_ensemble_number_scores.json"
TICKET_JSON = ROOT / "models" / "v44_1" / "v44_1_final_ensemble_ticket_prediction.json"
SUMMARY_JSON = ROOT / "reports" / "v44_1_final_ensemble_ticket_summary.json"
SCORES_CSV = ROOT / "reports" / "v44_1_final_ensemble_number_scores.csv"
SUMMARY_MD = ROOT / "reports" / "v44_1_final_ensemble_ticket_summary.md"


def bg(hex_text: str) -> str:
    return bytes.fromhex(hex_text).decode("utf-8")


def bounded(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_round(value: Any, digits: int = 3) -> float:
    return round(safe_float(value), digits)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [
            row
            for row in csv.DictReader(f)
            if any((value or "").strip() for value in row.values())
        ]


def parse_valid_events(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    number_cols = [f"n{i}" for i in range(1, 7)]

    if not rows or not all(col in rows[0] for col in number_cols):
        raise ValueError("Expected historical_draws.csv columns n1..n6.")

    events: list[dict[str, Any]] = []

    for raw_index, row in enumerate(rows, start=1):
        numbers = []

        for col in number_cols:
            try:
                numbers.append(int((row.get(col) or "").strip()))
            except ValueError:
                numbers.append(-1)

        if len(numbers) != 6:
            continue
        if len(set(numbers)) != 6:
            continue
        if not all(1 <= number <= 49 for number in numbers):
            continue

        events.append(
            {
                "event_index": len(events) + 1,
                "raw_index": raw_index,
                "numbers": sorted(numbers),
            }
        )

    return events


def historical_rules_scores(events: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    total_draws = len(events)
    expected_hits = total_draws * 6 / 49
    expected_last_250 = 250 * 6 / 49
    expected_last_100 = 100 * 6 / 49

    positions_by_number: dict[int, list[int]] = {number: [] for number in range(1, 50)}

    for event in events:
        event_index = int(event["event_index"])
        for number in event["numbers"]:
            positions_by_number[number].append(event_index)

    result: dict[int, dict[str, Any]] = {}

    for number in range(1, 50):
        positions = positions_by_number[number]
        total_hits = len(positions)
        last_seen = positions[-1] if positions else None
        current_gap = total_draws - last_seen if last_seen is not None else total_draws

        hits_last_100 = sum(1 for position in positions if position > total_draws - 100)
        hits_last_250 = sum(1 for position in positions if position > total_draws - 250)

        frequency_ratio = total_hits / expected_hits if expected_hits else 0.0
        recent_250_ratio = hits_last_250 / expected_last_250 if expected_last_250 else 0.0
        recent_100_ratio = hits_last_100 / expected_last_100 if expected_last_100 else 0.0

        frequency_score = bounded(50 + (frequency_ratio - 1) * 100)
        recent_250_score = bounded(50 + (recent_250_ratio - 1) * 80)
        recent_100_score = bounded(50 + (recent_100_ratio - 1) * 60)

        if current_gap <= 1:
            gap_score = 35
        elif current_gap <= 5:
            gap_score = 55
        elif current_gap <= 14:
            gap_score = 70
        elif current_gap <= 30:
            gap_score = 78
        else:
            gap_score = 62

        rules_score = bounded(
            0.35 * frequency_score
            + 0.25 * recent_250_score
            + 0.20 * recent_100_score
            + 0.20 * gap_score
        )

        result[number] = {
            "total_hits": total_hits,
            "current_gap": current_gap,
            "hits_last_100": hits_last_100,
            "hits_last_250": hits_last_250,
            "frequency_score": round(frequency_score, 3),
            "recent_100_score": round(recent_100_score, 3),
            "recent_250_score": round(recent_250_score, 3),
            "rules_score": round(rules_score, 3),
        }

    return result


def map_by_number(payload: dict[str, Any], key: str = "numbers") -> dict[int, dict[str, Any]]:
    rows = payload.get(key, [])
    result: dict[int, dict[str, Any]] = {}

    if not isinstance(rows, list):
        return result

    for row in rows:
        if not isinstance(row, dict):
            continue

        try:
            number = int(row.get("number"))
        except (TypeError, ValueError):
            continue

        if 1 <= number <= 49:
            result[number] = row

    return result


def extract_small_number_lists(value: Any, container_key: str = "") -> list[list[int]]:
    found: list[list[int]] = []

    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            should_scan = any(
                marker in key_text
                for marker in [
                    "prediction",
                    "predict",
                    "number",
                    "numbers",
                    "selected",
                    "suggest",
                    "recommend",
                    "top",
                    "final",
                    "combined",
                    "frequency",
                    "recency",
                ]
            )

            if should_scan or isinstance(child, (dict, list)):
                found.extend(extract_small_number_lists(child, key_text))

    elif isinstance(value, list):
        int_values = []
        all_int_like = True

        for item in value:
            if isinstance(item, bool):
                all_int_like = False
                break

            try:
                number = int(item)
            except (TypeError, ValueError):
                all_int_like = False
                break

            int_values.append(number)

        if all_int_like and 1 <= len(int_values) <= 12 and all(1 <= number <= 49 for number in int_values):
            found.append(int_values)
        else:
            for item in value:
                found.extend(extract_small_number_lists(item, container_key))

    return found


def build_vote_score(number: int, lists: list[list[int]]) -> float:
    if not lists:
        return 0.0

    weighted_hits = 0.0

    for values in lists:
        if number in values:
            if len(values) <= 6:
                weighted_hits += 1.0
            else:
                weighted_hits += 0.55

    return bounded(weighted_hits * 22)


def get_prediction_numbers(payload: dict[str, Any], keys: list[str]) -> set[int]:
    numbers: set[int] = set()

    for key in keys:
        values = payload.get(key, [])

        if isinstance(values, list):
            for value in values:
                try:
                    number = int(value)
                except (TypeError, ValueError):
                    continue

                if 1 <= number <= 49:
                    numbers.add(number)

    return numbers


def build_ensemble_scores() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    events = parse_valid_events(load_rows(DATA_PATH))

    if len(events) <= 0:
        raise RuntimeError(f"No valid draw events available, got {len(events)}")

    history_scores = historical_rules_scores(events)

    v42_scores_payload = load_json(V42_SCORES_PATH, {})
    v42_prediction = load_json(V42_PREDICTION_PATH, {})

    v43_scores_payload = load_json(V43_SCORES_PATH, {})
    v43_prediction = load_json(V43_PREDICTION_PATH, {})

    v41_prediction = load_json(V41_PREDICTION_PATH, {})

    v42_map = map_by_number(v42_scores_payload)
    v43_map = map_by_number(v43_scores_payload)

    v41_lists = extract_small_number_lists(v41_prediction)
    v42_selected = set(int(number) for number in v42_prediction.get("numbers", []) if 1 <= int(number) <= 49)
    v43_final = get_prediction_numbers(v43_prediction, ["final_refined_rhythm_numbers"])
    v43_next = get_prediction_numbers(v43_prediction, ["next_window_numbers"])
    v43_overdue = get_prediction_numbers(v43_prediction, ["overdue_watchlist_numbers"])
    v43_balanced = get_prediction_numbers(v43_prediction, ["balanced_rhythm_numbers"])

    rows: list[dict[str, Any]] = []

    for number in range(1, 50):
        h = history_scores[number]
        v42 = v42_map.get(number, {})
        v43 = v43_map.get(number, {})

        v42_combined = safe_float(v42.get("combined_score"), 50.0)
        v42_positive = safe_float(v42.get("positive_signal_score"), 50.0)
        v42_absence_risk = safe_float(v42.get("absence_risk_score"), 50.0)
        v42_absence_safety = bounded(100 - v42_absence_risk)

        v43_final_score = safe_float(v43.get("final_rhythm_score"), 50.0)
        v43_next_window = safe_float(v43.get("next_window_score"), 50.0)
        v43_overdue_score = safe_float(v43.get("overdue_score"), 50.0)
        v43_balanced_score = safe_float(v43.get("balanced_rhythm_score"), 50.0)

        rules_score = safe_float(h.get("rules_score"), 50.0)
        v41_vote_score = build_vote_score(number, v41_lists)

        consensus_hits = 0
        consensus_hits += 1 if number in v42_selected else 0
        consensus_hits += 1 if number in v43_final else 0
        consensus_hits += 1 if number in v43_next else 0
        consensus_hits += 1 if number in v43_overdue else 0
        consensus_hits += 1 if number in v43_balanced else 0
        consensus_hits += 1 if v41_vote_score > 0 else 0

        consensus_score = bounded(consensus_hits * 16.7)

        model_agreement_values = [
            v42_combined,
            v42_absence_safety,
            v43_final_score,
            v43_next_window,
            rules_score,
        ]

        model_agreement_score = bounded(100 - (max(model_agreement_values) - min(model_agreement_values)))

        final_score = bounded(
            0.24 * v42_combined
            + 0.14 * v42_absence_safety
            + 0.10 * v42_positive
            + 0.22 * v43_final_score
            + 0.12 * v43_next_window
            + 0.06 * v43_overdue_score
            + 0.06 * rules_score
            + 0.04 * consensus_score
            + 0.02 * model_agreement_score
        )

        rows.append(
            {
                "number": number,
                "final_ensemble_score": round(final_score, 3),
                "v42_combined_score": round(v42_combined, 3),
                "v42_positive_signal": round(v42_positive, 3),
                "v42_absence_risk": round(v42_absence_risk, 3),
                "v42_absence_safety": round(v42_absence_safety, 3),
                "rhythm_final_score": round(v43_final_score, 3),
                "rhythm_next_window_score": round(v43_next_window, 3),
                "rhythm_overdue_score": round(v43_overdue_score, 3),
                "rhythm_balanced_score": round(v43_balanced_score, 3),
                "rules_score": round(rules_score, 3),
                "v41_vote_score": round(v41_vote_score, 3),
                "consensus_hits": consensus_hits,
                "consensus_score": round(consensus_score, 3),
                "model_agreement_score": round(model_agreement_score, 3),
                "current_gap": h.get("current_gap"),
                "total_hits": h.get("total_hits"),
                "hits_last_100": h.get("hits_last_100"),
                "hits_last_250": h.get("hits_last_250"),
            }
        )

    metadata = {
        "valid_draws": len(events),
        "uses_bonus": False,
        "source_models": {
            "historical_rules_layer": True,
            "v41_prediction_file_found": V41_PREDICTION_PATH.exists(),
            "v42_combined_positive_negative_found": V42_SCORES_PATH.exists(),
            "v43_1_interval_rhythm_found": V43_SCORES_PATH.exists(),
        },
        "important_warning": "This is a statistical analysis artifact, not a winning guarantee. Lottery draws are random.",
    }

    return rows, metadata


def decade_bucket(number: int) -> int:
    if number <= 9:
        return 0
    if number <= 19:
        return 1
    if number <= 29:
        return 2
    if number <= 39:
        return 3
    return 4


def combo_balance_penalty(combo: list[int]) -> float:
    if len(combo) != 6:
        return 100.0

    even_count = sum(1 for number in combo if number % 2 == 0)
    bucket_counts: dict[int, int] = {}

    for number in combo:
        bucket = decade_bucket(number)
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1

    penalty = 0.0

    if even_count < 2 or even_count > 4:
        penalty += 10.0

    for count in bucket_counts.values():
        if count > 2:
            penalty += (count - 2) * 8.0

    spread = max(combo) - min(combo)
    if spread < 20:
        penalty += 8.0

    consecutive_pairs = 0
    ordered = sorted(combo)

    for index in range(1, len(ordered)):
        if ordered[index] == ordered[index - 1] + 1:
            consecutive_pairs += 1

    if consecutive_pairs > 2:
        penalty += (consecutive_pairs - 2) * 5.0

    return penalty


def would_exceed_overlap(candidate: int, selected: list[int], previous_combos: list[list[int]], max_overlap: int) -> bool:
    candidate_set = set(selected + [candidate])

    for previous in previous_combos:
        if len(candidate_set.intersection(previous)) > max_overlap:
            return True

    return False


def choose_combo(
    rows: list[dict[str, Any]],
    primary_key: str,
    used_counts: dict[int, int],
    previous_combos: list[list[int]],
    label: str,
    secondary_keys: list[str] | None = None,
    max_repeat: int = 2,
    max_overlap: int = 2,
) -> dict[str, Any]:
    secondary_keys = secondary_keys or []

    ranked = sorted(
        rows,
        key=lambda row: (
            safe_float(row.get(primary_key))
            - used_counts.get(int(row["number"]), 0) * 12.0
            + sum(safe_float(row.get(key)) for key in secondary_keys) * 0.030
            + safe_float(row.get("consensus_score")) * 0.020,
            safe_float(row.get("final_ensemble_score")),
            safe_float(row.get("model_agreement_score")),
        ),
        reverse=True,
    )

    selected: list[int] = []
    bucket_counts: dict[int, int] = {}
    parity_counts = {0: 0, 1: 0}

    def try_add(number: int, enforce_bucket: bool, enforce_parity: bool, enforce_overlap: bool) -> bool:
        if number in selected:
            return False

        if used_counts.get(number, 0) >= max_repeat:
            return False

        bucket = decade_bucket(number)
        parity = number % 2

        if enforce_bucket and bucket_counts.get(bucket, 0) >= 2:
            return False

        if enforce_parity and parity_counts[parity] >= 4:
            return False

        if enforce_overlap and would_exceed_overlap(number, selected, previous_combos, max_overlap):
            return False

        selected.append(number)
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
        parity_counts[parity] += 1
        return True

    # Strict pass: balanced and distinct combination.
    for row in ranked:
        if len(selected) == 6:
            break

        try_add(int(row["number"]), enforce_bucket=True, enforce_parity=True, enforce_overlap=True)

    # Relax overlap if needed, still keeping number repeat cap and basic balance.
    for row in ranked:
        if len(selected) == 6:
            break

        try_add(int(row["number"]), enforce_bucket=True, enforce_parity=True, enforce_overlap=False)

    # Relax bucket/parity only as final fallback, but still keep max_repeat.
    for row in ranked:
        if len(selected) == 6:
            break

        try_add(int(row["number"]), enforce_bucket=False, enforce_parity=False, enforce_overlap=False)

    if len(selected) != 6:
        raise RuntimeError(f"Could not build a 6-number combination for {label}")

    selected = sorted(selected)
    selected_rows = [row for row in rows if int(row["number"]) in selected]

    average_score = mean(safe_float(row.get("final_ensemble_score")) for row in selected_rows)
    average_rhythm = mean(safe_float(row.get("rhythm_final_score")) for row in selected_rows)
    average_combined = mean(safe_float(row.get("v42_combined_score")) for row in selected_rows)
    average_rules = mean(safe_float(row.get("rules_score")) for row in selected_rows)
    average_consensus = mean(safe_float(row.get("consensus_score")) for row in selected_rows)

    for number in selected:
        used_counts[number] = used_counts.get(number, 0) + 1

    return {
        "label": label,
        "numbers": selected,
        "average_final_ensemble_score": round(average_score, 3),
        "average_rhythm_score": round(average_rhythm, 3),
        "average_combined_score": round(average_combined, 3),
        "average_rules_score": round(average_rules, 3),
        "average_consensus_score": round(average_consensus, 3),
        "balance_penalty": round(combo_balance_penalty(selected), 3),
        "number_details": selected_rows,
    }


def build_ticket(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    used_counts: dict[int, int] = {}
    previous_combos: list[list[int]] = []

    definitions = [
        (
            "final_consensus",
            "final_ensemble_score",
            ["rhythm_final_score", "v42_combined_score", "rules_score"],
        ),
        (
            "interval_rhythm_next_window",
            "rhythm_next_window_score",
            ["rhythm_overdue_score", "final_ensemble_score"],
        ),
        (
            "combined_positive_negative",
            "v42_combined_score",
            ["v42_absence_safety", "final_ensemble_score"],
        ),
        (
            "coverage_diversified",
            "rules_score",
            ["final_ensemble_score", "consensus_score", "model_agreement_score"],
        ),
    ]

    combos: list[dict[str, Any]] = []

    for label, primary_key, secondary_keys in definitions:
        combo = choose_combo(
            rows=rows,
            primary_key=primary_key,
            used_counts=used_counts,
            previous_combos=previous_combos,
            label=label,
            secondary_keys=secondary_keys,
            max_repeat=2,
            max_overlap=2,
        )

        combos.append(combo)
        previous_combos.append(combo["numbers"])

    return combos


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def combo_line(combo: dict[str, Any]) -> str:
    numbers = " ".join(f"{int(number):02d}" for number in combo["numbers"])
    return f"{combo['label']}: {numbers}"


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Final Ensemble Ticket Foundation Report",
        "",
        "This foundation combines historical/rules-style signals, combined positive/negative analysis, and interval rhythm analysis.",
        "",
        "**Important:** This is statistical analysis, not a winning guarantee. Lottery draws are random.",
        "",
        f"Valid historical draws analyzed: **{payload['valid_draws']}**",
        f"Bonus number used: **{payload['uses_bonus']}**",
        "",
        f"## {bg('d09fd0a0d095d094d09bd09ed096d095d09dd098d09520d097d09020d0a7d098d0a1d09bd090')}",
        "",
    ]

    for index, combo in enumerate(payload["ticket_combinations"], start=1):
        numbers = ", ".join(str(number) for number in combo["numbers"])
        lines.append(f"Combination {index}: **{numbers}**")
        lines.append(
            f"- Average final ensemble score: {combo['average_final_ensemble_score']}"
        )
        lines.append(
            f"- Average rhythm score: {combo['average_rhythm_score']}"
        )
        lines.append(
            f"- Average combined score: {combo['average_combined_score']}"
        )
        lines.append("")

    lines.extend(
        [
            "## Top ensemble numbers",
            "",
            "| number | final score | combined | rhythm | next-window | rules | consensus |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for row in payload["top_ensemble_numbers"][:15]:
        lines.append(
            f"| {row['number']} | {row['final_ensemble_score']} | {row['v42_combined_score']} | "
            f"{row['rhythm_final_score']} | {row['rhythm_next_window_score']} | "
            f"{row['rules_score']} | {row['consensus_hits']} |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    rows, metadata = build_ensemble_scores()

    sorted_rows = sorted(
        rows,
        key=lambda row: (
            safe_float(row.get("final_ensemble_score")),
            safe_float(row.get("consensus_score")),
            safe_float(row.get("rhythm_final_score")),
        ),
        reverse=True,
    )

    ticket_combinations = build_ticket(sorted_rows)

    payload = {
        "model_name": "final_ensemble_ticket_foundation",
        "internal_version": "v44.1",
        "purpose": "Build four refined 6-number statistical ticket suggestions by combining previous model layers, submodel signals, and ticket-level coverage constraints.",
        **metadata,
        "ticket_combinations": ticket_combinations,
        "top_ensemble_numbers": sorted_rows[:20],
        "all_number_scores_file": str(SCORES_CSV.relative_to(ROOT)),
        "selection_note": "Four combinations are generated for a full ticket with 4 x 6 numbers. Repetition is limited and combinations are diversified. They are statistical suggestions, not predictions with a guarantee.",
    }

    scores_payload = {
        "model_name": "final_ensemble_number_scores",
        "internal_version": "v44.1",
        **metadata,
        "numbers": sorted_rows,
    }

    write_json(scores_payload, SCORES_JSON)
    write_json(payload, TICKET_JSON)
    write_json(payload, SUMMARY_JSON)
    write_csv(sorted_rows, SCORES_CSV)
    SUMMARY_MD.write_text(build_markdown(payload), encoding="utf-8")

    print(bg("d09fd0a0d095d094d09bd09ed096d095d09dd098d09520d097d09020d0a7d098d0a1d09bd090"))

    for index, combo in enumerate(ticket_combinations, start=1):
        print(f"{bg('d09ad09ed09cd091d098d09dd090d0a6d098d0af')} {index}: " + " ".join(f"{number:02d}" for number in combo["numbers"]))

    print()
    print(bg("d092d0b0d0b6d0bdd0be3a20d0a2d0bed0b2d0b020d0b520d181d182d0b0d182d0b8d181d182d0b8d187d0b5d181d0bad0be20d0bfd180d0b5d0b4d0bbd0bed0b6d0b5d0bdd0b8d0b52c20d0bdd0b520d0b3d0b0d180d0b0d0bdd186d0b8d18f20d0b7d0b020d0bfd0b5d187d0b0d0bbd0b1d0b02e"))
    print("VALID_DRAWS", payload["valid_draws"])
    print("USES_BONUS", payload["uses_bonus"])
    print("SCORED_NUMBERS", len(sorted_rows))
    print("TICKET_COMBINATIONS", len(ticket_combinations))
    print("FILES_CREATED")
    print(SCORES_JSON.relative_to(ROOT))
    print(TICKET_JSON.relative_to(ROOT))
    print(SUMMARY_JSON.relative_to(ROOT))
    print(SCORES_CSV.relative_to(ROOT))
    print(SUMMARY_MD.relative_to(ROOT))

    print()
    print("TOP_ENSEMBLE")
    for row in sorted_rows[:12]:
        print(
            row["number"],
            "final=", row["final_ensemble_score"],
            "combined=", row["v42_combined_score"],
            "rhythm=", row["rhythm_final_score"],
            "next=", row["rhythm_next_window_score"],
            "rules=", row["rules_score"],
            "consensus=", row["consensus_hits"],
            "gap=", row["current_gap"],
        )


if __name__ == "__main__":
    main()

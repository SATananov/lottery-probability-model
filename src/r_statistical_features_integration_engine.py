
from __future__ import annotations

import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

REPORTS_DIR = ROOT / "reports"
R_REPORTS_DIR = REPORTS_DIR / "r"
MODELS_DIR = ROOT / "models"

FREQUENCY_CSV = R_REPORTS_DIR / "r_frequency_statistics.csv"
GAP_CSV = R_REPORTS_DIR / "r_gap_statistics.csv"
PAIR_CSV = R_REPORTS_DIR / "r_pair_analysis.csv"
MONTE_CARLO_CSV = R_REPORTS_DIR / "r_monte_carlo_baseline.csv"
CANONICAL_CSV = ROOT / "data" / "v41_canonical_draw_events.csv"
PRIZE_HISTORY_CSV = ROOT / "data" / "prize_winner_history.csv"

NUMBER_FEATURES_CSV = REPORTS_DIR / "v121_r_statistical_number_features.csv"
PAIR_FEATURES_CSV = REPORTS_DIR / "v121_r_statistical_pair_features.csv"
BLENDED_SCORES_CSV = REPORTS_DIR / "v121_r_blended_number_scores.csv"
TICKET_PACK_CSV = REPORTS_DIR / "v121_r_feature_ticket_pack.csv"
SUMMARY_MD = REPORTS_DIR / "v121_r_statistical_features_summary.md"
STATUS_JSON = MODELS_DIR / "v121_r_statistical_features_status.json"

NUMBER_COLUMNS = [f"n{i}" for i in range(1, 7)]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value or "").strip()
        text = re.sub(r"[^0-9-]", "", text)
        return int(text) if text not in {"", "-"} else default
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        text = str(value or "").strip()
        text = text.replace("\xa0", " ").replace(",", ".")
        text = re.sub(r"[^0-9.\-]", "", text)
        return float(text) if text not in {"", ".", "-"} else default
    except Exception:
        return default


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue

    with path.open("r", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    final_fields = list(fields or [])
    for row in rows:
        for key in row.keys():
            if key not in final_fields:
                final_fields.append(key)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=final_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in final_fields})


def _column_names(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return []
    return list(rows[0].keys())


def _find_number_column(rows: list[dict[str, str]]) -> str | None:
    candidates = [
        "number", "Number", "num", "n", "value", "Число", "chislo",
        "ball", "lottery_number",
    ]
    columns = _column_names(rows)
    lowered = {column.lower(): column for column in columns}

    for candidate in candidates:
        if candidate in columns:
            return candidate
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]

    for column in columns:
        values = [_safe_int(row.get(column), -999) for row in rows[:20]]
        valid_count = sum(1 for value in values if 1 <= value <= 49)
        if valid_count >= max(3, min(10, len(rows[:20])) // 2):
            return column

    return None


def _find_metric_column(rows: list[dict[str, str]], preferred_terms: list[str], exclude: set[str] | None = None) -> str | None:
    columns = _column_names(rows)
    exclude = exclude or set()
    lowered = [(column.lower(), column) for column in columns if column not in exclude]

    for term in preferred_terms:
        term_lower = term.lower()
        for lower, original in lowered:
            if term_lower == lower or term_lower in lower:
                return original

    best_column = None
    best_non_zero = -1
    for column in columns:
        if column in exclude:
            continue
        values = [_safe_float(row.get(column), 0.0) for row in rows[:100]]
        non_zero = sum(1 for value in values if abs(value) > 0)
        if non_zero > best_non_zero:
            best_non_zero = non_zero
            best_column = column

    return best_column


def _scale(value: float, min_value: float, max_value: float) -> float:
    if math.isclose(max_value, min_value):
        return 0.5
    return max(0.0, min(1.0, (value - min_value) / (max_value - min_value)))


def _rank_score(value: float, values: list[float], higher_is_better: bool = True) -> float:
    if not values:
        return 0.5
    min_value = min(values)
    max_value = max(values)
    score = _scale(value, min_value, max_value)
    return score if higher_is_better else 1.0 - score


def _read_latest_draw() -> dict[str, Any]:
    rows = _read_csv(PRIZE_HISTORY_CSV) or _read_csv(CANONICAL_CSV)
    valid_rows: list[dict[str, Any]] = []

    for row in rows:
        year = _safe_int(row.get("draw_year") or row.get("year"), 0)
        draw_number = _safe_int(row.get("draw_number"), 0)
        numbers = []
        for key in NUMBER_COLUMNS:
            number = _safe_int(row.get(key), 0)
            if 1 <= number <= 49:
                numbers.append(number)
        if len(numbers) < 6 and row.get("numbers_text"):
            numbers = [_safe_int(token, 0) for token in re.findall(r"\b\d{1,2}\b", row["numbers_text"])]
            numbers = [number for number in numbers if 1 <= number <= 49][:6]
        if year and draw_number and len(numbers) == 6:
            valid_rows.append({
                "year": year,
                "draw_number": draw_number,
                "date": row.get("draw_date") or row.get("date") or "",
                "numbers": numbers,
            })

    if not valid_rows:
        return {"year": 0, "draw_number": 0, "date": "", "numbers": []}

    valid_rows.sort(key=lambda row: (row["year"], row["draw_number"], row["date"]))
    return valid_rows[-1]


def _extract_frequency_features() -> dict[int, dict[str, Any]]:
    rows = _read_csv(FREQUENCY_CSV)
    result = {number: {"r_frequency_count": 0.0, "r_frequency_score": 0.5} for number in range(1, 50)}

    if not rows:
        return result

    number_column = _find_number_column(rows)
    metric_column = _find_metric_column(
        rows,
        ["frequency", "freq", "count", "draw_count", "times", "occurrences", "hits"],
        exclude={number_column} if number_column else set(),
    )

    if not number_column or not metric_column:
        return result

    values_by_number: dict[int, float] = {}
    for row in rows:
        number = _safe_int(row.get(number_column), 0)
        if 1 <= number <= 49:
            values_by_number[number] = _safe_float(row.get(metric_column), 0.0)

    values = list(values_by_number.values())
    for number in range(1, 50):
        value = values_by_number.get(number, 0.0)
        result[number]["r_frequency_count"] = value
        result[number]["r_frequency_score"] = _rank_score(value, values, higher_is_better=True)

    return result


def _extract_gap_features() -> dict[int, dict[str, Any]]:
    rows = _read_csv(GAP_CSV)
    result = {number: {"r_current_gap": 0.0, "r_gap_score": 0.5} for number in range(1, 50)}

    if not rows:
        return result

    number_column = _find_number_column(rows)
    metric_column = _find_metric_column(
        rows,
        ["current_gap", "gap", "largest_gap", "days_since", "draws_since", "interval"],
        exclude={number_column} if number_column else set(),
    )

    if not number_column or not metric_column:
        return result

    values_by_number: dict[int, float] = {}
    for row in rows:
        number = _safe_int(row.get(number_column), 0)
        if 1 <= number <= 49:
            values_by_number[number] = _safe_float(row.get(metric_column), 0.0)

    values = list(values_by_number.values())
    for number in range(1, 50):
        value = values_by_number.get(number, 0.0)
        result[number]["r_current_gap"] = value
        # Larger gaps can be useful as a "due/interval" signal, but not dominant.
        result[number]["r_gap_score"] = _rank_score(value, values, higher_is_better=True)

    return result


def _extract_monte_carlo_features() -> dict[int, dict[str, Any]]:
    rows = _read_csv(MONTE_CARLO_CSV)
    result = {
        number: {
            "r_monte_carlo_observed": 0.0,
            "r_monte_carlo_expected": 0.0,
            "r_monte_carlo_deviation": 0.0,
            "r_monte_carlo_score": 0.5,
        }
        for number in range(1, 50)
    }

    if not rows:
        return result

    number_column = _find_number_column(rows)
    observed_column = _find_metric_column(rows, ["observed", "actual", "frequency", "count"], exclude={number_column} if number_column else set())
    expected_column = _find_metric_column(rows, ["expected", "mean", "baseline", "monte"], exclude={number_column, observed_column} if number_column and observed_column else set())

    if not number_column:
        return result

    deviations: dict[int, float] = {}
    observed_values: dict[int, float] = {}
    expected_values: dict[int, float] = {}

    for row in rows:
        number = _safe_int(row.get(number_column), 0)
        if not (1 <= number <= 49):
            continue
        observed = _safe_float(row.get(observed_column), 0.0) if observed_column else 0.0
        expected = _safe_float(row.get(expected_column), 0.0) if expected_column else 0.0
        deviation = observed - expected if expected_column else observed

        observed_values[number] = observed
        expected_values[number] = expected
        deviations[number] = deviation

    deviation_values = [abs(value) for value in deviations.values()]
    for number in range(1, 50):
        observed = observed_values.get(number, 0.0)
        expected = expected_values.get(number, 0.0)
        deviation = deviations.get(number, 0.0)
        # Prefer calm numbers near baseline rather than extreme Monte Carlo deviations.
        extremeness = _rank_score(abs(deviation), deviation_values, higher_is_better=True)
        score = 1.0 - extremeness if deviation_values else 0.5

        result[number].update({
            "r_monte_carlo_observed": observed,
            "r_monte_carlo_expected": expected,
            "r_monte_carlo_deviation": deviation,
            "r_monte_carlo_score": score,
        })

    return result


def _parse_pair_numbers(row: dict[str, str]) -> tuple[int, int] | None:
    keys = list(row.keys())

    explicit_a = None
    explicit_b = None
    for key in keys:
        lower = key.lower()
        if lower in {"n1", "number1", "number_a", "a", "first", "num1"}:
            explicit_a = _safe_int(row.get(key), 0)
        if lower in {"n2", "number2", "number_b", "b", "second", "num2"}:
            explicit_b = _safe_int(row.get(key), 0)

    if explicit_a and explicit_b and 1 <= explicit_a <= 49 and 1 <= explicit_b <= 49 and explicit_a != explicit_b:
        return tuple(sorted((explicit_a, explicit_b)))

    for key in keys:
        text = str(row.get(key) or "")
        numbers = [_safe_int(token, 0) for token in re.findall(r"\b\d{1,2}\b", text)]
        numbers = [number for number in numbers if 1 <= number <= 49]
        if len(numbers) >= 2 and numbers[0] != numbers[1]:
            return tuple(sorted((numbers[0], numbers[1])))

    return None


def _extract_pair_features() -> dict[tuple[int, int], dict[str, Any]]:
    rows = _read_csv(PAIR_CSV)
    result: dict[tuple[int, int], dict[str, Any]] = {}

    if not rows:
        return result

    pair_rows: list[tuple[tuple[int, int], float]] = []
    for row in rows:
        pair = _parse_pair_numbers(row)
        if not pair:
            continue

        metric_column = _find_metric_column(
            [row],
            ["count", "frequency", "pair_count", "support", "score", "hits"],
            exclude=set(row.keys()) - set(row.keys()),
        )

        value = 0.0
        if metric_column:
            value = _safe_float(row.get(metric_column), 0.0)

        if value <= 0:
            for key, raw_value in row.items():
                if pair and str(raw_value).strip() not in {str(pair[0]), str(pair[1])}:
                    value = max(value, _safe_float(raw_value, 0.0))

        pair_rows.append((pair, value))

    values = [value for _, value in pair_rows]
    for pair, value in pair_rows:
        result[pair] = {
            "number_a": pair[0],
            "number_b": pair[1],
            "r_pair_count": value,
            "r_pair_score": _rank_score(value, values, higher_is_better=True),
        }

    return result


def build_r_number_features() -> dict[str, Any]:
    frequency = _extract_frequency_features()
    gaps = _extract_gap_features()
    monte = _extract_monte_carlo_features()
    pair_features = _extract_pair_features()
    latest = _read_latest_draw()
    latest_numbers = set(latest.get("numbers") or [])

    rows: list[dict[str, Any]] = []
    for number in range(1, 50):
        freq_score = float(frequency[number]["r_frequency_score"])
        gap_score = float(gaps[number]["r_gap_score"])
        mc_score = float(monte[number]["r_monte_carlo_score"])

        repeat_penalty = 0.12 if number in latest_numbers else 0.0
        neighbor_bonus = 0.0
        for latest_number in latest_numbers:
            if abs(number - latest_number) == 1:
                neighbor_bonus = max(neighbor_bonus, 0.04)
            if abs(number - latest_number) == 2:
                neighbor_bonus = max(neighbor_bonus, 0.02)

        blended_score = (
            0.42 * freq_score
            + 0.28 * gap_score
            + 0.20 * mc_score
            + neighbor_bonus
            - repeat_penalty
        )
        blended_score = max(0.0, min(1.0, blended_score))

        rows.append({
            "number": number,
            "r_frequency_count": round(float(frequency[number]["r_frequency_count"]), 6),
            "r_frequency_score": round(freq_score, 6),
            "r_current_gap": round(float(gaps[number]["r_current_gap"]), 6),
            "r_gap_score": round(gap_score, 6),
            "r_monte_carlo_observed": round(float(monte[number]["r_monte_carlo_observed"]), 6),
            "r_monte_carlo_expected": round(float(monte[number]["r_monte_carlo_expected"]), 6),
            "r_monte_carlo_deviation": round(float(monte[number]["r_monte_carlo_deviation"]), 6),
            "r_monte_carlo_score": round(mc_score, 6),
            "latest_draw_repeat_flag": int(number in latest_numbers),
            "latest_draw_neighbor_flag": int(neighbor_bonus > 0),
            "r_blended_score": round(blended_score, 6),
            "feature_source": "R statistical reports",
        })

    rows = sorted(rows, key=lambda row: row["r_blended_score"], reverse=True)

    pair_rows = sorted(pair_features.values(), key=lambda row: row.get("r_pair_score", 0), reverse=True)

    _write_csv(NUMBER_FEATURES_CSV, sorted(rows, key=lambda row: row["number"]), [
        "number",
        "r_frequency_count", "r_frequency_score",
        "r_current_gap", "r_gap_score",
        "r_monte_carlo_observed", "r_monte_carlo_expected", "r_monte_carlo_deviation", "r_monte_carlo_score",
        "latest_draw_repeat_flag", "latest_draw_neighbor_flag",
        "r_blended_score", "feature_source",
    ])
    _write_csv(BLENDED_SCORES_CSV, rows, [
        "number",
        "r_blended_score",
        "r_frequency_score",
        "r_gap_score",
        "r_monte_carlo_score",
        "latest_draw_repeat_flag",
        "latest_draw_neighbor_flag",
    ])
    _write_csv(PAIR_FEATURES_CSV, pair_rows, ["number_a", "number_b", "r_pair_count", "r_pair_score"])

    return {
        "generated_at_utc": utc_now(),
        "latest_draw": latest,
        "number_features": rows,
        "pair_features": pair_rows,
        "source_files": {
            "frequency": str(FREQUENCY_CSV.relative_to(ROOT)),
            "gap": str(GAP_CSV.relative_to(ROOT)),
            "pair": str(PAIR_CSV.relative_to(ROOT)),
            "monte_carlo": str(MONTE_CARLO_CSV.relative_to(ROOT)),
        },
        "output_files": {
            "number_features": str(NUMBER_FEATURES_CSV.relative_to(ROOT)),
            "pair_features": str(PAIR_FEATURES_CSV.relative_to(ROOT)),
            "blended_scores": str(BLENDED_SCORES_CSV.relative_to(ROOT)),
        },
    }


def _score_lookup(number_rows: list[dict[str, Any]]) -> dict[int, float]:
    return {_safe_int(row.get("number"), 0): _safe_float(row.get("r_blended_score"), 0.0) for row in number_rows}


def _pair_lookup(pair_rows: list[dict[str, Any]]) -> dict[tuple[int, int], float]:
    lookup: dict[tuple[int, int], float] = {}
    for row in pair_rows:
        a = _safe_int(row.get("number_a"), 0)
        b = _safe_int(row.get("number_b"), 0)
        if 1 <= a <= 49 and 1 <= b <= 49 and a != b:
            lookup[tuple(sorted((a, b)))] = _safe_float(row.get("r_pair_score"), 0.0)
    return lookup


def _ticket_pair_score(ticket: list[int], pair_scores: dict[tuple[int, int], float]) -> float:
    values = []
    for i, a in enumerate(ticket):
        for b in ticket[i + 1:]:
            values.append(pair_scores.get(tuple(sorted((a, b))), 0.5))
    return sum(values) / len(values) if values else 0.5


def _ticket_shape_score(ticket: list[int]) -> float:
    total = sum(ticket)
    odd_count = sum(1 for number in ticket if number % 2)
    low_count = sum(1 for number in ticket if number <= 24)

    sum_score = 1.0 - min(abs(total - 150) / 90, 1.0)
    odd_score = 1.0 - min(abs(odd_count - 3) / 3, 1.0)
    low_score = 1.0 - min(abs(low_count - 3) / 3, 1.0)

    return max(0.0, min(1.0, 0.45 * sum_score + 0.30 * odd_score + 0.25 * low_score))


def _ticket_score(ticket: list[int], number_scores: dict[int, float], pair_scores: dict[tuple[int, int], float]) -> float:
    base = sum(number_scores.get(number, 0.0) for number in ticket) / len(ticket)
    pair = _ticket_pair_score(ticket, pair_scores)
    shape = _ticket_shape_score(ticket)
    return max(0.0, min(1.0, 0.62 * base + 0.18 * pair + 0.20 * shape))


def build_r_feature_ticket_pack(pack_count: int = 3, lines_per_pack: int = 4) -> dict[str, Any]:
    features = build_r_number_features()
    number_rows = features["number_features"]
    pair_rows = features["pair_features"]

    number_scores = _score_lookup(number_rows)
    pair_scores = _pair_lookup(pair_rows)

    ranked_numbers = [int(row["number"]) for row in number_rows]
    top_pool = ranked_numbers[:22]
    mid_pool = ranked_numbers[22:40]
    tail_pool = ranked_numbers[40:]

    used_tickets: set[tuple[int, ...]] = set()
    tickets: list[dict[str, Any]] = []
    total_lines = int(pack_count) * int(lines_per_pack)

    for index in range(total_lines * 8):
        rotation = index % max(1, len(top_pool))
        candidate = []

        candidate.extend(top_pool[rotation:rotation + 3])
        if len(candidate) < 3:
            candidate.extend(top_pool[:3 - len(candidate)])

        mid_rotation = (index * 3) % max(1, len(mid_pool))
        candidate.extend(mid_pool[mid_rotation:mid_rotation + 2])
        if len(candidate) < 5:
            candidate.extend(mid_pool[:5 - len(candidate)])

        tail_source = tail_pool if tail_pool else ranked_numbers[-9:]
        tail_rotation = (index * 5) % max(1, len(tail_source))
        candidate.append(tail_source[tail_rotation])

        candidate = sorted(set(candidate))

        # Repair to exactly six numbers.
        for number in ranked_numbers:
            if len(candidate) >= 6:
                break
            if number not in candidate:
                candidate.append(number)

        candidate = sorted(candidate[:6])
        key = tuple(candidate)

        if len(key) != 6 or key in used_tickets:
            continue

        total = sum(candidate)
        odd_count = sum(1 for number in candidate if number % 2)
        low_count = sum(1 for number in candidate if number <= 24)

        # Keep only normal playable shapes.
        if not (95 <= total <= 210):
            continue
        if odd_count not in {2, 3, 4}:
            continue
        if low_count not in {2, 3, 4}:
            continue

        used_tickets.add(key)
        ticket_score = _ticket_score(candidate, number_scores, pair_scores)
        pack_number = len(tickets) // int(lines_per_pack) + 1
        line_number = len(tickets) % int(lines_per_pack) + 1

        tickets.append({
            "pack_no": pack_number,
            "line_no": line_number,
            "n1": candidate[0],
            "n2": candidate[1],
            "n3": candidate[2],
            "n4": candidate[3],
            "n5": candidate[4],
            "n6": candidate[5],
            "numbers_text": ", ".join(str(number) for number in candidate),
            "r_ticket_score": round(ticket_score, 6),
            "sum": total,
            "odd_count": odd_count,
            "low_count": low_count,
            "source": "Step 121 R statistical features",
        })

        if len(tickets) >= total_lines:
            break

    _write_csv(TICKET_PACK_CSV, tickets, [
        "pack_no", "line_no", "n1", "n2", "n3", "n4", "n5", "n6",
        "numbers_text", "r_ticket_score", "sum", "odd_count", "low_count", "source",
    ])

    status = {
        "generated_at_utc": utc_now(),
        "latest_draw": features["latest_draw"],
        "feature_outputs": features["output_files"],
        "ticket_pack": str(TICKET_PACK_CSV.relative_to(ROOT)),
        "ticket_count": len(tickets),
        "model_retraining": {
            "performed": False,
            "policy": "R features are integrated as scoring artifacts and ticket-builder inputs, not as heavy ML retraining.",
        },
    }

    write_summary(status, number_rows, pair_rows, tickets)
    STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return status


def write_summary(status: dict[str, Any], number_rows: list[dict[str, Any]], pair_rows: list[dict[str, Any]], tickets: list[dict[str, Any]]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    latest = status.get("latest_draw", {})
    top_numbers = number_rows[:12]

    lines = [
        "# Step 121 — R Statistical Features Integration",
        "",
        f"- Generated at UTC: `{status.get('generated_at_utc', utc_now())}`",
        f"- Latest known draw: **{latest.get('year')} / {latest.get('draw_number')}** — `{latest.get('numbers')}`",
        f"- Number feature rows: **{len(number_rows)}**",
        f"- Pair feature rows: **{len(pair_rows)}**",
        f"- R feature ticket lines: **{len(tickets)}**",
        "",
        "## Output files",
        "",
        f"- `{NUMBER_FEATURES_CSV.relative_to(ROOT)}`",
        f"- `{PAIR_FEATURES_CSV.relative_to(ROOT)}`",
        f"- `{BLENDED_SCORES_CSV.relative_to(ROOT)}`",
        f"- `{TICKET_PACK_CSV.relative_to(ROOT)}`",
        f"- `{STATUS_JSON.relative_to(ROOT)}`",
        "",
        "## Top R-blended numbers",
        "",
    ]

    for row in top_numbers:
        lines.append(
            f"- {row['number']}: score `{row['r_blended_score']}`, "
            f"freq `{row['r_frequency_score']}`, gap `{row['r_gap_score']}`, MC `{row['r_monte_carlo_score']}`"
        )

    lines.extend([
        "",
        "## Policy",
        "",
        "Step 121 does not claim that lottery outcomes are predictable.",
        "It converts independent R statistical reports into Python-readable features and a controlled R-blended ticket pack.",
        "Heavy ML retraining is not performed automatically.",
        "",
    ])

    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def run_step121() -> dict[str, Any]:
    return build_r_feature_ticket_pack(pack_count=3, lines_per_pack=4)

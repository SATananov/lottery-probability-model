
from __future__ import annotations

import itertools
import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DATA_CANDIDATES = [
    ROOT / "data" / "v41_canonical_draw_events.csv",
    ROOT / "data" / "historical_draws.csv",
]

V45_TICKETS = ROOT / "models" / "v45" / "v45_final_prediction_tickets.json"
PAIR_CSV = ROOT / "reports" / "v50_pair_scores.csv"
GROUP_CSV = ROOT / "reports" / "v50_group_scores.csv"

MODEL_DIR = ROOT / "models" / "v51"
MODEL_JSON = MODEL_DIR / "v51_ticket_portfolio_intelligence.json"

REPORTS_DIR = ROOT / "reports"
SUMMARY_JSON = REPORTS_DIR / "v51_ticket_portfolio_summary.json"
SUMMARY_MD = REPORTS_DIR / "v51_ticket_portfolio_summary.md"
CURRENT_SCORE_CSV = REPORTS_DIR / "v51_current_pro_ticket_score.csv"


def _find_data_path() -> Path | None:
    for path in DATA_CANDIDATES:
        if path.exists():
            return path
    return None


def _extract_numbers_from_row(row: pd.Series) -> list[int]:
    column_sets = [
        [f"n{i}" for i in range(1, 7)],
        [f"num{i}" for i in range(1, 7)],
        [f"number_{i}" for i in range(1, 7)],
        [f"main_{i}" for i in range(1, 7)],
        [f"ball_{i}" for i in range(1, 7)],
    ]

    normalized = {str(col).lower(): col for col in row.index}

    for columns in column_sets:
        if all(col in normalized for col in columns):
            values = []
            for col in columns:
                try:
                    values.append(int(row[normalized[col]]))
                except Exception:
                    return []
            cleaned = sorted(set(values))
            if len(cleaned) == 6 and all(1 <= n <= 49 for n in cleaned):
                return cleaned

    text_columns = [
        "numbers",
        "main_numbers",
        "combination",
        "draw_numbers",
        "winning_numbers",
        "nums",
    ]

    for col in text_columns:
        if col in normalized:
            raw = str(row[normalized[col]])
            values = [int(x) for x in re.findall(r"\d+", raw)]
            cleaned = sorted(set(n for n in values if 1 <= n <= 49))
            if len(cleaned) >= 6:
                return cleaned[:6]

    values = []
    for value in row.values:
        try:
            n = int(value)
        except Exception:
            continue
        if 1 <= n <= 49:
            values.append(n)

    cleaned = sorted(set(values))
    if len(cleaned) >= 6:
        return cleaned[:6]

    return []


def _load_draws() -> list[list[int]]:
    data_path = _find_data_path()
    if data_path is None:
        return []

    try:
        df = pd.read_csv(data_path)
    except Exception:
        return []

    draws: list[list[int]] = []
    for _, row in df.iterrows():
        numbers = _extract_numbers_from_row(row)
        if len(numbers) == 6:
            draws.append(numbers)

    return draws


def _read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _load_pro_combinations() -> list[list[int]]:
    data = _read_json(V45_TICKETS)
    combos: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()

    def add(values: Any) -> None:
        if not isinstance(values, list):
            return
        try:
            cleaned = sorted({int(x) for x in values if 1 <= int(x) <= 49})
        except Exception:
            return
        if len(cleaned) != 6:
            return
        key = tuple(cleaned)
        if key not in seen:
            seen.add(key)
            combos.append(cleaned)

    def walk(obj: Any) -> None:
        if isinstance(obj, list):
            add(obj)
            for item in obj:
                walk(item)
        elif isinstance(obj, dict):
            for key in ["numbers", "combination", "ticket", "primary_numbers", "main_numbers"]:
                if key in obj:
                    add(obj.get(key))
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    walk(value)

    walk(data)
    return combos[:8]


def _load_score_map(path: Path, key_col: str, score_col: str) -> dict[str, float]:
    if not path.exists():
        return {}
    try:
        df = pd.read_csv(path)
    except Exception:
        return {}

    if key_col not in df.columns or score_col not in df.columns:
        return {}

    result: dict[str, float] = {}
    for _, row in df.iterrows():
        try:
            result[str(row[key_col])] = float(row[score_col])
        except Exception:
            continue
    return result


def _pair_key(a: int, b: int) -> str:
    x, y = sorted([a, b])
    return f"{x}-{y}"


def _group_key(values: tuple[int, int, int]) -> str:
    return "-".join(str(x) for x in sorted(values))


def _sum_bounds(draws: list[list[int]]) -> dict[str, float]:
    if not draws:
        return {
            "min_sum": 80.0,
            "low_sum": 105.0,
            "median_sum": 150.0,
            "high_sum": 195.0,
            "max_sum": 220.0,
        }

    sums = pd.Series([sum(draw) for draw in draws])
    return {
        "min_sum": float(sums.min()),
        "low_sum": float(sums.quantile(0.10)),
        "median_sum": float(sums.quantile(0.50)),
        "high_sum": float(sums.quantile(0.90)),
        "max_sum": float(sums.max()),
    }


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _sum_score(total: int, bounds: dict[str, float]) -> float:
    low = bounds["low_sum"]
    high = bounds["high_sum"]
    median = bounds["median_sum"]

    if low <= total <= high:
        distance = abs(total - median)
        span = max(high - low, 1.0)
        return _clamp(1.0 - (distance / span) * 0.35)

    if total < low:
        distance = low - total
        span = max(low - bounds["min_sum"], 1.0)
        return _clamp(0.75 - distance / span)

    distance = total - high
    span = max(bounds["max_sum"] - high, 1.0)
    return _clamp(0.75 - distance / span)


def _combo_score(
    combo: list[int],
    pair_scores: dict[str, float],
    group_scores: dict[str, float],
    bounds: dict[str, float],
) -> dict[str, Any]:
    numbers = sorted(combo)

    pair_keys = [_pair_key(a, b) for a, b in itertools.combinations(numbers, 2)]
    group_keys = [_group_key(g) for g in itertools.combinations(numbers, 3)]

    pair_values = [float(pair_scores.get(key, 0.0)) for key in pair_keys]
    group_values = [float(group_scores.get(key, 0.0)) for key in group_keys]

    pair_average = sum(pair_values) / len(pair_values) if pair_values else 0.0
    group_average = sum(group_values) / len(group_values) if group_values else 0.0

    strong_pairs = sum(1 for value in pair_values if value >= 0.65)
    strong_groups = sum(1 for value in group_values if value >= 0.65)

    even_count = sum(1 for n in numbers if n % 2 == 0)
    low_count = sum(1 for n in numbers if n <= 24)
    consecutive_pairs = sum(1 for a, b in zip(numbers, numbers[1:]) if b - a == 1)

    even_balance = 1.0 - abs(even_count - 3) / 3
    low_high_balance = 1.0 - abs(low_count - 3) / 3
    range_span = max(numbers) - min(numbers)
    range_score = _clamp(range_span / 38.0)
    total_sum = sum(numbers)
    sum_balance = _sum_score(total_sum, bounds)
    consecutive_penalty = _clamp(consecutive_pairs / 3.0)

    raw = (
        0.28 * pair_average
        + 0.12 * group_average
        + 0.16 * even_balance
        + 0.16 * low_high_balance
        + 0.18 * sum_balance
        + 0.10 * range_score
    )

    score = _clamp(raw - (0.08 * consecutive_penalty)) * 100.0

    return {
        "combination": " ".join(str(n) for n in numbers),
        "numbers": numbers,
        "combo_score": round(score, 2),
        "pair_average": round(pair_average, 5),
        "strong_pairs": int(strong_pairs),
        "group_average": round(group_average, 5),
        "strong_groups": int(strong_groups),
        "sum": int(total_sum),
        "even_count": int(even_count),
        "low_count": int(low_count),
        "range_span": int(range_span),
        "consecutive_pairs": int(consecutive_pairs),
    }


def _portfolio_score(combo_rows: list[dict[str, Any]]) -> dict[str, Any]:
    combos = [row["numbers"] for row in combo_rows]

    if not combos:
        return {
            "overall_score": 0.0,
            "rating": "missing",
            "warning_codes": ["missing_combinations"],
            "strength_codes": [],
            "metrics": {},
        }

    all_numbers = [n for combo in combos for n in combo]
    counts = Counter(all_numbers)
    unique_numbers = len(counts)
    max_repeat = max(counts.values()) if counts else 0

    overlaps = []
    for left, right in itertools.combinations(combos, 2):
        overlaps.append(len(set(left) & set(right)))

    avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0.0
    max_overlap = max(overlaps) if overlaps else 0

    combo_avg = sum(float(row["combo_score"]) for row in combo_rows) / len(combo_rows)

    ideal_total_slots = max(len(combos) * 6, 1)
    coverage_score = unique_numbers / ideal_total_slots
    overlap_score = _clamp(1.0 - avg_overlap / 3.0)
    repeat_score = _clamp(1.0 - max(0, max_repeat - 1) / 3.0)

    portfolio_layer = 100.0 * (
        0.40 * overlap_score
        + 0.35 * coverage_score
        + 0.25 * repeat_score
    )

    overall = (0.68 * combo_avg) + (0.32 * portfolio_layer)
    overall = round(_clamp(overall / 100.0) * 100.0, 2)

    warning_codes: list[str] = []
    strength_codes: list[str] = []

    if avg_overlap > 2.2:
        warning_codes.append("high_average_overlap")
    if max_overlap >= 4:
        warning_codes.append("high_max_overlap")
    if max_repeat >= 4:
        warning_codes.append("too_much_repetition")
    if combo_avg < 45:
        warning_codes.append("weak_combo_structure")
    if unique_numbers < max(12, len(combos) * 3):
        warning_codes.append("low_number_coverage")

    if avg_overlap <= 2.0:
        strength_codes.append("good_diversity")
    if max_repeat <= 2:
        strength_codes.append("controlled_repetition")
    if combo_avg >= 55:
        strength_codes.append("solid_combo_structure")
    if unique_numbers >= max(16, len(combos) * 4):
        strength_codes.append("good_number_coverage")

    if overall >= 78:
        rating = "strong"
    elif overall >= 65:
        rating = "balanced"
    elif overall >= 50:
        rating = "medium"
    else:
        rating = "weak"

    return {
        "overall_score": overall,
        "rating": rating,
        "warning_codes": warning_codes,
        "strength_codes": strength_codes,
        "metrics": {
            "combination_count": len(combos),
            "average_combo_score": round(combo_avg, 2),
            "unique_numbers": unique_numbers,
            "max_repeat": int(max_repeat),
            "average_overlap": round(avg_overlap, 3),
            "max_overlap": int(max_overlap),
            "coverage_score": round(coverage_score, 5),
            "overlap_score": round(overlap_score, 5),
            "repeat_score": round(repeat_score, 5),
        },
    }


def _write_outputs(combo_rows: list[dict[str, Any]], portfolio: dict[str, Any], bounds: dict[str, float]) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    csv_rows = []
    for row in combo_rows:
        cleaned = {k: v for k, v in row.items() if k != "numbers"}
        csv_rows.append(cleaned)

    pd.DataFrame(csv_rows).to_csv(CURRENT_SCORE_CSV, index=False, encoding="utf-8")

    summary = {
        "status": "v51_ticket_portfolio_intelligence_completed",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_tickets": str(V45_TICKETS.relative_to(ROOT)),
        "pair_source": str(PAIR_CSV.relative_to(ROOT)),
        "group_source": str(GROUP_CSV.relative_to(ROOT)),
        "sum_bounds": bounds,
        "portfolio": portfolio,
        "combination_scores": csv_rows,
        "warning": "Statistical analysis only. Lottery draws remain random and there is no winning guarantee.",
    }

    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    model = {
        "version": "v51",
        "type": "ticket_portfolio_intelligence",
        "portfolio": portfolio,
        "current_score_file": str(CURRENT_SCORE_CSV.relative_to(ROOT)),
        "summary_file": str(SUMMARY_JSON.relative_to(ROOT)),
        "warning": summary["warning"],
    }

    MODEL_JSON.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# V51 Ticket Portfolio Intelligence",
        "",
        f"Status: `{summary['status']}`",
        f"Overall score: **{portfolio.get('overall_score', 0)} / 100**",
        f"Rating: **{portfolio.get('rating', 'missing')}**",
        "",
        "Important: this is statistical analysis only. It is not a guarantee of winnings.",
        "",
        "## Portfolio metrics",
    ]

    for key, value in portfolio.get("metrics", {}).items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("## Combination scores")

    for row in csv_rows:
        lines.append(f"- {row.get('combination')} ? score {row.get('combo_score')}")

    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    draws = _load_draws()
    bounds = _sum_bounds(draws)

    pair_scores = _load_score_map(PAIR_CSV, "pair", "pair_score")
    group_scores = _load_score_map(GROUP_CSV, "group", "group_score")

    combos = _load_pro_combinations()
    combo_rows = [_combo_score(combo, pair_scores, group_scores, bounds) for combo in combos]
    portfolio = _portfolio_score(combo_rows)

    _write_outputs(combo_rows, portfolio, bounds)

    print("V51_STATUS v51_ticket_portfolio_intelligence_completed")
    print("COMBINATIONS", len(combo_rows))
    print("OVERALL_SCORE", portfolio.get("overall_score"))
    print("RATING", portfolio.get("rating"))
    print("OUTPUT", str(MODEL_JSON.relative_to(ROOT)))


if __name__ == "__main__":
    main()

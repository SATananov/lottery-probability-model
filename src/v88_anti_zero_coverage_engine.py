from __future__ import annotations

import csv
import json
import math
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOTAL_NUMBERS = 49
DRAW_SIZE = 6

SAFE_NOTE = "\u0422\u043e\u0432\u0430 \u0435 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043a\u043e\u043d\u0442\u0440\u043e\u043b \u043d\u0430 \u043f\u043e\u043a\u0440\u0438\u0442\u0438\u0435\u0442\u043e, \u0430 \u043d\u0435 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430 \u0438 \u043d\u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430."

NUMBER_FIELD_CANDIDATES = [
    ("n1", "n2", "n3", "n4", "n5", "n6"),
    ("number_1", "number_2", "number_3", "number_4", "number_5", "number_6"),
    ("num1", "num2", "num3", "num4", "num5", "num6"),
    ("main_1", "main_2", "main_3", "main_4", "main_5", "main_6"),
    ("1", "2", "3", "4", "5", "6"),
]

NUMBER_LIST_KEYS = {
    "numbers",
    "combination",
    "selected_numbers",
    "main_numbers",
    "ticket_numbers",
    "field_numbers",
    "draw_numbers",
    "candidate_numbers",
    "\u0447\u0438\u0441\u043b\u0430",
}

NESTED_KEYS = {
    "combinations",
    "tickets",
    "ticket_pack",
    "package",
    "rows",
    "items",
    "data",
    "candidate_combinations",
    "selected_combinations",
    "final_combinations",
    "active_package",
    "portfolio",
    "ticket_rows",
    "tickets_table",
}

PRIORITY_JSON_GLOBS = [
    "models/v84/*.json",
    "models/v73/*.json",
    "models/v71/*.json",
    "models/v70/*.json",
    "models/v67/*.json",
    "models/v66/*.json",
    "models/v65/*.json",
    "reports/v84*.json",
    "reports/v73*.json",
    "reports/v71*.json",
    "reports/v70*.json",
    "reports/v67*.json",
]

PRIORITY_CSV_GLOBS = [
    "reports/v84*.csv",
    "reports/v73*.csv",
    "reports/v71*.csv",
    "reports/v70*.csv",
    "reports/v67*.csv",
]


def safe_comb(n: int, k: int) -> int:
    try:
        n = int(n)
        k = int(k)
    except (TypeError, ValueError):
        return 0
    if n < 0 or k < 0 or k > n:
        return 0
    return math.comb(n, k)


def calculate_empty_package_risk(
    unique_covered_numbers: int,
    total_numbers: int = TOTAL_NUMBERS,
    draw_size: int = DRAW_SIZE,
) -> dict[str, Any]:
    unique = max(0, min(int(unique_covered_numbers or 0), total_numbers))
    denominator = safe_comb(total_numbers, draw_size)
    outside_count = total_numbers - unique
    if outside_count < draw_size:
        empty_risk = 0.0
    elif denominator:
        empty_risk = safe_comb(outside_count, draw_size) / denominator
    else:
        empty_risk = 0.0
    at_least_one = 1.0 - empty_risk
    return {
        "unique_covered_numbers": unique,
        "empty_risk": empty_risk,
        "empty_risk_percent": empty_risk * 100,
        "at_least_one_hit_probability": at_least_one,
        "at_least_one_hit_percent": at_least_one * 100,
        "formula": "C(49 - covered_numbers, 6) / C(49, 6)",
    }


def _parse_int(value: Any) -> int | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        number = int(float(text))
    except (TypeError, ValueError):
        return None
    if 1 <= number <= 49:
        return number
    return None


def normalize_combination(value: Any) -> list[int]:
    if isinstance(value, str):
        import re
        raw_values = re.findall(r"\d+", value)
    elif isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        return []
    numbers: list[int] = []
    seen: set[int] = set()
    for item in raw_values:
        number = _parse_int(item)
        if number is not None and number not in seen:
            seen.add(number)
            numbers.append(number)
    numbers = sorted(numbers)
    return numbers if len(numbers) == 6 else []


def _dedupe_combinations(combinations_list: list[list[int]]) -> list[list[int]]:
    result: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    for combo in combinations_list:
        normalized = normalize_combination(combo)
        key = tuple(normalized)
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def extract_combinations_from_payload(payload: Any) -> list[list[int]]:
    results: list[list[int]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for keys in NUMBER_FIELD_CANDIDATES:
                if all(key in value for key in keys):
                    combo = normalize_combination([value.get(key) for key in keys])
                    if combo:
                        results.append(combo)
            for key in NUMBER_LIST_KEYS:
                if key in value:
                    combo = normalize_combination(value.get(key))
                    if combo:
                        results.append(combo)
            for key in NESTED_KEYS:
                if key in value:
                    walk(value.get(key))
            for nested in value.values():
                if isinstance(nested, (dict, list, tuple)):
                    walk(nested)
        elif isinstance(value, (list, tuple)):
            combo = normalize_combination(value)
            if combo:
                results.append(combo)
            for item in value:
                if isinstance(item, (dict, list, tuple)):
                    walk(item)

    walk(payload)
    return _dedupe_combinations(results)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _extract_combinations_from_csv(path: Path) -> list[list[int]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return []

    combinations_list: list[list[int]] = []
    for row in rows:
        lower_row = {str(k).strip().lower(): v for k, v in row.items()}
        for keys in NUMBER_FIELD_CANDIDATES:
            if all(key in lower_row and str(lower_row.get(key, "")).strip() for key in keys):
                combo = normalize_combination([lower_row.get(key) for key in keys])
                if combo:
                    combinations_list.append(combo)
        for key in NUMBER_LIST_KEYS:
            if key in lower_row and str(lower_row.get(key, "")).strip():
                combo = normalize_combination(lower_row.get(key))
                if combo:
                    combinations_list.append(combo)
    return _dedupe_combinations(combinations_list)


def _limit_package(combinations_list: list[list[int]]) -> list[list[int]]:
    clean = _dedupe_combinations(combinations_list)
    if len(clean) >= 8:
        return clean[:8]
    if len(clean) >= 4:
        return clean[:4]
    return clean


def _glob_existing(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(sorted(ROOT.glob(pattern), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        if path.exists() and path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def load_existing_active_package() -> tuple[list[list[int]], dict[str, Any]]:
    for path in _glob_existing(PRIORITY_CSV_GLOBS):
        combos = _extract_combinations_from_csv(path)
        if combos:
            return _limit_package(combos), {
                "source_type": "csv",
                "source_name": path.name,
                "loaded_combinations": len(combos),
            }

    for path in _glob_existing(PRIORITY_JSON_GLOBS):
        payload = _load_json(path)
        combos = extract_combinations_from_payload(payload)
        if combos:
            return _limit_package(combos), {
                "source_type": "json",
                "source_name": path.name,
                "loaded_combinations": len(combos),
            }

    return [], {
        "source_type": "fallback",
        "source_name": "no_active_package_found",
        "loaded_combinations": 0,
    }


def _risk_level(empty_risk_percent: float) -> tuple[str, str]:
    if empty_risk_percent <= 2:
        return (
            "\u041c\u043d\u043e\u0433\u043e \u0441\u0438\u043b\u043d\u043e \u043f\u043e\u043a\u0440\u0438\u0442\u0438\u0435",
            "\u041f\u0430\u043a\u0435\u0442\u044a\u0442 \u043f\u043e\u043a\u0440\u0438\u0432\u0430 \u0448\u0438\u0440\u043e\u043a \u0434\u0438\u0430\u043f\u0430\u0437\u043e\u043d \u043e\u0442 \u0447\u0438\u0441\u043b\u0430 \u0441 \u043c\u043d\u043e\u0433\u043e \u043d\u0438\u0441\u044a\u043a \u0440\u0438\u0441\u043a \u043e\u0442 \u043f\u0440\u0430\u0437\u0435\u043d \u0444\u0438\u0448.",
        )
    if empty_risk_percent <= 5:
        return (
            "\u0421\u0438\u043b\u043d\u043e \u043f\u043e\u043a\u0440\u0438\u0442\u0438\u0435",
            "\u041f\u043e\u043a\u0440\u0438\u0442\u0438\u0435\u0442\u043e \u0435 \u0441\u0438\u043b\u043d\u043e \u0438 \u0441\u0432\u0430\u043b\u044f \u0440\u0438\u0441\u043a\u0430 \u043e\u0442 \u043d\u0443\u043b\u0435\u0432 \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442 \u0434\u043e \u043d\u0438\u0441\u043a\u043e \u043d\u0438\u0432\u043e.",
        )
    if empty_risk_percent <= 10:
        return (
            "\u0414\u043e\u0431\u0440\u043e \u043f\u043e\u043a\u0440\u0438\u0442\u0438\u0435",
            "\u041f\u0430\u043a\u0435\u0442\u044a\u0442 \u0438\u043c\u0430 \u0434\u043e\u0431\u0440\u0430 \u0437\u0430\u0449\u0438\u0442\u0430, \u043d\u043e \u043c\u043e\u0436\u0435 \u0434\u0430 \u0441\u0435 \u0440\u0430\u0437\u0448\u0438\u0440\u0438 \u043e\u0449\u0435.",
        )
    return (
        "\u0418\u043c\u0430 \u043d\u0443\u0436\u0434\u0430 \u043e\u0442 \u043f\u043e-\u0448\u0438\u0440\u043e\u043a\u043e \u043f\u043e\u043a\u0440\u0438\u0442\u0438\u0435",
        "\u041f\u0440\u0438\u043f\u043e\u043a\u0440\u0438\u0432\u0430\u043d\u0435\u0442\u043e \u0435 \u0432\u0438\u0441\u043e\u043a\u043e \u0438 \u0440\u0438\u0441\u043a\u044a\u0442 \u043e\u0442 \u043f\u0440\u0430\u0437\u0435\u043d \u043f\u0430\u043a\u0435\u0442 \u0435 \u043f\u043e-\u0432\u0438\u0441\u043e\u043a.",
    )


def _overlap_stats(clean: list[list[int]]) -> tuple[float, int]:
    if len(clean) < 2:
        return 0.0, 0
    overlaps = [len(set(a) & set(b)) for a, b in combinations(clean, 2)]
    return sum(overlaps) / len(overlaps), max(overlaps)


def analyze_package(combinations_list: list[list[int]]) -> dict[str, Any]:
    clean = _dedupe_combinations(combinations_list)
    unique_numbers = sorted({number for combo in clean for number in combo})
    counts = {number: 0 for number in range(1, 50)}
    for combo in clean:
        for number in combo:
            counts[number] += 1
    repeated_detail = {str(number): count for number, count in counts.items() if count > 1}
    repeated_total = sum(count - 1 for count in counts.values() if count > 1)
    avg_overlap, max_overlap = _overlap_stats(clean)
    risk = calculate_empty_package_risk(len(unique_numbers))
    risk_level, risk_message_bg = _risk_level(risk["empty_risk_percent"])
    return {
        "total_combinations": len(clean),
        "combinations": clean,
        "unique_covered_numbers": len(unique_numbers),
        "covered_numbers": unique_numbers,
        "repeated_numbers_count": repeated_total,
        "repeated_numbers_detail": repeated_detail,
        "average_overlap_between_combinations": avg_overlap,
        "max_overlap_between_combinations": max_overlap,
        "empty_risk_percent": risk["empty_risk_percent"],
        "at_least_one_hit_percent": risk["at_least_one_hit_percent"],
        "risk_level": risk_level,
        "risk_message_bg": risk_message_bg,
        "safe_note": SAFE_NOTE,
    }


def _score_number(number: int, existing: list[list[int]]) -> float:
    frequency = sum(1 for combo in existing for item in combo if item == number)
    middle_bonus = 1.0 - abs(number - 25) / 25
    return frequency * 3.0 + middle_bonus


def _rank_numbers(existing_combinations: list[list[int]] | None = None, ranked_numbers: list[int] | None = None) -> list[int]:
    explicit = []
    seen: set[int] = set()
    for number in ranked_numbers or []:
        parsed = _parse_int(number)
        if parsed and parsed not in seen:
            seen.add(parsed)
            explicit.append(parsed)

    existing = existing_combinations or []
    from_existing = sorted(range(1, 50), key=lambda n: (-_score_number(n, existing), n))
    result: list[int] = []
    for number in explicit + from_existing + list(range(1, 50)):
        if number not in result:
            result.append(number)
    return result


def _balance_key(number: int) -> tuple[int, int]:
    band = 0 if number <= 16 else 1 if number <= 33 else 2
    parity = number % 2
    return (band, parity)


def build_four_combination_coverage_ticket(
    ranked_numbers: list[int] | None = None,
    existing_combinations: list[list[int]] | None = None,
) -> list[list[int]]:
    ranked = _rank_numbers(existing_combinations, ranked_numbers)
    selected = ranked[:24]
    if len(selected) < 24:
        for number in range(1, 50):
            if number not in selected:
                selected.append(number)
            if len(selected) == 24:
                break

    buckets: dict[tuple[int, int], list[int]] = {}
    for number in selected:
        buckets.setdefault(_balance_key(number), []).append(number)

    combos: list[list[int]] = [[] for _ in range(4)]
    ordered_numbers = []
    for key in sorted(buckets):
        ordered_numbers.extend(buckets[key])
    for index, number in enumerate(ordered_numbers[:24]):
        combos[index % 4].append(number)

    used_per_combo = [set(combo) for combo in combos]
    for idx, combo in enumerate(combos):
        for number in selected:
            if len(combo) >= 6:
                break
            if number not in used_per_combo[idx]:
                combo.append(number)
                used_per_combo[idx].add(number)

    return [sorted(combo[:6]) for combo in combos[:4]]


def compare_current_vs_coverage_candidate(
    current_combinations: list[list[int]],
    candidate_combinations: list[list[int]],
) -> dict[str, Any]:
    current = analyze_package(current_combinations)
    candidate = analyze_package(candidate_combinations)
    delta = {
        "empty_risk_delta_percent": candidate["empty_risk_percent"] - current["empty_risk_percent"],
        "at_least_one_hit_delta_percent": candidate["at_least_one_hit_percent"] - current["at_least_one_hit_percent"],
        "unique_numbers_delta": candidate["unique_covered_numbers"] - current["unique_covered_numbers"],
        "repeated_numbers_delta": candidate["repeated_numbers_count"] - current["repeated_numbers_count"],
    }
    return {
        "current": current,
        "candidate": candidate,
        "delta": delta,
    }

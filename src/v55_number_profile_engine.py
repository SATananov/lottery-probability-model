from __future__ import annotations

import json
import re
from collections import Counter
from itertools import combinations
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any

import pandas as pd


MIN_NUMBER = 1
MAX_NUMBER = 49
NUMBERS_PER_DRAW = 6

DEFAULT_DATA_PATHS = [
    "data/historical_draws.csv",
    "data/v41_canonical_draw_events.csv",
    "data/canonical_draw_events.csv",
    "data/lottery_draws.csv",
    "data/lottery_6_49_dataset.csv",
    "data/processed/lottery_draws.csv",
    "data/processed_draws.csv",
    "reports/v41_model_backtest_events.csv",
]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def find_draw_data_path(data_path: str | None = None) -> Path:
    root = _project_root()

    if data_path:
        p = Path(data_path)
        if not p.is_absolute():
            p = root / p
        if p.exists():
            return p

    for candidate in DEFAULT_DATA_PATHS:
        p = root / candidate
        if p.exists():
            return p

    csv_files = sorted((root / "data").glob("**/*.csv")) if (root / "data").exists() else []
    preferred = [
        p for p in csv_files
        if not any(token in p.name.lower() for token in ["backtest", "score", "summary", "profile"])
    ]

    if preferred:
        return preferred[0]

    if csv_files:
        return csv_files[0]

    raise FileNotFoundError("Не е намерен CSV файл с исторически тиражи в папка data/.")


def _parse_numbers_from_value(value: Any) -> list[int]:
    if value is None or pd.isna(value):
        return []

    raw = str(value)
    numbers = [int(item) for item in re.findall(r"\d+", raw)]
    return [number for number in numbers if MIN_NUMBER <= number <= MAX_NUMBER]


def _normalize_ticket(numbers: list[int]) -> list[int]:
    clean = sorted(int(number) for number in numbers if MIN_NUMBER <= int(number) <= MAX_NUMBER)
    if len(clean) < NUMBERS_PER_DRAW:
        return []
    unique = sorted(set(clean))
    if len(unique) < NUMBERS_PER_DRAW:
        return []
    return unique[:NUMBERS_PER_DRAW]


def _find_column_by_names(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower = {str(col).lower().strip(): str(col) for col in df.columns}
    for candidate in candidates:
        key = candidate.lower().strip()
        if key in lower:
            return lower[key]
    return None


def _detect_wide_number_columns(df: pd.DataFrame) -> list[str]:
    columns = [str(col) for col in df.columns]
    lower_to_original = {col.lower().strip(): col for col in columns}

    candidate_patterns = [
        [f"n{i}" for i in range(1, 7)],
        [f"num{i}" for i in range(1, 7)],
        [f"num_{i}" for i in range(1, 7)],
        [f"number{i}" for i in range(1, 7)],
        [f"number_{i}" for i in range(1, 7)],
        [f"main{i}" for i in range(1, 7)],
        [f"main_{i}" for i in range(1, 7)],
        [f"ball{i}" for i in range(1, 7)],
        [f"ball_{i}" for i in range(1, 7)],
        [f"drawn_number_{i}" for i in range(1, 7)],
    ]

    for pattern in candidate_patterns:
        if all(name in lower_to_original for name in pattern):
            return [lower_to_original[name] for name in pattern]

    regex_matches: dict[int, str] = {}
    for col in columns:
        normalized = col.lower().strip()
        if "bonus" in normalized or "additional" in normalized:
            continue

        match = re.match(r"^(?:n|num|number|main|ball|drawn_number|chislo|число)[_\s-]?([1-6])$", normalized)
        if match:
            regex_matches[int(match.group(1))] = col

    if all(i in regex_matches for i in range(1, 7)):
        return [regex_matches[i] for i in range(1, 7)]

    return []


def _detect_list_column(df: pd.DataFrame) -> str | None:
    preferred_names = [
        "numbers",
        "main_numbers",
        "draw_numbers",
        "combination",
        "winning_numbers",
        "numbers_main",
        "main_combination",
    ]

    for name in preferred_names:
        col = _find_column_by_names(df, [name])
        if col:
            sample = df[col].dropna().head(20)
            if not sample.empty and sample.map(lambda value: len(_parse_numbers_from_value(value)) >= 6).mean() >= 0.50:
                return col

    for col in df.columns:
        normalized = str(col).lower()
        if "bonus" in normalized:
            continue
        if any(token in normalized for token in ["number", "combination", "main"]):
            sample = df[col].dropna().head(20)
            if not sample.empty and sample.map(lambda value: len(_parse_numbers_from_value(value)) >= 6).mean() >= 0.50:
                return str(col)

    return None


def _sort_draw_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(event: dict[str, Any]) -> tuple:
        year = event.get("year")
        draw_no = event.get("draw_no")
        date_value = event.get("date")

        try:
            year_key = int(year)
        except Exception:
            year_key = 0

        try:
            draw_key = int(draw_no)
        except Exception:
            draw_key = int(event.get("source_index", 0))

        date_key = str(date_value or "")

        return (year_key, date_key, draw_key, int(event.get("source_index", 0)))

    sorted_events = sorted(events, key=key)

    for index, event in enumerate(sorted_events, start=1):
        event["event_index"] = index

    return sorted_events


def _meta_from_row(row: pd.Series, source_index: int) -> dict[str, Any]:
    date_col = _find_column_by_names(row.to_frame().T, ["date", "draw_date", "drawing_date", "Дата", "дата"])
    year_col = _find_column_by_names(row.to_frame().T, ["year", "Година", "година"])
    draw_col = _find_column_by_names(row.to_frame().T, ["drawing_no", "draw_no", "draw_number", "tirazh", "тираж", "Тираж"])

    return {
        "source_index": source_index,
        "date": str(row[date_col]) if date_col and not pd.isna(row[date_col]) else "",
        "year": row[year_col] if year_col and not pd.isna(row[year_col]) else "",
        "draw_no": row[draw_col] if draw_col and not pd.isna(row[draw_col]) else source_index,
    }


def load_draw_events(data_path: str | None = None) -> list[dict[str, Any]]:
    path = find_draw_data_path(data_path)
    df = _read_csv(path)

    events: list[dict[str, Any]] = []

    number_cols = _detect_wide_number_columns(df)

    if number_cols:
        for source_index, (_, row) in enumerate(df.iterrows(), start=1):
            numbers = []
            for col in number_cols:
                try:
                    numbers.append(int(row[col]))
                except Exception:
                    pass

            ticket = _normalize_ticket(numbers)
            if not ticket:
                continue

            meta = _meta_from_row(row, source_index)
            meta["numbers"] = ticket
            meta["data_path"] = str(path)
            events.append(meta)

        return _sort_draw_events(events)

    list_col = _detect_list_column(df)

    if list_col:
        for source_index, (_, row) in enumerate(df.iterrows(), start=1):
            ticket = _normalize_ticket(_parse_numbers_from_value(row[list_col]))
            if not ticket:
                continue

            meta = _meta_from_row(row, source_index)
            meta["numbers"] = ticket
            meta["data_path"] = str(path)
            events.append(meta)

        return _sort_draw_events(events)

    number_col = _find_column_by_names(df, ["number", "main_number", "drawn_number", "ball", "value"])
    group_col = _find_column_by_names(df, ["event_id", "draw_id", "drawing_no", "draw_no", "draw_number", "tirazh", "тираж"])

    if number_col and group_col:
        for source_index, (group_value, group) in enumerate(df.groupby(group_col), start=1):
            numbers = []
            for value in group[number_col].tolist():
                try:
                    number = int(value)
                except Exception:
                    continue

                if MIN_NUMBER <= number <= MAX_NUMBER:
                    numbers.append(number)

            ticket = _normalize_ticket(numbers)
            if not ticket:
                continue

            row = group.iloc[0]
            meta = _meta_from_row(row, source_index)
            meta["draw_no"] = group_value
            meta["numbers"] = ticket
            meta["data_path"] = str(path)
            events.append(meta)

        return _sort_draw_events(events)

    numeric_cols = []
    excluded_tokens = ["year", "draw", "date", "bonus", "id", "index"]
    for col in df.columns:
        normalized = str(col).lower()
        if any(token in normalized for token in excluded_tokens):
            continue

        series = pd.to_numeric(df[col], errors="coerce")
        valid_ratio = series.between(MIN_NUMBER, MAX_NUMBER).mean()
        if valid_ratio > 0.80:
            numeric_cols.append(str(col))

    if len(numeric_cols) >= 6:
        selected_cols = numeric_cols[:6]

        for source_index, (_, row) in enumerate(df.iterrows(), start=1):
            numbers = []
            for col in selected_cols:
                try:
                    numbers.append(int(row[col]))
                except Exception:
                    pass

            ticket = _normalize_ticket(numbers)
            if not ticket:
                continue

            meta = _meta_from_row(row, source_index)
            meta["numbers"] = ticket
            meta["data_path"] = str(path)
            events.append(meta)

        return _sort_draw_events(events)

    raise ValueError("Не можах да разпозная колоните с шестте основни числа.")


def _rank_values(values: dict[int, float], high_is_good: bool = True) -> dict[int, float]:
    items = sorted(values.items(), key=lambda item: item[1], reverse=high_is_good)

    if len(items) <= 1:
        return {key: 50.0 for key, _ in items}

    ranks: dict[int, float] = {}
    for position, (key, _) in enumerate(items):
        score = 100.0 - (position / (len(items) - 1)) * 100.0
        ranks[key] = round(score, 2)

    return ranks


def _status_from_profile(draws_since_last: int, avg_interval: float, recent_50: int) -> str:
    expected_50 = 50 * NUMBERS_PER_DRAW / MAX_NUMBER

    if avg_interval <= 0:
        return "Няма достатъчно данни"

    if draws_since_last >= max(25, avg_interval * 2.3):
        return "Силно закъсняло"
    if draws_since_last >= max(14, avg_interval * 1.5):
        return "Закъсняло"
    if recent_50 >= expected_50 * 1.45:
        return "Активно напоследък"
    return "Нормален ритъм"


def _band(score: float) -> str:
    if score >= 80:
        return "Много силен профил"
    if score >= 65:
        return "Силен профил"
    if score >= 45:
        return "Нормален профил"
    return "По-слаб профил"


def build_number_profiles(draw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not draw_events:
        raise ValueError("Няма исторически тиражи за анализ.")

    total_draws = len(draw_events)
    expected_total = total_draws * NUMBERS_PER_DRAW / MAX_NUMBER

    positions: dict[int, list[int]] = {number: [] for number in range(MIN_NUMBER, MAX_NUMBER + 1)}
    pair_partners: dict[int, Counter[int]] = {number: Counter() for number in range(MIN_NUMBER, MAX_NUMBER + 1)}
    triple_partners: dict[int, Counter[tuple[int, int]]] = {number: Counter() for number in range(MIN_NUMBER, MAX_NUMBER + 1)}

    for event in draw_events:
        event_index = int(event["event_index"])
        numbers = sorted(set(int(number) for number in event["numbers"]))

        for number in numbers:
            if MIN_NUMBER <= number <= MAX_NUMBER:
                positions[number].append(event_index)

        for left, right in combinations(numbers, 2):
            pair_partners[left][right] += 1
            pair_partners[right][left] += 1

        for triple in combinations(numbers, 3):
            for number in triple:
                others = tuple(sorted(item for item in triple if item != number))
                triple_partners[number][others] += 1

    raw_profiles: dict[int, dict[str, Any]] = {}

    for number in range(MIN_NUMBER, MAX_NUMBER + 1):
        seen = positions[number]
        appearances = len(seen)
        intervals = [right - left for left, right in zip(seen, seen[1:])]

        first_seen = seen[0] if seen else None
        last_seen = seen[-1] if seen else None
        draws_since_last = total_draws - last_seen if last_seen else total_draws

        avg_interval = round(mean(intervals), 2) if intervals else 0.0
        median_interval = round(median(intervals), 2) if intervals else 0.0
        max_interval = max(intervals) if intervals else 0
        min_interval = min(intervals) if intervals else 0
        current_gap_ratio = round(draws_since_last / avg_interval, 2) if avg_interval else 0.0

        recent_50 = sum(1 for pos in seen if pos > total_draws - 50)
        recent_100 = sum(1 for pos in seen if pos > total_draws - 100)
        recent_250 = sum(1 for pos in seen if pos > total_draws - 250)
        recent_500 = sum(1 for pos in seen if pos > total_draws - 500)

        interval_stability = 0.0
        if len(intervals) >= 2 and mean(intervals) > 0:
            cv = pstdev(intervals) / mean(intervals)
            interval_stability = max(0.0, min(100.0, round(100.0 - min(85.0, cv * 45.0), 2)))
        elif appearances > 1:
            interval_stability = 50.0

        top_pairs = [
            {"partner": partner, "count": count}
            for partner, count in pair_partners[number].most_common(8)
        ]

        top_triples = [
            {"partners": list(partners), "count": count}
            for partners, count in triple_partners[number].most_common(8)
        ]

        status = _status_from_profile(draws_since_last, avg_interval, recent_50)

        notes = [
            f"Число {number} се е появило {appearances} пъти в {total_draws} анализирани тиража.",
            f"Последната поява е преди {draws_since_last} тиража.",
        ]

        if status in {"Закъсняло", "Силно закъсняло"}:
            notes.append("Статусът показва по-дълга пауза спрямо средния му ритъм.")
        elif status == "Активно напоследък":
            notes.append("Числото има по-висока активност в последните 50 тиража.")
        else:
            notes.append("Ритъмът не показва сериозна крайност.")

        recommendations = [
            "Използвай профила като статистически контекст, не като гаранция за бъдещо теглене.",
            "Сравни числото с други числа чрез честота, интервал и участие в двойки/тройки.",
        ]

        raw_profiles[number] = {
            "number": number,
            "total_draws": total_draws,
            "appearances": appearances,
            "expected_appearances": round(expected_total, 2),
            "appearance_vs_expected_ratio": round(appearances / expected_total, 4) if expected_total else 0.0,
            "draw_frequency_pct": round((appearances / total_draws) * 100, 4),
            "slot_frequency_pct": round((appearances / (total_draws * NUMBERS_PER_DRAW)) * 100, 4),
            "first_seen_index": first_seen,
            "last_seen_index": last_seen,
            "draws_since_last_seen": draws_since_last,
            "average_interval": avg_interval,
            "median_interval": median_interval,
            "min_interval": min_interval,
            "max_interval": max_interval,
            "current_gap_ratio": current_gap_ratio,
            "recent_50": recent_50,
            "recent_100": recent_100,
            "recent_250": recent_250,
            "recent_500": recent_500,
            "interval_stability_score": interval_stability,
            "status": status,
            "top_pairs": top_pairs,
            "top_triples": top_triples,
            "notes": notes,
            "recommendations": recommendations,
        }

    frequency_rank = _rank_values({n: p["appearances"] for n, p in raw_profiles.items()}, high_is_good=True)
    recent_rank = _rank_values({n: p["recent_250"] for n, p in raw_profiles.items()}, high_is_good=True)
    overdue_rank = _rank_values({n: p["draws_since_last_seen"] for n, p in raw_profiles.items()}, high_is_good=True)
    stability_rank = _rank_values({n: p["interval_stability_score"] for n, p in raw_profiles.items()}, high_is_good=True)

    profiles: list[dict[str, Any]] = []

    for number, profile in raw_profiles.items():
        profile_score = round(
            frequency_rank[number] * 0.35
            + recent_rank[number] * 0.25
            + overdue_rank[number] * 0.20
            + stability_rank[number] * 0.20,
            2,
        )

        profile["frequency_rank_score"] = frequency_rank[number]
        profile["recent_rank_score"] = recent_rank[number]
        profile["overdue_rank_score"] = overdue_rank[number]
        profile["stability_rank_score"] = stability_rank[number]
        profile["profile_score"] = profile_score
        profile["band"] = _band(profile_score)

        profiles.append(profile)

    return sorted(profiles, key=lambda item: int(item["number"]))


def profiles_to_dataframe(profiles: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for profile in profiles:
        top_pairs_text = "; ".join(
            f"{item['partner']} ({item['count']})"
            for item in profile.get("top_pairs", [])[:5]
        )

        top_triples_text = "; ".join(
            f"{item['partners'][0]}-{item['partners'][1]} ({item['count']})"
            for item in profile.get("top_triples", [])[:5]
        )

        row = {
            "number": profile["number"],
            "profile_score": profile["profile_score"],
            "band": profile["band"],
            "status": profile["status"],
            "appearances": profile["appearances"],
            "expected_appearances": profile["expected_appearances"],
            "appearance_vs_expected_ratio": profile["appearance_vs_expected_ratio"],
            "draw_frequency_pct": profile["draw_frequency_pct"],
            "last_seen_index": profile["last_seen_index"],
            "draws_since_last_seen": profile["draws_since_last_seen"],
            "average_interval": profile["average_interval"],
            "median_interval": profile["median_interval"],
            "max_interval": profile["max_interval"],
            "recent_50": profile["recent_50"],
            "recent_100": profile["recent_100"],
            "recent_250": profile["recent_250"],
            "recent_500": profile["recent_500"],
            "interval_stability_score": profile["interval_stability_score"],
            "top_pairs": top_pairs_text,
            "top_triples": top_triples_text,
        }

        rows.append(row)

    return pd.DataFrame(rows)


def export_number_profiles(
    profiles: list[dict[str, Any]],
    output_csv_path: str | Path,
    output_json_path: str | Path,
) -> None:
    df = profiles_to_dataframe(profiles)
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")

    Path(output_json_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_json_path).write_text(
        json.dumps(profiles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

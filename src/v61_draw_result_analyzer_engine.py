from __future__ import annotations

import csv
import json
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

import pandas as pd

from src.v54_pattern_balance_engine import analyze_combination_pattern
from src.v55_number_profile_engine import build_number_profiles, load_draw_events
from src.v56_draw_similarity_engine import analyze_single_combination_similarity
from src.v57_hot_cold_stable_engine import build_hot_cold_stable_center


MIN_NUMBER = 1
MAX_NUMBER = 49
NUMBERS_PER_DRAW = 6


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _clean_numbers(values: Any) -> list[int]:
    if not isinstance(values, list):
        return []

    cleaned: list[int] = []
    for value in values:
        try:
            number = int(value)
        except Exception:
            continue
        if MIN_NUMBER <= number <= MAX_NUMBER:
            cleaned.append(number)

    unique = sorted(set(cleaned))
    if len(unique) < NUMBERS_PER_DRAW:
        return []
    return unique[:NUMBERS_PER_DRAW]


def _numbers_text(numbers: list[int]) -> str:
    return ", ".join(str(number) for number in numbers)


def _hit_summary(candidate: list[int], actual: list[int]) -> dict[str, Any]:
    actual_set = set(actual)
    candidate_set = set(candidate)
    hits = sorted(candidate_set.intersection(actual_set))
    misses = sorted(candidate_set.difference(actual_set))
    return {
        "hit_count": len(hits),
        "matching_numbers": hits,
        "missing_numbers": misses,
        "matching_numbers_text": _numbers_text(hits),
        "missing_numbers_text": _numbers_text(misses),
    }


def _latest_event(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        raise ValueError("Няма налични исторически тиражи за анализ.")
    return events[-1]


def _event_draw_no(event: dict[str, Any]) -> Any:
    return event.get("draw_no") or event.get("draw_number") or event.get("drawing_no") or ""


def _event_identity(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_index": event.get("event_index", ""),
        "date": event.get("date", ""),
        "year": event.get("year", ""),
        "draw_no": _event_draw_no(event),
        "numbers": _clean_numbers(event.get("numbers", [])),
        "numbers_text": _numbers_text(_clean_numbers(event.get("numbers", []))),
    }


def _add_signal(
    signals: list[dict[str, Any]],
    source_key: str,
    source_bg: str,
    candidate_label: str,
    numbers: Any,
    actual_numbers: list[int],
    note_bg: str,
) -> None:
    candidate = _clean_numbers(numbers)
    if not candidate:
        return

    hit = _hit_summary(candidate, actual_numbers)
    signals.append(
        {
            "source_key": source_key,
            "source_bg": source_bg,
            "candidate_label": candidate_label,
            "candidate_numbers": candidate,
            "candidate_text": _numbers_text(candidate),
            "note_bg": note_bg,
            **hit,
        }
    )


def _extract_model_signals(root: Path, actual_numbers: list[int]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []

    v41 = _read_json(root / "models" / "v41" / "v41_latest_predictions.json")
    prediction_sets = v41.get("prediction_sets", {})
    if isinstance(prediction_sets, dict):
        names = {
            "frequency_baseline": "v41 честотен baseline",
            "recency_250_baseline": "v41 recent 250 baseline",
            "sgd_number_classifier": "v41 SGD класификатор",
        }
        for key, numbers in prediction_sets.items():
            _add_signal(
                signals,
                source_key=f"v41_{key}",
                source_bg=names.get(str(key), f"v41 {key}"),
                candidate_label=str(key),
                numbers=numbers,
                actual_numbers=actual_numbers,
                note_bg="Сравнение с текущия v41 statistical output.",
            )

    v42 = _read_json(root / "models" / "v42" / "v42_combined_prediction.json")
    _add_signal(
        signals,
        source_key="v42_combined",
        source_bg="v42 комбиниран позитивен/негативен анализ",
        candidate_label="combined_numbers",
        numbers=v42.get("numbers"),
        actual_numbers=actual_numbers,
        note_bg="Обединен номерен сигнал от v42.",
    )

    v43 = _read_json(root / "models" / "v43_1" / "v43_1_interval_rhythm_refined_prediction.json")
    for key, label in [
        ("balanced_rhythm_numbers", "балансиран ритъм"),
        ("next_window_numbers", "следващ прозорец"),
        ("overdue_watchlist_numbers", "закъснели числа"),
        ("final_refined_rhythm_numbers", "финален ритъм"),
    ]:
        _add_signal(
            signals,
            source_key=f"v43_1_{key}",
            source_bg=f"v43.1 интервален ритъм — {label}",
            candidate_label=key,
            numbers=v43.get(key),
            actual_numbers=actual_numbers,
            note_bg="Ритъм/интервален контекст, не прогноза.",
        )

    v44 = _read_json(root / "models" / "v44_1" / "v44_1_final_ensemble_ticket_prediction.json")
    for item in v44.get("ticket_combinations", []) if isinstance(v44.get("ticket_combinations"), list) else []:
        if not isinstance(item, dict):
            continue
        _add_signal(
            signals,
            source_key=f"v44_1_{item.get('label', 'ticket')}",
            source_bg="v44.1 финален ансамбъл",
            candidate_label=str(item.get("label", "ticket")),
            numbers=item.get("numbers"),
            actual_numbers=actual_numbers,
            note_bg="Финален ensemble ticket candidate.",
        )

    v45 = _read_json(root / "models" / "v45" / "v45_final_prediction_tickets.json")
    _add_signal(
        signals,
        source_key="v45_primary",
        source_bg="v45 Prediction Engine Pro — primary",
        candidate_label="primary_numbers",
        numbers=v45.get("primary_numbers"),
        actual_numbers=actual_numbers,
        note_bg="Primary statistical candidate от v45.",
    )
    for item in v45.get("ticket_combinations", []) if isinstance(v45.get("ticket_combinations"), list) else []:
        if not isinstance(item, dict):
            continue
        _add_signal(
            signals,
            source_key=f"v45_ticket_{item.get('ticket_index', '')}",
            source_bg="v45 Prediction Engine Pro — ticket",
            candidate_label=str(item.get("label") or item.get("ticket_index") or "ticket"),
            numbers=item.get("numbers"),
            actual_numbers=actual_numbers,
            note_bg="Ticket candidate от v45.",
        )

    for rel_path, source_bg, source_key in [
        ("reports/v59_smart_ticket_builder_2_sample.json", "v59 Интелигентен генератор 2 sample", "v59_sample"),
        ("reports/v60_ticket_builder_2_export_sample.json", "v60 export sample", "v60_sample"),
    ]:
        payload = _read_json(root / rel_path)
        selected = payload.get("selected_tickets")
        if isinstance(selected, list):
            for index, numbers in enumerate(selected, start=1):
                _add_signal(
                    signals,
                    source_key=f"{source_key}_{index}",
                    source_bg=source_bg,
                    candidate_label=f"ticket_{index}",
                    numbers=numbers,
                    actual_numbers=actual_numbers,
                    note_bg="Sample generated ticket, използва се само за post-draw overlap context.",
                )

    signals = sorted(
        signals,
        key=lambda item: (-int(item.get("hit_count", 0)), item.get("source_bg", ""), item.get("candidate_label", "")),
    )
    return signals


def _number_profile_context(actual_numbers: list[int], profiles: list[dict[str, Any]], center: dict[str, Any]) -> list[dict[str, Any]]:
    profile_by_number = {int(item["number"]): item for item in profiles if "number" in item}
    classified = center.get("classified_numbers", []) if isinstance(center, dict) else []
    class_by_number = {int(item["number"]): item for item in classified if isinstance(item, dict) and "number" in item}

    rows: list[dict[str, Any]] = []
    for number in actual_numbers:
        profile = profile_by_number.get(number, {})
        classified_item = class_by_number.get(number, {})
        rows.append(
            {
                "number": number,
                "main_group": classified_item.get("main_group", ""),
                "categories": classified_item.get("categories_text", ""),
                "combined_score": classified_item.get("combined_score", 0.0),
                "profile_score": profile.get("profile_score", 0.0),
                "appearances": profile.get("appearances", 0),
                "recent_50": profile.get("recent_50", 0),
                "recent_100": profile.get("recent_100", 0),
                "recent_250": profile.get("recent_250", 0),
                "draws_since_last_seen": profile.get("draws_since_last_seen", 0),
                "average_interval": profile.get("average_interval", 0.0),
                "current_gap_ratio": profile.get("current_gap_ratio", 0.0),
                "interval_stability_score": profile.get("interval_stability_score", 0.0),
            }
        )
    return rows


def _group_counts(number_rows: list[dict[str, Any]]) -> dict[str, int]:
    groups = Counter(str(row.get("main_group", "Неизвестно")) for row in number_rows)
    categories = Counter()

    for row in number_rows:
        raw = str(row.get("categories", ""))
        for part in raw.split(","):
            label = part.strip()
            if label:
                categories[label] += 1

    return {
        "hot_count": int(groups.get("Горещи", 0) + groups.get("hot", 0)),
        "cold_count": int(groups.get("Студени", 0) + groups.get("cold", 0)),
        "stable_count": int(groups.get("Стабилни", 0) + groups.get("stable", 0)),
        "overdue_count": int(sum(count for label, count in categories.items() if "закъс" in label.lower() or "overdue" in label.lower())),
        "unique_group_count": len([label for label, count in groups.items() if count > 0]),
    }


def _pair_group_context(root: Path, actual_numbers: list[int]) -> dict[str, Any]:
    v50 = _read_json(root / "models" / "v50" / "v50_pair_group_intelligence.json")
    actual_pairs = {tuple(sorted(pair)) for pair in combinations(actual_numbers, 2)}

    def collect(items: Any, key: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if not isinstance(items, list):
            return rows
        for item in items:
            if not isinstance(item, dict):
                continue
            n1 = item.get("n1")
            n2 = item.get("n2")
            try:
                pair = tuple(sorted((int(n1), int(n2))))
            except Exception:
                continue
            if pair in actual_pairs:
                rows.append(
                    {
                        "source": key,
                        "pair": f"{pair[0]}-{pair[1]}",
                        "count": item.get("count", 0),
                        "recent_count": item.get("recent_count", 0),
                        "gap": item.get("gap", ""),
                        "pair_score": item.get("pair_score", ""),
                        "watch_score": item.get("watch_score", ""),
                    }
                )
        return rows

    top_hits = collect(v50.get("top_pairs"), "top_pairs")
    watch_hits = collect(v50.get("watch_pairs"), "watch_pairs")

    return {
        "actual_pair_count": len(actual_pairs),
        "top_pair_hits_count": len(top_hits),
        "watch_pair_hits_count": len(watch_hits),
        "top_pair_hits": top_hits,
        "watch_pair_hits": watch_hits,
    }


def _model_signal_summary(signals: list[dict[str, Any]]) -> dict[str, Any]:
    if not signals:
        return {
            "signal_count": 0,
            "best_hit_count": 0,
            "average_hit_count": 0.0,
            "signals_with_3_or_more": 0,
            "signals_with_4_or_more": 0,
            "best_signals": [],
        }

    best = max(int(item.get("hit_count", 0)) for item in signals)
    avg = round(sum(int(item.get("hit_count", 0)) for item in signals) / len(signals), 2)

    return {
        "signal_count": len(signals),
        "best_hit_count": best,
        "average_hit_count": avg,
        "signals_with_3_or_more": sum(1 for item in signals if int(item.get("hit_count", 0)) >= 3),
        "signals_with_4_or_more": sum(1 for item in signals if int(item.get("hit_count", 0)) >= 4),
        "best_signals": [item for item in signals if int(item.get("hit_count", 0)) == best][:10],
    }


def _diagnostic_summary(
    pattern: dict[str, Any],
    group_counts: dict[str, int],
    signal_summary: dict[str, Any],
    similarity: dict[str, Any],
) -> list[str]:
    lines: list[str] = []

    lines.append(
        f"Последният тираж има {pattern.get('band', 'структурен профил')} "
        f"със сума {pattern.get('sum', '-')}, {pattern.get('odd_count', 0)} нечетни и {pattern.get('even_count', 0)} четни числа."
    )

    lines.append(
        f"Класификацията на числата показва {group_counts.get('hot_count', 0)} горещи, "
        f"{group_counts.get('cold_count', 0)} студени, {group_counts.get('stable_count', 0)} стабилни "
        f"и {group_counts.get('overdue_count', 0)} overdue/закъснели сигнала."
    )

    lines.append(
        f"Най-близкият текущ модел/артефакт има {signal_summary.get('best_hit_count', 0)} от 6 съвпадения, "
        f"а средното съвпадение между проверените сигнали е {signal_summary.get('average_hit_count', 0.0)} числа."
    )

    lines.append(
        f"Историческата близост спрямо предишните тиражи достига максимум "
        f"{similarity.get('max_match_count', 0)} от 6 съвпадения."
    )

    lines.append(
        "Това е post-draw диагностичен анализ. Той не доказва предсказателна сила и не гарантира бъдеща печалба."
    )

    return lines


def analyze_latest_draw_result(data_path: str | None = None, top_n: int = 10) -> dict[str, Any]:
    root = project_root()
    events = load_draw_events(data_path)
    latest = _latest_event(events)
    latest_info = _event_identity(latest)
    actual_numbers = latest_info["numbers"]

    previous_events = events[:-1]
    profiles = build_number_profiles(events)
    center = build_hot_cold_stable_center(events)

    pattern = analyze_combination_pattern(actual_numbers, index=1)
    number_rows = _number_profile_context(actual_numbers, profiles, center)
    group_counts = _group_counts(number_rows)
    similarity = analyze_single_combination_similarity(
        combo=actual_numbers,
        draw_events=previous_events,
        top_n=top_n,
        index=1,
    )
    model_signals = _extract_model_signals(root, actual_numbers)
    signal_summary = _model_signal_summary(model_signals)
    pair_context = _pair_group_context(root, actual_numbers)
    summary_lines = _diagnostic_summary(pattern, group_counts, signal_summary, similarity)

    return {
        "module": "draw_result_analyzer",
        "version": "v61",
        "user_facing_name_bg": "Анализ на нов тираж",
        "total_draws": len(events),
        "previous_draws_compared": len(previous_events),
        "latest_draw": latest_info,
        "pattern_analysis": pattern,
        "number_profile_rows": number_rows,
        "group_counts": group_counts,
        "historical_similarity_previous_draws": similarity,
        "model_signal_summary": signal_summary,
        "model_signal_hits": model_signals,
        "pair_group_context": pair_context,
        "diagnostic_summary_bg": summary_lines,
        "safety_note_bg": (
            "Това е анализ след излизане на тиража. Той сравнява реалния тираж с текущи "
            "статистически артефакти и исторически профили, но не е доказателство за предсказание "
            "и не е гаранция за печалба."
        ),
    }


def model_signals_to_dataframe(result: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for item in result.get("model_signal_hits", []):
        rows.append(
            {
                "source_bg": item.get("source_bg", ""),
                "candidate_label": item.get("candidate_label", ""),
                "candidate_text": item.get("candidate_text", ""),
                "hit_count": item.get("hit_count", 0),
                "matching_numbers_text": item.get("matching_numbers_text", ""),
                "missing_numbers_text": item.get("missing_numbers_text", ""),
                "note_bg": item.get("note_bg", ""),
            }
        )
    return pd.DataFrame(rows)


def number_rows_to_dataframe(result: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(result.get("number_profile_rows", []))


def closest_draws_to_dataframe(result: dict[str, Any]) -> pd.DataFrame:
    similarity = result.get("historical_similarity_previous_draws", {})
    rows = []
    for item in similarity.get("closest_draws", []):
        rows.append(
            {
                "year": item.get("year", ""),
                "draw_no": item.get("draw_no", ""),
                "date": item.get("date", ""),
                "draw_numbers_text": item.get("draw_numbers_text", ""),
                "match_count": item.get("match_count", 0),
                "matching_numbers_text": item.get("matching_numbers_text", ""),
                "different_query_numbers_text": item.get("different_query_numbers_text", ""),
            }
        )
    return pd.DataFrame(rows)


def export_latest_draw_result_analysis(result: dict[str, Any], root: Path | None = None) -> None:
    root = root or project_root()
    reports_dir = root / "reports"
    models_dir = root / "models" / "v61"
    reports_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    _write_json(reports_dir / "v61_latest_draw_analysis.json", result)

    summary = {
        "module": result.get("module"),
        "version": result.get("version"),
        "user_facing_name_bg": result.get("user_facing_name_bg"),
        "total_draws": result.get("total_draws"),
        "previous_draws_compared": result.get("previous_draws_compared"),
        "latest_draw": result.get("latest_draw"),
        "pattern_band": result.get("pattern_analysis", {}).get("band"),
        "pattern_score": result.get("pattern_analysis", {}).get("pattern_score"),
        "group_counts": result.get("group_counts"),
        "model_signal_summary": result.get("model_signal_summary"),
        "pair_group_context_summary": {
            "actual_pair_count": result.get("pair_group_context", {}).get("actual_pair_count"),
            "top_pair_hits_count": result.get("pair_group_context", {}).get("top_pair_hits_count"),
            "watch_pair_hits_count": result.get("pair_group_context", {}).get("watch_pair_hits_count"),
        },
        "historical_similarity_summary": {
            "max_match_count": result.get("historical_similarity_previous_draws", {}).get("max_match_count"),
            "four_matches_count": result.get("historical_similarity_previous_draws", {}).get("four_matches_count"),
            "five_matches_count": result.get("historical_similarity_previous_draws", {}).get("five_matches_count"),
            "exact_matches_count": result.get("historical_similarity_previous_draws", {}).get("exact_matches_count"),
        },
        "safety_note_bg": result.get("safety_note_bg"),
    }
    _write_json(reports_dir / "v61_draw_result_analyzer_summary.json", summary)

    manifest = {
        "module": "draw_result_analyzer",
        "version": "v61",
        "user_facing_name_bg": "Анализ на нов тираж",
        "total_draws": result.get("total_draws"),
        "latest_draw": result.get("latest_draw"),
        "depends_on": [
            "data/historical_draws.csv",
            "v54_pattern_balance",
            "v55_number_profile",
            "v56_draw_similarity",
            "v57_hot_cold_stable",
            "v41/v42/v43.1/v44.1/v45/v50/v59/v60 artifacts when available",
        ],
        "purpose_bg": "Анализира последния реален тираж след излизането му и го сравнява с исторически профили и текущи статистически артефакти.",
        "not_a_prediction_bg": result.get("safety_note_bg"),
    }
    _write_json(models_dir / "v61_draw_result_analyzer_manifest.json", manifest)

    model_signals_to_dataframe(result).to_csv(
        reports_dir / "v61_model_signal_hits.csv",
        index=False,
        encoding="utf-8-sig",
    )
    number_rows_to_dataframe(result).to_csv(
        reports_dir / "v61_latest_draw_number_profile.csv",
        index=False,
        encoding="utf-8-sig",
    )
    closest_draws_to_dataframe(result).to_csv(
        reports_dir / "v61_latest_draw_closest_previous_draws.csv",
        index=False,
        encoding="utf-8-sig",
    )

    md_lines = [
        "# v61 Draw Result Analyzer",
        "",
        f"Последен тираж: **{result['latest_draw']['numbers_text']}**",
        f"Дата: **{result['latest_draw'].get('date', '')}**",
        f"Общо тиражи: **{result.get('total_draws')}**",
        "",
        "## Диагностично обобщение",
        "",
    ]
    for line in result.get("diagnostic_summary_bg", []):
        md_lines.append(f"- {line}")
    md_lines.extend(
        [
            "",
            "## Важно",
            "",
            result.get("safety_note_bg", ""),
            "",
        ]
    )
    (reports_dir / "v61_draw_result_analyzer_summary.md").write_text("\n".join(md_lines), encoding="utf-8")


from __future__ import annotations

import itertools
import json
import random
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
V45_SCORES_PATH = ROOT / "models" / "v45" / "v45_latest_number_scores.json"
V45_TICKETS_PATH = ROOT / "models" / "v45" / "v45_final_prediction_tickets.json"
V45_SUMMARY_PATH = ROOT / "reports" / "v45_training_summary.json"


def T(value: str) -> str:
    text = value.encode("ascii").decode("unicode_escape")

    replacements = {
        "\u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440 \u043d\u0430 \u0444\u0438\u0448\u043e\u0432\u0435": "\u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440 \u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438",
        "\u041f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438 \u0444\u0438\u0448\u043e\u0432\u0435": "\u041f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u0437\u0430 \u0435\u0434\u0438\u043d \u0444\u0438\u0448",
        "\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u043d\u0430 \u0444\u0438\u0448\u043e\u0432\u0435\u0442\u0435": "\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438\u0442\u0435",
        "\u0411\u0440\u043e\u0439 \u0444\u0438\u0448\u043e\u0432\u0435": "\u0411\u0440\u043e\u0439 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u0432 \u0435\u0434\u0438\u043d \u0444\u0438\u0448",
        "\u041c\u0430\u043a\u0441. \u043e\u0431\u0449\u0438 \u0447\u0438\u0441\u043b\u0430 \u043c\u0435\u0436\u0434\u0443 \u0444\u0438\u0448\u043e\u0432\u0435": "\u041c\u0430\u043a\u0441. \u043e\u0431\u0449\u0438 \u0447\u0438\u0441\u043b\u0430 \u043c\u0435\u0436\u0434\u0443 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438\u0442\u0435",
        "\u0418\u0437\u043f\u043e\u043b\u0437\u0432\u0430\u0439 \u0442\u0435\u043a\u0443\u0449\u0438\u0442\u0435 Pro \u0444\u0438\u0448\u043e\u0432\u0435 \u043a\u0430\u0442\u043e \u043e\u0441\u043d\u043e\u0432\u0430": "\u0418\u0437\u043f\u043e\u043b\u0437\u0432\u0430\u0439 \u0442\u0435\u043a\u0443\u0449\u0438\u0442\u0435 Pro \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u043a\u0430\u0442\u043e \u043e\u0441\u043d\u043e\u0432\u0430",
        "\u041d\u0430\u043b\u0438\u0447\u043d\u0438 Pro \u0444\u0438\u0448\u043e\u0432\u0435": "\u041d\u0430\u043b\u0438\u0447\u043d\u0438 Pro \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438",
        "\u0422\u0430\u0431\u043b\u0438\u0446\u0430 \u0437\u0430 \u043a\u043e\u043f\u0438\u0440\u0430\u043d\u0435": "\u0422\u0430\u0431\u043b\u0438\u0446\u0430 \u0437\u0430 \u043f\u043e\u043f\u044a\u043b\u0432\u0430\u043d\u0435",
        "\u0421\u0432\u0430\u043b\u0438 CSV \u0441 \u0444\u0438\u0448\u043e\u0432\u0435": "\u0421\u0432\u0430\u043b\u0438 CSV \u0441 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438",
        "\u041d\u0435 \u0443\u0441\u043f\u044f\u0445\u043c\u0435 \u0434\u0430 \u0433\u0435\u043d\u0435\u0440\u0438\u0440\u0430\u043c\u0435 \u0444\u0438\u0448\u043e\u0432\u0435": "\u041d\u0435 \u0443\u0441\u043f\u044f\u0445\u043c\u0435 \u0434\u0430 \u0433\u0435\u043d\u0435\u0440\u0438\u0440\u0430\u043c\u0435 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438",
        "\u0424\u0438\u0448\u043e\u0432\u0435\u0442\u0435 \u0441\u0430 \u043f\u043e\u0434\u0431\u0440\u0430\u043d\u0438": "\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438\u0442\u0435 \u0441\u0430 \u043f\u043e\u0434\u0431\u0440\u0430\u043d\u0438",
        "\u043d\u044f\u043a\u043e\u043b\u043a\u043e \u0444\u0438\u0448\u0430": "\u043d\u044f\u043a\u043e\u043b\u043a\u043e \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u0437\u0430 \u0435\u0434\u0438\u043d \u0444\u0438\u0448",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text

def _load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return fallback



def _score_value(item: dict[str, Any]) -> float | None:
    preferred_keys = [
        "ensemble_score",
        "v45_score",
        "final_score",
        "combined_score",
        "model_score",
        "probability",
        "model_probability",
        "score",
    ]

    for key in preferred_keys:
        if key not in item:
            continue
        try:
            value = float(item[key])
        except Exception:
            continue
        if value != value:
            continue
        return value

    return None



def _extract_scores() -> list[dict[str, Any]]:
    data = _load_json(V45_SCORES_PATH, [])
    rows: list[dict[str, Any]] = []

    def add_row(number: Any, value: Any) -> None:
        try:
            n = int(number)
        except Exception:
            return
        if not 1 <= n <= 49:
            return

        if isinstance(value, dict):
            item = dict(value)
            item.setdefault("number", n)
            score = _score_value(item)
            if score is None:
                return
            rows.append({"number": n, "score": score, "raw": item})
            return

        try:
            score = float(value)
        except Exception:
            return
        if score != score:
            return
        rows.append({"number": n, "score": score, "raw": {"number": n, "score": score}})

    def list_has_number_scores(items: list[Any]) -> bool:
        dict_items = [item for item in items if isinstance(item, dict)]
        if not dict_items:
            return False
        with_number = 0
        with_score = 0
        for item in dict_items:
            if any(key in item for key in ["number", "n", "main_number"]):
                with_number += 1
            if _score_value(item) is not None:
                with_score += 1
        return with_number >= max(3, len(dict_items) // 2) and with_score >= max(3, len(dict_items) // 2)

    def consume_list(items: list[Any]) -> bool:
        if not list_has_number_scores(items):
            return False

        for item in items:
            if not isinstance(item, dict):
                continue
            number = item.get("number", item.get("n", item.get("main_number")))
            add_row(number, item)
        return True

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            # Direct mapping: {"1": 0.12, "2": 0.09, ...}
            numeric_keys = [key for key in obj.keys() if str(key).isdigit()]
            if len(numeric_keys) >= 6:
                for key in numeric_keys:
                    value = obj.get(key)
                    if isinstance(value, (int, float, dict)):
                        add_row(key, value)

            # Prefer known containers.
            for key in [
                "scores",
                "number_scores",
                "latest_scores",
                "latest_number_scores",
                "top_numbers",
                "numbers",
                "number_rankings",
            ]:
                value = obj.get(key)
                if isinstance(value, list) and consume_list(value):
                    return

            for value in obj.values():
                if isinstance(value, (dict, list)):
                    walk(value)

        elif isinstance(obj, list):
            if consume_list(obj):
                return
            for item in obj:
                if isinstance(item, (dict, list)):
                    walk(item)

    walk(data)

    if not rows:
        return [{"number": n, "score": 1.0 / 49.0, "raw": {}} for n in range(1, 50)]

    best_by_number: dict[int, dict[str, Any]] = {}
    for row in rows:
        n = row["number"]
        if n not in best_by_number or row["score"] > best_by_number[n]["score"]:
            best_by_number[n] = row

    raw_scores = [row["score"] for row in best_by_number.values()]
    min_score = min(raw_scores)
    max_score = max(raw_scores)

    normalized: dict[int, dict[str, Any]] = {}
    for n in range(1, 50):
        if n in best_by_number:
            row = best_by_number[n]
            if max_score > min_score:
                score = (row["score"] - min_score) / (max_score - min_score)
            else:
                score = 0.5
            normalized[n] = {"number": n, "score": float(score), "raw": row.get("raw", {})}
        else:
            normalized[n] = {"number": n, "score": 0.0, "raw": {}}

    return sorted(normalized.values(), key=lambda x: (x["score"], -x["number"]), reverse=True)


def _load_seed_tickets() -> list[list[int]]:
    data = _load_json(V45_TICKETS_PATH, [])
    tickets: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()

    def add_ticket(values: Any) -> None:
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
            tickets.append(cleaned)

    def walk(obj: Any) -> None:
        if isinstance(obj, list):
            add_ticket(obj)
            for item in obj:
                walk(item)
            return

        if isinstance(obj, dict):
            for key in [
                "numbers",
                "combination",
                "ticket",
                "primary_numbers",
                "main_numbers",
                "selected_numbers",
            ]:
                if key in obj:
                    add_ticket(obj.get(key))

            for value in obj.values():
                if isinstance(value, (dict, list)):
                    walk(value)

    walk(data)
    return tickets


def _combo_sum(combo: list[int]) -> int:
    return sum(combo)


def _odd_even(combo: list[int]) -> tuple[int, int]:
    odd = sum(1 for n in combo if n % 2 == 1)
    return odd, 6 - odd


def _low_high(combo: list[int]) -> tuple[int, int]:
    low = sum(1 for n in combo if n <= 24)
    return low, 6 - low


def _consecutive_pairs(combo: list[int]) -> int:
    ordered = sorted(combo)
    return sum(1 for a, b in zip(ordered, ordered[1:]) if b - a == 1)


def _max_overlap(combo: list[int], existing: list[list[int]]) -> int:
    s = set(combo)
    if not existing:
        return 0
    return max(len(s.intersection(set(other))) for other in existing)


def _structure_penalty(combo: list[int]) -> float:
    odd, even = _odd_even(combo)
    low, high = _low_high(combo)
    total = _combo_sum(combo)
    consecutive = _consecutive_pairs(combo)

    penalty = 0.0

    if odd not in {2, 3, 4}:
        penalty += 0.08
    if low not in {2, 3, 4}:
        penalty += 0.08
    if total < 100 or total > 200:
        penalty += 0.10
    if consecutive > 2:
        penalty += 0.10

    ranges = [
        sum(1 for n in combo if 1 <= n <= 9),
        sum(1 for n in combo if 10 <= n <= 19),
        sum(1 for n in combo if 20 <= n <= 29),
        sum(1 for n in combo if 30 <= n <= 39),
        sum(1 for n in combo if 40 <= n <= 49),
    ]
    if max(ranges) >= 4:
        penalty += 0.10

    return penalty



def _combo_score(combo: list[int], score_map: dict[int, float], style: str, existing: list[list[int]]) -> float:
    base = sum(score_map.get(n, 0.0) for n in combo) / 6.0
    penalty = _structure_penalty(combo)

    overlap = _max_overlap(combo, existing)
    if overlap > 2:
        penalty += 0.18 * (overlap - 2)

    if style == "balanced":
        penalty += abs(_combo_sum(combo) - 150) / 1000.0
    elif style == "recency":
        base *= 1.04
    elif style == "coverage":
        penalty += overlap * 0.05
    elif style == "creative":
        odd, even = _odd_even(combo)
        low, high = _low_high(combo)
        if odd in {2, 4} and low in {2, 4}:
            base *= 1.02

    return max(0.0, min(1.0, base - penalty))


def _candidate_pool(scores: list[dict[str, Any]], strength: str) -> list[int]:
    ordered = [int(row["number"]) for row in scores]

    if strength == "strict":
        pool_size = 22
    elif strength == "wide":
        pool_size = 34
    else:
        pool_size = 28

    return ordered[:pool_size]


def _generate_tickets(
    ticket_count: int,
    style: str,
    strength: str,
    max_overlap: int,
    include_seeds: bool,
    random_seed: int,
) -> list[dict[str, Any]]:
    scores = _extract_scores()
    score_map = {int(row["number"]): float(row["score"]) for row in scores}
    pool = _candidate_pool(scores, strength)

    rng = random.Random(random_seed)
    selected: list[list[int]] = []

    if include_seeds:
        for seed in _load_seed_tickets():
            if len(selected) >= ticket_count:
                break
            if _max_overlap(seed, selected) <= max_overlap:
                selected.append(seed)

    all_candidates: list[list[int]] = []

    # Build a controlled candidate set: all combos from top pool may be too many,
    # so mix deterministic top windows with random samples.
    top_pool = pool[: min(len(pool), 26)]
    for combo in itertools.combinations(top_pool, 6):
        combo_list = sorted(combo)
        if _structure_penalty(combo_list) <= 0.20:
            all_candidates.append(combo_list)

    if len(all_candidates) < 4000:
        attempts = 9000
        seen = {tuple(c) for c in all_candidates}
        for _ in range(attempts):
            combo = sorted(rng.sample(pool, 6))
            key = tuple(combo)
            if key in seen:
                continue
            seen.add(key)
            if _structure_penalty(combo) <= 0.25:
                all_candidates.append(combo)

    while len(selected) < ticket_count and all_candidates:
        ranked = sorted(
            all_candidates,
            key=lambda combo: _combo_score(combo, score_map, style, selected),
            reverse=True,
        )

        picked = None
        for combo in ranked:
            if _max_overlap(combo, selected) <= max_overlap:
                picked = combo
                break

        if picked is None:
            if max_overlap < 5:
                max_overlap += 1
                continue
            picked = ranked[0]

        selected.append(picked)
        all_candidates = [c for c in all_candidates if c != picked]

    result: list[dict[str, Any]] = []
    for index, combo in enumerate(selected[:ticket_count], start=1):
        odd, even = _odd_even(combo)
        low, high = _low_high(combo)
        result.append(
            {
                "index": index,
                "numbers": combo,
                "score": round(_combo_score(combo, score_map, style, [c for c in selected if c != combo]), 3),
                "sum": _combo_sum(combo),
                "odd_even": f"{odd} / {even}",
                "low_high": f"{low} / {high}",
                "consecutive_pairs": _consecutive_pairs(combo),
                "max_overlap": _max_overlap(combo, [c for c in selected if c != combo]),
            }
        )

    return result


def _style_label(style: str) -> str:
    labels = {
        "balanced": T("\\u0411\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d"),
        "recency": T("\\u0421\\u043a\\u043e\\u0440\\u043e\\u0448\\u043d\\u0430 \\u0430\\u043a\\u0442\\u0438\\u0432\\u043d\\u043e\\u0441\\u0442"),
        "coverage": T("\\u041d\\u0438\\u0441\\u043a\\u043e \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435"),
        "creative": T("\\u041f\\u043e-\\u0441\\u043c\\u0435\\u0441\\u0435\\u043d \\u0441\\u0442\\u0438\\u043b"),
    }
    return labels.get(style, style)


def _render_ticket(ticket: dict[str, Any]) -> None:
    title = T("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f") + f" {ticket['index']}"
    st.markdown(f"### {title}")

    separator = T("\\u00a0\\u00a0\\u2022\\u00a0\\u00a0")
    numbers = separator.join(str(n) for n in ticket["numbers"])
    st.markdown(
        f"""
<div style="display:inline-block;padding:0.65rem 0.85rem;border-radius:0.35rem;background:#171b24;font-size:1.6rem;font-weight:700;color:#56e685;letter-spacing:0.06rem;">
{numbers}
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(T("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430"), str(ticket["score"]))
    c2.metric(T("\\u041d\\u0435\\u0447\\u0435\\u0442\\u043d\\u0438 / \\u0447\\u0435\\u0442\\u043d\\u0438"), ticket["odd_even"])
    c3.metric(T("\\u041d\\u0438\\u0441\\u043a\\u0438 / \\u0432\\u0438\\u0441\\u043e\\u043a\\u0438"), ticket["low_high"])
    c4.metric(T("\\u0421\\u0443\\u043c\\u0430"), str(ticket["sum"]))
    c5.metric(T("\\u041c\\u0430\\u043a\\u0441. \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435"), str(ticket["max_overlap"]))

    with st.expander(T("\\u041e\\u0431\\u044f\\u0441\\u043d\\u0435\\u043d\\u0438\\u0435")):
        st.markdown(
            T(
                "\\u0422\\u0430\\u0437\\u0438 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f \\u0435 \\u043f\\u043e\\u0434\\u0431\\u0440\\u0430\\u043d\\u0430 \\u0447\\u0440\\u0435\\u0437 \\u0441\\u043c\\u0435\\u0441 \\u043e\\u0442 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0441\\u0438\\u0433\\u043d\\u0430\\u043b\\u0438, \\u0431\\u0430\\u043b\\u0430\\u043d\\u0441 \\u043d\\u0430 \\u0444\\u0438\\u0448\\u0430 \\u0438 \\u043a\\u043e\\u043d\\u0442\\u0440\\u043e\\u043b \\u0437\\u0430 \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435. \\u0422\\u043e\\u0432\\u0430 \\u043d\\u0435 \\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f \\u0437\\u0430 \\u043f\\u0435\\u0447\\u0430\\u043b\\u0431\\u0430."
            )
        )


def render() -> None:
    st.title(T("\\u0413\\u0435\\u043d\\u0435\\u0440\\u0430\\u0442\\u043e\\u0440 \\u043d\\u0430 \\u0444\\u0438\\u0448\\u043e\\u0432\\u0435"))

    st.caption(
        T(
            "\\u0422\\u0430\\u0437\\u0438 \\u0441\\u0442\\u0440\\u0430\\u043d\\u0438\\u0446\\u0430 \\u043f\\u043e\\u043c\\u0430\\u0433\\u0430 \\u0434\\u0430 \\u0441\\u0435 \\u0438\\u0437\\u0433\\u0440\\u0430\\u0434\\u044f\\u0442 \\u043d\\u044f\\u043a\\u043e\\u043b\\u043a\\u043e \\u0444\\u0438\\u0448\\u0430 \\u0441 \\u043d\\u0438\\u0441\\u043a\\u043e \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435, \\u0431\\u0430\\u043b\\u0430\\u043d\\u0441 \\u0438 \\u043e\\u0431\\u044f\\u0441\\u043d\\u0438\\u043c \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0438\\u0437\\u0431\\u043e\\u0440."
        )
    )

    st.warning(
        T(
            "\\u0412\\u0430\\u0436\\u043d\\u043e: \\u0442\\u043e\\u0432\\u0430 \\u0435 \\u0433\\u0435\\u043d\\u0435\\u0440\\u0430\\u0442\\u043e\\u0440 \\u0437\\u0430 \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0434\\u0438\\u0441\\u0446\\u0438\\u043f\\u043b\\u0438\\u043d\\u0438\\u0440\\u0430\\u043d \\u0438\\u0437\\u0431\\u043e\\u0440, \\u043d\\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f \\u0437\\u0430 \\u043f\\u0435\\u0447\\u0430\\u043b\\u0431\\u0430."
        )
    )

    scores = _extract_scores()
    seed_tickets = _load_seed_tickets()

    with st.sidebar:
        st.markdown("---")
        st.markdown(T("### \\u041d\\u0430\\u0441\\u0442\\u0440\\u043e\\u0439\\u043a\\u0438 \\u043d\\u0430 \\u0444\\u0438\\u0448\\u043e\\u0432\\u0435\\u0442\\u0435"))

        ticket_count = st.slider(T("\\u0411\\u0440\\u043e\\u0439 \\u0444\\u0438\\u0448\\u043e\\u0432\\u0435"), min_value=1, max_value=10, value=4, step=1)

        style_labels = {
            T("\\u0411\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d"): "balanced",
            T("\\u0421\\u043a\\u043e\\u0440\\u043e\\u0448\\u043d\\u0430 \\u0430\\u043a\\u0442\\u0438\\u0432\\u043d\\u043e\\u0441\\u0442"): "recency",
            T("\\u041d\\u0438\\u0441\\u043a\\u043e \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435"): "coverage",
            T("\\u041f\\u043e-\\u0441\\u043c\\u0435\\u0441\\u0435\\u043d \\u0441\\u0442\\u0438\\u043b"): "creative",
        }

        style_display = st.selectbox(
            T("\\u0421\\u0442\\u0438\\u043b"),
            list(style_labels.keys()),
            index=0,
        )
        style = style_labels[style_display]

        strength_labels = {
            T("\\u0421\\u0442\\u0440\\u043e\\u0433 \\u0438\\u0437\\u0431\\u043e\\u0440"): "strict",
            T("\\u041d\\u043e\\u0440\\u043c\\u0430\\u043b\\u0435\\u043d \\u0438\\u0437\\u0431\\u043e\\u0440"): "normal",
            T("\\u041f\\u043e-\\u0448\\u0438\\u0440\\u043e\\u043a \\u0438\\u0437\\u0431\\u043e\\u0440"): "wide",
        }

        strength_display = st.selectbox(
            T("\\u041e\\u0431\\u0445\\u0432\\u0430\\u0442 \\u043d\\u0430 \\u0447\\u0438\\u0441\\u043b\\u0430\\u0442\\u0430"),
            list(strength_labels.keys()),
            index=1,
        )
        strength = strength_labels[strength_display]

        max_overlap = st.slider(T("\\u041c\\u0430\\u043a\\u0441. \\u043e\\u0431\\u0449\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430 \\u043c\\u0435\\u0436\\u0434\\u0443 \\u0444\\u0438\\u0448\\u043e\\u0432\\u0435"), min_value=1, max_value=5, value=2, step=1)
        include_seeds = st.checkbox(T("\\u0418\\u0437\\u043f\\u043e\\u043b\\u0437\\u0432\\u0430\\u0439 \\u0442\\u0435\\u043a\\u0443\\u0449\\u0438\\u0442\\u0435 Pro \\u0444\\u0438\\u0448\\u043e\\u0432\\u0435 \\u043a\\u0430\\u0442\\u043e \\u043e\\u0441\\u043d\\u043e\\u0432\\u0430"), value=True)
        random_seed = st.number_input(T("\\u0421\\u0435\\u043c\\u0435 \\u0437\\u0430 \\u043f\\u043e\\u0432\\u0442\\u043e\\u0440\\u044f\\u0435\\u043c \\u0438\\u0437\\u0431\\u043e\\u0440"), min_value=1, max_value=999999, value=48, step=1)

    c1, c2, c3 = st.columns(3)
    c1.metric(T("\\u041d\\u0430\\u043b\\u0438\\u0447\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u043e\\u0432\\u0438 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0438"), str(len(scores)))
    c2.metric(T("\\u041d\\u0430\\u043b\\u0438\\u0447\\u043d\\u0438 Pro \\u0444\\u0438\\u0448\\u043e\\u0432\\u0435"), str(len(seed_tickets)))
    c3.metric(T("\\u0418\\u0437\\u0431\\u0440\\u0430\\u043d \\u0441\\u0442\\u0438\\u043b"), _style_label(style))

    tickets = _generate_tickets(
        ticket_count=int(ticket_count),
        style=style,
        strength=strength,
        max_overlap=int(max_overlap),
        include_seeds=bool(include_seeds),
        random_seed=int(random_seed),
    )

    st.subheader(T("\\u041f\\u0440\\u0435\\u0434\\u043b\\u043e\\u0436\\u0435\\u043d\\u0438 \\u0444\\u0438\\u0448\\u043e\\u0432\\u0435"))

    if not tickets:
        st.error(T("\\u041d\\u0435 \\u0443\\u0441\\u043f\\u044f\\u0445\\u043c\\u0435 \\u0434\\u0430 \\u0433\\u0435\\u043d\\u0435\\u0440\\u0438\\u0440\\u0430\\u043c\\u0435 \\u0444\\u0438\\u0448\\u043e\\u0432\\u0435 \\u0441 \\u0442\\u0435\\u0437\\u0438 \\u043d\\u0430\\u0441\\u0442\\u0440\\u043e\\u0439\\u043a\\u0438. \\u041e\\u043f\\u0438\\u0442\\u0430\\u0439 \\u0441 \\u043f\\u043e-\\u0448\\u0438\\u0440\\u043e\\u043a \\u0438\\u0437\\u0431\\u043e\\u0440 \\u0438\\u043b\\u0438 \\u043f\\u043e-\\u0432\\u0438\\u0441\\u043e\\u043a\\u043e \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435."))
        return

    for ticket in tickets:
        _render_ticket(ticket)
        st.divider()

    export_df = pd.DataFrame(
        [
            {
                T("\\u041f\\u043e\\u043b\\u0435"): row["index"],
                T("\\u0427\\u0438\\u0441\\u043b\\u0430"): " ".join(str(n) for n in row["numbers"]),
                T("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430"): row["score"],
                T("\\u0421\\u0443\\u043c\\u0430"): row["sum"],
                T("\\u041d\\u0435\\u0447\\u0435\\u0442\\u043d\\u0438 / \\u0447\\u0435\\u0442\\u043d\\u0438"): row["odd_even"],
                T("\\u041d\\u0438\\u0441\\u043a\\u0438 / \\u0432\\u0438\\u0441\\u043e\\u043a\\u0438"): row["low_high"],
            }
            for row in tickets
        ]
    )

    st.subheader(T("\\u0422\\u0430\\u0431\\u043b\\u0438\\u0446\\u0430 \\u0437\\u0430 \\u043a\\u043e\\u043f\\u0438\\u0440\\u0430\\u043d\\u0435"))
    st.dataframe(export_df, hide_index=True, use_container_width=True)

    csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label=T("\\u0421\\u0432\\u0430\\u043b\\u0438 CSV \\u0441 \\u0444\\u0438\\u0448\\u043e\\u0432\\u0435"),
        data=csv_bytes,
        file_name="ticket_builder_export.csv",
        mime="text/csv",
    )

    st.info(
        T(
            "\\u0424\\u0438\\u0448\\u043e\\u0432\\u0435\\u0442\\u0435 \\u0441\\u0430 \\u043f\\u043e\\u0434\\u0431\\u0440\\u0430\\u043d\\u0438 \\u0447\\u0440\\u0435\\u0437 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0438 \\u043e\\u0442 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u043c\\u043e\\u0434\\u0435\\u043b, \\u0431\\u0430\\u043b\\u0430\\u043d\\u0441 \\u0438 \\u043e\\u0433\\u0440\\u0430\\u043d\\u0438\\u0447\\u0435\\u043d\\u043e \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435. \\u0422\\u043e\\u0432\\u0430 \\u043d\\u0435 \\u043f\\u0440\\u043e\\u043c\\u0435\\u043d\\u044f \\u043c\\u0430\\u0442\\u0435\\u043c\\u0430\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438\\u044f \\u0448\\u0430\\u043d\\u0441 \\u043d\\u0430 \\u0438\\u0433\\u0440\\u0430\\u0442\\u0430."
        )
    )

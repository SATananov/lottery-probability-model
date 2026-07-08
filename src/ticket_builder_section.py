
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
    st.dataframe(export_df, hide_index=True, width="stretch")

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

# === Step 52 Smart Ticket Builder Integration ===
from pathlib import Path as _Step52Path
from typing import Any as _Step52Any
import json as _step52_json

import pandas as _step52_pd
import streamlit as _step52_st


_STEP52_ROOT = _Step52Path(__file__).resolve().parents[1]
_STEP52_SUMMARY_JSON = _STEP52_ROOT / "reports" / "v51_ticket_portfolio_summary.json"
_STEP52_SCORE_CSV = _STEP52_ROOT / "reports" / "v51_current_pro_ticket_score.csv"


def _step52_t(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


def _step52_read_json(path: _Step52Path) -> dict[str, _Step52Any]:
    if not path.exists():
        return {}
    try:
        data = _step52_json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _step52_read_csv(path: _Step52Path) -> _step52_pd.DataFrame:
    if not path.exists():
        return _step52_pd.DataFrame()
    try:
        return _step52_pd.read_csv(path)
    except Exception:
        return _step52_pd.DataFrame()


def _step52_rating_label(value: str) -> str:
    labels = {
        "strong": _step52_t("\\u0421\\u0438\\u043b\\u0435\\u043d \\u0444\\u0438\\u0448"),
        "balanced": _step52_t("\\u0411\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d \\u0444\\u0438\\u0448"),
        "medium": _step52_t("\\u0421\\u0440\\u0435\\u0434\\u0435\\u043d \\u0444\\u0438\\u0448"),
        "weak": _step52_t("\\u041d\\u0435\\u0431\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d \\u0444\\u0438\\u0448"),
        "missing": _step52_t("\\u041d\\u044f\\u043c\\u0430 \\u0434\\u0430\\u043d\\u043d\\u0438"),
    }
    return labels.get(str(value), str(value))


def _step52_warning_label(code: str) -> str:
    labels = {
        "missing_combinations": _step52_t("\\u041d\\u044f\\u043c\\u0430 \\u043d\\u0430\\u043b\\u0438\\u0447\\u043d\\u0438 Pro \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438."),
        "high_average_overlap": _step52_t("\\u0421\\u0440\\u0435\\u0434\\u043d\\u043e\\u0442\\u043e \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435 \\u043c\\u0435\\u0436\\u0434\\u0443 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438\\u0442\\u0435 \\u0435 \\u0432\\u0438\\u0441\\u043e\\u043a\\u043e."),
        "high_max_overlap": _step52_t("\\u0418\\u043c\\u0430 \\u0434\\u0432\\u0435 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438 \\u0441 \\u0442\\u0432\\u044a\\u0440\\u0434\\u0435 \\u043c\\u043d\\u043e\\u0433\\u043e \\u043e\\u0431\\u0449\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430."),
        "too_much_repetition": _step52_t("\\u041d\\u044f\\u043a\\u043e\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430 \\u0441\\u0435 \\u043f\\u043e\\u0432\\u0442\\u0430\\u0440\\u044f\\u0442 \\u0442\\u0432\\u044a\\u0440\\u0434\\u0435 \\u0447\\u0435\\u0441\\u0442\\u043e \\u0432 \\u0446\\u0435\\u043b\\u0438\\u044f \\u0444\\u0438\\u0448."),
        "weak_combo_structure": _step52_t("\\u0421\\u0440\\u0435\\u0434\\u043d\\u0430\\u0442\\u0430 \\u0441\\u0442\\u0440\\u0443\\u043a\\u0442\\u0443\\u0440\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438\\u0442\\u0435 \\u0435 \\u043d\\u0438\\u0441\\u043a\\u0430."),
        "low_number_coverage": _step52_t("\\u0424\\u0438\\u0448\\u044a\\u0442 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430 \\u0442\\u0432\\u044a\\u0440\\u0434\\u0435 \\u043c\\u0430\\u043b\\u043a\\u043e \\u0443\\u043d\\u0438\\u043a\\u0430\\u043b\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430."),
    }
    return labels.get(str(code), str(code))


def _step52_strength_label(code: str) -> str:
    labels = {
        "good_diversity": _step52_t("\\u0414\\u043e\\u0431\\u0440\\u043e \\u0440\\u0430\\u0437\\u043d\\u043e\\u043e\\u0431\\u0440\\u0430\\u0437\\u0438\\u0435 \\u043c\\u0435\\u0436\\u0434\\u0443 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438\\u0442\\u0435."),
        "controlled_repetition": _step52_t("\\u041f\\u043e\\u0432\\u0442\\u043e\\u0440\\u0435\\u043d\\u0438\\u044f\\u0442\\u0430 \\u043d\\u0430 \\u0447\\u0438\\u0441\\u043b\\u0430 \\u0441\\u0430 \\u043a\\u043e\\u043d\\u0442\\u0440\\u043e\\u043b\\u0438\\u0440\\u0430\\u043d\\u0438."),
        "solid_combo_structure": _step52_t("\\u041e\\u0442\\u0434\\u0435\\u043b\\u043d\\u0438\\u0442\\u0435 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438 \\u0438\\u043c\\u0430\\u0442 \\u0434\\u043e\\u0431\\u0440\\u0430 \\u0441\\u0442\\u0440\\u0443\\u043a\\u0442\\u0443\\u0440\\u0430."),
        "good_number_coverage": _step52_t("\\u0424\\u0438\\u0448\\u044a\\u0442 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430 \\u0434\\u043e\\u0431\\u044a\\u0440 \\u0431\\u0440\\u043e\\u0439 \\u0443\\u043d\\u0438\\u043a\\u0430\\u043b\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430."),
    }
    return labels.get(str(code), str(code))


def _step52_rename_combo_columns(df: _step52_pd.DataFrame) -> _step52_pd.DataFrame:
    rename = {
        "combination": _step52_t("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f"),
        "combo_score": _step52_t("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430"),
        "pair_average": _step52_t("\\u0421\\u0440\\u0435\\u0434\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438"),
        "strong_pairs": _step52_t("\\u0421\\u0438\\u043b\\u043d\\u0438 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438"),
        "group_average": _step52_t("\\u0421\\u0440\\u0435\\u0434\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438"),
        "strong_groups": _step52_t("\\u0421\\u0438\\u043b\\u043d\\u0438 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438"),
        "sum": _step52_t("\\u0421\\u0443\\u043c\\u0430"),
        "even_count": _step52_t("\\u0427\\u0435\\u0442\\u043d\\u0438"),
        "low_count": _step52_t("\\u041d\\u0438\\u0441\\u043a\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"),
        "range_span": _step52_t("\\u0420\\u0430\\u0437\\u043c\\u0430\\u0445"),
        "consecutive_pairs": _step52_t("\\u041f\\u043e\\u0440\\u0435\\u0434\\u043d\\u0438 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438"),
    }

    preferred = [
        "combination",
        "combo_score",
        "pair_average",
        "strong_pairs",
        "group_average",
        "strong_groups",
        "sum",
        "even_count",
        "low_count",
        "range_span",
        "consecutive_pairs",
    ]

    cols = [col for col in preferred if col in df.columns]
    remaining = [col for col in df.columns if col not in cols]
    return df[cols + remaining].rename(columns=rename)


def _step52_render_smart_ticket_intelligence() -> None:
    summary = _step52_read_json(_STEP52_SUMMARY_JSON)
    df = _step52_read_csv(_STEP52_SCORE_CSV)

    _step52_st.divider()
    _step52_st.subheader(_step52_t("\\u0418\\u043d\\u0442\\u0435\\u043b\\u0438\\u0433\\u0435\\u043d\\u0442\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u0442\\u0435\\u043a\\u0443\\u0449\\u0438\\u044f Pro \\u0444\\u0438\\u0448"))

    _step52_st.caption(
        _step52_t(
            "\\u0422\\u043e\\u0437\\u0438 \\u043f\\u0430\\u043d\\u0435\\u043b \\u0432\\u0437\\u0435\\u043c\\u0430 v51 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430\\u0442\\u0430 \\u0438 \\u044f \\u043f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430 \\u0434\\u0438\\u0440\\u0435\\u043a\\u0442\\u043d\\u043e \\u0432 \\u0433\\u0435\\u043d\\u0435\\u0440\\u0430\\u0442\\u043e\\u0440\\u0430. \\u0426\\u0435\\u043b\\u0442\\u0430 \\u0435 \\u043f\\u043e-\\u0434\\u043e\\u0431\\u0440\\u0430 \\u0441\\u0442\\u0440\\u0443\\u043a\\u0442\\u0443\\u0440\\u0430, \\u043d\\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f."
        )
    )

    if not summary or df.empty:
        _step52_st.info(
            _step52_t(
                "\\u041d\\u044f\\u043c\\u0430 \\u043d\\u0430\\u043b\\u0438\\u0447\\u043d\\u0430 v51 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430. \\u041f\\u0443\\u0441\\u043d\\u0438 \\u043f\\u044a\\u043b\\u0435\\u043d refresh v41 \\u2192 v51 \\u043e\\u0442 \\u0426\\u0435\\u043d\\u0442\\u044a\\u0440 \\u0437\\u0430 \\u043e\\u0431\\u0443\\u0447\\u0435\\u043d\\u0438\\u0435."
            )
        )
        return

    portfolio = summary.get("portfolio", {})
    metrics = portfolio.get("metrics", {})
    score = float(portfolio.get("overall_score", 0.0))
    rating = str(portfolio.get("rating", "missing"))

    c1, c2, c3, c4 = _step52_st.columns(4)
    c1.metric(_step52_t("\\u041e\\u0431\\u0449\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430"), f"{score:.2f} / 100")
    c2.metric(_step52_t("\\u041a\\u043b\\u0430\\u0441"), _step52_rating_label(rating))
    c3.metric(_step52_t("\\u0423\\u043d\\u0438\\u043a\\u0430\\u043b\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"), str(metrics.get("unique_numbers", "-")))
    c4.metric(_step52_t("\\u041c\\u0430\\u043a\\u0441. \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435"), str(metrics.get("max_overlap", "-")))

    _step52_st.progress(min(max(score / 100.0, 0.0), 1.0))

    with _step52_st.expander(_step52_t("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043f\\u043e \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438"), expanded=True):
        _step52_st.dataframe(_step52_rename_combo_columns(df), hide_index=True, width="stretch")

    col_left, col_right = _step52_st.columns(2)

    with col_left:
        _step52_st.markdown("**" + _step52_t("\\u0421\\u0438\\u043b\\u043d\\u0438 \\u0441\\u0442\\u0440\\u0430\\u043d\\u0438") + "**")
        strengths = portfolio.get("strength_codes", [])
        if strengths:
            for code in strengths:
                _step52_st.success(_step52_strength_label(str(code)))
        else:
            _step52_st.info(_step52_t("\\u041d\\u044f\\u043c\\u0430 \\u044f\\u0441\\u043d\\u043e \\u043e\\u0442\\u043a\\u0440\\u043e\\u0435\\u043d\\u0438 \\u0441\\u0438\\u043b\\u043d\\u0438 \\u0441\\u0442\\u0440\\u0430\\u043d\\u0438."))

    with col_right:
        _step52_st.markdown("**" + _step52_t("\\u0412\\u043d\\u0438\\u043c\\u0430\\u043d\\u0438\\u0435") + "**")
        warnings = portfolio.get("warning_codes", [])
        if warnings:
            for code in warnings:
                _step52_st.warning(_step52_warning_label(str(code)))
        else:
            _step52_st.success(_step52_t("\\u041d\\u044f\\u043c\\u0430 \\u043e\\u0441\\u043d\\u043e\\u0432\\u043d\\u0438 \\u0441\\u0442\\u0440\\u0443\\u043a\\u0442\\u0443\\u0440\\u043d\\u0438 \\u043f\\u0440\\u0435\\u0434\\u0443\\u043f\\u0440\\u0435\\u0436\\u0434\\u0435\\u043d\\u0438\\u044f."))

    _step52_st.caption(
        _step52_t(
            "\\u0410\\u043a\\u043e \\u043f\\u0440\\u043e\\u043c\\u0435\\u043d\\u0438\\u0448 \\u0434\\u0430\\u043d\\u043d\\u0438\\u0442\\u0435 \\u0438\\u043b\\u0438 \\u0433\\u0435\\u043d\\u0435\\u0440\\u0438\\u0440\\u0430\\u0448 \\u043d\\u043e\\u0432 Pro \\u0444\\u0438\\u0448, \\u043f\\u0443\\u0441\\u043d\\u0438 refresh \\u0434\\u043e v51, \\u0437\\u0430 \\u0434\\u0430 \\u0441\\u0435 \\u043e\\u0431\\u043d\\u043e\\u0432\\u0438 \\u0442\\u0430\\u0437\\u0438 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430."
        )
    )


_step52_original_render = render


def render() -> None:
    _step52_original_render()
    _step52_render_smart_ticket_intelligence()

# === Step 52.1 Dynamic Ticket Evaluation ===
import itertools as _step521_itertools
import re as _step521_re
from collections import Counter as _step521_Counter
from pathlib import Path as _Step521Path
from typing import Any as _Step521Any

import pandas as _step521_pd
import streamlit as _step521_st


_STEP521_ROOT = _Step521Path(__file__).resolve().parents[1]
_STEP521_PAIR_CSV = _STEP521_ROOT / "reports" / "v50_pair_scores.csv"
_STEP521_GROUP_CSV = _STEP521_ROOT / "reports" / "v50_group_scores.csv"
_STEP521_V51_SUMMARY = _STEP521_ROOT / "reports" / "v51_ticket_portfolio_summary.json"
_STEP521_V51_SCORE_CSV = _STEP521_ROOT / "reports" / "v51_current_pro_ticket_score.csv"


def _step521_t(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


def _step521_read_json(path: _Step521Path) -> dict[str, _Step521Any]:
    if not path.exists():
        return {}
    try:
        data = _step52_json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _step521_read_csv(path: _Step521Path) -> _step521_pd.DataFrame:
    if not path.exists():
        return _step521_pd.DataFrame()
    try:
        return _step521_pd.read_csv(path)
    except Exception:
        return _step521_pd.DataFrame()


def _step521_score_map(path: _Step521Path, key_col: str, score_col: str) -> dict[str, float]:
    df = _step521_read_csv(path)
    if df.empty or key_col not in df.columns or score_col not in df.columns:
        return {}

    result: dict[str, float] = {}
    for _, row in df.iterrows():
        try:
            result[str(row[key_col])] = float(row[score_col])
        except Exception:
            continue
    return result


def _step521_pair_key(a: int, b: int) -> str:
    x, y = sorted([a, b])
    return f"{x}-{y}"


def _step521_group_key(values: tuple[int, int, int]) -> str:
    return "-".join(str(x) for x in sorted(values))


def _step521_clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _step521_sum_bounds() -> dict[str, float]:
    summary = _step521_read_json(_STEP521_V51_SUMMARY)
    bounds = summary.get("sum_bounds", {})
    if isinstance(bounds, dict) and {"min_sum", "low_sum", "median_sum", "high_sum", "max_sum"}.issubset(bounds):
        try:
            return {key: float(bounds[key]) for key in ["min_sum", "low_sum", "median_sum", "high_sum", "max_sum"]}
        except Exception:
            pass

    return {
        "min_sum": 80.0,
        "low_sum": 105.0,
        "median_sum": 150.0,
        "high_sum": 195.0,
        "max_sum": 220.0,
    }


def _step521_sum_score(total: int, bounds: dict[str, float]) -> float:
    low = bounds["low_sum"]
    high = bounds["high_sum"]
    median = bounds["median_sum"]

    if low <= total <= high:
        distance = abs(total - median)
        span = max(high - low, 1.0)
        return _step521_clamp(1.0 - (distance / span) * 0.35)

    if total < low:
        distance = low - total
        span = max(low - bounds["min_sum"], 1.0)
        return _step521_clamp(0.75 - distance / span)

    distance = total - high
    span = max(bounds["max_sum"] - high, 1.0)
    return _step521_clamp(0.75 - distance / span)


def _step521_parse_combo_line(raw: str) -> list[int]:
    values = [int(x) for x in _step521_re.findall(r"\d+", raw)]
    cleaned = sorted({n for n in values if 1 <= n <= 49})
    if len(cleaned) != 6:
        return []
    return cleaned


def _step521_default_text() -> str:
    df = _step521_read_csv(_STEP521_V51_SCORE_CSV)
    if not df.empty and "combination" in df.columns:
        lines = []
        for value in df["combination"].dropna().tolist():
            combo = _step521_parse_combo_line(str(value))
            if combo:
                lines.append(" ".join(str(n) for n in combo))
        if lines:
            return "\n".join(lines)

    return "4 17 21 24 34 48\n6 12 25 31 37 45\n3 14 22 29 40 49\n8 19 27 33 41 46"


def _step521_combo_score(
    combo: list[int],
    pair_scores: dict[str, float],
    group_scores: dict[str, float],
    bounds: dict[str, float],
) -> dict[str, _Step521Any]:
    numbers = sorted(combo)

    pair_keys = [_step521_pair_key(a, b) for a, b in _step521_itertools.combinations(numbers, 2)]
    group_keys = [_step521_group_key(g) for g in _step521_itertools.combinations(numbers, 3)]

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
    range_score = _step521_clamp(range_span / 38.0)
    total_sum = sum(numbers)
    sum_balance = _step521_sum_score(total_sum, bounds)
    consecutive_penalty = _step521_clamp(consecutive_pairs / 3.0)

    raw = (
        0.28 * pair_average
        + 0.12 * group_average
        + 0.16 * even_balance
        + 0.16 * low_high_balance
        + 0.18 * sum_balance
        + 0.10 * range_score
    )

    score = _step521_clamp(raw - (0.08 * consecutive_penalty)) * 100.0

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


def _step521_portfolio_score(combo_rows: list[dict[str, _Step521Any]]) -> dict[str, _Step521Any]:
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
    counts = _step521_Counter(all_numbers)
    unique_numbers = len(counts)
    max_repeat = max(counts.values()) if counts else 0

    overlaps = []
    for left, right in _step521_itertools.combinations(combos, 2):
        overlaps.append(len(set(left) & set(right)))

    avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0.0
    max_overlap = max(overlaps) if overlaps else 0

    combo_avg = sum(float(row["combo_score"]) for row in combo_rows) / len(combo_rows)

    ideal_total_slots = max(len(combos) * 6, 1)
    coverage_score = unique_numbers / ideal_total_slots
    overlap_score = _step521_clamp(1.0 - avg_overlap / 3.0)
    repeat_score = _step521_clamp(1.0 - max(0, max_repeat - 1) / 3.0)

    portfolio_layer = 100.0 * (
        0.40 * overlap_score
        + 0.35 * coverage_score
        + 0.25 * repeat_score
    )

    overall = (0.68 * combo_avg) + (0.32 * portfolio_layer)
    overall = round(_step521_clamp(overall / 100.0) * 100.0, 2)

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
        },
    }


def _step521_rating_label(value: str) -> str:
    labels = {
        "strong": _step521_t("\\u0421\\u0438\\u043b\\u0435\\u043d \\u0444\\u0438\\u0448"),
        "balanced": _step521_t("\\u0411\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d \\u0444\\u0438\\u0448"),
        "medium": _step521_t("\\u0421\\u0440\\u0435\\u0434\\u0435\\u043d \\u0444\\u0438\\u0448"),
        "weak": _step521_t("\\u041d\\u0435\\u0431\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d \\u0444\\u0438\\u0448"),
        "missing": _step521_t("\\u041d\\u044f\\u043c\\u0430 \\u0434\\u0430\\u043d\\u043d\\u0438"),
    }
    return labels.get(str(value), str(value))


def _step521_warning_label(code: str) -> str:
    labels = {
        "missing_combinations": _step521_t("\\u041d\\u044f\\u043c\\u0430 \\u0432\\u044a\\u0432\\u0435\\u0434\\u0435\\u043d\\u0438 \\u0432\\u0430\\u043b\\u0438\\u0434\\u043d\\u0438 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438."),
        "high_average_overlap": _step521_t("\\u0421\\u0440\\u0435\\u0434\\u043d\\u043e\\u0442\\u043e \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435 \\u0435 \\u0432\\u0438\\u0441\\u043e\\u043a\\u043e."),
        "high_max_overlap": _step521_t("\\u0418\\u043c\\u0430 \\u0434\\u0432\\u0435 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438 \\u0441 \\u0442\\u0432\\u044a\\u0440\\u0434\\u0435 \\u043c\\u043d\\u043e\\u0433\\u043e \\u043e\\u0431\\u0449\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430."),
        "too_much_repetition": _step521_t("\\u041d\\u044f\\u043a\\u043e\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430 \\u0441\\u0435 \\u043f\\u043e\\u0432\\u0442\\u0430\\u0440\\u044f\\u0442 \\u0442\\u0432\\u044a\\u0440\\u0434\\u0435 \\u0447\\u0435\\u0441\\u0442\\u043e."),
        "weak_combo_structure": _step521_t("\\u0421\\u0440\\u0435\\u0434\\u043d\\u0430\\u0442\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438\\u0442\\u0435 \\u0435 \\u043d\\u0438\\u0441\\u043a\\u0430."),
        "low_number_coverage": _step521_t("\\u0424\\u0438\\u0448\\u044a\\u0442 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430 \\u0442\\u0432\\u044a\\u0440\\u0434\\u0435 \\u043c\\u0430\\u043b\\u043a\\u043e \\u0443\\u043d\\u0438\\u043a\\u0430\\u043b\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430."),
    }
    return labels.get(str(code), str(code))


def _step521_strength_label(code: str) -> str:
    labels = {
        "good_diversity": _step521_t("\\u0414\\u043e\\u0431\\u0440\\u043e \\u0440\\u0430\\u0437\\u043d\\u043e\\u043e\\u0431\\u0440\\u0430\\u0437\\u0438\\u0435 \\u043c\\u0435\\u0436\\u0434\\u0443 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438\\u0442\\u0435."),
        "controlled_repetition": _step521_t("\\u041f\\u043e\\u0432\\u0442\\u043e\\u0440\\u0435\\u043d\\u0438\\u044f\\u0442\\u0430 \\u0441\\u0430 \\u043a\\u043e\\u043d\\u0442\\u0440\\u043e\\u043b\\u0438\\u0440\\u0430\\u043d\\u0438."),
        "solid_combo_structure": _step521_t("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438\\u0442\\u0435 \\u0438\\u043c\\u0430\\u0442 \\u0434\\u043e\\u0431\\u0440\\u0430 \\u0441\\u0442\\u0440\\u0443\\u043a\\u0442\\u0443\\u0440\\u0430."),
        "good_number_coverage": _step521_t("\\u0424\\u0438\\u0448\\u044a\\u0442 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430 \\u0434\\u043e\\u0431\\u044a\\u0440 \\u0431\\u0440\\u043e\\u0439 \\u0443\\u043d\\u0438\\u043a\\u0430\\u043b\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430."),
    }
    return labels.get(str(code), str(code))


def _step521_rename_rows(df: _step521_pd.DataFrame) -> _step521_pd.DataFrame:
    rename = {
        "combination": _step521_t("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f"),
        "combo_score": _step521_t("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430"),
        "pair_average": _step521_t("\\u0421\\u0440\\u0435\\u0434\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438"),
        "strong_pairs": _step521_t("\\u0421\\u0438\\u043b\\u043d\\u0438 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438"),
        "group_average": _step521_t("\\u0421\\u0440\\u0435\\u0434\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438"),
        "strong_groups": _step521_t("\\u0421\\u0438\\u043b\\u043d\\u0438 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438"),
        "sum": _step521_t("\\u0421\\u0443\\u043c\\u0430"),
        "even_count": _step521_t("\\u0427\\u0435\\u0442\\u043d\\u0438"),
        "low_count": _step521_t("\\u041d\\u0438\\u0441\\u043a\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"),
        "range_span": _step521_t("\\u0420\\u0430\\u0437\\u043c\\u0430\\u0445"),
        "consecutive_pairs": _step521_t("\\u041f\\u043e\\u0440\\u0435\\u0434\\u043d\\u0438 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438"),
    }

    preferred = [
        "combination",
        "combo_score",
        "pair_average",
        "strong_pairs",
        "group_average",
        "strong_groups",
        "sum",
        "even_count",
        "low_count",
        "range_span",
        "consecutive_pairs",
    ]

    cols = [col for col in preferred if col in df.columns]
    remaining = [col for col in df.columns if col not in cols]
    return df[cols + remaining].rename(columns=rename)


def _step521_render_dynamic_ticket_evaluator() -> None:
    _step521_st.divider()
    _step521_st.subheader(_step521_t("\\u0414\\u0438\\u043d\\u0430\\u043c\\u0438\\u0447\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u043d\\u043e\\u0432 \\u0444\\u0438\\u0448"))

    _step521_st.caption(
        _step521_t(
            "\\u0412\\u044a\\u0432\\u0435\\u0434\\u0438 \\u0434\\u043e 8 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438, \\u043f\\u043e \\u0435\\u0434\\u043d\\u0430 \\u043d\\u0430 \\u0440\\u0435\\u0434. \\u0412\\u0441\\u044f\\u043a\\u0430 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f \\u0442\\u0440\\u044f\\u0431\\u0432\\u0430 \\u0434\\u0430 \\u0438\\u043c\\u0430 6 \\u0447\\u0438\\u0441\\u043b\\u0430 \\u043e\\u0442 1 \\u0434\\u043e 49."
        )
    )

    raw_text = _step521_st.text_area(
        _step521_t("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438 \\u0437\\u0430 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430"),
        value=_step521_default_text(),
        height=150,
    )

    combos = []
    invalid_lines = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        combo = _step521_parse_combo_line(stripped)
        if combo:
            combos.append(combo)
        else:
            invalid_lines.append(stripped)

    combos = combos[:8]

    if invalid_lines:
        _step521_st.warning(
            _step521_t("\\u0418\\u043c\\u0430 \\u0440\\u0435\\u0434\\u043e\\u0432\\u0435, \\u043a\\u043e\\u0438\\u0442\\u043e \\u043d\\u0435 \\u0441\\u0430 \\u0432\\u0430\\u043b\\u0438\\u0434\\u043d\\u0438 \\u0438 \\u0441\\u0430 \\u0438\\u0433\\u043d\\u043e\\u0440\\u0438\\u0440\\u0430\\u043d\\u0438.")
        )

    if not combos:
        _step521_st.info(_step521_t("\\u0412\\u044a\\u0432\\u0435\\u0434\\u0438 \\u043f\\u043e\\u043d\\u0435 \\u0435\\u0434\\u043d\\u0430 \\u0432\\u0430\\u043b\\u0438\\u0434\\u043d\\u0430 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f."))
        return

    pair_scores = _step521_score_map(_STEP521_PAIR_CSV, "pair", "pair_score")
    group_scores = _step521_score_map(_STEP521_GROUP_CSV, "group", "group_score")
    bounds = _step521_sum_bounds()

    rows = [_step521_combo_score(combo, pair_scores, group_scores, bounds) for combo in combos]
    portfolio = _step521_portfolio_score(rows)
    metrics = portfolio.get("metrics", {})
    score = float(portfolio.get("overall_score", 0.0))

    c1, c2, c3, c4 = _step521_st.columns(4)
    c1.metric(_step521_t("\\u041e\\u0431\\u0449\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430"), f"{score:.2f} / 100")
    c2.metric(_step521_t("\\u041a\\u043b\\u0430\\u0441"), _step521_rating_label(str(portfolio.get("rating", "missing"))))
    c3.metric(_step521_t("\\u0423\\u043d\\u0438\\u043a\\u0430\\u043b\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"), str(metrics.get("unique_numbers", "-")))
    c4.metric(_step521_t("\\u041c\\u0430\\u043a\\u0441. \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435"), str(metrics.get("max_overlap", "-")))

    _step521_st.progress(min(max(score / 100.0, 0.0), 1.0))

    _step521_st.dataframe(
        _step521_rename_rows(_step521_pd.DataFrame([{k: v for k, v in row.items() if k != "numbers"} for row in rows])),
        hide_index=True,
        width="stretch",
    )

    col_left, col_right = _step521_st.columns(2)

    with col_left:
        _step521_st.markdown("**" + _step521_t("\\u0421\\u0438\\u043b\\u043d\\u0438 \\u0441\\u0442\\u0440\\u0430\\u043d\\u0438") + "**")
        strengths = portfolio.get("strength_codes", [])
        if strengths:
            for code in strengths:
                _step521_st.success(_step521_strength_label(str(code)))
        else:
            _step521_st.info(_step521_t("\\u041d\\u044f\\u043c\\u0430 \\u044f\\u0441\\u043d\\u043e \\u043e\\u0442\\u043a\\u0440\\u043e\\u0435\\u043d\\u0438 \\u0441\\u0438\\u043b\\u043d\\u0438 \\u0441\\u0442\\u0440\\u0430\\u043d\\u0438."))

    with col_right:
        _step521_st.markdown("**" + _step521_t("\\u0412\\u043d\\u0438\\u043c\\u0430\\u043d\\u0438\\u0435") + "**")
        warnings = portfolio.get("warning_codes", [])
        if warnings:
            for code in warnings:
                _step521_st.warning(_step521_warning_label(str(code)))
        else:
            _step521_st.success(_step521_t("\\u041d\\u044f\\u043c\\u0430 \\u043e\\u0441\\u043d\\u043e\\u0432\\u043d\\u0438 \\u0441\\u0442\\u0440\\u0443\\u043a\\u0442\\u0443\\u0440\\u043d\\u0438 \\u043f\\u0440\\u0435\\u0434\\u0443\\u043f\\u0440\\u0435\\u0436\\u0434\\u0435\\u043d\\u0438\\u044f."))

    _step521_st.caption(
        _step521_t(
            "\\u0422\\u0430\\u0437\\u0438 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u0435 \\u0436\\u0438\\u0432\\u0430 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430 \\u0432 \\u0433\\u0435\\u043d\\u0435\\u0440\\u0430\\u0442\\u043e\\u0440\\u0430. \\u0422\\u044f \\u043d\\u0435 \\u0437\\u0430\\u043f\\u0438\\u0441\\u0432\\u0430 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438 \\u0438 \\u043d\\u0435 \\u0434\\u0430\\u0432\\u0430 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f."
        )
    )


_step521_original_render = render


def render() -> None:
    _step521_original_render()
    _step521_render_dynamic_ticket_evaluator()

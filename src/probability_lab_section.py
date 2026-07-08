from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None


ROOT = Path(__file__).resolve().parents[1]

V41_PATH = ROOT / "models" / "v41" / "v41_latest_predictions.json"
V42_TICKET_PATH = ROOT / "models" / "v42" / "v42_combined_prediction.json"
V42_SCORES_PATH = ROOT / "models" / "v42" / "v42_positive_negative_number_scores.json"
V43_TICKET_PATH = ROOT / "models" / "v43_1" / "v43_1_interval_rhythm_refined_prediction.json"
V43_SCORES_PATH = ROOT / "models" / "v43_1" / "v43_1_interval_rhythm_refined_scores.json"
FINAL_TICKET_PATH = ROOT / "models" / "v44_1" / "v44_1_final_ensemble_ticket_prediction.json"
FINAL_SCORES_PATH = ROOT / "models" / "v44_1" / "v44_1_final_ensemble_number_scores.json"


def txt(value: str) -> str:
    """Return safe Bulgarian UI text.

    If the value still contains literal unicode escapes, decode them once.
    If Python has already decoded the string to Cyrillic, return it unchanged.
    This prevents double-decoding mojibake / replacement-character text.
    """
    if "\\u" in value or "\\x" in value:
        return value.encode("utf-8").decode("unicode_escape")

    return value


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def score(value: Any) -> str:
    return f"{safe_float(value):.2f}"


def numbers_text(numbers: list[Any]) -> str:
    cleaned = []
    for value in numbers:
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if 1 <= number <= 49:
            cleaned.append(number)
    return " ".join(f"{number:02d}" for number in cleaned)


def collect_number_lists(value: Any, path: str = "") -> list[tuple[str, list[int]]]:
    found: list[tuple[str, list[int]]] = []

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            found.extend(collect_number_lists(child, child_path))

    elif isinstance(value, list):
        numbers: list[int] = []
        all_number_like = True

        for item in value:
            if isinstance(item, bool):
                all_number_like = False
                break

            try:
                number = int(item)
            except (TypeError, ValueError):
                all_number_like = False
                break

            numbers.append(number)

        if all_number_like and 1 <= len(numbers) <= 12 and all(1 <= number <= 49 for number in numbers):
            found.append((path, numbers))
        else:
            for index, child in enumerate(value):
                found.extend(collect_number_lists(child, f"{path}[{index}]"))

    return found


def extract_numbers(payload: dict[str, Any], keys: list[str]) -> list[int]:
    if not payload:
        return []

    # First try exact or near-exact top-level keys.
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            numbers = []
            for item in value:
                try:
                    number = int(item)
                except (TypeError, ValueError):
                    continue
                if 1 <= number <= 49:
                    numbers.append(number)
            if numbers:
                return numbers

    # Then search recursively, because some model artifacts store predictions nested.
    candidates = collect_number_lists(payload)
    if not candidates:
        return []

    def rank(candidate: tuple[str, list[int]]) -> tuple[int, int, int]:
        path_text, numbers = candidate
        lowered = path_text.lower()

        key_score = 0
        for key in keys:
            if key.lower() in lowered:
                key_score += 8

        for marker in ["sgd", "prediction", "latest", "recency", "frequency", "combined", "final", "numbers"]:
            if marker in lowered:
                key_score += 3

        length_score = 6 if len(numbers) == 6 else max(0, 5 - abs(len(numbers) - 6))

        return (key_score, length_score, -len(path_text))

    best_path, best_numbers = sorted(candidates, key=rank, reverse=True)[0]
    return best_numbers[:6]


def number_rows(rows: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    output = []
    for row in rows[:limit]:
        output.append(
            {
                txt("\\u0427\\u0438\\u0441\\u043b\\u043e"): int(row.get("number", 0)),
                txt("\\u0424\\u0438\\u043d\\u0430\\u043b\\u0435\\u043d \\u0440\\u0435\\u0437\\u0443\\u043b\\u0442\\u0430\\u0442"): score(row.get("final_ensemble_score")),
                txt("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0438\\u0440\\u0430\\u043d \\u0441\\u0438\\u0433\\u043d\\u0430\\u043b"): score(row.get("v42_combined_score")),
                txt("\\u0420\\u0438\\u0442\\u044a\\u043c"): score(row.get("rhythm_final_score")),
                txt("\\u0421\\u043b\\u0435\\u0434\\u0432\\u0430\\u0449 \\u043f\\u0440\\u043e\\u0437\\u043e\\u0440\\u0435\\u0446"): score(row.get("rhythm_next_window_score")),
                txt("\\u0418\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0441\\u0438\\u0433\\u043d\\u0430\\u043b"): score(row.get("rules_score")),
                txt("\\u041a\\u043e\\u043d\\u0441\\u0435\\u043d\\u0441\\u0443\\u0441"): int(row.get("consensus_hits", 0)),
                txt("\\u041f\\u0430\\u0443\\u0437\\u0430"): int(row.get("current_gap", 0)),
            }
        )
    return output


def show_table(rows: list[dict[str, Any]]) -> None:
    if not rows:
        st.info(txt("\\u041d\\u044f\\u043c\\u0430 \\u0434\\u0430\\u043d\\u043d\\u0438."))
        return

    if pd is None:
        st.dataframe(rows, width="stretch")
        return

    df = pd.DataFrame(rows)
    try:
        st.dataframe(df, width="stretch", hide_index=True)
    except TypeError:
        st.dataframe(df, width="stretch")


def render_css() -> None:
    st.markdown(
        """
        <style>
        .prob-hero {
            border: 1px solid rgba(214,174,84,.42);
            border-radius: 22px;
            padding: 24px 28px;
            margin: 10px 0 20px 0;
            background:
                radial-gradient(circle at top left, rgba(214,174,84,.15), transparent 36%),
                linear-gradient(135deg, rgba(24,27,33,.96), rgba(8,10,15,.98));
        }
        .prob-hero h1 {
            margin: 0 0 8px 0;
            font-size: 2.0rem;
            letter-spacing: -0.03em;
        }
        .prob-hero p {
            margin: 0;
            color: rgba(245,241,230,.70);
            line-height: 1.55;
            font-size: 1rem;
        }
        .prob-warning {
            border-left: 4px solid #d6ae54;
            border-radius: 12px;
            padding: 12px 16px;
            margin: 12px 0 20px 0;
            background: rgba(214,174,84,.12);
            color: rgba(245,241,230,.92);
            font-weight: 650;
        }
        .model-card {
            border: 1px solid rgba(255,255,255,.10);
            border-radius: 17px;
            padding: 16px 18px;
            background: rgba(255,255,255,.035);
            margin-bottom: 14px;
        }
        .model-title {
            font-size: 1.02rem;
            font-weight: 850;
            margin-bottom: 5px;
            color: #f5f1e6;
        }
        .model-text {
            color: rgba(245,241,230,.67);
            font-size: .92rem;
            line-height: 1.5;
        }
        .number-line {
            margin-top: 10px;
            font-size: 1.15rem;
            font-weight: 900;
            color: #4ee394;
            letter-spacing: .05em;
        }
        .combo-card {
            border: 1px solid rgba(38,184,117,.28);
            border-radius: 16px;
            padding: 14px 16px;
            margin-bottom: 10px;
            background: rgba(38,184,117,.055);
        }
        .combo-title {
            color: rgba(245,241,230,.75);
            font-weight: 750;
            margin-bottom: 7px;
        }
        .combo-numbers {
            color: #4ee394;
            font-size: 1.25rem;
            font-weight: 900;
            letter-spacing: .08em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_model_card(title: str, description: str, numbers: list[int] | None = None) -> None:
    number_html = ""
    if numbers:
        number_html = f'<div class="number-line">{numbers_text(numbers)}</div>'

    st.markdown(
        f"""
        <div class="model-card">
            <div class="model-title">{title}</div>
            <div class="model-text">{description}</div>
            {number_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def as_number_set(numbers: list[int]) -> set[int]:
    return {int(number) for number in numbers if 1 <= int(number) <= 49}


def relation_text(base: list[int], other: list[int]) -> str:
    base_set = as_number_set(base)
    other_set = as_number_set(other)

    if not base_set or not other_set:
        return ""

    if base_set == other_set:
        return txt("\u0421\u044a\u0432\u043f\u0430\u0434\u0430 \u0441 \u043e\u0441\u043d\u043e\u0432\u043d\u0438\u044f \u0440\u0438\u0442\u044a\u043c. \u0422\u043e\u0432\u0430 \u0435 \u043f\u043e\u0442\u0432\u044a\u0440\u0436\u0434\u0435\u043d\u0438\u0435 \u043e\u0442 \u043f\u043e\u0434\u0441\u0438\u0433\u043d\u0430\u043b, \u043d\u0435 \u0433\u0440\u0435\u0448\u043a\u0430.")

    added = sorted(other_set - base_set)
    removed = sorted(base_set - other_set)

    parts = []

    if added:
        parts.append(
            txt("\u0414\u043e\u0431\u0430\u0432\u044f: ") + numbers_text(added)
        )

    if removed:
        parts.append(
            txt("\u041e\u0442\u043f\u0430\u0434\u0430: ") + numbers_text(removed)
        )

    return txt("\u0420\u0430\u0437\u043b\u0438\u043a\u0430 \u0441\u043f\u0440\u044f\u043c\u043e \u043e\u0441\u043d\u043e\u0432\u043d\u0438\u044f \u0440\u0438\u0442\u044a\u043c: ") + "; ".join(parts)


def render_related_model_card(title: str, description: str, numbers: list[int], base_numbers: list[int]) -> None:
    relation = relation_text(base_numbers, numbers)

    if relation:
        description = description + " " + relation

    render_model_card(title, description, numbers)


def overlap_rows(layers: list[tuple[str, list[int]]], final_rows: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    score_map = {}

    for row in final_rows:
        try:
            number = int(row.get("number", 0))
        except (TypeError, ValueError):
            continue

        score_map[number] = safe_float(row.get("final_ensemble_score"))

    layer_hits: dict[int, list[str]] = {}

    for layer_name, numbers in layers:
        for number in sorted(as_number_set(numbers)):
            layer_hits.setdefault(number, []).append(layer_name)

    ranked = sorted(
        layer_hits.items(),
        key=lambda item: (len(item[1]), score_map.get(item[0], 0), -item[0]),
        reverse=True,
    )

    output = []

    for number, names in ranked[:limit]:
        output.append(
            {
                txt("\u0427\u0438\u0441\u043b\u043e"): number,
                txt("\u0421\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u044f"): len(names),
                txt("\u041c\u043e\u0434\u0435\u043b\u043d\u0438 \u0441\u043b\u043e\u0435\u0432\u0435"): ", ".join(names),
                txt("\u0424\u0438\u043d\u0430\u043b\u0435\u043d \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442"): score(score_map.get(number, 0)),
            }
        )

    return output


def render() -> None:
    render_css()

    v41 = load_json(V41_PATH)
    v42_ticket = load_json(V42_TICKET_PATH)
    v42_scores = load_json(V42_SCORES_PATH)
    v43_ticket = load_json(V43_TICKET_PATH)
    v43_scores = load_json(V43_SCORES_PATH)
    final_ticket = load_json(FINAL_TICKET_PATH)
    final_scores = load_json(FINAL_SCORES_PATH)

    st.markdown(
        f"""
        <div class="prob-hero">
            <h1>{txt("\u0412\u0435\u0440\u043e\u044f\u0442\u043d\u043e\u0441\u0442\u043d\u0430 \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f")}</h1>
            <p>{txt("\u0422\u0443\u043a \u0430\u043f\u044a\u0442 \u043e\u0431\u043e\u0431\u0449\u0430\u0432\u0430 \u0430\u043a\u0442\u0438\u0432\u043d\u0438\u0442\u0435 \u043c\u043e\u0434\u0435\u043b\u043d\u0438 \u0441\u043b\u043e\u0435\u0432\u0435, \u043f\u043e\u043a\u0430\u0437\u0432\u0430 \u043a\u044a\u0434\u0435 \u0442\u0435 \u0441\u044a\u0432\u043f\u0430\u0434\u0430\u0442 \u0438 \u043a\u0430\u043a \u0441\u0435 \u0441\u0442\u0438\u0433\u0430 \u0434\u043e \u0444\u0438\u043d\u0430\u043b\u043d\u043e\u0442\u043e \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u0435.")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="prob-warning">{txt("\u0412\u0430\u0436\u043d\u043e: \u0442\u043e\u0432\u0430 \u043d\u0435 \u0435 \u043f\u0435\u0447\u0435\u043b\u0438\u0432\u0448 \u043c\u043e\u0434\u0435\u043b \u0438 \u043d\u0435 \u0434\u0430\u0432\u0430 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f. \u041b\u043e\u0442\u0430\u0440\u0438\u0439\u043d\u0438\u0442\u0435 \u0442\u0435\u0433\u043b\u0435\u043d\u0438\u044f \u0441\u0430 \u0441\u043b\u0443\u0447\u0430\u0439\u043d\u0438; \u0442\u0443\u043a \u0438\u043c\u0430 \u0441\u0430\u043c\u043e \u0430\u043d\u0430\u043b\u0438\u0437 \u043d\u0430 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0438.")}</div>',
        unsafe_allow_html=True,
    )

    valid_draws = final_ticket.get("valid_draws") or v43_ticket.get("valid_draws") or "-"
    scored_numbers = len(final_scores.get("numbers", [])) or len(v43_scores.get("numbers", [])) or "-"
    final_combos = final_ticket.get("ticket_combinations", [])

    cols = st.columns(3)
    cols[0].metric(txt("\u0412\u0430\u043b\u0438\u0434\u043d\u0438 \u0442\u0438\u0440\u0430\u0436\u0438"), str(valid_draws))
    cols[1].metric(txt("\u041e\u0446\u0435\u043d\u0435\u043d\u0438 \u0447\u0438\u0441\u043b\u0430"), str(scored_numbers))
    cols[2].metric(txt("\u0424\u0438\u043d\u0430\u043b\u043d\u0438 \u0440\u0435\u0434\u043e\u0432\u0435 \u0432\u044a\u0432 \u0444\u0438\u0448\u0430"), str(len(final_combos)))

    v41_numbers = extract_numbers(
        v41,
        [
            "sgd_number_classifier",
            "recency_250_baseline",
            "frequency_baseline",
            "latest_predictions",
            "prediction",
            "numbers",
        ],
    )
    v42_numbers = extract_numbers(v42_ticket, ["numbers", "combined_numbers"])
    v43_final = extract_numbers(v43_ticket, ["final_refined_rhythm_numbers"])
    v43_next = extract_numbers(v43_ticket, ["next_window_numbers"])
    v43_overdue = extract_numbers(v43_ticket, ["overdue_watchlist_numbers"])

    st.subheader(txt("\u0410\u043a\u0442\u0438\u0432\u043d\u0438 \u043c\u043e\u0434\u0435\u043b\u043d\u0438 \u0441\u043b\u043e\u0435\u0432\u0435"))

    render_model_card(
        txt("\u0418\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0441\u043b\u043e\u0439"),
        txt("\u0413\u043b\u0435\u0434\u0430 \u0438\u0441\u0442\u043e\u0440\u0438\u044f, \u0447\u0435\u0441\u0442\u043e\u0442\u0430, \u0441\u043a\u043e\u0440\u043e\u0448\u043d\u043e \u043f\u043e\u044f\u0432\u044f\u0432\u0430\u043d\u0435 \u0438 \u0431\u0430\u0437\u043e\u0432\u0438 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u0440\u0430\u0432\u0438\u043b\u0430."),
        v41_numbers,
    )

    render_model_card(
        txt("\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u0430\u043d\u0430\u043b\u0438\u0437"),
        txt("\u0421\u044a\u0431\u0438\u0440\u0430 \u043f\u043e\u043b\u043e\u0436\u0438\u0442\u0435\u043b\u0435\u043d \u0441\u0438\u0433\u043d\u0430\u043b \u0438 \u0440\u0438\u0441\u043a \u043e\u0442 \u043e\u0442\u0441\u044a\u0441\u0442\u0432\u0438\u0435, \u0437\u0430 \u0434\u0430 \u0434\u0430\u0434\u0435 \u043f\u043e-\u0431\u0430\u043b\u0430\u043d\u0441\u0438\u0440\u0430\u043d \u0441\u0438\u0433\u043d\u0430\u043b."),
        v42_numbers,
    )

    render_model_card(
        txt("\u0420\u0438\u0442\u044a\u043c \u043d\u0430 \u043f\u043e\u044f\u0432\u044f\u0432\u0430\u043d\u0435"),
        txt("\u0413\u043b\u0435\u0434\u0430 \u043f\u0430\u0443\u0437\u0438, \u0441\u0440\u0435\u0434\u043d\u0438 \u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0438, \u0437\u0430\u043a\u044a\u0441\u043d\u0435\u043b\u0438 \u0447\u0438\u0441\u043b\u0430 \u0438 \u0441\u043b\u0435\u0434\u0432\u0430\u0449 \u043f\u0440\u043e\u0437\u043e\u0440\u0435\u0446."),
        v43_final,
    )

    rhythm_cols = st.columns(2)
    with rhythm_cols[0]:
        render_related_model_card(
            txt("\u0421\u043b\u0435\u0434\u0432\u0430\u0449 \u043f\u0440\u043e\u0437\u043e\u0440\u0435\u0446"),
            txt("\u0427\u0438\u0441\u043b\u0430, \u043a\u043e\u0438\u0442\u043e \u0440\u0438\u0442\u044a\u043c\u044a\u0442 \u043e\u0442\u0431\u0435\u043b\u044f\u0437\u0432\u0430 \u043a\u0430\u0442\u043e \u043f\u043e-\u0438\u043d\u0442\u0435\u0440\u0435\u0441\u043d\u0438 \u0437\u0430 \u0431\u043b\u0438\u0437\u043a\u0438 \u0445\u043e\u0440\u0438\u0437\u043e\u043d\u0442."),
            v43_next,
            v43_final,
        )
    with rhythm_cols[1]:
        render_related_model_card(
            txt("\u041d\u0430\u0431\u043b\u044e\u0434\u0430\u0432\u0430\u043d\u0438 \u0437\u0430\u043a\u044a\u0441\u043d\u0435\u043b\u0438 \u0447\u0438\u0441\u043b\u0430"),
            txt("\u0427\u0438\u0441\u043b\u0430 \u0441 \u043f\u043e-\u0433\u043e\u043b\u044f\u043c\u0430 \u0442\u0435\u043a\u0443\u0449\u0430 \u043f\u0430\u0443\u0437\u0430 \u0441\u043f\u0440\u044f\u043c\u043e \u0441\u043e\u0431\u0441\u0442\u0432\u0435\u043d\u0438\u044f \u0438\u043c \u0440\u0438\u0442\u044a\u043c."),
            v43_overdue,
            v43_final,
        )

    st.subheader(txt("\u0421\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u044f \u043c\u0435\u0436\u0434\u0443 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435"))
    overlap_layer_rows = [
        (txt("\u0418\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438"), v41_numbers),
        (txt("\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d"), v42_numbers),
        (txt("\u0420\u0438\u0442\u044a\u043c"), v43_final),
        (txt("\u0421\u043b\u0435\u0434\u0432\u0430\u0449 \u043f\u0440\u043e\u0437\u043e\u0440\u0435\u0446"), v43_next),
        (txt("\u0417\u0430\u043a\u044a\u0441\u043d\u0435\u043b\u0438"), v43_overdue),
    ]
    show_table(overlap_rows(overlap_layer_rows, final_ticket.get("top_ensemble_numbers", []), limit=20))

    st.subheader(txt("\u0424\u0438\u043d\u0430\u043b\u043d\u043e \u043e\u0431\u0435\u0434\u0438\u043d\u0435\u043d\u043e \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u0435"))

    if final_combos:
        for index, combo in enumerate(final_combos, start=1):
            st.markdown(
                f"""
                <div class="combo-card">
                    <div class="combo-title">{txt("\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f")} {index}</div>
                    <div class="combo-numbers">{numbers_text(combo.get("numbers", []))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info(txt("\u041d\u044f\u043c\u0430 \u0444\u0438\u043d\u0430\u043b\u043d\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438."))

    st.subheader(txt("\u0422\u043e\u043f \u0447\u0438\u0441\u043b\u0430 \u0441\u043f\u043e\u0440\u0435\u0434 \u043e\u0431\u0435\u0434\u0438\u043d\u0435\u043d\u0438\u044f \u0441\u0438\u0433\u043d\u0430\u043b"))
    show_table(number_rows(final_ticket.get("top_ensemble_numbers", []), limit=15))

    with st.expander(txt("\u041a\u0430\u043a \u0434\u0430 \u0441\u0435 \u0447\u0435\u0442\u0435")):
        st.write(
            txt("\u041f\u043e\u0432\u0442\u043e\u0440\u0435\u043d\u0438\u044f\u0442\u0430 \u043c\u0435\u0436\u0434\u0443 \u043f\u043e\u0434\u0441\u0438\u0433\u043d\u0430\u043b\u0438\u0442\u0435 \u043d\u0435 \u0441\u0430 \u0433\u0440\u0435\u0448\u043a\u0430. \u041a\u043e\u0433\u0430\u0442\u043e \u0434\u0432\u0430 \u0441\u043b\u043e\u044f \u0434\u0430\u0432\u0430\u0442 \u0435\u0434\u043d\u0438 \u0438 \u0441\u044a\u0449\u0438 \u0447\u0438\u0441\u043b\u0430, \u0442\u043e\u0432\u0430 \u043e\u0437\u043d\u0430\u0447\u0430\u0432\u0430 \u043f\u043e\u0442\u0432\u044a\u0440\u0436\u0434\u0435\u043d\u0438\u0435 \u043c\u0435\u0436\u0434\u0443 \u043c\u043e\u0434\u0435\u043b\u043d\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0438, \u0430 \u043d\u0435 \u043f\u0435\u0447\u0435\u043b\u0438\u0432\u0448\u0430 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f.")
        )

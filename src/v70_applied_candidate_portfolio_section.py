from __future__ import annotations

from pathlib import Path
import csv
import json

import streamlit as st

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

ROOT = Path(__file__).resolve().parents[1]

SUMMARY_PATH = ROOT / "reports" / "v70_applied_candidate_portfolio_summary.json"
TICKETS_PATH = ROOT / "reports" / "v70_applied_candidate_portfolio_tickets.csv"
COMPARISON_PATH = ROOT / "reports" / "v70_original_vs_candidate_portfolio.csv"
CHANGES_PATH = ROOT / "reports" / "v70_applied_candidate_portfolio_changes.csv"
MODEL_PATH = ROOT / "models" / "v70" / "v70_applied_candidate_portfolio_model.json"

TICKET_COLUMNS = [
    ("ticket_id", "Фиш"),
    ("strategy_label", "Стратегия"),
    ("numbers", "Числа"),
    ("average_step66_score", "Средна Step 66 оценка"),
    ("odd_count", "Нечетни"),
    ("even_count", "Четни"),
    ("low_count", "Ниски"),
    ("high_count", "Високи"),
    ("number_range", "Диапазон"),
    ("historical_exact_match", "Историческо повторение"),
]

CHANGE_COLUMNS = [
    ("ticket_id", "Фиш"),
    ("strategy_label", "Стратегия"),
    ("removed_numbers", "Махнати"),
    ("added_numbers", "Добавени"),
    ("original_numbers", "Оригинал"),
    ("applied_numbers", "Приложен"),
    ("average_score_delta", "Avg score delta"),
]

COMPARISON_COLUMNS = [
    ("ticket_id", "Фиш"),
    ("strategy_label", "Стратегия"),
    ("original_numbers", "Оригинален фиш"),
    ("candidate_numbers", "Приложен фиш"),
    ("removed_numbers", "Махнати"),
    ("added_numbers", "Добавени"),
    ("changed", "Променен"),
    ("average_score_delta", "Avg score delta"),
]


def _load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _as_float(value, default=0.0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return float(text.replace("%", "").replace(",", "."))
    except (TypeError, ValueError):
        return default


def _as_int(value, default=0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(float(text.replace(",", ".")))
    except (TypeError, ValueError):
        return default


def _format_numbers(value):
    return str(value).replace(",", ", ")


def _format_value(key, value):
    if key in {"average_step66_score", "average_score_delta"}:
        return f"{_as_float(value):.3f}"

    if key in {"ticket_id", "odd_count", "even_count", "low_count", "high_count", "number_range"}:
        return _as_int(value)

    if key in {
        "numbers",
        "removed_numbers",
        "added_numbers",
        "original_numbers",
        "applied_numbers",
        "candidate_numbers",
    }:
        return _format_numbers(value)

    if key in {"changed", "historical_exact_match"}:
        return "Да" if str(value).strip().lower() in {"true", "1", "yes"} else "Не"

    return value


def _localize_rows(rows, columns):
    result = []
    for row in rows:
        item = {}
        for source_key, bg_label in columns:
            item[bg_label] = _format_value(source_key, row.get(source_key, ""))
        result.append(item)
    return result


def _show_table(rows, columns):
    if not rows:
        st.info("Няма налични данни за показване.")
        return

    localized = _localize_rows(rows, columns)

    if pd is not None:
        st.dataframe(pd.DataFrame(localized), use_container_width=True, hide_index=True)
    else:
        st.table(localized)


def render_v70_applied_candidate_portfolio_section():
    st.title("Приложен подобрен портфейл")
    st.caption(
        "Превръща Step 69 candidate portfolio в отделен v70 приложен статистически портфейл. "
        "Step 67 остава запазен. Това не е гаранция за печалба."
    )

    summary = _load_json(SUMMARY_PATH)
    model = _load_json(MODEL_PATH)

    if not summary or not model:
        st.warning(
            "Липсва Step 70 report/model. "
            "Пусни: python scripts/v70_build_applied_candidate_portfolio.py"
        )
        return

    tickets = _load_csv(TICKETS_PATH)
    changes = _load_csv(CHANGES_PATH)
    comparison = _load_csv(COMPARISON_PATH)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Приложени фишове", summary.get("applied_portfolio_tickets", 0))
    col2.metric("Промени", summary.get("applied_changes_count", 0))
    col3.metric("Оригинална оценка", f"{summary.get('original_portfolio_score', 0)} / 100")
    col4.metric("Приложена оценка", f"{summary.get('applied_portfolio_score', 0)} / 100")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Top 20 оригинал", f"{summary.get('original_top20_coverage', 0)} / 20")
    col6.metric("Top 20 приложен", f"{summary.get('applied_top20_coverage', 0)} / 20")
    col7.metric("Двойки оригинал", summary.get("original_repeated_pairs", 0))
    col8.metric("Двойки приложен", summary.get("applied_repeated_pairs", 0))

    delta = _as_float(summary.get("portfolio_score_delta", 0))
    if delta >= 0:
        st.success(f"Приложеният портфейл подобрява или запазва оценката. Промяна: {delta:.3f}")
    else:
        st.warning(
            f"Приложеният портфейл има лек спад в оценката ({delta:.3f}), "
            "но може да подобрява покритието и разнообразието."
        )

    st.info(
        "Step 70 маркира кандидат портфейла като приложен статистически референтен слой. "
        "Той не презаписва Step 67 и не твърди, че предвижда бъдещ тираж."
    )

    st.markdown(f"**Решение:** {summary.get('decision', '')}")

    if int(summary.get("applied_historical_exact_matches", 0) or 0) == 0:
        st.success("Няма точни исторически повторения в приложения портфейл.")
    else:
        st.warning("Има точни исторически повторения — провери приложените фишове.")

    st.subheader("Приложени промени")
    _show_table(changes, CHANGE_COLUMNS)

    st.subheader("Приложен v70 портфейл")
    _show_table(tickets, TICKET_COLUMNS)

    st.subheader("Оригинал vs приложен кандидат")
    _show_table(comparison, COMPARISON_COLUMNS)

    with st.expander("Как работи Step 70"):
        st.markdown(
            """
1. Чете оригиналния portfolio от **Step 67**.
2. Чете кандидат portfolio от **Step 69**.
3. Сравнява оригиналните и приложените фишове.
4. Създава отделни **v70 applied portfolio** reports/models.
5. Запазва Step 67 като исторически оригинал.

Това е applied статистическа референция portfolio, не гаранция за печалба.
"""
        )

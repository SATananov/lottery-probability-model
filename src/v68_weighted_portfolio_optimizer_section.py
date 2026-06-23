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
SUMMARY_PATH = ROOT / "reports" / "v68_weighted_portfolio_summary.json"
TICKETS_PATH = ROOT / "reports" / "v68_weighted_portfolio_tickets.csv"
COVERAGE_PATH = ROOT / "reports" / "v68_weighted_portfolio_coverage.csv"
OVERLAPS_PATH = ROOT / "reports" / "v68_weighted_portfolio_overlaps.csv"
PAIRS_PATH = ROOT / "reports" / "v68_weighted_portfolio_repeated_pairs.csv"
TRIPLES_PATH = ROOT / "reports" / "v68_weighted_portfolio_repeated_triples.csv"

TICKET_COLUMNS = [
    ("ticket_id", "Комбинация"),
    ("strategy_label", "Стратегия"),
    ("numbers", "Числа"),
    ("average_step66_score", "Средна Step 66 оценка"),
    ("unique_help_count", "Уникален принос"),
    ("top20_numbers_count", "Top20 числа"),
    ("max_overlap_with_other_ticket", "Макс. припокриване"),
    ("portfolio_contribution_score", "Принос към пакета"),
    ("balance_status", "Баланс"),
]

COVERAGE_COLUMNS = [
    ("number", "Число"),
    ("step66_rank", "Step 66 ранг"),
    ("weighted_score_percent", "Step 66 оценка"),
    ("covered_count", "Покритие"),
    ("coverage_percent", "Експозиция"),
    ("number_group", "Група"),
    ("coverage_status", "Статус"),
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


def _format_value(key, value):
    if key in {
        "average_step66_score",
        "portfolio_contribution_score",
        "weighted_score_percent",
        "coverage_percent",
    }:
        return f"{_as_float(value):.2f}%"

    if key in {
        "ticket_id",
        "unique_help_count",
        "top20_numbers_count",
        "max_overlap_with_other_ticket",
        "number",
        "step66_rank",
        "covered_count",
    }:
        return _as_int(value)

    if key == "numbers":
        return str(value).replace(",", ", ")

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


def render_v68_weighted_portfolio_optimizer_section():
    st.title("Умен оптимизатор на портфейл")
    st.caption(
        "Оценява целия пакет от Step 67 комбинации: покритие, припокриване, "
        "повторени двойки/тройки и непокрити силни Step 66 сигнали. Това не е гаранция за печалба."
    )

    summary = _load_json(SUMMARY_PATH)

    if not summary:
        st.warning(
            "Липсва Step 68 report/model. "
            "Пусни: python scripts/v68_build_weighted_portfolio_optimizer.py"
        )
        return

    tickets = _load_csv(TICKETS_PATH)
    coverage = _load_csv(COVERAGE_PATH)
    overlaps = _load_csv(OVERLAPS_PATH)
    pairs = _load_csv(PAIRS_PATH)
    triples = _load_csv(TRIPLES_PATH)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Оценка на пакета", f"{summary.get('portfolio_score', 0)} / 100")
    col2.metric("Комбинации", summary.get("tickets_analyzed", 0))
    col3.metric("Покрити числа", f"{summary.get('unique_numbers_covered', 0)} / 49")
    col4.metric("Top20 покритие", f"{summary.get('covered_top20_numbers', 0)} / 20")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Средна оценка", f"{summary.get('average_ticket_step66_score', 0)}%")
    col6.metric("Средно припокриване", summary.get("average_ticket_overlap", 0))
    col7.metric("Максимално припокриване", summary.get("max_ticket_overlap", 0))
    col8.metric("Повторени двойки", summary.get("repeated_pairs_count", 0))

    status = summary.get("portfolio_status", "")
    if summary.get("portfolio_score", 0) >= 68:
        st.success(f"Статус: {status}")
    else:
        st.warning(f"Статус: {status}")

    st.info(
        "Step 68 не избира печеливши числа. Той оценява дали пакетът от комбинации е добре структуриран статистически."
    )

    recommendations = summary.get("recommendations", [])
    if recommendations:
        st.subheader("Препоръки")
        for item in recommendations:
            st.markdown(f"- {item}")

    st.subheader("Принос на комбинациите в пакета")
    _show_table(tickets, TICKET_COLUMNS)

    st.subheader("Покритие на числата")
    selected = st.radio(
        "Филтър",
        ["Top 20 Step 66", "Непокрити силни сигнали", "Всички числа"],
        horizontal=True,
    )

    if selected == "Top 20 Step 66":
        shown_coverage = [row for row in coverage if _as_int(row.get("step66_rank")) <= 20]
    elif selected == "Непокрити силни сигнали":
        shown_coverage = [
            row for row in coverage
            if _as_int(row.get("step66_rank")) <= 20 and _as_int(row.get("covered_count")) == 0
        ]
    else:
        shown_coverage = coverage

    _show_table(shown_coverage, COVERAGE_COLUMNS)

    with st.expander("Припокриване между комбинациите"):
        if overlaps:
            if pd is not None:
                st.dataframe(pd.DataFrame(overlaps), use_container_width=True, hide_index=True)
            else:
                st.table(overlaps)
        else:
            st.info("Няма данни за припокриване.")

    with st.expander("Повторени двойки и тройки"):
        st.markdown("**Повторени двойки**")
        if pairs:
            if pd is not None:
                st.dataframe(pd.DataFrame(pairs), use_container_width=True, hide_index=True)
            else:
                st.table(pairs)
        else:
            st.success("Няма повторени двойки.")

        st.markdown("**Повторени тройки**")
        if triples:
            if pd is not None:
                st.dataframe(pd.DataFrame(triples), use_container_width=True, hide_index=True)
            else:
                st.table(triples)
        else:
            st.success("Няма повторени тройки.")

    with st.expander("Как работи Step 68"):
        st.markdown(
            """
1. Чете комбинациите от **Step 67**.
2. Чете претеглените оценки от **Step 66**.
3. Изчислява:
   - колко уникални числа са покрити;
   - колко top 10 / top 20 Step 66 числа са покрити;
   - колко се припокриват комбинациите;
   - дали има повторени двойки и тройки;
   - кои силни числа остават непокрити.
4. Дава общ **обща оценка на пакета** и препоръки за следваща оптимизация.

Това е структурен статистически анализ, не предсказание на бъдещ тираж.
"""
        )

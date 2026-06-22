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
SUMMARY_PATH = ROOT / "reports" / "v67_weighted_ticket_builder_summary.json"
TICKETS_PATH = ROOT / "reports" / "v67_weighted_ticket_builder_tickets.csv"
MODEL_PATH = ROOT / "models" / "v67" / "v67_weighted_ticket_builder_model.json"

DISPLAY_COLUMNS = [
    ("ticket_id", "Фиш"),
    ("strategy_label", "Стратегия"),
    ("numbers", "Числа"),
    ("average_weighted_score", "Средна претеглена оценка"),
    ("odd_count", "Нечетни"),
    ("even_count", "Четни"),
    ("low_count", "Ниски"),
    ("high_count", "Високи"),
    ("number_range", "Диапазон"),
    ("max_overlap_with_previous", "Max overlap"),
    ("balance_status", "Баланс"),
    ("risk_note", "Бележка"),
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


def _format_value(key, value):
    if key == "average_weighted_score":
        return f"{_as_float(value):.2f}%"

    if key in {
        "ticket_id",
        "odd_count",
        "even_count",
        "low_count",
        "high_count",
        "number_range",
        "max_overlap_with_previous",
    }:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return value

    if key == "numbers":
        return str(value).replace(",", ", ")

    return value


def _localize_rows(rows):
    localized = []
    for row in rows:
        item = {}
        for source_key, bg_label in DISPLAY_COLUMNS:
            item[bg_label] = _format_value(source_key, row.get(source_key, ""))
        localized.append(item)

    return localized


def _show_table(rows):
    if not rows:
        st.info("Няма налични фишове за показване.")
        return

    localized = _localize_rows(rows)

    if pd is not None:
        st.dataframe(pd.DataFrame(localized), use_container_width=True, hide_index=True)
    else:
        st.table(localized)


def render_v67_weighted_ticket_builder_section():
    st.title("Умен генератор с тегла")
    st.caption(
        "Генерира статистически референтни фишове чрез Step 66 претеглените оценки. "
        "Това не е прогноза и не е гаранция за печалба."
    )

    summary = _load_json(SUMMARY_PATH)
    tickets = _load_csv(TICKETS_PATH)
    model = _load_json(MODEL_PATH)

    if not summary or not model:
        st.warning(
            "Липсва Step 67 report/model. "
            "Пусни: python scripts/v67_build_weighted_ticket_builder.py"
        )
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Генерирани фишове", summary.get("tickets_generated", 0))
    col2.metric("Стратегии", len(summary.get("strategies_used", [])))
    col3.metric("Top фиш", summary.get("top_average_weighted_score_ticket_id", "-"))
    col4.metric("Top средна оценка", f"{summary.get('top_average_weighted_score', 0)}%")

    if int(summary.get("historical_exact_matches", 0) or 0) == 0:
        st.success("Няма точни исторически повторения сред генерираните фишове.")
    else:
        st.warning(
            "Има фишове, които съвпадат с историческа комбинация. "
            "Провери таблицата преди използване."
        )

    st.info(
        "Генераторът използва статистически сигнали и баланс правила. "
        "Лотарийните тегления остават случайни."
    )

    st.subheader("Генерирани фишове")
    _show_table(tickets)

    st.subheader("Фишове като карти")
    for row in tickets:
        numbers = str(row.get("numbers", "")).replace(",", " · ")
        strategy = row.get("strategy_label", "")
        avg_score = _format_value("average_weighted_score", row.get("average_weighted_score", ""))
        status = row.get("balance_status", "")
        note = row.get("risk_note", "")

        st.markdown(
            f"""
**Фиш {row.get('ticket_id')} — {strategy}**  
`{numbers}`  
Средна претеглена оценка: **{avg_score}**  
Баланс: **{status}**  
{note}
"""
        )

    with st.expander("Как работи Step 67"):
        st.markdown(
            """
1. Чете **Step 66 претеглените оценки** за числа 1–49.
2. Строи няколко типа фишове чрез различни стратегии.
3. Оценява всеки фиш по:
   - средна претеглена оценка;
   - четни/нечетни;
   - ниски/високи;
   - диапазон;
   - групи по десетилетия;
   - поредни числа;
   - припокриване с други генерирани фишове.
4. Опитва да избегне точни исторически повторения, когато dataset-ът позволява това.

Това е статистически генератор, не предсказател на бъдещ тираж.
"""
        )

    source_top_numbers = model.get("source_top_numbers", [])
    if source_top_numbers:
        with st.expander("Top Step 66 числа, използвани като вход"):
            top_rows = []
            for item in source_top_numbers[:15]:
                top_rows.append({
                    "Число": item.get("number"),
                    "Step 66 оценка": f"{_as_float(item.get('weighted_score_percent')):.2f}%",
                    "Източници": item.get("source_count"),
                    "Статус": item.get("status", ""),
                })

            if pd is not None:
                st.dataframe(pd.DataFrame(top_rows), use_container_width=True, hide_index=True)
            else:
                st.table(top_rows)

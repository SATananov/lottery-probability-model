from __future__ import annotations

import csv
import io
from typing import Any

import pandas as pd
import streamlit as st

from src.v98_active_plan_result_history_engine import (
    HISTORY_CSV_PATH,
    PLAN_SUMMARY_CSV_PATH,
    SAFE_NOTE_BG,
    build_and_save,
    load_active_plan_result_history,
)

HISTORY_LABELS = {
    "evaluated_at_utc": "Оценено на",
    "plan_id": "План ID",
    "draw_date": "Дата",
    "draw_number": "Тираж",
    "draw_position": "Теглене",
    "draw_numbers": "Реални числа",
    "combination_count": "Комбинации",
    "best_hit_count": "Най-добри попадения",
    "best_combination_indexes": "Най-добри редове",
    "best_matching_numbers": "Познати числа",
    "total_hits_across_rows": "Общо попадения",
    "rows_with_hits": "Редове с попадение",
    "rows_with_3_plus": "Редове 3+",
    "rows_with_4_plus": "Редове 4+",
    "verdict_bg": "Извод",
    "status": "Статус",
    "performance_bucket_bg": "Категория",
}

PLAN_LABELS = {
    "plan_id": "План ID",
    "status": "Статус",
    "strategy_type": "Тип",
    "combination_count": "Комбинации",
    "cost_eur": "Цена EUR",
    "cost_text": "Цена",
    "saved_after_draw_date": "Заключен след дата",
    "saved_after_draw_numbers": "Заключен след числа",
    "v95_status": "Step 95",
    "real_result_rows": "Реални записи",
    "best_hit_count_max": "Макс. попадения",
    "best_hit_count_average": "Средно най-добри",
    "rows_with_3_plus_rate_percent": "3+ честота %",
    "rows_with_4_plus_rate_percent": "4+ честота %",
    "latest_result_date": "Последен резултат",
    "latest_verdict_bg": "Последен извод",
    "next_status_bg": "Следващо състояние",
}


def _read_rows(path: Any) -> list[dict[str, str]]:
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            return [dict(row) for row in csv.DictReader(f)]
    except Exception:
        return []


def _rename_rows(rows: list[dict[str, Any]], labels: dict[str, str]) -> pd.DataFrame:
    return pd.DataFrame([{labels.get(key, key): value for key, value in row.items()} for row in rows])


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    if not rows:
        return b""
    output = io.StringIO()
    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def _format_money(value: Any) -> str:
    try:
        return f"{float(value):.2f} EUR"
    except Exception:
        return "-"


def _format_float(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return "-"


def _format_percent(value: Any) -> str:
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "-"


def render_v98_active_plan_result_history_section() -> None:
    st.title("История на активния план")
    st.caption("Step 98 — проследява реалните резултати от запазения активен план след Step 95 оценки.")
    st.warning(SAFE_NOTE_BG)

    if st.button("Обнови Step 98 история", key="v98_rebuild_btn"):
        payload = build_and_save()
        st.success(f"Step 98 е обновен. Статус: {payload.get('status', 'UNKNOWN')}")
        st.rerun()

    payload = load_active_plan_result_history()
    plan = payload.get("active_plan", {}) or {}
    summary = payload.get("history_summary", {}) or {}
    history_rows = payload.get("history_rows", []) or []

    cols = st.columns(5)
    cols[0].metric("Статус", payload.get("status", "UNKNOWN"))
    cols[1].metric("План", plan.get("strategy_type", "-"))
    cols[2].metric("Комбинации", int(plan.get("combination_count", 0) or 0))
    cols[3].metric("Цена", _format_money(plan.get("cost_eur", 0.0)))
    cols[4].metric("Реални записи", int(summary.get("real_result_rows", 0) or 0))

    result_cols = st.columns(4)
    result_cols[0].metric("Макс. попадения", int(summary.get("best_hit_count_max", 0) or 0))
    result_cols[1].metric("Средно най-добри", _format_float(summary.get("best_hit_count_average", 0.0)))
    result_cols[2].metric("3+ честота", _format_percent(summary.get("rows_with_3_plus_rate_percent", 0.0)))
    result_cols[3].metric("4+ честота", _format_percent(summary.get("rows_with_4_plus_rate_percent", 0.0)))

    st.info(plan.get("next_status_bg") or payload.get("method_bg", ""))

    if not history_rows:
        st.warning("Все още няма реален резултат след заключването на активния план. Когато въведеш следващия реален тираж, Step 95 ще добави ред в историята.")
    else:
        st.success(f"Историята има {len(history_rows)} реални записа. Тренд: {summary.get('trend_bg', '-')}")

    tabs = st.tabs(["История", "Обобщение", "Активен план", "Метод"])

    with tabs[0]:
        rows = _read_rows(HISTORY_CSV_PATH)
        if rows:
            st.dataframe(_rename_rows(rows, HISTORY_LABELS), width="stretch", hide_index=True)
            st.download_button(
                "Свали история CSV",
                data=_csv_bytes(rows),
                file_name="v98_active_plan_result_history.csv",
                mime="text/csv",
            )
        else:
            st.info("Няма записани реални резултати. Това е нормално, докато Step 95 чака следващ тираж.")

    with tabs[1]:
        rows = _read_rows(PLAN_SUMMARY_CSV_PATH)
        if rows:
            st.dataframe(_rename_rows(rows, PLAN_LABELS), width="stretch", hide_index=True)
        else:
            st.info("Няма обобщение за активния план.")

    with tabs[2]:
        st.markdown("### Текущ активен план")
        st.write(f"Тип: **{plan.get('strategy_type', '-')}**")
        st.write(f"Комбинации: **{plan.get('combination_count', 0)}**")
        st.write(f"Цена: **{_format_money(plan.get('cost_eur', 0.0))}**")
        st.write(f"Заключен след: **{plan.get('saved_after_draw_date', '-')}** — `{plan.get('saved_after_draw_numbers', '-')}`")
        st.write(f"Step 95 статус: **{plan.get('v95_status', '-')}**")

    with tabs[3]:
        st.markdown(
            "Step 98 не прави нова прогноза. Той чете историята от Step 95, която се записва само при реален нов тираж след активния план. "
            "Така историята остава честна: няма backfit към стари тиражи и няма промяна на прогнозната математика."
        )
        st.warning(SAFE_NOTE_BG)

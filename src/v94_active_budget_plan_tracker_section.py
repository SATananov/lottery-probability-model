from __future__ import annotations

import csv
import io
from typing import Any

import pandas as pd
import streamlit as st

from src.v93_budget_advisor_engine import DEFAULT_PRICE_PER_COMBINATION, PREFERENCE_LABELS, build_budget_advice
from src.v94_active_budget_plan_tracker_engine import (
    SAFE_NOTE_BG,
    build_and_save,
    evaluate_plan_against_latest,
    load_active_plan,
    save_active_plan_from_advice,
)

COLUMN_LABELS = {
    "combination_index": "Комбинация",
    "numbers": "Числа",
    "hit_count": "Попадения",
    "matching_numbers": "Познати числа",
    "missing_numbers": "Различни числа",
    "is_empty": "Празна",
    "has_3_plus": "3+",
    "has_4_plus": "4+",
}


def _format_money(value: Any) -> str:
    try:
        return f"{float(value):.2f} EUR"
    except Exception:
        return "-"


def _format_percent(value: Any) -> str:
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "-"


def _combination_text(combo: list[int]) -> str:
    return ", ".join(str(number) for number in combo)


def _result_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame([{COLUMN_LABELS.get(key, key): value for key, value in row.items()} for row in rows])


def _history_dataframe() -> pd.DataFrame:
    try:
        return pd.read_csv("reports/v94_active_budget_plan_history.csv")
    except Exception:
        return pd.DataFrame()


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    fieldnames = ["combination_index", "numbers", "hit_count", "matching_numbers", "missing_numbers", "is_empty", "has_3_plus", "has_4_plus"]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in fieldnames})
    return buffer.getvalue().encode("utf-8-sig")


def _render_combinations(combinations: list[list[int]]) -> None:
    if not combinations:
        st.info("Няма комбинации за показване.")
        return
    for index, combo in enumerate(combinations, start=1):
        st.markdown(f"**Комбинация {index}:** `" + "  ".join(str(number) for number in combo) + "`")


def _render_active_plan(plan: dict[str, Any]) -> None:
    st.markdown("### Текущ активен план")
    if not plan:
        st.info("Все още няма запазен активен план.")
        return

    cols = st.columns(5)
    cols[0].metric("Тип", plan.get("strategy_type", "-"))
    cols[1].metric("Комбинации", int(plan.get("combination_count", 0)))
    cols[2].metric("Цена", _format_money(plan.get("cost_eur")))
    cols[3].metric("Уникални числа", int(plan.get("unique_covered_numbers", 0)))
    cols[4].metric("Оценка", f"{float(plan.get('advisor_score', 0.0)):.3f}")

    st.markdown(f"**Стратегия:** {plan.get('strategy_label', '-')}")
    st.caption(f"Запазен: {plan.get('created_at_utc', '-')} | След тираж: {(plan.get('saved_after_draw', {}) or {}).get('numbers_text', '-')}")


def _render_result(result: dict[str, Any], *, title: str) -> None:
    st.markdown(f"### {title}")
    status = result.get("status", "UNKNOWN")
    if status == "WAITING_NEXT_DRAW":
        st.info(result.get("message_bg", "Очаква се следващ тираж."))
        latest = result.get("latest_draw", {}) or {}
        st.caption(f"Последен наличен тираж: {latest.get('year', '')} / {latest.get('drawing_no') or latest.get('draw_number') or ''} — {latest.get('numbers_text', '')}")
        return
    if status != "EVALUATED":
        st.warning(result.get("message_bg", "Няма резултат за показване."))
        return

    latest = result.get("latest_draw", {}) or {}
    summary = result.get("summary", {}) or {}
    st.markdown(f"**Последен тираж:** {latest.get('year', '')} / {latest.get('drawing_no') or latest.get('draw_number') or ''} — `{latest.get('numbers_text', '')}`")

    cols = st.columns(5)
    cols[0].metric("Най-добър ред", int(summary.get("best_hit_count", 0)))
    cols[1].metric("Редове с попадение", int(summary.get("rows_with_hits", 0)))
    cols[2].metric("Редове 3+", int(summary.get("rows_with_3_plus", 0)))
    cols[3].metric("Редове 4+", int(summary.get("rows_with_4_plus", 0)))
    cols[4].metric("Извод", summary.get("verdict_bg", "-"))

    rows = result.get("rows", []) or []
    if rows:
        st.dataframe(_result_dataframe(rows), use_container_width=True, hide_index=True)
        st.download_button(
            "Свали резултат CSV",
            data=_csv_bytes(rows),
            file_name="active_budget_plan_latest_result.csv",
            mime="text/csv",
        )


def render_v94_active_budget_plan_tracker_section() -> None:
    st.title("План и резултат")
    st.caption("Step 94 — запази бюджетен план преди следващ тираж и после го провери срещу реалния резултат.")
    st.warning(SAFE_NOTE_BG)

    with st.expander("Създай и запази нов активен план", expanded=False):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            budget = st.number_input("Бюджет за активен план", min_value=0.90, max_value=500.00, value=10.00, step=0.90, format="%.2f")
        with col_b:
            price = st.number_input("Цена на комбинация", min_value=0.10, max_value=5.00, value=float(DEFAULT_PRICE_PER_COMBINATION), step=0.10, format="%.2f", key="v94_price")
        with col_c:
            labels = list(PREFERENCE_LABELS.values())
            selected_label = st.selectbox("Режим", labels, index=0, key="v94_preference")
            preference = next(key for key, value in PREFERENCE_LABELS.items() if value == selected_label)

        advice = build_budget_advice(float(budget), float(price), preference)
        rec = advice.get("recommendation", {}) or {}
        st.markdown(f"**Предложен план:** {rec.get('strategy_label', '-')} — {rec.get('combination_count', 0)} комбинации, {_format_money(rec.get('cost_eur'))}")
        st.caption("При запазване планът се заключва към текущия последен тираж. Реалната проверка ще е честна след добавяне на нов тираж.")
        if st.button("Запази като активен план за следващия тираж"):
            plan = save_active_plan_from_advice(advice, note_bg="Запазен от страницата План и резултат.")
            st.success(f"Активният план е запазен: {plan.get('strategy_type', '-')} / {plan.get('combination_count', 0)} комбинации.")
            st.rerun()

    with st.expander("Обнови Step 94 отчетите", expanded=False):
        if st.button("Обнови План и резултат"):
            model = build_and_save()
            st.success(f"Готово. Статус: {model.get('status', 'UNKNOWN')}")
            st.rerun()

    plan = load_active_plan()
    _render_active_plan(plan)

    tabs = st.tabs(["Активен план", "Реален резултат", "Демо проверка", "История", "Метод"])

    with tabs[0]:
        st.markdown("#### Комбинации в активния план")
        _render_combinations(plan.get("combinations", []) if plan else [])

    with tabs[1]:
        result = evaluate_plan_against_latest(plan, allow_same_draw=False)
        _render_result(result, title="Проверка след нов тираж")

    with tabs[2]:
        st.info("Демо проверката сравнява активния план с последния наличен тираж, дори ако планът е запазен след него. Използвай я само за преглед на формата.")
        demo_result = evaluate_plan_against_latest(plan, allow_same_draw=True)
        _render_result(demo_result, title="Демо срещу последния наличен тираж")

    with tabs[3]:
        history = _history_dataframe()
        if history.empty:
            st.info("Все още няма история на запазени планове.")
        else:
            st.dataframe(history, use_container_width=True, hide_index=True)

    with tabs[4]:
        st.markdown(
            "Step 94 пази активния план отделно от историческите тестове. Когато го запазиш, той помни кой е бил "
            "последният наличен тираж. След добавяне на нов тираж модулът сравнява само запазените комбинации с новите числа. "
            "Така се избягва следварително напасване."
        )
        st.warning(SAFE_NOTE_BG)

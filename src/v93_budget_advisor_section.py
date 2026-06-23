from __future__ import annotations

import csv
import io
from typing import Any

import pandas as pd
import streamlit as st

from src.v93_budget_advisor_engine import (
    DEFAULT_PRICE_PER_COMBINATION,
    PREFERENCE_LABELS,
    build_and_save,
    build_budget_advice,
)

COLUMN_LABELS = {
    "strategy_label": "Стратегия",
    "strategy_type": "Тип",
    "source_label": "Източник",
    "combination_count": "Комбинации",
    "cost_eur": "Цена EUR",
    "remaining_budget_eur": "Остатък EUR",
    "budget_utilization_percent": "Използван бюджет %",
    "unique_covered_numbers": "Уникални числа",
    "historical_average_best_hits": "Средно най-добро съвпадение",
    "historical_empty_rate_percent": "Празни тиражи %",
    "historical_at_least_2_percent": "2+ %",
    "historical_at_least_3_percent": "3+ %",
    "historical_at_least_4_percent": "4+ %",
    "budget_efficiency_score": "Бюджетна ефективност",
    "advisor_score": "Оценка на съветника",
    "core_numbers_text": "Числа в плана",
}


def _format_money(value: Any) -> str:
    try:
        return f"{float(value):.2f} EUR"
    except (TypeError, ValueError):
        return "-"


def _format_percent(value: Any) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "-"


def _combination_line(index: int, combo: list[int]) -> str:
    return f"{index}. " + ", ".join(str(number) for number in combo)


def _ticket_text(advice: dict[str, Any]) -> str:
    rec = advice.get("recommendation", {}) or {}
    lines = [
        "Бюджетен съветник — препоръчан план",
        f"Бюджет: {_format_money(advice.get('budget_eur'))}",
        f"Цена на комбинация: {_format_money(advice.get('price_per_combination_eur'))}",
        f"Максимум комбинации: {advice.get('max_budget_combinations', 0)}",
        f"Препоръка: {rec.get('strategy_label', '-')}",
        f"Тип: {rec.get('strategy_type', '-')}",
        f"Цена на плана: {_format_money(rec.get('cost_eur'))}",
        f"Остатък: {_format_money(rec.get('remaining_budget_eur'))}",
        "",
        "Комбинации:",
    ]
    for index, combo in enumerate(rec.get("combinations", []) or [], start=1):
        lines.append(_combination_line(index, combo))
    lines.extend(["", str(advice.get("safe_note_bg", ""))])
    return "\n".join(lines) + "\n"


def _csv_bytes(combinations: list[list[int]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["combination_index", "n1", "n2", "n3", "n4", "n5", "n6", "numbers"])
    for index, combo in enumerate(combinations, start=1):
        writer.writerow([index, *combo, ", ".join(str(number) for number in combo)])
    return buffer.getvalue().encode("utf-8-sig")


def _candidate_dataframe(candidates: list[dict[str, Any]]) -> pd.DataFrame:
    compact_keys = [
        "strategy_label",
        "strategy_type",
        "combination_count",
        "cost_eur",
        "remaining_budget_eur",
        "budget_utilization_percent",
        "unique_covered_numbers",
        "historical_average_best_hits",
        "historical_empty_rate_percent",
        "historical_at_least_3_percent",
        "budget_efficiency_score",
        "advisor_score",
    ]
    rows = []
    for row in candidates:
        rows.append({COLUMN_LABELS.get(key, key): row.get(key, "") for key in compact_keys})
    return pd.DataFrame(rows)


def _render_combination_cards(combinations: list[list[int]]) -> None:
    if not combinations:
        st.info("Няма комбинации за показване.")
        return
    for index, combo in enumerate(combinations, start=1):
        st.markdown(f"**Комбинация {index}:** `" + "  ".join(str(number) for number in combo) + "`")


def render_v93_budget_advisor_section() -> None:
    st.title("Бюджетен съветник")
    st.caption("Step 93 — въведи бюджет и получи адекватна структура: широк фиш, система или хибрид.")

    st.warning(
        "Този модул избира статистическа структура на фиш според бюджет. "
        "Не е прогноза, не е гаранция и не доказва бъдещ резултат."
    )

    with st.expander("Обнови базовия модел на съветника", expanded=False):
        st.write("Полезно е след Step 91, Step 92 или обновяване на тиражите.")
        if st.button("Обнови Budget Advisor"):
            with st.spinner("Обновявам бюджетните сценарии..."):
                model = build_and_save()
            st.success(f"Готово. Сценарии: {len(model.get('default_scenarios', []))}")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        budget = st.number_input("Бюджет", min_value=0.90, max_value=500.00, value=10.00, step=0.90, format="%.2f")
    with col_b:
        price = st.number_input("Цена на комбинация", min_value=0.10, max_value=5.00, value=float(DEFAULT_PRICE_PER_COMBINATION), step=0.10, format="%.2f")
    with col_c:
        labels = list(PREFERENCE_LABELS.values())
        selected_label = st.selectbox("Режим", labels, index=0)
        preference = next(key for key, value in PREFERENCE_LABELS.items() if value == selected_label)

    advice = build_budget_advice(float(budget), float(price), preference)
    rec = advice.get("recommendation", {}) or {}

    metric_cols = st.columns(5)
    metric_cols[0].metric("Бюджет", _format_money(advice.get("budget_eur")))
    metric_cols[1].metric("Максимум комбинации", int(advice.get("max_budget_combinations", 0)))
    metric_cols[2].metric("Препоръка", str(rec.get("strategy_type", "-")))
    metric_cols[3].metric("Цена на плана", _format_money(rec.get("cost_eur")))
    metric_cols[4].metric("Остатък", _format_money(rec.get("remaining_budget_eur")))

    if advice.get("warning_bg"):
        st.info(advice["warning_bg"])

    st.markdown("### Препоръка")
    st.markdown(f"**{rec.get('strategy_label', '-')}**")
    st.markdown(advice.get("reason_bg", ""))

    rec_cols = st.columns(4)
    rec_cols[0].metric("Комбинации", int(rec.get("combination_count", 0)))
    rec_cols[1].metric("Уникални числа", int(rec.get("unique_covered_numbers", 0)))
    rec_cols[2].metric("Празни тиражи исторически", _format_percent(rec.get("historical_empty_rate_percent")))
    rec_cols[3].metric("Оценка", f"{float(rec.get('advisor_score', 0.0)):.3f}")

    tabs = st.tabs(["Комбинации", "Сравнение", "Метод"])

    with tabs[0]:
        st.markdown("#### Комбинации за игра")
        _render_combination_cards(rec.get("combinations", []) or [])
        ticket_text = _ticket_text(advice)
        st.download_button(
            "Свали TXT план",
            data=ticket_text.encode("utf-8"),
            file_name="budget_advisor_ticket_plan.txt",
            mime="text/plain",
        )
        st.download_button(
            "Свали CSV комбинации",
            data=_csv_bytes(rec.get("combinations", []) or []),
            file_name="budget_advisor_combinations.csv",
            mime="text/csv",
        )
        st.divider()
        st.markdown("#### Активен план")
        st.caption("Запази този бюджетен план, за да го провериш честно след следващия реален тираж.")
        if st.button("Запази като активен план", key="v93_save_active_plan"):
            from src.v94_active_budget_plan_tracker_engine import save_active_plan_from_advice

            plan = save_active_plan_from_advice(advice, note_bg="Запазен от Бюджетен съветник.")
            st.success(f"Активният план е запазен: {plan.get('strategy_type', '-')} / {plan.get('combination_count', 0)} комбинации.")

    with tabs[1]:
        st.markdown("#### Сравнени варианти за този бюджет")
        candidates = advice.get("candidate_plans", []) or []
        if candidates:
            st.dataframe(_candidate_dataframe(candidates), use_container_width=True, hide_index=True)
        else:
            st.info("Няма достатъчен бюджет за валиден вариант.")

    with tabs[2]:
        st.markdown(advice.get("method_summary_bg", ""))
        st.markdown(
            "Съветникът започва от фиша със звездичката, защото Step 92 показа, че той е най-стабилният "
            "4-комбинационен вариант. При по-голям бюджет добавя хибридни или системни варианти и ги сравнява "
            "по историческо поведение, празен риск и бюджетна ефективност."
        )
        st.warning(advice.get("safe_note_bg", "Това е статистически съветник, не гаранция."))

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.v77_decision_recommendation_engine import (
    V77_DECISION_WARNINGS_CSV,
    V77_TICKET_RECOMMENDATIONS_CSV,
    build_decision_recommendation_center,
    load_summary,
)


COLUMN_LABELS = {
    "rank": "Ранг",
    "ticket_id": "Комбинация",
    "numbers": "Числа",
    "decision_score": "Оценка за решение",
    "recommendation_level": "Ниво на препоръка",
    "decision_action": "Действие",
    "validation_status": "Статус на валидация",
    "neural_ticket_score": "Невронна оценка",
    "explainability_score": "Обяснима оценка",
    "structure_score": "Структурна оценка",
    "odd_count": "Нечетни",
    "low_count": "Ниски числа",
    "sum": "Сума",
    "spread": "Диапазон",
    "top10_overlap": "Числа от топ 10",
    "main_reasons": "Основни причини",
    "caution_notes": "Предупреждения",
    "warning": "Предупреждение",
}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _display_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df.rename(columns={column: COLUMN_LABELS.get(column, column) for column in df.columns})


def render_v77_decision_recommendation_section() -> None:
    st.title("Решение и препоръка")
    st.caption(
        "Step 77 обединява Neural Meta Learner, обяснимостта и структурната валидация "
        "в ясен слой за решение за кандидат комбинациите."
    )

    st.warning(
        "Това е статистическа препоръка за подреждане и сравнение. "
        "Лотарията остава случайна игра и няма гаранция за печалба."
    )

    action_col, info_col = st.columns([1, 2])
    with action_col:
        if st.button("Обнови препоръките", type="primary"):
            with st.spinner("Изчислявам decision score, нива на препоръка и предупреждения..."):
                build_decision_recommendation_center()
            st.success("Step 77 е обновен успешно.")
            st.rerun()

    with info_col:
        st.info(
            "Центърът показва кои комбинации са водещи, кои са резервни и кои носят повече структурен риск."
        )

    summary = load_summary()

    metric_cols = st.columns(5)
    metric_cols[0].metric("Препоръки", summary.get("recommendations_count", 0))
    metric_cols[1].metric("Водещи", summary.get("leading_count", 0))
    metric_cols[2].metric("Силни", summary.get("strong_count", 0))
    metric_cols[3].metric("Резервни", summary.get("reserve_count", 0))
    metric_cols[4].metric("Предупреждения", summary.get("decision_warnings", 0))

    st.subheader("Най-високо класирана комбинация")
    best_numbers = summary.get("best_numbers", "")
    best_score = summary.get("best_decision_score", 0)
    best_level = summary.get("best_recommendation_level", "")

    if best_numbers:
        st.success(
            f"Комбинация {summary.get('best_ticket_id', '')}: {best_numbers} — "
            f"оценка {best_score}, ниво: {best_level}"
        )
    else:
        st.info("Още няма налична препоръка. Натисни бутона за обновяване.")

    st.subheader("Подреждане на кандидат комбинациите")
    rec_df = _read_csv(V77_TICKET_RECOMMENDATIONS_CSV)
    if rec_df.empty:
        st.info("Няма генерирани препоръки.")
    else:
        st.dataframe(_display_df(rec_df), width="stretch", hide_index=True)

    st.subheader("Предупредителни препоръки")
    warnings_df = _read_csv(V77_DECISION_WARNINGS_CSV)
    if warnings_df.empty:
        st.success("Няма комбинации с повишен риск според оценката.")
    else:
        st.dataframe(_display_df(warnings_df), width="stretch", hide_index=True)

    with st.expander("Как да се чете този раздел"):
        st.markdown(
            "- **Оценка за решение** комбинира невронна оценка, обяснима оценка и структурен баланс.\n"
            "- **Ниво на препоръка** показва дали фишът е водещ, силен, резервен или само за наблюдение.\n"
            "- **Действие** превежда анализа в практическа препоръка.\n"
            "- Този слой помага за дисциплина и сравнение, но не предсказва печеливш тираж."
        )

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.v78_final_play_plan_engine import (
    V78_PLAY_ACTIONS_CSV,
    V78_PLAY_WARNINGS_CSV,
    V78_SELECTED_TICKETS_CSV,
    build_final_play_plan_center,
    load_summary,
)


COLUMN_LABELS = {
    "plan_rank": "Ранг",
    "ticket_id": "Фиш",
    "numbers": "Числа",
    "plan_role": "Роля в плана",
    "plan_action": "Действие",
    "decision_score": "Оценка",
    "recommendation_level": "Ниво от Step 77",
    "validation_status": "Валидация",
    "risk_level": "Риск",
    "structure_score": "Структурна оценка",
    "neural_ticket_score": "Невронна оценка",
    "explainability_score": "Обяснима оценка",
    "discipline_note": "Бележка",
    "order": "Ред",
    "action": "Действие",
    "details": "Детайли",
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




def _v78_polish_df(df):
    try:
        if df is None:
            return df
        if getattr(df, "empty", False):
            return df

        polished = df.copy()

        rename_map = {
            "Бележка": "Бележка",
            "details": "Детайли",
            "action": "Действие",
            "warning": "Предупреждение",
            "risk": "Риск",
            "numbers": "Числа",
            "role_in_plan": "Роля в плана",
        }

        try:
            polished = polished.rename(columns=rename_map)
        except Exception:
            pass

        replacements = {
            "Финалният план": "Финалният план",
            "step 78": "финалният план",
            "данните": "данните",
            "данните": "данните",
            "записа на новия тираж": "записа на новия тираж",
            "Step 73.1": "предварителната проверка",
        }

        for col in list(getattr(polished, "columns", [])):
            try:
                series = polished[col].astype(str)
                for old, new in replacements.items():
                    series = series.str.replace(old, new, regex=False)
                polished[col] = series
            except Exception:
                pass

        return polished
    except Exception:
        return df

def render_v78_final_play_plan_section() -> None:

    st.title("Финален план")
    st.caption(
        "Финалният план превръща препоръките от Step 77 в дисциплиниран план: "
        "основни фишове, резерви, предупреждения и действия."
    )

    st.warning(
        "Това е статистическа организация на кандидат фишове. "
        "Лотарията остава случайна игра и няма гаранция за печалба."
    )

    action_col, info_col = st.columns([1, 2])
    with action_col:
        if st.button("Обнови финалния план", type="primary"):
            with st.spinner("Подреждам основни фишове, резерви и действия..."):
                build_final_play_plan_center()
            st.success("Финалният план е обновен успешно.")
            st.rerun()

    with info_col:
        st.info(
            "Финалният план не добавя обещание за резултат. Той помага да не се разширява пакетът хаотично."
        )

    summary = load_summary()

    metric_cols = st.columns(5)
    metric_cols[0].metric("Кандидати", summary.get("candidate_tickets", 0))
    metric_cols[1].metric("Основни", summary.get("active_tickets", 0))
    metric_cols[2].metric("Резервни", summary.get("reserve_tickets", 0))
    metric_cols[3].metric("Уникални числа", summary.get("unique_active_numbers", 0))
    metric_cols[4].metric("Средна оценка", summary.get("average_active_decision_score", 0))

    st.subheader("Най-високо класиран основен фиш")
    best_numbers = summary.get("best_numbers", "")
    if best_numbers:
        st.success(
            f"Фиш {summary.get('best_ticket_id', '')}: {best_numbers} — "
            f"средна оценка на основния пакет: {summary.get('average_active_decision_score', 0)}"
        )
    else:
        st.info("Още няма финален план. Натисни бутона за обновяване.")

    st.subheader("План по фишове")
    plan_df = _read_csv(V78_SELECTED_TICKETS_CSV)
    if plan_df.empty:
        st.info("Няма генериран финален план.")
    else:
        st.dataframe(_display_df(plan_df), use_container_width=True, hide_index=True)

    st.subheader("Действия")
    actions_df = _read_csv(V78_PLAY_ACTIONS_CSV)
    if actions_df.empty:
        st.info("Няма генерирани действия.")
    else:
        st.dataframe(_display_df(actions_df), use_container_width=True, hide_index=True)

    st.subheader("Предупреждения")
    warnings_df = _read_csv(V78_PLAY_WARNINGS_CSV)
    if warnings_df.empty:
        st.success("Няма фишове с повишен риск във финалния план.")
    else:
        st.dataframe(_display_df(warnings_df), use_container_width=True, hide_index=True)

    with st.expander("Как да се чете финалният план"):
        st.markdown(
            "- **Основен фиш** е част от финалния дисциплиниран пакет.\n"
            "- **Резервен фиш** се пази като алтернатива, без да се разширява пакетът хаотично.\n"
            "- **Само наблюдение** не влиза директно във финалния пакет.\n"
            "- След нов тираж първо провери пакета срещу реалните числа, после обнови данните."
        )


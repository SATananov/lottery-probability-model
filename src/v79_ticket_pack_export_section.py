from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.v79_ticket_pack_export_engine import (
    V79_COPY_TEXT_TXT,
    V79_EXECUTION_CHECKLIST_CSV,
    V79_EXPORT_TICKETS_CSV,
    build_ticket_pack_export_center,
    load_summary,
)


COLUMN_LABELS = {
    "export_order": "Ред",
    "ticket_id": "Фиш",
    "numbers_display": "Числа",
    "numbers_compact": "Числа за запис",
    "plan_role": "Роля от Step 78",
    "export_status": "Статус за изпълнение",
    "decision_score": "Оценка",
    "risk_level": "Риск",
    "execution_note": "Бележка",
    "order": "Ред",
    "check_item": "Проверка",
    "status": "Статус",
    "details": "Детайли",
}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _display_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df.rename(columns={column: COLUMN_LABELS.get(column, column) for column in df.columns})


def render_v79_ticket_pack_export_section() -> None:
    st.title("Експорт и изпълнение")
    st.caption(
        "Step 79 подготвя финалния пакет за копиране, печат и дисциплинирано изпълнение."
    )

    st.warning(
        "Това е организационен слой за финалния пакет. "
        "Лотарията остава случайна игра и няма гаранция за печалба."
    )

    action_col, info_col = st.columns([1, 2])
    with action_col:
        if st.button("Обнови експорт пакета", type="primary"):
            with st.spinner("Подготвям фишове за копиране, checklist и export files..."):
                build_ticket_pack_export_center()
            st.success("Step 79 е обновен успешно.")
            st.rerun()

    with info_col:
        st.info(
            "Използвай този екран за финално копиране на основните фишове и контрол преди игра."
        )

    summary = load_summary()

    metric_cols = st.columns(5)
    metric_cols[0].metric("Кандидати", summary.get("candidate_tickets", 0))
    metric_cols[1].metric("За игра", summary.get("play_tickets", 0))
    metric_cols[2].metric("Резерви", summary.get("reserve_tickets", 0))
    metric_cols[3].metric("Checklist", summary.get("checklist_items", 0))
    metric_cols[4].metric("Предупреждения", summary.get("warning_items_from_step78", 0))

    st.subheader("Готов текст за копиране")
    if V79_COPY_TEXT_TXT.exists():
        copy_text = V79_COPY_TEXT_TXT.read_text(encoding="utf-8")
        st.text_area("Копирай финалния пакет", copy_text, height=260)
    else:
        st.info("Още няма готов текст за копиране. Натисни бутона за обновяване.")

    st.subheader("Фишове за изпълнение")
    export_df = _read_csv(V79_EXPORT_TICKETS_CSV)
    if export_df.empty:
        st.info("Няма генериран export пакет.")
    else:
        st.dataframe(_display_df(export_df), use_container_width=True, hide_index=True)

    st.subheader("Checklist преди игра")
    checklist_df = _read_csv(V79_EXECUTION_CHECKLIST_CSV)
    if checklist_df.empty:
        st.info("Няма checklist.")
    else:
        st.dataframe(_display_df(checklist_df), use_container_width=True, hide_index=True)

    with st.expander("Как да се чете Step 79"):
        st.markdown(
            "- **За игра** са основните фишове от Step 78.\n"
            "- **Резерва** не се добавя автоматично — използва се само при ръчна причина.\n"
            "- **Copy text** е готов за копиране или печат.\n"
            "- След реален тираж първо сравни резултата с пакета, после обнови dataset-а."
        )

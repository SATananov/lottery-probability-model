from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.v76_explainability_validation_engine import (
    NUMBER_EXPLANATIONS_CSV,
    TICKET_VALIDATION_CSV,
    WARNINGS_CSV,
    build_explainability_validation_center,
    load_summary,
)


COLUMN_LABELS = {
    "rank": "Ранг",
    "number": "Число",
    "neural_score": "Невронна оценка",
    "percentile": "Персентил",
    "signal_level": "Ниво на сигнал",
    "score_band": "Зона",
    "historical_frequency": "Историческа честота",
    "recent_25": "Последни 25",
    "recent_50": "Последни 50",
    "recent_100": "Последни 100",
    "gap_from_last_seen": "Gap от последна поява",
    "overdue_signal": "Закъсняващ сигнал",
    "short_trend": "Кратък тренд",
    "main_reasons": "Основни причини",
    "caution_notes": "Предупреждения",
    "ticket_id": "Фиш",
    "numbers": "Числа",
    "neural_ticket_score": "Невронна оценка на фиша",
    "explainability_score": "Средна обяснима оценка",
    "odd_count": "Нечетни",
    "low_count": "Ниски числа",
    "sum": "Сума",
    "spread": "Диапазон",
    "adjacent_pairs": "Съседни двойки",
    "decade_groups": "Десетични групи",
    "top10_overlap": "Числа от топ 10",
    "validation_status": "Статус",
    "warnings": "Предупреждения",
    "type": "Тип",
    "item": "Елемент",
    "status": "Статус",
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


def render_v76_explainability_validation_section() -> None:
    st.title("Обяснимост и валидация")
    st.caption(
        "Step 76 превежда Neural Meta Learner сигналите в разбираеми причини, "
        "структурна проверка на фишовете и предупредителни бележки."
    )

    st.warning(
        "Лотарията остава случайна игра. Този център обяснява и валидира статистически сигнали, "
        "но не дава гаранция за бъдещ резултат."
    )

    col_action, col_note = st.columns([1, 2])
    with col_action:
        if st.button("Обнови обяснимостта и валидацията", type="primary"):
            with st.spinner("Изчислявам обясненията, проверките и предупредителните сигнали..."):
                build_explainability_validation_center()
            st.success("Step 76 е обновен успешно.")
            st.rerun()

    with col_note:
        st.info(
            "Тук гледаме защо едно число е получило оценка, дали фишовете са структурно балансирани "
            "и къде има риск от прекалена концентрация."
        )

    summary = load_summary()

    metric_cols = st.columns(5)
    metric_cols[0].metric("Валидни тиражи", summary.get("valid_draws", 0))
    metric_cols[1].metric("Обяснени числа", summary.get("numbers_explained", 0))
    metric_cols[2].metric("Валидирани фишове", summary.get("tickets_validated", 0))
    metric_cols[3].metric("С предупреждения", summary.get("warning_tickets", 0))
    metric_cols[4].metric("Предупредителни елементи", summary.get("warning_items", 0))

    st.subheader("Обяснения по числа")
    numbers_df = _read_csv(NUMBER_EXPLANATIONS_CSV)
    if numbers_df.empty:
        st.info("Още няма генерирани обяснения. Натисни бутона за обновяване.")
    else:
        st.dataframe(_display_df(numbers_df.head(49)), use_container_width=True, hide_index=True)

    st.subheader("Валидация на фишове")
    tickets_df = _read_csv(TICKET_VALIDATION_CSV)
    if tickets_df.empty:
        st.info("Още няма генерирана валидация на фишове.")
    else:
        st.dataframe(_display_df(tickets_df), use_container_width=True, hide_index=True)

    st.subheader("Предупредителни бележки")
    warnings_df = _read_csv(WARNINGS_CSV)
    if warnings_df.empty:
        st.success("Няма активни предупредителни бележки.")
    else:
        st.dataframe(_display_df(warnings_df), use_container_width=True, hide_index=True)

    with st.expander("Как да се чете този център"):
        st.markdown(
            "- **Основни причини** показват кои исторически сигнали подкрепят дадено число.\n"
            "- **Предупреждения** показват къде има слаб прозорец, скорошна поява или структурен риск.\n"
            "- **Валидация на фишове** проверява баланс: четни/нечетни, ниски/високи, сума, диапазон и концентрация.\n"
            "- Това е контролен слой за разбираемост, не обещание за печалба."
        )

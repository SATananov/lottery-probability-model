from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.v75_neural_meta_learner_engine import (
    CANDIDATE_TICKETS_CSV,
    NUMBER_SCORES_CSV,
    build_neural_meta_learner,
    load_summary,
)


COLUMN_LABELS = {
    "rank": "Ранг",
    "number": "Число",
    "neural_score": "Невронна оценка",
    "ticket_id": "Фиш",
    "numbers": "Числа",
    "neural_ticket_score": "Невронна оценка на фиша",
    "odd_count": "Нечетни",
    "low_count": "Ниски числа",
    "sum": "Сума",
    "историческа_честота": "Историческа честота",
    "честота_последни_25": "Честота последни 25",
    "честота_последни_50": "Честота последни 50",
    "честота_последни_100": "Честота последни 100",
    "gap_от_последна_поява": "Gap от последна поява",
    "overdue_сигнал": "Overdue сигнал",
    "кратък_тренд": "Кратък тренд",
}


def _display_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: COLUMN_LABELS.get(c, c) for c in df.columns})


def render_v75_neural_meta_learner_section() -> None:
    st.title("Невронна лаборатория")
    st.caption(
        "Лека neural meta-мрежа, която оценява числата по исторически признаци. "
        "Това е статистически експеримент, не прогноза с гаранция."
    )

    st.warning(
        "Лотарията е случайна игра. Невронната мрежа може да сравнява исторически сигнали, "
        "но не може честно да гарантира бъдещ резултат."
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Обнови невронния анализ", type="primary"):
            with st.spinner("Обучавам леката невронна мрежа и обновявам отчетите..."):
                summary = build_neural_meta_learner()
            st.success(
                "Невронният анализ е обновен. "
                f"Средно познати в top 6 при тест: {summary['metrics']['avg_hits_top6']:.3f}"
            )
            st.rerun()

    with col2:
        st.info(
            "Методът използва времево обучение: по-старите тиражи са за обучение, "
            "по-новите — за проверка. Така намаляваме риска моделът да е видял отговора."
        )

    summary = load_summary()
    if not summary:
        st.info("Няма изграден Step 75 анализ. Натисни бутона за обновяване.")
        return

    metrics = summary.get("metrics", {})
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Валидни тиражи", summary.get("valid_draws", 0))
    m2.metric("Средно top 6", f"{metrics.get('avg_hits_top6', 0):.3f}")
    m3.metric("Макс. top 6", metrics.get("max_hits_top6", 0))
    m4.metric("Скрит слой", summary.get("hidden_units", 0))

    st.subheader("Top neural числа")
    top_numbers = summary.get("top_numbers", [])
    st.markdown(" ".join([f"`{n}`" for n in top_numbers]))

    if Path(NUMBER_SCORES_CSV).exists():
        st.subheader("Оценка на числата")
        scores = pd.read_csv(NUMBER_SCORES_CSV)
        columns = [
            "rank",
            "number",
            "neural_score",
            "историческа_честота",
            "честота_последни_25",
            "честота_последни_100",
            "gap_от_последна_поява",
            "overdue_сигнал",
            "кратък_тренд",
        ]
        existing = [c for c in columns if c in scores.columns]
        st.dataframe(_display_df(scores[existing].head(20)), width="stretch", hide_index=True)

    if Path(CANDIDATE_TICKETS_CSV).exists():
        st.subheader("Кандидат комбинации от невронния слой")
        tickets = pd.read_csv(CANDIDATE_TICKETS_CSV)
        st.dataframe(_display_df(tickets), width="stretch", hide_index=True)

    with st.expander("Метод и безопасност"):
        st.markdown(
            "- Мрежата е лека MLP архитектура, реализирана с NumPy.\n"
            "- Не използва бъдещи тиражи като вход за обучение.\n"
            "- Оценява числа, а не обещава печеливша комбинация.\n"
            "- Резултатът трябва да се сравнява чрез историческа проверка/надеждност преди да се включва в основния комбиниран анализ."
        )

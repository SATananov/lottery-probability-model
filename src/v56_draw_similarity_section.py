from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v55_number_profile_engine import load_draw_events
from src.v56_draw_similarity_engine import analyze_draw_similarity, parse_combination_lines


@st.cache_data(show_spinner=False)
def _load_events() -> tuple[list[dict], int, str]:
    events = load_draw_events()
    data_path = str(events[0].get("data_path", "")) if events else ""
    return events, len(events), data_path


def _sample_text() -> str:
    return "\n".join(
        [
            "6, 13, 16, 19, 42, 44",
            "4, 12, 21, 25, 34, 48",
        ]
    )


def _distribution_table(distribution: dict[str, int]) -> pd.DataFrame:
    rows = []

    for hits in range(6, -1, -1):
        value = int(distribution.get(str(hits), 0))
        rows.append(
            {
                "Съвпадащи числа": hits,
                "Брой исторически тиражи": value,
            }
        )

    return pd.DataFrame(rows)


def _closest_draws_table(rows: list[dict]) -> pd.DataFrame:
    table_rows = []

    for row in rows:
        table_rows.append(
            {
                "Съвпадения": row["match_count"],
                "Съвпадащи числа": row["matching_numbers_text"],
                "Исторически числа": row["draw_numbers_text"],
                "Различни от въведената": row["different_query_numbers_text"],
                "Година": row["year"],
                "Тираж": row["draw_no"],
                "Дата": row["date"],
                "Индекс": row["event_index"],
            }
        )

    return pd.DataFrame(table_rows)


def render_v56_draw_similarity_section() -> None:
    st.title("Подобни исторически тиражи")

    st.markdown(
        "Този модул сравнява въведена комбинация с всички исторически тиражи "
        "и показва колко близки съвпадения са срещани в миналото."
    )

    st.warning(
        "Това е историческо сравнение, не предсказание. "
        "Сходството с минали тиражи не увеличава и не намалява математическата гаранция за печалба."
    )

    try:
        events, total_draws, data_path = _load_events()
    except Exception as exc:
        st.error(f"Не успях да заредя историческите данни: {exc}")
        return

    col_a, col_b = st.columns(2)
    col_a.metric("Исторически тиражи", total_draws)
    col_b.metric("Основни числа", "1-49")

    with st.expander("Източник на данни"):
        st.write(data_path or "Няма наличен път.")

    text = st.text_area(
        "Комбинации за сравнение",
        value=_sample_text(),
        height=120,
        help="Въведи по една комбинация на ред. Може със запетая, интервал или друг разделител.",
    )

    top_n = st.slider(
        "Брой най-близки исторически тиражи за показване",
        min_value=5,
        max_value=50,
        value=20,
        step=5,
    )

    if not st.button("Търси подобни тиражи", type="primary"):
        st.info("Въведи комбинация и натисни бутона за сравнение.")
        return

    combinations = parse_combination_lines(text)

    if not combinations:
        st.error("Не са открити комбинации. Въведи поне една линия с 6 числа.")
        return

    result = analyze_draw_similarity(
        combinations=combinations,
        draw_events=events,
        top_n=top_n,
    )

    st.subheader("Обобщение")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Валидни комбинации", result["valid_count"])
    c2.metric("Невалидни", result["invalid_count"])
    c3.metric("Най-много съвпадения", result["best_max_match_count"])
    c4.metric("Точни съвпадения", result["total_exact_matches"])

    st.caption(result["safety_note_bg"])

    for analysis in result["analyses"]:
        title = f"Комбинация {analysis['query_index']}: {analysis['query_text']}"

        with st.expander(title, expanded=True):
            if not analysis.get("is_valid"):
                st.error(analysis["status"])
                for recommendation in analysis.get("recommendations", []):
                    st.success(recommendation)
                continue

            st.markdown(f"### {analysis['band']}")

            score = float(analysis["historical_similarity_score"])
            st.progress(int(score) / 100)
            st.caption(f"Индекс на историческа близост: {score:.2f} / 100")

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Макс. съвпадения", analysis["max_match_count"])
            m2.metric("6 от 6", analysis["exact_matches_count"])
            m3.metric("5 от 6", analysis["five_matches_count"])
            m4.metric("4 от 6", analysis["four_matches_count"])
            m5.metric("3 от 6", analysis["three_matches_count"])

            st.markdown("#### Предупреждения")
            for warning in analysis["warnings"]:
                st.warning(warning)

            st.markdown("#### Препоръки")
            for recommendation in analysis["recommendations"]:
                st.success(recommendation)

            st.markdown("#### Разпределение на съвпаденията")
            st.dataframe(
                _distribution_table(analysis["match_distribution"]),
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("#### Най-близки исторически тиражи")
            st.dataframe(
                _closest_draws_table(analysis["closest_draws"]),
                use_container_width=True,
                hide_index=True,
            )

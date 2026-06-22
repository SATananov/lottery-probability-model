from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v55_number_profile_engine import build_number_profiles, load_draw_events
from src.v57_hot_cold_stable_engine import build_hot_cold_stable_center
from src.v58_smart_ensemble_score_engine import (
    analyze_smart_ensemble_scores,
    ensemble_to_dataframe,
    parse_combination_lines,
)


@st.cache_data(show_spinner=False)
def _load_context() -> tuple[list[dict], list[dict], dict, int, str]:
    events = load_draw_events()
    profiles = build_number_profiles(events)
    hot_cold_center = build_hot_cold_stable_center(events)
    data_path = str(events[0].get("data_path", "")) if events else ""
    return events, profiles, hot_cold_center, len(events), data_path


def _sample_text() -> str:
    saved_ticket = st.session_state.get("v60_last_generated_ticket_text") or st.session_state.get("v59_last_generated_ticket_text")

    if isinstance(saved_ticket, str) and saved_ticket.strip():
        return saved_ticket.strip()

    return "\n".join(
        [
            "6, 13, 16, 19, 42, 44",
            "4, 12, 21, 25, 34, 48",
            "22, 28, 37, 38, 42, 49",
        ]
    )

def _bg_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "query_index": "№",
        "combination": "Комбинация",
        "is_valid": "Валидна",
        "status": "Статус",
        "final_score": "Обща оценка",
        "band": "Ниво",
        "pattern_score": "Баланс",
        "coverage_score": "Покритие",
        "number_profile_score": "Профил числа",
        "hot_cold_balance_score": "Горещи/студени",
        "similarity_context_score": "Историческа близост",
    }

    visible = [col for col in rename_map if col in df.columns]
    return df[visible].rename(columns=rename_map)


def _component_table(components: dict) -> pd.DataFrame:
    rows = [
        {"Компонент": "Баланс на комбинацията", "Оценка": components.get("pattern_score", 0.0)},
        {"Компонент": "Покритие на фиша", "Оценка": components.get("coverage_score", 0.0)},
        {"Компонент": "Профил на числата", "Оценка": components.get("number_profile_score", 0.0)},
        {"Компонент": "Горещи / студени / стабилни", "Оценка": components.get("hot_cold_balance_score", 0.0)},
        {"Компонент": "Историческа близост", "Оценка": components.get("similarity_context_score", 0.0)},
    ]

    return pd.DataFrame(rows)


def render_v58_smart_ensemble_score_section() -> None:
    st.title("Обединена оценка")

    st.markdown(
        "Този модул обединява няколко анализа в една обща статистическа оценка: "
        "баланс, покритие, профил на числата, горещи/студени групи и историческа близост."
    )

    st.warning(
        "Това не е предсказание и не е гаранция за печалба. "
        "Обединената оценка е помощен статистически контролен слой."
    )

    try:
        events, profiles, hot_cold_center, total_draws, data_path = _load_context()
    except Exception as exc:
        st.error(f"Не успях да заредя данните за обединената оценка: {exc}")
        return

    c1, c2 = st.columns(2)
    c1.metric("Исторически тиражи", total_draws)
    c2.metric("Профилирани числа", len(profiles))

    with st.expander("Източник на данни"):
        st.write(data_path or "Няма наличен път.")

    text = st.text_area(
        "Комбинации за обединена оценка",
        value=_sample_text(),
        height=145,
        help="Въведи по една комбинация на ред. Може със запетая, интервал или друг разделител.",
    )

    if not st.button("Изчисли обединена оценка", type="primary"):
        st.info("Въведи комбинации и натисни бутона за обединена оценка.")
        return

    combinations = parse_combination_lines(text)

    if not combinations:
        st.error("Не са открити комбинации. Въведи поне една линия с 6 числа.")
        return

    result = analyze_smart_ensemble_scores(
        combinations=combinations,
        draw_events=events,
        profiles=profiles,
        hot_cold_center=hot_cold_center,
    )

    st.subheader(result["band"])

    average_score = float(result["average_final_score"])
    st.progress(max(0, min(100, int(average_score))) / 100)
    st.caption(f"Средна обединена оценка: {average_score:.2f} / 100")
    st.caption(result["safety_note_bg"])

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Валидни комбинации", result["valid_count"])
    s2.metric("Невалидни", result["invalid_count"])
    s3.metric("Най-висока оценка", result["best_score"])
    s4.metric("Най-ниска оценка", result["weakest_score"])

    coverage = result["portfolio_coverage"]

    st.markdown("### Покритие на целия фиш")

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Покритие", coverage.get("coverage_score", 0.0))
    p2.metric("Уникални числа", coverage.get("unique_numbers_count", 0))
    p3.metric("Средно припокриване", coverage.get("average_pairwise_overlap", 0.0))
    p4.metric("Повторени тройки", coverage.get("repeated_triples_count", 0))

    st.markdown("### Обобщена таблица")
    summary_df = ensemble_to_dataframe(result)
    st.dataframe(_bg_summary_table(summary_df), use_container_width=True, hide_index=True)

    st.markdown("### Детайли по комбинации")

    for item in result["analyses"]:
        title = f"Комбинация {item.get('query_index')}: {item.get('combination_text')}"

        with st.expander(title, expanded=True):
            if not item.get("is_valid"):
                st.error(item.get("status", "Невалидна комбинация"))
                for recommendation in item.get("recommendations", []):
                    st.success(recommendation)
                continue

            score = float(item["final_score"])
            st.subheader(item["band"])
            st.progress(max(0, min(100, int(score))) / 100)
            st.caption(f"Обща оценка: {score:.2f} / 100")

            st.markdown("#### Компоненти")
            st.dataframe(_component_table(item["components"]), use_container_width=True, hide_index=True)

            hot = item["hot_cold_details"]
            prof = item["number_profile_details"]
            sim = item["similarity"]

            a1, a2, a3, a4 = st.columns(4)
            a1.metric("Горещи", hot.get("hot_count", 0))
            a2.metric("Студени", hot.get("cold_count", 0))
            a3.metric("Закъснели", hot.get("overdue_count", 0))
            a4.metric("Стабилни", hot.get("stable_count", 0))

            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Среден профил", prof.get("average_profile_score", 0.0))
            b2.metric("Макс. историческо съвпадение", sim.get("max_match_count", 0))
            b3.metric("5 от 6 исторически", sim.get("five_matches_count", 0))
            b4.metric("4 от 6 исторически", sim.get("four_matches_count", 0))

            st.markdown("#### Предупреждения")
            for warning in item["warnings"]:
                st.warning(warning)

            st.markdown("#### Препоръки")
            for recommendation in item["recommendations"]:
                st.success(recommendation)

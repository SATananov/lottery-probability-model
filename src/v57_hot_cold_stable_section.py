from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v57_hot_cold_stable_engine import (
    build_hot_cold_stable_center,
    center_to_dataframe,
)


@st.cache_data(show_spinner=False)
def _load_center() -> tuple[dict, pd.DataFrame]:
    center = build_hot_cold_stable_center()
    df = center_to_dataframe(center)
    return center, df


def _bg_table(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "number": "Число",
        "main_group": "Основна група",
        "categories": "Категории",
        "combined_score": "Обща оценка",
        "historical_strength_score": "Историческа сила",
        "recent_activity_score": "Скорошна активност",
        "overdue_score": "Закъснение",
        "stability_score": "Стабилност",
        "profile_score": "Профилна оценка",
        "appearances": "Появи",
        "appearance_vs_expected_ratio": "Спрямо очакваното",
        "recent_50": "Последни 50",
        "recent_100": "Последни 100",
        "recent_250": "Последни 250",
        "recent_50_ratio": "Ритъм 50",
        "recent_100_ratio": "Ритъм 100",
        "recent_250_ratio": "Ритъм 250",
        "draws_since_last_seen": "Тиражи от последна поява",
        "average_interval": "Среден интервал",
        "current_gap_ratio": "Текуща пауза / среден интервал",
        "interval_stability_score": "Стабилност на интервала",
    }

    visible_cols = [col for col in rename_map if col in df.columns]
    return df[visible_cols].rename(columns=rename_map)


def _items_to_df(items: list[dict]) -> pd.DataFrame:
    rows = []

    for item in items:
        rows.append(
            {
                "Число": item["number"],
                "Основна група": item["main_group"],
                "Категории": item["categories_text"],
                "Обща оценка": item["combined_score"],
                "Скорошна активност": item["recent_activity_score"],
                "Закъснение": item["overdue_score"],
                "Историческа сила": item["historical_strength_score"],
                "Стабилност": item["stability_score"],
                "Появи": item["appearances"],
                "Последни 50": item["recent_50"],
                "Последни 100": item["recent_100"],
                "От последна поява": item["draws_since_last_seen"],
            }
        )

    return pd.DataFrame(rows)


def _show_group(title: str, items: list[dict]) -> None:
    st.markdown(f"#### {title}")

    if not items:
        st.info("Няма числа в тази група по текущите критерии.")
        return

    st.dataframe(_items_to_df(items), width="stretch", hide_index=True)


def render_v57_hot_cold_stable_section() -> None:
    st.title("Горещи, студени и стабилни числа")

    st.markdown(
        "Този модул групира числата според историческото им поведение, скорошната активност, "
        "закъснението и стабилността на интервалите."
    )

    st.warning(
        "Това не е предсказание и не е гаранция за печалба. "
        "Групите показват минало поведение и текущ статистически ритъм."
    )

    try:
        center, df = _load_center()
    except Exception as exc:
        st.error(f"Не успях да заредя анализа: {exc}")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Анализирани тиражи", center["total_draws"])
    c2.metric("Профилирани числа", center["numbers_profiled"])
    c3.metric("Източник", "historical_draws")

    with st.expander("Източник на данни"):
        st.write(center.get("data_path", ""))

    st.caption(center["safety_note_bg"])

    st.markdown("### Обобщение по групи")

    summary_rows = []
    for row in center["summary_rows"]:
        summary_rows.append(
            {
                "Група": row["group"],
                "Брой числа": row["count"],
                "Числа": ", ".join(str(number) for number in row["numbers"]),
            }
        )

    st.dataframe(summary_rows, width="stretch", hide_index=True)

    tab_hot, tab_cold, tab_overdue, tab_stable, tab_historical, tab_all = st.tabs(
        [
            "Горещи",
            "Студени",
            "Закъснели",
            "Стабилни",
            "Исторически силни",
            "Всички числа",
        ]
    )

    with tab_hot:
        _show_group("Горещи напоследък", center["top_hot"])

    with tab_cold:
        _show_group("Студени напоследък", center["top_cold"])

    with tab_overdue:
        _show_group("Най-дълго непоявявали се", center["top_overdue"])

    with tab_stable:
        _show_group("Най-стабилни по интервал", center["top_stable"])

    with tab_historical:
        _show_group("Исторически най-силни", center["top_historical"])

    with tab_all:
        st.markdown("#### Пълна таблица")

        sort_option = st.selectbox(
            "Подреди по",
            [
                "Обща оценка",
                "Скорошна активност",
                "Закъснение",
                "Историческа сила",
                "Стабилност",
                "Число",
            ],
        )

        sort_map = {
            "Обща оценка": "combined_score",
            "Скорошна активност": "recent_activity_score",
            "Закъснение": "overdue_score",
            "Историческа сила": "historical_strength_score",
            "Стабилност": "stability_score",
            "Число": "number",
        }

        sort_col = sort_map[sort_option]
        ascending = sort_option == "Число"
        sorted_df = df.sort_values(sort_col, ascending=ascending)

        st.dataframe(_bg_table(sorted_df), width="stretch", hide_index=True)

    st.markdown("### Детайли за избрано число")

    selected_number = st.selectbox("Избери число за обяснение", list(range(1, 50)))
    item = next((row for row in center["classified_numbers"] if int(row["number"]) == int(selected_number)), None)

    if item:
        st.subheader(f"Число {selected_number} — {item['main_group']}")

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Обща оценка", item["combined_score"])
        d2.metric("Скорошна активност", item["recent_activity_score"])
        d3.metric("Закъснение", item["overdue_score"])
        d4.metric("Стабилност", item["stability_score"])

        st.markdown("#### Категории")
        st.write(item["categories_text"])

        st.markdown("#### Обяснение")
        for line in item["explanation"]:
            st.info(line)

        st.markdown("#### Препоръки")
        for line in item["recommendations"]:
            st.success(line)

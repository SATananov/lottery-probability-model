from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v55_number_profile_engine import (
    build_number_profiles,
    load_draw_events,
    profiles_to_dataframe,
)


@st.cache_data(show_spinner=False)
def _load_profiles() -> tuple[list[dict], pd.DataFrame, int, str]:
    events = load_draw_events()
    profiles = build_number_profiles(events)
    df = profiles_to_dataframe(profiles)
    data_path = str(events[0].get("data_path", "")) if events else ""
    return profiles, df, len(events), data_path


def _profile_by_number(profiles: list[dict], number: int) -> dict:
    for profile in profiles:
        if int(profile["number"]) == int(number):
            return profile
    raise ValueError("Не е намерен профил за избраното число.")


def _bg_table(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "number": "Число",
        "profile_score": "Оценка",
        "band": "Профил",
        "status": "Статус",
        "appearances": "Появи",
        "expected_appearances": "Очаквани появи",
        "appearance_vs_expected_ratio": "Спрямо очакваното",
        "draw_frequency_pct": "Дял от тиражите %",
        "last_seen_index": "Последна поява",
        "draws_since_last_seen": "Тиражи от последна поява",
        "average_interval": "Среден интервал",
        "median_interval": "Медианен интервал",
        "max_interval": "Макс. интервал",
        "recent_50": "Последни 50",
        "recent_100": "Последни 100",
        "recent_250": "Последни 250",
        "recent_500": "Последни 500",
        "interval_stability_score": "Стабилност",
        "top_pairs": "Топ двойки",
        "top_triples": "Топ тройки",
    }

    visible_cols = [col for col in rename_map if col in df.columns]
    return df[visible_cols].rename(columns=rename_map)


def _show_pairs(profile: dict) -> None:
    pairs = profile.get("top_pairs", [])
    if not pairs:
        st.info("Няма достатъчно данни за двойки.")
        return

    rows = [
        {
            "Партньор число": item["partner"],
            "Съвместни появи": item["count"],
        }
        for item in pairs
    ]

    st.dataframe(rows, width="stretch", hide_index=True)


def _show_triples(profile: dict) -> None:
    triples = profile.get("top_triples", [])
    if not triples:
        st.info("Няма достатъчно данни за тройки.")
        return

    rows = [
        {
            "Други две числа": f"{item['partners'][0]}, {item['partners'][1]}",
            "Съвместни появи": item["count"],
        }
        for item in triples
    ]

    st.dataframe(rows, width="stretch", hide_index=True)


def render_v55_number_profile_section() -> None:
    st.title("Профил на число")

    st.markdown(
        "Този център показва статистически профил за всяко число от 1 до 49: "
        "честота, последна поява, интервали, скорошна активност и участие в двойки/тройки."
    )

    st.warning(
        "Това не е предсказание и не е гаранция за печалба. "
        "Профилът показва историческо поведение на числото, а не бъдещ резултат."
    )

    try:
        profiles, df, total_draws, data_path = _load_profiles()
    except Exception as exc:
        st.error(f"Не успях да заредя историческите данни: {exc}")
        return

    col_a, col_b = st.columns(2)
    col_a.metric("Анализирани тиражи", total_draws)
    col_b.metric("Профилирани числа", len(profiles))

    with st.expander("Източник на данни"):
        st.write(data_path or "Няма наличен път.")

    selected_number = st.selectbox(
        "Избери число",
        list(range(1, 50)),
        index=0,
    )

    profile = _profile_by_number(profiles, selected_number)

    st.subheader(f"Число {selected_number} — {profile['band']}")

    score = float(profile["profile_score"])
    st.progress(int(score) / 100)
    st.caption(f"Обща профилна оценка: {score:.2f} / 100")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Появи", profile["appearances"])
    c2.metric("Дял от тиражите", f"{profile['draw_frequency_pct']:.2f}%")
    c3.metric("От последна поява", profile["draws_since_last_seen"])
    c4.metric("Среден интервал", profile["average_interval"])
    c5.metric("Статус", profile["status"])

    c6, c7, c8, c9 = st.columns(4)
    c6.metric("Последни 50", profile["recent_50"])
    c7.metric("Последни 100", profile["recent_100"])
    c8.metric("Последни 250", profile["recent_250"])
    c9.metric("Стабилност", profile["interval_stability_score"])

    st.markdown("#### Обяснение")
    for note in profile.get("notes", []):
        st.info(note)

    st.markdown("#### Препоръки")
    for recommendation in profile.get("recommendations", []):
        st.success(recommendation)

    left, right = st.columns(2)

    with left:
        st.markdown("#### Най-чести двойки с това число")
        _show_pairs(profile)

    with right:
        st.markdown("#### Най-чести тройки с това число")
        _show_triples(profile)

    st.markdown("#### Всички числа — обща таблица")

    sort_option = st.selectbox(
        "Подреди таблицата по",
        [
            "Оценка",
            "Появи",
            "Тиражи от последна поява",
            "Последни 250",
            "Среден интервал",
            "Число",
        ],
    )

    sort_map = {
        "Оценка": "profile_score",
        "Появи": "appearances",
        "Тиражи от последна поява": "draws_since_last_seen",
        "Последни 250": "recent_250",
        "Среден интервал": "average_interval",
        "Число": "number",
    }

    sort_col = sort_map[sort_option]
    ascending = sort_option in {"Число", "Среден интервал"}
    sorted_df = df.sort_values(sort_col, ascending=ascending)

    st.dataframe(_bg_table(sorted_df), width="stretch", hide_index=True)

    st.markdown("#### Топ 10 по профилна оценка")
    top_10 = df.sort_values("profile_score", ascending=False).head(10)
    st.dataframe(_bg_table(top_10), width="stretch", hide_index=True)

    st.markdown("#### Топ 10 най-дълго непоявявали се")
    overdue_10 = df.sort_values("draws_since_last_seen", ascending=False).head(10)
    st.dataframe(_bg_table(overdue_10), width="stretch", hide_index=True)

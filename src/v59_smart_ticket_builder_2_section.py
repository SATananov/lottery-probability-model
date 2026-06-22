from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v55_number_profile_engine import build_number_profiles, load_draw_events
from src.v57_hot_cold_stable_engine import build_hot_cold_stable_center
from src.v59_smart_ticket_builder_2_engine import build_smart_ticket_builder_2
from src.v60_ticket_builder_export_utils import (
    result_to_copy_text,
    result_to_csv_bytes,
    result_to_dataframe,
    result_to_json_bytes,
    result_to_txt_bytes,
)


@st.cache_data(show_spinner=False)
def _load_context() -> tuple[list[dict], list[dict], dict, int, str]:
    events = load_draw_events()
    profiles = build_number_profiles(events)
    hot_cold_center = build_hot_cold_stable_center(events)
    data_path = str(events[0].get("data_path", "")) if events else ""
    return events, profiles, hot_cold_center, len(events), data_path


def _bg_table(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "ticket_index": "№",
        "combination": "Комбинация",
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


def _save_for_ensemble(result: dict) -> None:
    ticket_text = result_to_copy_text(result)
    st.session_state["v60_last_generated_ticket_text"] = ticket_text
    st.session_state["v59_last_generated_ticket_text"] = ticket_text
    st.session_state["generated_tickets"] = result.get("selected_tickets", [])
    st.session_state["current_ticket_combinations"] = result.get("selected_tickets", [])


def _render_ticket_card(index: int, row: dict) -> None:
    st.markdown(f"### Комбинация {index}")
    st.code(row["combination_text"], language="text")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Обща", row["final_score"])
    c2.metric("Баланс", row["pattern_score"])
    c3.metric("Покритие", row["coverage_score"])
    c4.metric("Профил", row["number_profile_score"])
    c5.metric("Историчност", row["similarity_context_score"])

    st.caption(row["band"])

    with st.expander("Защо е избрана тази комбинация"):
        st.markdown("**Предупреждения:**")
        for warning in row.get("warnings", []):
            st.warning(warning)

        st.markdown("**Препоръки:**")
        for recommendation in row.get("recommendations", []):
            st.success(recommendation)


def render_v59_smart_ticket_builder_2_section() -> None:
    st.title("Интелигентен генератор 2")

    st.markdown(
        "Този модул генерира кандидат-комбинации, оценява ги чрез обединената оценка "
        "и избира по-балансиран фиш с контрол на повторенията."
    )

    st.warning(
        "Това не е предсказание и не е гаранция за печалба. "
        "Генераторът е статистически помощник за изграждане на по-контролиран фиш."
    )

    try:
        events, profiles, hot_cold_center, total_draws, data_path = _load_context()
    except Exception as exc:
        st.error(f"Не успях да заредя данните за генератора: {exc}")
        return

    c1, c2 = st.columns(2)
    c1.metric("Исторически тиражи", total_draws)
    c2.metric("Профилирани числа", len(profiles))

    with st.expander("Източник на данни"):
        st.write(data_path or "Няма наличен път.")

    st.markdown("### Настройки")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        ticket_count = st.slider(
            "Брой комбинации за фиш",
            min_value=3,
            max_value=10,
            value=5,
            step=1,
        )

    with col_b:
        candidate_count = st.slider(
            "Брой кандидати за оценяване",
            min_value=50,
            max_value=400,
            value=120,
            step=10,
        )

    with col_c:
        seed = st.number_input(
            "Seed",
            min_value=1,
            max_value=999999,
            value=59,
            step=1,
        )

    col_d, col_e, col_f = st.columns(3)

    with col_d:
        strategy = st.selectbox(
            "Стратегия",
            [
                "Балансиран",
                "Скорошна активност",
                "Закъснели числа",
                "Стабилност",
                "Експериментален",
            ],
        )

    with col_e:
        max_number_reuse = st.slider(
            "Макс. повторение на число",
            min_value=1,
            max_value=4,
            value=2,
            step=1,
        )

    with col_f:
        max_shared_numbers = st.slider(
            "Макс. общи числа между комбинации",
            min_value=1,
            max_value=4,
            value=2,
            step=1,
        )

    generate_clicked = st.button("Генерирай интелигентен фиш", type="primary")

    if generate_clicked:
        with st.spinner("Генерирам и оценявам кандидат-комбинации..."):
            result = build_smart_ticket_builder_2(
                ticket_count=ticket_count,
                candidate_count=candidate_count,
                seed=int(seed),
                strategy=strategy,
                max_number_reuse=max_number_reuse,
                max_shared_numbers=max_shared_numbers,
                draw_events=events,
                profiles=profiles,
                hot_cold_center=hot_cold_center,
            )

        st.session_state["v60_last_builder_result"] = result
        _save_for_ensemble(result)

    result = st.session_state.get("v60_last_builder_result")

    if not result:
        st.info("Избери настройки и натисни бутона за генериране.")
        return

    st.subheader("Предложен фиш")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Избрани комбинации", result["selected_count"])
    s2.metric("Средна оценка", result["average_final_score"])
    s3.metric("Покритие", result["coverage_score"])
    s4.metric("Оценени кандидати", result["candidate_count_scored"])

    st.caption(result["safety_note_bg"])

    df = result_to_dataframe(result)

    if df.empty:
        st.error("Не са генерирани валидни предложения. Пробвай по-голям кандидатски пул или друг seed.")
        return

    st.markdown("### Готов фиш за копиране")
    st.code(result_to_copy_text(result), language="text")

    dl1, dl2, dl3 = st.columns(3)

    with dl1:
        st.download_button(
            "Изтегли TXT",
            data=result_to_txt_bytes(result),
            file_name="smart_ticket_builder_2_ticket.txt",
            mime="text/plain",
        )

    with dl2:
        st.download_button(
            "Изтегли CSV",
            data=result_to_csv_bytes(result),
            file_name="smart_ticket_builder_2_ticket.csv",
            mime="text/csv",
        )

    with dl3:
        st.download_button(
            "Изтегли JSON",
            data=result_to_json_bytes(result),
            file_name="smart_ticket_builder_2_ticket.json",
            mime="application/json",
        )

    if st.button("Запази този фиш за Обединена оценка"):
        _save_for_ensemble(result)
        st.success("Фишът е запазен. Отвори страницата „Обединена оценка“, за да го провериш там.")

    st.markdown("### Таблица на предложенията")
    st.dataframe(_bg_table(df), use_container_width=True, hide_index=True)

    st.markdown("### Карти на комбинациите")

    for index, row in enumerate(result["selected_rows"], start=1):
        with st.container(border=True):
            _render_ticket_card(index, row)

    st.markdown("### Предупреждения")
    for warning in result["warnings"]:
        st.warning(warning)

    st.markdown("### Препоръки")
    for recommendation in result["recommendations"]:
        st.success(recommendation)

    with st.expander("Топ кандидати преди финалния избор"):
        preview_rows = []

        for index, row in enumerate(result["top_candidates_preview"], start=1):
            preview_rows.append(
                {
                    "№": index,
                    "Комбинация": row["combination_text"],
                    "Оценка": row["final_score"],
                    "Баланс": row["pattern_score"],
                    "Профил": row["number_profile_score"],
                    "Горещи/студени": row["hot_cold_balance_score"],
                    "Историческа близост": row["similarity_context_score"],
                }
            )

        st.dataframe(preview_rows, use_container_width=True, hide_index=True)

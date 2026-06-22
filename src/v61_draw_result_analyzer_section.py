from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from src.v61_draw_result_analyzer_engine import (
    analyze_latest_draw_result,
    closest_draws_to_dataframe,
    export_latest_draw_result_analysis,
    model_signals_to_dataframe,
    number_rows_to_dataframe,
)


ROOT = Path(__file__).resolve().parents[1]


@st.cache_data(show_spinner=False)
def _load_analysis() -> dict:
    return analyze_latest_draw_result(top_n=12)


def _run_build_script() -> tuple[bool, str]:
    script = ROOT / "scripts" / "v61_build_draw_result_analyzer.py"
    if not script.exists():
        return False, "Липсва build script за v61."

    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    return completed.returncode == 0, output.strip()


def _bg_model_table(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "source_bg": "Модул / артефакт",
        "candidate_label": "Сигнал",
        "candidate_text": "Числа",
        "hit_count": "Съвпадения",
        "matching_numbers_text": "Съвпаднали числа",
        "missing_numbers_text": "Липсващи числа",
        "note_bg": "Бележка",
    }
    visible = [col for col in rename if col in df.columns]
    return df[visible].rename(columns=rename)


def _bg_number_table(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "number": "Число",
        "main_group": "Група",
        "categories": "Категории",
        "combined_score": "Обща оценка",
        "profile_score": "Профил",
        "appearances": "Появи",
        "recent_50": "Последни 50",
        "recent_100": "Последни 100",
        "recent_250": "Последни 250",
        "draws_since_last_seen": "Тиражи от последна поява",
        "average_interval": "Среден интервал",
        "current_gap_ratio": "Текущ gap ratio",
        "interval_stability_score": "Стабилност",
    }
    visible = [col for col in rename if col in df.columns]
    return df[visible].rename(columns=rename)


def _bg_closest_table(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "year": "Година",
        "draw_no": "Тираж",
        "date": "Дата",
        "draw_numbers_text": "Исторически числа",
        "match_count": "Съвпадения",
        "matching_numbers_text": "Съвпаднали",
        "different_query_numbers_text": "Различни от новия тираж",
    }
    visible = [col for col in rename if col in df.columns]
    return df[visible].rename(columns=rename)


def _render_number_badges(numbers: list[int]) -> None:
    badges = "".join(
        f"<span style='display:inline-flex;align-items:center;justify-content:center;"
        f"width:42px;height:42px;margin:4px;border-radius:12px;"
        f"border:1px solid rgba(212,175,55,.75);font-weight:700;'>{number}</span>"
        for number in numbers
    )
    st.markdown(badges, unsafe_allow_html=True)


def render_v61_draw_result_analyzer_section() -> None:
    st.title("Анализ на нов тираж")

    st.markdown(
        "Този модул анализира последния реален тираж след като вече е добавен в dataset-а. "
        "Целта е да се види как тиражът се държи спрямо историческите профили, баланса, "
        "подобните минали тиражи и текущите статистически артефакти."
    )

    st.warning(
        "Това е post-draw диагностичен анализ, не предсказание и не гаранция за печалба. "
        "Съвпаденията с модели показват статистически overlap, а не доказана предсказателна сила."
    )

    col_a, col_b = st.columns([1, 2])
    with col_a:
        if st.button("Обнови v61 анализа", type="primary"):
            ok, output = _run_build_script()
            st.cache_data.clear()
            if ok:
                st.success("v61 анализът е обновен успешно.")
            else:
                st.error("Грешка при обновяване на v61 анализа.")
            st.code(output or "-", language="text")

    with col_b:
        st.caption("При добавяне на нов тираж този модул може да се refresh-ва автоматично от Add Draw workflow.")

    try:
        result = _load_analysis()
    except Exception as exc:
        st.error(f"Не успях да заредя анализа на последния тираж: {exc}")
        return

    latest = result["latest_draw"]
    pattern = result.get("pattern_analysis", {})
    group_counts = result.get("group_counts", {})
    signal_summary = result.get("model_signal_summary", {})
    similarity = result.get("historical_similarity_previous_draws", {})

    st.markdown("### Последен тираж")
    _render_number_badges(latest.get("numbers", []))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Дата", latest.get("date", "-"))
    m2.metric("Тираж", latest.get("draw_no", "-"))
    m3.metric("Общо тиражи", result.get("total_draws", 0))
    m4.metric("Сравнени предишни", result.get("previous_draws_compared", 0))

    st.markdown("### Кратък извод")
    for line in result.get("diagnostic_summary_bg", []):
        st.info(line)

    st.markdown("### Структура на тиража")
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Баланс", pattern.get("band", "-"))
    p2.metric("Оценка", pattern.get("pattern_score", 0.0))
    p3.metric("Сума", pattern.get("sum", 0))
    p4.metric("Четни / нечетни", f"{pattern.get('even_count', 0)} / {pattern.get('odd_count', 0)}")
    p5.metric("Ниски / високи", f"{pattern.get('low_count', 0)} / {pattern.get('high_count', 0)}")

    with st.expander("Детайли за структурата", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Най-дълга поредица", pattern.get("longest_consecutive_run", 0))
        c2.metric("Последователни двойки", pattern.get("consecutive_pairs", 0))
        c3.metric("Мин. gap", pattern.get("min_gap", 0))
        c4.metric("Макс. gap", pattern.get("max_gap", 0))

        for warning in pattern.get("warnings", []):
            st.warning(warning)
        for recommendation in pattern.get("recommendations", []):
            st.success(recommendation)

    st.markdown("### Профил на числата")
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Горещи", group_counts.get("hot_count", 0))
    g2.metric("Студени", group_counts.get("cold_count", 0))
    g3.metric("Стабилни", group_counts.get("stable_count", 0))
    g4.metric("Закъснели", group_counts.get("overdue_count", 0))

    number_df = number_rows_to_dataframe(result)
    if not number_df.empty:
        st.dataframe(_bg_number_table(number_df), use_container_width=True, hide_index=True)

    st.markdown("### Сравнение с текущите статистически артефакти")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Проверени сигнали", signal_summary.get("signal_count", 0))
    s2.metric("Най-добро съвпадение", signal_summary.get("best_hit_count", 0))
    s3.metric("Средно съвпадение", signal_summary.get("average_hit_count", 0.0))
    s4.metric("Сигнали с 3+", signal_summary.get("signals_with_3_or_more", 0))

    signal_df = model_signals_to_dataframe(result)
    if not signal_df.empty:
        st.dataframe(_bg_model_table(signal_df), use_container_width=True, hide_index=True)

    st.markdown("### Историческа близост без самия последен тираж")
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Макс. съвпадение", similarity.get("max_match_count", 0))
    h2.metric("5 от 6", similarity.get("five_matches_count", 0))
    h3.metric("4 от 6", similarity.get("four_matches_count", 0))
    h4.metric("3 от 6", similarity.get("three_matches_count", 0))

    closest_df = closest_draws_to_dataframe(result)
    if not closest_df.empty:
        st.dataframe(_bg_closest_table(closest_df), use_container_width=True, hide_index=True)

    st.markdown("### Двойки от v50 контекст")
    pair_context = result.get("pair_group_context", {})
    q1, q2, q3 = st.columns(3)
    q1.metric("Двойки в тиража", pair_context.get("actual_pair_count", 0))
    q2.metric("Попадения в top двойки", pair_context.get("top_pair_hits_count", 0))
    q3.metric("Попадения в наблюдавани двойки", pair_context.get("watch_pair_hits_count", 0))

    pair_rows = pair_context.get("top_pair_hits", []) + pair_context.get("watch_pair_hits", [])
    if pair_rows:
        st.dataframe(pd.DataFrame(pair_rows), use_container_width=True, hide_index=True)
    else:
        st.caption("Няма двойки от последния тираж, които да попадат в текущите top/watch v50 списъци.")

    st.caption(result.get("safety_note_bg", ""))

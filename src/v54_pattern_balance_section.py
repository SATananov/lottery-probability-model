from __future__ import annotations

import streamlit as st

from src.v54_pattern_balance_engine import analyze_pattern_balance, parse_combination_lines


def _sample_text() -> str:
    return "\n".join(
        [
            "4, 12, 21, 25, 34, 48",
            "6, 13, 16, 19, 42, 44",
            "1, 2, 3, 4, 5, 6",
            "7, 17, 27, 37, 47, 49",
        ]
    )


def _percent_like_score(score: float) -> str:
    return f"{score:.2f} / 100"


def _show_rows_table(rows: list[dict]) -> None:
    table_rows = []

    for row in rows:
        table_rows.append(
            {
                "№": row["ticket_index"],
                "Комбинация": row["combination_text"],
                "Статус": row["status"],
                "Оценка": row["pattern_score"],
                "Баланс": row["band"],
                "Сума": row.get("sum", ""),
                "Четни": row.get("even_count", ""),
                "Нечетни": row.get("odd_count", ""),
                "Ниски 1-24": row.get("low_count", ""),
                "Високи 25-49": row.get("high_count", ""),
                "Най-дълга поредица": row.get("longest_consecutive_run", ""),
                "Макс. разстояние": row.get("max_gap", ""),
            }
        )

    st.dataframe(table_rows, use_container_width=True, hide_index=True)


def _show_distribution(title: str, data: dict[str, int]) -> None:
    st.markdown(f"#### {title}")
    rows = [{"Показател": key, "Брой": value} for key, value in data.items()]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_v54_pattern_balance_section() -> None:
    st.title("Баланс на комбинациите")

    st.markdown(
        "Този модул анализира структурата на комбинациите: четни и нечетни, ниски и високи числа, "
        "сума, диапазони, последователни числа, разстояния между числата и крайни цифри."
    )

    st.warning(
        "Този анализ не предсказва печеливши числа. Той оценява само дали комбинацията изглежда "
        "структурно балансирана или прекалено крайна."
    )

    text = st.text_area(
        "Комбинации за анализ",
        value=_sample_text(),
        height=180,
        help="Въведи по една комбинация на ред. Може със запетая, интервал или друг разделител.",
    )

    if not st.button("Анализирай баланса", type="primary"):
        st.info("Въведи комбинации и натисни бутона за анализ.")
        return

    combinations = parse_combination_lines(text)

    if not combinations:
        st.error("Не са открити комбинации. Въведи поне една линия с числа.")
        return

    result = analyze_pattern_balance(combinations)

    st.subheader(result["band"])

    average_score = float(result["average_pattern_score"])
    st.progress(int(average_score) / 100)
    st.caption(f"Средна оценка на структурния баланс: {_percent_like_score(average_score)}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Валидни комбинации", result["valid_count"])
    col2.metric("Невалидни", result["invalid_count"])
    col3.metric("Средна оценка", f"{average_score:.2f}")
    col4.metric("Средна сума", result["aggregate"]["average_sum"])

    st.markdown("#### Общи предупреждения")
    for warning in result["portfolio_warnings"]:
        st.warning(warning)

    st.markdown("#### Общи препоръки")
    for recommendation in result["portfolio_recommendations"]:
        st.success(recommendation)

    st.markdown("#### Комбинации")
    _show_rows_table(result["rows"])

    left, right = st.columns(2)

    with left:
        _show_distribution(
            "Четни / нечетни",
            {
                "Нечетни": result["aggregate"]["odd_even_distribution"]["odd"],
                "Четни": result["aggregate"]["odd_even_distribution"]["even"],
            },
        )

    with right:
        _show_distribution(
            "Ниски / високи",
            {
                "1-24": result["aggregate"]["low_high_distribution"]["low_1_24"],
                "25-49": result["aggregate"]["low_high_distribution"]["high_25_49"],
            },
        )

    _show_distribution("Разпределение по диапазони", result["aggregate"]["range_distribution"])
    _show_distribution("Крайни цифри", result["aggregate"]["final_digit_distribution"])

    st.markdown("#### Детайли по комбинации")

    for row in result["rows"]:
        with st.expander(f"Комбинация {row['ticket_index']}: {row['combination_text']}"):
            st.write(f"**Статус:** {row['status']}")
            st.write(f"**Оценка:** {row['pattern_score']} / 100")
            st.write(f"**Баланс:** {row['band']}")

            if row.get("is_valid"):
                st.write(f"**Сума:** {row['sum']} — {row['sum_band']}")
                st.write(f"**Разстояния:** {row['gaps']}")
                st.write(f"**Най-дълга поредица:** {row['longest_consecutive_run']}")
                st.write(f"**Последователни двойки:** {row['consecutive_pairs']}")

            st.markdown("**Предупреждения:**")
            for warning in row["warnings"]:
                st.warning(warning)

            st.markdown("**Препоръки:**")
            for recommendation in row["recommendations"]:
                st.success(recommendation)

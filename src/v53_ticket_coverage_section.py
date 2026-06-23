from __future__ import annotations

import streamlit as st

from src.v53_ticket_coverage_engine import analyze_ticket_coverage, parse_ticket_lines


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _sample_ticket_text() -> str:
    return "\n".join(
        [
            "4, 12, 21, 25, 34, 48",
            "6, 13, 16, 19, 42, 44",
            "4, 12, 22, 28, 37, 49",
            "1, 8, 15, 23, 31, 46",
        ]
    )


def _session_ticket_text() -> str:
    candidate_keys = [
        "generated_tickets",
        "ticket_builder_combinations",
        "smart_ticket_builder_combinations",
        "v52_generated_tickets",
        "current_ticket_combinations",
    ]

    for key in candidate_keys:
        value = st.session_state.get(key)
        if not isinstance(value, list):
            continue

        lines: list[str] = []
        for item in value:
            if isinstance(item, (list, tuple)) and len(item) == 6:
                try:
                    numbers = [int(number) for number in item]
                except Exception:
                    continue
                lines.append(", ".join(str(number) for number in numbers))

        if lines:
            return "\n".join(lines)

    return _sample_ticket_text()


def _show_validation_table(rows: list[dict]) -> None:
    table_rows = []

    for row in rows:
        table_rows.append(
            {
                "№": row["ticket_index"],
                "Комбинация": row["combination_text"],
                "Статус": row["status"],
            }
        )

    st.dataframe(table_rows, use_container_width=True, hide_index=True)


def _show_small_table(title: str, data: dict[str, int]) -> None:
    st.markdown(f"#### {title}")
    rows = [{"Показател": key, "Брой": value} for key, value in data.items()]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_v53_ticket_coverage_section() -> None:
    st.title("Покритие на комбинациите")

    st.markdown(
        "Тази страница проверява дали няколко комбинации във фиша са прекалено близки "
        "една до друга, или покриват по-различни числови сценарии."
    )

    st.warning(
        "Този анализ не увеличава математически гаранцията за печалба. "
        "Той оценява само разнообразието и покритието на избраните комбинации."
    )

    ticket_text = st.text_area(
        "Комбинации за анализ",
        value=_session_ticket_text(),
        height=170,
        help="Въведи по една комбинация на ред. Може със запетая, интервал или друг разделител.",
    )

    if not st.button("Анализирай покритието", type="primary"):
        st.info("Въведи или остави примерните комбинации и натисни бутона за анализ.")
        return

    combinations = parse_ticket_lines(ticket_text)
    result = analyze_ticket_coverage(combinations)

    if not combinations:
        st.error("Не са открити комбинации. Въведи поне една линия с числа.")
        return

    st.subheader(result["band"])

    score = float(result["coverage_score"])
    st.progress(int(score) / 100)
    st.caption(f"Оценка на покритието: {score:.2f} / 100")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Валидни комбинации", result["ticket_count"])
    col2.metric("Уникални числа", result["unique_numbers_count"])
    col3.metric("Ефективност", _percent(result["coverage_efficiency"]))
    col4.metric("Средно припокриване", result["average_pairwise_overlap"])
    col5.metric("Макс. припокриване", result["maximum_pairwise_overlap"])

    col6, col7, col8 = st.columns(3)
    col6.metric("Повторени двойки", result["repeated_pairs_count"])
    col7.metric("Повторени тройки", result["repeated_triples_count"])
    col8.metric("Дублирани комбинации", result["duplicate_tickets_count"])

    st.markdown("#### Използвани уникални числа")
    if result["unique_numbers"]:
        st.write(", ".join(str(number) for number in result["unique_numbers"]))
    else:
        st.write("Няма валидни числа за показване.")

    st.markdown("#### Предупреждения")
    for warning in result["warnings"]:
        st.warning(warning)

    st.markdown("#### Препоръки")
    for recommendation in result["recommendations"]:
        st.success(recommendation)

    st.markdown("#### Проверка на въведените комбинации")
    _show_validation_table(result["validation_rows"])

    left, right = st.columns(2)
    with left:
        _show_small_table(
            "Четни / нечетни",
            {
                "Нечетни": result["odd_even_distribution"]["odd"],
                "Четни": result["odd_even_distribution"]["even"],
            },
        )

    with right:
        _show_small_table(
            "Ниски / високи",
            {
                "1-24": result["low_high_distribution"]["low_1_24"],
                "25-49": result["low_high_distribution"]["high_25_49"],
            },
        )

    _show_small_table("Разпределение по диапазони", result["range_distribution"])

    if result["top_repeated_pairs"]:
        st.markdown("#### Най-често повторени двойки")
        pair_rows = [
            {"Двойка": ", ".join(str(number) for number in row["pair"]), "Повторения": row["count"]}
            for row in result["top_repeated_pairs"]
        ]
        st.dataframe(pair_rows, use_container_width=True, hide_index=True)

    if result["top_repeated_triples"]:
        st.markdown("#### Най-често повторени тройки")
        triple_rows = [
            {"Тройка": ", ".join(str(number) for number in row["triple"]), "Повторения": row["count"]}
            for row in result["top_repeated_triples"]
        ]
        st.dataframe(triple_rows, use_container_width=True, hide_index=True)


from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v88_anti_zero_coverage_engine import (
    analyze_package,
    build_four_combination_coverage_ticket,
    compare_current_vs_coverage_candidate,
    load_existing_active_package,
)


def _t(value: str) -> str:
    return value.encode("utf-8").decode("unicode_escape")


TITLE = _t("\\u0417\\u0430\\u0449\\u0438\\u0442\\u0430 \\u043e\\u0442 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d \\u0444\\u0438\\u0448")
INTRO = _t("\\u0422\\u043e\\u0437\\u0438 \\u0441\\u043b\\u043e\\u0439 \\u043d\\u0435 \\u043e\\u0431\\u0435\\u0449\\u0430\\u0432\\u0430 \\u043f\\u0435\\u0447\\u0430\\u043b\\u0431\\u0430. \\u0422\\u043e\\u0439 \\u043f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430 \\u043a\\u043e\\u043b\\u043a\\u043e \\u0448\\u0438\\u0440\\u043e\\u043a\\u043e \\u0435 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435\\u0442\\u043e \\u043d\\u0430 \\u0447\\u0438\\u0441\\u043b\\u0430\\u0442\\u0430 \\u0438 \\u043a\\u043e\\u043b\\u043a\\u043e \\u043d\\u0438\\u0441\\u044a\\u043a \\u0435 \\u0440\\u0438\\u0441\\u043a\\u044a\\u0442 \\u0446\\u0435\\u043b\\u0438\\u044f\\u0442 \\u043f\\u0430\\u043a\\u0435\\u0442 \\u0434\\u0430 \\u043e\\u0441\\u0442\\u0430\\u043d\\u0435 \\u0431\\u0435\\u0437 \\u043d\\u0438\\u0442\\u043e \\u0435\\u0434\\u043d\\u043e \\u0441\\u044a\\u0432\\u043f\\u0430\\u0434\\u0435\\u043d\\u0438\\u0435.")
HOW_TO_READ = _t("\\u041a\\u0430\\u043a \\u0434\\u0430 \\u0433\\u043e \\u0447\\u0435\\u0442\\u0435\\u0448")
CURRENT_PACKAGE = _t("\\u0422\\u0435\\u043a\\u0443\\u0449 \\u043f\\u0430\\u043a\\u0435\\u0442")
CANDIDATE_PACKAGE = _t("\\u0417\\u0430\\u0449\\u0438\\u0442\\u0435\\u043d \\u0432\\u0430\\u0440\\u0438\\u0430\\u043d\\u0442")
CANDIDATE_TITLE = _t("\\u0420\\u0435\\u0444\\u0435\\u0440\\u0435\\u043d\\u0442\\u0435\\u043d \\u0444\\u0438\\u0448 \\u0441 \\u043f\\u043e-\\u0448\\u0438\\u0440\\u043e\\u043a\\u043e \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435")
COMPARISON = _t("\\u0421\\u0440\\u0430\\u0432\\u043d\\u0435\\u043d\\u0438\\u0435")
SAFE_NOTE = _t("\\u0422\\u043e\\u0432\\u0430 \\u0435 \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u043a\\u043e\\u043d\\u0442\\u0440\\u043e\\u043b \\u043d\\u0430 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435\\u0442\\u043e, \\u043d\\u0435 \\u043f\\u0440\\u043e\\u0433\\u043d\\u043e\\u0437\\u0430 \\u0438 \\u043d\\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f \\u0437\\u0430 \\u043f\\u0435\\u0447\\u0430\\u043b\\u0431\\u0430.")
EMPTY_RISK = _t("\\u0420\\u0438\\u0441\\u043a \\u043e\\u0442 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442")
AT_LEAST_ONE = _t("\\u0428\\u0430\\u043d\\u0441 \\u0437\\u0430 \\u043f\\u043e\\u043d\\u0435 1 \\u0441\\u044a\\u0432\\u043f\\u0430\\u0434\\u0435\\u043d\\u0438\\u0435")
UNIQUE_NUMBERS = _t("\\u041f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438 \\u0440\\u0430\\u0437\\u043b\\u0438\\u0447\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430")
REPEATS = _t("\\u041f\\u043e\\u0432\\u0442\\u043e\\u0440\\u0435\\u043d\\u0438\\u044f")
COMBINATION = _t("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f")
NUMBERS = _t("\\u0427\\u0438\\u0441\\u043b\\u0430")
NOTE = _t("\\u0417\\u0430\\u0431\\u0435\\u043b\\u0435\\u0436\\u043a\\u0430")
VALID = _t("\\u0412\\u0430\\u043b\\u0438\\u0434\\u043d\\u0430 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f")
REFERENCE = _t("\\u0417\\u0430\\u0449\\u0438\\u0442\\u043d\\u0430 \\u0440\\u0435\\u0444\\u0435\\u0440\\u0435\\u043d\\u0446\\u0438\\u044f")
OVERLAP = _t("\\u041f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435")
BALANCE = _t("\\u0411\\u0430\\u043b\\u0430\\u043d\\u0441")
LOW = _t("\\u043d\\u0438\\u0441\\u043a\\u0438")
MID = _t("\\u0441\\u0440\\u0435\\u0434\\u043d\\u0438")
HIGH = _t("\\u0432\\u0438\\u0441\\u043e\\u043a\\u0438")
EVEN = _t("\\u0447\\u0435\\u0442\\u043d\\u0438")
ODD = _t("\\u043d\\u0435\\u0447\\u0435\\u0442\\u043d\\u0438")


def _numbers_text(numbers: list[int]) -> str:
    return ", ".join(str(number) for number in numbers)


def _percent(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _count_repeats(combinations: list[list[int]]) -> int:
    counts: dict[int, int] = {}
    for combo in combinations:
        for number in combo:
            counts[number] = counts.get(number, 0) + 1
    return sum(max(0, count - 1) for count in counts.values())


def _balance_text(numbers: list[int]) -> str:
    low = sum(1 for number in numbers if 1 <= number <= 16)
    mid = sum(1 for number in numbers if 17 <= number <= 33)
    high = sum(1 for number in numbers if 34 <= number <= 49)
    even = sum(1 for number in numbers if number % 2 == 0)
    odd = len(numbers) - even
    return f"{low} {LOW} / {mid} {MID} / {high} {HIGH}; {even} {EVEN} / {odd} {ODD}"


def _overlap_with_previous(index: int, combinations: list[list[int]]) -> str:
    if index == 0:
        return "0"
    current = set(combinations[index])
    overlaps = [len(current.intersection(set(previous))) for previous in combinations[:index]]
    return str(max(overlaps) if overlaps else 0)


def _package_table(combinations: list[list[int]], candidate: bool = False) -> pd.DataFrame:
    rows = []
    for index, combo in enumerate(combinations, start=1):
        row = {
            COMBINATION: index,
            NUMBERS: _numbers_text(combo),
            UNIQUE_NUMBERS: len(set(combo)),
            NOTE: REFERENCE if candidate else VALID,
        }
        if candidate:
            row[OVERLAP] = _overlap_with_previous(index - 1, combinations)
            row[BALANCE] = _balance_text(combo)
        rows.append(row)
    return pd.DataFrame(rows)


def _safe_analysis(combinations: list[list[int]]) -> dict:
    try:
        return analyze_package(combinations)
    except Exception:
        return {}


def render_v88_anti_zero_coverage_section() -> None:
    st.title(TITLE)
    st.caption(INTRO)

    try:
        current_combinations, _metadata = load_existing_active_package()
    except Exception as exc:
        st.error(_t("\\u041d\\u0435 \\u0443\\u0441\\u043f\\u044f\\u0445 \\u0434\\u0430 \\u0437\\u0430\\u0440\\u0435\\u0434\\u044f \\u0442\\u0435\\u043a\\u0443\\u0449\\u0438\\u044f \\u043f\\u0430\\u043a\\u0435\\u0442."))
        st.exception(exc)
        return

    if not current_combinations:
        st.warning(_t("\\u041d\\u044f\\u043c\\u0430 \\u043d\\u0430\\u043c\\u0435\\u0440\\u0435\\u043d \\u0430\\u043a\\u0442\\u0438\\u0432\\u0435\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442 \\u0437\\u0430 \\u0430\\u043d\\u0430\\u043b\\u0438\\u0437."))
        return

    candidate_combinations = build_four_combination_coverage_ticket(existing_combinations=current_combinations)

    try:
        comparison = compare_current_vs_coverage_candidate(current_combinations, candidate_combinations)
        current_analysis = comparison.get("current_analysis", _safe_analysis(current_combinations))
        candidate_analysis = comparison.get("candidate_analysis", _safe_analysis(candidate_combinations))
    except Exception:
        current_analysis = _safe_analysis(current_combinations)
        candidate_analysis = _safe_analysis(candidate_combinations)

    current_empty = _percent(current_analysis.get("empty_risk_percent"))
    candidate_empty = _percent(candidate_analysis.get("empty_risk_percent"))
    current_hit = _percent(current_analysis.get("at_least_one_hit_percent"))
    candidate_hit = _percent(candidate_analysis.get("at_least_one_hit_percent"))

    with st.container(border=True):
        st.subheader(HOW_TO_READ)
        st.markdown(
            _t(
                "- \\u0422\\u0435\\u043a\\u0443\\u0449\\u0438\\u044f\\u0442 \\u043f\\u0430\\u043a\\u0435\\u0442 \\u0435 \\u0442\\u043e\\u0432\\u0430, \\u043a\\u043e\\u0435\\u0442\\u043e \\u0432\\u0435\\u0447\\u0435 \\u0438\\u043c\\u0430\\u0448 \\u0432 \\u0441\\u0438\\u0441\\u0442\\u0435\\u043c\\u0430\\u0442\\u0430.\\n"
                "- \\u0417\\u0430\\u0449\\u0438\\u0442\\u043d\\u0438\\u044f\\u0442 \\u0432\\u0430\\u0440\\u0438\\u0430\\u043d\\u0442 \\u0435 \\u0441\\u0430\\u043c\\u043e \\u043f\\u0440\\u0438\\u043c\\u0435\\u0440 \\u0441 4 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438 \\u0438 \\u043f\\u043e-\\u043c\\u0430\\u043b\\u043a\\u043e \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435.\\n"
                "- \\u041a\\u043e\\u043b\\u043a\\u043e\\u0442\\u043e \\u043f\\u043e\\u0432\\u0435\\u0447\\u0435 \\u0440\\u0430\\u0437\\u043b\\u0438\\u0447\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430 \\u043f\\u0430\\u043a\\u0435\\u0442\\u044a\\u0442, \\u0442\\u043e\\u043b\\u043a\\u043e\\u0432\\u0430 \\u043f\\u043e-\\u043c\\u0430\\u043b\\u044a\\u043a \\u0435 \\u0440\\u0438\\u0441\\u043a\\u044a\\u0442 \\u0434\\u0430 \\u043d\\u044f\\u043c\\u0430 \\u043d\\u0438\\u0442\\u043e \\u0435\\u0434\\u043d\\u043e \\u0441\\u044a\\u0432\\u043f\\u0430\\u0434\\u0435\\u043d\\u0438\\u0435.\\n"
                "- \\u0422\\u043e\\u0432\\u0430 \\u043d\\u0435 \\u043f\\u043e\\u0432\\u0438\\u0448\\u0430\\u0432\\u0430 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0442\\u0438\\u0440\\u0430\\u043d\\u043e \\u0448\\u0430\\u043d\\u0441\\u0430 \\u0437\\u0430 6/6; \\u0442\\u043e \\u0435 \\u043a\\u043e\\u043d\\u0442\\u0440\\u043e\\u043b \\u043d\\u0430 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435\\u0442\\u043e."
            )
        )

    status = str(candidate_analysis.get("risk_level") or current_analysis.get("risk_level") or _t("\\u0414\\u043e\\u0431\\u0440\\u043e \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435"))
    message = str(candidate_analysis.get("risk_message_bg") or _t("\\u0417\\u0430\\u0449\\u0438\\u0442\\u043d\\u0438\\u044f\\u0442 \\u0432\\u0430\\u0440\\u0438\\u0430\\u043d\\u0442 \\u0440\\u0430\\u0437\\u0448\\u0438\\u0440\\u044f\\u0432\\u0430 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435\\u0442\\u043e."))
    st.info(f"**{status}**  \\n{message}")

    col1, col2, col3, col4 = st.columns(4)
    current_unique = int(current_analysis.get("unique_covered_numbers", 0) or 0)
    candidate_unique = int(candidate_analysis.get("unique_covered_numbers", 0) or 0)
    col1.metric(UNIQUE_NUMBERS, f"{current_unique} -> {candidate_unique}", delta=f"+{candidate_unique - current_unique}")
    col2.metric(EMPTY_RISK, f"{current_empty:.2f}% -> {candidate_empty:.2f}%", delta=f"{candidate_empty - current_empty:.2f} p.p.")
    col3.metric(AT_LEAST_ONE, f"{current_hit:.2f}% -> {candidate_hit:.2f}%", delta=f"+{candidate_hit - current_hit:.2f} p.p.")
    col4.metric(REPEATS, f"{_count_repeats(current_combinations)} -> {_count_repeats(candidate_combinations)}")

    st.subheader(CURRENT_PACKAGE)
    st.write(_t("\\u0422\\u043e\\u0432\\u0430 \\u0435 \\u0430\\u043a\\u0442\\u0438\\u0432\\u043d\\u0438\\u044f\\u0442 \\u043f\\u0430\\u043a\\u0435\\u0442. \\u0421\\u0438\\u0441\\u0442\\u0435\\u043c\\u0430\\u0442\\u0430 \\u043d\\u0435 \\u0433\\u043e \\u043f\\u0440\\u043e\\u043c\\u0435\\u043d\\u044f \\u0430\\u0432\\u0442\\u043e\\u043c\\u0430\\u0442\\u0438\\u0447\\u043d\\u043e; \\u0441\\u0430\\u043c\\u043e \\u0433\\u043e \\u0430\\u043d\\u0430\\u043b\\u0438\\u0437\\u0438\\u0440\\u0430."))
    st.dataframe(_package_table(current_combinations), use_container_width=True, hide_index=True)

    st.subheader(CANDIDATE_TITLE)
    st.write(_t("\\u0422\\u043e\\u0432\\u0430 \\u0435 \\u043f\\u0440\\u0438\\u043c\\u0435\\u0440\\u0435\\u043d \\u0437\\u0430\\u0449\\u0438\\u0442\\u0435\\u043d \\u0444\\u0438\\u0448 \\u0441 4 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438. \\u0418\\u0434\\u0435\\u044f\\u0442\\u0430 \\u0435 \\u0434\\u0430 \\u0438\\u043c\\u0430 \\u043f\\u043e-\\u043c\\u0430\\u043b\\u043a\\u043e \\u0434\\u0443\\u0431\\u043b\\u0438\\u0440\\u0430\\u043d\\u0435 \\u0438 \\u043f\\u043e-\\u0448\\u0438\\u0440\\u043e\\u043a\\u043e \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435."))
    st.dataframe(_package_table(candidate_combinations, candidate=True), use_container_width=True, hide_index=True)

    st.subheader(COMPARISON)
    comparison_rows = [
        {
            _t("\\u041f\\u043e\\u043a\\u0430\\u0437\\u0430\\u0442\\u0435\\u043b"): UNIQUE_NUMBERS,
            CURRENT_PACKAGE: current_unique,
            CANDIDATE_PACKAGE: candidate_unique,
            _t("\\u0420\\u0430\\u0437\\u043b\\u0438\\u043a\\u0430"): candidate_unique - current_unique,
        },
        {
            _t("\\u041f\\u043e\\u043a\\u0430\\u0437\\u0430\\u0442\\u0435\\u043b"): EMPTY_RISK,
            CURRENT_PACKAGE: f"{current_empty:.2f}%",
            CANDIDATE_PACKAGE: f"{candidate_empty:.2f}%",
            _t("\\u0420\\u0430\\u0437\\u043b\\u0438\\u043a\\u0430"): f"{candidate_empty - current_empty:.2f} p.p.",
        },
        {
            _t("\\u041f\\u043e\\u043a\\u0430\\u0437\\u0430\\u0442\\u0435\\u043b"): AT_LEAST_ONE,
            CURRENT_PACKAGE: f"{current_hit:.2f}%",
            CANDIDATE_PACKAGE: f"{candidate_hit:.2f}%",
            _t("\\u0420\\u0430\\u0437\\u043b\\u0438\\u043a\\u0430"): f"+{candidate_hit - current_hit:.2f} p.p.",
        },
    ]
    st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True, hide_index=True)

    with st.expander(_t("\\u041a\\u0430\\u043a \\u0441\\u0435 \\u0438\\u0437\\u0447\\u0438\\u0441\\u043b\\u044f\\u0432\\u0430 \\u0440\\u0438\\u0441\\u043a\\u044a\\u0442?")):
        st.markdown(_t("\\u0418\\u0437\\u0447\\u0438\\u0441\\u043b\\u0435\\u043d\\u0438\\u0435\\u0442\\u043e \\u0433\\u043b\\u0435\\u0434\\u0430 \\u043a\\u043e\\u043b\\u043a\\u043e \\u0440\\u0430\\u0437\\u043b\\u0438\\u0447\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430 \\u043f\\u0430\\u043a\\u0435\\u0442\\u044a\\u0442. \\u0410\\u043a\\u043e \\u0442\\u0435\\u0433\\u043b\\u0435\\u043d\\u0435\\u0442\\u043e \\u043f\\u043e\\u043f\\u0430\\u0434\\u043d\\u0435 \\u0438\\u0437\\u0446\\u044f\\u043b\\u043e \\u0438\\u0437\\u0432\\u044a\\u043d \\u0442\\u0435\\u0437\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430, \\u043f\\u0430\\u043a\\u0435\\u0442\\u044a\\u0442 \\u043e\\u0441\\u0442\\u0430\\u0432\\u0430 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d.\\n\\n**C(49 - \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430, 6) / C(49, 6)**"))

    st.warning(SAFE_NOTE)

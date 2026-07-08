
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_JSON = ROOT / "reports" / "v51_ticket_portfolio_summary.json"
CURRENT_SCORE_CSV = ROOT / "reports" / "v51_current_pro_ticket_score.csv"


def T(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _rating_label(value: str) -> str:
    labels = {
        "strong": T("\\u0421\\u0438\\u043b\\u0435\\u043d \\u0444\\u0438\\u0448"),
        "balanced": T("\\u0411\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d \\u0444\\u0438\\u0448"),
        "medium": T("\\u0421\\u0440\\u0435\\u0434\\u0435\\u043d \\u0444\\u0438\\u0448"),
        "weak": T("\\u041d\\u0435\\u0431\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d \\u0444\\u0438\\u0448"),
        "missing": T("\\u041d\\u044f\\u043c\\u0430 \\u0434\\u0430\\u043d\\u043d\\u0438"),
    }
    return labels.get(value, value)


def _warning_label(code: str) -> str:
    labels = {
        "missing_combinations": T("\\u041d\\u044f\\u043c\\u0430 \\u043d\\u0430\\u043b\\u0438\\u0447\\u043d\\u0438 Pro \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438."),
        "high_average_overlap": T("\\u0421\\u0440\\u0435\\u0434\\u043d\\u043e\\u0442\\u043e \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435 \\u043c\\u0435\\u0436\\u0434\\u0443 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438\\u0442\\u0435 \\u0435 \\u0432\\u0438\\u0441\\u043e\\u043a\\u043e."),
        "high_max_overlap": T("\\u0418\\u043c\\u0430 \\u0434\\u0432\\u0435 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438 \\u0441 \\u0442\\u0432\\u044a\\u0440\\u0434\\u0435 \\u043c\\u043d\\u043e\\u0433\\u043e \\u043e\\u0431\\u0449\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430."),
        "too_much_repetition": T("\\u041d\\u044f\\u043a\\u043e\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430 \\u0441\\u0435 \\u043f\\u043e\\u0432\\u0442\\u0430\\u0440\\u044f\\u0442 \\u0442\\u0432\\u044a\\u0440\\u0434\\u0435 \\u0447\\u0435\\u0441\\u0442\\u043e \\u0432 \\u0446\\u0435\\u043b\\u0438\\u044f \\u0444\\u0438\\u0448."),
        "weak_combo_structure": T("\\u0421\\u0440\\u0435\\u0434\\u043d\\u0430\\u0442\\u0430 \\u0441\\u0442\\u0440\\u0443\\u043a\\u0442\\u0443\\u0440\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438\\u0442\\u0435 \\u0435 \\u043d\\u0438\\u0441\\u043a\\u0430."),
        "low_number_coverage": T("\\u0424\\u0438\\u0448\\u044a\\u0442 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430 \\u0442\\u0432\\u044a\\u0440\\u0434\\u0435 \\u043c\\u0430\\u043b\\u043a\\u043e \\u0443\\u043d\\u0438\\u043a\\u0430\\u043b\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430."),
    }
    return labels.get(code, code)


def _strength_label(code: str) -> str:
    labels = {
        "good_diversity": T("\\u0414\\u043e\\u0431\\u0440\\u043e \\u0440\\u0430\\u0437\\u043d\\u043e\\u043e\\u0431\\u0440\\u0430\\u0437\\u0438\\u0435 \\u043c\\u0435\\u0436\\u0434\\u0443 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438\\u0442\\u0435."),
        "controlled_repetition": T("\\u041f\\u043e\\u0432\\u0442\\u043e\\u0440\\u0435\\u043d\\u0438\\u044f\\u0442\\u0430 \\u043d\\u0430 \\u0447\\u0438\\u0441\\u043b\\u0430 \\u0441\\u0430 \\u043a\\u043e\\u043d\\u0442\\u0440\\u043e\\u043b\\u0438\\u0440\\u0430\\u043d\\u0438."),
        "solid_combo_structure": T("\\u041e\\u0442\\u0434\\u0435\\u043b\\u043d\\u0438\\u0442\\u0435 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438 \\u0438\\u043c\\u0430\\u0442 \\u0434\\u043e\\u0431\\u0440\\u0430 \\u0441\\u0442\\u0440\\u0443\\u043a\\u0442\\u0443\\u0440\\u0430."),
        "good_number_coverage": T("\\u0424\\u0438\\u0448\\u044a\\u0442 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430 \\u0434\\u043e\\u0431\\u044a\\u0440 \\u0431\\u0440\\u043e\\u0439 \\u0443\\u043d\\u0438\\u043a\\u0430\\u043b\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430."),
    }
    return labels.get(code, code)


def _rename_combo_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "combination": T("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f"),
        "combo_score": T("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430"),
        "pair_average": T("\\u0421\\u0440\\u0435\\u0434\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438"),
        "strong_pairs": T("\\u0421\\u0438\\u043b\\u043d\\u0438 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438"),
        "group_average": T("\\u0421\\u0440\\u0435\\u0434\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438"),
        "strong_groups": T("\\u0421\\u0438\\u043b\\u043d\\u0438 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438"),
        "sum": T("\\u0421\\u0443\\u043c\\u0430"),
        "even_count": T("\\u0427\\u0435\\u0442\\u043d\\u0438"),
        "low_count": T("\\u041d\\u0438\\u0441\\u043a\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"),
        "range_span": T("\\u0420\\u0430\\u0437\\u043c\\u0430\\u0445"),
        "consecutive_pairs": T("\\u041f\\u043e\\u0440\\u0435\\u0434\\u043d\\u0438 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438"),
    }

    preferred = [
        "combination",
        "combo_score",
        "pair_average",
        "strong_pairs",
        "group_average",
        "strong_groups",
        "sum",
        "even_count",
        "low_count",
        "range_span",
        "consecutive_pairs",
    ]

    cols = [col for col in preferred if col in df.columns]
    remaining = [col for col in df.columns if col not in cols]
    return df[cols + remaining].rename(columns=rename)


def render() -> None:
    st.title(T("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u0444\\u0438\\u0448"))

    st.caption(
        T(
            "\\u0422\\u043e\\u0437\\u0438 \\u043c\\u043e\\u0434\\u0443\\u043b \\u0433\\u043b\\u0435\\u0434\\u0430 \\u0446\\u0435\\u043b\\u0438\\u044f \\u0444\\u0438\\u0448 \\u043a\\u0430\\u0442\\u043e \\u0441\\u0438\\u0441\\u0442\\u0435\\u043c\\u0430: \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435, \\u0440\\u0430\\u0437\\u043d\\u043e\\u043e\\u0431\\u0440\\u0430\\u0437\\u0438\\u0435, \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438, \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438 \\u0438 \\u0431\\u0430\\u043b\\u0430\\u043d\\u0441."
        )
    )

    st.warning(
        T(
            "\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430\\u0442\\u0430 \\u0435 \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430. \\u0422\\u044f \\u043d\\u0435 \\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f \\u0437\\u0430 \\u043f\\u0435\\u0447\\u0430\\u043b\\u0431\\u0430."
        )
    )

    summary = _read_json(SUMMARY_JSON)
    df = _read_csv(CURRENT_SCORE_CSV)

    if not summary or df.empty:
        st.info(T("\\u041f\\u0443\\u0441\\u043d\\u0438 `python scripts/v51_build_ticket_portfolio_intelligence.py`, \\u0437\\u0430 \\u0434\\u0430 \\u0441\\u0435 \\u0441\\u044a\\u0437\\u0434\\u0430\\u0434\\u0430\\u0442 v51 \\u043e\\u0442\\u0447\\u0435\\u0442\\u0438\\u0442\\u0435."))
        return

    portfolio = summary.get("portfolio", {})
    metrics = portfolio.get("metrics", {})
    score = float(portfolio.get("overall_score", 0.0))
    rating = str(portfolio.get("rating", "missing"))

    tabs = st.tabs(
        [
            T("\\u041e\\u0431\\u043e\\u0431\\u0449\\u0435\\u043d\\u0438\\u0435"),
            T("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438"),
            T("\\u0421\\u0438\\u043b\\u043d\\u0438 \\u0441\\u0442\\u0440\\u0430\\u043d\\u0438"),
            T("\\u0412\\u043d\\u0438\\u043c\\u0430\\u043d\\u0438\\u0435"),
            T("\\u041a\\u0430\\u043a \\u0441\\u0435 \\u0438\\u0437\\u043f\\u043e\\u043b\\u0437\\u0432\\u0430"),
        ]
    )

    with tabs[0]:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T("\\u041e\\u0431\\u0449\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430"), f"{score:.2f} / 100")
        c2.metric(T("\\u041a\\u043b\\u0430\\u0441"), _rating_label(rating))
        c3.metric(T("\\u0423\\u043d\\u0438\\u043a\\u0430\\u043b\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"), str(metrics.get("unique_numbers", "-")))
        c4.metric(T("\\u041c\\u0430\\u043a\\u0441. \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435"), str(metrics.get("max_overlap", "-")))

        st.progress(min(max(score / 100.0, 0.0), 1.0))

        metric_rows = [
            {T("\\u041f\\u043e\\u043a\\u0430\\u0437\\u0430\\u0442\\u0435\\u043b"): T("\\u0411\\u0440\\u043e\\u0439 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438"), T("\\u0421\\u0442\\u043e\\u0439\\u043d\\u043e\\u0441\\u0442"): metrics.get("combination_count", "-")},
            {T("\\u041f\\u043e\\u043a\\u0430\\u0437\\u0430\\u0442\\u0435\\u043b"): T("\\u0421\\u0440\\u0435\\u0434\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438"), T("\\u0421\\u0442\\u043e\\u0439\\u043d\\u043e\\u0441\\u0442"): metrics.get("average_combo_score", "-")},
            {T("\\u041f\\u043e\\u043a\\u0430\\u0437\\u0430\\u0442\\u0435\\u043b"): T("\\u0421\\u0440\\u0435\\u0434\\u043d\\u043e \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435"), T("\\u0421\\u0442\\u043e\\u0439\\u043d\\u043e\\u0441\\u0442"): metrics.get("average_overlap", "-")},
            {T("\\u041f\\u043e\\u043a\\u0430\\u0437\\u0430\\u0442\\u0435\\u043b"): T("\\u041d\\u0430\\u0439-\\u0447\\u0435\\u0441\\u0442\\u043e \\u043f\\u043e\\u0432\\u0442\\u043e\\u0440\\u0435\\u043d\\u043e \\u0447\\u0438\\u0441\\u043b\\u043e"), T("\\u0421\\u0442\\u043e\\u0439\\u043d\\u043e\\u0441\\u0442"): metrics.get("max_repeat", "-")},
        ]
        st.dataframe(pd.DataFrame(metric_rows), hide_index=True, width="stretch")

    with tabs[1]:
        st.subheader(T("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u0432\\u0441\\u044f\\u043a\\u0430 Pro \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f"))
        st.dataframe(_rename_combo_columns(df), hide_index=True, width="stretch")

    with tabs[2]:
        strengths = portfolio.get("strength_codes", [])
        if not strengths:
            st.info(T("\\u041d\\u044f\\u043c\\u0430 \\u044f\\u0441\\u043d\\u043e \\u043e\\u0442\\u043a\\u0440\\u043e\\u0435\\u043d\\u0438 \\u0441\\u0438\\u043b\\u043d\\u0438 \\u0441\\u0442\\u0440\\u0430\\u043d\\u0438."))
        else:
            for code in strengths:
                st.success(_strength_label(str(code)))

    with tabs[3]:
        warnings = portfolio.get("warning_codes", [])
        if not warnings:
            st.success(T("\\u041d\\u044f\\u043c\\u0430 \\u043e\\u0441\\u043d\\u043e\\u0432\\u043d\\u0438 \\u0441\\u0442\\u0440\\u0443\\u043a\\u0442\\u0443\\u0440\\u043d\\u0438 \\u043f\\u0440\\u0435\\u0434\\u0443\\u043f\\u0440\\u0435\\u0436\\u0434\\u0435\\u043d\\u0438\\u044f."))
        else:
            for code in warnings:
                st.warning(_warning_label(str(code)))

    with tabs[4]:
        st.markdown(
            T(
                """
- \\u0422\\u043e\\u0437\\u0438 \\u043c\\u043e\\u0434\\u0435\\u043b \\u043d\\u0435 \\u0438\\u0437\\u0431\\u0438\\u0440\\u0430 \\u0441\\u0430\\u043c \\u0447\\u0438\\u0441\\u043b\\u0430, \\u0430 \\u043e\\u0446\\u0435\\u043d\\u044f\\u0432\\u0430 \\u0446\\u0435\\u043b\\u0438\\u044f \\u0444\\u0438\\u0448.
- \\u0418\\u0437\\u043f\\u043e\\u043b\\u0437\\u0432\\u0430 v50 \\u0441\\u0438\\u0433\\u043d\\u0430\\u043b\\u0438\\u0442\\u0435 \\u0437\\u0430 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438 \\u0438 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438.
- \\u0413\\u043b\\u0435\\u0434\\u0430 \\u043f\\u0440\\u0438\\u043f\\u043e\\u043a\\u0440\\u0438\\u0432\\u0430\\u043d\\u0435, \\u0440\\u0430\\u0437\\u043d\\u043e\\u043e\\u0431\\u0440\\u0430\\u0437\\u0438\\u0435, \\u0441\\u0443\\u043c\\u0430, \\u0447\\u0435\\u0442\\u043d\\u0438/\\u043d\\u0435\\u0447\\u0435\\u0442\\u043d\\u0438 \\u0438 \\u043d\\u0438\\u0441\\u043a\\u0438/\\u0432\\u0438\\u0441\\u043e\\u043a\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430.
- \\u0426\\u0435\\u043b\\u0442\\u0430 \\u0435 \\u043f\\u043e-\\u0434\\u043e\\u0431\\u0440\\u0430 \\u0434\\u0438\\u0441\\u0446\\u0438\\u043f\\u043b\\u0438\\u043d\\u0430 \\u043d\\u0430 \\u0444\\u0438\\u0448\\u0430, \\u043d\\u0435 \\u043e\\u0431\\u0435\\u0449\\u0430\\u043d\\u0438\\u0435 \\u0437\\u0430 \\u043f\\u0435\\u0447\\u0430\\u043b\\u0431\\u0430.
"""
            )
        )

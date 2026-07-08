
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.v89_final_statistical_portfolio_selector_engine import (
    MODEL_PATH,
    build_and_save,
)


def _t(value: str) -> str:
    return value.encode("utf-8").decode("unicode_escape")


TITLE = _t("\\u0424\\u0438\\u043d\\u0430\\u043b\\u0435\\u043d \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0438\\u0437\\u0431\\u043e\\u0440")
INTRO = _t("\\u0422\\u043e\\u0437\\u0438 \\u0441\\u043b\\u043e\\u0439 \\u0441\\u044a\\u0431\\u0438\\u0440\\u0430 \\u0441\\u0438\\u043b\\u0430\\u0442\\u0430 \\u043d\\u0430 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438\\u0442\\u0435, \\u043a\\u0430\\u0447\\u0435\\u0441\\u0442\\u0432\\u043e\\u0442\\u043e \\u043d\\u0430 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438\\u0442\\u0435, \\u0437\\u0430\\u0449\\u0438\\u0442\\u0430\\u0442\\u0430 \\u043e\\u0442 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442 \\u0438 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430\\u0442\\u0430 \\u0431\\u0435\\u0437\\u043e\\u043f\\u0430\\u0441\\u043d\\u043e\\u0441\\u0442.")
SAFE_NOTE = _t("\\u0422\\u043e\\u0432\\u0430 \\u0435 \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0438\\u0437\\u0431\\u043e\\u0440, \\u043d\\u0435 \\u043f\\u0440\\u043e\\u0433\\u043d\\u043e\\u0437\\u0430 \\u0438 \\u043d\\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f \\u0437\\u0430 \\u043f\\u0435\\u0447\\u0430\\u043b\\u0431\\u0430.")


def _load_model() -> dict[str, Any]:
    try:
        if Path(MODEL_PATH).exists():
            return json.loads(Path(MODEL_PATH).read_text(encoding="utf-8-sig"))
    except Exception:
        pass
    return build_and_save()


def _numbers_text(numbers: list[int]) -> str:
    return ", ".join(str(number) for number in numbers)


def _package_table(package: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for index, combo in enumerate(package.get("combinations", []), start=1):
        rows.append(
            {
                _t("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f"): index,
                _t("\\u0427\\u0438\\u0441\\u043b\\u0430"): _numbers_text(combo),
                _t("\\u0411\\u0440\\u043e\\u0439 \\u0447\\u0438\\u0441\\u043b\\u0430"): len(set(combo)),
            }
        )
    return pd.DataFrame(rows)


def _comparison_table(model: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for package in model.get("packages", []):
        mode_scores = package.get("mode_scores", {})
        rows.append(
            {
                _t("\\u041f\\u0430\\u043a\\u0435\\u0442"): package.get("package_label", ""),
                _t("\\u041f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"): package.get("unique_covered_numbers", 0),
                _t("\\u0420\\u0438\\u0441\\u043a \\u043e\\u0442 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442"): f"{float(package.get('empty_risk_percent', 0.0)):.2f}%",
                _t("\\u0421\\u0438\\u043b\\u0430 \\u043d\\u0430 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438\\u0442\\u0435"): f"{float(package.get('model_strength_score', 0.0)):.1f}",
                _t("\\u041a\\u0430\\u0447\\u0435\\u0441\\u0442\\u0432\\u043e"): f"{float(package.get('combination_quality_score', 0.0)):.1f}",
                _t("\\u0417\\u0430\\u0449\\u0438\\u0442\\u0430"): f"{float(package.get('anti_zero_score', 0.0)):.1f}",
                _t("\\u0411\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d \\u0440\\u0435\\u0436\\u0438\\u043c"): f"{float(mode_scores.get('balanced', 0.0)):.1f}",
                _t("\\u0417\\u0430\\u0449\\u0438\\u0442\\u0435\\u043d \\u0440\\u0435\\u0436\\u0438\\u043c"): f"{float(mode_scores.get('conservative', 0.0)):.1f}",
                _t("\\u0410\\u0433\\u0440\\u0435\\u0441\\u0438\\u0432\\u0435\\u043d \\u0440\\u0435\\u0436\\u0438\\u043c"): f"{float(mode_scores.get('aggressive', 0.0)):.1f}",
            }
        )
    return pd.DataFrame(rows)


def render_v89_final_statistical_portfolio_selector_section() -> None:
    st.title(TITLE)
    st.caption(INTRO)

    model = _load_model()
    recommendations = model.get("recommendations", {})
    balanced = model.get("balanced_recommendation") or recommendations.get("balanced") or {}

    st.info(
        _t(
            "\\u0418\\u0434\\u0435\\u044f\\u0442\\u0430 \\u0435 \\u0434\\u0430 \\u043d\\u0435 \\u0438\\u0437\\u0431\\u0438\\u0440\\u0430\\u043c\\u0435 \\u0441\\u0430\\u043c\\u043e \\u043d\\u0430\\u0439-\\u0441\\u0438\\u043b\\u043d\\u0438\\u0442\\u0435 \\u0447\\u0438\\u0441\\u043b\\u0430 \\u0438\\u043b\\u0438 \\u0441\\u0430\\u043c\\u043e \\u043d\\u0430\\u0439-\\u0448\\u0438\\u0440\\u043e\\u043a\\u043e\\u0442\\u043e \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435. \\u0422\\u0443\\u043a \\u0441\\u0438\\u0441\\u0442\\u0435\\u043c\\u0430\\u0442\\u0430 \\u0442\\u044a\\u0440\\u0441\\u0438 \\u043d\\u0430\\u0439-\\u0434\\u043e\\u0431\\u0440\\u0438\\u044f \\u043a\\u043e\\u043c\\u043f\\u0440\\u043e\\u043c\\u0438\\u0441."
        )
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(_t("\\u041f\\u0440\\u0435\\u0433\\u043b\\u0435\\u0434\\u0430\\u043d\\u0438 \\u043f\\u0430\\u043a\\u0435\\u0442\\u0438"), model.get("candidate_count", 0))
    col2.metric(_t("\\u0418\\u0437\\u0431\\u0440\\u0430\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442"), balanced.get("package_label", "-"))
    col3.metric(_t("\\u041a\\u0440\\u0430\\u0439\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430"), f"{float(balanced.get('mode_scores', {}).get('balanced', 0.0)):.1f}")
    col4.metric(_t("\\u0420\\u0438\\u0441\\u043a \\u043e\\u0442 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442"), f"{float(balanced.get('empty_risk_percent', 0.0)):.2f}%")

    st.subheader(_t("\\u0420\\u0435\\u0436\\u0438\\u043c\\u0438 \\u043d\\u0430 \\u0438\\u0437\\u0431\\u043e\\u0440"))
    mode_labels = model.get("mode_labels", {})
    mode_descriptions = model.get("mode_descriptions", {})

    mode_cols = st.columns(3)
    for col, mode in zip(mode_cols, ["balanced", "conservative", "aggressive"]):
        recommendation = recommendations.get(mode, {})
        with col:
            st.markdown(f"**{mode_labels.get(mode, mode)}**")
            st.write(mode_descriptions.get(mode, ""))
            st.metric(
                _t("\\u041f\\u0430\\u043a\\u0435\\u0442"),
                recommendation.get("package_label", "-"),
            )
            st.metric(
                _t("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430"),
                f"{float(recommendation.get('mode_scores', {}).get(mode, 0.0)):.1f}",
            )

    st.subheader(_t("\\u0421\\u0440\\u0430\\u0432\\u043d\\u0435\\u043d\\u0438\\u0435 \\u043d\\u0430 \\u043f\\u0430\\u043a\\u0435\\u0442\\u0438\\u0442\\u0435"))
    st.dataframe(_comparison_table(model), width="stretch", hide_index=True)

    st.subheader(_t("\\u0411\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d \\u043f\\u0440\\u0435\\u043f\\u043e\\u0440\\u044a\\u0447\\u0430\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442"))
    st.write(
        _t(
            "\\u0422\\u043e\\u0432\\u0430 \\u0435 \\u043f\\u0430\\u043a\\u0435\\u0442\\u044a\\u0442, \\u043a\\u043e\\u0439\\u0442\\u043e \\u0441\\u044a\\u0431\\u0438\\u0440\\u0430 \\u043d\\u0430\\u0439-\\u0434\\u043e\\u0431\\u044a\\u0440 \\u043e\\u0431\\u0449 \\u0431\\u0430\\u043b\\u0430\\u043d\\u0441 \\u043c\\u0435\\u0436\\u0434\\u0443 \\u043c\\u043e\\u0434\\u0435\\u043b\\u043d\\u0430 \\u0441\\u0438\\u043b\\u0430, \\u043a\\u0430\\u0447\\u0435\\u0441\\u0442\\u0432\\u043e, \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435 \\u0438 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430 \\u0431\\u0435\\u0437\\u043e\\u043f\\u0430\\u0441\\u043d\\u043e\\u0441\\u0442."
        )
    )
    st.dataframe(_package_table(balanced), width="stretch", hide_index=True)

    with st.expander(_t("\\u041a\\u0430\\u043a \\u0441\\u0435 \\u0441\\u043c\\u044f\\u0442\\u0430 \\u0438\\u0437\\u0431\\u043e\\u0440\\u044a\\u0442?")):
        st.markdown(
            _t(
                "- \\u0411\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d \\u0440\\u0435\\u0436\\u0438\\u043c: 50% \\u043c\\u043e\\u0434\\u0435\\u043b\\u043d\\u0430 \\u0441\\u0438\\u043b\\u0430, 20% \\u043a\\u0430\\u0447\\u0435\\u0441\\u0442\\u0432\\u043e, 20% \\u0437\\u0430\\u0449\\u0438\\u0442\\u0430 \\u043e\\u0442 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442, 10% \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430 \\u0431\\u0435\\u0437\\u043e\\u043f\\u0430\\u0441\\u043d\\u043e\\u0441\\u0442.\\n"
                "- \\u0417\\u0430\\u0449\\u0438\\u0442\\u0435\\u043d \\u0440\\u0435\\u0436\\u0438\\u043c: \\u043f\\u043e-\\u0433\\u043e\\u043b\\u044f\\u043c\\u0430 \\u0442\\u0435\\u0436\\u0435\\u0441\\u0442 \\u043d\\u0430 \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435\\u0442\\u043e.\\n"
                "- \\u0410\\u0433\\u0440\\u0435\\u0441\\u0438\\u0432\\u0435\\u043d \\u0440\\u0435\\u0436\\u0438\\u043c: \\u043f\\u043e-\\u0433\\u043e\\u043b\\u044f\\u043c\\u0430 \\u0442\\u0435\\u0436\\u0435\\u0441\\u0442 \\u043d\\u0430 \\u0441\\u0438\\u043b\\u0430\\u0442\\u0430 \\u043d\\u0430 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438\\u0442\\u0435.\\n"
                "- \\u0418 \\u0432 \\u0442\\u0440\\u0438\\u0442\\u0435 \\u0441\\u043b\\u0443\\u0447\\u0430\\u044f \\u0442\\u043e\\u0432\\u0430 \\u043e\\u0441\\u0442\\u0430\\u0432\\u0430 \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430 \\u043f\\u0440\\u0435\\u0446\\u0435\\u043d\\u043a\\u0430, \\u0430 \\u043d\\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f."
            )
        )

    st.warning(SAFE_NOTE)

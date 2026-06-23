
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

MODEL_PATH = Path("models/v89/v89_final_statistical_portfolio_selector_model.json")


def _t(value: str) -> str:
    return value.encode("utf-8").decode("unicode_escape")


TITLE = _t("\\u2b50 \\u041f\\u0440\\u0435\\u043f\\u043e\\u0440\\u044a\\u0447\\u0430\\u043d \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0444\\u0438\\u0448")
SUBTITLE = _t("\\u0422\\u043e\\u0432\\u0430 \\u0435 \\u0431\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d\\u0438\\u044f\\u0442 \\u0438\\u0437\\u0431\\u043e\\u0440 \\u043e\\u0442 \\u0444\\u0438\\u043d\\u0430\\u043b\\u043d\\u0438\\u044f \\u0441\\u0435\\u043b\\u0435\\u043a\\u0442\\u043e\\u0440. \\u0422\\u043e\\u0439 \\u043e\\u0431\\u0435\\u0434\\u0438\\u043d\\u044f\\u0432\\u0430 \\u043c\\u043e\\u0434\\u0435\\u043b\\u043d\\u0430 \\u0441\\u0438\\u043b\\u0430, \\u043a\\u0430\\u0447\\u0435\\u0441\\u0442\\u0432\\u043e, \\u043f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438\\u0435 \\u0438 \\u0440\\u0438\\u0441\\u043a \\u043e\\u0442 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442.")
SAFE_NOTE = _t("\\u0422\\u043e\\u0432\\u0430 \\u043d\\u0435 \\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f \\u0437\\u0430 \\u043f\\u0435\\u0447\\u0430\\u043b\\u0431\\u0430. \\u041f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430 \\u0441\\u0430\\u043c\\u043e \\u043d\\u0430\\u0439-\\u0434\\u043e\\u0431\\u0440\\u0438\\u044f \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u043a\\u043e\\u043c\\u043f\\u0440\\u043e\\u043c\\u0438\\u0441 \\u0441\\u043f\\u043e\\u0440\\u0435\\u0434 \\u043d\\u0430\\u043b\\u0438\\u0447\\u043d\\u0438\\u0442\\u0435 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438.")
BALANCED = _t("\\u0411\\u0430\\u043b\\u0430\\u043d\\u0441\\u0438\\u0440\\u0430\\u043d")
CONSERVATIVE = _t("\\u0417\\u0430\\u0449\\u0438\\u0442\\u0435\\u043d")
AGGRESSIVE = _t("\\u0410\\u0433\\u0440\\u0435\\u0441\\u0438\\u0432\\u0435\\u043d")
EMPTY_RISK = _t("\\u0420\\u0438\\u0441\\u043a \\u043e\\u0442 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d \\u043f\\u0430\\u043a\\u0435\\u0442")
UNIQUE = _t("\\u041f\\u043e\\u043a\\u0440\\u0438\\u0442\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430")
SCORE = _t("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430")
MODE = _t("\\u0420\\u0435\\u0436\\u0438\\u043c")
COMBINATION = _t("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f")
WHY = _t("\\u0417\\u0430\\u0449\\u043e \\u0442\\u043e\\u0437\\u0438 \\u0444\\u0438\\u0448 \\u0435 \\u0438\\u0437\\u0432\\u0435\\u0434\\u0435\\u043d \\u043d\\u0430\\u0439-\\u043e\\u0442\\u0433\\u043e\\u0440\\u0435?")
ALT_TITLE = _t("\\u0410\\u043b\\u0442\\u0435\\u0440\\u043d\\u0430\\u0442\\u0438\\u0432\\u043d\\u0438 \\u0440\\u0435\\u0436\\u0438\\u043c\\u0438")


def _load_model() -> dict[str, Any] | None:
    if not MODEL_PATH.exists():
        return None
    try:
        return json.loads(MODEL_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _format_float(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "0.00"


def _numbers_html(numbers: list[int]) -> str:
    balls = []
    for number in numbers:
        try:
            value = int(number)
        except (TypeError, ValueError):
            continue
        balls.append(f'<span class="v891-ball">{value}</span>')
    return '<div class="v891-ball-row">' + "".join(balls) + "</div>"


def _render_styles() -> None:
    st.markdown(
        "<style>\n"
        ".v891-card { border: 1px solid rgba(212, 175, 55, 0.34); background: radial-gradient(circle at top left, rgba(212, 175, 55, 0.12), rgba(18, 20, 27, 0.98) 45%); border-radius: 24px; padding: 1.35rem 1.45rem; margin: 0.4rem 0 1.2rem 0; box-shadow: 0 18px 44px rgba(0, 0, 0, 0.26); }\n"
        ".v891-title { font-size: 1.45rem; font-weight: 800; margin-bottom: 0.35rem; }\n"
        ".v891-subtitle { opacity: 0.86; line-height: 1.55; margin-bottom: 1rem; }\n"
        ".v891-badge { display: inline-flex; align-items: center; gap: 0.35rem; border: 1px solid rgba(212, 175, 55, 0.35); background: rgba(212, 175, 55, 0.10); color: #f4e2a2; border-radius: 999px; padding: 0.28rem 0.68rem; margin: 0 0.45rem 0.55rem 0; font-size: 0.88rem; font-weight: 700; }\n"
        ".v891-combo-label { font-weight: 800; margin: 0.78rem 0 0.38rem 0; opacity: 0.92; }\n"
        ".v891-ball-row { display: flex; flex-wrap: wrap; gap: 0.58rem; align-items: center; margin-bottom: 0.48rem; }\n"
        ".v891-ball { width: 3.05rem; height: 3.05rem; border-radius: 999px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; color: #0e0e10; background: radial-gradient(circle at 32% 28%, #fff2a6 0%, #f1d15a 35%, #c99a13 70%, #80610a 100%); border: 1px solid rgba(255, 241, 160, 0.76); box-shadow: inset 0 1px 6px rgba(255,255,255,.55), 0 8px 18px rgba(0,0,0,.35); }\n"
        ".v891-note { margin-top: 0.8rem; opacity: 0.78; font-size: 0.92rem; }\n"
        "</style>",
        unsafe_allow_html=True,
    )


def _get_recommendation(model: dict[str, Any], mode: str) -> dict[str, Any]:
    recommendations = model.get("recommendations", {})
    if isinstance(recommendations, dict):
        item = recommendations.get(mode)
        if isinstance(item, dict):
            return item
    if mode == "balanced":
        item = model.get("balanced_recommendation")
        if isinstance(item, dict):
            return item
    return {}


def _render_mode_summary(model: dict[str, Any]) -> None:
    recommendations = model.get("recommendations", {})
    if not isinstance(recommendations, dict):
        return

    with st.expander(ALT_TITLE):
        cols = st.columns(3)
        mode_data = [
            ("balanced", BALANCED),
            ("conservative", CONSERVATIVE),
            ("aggressive", AGGRESSIVE),
        ]
        for col, (mode_key, label) in zip(cols, mode_data):
            package = _get_recommendation(model, mode_key)
            with col:
                st.markdown(f"**{label}**")
                st.write(str(package.get("package_label", "-")))
                st.metric(SCORE, _format_float(package.get("mode_scores", {}).get(mode_key, 0.0), 1))
                st.caption(f"{UNIQUE}: {package.get('unique_covered_numbers', 0)}")


def render_v89_1_user_menu_final_selection() -> None:
    model = _load_model()
    if not model:
        return

    package = _get_recommendation(model, "balanced")
    if not package:
        return

    combinations = package.get("combinations", [])
    if not isinstance(combinations, list) or not combinations:
        return

    _render_styles()

    mode_score = package.get("mode_scores", {}).get("balanced", 0.0)
    risk = _format_float(package.get("empty_risk_percent", 0.0), 2)
    unique = package.get("unique_covered_numbers", 0)
    package_label = str(package.get("package_label", ""))

    st.markdown('<div class="v891-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="v891-title">{TITLE}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="v891-subtitle">{SUBTITLE}</div>', unsafe_allow_html=True)

    st.markdown(
        f'<span class="v891-badge">{MODE}: {BALANCED}</span>'
        f'<span class="v891-badge">{UNIQUE}: {unique}</span>'
        f'<span class="v891-badge">{EMPTY_RISK}: {risk}%</span>'
        f'<span class="v891-badge">{SCORE}: {_format_float(mode_score, 1)}</span>',
        unsafe_allow_html=True,
    )

    if package_label:
        st.caption(package_label)

    for index, combo in enumerate(combinations[:4], start=1):
        if not isinstance(combo, list):
            continue
        st.markdown(f'<div class="v891-combo-label">{COMBINATION} {index}</div>', unsafe_allow_html=True)
        st.markdown(_numbers_html(combo), unsafe_allow_html=True)

    st.markdown(f'<div class="v891-note">{SAFE_NOTE}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander(WHY):
        st.markdown(
            _t(
                "- \\u0422\\u043e\\u0437\\u0438 \\u0431\\u043b\\u043e\\u043a \\u0438\\u0434\\u0432\\u0430 \\u043e\\u0442 \\u0444\\u0438\\u043d\\u0430\\u043b\\u043d\\u0438\\u044f \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0438\\u0437\\u0431\\u043e\\u0440.\\n"
                "- \\u0422\\u043e\\u0439 \\u043d\\u0435 \\u043f\\u0440\\u043e\\u043c\\u0435\\u043d\\u044f \\u0447\\u0438\\u0441\\u043b\\u0430\\u0442\\u0430 \\u043d\\u0430 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438\\u0442\\u0435, \\u0430 \\u0438\\u0437\\u0431\\u0438\\u0440\\u0430 \\u043d\\u0430\\u0439-\\u0434\\u043e\\u0431\\u0440\\u0438\\u044f \\u043a\\u043e\\u043c\\u043f\\u0440\\u043e\\u043c\\u0438\\u0441 \\u043c\\u0435\\u0436\\u0434\\u0443 \\u043d\\u0430\\u043b\\u0438\\u0447\\u043d\\u0438\\u0442\\u0435 \\u043f\\u0430\\u043a\\u0435\\u0442\\u0438.\\n"
                "- \\u041e\\u0441\\u0442\\u0430\\u043d\\u0430\\u043b\\u0438\\u0442\\u0435 \\u0444\\u0438\\u0448\\u043e\\u0432\\u0435 \\u043e\\u0441\\u0442\\u0430\\u0432\\u0430\\u0442 \\u043f\\u043e-\\u043d\\u0430\\u0434\\u043e\\u043b\\u0443 \\u043a\\u0430\\u0442\\u043e \\u0430\\u043b\\u0442\\u0435\\u0440\\u043d\\u0430\\u0442\\u0438\\u0432\\u0438."
            )
        )

    _render_mode_summary(model)

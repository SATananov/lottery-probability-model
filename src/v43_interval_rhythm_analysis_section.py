
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
PREDICTION_PATH = ROOT / "models" / "v43_1" / "v43_1_interval_rhythm_refined_prediction.json"
SCORES_PATH = ROOT / "models" / "v43_1" / "v43_1_interval_rhythm_refined_scores.json"
SUMMARY_PATH = ROOT / "reports" / "v43_1_interval_rhythm_refined_summary.json"


def _bg(hex_text: str) -> str:
    return bytes.fromhex(hex_text).decode("utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        st.error(_bg("d09fd18ad182d18fd18220d0bad18ad0bc20d184d0b0d0b9d0bbd0b020d0bbd0b8d0bfd181d0b2d0b03a") + f" {path}")
        return {}

    return json.loads(path.read_text(encoding="utf-8-sig"))


def _format_score(value: Any) -> str:
    if value is None or value == "":
        return "-"

    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)


def _format_probability(value: Any) -> str:
    if value is None or value == "":
        return "-"

    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return str(value)


def _status_label(status: Any) -> str:
    labels = {
        "late": _bg("d0b7d0b0d0bad18ad181d0bdd18fd0b2d0b0"),
        "watch_zone": _bg("d0b7d0bed0bdd0b020d0b7d0b020d0bdd0b0d0b1d0bbd18ed0b4d0b5d0bdd0b8d0b5"),
        "normal": _bg("d0bdd0bed180d0bcd0b0d0bbd0bdd0be"),
        "early": _bg("d180d0b0d0bdd0be"),
        "beyond_historical_gap": _bg("d0b8d0b7d0b2d18ad0bd20d0b8d181d182d0bed180d0b8d187d0b5d181d0bad0b020d0bfd0b0d183d0b7d0b0"),
        "insufficient_history": _bg("d0bdd0b5d0b4d0bed181d182d0b0d182d18ad187d0bdd0b020d0b8d181d182d0bed180d0b8d18f"),
    }

    return labels.get(str(status), str(status))


def _render_number_cards(numbers: list[int]) -> None:
    if not numbers:
        st.warning(_bg("d09dd18fd0bcd0b020d0bdd0b0d0bbd0b8d187d0bdd0b820d0b4d0b0d0bdd0bdd0b820d0b7d0b020d180d0b8d182d18ad0bc20d0b0d0bdd0b0d0bbd0b8d0b7d0b02e"))
        return

    columns = st.columns(6)

    for column, number in zip(columns, numbers):
        column.metric(_bg("d0a7d0b8d181d0bbd0be"), number)


def _score_table(rows: list[dict[str, Any]], limit: int | None = 12) -> None:
    if not rows:
        st.warning(_bg("d09dd18fd0bcd0b020d0bdd0b0d0bbd0b8d187d0bdd0b820d0b4d0b0d0bdd0bdd0b820d0b7d0b020d180d0b8d182d18ad0bc20d0b0d0bdd0b0d0bbd0b8d0b7d0b02e"))
        return

    selected_rows = rows if limit is None else rows[:limit]
    display_rows = []

    for row in selected_rows:
        display_rows.append(
            {
                _bg("d0a7d0b8d181d0bbd0be"): row.get("number"),
                _bg("d184d0b8d0bdd0b0d0bbd0b5d0bd20d180d0b5d0b7d183d0bbd182d0b0d182"): _format_score(row.get("final_rhythm_score")),
                _bg("d181d0bbd0b5d0b4d0b2d0b0d18920d0bfd180d0bed0b7d0bed180d0b5d186"): _format_score(row.get("next_window_score")),
                _bg("d0b1d0b0d0bbd0b0d0bdd181d0b8d180d0b0d0bd20d180d0b8d182d18ad0bc"): _format_score(row.get("balanced_rhythm_score")),
                _bg("d0b7d0b0d0bad18ad181d0bdd0b5d0bdd0b8d0b5"): _format_score(row.get("overdue_score")),
                _bg("d0bfd0b0d183d0b7d0b0"): row.get("current_gap"),
                _bg("d0bcd0b5d0b4d0b8d0b0d0bdd0b0"): row.get("median_interval"),
                _bg("d181d180d0b5d0b4d0b5d0bd20d0b8d0bdd182d0b5d180d0b2d0b0d0bb"): row.get("average_interval"),
                _bg("d0b2d0b5d180d0bed18fd182d0bdd0bed181d18220d0b4d0be203520d182d0b8d180d0b0d0b6d0b0"): _format_probability(row.get("probability_next_5_draws")),
                _bg("d181d182d0b0d182d183d181"): _status_label(row.get("rhythm_status")),
            }
        )

    st.dataframe(pd.DataFrame(display_rows), hide_index=True, use_container_width=True)


def render_interval_rhythm_analysis() -> None:
    prediction = _load_json(PREDICTION_PATH)
    scores = _load_json(SCORES_PATH)
    summary = _load_json(SUMMARY_PATH)

    if not prediction or not scores or not summary:
        return

    final_numbers = prediction.get("final_refined_rhythm_numbers", [])
    next_window_numbers = prediction.get("next_window_numbers", [])
    overdue_numbers = prediction.get("overdue_watchlist_numbers", [])
    balanced_numbers = prediction.get("balanced_rhythm_numbers", [])

    st.title(_bg("d090d0bdd0b0d0bbd0b8d0b720d0bfd0be20d180d0b8d182d18ad0bc20d0bdd0b020d0bfd0bed18fd0b2d18fd0b2d0b0d0bdd0b5"))
    st.caption(
        _bg("d0a1d182d0b0d182d0b8d181d182d0b8d187d0b5d181d0bad0b820d0b0d0bdd0b0d0bbd0b8d0b720d0bdd0b020d0b8d181d182d0bed180d0b8d187d0b5d181d0bad0b8d182d0b520d0b8d0bdd182d0b5d180d0b2d0b0d0bbd0b820d0bcd0b5d0b6d0b4d18320d0bfd0bed18fd0b2d18fd0b2d0b0d0bdd0b8d18fd182d0b020d0bdd0b020d187d0b8d181d0bbd0b0d182d0b02e20d0a2d0bed0b2d0b020d0bdd0b520d0b520d0bfd180d0bed0b3d0bdd0bed0b7d0b020d0b8d0bbd0b820d0b3d0b0d180d0b0d0bdd186d0b8d18f20d0b7d0b020d0bfd0b5d187d0b0d0bbd0b1d0b02e")
    )

    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
    metric_col_1.metric(_bg("d092d0b0d0bbd0b8d0b4d0bdd0b820d182d0b8d180d0b0d0b6d0b8"), prediction.get("valid_draws", "-"))
    metric_col_2.metric(_bg("426f6e757320d187d0b8d181d0bbd0be"), _bg("d0bdd0b520d181d0b520d0b8d0b7d0bfd0bed0bbd0b7d0b2d0b0"))
    metric_col_3.metric(_bg("d0a7d0b8d181d0bbd0be"), len(scores.get("numbers", [])))

    st.subheader(_bg("d09ed181d0bdd0bed0b2d0bdd0be20d0bfd180d0b5d0b4d0bbd0bed0b6d0b5d0bdd0b8d0b5"))
    st.markdown("### " + _bg("d0a4d0b8d0bdd0b0d0bbd0bdd0be20d0bfd180d0b5d0b4d0bbd0bed0b6d0b5d0bdd0b8d0b520d181d0bfd0bed180d0b5d0b420d180d0b8d182d18ad0bcd0b0"))
    _render_number_cards([int(number) for number in final_numbers])

    st.info(
        _bg("d09fd0bed0bad0b0d0b7d0b2d0b020d0bad0bed0b820d187d0b8d181d0bbd0b020d181d0b020d0b8d0bdd182d0b5d180d0b5d181d0bdd0b820d181d0bfd0bed180d0b5d0b420d0b8d181d182d0bed180d0b8d187d0b5d181d0bad0b8d18f20d0b8d0bdd182d0b5d180d0b2d0b0d0bb20d0bcd0b5d0b6d0b4d18320d0bfd0bed18fd0b2d18fd0b2d0b2d0b0d0bdd0b8d18fd182d0b020d0b8d0bc2e")
    )

    st.warning(
        _bg("d09bd0bed182d0b0d180d0b8d0b9d0bdd0b8d182d0b520d182d0b5d0b3d0bbd0b5d0bdd0b8d18f20d181d0b020d181d0bbd183d187d0b0d0b9d0bdd0b82e20d0a2d0bed0b7d0b820d0b0d0bdd0b0d0bbd0b8d0b720d0bfd0bed0bad0b0d0b7d0b2d0b020d0b8d181d182d0bed180d0b8d187d0b5d181d0bad0b820d180d0b8d182d18ad0bc2c20d0bdd0b520d0bed0b1d0b5d189d0b0d0b2d0b020d0bfd0b5d187d0b0d0bbd0b1d0b02e")
    )

    tabs = st.tabs(
        [
            _bg("d0a4d0b8d0bdd0b0d0bbd0b5d0bd20d180d0b8d182d18ad0bc"),
            _bg("d0a1d0bbd0b5d0b4d0b2d0b0d18920d0bfd180d0bed0b7d0bed180d0b5d186"),
            _bg("d097d0b0d0bad18ad181d0bdd0b5d0bbd0b820d187d0b8d181d0bbd0b0"),
            _bg("d091d0b0d0bbd0b0d0bdd181d0b8d180d0b0d0bd20d180d0b8d182d18ad0bc"),
            _bg("d092d181d0b8d187d0bad0b820d187d0b8d181d0bbd0b0"),
            _bg("d09ad0b0d0ba20d0b4d0b020d181d0b520d187d0b5d182d0b5"),
        ]
    )

    with tabs[0]:
        st.subheader(_bg("d09dd0b0d0b92dd181d0b8d0bbd0bdd0b820d181d0bfd0bed180d0b5d0b420d184d0b8d0bdd0b0d0bbd0bdd0b8d18f20d180d0b8d182d18ad0bc"))
        _render_number_cards([int(number) for number in final_numbers])
        _score_table(summary.get("top_final_numbers", []), limit=12)

    with tabs[1]:
        st.subheader(_bg("d0a1d0bbd0b5d0b4d0b2d0b0d18920d0bfd180d0bed0b7d0bed180d0b5d1863a20d187d0b8d181d0bbd0b020d181d18ad18120d181d0b8d0b3d0bdd0b0d0bb20d0b7d0b020d181d0bbd0b5d0b4d0b2d0b0d189d0b8d182d0b52033e280933520d182d0b8d180d0b0d0b6d0b0"))
        _render_number_cards([int(number) for number in next_window_numbers])
        _score_table(summary.get("top_next_window_numbers", []), limit=12)

    with tabs[2]:
        st.subheader(_bg("d097d0b0d0bad18ad181d0bdd0b5d0bbd0b820d181d0bfd180d18fd0bcd0be20d181d0bed0b1d181d182d0b2d0b5d0bdd0b8d18f20d181d0b820d180d0b8d182d18ad0bc"))
        _render_number_cards([int(number) for number in overdue_numbers])
        _score_table(summary.get("top_overdue_numbers", []), limit=12)

    with tabs[3]:
        st.subheader(_bg("d0a7d0b8d181d0bbd0b020d0b1d0bbd0b8d0b7d0be20d0b4d0be20d0bdd0bed180d0bcd0b0d0bbd0bdd0b8d18f20d181d0b820d0b8d181d182d0bed180d0b8d187d0b5d181d0bad0b820d180d0b8d182d18ad0bc"))
        _render_number_cards([int(number) for number in balanced_numbers])
        _score_table(summary.get("top_balanced_numbers", []), limit=12)

    with tabs[4]:
        st.subheader(_bg("d09fd0bed0b4d180d0bed0b1d0bdd0b020d182d0b0d0b1d0bbd0b8d186d0b020d0b7d0b020343920d187d0b8d181d0bbd0b0"))
        _score_table(scores.get("numbers", []), limit=None)

    with tabs[5]:
        st.markdown("- " + _bg("63757272656e745f67617020d0bfd0bed0bad0b0d0b7d0b2d0b020d0bad0bed0bbd0bad0be20d182d0b8d180d0b0d0b6d0b020d181d0b020d0bcd0b8d0bdd0b0d0bbd0b820d0bed18220d0bfd0bed181d0bbd0b5d0b4d0bdd0bed182d0be20d0bfd0bed18fd0b2d18fd0b2d0b0d0bdd0b52e"))
        st.markdown("- " + _bg("6d656469616e5f696e74657276616c20d0bfd0bed0bad0b0d0b7d0b2d0b020d182d0b8d0bfd0b8d187d0bdd0b8d18f20d0b8d181d182d0bed180d0b8d187d0b5d181d0bad0b820d0b8d0bdd182d0b5d180d0b2d0b0d0bb2e"))
        st.markdown("- " + _bg("6e6578745f77696e646f775f73636f726520d182d18ad180d181d0b820d187d0b8d181d0bbd0b020d18120d0bfd0be2dd181d0b8d0bbd0b5d0bd20d181d0b8d0b3d0bdd0b0d0bb20d0b7d0b020d181d0bbd0b5d0b4d0b2d0b0d189d0b8d182d0b520d0bdd18fd0bad0bed0bbd0bad0be20d182d0b8d180d0b0d0b6d0b02e"))
        st.markdown("- " + _bg("6f7665726475655f73636f726520d0bfd0bed0bad0b0d0b7d0b2d0b020d187d0b8d181d0bbd0b02c20d0bad0bed0b8d182d0be20d181d0b020d0b7d0b0d0bad18ad181d0bdd0b5d0bbd0b820d181d0bfd180d18fd0bcd0be20d181d0bed0b1d181d182d0b2d0b5d0bdd0b8d18f20d181d0b820d180d0b8d182d18ad0bc2e"))
        st.markdown("- " + _bg("d092d181d0b8d187d0bad0be20d182d0bed0b2d0b020d0b520d181d182d0b0d182d0b8d181d182d0b8d187d0b5d181d0bad0b820d0bed180d0b8d0b5d0bdd182d0b8d1802c20d0bdd0b520d181d0b8d0b3d183d180d0bdd0b020d0bfd180d0bed0b3d0bdd0bed0b7d0b02e"))

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None


ROOT = Path(__file__).resolve().parents[1]
TICKET_PATH = ROOT / "models" / "v44_1" / "v44_1_final_ensemble_ticket_prediction.json"
SCORES_PATH = ROOT / "models" / "v44_1" / "v44_1_final_ensemble_number_scores.json"


def _bg(hex_text: str) -> str:
    return bytes.fromhex(hex_text).decode("utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    return json.loads(path.read_text(encoding="utf-8-sig"))


def _format_numbers(numbers: list[int]) -> str:
    return "   ".join(f"{int(number):02d}" for number in numbers)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _score(value: Any) -> str:
    return f"{_safe_float(value):.2f}"


def _combo_reason(label: str) -> str:
    reasons = {
        "final_consensus": "\u041e\u0431\u0449 \u043a\u043e\u043d\u0441\u0435\u043d\u0441\u0443\u0441",
        "interval_rhythm_next_window": "\u0420\u0438\u0442\u044a\u043c \u0438 \u0441\u043b\u0435\u0434\u0432\u0430\u0449 \u043f\u0440\u043e\u0437\u043e\u0440\u0435\u0446",
        "combined_positive_negative": "\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u0441\u0438\u0433\u043d\u0430\u043b",
        "coverage_diversified": "\u041f\u043e\u043a\u0440\u0438\u0442\u0438\u0435 \u043d\u0430 \u0444\u0438\u0448\u0430",
    }

    return reasons.get(label, str(label))


def _combo_table_rows(combo: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []

    for row in combo.get("number_details", []):
        rows.append(
            {
                "\u0427\u0438\u0441\u043b\u043e": int(row.get("number", 0)),
                "\u0424\u0438\u043d\u0430\u043b\u0435\u043d \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442": _score(row.get("final_ensemble_score")),
                "\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u0441\u0438\u0433\u043d\u0430\u043b": _score(row.get("v42_combined_score")),
                "\u0420\u0438\u0442\u044a\u043c": _score(row.get("rhythm_final_score")),
                "\u0421\u043b\u0435\u0434\u0432\u0430\u0449 \u043f\u0440\u043e\u0437\u043e\u0440\u0435\u0446": _score(row.get("rhythm_next_window_score")),
                "\u0418\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0441\u0438\u0433\u043d\u0430\u043b": _score(row.get("rules_score")),
                "\u041a\u043e\u043d\u0441\u0435\u043d\u0441\u0443\u0441": int(row.get("consensus_hits", 0)),
                "\u041f\u0430\u0443\u0437\u0430": int(row.get("current_gap", 0)),
                "\u041e\u0431\u0449\u043e \u043f\u043e\u044f\u0432\u0438": int(row.get("total_hits", 0)),
            }
        )

    return rows


def _top_table_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []

    for row in rows[:20]:
        output.append(
            {
                "\u0427\u0438\u0441\u043b\u043e": int(row.get("number", 0)),
                "\u0424\u0438\u043d\u0430\u043b\u0435\u043d \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442": _score(row.get("final_ensemble_score")),
                "\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u0441\u0438\u0433\u043d\u0430\u043b": _score(row.get("v42_combined_score")),
                "\u0420\u0438\u0442\u044a\u043c": _score(row.get("rhythm_final_score")),
                "\u0421\u043b\u0435\u0434\u0432\u0430\u0449 \u043f\u0440\u043e\u0437\u043e\u0440\u0435\u0446": _score(row.get("rhythm_next_window_score")),
                "\u0418\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0441\u0438\u0433\u043d\u0430\u043b": _score(row.get("rules_score")),
                "\u041a\u043e\u043d\u0441\u0435\u043d\u0441\u0443\u0441": int(row.get("consensus_hits", 0)),
                "\u0422\u0435\u043a\u0443\u0449\u0430 \u043f\u0430\u0443\u0437\u0430": int(row.get("current_gap", 0)),
            }
        )

    return output


def _show_table(rows: list[dict[str, Any]]) -> None:
    if not rows:
        st.info(_bg("d09dd18fd0bcd0b020d0b4d0b0d0bdd0bdd0b820d0b7d0b020d0bad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d0b82e"))
        return

    if pd is None:
        st.dataframe(rows, width="stretch")
        return

    df = pd.DataFrame(rows)

    try:
        st.dataframe(df, width="stretch", hide_index=True)
    except TypeError:
        st.dataframe(df, width="stretch")


def render() -> None:
    ticket = _load_json(TICKET_PATH)
    scores = _load_json(SCORES_PATH)

    st.title(_bg("d0a4d0b8d0bdd0b0d0bbd0b5d0bd20d0bed0b1d0bed0b1d189d0b5d0bd20d0b0d0bdd0b0d0bbd0b8d0b7"))

    if not ticket or not scores:
        st.error(_bg("d0a4d0b0d0b9d0bbd0bed0b2d0b5d182d0b520d0b7d0b020d184d0b8d0bdd0b0d0bbd0bdd0b8d18f20d0b0d0bdd0b0d0bbd0b8d0b720d0bdd0b520d181d0b020d0bdd0b0d0bcd0b5d180d0b5d0bdd0b82e20d09fd18ad180d0b2d0be20d181d182d0b0d180d182d0b8d180d0b0d0b920666f756e646174696f6e20d0bcd0bed0b4d0b5d0bbd0b02e"))
        return

    combinations = ticket.get("ticket_combinations", [])

    st.caption(
        _bg("d0a2d0bed0b2d0b020d0b520d0bed0b1d0b5d0b4d0b8d0bdd0b5d0bd20d181d182d0b0d182d0b8d181d182d0b8d187d0b5d181d0bad0b820d0b0d0bdd0b0d0bbd0b8d0b72c20d0bad0bed0b9d182d0be20d181d18ad0b1d0b8d180d0b020d181d0b8d0b3d0bdd0b0d0bbd0b8d182d0b520d0bed18220d0b8d181d182d0bed180d0b8d187d0b5d181d0bad0b8d18f20d181d0bbd0bed0b92c20d0bad0bed0bcd0b1d0b8d0bdd0b8d180d0b0d0bdd0b8d18f20706f7369746976652f6e6567617469766520d0b0d0bdd0b0d0bbd0b8d0b720d0b820d0b0d0bdd0b0d0bbd0b8d0b7d0b020d0bfd0be20d180d0b8d182d18ad0bc20d0bdd0b020d0bfd0bed18fd0b2d18fd0b2d0b0d0bdd0b52e")
    )

    st.warning(
        _bg("d092d0b0d0b6d0bdd0be3a20d182d0bed0b2d0b020d0bdd0b520d0b520d0b3d0b0d180d0b0d0bdd186d0b8d18f20d0b7d0b020d0bfd0b5d187d0b0d0bbd0b1d0b02e20d0a2d0b5d0b3d0bbd0b5d0bdd0b8d18fd182d0b020d181d0b020d181d0bbd183d187d0b0d0b9d0bdd0b82c20d0b020d180d0b5d0b7d183d0bbd182d0b0d182d18ad18220d0b520d181d182d0b0d182d0b8d181d182d0b8d187d0b5d181d0bad0be20d0bfd180d0b5d0b4d0bbd0bed0b6d0b5d0bdd0b8d0b52e")
    )

    metrics = st.columns(3)
    metrics[0].metric(_bg("d092d0b0d0bbd0b8d0b4d0bdd0b820d182d0b8d180d0b0d0b6d0b8"), str(ticket.get("valid_draws", "-")))
    metrics[1].metric(_bg("d091d0bed0bdd183d18120d187d0b8d181d0bbd0be"), _bg("d09dd0b520d181d0b520d0b8d0b7d0bfd0bed0bbd0b7d0b2d0b0"))
    metrics[2].metric(_bg("d091d180d0bed0b920d0bad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d0b8"), str(len(combinations)))

    st.markdown("---")
    st.subheader(_bg("d09fd0a0d095d094d09bd09ed096d095d09dd098d09520d097d09020d0a7d098d0a1d09bd090"))
    st.caption(_bg("d09ad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d0b8d182d0b520d181d0b020d181d182d0b0d182d0b8d181d182d0b8d187d0b5d181d0bad0be20d0bfd180d0b5d0b4d0bbd0bed0b6d0b5d0bdd0b8d0b520d0b7d0b020d0bfd0bed0bfd18ad0bbd0b2d0b0d0bdd0b520d0bdd0b020d186d18fd0bb20d184d0b8d188203420c397203620d187d0b8d181d0bbd0b02e"))

    if not combinations:
        st.info(_bg("d09dd18fd0bcd0b020d0b4d0b0d0bdd0bdd0b820d0b7d0b020d0bad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d0b82e"))
        return

    for index, combo in enumerate(combinations, start=1):
        numbers = [int(number) for number in combo.get("numbers", [])]

        st.markdown(f"### {_bg('d09ad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d18f')} {index}")
        st.markdown(f"## `{_format_numbers(numbers)}`")
        st.caption(f"{_bg('d09fd180d0b8d187d0b8d0bdd0b0')}: {_combo_reason(str(combo.get('label', '')))}")

        score_cols = st.columns(5)
        score_cols[0].metric("\u0424\u0438\u043d\u0430\u043b\u0435\u043d \u0441\u0440\u0435\u0434\u0435\u043d \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442", _score(combo.get("average_final_ensemble_score")))
        score_cols[1].metric("\u0421\u0440\u0435\u0434\u0435\u043d \u0440\u0438\u0442\u044a\u043c", _score(combo.get("average_rhythm_score")))
        score_cols[2].metric("\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u0441\u0438\u0433\u043d\u0430\u043b", _score(combo.get("average_combined_score")))
        score_cols[3].metric("\u0418\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0441\u0438\u0433\u043d\u0430\u043b", _score(combo.get("average_rules_score")))
        score_cols[4].metric("\u0421\u0440\u0435\u0434\u0435\u043d \u043a\u043e\u043d\u0441\u0435\u043d\u0441\u0443\u0441", _score(combo.get("average_consensus_score")))
        with st.expander(_bg("d094d0b5d182d0b0d0b9d0bbd0b820d0b7d0b020d187d0b8d181d0bbd0b0d182d0b0")):
            _show_table(_combo_table_rows(combo))

        st.markdown("---")

    st.subheader(_bg("d09fd180d0bed0b2d0b5d180d0bad0b020d0bdd0b020d0bed0b3d180d0b0d0bdd0b8d187d0b5d0bdd0b8d18fd182d0b0"))

    check_rows = [
        {
            _bg("d09cd0b5d182d0bed0b4"): _bg("d0a7d0b8d181d0bbd0be20d0bcd0b0d0bad181d0b8d0bcd183d0bc20d0b4d0b2d0b020d0bfd18ad182d0b8"),
            _bg("d0a0d0b5d0b7d183d0bbd182d0b0d182"): _bg("d098d0b7d0bfd18ad0bbd0bdd0b5d0bdd0be"),
        },
        {
            _bg("d09cd0b5d182d0bed0b4"): _bg("d09cd0b0d0bad181d0b8d0bcd183d0bc20d0b4d0b2d0b520d0bed0b1d189d0b820d187d0b8d181d0bbd0b020d0bcd0b5d0b6d0b4d18320d0b4d0b2d0b520d0bad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d0b8"),
            _bg("d0a0d0b5d0b7d183d0bbd182d0b0d182"): _bg("d098d0b7d0bfd18ad0bbd0bdd0b5d0bdd0be"),
        },
    ]

    _show_table(check_rows)

    st.subheader(_bg("d0a2d0bed0bf20d187d0b8d181d0bbd0b020d0bfd0be20d184d0b8d0bdd0b0d0bbd0b5d0bd20d180d0b5d0b7d183d0bbd182d0b0d182"))
    _show_table(_top_table_rows(ticket.get("top_ensemble_numbers", [])))

    with st.expander(_bg("d09ad0b0d0ba20d0b4d0b020d181d0b520d187d0b5d182d0b5")):
        st.write(_bg("d0a2d0bed0b7d0b820d0b5d0bad180d0b0d0bd20d0bdd0b520d0b8d0b7d0b1d0b8d180d0b020d187d0b8d181d0bbd0b020d0bdd0b020d181d0bbd183d187d0b0d0b5d0bd20d0bfd180d0b8d0bdd186d0b8d0bf2e20d0a2d0bed0b920d0bed0b1d0bed0b1d189d0b0d0b2d0b020d0b2d0b5d187d0b520d181d18ad0b7d0b4d0b0d0b4d0b5d0bdd0b8d182d0b520d0bcd0bed0b4d0b5d0bbd0b820d0b820d0bfd0bed0b4d0bcd0bed0b4d0b5d0bbd0b82e"))
        st.write(_bg("d09fd18ad180d0b2d0b0d182d0b020d0bad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d18f20d0b520d0bdd0b0d0b92dd181d0b8d0bbd0b5d0bd20d0bed0b1d18920d0bad0bed0bdd181d0b5d0bdd181d183d1812e20d092d182d0bed180d0b0d182d0b020d0b3d0bbd0b5d0b4d0b020d0bfd0bed0b2d0b5d187d0b520d180d0b8d182d18ad0bc20d0b820d181d0bbd0b5d0b4d0b2d0b0d18920d0bfd180d0bed0b7d0bed180d0b5d1862e20d0a2d180d0b5d182d0b0d182d0b020d0b3d0bbd0b5d0b4d0b020d0bad0bed0bcd0b1d0b8d0bdd0b8d180d0b0d0bdd0b8d18f20706f7369746976652f6e6567617469766520d181d0bbd0bed0b92e20d0a7d0b5d182d0b2d18ad180d182d0b0d182d0b020d182d18ad180d181d0b820d0bfd0be2dd0b4d0bed0b1d180d0be20d0bfd0bed0bad180d0b8d182d0b8d0b520d0b820d180d0b0d0b7d0bdd0bed0bed0b1d180d0b0d0b7d18fd0b2d0b0d0bdd0b520d0bdd0b020d184d0b8d188d0b02e"))
        st.write(_bg("d09ed0b3d180d0b0d0bdd0b8d187d0b5d0bdd0b8d18fd182d0b020d0bfd0b0d0b7d18fd18220d184d0b8d188d0b020d0bed18220d0bfd180d0b5d0bad0b0d0bbd0b5d0bdd0be20d0bfd0bed0b2d182d0bed180d0b5d0bdd0b8d0b53a20d187d0b8d181d0bbd0be20d0bcd0b0d0bad181d0b8d0bcd183d0bc20d0b4d0b2d0b020d0bfd18ad182d0b820d0b820d0bcd0b0d0bad181d0b8d0bcd183d0bc20d0b4d0b2d0b520d0bed0b1d189d0b820d187d0b8d181d0bbd0b020d0bcd0b5d0b6d0b4d18320d0b4d0b2d0b520d0bad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d0b82e"))

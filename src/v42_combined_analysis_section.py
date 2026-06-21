from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
PREDICTION_PATH = ROOT / "models" / "v42" / "v42_combined_prediction.json"
SCORES_PATH = ROOT / "models" / "v42" / "v42_positive_negative_number_scores.json"
SUMMARY_PATH = ROOT / "reports" / "v42_combined_positive_negative_summary.json"


def _bg(hex_text: str) -> str:
    return bytes.fromhex(hex_text).decode("utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _format_score(value: Any) -> str:
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "-"


def _risk_label(value: Any) -> str:
    labels = {
        "very_low": _bg("d09cd0bdd0bed0b3d0be20d0bdd0b8d181d18ad0ba20d180d0b8d181d0ba"),
        "low": _bg("d09dd0b8d181d18ad0ba20d180d0b8d181d0ba"),
        "medium": _bg("d0a1d180d0b5d0b4d0b5d0bd20d180d0b8d181d0ba"),
        "high": _bg("d092d0b8d181d0bed0ba20d180d0b8d181d0ba"),
        "very_high": _bg("d09cd0bdd0bed0b3d0be20d0b2d0b8d181d0bed0ba20d180d0b8d181d0ba"),
    }
    return labels.get(str(value), str(value))


def _numbers_line(numbers: list[int]) -> str:
    return " - ".join(str(number) for number in numbers)


def _details_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    display_rows = []

    for row in rows:
        display_rows.append(
            {
                _bg("d0a7d0b8d181d0bbd0be"): row.get("number"),
                _bg("d09fd0bed0bbd0bed0b6d0b8d182d0b5d0bbd0b5d0bd20d181d0b8d0b3d0bdd0b0d0bb"): _format_score(row.get("positive_signal_score")),
                _bg("d0a0d0b8d181d0ba20d0bed18220d0bed182d181d18ad181d182d0b2d0b8d0b5"): _format_score(row.get("absence_risk_score")),
                _bg("d09ad0bed0bcd0b1d0b8d0bdd0b8d180d0b0d0bd20d180d0b5d0b7d183d0bbd182d0b0d182"): _format_score(row.get("combined_score")),
                _bg("d09fd0b0d183d0b7d0b0"): row.get("current_absence_gap"),
                _bg("d09ed0b1d189d0be20d0bfd0b0d0b4d0b0d0bdd0b8d18f"): row.get("total_hits"),
            }
        )

    return pd.DataFrame(display_rows)


def _risk_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    display_rows = []

    for row in rows:
        display_rows.append(
            {
                _bg("d0a7d0b8d181d0bbd0be"): row.get("number"),
                _bg("d0a0d0b8d181d0ba20d0bed18220d0bed182d181d18ad181d182d0b2d0b8d0b5"): _format_score(row.get("absence_risk_score")),
                _bg("d09dd0b8d0b2d0be20d0bdd0b020d180d0b8d181d0ba"): _risk_label(row.get("absence_risk_level")),
                _bg("d09fd0b0d183d0b7d0b0"): row.get("current_absence_gap"),
                "Max gap": row.get("max_absence_gap"),
                _bg("d09ed0b1d189d0be20d0bfd0b0d0b4d0b0d0bdd0b8d18f"): row.get("total_hits"),
            }
        )

    return pd.DataFrame(display_rows)


def _combined_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return _details_dataframe(rows)



# USER_COMBINATION_CHECKER_HELPERS_START
def _number_scores_map(scores_payload: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rows = scores_payload.get("numbers", [])
    result: dict[int, dict[str, Any]] = {}

    for row in rows:
        try:
            number = int(row.get("number"))
        except Exception:
            continue

        if 1 <= number <= 49:
            result[number] = row

    return result


def _evaluate_user_combination(numbers: list[int], score_map: dict[int, dict[str, Any]]) -> dict[str, Any]:
    selected_rows = [score_map[number] for number in numbers if number in score_map]

    if not selected_rows:
        return {
            "average_positive": 0.0,
            "average_risk": 0.0,
            "average_combined": 0.0,
            "strongest": [],
            "highest_risk": [],
            "details": [],
        }

    average_positive = sum(float(row.get("positive_signal_score", 0)) for row in selected_rows) / len(selected_rows)
    average_risk = sum(float(row.get("absence_risk_score", 0)) for row in selected_rows) / len(selected_rows)
    average_combined = sum(float(row.get("combined_score", 0)) for row in selected_rows) / len(selected_rows)

    strongest = sorted(
        selected_rows,
        key=lambda row: float(row.get("combined_score", 0)),
        reverse=True,
    )[:3]

    highest_risk = sorted(
        selected_rows,
        key=lambda row: float(row.get("absence_risk_score", 0)),
        reverse=True,
    )[:3]

    return {
        "average_positive": average_positive,
        "average_risk": average_risk,
        "average_combined": average_combined,
        "strongest": strongest,
        "highest_risk": highest_risk,
        "details": selected_rows,
    }


def _combination_details_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    display_rows = []

    for row in sorted(rows, key=lambda item: int(item.get("number", 0))):
        display_rows.append(
            {
                _bg("d0a7d0b8d181d0bbd0be"): row.get("number"),
                _bg("d09fd0bed0bbd0bed0b6d0b8d182d0b5d0bbd0b5d0bd20d181d0b8d0b3d0bdd0b0d0bb"): _format_score(row.get("positive_signal_score")),
                _bg("d0a0d0b8d181d0ba20d0bed18220d0bed182d181d18ad181d182d0b2d0b8d0b5"): _format_score(row.get("absence_risk_score")),
                _bg("d09ad0bed0bcd0b1d0b8d0bdd0b8d180d0b0d0bd20d180d0b5d0b7d183d0bbd182d0b0d182"): _format_score(row.get("combined_score")),
                _bg("d09fd0b0d183d0b7d0b0"): row.get("current_absence_gap"),
                _bg("d09ed0b1d189d0be20d0bfd0b0d0b4d0b0d0bdd0b8d18f"): row.get("total_hits"),
            }
        )

    return pd.DataFrame(display_rows)
# USER_COMBINATION_CHECKER_HELPERS_END


def render_v42_combined_analysis() -> None:
    st.title(_bg("d09ad0bed0bcd0b1d0b8d0bdd0b8d180d0b0d0bd20d0b0d0bdd0b0d0bbd0b8d0b7"))

    st.caption(_bg("d09fd0bed0bbd0bed0b6d0b8d182d0b5d0bbd0b5d0bd202b20d0bed182d180d0b8d186d0b0d182d0b5d0bbd0b5d0bd20d0bcd0bed0b4d0b5d0bb"))

    st.info(
        _bg("d0a2d0b0d0b7d0b820d181d0b5d0bad186d0b8d18f20d0bad0bed0bcd0b1d0b8d0bdd0b8d180d0b020d0bfd0bed0bbd0bed0b6d0b8d182d0b5d0bbd0b5d0bd20d181d0b8d0b3d0bdd0b0d0bb20d18120d180d0b8d181d0ba20d0bed18220d0bed182d181d18ad181d182d0b2d0b8d0b52e20d0a2d0bed0b2d0b020d0b520d181d182d0b0d182d0b8d181d182d0b8d187d0b5d181d0bad0b820d0b0d0bdd0b0d0bbd0b8d0b72c20d0bdd0b520d0b3d0b0d180d0b0d0bdd186d0b8d18f20d0b7d0b020d0bfd0b5d187d0b0d0bbd0b1d0b02e")
    )

    missing_paths = [
        path
        for path in [PREDICTION_PATH, SCORES_PATH, SUMMARY_PATH]
        if not path.exists()
    ]

    if missing_paths:
        st.error(_bg("d0a4d0b0d0b9d0bbd0bed0b2d0b5d182d0b520d0bdd0b02076343220d0bdd0b520d181d0b020d0bdd0b0d0bcd0b5d180d0b5d0bdd0b82e20d09fd18ad180d0b2d0be20d181d182d0b0d180d182d0b8d180d0b0d0b92076343220666f756e646174696f6e20d181d0bad180d0b8d0bfd182d0b02e"))
        for path in missing_paths:
            st.code(str(path.relative_to(ROOT)))
        return

    try:
        prediction = _load_json(PREDICTION_PATH)
        scores = _load_json(SCORES_PATH)
        summary = _load_json(SUMMARY_PATH)
    except Exception as exc:
        st.error(f'{_bg("d094d0b0d0bdd0bdd0b8d182d0b520d0bdd0b02076343220d0bdd0b520d0bcd0bed0b3d0b0d18220d0b4d0b020d181d0b520d0b7d0b0d180d0b5d0b4d18fd182")}: {exc}')
        return

    numbers = prediction.get("numbers", [])
    details = prediction.get("selected_number_details", [])

    if not numbers:
        st.warning(_bg("d09dd18fd0bcd0b020d0bdd0b0d0bbd0b8d187d0bdd0b820d0b4d0b0d0bdd0bdd0b820d0b7d0b020d0bfd0bed0bad0b0d0b7d0b2d0b0d0bdd0b52e"))
        return

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric(_bg("d0a1d180d0b5d0b4d0b5d0bd20d0bfd0bed0bbd0bed0b6d0b8d182d0b5d0bbd0b5d0bd20d181d0b8d0b3d0bdd0b0d0bb"), _format_score(prediction.get("average_positive_signal_score")))
    metric_2.metric(_bg("d0a1d180d0b5d0b4d0b5d0bd20d180d0b8d181d0ba20d0bed18220d0bed182d181d18ad181d182d0b2d0b8d0b5"), _format_score(prediction.get("average_absence_risk_score")))
    metric_3.metric(_bg("d0a1d180d0b5d0b4d0b5d0bd20d0bad0bed0bcd0b1d0b8d0bdd0b8d180d0b0d0bd20d180d0b5d0b7d183d0bbd182d0b0d182"), _format_score(prediction.get("average_combined_score")))

    st.subheader(_bg("d0a1d182d0b0d182d0b8d181d182d0b8d187d0b5d181d0bad0be20d0bfd180d0b5d0b4d0bbd0bed0b6d0b5d0bdd0b8d0b5"))
    st.markdown(f"### `{_numbers_line(numbers)}`")
    st.caption(_bg("d09dd0b520d0b520d0bfd0b5d187d0b5d0bbd0b8d0b2d188d0b020d0bfd180d0bed0b3d0bdd0bed0b7d0b0"))

    if details:
        st.dataframe(_details_dataframe(details), hide_index=True, use_container_width=True)

    dataset = scores.get("dataset", {})
    data_col_1, data_col_2, data_col_3 = st.columns(3)
    data_col_1.metric(_bg("d092d0b0d0bbd0b8d0b4d0bdd0b820d182d0b8d180d0b0d0b6d0b8"), dataset.get("valid_draw_events", "-"))
    data_col_2.metric(_bg("426f6e757320d187d0b8d181d0bbd0be"), _bg("d0bdd0b520d181d0b520d0b8d0b7d0bfd0bed0bbd0b7d0b2d0b0") if dataset.get("uses_bonus") is False else str(dataset.get("uses_bonus")))
    data_col_3.metric(_bg("d09cd0bed0b4d0b5d0bb"), _bg("d09ad0bed0bcd0b1d0b8d0bdd0b8d180d0b0d0bd"))

    st.subheader(_bg("d0a2d0bed0bf20d0bad0bed0bcd0b1d0b8d0bdd0b8d180d0b0d0bdd0b820d187d0b8d181d0bbd0b0"))
    top_combined = summary.get("top_combined_numbers", [])[:12]
    if top_combined:
        st.dataframe(_combined_dataframe(top_combined), hide_index=True, use_container_width=True)

    st.subheader(_bg("d0a2d0bed0bf20d180d0b8d181d0ba20d0bed18220d0bed182d181d18ad181d182d0b2d0b8d0b5"))
    top_risk = summary.get("top_absence_risk_numbers", [])[:12]
    if top_risk:
        st.dataframe(_risk_dataframe(top_risk), hide_index=True, use_container_width=True)

    all_number_rows = scores.get("numbers", [])
    avoided = sorted(
        all_number_rows,
        key=lambda row: (row.get("combined_score", 0), -row.get("absence_risk_score", 0)),
    )[:10]

    st.subheader(_bg("d098d0b7d0b1d18fd0b3d0b2d0b0d0bdd0b820d0bed18220d0bcd0bed0b4d0b5d0bbd0b020d187d0b8d181d0bbd0b0"))
    st.caption(
        _bg("d0a2d0bed0b2d0b020d0bdd0b520d0bed0b7d0bdd0b0d187d0b0d0b2d0b02c20d187d0b520d182d0b5d0b7d0b820d187d0b8d181d0bbd0b020d0bdd18fd0bcd0b020d0b4d0b020d181d0b520d0bfd0b0d0b4d0bdd0b0d1822e20d09ed0b7d0bdd0b0d187d0b0d0b2d0b020d181d0b0d0bcd0be2c20d187d0b520d181d0bfd0bed180d0b5d0b420d182d0b5d0bad183d189d0b8d18f20d0b0d0bdd0b0d0bbd0b8d0b720d0b8d0bcd0b0d18220d0bfd0be2dd181d0bbd0b0d0b120d0bad0bed0bcd0b1d0b8d0bdd0b8d180d0b0d0bd20d0bfd180d0bed184d0b8d0bb20d0b8d0bbd0b820d0bfd0be2dd0b2d0b8d181d0bed0ba20d180d0b8d181d0ba20d0bed18220d0bed182d181d18ad181d182d0b2d0b8d0b52e")
    )
    if avoided:
        st.dataframe(_details_dataframe(avoided), hide_index=True, use_container_width=True)


    # USER_COMBINATION_CHECKER_UI_START
    st.divider()
    st.subheader(_bg("d09fd180d0bed0b2d0b5d180d0b820d0bcd0bed18fd182d0b020d0bad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d18f"))

    st.info(
        _bg("d092d18ad0b2d0b5d0b4d0b820d0b2d181d18fd0bad0be20d187d0b8d181d0bbd0be20d0b220d0bed182d0b4d0b5d0bbd0bdd0be20d0bfd0bed0bbd0b52e20d0a2d0b0d0bad0b020d0bdd0b520d181d0b020d0bdd183d0b6d0bdd0b820d0b7d0b0d0bfd0b5d182d0b0d0b82e")
    )

    input_cols = st.columns(6)
    cell_values = []

    for index, input_col in enumerate(input_cols, start=1):
        with input_col:
            cell_values.append(
                st.text_input(
                    _bg("d0a7d0b8d181d0bbd0be") + f" {index}",
                    value="",
                    placeholder="1-49",
                    max_chars=2,
                    key=f"combined_analysis_number_cell_{index}",
                )
            )

    check_clicked = st.button(
        _bg("d09fd180d0bed0b2d0b5d180d0b820d0bad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d18fd182d0b0"),
        type="primary",
        use_container_width=True,
    )

    if check_clicked:
        stripped_values = [value.strip() for value in cell_values]

        if not any(stripped_values):
            st.error(_bg("d09fd18ad180d0b2d0be20d0b2d18ad0b2d0b5d0b4d0b8203620d187d0b8d181d0bbd0b02e"))
        elif not all(stripped_values):
            st.error(_bg("d092d181d0b8d187d0bad0b820d0bfd0bed0bbd0b5d182d0b020d182d180d18fd0b1d0b2d0b020d0b4d0b020d181d18ad0b4d18ad180d0b6d0b0d18220d187d0b8d181d0bbd0b02e"))
        else:
            parsed_numbers = []
            parse_errors = []

            for value in stripped_values:
                try:
                    parsed_numbers.append(int(value))
                except ValueError:
                    parse_errors.append(value)

            invalid_range = [number for number in parsed_numbers if number < 1 or number > 49]

            unique_numbers = []
            for number in parsed_numbers:
                if 1 <= number <= 49 and number not in unique_numbers:
                    unique_numbers.append(number)

            if parse_errors:
                st.error(
                    _bg("d092d181d0b8d187d0bad0b820d0bfd0bed0bbd0b5d182d0b020d182d180d18fd0b1d0b2d0b020d0b4d0b020d181d18ad0b4d18ad180d0b6d0b0d18220d187d0b8d181d0bbd0b02e")
                    + " "
                    + ", ".join(parse_errors)
                )
            elif invalid_range:
                st.error(
                    _bg("d0a7d0b8d181d0bbd0b0d182d0b020d182d180d18fd0b1d0b2d0b020d0b4d0b020d181d0b020d0bcd0b5d0b6d0b4d183203120d0b8203439")
                    + ": "
                    + ", ".join(str(number) for number in invalid_range)
                )
            elif len(unique_numbers) != 6:
                st.error(_bg("d09ad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d18fd182d0b020d182d180d18fd0b1d0b2d0b020d0b4d0b020d181d18ad0b4d18ad180d0b6d0b0203620d180d0b0d0b7d0bbd0b8d187d0bdd0b820d187d0b8d181d0bbd0b02e"))
            else:
                score_map = _number_scores_map(scores)
                evaluation = _evaluate_user_combination(unique_numbers, score_map)

                st.success(_bg("d0a2d0b2d0bed18fd182d0b020d0bad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d18f"))

                st.subheader(_bg("d0a2d0b2d0bed18fd182d0b020d0bad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d18f"))
                number_cols = st.columns(6)
                for column, number in zip(number_cols, unique_numbers):
                    column.metric(_bg("d0a7d0b8d181d0bbd0be"), number)

                st.subheader(_bg("d09ed186d0b5d0bdd0bad0b020d0bdd0b020d0bad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d18fd182d0b0"))

                combo_col_1, combo_col_2, combo_col_3 = st.columns(3)
                combo_col_1.metric(
                    _bg("d09fd0bed0bbd0bed0b6d0b8d182d0b5d0bbd0b5d0bd20d181d0b8d0b3d0bdd0b0d0bb"),
                    _format_score(evaluation["average_positive"]),
                )
                combo_col_2.metric(
                    _bg("d0a0d0b8d181d0ba20d0bed18220d0bed182d181d18ad181d182d0b2d0b8d0b5"),
                    _format_score(evaluation["average_risk"]),
                )
                combo_col_3.metric(
                    _bg("d09ad0bed0bcd0b1d0b8d0bdd0b8d180d0b0d0bd20d180d0b5d0b7d183d0bbd182d0b0d182"),
                    _format_score(evaluation["average_combined"]),
                )

                st.subheader(_bg("d0a1d182d0b0d182d0b8d181d182d0b8d0bad0b020d0b7d0b020d0b8d0b7d0b1d180d0b0d0bdd0b8d182d0b520d187d0b8d181d0bbd0b0"))

                details_df = _combination_details_dataframe(evaluation["details"])
                if not details_df.empty:
                    st.dataframe(details_df, hide_index=True, use_container_width=True)

                strongest_numbers = [str(row.get("number")) for row in evaluation["strongest"]]
                risk_numbers = [str(row.get("number")) for row in evaluation["highest_risk"]]

                info_col_1, info_col_2 = st.columns(2)
                with info_col_1:
                    st.info(
                        _bg("d09dd0b0d0b92dd181d0b8d0bbd0bdd0b820d187d0b8d181d0bbd0b0")
                        + ": "
                        + ", ".join(strongest_numbers)
                    )
                with info_col_2:
                    st.warning(
                        _bg("d09fd0be2dd0b2d0b8d181d0bed0ba20d180d0b8d181d0ba")
                        + ": "
                        + ", ".join(risk_numbers)
                    )

                st.caption(
                    _bg("d0a2d0b5d0b7d0b820d187d0b8d181d0bbd0b020d0bdd0b520d181d0b020d0bfd180d0bed0b3d0bdd0bed0b7d0b02e20d0a2d0bed0b2d0b020d0b520d181d182d0b0d182d0b8d181d182d0b8d187d0b5d181d0bad0b020d0bed186d0b5d0bdd0bad0b020d0bdd0b020d0b8d181d182d0bed180d0b8d187d0b5d181d0bad0b820d0b4d0b0d0bdd0bdd0b82e")
                )

    # USER_COMBINATION_CHECKER_UI_END


    with st.expander(_bg("d09ad0b0d0ba20d0b4d0b020d181d0b520d187d0b5d182d0b5")):
        st.write(
            _bg("d09fd0bed0bbd0bed0b6d0b8d182d0b5d0bbd0bdd0b8d18fd18220d181d0b8d0b3d0bdd0b0d0bb20d0bfd0bed0bad0b0d0b7d0b2d0b020d0b8d181d182d0bed180d0b8d187d0b5d181d0bad0b020d0b0d0bad182d0b8d0b2d0bdd0bed181d18220d0b820d0bfd0bed0b4d0bad180d0b5d0bfd0b020d0bed18220d0bfd180d0b5d0b4d0b8d188d0bdd0b8d182d0b52076343120d180d0b5d0b7d183d0bbd182d0b0d182d0b82e20d0a0d0b8d181d0bad18ad18220d0bed18220d0bed182d181d18ad181d182d0b2d0b8d0b520d0bfd0bed0bad0b0d0b7d0b2d0b020d0b4d0bed0bad0bed0bbd0bad0be20d187d0b8d181d0bbd0bed182d0be20d0b520d181d0bbd0b0d0b1d0be2c20d0b7d0b0d0bad18ad181d0bdd18fd0b2d0b0d189d0be20d0b8d0bbd0b820d0bfd0bed0b420d0bed187d0b0d0bad0b2d0b0d0bdd0bed182d0be2e20d09ad0bed0bcd0b1d0b8d0bdd0b8d180d0b0d0bdd0b8d18fd18220d180d0b5d0b7d183d0bbd182d0b0d18220d0b1d0b0d0bbd0b0d0bdd181d0b8d180d0b020d0b4d0b2d0b5d182d0b520d0bfd0bed181d0bed0bad0b82e")
        )

    st.warning(_bg("d09bd0bed182d0b0d180d0b8d0b9d0bdd0b8d182d0b520d182d0b5d0b3d0bbd0b5d0bdd0b8d18f20d181d0b020d181d0bbd183d187d0b0d0b9d0bdd0b82e20d0a2d0bed0b7d0b820d0bcd0bed0b4d0b5d0bb20d0bdd0b520d0b7d0bdd0b0d0b520d0b1d18ad0b4d0b5d189d0b5d182d0be20d0b820d0bdd0b520d0bed0b1d0b5d189d0b0d0b2d0b020d0bfd0b5d187d0b0d0bbd0b1d0b02e"))

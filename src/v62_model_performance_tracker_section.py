from __future__ import annotations

from pathlib import Path
import csv
import json

import streamlit as st

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "reports" / "v62_model_performance_summary.json"
LATEST_PATH = ROOT / "reports" / "v62_latest_model_performance.csv"
HISTORY_PATH = ROOT / "reports" / "v62_model_performance_history.csv"


MODEL_LABELS = {
    "v41_latest_predictions": "v41 \u2014 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0438 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u043d\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0438",
    "v42_combined_prediction": "v42 \u2014 \u043a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u043f\u043e\u0437\u0438\u0442\u0438\u0432\u0435\u043d/\u043d\u0435\u0433\u0430\u0442\u0438\u0432\u0435\u043d \u043c\u043e\u0434\u0435\u043b",
    "v44_1_final_ensemble_ticket": "v44.1 \u2014 \u0444\u0438\u043d\u0430\u043b\u0435\u043d ensemble \u0444\u0438\u0448",
    "v45_final_prediction_tickets": "v45 \u2014 Prediction Dashboard Pro",
    "v50_pair_group_intelligence": "v50 \u2014 \u0434\u0432\u043e\u0439\u043a\u0438 \u0438 \u0433\u0440\u0443\u043f\u0438",
    "v51_ticket_portfolio_intelligence": "v51 \u2014 \u043f\u043e\u0440\u0442\u0444\u043e\u043b\u0438\u043e \u043e\u0442 \u0444\u0438\u0448\u043e\u0432\u0435",
    "v57_hot_cold_stable": "v57 \u2014 \u0433\u043e\u0440\u0435\u0449\u0438, \u0441\u0442\u0443\u0434\u0435\u043d\u0438 \u0438 \u0441\u0442\u0430\u0431\u0438\u043b\u043d\u0438",
    "v58_smart_ensemble": "v58 \u2014 \u043e\u0431\u0435\u0434\u0438\u043d\u0435\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430",
    "v59_smart_ticket_builder_2": "v59 \u2014 \u0438\u043d\u0442\u0435\u043b\u0438\u0433\u0435\u043d\u0442\u0435\u043d \u0433\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440 2",
    "v61_latest_draw_signal_hits": "v61 \u2014 \u0441\u0438\u0433\u043d\u0430\u043b\u0438 \u043a\u044a\u043c \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u044f \u0442\u0438\u0440\u0430\u0436",
}

STATUS_LABELS = {
    "ok": "\u0438\u043c\u0430 \u0441\u0438\u0433\u043d\u0430\u043b",
    "no_candidate_signal": "\u043d\u044f\u043c\u0430 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442-\u0441\u0438\u0433\u043d\u0430\u043b",
}

LATEST_COLUMNS = [
    ("model_name", "\u041c\u043e\u0434\u0443\u043b / \u043c\u043e\u0434\u0435\u043b"),
    ("candidate_count", "\u0411\u0440\u043e\u0439 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u0438"),
    ("best_hits", "\u041d\u0430\u0439-\u0434\u043e\u0431\u0440\u0438 \u0441\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u044f"),
    ("coverage_percent", "\u041f\u043e\u043a\u0440\u0438\u0442\u0438\u0435 %"),
    ("hit_numbers", "\u0423\u043b\u0443\u0447\u0435\u043d\u0438 \u0447\u0438\u0441\u043b\u0430"),
    ("best_candidate", "\u041d\u0430\u0439-\u0431\u043b\u0438\u0437\u044a\u043a \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442"),
    ("status", "\u0421\u0442\u0430\u0442\u0443\u0441"),
]

HISTORY_COLUMNS = [
    ("date", "\u0414\u0430\u0442\u0430"),
    ("draw_number", "\u0422\u0438\u0440\u0430\u0436"),
    ("draw_position", "\u0422\u0435\u0433\u043b\u0435\u043d\u0435"),
    ("draw_numbers", "\u0420\u0435\u0430\u043b\u043d\u0438 \u0447\u0438\u0441\u043b\u0430"),
    ("model_name", "\u041c\u043e\u0434\u0443\u043b / \u043c\u043e\u0434\u0435\u043b"),
    ("best_hits", "\u041d\u0430\u0439-\u0434\u043e\u0431\u0440\u0438 \u0441\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u044f"),
    ("coverage_percent", "\u041f\u043e\u043a\u0440\u0438\u0442\u0438\u0435 %"),
    ("hit_numbers", "\u0423\u043b\u0443\u0447\u0435\u043d\u0438 \u0447\u0438\u0441\u043b\u0430"),
    ("best_candidate", "\u041d\u0430\u0439-\u0431\u043b\u0438\u0437\u044a\u043a \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442"),
    ("candidate_count", "\u0411\u0440\u043e\u0439 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u0438"),
    ("status", "\u0421\u0442\u0430\u0442\u0443\u0441"),
    ("updated_at", "\u041e\u0431\u043d\u043e\u0432\u0435\u043d\u043e"),
]


def _load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _model_label(value):
    value = str(value or "")
    return MODEL_LABELS.get(value, value)


def _status_label(value):
    value = str(value or "")
    return STATUS_LABELS.get(value, value)


def _format_value(key, value):
    if value is None:
        return ""

    if key == "model_name":
        return _model_label(value)

    if key == "status":
        return _status_label(value)

    if key == "coverage_percent":
        try:
            number = float(value)
            return f"{number:.2f}%"
        except (TypeError, ValueError):
            return value

    if key in {"best_hits", "candidate_count"}:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return value

    return value


def _localize_rows(rows, columns):
    localized = []

    for row in rows:
        item = {}
        for source_key, bg_label in columns:
            item[bg_label] = _format_value(source_key, row.get(source_key, ""))
        localized.append(item)

    return localized


def _show_table(rows, columns):
    if not rows:
        st.info("\u041d\u044f\u043c\u0430 \u043d\u0430\u043b\u0438\u0447\u043d\u0438 \u0440\u0435\u0434\u043e\u0432\u0435 \u0437\u0430 \u043f\u043e\u043a\u0430\u0437\u0432\u0430\u043d\u0435.")
        return

    localized = _localize_rows(rows, columns)

    if pd is not None:
        st.dataframe(pd.DataFrame(localized), use_container_width=True, hide_index=True)
    else:
        st.table(localized)


def render_v62_model_performance_tracker_section():
    st.title("\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435")
    st.caption(
        "\u0418\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 post-draw \u0430\u043d\u0430\u043b\u0438\u0437: "
        "\u043a\u043e\u043b\u043a\u043e \u0431\u043b\u0438\u0437\u043e \u0441\u0430 \u0431\u0438\u043b\u0438 \u0442\u0435\u043a\u0443\u0449\u0438\u0442\u0435 "
        "\u043c\u043e\u0434\u0435\u043b\u043d\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0438 \u0434\u043e \u0440\u0435\u0430\u043b\u043d\u0438\u044f \u0442\u0438\u0440\u0430\u0436. "
        "\u0422\u043e\u0432\u0430 \u043d\u0435 \u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430."
    )

    summary = _load_json(SUMMARY_PATH)
    latest_rows = _load_csv(LATEST_PATH)
    history_rows = _load_csv(HISTORY_PATH)

    if not summary:
        st.warning(
            "\u041b\u0438\u043f\u0441\u0432\u0430 Step 62 report. "
            "\u041f\u0443\u0441\u043d\u0438: python scripts/v62_build_model_performance_tracker.py"
        )
        return

    latest_draw = summary.get("latest_draw", {})
    numbers = latest_draw.get("numbers", [])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("\u0422\u0438\u0440\u0430\u0436\u0438", summary.get("total_draws", 0))
    col2.metric("\u041c\u043e\u0434\u0435\u043b\u0438", summary.get("models_evaluated", 0))
    col3.metric("\u041d\u0430\u0439-\u0434\u043e\u0431\u0440\u043e \u0441\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u0435", f"{summary.get('best_hits', 0)}/6")
    col4.metric("\u0421\u0440\u0435\u0434\u043d\u043e \u043d\u0430\u0439-\u0434\u043e\u0431\u0440\u043e", summary.get("average_best_hits", 0))

    st.subheader("\u041f\u043e\u0441\u043b\u0435\u0434\u0435\u043d \u0440\u0435\u0430\u043b\u0435\u043d \u0442\u0438\u0440\u0430\u0436")
    st.write(
        f"**{latest_draw.get('date', '')} / {latest_draw.get('draw_number', '')}** \u2014 "
        f"{', '.join(str(n) for n in numbers)}"
    )

    best_models = [_model_label(model) for model in summary.get("best_models", [])]
    if best_models:
        st.success(
            "\u041d\u0430\u0439-\u0431\u043b\u0438\u0437\u043a\u0438 \u043c\u043e\u0434\u0435\u043b\u043d\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0438: "
            + ", ".join(best_models)
        )

    st.subheader("\u041f\u0440\u0435\u0434\u0441\u0442\u0430\u0432\u044f\u043d\u0435 \u043f\u043e \u043c\u043e\u0434\u0435\u043b \u0437\u0430 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u044f \u0442\u0438\u0440\u0430\u0436")
    _show_table(latest_rows, LATEST_COLUMNS)

    st.subheader("\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043d\u0430 \u043f\u0440\u043e\u0441\u043b\u0435\u0434\u044f\u0432\u0430\u043d\u0435\u0442\u043e")
    st.caption(
        "\u041f\u0440\u0438 \u0432\u0441\u0435\u043a\u0438 \u043d\u043e\u0432 \u0442\u0438\u0440\u0430\u0436 \u0442\u0443\u043a \u0449\u0435 \u0441\u0435 \u0434\u043e\u0431\u0430\u0432\u044f "
        "\u043d\u043e\u0432 \u0441\u043b\u043e\u0439 \u043e\u0442 \u0441\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u044f."
    )
    _show_table(history_rows, HISTORY_COLUMNS)

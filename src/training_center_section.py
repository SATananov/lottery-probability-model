
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]

TRAINING_STEPS = [
    {
        "name": "\\u041f\\u0440\\u0430\\u0432\\u0438\\u043b\\u043e\\u0432\\u043e-\\u0441\\u044a\\u0437\\u043d\\u0430\\u0442\\u0438 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438",
        "script": "scripts/v41_train_rules_aware_models.py",
        "outputs": ["models/v41", "reports/v41_model_retraining_summary.json"],
    },
    {
        "name": "\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0438\\u0440\\u0430\\u043d \\u043f\\u043e\\u0437\\u0438\\u0442\\u0438\\u0432\\u0435\\u043d / \\u043e\\u0442\\u0440\\u0438\\u0446\\u0430\\u0442\\u0435\\u043b\\u0435\\u043d \\u0430\\u043d\\u0430\\u043b\\u0438\\u0437",
        "script": "scripts/v42_build_combined_positive_negative_foundation.py",
        "outputs": ["models/v42", "reports"],
    },
    {
        "name": "\\u0418\\u043d\\u0442\\u0435\\u0440\\u0432\\u0430\\u043b\\u0435\\u043d \\u0440\\u0438\\u0442\\u044a\\u043c",
        "script": "scripts/v43_1_refine_interval_rhythm_foundation.py",
        "outputs": ["models/v43_1", "reports"],
    },
    {
        "name": "\\u0424\\u0438\\u043d\\u0430\\u043b\\u0435\\u043d \\u0430\\u043d\\u0441\\u0430\\u043c\\u0431\\u044a\\u043b",
        "script": "scripts/v44_1_refine_final_ensemble_ticket_foundation.py",
        "outputs": ["models/v44_1", "reports"],
    },
    {
        "name": "\\u041f\\u0440\\u043e\\u0433\\u043d\\u043e\\u0437\\u043d\\u043e \\u0442\\u0430\\u0431\\u043b\\u043e Pro",
        "script": "scripts/v45_train_prediction_engine_pro.py",
        "outputs": ["models/v45", "reports/v45_training_summary.json"],
    },
]

V45_SUMMARY_PATH = ROOT / "reports" / "v45_training_summary.json"
V45_BY_MODEL_PATH = ROOT / "reports" / "v45_backtest_by_model.csv"


def T(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


def _exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def _mtime(rel_path: str) -> str:
    path = ROOT / rel_path
    if not path.exists():
        return "-"
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _run_script(script: str) -> tuple[bool, str]:
    script_path = ROOT / script
    if not script_path.exists():
        return False, T("\\u0421\\u043a\\u0440\\u0438\\u043f\\u0442\\u044a\\u0442 \\u043d\\u0435 \\u0435 \\u043d\\u0430\\u043c\\u0435\\u0440\\u0435\\u043d: ") + script

    try:
        completed = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=900,
        )
    except subprocess.TimeoutExpired:
        return False, T("\\u041f\\u0440\\u043e\\u0446\\u0435\\u0441\\u044a\\u0442 \\u043d\\u0430\\u0434\\u0445\\u0432\\u044a\\u0440\\u043b\\u0438 \\u043b\\u0438\\u043c\\u0438\\u0442\\u0430 \\u0437\\u0430 \\u0432\\u0440\\u0435\\u043c\\u0435.")

    output = []
    if completed.stdout:
        output.append(completed.stdout)
    if completed.stderr:
        output.append(completed.stderr)

    return completed.returncode == 0, "\n".join(output).strip()


def _render_status_table() -> None:
    rows = []

    for step in TRAINING_STEPS:
        script = step["script"]
        outputs = step["outputs"]

        rows.append(
            {
                T("\\u0415\\u0442\\u0430\\u043f"): T(step["name"]),
                T("\\u0421\\u043a\\u0440\\u0438\\u043f\\u0442"): script,
                T("\\u0421\\u043a\\u0440\\u0438\\u043f\\u0442 \\u043d\\u0430\\u043b\\u0438\\u0447\\u0435\\u043d"): T("\\u0414\\u0430") if _exists(script) else T("\\u041d\\u0435"),
                T("\\u041e\\u0441\\u043d\\u043e\\u0432\\u043d\\u0438 \\u0430\\u0440\\u0442\\u0435\\u0444\\u0430\\u043a\\u0442\\u0438"): ", ".join(outputs),
                T("\\u0410\\u0440\\u0442\\u0435\\u0444\\u0430\\u043a\\u0442\\u0438 OK"): T("\\u0414\\u0430") if all(_exists(p) for p in outputs) else T("\\u041d\\u0435"),
                T("\\u041f\\u043e\\u0441\\u043b\\u0435\\u0434\\u043d\\u0430 \\u043f\\u0440\\u043e\\u043c\\u044f\\u043d\\u0430"): _mtime(outputs[-1]),
            }
        )

    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def _render_v45_summary() -> None:
    summary = _read_json(V45_SUMMARY_PATH)

    if not summary:
        st.info(T("\\u041d\\u044f\\u043c\\u0430 \\u043d\\u0430\\u043b\\u0438\\u0447\\u0435\\u043d v45 summary. \\u041f\\u0443\\u0441\\u043d\\u0438 Pro \\u043e\\u0431\\u0443\\u0447\\u0435\\u043d\\u0438\\u0435\\u0442\\u043e."))
        return

    dataset_events = summary.get("dataset_events", summary.get("DATASET_EVENTS", "-"))
    feature_rows = summary.get("feature_rows", summary.get("FEATURE_ROWS", "-"))
    train_events = summary.get("train_events", summary.get("TRAIN_EVENTS", "-"))
    test_events = summary.get("test_events", summary.get("TEST_EVENTS", "-"))

    best_model = summary.get("best_model", {})
    best_model_name = "-"
    best_model_score = "-"

    if isinstance(best_model, dict):
        best_model_name = str(best_model.get("model", "-"))
        best_model_score = best_model.get("average_hits_top6", best_model.get("avg_hits", "-"))
    elif isinstance(best_model, str):
        best_model_name = best_model

    model_labels = {
        "recency_250_baseline": "\\u041c\\u043e\\u0434\\u0435\\u043b \\u043f\\u043e \\u0441\\u043a\\u043e\\u0440\\u043e\\u0448\\u043d\\u0430 \\u0430\\u043a\\u0442\\u0438\\u0432\\u043d\\u043e\\u0441\\u0442",
        "frequency_baseline": "\\u0427\\u0435\\u0441\\u0442\\u043e\\u0442\\u0435\\u043d \\u043c\\u043e\\u0434\\u0435\\u043b",
        "v45_pro_ensemble": "\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0438\\u0440\\u0430\\u043d Pro \\u0430\\u043d\\u0441\\u0430\\u043c\\u0431\\u044a\\u043b",
    }
    best_model_display = T(model_labels.get(best_model_name, best_model_name))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(T("\\u0412\\u0430\\u043b\\u0438\\u0434\\u043d\\u0438 \\u0442\\u0438\\u0440\\u0430\\u0436\\u0438"), str(dataset_events))
    c2.metric(T("\\u0420\\u0435\\u0434\\u043e\\u0432\\u0435 \\u0441 \\u043f\\u0440\\u0438\\u0437\\u043d\\u0430\\u0446\\u0438"), str(feature_rows))
    c3.metric(T("\\u0422\\u0440\\u0435\\u043d\\u0438\\u0440\\u0430\\u0449\\u0438 / \\u0442\\u0435\\u0441\\u0442\\u043e\\u0432\\u0438"), f"{train_events} / {test_events}")
    c4.metric(T("\\u041d\\u0430\\u0439-\\u0434\\u043e\\u0431\\u044a\\u0440 \\u043c\\u043e\\u0434\\u0435\\u043b"), best_model_display)

    st.caption(T("\\u041d\\u0430\\u0439-\\u0434\\u043e\\u0431\\u044a\\u0440 \\u0440\\u0435\\u0437\\u0443\\u043b\\u0442\\u0430\\u0442 \\u043e\\u0442 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430\\u0442\\u0430 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430: ") + str(best_model_score))


def _render_backtest_preview() -> None:
    if not V45_BY_MODEL_PATH.exists():
        st.info(T("\\u041d\\u044f\\u043c\\u0430 reports/v45_backtest_by_model.csv."))
        return

    try:
        df = pd.read_csv(V45_BY_MODEL_PATH)
    except Exception as exc:
        st.error(T("\\u0413\\u0440\\u0435\\u0448\\u043a\\u0430 \\u043f\\u0440\\u0438 \\u0447\\u0435\\u0442\\u0435\\u043d\\u0435 \\u043d\\u0430 backtest \\u0444\\u0430\\u0439\\u043b\\u0430: ") + str(exc))
        return

    st.dataframe(df, hide_index=True, use_container_width=True)


def _render_training_buttons() -> None:
    st.subheader(T("\\u0420\\u044a\\u0447\\u043d\\u043e \\u043e\\u0431\\u043d\\u043e\\u0432\\u044f\\u0432\\u0430\\u043d\\u0435"))

    st.caption(
        T(
            "\\u041f\\u0443\\u0441\\u043a\\u0430\\u0439 \\u0433\\u0438 \\u0441\\u0430\\u043c\\u043e \\u043a\\u043e\\u0433\\u0430\\u0442\\u043e \\u0434\\u0430\\u043d\\u043d\\u0438\\u0442\\u0435 \\u0441\\u0430 \\u043f\\u0440\\u043e\\u043c\\u0435\\u043d\\u0435\\u043d\\u0438 \\u0438\\u043b\\u0438 \\u0438\\u0441\\u043a\\u0430\\u0448 \\u0434\\u0430 \\u043e\\u0431\\u043d\\u043e\\u0432\\u0438\\u0448 \\u0432\\u0441\\u0438\\u0447\\u043a\\u0438 \\u0430\\u0440\\u0442\\u0435\\u0444\\u0430\\u043a\\u0442\\u0438. \\u0422\\u043e\\u0432\\u0430 \\u043d\\u0435 \\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f \\u0437\\u0430 \\u043f\\u0435\\u0447\\u0430\\u043b\\u0431\\u0430."
        )
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(T("\\u041f\\u0443\\u0441\\u043d\\u0438 \\u0441\\u0430\\u043c\\u043e Pro \\u043e\\u0431\\u0443\\u0447\\u0435\\u043d\\u0438\\u0435"), type="primary"):
            ok, output = _run_script("scripts/v45_train_prediction_engine_pro.py")
            if ok:
                st.success(T("\\u0413\\u043e\\u0442\\u043e\\u0432\\u043e: Pro \\u043e\\u0431\\u0443\\u0447\\u0435\\u043d\\u0438\\u0435\\u0442\\u043e \\u043c\\u0438\\u043d\\u0430 \\u0443\\u0441\\u043f\\u0435\\u0448\\u043d\\u043e."))
            else:
                st.error(T("\\u0418\\u043c\\u0430 \\u0433\\u0440\\u0435\\u0448\\u043a\\u0430 \\u043f\\u0440\\u0438 Pro \\u043e\\u0431\\u0443\\u0447\\u0435\\u043d\\u0438\\u0435\\u0442\\u043e."))
            st.code(output or "-", language="text")

    with col2:
        if st.button(T("\\u041f\\u044a\\u043b\\u0435\\u043d refresh v41 \\u2192 v45")):
            full_output = []
            all_ok = True

            for step in TRAINING_STEPS:
                script = step["script"]
                ok, output = _run_script(script)
                all_ok = all_ok and ok
                status = "OK" if ok else "ERROR"
                full_output.append(f"=== {status}: {script} ===\n{output or '-'}")

                if not ok:
                    break

            if all_ok:
                st.success(T("\\u0413\\u043e\\u0442\\u043e\\u0432\\u043e: \\u043f\\u044a\\u043b\\u043d\\u0438\\u044f\\u0442 refresh \\u043c\\u0438\\u043d\\u0430 \\u0443\\u0441\\u043f\\u0435\\u0448\\u043d\\u043e."))
            else:
                st.error(T("\\u041f\\u044a\\u043b\\u043d\\u0438\\u044f\\u0442 refresh \\u0441\\u043f\\u0440\\u044f \\u043f\\u0440\\u0438 \\u0433\\u0440\\u0435\\u0448\\u043a\\u0430."))

            st.code("\n\n".join(full_output), language="text")


def render() -> None:
    st.title(T("\\u0426\\u0435\\u043d\\u0442\\u044a\\u0440 \\u0437\\u0430 \\u043e\\u0431\\u0443\\u0447\\u0435\\u043d\\u0438\\u0435 \\u043d\\u0430 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438\\u0442\\u0435"))

    st.caption(
        T(
            "\\u0422\\u0443\\u043a \\u0441\\u0435 \\u0432\\u0438\\u0436\\u0434\\u0430 \\u0441\\u044a\\u0441\\u0442\\u043e\\u044f\\u043d\\u0438\\u0435\\u0442\\u043e \\u043d\\u0430 training scripts, \\u043c\\u043e\\u0434\\u0435\\u043b\\u043d\\u0438\\u0442\\u0435 \\u0430\\u0440\\u0442\\u0435\\u0444\\u0430\\u043a\\u0442\\u0438 \\u0438 \\u043f\\u043e\\u0441\\u043b\\u0435\\u0434\\u043d\\u043e\\u0442\\u043e Pro \\u043e\\u0431\\u0443\\u0447\\u0435\\u043d\\u0438\\u0435."
        )
    )

    st.warning(
        T(
            "\\u041e\\u0431\\u0443\\u0447\\u0435\\u043d\\u0438\\u0435\\u0442\\u043e \\u043e\\u0431\\u043d\\u043e\\u0432\\u044f\\u0432\\u0430 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438\\u0442\\u0435 \\u0438 \\u043e\\u0442\\u0447\\u0435\\u0442\\u0438\\u0442\\u0435. \\u0422\\u043e \\u043d\\u0435 \\u043f\\u0440\\u043e\\u043c\\u0435\\u043d\\u044f \\u0441\\u043b\\u0443\\u0447\\u0430\\u0439\\u043d\\u0438\\u044f \\u0445\\u0430\\u0440\\u0430\\u043a\\u0442\\u0435\\u0440 \\u043d\\u0430 \\u0438\\u0433\\u0440\\u0430\\u0442\\u0430."
        )
    )

    tabs = st.tabs(
        [
            T("\\u041e\\u0431\\u043e\\u0431\\u0449\\u0435\\u043d\\u0438\\u0435"),
            T("\\u0410\\u0440\\u0442\\u0435\\u0444\\u0430\\u043a\\u0442\\u0438"),
            T("\\u0420\\u044a\\u0447\\u043d\\u043e \\u043e\\u0431\\u0443\\u0447\\u0435\\u043d\\u0438\\u0435"),
            T("Backtest"),
        ]
    )

    with tabs[0]:
        st.subheader(T("\\u041f\\u043e\\u0441\\u043b\\u0435\\u0434\\u043d\\u043e Pro \\u043e\\u0431\\u0443\\u0447\\u0435\\u043d\\u0438\\u0435"))
        _render_v45_summary()

    with tabs[1]:
        st.subheader(T("\\u0421\\u044a\\u0441\\u0442\\u043e\\u044f\\u043d\\u0438\\u0435 \\u043d\\u0430 \\u0430\\u0440\\u0442\\u0435\\u0444\\u0430\\u043a\\u0442\\u0438\\u0442\\u0435"))
        _render_status_table()

    with tabs[2]:
        _render_training_buttons()

    with tabs[3]:
        st.subheader(T("\\u041f\\u0440\\u0435\\u0433\\u043b\\u0435\\u0434 \\u043d\\u0430 Pro backtest"))
        _render_backtest_preview()

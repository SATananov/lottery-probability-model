
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
    {
        "name": "\\u0410\\u043d\\u0430\\u043b\\u0438\\u0437 \\u043d\\u0430 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438 \\u0438 \\u0433\\u0440\\u0443\\u043f\\u0438",
        "script": "scripts/v50_build_pair_group_intelligence.py",
        "outputs": ["models/v50", "reports/v50_pair_group_summary.json"],
    },
    {
        "name": "\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u0444\\u0438\\u0448",
        "script": "scripts/v51_build_ticket_portfolio_intelligence.py",
        "outputs": ["models/v51", "reports/v51_ticket_portfolio_summary.json"],
    },
    {
        "name": "\u041f\u043e\u043a\u0440\u0438\u0442\u0438\u0435 \u043d\u0430 \u0444\u0438\u0448\u0430",
        "script": "scripts/v53_build_ticket_coverage_intelligence.py",
        "outputs": ["models/v53", "reports/v53_ticket_coverage_summary.json"],
    },
    {
        "name": "\u0411\u0430\u043b\u0430\u043d\u0441 \u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438\u0442\u0435",
        "script": "scripts/v54_build_pattern_balance_engine.py",
        "outputs": ["models/v54", "reports/v54_pattern_balance_summary.json"],
    },
    {
        "name": "\u041f\u0440\u043e\u0444\u0438\u043b \u043d\u0430 \u0447\u0438\u0441\u043b\u043e",
        "script": "scripts/v55_build_number_profile_center.py",
        "outputs": ["models/v55", "reports/v55_number_profile_summary.json"],
    },
    {
        "name": "\u041f\u043e\u0434\u043e\u0431\u043d\u0438 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0442\u0438\u0440\u0430\u0436\u0438",
        "script": "scripts/v56_build_draw_similarity_search.py",
        "outputs": ["models/v56", "reports/v56_draw_similarity_summary.json"],
    },
    {
        "name": "\u0413\u043e\u0440\u0435\u0449\u0438, \u0441\u0442\u0443\u0434\u0435\u043d\u0438 \u0438 \u0441\u0442\u0430\u0431\u0438\u043b\u043d\u0438 \u0447\u0438\u0441\u043b\u0430",
        "script": "scripts/v57_build_hot_cold_stable_center.py",
        "outputs": ["models/v57", "reports/v57_hot_cold_stable_summary.json"],
    },
    {
        "name": "\u041e\u0431\u0435\u0434\u0438\u043d\u0435\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430",
        "script": "scripts/v58_build_smart_ensemble_score_2.py",
        "outputs": ["models/v58", "reports/v58_smart_ensemble_summary.json"],
    },
    {
        "name": "\u0418\u043d\u0442\u0435\u043b\u0438\u0433\u0435\u043d\u0442\u0435\u043d \u0433\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440 2",
        "script": "scripts/v59_build_smart_ticket_builder_2.py",
        "outputs": ["models/v59", "reports/v59_smart_ticket_builder_2_summary.json"],
    },
    {
        "name": "Изтегляне и финално изглаждане на генератор 2",
        "script": "scripts/v60_build_ticket_builder_2_polish_export.py",
        "outputs": ["models/v60", "reports/v60_ticket_builder_2_polish_export_summary.json"],
    },
    {
        "name": "\u0410\u043d\u0430\u043b\u0438\u0437 \u043d\u0430 \u043d\u043e\u0432 \u0442\u0438\u0440\u0430\u0436",
        "script": "scripts/v61_build_draw_result_analyzer.py",
        "outputs": ["models/v61", "reports/v61_draw_result_analyzer_summary.json"],
    },

    {
        "name": "\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435",
        "script": "scripts/v62_build_model_performance_tracker.py",
        "outputs": ['models/v62', 'reports/v62_model_performance_summary.json'],
    },
    {
        "name": "\u041d\u0430\u0434\u0435\u0436\u0434\u043d\u043e\u0441\u0442 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435",
        "script": "scripts/v63_build_model_reliability_dashboard.py",
        "outputs": ['models/v63', 'reports/v63_model_reliability_summary.json'],
    },
    {
        "name": "\u0423\u043c\u043d\u043e \u0442\u0435\u0433\u043b\u043e \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435",
        "script": "scripts/v65_build_model_weighting_center.py",
        "outputs": ['models/v65', 'reports/v65_model_weighting_summary.json'],
    },
    {
        "name": "\u041f\u0440\u0435\u0442\u0435\u0433\u043b\u0435\u043d ensemble \u0430\u043d\u0430\u043b\u0438\u0437",
        "script": "scripts/v66_build_weighted_smart_ensemble.py",
        "outputs": ['models/v66', 'reports/v66_weighted_smart_ensemble_summary.json'],
    },
    {
        "name": "\u0423\u043c\u0435\u043d \u0433\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440 \u0441 \u0442\u0435\u0433\u043b\u0430",
        "script": "scripts/v67_build_weighted_ticket_builder.py",
        "outputs": ['models/v67', 'reports/v67_weighted_ticket_builder_summary.json'],
    },
    {
        "name": "\u0423\u043c\u0435\u043d оптимизатор на портфейл",
        "script": "scripts/v68_build_weighted_portfolio_optimizer.py",
        "outputs": ['models/v68', 'reports/v68_weighted_portfolio_summary.json'],
    },
    {
        "name": "\u041f\u043e\u0434\u043e\u0431\u0440\u044f\u0432\u0430\u043d\u0435 \u043d\u0430 \u043f\u043e\u0440\u0442\u0444\u043e\u043b\u0438\u043e",
        "script": "scripts/v69_build_portfolio_improvement_suggestions.py",
        "outputs": ['models/v69', 'reports/v69_portfolio_improvement_summary.json'],
    },
    {
        "name": "\u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d \u043f\u043e\u0434\u043e\u0431\u0440\u0435\u043d \u043f\u043e\u0440\u0442\u0444\u0435\u0439\u043b",
        "script": "scripts/v70_build_applied_candidate_portfolio.py",
        "outputs": ['models/v70', 'reports/v70_applied_candidate_portfolio_summary.json'],
    },
    {
        "name": "\u041f\u0430\u043a\u0435\u0442 \u0437\u0430 \u0438\u0433\u0440\u0430",
        "script": "scripts/v71_build_ticket_pack_export.py",
        "outputs": ['models/v71', 'reports/v71_ticket_pack_summary.json'],
    },
    {
        "name": "Представяне на пакета",
        "script": "scripts/v73_build_ticket_pack_performance_tracker.py",
        "outputs": ["models/v73", "reports/v73_ticket_pack_performance_summary.json"],
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

    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


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


def _training_model_label(model: Any) -> str:
    labels = {
        "frequency_baseline": T("\\u0427\\u0435\\u0441\\u0442\\u043e\\u0442\\u0435\\u043d \\u043c\\u043e\\u0434\\u0435\\u043b"),
        "recency_250_baseline": T("\\u041c\\u043e\\u0434\\u0435\\u043b \\u043f\\u043e \\u0441\\u043a\\u043e\\u0440\\u043e\\u0448\\u043d\\u0430 \\u0430\\u043a\\u0442\\u0438\\u0432\\u043d\\u043e\\u0441\\u0442"),
        "gap_rhythm_statistical": T("\\u041c\\u043e\\u0434\\u0435\\u043b \\u043f\\u043e \\u0438\\u043d\\u0442\\u0435\\u0440\\u0432\\u0430\\u043b\\u0435\\u043d \\u0440\\u0438\\u0442\\u044a\\u043c"),
        "random_baseline": T("\\u0421\\u043b\\u0443\\u0447\\u0430\\u0435\\u043d \\u0431\\u0430\\u0437\\u043e\\u0432 \\u043c\\u043e\\u0434\\u0435\\u043b"),
        "sgd_logistic_probability": T("\\u0412\\u0435\\u0440\\u043e\\u044f\\u0442\\u043d\\u043e\\u0441\\u0442\\u0435\\u043d ML \\u043c\\u043e\\u0434\\u0435\\u043b"),
        "gaussian_naive_bayes": T("Naive Bayes \\u043c\\u043e\\u0434\\u0435\\u043b"),
        "v45_pro_ensemble": T("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0438\\u0440\\u0430\\u043d Pro \\u0430\\u043d\\u0441\\u0430\\u043c\\u0431\\u044a\\u043b"),
    }
    return labels.get(str(model), str(model))

def _render_backtest_preview() -> None:
    if not V45_BY_MODEL_PATH.exists():
        st.info(T("\\u041d\\u044f\\u043c\\u0430 reports/v45_backtest_by_model.csv."))
        return

    try:
        df = pd.read_csv(V45_BY_MODEL_PATH)
    except Exception as exc:
        st.error(T("\\u0413\\u0440\\u0435\\u0448\\u043a\\u0430 \\u043f\\u0440\\u0438 \\u0447\\u0435\\u0442\\u0435\\u043d\\u0435 \\u043d\\u0430 backtest \\u0444\\u0430\\u0439\\u043b\\u0430: ") + str(exc))
        return

    if df.empty:
        st.info(T("\\u0424\\u0430\\u0439\\u043b\\u044a\\u0442 \\u0437\\u0430 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430 \\u0435 \\u043f\\u0440\\u0430\\u0437\\u0435\\u043d."))
        return

    shown = df.copy()

    if "model" in shown.columns:
        shown["model"] = shown["model"].map(_training_model_label)

    rename_map = {
        "model": T("\\u041c\\u043e\\u0434\\u0435\\u043b"),
        "test_events": T("\\u0422\\u0435\\u0441\\u0442\\u043e\\u0432\\u0438 \\u0442\\u0438\\u0440\\u0430\\u0436\\u0438"),
        "average_hits_top6": T("\\u0421\\u0440\\u0435\\u0434\\u043d\\u043e \\u0443\\u0446\\u0435\\u043b\\u0435\\u043d\\u0438"),
        "median_hits_top6": T("\\u041c\\u0435\\u0434\\u0438\\u0430\\u043d\\u0430 \\u0443\\u0446\\u0435\\u043b\\u0435\\u043d\\u0438"),
        "max_hits_top6": T("\\u041c\\u0430\\u043a\\u0441. \\u0443\\u0446\\u0435\\u043b\\u0435\\u043d\\u0438"),
        "hit_distribution": T("\\u0420\\u0430\\u0437\\u043f\\u0440\\u0435\\u0434\\u0435\\u043b\\u0435\\u043d\\u0438\\u0435 \\u043d\\u0430 \\u0443\\u0446\\u0435\\u043b\\u0432\\u0430\\u043d\\u0438\\u044f\\u0442\\u0430"),
        "events_with_3plus_hits": T("\\u0422\\u0438\\u0440\\u0430\\u0436\\u0438 \\u0441 3+ \\u0443\\u0446\\u0435\\u043d\\u0438"),
        "events_with_4plus_hits": T("\\u0422\\u0438\\u0440\\u0430\\u0436\\u0438 \\u0441 4+ \\u0443\\u0446\\u0435\\u043d\\u0438"),
        "events_with_5plus_hits": T("\\u0422\\u0438\\u0440\\u0430\\u0436\\u0438 \\u0441 5+ \\u0443\\u0446\\u0435\\u043d\\u0438"),
        "events_with_6_hits": T("\\u0422\\u0438\\u0440\\u0430\\u0436\\u0438 \\u0441 6 \\u0443\\u0446\\u0435\\u043d\\u0438"),
    }

    preferred_order = [
        "model",
        "test_events",
        "average_hits_top6",
        "median_hits_top6",
        "max_hits_top6",
        "hit_distribution",
        "events_with_3plus_hits",
        "events_with_4plus_hits",
        "events_with_5plus_hits",
        "events_with_6_hits",
    ]

    ordered = [col for col in preferred_order if col in shown.columns]
    remaining = [col for col in shown.columns if col not in ordered]
    shown = shown[ordered + remaining].rename(columns=rename_map)

    st.caption(
        T(
            "\\u0422\\u0430\\u0431\\u043b\\u0438\\u0446\\u0430\\u0442\\u0430 \\u043f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u043e \\u0441\\u0440\\u0430\\u0432\\u043d\\u0435\\u043d\\u0438\\u0435 \\u043d\\u0430 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438\\u0442\\u0435. \\u0422\\u043e\\u0432\\u0430 \\u043d\\u0435 \\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f \\u0437\\u0430 \\u0431\\u044a\\u0434\\u0435\\u0449 \\u0440\\u0435\\u0437\\u0443\\u043b\\u0442\\u0430\\u0442."
        )
    )

    st.dataframe(shown, hide_index=True, width="stretch")

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
        if st.button(T("\\u041f\\u044a\\u043b\\u0435\\u043d refresh v41 \\u2192 v71")):
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



def _run_git_command(args: list[str]) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            args,
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return False, T("\\u041f\\u0440\\u043e\\u0446\\u0435\\u0441\\u044a\\u0442 \\u043d\\u0430 Git \\u043d\\u0430\\u0434\\u0445\\u0432\\u044a\\u0440\\u043b\\u0438 \\u043b\\u0438\\u043c\\u0438\\u0442\\u0430 \\u0437\\u0430 \\u0432\\u0440\\u0435\\u043c\\u0435.")
    except Exception as exc:
        return False, str(exc)

    output = []
    if completed.stdout:
        output.append(completed.stdout)
    if completed.stderr:
        output.append(completed.stderr)

    return completed.returncode == 0, "\\n".join(output).strip()


def _render_github_sync() -> None:
    st.subheader(T("\\u0421\\u0438\\u043d\\u0445\\u0440\\u043e\\u043d\\u0438\\u0437\\u0430\\u0446\\u0438\\u044f \\u0441 GitHub"))

    st.caption(
        T(
            "\\u0422\\u043e\\u0437\\u0438 \\u0431\\u0443\\u0442\\u043e\\u043d \\u043a\\u0430\\u0447\\u0432\\u0430 \\u0432 GitHub \\u0441\\u0430\\u043c\\u043e \\u043e\\u0431\\u043d\\u043e\\u0432\\u0435\\u043d\\u0438\\u0442\\u0435 \\u043f\\u0430\\u043f\\u043a\\u0438 models \\u0438 reports. \\u041d\\u0435 \\u0434\\u043e\\u0431\\u0430\\u0432\\u044f \\u0434\\u0440\\u0443\\u0433\\u0438 \\u0444\\u0430\\u0439\\u043b\\u043e\\u0432\\u0435."
        )
    )

    commit_message = st.text_input(
        T("\\u0421\\u044a\\u043e\\u0431\\u0449\\u0435\\u043d\\u0438\\u0435 \\u0437\\u0430 commit"),
        value="Refresh full претеглена верига artifacts from training center",
    )

    if st.button(T("\\u041a\\u0430\\u0447\\u0438 models/reports \\u0432 GitHub"), type="primary"):
        logs: list[str] = []

        ok_status, before_status = _run_git_command(["git", "status", "--short", "--", "models", "reports"])
        logs.append("=== git status --short -- models reports ===\\n" + (before_status or "-"))

        if ok_status and not before_status.strip():
            st.info(T("\\u041d\\u044f\\u043c\\u0430 \\u043f\\u0440\\u043e\\u043c\\u0435\\u043d\\u0438 \\u0432 models/reports \\u0437\\u0430 \\u043a\\u0430\\u0447\\u0432\\u0430\\u043d\\u0435."))
            st.code("\\n\\n".join(logs), language="text")
            return

        ok_add, add_output = _run_git_command(["git", "add", "models", "reports"])
        logs.append("=== git add models reports ===\\n" + (add_output or "-"))

        if not ok_add:
            st.error(T("\\u0413\\u0440\\u0435\\u0448\\u043a\\u0430 \\u043f\\u0440\\u0438 git add."))
            st.code("\\n\\n".join(logs), language="text")
            return

        ok_diff, diff_output = _run_git_command(["git", "diff", "--cached", "--name-only"])
        logs.append("=== staged files ===\\n" + (diff_output or "-"))

        if ok_diff and not diff_output.strip():
            st.info(T("\\u041d\\u044f\\u043c\\u0430 staged \\u043f\\u0440\\u043e\\u043c\\u0435\\u043d\\u0438 \\u0437\\u0430 commit."))
            st.code("\\n\\n".join(logs), language="text")
            return

        safe_message = commit_message.strip() or "Refresh full претеглена верига artifacts from training center"

        ok_commit, commit_output = _run_git_command(["git", "commit", "-m", safe_message])
        logs.append("=== git commit ===\\n" + (commit_output or "-"))

        if not ok_commit:
            st.error(T("\\u0413\\u0440\\u0435\\u0448\\u043a\\u0430 \\u043f\\u0440\\u0438 git commit."))
            st.code("\\n\\n".join(logs), language="text")
            return

        ok_push, push_output = _run_git_command(["git", "push"])
        logs.append("=== git push ===\\n" + (push_output or "-"))

        if ok_push:
            st.success(T("\\u0413\\u043e\\u0442\\u043e\\u0432\\u043e: models/reports \\u0441\\u0430 \\u043a\\u0430\\u0447\\u0435\\u043d\\u0438 \\u0432 GitHub."))
        else:
            st.error(T("\\u0413\\u0440\\u0435\\u0448\\u043a\\u0430 \\u043f\\u0440\\u0438 git push."))

        st.code("\\n\\n".join(logs), language="text")


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
            T("GitHub"),
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
        _render_github_sync()

    with tabs[4]:
        st.subheader(T("\\u041f\\u0440\\u0435\\u0433\\u043b\\u0435\\u0434 \\u043d\\u0430 Pro backtest"))
        _render_backtest_preview()

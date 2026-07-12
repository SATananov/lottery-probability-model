from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.v146_controlled_neural_robustness_engine import (
    FOLD_STABILITY_CSV_PATH,
    SEED_STABILITY_CSV_PATH,
    SUMMARY_JSON_PATH,
    run_controlled_neural_robustness,
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _load_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def render_v146_controlled_neural_robustness_section() -> None:
    st.title("Контролирана neural robustness проверка")
    st.caption(
        "Step 146 — multi-seed и multi-period walk-forward проверка с confidence intervals, stability анализ и разширени baselines."
    )
    st.warning(
        "Това е research-only исторически експеримент. Няма връзка с production pipeline или с реалните фишове."
    )

    summary = _load_json(SUMMARY_JSON_PATH)
    strategy = summary.get("strategy_summary", {}) or {}
    comparison = summary.get("comparison", {}) or {}
    split = summary.get("split_policy", {}) or {}

    neural = strategy.get("neural_dynamics_reservoir", {}) or {}
    frequency = strategy.get("frequency_walk_forward", {}) or {}
    recency = strategy.get("recency_weighted_walk_forward", {}) or {}
    random_mean = strategy.get("uniform_random_mean", {}) or {}
    metrics = st.columns(6)
    metrics[0].metric("Neural", f"{float(neural.get('average_best_hits_mean', 0)):.4f}")
    metrics[1].metric("Frequency", f"{float(frequency.get('average_best_hits_mean', 0)):.4f}")
    metrics[2].metric("Recency", f"{float(recency.get('average_best_hits_mean', 0)):.4f}")
    metrics[3].metric("Random mean", f"{float(random_mean.get('average_best_hits_mean', 0)):.4f}")
    metrics[4].metric("Runs", int(split.get("run_count", 0)))
    metrics[5].metric("Promotion", "PASS" if comparison.get("promotion_gate_passed") else "BLOCKED")

    st.info(str(comparison.get("interpretation", "Все още няма записан Step 146 резултат.")))

    if st.button("Повтори официалния Step 146 robustness run", type="primary", use_container_width=True):
        with st.spinner("Изпълняват се 15 контролирани walk-forward runs..."):
            report = run_controlled_neural_robustness(write_outputs=True, register=True)
        st.session_state["v146_experiment"] = report
        st.success(f"Експериментът е регистриран: {report['experiment']['experiment_id']}")
        summary = _load_json(SUMMARY_JSON_PATH)
        comparison = summary.get("comparison", {}) or {}

    st.markdown("### Сравнение с baselines и 95% confidence intervals")
    baseline_rows = [value for value in (comparison.get("baselines", {}) or {}).values() if isinstance(value, dict)]
    if baseline_rows:
        st.dataframe(pd.DataFrame(baseline_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Няма налична Step 146 comparison таблица.")

    st.markdown("### Стабилност по random seed")
    seed_rows = _load_csv(SEED_STABILITY_CSV_PATH)
    if seed_rows:
        st.dataframe(pd.DataFrame(seed_rows), use_container_width=True, hide_index=True)

    st.markdown("### Стабилност по исторически период")
    fold_rows = _load_csv(FOLD_STABILITY_CSV_PATH)
    if fold_rows:
        st.dataframe(pd.DataFrame(fold_rows), use_container_width=True, hide_index=True)

    st.markdown("### Promotion gate")
    requirements = comparison.get("promotion_requirements", {}) or {}
    for name, passed in requirements.items():
        st.markdown(f"- {'✅' if passed else '❌'} `{name}`")

    st.markdown("### Защити")
    st.markdown(
        "- Три неприпокриващи се исторически holdout периода.\n"
        "- Пет отделни random seeds.\n"
        "- Всеки target тираж се добавя в обучението едва след scoring.\n"
        "- 95% bootstrap confidence intervals и paired sign tests.\n"
        "- Личният дневник не се отваря и production pipeline не се използва.\n"
        "- Дори PASS не включва автоматично модела в реалните фишове."
    )

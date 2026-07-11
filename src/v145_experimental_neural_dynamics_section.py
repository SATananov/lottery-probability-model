from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.v145_experimental_neural_dynamics_engine import (
    DEFAULT_CONFIG,
    DRAW_COMPARISON_CSV_PATH,
    SUMMARY_JSON_PATH,
    run_experimental_neural_dynamics,
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _load_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def render_v145_experimental_neural_dynamics_section() -> None:
    st.title("Експериментален neural dynamics sandbox")
    st.caption(
        "Step 145 — изолиран walk-forward експеримент с leaky neural reservoir и сравнение срещу frequency, recency и uniform-random baselines."
    )
    st.warning(
        "Моделът е само за исторически изследвания. Не е включен в production pipeline, не генерира реални фишове и не гарантира печалба."
    )

    summary = _load_json(SUMMARY_JSON_PATH)
    neural = summary.get("neural_dynamics", {}) or {}
    frequency = summary.get("frequency_baseline", {}) or {}
    recency = summary.get("recency_baseline", {}) or {}
    random_summary = summary.get("random_summary", {}) or {}
    comparison = summary.get("comparison", {}) or {}

    metrics = st.columns(5)
    metrics[0].metric("Neural dynamics", f"{float(neural.get('average_best_hits', 0)):.4f}")
    metrics[1].metric("Frequency", f"{float(frequency.get('average_best_hits', 0)):.4f}")
    metrics[2].metric("Recency", f"{float(recency.get('average_best_hits', 0)):.4f}")
    metrics[3].metric("Uniform random", f"{float(random_summary.get('average_best_hits_mean', 0)):.4f}")
    metrics[4].metric("Promotion gate", "PASS" if comparison.get("promotion_gate_passed") else "BLOCKED")

    st.info(str(comparison.get("interpretation", "Няма изпълнен Step 145 експеримент.")))

    with st.expander("Конфигурация за нов sandbox експеримент", expanded=False):
        row1 = st.columns(4)
        holdout = row1[0].number_input("Holdout тиражи", 30, 2000, int(DEFAULT_CONFIG["holdout_draws"]), 10)
        training = row1[1].number_input(
            "Минимални обучаващи тиражи", 100, 9000, int(DEFAULT_CONFIG["minimum_training_draws"]), 100
        )
        package_size = row1[2].number_input("Комбинации в пакет", 1, 100, int(DEFAULT_CONFIG["package_size"]), 1)
        trials = row1[3].number_input("Random baseline опити", 1, 1000, int(DEFAULT_CONFIG["random_trials"]), 10)

        row2 = st.columns(4)
        pool = row2[0].number_input("Candidate pool", 6, 49, int(DEFAULT_CONFIG["frequency_pool_size"]), 1)
        decay = row2[1].number_input(
            "Recency decay", 0.8, 0.9999, float(DEFAULT_CONFIG["recency_decay"]), 0.001, format="%.4f"
        )
        reservoir = row2[2].number_input("Reservoir size", 4, 256, int(DEFAULT_CONFIG["reservoir_size"]), 4)
        leak = row2[3].number_input("Leak rate", 0.01, 1.0, float(DEFAULT_CONFIG["leak_rate"]), 0.01)

        row3 = st.columns(4)
        radius = row3[0].number_input(
            "Spectral radius", 0.05, 1.49, float(DEFAULT_CONFIG["spectral_radius"]), 0.01
        )
        ridge = row3[1].number_input("Ridge alpha", 0.01, 1000.0, float(DEFAULT_CONFIG["ridge_alpha"]), 1.0)
        power = row3[2].number_input("Score power", 0.1, 5.0, float(DEFAULT_CONFIG["score_power"]), 0.1)
        seed = row3[3].number_input("Random seed", 0, 2_147_483_647, int(DEFAULT_CONFIG["seed"]), 1)

        if st.button("Изпълни и регистрирай Step 145 експеримента", type="primary", use_container_width=True):
            with st.spinner("Изпълнява се neural dynamics walk-forward sandbox..."):
                report = run_experimental_neural_dynamics(
                    holdout_draws=int(holdout),
                    minimum_training_draws=int(training),
                    package_size=int(package_size),
                    random_trials=int(trials),
                    frequency_pool_size=int(pool),
                    recency_decay=float(decay),
                    reservoir_size=int(reservoir),
                    leak_rate=float(leak),
                    spectral_radius=float(radius),
                    ridge_alpha=float(ridge),
                    score_power=float(power),
                    seed=int(seed),
                    write_outputs=True,
                    register=True,
                )
            st.session_state["v145_experiment"] = report
            st.success(f"Експериментът е регистриран: {report['experiment']['experiment_id']}")
            summary = _load_json(SUMMARY_JSON_PATH)

    st.markdown("### Архитектура")
    architecture = summary.get("architecture", {}) or {}
    st.code(
        "\n".join(
            [
                f"model = {architecture.get('name', '—')}",
                f"state_equation = {architecture.get('state_equation', '—')}",
                f"reservoir_size = {architecture.get('reservoir_size', '—')}",
                f"actual_spectral_radius = {architecture.get('actual_spectral_radius', '—')}",
                "production_integration = false",
            ]
        )
    )

    st.markdown("### Paired comparison")
    paired = comparison.get("paired", {}) or {}
    paired_rows = [value for value in paired.values() if isinstance(value, dict)]
    if paired_rows:
        st.dataframe(pd.DataFrame(paired_rows), use_container_width=True, hide_index=True)

    st.markdown("### Holdout по тиражи")
    rows = _load_csv(DRAW_COMPARISON_CSV_PATH)
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Все още няма Step 145 draw-level резултати.")

    st.markdown("### Защити")
    st.markdown(
        "- Target тиражът се използва за обучение едва след scoring.\n"
        "- И четирите стратегии използват еднакъв брой комбинации.\n"
        "- Личният дневник не се отваря.\n"
        "- Не се изпълнява тежко ML преобучение.\n"
        "- Няма автоматично включване в реалните фишове, дори при положителен резултат."
    )

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
from src.v150_global_ui_polish import translate_value, ui_text


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


def _t(bg: str, en: str) -> str:
    return ui_text(bg, en, st)


def render_v145_experimental_neural_dynamics_section() -> None:
    st.title(_t("Лаборатория за невронна динамика", "Neural Dynamics Laboratory"))
    st.caption(
        _t(
            "Изолиран последователен исторически експеримент с невронен резервоар и сравнение с честотен, скорошен и случаен базов модел.",
            "Isolated walk-forward experiment with a neural reservoir compared with frequency, recency and uniform-random baselines.",
        )
    )
    st.warning(
        _t(
            "Моделът е само за исторически изследвания. Не е включен в работната верига, не генерира реални фишове и не гарантира печалба.",
            "The model is for historical research only. It is not part of the production pipeline, does not generate real tickets and does not guarantee a win.",
        )
    )

    summary = _load_json(SUMMARY_JSON_PATH)
    neural = summary.get("neural_dynamics", {}) or {}
    frequency = summary.get("frequency_baseline", {}) or {}
    recency = summary.get("recency_baseline", {}) or {}
    random_summary = summary.get("random_summary", {}) or {}
    comparison = summary.get("comparison", {}) or {}

    metrics = st.columns(4)
    metrics[0].metric(_t("Невронен модел", "Neural model"), f"{float(neural.get('average_best_hits', 0)):.4f}")
    metrics[1].metric(_t("Честотен модел", "Frequency model"), f"{float(frequency.get('average_best_hits', 0)):.4f}")
    metrics[2].metric(_t("Модел на скорошната активност", "Recency model"), f"{float(recency.get('average_best_hits', 0)):.4f}")
    metrics[3].metric(_t("Случаен модел", "Random model"), f"{float(random_summary.get('average_best_hits_mean', 0)):.4f}")

    gate_passed = bool(comparison.get("promotion_gate_passed"))
    if gate_passed:
        st.success(_t("Решение: условията за допускане са изпълнени.", "Decision: promotion criteria passed."))
    else:
        st.warning(_t("Решение: моделът не е допуснат до работния режим.", "Decision: the model is not promoted to production mode."))
    st.info(translate_value(comparison.get("interpretation") or _t("Все още няма изпълнен експеримент.", "No experiment has been run.")))

    with st.expander(_t("Нова експериментална проверка", "New experimental evaluation"), expanded=False):
        row1 = st.columns(4)
        holdout = row1[0].number_input(_t("Тиражи за независима проверка", "Independent evaluation draws"), 30, 2000, int(DEFAULT_CONFIG["holdout_draws"]), 10)
        training = row1[1].number_input(_t("Минимални обучаващи тиражи", "Minimum training draws"), 100, 9000, int(DEFAULT_CONFIG["minimum_training_draws"]), 100)
        package_size = row1[2].number_input(_t("Комбинации в пакет", "Combinations per package"), 1, 100, int(DEFAULT_CONFIG["package_size"]), 1)
        trials = row1[3].number_input(_t("Опити със случаен базов модел", "Random baseline trials"), 1, 1000, int(DEFAULT_CONFIG["random_trials"]), 10)

        row2 = st.columns(4)
        pool = row2[0].number_input(_t("Размер на набора кандидати", "Candidate pool size"), 6, 49, int(DEFAULT_CONFIG["frequency_pool_size"]), 1)
        decay = row2[1].number_input(_t("Коефициент за скорошна активност", "Recency decay"), 0.8, 0.9999, float(DEFAULT_CONFIG["recency_decay"]), 0.001, format="%.4f")
        reservoir = row2[2].number_input(_t("Размер на невронния резервоар", "Reservoir size"), 4, 256, int(DEFAULT_CONFIG["reservoir_size"]), 4)
        leak = row2[3].number_input(_t("Коефициент на пропускане", "Leak rate"), 0.01, 1.0, float(DEFAULT_CONFIG["leak_rate"]), 0.01)

        row3 = st.columns(4)
        radius = row3[0].number_input(_t("Спектрален радиус", "Spectral radius"), 0.05, 1.49, float(DEFAULT_CONFIG["spectral_radius"]), 0.01)
        ridge = row3[1].number_input(_t("Коефициент за регуляризация", "Ridge alpha"), 0.01, 1000.0, float(DEFAULT_CONFIG["ridge_alpha"]), 1.0)
        power = row3[2].number_input(_t("Степен на оценката", "Score power"), 0.1, 5.0, float(DEFAULT_CONFIG["score_power"]), 0.1)
        seed = row3[3].number_input(_t("Начална стойност за повторяемост", "Random seed"), 0, 2_147_483_647, int(DEFAULT_CONFIG["seed"]), 1)

        if st.button(_t("Изпълни и регистрирай експеримента", "Run and register experiment"), type="primary", use_container_width=True):
            with st.spinner(_t("Изпълнява се историческата проверка на невронната динамика...", "Running the neural dynamics walk-forward evaluation...")):
                report = run_experimental_neural_dynamics(
                    holdout_draws=int(holdout), minimum_training_draws=int(training), package_size=int(package_size),
                    random_trials=int(trials), frequency_pool_size=int(pool), recency_decay=float(decay),
                    reservoir_size=int(reservoir), leak_rate=float(leak), spectral_radius=float(radius),
                    ridge_alpha=float(ridge), score_power=float(power), seed=int(seed), write_outputs=True, register=True,
                )
            st.session_state["v145_experiment"] = report
            st.success(_t(f"Експериментът е регистриран: {report['experiment']['experiment_id']}", f"Experiment registered: {report['experiment']['experiment_id']}"))
            summary = _load_json(SUMMARY_JSON_PATH)

    with st.expander(_t("Архитектура и технически параметри", "Architecture and technical parameters"), expanded=False):
        architecture = summary.get("architecture", {}) or {}
        st.caption(_t("Този раздел е за технически одит и възпроизводимост.", "This section is for technical audit and reproducibility."))
        st.code("\n".join([
            f"model = {architecture.get('name', '—')}",
            f"state_equation = {architecture.get('state_equation', '—')}",
            f"reservoir_size = {architecture.get('reservoir_size', '—')}",
            f"actual_spectral_radius = {architecture.get('actual_spectral_radius', '—')}",
            "production_integration = false",
        ]))

    st.markdown(_t("### Сравнение по двойки", "### Paired comparison"))
    paired = comparison.get("paired", {}) or {}
    paired_rows = [value for value in paired.values() if isinstance(value, dict)]
    if paired_rows:
        st.dataframe(pd.DataFrame(paired_rows), use_container_width=True, hide_index=True)

    st.markdown(_t("### Резултати по тиражи за независима проверка", "### Per-draw independent evaluation results"))
    rows = _load_csv(DRAW_COMPARISON_CSV_PATH)
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info(_t("Все още няма резултати по отделни тиражи.", "No per-draw results are available yet."))

    st.markdown(_t("### Защити", "### Safeguards"))
    st.markdown(_t(
        "- Целевият тираж се използва за обучение едва след оценяването му.\n"
        "- Всички стратегии използват еднакъв брой комбинации.\n"
        "- Личният дневник не се отваря.\n"
        "- Не се изпълнява тежко преобучение на моделите.\n"
        "- Няма автоматично включване в реалните фишове, дори при положителен резултат.",
        "- The target draw is used for training only after scoring.\n"
        "- All strategies use the same number of combinations.\n"
        "- The personal journal is not opened.\n"
        "- Heavy model retraining is not performed.\n"
        "- There is no automatic inclusion in real tickets, even after a positive result.",
    ))

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
from src.v150_global_ui_polish import translate_value, ui_text


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


def _t(bg: str, en: str) -> str:
    return ui_text(bg, en, st)


def render_v146_controlled_neural_robustness_section() -> None:
    st.title(_t("Проверка за устойчивост на невронния модел", "Neural Model Robustness Check"))
    st.caption(
        _t(
            "Последователна историческа проверка с няколко начални стойности и периода, доверителни интервали и разширени базови модели.",
            "Multi-seed, multi-period walk-forward evaluation with confidence intervals, stability analysis and extended baselines.",
        )
    )
    st.warning(
        _t(
            "Това е исторически експеримент само за изследване. Няма връзка с работната верига или с реалните фишове.",
            "This is a research-only historical experiment. It is not connected to the production pipeline or real tickets.",
        )
    )

    summary = _load_json(SUMMARY_JSON_PATH)
    strategy = summary.get("strategy_summary", {}) or {}
    comparison = summary.get("comparison", {}) or {}
    split = summary.get("split_policy", {}) or {}

    neural = strategy.get("neural_dynamics_reservoir", {}) or {}
    frequency = strategy.get("frequency_walk_forward", {}) or {}
    recency = strategy.get("recency_weighted_walk_forward", {}) or {}
    random_mean = strategy.get("uniform_random_mean", {}) or {}
    metrics = st.columns(4)
    metrics[0].metric(_t("Невронен модел", "Neural model"), f"{float(neural.get('average_best_hits_mean', 0)):.4f}")
    metrics[1].metric(_t("Честотен модел", "Frequency model"), f"{float(frequency.get('average_best_hits_mean', 0)):.4f}")
    metrics[2].metric(_t("Модел на скорошната активност", "Recency model"), f"{float(recency.get('average_best_hits_mean', 0)):.4f}")
    metrics[3].metric(_t("Случаен модел", "Random model"), f"{float(random_mean.get('average_best_hits_mean', 0)):.4f}")
    secondary = st.columns(2)
    secondary[0].metric(_t("Независими изпълнения", "Independent runs"), int(split.get("run_count", 0)))
    gate_passed = bool(comparison.get("promotion_gate_passed"))
    secondary[1].metric(
        _t("Решение", "Decision"),
        _t("Допуснат", "Promoted") if gate_passed else _t("Не е допуснат", "Not promoted"),
    )

    st.info(translate_value(comparison.get("interpretation") or _t("Все още няма записан резултат.", "No result is available yet.")))

    if st.button(_t("Повтори официалната проверка за устойчивост", "Repeat the official robustness evaluation"), type="primary", use_container_width=True):
        with st.spinner(_t("Изпълняват се 15 контролирани исторически проверки...", "Running 15 controlled walk-forward evaluations...")):
            report = run_controlled_neural_robustness(write_outputs=True, register=True)
        st.session_state["v146_experiment"] = report
        st.success(_t(f"Експериментът е регистриран: {report['experiment']['experiment_id']}", f"Experiment registered: {report['experiment']['experiment_id']}"))
        summary = _load_json(SUMMARY_JSON_PATH)
        comparison = summary.get("comparison", {}) or {}

    st.markdown(_t("### Сравнение с базовите модели и 95% доверителни интервали", "### Baseline comparison and 95% confidence intervals"))
    baseline_rows = []
    for value in (comparison.get("baselines", {}) or {}).values():
        if not isinstance(value, dict):
            continue
        baseline_rows.append({
            key: item for key, item in value.items()
            if key not in {"seed_advantages", "fold_advantages"}
        })
    if baseline_rows:
        st.dataframe(pd.DataFrame(baseline_rows), use_container_width=True, hide_index=True)
    else:
        st.info(_t("Няма налична таблица за сравнение.", "No comparison table is available."))

    st.markdown(_t("### Стабилност по начална стойност", "### Stability by random seed"))
    seed_rows = _load_csv(SEED_STABILITY_CSV_PATH)
    if seed_rows:
        st.dataframe(pd.DataFrame(seed_rows), use_container_width=True, hide_index=True)

    st.markdown(_t("### Стабилност по исторически период", "### Stability by historical period"))
    fold_rows = _load_csv(FOLD_STABILITY_CSV_PATH)
    if fold_rows:
        st.dataframe(pd.DataFrame(fold_rows), use_container_width=True, hide_index=True)

    st.markdown(_t("### Условия за допускане", "### Promotion criteria"))
    requirements = comparison.get("promotion_requirements", {}) or {}
    for name, passed in requirements.items():
        st.markdown(f"- {'✅' if passed else '❌'} {translate_value(str(name))}")

    with st.expander(_t("Технически параметри на проверката", "Technical evaluation parameters"), expanded=False):
        st.json({"split_policy": split, "reproducibility": summary.get("reproducibility", {})})

    st.markdown(_t("### Защити", "### Safeguards"))
    st.markdown(_t(
        "- Три неприпокриващи се исторически периода за независима проверка.\n"
        "- Пет отделни начални стойности.\n"
        "- Всеки целеви тираж се добавя в обучението едва след оценяването му.\n"
        "- Използват се 95% доверителни интервали и свързани знакови тестове.\n"
        "- Личният дневник не се отваря и работната верига не се използва.\n"
        "- Дори преминатите условия не включват автоматично модела в реалните фишове.",
        "- Three non-overlapping historical evaluation periods.\n"
        "- Five separate random seeds.\n"
        "- Each target draw is added to training only after scoring.\n"
        "- 95% confidence intervals and paired sign tests are used.\n"
        "- The personal journal and production pipeline are not used.\n"
        "- Passing the criteria does not automatically include the model in real tickets.",
    ))

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
from src.v150_2_plain_language import plain_label, robustness_user_rows
from src.v150_global_ui_polish import current_language, translate_value, ui_text


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
    language = current_language(st)
    st.title(_t("Проверка за устойчивост на невронния модел", "Neural Model Robustness Check"))
    st.caption(
        _t(
            "Проверява дали резултатът се запазва при различни начални стойности и различни исторически периоди.",
            "Checks whether the result remains stable across different seeds and historical periods.",
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
        _t("Условията са изпълнени", "Criteria met") if gate_passed else _t("Не е допуснат", "Not promoted"),
    )

    if gate_passed:
        st.success(
            _t(
                "Всички условия за устойчивост са изпълнени. Това не включва автоматично модела в работната верига.",
                "All robustness criteria are met. This does not automatically connect the model to production.",
            )
        )
    else:
        st.info(
            _t(
                "Резултатът не е достатъчно устойчив при различните начални стойности и исторически периоди. Моделът остава само за изследване.",
                "The result is not sufficiently stable across seeds and historical periods. The model remains research-only.",
            )
        )

    if st.button(
        _t("Повтори официалната проверка за устойчивост", "Repeat the official robustness evaluation"),
        type="primary",
        use_container_width=True,
    ):
        with st.spinner(_t("Изпълняват се 15 контролирани исторически проверки...", "Running 15 controlled historical evaluations...")):
            run_controlled_neural_robustness(write_outputs=True, register=True)
        st.success(_t("Проверката е завършена и резултатите са обновени.", "The evaluation is complete and the results were updated."))
        summary = _load_json(SUMMARY_JSON_PATH)
        comparison = summary.get("comparison", {}) or {}

    st.markdown(_t("### Сравнение с базовите модели", "### Comparison with baseline models"))
    st.caption(
        _t(
            "Положителна средна разлика означава по-добър резултат на невронния модел. За допускане обаче е необходимо предимството да бъде устойчиво при всички проверки.",
            "A positive mean difference indicates a better neural result, but promotion requires the advantage to remain robust across all checks.",
        )
    )
    baselines = comparison.get("baselines", {}) or {}
    user_rows = robustness_user_rows(baselines, language=language)
    if user_rows:
        st.dataframe(pd.DataFrame(user_rows), use_container_width=True, hide_index=True)
    else:
        st.info(_t("Няма налични резултати за сравнение.", "No comparison results are available."))

    st.markdown(_t("### Условия за допускане", "### Promotion criteria"))
    st.caption(
        _t(
            "Всички условия трябва да бъдат изпълнени едновременно. Една непремината проверка е достатъчна моделът да остане само за изследване.",
            "All criteria must be met at the same time. One failed check is enough to keep the model research-only.",
        )
    )
    requirements = comparison.get("promotion_requirements", {}) or {}
    for name, passed in requirements.items():
        st.markdown(f"- {'✅' if passed else '❌'} {plain_label(name, language=language)}")

    with st.expander(_t("Статистически и технически подробности", "Statistical and technical details"), expanded=False):
        st.caption(
            _t(
                "Този раздел съдържа доверителни интервали, статистически проверки и резултати по отделни начални стойности и периоди.",
                "This section contains confidence intervals, statistical tests and results by seed and period.",
            )
        )
        baseline_rows = []
        for value in baselines.values():
            if isinstance(value, dict):
                baseline_rows.append({key: item for key, item in value.items() if key not in {"seed_advantages", "fold_advantages"}})
        if baseline_rows:
            st.dataframe(pd.DataFrame(baseline_rows), use_container_width=True, hide_index=True)

        seed_rows = _load_csv(SEED_STABILITY_CSV_PATH)
        if seed_rows:
            st.markdown(_t("#### Резултати по начални стойности", "#### Results by seed"))
            st.dataframe(pd.DataFrame(seed_rows), use_container_width=True, hide_index=True)

        fold_rows = _load_csv(FOLD_STABILITY_CSV_PATH)
        if fold_rows:
            st.markdown(_t("#### Резултати по исторически периоди", "#### Results by historical period"))
            st.dataframe(pd.DataFrame(fold_rows), use_container_width=True, hide_index=True)

        st.json({"split_policy": split, "reproducibility": summary.get("reproducibility", {})})

    st.markdown(_t("### Защити", "### Safeguards"))
    st.markdown(_t(
        "- Използват се три неприпокриващи се исторически периода.\n"
        "- Използват се пет отделни начални стойности.\n"
        "- Всеки целеви тираж се добавя към обучението едва след оценяването му.\n"
        "- Личният дневник и работната верига не се използват.\n"
        "- Дори положителен резултат не включва автоматично модела в реалните фишове.",
        "- Three non-overlapping historical periods are used.\n"
        "- Five separate seeds are used.\n"
        "- Each target draw is added to training only after scoring.\n"
        "- The personal journal and production pipeline are not used.\n"
        "- A positive result does not automatically include the model in real tickets.",
    ))

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.v144_reproducible_experiment_registry_engine import (
    DEFAULT_CONFIG,
    INDEX_CSV_PATH,
    SUMMARY_JSON_PATH,
    run_reproducible_baseline_experiment,
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


def render_v144_reproducible_experiment_registry_section() -> None:
    st.title(_t("Регистър на възпроизводимите експерименти", "Reproducible Experiment Registry"))
    st.caption(
        _t(
            "Заключва данните, конфигурацията, началната стойност, правилото за разделяне, кода, резултатите и създадените артефакти.",
            "Locks the dataset, configuration, random seed, split policy, code, results and generated artifacts.",
        )
    )
    st.warning(
        _t(
            "Това е лична експериментална лаборатория. Исторически резултат над случаен базов модел не доказва бъдеща предвидимост и не гарантира печалба.",
            "This is a personal experimental laboratory. A historical result above a random baseline does not prove future predictability or guarantee a win.",
        )
    )

    summary = _load_json(SUMMARY_JSON_PATH)
    dataset = summary.get("dataset", {}) or {}
    comparison = summary.get("comparison", {}) or {}
    frequency = summary.get("frequency_baseline", {}) or {}
    random_summary = summary.get("random_summary", {}) or {}

    metrics = st.columns(5)
    metrics[0].metric(_t("Регистрирани експерименти", "Registered experiments"), int(summary.get("registry_entries", 0)))
    metrics[1].metric(_t("Последен тираж в данните", "Latest draw in data"), str(dataset.get("latest_draw", "—")))
    metrics[2].metric(
        _t("Тиражи за независима проверка", "Independent evaluation draws"),
        int((summary.get("split_policy") or {}).get("holdout_draws", 0)),
    )
    metrics[3].metric(
        _t("Среден резултат — честотен модел", "Average result — frequency model"),
        f"{float(frequency.get('average_best_hits', 0)):.4f}",
    )
    metrics[4].metric(
        _t("Среден резултат — случаен модел", "Average result — random model"),
        f"{float(random_summary.get('average_best_hits_mean', 0)):.4f}",
    )

    with st.expander(_t("Нова възпроизводима проверка", "New reproducible evaluation"), expanded=False):
        col1, col2, col3 = st.columns(3)
        holdout = col1.number_input(
            _t("Тиражи за независима проверка", "Independent evaluation draws"),
            30,
            2000,
            int(DEFAULT_CONFIG["holdout_draws"]),
            10,
        )
        training = col2.number_input(
            _t("Минимални обучаващи тиражи", "Minimum training draws"),
            100,
            9000,
            int(DEFAULT_CONFIG["minimum_training_draws"]),
            100,
        )
        package_size = col3.number_input(
            _t("Комбинации в пакет", "Combinations per package"),
            1,
            100,
            int(DEFAULT_CONFIG["package_size"]),
            1,
        )
        col4, col5, col6 = st.columns(3)
        trials = col4.number_input(
            _t("Опити със случаен базов модел", "Random baseline trials"),
            1,
            1000,
            int(DEFAULT_CONFIG["random_trials"]),
            10,
        )
        pool = col5.number_input(
            _t("Размер на честотния набор", "Frequency pool size"),
            6,
            49,
            int(DEFAULT_CONFIG["frequency_pool_size"]),
            1,
        )
        seed = col6.number_input(
            _t("Начална стойност за повторяемост", "Random seed"),
            0,
            2_147_483_647,
            int(DEFAULT_CONFIG["seed"]),
            1,
        )

        if st.button(
            _t("Изпълни и регистрирай проверката", "Run and register evaluation"),
            type="primary",
            use_container_width=True,
        ):
            with st.spinner(
                _t(
                    "Изпълнява се последователната историческа проверка...",
                    "Running the walk-forward baseline evaluation...",
                )
            ):
                report = run_reproducible_baseline_experiment(
                    holdout_draws=int(holdout),
                    minimum_training_draws=int(training),
                    package_size=int(package_size),
                    random_trials=int(trials),
                    frequency_pool_size=int(pool),
                    seed=int(seed),
                    write_outputs=True,
                    register=True,
                )
            st.session_state["v144_experiment"] = report
            st.success(
                _t(
                    f"Експериментът е регистриран: {report['experiment']['experiment_id']}",
                    f"Experiment registered: {report['experiment']['experiment_id']}",
                )
            )
            summary = _load_json(SUMMARY_JSON_PATH)

    st.markdown(_t("### Последен резултат", "### Latest result"))
    interpretation = comparison.get("interpretation", "Няма изпълнен експеримент с базови модели.")
    st.write(translate_value(str(interpretation)))

    with st.expander(
        _t("Технически подробности и криптографски подписи", "Technical details and cryptographic signatures"),
        expanded=False,
    ):
        st.caption(
            _t(
                "Тези стойности са предназначени за възпроизводимост и одит, а не за ежедневна работа.",
                "These values are intended for reproducibility and audit, not for everyday use.",
            )
        )
        st.code(
            "\n".join(
                [
                    f"dataset_sha256 = {dataset.get('sha256', '—')}",
                    f"configuration_sha256 = {(summary.get('reproducibility') or {}).get('configuration_sha256', '—')}",
                    f"result_signature_sha256 = {(summary.get('reproducibility') or {}).get('result_signature_sha256', '—')}",
                ]
            )
        )

    rows = _load_csv(INDEX_CSV_PATH)
    st.markdown(_t("### Регистър", "### Registry"))
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info(_t("Все още няма регистрирани експерименти.", "No experiments have been registered yet."))

    st.markdown(_t("### Методологични защити", "### Methodological safeguards"))
    st.markdown(
        _t(
            "- Разширяващ се прозорец за последователна историческа проверка.\n"
            "- Всеки целеви тираж влиза в историята едва след оценяването му.\n"
            "- Еднакви данни, код, конфигурация и начална стойност дават еднакъв подпис на резултата.\n"
            "- Личният дневник не се използва.\n"
            "- Тежко преобучение на моделите не се изпълнява.",
            "- Expanding walk-forward evaluation window.\n"
            "- Each target draw enters the history only after it is scored.\n"
            "- Identical data, code, configuration and seed produce the same result signature.\n"
            "- The personal journal is not used.\n"
            "- Heavy model retraining is not performed.",
        )
    )

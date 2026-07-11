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


def render_v144_reproducible_experiment_registry_section() -> None:
    st.title("Регистър на възпроизводимите експерименти")
    st.caption("Step 144 — заключва dataset hash, configuration, seed, split policy, code hash, резултати и създадени artifacts.")
    st.warning(
        "Това е лична експериментална лаборатория. Исторически резултат над случаен baseline не доказва бъдеща предвидимост и не гарантира печалба."
    )

    summary = _load_json(SUMMARY_JSON_PATH)
    dataset = summary.get("dataset", {}) or {}
    comparison = summary.get("comparison", {}) or {}
    frequency = summary.get("frequency_baseline", {}) or {}
    random_summary = summary.get("random_summary", {}) or {}

    metrics = st.columns(5)
    metrics[0].metric("Регистрирани експерименти", int(summary.get("registry_entries", 0)))
    metrics[1].metric("Последен dataset тираж", str(dataset.get("latest_draw", "—")))
    metrics[2].metric("Holdout тиражи", int((summary.get("split_policy") or {}).get("holdout_draws", 0)))
    metrics[3].metric("Frequency средно", f"{float(frequency.get('average_best_hits', 0)):.4f}")
    metrics[4].metric("Random средно", f"{float(random_summary.get('average_best_hits_mean', 0)):.4f}")

    with st.expander("Конфигурация за ново възпроизводимо изпълнение", expanded=False):
        col1, col2, col3 = st.columns(3)
        holdout = col1.number_input("Holdout тиражи", 30, 2000, int(DEFAULT_CONFIG["holdout_draws"]), 10)
        training = col2.number_input("Минимални обучаващи тиражи", 100, 9000, int(DEFAULT_CONFIG["minimum_training_draws"]), 100)
        package_size = col3.number_input("Комбинации в пакет", 1, 100, int(DEFAULT_CONFIG["package_size"]), 1)
        col4, col5, col6 = st.columns(3)
        trials = col4.number_input("Случайни baseline опити", 1, 1000, int(DEFAULT_CONFIG["random_trials"]), 10)
        pool = col5.number_input("Frequency pool", 6, 49, int(DEFAULT_CONFIG["frequency_pool_size"]), 1)
        seed = col6.number_input("Random seed", 0, 2_147_483_647, int(DEFAULT_CONFIG["seed"]), 1)

        if st.button("Изпълни и регистрирай експеримента", type="primary", use_container_width=True):
            with st.spinner("Изпълнява се walk-forward baseline лабораторията..."):
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
            st.success(f"Експериментът е регистриран: {report['experiment']['experiment_id']}")
            summary = _load_json(SUMMARY_JSON_PATH)

    st.markdown("### Последен резултат")
    st.write(str(comparison.get("interpretation", "Няма изпълнен baseline експеримент.")))
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
    st.markdown("### Регистър")
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Все още няма регистрирани експерименти.")

    st.markdown("### Методологични защити")
    st.markdown(
        "- Разширяващ се walk-forward прозорец.\n"
        "- Всеки target тираж влиза в историята едва след оценяването му.\n"
        "- Един и същ dataset hash, code hash, configuration и seed дават същия result signature.\n"
        "- Личният дневник не се използва.\n"
        "- Тежко ML преобучение не се изпълнява."
    )

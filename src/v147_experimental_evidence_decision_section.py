from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.v147_experimental_evidence_decision_engine import (
    EVIDENCE_MATRIX_CSV_PATH,
    SUMMARY_JSON_PATH,
    run_experimental_evidence_decision,
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


def render_v147_experimental_evidence_decision_section() -> None:
    st.title("Research decision gate")
    st.caption("Step 147 — обединена оценка на доказателствата от Step 144–146 и формално решение за neural посоката.")
    st.warning(
        "Този екран не прогнозира тиражи и не създава фишове. Той управлява само research решенията и защитава production слоя."
    )

    summary = _load_json(SUMMARY_JSON_PATH)
    synthesis = summary.get("synthesis", {}) or {}
    decision = summary.get("decision", {}) or {}
    gate = summary.get("decision_gate", {}) or {}

    metrics = st.columns(6)
    metrics[0].metric("Експерименти", int(synthesis.get("source_experiments", 0)))
    metrics[1].metric("Evidence редове", int(synthesis.get("evidence_rows", 0)))
    metrics[2].metric("Robust positive", int(synthesis.get("robust_positive_rows", 0)))
    metrics[3].metric("Robust negative", int(synthesis.get("robust_negative_rows", 0)))
    metrics[4].metric("Production", str(decision.get("production_promotion", "unknown")).upper())
    metrics[5].metric("Neural config", str(decision.get("current_neural_configuration", "unknown")).upper())

    st.info(str(decision.get("reason", "Все още няма записано Step 147 решение.")))

    if st.button("Преизчисли research решението", type="primary", use_container_width=True):
        report = run_experimental_evidence_decision(write_outputs=True)
        st.success(f"Research decision е обновено: {report['decision_id']}")
        summary = _load_json(SUMMARY_JSON_PATH)
        gate = summary.get("decision_gate", {}) or {}

    st.markdown("### Decision gate")
    for name, passed in gate.items():
        st.markdown(f"- {'✅' if passed else '❌'} `{name}`")

    st.markdown("### Обединена evidence матрица")
    rows = _load_csv(EVIDENCE_MATRIX_CSV_PATH)
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Няма налична Step 147 evidence матрица.")

    st.markdown("### Разрешена следваща research посока")
    requirements = ((summary.get("policy") or {}).get("next_experiment_requirements") or [])
    for item in requirements:
        st.markdown(f"- `{item}`")

    st.markdown("### Защити")
    st.markdown(
        "- Същата neural конфигурация не се дооптимизира върху вече видените holdout периоди.\n"
        "- Production promotion остава блокиран без robust superiority.\n"
        "- Личният дневник, реалните фишове и production pipeline не се използват.\n"
        "- Отрицателните резултати се пазят като валидно експериментално доказателство."
    )

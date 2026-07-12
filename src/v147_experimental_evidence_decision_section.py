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


def render_v147_experimental_evidence_decision_section() -> None:
    st.title(_t("Решение за изследователските модели", "Research Model Decision"))
    st.caption(
        _t(
            "Обединява доказателствата от предишните експерименти и формализира решението за невронната посока.",
            "Combines evidence from the preceding experiments and formalizes the decision for the neural direction.",
        )
    )
    st.warning(
        _t(
            "Този екран не прогнозира тиражи и не създава фишове. Той управлява само изследователските решения и защитава работния слой.",
            "This screen does not predict draws or create tickets. It manages research decisions only and protects the production layer.",
        )
    )

    summary = _load_json(SUMMARY_JSON_PATH)
    synthesis = summary.get("synthesis", {}) or {}
    decision = summary.get("decision", {}) or {}
    gate = summary.get("decision_gate", {}) or {}

    metrics = st.columns(6)
    metrics[0].metric(_t("Експерименти", "Experiments"), int(synthesis.get("source_experiments", 0)))
    metrics[1].metric(_t("Сравнения с доказателства", "Evidence comparisons"), int(synthesis.get("evidence_rows", 0)))
    metrics[2].metric(_t("Устойчиво положителни", "Robust positive"), int(synthesis.get("robust_positive_rows", 0)))
    metrics[3].metric(_t("Устойчиво отрицателни", "Robust negative"), int(synthesis.get("robust_negative_rows", 0)))
    metrics[4].metric(_t("Работен режим", "Production"), translate_value(str(decision.get("production_promotion", "unknown"))).upper())
    metrics[5].metric(_t("Невронна конфигурация", "Neural configuration"), translate_value(str(decision.get("current_neural_configuration", "unknown"))).upper())

    st.info(translate_value(str(decision.get("reason", _t("Все още няма записано решение.", "No decision has been recorded yet.")))))

    if st.button(_t("Преизчисли изследователското решение", "Recalculate research decision"), type="primary", use_container_width=True):
        report = run_experimental_evidence_decision(write_outputs=True)
        st.success(_t(f"Решението е обновено: {report['decision_id']}", f"Decision updated: {report['decision_id']}"))
        summary = _load_json(SUMMARY_JSON_PATH)
        gate = summary.get("decision_gate", {}) or {}

    st.markdown(_t("### Условия за решение", "### Decision criteria"))
    for name, passed in gate.items():
        st.markdown(f"- {'✅' if passed else '❌'} {translate_value(str(name))}")

    st.markdown(_t("### Обединена матрица на доказателствата", "### Combined evidence matrix"))
    rows = _load_csv(EVIDENCE_MATRIX_CSV_PATH)
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info(_t("Няма налична матрица на доказателствата.", "No evidence matrix is available."))

    st.markdown(_t("### Допустима следваща изследователска посока", "### Permitted next research direction"))
    requirements = ((summary.get("policy") or {}).get("next_experiment_requirements") or [])
    for item in requirements:
        st.markdown(f"- {translate_value(str(item))}")

    with st.expander(_t("Технически подробности за решението", "Technical decision details"), expanded=False):
        st.json({
            "decision_id": summary.get("decision_id"),
            "result_signature_sha256": summary.get("result_signature_sha256"),
            "source_experiment_signatures": summary.get("source_experiment_signatures"),
        })

    st.markdown(_t("### Защити", "### Safeguards"))
    st.markdown(_t(
        "- Същата невронна конфигурация не се дооптимизира върху вече използваните периоди за независима проверка.\n"
        "- Допускането до работния режим остава блокирано без устойчиво превъзходство.\n"
        "- Личният дневник, реалните фишове и работната верига не се използват.\n"
        "- Отрицателните резултати се пазят като валидно експериментално доказателство.",
        "- The same neural configuration is not further tuned on already-used evaluation periods.\n"
        "- Production promotion remains blocked without robust superiority.\n"
        "- The personal journal, real tickets and production pipeline are not used.\n"
        "- Negative results are preserved as valid experimental evidence.",
    ))

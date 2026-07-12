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
from src.v150_2_plain_language import (
    decision_reason_text,
    decision_value_text,
    evidence_user_rows,
    plain_label,
    requirement_text,
)
from src.v150_global_ui_polish import current_language, ui_text


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
    language = current_language(st)
    st.title(_t("Решение за изследователските модели", "Research Model Decision"))
    st.caption(
        _t(
            "Обединява резултатите от предишните експерименти и показва на разбираем език дали невронният модел може да продължи към работна употреба.",
            "Combines the previous experiment results and explains whether the neural model may proceed toward production use.",
        )
    )
    st.warning(
        _t(
            "Тази страница не прогнозира тиражи и не създава фишове. Тя служи само за безопасно изследователско решение.",
            "This page does not predict draws or create tickets. It is used only for a safe research decision.",
        )
    )

    summary = _load_json(SUMMARY_JSON_PATH)
    synthesis = summary.get("synthesis", {}) or {}
    decision = summary.get("decision", {}) or {}
    gate = summary.get("decision_gate", {}) or {}

    metrics = st.columns(5)
    metrics[0].metric(_t("Използвани експерименти", "Experiments used"), int(synthesis.get("source_experiments", 0)))
    metrics[1].metric(_t("Направени сравнения", "Comparisons"), int(synthesis.get("evidence_rows", 0)))
    metrics[2].metric(_t("Устойчиво положителни", "Robust positive"), int(synthesis.get("robust_positive_rows", 0)))
    metrics[3].metric(
        _t("Решение за работна употреба", "Production decision"),
        decision_value_text(decision.get("production_promotion", "blocked"), language=language),
    )
    metrics[4].metric(
        _t("Текущ невронен модел", "Current neural model"),
        decision_value_text(decision.get("current_neural_configuration", "pause_and_archive"), language=language),
    )

    st.info(decision_reason_text(decision, language=language))

    if st.button(
        _t("Преизчисли изследователското решение", "Recalculate research decision"),
        type="primary",
        use_container_width=True,
    ):
        run_experimental_evidence_decision(write_outputs=True)
        st.success(_t("Решението е обновено успешно.", "The decision was updated successfully."))
        summary = _load_json(SUMMARY_JSON_PATH)
        gate = summary.get("decision_gate", {}) or {}

    st.markdown(_t("### Условия за решение", "### Decision criteria"))
    st.caption(
        _t(
            "Зелена отметка означава, че условието е изпълнено. Червен знак означава, че условието все още не е изпълнено.",
            "A green check means the criterion is met. A red mark means it is not yet met.",
        )
    )
    for name, passed in gate.items():
        st.markdown(f"- {'✅' if passed else '❌'} {plain_label(name, language=language)}")

    st.markdown(_t("### Обобщение на доказателствата", "### Evidence summary"))
    rows = _load_csv(EVIDENCE_MATRIX_CSV_PATH)
    if rows:
        st.dataframe(pd.DataFrame(evidence_user_rows(rows, language=language)), use_container_width=True, hide_index=True)
    else:
        st.info(_t("Все още няма налични сравнения.", "No comparisons are available yet."))

    with st.expander(
        _t("Статистически и технически подробности", "Statistical and technical details"),
        expanded=False,
    ):
        st.caption(
            _t(
                "Тук са пълните статистически полета, идентификаторите и контролните стойности. Те не са необходими за ежедневното използване на приложението.",
                "This section contains full statistical fields, identifiers and control values. They are not needed for everyday use.",
            )
        )
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.json({
            "decision_id": summary.get("decision_id"),
            "result_signature_sha256": summary.get("result_signature_sha256"),
            "source_experiment_signatures": summary.get("source_experiment_signatures"),
        })

    st.markdown(_t("### Допустима следваща изследователска посока", "### Permitted next research direction"))
    st.caption(
        _t(
            "Следващ експеримент е допустим само ако изпълнява всички условия по-долу.",
            "A new experiment is permitted only when all requirements below are met.",
        )
    )
    requirements = ((summary.get("policy") or {}).get("next_experiment_requirements") or [])
    for item in requirements:
        st.markdown(f"- {requirement_text(item, language=language)}")

    st.markdown(_t("### Защити", "### Safeguards"))
    st.markdown(_t(
        "- Същият невронен модел не се донастройва върху вече използваните периоди.\n"
        "- Включването в работния режим остава блокирано без доказано устойчиво превъзходство.\n"
        "- Личният дневник, реалните фишове и работната верига не се използват.\n"
        "- Отрицателните резултати се пазят като валидно експериментално доказателство.",
        "- The same neural model is not tuned again on already-used evaluation periods.\n"
        "- Production promotion remains blocked without robust superiority.\n"
        "- The personal journal, real tickets and production pipeline are not used.\n"
        "- Negative results are preserved as valid experimental evidence.",
    ))

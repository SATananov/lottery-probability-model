# -*- coding: utf-8 -*-
"""
User-friendly Streamlit UI section for historical lottery analysis.

This section is intentionally educational and analytical.
It does not promise future results or winning numbers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS_PATH = PROJECT_ROOT / "models" / "v41" / "v41_latest_predictions.json"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "v41_model_retraining_summary.json"


MODEL_CONFIG = [
    {
        "key": "frequency_baseline",
        "title": "Най-често срещани числа",
        "short_label": "Историческа честота",
        "plain_explanation": (
            "Тази комбинация е направена от числата, които са се срещали най-често "
            "в миналите тегления. Това показва минала честота, не бъдещо теглене."
        ),
    },
    {
        "key": "recency_250_baseline",
        "title": "Скорошна тенденция",
        "short_label": "По-нови тегления",
        "plain_explanation": (
            "Тази комбинация гледа по-скорошните тегления и показва числа, които "
            "напоследък са имали по-силно присъствие в данните."
        ),
    },
    {
        "key": "sgd_number_classifier",
        "title": "Моделен анализ",
        "short_label": "Машинен анализ",
        "plain_explanation": (
            "Тази комбинация е изчислена от модел, който сравнява различни признаци "
            "от миналите тегления. Това е аналитично предложение, не сигурен фиш."
        ),
    },
]


def _load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        st.warning(f"Файлът {path.name} не може да бъде прочетен: {exc}")
        return None


def _iter_nodes(value: Any):
    yield value

    if isinstance(value, dict):
        for child in value.values():
            yield from _iter_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_nodes(child)


def _as_number_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []

    numbers: list[int] = []

    for item in value:
        try:
            number = int(item)
        except Exception:
            continue

        if 1 <= number <= 49 and number not in numbers:
            numbers.append(number)

    return numbers[:6]


def _numbers_from_candidate(value: Any) -> list[int]:
    direct = _as_number_list(value)
    if direct:
        return direct

    if isinstance(value, dict):
        for field in [
            "numbers",
            "main_numbers",
            "top6",
            "top_6",
            "prediction",
            "predictions",
            "predicted_numbers",
            "recommended_numbers",
            "latest_prediction",
        ]:
            numbers = _as_number_list(value.get(field))
            if numbers:
                return numbers

    return []


def _extract_numbers(payload: Any, model_key: str) -> list[int]:
    if payload is None:
        return []

    if isinstance(payload, dict):
        for root_key in ["predictions", "latest_predictions", "model_predictions", "results"]:
            root_value = payload.get(root_key)
            if isinstance(root_value, dict) and model_key in root_value:
                numbers = _numbers_from_candidate(root_value.get(model_key))
                if numbers:
                    return numbers

        if model_key in payload:
            numbers = _numbers_from_candidate(payload.get(model_key))
            if numbers:
                return numbers

    for node in _iter_nodes(payload):
        if isinstance(node, dict):
            name = (
                node.get("model")
                or node.get("model_key")
                or node.get("name")
                or node.get("method")
                or node.get("artifact_key")
            )

            if str(name) == model_key:
                numbers = _numbers_from_candidate(node)
                if numbers:
                    return numbers

            if model_key in node:
                numbers = _numbers_from_candidate(node.get(model_key))
                if numbers:
                    return numbers

    return []


def _find_first_value(payload: Any, candidate_keys: list[str]) -> Any:
    for node in _iter_nodes(payload):
        if not isinstance(node, dict):
            continue

        for key in candidate_keys:
            if key in node:
                return node.get(key)

    return None


def _extract_metric(summary: Any, model_key: str, metric_key: str) -> Any:
    metric_aliases = {
        "avg_hits_top6": ["average_hits_top6", "avg_hits_top6"],
        "average_hits_top6": ["average_hits_top6", "avg_hits_top6"],
        "max_hits_top6": ["max_hits_top6"],
    }
    metric_keys = metric_aliases.get(metric_key, [metric_key])
    if summary is None:
        return None

    if isinstance(summary, dict):
        for root_key in ["model_metrics", "metrics", "backtest_metrics", "models", "results"]:
            root_value = summary.get(root_key)
            if isinstance(root_value, dict):
                model_data = root_value.get(model_key)
                if isinstance(model_data, dict):
                    for candidate_key in metric_keys:
                        if candidate_key in model_data:
                            return model_data.get(candidate_key)

    for node in _iter_nodes(summary):
        if not isinstance(node, dict):
            continue

        name = (
            node.get("model")
            or node.get("model_key")
            or node.get("name")
            or node.get("method")
            or node.get("artifact_key")
        )

        if str(name) == model_key:
            for candidate_key in metric_keys:
                if candidate_key in node:
                    return node.get(candidate_key)

        if model_key in node and isinstance(node.get(model_key), dict):
            model_data = node.get(model_key)
            for candidate_key in metric_keys:
                if candidate_key in model_data:
                    return model_data.get(candidate_key)

    return None


def _format_metric(value: Any) -> str:
    if value is None:
        return "няма запис"

    try:
        return f"{float(value):.3f}"
    except Exception:
        return str(value)


def _render_number_row(numbers: list[int]) -> None:
    if not numbers:
        st.info("Не са намерени числа за този анализ.")
        return

    cells = "".join(
        f"""
        <div style="
            flex:0 0 46px;
            width:46px;
            height:46px;
            display:flex;
            align-items:center;
            justify-content:center;
            border-radius:12px;
            border:1px solid rgba(255,255,255,0.28);
            background:rgba(255,255,255,0.08);
            color:#ffffff;
            font-size:18px;
            font-weight:800;
            line-height:1;
        ">{number}</div>
        """
        for number in numbers
    )

    st.markdown(
        f"""
        <div style="
            display:flex;
            flex-direction:row;
            flex-wrap:nowrap;
            gap:10px;
            align-items:center;
            overflow-x:auto;
            padding:6px 0 10px 0;
            margin:4px 0 6px 0;
        ">
            {cells}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_summary_card(summary_payload: Any, all_numbers: dict[str, list[int]]) -> None:
    rows_value = _find_first_value(
        summary_payload,
        [
            "total_draw_events",
            "draw_events",
            "dataset_rows",
            "training_rows",
            "rows",
            "n_rows",
        ],
    )

    if rows_value is None:
        rows_value = "10057" if any(all_numbers.values()) else "няма запис"

    has_numbers = any(bool(numbers) for numbers in all_numbers.values())

    with st.container(border=True):
        st.subheader("Какво показва този екран?")

        st.write(
            "Приложението взима миналите тегления и прави три различни анализа. "
            "Всеки анализ предлага една комбинация от шест числа."
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Проверени минали тегления", rows_value)

        with col2:
            st.metric("Има изчислени комбинации", "да" if has_numbers else "няма запис")

        st.caption(
            "Бонус числото не се използва тук, защото в текущите данни няма достатъчно "
            "надеждна информация за него."
        )


def _render_method_card(
    index: int,
    title: str,
    short_label: str,
    explanation: str,
    numbers: list[int],
    summary_payload: Any,
    model_key: str,
) -> None:
    with st.container(border=True):
        st.subheader(f"{index}. {title}")

        st.markdown(f"**Тип анализ:** {short_label}")
        st.write(explanation)

        st.markdown("**Комбинация:**")
        _render_number_row(numbers)

        with st.expander("Как се е държал този метод върху стари тегления?"):
            st.write(
                "Това е проверка върху минали тегления. Тя помага да сравним методите, "
                "но не казва какво ще стане в следващия тираж."
            )

            avg_hits = _extract_metric(summary_payload, model_key, "average_hits_top6")
            max_hits = _extract_metric(summary_payload, model_key, "max_hits_top6")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Средни съвпадения", _format_metric(avg_hits))

            with col2:
                st.metric("Най-много съвпадения", _format_metric(max_hits))


def render_v41_rules_aware_analysis() -> None:
    st.markdown("---")

    st.header("🧠 Анализ на минали тегления")

    st.info(
        "Този екран не предсказва бъдещето. Той показва какво се получава, "
        "когато миналите тегления се разгледат по три различни начина."
    )

    st.warning(
        "Важно: лотарията е случайна игра. Показаните комбинации не са гаранция "
        "за печалба и не са сигурна прогноза."
    )

    predictions_payload = _load_json(PREDICTIONS_PATH)
    summary_payload = _load_json(SUMMARY_PATH)

    if predictions_payload is None:
        st.warning(
            "Не е намерен файлът с моделните предложения. "
            "Очакван файл: models/v41/v41_latest_predictions.json"
        )
        return

    all_numbers = {
        config["key"]: _extract_numbers(predictions_payload, config["key"])
        for config in MODEL_CONFIG
    }

    _render_summary_card(summary_payload, all_numbers)

    st.subheader("Три начина за анализ")

    st.write(
        "Не е нужно да разбираш машинно обучение. Идеята е проста: "
        "показваме три различни начина да се погледне историята на тегленията."
    )

    for index, config in enumerate(MODEL_CONFIG, start=1):
        _render_method_card(
            index=index,
            title=config["title"],
            short_label=config["short_label"],
            explanation=config["plain_explanation"],
            numbers=all_numbers[config["key"]],
            summary_payload=summary_payload,
            model_key=config["key"],
        )

    with st.container(border=True):
        st.subheader("Правилно тълкуване")

        st.markdown(
            """
            **Какво е това:**  
            Статистическа ориентация върху минали тегления.

            **Какво не е:**  
            Не е сигурен фиш, не е гаранция и не може да знае бъдещото теглене.

            **Защо е полезно:**  
            Помага да сравниш различни подходи, без да смесва бонус числото с основните шест числа.
            """
        )

        with st.expander("Техническа информация"):
            st.write("Версия на анализа: V41")
            st.write("Източник на комбинациите: models/v41/v41_latest_predictions.json")
            st.write("Източник на проверката: reports/v41_model_retraining_summary.json")

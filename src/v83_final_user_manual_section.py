from __future__ import annotations

from pathlib import Path
import csv
import json
from typing import Any

import streamlit as st

from src.v83_final_user_manual_engine import build_final_user_manual_center

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"

SUMMARY_JSON = REPORTS_DIR / "v83_final_user_manual_summary.json"
GUIDE_SECTIONS_CSV = REPORTS_DIR / "v83_app_guide_sections.csv"
WORKFLOW_CSV = REPORTS_DIR / "v83_recommended_workflow.csv"
SAFE_CHECKLIST_CSV = REPORTS_DIR / "v83_safe_usage_checklist.csv"

COLUMN_LABELS_BG = {
    "section_order": "Ред",
    "section": "Раздел",
    "purpose": "Предназначение",
    "user_action": "Действие за потребителя",
    "safe_note": "Важно уточнение",
    "step_order": "Ред",
    "page": "Страница",
    "when_to_use": "Кога се използва",
    "expected_result": "Очакван резултат",
    "caution": "Внимание",
    "check_order": "Ред",
    "check_item": "Проверка",
    "recommended_behavior": "Препоръчително поведение",
    "risk_if_ignored": "Риск при игнориране",
}

ORDER_GUIDE = [
    "Ред",
    "Раздел",
    "Предназначение",
    "Действие за потребителя",
    "Важно уточнение",
]

ORDER_WORKFLOW = [
    "Ред",
    "Страница",
    "Кога се използва",
    "Очакван резултат",
    "Внимание",
]

ORDER_SAFE = [
    "Ред",
    "Проверка",
    "Препоръчително поведение",
    "Риск при игнориране",
]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _translate_rows(rows: list[dict[str, str]], preferred_order: list[str]) -> list[dict[str, str]]:
    translated: list[dict[str, str]] = []

    for row in rows:
        translated_row = {
            COLUMN_LABELS_BG.get(str(key), str(key)): value
            for key, value in row.items()
        }

        ordered_row: dict[str, str] = {}
        for key in preferred_order:
            if key in translated_row:
                ordered_row[key] = translated_row[key]

        for key, value in translated_row.items():
            if key not in ordered_row:
                ordered_row[key] = value

        translated.append(ordered_row)

    return translated


def _show_table(title: str, rows: list[dict[str, str]], preferred_order: list[str]) -> None:
    st.subheader(title)

    if not rows:
        st.info("Няма налични редове за показване.")
        return

    st.dataframe(
        _translate_rows(rows, preferred_order),
        use_container_width=True,
        hide_index=True,
    )


def render_v83_final_user_manual_section() -> None:
    st.title("Ръководство за апа")
    st.caption("Финално потребителско ръководство, последователност на работа и безопасно използване.")

    st.warning(
        "Този модул е помощно ръководство. Приложението прави статистически анализ, "
        "не предсказва сигурно бъдещи тиражи и не гарантира печалба."
    )

    if st.button("Обнови ръководството"):
        with st.spinner("Обновяване на ръководството и контролните списъци..."):
            summary = build_final_user_manual_center()

        if summary.get("status") == "OK":
            st.success("Ръководството е обновено успешно.")
        else:
            st.warning("Ръководството намери елементи за преглед.")

    summary = _load_json(SUMMARY_JSON)
    if not summary:
        summary = build_final_user_manual_center()

    cols = st.columns(4)
    cols[0].metric("Статус", str(summary.get("status", "-")))
    cols[1].metric("Редове в данните", int(summary.get("dataset_rows", 0)))
    cols[2].metric("Стъпки в работата", int(summary.get("workflow_steps_count", 0)))
    cols[3].metric("Контролни точки", int(summary.get("safe_checklist_count", 0)))

    st.markdown("### Основна идея")
    st.markdown(
        "Това приложение е статистически помощник за 6/49. То събира исторически данни, "
        "анализира модели, оценява комбинации, подготвя портфолио и помага за дисциплиниран финален план. "
        "**Не е система за сигурна печалба.**"
    )

    st.markdown("### Последно състояние")
    st.write(f"Последен тираж в данните: **{summary.get('latest_draw_date', '-')}**")
    st.write(f"Последни числа: **{summary.get('latest_numbers', '-')}**")
    st.write(f"Статус на финалния пакет: **{summary.get('v82_release_status', '-')}**")
    st.write(f"Статус на навигацията: **{summary.get('v81_ux_status', '-')}**")

    issues = summary.get("issues_preview") or []
    if issues:
        st.error("Има елементи за преглед:")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.success("Ръководството е синхронизирано и готово за използване.")

    _show_table(
        "Раздели в ръководството",
        _load_rows(GUIDE_SECTIONS_CSV),
        ORDER_GUIDE,
    )

    _show_table(
        "Препоръчителна последователност",
        _load_rows(WORKFLOW_CSV),
        ORDER_WORKFLOW,
    )

    _show_table(
        "Контролен списък за безопасно използване",
        _load_rows(SAFE_CHECKLIST_CSV),
        ORDER_SAFE,
    )

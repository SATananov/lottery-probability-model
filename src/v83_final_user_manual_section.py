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


def _show_rows(title: str, rows: list[dict[str, str]]) -> None:
    st.subheader(title)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("Няма налични редове за показване.")


def render_v83_final_user_manual_section() -> None:
    st.title("Ръководство за апа")
    st.caption("Step 83 — финално потребителско ръководство и безопасен workflow.")
    st.warning(
        "Този модул е помощно ръководство. Приложението прави статистически анализ, "
        "не предсказва сигурно бъдещи тиражи и не гарантира печалба."
    )

    if st.button("Обнови ръководството"):
        with st.spinner("Обновяване на ръководството и workflow checklist..."):
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
    cols[1].metric("Dataset редове", int(summary.get("dataset_rows", 0)))
    cols[2].metric("Workflow стъпки", int(summary.get("workflow_steps_count", 0)))
    cols[3].metric("Safe точки", int(summary.get("safe_checklist_count", 0)))

    st.markdown("### Основна идея")
    st.markdown(
        "Това приложение е статистически помощник за 6/49. То събира исторически данни, "
        "анализира модели, оценява комбинации, подготвя портфолио и помага за дисциплиниран финален план. "
        "**Не е система за сигурна печалба.**"
    )

    st.markdown("### Последно състояние")
    st.write(f"Последен тираж в dataset-а: **{summary.get('latest_draw_date', '-')}**")
    st.write(f"Последни числа: **{summary.get('latest_numbers', '-')}**")
    st.write(f"Step 82 release статус: **{summary.get('v82_release_status', '-')}**")
    st.write(f"Step 81 UX статус: **{summary.get('v81_ux_status', '-')}**")

    issues = summary.get("issues_preview") or []
    if issues:
        st.error("Има елементи за преглед:")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.success("Ръководството е синхронизирано и готово за използване.")

    _show_rows("Раздели в ръководството", _load_rows(GUIDE_SECTIONS_CSV))
    _show_rows("Препоръчителен workflow", _load_rows(WORKFLOW_CSV))
    _show_rows("Safe usage checklist", _load_rows(SAFE_CHECKLIST_CSV))

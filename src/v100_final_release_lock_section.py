from __future__ import annotations

import csv
import io
from typing import Any

import pandas as pd
import streamlit as st
from src.v110_user_friendly_ui_helpers import friendly_status, polish_dataframe

from src.v100_final_release_lock_engine import (
    CHECKLIST_CSV_PATH,
    MANIFEST_CSV_PATH,
    SAFE_NOTE_BG,
    build_and_save,
    load_final_release_lock,
)

CHECKLIST_LABELS = {
    "area_bg": "Област",
    "check_bg": "Проверка",
    "status": "Статус",
    "blocking": "Блокираща",
    "details_bg": "Детайл",
}

MANIFEST_LABELS = {
    "artifact_type": "Тип",
    "path": "Път",
    "status": "Статус",
    "note_bg": "Бележка",
}


def _read_rows(path: Any) -> list[dict[str, str]]:
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            return [dict(row) for row in csv.DictReader(f)]
    except Exception:
        return []


def _rename_rows(rows: list[dict[str, Any]], labels: dict[str, str]) -> pd.DataFrame:
    return pd.DataFrame([{labels.get(key, key): value for key, value in row.items()} for row in rows])


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    if not rows:
        return b""
    buffer = io.StringIO()
    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


def _format_money(value: Any) -> str:
    try:
        return f"{float(value):.2f} EUR"
    except Exception:
        return "-"


CSS = """
<style>
.v100-lock-card {
    border: 1px solid rgba(120,120,120,0.22);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 12px;
    background: linear-gradient(180deg, rgba(23,29,37,0.96), rgba(15,18,24,0.96));
    box-shadow: 0 8px 22px rgba(0,0,0,0.16);
}
.v100-lock-title {
    font-weight: 850;
    font-size: 1.05rem;
    margin-bottom: 6px;
}
.v100-lock-meta {
    opacity: 0.86;
    font-size: 0.92rem;
    margin-top: 8px;
}
.v100-pill-ok {
    display: inline-block;
    border-radius: 999px;
    padding: 4px 10px;
    background: rgba(34,197,94,0.18);
    border: 1px solid rgba(34,197,94,0.38);
    font-weight: 800;
}
.v100-pill-fail {
    display: inline-block;
    border-radius: 999px;
    padding: 4px 10px;
    background: rgba(239,68,68,0.18);
    border: 1px solid rgba(239,68,68,0.38);
    font-weight: 800;
}
</style>
"""


def render_v100_final_release_lock_section() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.title("Финално заключване")
    st.caption("Контролен екран: активен план, добавяне на тираж, история, финално табло и синхрон на данните.")
    st.warning(SAFE_NOTE_BG)

    if st.button("Обнови финалното заключване", key="v100_rebuild_btn"):
        payload = build_and_save()
        st.success(f"Финалното заключване е обновено. Статус: {friendly_status(payload.get('status'))}")
        st.rerun()

    payload = load_final_release_lock()
    active_plan = payload.get("active_plan", {}) or {}
    dataset = payload.get("dataset", {}) or {}
    statuses = payload.get("statuses", {}) or {}
    failures = payload.get("blocking_failures", []) or []
    warnings = payload.get("warnings", []) or []

    cols = st.columns(5)
    cols[0].metric("Статус", friendly_status(payload.get("status")))
    cols[1].metric("План", active_plan.get("strategy_type", "-"))
    cols[2].metric("Комбинации", int(active_plan.get("combination_count", 0) or 0))
    cols[3].metric("Цена", _format_money(active_plan.get("cost_eur", 0.0)))
    cols[4].metric("Редове в данните", int(dataset.get("historical_rows", 0) or 0))

    status_cols = st.columns(4)
    status_cols[0].metric("Преди запис", friendly_status(statuses.get("step95_status")))
    status_cols[1].metric("Реален цикъл", friendly_status(statuses.get("step97_status")))
    status_cols[2].metric("История", friendly_status(statuses.get("step98_status")))
    status_cols[3].metric("Табло", friendly_status(statuses.get("step99_status")))

    if failures:
        st.error("Има блокиращи проверки. Прегледай контролния списък преди финалното заключване.")
        for failure in failures:
            st.write(f"- {failure.get('area_bg', '')}: {failure.get('check_bg', '')} — {failure.get('details_bg', '')}")
    else:
        st.success("Работният процес е заключен и е готов за следващия реален тираж.")

    st.info(f"Следващо действие: {payload.get('next_action_bg', '-')}")

    tabs = st.tabs(["Проверки", "Данни", "Артефакти", "Бележки"])

    with tabs[0]:
        checklist_rows = _read_rows(CHECKLIST_CSV_PATH)
        if checklist_rows:
            st.dataframe(_rename_rows(checklist_rows, CHECKLIST_LABELS), width="stretch", hide_index=True)
            st.download_button(
                "Свали контролния списък",
                data=_csv_bytes(checklist_rows),
                file_name="v100_final_release_lock_checklist.csv",
                mime="text/csv",
            )
        else:
            st.info("Няма данни за контролния списък.")

    with tabs[1]:
        st.write(f"historical_draws.csv: **{dataset.get('historical_rows', 0)}** реда")
        st.write(f"v40_normalized_draw_events.csv: **{dataset.get('normalized_rows', 0)}** реда")
        st.write(f"v41_canonical_draw_events.csv: **{dataset.get('canonical_rows', 0)}** реда")
        st.write(f"Последен тираж: **{dataset.get('latest_draw_date', '-')}** — `{dataset.get('latest_numbers_text', '-')}`")

    with tabs[2]:
        manifest_rows = _read_rows(MANIFEST_CSV_PATH)
        if manifest_rows:
            st.dataframe(_rename_rows(manifest_rows, MANIFEST_LABELS), width="stretch", hide_index=True)
            st.download_button(
                "Свали manifest CSV",
                data=_csv_bytes(manifest_rows),
                file_name="v100_final_release_lock_manifest.csv",
                mime="text/csv",
            )
        else:
            st.info("Няма данни за описа на файловете.")

    with tabs[3]:
        for warning in warnings:
            st.write(f"- {warning}")
        st.markdown("Това е контролен екран. Той не генерира числа, не обучава модел и не променя прогнозната логика.")
        st.warning(SAFE_NOTE_BG)

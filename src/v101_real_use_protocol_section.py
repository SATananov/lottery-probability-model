from __future__ import annotations

import csv
import io
from typing import Any

import pandas as pd
import streamlit as st
from src.v110_user_friendly_ui_helpers import friendly_status, polish_dataframe

from src.v101_real_use_protocol_engine import (
    CHECKLIST_CSV_PATH,
    PROTOCOL_STEPS_CSV_PATH,
    SAFE_NOTE_BG,
    build_and_save,
    load_real_use_protocol,
)

CHECKLIST_LABELS = {
    "area_bg": "Област",
    "check_bg": "Проверка",
    "status": "Статус",
    "blocking": "Блокираща",
    "details_bg": "Детайл",
}

PROTOCOL_LABELS = {
    "order": "Ред",
    "phase_bg": "Фаза",
    "action_bg": "Действие",
    "why_bg": "Защо",
    "expected_result_bg": "Очакван резултат",
}

CSS = """
<style>
.v101-card {
    border: 1px solid rgba(120,120,120,0.22);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 12px;
    background: linear-gradient(180deg, rgba(23,29,37,0.96), rgba(15,18,24,0.96));
    box-shadow: 0 8px 22px rgba(0,0,0,0.16);
}
.v101-title {
    font-weight: 850;
    font-size: 1.05rem;
    margin-bottom: 6px;
}
.v101-meta {
    opacity: 0.86;
    font-size: 0.92rem;
    margin-top: 8px;
}
.v101-pill-ok {
    display: inline-block;
    border-radius: 999px;
    padding: 4px 10px;
    background: rgba(34,197,94,0.18);
    border: 1px solid rgba(34,197,94,0.38);
    font-weight: 800;
}
.v101-pill-warn {
    display: inline-block;
    border-radius: 999px;
    padding: 4px 10px;
    background: rgba(245,158,11,0.18);
    border: 1px solid rgba(245,158,11,0.38);
    font-weight: 800;
}
</style>
"""


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


def render_v101_real_use_protocol_section() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.title("Протокол за реална употреба")
    st.caption("Практически протокол след заключен план. Без нови модели, без промяна на математиката, без нови числа.")
    st.warning(SAFE_NOTE_BG)

    if st.button("Обнови протокола", key="v101_rebuild_btn"):
        payload = build_and_save()
        st.success(f"Протоколът е обновен. Статус: {friendly_status(payload.get('status'))}")
        st.rerun()

    payload = load_real_use_protocol()
    active_plan = payload.get("active_plan", {}) or {}
    dataset = payload.get("dataset", {}) or {}
    failures = payload.get("blocking_failures", []) or []
    status = payload.get("status", "UNKNOWN")

    pill_class = "v101-pill-ok" if not failures else "v101-pill-warn"
    st.markdown(
        f"""
        <div class="v101-card">
            <div class="v101-title">Статус на реалния протокол</div>
            <span class="{pill_class}">{friendly_status(status)}</span>
            <div class="v101-meta">Следващо действие: {payload.get('next_action_bg', '-')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Финално заключване", friendly_status(payload.get("step100_status")))
    c2.metric("План", active_plan.get("strategy_type", "-"))
    c3.metric("Комбинации", active_plan.get("combination_count", 0))
    c4.metric("Цена", active_plan.get("cost_text", "-"))

    d1, d2, d3 = st.columns(3)
    d1.metric("Редове в данните", dataset.get("historical_rows", 0))
    d2.metric("Последен тираж", dataset.get("latest_draw_date", "-"))
    d3.metric("Последни числа", dataset.get("latest_numbers_text", "-"))

    st.subheader("Ред за реална употреба")
    protocol_rows = payload.get("protocol_steps", []) or _read_rows(PROTOCOL_STEPS_CSV_PATH)
    if protocol_rows:
        st.dataframe(_rename_rows(protocol_rows, PROTOCOL_LABELS), width="stretch", hide_index=True)
        st.download_button(
            "Изтегли протокола CSV",
            data=_csv_bytes(protocol_rows),
            file_name="v101_real_use_protocol_steps.csv",
            mime="text/csv",
            key="v101_protocol_download",
        )
    else:
        st.info("Няма записани protocol стъпки.")

    st.subheader("Контролен checklist")
    checklist_rows = payload.get("checklist", []) or _read_rows(CHECKLIST_CSV_PATH)
    if checklist_rows:
        st.dataframe(_rename_rows(checklist_rows, CHECKLIST_LABELS), width="stretch", hide_index=True)
        st.download_button(
            "Изтегли checklist CSV",
            data=_csv_bytes(checklist_rows),
            file_name="v101_real_use_protocol_checklist.csv",
            mime="text/csv",
            key="v101_checklist_download",
        )

    st.subheader("Заключен обхват")
    st.info(payload.get("locked_scope_bg", "Без нови модели и без промяна на прогнозната логика преди следващ реален тираж."))

    if failures:
        st.error("Има блокиращи проверки. Прегледай checklist-а преди реална употреба.")
    else:
        st.success("Протоколът е готов: чака се следващият реален тираж.")

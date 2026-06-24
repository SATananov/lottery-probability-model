from __future__ import annotations

import csv
import io
from typing import Any

import pandas as pd
import streamlit as st

from src.v99_final_user_dashboard_engine import (
    ACTIONS_CSV_PATH,
    SAFE_NOTE_BG,
    SNAPSHOT_CSV_PATH,
    build_and_save,
    load_final_user_dashboard,
)

ACTION_LABELS = {
    "order": "Ред",
    "status": "Статус",
    "title_bg": "Действие",
    "description_bg": "Описание",
    "page_bg": "Страница",
    "is_ready": "Готово",
}

SNAPSHOT_LABELS = {
    "metric": "Показател",
    "value": "Стойност",
    "note_bg": "Бележка",
}


def _format_money(value: Any) -> str:
    try:
        return f"{float(value):.2f} EUR"
    except Exception:
        return "-"


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


def _numbers_chip_html(numbers_text: str) -> str:
    numbers = []
    for part in str(numbers_text or "").replace(";", ",").split(","):
        part = part.strip()
        if part:
            numbers.append(part)
    if not numbers:
        return "<span>-</span>"
    chips = "".join(f'<span class="v99-number-chip">{number}</span>' for number in numbers)
    return f'<div class="v99-number-strip">{chips}</div>'


CSS = """
<style>
.v99-action-card {
    border: 1px solid rgba(120,120,120,0.22);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 12px;
    background: linear-gradient(180deg, rgba(28,32,38,0.96), rgba(18,22,28,0.96));
    box-shadow: 0 8px 22px rgba(0,0,0,0.16);
}
.v99-action-title {
    font-weight: 800;
    font-size: 1rem;
    margin-bottom: 6px;
}
.v99-action-meta {
    opacity: 0.86;
    font-size: 0.9rem;
    margin-top: 8px;
}
.v99-number-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
    align-items: center;
    margin-top: 4px;
}
.v99-number-chip {
    width: 42px;
    height: 42px;
    min-width: 42px;
    border-radius: 999px;
    background: radial-gradient(circle at 32% 24%, rgba(255,246,176,0.98), rgba(244,210,84,0.98) 42%, rgba(184,144,24,0.98) 100%);
    color: #090909;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    border: 1px solid rgba(255,232,129,0.72);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.45), 0 8px 18px rgba(212,175,55,0.18);
}
</style>
"""


def render_v99_final_user_dashboard_section() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.title("Финално табло")
    st.caption("Step 99 — един ясен потребителски екран за активния план, следващото действие, реалния цикъл и историята.")
    st.warning(SAFE_NOTE_BG)

    if st.button("Обнови финалното табло", key="v99_rebuild_btn"):
        payload = build_and_save()
        st.success(f"Step 99 е обновен. Статус: {payload.get('status', 'UNKNOWN')}")
        st.rerun()

    payload = load_final_user_dashboard()
    active_plan = payload.get("active_plan", {}) or {}
    dataset = payload.get("dataset", {}) or {}
    statuses = payload.get("statuses", {}) or {}
    next_action = payload.get("next_action", {}) or {}
    actions = payload.get("actions", []) or []
    issues = payload.get("issues", []) or []

    cols = st.columns(5)
    cols[0].metric("Статус", payload.get("status", "UNKNOWN"))
    cols[1].metric("План", active_plan.get("strategy_type", "-"))
    cols[2].metric("Комбинации", int(active_plan.get("combination_count", 0) or 0))
    cols[3].metric("Цена", _format_money(active_plan.get("cost_eur", 0.0)))
    cols[4].metric("История", int(active_plan.get("real_result_rows", 0) or 0))

    status_cols = st.columns(4)
    status_cols[0].metric("Step 95", statuses.get("step95_status", "UNKNOWN"))
    status_cols[1].metric("Step 97", statuses.get("step97_status", "UNKNOWN"))
    status_cols[2].metric("Step 98", statuses.get("step98_status", "UNKNOWN"))
    status_cols[3].metric("Dataset", int(dataset.get("dataset_rows", 0) or 0))

    st.markdown("### Следващо действие")
    st.success(f"**{next_action.get('title_bg', '-')}**")
    st.write(next_action.get("description_bg", ""))
    st.caption(f"Отвори страница: {next_action.get('page_bg', '-')}")

    st.markdown("### Последен наличен тираж")
    st.write(f"Дата: **{dataset.get('latest_draw_date', '-')}** | Тираж: **{dataset.get('latest_draw_number', '-')}** | Теглене: **{dataset.get('latest_draw_position', '-')}**")
    st.markdown(_numbers_chip_html(dataset.get("latest_numbers_text", "")), unsafe_allow_html=True)

    if issues:
        st.warning("Има контролни бележки за преглед:")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.info("Няма критични контролни бележки. Таблото е готово за следващ реален тираж.")

    tabs = st.tabs(["Път на действие", "Активен план", "Snapshot", "Метод"])

    with tabs[0]:
        for action in actions:
            ready = "Да" if str(action.get("is_ready", "")).lower() in {"true", "1", "yes", "да"} or action.get("is_ready") is True else "Не"
            st.markdown(
                f"""
<div class="v99-action-card">
  <div class="v99-action-title">{action.get('order', '')}. {action.get('title_bg', '')}</div>
  <div>{action.get('description_bg', '')}</div>
  <div class="v99-action-meta">Статус: <b>{action.get('status', '-')}</b> · Страница: <b>{action.get('page_bg', '-')}</b> · Готово: <b>{ready}</b></div>
</div>
""",
                unsafe_allow_html=True,
            )

        action_rows = _read_rows(ACTIONS_CSV_PATH)
        if action_rows:
            st.download_button(
                "Свали път на действие CSV",
                data=_csv_bytes(action_rows),
                file_name="v99_final_user_dashboard_actions.csv",
                mime="text/csv",
            )

    with tabs[1]:
        st.markdown("### Активен план")
        st.write(f"Тип: **{active_plan.get('strategy_type', '-')}**")
        st.write(f"Комбинации: **{active_plan.get('combination_count', 0)}**")
        st.write(f"Цена: **{_format_money(active_plan.get('cost_eur', 0.0))}**")
        st.write(f"Заключен след: **{active_plan.get('saved_after_draw_date', '-')}** — `{active_plan.get('saved_after_draw_numbers', '-')}`")
        st.write(active_plan.get("next_status_bg", ""))

    with tabs[2]:
        snapshot_rows = _read_rows(SNAPSHOT_CSV_PATH)
        if snapshot_rows:
            st.dataframe(_rename_rows(snapshot_rows, SNAPSHOT_LABELS), use_container_width=True, hide_index=True)
        else:
            st.info("Няма snapshot данни.")

    with tabs[3]:
        st.markdown(
            "Step 99 не генерира нови числа и не променя моделите. Той събира вече готовите слоеве: "
            "Step 94 активен план, Step 95 pre-save проверка, Step 96 контролиран ред, Step 97 lifecycle и Step 98 история."
        )
        st.warning(SAFE_NOTE_BG)

from __future__ import annotations

import csv
import io
from typing import Any

import pandas as pd
import streamlit as st

from src.v97_real_draw_lifecycle_engine import (
    ARTIFACTS_CSV,
    CHECKLIST_CSV,
    SAFE_NOTE_BG,
    build_and_save,
    load_real_draw_lifecycle_summary,
)

CHECKLIST_LABELS = {
    "step_order": "Ред",
    "phase_bg": "Фаза",
    "page_bg": "Страница",
    "action_bg": "Действие",
    "expected_artifact_bg": "Артефакт",
    "guard_bg": "Контрол",
    "status_rule_bg": "Правило за статус",
}

ARTIFACT_LABELS = {
    "artifact_group": "Група",
    "path": "Файл",
    "purpose_bg": "Роля",
    "owner_step": "Стъпка",
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
    output = io.StringIO()
    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def _format_money(value: Any) -> str:
    try:
        return f"{float(value):.2f} EUR"
    except Exception:
        return "-"


def render_v97_real_draw_lifecycle_section() -> None:
    st.title("Реален цикъл на тираж")
    st.caption("Step 97 — затваря работния процес при нов реален тираж: pre-save проверки, запис, refresh, sync и clean checkpoint.")
    st.warning(SAFE_NOTE_BG)

    if st.button("Обнови Step 97 lifecycle status", key="v97_rebuild_btn"):
        payload = build_and_save()
        st.success(f"Step 97 е обновен. Статус: {payload.get('status', 'UNKNOWN')}")
        st.rerun()

    payload = load_real_draw_lifecycle_summary()
    current = payload.get("current_state", {}) or {}
    plan = current.get("active_plan", {}) or {}
    step95 = current.get("step95", {}) or {}
    step96 = current.get("step96", {}) or {}
    wiring = current.get("add_draw_wiring", {}) or {}
    anti_backfit = current.get("anti_backfit", {}) or {}

    cols = st.columns(5)
    cols[0].metric("Статус", payload.get("status", "UNKNOWN"))
    cols[1].metric("Dataset редове", int(current.get("dataset_rows", 0)))
    cols[2].metric("Step 95", step95.get("status", "UNKNOWN"))
    cols[3].metric("Активен план", plan.get("strategy_type", "-"))
    cols[4].metric("Цена", _format_money(plan.get("cost_eur", 0.0)))

    st.markdown("### Активен цикъл")
    st.write(f"Последен наличен тираж: **{current.get('latest_draw_date', '-')}** — `{current.get('latest_draw_numbers', '-')}`")
    st.write(
        "Активен план: "
        f"**{plan.get('strategy_type', '-')}**, "
        f"**{plan.get('combination_count', 0)} комбинации**, "
        f"**{_format_money(plan.get('cost_eur', 0.0))}**"
    )
    st.write(f"Step 96 status: **{step96.get('status', 'UNKNOWN')}** / workflow стъпки: **{step96.get('workflow_step_count', 0)}**")

    issues = payload.get("issues", []) or []
    if issues:
        st.error("Има елементи за преглед преди следващ реален тираж:")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.success("Lifecycle контролът е готов за следващ реален тираж.")

    st.markdown("### Проверки на реда")
    check_cols = st.columns(4)
    check_cols[0].metric("Step 95 преди запис", "OK" if wiring.get("v95_before_save_draws") else "REVIEW")
    check_cols[1].metric("Refresh след запис", "OK" if wiring.get("refresh_after_save_reference") else "REVIEW")
    check_cols[2].metric("Step 97 във веригата", "OK" if wiring.get("v97_refresh_script_present") else "REVIEW")
    check_cols[3].metric("Anti-backfit", "OK" if anti_backfit.get("draw_not_after_marker") and anti_backfit.get("is_draw_after_saved_guard") else "REVIEW")

    st.info(payload.get("next_user_action_bg", ""))

    tabs = st.tabs(["Последователност", "Артефакти", "Dataset-и", "Метод"])

    with tabs[0]:
        rows = _read_rows(CHECKLIST_CSV)
        if rows:
            st.dataframe(_rename_rows(rows, CHECKLIST_LABELS), use_container_width=True, hide_index=True)
            st.download_button(
                "Свали lifecycle checklist CSV",
                data=_csv_bytes(rows),
                file_name="v97_real_draw_lifecycle_checklist.csv",
                mime="text/csv",
            )
        else:
            st.info("Няма lifecycle checklist редове.")

    with tabs[1]:
        rows = _read_rows(ARTIFACTS_CSV)
        if rows:
            st.dataframe(_rename_rows(rows, ARTIFACT_LABELS), use_container_width=True, hide_index=True)
        else:
            st.info("Няма artifact map редове.")

    with tabs[2]:
        datasets = payload.get("datasets", []) or []
        if datasets:
            labels = {
                "path": "Файл",
                "exists": "Наличен",
                "rows": "Редове",
                "latest_date": "Последна дата",
                "latest_numbers": "Последни числа",
                "latest_year": "Година",
                "latest_draw_no": "Тираж",
                "latest_position": "Теглене",
                "parse_ok": "Parse OK",
            }
            st.dataframe(_rename_rows(datasets, labels), use_container_width=True, hide_index=True)
        else:
            st.info("Няма dataset status информация.")

    with tabs[3]:
        st.markdown(
            "Step 97 не добавя нова прогноза. Той служи като operational checklist за реален нов тираж: "
            "първо се оценява активният план срещу въведените числа, после се записва dataset-ът, "
            "после се обновява веригата и чак тогава се прави clean checkpoint."
        )
        st.warning(SAFE_NOTE_BG)

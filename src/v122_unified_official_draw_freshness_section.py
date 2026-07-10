from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v122_unified_official_draw_freshness_engine import (
    REPORT_CSV,
    SUMMARY_MD,
    build_freshness_report,
)

STATUS_ICON = {"synced": "🟢", "behind": "🔴", "ahead": "🔴", "unavailable": "⚪"}
STATUS_BG = {"synced": "Синхронизиран", "behind": "Назад", "ahead": "Пред официалния", "unavailable": "Няма данни"}


def render_v122_unified_official_draw_freshness_section() -> None:
    st.title("Свежест на официалния тираж")
    st.caption("Step 122 — единен source-of-truth статус за данни, R слой, решения, фишове и модели.")

    report = build_freshness_report(write_outputs=True)
    official = report["official_latest_draw"]

    left, middle, right = st.columns(3)
    left.metric("Официален последен тираж", f"{official.get('year')}-{official.get('draw_number')}")
    middle.metric("Дата", official.get("date") or "—")
    right.metric("Модули извън синхрон", report["blocking_out_of_sync_count"])

    if report["overall_status"] == "synced":
        st.success("Всички проверени модули са синхронизирани с официалния последен тираж.")
    else:
        st.error("Има модули, които не са синхронизирани. Не приемай техните решения като текущи, докато не бъдат обновени.")

    rows = []
    for source in report["sources"]:
        latest = source.get("latest") or {}
        rows.append({
            "Статус": f"{STATUS_ICON[source['status']]} {STATUS_BG[source['status']]}",
            "Модул": source["label"],
            "Тираж": f"{latest.get('year', '—')}-{latest.get('draw_number', '—')}",
            "Дата": latest.get("date") or "—",
            "Разлика": source.get("draw_delta") if source.get("draw_delta") is not None else "—",
            "Източник": source["path"],
            "Диагноза": source["message"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    stale = [source for source in report["sources"] if source["key"] != "official" and source["status"] != "synced"]
    if stale:
        st.markdown("### Какво трябва да се обнови")
        for source in stale:
            st.warning(f"**{source['label']}** — {source['message']} Източник: `{source['path']}`")

    st.info("Step 122 не стартира тежко обучение. Той диагностицира drift-а и показва кои downstream артефакти трябва да бъдат регенерирани.")

    if REPORT_CSV.exists():
        st.download_button(
            "Изтегли freshness matrix",
            data=REPORT_CSV.read_bytes(),
            file_name=REPORT_CSV.name,
            mime="text/csv",
        )
    if SUMMARY_MD.exists():
        with st.expander("Step 122 summary", expanded=False):
            st.markdown(SUMMARY_MD.read_text(encoding="utf-8", errors="replace"))

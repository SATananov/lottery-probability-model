from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v122_unified_official_draw_freshness_engine import build_freshness_report
from src.v143_3_downstream_zero_blocker_closure_engine import run_final_zero_blocker_closure


def render_v143_3_downstream_zero_blocker_closure_section() -> None:
    st.title("Финална синхронизация до нулеви блокери")
    st.caption("Обновява само леките downstream слоеве и потвърждава, че всички оперативни артефакти са на последния официален тираж.")
    st.info("Тежките ML модели не се преобучават. Личният дневник е защитен и не се включва в repair операциите.")

    freshness = build_freshness_report(write_outputs=False)
    c1, c2, c3 = st.columns(3)
    c1.metric("Последен официален тираж", f"{freshness['official_latest_draw'].get('year')}-{freshness['official_latest_draw'].get('draw_number')}")
    c2.metric("Блокиращи слоеве", int(freshness.get("blocking_out_of_sync_count", 0)))
    c3.metric("Статус", "Синхронизиран" if freshness.get("overall_status") == "synced" else "Изисква обновяване")

    rows = []
    for source in freshness.get("sources", []):
        if source.get("key") == "official" or source.get("status") == "informational":
            continue
        latest = source.get("latest") or {}
        rows.append({
            "Слой": source.get("label"),
            "Последен тираж": f"{latest.get('year', '?')}-{latest.get('draw_number', '?')}",
            "Статус": source.get("status"),
            "Разлика": source.get("draw_delta"),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    timeout = st.slider("Максимално време за отделен етап (секунди)", 60, 1800, 900, 60, key="v143_3_timeout")
    left, right = st.columns(2)
    with left:
        if st.button("Покажи безопасния план", use_container_width=True):
            st.session_state["v143_3_report"] = run_final_zero_blocker_closure(plan_only=True, timeout_seconds=timeout)
    with right:
        if st.button("Синхронизирай до нулеви блокери", type="primary", use_container_width=True):
            with st.spinner("Изпълнява се контролираното downstream обновяване..."):
                st.session_state["v143_3_report"] = run_final_zero_blocker_closure(timeout_seconds=timeout)

    report = st.session_state.get("v143_3_report")
    if not report:
        return
    if report.get("zero_blocker_confirmed"):
        st.success("Потвърдени са нулеви блокери. Всички оперативни downstream слоеве са синхронизирани.")
    elif report.get("status") in {"planned", "already_synced"}:
        st.info("Планът е готов. Не са изпълнени промени." if report.get("status") == "planned" else "Всички слоеве вече са синхронизирани.")
    else:
        st.error("Остава поне един блокиращ слой. Прегледай подробностите по-долу.")

    for row in report.get("repair", {}).get("results", []):
        icon = "✅" if row.get("ok") else ("⏸️" if row.get("status") in {"planned", "blocked"} else "❌")
        with st.expander(f"{icon} {row.get('name')} — {row.get('status')}"):
            st.write(row.get("message", ""))
            if row.get("output_tail"):
                st.code(row.get("output_tail"))

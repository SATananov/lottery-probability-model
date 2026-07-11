from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v142_downstream_freshness_repair_engine import build_repair_plan, run_targeted_repair


def render_v142_downstream_freshness_repair_section() -> None:
    st.title("Обновяване на изоставащите слоеве")
    st.caption("Обновява само необходимите производни отчети и фишове след нов официален тираж. Не преобучава тежките модели.")

    plan = build_repair_plan()
    if plan["status"] == "already_synced":
        st.success("Всички оперативни слоеве вече са синхронизирани.")
        return

    st.warning("Открити са изоставащи производни слоеве.")
    rows = [{"Ред": index, "Етап": stage["name"]} for index, stage in enumerate(plan["stages"], start=1)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    timeout = st.slider("Максимално време за отделен етап (секунди)", 60, 1800, 900, 60)
    left, right = st.columns(2)
    with left:
        if st.button("Покажи плана", use_container_width=True):
            st.session_state["v142_report"] = run_targeted_repair(plan_only=True)
    with right:
        if st.button("Обнови изоставащите слоеве", type="primary", use_container_width=True):
            with st.spinner("Изпълнява се безопасно обновяване..."):
                st.session_state["v142_report"] = run_targeted_repair(timeout_seconds=timeout)

    report = st.session_state.get("v142_report")
    if not report:
        return
    if report.get("status") == "completed":
        st.success("Всички изоставащи слоеве са обновени успешно.")
    elif report.get("status") == "planned":
        st.info("Планът е показан. Не са направени промени.")
    elif report.get("status") == "already_synced":
        st.success("Няма слоеве за обновяване.")
    else:
        st.error("Обновяването спря безопасно. Отвори подробностите за проблемния етап.")

    for row in report.get("results", []):
        icon = "✅" if row.get("ok") else ("⏸️" if row.get("status") in {"planned", "blocked"} else "❌")
        with st.expander(f"{icon} {row.get('name')} — {row.get('status')}"):
            st.write(row.get("message", ""))
            if row.get("output_tail"):
                st.code(row["output_tail"])

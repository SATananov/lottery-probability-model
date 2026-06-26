from __future__ import annotations

import pandas as pd
import streamlit as st
from src.v110_user_friendly_ui_helpers import friendly_status, polish_dataframe

from src.v104_final_audit_refresh_engine import build_and_write_final_audit_refresh_summary


def render_v104_final_audit_refresh_section() -> None:
    st.title("Финална проверка на проекта")
    st.caption("Актуален release audit след runtime hardening и clean ZIP checkpoint слоя.")

    summary = build_and_write_final_audit_refresh_summary()
    dataset = summary.get("dataset", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Статус", friendly_status(summary.get("status")))
    c2.metric("Проблеми за преглед", int(summary.get("blocking_failures", 0)))
    c3.metric("Редове в данните", int(dataset.get("rows", 0)))
    c4.metric("Последен тираж", str(dataset.get("latest_date", "")))

    if int(summary.get("blocking_failures", 0)) == 0:
        st.success("Финалният одит е актуален и няма блокиращи проблеми.")
    else:
        st.warning("Има проверки, които искат внимание.")

    st.subheader("Проверки")
    st.dataframe(pd.DataFrame(summary.get("checks", [])), use_container_width=True, hide_index=True)

    st.subheader("Статуси на финалните слоеве")
    st.dataframe(polish_dataframe(pd.DataFrame(summary.get("step_statuses", []))), use_container_width=True, hide_index=True)

    markers = summary.get("active_text_markers", {}).get("findings", [])
    if markers:
        st.subheader("Encoding markers")
        st.dataframe(pd.DataFrame(markers), use_container_width=True, hide_index=True)

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v110_user_friendly_ui_helpers import friendly_status, polish_dataframe
from src.v110_user_friendly_ui_polish_engine import build_and_write


def render_v110_user_friendly_ui_polish_section() -> None:
    st.title("Потребителска яснота")
    st.caption("Проверка дали основните екрани говорят на разбираем български, без излишни технически термини.")

    if st.button("Обнови проверката", width="stretch", key="v110_refresh_ui_polish_btn"):
        summary = build_and_write()
        st.success("Проверката е обновена.")
    else:
        summary = build_and_write()

    c1, c2, c3 = st.columns(3)
    c1.metric("Статус", friendly_status(summary.get("status")))
    c2.metric("Проблеми за преглед", int(summary.get("blocking_failures", 0)))
    c3.metric("Проверени екрани", len(summary.get("polished_files", [])))

    st.markdown("### Какво е изчистено")
    for note in summary.get("notes_bg", []):
        st.write(f"• {note}")

    checks = summary.get("checks", []) or []
    if checks:
        st.markdown("### Проверки")
        st.dataframe(polish_dataframe(pd.DataFrame(checks)), width="stretch", hide_index=True)

    st.info("Тази страница е контролна. Тя не променя числата, моделите, фишовете или резултатите.")

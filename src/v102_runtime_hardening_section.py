from __future__ import annotations

import pandas as pd
import streamlit as st
from src.v110_user_friendly_ui_helpers import friendly_status

from src.v102_runtime_hardening_engine import load_runtime_hardening_summary, write_runtime_hardening_artifacts


def render_v102_runtime_hardening_section() -> None:
    st.title("Защита при обновяване")
    st.caption(
        "Контролна страница за бързото обновяване след реален тираж, timeout защитата "
        "и отделянето на тежките лабораторни процеси от стандартния поток."
    )

    if st.button("Обнови проверката", use_container_width=True, key="v102_refresh_btn"):
        summary = write_runtime_hardening_artifacts()
        st.success("Проверката е обновена.")
    else:
        summary = load_runtime_hardening_summary()

    cols = st.columns(4)
    cols[0].metric("Статус", friendly_status(summary.get("status")))
    cols[1].metric("Проблеми за преглед", int(summary.get("blocking_failures", 0)))
    cols[2].metric("Default timeout", f"{summary.get('default_timeout_seconds', 0)} сек.")
    cols[3].metric("Само ръчно", len(summary.get("heavy_scripts_kept_manual", [])))

    st.markdown("### Какво прави тази защита")
    for item in summary.get("what_changed_bg", []):
        st.write("- " + str(item))

    checks = summary.get("checks", [])
    if checks:
        st.markdown("### Проверки")
        df = pd.DataFrame(checks)
        st.dataframe(df, use_container_width=True, hide_index=True)

    heavy = summary.get("heavy_scripts_kept_manual", [])
    if heavy:
        st.markdown("### Тежки процеси, оставени за ръчно пускане")
        st.info(
            "Тези скриптове не са премахнати. Те просто не трябва да блокират стандартния поток "
            "след въвеждане на реален тираж: " + ", ".join(heavy)
        )

    st.warning(
        "Тази страница не променя математиката на моделите. Тя защитава runtime поведението на app-а "
        "и намалява риска от забиване при обновяване."
    )

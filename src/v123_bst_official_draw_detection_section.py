from __future__ import annotations

import streamlit as st

from src.v123_bst_official_draw_detection_engine import (
    OFFICIAL_BASE_URL,
    SUMMARY_MD,
    detect_latest_official_draw,
    latest_local_draw,
)


def _draw_label(draw: dict) -> str:
    if not draw:
        return "—"
    return f"{draw.get('year', '—')}-{draw.get('draw_number', '—')}"


def render_v123_bst_official_draw_detection_section() -> None:
    st.title("Проверка за нов официален тираж")
    st.caption("Step 123 — read-only проверка на БСТ. Не записва тиражи и не обновява downstream модулите.")

    local = latest_local_draw()
    c1, c2 = st.columns(2)
    c1.metric("Локален последен тираж", _draw_label(local))
    c2.metric("Локална дата", local.get("date") or "—")

    st.info(
        "Тази стъпка само проверява и валидира. Безопасното записване ще бъде отделен Step 124, "
        "а обновяването по веригата — Step 125."
    )
    st.markdown(f"Официален източник: `{OFFICIAL_BASE_URL}`")

    validate_details = st.checkbox("Валидирай и детайлната страница на последния тираж", value=True)
    timeout = st.slider("Timeout за официалната проверка (секунди)", 10, 60, 30, 5)

    if st.button("Провери БСТ за нов тираж", type="primary"):
        with st.spinner("Проверявам официалния БСТ източник..."):
            report = detect_latest_official_draw(timeout=timeout, validate_details=validate_details, write_outputs=True)

        official = report.get("official_latest_draw") or {}
        a, b, c = st.columns(3)
        a.metric("Официален последен тираж", _draw_label(official))
        b.metric("Дата", official.get("date") or "—")
        c.metric("Разлика", report.get("draw_delta") if report.get("draw_delta") is not None else "—")

        status = report.get("status")
        if status == "up_to_date":
            st.success("Няма неприложен официален тираж. Локалният source of truth е актуален.")
        elif status == "update_available":
            st.warning("Има нов официален тираж, който още не е приложен локално.")
        elif status == "local_ahead":
            st.error("Локалният тираж изглежда пред официално открития. Не предприемай автоматичен запис.")
        else:
            st.error("Официалната проверка не завърши надеждно. Локалните данни не са променени.")

        st.write(report.get("message") or "")
        validation = report.get("validation") or {}
        st.write("Детайлна валидация:", "успешна" if validation.get("passed") else "неуспешна")
        if official.get("numbers"):
            st.write("Печеливши числа:", ", ".join(str(x) for x in official["numbers"]))
        if validation.get("errors"):
            st.code("\n".join(validation["errors"]), language="text")

    if SUMMARY_MD.exists():
        with st.expander("Последен Step 123 detection summary", expanded=False):
            st.markdown(SUMMARY_MD.read_text(encoding="utf-8", errors="replace"))

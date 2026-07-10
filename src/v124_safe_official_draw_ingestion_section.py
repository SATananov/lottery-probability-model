from __future__ import annotations

import streamlit as st

from src.v123_bst_official_draw_detection_engine import detect_latest_official_draw, latest_local_draw
from src.v124_safe_official_draw_ingestion_engine import (
    AUDIT_JSONL,
    SUMMARY_MD,
    detect_and_ingest_latest_official_draw,
)


def _label(draw: dict) -> str:
    if not draw:
        return "—"
    return f"{draw.get('year', '—')}-{draw.get('draw_number', '—')}"


def render_v124_safe_official_draw_ingestion_section() -> None:
    st.title("Безопасно прилагане на официален тираж")
    st.caption("Step 124 — backup, staging, duplicate защита, audit и rollback. Не обновява downstream модулите.")

    local = latest_local_draw()
    c1, c2 = st.columns(2)
    c1.metric("Локален последен тираж", _label(local))
    c2.metric("Локална дата", local.get("date") or "—")

    st.warning(
        "Тази страница може да запише само строго по-нов, успешно валидиран официален тираж. "
        "R, Decision Center, ticket packs и моделите остават непроменени до Step 125."
    )
    timeout = st.slider("Timeout за БСТ (секунди)", 10, 60, 30, 5, key="v124_timeout")

    if st.button("1. Провери за нов официален тираж", type="primary"):
        with st.spinner("Проверявам и валидирам БСТ..."):
            st.session_state["v124_detection"] = detect_latest_official_draw(
                timeout=timeout, validate_details=True, write_outputs=True
            )

    detection = st.session_state.get("v124_detection")
    if detection:
        official = detection.get("official_latest_draw") or {}
        a, b, c = st.columns(3)
        a.metric("Официален тираж", _label(official))
        b.metric("Дата", official.get("date") or "—")
        c.metric("Разлика", detection.get("draw_delta") if detection.get("draw_delta") is not None else "—")

        status = detection.get("status")
        if status == "up_to_date":
            st.success("Няма нов официален тираж за прилагане.")
        elif status == "update_available":
            st.warning("Открит е строго по-нов официален тираж. Може да бъде приложен безопасно.")
            if official.get("numbers"):
                st.write("Печеливши числа:", ", ".join(str(x) for x in official["numbers"]))
            confirmed = st.checkbox(
                "Потвърждавам прилагането само към official source of truth и journal mirror",
                key="v124_confirm",
            )
            if st.button("2. Направи backup и приложи тиража", disabled=not confirmed):
                with st.spinner("Създавам backup, staging и изпълнявам безопасно прилагане..."):
                    result = detect_and_ingest_latest_official_draw(timeout=timeout)
                    st.session_state["v124_result"] = result
                st.session_state["v124_detection"] = None
        else:
            st.error("Прилагането е блокирано, защото официалната проверка не е надеждна.")
            st.write(detection.get("message") or "")

    result = st.session_state.get("v124_result")
    if result:
        status = result.get("status")
        if status == "inserted":
            st.success("Официалният тираж е приложен безопасно. Downstream модулите още не са обновени.")
        elif status in {"duplicate_blocked", "nothing_to_ingest"}:
            st.info(result.get("message") or "Не са направени промени.")
        elif status == "rolled_back":
            st.error("Операцията се провали, но rollback-ът възстанови оригиналните данни.")
        else:
            st.error(result.get("message") or "Тиражът не беше приложен.")

        cols = st.columns(4)
        cols[0].metric("Статус", status or "—")
        cols[1].metric("Тираж", result.get("draw_key") or "—")
        cols[2].metric("Backup", "Да" if result.get("backup_created") else "Не")
        cols[3].metric("Rollback", "Да" if result.get("rollback_performed") else "Не")
        with st.expander("Технически отчет за операцията", expanded=False):
            st.json(result)

    if SUMMARY_MD.exists():
        with st.expander("Последен Step 124 summary", expanded=False):
            st.markdown(SUMMARY_MD.read_text(encoding="utf-8", errors="replace"))
    if AUDIT_JSONL.exists():
        st.caption(f"Audit журнал: {AUDIT_JSONL.relative_to(AUDIT_JSONL.parents[1])}")

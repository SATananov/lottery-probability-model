from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v122_unified_official_draw_freshness_engine import REPORT_CSV, SUMMARY_MD, build_freshness_report
from src.v142_downstream_freshness_repair_engine import run_targeted_repair

STATUS_ICON = {"synced": "🟢", "behind": "🔴", "ahead": "🔴", "unavailable": "⚪", "informational": "🔵", "local_optional": "🟡"}
STATUS_BG = {"synced": "Синхронизиран", "behind": "Назад", "ahead": "Пред официалния", "unavailable": "Няма данни", "informational": "Информация", "local_optional": "Само локално"}


def _draw_label(source: dict) -> str:
    if source.get("status") in {"informational", "local_optional"}:
        return "Не се следи по тираж"
    latest = source.get("latest") or {}
    year = latest.get("year")
    draw = latest.get("draw_number")
    return f"{year}-{draw}" if year and draw is not None else "—"


def render_v122_unified_official_draw_freshness_section() -> None:
    st.title("Свежест на официалния тираж")
    st.caption("Единен преглед на данните, статистическите слоеве, решенията и готовите фишове.")

    report = build_freshness_report(write_outputs=True)
    official = report["official_latest_draw"]

    left, middle, right = st.columns(3)
    left.metric("Последен официален тираж", f"{official.get('year')}-{official.get('draw_number')}")
    middle.metric("Дата", official.get("date") or "—")
    right.metric("Изоставащи слоеве", report["blocking_out_of_sync_count"])

    if report["overall_status"] == "synced":
        st.success("Всички оперативни слоеве са синхронизирани с последния официален тираж.")
    else:
        st.error("Има изоставащи слоеве. Обнови ги, преди да използваш решенията и готовите фишове.")

    rows = []
    for source in report["sources"]:
        latest = source.get("latest") or {}
        rows.append({
            "Статус": f"{STATUS_ICON[source['status']]} {STATUS_BG[source['status']]}",
            "Модул": source["label"],
            "Тираж": _draw_label(source),
            "Дата": latest.get("date") or "—",
            "Разлика": source.get("draw_delta") if source.get("draw_delta") is not None else "—",
            "Диагноза": source["message"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    stale = [source for source in report["sources"] if source["key"] != "official" and source["status"] not in {"synced", "informational", "local_optional"}]
    if stale:
        st.markdown("### Какво трябва да се обнови")
        for source in stale:
            st.warning(f"**{source['label']}** — {source['message']}")
        if st.button("Обнови изоставащите слоеве", type="primary", use_container_width=True):
            with st.spinner("Обновяване на необходимите слоеве..."):
                result = run_targeted_repair(timeout_seconds=900)
            if result.get("status") == "completed":
                st.success("Обновяването приключи успешно. Страницата ще бъде презаредена.")
                st.rerun()
            else:
                st.error("Обновяването спря безопасно. Отвори страницата „Обновяване на изоставащите слоеве“ за подробности.")

    st.info("Обучените ML модели имат собствен график за обновяване и не се считат за изоставащи след всеки нов тираж.")

    with st.expander("Технически подробности", expanded=False):
        tech_rows = [{"Модул": source["label"], "Файл": source["path"]} for source in report["sources"]]
        st.dataframe(pd.DataFrame(tech_rows), use_container_width=True, hide_index=True)
        if REPORT_CSV.exists():
            st.download_button("Изтегли техническата матрица", data=REPORT_CSV.read_bytes(), file_name=REPORT_CSV.name, mime="text/csv")
        if SUMMARY_MD.exists():
            st.markdown(SUMMARY_MD.read_text(encoding="utf-8", errors="replace"))

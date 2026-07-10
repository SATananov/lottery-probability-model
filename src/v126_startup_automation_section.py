from __future__ import annotations

import streamlit as st

from src.v126_startup_automation_engine import (
    DEFAULT_CONFIG,
    load_config,
    load_status,
    run_startup_automation,
    save_config,
)

SESSION_KEY = "v126_startup_check_done"
REPORT_KEY = "v126_report"


def initialize_v126_startup_automation() -> dict:
    """Run at most once per Streamlit session; the engine also enforces disk-cache TTL."""
    if st.session_state.get(SESSION_KEY):
        return st.session_state.get(REPORT_KEY) or load_status()
    st.session_state[SESSION_KEY] = True
    config = load_config()
    if not config.get("auto_check_enabled", True):
        report = run_startup_automation(trigger="startup", config=config)
    else:
        report = run_startup_automation(trigger="startup", config=config)
    st.session_state[REPORT_KEY] = report
    return report


def _show_report(report: dict) -> None:
    status = report.get("status", "unknown")
    message = report.get("message", "")
    if status in {"up_to_date", "completed", "draw_applied"}:
        st.success(message)
    elif status in {"cached", "disabled", "update_available"}:
        st.info(message)
    elif status in {"check_failed", "operator_review_required", "ingestion_blocked", "refresh_check_required"}:
        st.warning(message)
    else:
        st.error(message or "Операцията не завърши успешно.")

    detection = report.get("detection") or {}
    if detection:
        local = detection.get("local_latest_draw") or {}
        official = detection.get("official_latest_draw") or {}
        c1, c2, c3 = st.columns(3)
        c1.metric("Локален тираж", local.get("draw_key") or f"{local.get('year','?')}-{local.get('draw_number','?')}")
        c2.metric("Официален тираж", official.get("draw_key") or f"{official.get('year','?')}-{official.get('draw_number','?')}")
        c3.metric("Detection статус", detection.get("status", "—"))

    if report.get("ingestion"):
        with st.expander("Резултат от безопасното прилагане"):
            st.json(report["ingestion"])
    if report.get("downstream_refresh"):
        with st.expander("Резултат от downstream обновяването"):
            st.json(report["downstream_refresh"])


def render_v126_startup_automation_section() -> None:
    st.title("Автоматична проверка и операторски контрол")
    st.caption("Step 126 — проверка при старт, защита от Streamlit rerun, ръчни контроли и optional auto-apply. Без тежко ML retraining.")

    config = load_config()
    with st.form("v126_settings"):
        auto_check = st.checkbox("Автоматична проверка при старт", value=config["auto_check_enabled"])
        auto_apply = st.checkbox("Автоматично приложи валидиран нов тираж", value=config["auto_apply_enabled"])
        auto_refresh = st.checkbox(
            "След успешно прилагане обнови оперативната downstream верига",
            value=config["auto_refresh_enabled"],
            disabled=not auto_apply,
        )
        cache_minutes = st.slider("Кеш между проверки (минути)", 5, 240, int(config["cache_minutes"]), 5)
        network_timeout = st.slider("Timeout към БСТ (секунди)", 5, 60, int(config["network_timeout_seconds"]), 1)
        downstream_timeout = st.slider("Timeout за downstream етап (секунди)", 60, 1800, int(config["downstream_timeout_seconds"]), 60)
        saved = st.form_submit_button("Запази настройките", type="primary", use_container_width=True)
    if saved:
        saved_config = save_config({
            **DEFAULT_CONFIG,
            "auto_check_enabled": auto_check,
            "auto_apply_enabled": auto_apply,
            "auto_refresh_enabled": auto_refresh if auto_apply else False,
            "cache_minutes": cache_minutes,
            "network_timeout_seconds": network_timeout,
            "downstream_timeout_seconds": downstream_timeout,
        })
        st.success("Настройките са запазени.")
        st.session_state["v126_saved_config"] = saved_config

    st.warning("Препоръчителен начален режим: автоматична проверка ON, auto-apply OFF. Включи пълната автоматизация след реален успешен нов тираж.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Провери сега", use_container_width=True):
            with st.spinner("Проверка на официалния източник..."):
                report = run_startup_automation(trigger="manual_check", force_check=True, config=load_config())
                st.session_state[REPORT_KEY] = report
    with col2:
        if st.button("Провери и изпълни според настройките", type="primary", use_container_width=True):
            with st.spinner("Изпълнение на контролираната автоматизация..."):
                report = run_startup_automation(trigger="operator_run", force_check=True, config=load_config())
                st.session_state[REPORT_KEY] = report

    report = st.session_state.get(REPORT_KEY) or load_status()
    if report:
        _show_report(report)

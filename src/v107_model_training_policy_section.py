from __future__ import annotations

import pandas as pd
import streamlit as st
from src.v110_user_friendly_ui_helpers import friendly_status, polish_dataframe

from src.v107_model_training_policy_engine import load_summary, write_artifacts


def render_v107_model_training_policy_section() -> None:
    st.title("Политика за обучение")
    st.caption(
        "Тази страница показва дали има смисъл от ново обучение на моделите. "
        "След единичен нов тираж обикновено обновяваме само отчетите и дневника."
    )

    if st.button("Обнови политиката за обучение", use_container_width=True, key="v107_refresh_policy_btn"):
        summary = write_artifacts()
        st.success("Политиката за обучение е обновена.")
    else:
        summary = load_summary()

    dataset = summary.get("dataset", {}) or {}
    latest = dataset.get("latest_draw", {}) or {}
    policy = summary.get("policy_decision", {}) or {}

    cols = st.columns(4)
    cols[0].metric("Статус", friendly_status(summary.get("status")))
    cols[1].metric("Редове в данните", dataset.get("dataset_rows", 0))
    cols[2].metric("Реални резултати", summary.get("real_result_rows_since_active_plan", 0))
    cols[3].metric("Проблеми за преглед", summary.get("blocking_failures", 0))

    st.markdown("### Текуща препоръка")
    if summary.get("status") == "TRAINING_POLICY_READY":
        st.success(policy.get("label_bg", "Политиката е готова"))
    else:
        st.warning(policy.get("label_bg", "Нужна е проверка"))
    st.write(policy.get("message_bg", ""))
    st.info(policy.get("recommended_action_bg", ""))
    if policy.get("next_threshold_bg"):
        st.caption(policy.get("next_threshold_bg"))

    st.markdown("### Последен реален тираж")
    st.write(
        f"Дата: **{latest.get('date', '—')}** · Тираж: **{latest.get('draw_no', '—')}** · "
        f"Числа: **{', '.join(str(n) for n in latest.get('numbers', [])) or '—'}**"
    )

    st.markdown("### Политика по групи")
    policy_table = summary.get("policy_table", []) or []
    if policy_table:
        st.dataframe(polish_dataframe(pd.DataFrame(policy_table)), use_container_width=True, hide_index=True)

    st.markdown("### Проверки")
    checks = summary.get("checks", []) or []
    if checks:
        st.dataframe(polish_dataframe(pd.DataFrame(checks)), use_container_width=True, hide_index=True)

    st.warning(
        "Тази страница не обучава модели и не обещава печалба. Тя пази проекта от ненужно тежко обучение "
        "след единичен тираж и оставя тежките лабораторни процеси само за ръчен контрол."
    )

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v107_model_training_policy_engine import load_summary, write_artifacts


def render_v107_model_training_policy_section() -> None:
    st.title("Политика за обучение")
    st.caption(
        "Контролен слой за това кога се прави бърз refresh, кога има смисъл от лек статистически refresh "
        "и кога тежките лабораторни модели се пускат само ръчно."
    )

    if st.button("Обнови Step 107 политиката", use_container_width=True, key="v107_refresh_policy_btn"):
        summary = write_artifacts()
        st.success("Step 107 политиката е обновена.")
    else:
        summary = load_summary()

    dataset = summary.get("dataset", {}) or {}
    latest = dataset.get("latest_draw", {}) or {}
    policy = summary.get("policy_decision", {}) or {}

    cols = st.columns(4)
    cols[0].metric("Статус", summary.get("status", "UNKNOWN"))
    cols[1].metric("Dataset редове", dataset.get("dataset_rows", 0))
    cols[2].metric("Реални резултати", summary.get("real_result_rows_since_active_plan", 0))
    cols[3].metric("Blocking failures", summary.get("blocking_failures", 0))

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
        st.dataframe(pd.DataFrame(policy_table), use_container_width=True, hide_index=True)

    st.markdown("### Проверки")
    checks = summary.get("checks", []) or []
    if checks:
        st.dataframe(pd.DataFrame(checks), use_container_width=True, hide_index=True)

    st.warning(
        "Step 107 не обучава модели и не обещава печалба. Той пази проекта от ненужно тежко обучение "
        "след единичен тираж и оставя heavy/lab процесите само за ръчен контрол."
    )

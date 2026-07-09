
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.post_bst_model_data_refresh_engine import (
    CHECKLIST_CSV,
    SUMMARY_MD,
    get_sync_status,
    refresh_model_data_from_prize_history,
)


def _df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def render_post_bst_model_data_refresh_section() -> None:
    st.title("Обновяване на моделни данни")
    st.caption(
        "Step 120 — синхронизира официалната БСТ prize history към historical/canonical dataset слоя, "
        "за да работят анализите върху последните официални тиражи."
    )

    st.info(
        "Тази стъпка НЕ retrain-ва тежките ML модели автоматично. Тя обновява dataset слоя. "
        "Пълното retraining решение остава ръчно и осъзнато."
    )

    status = get_sync_status()

    st.markdown("### Текущ статус")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Статус", status.get("status", "UNKNOWN"))
    c2.metric("БСТ prize latest", f"{status['latest_prize_history'].get('year')} / {status['latest_prize_history'].get('draw_number')}")
    c3.metric("Historical latest", f"{status['latest_historical_draws'].get('year')} / {status['latest_historical_draws'].get('draw_number')}")
    c4.metric("Canonical latest", f"{status['latest_v41_canonical'].get('year')} / {status['latest_v41_canonical'].get('draw_number')}")

    st.markdown("### Липсващи записи по dataset")
    missing = status.get("missing", {})
    tabs = st.tabs(["historical_draws", "v40_normalized", "v41_canonical"])

    with tabs[0]:
        df = _df(missing.get("historical_draws", []))
        st.dataframe(df, use_container_width=True, hide_index=True) if not df.empty else st.success("Няма липсващи записи.")

    with tabs[1]:
        df = _df(missing.get("v40_normalized", []))
        st.dataframe(df, use_container_width=True, hide_index=True) if not df.empty else st.success("Няма липсващи записи.")

    with tabs[2]:
        df = _df(missing.get("v41_canonical", []))
        st.dataframe(df, use_container_width=True, hide_index=True) if not df.empty else st.success("Няма липсващи записи.")

    st.markdown("### Действие")
    if st.button("Обнови моделните данни от БСТ prize history", type="primary"):
        with st.spinner("Синхронизирам historical/v40/v41 dataset слоя..."):
            try:
                result = refresh_model_data_from_prize_history()
                after = result.get("status_after", {})
                st.success(f"Готово. Финален статус: {after.get('status', 'UNKNOWN')}")

                inserted = result.get("inserted", {})
                st.write("Добавени записи:")
                st.json({key: len(value) for key, value in inserted.items()})

                updated = result.get("updated", {})
                st.write("Обновени записи:")
                st.json({key: len(value) for key, value in updated.items()})

                st.warning("ML retraining не е изпълнен автоматично. Това е само dataset refresh.")
            except Exception as exc:
                st.error(f"Неуспешно обновяване: {exc}")

    st.markdown("### Отчети")
    if SUMMARY_MD.exists():
        with st.expander("Step 120 summary", expanded=False):
            st.markdown(SUMMARY_MD.read_text(encoding="utf-8", errors="replace"))

    if CHECKLIST_CSV.exists():
        with st.expander("Step 120 checklist", expanded=False):
            try:
                st.dataframe(pd.read_csv(CHECKLIST_CSV), use_container_width=True, hide_index=True)
            except Exception:
                st.warning("Checklist CSV не може да бъде прочетен.")

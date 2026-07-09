
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.r_statistical_features_integration_engine import (
    BLENDED_SCORES_CSV,
    NUMBER_FEATURES_CSV,
    PAIR_FEATURES_CSV,
    SUMMARY_MD,
    TICKET_PACK_CSV,
    build_r_number_features,
    build_r_feature_ticket_pack,
)


def _read_csv(path):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def render_r_statistical_features_integration_section() -> None:
    st.title("R feature интеграция")
    st.caption(
        "Step 121 — превръща R статистическите отчети в Python-readable features, "
        "R-blended number scores и контролиран ticket pack."
    )

    st.info(
        "Тази стъпка не retrain-ва тежките ML модели. Тя интегрира R като feature/scoring слой, "
        "който може да подпомага избора на числа и бъдещи моделни решения."
    )

    left, right = st.columns(2)

    with left:
        if st.button("Генерирай R features", type="secondary"):
            with st.spinner("Чета reports/r и генерирам feature таблици..."):
                try:
                    result = build_r_number_features()
                    st.success("R feature таблиците са генерирани.")
                    st.json(result.get("output_files", {}))
                except Exception as exc:
                    st.error(f"Грешка при feature generation: {exc}")

    with right:
        if st.button("Генерирай R ticket pack", type="primary"):
            with st.spinner("Генерирам R-blended ticket pack..."):
                try:
                    result = build_r_feature_ticket_pack(pack_count=3, lines_per_pack=4)
                    st.success(f"Готово. Генерирани линии: {result.get('ticket_count', 0)}")
                    st.json(result.get("model_retraining", {}))
                except Exception as exc:
                    st.error(f"Грешка при ticket pack generation: {exc}")

    st.markdown("### R-blended number scores")
    scores_df = _read_csv(BLENDED_SCORES_CSV)
    if scores_df.empty:
        st.warning("Още няма генерирани R blended scores.")
    else:
        st.dataframe(scores_df.head(20), use_container_width=True, hide_index=True)

    st.markdown("### R feature ticket pack")
    ticket_df = _read_csv(TICKET_PACK_CSV)
    if ticket_df.empty:
        st.warning("Още няма генериран R ticket pack.")
    else:
        st.dataframe(ticket_df, use_container_width=True, hide_index=True)

    st.markdown("### Output files")
    st.code(
        "\n".join([
            str(NUMBER_FEATURES_CSV.relative_to(NUMBER_FEATURES_CSV.parents[1])),
            str(PAIR_FEATURES_CSV.relative_to(PAIR_FEATURES_CSV.parents[1])),
            str(BLENDED_SCORES_CSV.relative_to(BLENDED_SCORES_CSV.parents[1])),
            str(TICKET_PACK_CSV.relative_to(TICKET_PACK_CSV.parents[1])),
        ]),
        language="text",
    )

    if SUMMARY_MD.exists():
        with st.expander("Step 121 summary", expanded=False):
            st.markdown(SUMMARY_MD.read_text(encoding="utf-8", errors="replace"))

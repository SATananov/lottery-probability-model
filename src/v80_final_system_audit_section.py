from __future__ import annotations

from pathlib import Path
import json
import pandas as pd
import streamlit as st

from src.v80_final_system_audit_engine import (
    ARTIFACT_AUDIT_CSV,
    DATASET_AUDIT_CSV,
    FILE_QUALITY_AUDIT_CSV,
    SAFE_NOTE,
    SUMMARY_JSON,
    SYNC_PLAN_AUDIT_CSV,
    build_final_system_audit_center,
)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        return pd.DataFrame()


def _status_badge(status: str) -> str:
    return "✅ OK" if str(status) == "OK" else "⚠️ За преглед"


def render_v80_final_system_audit_section() -> None:
    st.title("🧾 Финален системен одит")
    st.caption(
        "Контролен център за datasets, артефакти, sync планове, Python compile, JSON/CSV parse и кирилица."
    )
    st.warning(SAFE_NOTE)

    action_col, info_col = st.columns([1, 2])
    with action_col:
        if st.button("Обнови финалния одит", type="primary", key="v80_refresh_audit"):
            with st.spinner("Проверявам datasets, артефакти, sync планове и файлово качество..."):
                build_final_system_audit_center()
            st.success("Step 80 одитът е обновен успешно.")
            st.rerun()
    with info_col:
        st.info(
            "Този екран не избира числа. Той проверява дали системата е последователна, чиста и готова за checkpoint."
        )

    summary = _read_json(SUMMARY_JSON)
    if not summary:
        st.info("Още няма Step 80 отчет. Натисни бутона за обновяване.")
        return

    cols = st.columns(5)
    cols[0].metric("Статус", _status_badge(str(summary.get("status", ""))))
    cols[1].metric("Datasets", summary.get("datasets_checked", 0))
    cols[2].metric("Артефакти", summary.get("artifacts_checked", 0))
    cols[3].metric("Sync планове", summary.get("sync_plans_checked", 0))
    cols[4].metric("Проблеми", summary.get("issues_found", 0))

    st.subheader("Dataset проверки")
    dataset_df = _read_csv(DATASET_AUDIT_CSV)
    if dataset_df.empty:
        st.info("Няма dataset audit таблица.")
    else:
        st.dataframe(dataset_df, use_container_width=True, hide_index=True)

    st.subheader("Sync планове")
    sync_df = _read_csv(SYNC_PLAN_AUDIT_CSV)
    if sync_df.empty:
        st.info("Няма sync plan audit таблица.")
    else:
        st.dataframe(sync_df, use_container_width=True, hide_index=True)

    with st.expander("Step 76–79 артефакти"):
        artifact_df = _read_csv(ARTIFACT_AUDIT_CSV)
        if artifact_df.empty:
            st.info("Няма artifact audit таблица.")
        else:
            st.dataframe(artifact_df, use_container_width=True, hide_index=True)

    with st.expander("Файлово качество: compile, labels, кирилица"):
        quality_df = _read_csv(FILE_QUALITY_AUDIT_CSV)
        if quality_df.empty:
            st.info("Няма quality audit таблица.")
        else:
            st.dataframe(quality_df, use_container_width=True, hide_index=True)

    with st.expander("Как да се чете Step 80"):
        st.markdown(
            "- **OK** означава, че проверката е минала според текущите правила.\n"
            "- **За преглед** не значи автоматично счупване, а че има файл, стойност или chain, който трябва да се види.\n"
            "- Одитът проверява стабилност на системата, не вероятност за печалба.\n"
            "- След нов тираж първо минава refresh chain-ът, после Step 80 и накрая Step 74 sync контрол."
        )

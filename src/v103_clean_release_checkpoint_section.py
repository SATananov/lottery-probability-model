from __future__ import annotations

import pandas as pd
import streamlit as st
from src.v110_user_friendly_ui_helpers import friendly_status

from src.v103_clean_release_checkpoint_engine import (
    build_clean_release_summary,
    create_clean_release_checkpoint,
)


def _checks_df(summary: dict) -> pd.DataFrame:
    return pd.DataFrame(summary.get("checks", []))


def render_v103_clean_release_checkpoint_section() -> None:
    st.title("Чист архив на проекта")
    st.caption("Контрол за чист release ZIP без .git, cache, helper patch файлове и nested ZIP артефакти.")

    # Build a live UI summary without writing reports to disk.
    # This prevents the Step 103 page from making git status dirty after a clean commit.
    summary = build_clean_release_summary()

    c1, c2, c3 = st.columns(3)
    c1.metric("Статус", friendly_status(summary.get("status")))
    c2.metric("Tracked файлове", int(summary.get("tracked_file_count", 0)))
    c3.metric("Проблеми за преглед", int(summary.get("blocking_failures", 0)))

    status = str(summary.get("git_status_short", ""))
    if status:
        st.warning("Има незаписани промени. Първо commit/push, после създай чист архив.")
        st.code(status, language="text")
    else:
        st.success("Няма незаписани промени. Можеш да създадеш чист архив.")

    st.subheader("Команда за терминала")
    st.code(str(summary.get("recommended_command", "python .\\scripts\\v103_create_clean_release_checkpoint.py")), language="powershell")

    if st.button("Създай clean ZIP checkpoint", width="stretch"):
        try:
            result = create_clean_release_checkpoint()
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))
        else:
            st.success("Clean ZIP checkpoint е създаден с актуален metadata report вътре в архива.")
            st.code(str(result.get("zip_path")), language="text")
            st.write(result)

    st.subheader("Проверки")
    st.dataframe(_checks_df(summary), width="stretch", hide_index=True)

    forbidden_preview = summary.get("forbidden_tracked_preview") or []
    if forbidden_preview:
        st.subheader("Forbidden tracked preview")
        st.code("\n".join(forbidden_preview), language="text")

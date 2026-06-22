from __future__ import annotations

from pathlib import Path
import csv
import json

import streamlit as st

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

from src.v72_pipeline_refresh_engine import build_pipeline_refresh_plan

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "reports" / "v72_pipeline_refresh_summary.json"
PLAN_PATH = ROOT / "reports" / "v72_pipeline_refresh_plan.csv"


def _load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _show_table(rows):
    if not rows:
        st.info("Няма налични pipeline данни.")
        return

    shown = []
    for row in rows:
        shown.append({
            "Step": row.get("step", ""),
            "Име": row.get("name", ""),
            "Скрипт": row.get("script", ""),
            "Скрипт OK": row.get("script_exists", ""),
            "Артефакти OK": row.get("outputs_ok", ""),
            "Последна промяна": row.get("latest_output_mtime", ""),
            "Run статус": row.get("run_status", ""),
        })

    if pd is not None:
        st.dataframe(pd.DataFrame(shown), use_container_width=True, hide_index=True)
    else:
        st.table(shown)


def render_v72_pipeline_refresh_section():
    st.title("Обновяване на pipeline")
    st.caption(
        "Единен refresh center за weighted pipeline: Step 61–63 и Step 65–71. "
        "При нужда може да включи и core steps v41–v60."
    )

    summary = _load_json(SUMMARY_PATH)
    rows = _load_csv(PLAN_PATH)

    if not summary:
        st.warning(
            "Липсва Step 72 audit report. "
            "Пусни: python scripts/v72_build_pipeline_refresh_plan.py"
        )
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mode", summary.get("mode", "-"))
        col2.metric("Steps", summary.get("steps_planned", 0))
        col3.metric("Scripts OK", "Да" if summary.get("all_scripts_present") else "Не")
        col4.metric("Outputs OK", "Да" if summary.get("all_outputs_present") else "Не")

        st.info(
            "Това е refresh orchestration слой. Той обновява статистически artifacts, "
            "но не е предсказание и не е гаранция за печалба."
        )

    st.subheader("Pipeline status")
    _show_table(rows)

    st.subheader("Действия")

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Audit без обновяване", key="v72_audit_only"):
            with st.spinner("Проверявам pipeline artifacts..."):
                result = build_pipeline_refresh_plan(run_pipeline=False, include_core=False)
            st.success("Audit завърши.")
            st.json(result)
            st.rerun()

    with col_b:
        if st.button("Обнови weighted pipeline Step 61–71", key="v72_run_weighted", type="primary"):
            with st.spinner("Обновявам Step 61–63 и Step 65–71..."):
                result = build_pipeline_refresh_plan(run_pipeline=True, include_core=False)
            if result.get("run_ok"):
                st.success("Weighted pipeline refresh мина успешно.")
            else:
                st.error(f"Pipeline refresh спря при: {result.get('stopped_at')}")
            st.json(result)
            st.rerun()

    with st.expander("Пълен refresh след нов тираж"):
        st.warning(
            "Тази опция пуска core scripts v41–v60 плюс weighted pipeline Step 61–71. "
            "Използвай я след добавяне на нов тираж, когато искаш пълно обновяване."
        )

        if st.button("Пълен refresh v41–v71", key="v72_run_full"):
            with st.spinner("Пускам пълен refresh v41–v71..."):
                result = build_pipeline_refresh_plan(run_pipeline=True, include_core=True)
            if result.get("run_ok"):
                st.success("Пълният refresh мина успешно.")
            else:
                st.error(f"Пълният refresh спря при: {result.get('stopped_at')}")
            st.json(result)
            st.rerun()

    with st.expander("Как работи Step 72"):
        st.markdown(
            """
- **Audit без обновяване** само проверява дали скриптовете и artifacts съществуват.
- **Weighted pipeline refresh** пуска Step 61, 62, 63 и Step 65–71.
- **Пълен refresh v41–v71** пуска core моделите и после weighted pipeline.
- Add Draw auto-refresh вече е подравнен да обновява целия pipeline след запис.
- Training Center вече показва Step 65–71 като част от refresh flow.

Това е технически refresh/control layer, не предсказател на бъдещ тираж.
"""
        )

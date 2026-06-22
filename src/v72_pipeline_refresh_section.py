from __future__ import annotations

from pathlib import Path
import csv
import json

import streamlit as st

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

from src.v72_pipeline_refresh_engine import (
    build_pipeline_refresh_plan,
    git_status_short,
    git_sync_data_models_reports,
)

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
    st.title("Обновяване на анализите")
    st.caption(
        "Център за обновяване на статистическите анализи: Step 61–63 и Step 65–73. "
        "При нужда може да включи и основните стъпки v41–v60."
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
        col1.metric("Режим", summary.get("mode", "-"))
        col2.metric("Стъпки", summary.get("steps_planned", 0))
        col3.metric("Скриптове OK", "Да" if summary.get("all_scripts_present") else "Не")
        col4.metric("Артефакти OK", "Да" if summary.get("all_outputs_present") else "Не")

        st.info(
            "Това е контролен слой за обновяване. Той преизчислява статистическите файлове, "
            "но не е предсказание и не е гаранция за печалба."
        )

    st.subheader("Статус на обновяването")
    _show_table(rows)

    st.subheader("Действия")

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Audit без обновяване", key="v72_audit_only"):
            with st.spinner("Проверявам файловете от анализа..."):
                result = build_pipeline_refresh_plan(run_pipeline=False, include_core=False)
            st.success("Audit завърши.")
            st.json(result)
            st.rerun()

    with col_b:
        if st.button("Обнови статистическия pipeline Step 61–73", key="v72_run_weighted", type="primary"): 
            with st.spinner("Обновявам Step 61–63 и Step 65–73..."):
                result = build_pipeline_refresh_plan(run_pipeline=True, include_core=False)
            if result.get("run_ok"):
                st.success("Статистическият pipeline се обнови успешно.")
            else:
                st.error(f"Обновяването спря при: {result.get('stopped_at')}")
            st.json(result)
            st.rerun()

    with st.expander("Пълен refresh след нов тираж"):
        st.warning(
            "Тази опция пуска core scripts v41–v60 плюс weighted pipeline Step 61–73. "
            "Използвай я след добавяне на нов тираж, когато искаш пълно обновяване."
        )

        if st.button("Пълно обновяване v41–v73", key="v72_run_full"): 
            with st.spinner("Пускам пълно обновяване v41–v73..."):
                result = build_pipeline_refresh_plan(run_pipeline=True, include_core=True)
            if result.get("run_ok"):
                st.success("Пълният refresh мина успешно.")
            else:
                st.error(f"Пълният refresh спря при: {result.get('stopped_at')}")
            st.json(result)
            st.rerun()



    st.subheader("GitHub синхронизация след обновяване")

    git_info = git_status_short()
    current_status = str(git_info.get("status", "") or "").strip()

    if current_status:
        st.warning("Има локални промени. Този бутон commit-ва само data/, models/ и reports/.")
        st.code(current_status, language="text")
    else:
        st.success("Git status е clean. Няма чакащи локални промени.")

    commit_message = st.text_input(
        "Съобщение за GitHub commit",
        value="Refresh lottery data models and reports after pipeline update",
        key="v72_github_sync_commit_message",
    )

    confirm_sync = st.checkbox(
        "Потвърждавам: commit/push само на data/, models/ и reports/",
        key="v72_github_sync_confirm",
    )

    if st.button(
        "Запази и качи data/models/reports в GitHub",
        key="v72_github_sync_button",
        disabled=not confirm_sync,
    ):
        with st.spinner("Изпълнявам git add / commit / push за data/models/reports..."):
            result = git_sync_data_models_reports(commit_message)

        if result.get("ok"):
            if result.get("status") == "nothing_to_commit":
                st.info(result.get("message"))
            else:
                st.success(result.get("message"))
                st.write("Commit:", result.get("commit", ""))
        else:
            st.error(result.get("message", "GitHub синхронизацията не успя."))

        staged = result.get("staged_files") or []
        if staged:
            st.write("Файлове:")
            st.code("\\n".join(staged), language="text")

        with st.expander("Git технически детайли"):
            st.json(result)


    with st.expander("Как работи Step 72"):
        st.markdown(
            """
- **Audit без обновяване** само проверява дали скриптовете и artifacts съществуват.
- **Статистическо обновяване** пуска Step 61, 62, 63 и Step 65–73.
- **Пълно обновяване v41–v73** пуска основните модели и после статистическия pipeline.
- Add Draw auto-refresh вече е подравнен да обновява целия pipeline след запис.
- Training Center вече показва Step 65–73 като част от refresh flow.

Това е технически контролен слой за обновяване, не предсказател на бъдещ тираж.
"""
        )

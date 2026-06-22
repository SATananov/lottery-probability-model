from __future__ import annotations

from pathlib import Path
import csv
import json

import streamlit as st

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

from src.v74_model_dependency_sync_center_engine import build_model_dependency_sync_center

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "reports" / "v74_model_dependency_summary.json"
STATUS_PATH = ROOT / "reports" / "v74_model_sync_status.csv"
MAP_PATH = ROOT / "reports" / "v74_model_dependency_map.csv"


def _load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _show_table(rows, columns):
    if not rows:
        st.info("Няма данни за показване.")
        return
    shown = []
    for row in rows:
        shown.append({label: row.get(key, "") for label, key in columns})
    if pd is not None:
        st.dataframe(pd.DataFrame(shown), use_container_width=True, hide_index=True)
    else:
        st.table(shown)


def render_v74_model_dependency_sync_center_section():
    st.title("Контрол на синхрона")
    st.caption(
        "Показва дали dataset-ите, моделите, отчетите и pipeline стъпките са подравнени. "
        "Това е диагностичен център, не прогноза и не гаранция за печалба."
    )

    summary = _load_json(SUMMARY_PATH)
    if not summary:
        st.warning("Липсва Step 74 report. Пусни: python scripts/v74_build_model_dependency_sync_center.py")
        return

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Статус", summary.get("status", "-"))
    col2.metric("Проверени", summary.get("models_checked", 0))
    col3.metric("Синхронизирани", summary.get("synced_models", 0))
    col4.metric("За обновяване", summary.get("stale_models", 0))
    col5.metric("Липсващи", summary.get("missing_models", 0))

    dataset_sync = summary.get("dataset_sync", {}) or {}
    if dataset_sync.get("rows_synced") and dataset_sync.get("latest_draw_synced"):
        st.success("Главните dataset-и са синхронизирани по редове и последен тираж.")
    else:
        st.warning("Има разминаване между главните dataset-и. Провери data refresh flow-а.")

    st.subheader("Главни dataset-и")
    dataset_rows = []
    for item in summary.get("datasets", []) or []:
        dataset_rows.append({
            "path": item.get("path", ""),
            "rows": item.get("rows", ""),
            "latest_date": item.get("latest_date", ""),
            "latest_draw_no": item.get("latest_draw_no", ""),
            "latest_numbers": item.get("latest_numbers", ""),
            "mtime": item.get("mtime", ""),
        })
    _show_table(dataset_rows, [
        ("Dataset", "path"),
        ("Редове", "rows"),
        ("Последна дата", "latest_date"),
        ("Последен тираж", "latest_draw_no"),
        ("Последни числа", "latest_numbers"),
        ("Последна промяна", "mtime"),
    ])

    st.subheader("Синхрон на моделите")
    status_rows = _load_csv(STATUS_PATH)
    _show_table(status_rows, [
        ("Step", "step"),
        ("Име", "label"),
        ("Категория", "category"),
        ("Статус", "sync_status"),
        ("Помага на", "feeds"),
        ("Роля", "role"),
    ])

    st.subheader("Карта на зависимостите")
    edge_rows = _load_csv(MAP_PATH)
    _show_table(edge_rows[:200], [
        ("От", "from"),
        ("Към", "to"),
        ("Тип", "type"),
        ("Описание", "description"),
    ])

    if st.button("Обнови Step 74 audit", key="v74_refresh_button", type="primary"):
        with st.spinner("Проверявам синхрона между моделите..."):
            result = build_model_dependency_sync_center()
        st.success("Step 74 audit е обновен.")
        st.json(result)
        st.rerun()

    with st.expander("Как да се чете този център"):
        st.markdown(
            """
- **Синхронизиран** означава, че входните dataset-и/артефакти и изходите са налични и изходите не изглеждат по-стари от входовете.
- **Нужно обновяване** означава, че входен файл е по-нов от изхода и е добре да се пусне pipeline refresh.
- **Липсва файл** означава липсващ script, input или output artifact.
- Моделите не се учат сляпо един от друг. Те си помагат чрез сигнали, reliability, тегла, ensemble и portfolio логика.
- Истината за обновяване остава реалният тираж, не прогнозата на друг модел.
"""
        )

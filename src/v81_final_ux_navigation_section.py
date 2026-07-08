from __future__ import annotations

from pathlib import Path
import csv
import json
from typing import Any

import streamlit as st

from src.v81_final_ux_navigation_engine import build_final_ux_navigation_center

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
SUMMARY_JSON = REPORTS_DIR / "v81_final_ux_navigation_summary.json"
GROUPS_CSV = REPORTS_DIR / "v81_navigation_groups.csv"
PAGES_CSV = REPORTS_DIR / "v81_navigation_page_audit.csv"
LABELS_CSV = REPORTS_DIR / "v81_streamlit_label_audit.csv"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _show_rows(title: str, rows: list[dict[str, str]]) -> None:
    st.subheader(title)
    if rows:
        st.dataframe(rows, width="stretch", hide_index=True)
    else:
        st.info("Няма налични редове за показване.")


def render_v81_final_ux_navigation_section() -> None:
    st.title("Финален UX контрол")
    st.caption("Step 81 — финална навигационна подредба и UX проверка на страниците.")
    st.warning("Този модул е организационен и визуален контрол. Той не е прогноза и не е гаранция за печалба.")
    if st.button("Обнови финалния UX контрол"):
        with st.spinner("Обновяване на UX/навигационния одит..."):
            summary = build_final_ux_navigation_center()
        if summary.get("status") == "OK":
            st.success("Финалният UX контрол е обновен успешно.")
        else:
            st.warning("Финалният UX контрол намери елементи за преглед.")
    summary = _load_json(SUMMARY_JSON)
    if not summary:
        summary = build_final_ux_navigation_center()
    cols = st.columns(4)
    cols[0].metric("Статус", str(summary.get("status", "-")))
    cols[1].metric("Групи", int(summary.get("groups_count", 0)))
    cols[2].metric("Страници", int(summary.get("navigation_pages_count", 0)))
    cols[3].metric("Проблеми", int(summary.get("issues_found", 0)))
    st.markdown("### Какво проверява този модул")
    st.markdown(
        "- дали финалните групи в менюто са налични;\n"
        "- дали важните финални страници са видими;\n"
        "- дали има повторени страници в навигацията;\n"
        "- дали системният ред е логичен: обновяване, финален системен одит, UX контрол, sync контрол."
    )
    issues = summary.get("issues_preview") or []
    if issues:
        st.error("Има елементи за преглед:")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.success("Навигацията е подредена и основните UX labels са налични.")
    _show_rows("Навигационни групи", _load_rows(GROUPS_CSV))
    _show_rows("Страници по групи", _load_rows(PAGES_CSV))
    _show_rows("Streamlit labels", _load_rows(LABELS_CSV))

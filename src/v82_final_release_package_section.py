from __future__ import annotations

from pathlib import Path
import csv
import json
from typing import Any

import streamlit as st

from src.v82_final_release_package_engine import build_final_release_package_center

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
SUMMARY_JSON = REPORTS_DIR / "v82_final_release_summary.json"
CHECKLIST_CSV = REPORTS_DIR / "v82_release_readiness_checklist.csv"
EXCLUSIONS_CSV = REPORTS_DIR / "v82_clean_zip_exclusion_plan.csv"
MANIFEST_CSV = REPORTS_DIR / "v82_release_file_manifest.csv"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _load_rows(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = [dict(row) for row in csv.DictReader(f)]
    if limit is not None:
        return rows[:limit]
    return rows


def _show_rows(title: str, rows: list[dict[str, str]]) -> None:
    st.subheader(title)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("Няма налични редове за показване.")


def render_v82_final_release_package_section() -> None:
    st.title("Финален пакет за предаване")
    st.caption("Step 82 — финална готовност на пакета и чист ZIP контрол преди checkpoint.")
    st.warning("Този модул подготвя чист контролен ZIP. Той не е прогноза и не е гаранция за печалба.")

    if st.button("Обнови финалния контрол на готовността"):
        with st.spinner("Обновяване на проверките за готовност на финалния пакет..."):
            summary = build_final_release_package_center()
        if summary.get("status") == "OK":
            st.success("Финалният контрол на готовността е обновен успешно.")
        else:
            st.warning("Контролът на готовността намери елементи за преглед.")

    summary = _load_json(SUMMARY_JSON)
    if not summary:
        summary = build_final_release_package_center()

    cols = st.columns(4)
    cols[0].metric("Статус", str(summary.get("status", "-")))
    cols[1].metric("Набори данни", int(summary.get("datasets_checked", 0)))
    cols[2].metric("Файлове в списъка", int(summary.get("manifest_files_count", 0)))
    cols[3].metric("Проблеми", int(summary.get("issues_found", 0)))

    st.markdown("### Какво заключва Step 82")
    st.markdown(
        "- проверява файловете, готови за предаване и финалните набори данни;\n"
        "- описва кои файлове влизат в чист ZIP контролен архив;\n"
        "- пази списък с файлове, които не трябва да попадат в чист ZIP;\n"
        "- потвърждава финалната верига: Step 79 → Step 80 → Step 81 → Step 82 → Step 74."
    )

    issues = summary.get("issues_preview") or []
    if issues:
        st.error("Има елементи за преглед преди финален ZIP:")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.success("Проверките за готовност за предаване са чисти. Можеш да създадеш чист ZIP контролен архив след commit и push.")

    st.markdown("### Финална логика на синхрона")
    for item in summary.get("sync_expectations", []):
        expected = " -> ".join(str(step) for step in item.get("expected", []))
        st.write(f"- **{item.get('name', '-')}:** `{expected}`")

    _show_rows("Списък за готовност", _load_rows(CHECKLIST_CSV))
    _show_rows("План за изключване от чистия ZIP", _load_rows(EXCLUSIONS_CSV))
    _show_rows("Преглед на списъка с файлове", _load_rows(MANIFEST_CSV, limit=100))

from __future__ import annotations

from pathlib import Path
import csv
import json

import streamlit as st

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

ROOT = Path(__file__).resolve().parents[1]

SUMMARY_PATH = ROOT / "reports" / "v71_ticket_pack_summary.json"
CSV_PATH = ROOT / "reports" / "v71_ticket_pack.csv"
JSON_PATH = ROOT / "reports" / "v71_ticket_pack.json"
TXT_PATH = ROOT / "reports" / "v71_ticket_pack.txt"
MD_PATH = ROOT / "reports" / "v71_ticket_pack_printable.md"
HTML_PATH = ROOT / "reports" / "v71_ticket_pack_printable.html"

TICKET_COLUMNS = [
    ("ticket_id", "Фиш"),
    ("numbers_display", "Числа"),
    ("average_step66_score", "Средна Step 66 оценка"),
    ("strategy_label", "Стратегия"),
    ("odd_count", "Нечетни"),
    ("even_count", "Четни"),
    ("low_count", "Ниски"),
    ("high_count", "Високи"),
    ("number_range", "Диапазон"),
    ("historical_exact_match", "Историческо повторение"),
]


def _load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _read_bytes(path):
    if not path.exists():
        return b""
    return path.read_bytes()


def _read_text(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def _as_float(value, default=0.0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return float(text.replace("%", "").replace(",", "."))
    except (TypeError, ValueError):
        return default


def _as_int(value, default=0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(float(text.replace(",", ".")))
    except (TypeError, ValueError):
        return default


def _format_value(key, value):
    if key == "average_step66_score":
        return f"{_as_float(value):.3f}"

    if key in {"ticket_id", "odd_count", "even_count", "low_count", "high_count", "number_range"}:
        return _as_int(value)

    if key == "historical_exact_match":
        return "Да" if str(value).strip().lower() in {"true", "1", "yes"} else "Не"

    return value


def _localize_rows(rows):
    result = []
    for row in rows:
        item = {}
        for source_key, bg_label in TICKET_COLUMNS:
            item[bg_label] = _format_value(source_key, row.get(source_key, ""))
        result.append(item)
    return result


def _show_table(rows):
    if not rows:
        st.info("Няма налични фишове за показване.")
        return

    localized = _localize_rows(rows)

    if pd is not None:
        st.dataframe(pd.DataFrame(localized), use_container_width=True, hide_index=True)
    else:
        st.table(localized)


def render_v71_ticket_pack_export_section():
    st.title("Пакет за игра")
    st.caption(
        "Готов export/print пакет от Step 70 applied portfolio. "
        "Това е статистически reference пакет, не гаранция за печалба."
    )

    summary = _load_json(SUMMARY_PATH)
    rows = _load_csv(CSV_PATH)

    if not summary:
        st.warning(
            "Липсва Step 71 export report. "
            "Пусни: python scripts/v71_build_ticket_pack_export.py"
        )
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Фишове", summary.get("tickets_exported", 0))
    col2.metric("Промени", summary.get("changes_included", 0))
    col3.metric("Applied score", f"{summary.get('applied_portfolio_score', 0)} / 100")
    col4.metric("Top20", f"{summary.get('applied_top20_coverage', 0)} / 20")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Уникални числа", summary.get("applied_unique_numbers", 0))
    col6.metric("Repeated pairs", summary.get("applied_repeated_pairs", 0))
    col7.metric("Repeated triples", summary.get("applied_repeated_triples", 0))
    col8.metric("Исторически съвпадения", summary.get("applied_historical_exact_matches", 0))

    st.success("Пакетът е готов за преглед, печат и export.")
    st.info("Лотарийните тегления са случайни. Този пакет не е обещание за печалба.")

    st.subheader("Фишове")
    _show_table(rows)

    st.subheader("Бърз printable preview")
    txt_preview = _read_text(TXT_PATH)
    if txt_preview:
        st.code(txt_preview, language="text")

    st.subheader("Export файлове")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.download_button(
            "CSV export",
            data=_read_bytes(CSV_PATH),
            file_name="v71_ticket_pack.csv",
            mime="text/csv",
        )
        st.download_button(
            "TXT export",
            data=_read_bytes(TXT_PATH),
            file_name="v71_ticket_pack.txt",
            mime="text/plain",
        )

    with col_b:
        st.download_button(
            "JSON export",
            data=_read_bytes(JSON_PATH),
            file_name="v71_ticket_pack.json",
            mime="application/json",
        )
        st.download_button(
            "Markdown print",
            data=_read_bytes(MD_PATH),
            file_name="v71_ticket_pack_printable.md",
            mime="text/markdown",
        )

    with col_c:
        st.download_button(
            "HTML print page",
            data=_read_bytes(HTML_PATH),
            file_name="v71_ticket_pack_printable.html",
            mime="text/html",
        )

    with st.expander("Как работи Step 71"):
        st.markdown(
            """
1. Чете **Step 70 applied portfolio**.
2. Подготвя фишовете в CSV, JSON, TXT, Markdown и HTML.
3. Показва printable preview в app-а.
4. Пази safe note във всички export файлове.
5. Не променя Step 70, Step 69 или Step 67.

Това е export/print слой, не предсказател на бъдещ тираж.
"""
        )

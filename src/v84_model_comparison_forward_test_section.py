from __future__ import annotations

from pathlib import Path
import csv
import json
from typing import Any

import streamlit as st

from src.v84_model_comparison_forward_test_engine import (
    build_model_comparison_forward_test_center,
    create_snapshot_from_current_candidates,
    add_manual_snapshot_row,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data"

SUMMARY_JSON = REPORTS_DIR / "v84_model_comparison_summary.json"
CANDIDATES_CSV = REPORTS_DIR / "v84_model_source_candidates.csv"
RESULTS_CSV = REPORTS_DIR / "v84_model_comparison_results.csv"
SNAPSHOT_CSV = DATA_DIR / "v84_model_forward_test_snapshots.csv"

COLUMN_LABELS = {
    "model_key": "Ключ на модела",
    "model_label": "Модел",
    "ticket_label": "Комбинация / препоръка",
    "numbers": "Числа",
    "source_file": "Източник",
    "source_priority": "Приоритет",
    "safe_note": "Важно уточнение",
    "snapshot_id": "ID на заключен запис",
    "snapshot_name": "Име на заключен запис",
    "snapshot_created_at": "Записан на",
    "dataset_draw_index_at_snapshot": "Брой тиражи при запис",
    "dataset_latest_draw_date_at_snapshot": "Дата на последен тираж при запис",
    "status": "Статус",
    "target_draw_index": "Проверен тираж",
    "target_draw_date": "Дата на проверка",
    "target_numbers": "Реални числа",
    "hits_count": "Познати числа",
    "hit_numbers": "Познати",
    "result_bucket": "Резултат",
    "tickets_evaluated": "Проверени комбинации",
    "average_hits": "Средно познати",
    "max_hits": "Най-добър резултат",
    "pct_at_least_2": "% с 2+",
    "pct_at_least_3": "% с 3+",
    "pct_at_least_4": "% с 4+",
}


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


def _translate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    translated = []
    for row in rows:
        translated.append({
            COLUMN_LABELS.get(str(key), str(key)): value
            for key, value in row.items()
        })
    return translated


def _show_table(title: str, rows: list[dict[str, Any]]) -> None:
    st.subheader(title)
    if rows:
        st.dataframe(_translate_rows(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Няма налични редове за показване.")


def render_v84_model_comparison_forward_test_section() -> None:
    st.title("Сравнение на модели")
    st.caption("Step 84 — център за реална проверка на моделите във времето.")

    st.warning(
        "Този модул сравнява модели само по предварително записани препоръки. "
        "Това е статистическа проверка, не прогноза и не гаранция за печалба."
    )

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Обнови анализа"):
            with st.spinner("Обновяване на кандидатите и резултатите..."):
                summary = build_model_comparison_forward_test_center()
            st.success(f"Готово. Намерени кандидати: {summary.get('current_candidates', 0)}")

    with col_b:
        if st.button("Запази заключен запис преди тираж"):
            with st.spinner("Записване на текущите препоръки..."):
                result = create_snapshot_from_current_candidates("Автоматичен заключен запис преди тираж")
            st.success(f"Записани редове: {result.get('rows_added', 0)}")

    summary = _load_json(SUMMARY_JSON)
    if not summary:
        summary = build_model_comparison_forward_test_center()

    metric_cols = st.columns(5)
    metric_cols[0].metric("Статус", str(summary.get("status", "-")))
    metric_cols[1].metric("Кандидат комбинации", int(summary.get("current_candidates", 0)))
    metric_cols[2].metric("Заключени записи", int(summary.get("locked_snapshot_records", summary.get("snapshots_recorded", 0))))
    metric_cols[3].metric("Редове в записите", int(summary.get("snapshot_rows_recorded", 0)))
    metric_cols[4].metric("Сравнени модели", int(summary.get("models_compared", 0)))

    st.markdown("### Как се използва")
    st.markdown(
        "Преди тиража натискаш **Запази заключен запис преди тираж**. "
        "След като излезе реалният тираж, въвеждаш го в **Добавяне на тираж**, "
        "после се връщаш тук и натискаш **Обнови анализа**. "
        "Така виждаме кой модел реално се е държал по-добре."
    )

    st.markdown("### Ръчно добавяне на контролна комбинация")
    with st.form("v84_manual_snapshot_form"):
        model_label = st.text_input("Име на модела", value="Ръчна контролна комбинация")
        numbers_text = st.text_input("Числа, разделени със запетая или интервал", value="")
        submitted = st.form_submit_button("Запази ръчен заключен запис")

    if submitted:
        result = add_manual_snapshot_row(model_label, numbers_text, "Ръчен заключен запис преди тираж")
        if result.get("status") == "OK":
            st.success(f"Записана комбинация в заключен запис: {result.get('numbers')}")
        else:
            st.error(str(result.get("message", "Неуспешен запис.")))

    summary_rows = summary.get("summary_rows") or []
    _show_table("Обобщение по модели", summary_rows)
    _show_table("Текущи открити кандидати", _load_rows(CANDIDATES_CSV))
    _show_table("Заключени записи и редове", _load_rows(SNAPSHOT_CSV))
    _show_table("Резултати след реален тираж", _load_rows(RESULTS_CSV))

    st.info(
        "Най-важната таблица е „Обобщение по модели“. Там гледаме средно познати числа, "
        "най-добър резултат и проценти с 2+, 3+ и 4+ познати."
    )

from __future__ import annotations

from pathlib import Path
import csv
import json

import streamlit as st

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

from src.v73_ticket_pack_performance_tracker_engine import (
    evaluate_current_pack_against_draw,
    build_ticket_pack_performance_tracker,
)

ROOT = Path(__file__).resolve().parents[1]

SUMMARY_PATH = ROOT / "reports" / "v73_ticket_pack_performance_summary.json"
HISTORY_PATH = ROOT / "reports" / "v73_ticket_pack_performance_history.csv"


def _load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _show_history(rows):
    if not rows:
        st.info("Все още няма официална история. Тя ще се запише, когато Step 73 бъде вързан към Add Draw.")
        return

    shown = []
    for row in reversed(rows[-30:]):
        shown.append({
            "Дата оценка": row.get("evaluated_at", ""),
            "Източник": row.get("source", ""),
            "Тираж дата": row.get("draw_date", ""),
            "Тираж": row.get("draw_number", ""),
            "Числа": row.get("draw_numbers", ""),
            "Най-добър фиш": row.get("best_ticket_id", ""),
            "Best hits": row.get("best_hit_count", ""),
            "Покрити числа": row.get("package_unique_hits", ""),
            "2 hits": row.get("tickets_with_2_hits", ""),
            "3 hits": row.get("tickets_with_3_hits", ""),
            "4 hits": row.get("tickets_with_4_hits", ""),
        })

    if pd is not None:
        st.dataframe(pd.DataFrame(shown), use_container_width=True, hide_index=True)
    else:
        st.table(shown)


def _show_ticket_results(rows):
    shown = []
    for row in rows:
        shown.append({
            "Фиш": row.get("ticket_id", ""),
            "Стратегия": row.get("strategy_label", ""),
            "Фиш числа": str(row.get("ticket_numbers", "")).replace(",", ", "),
            "Съвпадения": str(row.get("matched_numbers", "")).replace(",", ", "),
            "Hits": row.get("hit_count", 0),
            "Avg Step66": row.get("average_step66_score", ""),
        })

    if pd is not None:
        st.dataframe(pd.DataFrame(shown), use_container_width=True, hide_index=True)
    else:
        st.table(shown)


def render_v73_ticket_pack_performance_tracker_section():
    st.title("Представяне на пакета")
    st.caption(
        "Проверява текущия активен Step 71 пакет срещу нови числа. "
        "Това трябва да се случва преди новият тираж да обнови dataset-а."
    )

    summary = _load_json(SUMMARY_PATH)
    if not summary:
        st.warning("Липсва обобщение за Step 73. Пусни: python scripts/v73_build_ticket_pack_performance_tracker.py")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Активни фишове", summary.get("active_pack_tickets", 0))
    col2.metric("History rows", summary.get("history_rows", 0))
    col3.metric("Pack snapshot", summary.get("active_pack_snapshot_id", "-"))

    st.info(
        "Ръчното поле тук е за preview. Официалната история трябва да се записва от Add Draw flow-а "
        "преди dataset refresh."
    )

    st.subheader("Manual preview срещу 6 числа")

    cols = st.columns(6)
    numbers = []
    for index, col in enumerate(cols, start=1):
        with col:
            numbers.append(
                st.number_input(
                    f"N{index}",
                    min_value=1,
                    max_value=49,
                    value=index,
                    step=1,
                    key=f"v73_preview_n{index}",
                )
            )

    if st.button("Провери текущия пакет срещу тези числа", key="v73_preview_button"):
        try:
            evaluation = evaluate_current_pack_against_draw(
                numbers,
                source="manual_preview",
                persist=False,
            )
            history = evaluation["history_row"]
            st.success(
                f"Preview готов: най-добър фиш {history['best_ticket_id']} "
                f"с {history['best_hit_count']} попадения. "
                f"Пакетът покрива {history['package_unique_hits']} от 6 изтеглени числа."
            )
            _show_ticket_results(evaluation["ticket_results"])
        except Exception as exc:
            st.error(f"Step 73 preview failed: {exc}")

    st.subheader("Официална история")
    history_rows = _load_csv(HISTORY_PATH)
    _show_history(history_rows)

    if st.button("Обнови обобщението на Step 73", key="v73_refresh_summary"):
        result = build_ticket_pack_performance_tracker()
        st.success("Обобщението на Step 73 е обновено.")
        st.json(result)
        st.rerun()

    with st.expander("Как работи Step 73"):
        st.markdown(
            """
- Step 73 не генерира нови числа.
- Той взима текущия активен **Step 71 пакет**.
- При нов тираж трябва първо да провери стария пакет срещу новите числа.
- После резултатът се записва в performance history.
- Едва след това новият тираж се добавя в dataset-а и pipeline-ът се обновява.

Това пази проверката честна: пакетът се оценява преди да е видял новия тираж.
"""
        )

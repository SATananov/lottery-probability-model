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
    COMBINATIONS_PER_PHYSICAL_TICKET,
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
        st.info("Все още няма официална история. Тя ще се запише автоматично от „Добавяне на тираж“ преди обновяването на данните.")
        return

    shown = []
    for row in reversed(rows[-30:]):
        shown.append({
            "Дата на оценка": row.get("evaluated_at", ""),
            "Източник": row.get("source", ""),
            "Дата на тиража": row.get("draw_date", ""),
            "Тираж №": row.get("draw_number", ""),
            "Изтеглени числа": row.get("draw_numbers", ""),
            "Най-добра комбинация": row.get("best_combination_label") or row.get("best_ticket_id", ""),
            "Познати числа": row.get("best_hit_count", ""),
            "Покрити числа от пакета": row.get("package_unique_hits", ""),
            "Комбинации с 2 познати": row.get("tickets_with_2_hits", ""),
            "Комбинации с 3 познати": row.get("tickets_with_3_hits", ""),
            "Комбинации с 4 познати": row.get("tickets_with_4_hits", ""),
        })

    if pd is not None:
        st.dataframe(pd.DataFrame(shown), use_container_width=True, hide_index=True)
    else:
        st.table(shown)


def _show_ticket_results(rows):
    shown = []
    for row in rows:
        shown.append({
            "Комбинация": row.get("combination_label") or row.get("ticket_id", ""),
            "Стратегия": row.get("strategy_label", ""),
            "Числа в комбинацията": str(row.get("ticket_numbers", "")).replace(",", ", "),
            "Познати числа": str(row.get("matched_numbers", "")).replace(",", ", "),
            "Брой познати": row.get("hit_count", 0),
            "Средна Step 66 оценка": row.get("average_step66_score", ""),
        })

    if pd is not None:
        st.dataframe(pd.DataFrame(shown), use_container_width=True, hide_index=True)
    else:
        st.table(shown)


def render_v73_ticket_pack_performance_tracker_section():
    st.title("Представяне на пакета")
    st.caption(
        "Проверява текущия активен Step 71 пакет срещу нови числа, преди новият тираж да обнови данните. "
        f"В един физически фиш могат да се попълнят {COMBINATIONS_PER_PHYSICAL_TICKET} комбинации по 6 числа."
    )

    summary = _load_json(SUMMARY_PATH)
    if not summary:
        st.warning("Липсва обобщение за Step 73. Пусни: python scripts/v73_build_ticket_pack_performance_tracker.py")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Комбинации", summary.get("active_pack_combinations", summary.get("active_pack_tickets", 0)))
    col2.metric("Физически фишове", summary.get("active_pack_physical_tickets", 0))
    col3.metric("Записи в историята", summary.get("history_rows", 0))
    col4.metric("Заключен запис на пакета", summary.get("active_pack_snapshot_id", "-"))

    st.info(
        "Ръчното поле е само за предварителна проверка. Официалният резултат се записва от „Добавяне на тираж“ "
        "преди обновяването на данните, за да остане проверката честна."
    )

    st.subheader("Ръчна проверка срещу 6 числа")

    cols = st.columns(6)
    numbers = []
    for index, col in enumerate(cols, start=1):
        with col:
            numbers.append(
                st.number_input(
                    f"Число {index}",
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
                f"Проверката е готова: най-добра е {history['best_combination_label']} "
                f"с {history['best_hit_count']} познати числа. "
                f"Пакетът покрива {history['package_unique_hits']} от 6 изтеглени числа."
            )
            _show_ticket_results(evaluation["ticket_results"])
        except Exception as exc:
            st.error(f"Step 73 проверката не успя: {exc}")

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
            f"""
- Step 73 не генерира нови числа.
- Той взима текущия активен **Step 71 пакет**.
- Една комбинация е ред от 6 числа.
- Един физически фиш може да съдържа **{COMBINATIONS_PER_PHYSICAL_TICKET} комбинации**.
- Ако пакетът има 8 комбинации, това означава 2 физически фиша за попълване.
- При нов тираж първо се проверява старият пакет срещу новите числа.
- После резултатът се записва в историята на представянето.
- Едва след това новият тираж се добавя в данните и веригата за обновяване се обновява.

Това пази проверката честна: пакетът се оценява преди да е видял новия тираж.
"""
        )

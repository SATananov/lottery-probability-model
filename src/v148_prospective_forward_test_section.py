from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.v148_prospective_forward_test_engine import (
    ACTIVE_PACKAGES_CSV_PATH,
    LEDGER_INDEX_CSV_PATH,
    SETTLEMENTS_CSV_PATH,
    SUMMARY_JSON_PATH,
    lock_next_draw_forecast,
    settle_available_locked_forecast,
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _load_csv(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def render_v148_prospective_forward_test_section() -> None:
    st.title("Проспективен forward test")
    st.caption("Step 148 — предварително заключени evaluation packages и append-only ledger за бъдещи официални тиражи.")
    st.warning(
        "Това е research-only протокол. Показаните комбинации са заключени evaluation packages, "
        "не са production препоръки или реални фишове и не гарантират печалба."
    )

    summary = _load_json(SUMMARY_JSON_PATH)
    active = summary.get("active_lock") or {}
    metrics = st.columns(6)
    metrics[0].metric("Статус", str(summary.get("status", "unknown")).upper())
    metrics[1].metric("Оценени тиражи", f"{int(summary.get('eligible_settled_draws', 0))} / {int(summary.get('target_settled_draws', 30))}")
    metrics[2].metric("Остават", int(summary.get("remaining_draws", 30)))
    metrics[3].metric("Следващ milestone", summary.get("next_milestone") or "Завършен")
    metrics[4].metric("Ledger events", int(summary.get("ledger_event_count", 0)))
    metrics[5].metric("Integrity", "PASS" if summary.get("ledger_integrity_ok") else "FAIL")

    if active:
        st.success(
            f"Активен pre-draw lock: {active.get('lock_id')} · очакван тираж {active.get('expected_draw_key')} · "
            f"заключен {active.get('locked_at_utc')}"
        )
    else:
        st.info("В момента няма активен pre-draw lock.")

    left, right = st.columns(2)
    with left:
        if st.button("Заключи следващия невидян тираж", use_container_width=True):
            try:
                result = lock_next_draw_forecast()
                st.success("Новият lock е създаден." if result.get("created") else f"Няма промяна: {result.get('reason')}")
                st.rerun()
            except Exception as exc:
                st.error(f"Lock операцията е блокирана: {exc}")
    with right:
        if st.button("Провери и оцени след официален sync", type="primary", use_container_width=True):
            try:
                result = settle_available_locked_forecast(auto_lock_next=True)
                st.success("Заключеният тираж е оценен и следващият е заключен." if result.get("settled") else f"Няма settlement: {result.get('reason')}")
                st.rerun()
            except Exception as exc:
                st.error(f"Settlement операцията е блокирана: {exc}")

    st.markdown("### Натрупани prospective резултати")
    aggregate = summary.get("aggregate_results") or {}
    aggregate_rows = []
    for method, values in aggregate.items():
        aggregate_rows.append(
            {
                "Метод": method,
                "Оценени тиражи": values.get("eligible_draws", 0),
                "Среден най-добър резултат": values.get("average_best_hits"),
            }
        )
    if aggregate_rows:
        st.dataframe(pd.DataFrame(aggregate_rows), use_container_width=True, hide_index=True)

    settlement_rows = _load_csv(SETTLEMENTS_CSV_PATH)
    if settlement_rows:
        st.markdown("### Оценени бъдещи тиражи")
        st.dataframe(pd.DataFrame(settlement_rows), use_container_width=True, hide_index=True)

    with st.expander("Активни заключени evaluation packages", expanded=False):
        st.caption("Тези редове се показват само за audit прозрачност; не са предназначени за реална игра.")
        package_rows = _load_csv(ACTIVE_PACKAGES_CSV_PATH)
        if package_rows:
            st.dataframe(pd.DataFrame(package_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Няма активни заключени evaluation packages.")

    with st.expander("SHA-256 ledger", expanded=False):
        ledger_rows = _load_csv(LEDGER_INDEX_CSV_PATH)
        if ledger_rows:
            st.dataframe(pd.DataFrame(ledger_rows), use_container_width=True, hide_index=True)

    st.markdown("### Протоколни защити")
    st.markdown(
        "- Прогнозата се заключва преди целевият тираж да влезе в canonical dataset.\n"
        "- Всеки ledger event е свързан с предишния чрез SHA-256.\n"
        "- Тираж без предварителен lock се изключва и не се backfill-ва.\n"
        "- Step 146 параметрите са замразени; няма tuning по време на 30-тиражния прозорец.\n"
        "- Резултатът се оценява преди наблюдаваният тираж да може да участва в следващия lock.\n"
        "- След 10, 20 или 30 тиража няма автоматично production promotion."
    )

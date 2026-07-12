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
from src.v150_global_ui_polish import technical_details_enabled, translate_value, ui_text


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


def _t(bg: str, en: str) -> str:
    return ui_text(bg, en, st)


def render_v148_prospective_forward_test_section() -> None:
    st.title(_t("Проспективна проверка", "Prospective Evaluation"))
    st.caption(
        _t(
            "Предварително заключени пакети за оценяване и защитен дневник само с добавяне за бъдещи официални тиражи.",
            "Pre-draw locked evaluation packages and an append-only ledger for future official draws.",
        )
    )
    st.warning(
        _t(
            "Това е протокол само за изследване. Показаните комбинации са пакети за оценяване, не са препоръки за реална игра и не гарантират печалба.",
            "This is a research-only protocol. Displayed combinations are evaluation packages, not real-play recommendations, and do not guarantee a win.",
        )
    )

    summary = _load_json(SUMMARY_JSON_PATH)
    active = summary.get("active_lock") or {}
    primary = st.columns(3)
    primary[0].metric(_t("Статус", "Status"), translate_value(summary.get("status", "unknown")))
    primary[1].metric(_t("Оценени тиражи", "Evaluated draws"), f"{int(summary.get('eligible_settled_draws', 0))} / {int(summary.get('target_settled_draws', 30))}")
    primary[2].metric(_t("Оставащи тиражи", "Remaining draws"), int(summary.get("remaining_draws", 30)))
    secondary = st.columns(3)
    secondary[0].metric(_t("Следваща контролна точка", "Next milestone"), summary.get("next_milestone") or _t("Завършено", "Completed"))
    secondary[1].metric(_t("Събития в защитения дневник", "Ledger events"), int(summary.get("ledger_event_count", 0)))
    secondary[2].metric(_t("Цялост на дневника", "Ledger integrity"), _t("Потвърдена", "Passed") if summary.get("ledger_integrity_ok") else _t("Нарушена", "Failed"))

    if active:
        if technical_details_enabled(st):
            st.success(_t(
                f"Има активно заключване преди тиража: {active.get('lock_id')} · очакван тираж {active.get('expected_draw_key')}",
                f"An active pre-draw lock exists: {active.get('lock_id')} · expected draw {active.get('expected_draw_key')}",
            ))
        else:
            st.success(_t(
                f"Има активно заключване преди тиража. Очакван официален тираж: {active.get('expected_draw_key')}.",
                f"An active pre-draw lock exists. Expected official draw: {active.get('expected_draw_key')}.",
            ))
    else:
        st.info(_t("В момента няма активно заключване преди тиража.", "There is no active pre-draw lock."))

    left, right = st.columns(2)
    with left:
        if st.button(_t("Заключи следващия невидян тираж", "Lock the next unseen draw"), use_container_width=True):
            try:
                result = lock_next_draw_forecast()
                st.success(_t("Новото заключване е създадено.", "A new lock was created.") if result.get("created") else _t(f"Няма промяна: {translate_value(str(result.get('reason')))}", f"No change: {result.get('reason')}"))
                st.rerun()
            except Exception as exc:
                st.error(_t(f"Операцията по заключване е блокирана: {exc}", f"Lock operation blocked: {exc}"))
    with right:
        if st.button(_t("Провери и оцени след официална синхронизация", "Check and settle after official synchronization"), type="primary", use_container_width=True):
            try:
                result = settle_available_locked_forecast(auto_lock_next=True)
                st.success(_t("Заключеният тираж е оценен и следващият е заключен.", "The locked draw was settled and the next draw was locked.") if result.get("settled") else _t(f"Няма оценяване: {translate_value(str(result.get('reason')))}", f"No settlement: {result.get('reason')}"))
                st.rerun()
            except Exception as exc:
                st.error(_t(f"Операцията по оценяване е блокирана: {exc}", f"Settlement operation blocked: {exc}"))

    st.markdown(_t("### Натрупани проспективни резултати", "### Accumulated prospective results"))
    aggregate = summary.get("aggregate_results") or {}
    aggregate_rows = []
    for method, values in aggregate.items():
        aggregate_rows.append({
            "method": method,
            "eligible_draws": values.get("eligible_draws", 0),
            "average_best_hits": values.get("average_best_hits"),
        })
    if aggregate_rows:
        st.dataframe(pd.DataFrame(aggregate_rows), use_container_width=True, hide_index=True)
    else:
        st.info(_t("Все още няма оценени бъдещи тиражи.", "No future draws have been evaluated yet."))

    settlement_rows = _load_csv(SETTLEMENTS_CSV_PATH)
    if settlement_rows:
        st.markdown(_t("### Оценени бъдещи тиражи", "### Evaluated future draws"))
        st.dataframe(pd.DataFrame(settlement_rows), use_container_width=True, hide_index=True)

    with st.expander(_t("Активни заключени пакети за оценяване", "Active locked evaluation packages"), expanded=False):
        st.caption(_t("Тези редове са само за прозрачност на проверката и не са предназначени за реална игра.", "These rows are displayed only for evaluation transparency and are not intended for real play."))
        package_rows = _load_csv(ACTIVE_PACKAGES_CSV_PATH)
        if package_rows:
            st.dataframe(pd.DataFrame(package_rows), use_container_width=True, hide_index=True)
        else:
            st.info(_t("Няма активни заключени пакети за оценяване.", "No active locked evaluation packages are available."))

    with st.expander(_t("Технически дневник с SHA-256 подписи", "Technical SHA-256 ledger"), expanded=False):
        ledger_rows = _load_csv(LEDGER_INDEX_CSV_PATH)
        if ledger_rows:
            st.dataframe(pd.DataFrame(ledger_rows), use_container_width=True, hide_index=True)

    st.markdown(_t("### Протоколни защити", "### Protocol safeguards"))
    st.markdown(_t(
        "- Прогнозата се заключва преди целевият тираж да влезе в основните данни.\n"
        "- Всяко събитие е свързано с предишното чрез SHA-256.\n"
        "- Тираж без предварително заключване се изключва и не се добавя впоследствие.\n"
        "- Параметрите на проверката са замразени; няма донастройване по време на 30-тиражния прозорец.\n"
        "- Резултатът се оценява преди наблюдаваният тираж да участва в следващото заключване.\n"
        "- След 10, 20 или 30 тиража няма автоматично допускане до работния режим.",
        "- The forecast is locked before the target draw enters the canonical dataset.\n"
        "- Every ledger event is linked to the previous event through SHA-256.\n"
        "- A draw without a pre-draw lock is excluded and cannot be backfilled.\n"
        "- Evaluation parameters are frozen; no tuning is allowed during the 30-draw window.\n"
        "- The result is settled before the observed draw may participate in the next lock.\n"
        "- There is no automatic production promotion after 10, 20 or 30 draws.",
    ))

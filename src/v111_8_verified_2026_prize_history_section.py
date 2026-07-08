from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from src.v111_8_verified_2026_prize_history_import import (
    SOURCE_CSV,
    build_verified_2026_stats,
    import_verified_2026_history,
    load_verified_rows,
    validate_verified_rows,
)


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .verified-hero {
            border: 1px solid rgba(225,190,92,0.34);
            border-radius: 22px;
            padding: 24px;
            margin-bottom: 18px;
            background:
                radial-gradient(circle at top left, rgba(225,190,92,0.16), transparent 36%),
                linear-gradient(135deg, rgba(25,34,26,0.96), rgba(12,17,15,0.98));
            box-shadow: 0 18px 38px rgba(0,0,0,0.32);
        }
        .verified-title { color: #f7e9bf; font-size: 1.58rem; font-weight: 950; margin-bottom: 8px; }
        .verified-text { color: rgba(246,241,232,0.78); line-height: 1.55; }
        .verified-card-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 14px 0 18px 0; }
        .verified-card { border: 1px solid rgba(225,190,92,0.24); border-radius: 17px; padding: 15px; background: rgba(255,255,255,0.045); }
        .verified-label { color: rgba(246,241,232,0.62); font-size: 0.82rem; margin-bottom: 6px; }
        .verified-value { color: #f7e9bf; font-size: 1.35rem; font-weight: 950; }
        .verified-panel { border: 1px solid rgba(255,255,255,0.12); border-radius: 18px; padding: 16px; background: rgba(0,0,0,0.16); margin: 12px 0; }
        .verified-panel-title { color: #f7e9bf; font-weight: 950; margin-bottom: 8px; }
        .verified-muted { color: rgba(246,241,232,0.70); line-height: 1.5; font-size: 0.94rem; }
        .verified-warning { border-left: 4px solid rgba(225,190,92,0.75); padding: 12px 14px; border-radius: 12px; background: rgba(225,190,92,0.08); color: rgba(246,241,232,0.84); margin: 12px 0; }
        @media (max-width: 900px) { .verified-card-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _fmt_money(value: Any) -> str:
    try:
        return f"{float(value):,.2f}".replace(",", " ") + " EUR"
    except Exception:
        return "0.00 EUR"


def _cards(stats: dict[str, Any]) -> None:
    last_six = stats.get("last_six_draw") or {}
    latest = stats.get("latest_draw") or {}
    st.markdown(
        f"""
        <div class="verified-card-grid">
            <div class="verified-card"><div class="verified-label">Проверени тиражи</div><div class="verified-value">{escape(str(stats.get('draws', 0)))}</div></div>
            <div class="verified-card"><div class="verified-label">Диапазон</div><div class="verified-value">{escape(str(stats.get('draw_range', '—')))}</div></div>
            <div class="verified-card"><div class="verified-label">Последна 6-ца</div><div class="verified-value">{escape(str(last_six.get('draw_number', '—')))}</div></div>
            <div class="verified-card"><div class="verified-label">Тиражи след 6-цата</div><div class="verified-value">{escape(str(stats.get('current_gap_after_last_six', '—')))}</div></div>
        </div>
        <div class="verified-panel">
            <div class="verified-panel-title">Последен проверен тираж</div>
            <div class="verified-muted">
                Тираж {escape(str(latest.get('draw_number', '—')))} / {escape(str(latest.get('draw_date', '—')))}<br>
                Числа: {escape(str(latest.get('numbers_text', '—')))}<br>
                Джакпот: {escape(_fmt_money(latest.get('jackpot_eur', 0)))}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _category_table(stats: dict[str, Any]) -> pd.DataFrame:
    rows = []
    categories = stats.get("categories") or {}
    for category in (6, 5, 4, 3):
        item = categories.get(str(category), {})
        rows.append({
            "Категория": f"{category} числа",
            "Общо печалби": item.get("total_winners"),
            "Средно на тираж": item.get("avg_winners_per_draw"),
            "Най-много": item.get("max_winners"),
            "Тираж с най-много": item.get("max_winners_draw"),
            "Най-малко": item.get("min_winners"),
            "Тираж с най-малко": item.get("min_winners_draw"),
            "Средна печалба": _fmt_money(item.get("avg_prize_eur", 0)),
        })
    return pd.DataFrame(rows)


def render_v111_8_verified_2026_prize_history_section() -> None:
    _inject_css()
    st.markdown(
        """
        <div class="verified-hero">
            <div class="verified-title">Проверена история на печалбите — 2026</div>
            <div class="verified-text">
                Тук вкарваме ръчно проверените официални екрани за тиражи 24–49/2026. Това е чиста история на печалбите: числа, джакпот, 6/5/4/3 категории, размер и обща сума. Използва се за начален анализ на ритъм, риск и стойност — не за обещание за печалба.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        rows = load_verified_rows()
    except Exception as exc:
        st.error(f"Не мога да заредя проверения CSV: {exc}")
        return

    checks = validate_verified_rows(rows)
    blocking = sum(1 for item in checks if item.get("blocking") == "yes" and item.get("status") != "OK")
    stats = build_verified_2026_stats(rows)
    _cards(stats)

    st.markdown(
        """
        <div class="verified-warning">
            <b>Честна бележка:</b> 26 тиража са достатъчни за начална статистика за 2026, но не са достатъчни за силен дългосрочен модел. Апът ще ги използва като проверен стартов слой.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Импортирай проверените тиражи 24–49/2026", width="stretch"):
            with st.spinner("Записвам проверената история в CSV и SQLite..."):
                summary = import_verified_2026_history(clean_invalid_existing_rows=True)
                if summary.get("blocking_failures", 0) == 0:
                    upsert = summary.get("upsert_result") or {}
                    quarantine = summary.get("quarantine_result") or {}
                    st.success(
                        f"Готово. Добавени: {upsert.get('inserted', 0)}, обновени: {upsert.get('updated', 0)}, карантинирани невалидни стари редове: {quarantine.get('quarantined', 0)}."
                    )
                    st.rerun()
                else:
                    st.error("Импортът е спрян, защото проверките не са зелени.")
    with col2:
        if SOURCE_CSV.exists():
            st.download_button(
                "Свали проверения CSV",
                SOURCE_CSV.read_bytes(),
                file_name="verified_2026_prize_history_draws_24_49.csv",
                mime="text/csv",
                width="stretch",
            )

    tabs = st.tabs(["Начална статистика", "Проверки", "Данни"])
    with tabs[0]:
        st.dataframe(_category_table(stats), width="stretch", hide_index=True)
        last_six = stats.get("last_six_draw") or {}
        st.info(
            f"В проверения пакет има {stats.get('six_winning_draws_count')} тираж със 6-ца. Последната 6-ца е тираж {last_six.get('draw_number', '—')} / {last_six.get('draw_date', '—')}. След нея има {stats.get('current_gap_after_last_six')} тиража без нова 6-ца до тираж 49."
        )
    with tabs[1]:
        if blocking:
            st.error("Има блокираща проверка. Не импортирай преди поправка.")
        else:
            st.success("Всички блокиращи проверки са зелени.")
        st.dataframe(pd.DataFrame(checks), width="stretch", hide_index=True)
    with tabs[2]:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from src.v111_prize_winner_history_engine import history_count, history_rows
from src.v111_7_historical_prize_archive_harvester import (
    harvest_virtbg_year_range,
    import_virtbg_urls,
    virtbg_url,
)


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .archive-hero {
            border: 1px solid rgba(225,190,92,0.34);
            border-radius: 22px;
            padding: 22px;
            margin-bottom: 18px;
            background:
                radial-gradient(circle at top left, rgba(225,190,92,0.18), transparent 35%),
                linear-gradient(135deg, rgba(34,45,34,0.96), rgba(13,20,15,0.98));
            box-shadow: 0 18px 38px rgba(0,0,0,0.32);
        }
        .archive-title {
            color: #f7e9bf;
            font-size: 1.55rem;
            font-weight: 950;
            margin-bottom: 8px;
        }
        .archive-text {
            color: rgba(246,241,232,0.78);
            line-height: 1.55;
        }
        .archive-card-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin: 14px 0 18px 0;
        }
        .archive-card {
            border: 1px solid rgba(225,190,92,0.24);
            border-radius: 17px;
            padding: 15px;
            background: rgba(255,255,255,0.045);
        }
        .archive-label {
            color: rgba(246,241,232,0.62);
            font-size: 0.82rem;
            margin-bottom: 6px;
        }
        .archive-value {
            color: #f7e9bf;
            font-size: 1.35rem;
            font-weight: 950;
        }
        .archive-panel {
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 18px;
            padding: 16px;
            background: rgba(0,0,0,0.16);
            margin: 12px 0;
        }
        .archive-panel-title {
            color: #f7e9bf;
            font-weight: 950;
            margin-bottom: 8px;
        }
        .archive-muted {
            color: rgba(246,241,232,0.68);
            line-height: 1.5;
            font-size: 0.93rem;
        }
        .archive-warning {
            border-left: 4px solid rgba(225,190,92,0.75);
            padding: 12px 14px;
            border-radius: 12px;
            background: rgba(225,190,92,0.08);
            color: rgba(246,241,232,0.82);
            margin: 12px 0;
        }
        @media (max-width: 900px) {
            .archive-card-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _source_counts() -> dict[str, int]:
    rows = history_rows(limit=None)
    total = len(rows)
    official = 0
    manual = 0
    unofficial = 0
    verified = 0
    review = 0
    for row in rows:
        source_url = str(row.get("source_url") or "").lower()
        note = str(row.get("note") or "").lower()
        if "virtbg" in source_url or "virtbg" in note or "неофициален" in note:
            unofficial += 1
            if "проверка по числа: да" in note:
                verified += 1
            else:
                review += 1
        elif "ръчен" in source_url or "csv" in note:
            manual += 1
        else:
            official += 1
    return {"total": total, "official": official, "manual": manual, "unofficial": unofficial, "verified": verified, "review": review}


def _cards(counts: dict[str, int]) -> None:
    st.markdown(
        f"""
        <div class="archive-card-grid">
            <div class="archive-card"><div class="archive-label">Всички записи с печалби</div><div class="archive-value">{escape(str(counts['total']))}</div></div>
            <div class="archive-card"><div class="archive-label">Официални / ръчни</div><div class="archive-value">{escape(str(counts['official'] + counts['manual']))}</div></div>
            <div class="archive-card"><div class="archive-label">Неофициален архив</div><div class="archive-value">{escape(str(counts['unofficial']))}</div></div>
            <div class="archive-card"><div class="archive-label">Проверени по числа</div><div class="archive-value">{escape(str(counts['verified']))}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _show_result(result: dict[str, Any]) -> None:
    imported = int(result.get("imported_records", 0) or 0)
    errors = result.get("errors") or []
    verified = int(result.get("verified_by_numbers", 0) or 0)
    review = int(result.get("needs_review", 0) or 0)
    if imported:
        st.success(f"Импортирани/обновени записи: {imported}. Проверени по числа: {verified}. За преглед: {review}.")
    else:
        st.warning("Не бяха импортирани записи. Това може да е нормално, ако архивът не отговори или страниците са с различна структура.")
    if errors:
        with st.expander("Покажи пропуснати страници / грешки", expanded=False):
            st.dataframe(pd.DataFrame(errors).head(80), use_container_width=True, hide_index=True)


def render_v111_7_historical_prize_archive_section() -> None:
    _inject_css()
    counts = _source_counts()
    st.markdown(
        """
        <div class="archive-hero">
            <div class="archive-title">Исторически архив на печалбите</div>
            <div class="archive-text">
                Тук пробваме да съберем по-стара история за печалбите с 6, 5, 4 и 3 числа. Официалният БСТ сайт остава най-добрият източник, но при автоматичен импорт може да върне CAPTCHA. Затова този панел използва неофициален архив само като помощен източник и винаги го маркира ясно.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _cards(counts)

    st.markdown(
        """
        <div class="archive-warning">
            <b>Важно:</b> VirtBG е неофициален исторически архив. Апът не представя тези записи като официални. Когато е възможно, числата се сравняват с локалната история на тиражите и записът се маркира като проверен по числа.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Импорт от VirtBG исторически архив", expanded=True):
        st.caption("Адресният модел е от вида https://toto.virtbg.com/sportToto-y2023-t6.html. Започни с малък диапазон — например 2023, от 1 до 10.")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            year = st.number_input("Година", min_value=2010, max_value=2026, value=2023, step=1, key="v1117_year")
        with col2:
            start_draw = st.number_input("От страница/тираж", min_value=1, max_value=150, value=1, step=1, key="v1117_start")
        with col3:
            end_draw = st.number_input("До страница/тираж", min_value=1, max_value=150, value=10, step=1, key="v1117_end")
        with col4:
            delay = st.number_input("Пауза между заявки", min_value=0.0, max_value=5.0, value=0.7, step=0.1, key="v1117_delay")
        sample = virtbg_url(int(year), int(start_draw))
        st.caption(f"Първи примерен адрес: {sample}")
        if st.button("Пробвай историческия архив", use_container_width=True, key="v1117_harvest_range"):
            with st.spinner("Чета историческия архив внимателно и записвам намерените печалби..."):
                result = harvest_virtbg_year_range(int(year), int(start_draw), int(end_draw), delay_seconds=float(delay))
            _show_result(result)
            st.rerun()

        st.markdown("---")
        st.markdown("**Импорт по конкретни VirtBG адреси**")
        url_text = st.text_area(
            "Постави един или повече адреса — по един на ред",
            value="",
            height=120,
            placeholder="https://toto.virtbg.com/sportToto-y2023-t6.html",
            key="v1117_url_text",
        )
        if st.button("Импортирай поставените адреси", use_container_width=True, key="v1117_harvest_urls"):
            urls = [line.strip() for line in url_text.splitlines() if line.strip()]
            if not urls:
                st.warning("Постави поне един адрес.")
            else:
                with st.spinner("Чета поставените адреси..."):
                    result = import_virtbg_urls(urls, delay_seconds=float(delay))
                _show_result(result)
                st.rerun()

    with st.expander("Какво означава това за модела на интервали", expanded=False):
        st.markdown(
            """
            - **История на числата**: вече имаме голям локален архив от тиражи.
            - **История на печалбите**: натрупва се отделно, защото ни трябват брой печеливши с 6, 5, 4 и 3 числа.
            - **Step 112** ще прави силни изводи само когато има достатъчно записи с печалби.
            - Ако записите са малко, апът трябва да казва: „историята е недостатъчна“, а не да внушава сигурност.
            """
        )

    rows = history_rows(limit=40)
    if rows:
        st.markdown("### Последни записи в историята на печалбите")
        df = pd.DataFrame(rows)
        visible = [
            "draw_year", "draw_number", "draw_date", "numbers_text",
            "winners_6", "winners_5", "winners_4", "winners_3", "source_url", "note",
        ]
        visible = [col for col in visible if col in df.columns]
        st.dataframe(df[visible], use_container_width=True, hide_index=True)

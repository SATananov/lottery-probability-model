from __future__ import annotations

from datetime import date, timedelta
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from src.v109_2_ticket_pack_4line_engine import LINES_PER_TICKET, save_ticket_cards_as_played
from src.v109_sqlite_journal_engine import format_numbers
from src.v118_model_system_ticket_builder_engine import (
    COPY_TEXT,
    PACK_CSV,
    DEFAULT_CORE_SIZE,
    DEFAULT_SOURCE,
    DEFAULT_TARGET_LINES,
    SOURCE_LABELS_BG,
    build_full_system_price_table,
    build_model_system_ticket_builder,
    load_summary,
)


def _next_sunday() -> date:
    today = date.today()
    days_ahead = (6 - today.weekday()) % 7
    return today + timedelta(days=days_ahead or 7)


def _balls(numbers: list[int]) -> str:
    return "<div class='v118-balls'>" + "".join(f"<span class='v118-ball'>{int(n)}</span>" for n in numbers) + "</div>"


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .v118-hero{border:1px solid rgba(90,120,90,.25);border-radius:18px;padding:18px 20px;margin:8px 0 18px;background:linear-gradient(135deg,rgba(28,91,54,.12),rgba(255,255,255,.03));}
        .v118-title{font-size:1.26rem;font-weight:850;margin-bottom:6px;}
        .v118-text{opacity:.86;line-height:1.45;}
        .v118-core{border-radius:16px;padding:14px 16px;margin:10px 0 18px;background:rgba(28,91,54,.10);border:1px solid rgba(28,91,54,.22);}
        .v118-card{border:1px solid rgba(90,120,90,.28);border-radius:18px;padding:16px 18px;margin:14px 0;background:rgba(255,255,255,.035);box-shadow:0 8px 22px rgba(0,0,0,.05);}
        .v118-card-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:12px;}
        .v118-card-title{font-weight:850;font-size:1.08rem;}
        .v118-muted{opacity:.76;font-size:.92rem;line-height:1.42;}
        .v118-badge{border-radius:999px;padding:5px 10px;background:rgba(28,91,54,.14);font-weight:750;white-space:nowrap;}
        .v118-line{border-top:1px solid rgba(90,120,90,.16);padding:10px 0;}
        .v118-balls{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;}
        .v118-ball{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:999px;border:1px solid rgba(28,91,54,.38);font-weight:850;background:rgba(28,91,54,.08);}
        .v118-safe{border-radius:14px;padding:12px 14px;background:rgba(255,193,7,.10);border:1px solid rgba(255,193,7,.22);margin:10px 0 16px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_card(card: dict[str, Any]) -> None:
    title = escape(str(card.get("title") or "Системен фиш"))
    subtitle = escape(str(card.get("subtitle") or ""))
    source_note = escape(str(card.get("source_note") or ""))
    strategy = escape(str(card.get("strategy") or "системен модел"))
    st.markdown(
        f"""
        <div class='v118-card'>
          <div class='v118-card-head'>
            <div>
              <div class='v118-card-title'>🎫 {title}</div>
              <div class='v118-muted'>{subtitle}</div>
              <div class='v118-muted'>{source_note}</div>
            </div>
            <span class='v118-badge'>{strategy}</span>
          </div>
        """,
        unsafe_allow_html=True,
    )
    for line in card.get("lines", []) or []:
        nums = [int(n) for n in line.get("numbers", [])]
        line_no = escape(str(line.get("line_no") or "—"))
        role = escape(str(line.get("role") or "системна комбинация"))
        st.markdown(
            f"""
            <div class='v118-line'>
              <div class='v118-muted'>Ред {line_no} · {role}</div>
              {_balls(nums)}
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def _full_system_table(summary: dict[str, Any], price: float) -> pd.DataFrame:
    rows = summary.get("full_system_price_table") or build_full_system_price_table(price)
    return pd.DataFrame([
        {
            "Система": f"{row.get('system_numbers')} числа",
            "Комбинации": row.get("combinations"),
            "Фишове по 4 реда": row.get("tickets_4_lines"),
            "Цена": row.get("total_price_label"),
        }
        for row in rows
    ])


def _ranking_table(summary: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Ранг": row.get("rank"),
            "Число": row.get("number"),
            "Моделна оценка": row.get("model_score"),
        }
        for row in summary.get("model_number_ranking", [])[:18]
    ])


def _source_from_label(label: str) -> str:
    for key, value in SOURCE_LABELS_BG.items():
        if value == label:
            return key
    return DEFAULT_SOURCE


def render_v118_model_system_ticket_builder_section() -> None:
    _inject_css()
    st.title("🧩 Системен фиш от моделите")
    st.markdown(
        """
        <div class='v118-hero'>
          <div class='v118-title'>Система от числа, които моделите вече са избрали</div>
          <div class='v118-text'>
            Този екран не измисля нови числа на ръка. Той взема моделния ранг и текущия готов пакет,
            прави ядро от 7–12 числа и от него подрежда пълна или редуцирана система.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='v118-safe'><b>Важно:</b> системата увеличава организацията и покритието вътре в избраното ядро, но не променя случайността на тиража и не гарантира печалба.</div>",
        unsafe_allow_html=True,
    )

    current = load_summary()
    default_price = float(current.get("price_per_line_eur", 0.90) or 0.90)

    col_source, col_size, col_mode, col_lines, col_refresh = st.columns([1.7, 1.0, 1.2, 1.0, 1.0])
    source_label = col_source.selectbox(
        "Източник на числата",
        list(SOURCE_LABELS_BG.values()),
        index=list(SOURCE_LABELS_BG).index(DEFAULT_SOURCE),
        key="v118_core_source_label",
    )
    core_source = _source_from_label(source_label)
    core_size = col_size.selectbox("Система от", [7, 8, 9, 10, 11, 12], index=2, key="v118_core_size")
    mode_label = col_mode.radio("Режим", ["Редуцирана", "Пълна"], horizontal=True, key="v118_mode")
    full_system = mode_label == "Пълна"
    if full_system:
        target_lines = 0
        col_lines.metric("Линии", "всички")
    else:
        possible_lines = [7, 8, 12, 16, 20, 24, 28]
        max_lines = max(1, min(max(possible_lines), int(__import__('math').comb(int(core_size), 6))))
        available = [line for line in possible_lines if line <= max_lines]
        if DEFAULT_TARGET_LINES not in available and max_lines >= DEFAULT_TARGET_LINES:
            available.append(DEFAULT_TARGET_LINES)
            available = sorted(set(available))
        target_lines = col_lines.selectbox("Комбинации", available, index=available.index(DEFAULT_TARGET_LINES) if DEFAULT_TARGET_LINES in available else len(available) - 1, key="v118_target_lines")
    refresh = col_refresh.button("Обнови", type="primary", use_container_width=True, key="v118_refresh")

    price = st.number_input("Цена на една комбинация в EUR", min_value=0.10, max_value=5.00, value=default_price, step=0.10, key="v118_price")

    if refresh or not current:
        with st.spinner("Строя системен фиш от моделните числа..."):
            summary = build_model_system_ticket_builder(
                core_source=core_source,
                core_size=int(core_size),
                target_lines=int(target_lines or DEFAULT_TARGET_LINES),
                full_system=full_system,
                price_per_line=float(price),
                write_outputs=True,
            )
        st.success(f"Системният фиш е обновен. Статус: {summary.get('status')}")
    else:
        summary = current

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Ядро", format_numbers(summary.get("core_numbers", [])))
    m2.metric("Комбинации", summary.get("selected_combinations", 0))
    m3.metric("Цена", summary.get("total_price_label", "—"))
    m4.metric("Покритие двойки", f"{float(summary.get('pair_coverage_percent', 0.0)):.1f}%")
    m5.metric("Оценка", f"{float(summary.get('system_score', 0.0)):.1f}")

    st.markdown(
        f"""
        <div class='v118-core'>
          <b>Избрано ядро:</b> {escape(format_numbers(summary.get('core_numbers', [])))}<br>
          <span class='v118-muted'>Източник: {escape(str(summary.get('core_source_label_bg', '')))} · режим: {escape(str(summary.get('mode_label', '')))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Готов пакет", "Пълни системи", "Моделен ранг", "Копиране / запис"])
    with tabs[0]:
        if int(summary.get("blocking_failures", 0) or 0):
            st.error("Има блокираща проверка. Виж проверките долу преди игра.")
        else:
            st.success("Системният пакет е готов за преглед.")
        for card in summary.get("cards", []) or []:
            _render_card(card)

    with tabs[1]:
        st.caption("Пълното комбиниране става скъпо бързо. Тази таблица използва текущата цена на една комбинация.")
        st.dataframe(_full_system_table(summary, float(price)), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.caption("Това са числата, от които се избира ядрото. Те идват от моделния скоринг, не от ръчно въвеждане.")
        st.dataframe(_ranking_table(summary), use_container_width=True, hide_index=True)
        pack_numbers = summary.get("current_pack_numbers", [])
        if pack_numbers:
            st.info("Числа, намерени в текущия готов пакет: " + format_numbers(pack_numbers))

    with tabs[3]:
        copy_text = COPY_TEXT.read_text(encoding="utf-8") if COPY_TEXT.exists() else ""
        st.text_area("Текст за копиране / преписване", value=copy_text, height=260, key="v118_copy_text")
        cards = summary.get("cards", []) or []
        can_save = cards and all(len(card.get("lines", []) or []) == LINES_PER_TICKET for card in cards)
        if not can_save:
            st.warning("Този вариант не е кратен на 4 реда във всеки фиш. За запис като реален пакет избери редуцирана система с 12 комбинации.")
        d1, d2, d3 = st.columns(3)
        play_date = d1.date_input("Дата на игра", value=date.today(), key="v118_play_date")
        target_draw_date = d2.date_input("Дата на целевия тираж", value=_next_sunday(), key="v118_target_draw_date")
        target_draw_number = d3.text_input("Номер на тиража, ако го знаеш", value="", key="v118_target_draw_number")
        note = st.text_area("Бележка", value="Записано от системен фиш от моделите", key="v118_note")
        if st.button("Запази системния пакет като реално игран", use_container_width=True, disabled=not can_save, key="v118_save_as_played"):
            result = save_ticket_cards_as_played(
                cards=cards,
                play_date=str(play_date),
                target_draw_date=str(target_draw_date),
                target_draw_number=target_draw_number.strip(),
                note=note.strip(),
            )
            if result.get("issues"):
                for issue in result.get("issues", []):
                    st.error(issue)
            else:
                st.success(f"Записани фишове: {result.get('inserted', 0)} · вече съществуващи: {result.get('existing', 0)} · общо комбинации: {result.get('total_lines', 0)}")
                st.rerun()
        if PACK_CSV.exists():
            st.download_button(
                "Свали системния пакет като CSV",
                data=PACK_CSV.read_bytes(),
                file_name="model_system_ticket_builder_step118.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with st.expander("Проверки"):
        for check in summary.get("checks", []) or []:
            marker = "✅" if check.get("status") == "OK" else "❌"
            st.write(f"{marker} {check.get('check')} — {check.get('details_bg')}")

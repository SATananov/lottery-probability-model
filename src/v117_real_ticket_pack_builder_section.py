from __future__ import annotations

from datetime import date, timedelta
from html import escape
from typing import Any

import streamlit as st

from src.v109_2_ticket_pack_4line_engine import LINES_PER_TICKET, save_ticket_cards_as_played
from src.v117_real_ticket_pack_builder_engine import (
    COPY_TEXT,
    PACK_CSV,
    build_real_ticket_pack_builder,
    ensure_current_real_ticket_pack_summary,
    is_summary_current,
    load_summary,
)


def _next_sunday() -> date:
    today = date.today()
    days_ahead = (6 - today.weekday()) % 7
    return today + timedelta(days=days_ahead or 7)


def _balls(numbers: list[int]) -> str:
    return "<div class='v117-balls'>" + "".join(f"<span class='v117-ball'>{int(n)}</span>" for n in numbers) + "</div>"


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .v117-hero{border:1px solid rgba(90,120,90,.25);border-radius:18px;padding:18px 20px;margin:8px 0 18px;background:linear-gradient(135deg,rgba(28,91,54,.10),rgba(255,255,255,.03));}
        .v117-hero-title{font-size:1.22rem;font-weight:800;margin-bottom:6px;}
        .v117-hero-text{opacity:.86;line-height:1.45;}
        .v117-card{border:1px solid rgba(90,120,90,.28);border-radius:18px;padding:16px 18px;margin:14px 0;background:rgba(255,255,255,.035);box-shadow:0 8px 22px rgba(0,0,0,.05);}
        .v117-card-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:12px;}
        .v117-title{font-weight:800;font-size:1.08rem;}
        .v117-muted{opacity:.76;font-size:.92rem;line-height:1.42;}
        .v117-badge{border-radius:999px;padding:5px 10px;background:rgba(28,91,54,.14);font-weight:700;white-space:nowrap;}
        .v117-line{border-top:1px solid rgba(90,120,90,.16);padding:10px 0;}
        .v117-balls{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;}
        .v117-ball{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:999px;border:1px solid rgba(28,91,54,.38);font-weight:800;background:rgba(28,91,54,.08);}
        .v117-safe{border-radius:14px;padding:12px 14px;background:rgba(255,193,7,.10);border:1px solid rgba(255,193,7,.22);margin:10px 0 16px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_card(card: dict[str, Any], index: int) -> None:
    title = escape(str(card.get("title") or f"Фиш {index}"))
    subtitle = escape(str(card.get("subtitle") or ""))
    strategy = escape(str(card.get("strategy") or "—"))
    source_note = escape(str(card.get("source_note") or ""))
    st.markdown(
        f"""
        <div class='v117-card'>
          <div class='v117-card-head'>
            <div>
              <div class='v117-title'>🎫 {title}</div>
              <div class='v117-muted'>{subtitle}</div>
              <div class='v117-muted'>{source_note}</div>
            </div>
            <span class='v117-badge'>{strategy}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for line in card.get("lines", []):
        nums = [int(n) for n in line.get("numbers", [])]
        line_no = escape(str(line.get("line_no") or "—"))
        role = escape(str(line.get("role") or "комбинация"))
        st.markdown(
            f"""
            <div class='v117-line'>
              <div class='v117-muted'>Ред {line_no} · {role}</div>
              {_balls(nums)}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_v117_real_ticket_pack_builder_section() -> None:
    _inject_css()
    st.title("🎫 Готов фиш пакет")
    st.markdown(
        """
        <div class='v117-hero'>
          <div class='v117-hero-title'>Готов фиш пакет за следващия тираж</div>
          <div class='v117-hero-text'>
            Този екран подрежда готов физически пакет за пускане: 1 фиш = 4 комбинации.
            Целта е ясно копиране, печат и запис в дневника, без да се променят моделите и без обещание за печалба.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='v117-safe'><b>Важно:</b> лотарията остава случайна игра. Този пакет е дисциплинирана организация на числа, не гаранция за резултат.</div>",
        unsafe_allow_html=True,
    )

    col_mode, col_count, col_refresh = st.columns([2, 1, 1])
    with col_mode:
        mode_label = st.radio(
            "Режим на пакета",
            ["Разширен пакет — 3 фиша / 12 комбинации", "Само финалният план — 2 фиша / 8 комбинации"],
            horizontal=False,
            key="v117_package_mode_label",
        )
    package_mode = "final_plan_only" if mode_label.startswith("Само") else "extended"
    available_counts = [1, 2] if package_mode == "final_plan_only" else [1, 2, 3]
    with col_count:
        ticket_count = st.selectbox("Брой фишове", available_counts, index=len(available_counts) - 1, key="v117_ticket_count")
    with col_refresh:
        st.write("")
        refresh = st.button("Обнови пакета", type="primary", use_container_width=True, key="v117_refresh_builder")

    current_summary = load_summary()
    summary_is_current = is_summary_current(current_summary)

    if refresh:
        with st.spinner("Подреждам готовия фиш пакет..."):
            summary = build_real_ticket_pack_builder(ticket_count=int(ticket_count), package_mode=package_mode)
        st.success("Пакетът е обновен и е готов за следващия тираж.")
    elif not current_summary or not summary_is_current:
        with st.spinner("Открит е нов тираж. Обновявам пакета за следващия тираж..."):
            summary = ensure_current_real_ticket_pack_summary(ticket_count=int(ticket_count), package_mode=package_mode)
        st.info("Пакетът беше обновен автоматично, за да не виждаш стари числа след последния въведен тираж.")
    else:
        summary = current_summary

    latest_draw = summary.get("latest_dataset_draw") or {}
    latest_draw_date = str(summary.get("latest_dataset_draw_date") or latest_draw.get("date") or "—")
    latest_draw_numbers = latest_draw.get("numbers") or []
    next_target_draw_date = str(summary.get("next_target_draw_date") or _next_sunday().isoformat())
    if latest_draw_numbers:
        st.caption(f"Последен въведен тираж: {latest_draw_date} · числа: {', '.join(str(int(n)) for n in latest_draw_numbers)} · целеви следващ тираж: {next_target_draw_date}")
    else:
        st.caption(f"Целеви следващ тираж: {next_target_draw_date}")

    cards = summary.get("cards", []) or []
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Фишове", summary.get("ticket_count", 0))
    m2.metric("Комбинации", summary.get("total_lines", 0))
    m3.metric("Комбинации във фиш", summary.get("lines_per_ticket", LINES_PER_TICKET))
    m4.metric("Цена", summary.get("total_price_label", "—"))

    if summary.get("blocking_failures", 0):
        st.error("Има блокираща проверка. Виж checklist-а преди да използваш пакета.")
    else:
        st.success("Пакетът е готов за преглед, копиране или запис в дневника.")

    with st.expander("Текст за копиране / преписване", expanded=True):
        copy_text = COPY_TEXT.read_text(encoding="utf-8") if COPY_TEXT.exists() else ""
        st.text_area("Копирай готовия пакет", value=copy_text, height=260, key="v117_copy_text_area")

    for index, card in enumerate(cards, start=1):
        _render_card(card, index)

    st.subheader("Запис в дневника като реално игран пакет")
    st.caption("Използвай това само когато наистина ще пуснеш или вече си пуснал тези фишове.")
    d1, d2, d3 = st.columns(3)
    play_date = d1.date_input("Дата на игра", value=date.today(), key="v117_play_date")
    target_draw_date = d2.date_input("Дата на целевия тираж", value=_next_sunday(), key="v117_target_draw_date")
    target_draw_number = d3.text_input("Номер на тиража, ако го знаеш", value="", key="v117_target_draw_number")
    note = st.text_area("Бележка към записа", value="Записано от готов фиш пакет", key="v117_note")

    if st.button("Запази този пакет като реално игран", use_container_width=True, key="v117_save_as_played"):
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
            st.success(
                f"Записани фишове: {result.get('inserted', 0)} · вече съществуващи: {result.get('existing', 0)} · общо комбинации: {result.get('total_lines', 0)}"
            )
            st.rerun()

    if PACK_CSV.exists():
        st.download_button(
            "Свали пакета като CSV",
            data=PACK_CSV.read_bytes(),
            file_name="gotov-fish-paket.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with st.expander("Проверки на готовия пакет"):
        for check in summary.get("checks", []) or []:
            marker = "✅" if check.get("status") == "OK" else "❌"
            st.write(f"{marker} {check.get('check')} — {check.get('details_bg')}")

from __future__ import annotations

from datetime import date
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from src.v109_sqlite_journal_engine import (
    default_next_sunday,
    evaluate_open_tickets_against_latest_draw,
    sync_latest_draw_entry,
    table_rows,
    write_artifacts,
)
from src.v109_3_ticket_pack_source_clarity_engine import latest_dataset_context
from src.v109_2_ticket_pack_4line_engine import (
    DEFAULT_TICKET_COUNT,
    LINES_PER_TICKET,
    build_suggested_ticket_cards,
    parse_numbers_text,
    save_ticket_cards_as_played,
    validate_numbers,
)

STATUS_LABELS = {
    "SQLITE_JOURNAL_READY": "Дневникът е активен",
    "CHECK_REQUIRED": "Нужна е проверка",
    "PLAYED_WAITING_RESULT": "Игран — чака резултат",
    "PLANNED": "Планиран",
    "PLAYED": "Игран",
    "EVALUATED": "Оценен",
}

SOURCE_LABELS = {
    "dataset_latest_draw": "Последен записан тираж",
}


def _inject_journal_css() -> None:
    st.markdown(
        """
        <style>
        .journal-hero {
            border: 1px solid rgba(225, 190, 92, 0.24);
            border-radius: 22px;
            padding: 24px 26px;
            margin: 10px 0 22px 0;
            background: linear-gradient(135deg, rgba(225,190,92,0.14), rgba(36,41,54,0.42));
            box-shadow: 0 16px 42px rgba(0,0,0,0.24);
        }
        .journal-hero-title {
            font-size: 1.16rem;
            font-weight: 900;
            color: #f7e9bf;
            margin-bottom: 8px;
        }
        .journal-hero-text {
            color: rgba(246, 241, 225, 0.84);
            line-height: 1.52;
        }
        .journal-chip-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin: 14px 0 4px 0;
        }
        .journal-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border: 1px solid rgba(225,190,92,0.25);
            border-radius: 999px;
            padding: 7px 12px;
            background: rgba(225,190,92,0.09);
            color: #f5e7bd;
            font-weight: 750;
            font-size: 0.92rem;
        }
        .journal-card {
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 18px;
            padding: 16px 18px;
            background: rgba(255,255,255,0.035);
            margin: 10px 0;
        }
        .journal-card-title {
            font-weight: 850;
            color: #f6f1e8;
            font-size: 1.03rem;
            margin-bottom: 10px;
        }
        .journal-muted {
            color: rgba(246,241,232,0.62);
            font-size: 0.92rem;
            line-height: 1.42;
        }
        .pack-summary {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin: 14px 0 18px 0;
        }
        .pack-stat {
            border: 1px solid rgba(225,190,92,0.18);
            border-radius: 16px;
            padding: 13px 14px;
            background: rgba(225,190,92,0.055);
        }
        .pack-stat-label {
            color: rgba(246,241,232,0.65);
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 5px;
        }
        .pack-stat-value {
            color: #f6f1e8;
            font-size: 1.35rem;
            font-weight: 900;
        }
        .physical-ticket-card {
            border: 1px solid rgba(225,190,92,0.22);
            border-radius: 22px;
            padding: 18px 20px;
            margin: 16px 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.045), rgba(225,190,92,0.04));
            box-shadow: 0 12px 28px rgba(0,0,0,0.18);
        }
        .physical-ticket-head {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: flex-start;
            margin-bottom: 14px;
        }
        .physical-ticket-title {
            color: #f7e9bf;
            font-weight: 900;
            font-size: 1.14rem;
        }
        .physical-ticket-subtitle {
            color: rgba(246,241,232,0.68);
            font-size: 0.92rem;
            margin-top: 4px;
        }
        .physical-ticket-badge {
            border-radius: 999px;
            border: 1px solid rgba(225,190,92,0.28);
            background: rgba(225,190,92,0.10);
            color: #f5e7bd;
            padding: 7px 11px;
            font-size: 0.85rem;
            font-weight: 800;
            white-space: nowrap;
        }
        .ticket-line-card {
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 13px 14px;
            margin: 10px 0;
            background: rgba(0,0,0,0.14);
        }
        .ticket-line-header {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: center;
            margin-bottom: 12px;
            color: rgba(246,241,232,0.86);
            font-weight: 800;
        }
        .ticket-role {
            color: #e1be5c;
            font-size: 0.9rem;
        }
        .number-ball-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }
        .number-ball {
            width: 46px;
            height: 46px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            color: #141414;
            background: radial-gradient(circle at 32% 25%, #fff3a7 0%, #f1cf54 42%, #c89a19 100%);
            border: 1px solid rgba(255,255,255,0.36);
            box-shadow: inset 0 2px 7px rgba(255,255,255,0.28), 0 8px 16px rgba(0,0,0,0.32);
        }

        .source-context-panel {
            border: 1px solid rgba(225,190,92,0.22);
            border-radius: 20px;
            padding: 18px 20px;
            margin: 14px 0 18px 0;
            background: linear-gradient(135deg, rgba(40,54,72,0.58), rgba(225,190,92,0.065));
        }
        .source-context-title {
            color: #f7e9bf;
            font-weight: 900;
            font-size: 1.05rem;
            margin-bottom: 8px;
        }
        .source-context-text {
            color: rgba(246,241,232,0.82);
            line-height: 1.55;
            margin-bottom: 12px;
        }
        .source-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 9px;
            margin-top: 10px;
        }
        .source-chip {
            display: inline-flex;
            border: 1px solid rgba(225,190,92,0.24);
            border-radius: 999px;
            padding: 7px 11px;
            background: rgba(225,190,92,0.08);
            color: #f4e4b4;
            font-size: 0.86rem;
            font-weight: 800;
        }
        .ticket-source-strip {
            border-left: 3px solid rgba(225,190,92,0.72);
            padding: 8px 11px;
            margin: 10px 0 14px 0;
            border-radius: 10px;
            background: rgba(225,190,92,0.055);
            color: rgba(246,241,232,0.80);
            font-size: 0.91rem;
            line-height: 1.45;
        }
        .journal-result-note {
            border-radius: 14px;
            border: 1px solid rgba(51, 153, 255, 0.22);
            background: rgba(31, 87, 138, 0.25);
            color: rgba(223,240,255,0.95);
            padding: 14px 16px;
            margin: 14px 0;
        }
        .package-mode-panel {
            border: 1px solid rgba(225,190,92,0.22);
            border-radius: 18px;
            padding: 16px 18px;
            margin: 14px 0 18px 0;
            background: linear-gradient(135deg, rgba(225,190,92,0.10), rgba(22,28,36,0.42));
        }
        .package-mode-title {
            color: #f7e9bf;
            font-weight: 900;
            font-size: 1.02rem;
            margin-bottom: 8px;
        }
        .package-mode-text {
            color: rgba(246,241,232,0.82);
            line-height: 1.52;
        }
        .source-scope-label {
            display: inline-flex;
            border-radius: 999px;
            border: 1px solid rgba(225,190,92,0.28);
            background: rgba(225,190,92,0.10);
            color: #f5e7bd;
            padding: 6px 10px;
            font-size: 0.82rem;
            font-weight: 850;
            margin-top: 8px;
        }
        @media (max-width: 900px) {
            .pack-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .physical-ticket-head { flex-direction: column; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _status_label(value: Any) -> str:
    if value is None:
        return "—"
    value_text = str(value)
    return STATUS_LABELS.get(value_text, value_text.replace("_", " ").title())


def _source_label(value: Any) -> str:
    if value is None:
        return "—"
    value_text = str(value)
    return SOURCE_LABELS.get(value_text, value_text)


def _format_datetime(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return "—"
    text = str(value).replace("T", " ")
    text = text.replace("+00:00", " UTC")
    return text


def _numbers_html(numbers: list[int] | str | None) -> str:
    if numbers is None:
        values: list[str] = []
    elif isinstance(numbers, list):
        values = [str(number) for number in numbers]
    else:
        text = str(numbers).replace(";", ",").replace("|", ",")
        values = [part.strip() for part in text.split(",") if part.strip()]
    if not values:
        return '<span class="journal-muted">няма числа</span>'
    balls = "".join(f'<span class="number-ball">{escape(value)}</span>' for value in values)
    return f'<div class="number-ball-row">{balls}</div>'


def _latest_numbers(latest: dict[str, Any]) -> str:
    numbers = latest.get("numbers") or latest.get("numbers_text") or ""
    if isinstance(numbers, list):
        return ", ".join(str(number) for number in numbers)
    return str(numbers or "—")


def _numbers_inline(numbers: list[int] | str | None) -> str:
    if numbers is None:
        return "—"
    if isinstance(numbers, list):
        return ", ".join(str(number) for number in numbers)
    return str(numbers or "—")


def _render_source_context_panel(context: dict[str, Any]) -> None:
    latest = context.get("latest_draw") or {}
    latest_date = latest.get("date") or "—"
    latest_numbers = _numbers_inline(latest.get("numbers"))
    dataset_rows = context.get("dataset_rows") or "—"
    recommendation = context.get("training_recommendation") or "Не обучавай тежки модели сега"
    heavy_status = context.get("heavy_training_status") or "Тежко обучение не е пускано"
    source_statement = context.get("source_statement") or "Числата са текуща препоръка от активния финален план и наличните модели."
    st.markdown(
        f"""
        <div class="source-context-panel">
            <div class="source-context-title">Как са избрани тези фишове?</div>
            <div class="source-context-text">
                {escape(str(source_statement))}
                Това е пакет за игра от текущото състояние на системата, а не обещание за резултат.
            </div>
            <div class="source-chip-row">
                <span class="source-chip">Данни: {escape(str(dataset_rows))} тиража</span>
                <span class="source-chip">Последен тираж: {escape(str(latest_date))}</span>
                <span class="source-chip">Последни числа: {escape(str(latest_numbers))}</span>
                <span class="source-chip">{escape(str(heavy_status))}</span>
                <span class="source-chip">{escape(str(recommendation))}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _mode_display(value: Any) -> str:
    mapping = {
        "main": "Основни комбинации",
        "main_reserve": "Основни + резервни",
        "all_export": "Всички редове от експорта",
        "active_plan_all_11": "Всички 11 комбинации",
        "ticket_pack_4_lines": "Фиш с 4 комбинации",
    }
    if value is None:
        return "—"
    return mapping.get(str(value), str(value))


def _table_for_display(table_name: str, rows: list[dict[str, Any]]) -> pd.DataFrame:
    cleaned: list[dict[str, Any]] = []
    for row in rows:
        if table_name == "user_draw_entries":
            cleaned.append(
                {
                    "ID": row.get("id"),
                    "Дата": row.get("draw_date"),
                    "Тираж №": row.get("draw_number") or "—",
                    "Теглене": row.get("drawing_position") or "—",
                    "Числа": row.get("numbers_text"),
                    "Въведено на": _format_datetime(row.get("entered_at_utc")),
                    "Източник": _source_label(row.get("source")),
                    "Бележка": row.get("note") or "—",
                }
            )
        elif table_name == "played_tickets":
            cleaned.append(
                {
                    "Фиш ID": row.get("id"),
                    "Дата на игра": row.get("play_date"),
                    "Целеви тираж": row.get("target_draw_date") or "—",
                    "Тираж №": row.get("target_draw_number") or "—",
                    "Тип": _mode_display(row.get("mode")),
                    "Комбинации": row.get("line_count"),
                    "Цена": f"{float(row.get('total_price_eur') or 0):.2f} EUR",
                    "Статус": _status_label(row.get("status")),
                    "Бележка": row.get("note") or "—",
                }
            )
        elif table_name == "played_ticket_lines":
            cleaned.append(
                {
                    "Фиш ID": row.get("ticket_id"),
                    "Комбинация": row.get("line_no"),
                    "Роля": row.get("role") or "—",
                    "Числа": row.get("numbers_text"),
                    "Цена": f"{float(row.get('price_eur') or 0):.2f} EUR",
                    "Игран": "Да" if int(row.get("played") or 0) == 1 else "Не",
                    "Бележка": row.get("note") or "—",
                }
            )
        elif table_name == "played_ticket_results":
            cleaned.append(
                {
                    "Фиш ID": row.get("ticket_id"),
                    "Тираж ID": row.get("draw_entry_id"),
                    "Оценено на": _format_datetime(row.get("evaluated_at_utc")),
                    "Най-добра комбинация": row.get("best_line_no") or "—",
                    "Най-добри попадения": row.get("best_hits"),
                    "Общо попадения": row.get("total_hits"),
                    "Комбинации с попадение": row.get("rows_with_hits"),
                    "Комбинации 3+": row.get("rows_with_3_plus"),
                    "Комбинации 4+": row.get("rows_with_4_plus"),
                    "Познати числа": row.get("matched_numbers_text") or "—",
                    "Бележка": row.get("note") or "—",
                }
            )
        else:
            cleaned.append(row)
    return pd.DataFrame(cleaned)


def _show_dataframe(title: str, rows: list[dict[str, Any]], empty_text: str, table_name: str) -> None:
    st.markdown(f"### {title}")
    if rows:
        st.dataframe(_table_for_display(table_name, rows), use_container_width=True, hide_index=True)
    else:
        st.info(empty_text)


def _render_ticket_card_preview(card: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="physical-ticket-card">
            <div class="physical-ticket-head">
                <div>
                    <div class="physical-ticket-title">{escape(str(card.get('title') or 'Фиш'))}</div>
                    <div class="physical-ticket-subtitle">{escape(str(card.get('subtitle') or ''))}</div>
                </div>
                <div class="physical-ticket-badge">{len(card.get('lines', []))} комбинации</div>
            </div>
        """,
        unsafe_allow_html=True,
    )
    for line in card.get("lines", []):
        st.markdown(
            f"""
            <div class="ticket-line-card">
                <div class="ticket-line-header">
                    <span>Комбинация {escape(str(line.get('line_no')))}</span>
                    <span class="ticket-role">{escape(str(line.get('role') or 'комбинация'))}</span>
                </div>
                {_numbers_html(line.get('numbers'))}
                <div class="journal-muted" style="margin-top:10px;">Източник: {escape(str(line.get('source_group') or line.get('source_ticket_id') or '—'))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def _editable_ticket_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edited_cards: list[dict[str, Any]] = []
    for card in cards:
        st.markdown(
            f"""
            <div class="physical-ticket-card">
                <div class="physical-ticket-head">
                    <div>
                        <div class="physical-ticket-title">{escape(str(card.get('title') or 'Фиш'))}</div>
                        <div class="physical-ticket-subtitle">Можеш да оставиш предложенията или да редактираш числата преди запис.</div>
                        <span class="source-scope-label">Източник: {escape('само от финалния план' if card.get('package_scope') == 'final_plan' else 'допълващ модел')}</span>
                    </div>
                    <div class="physical-ticket-badge">реален фиш · 4 реда</div>
                </div>
                <div class="ticket-source-strip">
                    {escape(str(card.get('source_note') or 'Източникът е текущият модел.'))}<br>
                    Можеш да редактираш числата. След редакция дневникът пази точно това, което реално си играл.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        edited_lines: list[dict[str, Any]] = []
        for line in card.get("lines", []):
            default_text = ", ".join(str(number) for number in line.get("numbers", []))
            key = f"v1092_ticket_{card.get('ticket_no')}_line_{line.get('line_no')}"
            value = st.text_input(
                f"{card.get('title')} · Комбинация {line.get('line_no')}",
                value=default_text,
                key=key,
                help="Въведи 6 числа между 1 и 49, разделени със запетая или интервал.",
            )
            numbers = parse_numbers_text(value)
            valid, message = validate_numbers(numbers)
            if valid:
                st.markdown(_numbers_html(numbers), unsafe_allow_html=True)
            else:
                st.warning(message)
            line_copy = dict(line)
            line_copy["numbers"] = numbers
            line_copy["numbers_text"] = ", ".join(str(number) for number in numbers)
            edited_lines.append(line_copy)
        card_copy = dict(card)
        card_copy["lines"] = edited_lines
        edited_cards.append(card_copy)
    return edited_cards


def render_v109_sqlite_journal_section() -> None:
    _inject_journal_css()

    st.title("Дневник на фишовете")
    st.markdown(
        """
        <div class="journal-hero">
            <div class="journal-hero-title">Личен дневник за реални тиражи и изиграни фишове</div>
            <div class="journal-hero-text">
                Тук се пази какво е въведено като реален тираж, какви фишове са играни
                и какъв е резултатът им след тегленето. Един реален фиш се приема като 4 комбинации.
                Дневникът е за отчетност — не променя вероятностите и не обещава печалба.
            </div>
            <div class="journal-chip-row">
                <span class="journal-chip">Локален дневник: активен</span>
                <span class="journal-chip">Един фиш: 4 комбинации</span>
                <span class="journal-chip">CSV архив: наличен</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Обнови дневника", use_container_width=True, key="v109_refresh_journal_btn"):
        summary = write_artifacts(sync_latest_draw=True, evaluate_open=True)
        st.success("Дневникът е обновен.")
    else:
        summary = write_artifacts(sync_latest_draw=True, evaluate_open=False)

    counts = summary.get("counts", {}) or {}
    latest = summary.get("latest_journal_draw") or summary.get("latest_dataset_draw") or {}

    cols = st.columns(5)
    cols[0].metric("Статус", _status_label(summary.get("status")))
    cols[1].metric("Реални тиражи", counts.get("draw_entries", 0))
    cols[2].metric("Запазени фишове", counts.get("played_tickets", 0))
    cols[3].metric("Комбинации във фишове", counts.get("played_ticket_lines", 0))
    cols[4].metric("Резултати", counts.get("played_ticket_results", 0))

    st.markdown("### Последен реален тираж")
    numbers_text = _latest_numbers(latest)
    st.markdown(
        f"""
        <div class="journal-card">
            <div class="journal-card-title">
                Дата: {escape(str(latest.get('draw_date') or latest.get('date') or '—'))}
                · Тираж: {escape(str(latest.get('draw_number') or '—'))}
            </div>
            {_numbers_html(numbers_text)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Синхронизирай последния реален тираж", use_container_width=True, key="v109_sync_latest_draw_btn"):
            result = sync_latest_draw_entry(note="Ръчно обновяване от страницата Дневник на фишовете.")
            write_artifacts(sync_latest_draw=False, evaluate_open=False)
            if result.get("inserted"):
                st.success("Последният реален тираж е добавен в дневника.")
            else:
                st.info("Последният реален тираж вече е наличен в дневника.")
            st.rerun()
    with c2:
        if st.button("Провери чакащите фишове", use_container_width=True, key="v109_evaluate_open_tickets_btn"):
            result = evaluate_open_tickets_against_latest_draw()
            write_artifacts(sync_latest_draw=True, evaluate_open=False)
            st.success(f"Проверени фишове: {result.get('evaluated', 0)}")
            st.rerun()

    st.markdown("---")
    st.markdown("## Подготви фишове за игра")
    st.markdown(
        '<div class="journal-muted">Автоматичното предложение подрежда фишове по 4 комбинации. Можеш да запазиш само това, което реално ще играеш, или да редактираш редовете ръчно.</div>',
        unsafe_allow_html=True,
    )

    _render_source_context_panel(latest_dataset_context())

    package_mode_label = st.radio(
        "Източник на пакета",
        [
            "Само финалният план — 2 фиша / 8 комбинации",
            "Разширен пакет — 3 фиша / 12 комбинации",
        ],
        index=1,
        horizontal=True,
        key="v1094_package_mode",
    )
    package_mode = "final_plan_only" if package_mode_label.startswith("Само") else "extended"
    if package_mode == "final_plan_only":
        st.markdown(
            """
            <div class="package-mode-panel">
                <div class="package-mode-title">Само финалният план</div>
                <div class="package-mode-text">
                    Този режим използва само видимите 8 комбинации от страницата „Финален план“.
                    Това прави 2 реални фиша по 4 комбинации. Няма допълващи редове извън финалната таблица.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        available_ticket_counts = [1, 2]
        default_index = 1
    else:
        st.markdown(
            """
            <div class="package-mode-panel">
                <div class="package-mode-title">Разширен пакет</div>
                <div class="package-mode-text">
                    Първите 2 фиша идват от видимия финален план. Третият фиш е ясно маркиран като
                    допълващ модел извън финалната таблица. Така се вижда откъде идват всичките 12 комбинации.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        available_ticket_counts = [1, 2, 3]
        default_index = 2

    package_cols = st.columns(4)
    ticket_count = package_cols[0].selectbox("Брой фишове", available_ticket_counts, index=default_index, key="v1092_ticket_count")
    edit_mode = package_cols[1].toggle("Ръчна редакция", value=False, key="v1092_manual_edit")
    package_cols[2].metric("Комбинации във фиш", LINES_PER_TICKET)
    package_cols[3].metric("Общо комбинации", int(ticket_count) * LINES_PER_TICKET)

    suggested_cards = build_suggested_ticket_cards(int(ticket_count), package_mode=package_mode)
    st.markdown(
        f"""
        <div class="pack-summary">
            <div class="pack-stat"><div class="pack-stat-label">Фишове</div><div class="pack-stat-value">{int(ticket_count)}</div></div>
            <div class="pack-stat"><div class="pack-stat-label">Комбинации</div><div class="pack-stat-value">{int(ticket_count) * LINES_PER_TICKET}</div></div>
            <div class="pack-stat"><div class="pack-stat-label">Структура</div><div class="pack-stat-value">4 реда</div></div>
            <div class="pack-stat"><div class="pack-stat-label">Режим</div><div class="pack-stat-value">{'Ръчен' if edit_mode else 'Авто'}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if edit_mode:
        cards_to_save = _editable_ticket_cards(suggested_cards)
    else:
        cards_to_save = suggested_cards
        for card in suggested_cards:
            _render_ticket_card_preview(card)

    input_cols = st.columns(3)
    play_date = input_cols[0].date_input("Дата на игра", value=date.today(), key="v109_play_date")
    target_draw_date = input_cols[1].date_input("Дата на целевия тираж", value=default_next_sunday(), key="v109_target_draw_date")
    target_draw_number = input_cols[2].text_input("Номер на тиража, ако го знаеш", value="", key="v109_target_draw_number")
    note = st.text_area("Бележка към пакета", value="", key="v109_play_note")

    if st.button("Запази избраните фишове като изиграни", use_container_width=True, key="v1092_save_ticket_cards_btn"):
        result = save_ticket_cards_as_played(
            cards=cards_to_save,
            play_date=str(play_date),
            target_draw_date=str(target_draw_date),
            target_draw_number=target_draw_number.strip(),
            note=note.strip(),
        )
        write_artifacts(sync_latest_draw=True, evaluate_open=False)
        if result.get("issues"):
            for issue in result.get("issues", []):
                st.error(issue)
        else:
            st.success(
                f"Записани фишове: {result.get('inserted', 0)} · вече съществуващи: {result.get('existing', 0)} · общо комбинации: {result.get('total_lines', 0)}"
            )
            st.rerun()

    st.markdown("---")
    tab_draws, tab_tickets, tab_lines, tab_results = st.tabs(["Реални тиражи", "Фишове", "Комбинации", "Резултати"])
    with tab_draws:
        _show_dataframe("Реални тиражи в дневника", table_rows("user_draw_entries", 200), "Още няма синхронизирани тиражи.", "user_draw_entries")
    with tab_tickets:
        _show_dataframe("Запазени фишове", table_rows("played_tickets", 200), "Още няма запазени фишове.", "played_tickets")
    with tab_lines:
        _show_dataframe("Комбинации в запазените фишове", table_rows("played_ticket_lines", 500), "Още няма комбинации.", "played_ticket_lines")
    with tab_results:
        _show_dataframe("Резултати срещу реални тиражи", table_rows("played_ticket_results", 200), "Още няма оценени резултати.", "played_ticket_results")

    st.markdown(
        """
        <div class="journal-result-note">
            Дневникът е за отчетност: какво е въведено и какво реално е играно.
            Той не променя вероятностите и не е гаранция за печалба.
        </div>
        """,
        unsafe_allow_html=True,
    )

from __future__ import annotations

from datetime import date
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from src.v111_prize_winner_history_engine import (
    OFFICIAL_BASE_URL,
    DATA_PATH,
    draw_dataframe_rows,
    history_count,
    import_year_range,
    import_manual_csv_text,
    manual_csv_template_text,
    interval_summary,
    latest_record,
    write_artifacts,
)


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .prize-hero {
            border: 1px solid rgba(225, 190, 92, 0.24);
            border-radius: 22px;
            padding: 24px 26px;
            margin: 10px 0 22px 0;
            background: linear-gradient(135deg, rgba(225,190,92,0.14), rgba(36,41,54,0.42));
            box-shadow: 0 16px 42px rgba(0,0,0,0.24);
        }
        .prize-title {
            font-size: 1.24rem;
            font-weight: 950;
            color: #f7e9bf;
            margin-bottom: 8px;
        }
        .prize-text {
            color: rgba(246, 241, 225, 0.84);
            line-height: 1.55;
        }
        .prize-card-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin: 14px 0 18px 0;
        }
        .prize-card {
            border: 1px solid rgba(225,190,92,0.18);
            border-radius: 16px;
            padding: 14px 15px;
            background: rgba(225,190,92,0.055);
        }
        .prize-card-label {
            color: rgba(246,241,232,0.65);
            font-size: 0.82rem;
            font-weight: 760;
            margin-bottom: 6px;
        }
        .prize-card-value {
            color: #f6f1e8;
            font-size: 1.35rem;
            font-weight: 950;
        }
        .prize-panel {
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 18px;
            padding: 16px 18px;
            background: rgba(255,255,255,0.035);
            margin: 10px 0 16px 0;
        }
        .prize-panel-title {
            font-weight: 900;
            color: #f7e9bf;
            font-size: 1.05rem;
            margin-bottom: 8px;
        }
        .prize-muted {
            color: rgba(246,241,232,0.66);
            font-size: 0.92rem;
            line-height: 1.45;
        }
        .interval-card {
            border-left: 3px solid rgba(225,190,92,0.72);
            padding: 12px 14px;
            margin: 10px 0;
            border-radius: 13px;
            background: rgba(225,190,92,0.055);
        }
        .interval-title {
            color: #f7e9bf;
            font-weight: 900;
            margin-bottom: 6px;
        }
        .number-ball-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            margin-top: 8px;
        }
        .number-ball {
            width: 38px;
            height: 38px;
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
        @media (max-width: 900px) {
            .prize-card-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _numbers_html(numbers_text: str | None) -> str:
    values = []
    for part in str(numbers_text or "").replace(";", ",").replace("|", ",").split(","):
        part = part.strip()
        if part:
            values.append(part)
    if not values:
        return '<span class="prize-muted">няма числа</span>'
    return '<div class="number-ball-row">' + ''.join(f'<span class="number-ball">{escape(value)}</span>' for value in values) + '</div>'


def _fmt_money(value: Any) -> str:
    try:
        return f"{float(value):,.2f}".replace(",", " ") + " EUR"
    except Exception:
        return "0.00 EUR"


def _metric_cards(count: int, latest: dict[str, Any] | None) -> None:
    latest_date = latest.get("draw_date") if latest else "—"
    latest_draw = latest.get("draw_number") if latest else "—"
    jackpot = _fmt_money(latest.get("jackpot_eur")) if latest else "—"
    winners_6 = latest.get("winners_6") if latest else "—"
    st.markdown(
        f"""
        <div class="prize-card-grid">
            <div class="prize-card"><div class="prize-card-label">Импортирани тиражи</div><div class="prize-card-value">{escape(str(count))}</div></div>
            <div class="prize-card"><div class="prize-card-label">Последен тираж</div><div class="prize-card-value">{escape(str(latest_draw))}</div></div>
            <div class="prize-card"><div class="prize-card-label">Дата</div><div class="prize-card-value">{escape(str(latest_date))}</div></div>
            <div class="prize-card"><div class="prize-card-label">6 числа</div><div class="prize-card-value">{escape(str(winners_6))}</div></div>
        </div>
        <div class="prize-panel">
            <div class="prize-panel-title">Последен запис в историята</div>
            <div class="prize-muted">Джакпот: {escape(str(jackpot))}</div>
            {_numbers_html(latest.get('numbers_text') if latest else None)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_interval_card(title: str, stats: dict[str, Any]) -> None:
    last_date = stats.get("last_event_date") or "няма запис"
    last_draw = stats.get("last_event_draw") or "—"
    avg_interval = stats.get("avg_interval")
    avg_text = f"{avg_interval} тиража" if avg_interval is not None else "няма достатъчно история"
    st.markdown(
        f"""
        <div class="interval-card">
            <div class="interval-title">{escape(title)}</div>
            <div class="prize-muted">
                Последно: тираж {escape(str(last_draw))} / {escape(str(last_date))}<br>
                Текущ интервал: {escape(str(stats.get('current_gap', '—')))} тиража<br>
                Среден интервал: {escape(str(avg_text))}<br>
                Най-дълъг видян интервал: {escape(str(stats.get('max_interval') or '—'))} тиража
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_v111_prize_winner_history_section() -> None:
    _inject_css()
    st.markdown(
        f"""
        <div class="prize-hero">
            <div class="prize-title">История на печалбите</div>
            <div class="prize-text">
                Тук апът събира официалната история на печалбите за 6 от 49: колко печеливши има с 6, 5, 4 и 3 числа, какъв е джакпотът и през колко тиража се появяват печалби по категории. Това помага за ритъм, риск и стойност на играта — не е гаранция за следващ тираж.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    count = history_count()
    latest = latest_record()
    _metric_cards(count, latest)

    with st.expander("Импорт от официалния сайт на БСТ", expanded=count == 0):
        st.caption(f"Официален източник: {OFFICIAL_BASE_URL}")
        current_year = date.today().year
        col1, col2, col3 = st.columns(3)
        with col1:
            year = st.number_input("Година", min_value=1958, max_value=current_year + 1, value=current_year, step=1)
        with col2:
            start_draw = st.number_input("От тираж", min_value=1, max_value=150, value=1, step=1)
        with col3:
            default_end = 49 if int(year) == 2026 else 104
            end_draw = st.number_input("До тираж", min_value=1, max_value=150, value=default_end, step=1)
        st.info("За първи тест избери 2026 и тиражи 1–49. Ако БСТ върне CAPTCHA към Python, това не е грешка в апа — използвай ръчния CSV импорт по-долу.")
        if st.button("Импортирай печалбите от БСТ", use_container_width=True):
            with st.spinner("Чета официалните страници и записвам историята локално..."):
                try:
                    summary = import_year_range(int(year), int(start_draw), int(end_draw))
                    result = summary.get("import_result") or {}
                    imported = int(result.get("imported_records", 0) or 0)
                    errors = result.get("errors") or []
                    st.success(f"Готово. Импортирани/обновени записи: {imported}. Грешки: {result.get('error_count', 0)}.")
                    if errors:
                        error_text = " ".join(str(item.get("error", "")) for item in errors[:3])
                        if "CAPTCHA" in error_text or "captcha" in error_text.lower():
                            st.warning("БСТ върна CAPTCHA към автоматичния импорт. Не заобикаляме защитата. Използвай ръчния CSV импорт от панела по-долу.")
                        else:
                            st.warning("Има пропуснати тиражи. Това може да е нормално, ако страницата още не съществува или БСТ временно не върне данни.")
                    st.rerun()
                except Exception as exc:
                    message = str(exc)
                    if "CAPTCHA" in message or "captcha" in message.lower():
                        st.error("БСТ върна CAPTCHA към автоматичния импорт. Данните може да се въведат безопасно чрез CSV импорт от панела по-долу.")
                    else:
                        st.error(f"Импортът не успя: {exc}")

        st.markdown("---")
        st.markdown("**Ръчен CSV импорт при CAPTCHA**")
        st.caption("Това е безопасният резервен режим: отваряш официалната страница в браузър, преписваш таблицата в CSV шаблона и апът я записва локално.")
        template = manual_csv_template_text()
        st.download_button(
            "Свали CSV шаблон",
            template.encode("utf-8-sig"),
            file_name="prize_winner_history_template.csv",
            mime="text/csv",
            use_container_width=True,
        )
        uploaded_csv = st.file_uploader("Качи попълнен CSV файл", type=["csv"], key="v111_manual_csv_upload")
        manual_csv_text = st.text_area(
            "Или постави CSV текст тук",
            value="",
            height=140,
            placeholder=template,
            key="v111_manual_csv_text",
        )
        if st.button("Импортирай CSV в локалната история", use_container_width=True):
            try:
                csv_text = ""
                if uploaded_csv is not None:
                    csv_text = uploaded_csv.getvalue().decode("utf-8-sig", errors="replace")
                elif manual_csv_text.strip():
                    csv_text = manual_csv_text
                else:
                    st.warning("Първо качи CSV файл или постави CSV текст.")
                    csv_text = ""
                if csv_text:
                    summary = import_manual_csv_text(csv_text)
                    result = summary.get("import_result") or {}
                    st.success(f"CSV импортът е готов. Записи: {result.get('imported_records', 0)}.")
                    st.rerun()
            except Exception as exc:
                st.error(f"CSV импортът не успя: {exc}")

        if st.button("Обнови локалните отчети", use_container_width=True):
            summary = write_artifacts()
            st.success(f"Отчетите са обновени. Проверки с проблеми: {summary.get('blocking_failures')}.")

    tabs = st.tabs(["Архив", "Интервали", "За какво служи"])
    with tabs[0]:
        rows = draw_dataframe_rows(limit=300)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            if DATA_PATH.exists():
                st.download_button(
                    "Свали CSV архива",
                    DATA_PATH.read_bytes(),
                    file_name="prize_winner_history.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        else:
            st.info("Още няма импортирана история на печалбите. Стартирай импорт от БСТ от панела по-горе.")
    with tabs[1]:
        intervals = interval_summary()
        _render_interval_card("6 числа — голямата печалба", intervals.get("6", {}))
        _render_interval_card("5 числа — силна печалба", intervals.get("5", {}))
        _render_interval_card("4 числа — средна категория", intervals.get("4", {}))
        _render_interval_card("3 числа — базова категория", intervals.get("3", {}))
        st.warning("Интервалите показват история и ритъм на печалбите. Те не правят следващия тираж предвидим.")
    with tabs[2]:
        st.markdown(
            """
            Този слой е нужен, за да сравняваме нашите фишове с реалната история на печалбите. Така апът може да показва не само колко числа сме улучили, а и какъв е бил контекстът на тиража — имало ли е 6-ца, колко хора са хванали 5 или 4 числа и дали периодът без голяма печалба е нормален или по-дълъг от обичайното.

            Следващата логична стъпка е отделен анализ на стойност и риск: кога има смисъл да играеш само основен пакет и кога разширен пакет от няколко фиша.
            """
        )


from __future__ import annotations

import pandas as pd
import streamlit as st

from src.bst_official_sync_engine import (
    CHECKLIST_CSV,
    DATA_PATH,
    EXPORT_PATH,
    OFFICIAL_BASE_URL,
    SUMMARY_MD,
    latest_local_rows,
    preview_latest,
    sync_latest,
)


def _rows_to_df(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def render_bst_official_sync_section() -> None:
    st.title("БСТ официална синхронизация")
    st.caption(
        "Синхронизация на официалните резултати за Тото 2 — 6 от 49 към "
        "`data/prize_winner_history.csv` и journal export CSV."
    )

    st.info(
        "Тази страница не предсказва тиражи. Тя само чете официално публикувани БСТ резултати, "
        "прави проверка и записва липсващите БСТ записи."
    )

    st.markdown("### Локално състояние")
    latest_df = _rows_to_df(latest_local_rows(limit=10))
    if latest_df.empty:
        st.warning("Няма локални записи в `data/prize_winner_history.csv`.")
    else:
        show_cols = [
            column for column in [
                "draw_year", "draw_number", "draw_date", "numbers_text",
                "jackpot_eur", "winners_6", "winners_5", "winners_4", "winners_3",
            ]
            if column in latest_df.columns
        ]
        st.dataframe(latest_df[show_cols], use_container_width=True, hide_index=True)

    st.markdown("### Официален източник")
    st.write(OFFICIAL_BASE_URL)

    recent_count = st.slider("Колко последни официални тиража да провери", 1, 15, 5)
    update_existing = st.checkbox(
        "Обнови и вече съществуващи записи",
        value=False,
        help="Остави изключено за нормална работа. Включи само ако искаш да презапишеш съществуващи БСТ записи.",
    )

    left, right = st.columns(2)

    with left:
        if st.button("Провери БСТ без запис", type="secondary"):
            with st.spinner("Чета официалната БСТ страница..."):
                try:
                    result = preview_latest(recent_count=recent_count)
                    st.success("Проверката завърши.")
                    st.dataframe(_rows_to_df(result.get("latest_candidates", [])), use_container_width=True, hide_index=True)
                except Exception as exc:
                    st.error(f"Неуспешна проверка: {exc}")

    with right:
        if st.button("Синхронизирай и запиши", type="primary"):
            with st.spinner("Чета БСТ, валидирам и записвам липсващите записи..."):
                try:
                    result = sync_latest(recent_count=recent_count, update_existing=update_existing)
                    inserted = len(result.get("inserted", []))
                    updated = len(result.get("updated", []))
                    skipped = len(result.get("skipped", []))
                    errors = len(result.get("parse_errors", []))
                    st.success(
                        f"Готово: добавени {inserted}, обновени {updated}, пропуснати {skipped}, грешки {errors}."
                    )

                    if result.get("inserted"):
                        st.markdown("#### Добавени записи")
                        st.dataframe(_rows_to_df(result["inserted"]), use_container_width=True, hide_index=True)

                    if result.get("updated"):
                        st.markdown("#### Обновени записи")
                        st.dataframe(_rows_to_df(result["updated"]), use_container_width=True, hide_index=True)

                    if result.get("parse_errors"):
                        st.markdown("#### Грешки при четене")
                        st.dataframe(_rows_to_df(result["parse_errors"]), use_container_width=True, hide_index=True)

                except Exception as exc:
                    st.error(f"Неуспешна синхронизация: {exc}")

    st.markdown("### Файлове, които се обновяват")
    st.code(
        "\n".join([
            "data/prize_winner_history.csv",
            "data/user_journal_exports/prize_winner_history.csv",
            "data/raw/bst_official_sync/",
            "reports/bst_official_sync_summary.md",
            "reports/bst_official_sync_checklist.csv",
        ]),
        language="text",
    )

    if SUMMARY_MD.exists():
        with st.expander("Последен sync summary", expanded=False):
            st.markdown(SUMMARY_MD.read_text(encoding="utf-8", errors="replace"))

    if CHECKLIST_CSV.exists():
        with st.expander("Последен sync checklist", expanded=False):
            try:
                st.dataframe(pd.read_csv(CHECKLIST_CSV), use_container_width=True, hide_index=True)
            except Exception:
                st.warning("Checklist CSV не може да бъде прочетен.")

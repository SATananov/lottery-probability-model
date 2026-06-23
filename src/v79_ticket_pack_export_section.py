from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.v79_ticket_pack_export_engine import (
    V79_COPY_TEXT_TXT,
    V79_EXECUTION_CHECKLIST_CSV,
    V79_EXPORT_TICKETS_CSV,
    build_ticket_pack_export_center,
    load_summary,
)


COLUMN_LABELS = {
    "export_order": "Ред",
    "ticket_id": "Фиш",
    "numbers_display": "Числа",
    "numbers_compact": "Числа за запис",
    "plan_role": "Роля от финалния план",
    "export_status": "Статус за изпълнение",
    "decision_score": "Оценка",
    "risk_level": "Риск",
    "execution_note": "Бележка",
    "order": "Ред",
    "check_item": "Проверка",
    "status": "Статус",
    "details": "Детайли",
}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _display_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df.rename(columns={column: COLUMN_LABELS.get(column, column) for column in df.columns})




def _v79_polish_df(df):
    try:
        if df is None:
            return df
        if getattr(df, "empty", False):
            return df

        polished = df.copy()

        rename_map = {
            "Бележка": "Бележка",
            "role_from_step_78": "Роля от финалния план",
            "role_in_plan": "Роля в плана",
            "execution_status": "Статус за изпълнение",
            "status": "Статус",
            "details": "Детайли",
            "action": "Действие",
            "check": "Проверка",
            "warning": "Предупреждение",
            "risk": "Риск",
            "numbers": "Числа",
            "numbers_to_write": "Числа за запис",
            "ticket": "Фиш",
            "ticket_id": "Фиш",
            "rank": "Ранг",
            "score": "Оценка",
            "validation": "Валидация",
            "neural_score": "Невронна оценка",
            "structural_score": "Структурна оценка",
            "model_label": "Модел",
            "snapshot_created_at": "Дата на заключване",
            "данните_draw_index_at_snapshot": "Тиражи в данните при запис",
        }

        try:
            polished = polished.rename(columns=rename_map)
        except Exception:
            pass

        replacements = {
            "Финалният план": "Финалният план",
            "Финалният пакет": "Финалният пакет",
            "Step 73.1": "предварителната проверка",
            "step 78": "финалният план",
            "step 79": "финалният пакет",
            "данните": "данните",
            "данните": "данните",
            "записа на новия тираж": "записа на новия тираж",
            "Добавяне на тираж": "Добавяне на тираж",
            "проверка на резултата": "проверка на резултата",
            "последния чист checkpoint": "последния чист checkpoint",
            "работен процес": "работен процес",
            "Проверки": "Проверки",
            "проверки": "проверки",
            "Бележка": "Бележка",
        }

        for col in list(getattr(polished, "columns", [])):
            try:
                series = polished[col].astype(str)
                for old, new in replacements.items():
                    series = series.str.replace(old, new, regex=False)
                polished[col] = series
            except Exception:
                pass

        return polished
    except Exception:
        return df

def render_v79_ticket_pack_export_section() -> None:
    st.title("Експорт и изпълнение")
    st.caption(
        "Финалният пакет подготвя фишовете за копиране, печат и дисциплинирано изпълнение."
    )

    st.warning(
        "Това е организационен слой за финалния пакет. "
        "Лотарията остава случайна игра и няма гаранция за печалба."
    )

    action_col, info_col = st.columns([1, 2])
    with action_col:
        if st.button("Обнови експорт пакета", type="primary"):
            with st.spinner("Подготвям фишове за копиране, проверки и export files..."):
                build_ticket_pack_export_center()
            st.success("Финалният пакет е обновен успешно.")
            st.rerun()

    with info_col:
        st.info(
            "Използвай този екран за финално копиране на основните фишове и контрол преди игра."
        )

    summary = load_summary()

    metric_cols = st.columns(5)
    metric_cols[0].metric("Кандидати", summary.get("candidate_tickets", 0))
    metric_cols[1].metric("За игра", summary.get("play_tickets", 0))
    metric_cols[2].metric("Резерви", summary.get("reserve_tickets", 0))
    metric_cols[3].metric("Проверки", summary.get("проверки_items", 0))
    metric_cols[4].metric("Предупреждения", summary.get("warning_items_from_step78", 0))

    st.subheader("Готов текст за копиране")
    if V79_COPY_TEXT_TXT.exists():
        copy_text = V79_COPY_TEXT_TXT.read_text(encoding="utf-8")
        st.text_area("Копирай финалния пакет", copy_text, height=260)
    else:
        st.info("Още няма готов текст за копиране. Натисни бутона за обновяване.")

    st.subheader("Фишове за изпълнение")
    export_df = _read_csv(V79_EXPORT_TICKETS_CSV)
    if export_df.empty:
        st.info("Няма генериран export пакет.")
    else:
        st.dataframe(_display_df(export_df), use_container_width=True, hide_index=True)


    # Визуални фишове от заключения запис — реален игрови лист за изпълнение.
    try:
        from src.v84_1_final_plan_snapshot_slips import render_v84_1_final_plan_snapshot_slips

        render_v84_1_final_plan_snapshot_slips()
    except Exception as exc:
        st.warning(f"Неуспешно зареждане на визуалните фишове: {exc}")

    st.subheader("Проверки преди игра")
    проверки_df = _read_csv(V79_EXECUTION_CHECKLIST_CSV)
    if проверки_df.empty:
        st.info("Няма проверки.")
    else:
        st.dataframe(_display_df(проверки_df), use_container_width=True, hide_index=True)

    with st.expander("Как да се чете финалният пакет"):
        st.markdown(
            "- **За игра** са основните фишове от Финалният план.\n"
            "- **Резерва** не се добавя автоматично — използва се само при ръчна причина.\n"
            "- **Copy text** е готов за копиране или печат.\n"
            "- След реален тираж първо сравни резултата с пакета, после обнови данните."
        )

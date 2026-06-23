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
    "ticket_id": "Комбинация",
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
            "ticket": "Комбинация",
            "ticket_id": "Комбинация",
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



def _v841_combo_visible_polish_df(df):
    try:
        if df is None:
            return df
        if getattr(df, "empty", False):
            return df

        polished = df.copy()

        rename_map = {
            "safe_note": "Важно уточнение",
            "role_in_plan": "Роля в плана",
            "role_from_step_78": "Роля от финалния план",
            "execution_status": "Статус за изпълнение",
            "numbers_to_write": "Числа за запис",
            "ticket": "Комбинация",
            "ticket_id": "Комбинация",
        }

        try:
            polished = polished.rename(columns=rename_map)
        except Exception:
            pass

        replacements = {
            "основните комбинации": "основните комбинации",
            "Основните фишове": "Основните комбинации",
            "основни фишове": "основни комбинации",
            "Основни фишове": "Основни комбинации",
            "основен фиш": "основна комбинация",
            "Основен фиш": "Основна комбинация",
            "резервните фишове": "резервните комбинации",
            "Резервните фишове": "Резервните комбинации",
            "резервни фишове": "резервни комбинации",
            "Резервни фишове": "Резервни комбинации",
            "резервен фиш": "резервна комбинация",
            "Резервен фиш": "Резервна комбинация",
            "фишове в пакета": "комбинации в пакета",
            "Фишове в пакета": "Комбинации в пакета",
            "фиша в пакета": "комбинации в пакета",
            "Комбинации за изпълнение": "Комбинации за изпълнение",
            "фишове за изпълнение": "комбинации за изпълнение",
            "Фиш за изпълнение": "Комбинация за изпълнение",
            "фиш за изпълнение": "комбинация за изпълнение",
            "Фиш ": "Комбинация ",
            "clean checkpoint": "последното чисто състояние",
            "Добавяне на тираж save": "записа на новия тираж",
            "Добавяне на тираж": "Добавяне на тираж",
            "checker/result сравнение": "проверка на резултата",
            "checker/result": "проверка на резултата",
            "workflow": "работен процес",
            "dataset-а": "данните",
            "dataset": "данните",
            "Step 78": "Финалният план",
            "Step 79": "Финалният пакет",
            "Checklist": "Проверки",
        }

        for col in list(getattr(polished, "columns", [])):
            try:
                series = polished[col].astype(str)
                for old, new in replacements.items():
                    series = series.str.replace(old, new, regex=False)
                polished[col] = series
            except Exception:
                pass

        # Streamlit cannot render duplicate column names.
        # Keep labels human-readable while guaranteeing uniqueness.
        used = set()
        new_columns = []
        for col in list(polished.columns):
            base = str(col)
            if base in used:
                if base == "Бележка":
                    candidate_base = "Допълнителна бележка"
                elif base == "Важно уточнение":
                    candidate_base = "Допълнително уточнение"
                else:
                    candidate_base = base

                candidate = candidate_base
                counter = 2
                while candidate in used:
                    candidate = f"{candidate_base} {counter}"
                    counter += 1
                new_columns.append(candidate)
                used.add(candidate)
            else:
                new_columns.append(base)
                used.add(base)

        polished.columns = new_columns

        return polished
    except Exception:
        return df

def render_v79_ticket_pack_export_section() -> None:
    st.title("Експорт и изпълнение")
    st.caption(
        "Финалният пакет подготвя комбинациите за копиране, печат и дисциплинирано изпълнение."
    )

    st.warning(
        "Това е организационен слой за финалния пакет. "
        "Лотарията остава случайна игра и няма гаранция за печалба."
    )

    action_col, info_col = st.columns([1, 2])
    with action_col:
        if st.button("Обнови пакета за изтегляне", type="primary"):
            with st.spinner("Подготвям комбинациите за копиране, проверки и файлове за изтегляне..."):
                build_ticket_pack_export_center()
            st.success("Финалният пакет е обновен успешно.")
            st.rerun()

    with info_col:
        st.info(
            "Използвай този екран за финално копиране на основните комбинации и контрол преди игра."
        )

    summary = load_summary()

    metric_cols = st.columns(5)
    metric_cols[0].metric("Кандидат комбинации", summary.get("candidate_tickets", 0))
    metric_cols[1].metric("Комбинации за игра", summary.get("play_tickets", 0))
    metric_cols[2].metric("Резервни комбинации", summary.get("reserve_tickets", 0))
    metric_cols[3].metric("Проверки", summary.get("checklist_items", 0))
    metric_cols[4].metric("Предупреждения", summary.get("warning_items_from_step78", 0))

    st.subheader("Готов текст за копиране")
    if V79_COPY_TEXT_TXT.exists():
        copy_text = V79_COPY_TEXT_TXT.read_text(encoding="utf-8")
        st.text_area("Копирай финалния пакет", copy_text, height=260)
    else:
        st.info("Още няма готов текст за копиране. Натисни бутона за обновяване.")

    st.subheader("Комбинации за изпълнение")
    export_df = _read_csv(V79_EXPORT_TICKETS_CSV)
    if export_df.empty:
        st.info("Няма генериран пакет за изтегляне.")
    else:
        st.dataframe(_v841_combo_visible_polish_df(_display_df(export_df)), use_container_width=True, hide_index=True)


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
        st.dataframe(_v841_combo_visible_polish_df(_display_df(проверки_df)), use_container_width=True, hide_index=True)

    with st.expander("Как да се чете финалният пакет"):
        st.markdown(
            "- **За игра** са основните комбинации от Финалният план.\n"
            "- **Резерва** не се добавя автоматично — използва се само при ръчна причина.\n"
            "- **Текстът за копиране** е готов за копиране или печат.\n"
            "- След реален тираж първо сравни резултата с пакета, после обнови данните."
        )

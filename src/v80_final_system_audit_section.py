from __future__ import annotations

from pathlib import Path
import json
import pandas as pd
import streamlit as st


V80_COLUMN_LABELS_BG = {
    "check": "Проверка",
    "check_name": "Проверка",
    "check_item": "Проверка",
    "category": "Категория",
    "section": "Секция",
    "component": "Компонент",
    "step": "Стъпка",
    "step_order": "Ред",
    "order": "Ред",
    "page": "Страница",
    "label": "Етикет",
    "name": "Име",
    "path": "Път",
    "file": "Файл",
    "file_path": "Файл",
    "artifact": "Артефакт",
    "artifact_path": "Артефакт",
    "artifact_exists": "Наличен артефакт",
    "exists": "Наличен",
    "status": "Статус",
    "result": "Резултат",
    "details": "Детайли",
    "note": "Бележка",
    "safe_note": "Важно уточнение",
    "issue": "Проблем",
    "issues": "Проблеми",
    "severity": "Тежест",
    "recommendation": "Препоръка",
    "source": "Източник",
    "target": "Цел",
    "from_step": "От стъпка",
    "to_step": "Към стъпка",
    "plan": "План",
    "sync_plan": "План за синхронизация",
    "chain": "Верига",
    "script": "Скрипт",
    "command": "Команда",
    "dataset": "Набор от данни",
    "dataset_file": "Файл с данни",
    "rows": "Редове",
    "row_count": "Брой редове",
    "columns": "Колони",
    "column_count": "Брой колони",
    "min_year": "Първа година",
    "max_year": "Последна година",
    "latest_date": "Последна дата",
    "latest_draw_date": "Дата на последен тираж",
    "latest_numbers": "Последни числа",
    "size": "Размер",
    "size_bytes": "Размер в байтове",
    "kind": "Тип",
    "type": "Тип",
    "quality_check": "Проверка на качеството",
    "compile": "Компилация",
    "labels": "Етикети",
    "encoding": "Кодировка",
    "cyrillic": "Кирилица",
    "model": "Модел",
    "report": "Отчет",
    "expected": "Очаквано",
    "actual": "Реално",
    "passed": "Минато",
    "failed": "Неуспешно",
    "warning": "Предупреждение",
}


def _v80_pretty_unknown_column(column: object) -> str:
    raw = str(column).strip()
    lower = raw.lower()

    # Conservative fallback for unknown technical columns.
    fallback_map = {
        "id": "ID",
        "ok": "OK",
        "json": "JSON",
        "csv": "CSV",
        "zip": "ZIP",
        "ui": "UI",
        "ux": "UX",
    }
    if lower in fallback_map:
        return fallback_map[lower]

    words = raw.replace("-", "_").split("_")
    translated_words = []
    word_map = {
        "draw": "тираж",
        "draws": "тиражи",
        "number": "число",
        "numbers": "числа",
        "date": "дата",
        "year": "година",
        "years": "години",
        "count": "брой",
        "total": "общо",
        "missing": "липсващи",
        "present": "налични",
        "valid": "валидни",
        "invalid": "невалидни",
        "input": "вход",
        "output": "изход",
        "summary": "обобщение",
        "manifest": "опис",
        "release": "финален пакет",
        "dependency": "зависимост",
        "sync": "синхрон",
        "audit": "одит",
        "file": "файл",
        "files": "файлове",
        "model": "модел",
        "models": "модели",
        "report": "отчет",
        "reports": "отчети",
        "status": "статус",
        "message": "съобщение",
        "note": "бележка",
    }

    for word in words:
        translated_words.append(word_map.get(word.lower(), word))

    pretty = " ".join(translated_words).strip()
    if not pretty:
        return raw
    return pretty[:1].upper() + pretty[1:]


def _v80_translate_dataframe(df):
    if df is None or getattr(df, "empty", True):
        return df

    renamed = df.copy()
    renamed.columns = [
        V80_COLUMN_LABELS_BG.get(str(column), _v80_pretty_unknown_column(column))
        for column in renamed.columns
    ]
    return renamed

from src.v80_final_system_audit_engine import (
    ARTIFACT_AUDIT_CSV,
    DATASET_AUDIT_CSV,
    FILE_QUALITY_AUDIT_CSV,
    SAFE_NOTE,
    SUMMARY_JSON,
    SYNC_PLAN_AUDIT_CSV,
    build_final_system_audit_center,
)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        return pd.DataFrame()


def _status_badge(status: str) -> str:
    return "✅ OK" if str(status) == "OK" else "⚠️ За преглед"


def render_v80_final_system_audit_section() -> None:
    st.title("🧾 Финален системен одит")
    st.caption(
        "Контролен център за datasets, артефакти, sync планове, Python compile, JSON/CSV parse и кирилица."
    )
    st.warning(SAFE_NOTE)

    action_col, info_col = st.columns([1, 2])
    with action_col:
        if st.button("Обнови финалния одит", type="primary", key="v80_refresh_audit"):
            with st.spinner("Проверявам datasets, артефакти, sync планове и файлово качество..."):
                build_final_system_audit_center()
            st.success("Step 80 одитът е обновен успешно.")
            st.rerun()
    with info_col:
        st.info(
            "Този екран не избира числа. Той проверява дали системата е последователна, чиста и готова за checkpoint."
        )

    summary = _read_json(SUMMARY_JSON)
    if not summary:
        st.info("Още няма Step 80 отчет. Натисни бутона за обновяване.")
        return

    cols = st.columns(5)
    cols[0].metric("Статус", _status_badge(str(summary.get("status", ""))))
    cols[1].metric("Набори данни", summary.get("datasets_checked", 0))
    cols[2].metric("Артефакти", summary.get("artifacts_checked", 0))
    cols[3].metric("Планове за синхронизация", summary.get("sync_plans_checked", 0))
    cols[4].metric("Проблеми", summary.get("issues_found", 0))

    st.subheader("Dataset проверки")
    dataset_df = _read_csv(DATASET_AUDIT_CSV)
    if dataset_df.empty:
        st.info("Няма таблица за одит на данните.")
    else:
        st.dataframe(_v80_translate_dataframe(dataset_df), use_container_width=True, hide_index=True)

    st.subheader("Планове за синхронизация")
    sync_df = _read_csv(SYNC_PLAN_AUDIT_CSV)
    if sync_df.empty:
        st.info("Няма таблица за одит на плановете за синхронизация.")
    else:
        st.dataframe(_v80_translate_dataframe(sync_df), use_container_width=True, hide_index=True)

    with st.expander("Step 76–79 артефакти"):
        artifact_df = _read_csv(ARTIFACT_AUDIT_CSV)
        if artifact_df.empty:
            st.info("Няма таблица за одит на артефактите.")
        else:
            st.dataframe(_v80_translate_dataframe(artifact_df), use_container_width=True, hide_index=True)

    with st.expander("Файлово качество: компилация, етикети, кирилица"):
        quality_df = _read_csv(FILE_QUALITY_AUDIT_CSV)
        if quality_df.empty:
            st.info("Няма таблица за одит на качеството.")
        else:
            st.dataframe(_v80_translate_dataframe(quality_df), use_container_width=True, hide_index=True)

    with st.expander("Как да се чете Step 80"):
        st.markdown(
            "- **OK** означава, че проверката е минала според текущите правила.\n"
            "- **За преглед** не значи автоматично счупване, а че има файл, стойност или chain, който трябва да се види.\n"
            "- Одитът проверява стабилност на системата, не вероятност за печалба.\n"
            "- След нов тираж първо минава веригата за обновяване, после Step 80 и накрая Step 74 контрол на синхрона."
        )

from __future__ import annotations

from pathlib import Path
import csv
import json

import streamlit as st

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "reports" / "v66_weighted_smart_ensemble_summary.json"
SCORES_PATH = ROOT / "reports" / "v66_weighted_smart_ensemble_scores.csv"
MODEL_PATH = ROOT / "models" / "v66" / "v66_weighted_smart_ensemble_model.json"

SCORE_COLUMNS = [
    ("rank", "Ранг"),
    ("number", "Число"),
    ("weighted_score_percent", "Претеглена оценка %"),
    ("source_count", "Брой източници"),
    ("top_sources", "Основни източници"),
    ("status", "Статус"),
]


def _load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _as_float(value, default=0.0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _format_value(key, value):
    if key == "weighted_score_percent":
        return f"{_as_float(value):.2f}%"

    if key in {"rank", "number", "source_count"}:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return value

    return value


def _localize_score_rows(rows):
    result = []
    for row in rows:
        item = {}
        for source_key, bg_label in SCORE_COLUMNS:
            item[bg_label] = _format_value(source_key, row.get(source_key, ""))
        result.append(item)
    return result


def _show_dataframe(rows):
    if not rows:
        st.info("Няма налични претеглени оценки.")
        return

    localized = _localize_score_rows(rows)

    if pd is not None:
        st.dataframe(pd.DataFrame(localized), use_container_width=True, hide_index=True)
    else:
        st.table(localized)


def render_v66_weighted_smart_ensemble_section():
    st.title("Претеглен комбиниран анализ")
    st.caption(
        "Комбинира Step 65 адаптивните тегла с наличните източници на оценка, "
        "за да даде претеглена статистическа оценка на числата. "
        "Това не е гаранция за печалба."
    )

    summary = _load_json(SUMMARY_PATH)
    scores = _load_csv(SCORES_PATH)
    model = _load_json(MODEL_PATH)

    if not summary or not model:
        st.warning(
            "Липсва Step 66 отчет/модел. "
            "Пусни: python scripts/v66_build_weighted_smart_ensemble.py"
        )
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Използвани източници", summary.get("sources_used", 0))
    col2.metric("Оценени числа", summary.get("numbers_scored", 0))
    col3.metric("Водещо число", summary.get("top_number", "-"))
    col4.metric("Водеща оценка", f"{summary.get('top_weighted_score_percent', 0)}%")

    st.info(
        "Step 66 не заменя случайността на лотарията. "
        "Той само подрежда статистическите сигнали според тежестта на моделите от Step 65."
    )

    source_models = model.get("source_models", [])
    if source_models:
        st.subheader("Използвани model-weight източници")
        source_rows = []
        for item in source_models:
            source_rows.append({
                "Модул / модел": item.get("model_label", ""),
                "Step 65 тегло": f"{_as_float(item.get('original_adaptive_weight')) * 100:.2f}%",
                "Използвано Step 66 тегло": f"{_as_float(item.get('used_weight')) * 100:.2f}%",
                "Файлове": ", ".join(item.get("source_files", [])),
            })

        if pd is not None:
            st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)
        else:
            st.table(source_rows)

    st.subheader("Претеглени числа")
    _show_dataframe(scores[:25])

    tickets = model.get("reference_tickets", [])
    if tickets:
        st.subheader("Референтни комбинации")
        st.caption(
            "Това са статистически референтни комбинации от претеглените сигнали, "
            "не обещание за печалба."
        )

        for ticket in tickets:
            numbers = ", ".join(str(n) for n in ticket.get("numbers", []))
            st.markdown(f"**Комбинация {ticket.get('ticket_id')}**: {numbers}")

    skipped = summary.get("skipped_sources", [])
    if skipped:
        with st.expander("Пропуснати източници"):
            for item in skipped:
                st.write(f"- `{item.get('model_name')}` — {item.get('reason')}")

    with st.expander("Как работи Step 66"):
        st.markdown(
            """
1. Чете адаптивните тегла от **Step 65**.
2. Намира наличните score/model файлове от по-старите analysis modules.
3. Нормализира всеки източник към скала 0–100.
4. Преизчислява теглата само между реално наличните източници на оценка.
5. Изчислява финална претеглена оценка за всяко число от 1 до 49.

Тази страница е слой за статистическо управление на сигнали. Тя не твърди, че може да предвиди бъдещ случаен тираж.
"""
        )

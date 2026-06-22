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
SUMMARY_PATH = ROOT / "reports" / "v63_model_reliability_summary.json"
SCORES_PATH = ROOT / "reports" / "v63_model_reliability_scores.csv"


COLUMNS = [
    ("rank", "Ранг"),
    ("model_label", "Модул / модел"),
    ("tracked_draws", "Проследени тиражи"),
    ("average_hits", "Средни съвпадения"),
    ("max_hits", "Най-добър резултат"),
    ("hit_rate_1_plus", "1+ попадение"),
    ("hit_rate_2_plus", "2+ попадения"),
    ("hit_rate_3_plus", "3+ попадения"),
    ("hit_rate_4_plus", "4+ попадения"),
    ("consistency_score", "Стабилност %"),
    ("reliability_score", "Надеждност %"),
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


def _format_value(key, value):
    if value is None:
        return ""

    if key in {
        "hit_rate_1_plus",
        "hit_rate_2_plus",
        "hit_rate_3_plus",
        "hit_rate_4_plus",
        "consistency_score",
        "reliability_score",
    }:
        try:
            return f"{float(value):.2f}%"
        except (TypeError, ValueError):
            return value

    if key in {"rank", "tracked_draws", "max_hits"}:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return value

    if key == "average_hits":
        try:
            return f"{float(value):.3f}"
        except (TypeError, ValueError):
            return value

    return value


def _localize_rows(rows):
    result = []
    for row in rows:
        item = {}
        for source_key, bg_label in COLUMNS:
            item[bg_label] = _format_value(source_key, row.get(source_key, ""))
        result.append(item)
    return result


def _show_table(rows):
    if not rows:
        st.info("Няма налични редове за показване.")
        return

    localized = _localize_rows(rows)

    if pd is not None:
        st.dataframe(pd.DataFrame(localized), use_container_width=True, hide_index=True)
    else:
        st.table(localized)


def render_v63_model_reliability_dashboard_section():
    st.title("Надеждност на моделите")
    st.caption(
        "Обобщава историческото представяне на моделите според Step 62 историята. "
        "Това е post-draw статистика, не гаранция и не обещание за бъдещ резултат."
    )

    summary = _load_json(SUMMARY_PATH)
    rows = _load_csv(SCORES_PATH)

    if not summary:
        st.warning(
            "Липсва Step 63 report. "
            "Пусни: python scripts/v63_build_model_reliability_dashboard.py"
        )
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Исторически редове", summary.get("history_rows", 0))
    col2.metric("Проследени тиражи", summary.get("tracked_draws", 0))
    col3.metric("Модели", summary.get("models_ranked", 0))
    col4.metric("Най-добра надеждност", f"{summary.get('best_reliability_score', 0)}%")

    if summary.get("tracked_draws", 0) < 3:
        st.info(
            "Оценката е предварителна, защото историята още съдържа малко реални тиражи. "
            "С всеки следващ добавен тираж Step 62 и Step 63 ще стават по-полезни."
        )

    best_model = summary.get("best_model_label")
    if best_model:
        st.success(f"Текущо най-силен исторически сигнал: {best_model}")

    st.subheader("Класация по историческа надеждност")
    _show_table(rows)

    st.markdown(
        """
**Как се чете тази страница**

- **Средни съвпадения** показва средно колко числа е улучвал най-близкият сигнал на модела.
- **2+ / 3+ попадения** показват колко често моделът е стигал поне до този праг.
- **Стабилност %** наказва големи колебания между различни тиражи.
- **Надеждност %** е комбинирана историческа оценка, не прогноза за печалба.
"""
    )

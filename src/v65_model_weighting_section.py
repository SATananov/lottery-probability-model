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
SUMMARY_PATH = ROOT / "reports" / "v65_model_weighting_summary.json"
WEIGHTS_PATH = ROOT / "reports" / "v65_model_weights.csv"

COLUMNS = [
    ("rank", "Ранг"),
    ("model_label", "Модул / модел"),
    ("tracked_draws", "Проследени тиражи"),
    ("reliability_score", "Надеждност %"),
    ("confidence_factor", "Коефициент доверие"),
    ("adjusted_score", "Адаптиран резултат"),
    ("adaptive_weight_percent", "Тегло %"),
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
    if value is None:
        return ""

    if key in {"reliability_score", "adaptive_weight_percent"}:
        return f"{_as_float(value):.2f}%"

    if key in {"confidence_factor", "adjusted_score"}:
        return f"{_as_float(value):.3f}"

    if key in {"rank", "tracked_draws"}:
        try:
            return int(float(value))
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
        st.info("Няма налични тегла за показване.")
        return

    localized = _localize_rows(rows)

    if pd is not None:
        st.dataframe(pd.DataFrame(localized), width="stretch", hide_index=True)
    else:
        st.table(localized)


def render_v65_model_weighting_section():
    st.title("Умно тегло на моделите")
    st.caption(
        "Преобразува историческата надеждност от Step 63 в адаптивни тегла за моделите. "
        "Това е статистическо управление на сигнали, не гаранция за печалба."
    )

    summary = _load_json(SUMMARY_PATH)
    rows = _load_csv(WEIGHTS_PATH)

    if not summary:
        st.warning(
            "Липсва Step 65 report. "
            "Пусни: python scripts/v65_build_model_weighting_center.py"
        )
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Модели с тегло", summary.get("models_weighted", 0))
    col2.metric("Мин. проследени тиражи", summary.get("min_tracked_draws", 0))
    col3.metric("Макс. проследени тиражи", summary.get("max_tracked_draws", 0))
    col4.metric("Водещо тегло", f"{summary.get('top_adaptive_weight_percent', 0)}%")

    top_model = summary.get("top_model_label")
    if top_model:
        st.success(f"Текущ водещ адаптивен сигнал: {top_model}")

    if int(summary.get("min_tracked_draws", 0) or 0) < 3:
        st.info(
            "Теглата са предварителни, защото post-draw историята още е малка. "
            "С всеки нов тираж Step 62, Step 63 и Step 65 ще стават по-надеждни."
        )

    st.subheader("Адаптивни тегла")
    _show_table(rows)

    st.markdown(
        """
**Как се чете тази страница**

- **Надеждност %** идва от Step 63 и показва историческо post-draw представяне.
- **Коефициент доверие** пази системата от прекалено силни заключения при малко проследени тиражи.
- **Адаптиран резултат** комбинира надеждност, стабилност, средни попадения и 2+/3+ hit rate.
- **Тегло %** показва каква част от общия model-signal слой получава конкретният модел.

Тази страница не казва кои числа ще се паднат. Тя казва кои модели в момента заслужават по-голяма или по-малка тежест според наличната историческа проверка.
"""
    )

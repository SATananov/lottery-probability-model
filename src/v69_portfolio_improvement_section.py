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

SUMMARY_PATH = ROOT / "reports" / "v69_portfolio_improvement_summary.json"
SUGGESTIONS_PATH = ROOT / "reports" / "v69_portfolio_improvement_suggestions.csv"
CANDIDATE_PATH = ROOT / "reports" / "v69_candidate_portfolio_tickets.csv"
MODEL_PATH = ROOT / "models" / "v69" / "v69_portfolio_improvement_model.json"

SUGGESTION_COLUMNS = [
    ("rank", "Ранг"),
    ("ticket_id", "Фиш"),
    ("remove_number", "Махни"),
    ("add_number", "Добави"),
    ("current_numbers", "Текущ фиш"),
    ("suggested_numbers", "Предложен фиш"),
    ("portfolio_score_delta", "Portfolio delta"),
    ("expected_gain_score", "Очаквана полза"),
    ("recommendation_strength", "Сила"),
    ("reason", "Причина"),
]

CANDIDATE_COLUMNS = [
    ("ticket_id", "Фиш"),
    ("strategy_label", "Стратегия"),
    ("numbers", "Числа"),
    ("average_step66_score", "Средна Step 66 оценка"),
    ("changed", "Променен"),
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
        return float(text.replace("%", "").replace(",", "."))
    except (TypeError, ValueError):
        return default


def _as_int(value, default=0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(float(text.replace(",", ".")))
    except (TypeError, ValueError):
        return default


def _format_value(key, value):
    if key in {"portfolio_score_delta", "expected_gain_score", "average_step66_score"}:
        return f"{_as_float(value):.3f}"

    if key in {"rank", "ticket_id", "remove_number", "add_number"}:
        return _as_int(value)

    if key in {"current_numbers", "suggested_numbers", "numbers"}:
        return str(value).replace(",", ", ")

    if key == "changed":
        return "Да" if str(value).lower() in {"true", "1", "yes"} else "Не"

    return value


def _localize_rows(rows, columns):
    result = []
    for row in rows:
        item = {}
        for source_key, bg_label in columns:
            item[bg_label] = _format_value(source_key, row.get(source_key, ""))
        result.append(item)
    return result


def _show_table(rows, columns):
    if not rows:
        st.info("Няма налични данни за показване.")
        return

    localized = _localize_rows(rows, columns)

    if pd is not None:
        st.dataframe(pd.DataFrame(localized), use_container_width=True, hide_index=True)
    else:
        st.table(localized)


def render_v69_portfolio_improvement_section():
    st.title("Подобряване на портфолио")
    st.caption(
        "Дава конкретни статистически предложения за подобрение на Step 67 портфолиото чрез Step 66/68 анализ. "
        "Това не е гаранция за печалба."
    )

    summary = _load_json(SUMMARY_PATH)
    model = _load_json(MODEL_PATH)

    if not summary or not model:
        st.warning(
            "Липсва Step 69 report/model. "
            "Пусни: python scripts/v69_build_portfolio_improvement_suggestions.py"
        )
        return

    suggestions = _load_csv(SUGGESTIONS_PATH)
    candidate = _load_csv(CANDIDATE_PATH)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Предложения", summary.get("suggestions_generated", 0))
    col2.metric("Промени в кандидат портфолио", summary.get("candidate_changes_applied", 0))
    col3.metric("Базова оценка", f"{summary.get('baseline_portfolio_score', 0)} / 100")
    col4.metric("Кандидат оценка", f"{summary.get('candidate_portfolio_score', 0)} / 100")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Top20 преди", f"{summary.get('baseline_top20_coverage', 0)} / 20")
    col6.metric("Top20 след", f"{summary.get('candidate_top20_coverage', 0)} / 20")
    col7.metric("Повторени двойки преди", summary.get("baseline_repeated_pairs", 0))
    col8.metric("Повторени двойки след", summary.get("candidate_repeated_pairs", 0))

    delta = _as_float(summary.get("portfolio_score_delta", 0))
    if delta >= 0:
        st.success(f"Кандидат портфолиото не влошава общата оценка. Промяна: {delta:.3f}")
    else:
        st.warning(
            f"Кандидат портфолиото има лек спад в оценката ({delta:.3f}), "
            "но може да подобрява покритието и разнообразието."
        )

    st.info(
        "Step 69 предлага промени за преглед. Той не презаписва Step 67 фишовете и не твърди, че предвижда бъдещ тираж."
    )

    under_before = summary.get("undercovered_top20_before", [])
    under_after = summary.get("undercovered_top20_after", [])

    if under_before:
        st.markdown(
            "**Непокрити top20 сигнали преди:** "
            + ", ".join(str(item.get("number")) for item in under_before)
        )

    if under_after:
        st.markdown(
            "**Непокрити top20 сигнали след кандидат промените:** "
            + ", ".join(str(item.get("number")) for item in under_after)
        )
    else:
        st.success("Кандидат портфолиото покрива всички top20 сигнали.")

    st.subheader("Най-добри предложения")
    _show_table(suggestions[:25], SUGGESTION_COLUMNS)

    st.subheader("Кандидат портфолио")
    _show_table(candidate, CANDIDATE_COLUMNS)

    applied = model.get("applied_suggestions", [])
    if applied:
        st.subheader("Приложени предложения в кандидат портфолиото")
        for item in applied:
            st.markdown(
                f"- Фиш **{item.get('ticket_id')}**: махни **{item.get('remove_number')}**, "
                f"добави **{item.get('add_number')}** — {item.get('reason')}"
            )

    with st.expander("Как работи Step 69"):
        st.markdown(
            """
1. Чете текущите фишове от **Step 67**.
2. Чете претеглена оценкаs от **Step 66**.
3. Чете portfolio анализа от **Step 68**.
4. Търси замени, които:
   - покриват непокрити top20 числа;
   - намаляват repeated pairs/triples;
   - пазят или подобряват portfolio score;
   - избягват точни исторически повторения.
5. Показва предложенията отделно, без да променя оригиналните Step 67 фишове.

Това е статистически помощник за подобрение, не предсказател на бъдещ тираж.
"""
        )

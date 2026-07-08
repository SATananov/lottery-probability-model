
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
BACKTEST_BY_MODEL_PATH = ROOT / "reports" / "v45_backtest_by_model.csv"
BACKTEST_RESULTS_PATH = ROOT / "reports" / "v45_backtest_results.csv"


def T(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


def _model_label(model: Any) -> str:
    labels = {
        "recency_250_baseline": T("\\u041c\\u043e\\u0434\\u0435\\u043b \\u043f\\u043e \\u0441\\u043a\\u043e\\u0440\\u043e\\u0448\\u043d\\u0430 \\u0430\\u043a\\u0442\\u0438\\u0432\\u043d\\u043e\\u0441\\u0442"),
        "frequency_baseline": T("\\u0427\\u0435\\u0441\\u0442\\u043e\\u0442\\u0435\\u043d \\u043c\\u043e\\u0434\\u0435\\u043b"),
        "gap_rhythm_statistical": T("\\u041c\\u043e\\u0434\\u0435\\u043b \\u043f\\u043e \\u0438\\u043d\\u0442\\u0435\\u0440\\u0432\\u0430\\u043b\\u0435\\u043d \\u0440\\u0438\\u0442\\u044a\\u043c"),
        "random_baseline": T("\\u0421\\u043b\\u0443\\u0447\\u0430\\u0435\\u043d \\u0431\\u0430\\u0437\\u043e\\u0432 \\u043c\\u043e\\u0434\\u0435\\u043b"),
        "sgd_logistic_probability": T("\\u0412\\u0435\\u0440\\u043e\\u044f\\u0442\\u043d\\u043e\\u0441\\u0442\\u0435\\u043d ML \\u043c\\u043e\\u0434\\u0435\\u043b"),
        "gaussian_naive_bayes": T("Naive Bayes \\u043c\\u043e\\u0434\\u0435\\u043b"),
        "v45_pro_ensemble": T("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0438\\u0440\\u0430\\u043d Pro \\u0430\\u043d\\u0441\\u0430\\u043c\\u0431\\u044a\\u043b"),
    }
    return labels.get(str(model), str(model))


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _prepare_backtest_table_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Return a display-safe copy with friendly and unique Bulgarian column labels."""
    if df is None or df.empty:
        return pd.DataFrame() if df is None else df.copy()

    label_map = {
        "model": T("\\u041c\\u043e\\u0434\\u0435\\u043b"),
        "model_name": T("\\u041c\\u043e\\u0434\\u0435\\u043b"),
        "event_index": T("\\u0420\\u0435\\u0434"),
        "draw_year": T("\\u0413\\u043e\\u0434\\u0438\\u043d\\u0430"),
        "year": T("\\u0413\\u043e\\u0434\\u0438\\u043d\\u0430"),
        T("\\u0413\\u043e\\u0434\\u0438\\u043d\\u0430"): T("\\u0413\\u043e\\u0434\\u0438\\u043d\\u0430"),
        "draw_number": T("\\u0422\\u0438\\u0440\\u0430\\u0436 \\u2116"),
        "draw_no": T("\\u0422\\u0438\\u0440\\u0430\\u0436 \\u2116"),
        T("\\u0422\\u0438\\u0440\\u0430\\u0436 \\u2116"): T("\\u0422\\u0438\\u0440\\u0430\\u0436 \\u2116"),
        "draw_date": T("\\u0414\\u0430\\u0442\\u0430"),
        "date": T("\\u0414\\u0430\\u0442\\u0430"),
        T("\\u0414\\u0430\\u0442\\u0430"): T("\\u0414\\u0430\\u0442\\u0430"),
        "predicted_top6": T("\\u041f\\u0440\\u0435\\u0434\\u043b\\u043e\\u0436\\u0435\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"),
        "predicted_numbers": T("\\u041f\\u0440\\u0435\\u0434\\u043b\\u043e\\u0436\\u0435\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"),
        "actual_numbers": T("\\u0420\\u0435\\u0430\\u043b\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"),
        "real_numbers": T("\\u0420\\u0435\\u0430\\u043b\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"),
        "hits": T("\\u041f\\u043e\\u0437\\u043d\\u0430\\u0442\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"),
        "hit_count": T("\\u041f\\u043e\\u0437\\u043d\\u0430\\u0442\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"),
        "matched_numbers": T("\\u041f\\u043e\\u0437\\u043d\\u0430\\u0442\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"),
        T("\\u041f\\u043e\\u0437\\u043d\\u0430\\u0442\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"): T("\\u041f\\u043e\\u0437\\u043d\\u0430\\u0442\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"),
    }

    result = df.copy()
    new_columns: list[str] = []
    seen: dict[str, int] = {}

    for column in result.columns:
        base = label_map.get(str(column), str(column))
        count = seen.get(base, 0) + 1
        seen[base] = count
        if count == 1:
            new_columns.append(base)
        else:
            new_columns.append(f"{base} ({count})")

    result.columns = new_columns
    return result


def _best_available_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _format_float(value: Any, digits: int = 4) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return "-"


def _show_model_cards(df: pd.DataFrame) -> None:
    if df.empty:
        st.info(T("\\u041d\\u044f\\u043c\\u0430 \\u043d\\u0430\\u043b\\u0438\\u0447\\u0435\\u043d \\u0444\\u0430\\u0439\\u043b reports/v45_backtest_by_model.csv. \\u041f\\u0443\\u0441\\u043d\\u0438 \\u043e\\u0431\\u0443\\u0447\\u0435\\u043d\\u0438\\u0435\\u0442\\u043e, \\u0437\\u0430 \\u0434\\u0430 \\u0441\\u0435 \\u0433\\u0435\\u043d\\u0435\\u0440\\u0438\\u0440\\u0430 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430\\u0442\\u0430 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430."))
        return

    model_col = _best_available_column(df, ["model", "model_name"])
    avg_col = _best_available_column(df, ["average_hits_top6", "avg_hits_top6", "avg_hits"])
    max_col = _best_available_column(df, ["max_hits_top6", "max_hits"])

    if not model_col or not avg_col:
        st.dataframe(df, hide_index=True, width="stretch")
        return

    view = df.copy()
    view[T("\\u041f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430\\u043d \\u043c\\u043e\\u0434\\u0435\\u043b")] = view[model_col].map(_model_label)
    view = view.sort_values(avg_col, ascending=False)

    best = view.iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric(T("\\u041d\\u0430\\u0439-\\u0434\\u043e\\u0431\\u044a\\u0440 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u043c\\u043e\\u0434\\u0435\\u043b"), best[T("\\u041f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430\\u043d \\u043c\\u043e\\u0434\\u0435\\u043b")])
    c2.metric(T("\\u0421\\u0440\\u0435\\u0434\\u043d\\u043e \\u0443\\u0446\\u0435\\u043b\\u0435\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430"), _format_float(best[avg_col], 4))
    if max_col:
        c3.metric(T("\\u041d\\u0430\\u0439-\\u0434\\u043e\\u0431\\u044a\\u0440 \\u0435\\u0434\\u0438\\u043d\\u0438\\u0447\\u0435\\u043d \\u0440\\u0435\\u0437\\u0443\\u043b\\u0442\\u0430\\u0442"), str(best[max_col]))
    else:
        c3.metric(T("\\u0421\\u0440\\u0430\\u0432\\u043d\\u0435\\u043d\\u0438 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438"), str(len(view)))

    st.caption(T("\\u0422\\u043e\\u0432\\u0430 \\u0435 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430 \\u0432\\u044a\\u0440\\u0445\\u0443 \\u043c\\u0438\\u043d\\u0430\\u043b\\u0438 \\u0442\\u0438\\u0440\\u0430\\u0436\\u0438. \\u0422\\u044f \\u043f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430 \\u043a\\u0430\\u043a \\u0441\\u0435 \\u0435 \\u0434\\u044a\\u0440\\u0436\\u0430\\u043b \\u043c\\u043e\\u0434\\u0435\\u043b\\u044a\\u0442 \\u043d\\u0430\\u0437\\u0430\\u0434 \\u0432\\u044a\\u0432 \\u0432\\u0440\\u0435\\u043c\\u0435\\u0442\\u043e, \\u043d\\u043e \\u043d\\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0442\\u0438\\u0440\\u0430 \\u0431\\u044a\\u0434\\u0435\\u0449 \\u0440\\u0435\\u0437\\u0443\\u043b\\u0442\\u0430\\u0442."))

    columns_to_show = [T("\\u041f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430\\u043d \\u043c\\u043e\\u0434\\u0435\\u043b")]
    rename_map = {T("\\u041f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430\\u043d \\u043c\\u043e\\u0434\\u0435\\u043b"): T("\\u041c\\u043e\\u0434\\u0435\\u043b")}

    if avg_col:
        columns_to_show.append(avg_col)
        rename_map[avg_col] = T("\\u0421\\u0440\\u0435\\u0434\\u043d\\u043e \\u0443\\u0446\\u0435\\u043b\\u0435\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430")

    if max_col:
        columns_to_show.append(max_col)
        rename_map[max_col] = T("\\u041c\\u0430\\u043a\\u0441\\u0438\\u043c\\u0443\\u043c \\u0443\\u0446\\u0435\\u043b\\u0435\\u043d\\u0438")

    for col in ["hits_0", "hits_1", "hits_2", "hits_3", "hits_4", "hits_5", "hits_6"]:
        if col in view.columns:
            columns_to_show.append(col)
            rename_map[col] = T("\\u0423\\u0446\\u0435\\u043b\\u0435\\u043d\\u0438 ") + col.replace("hits_", "")

    shown = view[columns_to_show].rename(columns=rename_map)
    st.dataframe(shown, hide_index=True, width="stretch")


def _show_distribution(df: pd.DataFrame) -> None:
    if df.empty:
        return

    model_col = _best_available_column(df, ["model", "model_name"])
    avg_col = _best_available_column(df, ["average_hits_top6", "avg_hits_top6", "avg_hits"])
    hit_cols = [col for col in df.columns if col.startswith("hits_")]

    if not model_col or not hit_cols:
        st.info(T("\\u041d\\u044f\\u043c\\u0430 \\u043e\\u0442\\u0434\\u0435\\u043b\\u043d\\u0430 hit distribution \\u0442\\u0430\\u0431\\u043b\\u0438\\u0446\\u0430 \\u0432 \\u0442\\u0435\\u043a\\u0443\\u0449\\u0438\\u044f \\u043e\\u0442\\u0447\\u0435\\u0442. \\u041f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430\\u043c\\u0435 \\u043d\\u0430\\u043b\\u0438\\u0447\\u043d\\u043e\\u0442\\u043e \\u0441\\u0440\\u0430\\u0432\\u043d\\u0435\\u043d\\u0438\\u0435 \\u043f\\u043e \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438."))
        return

    st.subheader(T("\\u0420\\u0430\\u0437\\u043f\\u0440\\u0435\\u0434\\u0435\\u043b\\u0435\\u043d\\u0438\\u0435 \\u043d\\u0430 \\u0443\\u0446\\u0435\\u043b\\u0432\\u0430\\u043d\\u0438\\u044f\\u0442\\u0430"))
    st.caption(T("\\u041a\\u043e\\u043b\\u043a\\u043e \\u0447\\u0435\\u0441\\u0442\\u043e \\u0434\\u0430\\u0434\\u0435\\u043d \\u043c\\u043e\\u0434\\u0435\\u043b \\u0435 \\u0443\\u0446\\u0435\\u043b\\u0432\\u0430\\u043b 0, 1, 2, 3 \\u0438\\u043b\\u0438 \\u043f\\u043e\\u0432\\u0435\\u0447\\u0435 \\u0447\\u0438\\u0441\\u043b\\u0430 \\u043f\\u0440\\u0438 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430\\u0442\\u0430 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430."))

    view = df.copy()
    view[T("\\u041c\\u043e\\u0434\\u0435\\u043b")] = view[model_col].map(_model_label)

    cols = [T("\\u041c\\u043e\\u0434\\u0435\\u043b")] + hit_cols
    shown = view[cols].copy()
    shown = shown.rename(columns={col: T("\\u0423\\u0446\\u0435\\u043b\\u0435\\u043d\\u0438 ") + col.replace("hits_", "") for col in hit_cols})
    st.dataframe(shown, hide_index=True, width="stretch")

    if avg_col:
        chart_df = view[[T("\\u041c\\u043e\\u0434\\u0435\\u043b"), avg_col]].rename(columns={avg_col: T("\\u0421\\u0440\\u0435\\u0434\\u043d\\u043e \\u0443\\u0446\\u0435\\u043b\\u0435\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430")})
        st.bar_chart(chart_df.set_index(T("\\u041c\\u043e\\u0434\\u0435\\u043b")))


def _show_raw_results(df: pd.DataFrame) -> None:
    if df.empty:
        st.info(T("\\u041d\\u044f\\u043c\\u0430 \\u043d\\u0430\\u043b\\u0438\\u0447\\u0435\\u043d \\u043f\\u043e\\u0434\\u0440\\u043e\\u0431\\u0435\\u043d \\u0444\\u0430\\u0439\\u043b reports/v45_backtest_results.csv."))
        return

    st.subheader(T("\\u041f\\u043e\\u0434\\u0440\\u043e\\u0431\\u043d\\u0438 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0440\\u0435\\u0437\\u0443\\u043b\\u0442\\u0430\\u0442\\u0438"))
    st.caption(T("\\u0422\\u043e\\u0432\\u0430 \\u0435 \\u043f\\u043e-\\u043d\\u0438\\u0441\\u043a\\u043e \\u043d\\u0438\\u0432\\u043e \\u043d\\u0430 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430\\u0442\\u0430 - \\u043f\\u043e\\u043b\\u0435\\u0437\\u043d\\u043e \\u0437\\u0430 \\u043e\\u0434\\u0438\\u0442 \\u0438 \\u0431\\u044a\\u0434\\u0435\\u0449\\u0438 \\u043f\\u043e\\u0434\\u043e\\u0431\\u0440\\u0435\\u043d\\u0438\\u044f."))

    shown = df.copy()
    if "model" in shown.columns:
        shown["model"] = shown["model"].map(_model_label)

    max_rows = st.slider(T("\\u0411\\u0440\\u043e\\u0439 \\u0440\\u0435\\u0434\\u043e\\u0432\\u0435 \\u0437\\u0430 \\u043f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430\\u043d\\u0435"), min_value=20, max_value=500, value=100, step=20)
    display_df = _prepare_backtest_table_for_display(shown.head(max_rows))
    st.dataframe(display_df, hide_index=True, width="stretch")


def render() -> None:
    st.title(T("\\u0426\\u0435\\u043d\\u0442\\u044a\\u0440 \\u0437\\u0430 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430"))

    st.caption(T("\\u0422\\u0430\\u0437\\u0438 \\u0441\\u0442\\u0440\\u0430\\u043d\\u0438\\u0446\\u0430 \\u043f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430 \\u043a\\u0430\\u043a \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438\\u0442\\u0435 \\u0441\\u0430 \\u0441\\u0435 \\u0434\\u044a\\u0440\\u0436\\u0430\\u043b\\u0438 \\u0432\\u044a\\u0440\\u0445\\u0443 \\u043c\\u0438\\u043d\\u0430\\u043b\\u0438 \\u0442\\u0438\\u0440\\u0430\\u0436\\u0438. \\u0426\\u0435\\u043b\\u0442\\u0430 \\u0435 \\u0447\\u0435\\u0441\\u0442\\u043d\\u0430 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430, \\u0441\\u0440\\u0430\\u0432\\u043d\\u0435\\u043d\\u0438\\u0435 \\u0438 \\u043a\\u043e\\u043d\\u0442\\u0440\\u043e\\u043b \\u0441\\u0440\\u0435\\u0449\\u0443 \\u0441\\u043b\\u0443\\u0447\\u0430\\u0439\\u043d\\u0438 \\u0431\\u0430\\u0437\\u043e\\u0432\\u0438 \\u043f\\u043e\\u0434\\u0445\\u043e\\u0434\\u0438."))

    st.warning(T("\\u0412\\u0430\\u0436\\u043d\\u043e: \\u0434\\u043e\\u0431\\u044a\\u0440 backtest \\u043d\\u0435 \\u043e\\u0437\\u043d\\u0430\\u0447\\u0430\\u0432\\u0430 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f \\u0437\\u0430 \\u0431\\u044a\\u0434\\u0435\\u0449\\u0430 \\u043f\\u0435\\u0447\\u0430\\u043b\\u0431\\u0430. \\u041b\\u043e\\u0442\\u0430\\u0440\\u0438\\u0439\\u043d\\u0438\\u0442\\u0435 \\u0442\\u0435\\u0433\\u043b\\u0435\\u043d\\u0438\\u044f \\u0441\\u0430 \\u0441\\u043b\\u0443\\u0447\\u0430\\u0439\\u043d\\u0438, \\u0430 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430\\u0442\\u0430 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430 \\u0435 \\u0438\\u043d\\u0441\\u0442\\u0440\\u0443\\u043c\\u0435\\u043d\\u0442 \\u0437\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430, \\u043d\\u0435 \\u043e\\u0431\\u0435\\u0449\\u0430\\u043d\\u0438\\u0435."))

    by_model = _read_csv(BACKTEST_BY_MODEL_PATH)
    raw_results = _read_csv(BACKTEST_RESULTS_PATH)

    tabs = st.tabs([
        T("\\u041e\\u0431\\u043e\\u0431\\u0449\\u0435\\u043d\\u0438\\u0435"),
        T("\\u0420\\u0430\\u0437\\u043f\\u0440\\u0435\\u0434\\u0435\\u043b\\u0435\\u043d\\u0438\\u0435"),
        T("\\u041f\\u043e\\u0434\\u0440\\u043e\\u0431\\u043d\\u0438 \\u0440\\u0435\\u0437\\u0443\\u043b\\u0442\\u0430\\u0442\\u0438"),
        T("\\u041a\\u0430\\u043a \\u0441\\u0435 \\u0447\\u0435\\u0442\\u0435"),
    ])

    with tabs[0]:
        st.subheader(T("\\u0421\\u0440\\u0430\\u0432\\u043d\\u0435\\u043d\\u0438\\u0435 \\u043d\\u0430 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0438\\u0442\\u0435"))
        _show_model_cards(by_model)

    with tabs[1]:
        _show_distribution(by_model)

    with tabs[2]:
        _show_raw_results(raw_results)

    with tabs[3]:
        st.subheader(T("\\u041a\\u0430\\u043a \\u0434\\u0430 \\u0447\\u0435\\u0442\\u0435\\u043c \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0430\\u0442\\u0430 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430"))

        st.markdown(T("""
- **\\u0421\\u0440\\u0435\\u0434\\u043d\\u043e \\u0443\\u0446\\u0435\\u043b\\u0435\\u043d\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430** \\u043f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430 \\u0441\\u0440\\u0435\\u0434\\u043d\\u0438\\u044f \\u0440\\u0435\\u0437\\u0443\\u043b\\u0442\\u0430\\u0442 \\u043d\\u0430 \\u043c\\u043e\\u0434\\u0435\\u043b\\u0430 \\u0432\\u044a\\u0440\\u0445\\u0443 \\u043c\\u0438\\u043d\\u0430\\u043b\\u0438 \\u0442\\u0438\\u0440\\u0430\\u0436\\u0438.
- **\\u041c\\u0430\\u043a\\u0441\\u0438\\u043c\\u0443\\u043c \\u0443\\u0446\\u0435\\u043b\\u0435\\u043d\\u0438** \\u043f\\u043e\\u043a\\u0430\\u0437\\u0432\\u0430 \\u043d\\u0430\\u0439-\\u0434\\u043e\\u0431\\u0440\\u0438\\u044f \\u0435\\u0434\\u0438\\u043d\\u0438\\u0447\\u0435\\u043d \\u0440\\u0435\\u0437\\u0443\\u043b\\u0442\\u0430\\u0442.
- **\\u0421\\u043b\\u0443\\u0447\\u0430\\u0435\\u043d \\u0431\\u0430\\u0437\\u043e\\u0432 \\u043c\\u043e\\u0434\\u0435\\u043b** \\u0435 \\u043a\\u043e\\u043d\\u0442\\u0440\\u043e\\u043b\\u043d\\u0430 \\u043b\\u0438\\u043d\\u0438\\u044f. \\u0410\\u043a\\u043e \\u0434\\u0430\\u0434\\u0435\\u043d \\u043c\\u043e\\u0434\\u0435\\u043b \\u043d\\u0435 \\u0435 \\u043f\\u043e-\\u0434\\u043e\\u0431\\u044a\\u0440 \\u043e\\u0442 \\u0441\\u043b\\u0443\\u0447\\u0430\\u0439\\u043d\\u0438\\u044f \\u043f\\u043e\\u0434\\u0445\\u043e\\u0434, \\u0442\\u043e\\u0439 \\u043d\\u044f\\u043c\\u0430 \\u0440\\u0435\\u0430\\u043b\\u043d\\u0430 \\u0430\\u043d\\u0430\\u043b\\u0438\\u0442\\u0438\\u0447\\u043d\\u0430 \\u0441\\u0442\\u043e\\u0439\\u043d\\u043e\\u0441\\u0442.
- **Backtest** \\u043f\\u0430\\u0437\\u0438 \\u043f\\u0440\\u043e\\u0435\\u043a\\u0442\\u0430 \\u043e\\u0442 \\u0441\\u0430\\u043c\\u043e\\u0437\\u0430\\u0431\\u043b\\u0443\\u0434\\u0430: \\u043d\\u0435 \\u0432\\u044f\\u0440\\u0432\\u0430\\u043c\\u0435 \\u043d\\u0430 \\u043a\\u0440\\u0430\\u0441\\u0438\\u0432\\u0438 \\u0447\\u0438\\u0441\\u043b\\u0430 \\u0431\\u0435\\u0437 \\u043f\\u0440\\u043e\\u0432\\u0435\\u0440\\u043a\\u0430.
"""))

        st.success(T("\\u041d\\u0430\\u0439-\\u0432\\u0430\\u0436\\u043d\\u043e\\u0442\\u043e \\u043f\\u0440\\u0430\\u0432\\u0438\\u043b\\u043e: \\u043c\\u043e\\u0434\\u0435\\u043b\\u044a\\u0442 \\u0442\\u0440\\u044f\\u0431\\u0432\\u0430 \\u0434\\u0430 \\u0431\\u044a\\u0434\\u0435 \\u0441\\u0440\\u0430\\u0432\\u043d\\u044f\\u0432\\u0430\\u043d \\u0441 \\u0431\\u0430\\u0437\\u043e\\u0432\\u0438 \\u043f\\u043e\\u0434\\u0445\\u043e\\u0434\\u0438 \\u0438 \\u0434\\u0430 \\u0431\\u044a\\u0434\\u0435 \\u043e\\u0431\\u044f\\u0441\\u043d\\u0438\\u043c. \\u0422\\u043e\\u0432\\u0430 \\u043f\\u0440\\u0430\\u0432\\u0438 app-\\u0430 \\u0441\\u0442\\u0430\\u0442\\u0438\\u0441\\u0442\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0438\\u043d\\u0441\\u0442\\u0440\\u0443\\u043c\\u0435\\u043d\\u0442, \\u043d\\u0435 \\u0433\\u0435\\u043d\\u0435\\u0440\\u0430\\u0442\\u043e\\u0440 \\u043d\\u0430 \\u043e\\u0431\\u0435\\u0449\\u0430\\u043d\\u0438\\u044f."))

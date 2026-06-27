from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


DATA_PATHS = [
    Path("data/historical_draws.csv"),
    Path("data/v41_canonical_draw_events.csv"),
    Path("data/v40_normalized_draw_events.csv"),
]


def _load_draw_history() -> tuple[pd.DataFrame, str]:
    for path in DATA_PATHS:
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        if df.empty:
            continue
        return _normalize_draw_history(df), str(path)
    return pd.DataFrame(), ""


def _first_existing(df: pd.DataFrame, names: list[str]) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    return None


def _normalize_draw_history(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    year_col = _first_existing(out, ["year", "draw_year"])
    draw_col = _first_existing(out, ["draw_number", "draw_no", "tirazh", "draw"])
    pos_col = _first_existing(out, ["draw_position", "drawing_position", "position"])
    date_col = _first_existing(out, ["date", "draw_date"])

    out["_year"] = pd.to_numeric(out[year_col], errors="coerce") if year_col else pd.NA
    out["_draw_number"] = pd.to_numeric(out[draw_col], errors="coerce") if draw_col else pd.NA
    out["_draw_position"] = pd.to_numeric(out[pos_col], errors="coerce").fillna(1).astype(int) if pos_col else 1
    out["_date"] = out[date_col].fillna("").astype(str) if date_col else ""

    number_cols = []
    for name in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        if name in out.columns:
            out[name] = pd.to_numeric(out[name], errors="coerce")
            number_cols.append(name)

    if len(number_cols) == 6:
        def combo(row: pd.Series) -> str:
            nums = []
            for col in number_cols:
                val = row.get(col)
                if pd.isna(val):
                    return ""
                nums.append(str(int(val)))
            return " - ".join(nums)
        out["_combination"] = out.apply(combo, axis=1)
    elif "numbers_text" in out.columns:
        out["_combination"] = out["numbers_text"].fillna("").astype(str)
    else:
        out["_combination"] = ""

    out = out.dropna(subset=["_year", "_draw_number"])
    if not out.empty:
        out["_year"] = out["_year"].astype(int)
        out["_draw_number"] = out["_draw_number"].astype(int)
        out = out.sort_values(["_year", "_draw_number", "_draw_position"], kind="stable")
    return out


def _display_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Дата", "Година", "Тираж №", "Теглене", "Комбинация"])
    return pd.DataFrame({
        "Дата": df["_date"].replace("nan", "").replace("NaN", ""),
        "Година": df["_year"].astype(int),
        "Тираж №": df["_draw_number"].astype(int),
        "Теглене": df["_draw_position"].astype(int),
        "Комбинация": df["_combination"],
    })


def _frequency_table(df: pd.DataFrame) -> pd.DataFrame:
    counts = {n: 0 for n in range(1, 50)}
    if not df.empty:
        for col in ["n1", "n2", "n3", "n4", "n5", "n6"]:
            if col not in df.columns:
                continue
            vals = pd.to_numeric(df[col], errors="coerce").dropna().astype(int)
            for value in vals:
                if 1 <= value <= 49:
                    counts[int(value)] += 1
    table = pd.DataFrame({"Число": list(counts.keys()), "Появи": list(counts.values())})
    return table.sort_values(["Появи", "Число"], ascending=[False, True], kind="stable")


def _year_coverage(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Година", "Брой тиражи", "От тираж", "До тираж"])
    grouped = df.groupby("_year", dropna=True).agg(
        draws=("_draw_number", "count"),
        first_draw=("_draw_number", "min"),
        last_draw=("_draw_number", "max"),
    ).reset_index()
    grouped = grouped.sort_values("_year", ascending=False)
    return grouped.rename(columns={
        "_year": "Година",
        "draws": "Брой тиражи",
        "first_draw": "От тираж",
        "last_draw": "До тираж",
    })


def render_full_historical_draws_section() -> None:
    st.title("Историческа статистика на изтеглените числа")
    st.caption("Тук се показва пълната локална история на изтеглените комбинации, а не само последните тиражи.")

    df, source = _load_draw_history()
    if df.empty:
        st.warning("Няма налична локална история на изтеглените числа.")
        return

    years = sorted([int(y) for y in df["_year"].dropna().unique()])
    first_year = min(years) if years else "—"
    last_year = max(years) if years else "—"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Всички тиражи в историята", f"{len(df):,}".replace(",", " "))
    c2.metric("Първа година", first_year)
    c3.metric("Последна година", last_year)
    c4.metric("Източник", source or "локален файл")

    st.info(
        "Историята на числата е отделна от историята на печалбите. "
        "Тук виждаш всички изтеглени комбинации, докато страницата „Проверена история 2026“ съдържа печалбите по категории."
    )

    year_options: list[Any] = ["Всички години"] + sorted(years, reverse=True)
    selected_year = st.selectbox("Избери година", year_options, index=0)
    filtered = df.copy()
    if selected_year != "Всички години":
        filtered = filtered[filtered["_year"] == int(selected_year)]

    if filtered.empty:
        st.warning("Няма тиражи за избрания филтър.")
        return

    min_draw = int(filtered["_draw_number"].min())
    max_draw = int(filtered["_draw_number"].max())
    fc1, fc2, fc3 = st.columns(3)
    from_draw = fc1.number_input("От тираж", min_value=min_draw, max_value=max_draw, value=min_draw, step=1)
    to_draw = fc2.number_input("До тираж", min_value=min_draw, max_value=max_draw, value=max_draw, step=1)
    show_mode = fc3.selectbox("Показване", ["Последните 50", "Първите 50", "Всички за филтъра"])

    filtered = filtered[(filtered["_draw_number"] >= int(from_draw)) & (filtered["_draw_number"] <= int(to_draw))]
    filtered = filtered.sort_values(["_year", "_draw_number", "_draw_position"], ascending=[False, False, True], kind="stable")

    st.subheader("Покритие на избрания филтър")
    k1, k2, k3 = st.columns(3)
    k1.metric("Тиражи в избора", f"{len(filtered):,}".replace(",", " "))
    k2.metric("От тираж", int(filtered["_draw_number"].min()) if not filtered.empty else "—")
    k3.metric("До тираж", int(filtered["_draw_number"].max()) if not filtered.empty else "—")

    tab_draws, tab_freq, tab_years = st.tabs(["Тиражи", "Честота на числата", "Покритие по години"])

    with tab_draws:
        if show_mode == "Последните 50":
            view = filtered.head(50)
        elif show_mode == "Първите 50":
            view = filtered.sort_values(["_year", "_draw_number", "_draw_position"], ascending=[True, True, True], kind="stable").head(50)
        else:
            view = filtered
        st.dataframe(_display_df(view), hide_index=True, use_container_width=True)
        csv_data = _display_df(filtered).to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Свали избраната история като CSV",
            data=csv_data,
            file_name="historical_draws_selected.csv",
            mime="text/csv",
        )

    with tab_freq:
        freq = _frequency_table(filtered)
        st.dataframe(freq, hide_index=True, use_container_width=True)
        top = freq.head(10)
        if not top.empty:
            st.caption("Най-често срещани числа в избрания диапазон")
            st.bar_chart(top.set_index("Число"))

    with tab_years:
        st.dataframe(_year_coverage(df), hide_index=True, use_container_width=True)

    st.info("Тази страница показва история и честоти. Тя не предсказва бъдещ тираж и не гарантира печалба.")

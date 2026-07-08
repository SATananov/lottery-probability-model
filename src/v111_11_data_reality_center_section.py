from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

DRAW_PATHS = [
    Path("data/historical_draws.csv"),
    Path("data/v41_canonical_draw_events.csv"),
    Path("data/v40_normalized_draw_events.csv"),
]
PRIZE_PATHS = [
    Path("data/prize_winner_history.csv"),
    Path("data/user_journal_exports/prize_winner_history.csv"),
]
DB_PATH = Path("data/user_journal.db")


def _first_existing(df: pd.DataFrame, names: list[str]) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    return None


def _num(value: Any, default: int | None = None) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def _format_money(value: Any) -> str:
    try:
        if value is None or str(value).strip() == "" or pd.isna(value):
            return "—"
        return f"{float(value):,.2f}".replace(",", " ") + " EUR"
    except Exception:
        return "—"


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()


def _normalize_draw_history(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = df.copy()
    year_col = _first_existing(out, ["year", "draw_year"])
    draw_col = _first_existing(out, ["draw_number", "draw_no", "draw", "tirazh"])
    pos_col = _first_existing(out, ["draw_position", "drawing_position", "position"])
    date_col = _first_existing(out, ["date", "draw_date"])

    out["_year"] = pd.to_numeric(out[year_col], errors="coerce") if year_col else pd.NA
    out["_draw_number"] = pd.to_numeric(out[draw_col], errors="coerce") if draw_col else pd.NA
    out["_draw_position"] = pd.to_numeric(out[pos_col], errors="coerce").fillna(1).astype(int) if pos_col else 1
    out["_date"] = out[date_col].fillna("").astype(str) if date_col else ""

    number_cols = [c for c in ["n1", "n2", "n3", "n4", "n5", "n6"] if c in out.columns]
    for col in number_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    def combo(row: pd.Series) -> str:
        values: list[str] = []
        if len(number_cols) == 6:
            for col in number_cols:
                val = row.get(col)
                if pd.isna(val):
                    return ""
                values.append(str(int(val)))
            return " - ".join(values)
        for col in ["numbers_text", "numbers", "combination"]:
            if col in out.columns and str(row.get(col, "")).strip():
                return str(row.get(col, "")).strip()
        return ""

    out["_combination"] = out.apply(combo, axis=1)
    out = out.dropna(subset=["_year", "_draw_number"])
    if out.empty:
        return pd.DataFrame()
    out["_year"] = out["_year"].astype(int)
    out["_draw_number"] = out["_draw_number"].astype(int)
    out["_draw_key"] = out["_year"].astype(str) + "-" + out["_draw_number"].astype(str)
    return out.sort_values(["_year", "_draw_number", "_draw_position"], kind="stable")


def _load_draws() -> tuple[pd.DataFrame, str]:
    for path in DRAW_PATHS:
        df = _safe_read_csv(path)
        normalized = _normalize_draw_history(df)
        if not normalized.empty:
            return normalized, str(path)
    return pd.DataFrame(), ""


def _normalize_prizes(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = df.copy()
    year_col = _first_existing(out, ["draw_year", "year"])
    draw_col = _first_existing(out, ["draw_number", "draw_no", "draw"])
    date_col = _first_existing(out, ["draw_date", "date"])
    out["_year"] = pd.to_numeric(out[year_col], errors="coerce") if year_col else pd.NA
    out["_draw_number"] = pd.to_numeric(out[draw_col], errors="coerce") if draw_col else pd.NA
    out["_date"] = out[date_col].fillna("").astype(str) if date_col else ""
    out = out.dropna(subset=["_year", "_draw_number"])
    if out.empty:
        return pd.DataFrame()
    out["_year"] = out["_year"].astype(int)
    out["_draw_number"] = out["_draw_number"].astype(int)
    out["_draw_key"] = out["_year"].astype(str) + "-" + out["_draw_number"].astype(str)
    note = out.get("note", pd.Series([""] * len(out))).fillna("").astype(str).str.lower()
    source = out.get("source_url", pd.Series([""] * len(out))).fillna("").astype(str).str.lower()
    out["_unofficial"] = note.str.contains("неофициален|virtbg", regex=True) | source.str.contains("virtbg", regex=False)
    out["_source_label"] = out["_unofficial"].map({True: "Неофициален / карантина", False: "БСТ / ръчно проверено"})
    for col in [
        "jackpot_eur", "winners_6", "winners_5", "winners_4", "winners_3",
        "prize_6_eur", "prize_5_eur", "prize_4_eur", "prize_3_eur",
        "total_6_eur", "total_5_eur", "total_4_eur", "total_3_eur",
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.sort_values(["_year", "_draw_number"], kind="stable")


def _load_prizes() -> tuple[pd.DataFrame, str]:
    for path in PRIZE_PATHS:
        df = _safe_read_csv(path)
        normalized = _normalize_prizes(df)
        if not normalized.empty:
            return normalized, str(path)
    return pd.DataFrame(), ""


def _read_sql_table(query: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn)
    except Exception:
        return pd.DataFrame()


def _ticket_summary() -> tuple[pd.DataFrame, int, int]:
    tickets = _read_sql_table(
        """
        SELECT target_draw_date, target_draw_number, COUNT(*) AS tickets,
               COALESCE(SUM(line_count), 0) AS lines,
               COALESCE(SUM(total_price_eur), 0) AS total_price_eur
        FROM played_tickets
        GROUP BY target_draw_date, target_draw_number
        """
    )
    results = _read_sql_table(
        """
        SELECT ude.draw_date, ude.draw_number, COUNT(ptr.id) AS evaluated_results
        FROM played_ticket_results ptr
        JOIN user_draw_entries ude ON ude.id = ptr.draw_entry_id
        GROUP BY ude.draw_date, ude.draw_number
        """
    )
    total_tickets = int(tickets["tickets"].sum()) if not tickets.empty and "tickets" in tickets.columns else 0
    total_results = int(results["evaluated_results"].sum()) if not results.empty and "evaluated_results" in results.columns else 0
    if tickets.empty:
        merged = pd.DataFrame(columns=["_date", "_draw_number", "tickets", "lines", "total_price_eur", "evaluated_results"])
    else:
        merged = tickets.copy()
        merged["_date"] = merged.get("target_draw_date", "").fillna("").astype(str)
        merged["_draw_number"] = pd.to_numeric(merged.get("target_draw_number", pd.NA), errors="coerce")
        if not results.empty:
            r = results.copy()
            r["_date"] = r.get("draw_date", "").fillna("").astype(str)
            r["_draw_number"] = pd.to_numeric(r.get("draw_number", pd.NA), errors="coerce")
            merged = merged.merge(r[["_date", "_draw_number", "evaluated_results"]], on=["_date", "_draw_number"], how="left")
        else:
            merged["evaluated_results"] = 0
        merged["evaluated_results"] = pd.to_numeric(merged["evaluated_results"], errors="coerce").fillna(0).astype(int)
    return merged, total_tickets, total_results


def _coverage_by_year(draws: pd.DataFrame, prizes: pd.DataFrame) -> pd.DataFrame:
    if draws.empty:
        return pd.DataFrame(columns=["Година", "Тиражи с числа", "Тиражи с печалби", "Покритие"])
    d = draws.groupby("_year").agg(draws=("_draw_key", "nunique")).reset_index()
    if prizes.empty:
        d["prizes"] = 0
    else:
        p = prizes[~prizes["_unofficial"]].groupby("_year").agg(prizes=("_draw_key", "nunique")).reset_index()
        d = d.merge(p, on="_year", how="left")
        d["prizes"] = pd.to_numeric(d["prizes"], errors="coerce").fillna(0).astype(int)
    d["coverage"] = (d["prizes"] / d["draws"].replace(0, pd.NA) * 100).fillna(0)
    d = d.sort_values("_year", ascending=False)
    return pd.DataFrame({
        "Година": d["_year"].astype(int),
        "Тиражи с числа": d["draws"].astype(int),
        "Тиражи с печалби": d["prizes"].astype(int),
        "Покритие": d["coverage"].map(lambda x: f"{x:.1f}%"),
    })


def _build_matrix(draws: pd.DataFrame, prizes: pd.DataFrame, tickets_by_draw: pd.DataFrame) -> pd.DataFrame:
    if draws.empty:
        return pd.DataFrame()
    base = draws.copy()
    base = base.sort_values(["_year", "_draw_number", "_draw_position"], ascending=[False, False, True], kind="stable")

    prize_cols = ["_draw_key", "jackpot_eur", "winners_6", "winners_5", "winners_4", "winners_3", "_source_label"]
    if prizes.empty:
        base["_has_prize"] = False
    else:
        p = prizes[~prizes["_unofficial"]].drop_duplicates("_draw_key", keep="last")
        keep = [c for c in prize_cols if c in p.columns]
        base = base.merge(p[keep], on="_draw_key", how="left")
        base["_has_prize"] = base.get("winners_3", pd.Series([pd.NA] * len(base))).notna()

    if not tickets_by_draw.empty:
        t = tickets_by_draw.copy()
        # Date match is safest for played tickets, because target draw number can be empty.
        base = base.merge(t[["_date", "tickets", "lines", "total_price_eur", "evaluated_results"]], on="_date", how="left")
    for col in ["tickets", "lines", "total_price_eur", "evaluated_results"]:
        if col not in base.columns:
            base[col] = 0
        base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0)

    display = pd.DataFrame({
        "Дата": base["_date"],
        "Година": base["_year"].astype(int),
        "Тираж №": base["_draw_number"].astype(int),
        "Числа": base["_combination"],
        "История на числата": "Да",
        "Печалби от БСТ": base["_has_prize"].map({True: "Да", False: "Не"}),
        "6-ци": base.get("winners_6", pd.Series([pd.NA] * len(base))).map(lambda x: "—" if pd.isna(x) else str(int(x))),
        "5-ци": base.get("winners_5", pd.Series([pd.NA] * len(base))).map(lambda x: "—" if pd.isna(x) else str(int(x))),
        "Джакпот": base.get("jackpot_eur", pd.Series([pd.NA] * len(base))).map(_format_money),
        "Играни фишове": base["tickets"].astype(int),
        "Редове във фишове": base["lines"].astype(int),
        "Резултат на фишове": base["evaluated_results"].map(lambda x: "Проверен" if int(x) > 0 else "Няма/чака"),
    })
    return display


def render_v111_11_data_reality_center_section() -> None:
    st.title("Матрица на данните")
    st.caption("Една ясна картина: кои тиражи имат изтеглени числа, кои имат печалби от БСТ и къде имаме играни фишове.")

    draws, draw_source = _load_draws()
    prizes, prize_source = _load_prizes()
    tickets_by_draw, total_tickets, total_results = _ticket_summary()

    official_prizes = prizes[~prizes["_unofficial"]] if not prizes.empty and "_unofficial" in prizes.columns else prizes
    draw_rows = len(draws)
    prize_rows = len(official_prizes)
    years = sorted(draws["_year"].dropna().astype(int).unique().tolist()) if not draws.empty else []

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("История на числата", f"{draw_rows:,}".replace(",", " "))
    m2.metric("Печалби от БСТ", f"{prize_rows:,}".replace(",", " "))
    m3.metric("Играни фишове", total_tickets)
    m4.metric("Проверени резултати", total_results)

    st.info(
        "Историята на числата и историята на печалбите са различни слоеве. "
        "Пълната история на числата се използва за модели и проверки, а печалбите показват реалната стойност на категориите, когато имаме проверен БСТ запис."
    )

    if draws.empty:
        st.warning("Липсва локална история на изтеглените числа.")
        return

    year_options: list[Any] = ["Всички години"] + sorted(years, reverse=True)
    default_index = 1 if 2026 in years else 0
    c1, c2, c3 = st.columns(3)
    selected_year = c1.selectbox("Година", year_options, index=default_index)
    show_count = c2.selectbox("Показване", ["Последни 30", "Последни 50", "Последни 100", "Всички за избора"], index=1)
    only_with_prizes = c3.checkbox("Само тиражи с печалби от БСТ", value=False)

    matrix = _build_matrix(draws, official_prizes, tickets_by_draw)
    if matrix.empty:
        st.warning("Матрицата не може да бъде изградена в момента.")
        return
    if selected_year != "Всички години":
        matrix = matrix[matrix["Година"] == int(selected_year)]
    if only_with_prizes:
        matrix = matrix[matrix["Печалби от БСТ"] == "Да"]
    matrix = matrix.sort_values(["Година", "Тираж №"], ascending=[False, False], kind="stable")
    if show_count != "Всички за избора":
        limit = int(show_count.split()[1])
        matrix = matrix.head(limit)

    tab_matrix, tab_quality, tab_next = st.tabs(["Матрица", "Качество на данните", "Какво следва"])

    with tab_matrix:
        st.subheader("Реална картина по тиражи")
        st.dataframe(matrix, hide_index=True, width="stretch")
        csv_data = matrix.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Свали матрицата като CSV",
            data=csv_data,
            file_name="data_reality_matrix.csv",
            mime="text/csv",
        )

    with tab_quality:
        st.subheader("Покритие по години")
        st.dataframe(_coverage_by_year(draws, official_prizes), hide_index=True, width="stretch")
        st.markdown(
            """
**Как да го четеш:**

- **Тиражи с числа** — имаме изтеглената комбинация.
- **Тиражи с печалби** — имаме проверен запис от БСТ screenshots / ръчен официален импорт.
- Когато покритието на печалбите е малко, статистиката за джакпот и 6-ци е начална, не силен модел.
            """.strip()
        )
        st.caption(f"Източник на числата: {draw_source or 'локална история'}")
        st.caption(f"Източник на печалбите: {prize_source or 'няма активен файл'}")

    with tab_next:
        st.subheader("Следващото логично развитие")
        st.markdown(
            """
1. Да пазим числата и печалбите като отделни, ясни слоеве.
2. Да добавяме нови БСТ записи постепенно, без неофициални източници в активната история.
3. Да направим начална статистика на печалбите само върху проверените записи.
4. Да вържем дневника на фишовете с печалбите, за да показва реална стойност на попаденията.
            """.strip()
        )
        st.warning("Тази страница е контролен център. Тя не предсказва следващ тираж и не гарантира печалба.")

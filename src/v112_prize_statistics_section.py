from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

try:
    import streamlit as st
except Exception:  # pragma: no cover - report script can run without Streamlit UI installed
    st = None

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "prize_winner_history.csv"
REPORT_JSON = ROOT / "reports" / "v112_prize_statistics_report.json"
REPORT_MD = ROOT / "reports" / "v112_prize_statistics_report.md"
MODEL_JSON = ROOT / "models" / "v112" / "prize_statistics_model.json"

REQUIRED_COLUMNS = [
    "draw_key",
    "draw_year",
    "draw_number",
    "draw_date",
    "n1",
    "n2",
    "n3",
    "n4",
    "n5",
    "n6",
    "jackpot_eur",
    "winners_6",
    "winners_5",
    "winners_4",
    "winners_3",
]

DISPLAY_COLUMNS = {
    "draw_key": "Тираж",
    "draw_year": "Година",
    "draw_number": "№",
    "draw_date": "Дата",
    "numbers_text": "Числа",
    "jackpot_eur": "Джакпот EUR",
    "winners_6": "6 числа",
    "prize_6_eur": "Печалба 6 EUR",
    "total_6_eur": "Общо 6 EUR",
    "winners_5": "5 числа",
    "prize_5_eur": "Печалба 5 EUR",
    "total_5_eur": "Общо 5 EUR",
    "winners_4": "4 числа",
    "prize_4_eur": "Печалба 4 EUR",
    "total_4_eur": "Общо 4 EUR",
    "winners_3": "3 числа",
    "prize_3_eur": "Печалба 3 EUR",
    "total_3_eur": "Общо 3 EUR",
    "source_url": "Източник",
    "note": "Бележка",
}


def _safe_number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        if isinstance(value, str):
            cleaned = (
                value.replace("\u00a0", " ")
                .replace(" ", "")
                .replace(",", ".")
                .replace("euro", "")
                .replace("EUR", "")
                .strip()
            )
            if not cleaned or cleaned.lower() in {"nan", "none", "-"}:
                return default
            return float(cleaned)
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(_safe_number(value, default=float(default))))
    except Exception:
        return default


def _format_eur(value: Any) -> str:
    try:
        amount = _safe_number(value)
        return f"{amount:,.2f} EUR".replace(",", " ")
    except Exception:
        return "—"


def _format_int(value: Any) -> str:
    try:
        return f"{_safe_int(value):,}".replace(",", " ")
    except Exception:
        return "—"


def _valid_numbers(row: pd.Series) -> bool:
    nums = [_safe_int(row.get(f"n{i}"), 0) for i in range(1, 7)]
    return len(nums) == 6 and len(set(nums)) == 6 and all(1 <= n <= 49 for n in nums)


def _make_numbers_text(row: pd.Series) -> str:
    nums = [_safe_int(row.get(f"n{i}"), 0) for i in range(1, 7)]
    if len(nums) == 6 and all(n > 0 for n in nums):
        return ", ".join(str(n) for n in nums)
    text = str(row.get("numbers_text", "")).strip()
    return text if text else "—"


def load_prize_history() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    try:
        df = pd.read_csv(DATA_PATH)
    except Exception:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = 0 if col.startswith("winners_") or col.startswith("n") or col in {"draw_year", "draw_number", "jackpot_eur"} else ""
    for col in ["draw_year", "draw_number", "n1", "n2", "n3", "n4", "n5", "n6", "winners_6", "winners_5", "winners_4", "winners_3"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_int)
    money_cols = [c for c in df.columns if c.endswith("_eur") or c == "jackpot_eur"]
    for col in money_cols:
        df[col] = df[col].apply(_safe_number)
    if "numbers_text" not in df.columns:
        df["numbers_text"] = df.apply(_make_numbers_text, axis=1)
    else:
        df["numbers_text"] = df.apply(_make_numbers_text, axis=1)
    df["valid_numbers"] = df.apply(_valid_numbers, axis=1)
    df["draw_date_dt"] = pd.to_datetime(df.get("draw_date", ""), errors="coerce")
    df = df.sort_values(["draw_year", "draw_number", "draw_date_dt"], na_position="last").reset_index(drop=True)
    return df


def _source_kind(note: Any, source_url: Any) -> str:
    text = f"{note or ''} {source_url or ''}".lower()
    if "official_manual_screenshot" in text or "бст" in text or "официал" in text:
        return "БСТ / ръчно проверено"
    if "manual" in text or "ръчен" in text:
        return "Ръчен запис"
    if "virtbg" in text or "неофициал" in text:
        return "Неофициален архив"
    return "Неуточнен източник"


def _confidence_label(rows: int, valid_ratio: float, verified_like_ratio: float) -> Tuple[str, str]:
    if rows == 0:
        return "няма данни", "Няма импортната история на печалбите."
    if rows < 20:
        return "начална", "Има малко записи. Полезно е за преглед, но не за силни изводи."
    if rows < 100:
        if valid_ratio >= 0.95 and verified_like_ratio >= 0.8:
            return "ограничена, но проверена", "Данните са проверени, но периодът е кратък. Изводите са начални."
        return "ограничена", "Има данни, но част от източниците/числата трябва да се проверят."
    if rows < 500:
        return "средна", "Историята вече позволява по-смислени сравнения, но не е пълна."
    return "силна историческа база", "Има достатъчно записи за устойчиви исторически сравнения."


def build_prize_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    rows = int(len(df))
    if rows == 0:
        return {
            "status": "NO_PRIZE_HISTORY",
            "rows": 0,
            "blocking_failures": 0,
            "summary_bg": "Няма импортната история на печалбите.",
        }
    valid_rows = int(df["valid_numbers"].sum()) if "valid_numbers" in df.columns else 0
    source_series = df.apply(lambda r: _source_kind(r.get("note"), r.get("source_url")), axis=1)
    source_counts = source_series.value_counts().to_dict()
    verified_like = int(source_series.isin(["БСТ / ръчно проверено", "Ръчен запис"]).sum())
    years = [int(y) for y in sorted(df["draw_year"].dropna().unique().tolist())]
    draw_min = int(df["draw_number"].min()) if rows else None
    draw_max = int(df["draw_number"].max()) if rows else None
    six_df = df[df["winners_6"].apply(_safe_int) > 0].copy()
    six_count = int(len(six_df))
    last_six: Optional[Dict[str, Any]] = None
    current_gap = None
    if six_count:
        last = six_df.sort_values(["draw_year", "draw_number"]).iloc[-1]
        latest = df.sort_values(["draw_year", "draw_number"]).iloc[-1]
        last_six = {
            "draw_key": str(last.get("draw_key", "")),
            "draw_year": int(last.get("draw_year", 0)),
            "draw_number": int(last.get("draw_number", 0)),
            "draw_date": str(last.get("draw_date", "")),
            "numbers": _make_numbers_text(last),
            "winners_6": int(last.get("winners_6", 0)),
            "prize_6_eur": _safe_number(last.get("prize_6_eur", 0)),
            "jackpot_eur": _safe_number(last.get("jackpot_eur", 0)),
        }
        if int(latest.get("draw_year", 0)) == int(last.get("draw_year", 0)):
            current_gap = int(latest.get("draw_number", 0)) - int(last.get("draw_number", 0))
    avg = {
        "winners_5": round(float(df["winners_5"].mean()), 2),
        "winners_4": round(float(df["winners_4"].mean()), 2),
        "winners_3": round(float(df["winners_3"].mean()), 2),
        "jackpot_eur": round(float(df["jackpot_eur"].mean()), 2),
    }
    max_rows: Dict[str, Any] = {}
    for col in ["winners_5", "winners_4", "winners_3", "jackpot_eur"]:
        try:
            idx = df[col].astype(float).idxmax()
            row = df.loc[idx]
            max_rows[col] = {
                "draw_key": str(row.get("draw_key", "")),
                "draw_date": str(row.get("draw_date", "")),
                "value": _safe_number(row.get(col)),
                "numbers": _make_numbers_text(row),
            }
        except Exception:
            max_rows[col] = {}
    confidence, confidence_note = _confidence_label(
        rows,
        valid_rows / max(rows, 1),
        verified_like / max(rows, 1),
    )
    return {
        "status": "PRIZE_STATISTICS_READY",
        "blocking_failures": 0,
        "rows": rows,
        "valid_number_rows": valid_rows,
        "valid_number_ratio": round(valid_rows / max(rows, 1), 4),
        "verified_like_rows": verified_like,
        "years": years,
        "draw_number_min": draw_min,
        "draw_number_max": draw_max,
        "source_counts": source_counts,
        "six_winning_draws": six_count,
        "last_six": last_six,
        "current_gap_after_last_six": current_gap,
        "averages": avg,
        "maximums": max_rows,
        "confidence": confidence,
        "confidence_note_bg": confidence_note,
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


def write_statistics_reports() -> Dict[str, Any]:
    df = load_prize_history()
    stats = build_prize_statistics(df)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Step 112 — Начална статистика на печалбите",
        "",
        f"Статус: `{stats.get('status')}`",
        f"Записи: **{stats.get('rows', 0)}**",
        f"Проверени числа: **{stats.get('valid_number_rows', 0)}**",
        f"Ниво на данните: **{stats.get('confidence', '—')}**",
        "",
        stats.get("confidence_note_bg", ""),
        "",
        "Тази статистика описва наличната история на печалбите. Тя не е гаранция за следващ тираж.",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return stats


def _render_metric_card(label: str, value: str, help_text: str = "") -> None:
    st.metric(label, value, help=help_text if help_text else None)


def _display_df(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in DISPLAY_COLUMNS.keys() if c in df.columns]
    if not cols:
        return df
    shown = df[cols].copy()
    for c in ["jackpot_eur", "prize_6_eur", "total_6_eur", "prize_5_eur", "total_5_eur", "prize_4_eur", "total_4_eur", "prize_3_eur", "total_3_eur"]:
        if c in shown.columns:
            shown[c] = shown[c].apply(_format_eur)
    for c in ["winners_6", "winners_5", "winners_4", "winners_3"]:
        if c in shown.columns:
            shown[c] = shown[c].apply(_format_int)
    return shown.rename(columns=DISPLAY_COLUMNS)


def render_v112_prize_statistics_section() -> None:
    if st is None:
        raise RuntimeError("Streamlit не е наличен за визуалната страница.")
    st.title("Статистика на печалбите")
    st.caption("Начален анализ на наличните данни за печалби по категории. Това е исторически преглед, не прогноза за следващ тираж.")

    df = load_prize_history()
    stats = build_prize_statistics(df)

    if df.empty:
        st.warning("Още няма импортната история на печалбите. Първо добави проверени данни от БСТ или CSV импорт.")
        if st.button("Обнови отчета", width="stretch"):
            write_statistics_reports()
            st.success("Отчетът е обновен. Няма налични записи за анализ.")
        return

    with st.container(border=True):
        st.markdown("### Ниво на данните")
        st.info(stats.get("confidence_note_bg", ""))
        st.caption("Историята на изтеглените числа може да е пълна, но историята на печалбите е отделен слой. Тук анализираме само импортнатите печалби.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _render_metric_card("Записи с печалби", _format_int(stats.get("rows", 0)))
    with c2:
        _render_metric_card("Проверени числа", _format_int(stats.get("valid_number_rows", 0)))
    with c3:
        _render_metric_card("Тиражи със 6-ца", _format_int(stats.get("six_winning_draws", 0)))
    with c4:
        gap = stats.get("current_gap_after_last_six")
        _render_metric_card("Текущ период без 6-ца", "—" if gap is None else f"{gap} тиража")

    years = [int(y) for y in sorted(df["draw_year"].dropna().unique().tolist())]
    selected_years = st.multiselect("Години за преглед", years, default=years, help="Филтърът не променя данните, само показаната статистика.")
    view_df = df[df["draw_year"].isin(selected_years)].copy() if selected_years else df.copy()
    view_stats = build_prize_statistics(view_df)

    tab_summary, tab_six, tab_categories, tab_quality, tab_table = st.tabs([
        "Обобщение",
        "6 числа и джакпот",
        "5 / 4 / 3 числа",
        "Качество на данните",
        "Таблица",
    ])

    with tab_summary:
        st.markdown("### Обобщение за избрания период")
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            st.metric("Тиражи", _format_int(view_stats.get("rows", 0)))
        with a2:
            st.metric("Средно 5-ци", view_stats.get("averages", {}).get("winners_5", "—"))
        with a3:
            st.metric("Средно 4-ки", view_stats.get("averages", {}).get("winners_4", "—"))
        with a4:
            st.metric("Средно 3-ки", view_stats.get("averages", {}).get("winners_3", "—"))
        chart_cols = ["winners_5", "winners_4", "winners_3"]
        if len(view_df) >= 2 and all(c in view_df.columns for c in chart_cols):
            chart_df = view_df.set_index("draw_key")[chart_cols].rename(columns={
                "winners_5": "5 числа",
                "winners_4": "4 числа",
                "winners_3": "3 числа",
            })
            st.line_chart(chart_df)
        else:
            st.caption("Нужни са поне два тиража, за да се покаже графика.")

    with tab_six:
        st.markdown("### 6 числа и джакпот цикъл")
        last_six = view_stats.get("last_six")
        if last_six:
            st.success(
                f"Последна 6-ца в наличните данни: тираж {last_six.get('draw_number')} / {last_six.get('draw_year')} "
                f"на {last_six.get('draw_date')} — числа {last_six.get('numbers')}"
            )
            st.write(f"Печалба за 6 числа: **{_format_eur(last_six.get('prize_6_eur'))}**")
        else:
            st.warning("В избрания период няма записан тираж със спечелена 6-ца.")
        if len(view_df) >= 2 and "jackpot_eur" in view_df.columns:
            jackpot_chart = view_df.set_index("draw_key")[["jackpot_eur"]].rename(columns={"jackpot_eur": "Джакпот EUR"})
            st.line_chart(jackpot_chart)
        st.caption("Джакпот цикълът показва натрупване и рестарт след спечелена 6-ца. Това не гарантира кога ще има следваща 6-ца.")

    with tab_categories:
        st.markdown("### Активност по категории")
        maxes = view_stats.get("maximums", {})
        for col, title in [
            ("winners_5", "Най-много печалби с 5 числа"),
            ("winners_4", "Най-много печалби с 4 числа"),
            ("winners_3", "Най-много печалби с 3 числа"),
        ]:
            row = maxes.get(col, {})
            if row:
                st.write(f"**{title}:** {int(row.get('value', 0))} — {row.get('draw_key')} / {row.get('draw_date')} / числа {row.get('numbers')}")
        if len(view_df) >= 2:
            category_view = view_df[["draw_key", "winners_5", "winners_4", "winners_3"]].copy()
            category_view = category_view.rename(columns={
                "draw_key": "Тираж",
                "winners_5": "5 числа",
                "winners_4": "4 числа",
                "winners_3": "3 числа",
            })
            st.dataframe(category_view, width="stretch", hide_index=True)

    with tab_quality:
        st.markdown("### Качество и произход")
        source_counts = view_df.apply(lambda r: _source_kind(r.get("note"), r.get("source_url")), axis=1).value_counts().reset_index()
        source_counts.columns = ["Източник", "Записи"]
        st.dataframe(source_counts, width="stretch", hide_index=True)
        invalid = view_df[~view_df["valid_numbers"]].copy() if "valid_numbers" in view_df.columns else pd.DataFrame()
        if invalid.empty:
            st.success("Всички показани записи имат 6 различни числа от 1 до 49.")
        else:
            st.warning(f"Има {len(invalid)} записа със съмнителни числа. Те не трябва да се използват за силен анализ.")
            st.dataframe(_display_df(invalid), width="stretch", hide_index=True)
        st.caption("Проверените БСТ screenshots са най-надеждният слой. Неофициални или стари редове трябва да стоят отделно/карантинирани.")

    with tab_table:
        st.markdown("### Данни за избрания период")
        st.dataframe(_display_df(view_df), width="stretch", hide_index=True)
        csv_bytes = view_df.drop(columns=["draw_date_dt"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Свали избраните записи като CSV",
            data=csv_bytes,
            file_name="selected_prize_winner_history.csv",
            mime="text/csv",
            width="stretch",
        )

    if st.button("Обнови локалния отчет", width="stretch"):
        new_stats = write_statistics_reports()
        st.success(f"Отчетът е обновен. Записи: {new_stats.get('rows', 0)}. Статус: {new_stats.get('status')}.")

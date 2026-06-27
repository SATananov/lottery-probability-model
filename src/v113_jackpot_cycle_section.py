from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "prize_winner_history.csv"
REPORT_JSON = ROOT / "reports" / "v113_jackpot_cycle_report.json"
REPORT_MD = ROOT / "reports" / "v113_jackpot_cycle_report.md"
MODEL_JSON = ROOT / "models" / "v113" / "jackpot_cycle_model.json"

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
    "numbers_text",
    "jackpot_eur",
    "winners_6",
    "prize_6_eur",
    "total_6_eur",
    "winners_5",
    "winners_4",
    "winners_3",
    "source_url",
    "note",
]

DISPLAY_COLUMNS = {
    "draw_key": "Тираж",
    "draw_date": "Дата",
    "numbers_text": "Числа",
    "jackpot_eur": "Джакпот",
    "jackpot_change_eur": "Промяна",
    "winners_6": "6 числа",
    "winners_5": "5 числа",
    "winners_4": "4 числа",
    "winners_3": "3 числа",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, str):
            text = (
                value.replace("\u00a0", " ")
                .replace("euro", "")
                .replace("EUR", "")
                .replace("€", "")
                .strip()
            )
            text = text.replace(" ", "").replace(",", ".")
            keep = "".join(ch for ch in text if ch.isdigit() or ch in ".-")
            if keep in {"", ".", "-"}:
                return default
            return float(keep)
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(_safe_float(value, float(default))))
    except Exception:
        return default


def _format_eur(value: Any) -> str:
    amount = _safe_float(value)
    return f"{amount:,.2f} EUR".replace(",", " ")


def _format_change(value: Any) -> str:
    amount = _safe_float(value)
    if abs(amount) < 0.005:
        return "—"
    prefix = "+" if amount > 0 else ""
    return f"{prefix}{amount:,.2f} EUR".replace(",", " ")


def _format_int(value: Any) -> str:
    return f"{_safe_int(value):,}".replace(",", " ")


def _numbers_valid(row: pd.Series) -> bool:
    nums = [_safe_int(row.get(f"n{i}"), 0) for i in range(1, 7)]
    return len(nums) == 6 and len(set(nums)) == 6 and all(1 <= n <= 49 for n in nums)


def _numbers_text(row: pd.Series) -> str:
    nums = [_safe_int(row.get(f"n{i}"), 0) for i in range(1, 7)]
    if len(nums) == 6 and all(1 <= n <= 49 for n in nums):
        return ", ".join(str(n) for n in nums)
    return str(row.get("numbers_text", "—") or "—")


def _source_label(row: pd.Series) -> str:
    text = f"{row.get('source_url', '')} {row.get('note', '')}".lower()
    if "official_manual_screenshot" in text or "бст" in text or "официал" in text:
        return "БСТ / ръчно проверено"
    if "manual" in text or "ръчен" in text:
        return "Ръчен запис"
    return "Друг източник"


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
    money_cols = [col for col in df.columns if col.endswith("_eur") or col == "jackpot_eur"]
    for col in money_cols:
        df[col] = df[col].apply(_safe_float)
    df["valid_numbers"] = df.apply(_numbers_valid, axis=1)
    df["numbers_text"] = df.apply(_numbers_text, axis=1)
    df["source_label"] = df.apply(_source_label, axis=1)
    df["draw_date_dt"] = pd.to_datetime(df.get("draw_date", ""), errors="coerce")
    df = df.sort_values(["draw_year", "draw_number", "draw_date_dt"], na_position="last").reset_index(drop=True)
    return df


def _confidence_note(row_count: int, official_count: int) -> str:
    if row_count == 0:
        return "Няма налична история на печалбите."
    if row_count < 20:
        return "Има малко записи. Използвай анализа само като ориентир."
    if row_count < 100:
        if official_count == row_count:
            return "Данните са проверени, но периодът е още кратък. Анализът е начален."
        return "Има ограничен период и смесени източници. Не прави силни изводи."
    return "Има по-широка история, но анализът пак не е гаранция за следващ тираж."


def _cycle_label(gap: Optional[int]) -> str:
    if gap is None:
        return "няма данни"
    if gap < 5:
        return "ранен цикъл"
    if gap <= 15:
        return "натрупващ се цикъл"
    return "дълъг цикъл в наличната история"


def _recommendation(gap: Optional[int], growth: float, row_count: int) -> str:
    if row_count < 20:
        return "Данните са малко. Не увеличавай фишовете само на база този анализ."
    if gap is None:
        return "Няма записана 6-ца в наличната история. Използвай само стандартен пакет."
    if gap <= 5:
        return "Цикълът е ранен. Подходящо е да се остане на основен пакет."
    if gap <= 15:
        return "Има натрупване след последната 6-ца. Разширен пакет може да се разглежда, но само в предварително избран бюджет."
    if growth > 0:
        return "Периодът без 6-ца е по-дълъг за наличните данни и джакпотът расте. Разширен пакет е допустим само като контролиран риск."
    return "Периодът е дълъг, но няма ясно натрупване. Не увеличавай агресивно фишовете."


def build_jackpot_cycle(df: pd.DataFrame) -> Dict[str, Any]:
    rows = int(len(df))
    if rows == 0:
        return {
            "status": "NO_PRIZE_HISTORY",
            "blocking_failures": 0,
            "rows": 0,
            "summary_bg": "Няма налична история на печалбите за анализ на джакпот цикъл.",
        }

    valid_df = df[df["valid_numbers"]].copy() if "valid_numbers" in df.columns else df.copy()
    official_df = valid_df[valid_df["source_label"].isin(["БСТ / ръчно проверено", "Ръчен запис"])].copy()
    analysis_df = official_df if len(official_df) else valid_df
    analysis_df = analysis_df.sort_values(["draw_year", "draw_number"]).reset_index(drop=True)

    six_df = analysis_df[analysis_df["winners_6"].apply(_safe_int) > 0].copy()
    latest = analysis_df.iloc[-1]
    first = analysis_df.iloc[0]
    last_six: Optional[pd.Series] = None
    last_six_pos = None
    if not six_df.empty:
        last_six = six_df.iloc[-1]
        matches = analysis_df.index[
            (analysis_df["draw_year"] == int(last_six.get("draw_year", 0)))
            & (analysis_df["draw_number"] == int(last_six.get("draw_number", 0)))
        ].tolist()
        last_six_pos = int(matches[-1]) if matches else None

    cycle_df = pd.DataFrame()
    restart_draw: Optional[pd.Series] = None
    gap_after_six: Optional[int] = None
    restart_jackpot = 0.0
    latest_jackpot = _safe_float(latest.get("jackpot_eur"), 0.0)
    growth = 0.0
    avg_growth_per_draw = 0.0

    if last_six is not None and last_six_pos is not None:
        cycle_df = analysis_df.iloc[last_six_pos + 1 :].copy()
        gap_after_six = int(latest.get("draw_number", 0)) - int(last_six.get("draw_number", 0)) if int(latest.get("draw_year", 0)) == int(last_six.get("draw_year", 0)) else int(len(cycle_df))
        if not cycle_df.empty:
            restart_draw = cycle_df.iloc[0]
            restart_jackpot = _safe_float(restart_draw.get("jackpot_eur"), 0.0)
            growth = latest_jackpot - restart_jackpot
            steps = max(int(len(cycle_df)) - 1, 1)
            avg_growth_per_draw = growth / steps if steps else 0.0
    else:
        cycle_df = analysis_df.copy()
        restart_draw = first
        restart_jackpot = _safe_float(first.get("jackpot_eur"), 0.0)
        growth = latest_jackpot - restart_jackpot
        avg_growth_per_draw = growth / max(len(cycle_df) - 1, 1)

    full_df = analysis_df.copy()
    full_df["jackpot_change_eur"] = full_df["jackpot_eur"].diff().fillna(0.0)
    if not cycle_df.empty:
        cycle_df = cycle_df.copy()
        cycle_df["jackpot_change_eur"] = cycle_df["jackpot_eur"].diff().fillna(0.0)

    max_jackpot_row = analysis_df.loc[analysis_df["jackpot_eur"].astype(float).idxmax()]
    min_jackpot_row = analysis_df.loc[analysis_df["jackpot_eur"].astype(float).idxmin()]
    six_events: List[Dict[str, Any]] = []
    for _, row in six_df.iterrows():
        six_events.append({
            "draw_key": str(row.get("draw_key", "")),
            "draw_year": int(row.get("draw_year", 0)),
            "draw_number": int(row.get("draw_number", 0)),
            "draw_date": str(row.get("draw_date", "")),
            "numbers": str(row.get("numbers_text", "")),
            "winners_6": int(row.get("winners_6", 0)),
            "prize_6_eur": _safe_float(row.get("prize_6_eur", 0.0)),
            "jackpot_eur": _safe_float(row.get("jackpot_eur", 0.0)),
        })

    summary = {
        "status": "JACKPOT_CYCLE_READY",
        "blocking_failures": 0,
        "rows": rows,
        "analysis_rows": int(len(analysis_df)),
        "official_or_manual_rows": int(len(official_df)),
        "years": [int(y) for y in sorted(analysis_df["draw_year"].dropna().unique().tolist())],
        "first_draw": {
            "draw_key": str(first.get("draw_key", "")),
            "draw_date": str(first.get("draw_date", "")),
            "jackpot_eur": _safe_float(first.get("jackpot_eur", 0.0)),
        },
        "latest_draw": {
            "draw_key": str(latest.get("draw_key", "")),
            "draw_year": int(latest.get("draw_year", 0)),
            "draw_number": int(latest.get("draw_number", 0)),
            "draw_date": str(latest.get("draw_date", "")),
            "numbers": str(latest.get("numbers_text", "")),
            "jackpot_eur": latest_jackpot,
        },
        "six_events": six_events,
        "six_event_count": int(len(six_events)),
        "last_six_draw": six_events[-1] if six_events else None,
        "gap_after_last_six": gap_after_six,
        "cycle_label_bg": _cycle_label(gap_after_six),
        "restart_draw": None if restart_draw is None else {
            "draw_key": str(restart_draw.get("draw_key", "")),
            "draw_date": str(restart_draw.get("draw_date", "")),
            "jackpot_eur": restart_jackpot,
        },
        "current_cycle_draws": int(len(cycle_df)),
        "jackpot_growth_eur": round(growth, 2),
        "avg_growth_per_draw_eur": round(avg_growth_per_draw, 2),
        "max_jackpot": {
            "draw_key": str(max_jackpot_row.get("draw_key", "")),
            "draw_date": str(max_jackpot_row.get("draw_date", "")),
            "jackpot_eur": _safe_float(max_jackpot_row.get("jackpot_eur", 0.0)),
        },
        "min_jackpot": {
            "draw_key": str(min_jackpot_row.get("draw_key", "")),
            "draw_date": str(min_jackpot_row.get("draw_date", "")),
            "jackpot_eur": _safe_float(min_jackpot_row.get("jackpot_eur", 0.0)),
        },
        "confidence_note_bg": _confidence_note(int(len(analysis_df)), int(len(official_df))),
        "ticket_pack_recommendation_bg": _recommendation(gap_after_six, growth, int(len(analysis_df))),
        "safe_note_bg": "Анализът описва историята на джакпота и наличните печалби. Той не предсказва следващия тираж и не гарантира печалба.",
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    return summary


def write_jackpot_cycle_reports() -> Dict[str, Any]:
    df = load_prize_history()
    stats = build_jackpot_cycle(df)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Step 113 — Джакпот цикъл",
        "",
        f"Статус: `{stats.get('status')}`",
        f"Записи в анализа: **{stats.get('analysis_rows', 0)}**",
        f"Тиражи със 6-ца: **{stats.get('six_event_count', 0)}**",
        f"Текущ период след последна 6-ца: **{stats.get('gap_after_last_six', '—')}**",
        f"Натрупване в текущия цикъл: **{_format_eur(stats.get('jackpot_growth_eur', 0))}**",
        "",
        stats.get("confidence_note_bg", ""),
        "",
        stats.get("safe_note_bg", ""),
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return stats


def _prepare_display(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cols = [col for col in DISPLAY_COLUMNS if col in df.columns]
    shown = df[cols].copy()
    if "jackpot_eur" in shown.columns:
        shown["jackpot_eur"] = shown["jackpot_eur"].apply(_format_eur)
    if "jackpot_change_eur" in shown.columns:
        shown["jackpot_change_eur"] = shown["jackpot_change_eur"].apply(_format_change)
    for col in ["winners_6", "winners_5", "winners_4", "winners_3"]:
        if col in shown.columns:
            shown[col] = shown[col].apply(_format_int)
    return shown.rename(columns=DISPLAY_COLUMNS)


def render_v113_jackpot_cycle_section() -> None:
    if st is None:
        raise RuntimeError("Streamlit не е наличен за визуалната страница.")

    st.title("Джакпот цикъл")
    st.caption("Проследява натрупването на джакпота след последната спечелена 6-ца. Това е исторически анализ, не прогноза.")

    df = load_prize_history()
    if df.empty:
        st.warning("Още няма активна история на печалбите. Първо добави проверени записи от БСТ.")
        if st.button("Обнови отчета", use_container_width=True):
            stats = write_jackpot_cycle_reports()
            st.success(f"Отчетът е обновен. Статус: {stats.get('status')}")
        return

    years = [int(y) for y in sorted(df["draw_year"].dropna().unique().tolist())]
    selected_years = st.multiselect("Години за анализ", years, default=years)
    view_df = df[df["draw_year"].isin(selected_years)].copy() if selected_years else df.copy()
    view_df = view_df[view_df["valid_numbers"]].copy() if "valid_numbers" in view_df.columns else view_df
    view_df = view_df.sort_values(["draw_year", "draw_number"]).reset_index(drop=True)
    stats = build_jackpot_cycle(view_df)

    with st.container(border=True):
        st.markdown("### Как да се чете този анализ")
        st.info(stats.get("confidence_note_bg", ""))
        st.caption(stats.get("safe_note_bg", ""))

    latest = stats.get("latest_draw") or {}
    last_six = stats.get("last_six_draw") or {}
    restart = stats.get("restart_draw") or {}

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Последна 6-ца", "—" if not last_six else f"{last_six.get('draw_number')} / {last_six.get('draw_year')}")
    with c2:
        gap = stats.get("gap_after_last_six")
        st.metric("Тиражи без 6-ца", "—" if gap is None else f"{gap}")
    with c3:
        st.metric("Текущ джакпот", _format_eur(latest.get("jackpot_eur", 0)))
    with c4:
        st.metric("Натрупване", _format_eur(stats.get("jackpot_growth_eur", 0)))

    tab_cycle, tab_six, tab_value, tab_table = st.tabs([
        "Текущ цикъл",
        "6-ци и рестарти",
        "Решение за фишове",
        "Данни",
    ])

    with tab_cycle:
        st.markdown("### Текущ джакпот цикъл")
        st.write(f"**Статус:** {stats.get('cycle_label_bg', '—')}")
        if last_six:
            st.write(
                f"Последната 6-ца в наличните данни е в тираж **{last_six.get('draw_number')} / {last_six.get('draw_year')}** "
                f"на **{last_six.get('draw_date')}** с числа **{last_six.get('numbers')}**."
            )
            st.write(f"Печалба за 6 числа: **{_format_eur(last_six.get('prize_6_eur', 0))}**")
        else:
            st.warning("В избрания период няма записана 6-ца. Цикълът се изчислява само като натрупване в наличните данни.")
        if restart:
            st.write(f"Първи тираж след рестарта: **{restart.get('draw_key')}** / {restart.get('draw_date')} — джакпот **{_format_eur(restart.get('jackpot_eur', 0))}**")
        st.write(f"Последен наличен тираж: **{latest.get('draw_key', '—')}** / {latest.get('draw_date', '—')} — джакпот **{_format_eur(latest.get('jackpot_eur', 0))}**")
        st.write(f"Средно нарастване в текущия цикъл: **{_format_eur(stats.get('avg_growth_per_draw_eur', 0))}** на тираж")

        chart_df = view_df.copy()
        if last_six:
            six_year = int(last_six.get("draw_year", 0))
            six_draw = int(last_six.get("draw_number", 0))
            chart_df = chart_df[(chart_df["draw_year"] > six_year) | ((chart_df["draw_year"] == six_year) & (chart_df["draw_number"] >= six_draw))]
        if len(chart_df) >= 2:
            st.line_chart(chart_df.set_index("draw_key")[["jackpot_eur"]].rename(columns={"jackpot_eur": "Джакпот EUR"}))
        else:
            st.caption("Нужни са поне два тиража, за да се покаже графика на цикъла.")

    with tab_six:
        st.markdown("### Тиражи със спечелена 6-ца")
        six_events = stats.get("six_events") or []
        if not six_events:
            st.warning("Няма записана 6-ца в избрания период.")
        else:
            six_df = pd.DataFrame(six_events)
            six_df = six_df.rename(columns={
                "draw_key": "Тираж",
                "draw_date": "Дата",
                "numbers": "Числа",
                "winners_6": "Брой 6-ци",
                "prize_6_eur": "Печалба 6 EUR",
                "jackpot_eur": "Джакпот EUR",
            })
            for col in ["Печалба 6 EUR", "Джакпот EUR"]:
                if col in six_df.columns:
                    six_df[col] = six_df[col].apply(_format_eur)
            st.dataframe(six_df, use_container_width=True, hide_index=True)
        st.caption("Един запис със 6-ца не е достатъчен за надежден интервален модел. Той е полезен за джакпот цикъл и контрол на бюджета.")

    with tab_value:
        st.markdown("### Какво означава това за фишовете")
        st.success(stats.get("ticket_pack_recommendation_bg", "—"))
        st.write("Практическо правило:")
        st.markdown(
            "- **Основен пакет** — когато цикълът е ранен или данните са малко.\n"
            "- **Разширен пакет** — само когато има натрупване и бюджетът е предварително ограничен.\n"
            "- **Без агресивно увеличаване** — джакпотът не променя математически шанса за конкретна комбинация."
        )
        max_j = stats.get("max_jackpot") or {}
        min_j = stats.get("min_jackpot") or {}
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Най-висок джакпот в данните", _format_eur(max_j.get("jackpot_eur", 0)))
            st.caption(f"{max_j.get('draw_key', '—')} / {max_j.get('draw_date', '—')}")
        with c2:
            st.metric("Най-нисък джакпот в данните", _format_eur(min_j.get("jackpot_eur", 0)))
            st.caption(f"{min_j.get('draw_key', '—')} / {min_j.get('draw_date', '—')}")

    with tab_table:
        st.markdown("### Данни за джакпот цикъла")
        table_df = view_df.copy()
        table_df["jackpot_change_eur"] = table_df["jackpot_eur"].diff().fillna(0.0)
        st.dataframe(_prepare_display(table_df), use_container_width=True, hide_index=True)
        csv_bytes = table_df.drop(columns=["draw_date_dt"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Свали данните за цикъла като CSV",
            data=csv_bytes,
            file_name="jackpot_cycle_data.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if st.button("Обнови локалния отчет", use_container_width=True):
        new_stats = write_jackpot_cycle_reports()
        st.success(f"Отчетът е обновен. Статус: {new_stats.get('status')}. Записи: {new_stats.get('analysis_rows', 0)}.")

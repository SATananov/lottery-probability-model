from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v115"
EXPORT_DIR = DATA_DIR / "user_journal_exports"
PRIZE_HISTORY_CSV = DATA_DIR / "prize_winner_history.csv"
HISTORICAL_DRAWS_CSV = DATA_DIR / "historical_draws.csv"
DB_PATH = DATA_DIR / "user_journal.db"
PLAYED_TICKETS_CSV = EXPORT_DIR / "played_tickets.csv"
REPORT_JSON = REPORTS_DIR / "v115_play_decision_center_report.json"
REPORT_MD = REPORTS_DIR / "v115_play_decision_center_report.md"
MODEL_JSON = MODELS_DIR / "play_decision_policy.json"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, str):
            text = value.replace("\u00a0", " ").replace("EUR", "").replace("euro", "").replace("€", "").strip()
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
    return f"{_safe_float(value):,.2f} EUR".replace(",", " ")


def _format_int(value: Any) -> str:
    return f"{_safe_int(value):,}".replace(",", " ")


def _format_date(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else "—"


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _numbers_valid(row: pd.Series) -> bool:
    values = [_safe_int(row.get(f"n{i}"), 0) for i in range(1, 7)]
    return len(values) == 6 and len(set(values)) == 6 and all(1 <= value <= 49 for value in values)


def load_prize_history() -> pd.DataFrame:
    df = _read_csv(PRIZE_HISTORY_CSV)
    if df.empty:
        return df
    for col in ["draw_year", "draw_number", "winners_6", "winners_5", "winners_4", "winners_3"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_int)
    for col in ["jackpot_eur", "prize_6_eur", "prize_5_eur", "prize_4_eur", "prize_3_eur", "total_6_eur", "total_5_eur", "total_4_eur", "total_3_eur"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)
    for i in range(1, 7):
        col = f"n{i}"
        if col in df.columns:
            df[col] = df[col].apply(_safe_int)
    if "draw_date" in df.columns:
        df["draw_date_dt"] = pd.to_datetime(df["draw_date"], errors="coerce")
    else:
        df["draw_date_dt"] = pd.NaT
    df["valid_numbers"] = df.apply(_numbers_valid, axis=1)
    df = df[df["valid_numbers"]].copy()
    if "note" in df.columns:
        note = df["note"].astype(str).str.lower()
        unofficial = note.str.contains("virtbg") | note.str.contains("неофициален")
        if unofficial.any():
            df = df[~unofficial].copy()
    if not df.empty:
        df = df.sort_values(["draw_date_dt", "draw_year", "draw_number"], na_position="last").reset_index(drop=True)
    return df


def load_historical_draws_summary() -> Dict[str, Any]:
    df = _read_csv(HISTORICAL_DRAWS_CSV)
    if df.empty:
        return {"rows": 0, "first_year": None, "last_year": None}
    year_col = None
    for candidate in ["year", "draw_year", "Year", "Година"]:
        if candidate in df.columns:
            year_col = candidate
            break
    if year_col:
        years = pd.to_numeric(df[year_col], errors="coerce").dropna().astype(int)
        return {"rows": len(df), "first_year": int(years.min()) if not years.empty else None, "last_year": int(years.max()) if not years.empty else None}
    date_col = "draw_date" if "draw_date" in df.columns else None
    if date_col:
        dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
        return {"rows": len(df), "first_year": int(dates.dt.year.min()) if not dates.empty else None, "last_year": int(dates.dt.year.max()) if not dates.empty else None}
    return {"rows": len(df), "first_year": None, "last_year": None}


def load_played_tickets() -> pd.DataFrame:
    if DB_PATH.exists():
        try:
            with sqlite3.connect(DB_PATH) as conn:
                df = pd.read_sql_query("SELECT * FROM played_tickets", conn)
            return df
        except Exception:
            pass
    return _read_csv(PLAYED_TICKETS_CSV)


def _coverage_label(rows: int) -> Tuple[str, str]:
    if rows <= 0:
        return "няма данни", "Няма активна история на печалбите. Не прави изводи."
    if rows < 20:
        return "много малко данни", "Само начална ориентация. Не увеличавай играта по тази база."
    if rows < 100:
        return "начална база", "Може да се гледа текущият цикъл, но изводите са ограничени."
    if rows < 500:
        return "добра частична база", "Може да се сравняват периоди, но пак без гаранции."
    return "стабилна историческа база", "Има достатъчно история за по-смислени сравнения, но играта остава случайна."


def compute_decision(prize_df: pd.DataFrame, ticket_price_eur: float = 3.60, max_tickets: int = 3) -> Dict[str, Any]:
    history_summary = load_historical_draws_summary()
    rows = len(prize_df)
    coverage, coverage_note = _coverage_label(rows)
    latest: Optional[pd.Series] = prize_df.iloc[-1] if rows else None
    six_rows = prize_df[prize_df.get("winners_6", pd.Series(dtype=int)).apply(_safe_int) > 0] if rows else pd.DataFrame()
    last_six: Optional[pd.Series] = six_rows.iloc[-1] if not six_rows.empty else None

    latest_draw = _safe_int(latest.get("draw_number"), 0) if latest is not None else 0
    latest_year = _safe_int(latest.get("draw_year"), 0) if latest is not None else 0
    latest_jackpot = _safe_float(latest.get("jackpot_eur"), 0.0) if latest is not None else 0.0
    last_six_draw = _safe_int(last_six.get("draw_number"), 0) if last_six is not None else 0
    last_six_year = _safe_int(last_six.get("draw_year"), 0) if last_six is not None else 0
    last_six_date = str(last_six.get("draw_date", "") or "") if last_six is not None else ""
    gap_after_last_six = latest_draw - last_six_draw if latest is not None and last_six is not None and latest_year == last_six_year else None

    restart_jackpot = 0.0
    jackpot_growth = 0.0
    if last_six is not None and latest is not None and latest_year == last_six_year:
        after = prize_df[(prize_df["draw_year"].apply(_safe_int) == last_six_year) & (prize_df["draw_number"].apply(_safe_int) > last_six_draw)].copy()
        if not after.empty:
            restart_jackpot = _safe_float(after.iloc[0].get("jackpot_eur"), 0.0)
            jackpot_growth = max(0.0, latest_jackpot - restart_jackpot)

    avg_w5 = float(prize_df["winners_5"].mean()) if rows and "winners_5" in prize_df.columns else 0.0
    avg_w4 = float(prize_df["winners_4"].mean()) if rows and "winners_4" in prize_df.columns else 0.0
    avg_w3 = float(prize_df["winners_3"].mean()) if rows and "winners_3" in prize_df.columns else 0.0

    if rows < 20:
        recommended_tickets = 1
        stance = "само основен фиш"
        reason = "Историята на печалбите е твърде малка за разширяване."
        risk_level = "висок риск"
    elif gap_after_last_six is not None and gap_after_last_six >= 12 and jackpot_growth >= 500000:
        recommended_tickets = min(max_tickets, 3)
        stance = "разширен пакет е допустим"
        reason = "Има натрупване след последната 6-ца, но това не е гаранция за следващ тираж."
        risk_level = "умерен контрол на риска"
    elif gap_after_last_six is not None and gap_after_last_six >= 6 and jackpot_growth >= 250000:
        recommended_tickets = min(max_tickets, 2)
        stance = "балансиран пакет"
        reason = "Има натрупване, но историята още е частична."
        risk_level = "контролиран риск"
    else:
        recommended_tickets = 1
        stance = "основен фиш"
        reason = "Няма достатъчно силен сигнал за разширяване на броя фишове."
        risk_level = "пази бюджета"

    recommended_cost = round(recommended_tickets * ticket_price_eur, 2)
    plans = [
        {
            "tickets": 1,
            "title": "Основен фиш",
            "cost_eur": round(ticket_price_eur, 2),
            "use_when": "Когато искаш минимален разход и контрол на риска.",
            "status": "препоръчан" if recommended_tickets == 1 else "безопасен вариант",
        },
        {
            "tickets": 2,
            "title": "Балансиран пакет",
            "cost_eur": round(ticket_price_eur * 2, 2),
            "use_when": "Когато има частично натрупване и искаш повече покритие, без да прескачаш бюджета.",
            "status": "препоръчан" if recommended_tickets == 2 else "по избор",
        },
        {
            "tickets": 3,
            "title": "Разширен пакет",
            "cost_eur": round(ticket_price_eur * 3, 2),
            "use_when": "Само когато бюджетът е ясен и джакпот цикълът е в интересна фаза.",
            "status": "препоръчан" if recommended_tickets == 3 else "внимателно",
        },
    ]

    pending_tickets = 0
    played = load_played_tickets()
    if not played.empty and "status" in played.columns:
        status_text = played["status"].astype(str).str.lower()
        pending_tickets = int(status_text.str.contains("чака|pending|waiting", regex=True).sum())

    return {
        "status": "PLAY_DECISION_READY" if rows else "NO_PRIZE_HISTORY",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "history": history_summary,
        "prize_rows": rows,
        "coverage": coverage,
        "coverage_note": coverage_note,
        "latest_draw": {
            "year": latest_year,
            "draw_number": latest_draw,
            "draw_date": str(latest.get("draw_date", "") or "") if latest is not None else "",
            "jackpot_eur": latest_jackpot,
        },
        "last_six": {
            "year": last_six_year,
            "draw_number": last_six_draw,
            "draw_date": last_six_date,
            "gap_after_last_six": gap_after_last_six,
        },
        "jackpot_cycle": {
            "restart_jackpot_eur": restart_jackpot,
            "latest_jackpot_eur": latest_jackpot,
            "growth_eur": jackpot_growth,
        },
        "averages": {
            "winners_5": round(avg_w5, 2),
            "winners_4": round(avg_w4, 2),
            "winners_3": round(avg_w3, 2),
        },
        "recommendation": {
            "recommended_tickets": recommended_tickets,
            "recommended_cost_eur": recommended_cost,
            "stance_bg": stance,
            "reason_bg": reason,
            "risk_level_bg": risk_level,
            "ticket_price_eur": ticket_price_eur,
            "max_tickets": max_tickets,
        },
        "plans": plans,
        "pending_tickets": pending_tickets,
    }


def build_report() -> Dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    prize_df = load_prize_history()
    report = compute_decision(prize_df)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps({
        "name": "Контролирана препоръка за брой фишове",
        "version": "v115",
        "rules_bg": [
            "Ако историята на печалбите е твърде малка, не се препоръчва разширяване.",
            "Разширен пакет се допуска само при видимо натрупване и ясен бюджет.",
            "Това не е прогноза за печалба и не гарантира резултат.",
        ],
        "report_status": report.get("status"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [
        "# Step 115 — Решение за игра",
        "",
        f"Статус: {report.get('status')}",
        f"Активни записи за печалби: {report.get('prize_rows')}",
        f"Препоръка: {report.get('recommendation', {}).get('stance_bg')}",
        f"Брой фишове: {report.get('recommendation', {}).get('recommended_tickets')}",
        "",
        "Бележка: това е контрол на бюджета и риска, не гаранция за печалба.",
    ]
    REPORT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return report


def render_v115_play_decision_center_section() -> None:
    if st is None:
        raise RuntimeError("Streamlit не е наличен.")

    st.title("🎯 Решение за игра")
    st.caption("Свързва историята на числата, проверените БСТ печалби, джакпот цикъла и бюджета за фишове.")
    st.warning("Това е контрол на риска и бюджета. Не е прогноза и не гарантира печалба.")

    prize_df = load_prize_history()
    with st.sidebar:
        st.markdown("### Настройки за решение")
        ticket_price = st.number_input("Цена на един фиш", min_value=0.10, max_value=100.0, value=3.60, step=0.10)
        max_tickets = st.slider("Максимум фишове", min_value=1, max_value=3, value=3)

    report = compute_decision(prize_df, ticket_price_eur=float(ticket_price), max_tickets=int(max_tickets))
    recommendation = report.get("recommendation", {})
    latest = report.get("latest_draw", {})
    last_six = report.get("last_six", {})
    cycle = report.get("jackpot_cycle", {})
    averages = report.get("averages", {})
    history = report.get("history", {})

    if report.get("status") == "NO_PRIZE_HISTORY":
        st.info("Все още няма активна проверена история на печалбите. Първо въведи БСТ печалбите, после тази страница ще даде решение за обем на играта.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("История на числата", _format_int(history.get("rows", 0)))
    c2.metric("Печалби от БСТ", _format_int(report.get("prize_rows", 0)))
    c3.metric("Последна 6-ца", f"тираж {last_six.get('draw_number') or '—'}")
    c4.metric("Тиражи без 6-ца", str(last_six.get("gap_after_last_six") if last_six.get("gap_after_last_six") is not None else "—"))

    st.markdown("### Препоръка за текущия цикъл")
    st.success(f"**{recommendation.get('stance_bg', '—')}** — {recommendation.get('recommended_tickets', 0)} фиш/а, приблизително {_format_eur(recommendation.get('recommended_cost_eur', 0))}.")
    st.write(recommendation.get("reason_bg", ""))
    st.caption(f"Ниво: {recommendation.get('risk_level_bg', '—')} · Данни: {report.get('coverage')} — {report.get('coverage_note')}")

    a, b, c = st.columns(3)
    a.metric("Последен джакпот", _format_eur(latest.get("jackpot_eur", 0)))
    b.metric("Натрупване в цикъла", _format_eur(cycle.get("growth_eur", 0)))
    c.metric("Чакащи фишове", _format_int(report.get("pending_tickets", 0)))

    st.markdown("### Варианти")
    plan_cols = st.columns(3)
    for col, plan in zip(plan_cols, report.get("plans", [])):
        with col:
            st.markdown(f"#### {plan['title']}")
            st.metric("Разход", _format_eur(plan.get("cost_eur", 0)))
            st.write(plan.get("use_when", ""))
            st.caption(f"Статус: {plan.get('status', '—')}")

    st.markdown("### Контекст")
    ctx1, ctx2, ctx3 = st.columns(3)
    ctx1.metric("Средно 5-ци", str(averages.get("winners_5", 0)))
    ctx2.metric("Средно 4-ки", str(averages.get("winners_4", 0)))
    ctx3.metric("Средно 3-ки", str(averages.get("winners_3", 0)))

    with st.expander("Как се взема решението"):
        st.markdown(
            """
- Ако историята на печалбите е малка, страницата не позволява силни изводи.
- Ако има период без 6-ца и джакпотът се е натрупал, може да се допусне разширен пакет.
- Ако няма достатъчно натрупване или данните са малко, препоръката остава към основен фиш.
- Това управлява бюджета, а не предсказва печалба.
            """.strip()
        )

    if st.button("Обнови отчета за решение"):
        saved = build_report()
        st.success(f"Отчетът е обновен. Статус: {saved.get('status')}")

    st.markdown("### Последни БСТ записи")
    show_cols = [c for c in ["draw_year", "draw_number", "draw_date", "numbers_text", "jackpot_eur", "winners_6", "winners_5", "winners_4", "winners_3"] if c in prize_df.columns]
    if show_cols:
        st.dataframe(prize_df[show_cols].tail(20).iloc[::-1], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    result = build_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))

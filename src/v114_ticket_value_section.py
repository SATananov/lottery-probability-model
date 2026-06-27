from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "user_journal.db"
PRIZE_HISTORY_CSV = ROOT / "data" / "prize_winner_history.csv"
EXPORT_DIR = ROOT / "data" / "user_journal_exports"
PLAYED_TICKETS_CSV = EXPORT_DIR / "played_tickets.csv"
PLAYED_LINES_CSV = EXPORT_DIR / "played_ticket_lines.csv"
RESULTS_CSV = EXPORT_DIR / "played_ticket_results.csv"
DRAW_ENTRIES_CSV = EXPORT_DIR / "user_draw_entries.csv"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v114"
REPORT_JSON = REPORTS_DIR / "v114_ticket_value_report.json"
REPORT_MD = REPORTS_DIR / "v114_ticket_value_report.md"
LINE_VALUE_CSV = REPORTS_DIR / "v114_ticket_line_value.csv"
MODEL_JSON = MODELS_DIR / "ticket_value_model.json"

PRIZE_COLUMNS = [
    "draw_key", "draw_year", "draw_number", "draw_date", "n1", "n2", "n3", "n4", "n5", "n6",
    "numbers_text", "jackpot_eur", "winners_6", "prize_6_eur", "total_6_eur", "winners_5", "prize_5_eur",
    "total_5_eur", "winners_4", "prize_4_eur", "total_4_eur", "winners_3", "prize_3_eur", "total_3_eur",
    "source_url", "note",
]

TICKET_COLUMNS = [
    "id", "ticket_key", "saved_at_utc", "play_date", "target_draw_date", "target_draw_number", "mode", "plan_source",
    "strategy_type", "total_price_eur", "line_count", "status", "note",
]

LINE_COLUMNS = [
    "id", "ticket_id", "line_no", "source_ticket_id", "role", "n1", "n2", "n3", "n4", "n5", "n6", "numbers_text", "price_eur", "played", "note",
]

DRAW_ENTRY_COLUMNS = [
    "id", "draw_key", "draw_date", "draw_number", "drawing_position", "n1", "n2", "n3", "n4", "n5", "n6", "numbers_text", "source", "note",
]

RESULT_COLUMNS = [
    "id", "ticket_id", "draw_entry_id", "best_hits", "total_hits", "rows_with_hits", "rows_with_3_plus", "rows_with_4_plus", "matched_numbers_text", "best_line_no", "note",
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, str):
            text = value.replace("\u00a0", " ").replace("euro", "").replace("EUR", "").replace("€", "").strip()
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


def _format_numbers(numbers: List[int]) -> str:
    return ", ".join(str(int(n)) for n in sorted(numbers)) if numbers else "—"


def _read_csv(path: Path, columns: List[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    try:
        df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=columns)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df


def _read_db_table(table_name: str, fallback_path: Path, columns: List[str]) -> pd.DataFrame:
    if DB_PATH.exists():
        try:
            with sqlite3.connect(DB_PATH) as conn:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            pass
    return _read_csv(fallback_path, columns)


def _numbers_from_row(row: Any) -> List[int]:
    values = [_safe_int(row.get(f"n{i}"), 0) for i in range(1, 7)]
    if len(values) == 6 and len(set(values)) == 6 and all(1 <= value <= 49 for value in values):
        return sorted(values)
    text = str(row.get("numbers_text", "") or "")
    parts = []
    clean = text.replace("[", " ").replace("]", " ").replace(";", " ").replace(",", " ").replace("|", " ")
    for piece in clean.split():
        value = _safe_int(piece, 0)
        if 1 <= value <= 49:
            parts.append(value)
    if len(parts) >= 6:
        values = parts[:6]
        if len(set(values)) == 6:
            return sorted(values)
    return []


def _numbers_valid(row: Any) -> bool:
    return len(_numbers_from_row(row)) == 6


def load_prize_history() -> pd.DataFrame:
    df = _read_csv(PRIZE_HISTORY_CSV, PRIZE_COLUMNS)
    for col in ["draw_year", "draw_number", "n1", "n2", "n3", "n4", "n5", "n6", "winners_6", "winners_5", "winners_4", "winners_3"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_int)
    for col in [c for c in df.columns if c.endswith("_eur") or c == "jackpot_eur"]:
        df[col] = df[col].apply(_safe_float)
    if not df.empty:
        df["valid_numbers"] = df.apply(_numbers_valid, axis=1)
        df["draw_date_dt"] = pd.to_datetime(df.get("draw_date", ""), errors="coerce")
        df = df[df["valid_numbers"]].copy()
        df = df.sort_values(["draw_date_dt", "draw_year", "draw_number"], na_position="last").reset_index(drop=True)
    return df


def load_played_tickets() -> pd.DataFrame:
    df = _read_db_table("played_tickets", PLAYED_TICKETS_CSV, TICKET_COLUMNS)
    for col in ["id", "line_count"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_int)
    for col in ["total_price_eur", "budget_eur", "price_per_line_eur"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)
    if not df.empty:
        df = df.sort_values(["id"], ascending=True).reset_index(drop=True)
    return df


def load_played_lines() -> pd.DataFrame:
    df = _read_db_table("played_ticket_lines", PLAYED_LINES_CSV, LINE_COLUMNS)
    for col in ["id", "ticket_id", "line_no", "n1", "n2", "n3", "n4", "n5", "n6", "played"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_int)
    if "price_eur" in df.columns:
        df["price_eur"] = df["price_eur"].apply(_safe_float)
    if not df.empty:
        df = df.sort_values(["ticket_id", "line_no"], ascending=True).reset_index(drop=True)
    return df


def load_draw_entries() -> pd.DataFrame:
    df = _read_db_table("user_draw_entries", DRAW_ENTRIES_CSV, DRAW_ENTRY_COLUMNS)
    for col in ["id", "n1", "n2", "n3", "n4", "n5", "n6"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_int)
    return df


def load_saved_results() -> pd.DataFrame:
    df = _read_db_table("played_ticket_results", RESULTS_CSV, RESULT_COLUMNS)
    for col in ["id", "ticket_id", "draw_entry_id", "best_hits", "total_hits", "rows_with_hits", "rows_with_3_plus", "rows_with_4_plus", "best_line_no"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_int)
    return df


def _match_prize_row(ticket: pd.Series, prize_df: pd.DataFrame) -> Optional[pd.Series]:
    if prize_df.empty:
        return None
    target_date = str(ticket.get("target_draw_date", "") or "").strip()
    target_no = str(ticket.get("target_draw_number", "") or "").strip()
    play_date = str(ticket.get("play_date", "") or "").strip()

    candidates = prize_df.copy()
    if target_date:
        by_date = candidates[candidates["draw_date"].astype(str) == target_date]
        if not by_date.empty:
            return by_date.iloc[-1]
    if target_no:
        no = _safe_int(target_no, -1)
        by_no = candidates[candidates["draw_number"].apply(_safe_int) == no]
        if not by_no.empty:
            if target_date[:4].isdigit():
                by_no_year = by_no[by_no["draw_year"].apply(_safe_int) == int(target_date[:4])]
                if not by_no_year.empty:
                    return by_no_year.iloc[-1]
            return by_no.iloc[-1]
    if play_date:
        # Last fallback: if a ticket was saved exactly for a known draw date.
        by_play_date = candidates[candidates["draw_date"].astype(str) == play_date]
        if not by_play_date.empty:
            return by_play_date.iloc[-1]
    return None


def _hit_label(hits: int) -> str:
    if hits >= 6:
        return "6 числа"
    if hits == 5:
        return "5 числа"
    if hits == 4:
        return "4 числа"
    if hits == 3:
        return "3 числа"
    if hits > 0:
        return f"{hits} числа"
    return "няма попадение"


def _line_prize_for_hits(prize_row: pd.Series, hits: int) -> float:
    if hits in (3, 4, 5, 6):
        return _safe_float(prize_row.get(f"prize_{hits}_eur"), 0.0)
    return 0.0


def build_ticket_value_analysis() -> Dict[str, Any]:
    prize_df = load_prize_history()
    tickets_df = load_played_tickets()
    lines_df = load_played_lines()
    draw_entries_df = load_draw_entries()
    saved_results_df = load_saved_results()

    line_rows: List[Dict[str, Any]] = []
    ticket_rows: List[Dict[str, Any]] = []

    for _, ticket in tickets_df.iterrows():
        ticket_id = _safe_int(ticket.get("id"), 0)
        ticket_lines = lines_df[lines_df["ticket_id"].apply(_safe_int) == ticket_id].copy() if not lines_df.empty else pd.DataFrame()
        prize_row = _match_prize_row(ticket, prize_df)
        has_prize = prize_row is not None
        draw_numbers = _numbers_from_row(prize_row) if has_prize else []
        draw_key = str(prize_row.get("draw_key", "")) if has_prize else ""
        draw_date = str(prize_row.get("draw_date", "")) if has_prize else str(ticket.get("target_draw_date", "") or "")
        ticket_return = 0.0
        best_hits = 0
        rows_with_prize = 0
        matched_all: set[int] = set()

        for _, line in ticket_lines.iterrows():
            line_numbers = _numbers_from_row(line)
            matched = sorted(set(line_numbers) & set(draw_numbers)) if draw_numbers else []
            hits = len(matched)
            prize_eur = _line_prize_for_hits(prize_row, hits) if has_prize else 0.0
            if prize_eur > 0:
                rows_with_prize += 1
            ticket_return += prize_eur
            best_hits = max(best_hits, hits)
            matched_all.update(matched)
            line_rows.append({
                "ticket_id": ticket_id,
                "Фиш": f"Фиш {ticket_id}",
                "Ред": _safe_int(line.get("line_no"), 0),
                "Комбинация": _format_numbers(line_numbers),
                "Тираж": draw_key or "чака данни",
                "Дата": draw_date or "—",
                "Печеливши числа": _format_numbers(draw_numbers),
                "Попадения": hits,
                "Категория": _hit_label(hits),
                "Съвпаднали числа": _format_numbers(matched),
                "Печалба от реда": round(prize_eur, 2),
                "Статус": "оценен" if has_prize else "чака данни за печалбите",
                "Произход": str(line.get("role", "") or line.get("source_ticket_id", "") or "—"),
            })

        total_price = _safe_float(ticket.get("total_price_eur"), 0.0)
        if total_price <= 0 and not ticket_lines.empty:
            total_price = sum(_safe_float(v, 0.0) for v in ticket_lines.get("price_eur", []))
        balance = ticket_return - total_price
        saved_result = saved_results_df[saved_results_df["ticket_id"].apply(_safe_int) == ticket_id] if not saved_results_df.empty else pd.DataFrame()
        ticket_rows.append({
            "ticket_id": ticket_id,
            "Фиш": f"Фиш {ticket_id}",
            "Дата на игра": str(ticket.get("play_date", "") or ""),
            "Целеви тираж": draw_key or str(ticket.get("target_draw_number", "") or "—"),
            "Целева дата": str(ticket.get("target_draw_date", "") or draw_date or "—"),
            "Комбинации": int(len(ticket_lines)),
            "Цена": round(total_price, 2),
            "Печалба": round(ticket_return, 2),
            "Баланс": round(balance, 2),
            "Най-добър ред": best_hits,
            "Редове с печалба": rows_with_prize,
            "Съвпаднали числа": _format_numbers(sorted(matched_all)),
            "Статус": "оценен по БСТ печалби" if has_prize else "чака БСТ печалби за този тираж",
            "Записан резултат": "има" if not saved_result.empty else "няма",
            "Бележка": str(ticket.get("note", "") or ""),
        })

    total_spent = sum(_safe_float(row.get("Цена"), 0.0) for row in ticket_rows)
    total_return = sum(_safe_float(row.get("Печалба"), 0.0) for row in ticket_rows)
    evaluated_tickets = sum(1 for row in ticket_rows if str(row.get("Статус")) == "оценен по БСТ печалби")
    waiting_tickets = max(len(ticket_rows) - evaluated_tickets, 0)
    best_ticket = max(ticket_rows, key=lambda r: _safe_float(r.get("Печалба"), 0.0), default=None)

    if prize_df.empty:
        status = "NO_PRIZE_HISTORY"
        note = "Няма налични БСТ данни за печалбите. Първо добави проверени печалби."
    elif tickets_df.empty:
        status = "NO_PLAYED_TICKETS"
        note = "Няма запазени фишове в дневника. Анализът ще се активира след като запазиш реален фиш."
    else:
        status = "TICKET_VALUE_READY"
        note = "Анализът сравнява реално запазените фишове с наличните проверени печалби от БСТ."

    summary = {
        "step": 114,
        "name": "Real Ticket Value",
        "status": status,
        "blocking_failures": 0,
        "prize_history_rows": int(len(prize_df)),
        "played_tickets": int(len(tickets_df)),
        "played_lines": int(len(lines_df)),
        "evaluated_tickets": int(evaluated_tickets),
        "waiting_tickets": int(waiting_tickets),
        "total_spent_eur": round(total_spent, 2),
        "total_return_eur": round(total_return, 2),
        "net_balance_eur": round(total_return - total_spent, 2),
        "best_ticket": best_ticket,
        "ticket_rows": ticket_rows,
        "line_rows": line_rows,
        "draw_entries": int(len(draw_entries_df)),
        "saved_result_rows": int(len(saved_results_df)),
        "note_bg": note,
        "safe_note_bg": "Това е отчет на реална стойност по вече изтеглени тиражи и проверени печалби. Не е прогноза и не гарантира бъдеща печалба.",
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    return summary


def write_artifacts() -> Dict[str, Any]:
    summary = build_ticket_value_analysis()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    REPORT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps({
        "step": summary["step"],
        "status": summary["status"],
        "blocking_failures": summary["blocking_failures"],
        "prize_history_rows": summary["prize_history_rows"],
        "played_tickets": summary["played_tickets"],
        "evaluated_tickets": summary["evaluated_tickets"],
        "total_spent_eur": summary["total_spent_eur"],
        "total_return_eur": summary["total_return_eur"],
        "net_balance_eur": summary["net_balance_eur"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    line_rows = summary.get("line_rows") or []
    with LINE_VALUE_CSV.open("w", encoding="utf-8", newline="") as handle:
        if line_rows:
            writer = csv.DictWriter(handle, fieldnames=list(line_rows[0].keys()))
            writer.writeheader()
            writer.writerows(line_rows)
        else:
            handle.write("")

    md = [
        "# Step 114 — Реална стойност на фишовете",
        "",
        f"- Статус: `{summary['status']}`",
        f"- Блокиращи проблеми: `{summary['blocking_failures']}`",
        f"- История на печалбите: {summary['prize_history_rows']} записа",
        f"- Запазени фишове: {summary['played_tickets']}",
        f"- Оценени фишове: {summary['evaluated_tickets']}",
        f"- Обща цена: {_format_eur(summary['total_spent_eur'])}",
        f"- Потенциална печалба: {_format_eur(summary['total_return_eur'])}",
        f"- Баланс: {_format_eur(summary['net_balance_eur'])}",
        "",
        summary.get("safe_note_bg", ""),
    ]
    REPORT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


def _rename_ticket_rows(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows).drop(columns=["ticket_id"], errors="ignore")


def _rename_line_rows(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows).drop(columns=["ticket_id"], errors="ignore")


def render_v114_ticket_value_section() -> None:
    if st is None:
        return
    st.title("Реална стойност на фишовете")
    st.caption("Сравнява запазените фишове с вече изтеглен тираж и проверените печалби от БСТ.")
    st.info("Това е отчет след тиража: цена на фиша, попадения, реална категория и възможна печалба по БСТ. Не е прогноза.")

    if st.button("Обнови реалната стойност", use_container_width=True, key="v114_refresh_ticket_value"):
        summary = write_artifacts()
        st.success("Анализът е обновен.")
    else:
        summary = write_artifacts()

    cols = st.columns(6)
    cols[0].metric("Фишове", _format_int(summary.get("played_tickets", 0)))
    cols[1].metric("Оценени", _format_int(summary.get("evaluated_tickets", 0)))
    cols[2].metric("Чакащи", _format_int(summary.get("waiting_tickets", 0)))
    cols[3].metric("Цена", _format_eur(summary.get("total_spent_eur", 0)))
    cols[4].metric("Печалба", _format_eur(summary.get("total_return_eur", 0)))
    cols[5].metric("Баланс", _format_eur(summary.get("net_balance_eur", 0)))

    st.markdown("### Как да се чете")
    st.markdown(
        "- Ако има проверени БСТ печалби за целевия тираж, всеки ред получава категория: 3, 4, 5 или 6 числа.\n"
        "- Ако няма БСТ печалби за този тираж, фишът остава в статус **чака данни**.\n"
        "- Балансът е само отчет: **печалба минус цена на фиша**."
    )

    status = str(summary.get("status", ""))
    if status == "NO_PRIZE_HISTORY":
        st.warning("Няма налична история на печалбите. Добави проверени БСТ данни, за да се изчислява стойност на фишовете.")
    elif status == "NO_PLAYED_TICKETS":
        st.warning("Няма запазени фишове в дневника. Запази реално изигран фиш, после тази страница ще го оцени.")
    else:
        st.success("Има достатъчно данни за отчет на реалната стойност на наличните фишове.")

    tab_summary, tab_tickets, tab_lines, tab_missing = st.tabs(["Обобщение", "Фишове", "Комбинации", "Нужни данни"])

    with tab_summary:
        best = summary.get("best_ticket") or {}
        if best:
            st.markdown("#### Най-добър фиш в наличния отчет")
            st.write(
                f"{best.get('Фиш', 'Фиш')} · печалба {_format_eur(best.get('Печалба', 0))} · "
                f"баланс {_format_eur(best.get('Баланс', 0))} · най-добър ред: {best.get('Най-добър ред', 0)} числа"
            )
        st.markdown("#### Бележка")
        st.write(summary.get("safe_note_bg", ""))

    with tab_tickets:
        rows = summary.get("ticket_rows") or []
        if rows:
            st.dataframe(_rename_ticket_rows(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Още няма фишове за показване.")

    with tab_lines:
        rows = summary.get("line_rows") or []
        if rows:
            st.dataframe(_rename_line_rows(rows), use_container_width=True, hide_index=True)
            st.download_button(
                "Свали CSV с оценката по комбинации",
                data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"),
                file_name="ticket_line_value.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.info("Още няма комбинации за оценка.")

    with tab_missing:
        st.markdown("#### Какво е нужно за пълна оценка")
        st.markdown(
            "1. Фишът трябва да е запазен в **Дневник на фишовете**.\n"
            "2. Реалният тираж трябва да е въведен.\n"
            "3. За този тираж трябва да има проверени БСТ печалби.\n"
            "4. Тогава страницата изчислява попадения, категория, печалба и баланс."
        )
        st.write(f"История на печалбите: {_format_int(summary.get('prize_history_rows', 0))} записа")
        st.write(f"Реални тиражи в дневника: {_format_int(summary.get('draw_entries', 0))}")
        st.write(f"Записани резултати в дневника: {_format_int(summary.get('saved_result_rows', 0))}")

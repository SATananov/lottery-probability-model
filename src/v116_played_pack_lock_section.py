from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EXPORT_DIR = DATA_DIR / "user_journal_exports"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v116"
DB_PATH = DATA_DIR / "user_journal.db"
PLAYED_TICKETS_CSV = EXPORT_DIR / "played_tickets.csv"
PLAYED_LINES_CSV = EXPORT_DIR / "played_ticket_lines.csv"
PLAYED_RESULTS_CSV = EXPORT_DIR / "played_ticket_results.csv"
DRAW_ENTRIES_CSV = EXPORT_DIR / "user_draw_entries.csv"
REPORT_JSON = REPORTS_DIR / "v116_played_pack_lock_report.json"
REPORT_MD = REPORTS_DIR / "v116_played_pack_lock_report.md"
LOCK_EXPORT_CSV = EXPORT_DIR / "played_pack_lock.csv"
MODEL_JSON = MODELS_DIR / "played_pack_lock_policy.json"


STATUS_LABELS = {
    "PLAYED_WAITING_RESULT": "Игран — чака резултат",
    "PLAYED": "Игран",
    "PLANNED": "Планиран",
    "EVALUATED": "Проверен",
    "WAITING_RESULT": "Чака резултат",
    "PENDING": "Чака резултат",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        text = str(value).strip()
        if not text:
            return default
        return int(float(text))
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        text = str(value).replace("\u00a0", " ").replace("EUR", "").replace("euro", "").replace("€", "").strip()
        if not text:
            return default
        text = text.replace(" ", "").replace(",", ".")
        keep = "".join(ch for ch in text if ch.isdigit() or ch in ".-")
        if keep in {"", ".", "-"}:
            return default
        return float(keep)
    except Exception:
        return default


def _format_eur(value: Any) -> str:
    return f"{_safe_float(value):,.2f} EUR".replace(",", " ")


def _format_int(value: Any) -> str:
    return f"{_safe_int(value):,}".replace(",", " ")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _read_sql_table(table: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(f"SELECT * FROM {table}", conn)
    except Exception:
        return pd.DataFrame()


def load_played_tickets() -> pd.DataFrame:
    df = _read_sql_table("played_tickets")
    if df.empty:
        df = _read_csv(PLAYED_TICKETS_CSV)
    if df.empty:
        return df
    for col in ["id", "line_count"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_int)
    for col in ["budget_eur", "price_per_line_eur", "total_price_eur"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)
    for col in ["play_date", "target_draw_date", "saved_at_utc", "status", "note", "ticket_key"]:
        if col not in df.columns:
            df[col] = ""
    return df


def load_played_lines() -> pd.DataFrame:
    df = _read_sql_table("played_ticket_lines")
    if df.empty:
        df = _read_csv(PLAYED_LINES_CSV)
    if df.empty:
        return df
    for col in ["id", "ticket_id", "line_no", "n1", "n2", "n3", "n4", "n5", "n6", "played"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_int)
    for col in ["price_eur"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)
    for col in ["numbers_text", "role", "source_ticket_id", "note"]:
        if col not in df.columns:
            df[col] = ""
    return df


def load_results() -> pd.DataFrame:
    df = _read_sql_table("played_ticket_results")
    if df.empty:
        df = _read_csv(PLAYED_RESULTS_CSV)
    if df.empty:
        return df
    for col in ["id", "ticket_id", "draw_entry_id", "best_hits", "total_hits", "rows_with_hits", "rows_with_3_plus", "rows_with_4_plus", "best_line_no"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_int)
    for col in ["matched_numbers_text", "evaluated_at_utc", "note"]:
        if col not in df.columns:
            df[col] = ""
    return df


def _numbers_from_line(row: pd.Series) -> List[int]:
    values = [_safe_int(row.get(f"n{i}"), 0) for i in range(1, 7)]
    if len(values) == 6 and len(set(values)) == 6 and all(1 <= value <= 49 for value in values):
        return values
    text = str(row.get("numbers_text", "") or "").replace(";", ",").replace("|", ",").replace("-", ",")
    parts = [part.strip() for part in text.replace(" ", ",").split(",") if part.strip()]
    values = [_safe_int(part, 0) for part in parts]
    values = [value for value in values if 1 <= value <= 49]
    return values[:6]


def _numbers_text(numbers: List[int]) -> str:
    return ", ".join(str(value) for value in numbers)


def _status_label(status: Any) -> str:
    raw = str(status or "").strip()
    if not raw:
        return "—"
    return STATUS_LABELS.get(raw, raw)


def _group_key(row: pd.Series) -> str:
    target = str(row.get("target_draw_date", "") or "").strip() or "без целеви тираж"
    play = str(row.get("play_date", "") or "").strip() or "без дата на игра"
    return f"{target} · играно на {play}"


def _ticket_sort(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cols = [col for col in ["target_draw_date", "play_date", "id"] if col in df.columns]
    return df.sort_values(cols, na_position="last").reset_index(drop=True) if cols else df


def build_lock_snapshot() -> Dict[str, Any]:
    tickets = _ticket_sort(load_played_tickets())
    lines = load_played_lines()
    results = load_results()
    status = "PLAYED_PACK_LOCK_READY" if not tickets.empty else "NO_PLAYED_TICKETS"

    active_tickets = tickets.copy()
    if not active_tickets.empty and "status" in active_tickets.columns:
        text = active_tickets["status"].astype(str).str.lower()
        archived = text.str.contains("draft|чернова|deleted|изтрит", regex=True)
        active_tickets = active_tickets[~archived].copy()

    ticket_ids = set(active_tickets.get("id", pd.Series(dtype=int)).apply(_safe_int).tolist()) if not active_tickets.empty else set()
    active_lines = lines[lines.get("ticket_id", pd.Series(dtype=int)).apply(_safe_int).isin(ticket_ids)].copy() if not lines.empty and ticket_ids else pd.DataFrame()
    active_results = results[results.get("ticket_id", pd.Series(dtype=int)).apply(_safe_int).isin(ticket_ids)].copy() if not results.empty and ticket_ids else pd.DataFrame()

    total_price = float(active_tickets.get("total_price_eur", pd.Series(dtype=float)).apply(_safe_float).sum()) if not active_tickets.empty else 0.0
    line_count = int(len(active_lines)) if not active_lines.empty else int(active_tickets.get("line_count", pd.Series(dtype=int)).apply(_safe_int).sum()) if not active_tickets.empty else 0
    target_dates = sorted({str(value).strip() for value in active_tickets.get("target_draw_date", pd.Series(dtype=str)).tolist() if str(value).strip()}) if not active_tickets.empty else []
    play_dates = sorted({str(value).strip() for value in active_tickets.get("play_date", pd.Series(dtype=str)).tolist() if str(value).strip()}) if not active_tickets.empty else []

    pending_count = 0
    evaluated_count = 0
    if not active_tickets.empty and "status" in active_tickets.columns:
        status_text = active_tickets["status"].astype(str).str.lower()
        pending_count = int(status_text.str.contains("чака|waiting|pending|played", regex=True).sum())
        evaluated_count = int(status_text.str.contains("провер|evaluated|closed", regex=True).sum())
    if not active_results.empty:
        evaluated_count = max(evaluated_count, int(active_results["ticket_id"].nunique()))
        pending_count = max(0, len(active_tickets) - evaluated_count)

    export_rows: List[Dict[str, Any]] = []
    if not active_tickets.empty:
        for _, ticket in active_tickets.iterrows():
            ticket_id = _safe_int(ticket.get("id"), 0)
            ticket_lines = active_lines[active_lines.get("ticket_id", pd.Series(dtype=int)).apply(_safe_int) == ticket_id].copy() if not active_lines.empty else pd.DataFrame()
            if ticket_lines.empty:
                export_rows.append({
                    "ticket_id": ticket_id,
                    "ticket_key": ticket.get("ticket_key", ""),
                    "play_date": ticket.get("play_date", ""),
                    "target_draw_date": ticket.get("target_draw_date", ""),
                    "line_no": "",
                    "numbers_text": "",
                    "status": _status_label(ticket.get("status", "")),
                    "total_price_eur": _safe_float(ticket.get("total_price_eur"), 0.0),
                })
            else:
                ticket_lines = ticket_lines.sort_values("line_no") if "line_no" in ticket_lines.columns else ticket_lines
                for _, line in ticket_lines.iterrows():
                    nums = _numbers_from_line(line)
                    export_rows.append({
                        "ticket_id": ticket_id,
                        "ticket_key": ticket.get("ticket_key", ""),
                        "play_date": ticket.get("play_date", ""),
                        "target_draw_date": ticket.get("target_draw_date", ""),
                        "line_no": _safe_int(line.get("line_no"), 0),
                        "numbers_text": _numbers_text(nums),
                        "role": line.get("role", ""),
                        "status": _status_label(ticket.get("status", "")),
                        "total_price_eur": _safe_float(ticket.get("total_price_eur"), 0.0),
                    })

    return {
        "status": status,
        "created_at_utc": _now(),
        "ticket_count": int(len(active_tickets)),
        "line_count": line_count,
        "target_dates": target_dates,
        "play_dates": play_dates,
        "total_price_eur": round(total_price, 2),
        "pending_ticket_count": pending_count,
        "evaluated_ticket_count": evaluated_count,
        "has_results": not active_results.empty,
        "export_rows": export_rows,
        "note_bg": "Това е заключен изглед на реално пуснатите фишове. Тук не се показват предложения, а записаните като играни фишове.",
    }


def write_export(rows: List[Dict[str, Any]]) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not rows:
        LOCK_EXPORT_CSV.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with LOCK_EXPORT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_report() -> Dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = build_lock_snapshot()
    write_export(snapshot.get("export_rows", []))
    report_for_json = dict(snapshot)
    # Keep JSON report compact; CSV has the row-level details.
    report_for_json["export_rows"] = snapshot.get("export_rows", [])[:30]
    REPORT_JSON.write_text(json.dumps(report_for_json, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps({
        "name": "Заключване на реално играни фишове",
        "version": "v116",
        "rules_bg": [
            "Заключеният изглед показва само фишове, които вече са записани като играни.",
            "Предложенията от модела не се смесват с реално пуснатите фишове.",
            "След реалния тираж резултатите се проверяват от дневника и се показват отделно.",
        ],
        "report_status": snapshot.get("status"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [
        "# Step 116 — Реално играни фишове",
        "",
        f"Статус: {snapshot.get('status')}",
        f"Фишове: {snapshot.get('ticket_count')}",
        f"Комбинации: {snapshot.get('line_count')}",
        f"Обща цена: {_format_eur(snapshot.get('total_price_eur', 0))}",
        "",
        "Бележка: това е заключен изглед на реално пуснатите фишове, не нова прогноза.",
    ]
    REPORT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return snapshot


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .lock-hero {
            border: 1px solid rgba(225,190,92,0.26);
            border-radius: 22px;
            padding: 22px 24px;
            background: linear-gradient(135deg, rgba(225,190,92,0.12), rgba(36,42,55,0.44));
            margin: 10px 0 20px 0;
        }
        .lock-hero-title { color: #f7e9bf; font-weight: 950; font-size: 1.14rem; margin-bottom: 8px; }
        .lock-hero-text { color: rgba(246,241,232,0.84); line-height: 1.55; }
        .lock-card {
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 20px;
            padding: 18px 20px;
            background: rgba(255,255,255,0.035);
            margin: 14px 0;
        }
        .lock-card-title { color: #f7e9bf; font-weight: 900; font-size: 1.06rem; margin-bottom: 8px; }
        .lock-muted { color: rgba(246,241,232,0.65); font-size: 0.91rem; }
        .lock-line { border-top: 1px solid rgba(255,255,255,0.08); padding-top: 12px; margin-top: 12px; }
        .lock-balls { display: flex; gap: 9px; flex-wrap: wrap; align-items: center; margin: 7px 0; }
        .lock-ball {
            width: 42px; height: 42px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
            background: radial-gradient(circle at 32% 25%, #fff3a7 0%, #f1cf54 44%, #c89a19 100%);
            color: #111; font-weight: 950; border: 1px solid rgba(255,255,255,0.34);
            box-shadow: inset 0 2px 7px rgba(255,255,255,0.30), 0 7px 15px rgba(0,0,0,0.30);
        }
        .lock-badge { display:inline-block; border:1px solid rgba(225,190,92,0.26); border-radius:999px; padding:5px 10px; color:#f5e7bd; background:rgba(225,190,92,0.08); font-size:0.84rem; font-weight:800; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_balls(numbers: List[int]) -> str:
    return "<div class='lock-balls'>" + "".join(f"<span class='lock-ball'>{n}</span>" for n in numbers) + "</div>"


def render_v116_played_pack_lock_section() -> None:
    if st is None:
        raise RuntimeError("Streamlit не е наличен.")
    _inject_css()
    st.title("🔒 Реално играни фишове")
    st.markdown(
        """
        <div class="lock-hero">
          <div class="lock-hero-title">Заключен изглед на това, което реално е пуснато</div>
          <div class="lock-hero-text">Тази страница не показва нови предложения. Тя показва фишовете, които вече са записани като играни в дневника, с целевия тираж, цената, редовете и статуса им.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tickets = load_played_tickets()
    lines = load_played_lines()
    results = load_results()
    snapshot = build_lock_snapshot()

    if tickets.empty:
        st.info("Все още няма записани реално играни фишове. Запази пакет от страницата „Дневник на фишовете“, след което той ще се появи тук като заключен.")
        if st.button("Обнови заключения отчет"):
            saved = build_report()
            st.success(f"Отчетът е обновен. Статус: {saved.get('status')}")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Фишове", _format_int(snapshot.get("ticket_count", 0)))
    c2.metric("Комбинации", _format_int(snapshot.get("line_count", 0)))
    c3.metric("Обща цена", _format_eur(snapshot.get("total_price_eur", 0)))
    c4.metric("Чакащи", _format_int(snapshot.get("pending_ticket_count", 0)))

    target_dates = snapshot.get("target_dates", []) or []
    selected_target = None
    if target_dates:
        selected_target = st.selectbox("Целеви тираж", options=["Всички"] + target_dates, index=0)

    view_tickets = tickets.copy()
    if selected_target and selected_target != "Всички" and "target_draw_date" in view_tickets.columns:
        view_tickets = view_tickets[view_tickets["target_draw_date"].astype(str) == selected_target].copy()
    view_tickets = _ticket_sort(view_tickets)

    st.caption("Ако си играл днес за неделния тираж, тук трябва да виждаш точно пуснатите фишове. След реалния тираж дневникът ще ги провери.")

    for _, ticket in view_tickets.iterrows():
        ticket_id = _safe_int(ticket.get("id"), 0)
        target = str(ticket.get("target_draw_date", "") or "—")
        play_date = str(ticket.get("play_date", "") or "—")
        status = _status_label(ticket.get("status", ""))
        total_price = _format_eur(ticket.get("total_price_eur", 0))
        note = str(ticket.get("note", "") or "")
        ticket_lines = lines[lines.get("ticket_id", pd.Series(dtype=int)).apply(_safe_int) == ticket_id].copy() if not lines.empty else pd.DataFrame()
        ticket_results = results[results.get("ticket_id", pd.Series(dtype=int)).apply(_safe_int) == ticket_id].copy() if not results.empty else pd.DataFrame()
        if not ticket_lines.empty and "line_no" in ticket_lines.columns:
            ticket_lines = ticket_lines.sort_values("line_no")

        st.markdown(
            f"""
            <div class="lock-card">
              <div class="lock-card-title">🎫 Фиш #{ticket_id} <span class="lock-badge">{status}</span></div>
              <div class="lock-muted">Играно на: <b>{play_date}</b> · Целеви тираж: <b>{target}</b> · Цена: <b>{total_price}</b></div>
              <div class="lock-muted">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if ticket_lines.empty:
            st.warning("За този фиш няма записани редове.")
        else:
            for _, line in ticket_lines.iterrows():
                nums = _numbers_from_line(line)
                role = str(line.get("role", "") or "ред")
                line_no = _safe_int(line.get("line_no"), 0)
                st.markdown(
                    f"""
                    <div class="lock-line">
                      <div class="lock-muted">Ред {line_no} · {role}</div>
                      {_render_balls(nums)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        if not ticket_results.empty:
            best = ticket_results.iloc[-1]
            st.success(f"Проверен резултат: най-добър ред {best.get('best_hits', 0)} числа · общо попадения {best.get('total_hits', 0)}")
        else:
            st.info("Статус: чака реален тираж и проверка на фиша.")

    if st.button("Обнови заключения отчет"):
        saved = build_report()
        st.success(f"Отчетът е обновен. Статус: {saved.get('status')}")

    if LOCK_EXPORT_CSV.exists():
        st.download_button(
            "Свали заключения пакет като CSV",
            data=LOCK_EXPORT_CSV.read_bytes(),
            file_name="played_pack_lock.csv",
            mime="text/csv",
        )

    with st.expander("Какво означава заключен пакет"):
        st.markdown(
            """
- Предложен пакет = моделът предлага числа.
- Реално игран пакет = ти си ги пуснал и си ги записал в дневника.
- Заключен пакет = app-ът ги показва отделно, за да не ги объркаме с нови предложения.
- След като въведеш реалния тираж, натискаш „Провери чакащите фишове“ в дневника.
            """.strip()
        )


if __name__ == "__main__":
    result = build_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))

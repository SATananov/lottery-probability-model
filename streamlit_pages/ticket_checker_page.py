
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DRAW_EVENTS_PATH = ROOT / "data" / "v40_sample_draw_event_result.csv"
NORMALIZED_DRAW_EVENTS_PATH = ROOT / "data" / "v40_normalized_draw_events.csv"
TICKET_CHECKER_SCRIPT_PATH = ROOT / "scripts" / "v40_ticket_checker.py"

NUMBER_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]

DEMO_TICKET_TABLES = [
    [22, 26, 28, 29, 40, 42],
    [1, 7, 14, 21, 35, 49],
    [7, 14, 21, 28, 35, 42],
    [3, 11, 18, 27, 34, 49],
]

T = {
    "title": "\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043d\u0430 \u0444\u0438\u0448",
    "hero": "\u041f\u043e\u043f\u044a\u043b\u043d\u0438 \u0444\u0438\u0448\u0430 \u043a\u0430\u0442\u043e \u0438\u0437\u0431\u0438\u0440\u0430\u0448 \u0447\u0438\u0441\u043b\u0430\u0442\u0430 \u0434\u0438\u0440\u0435\u043a\u0442\u043d\u043e \u0432\u044a\u0432 \u0432\u0441\u044f\u043a\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f. \u0412\u0441\u044f\u043a\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0442\u0440\u044f\u0431\u0432\u0430 \u0434\u0430 \u0438\u043c\u0430 \u0442\u043e\u0447\u043d\u043e 6 \u0447\u0438\u0441\u043b\u0430.",
    "note": "\u0422\u043e\u0432\u0430 \u0435 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043d\u0430 \u0444\u0438\u0448, \u043d\u0435 \u043e\u0431\u0435\u0449\u0430\u043d\u0438\u0435 \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430.",
    "how": "\u041a\u0430\u043a \u0441\u0435 \u043f\u043e\u043f\u044a\u043b\u0432\u0430?",
    "how_text": "- \u0418\u0437\u0431\u0435\u0440\u0438 \u0431\u0440\u043e\u0439 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438.\n- \u041d\u0430\u0442\u0438\u0441\u043a\u0430\u0439 \u0447\u0438\u0441\u043b\u0430\u0442\u0430 \u0434\u0438\u0440\u0435\u043a\u0442\u043d\u043e \u0432\u044a\u0432 \u0441\u044a\u043e\u0442\u0432\u0435\u0442\u043d\u0430\u0442\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f.\n- \u0418\u0437\u0431\u0440\u0430\u043d\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u0430 \u0441\u0435 \u043e\u0442\u0431\u0435\u043b\u044f\u0437\u0432\u0430\u0442 \u0441 X.\n- \u0424\u0438\u0448\u044a\u0442 \u0441\u0435 \u043f\u0440\u043e\u0432\u0435\u0440\u044f\u0432\u0430 \u0441\u0440\u0435\u0449\u0443 \u0432\u0441\u044f\u043a\u043e \u0442\u0435\u0433\u043b\u0435\u043d\u0435 \u043e\u0442 \u0438\u0437\u0431\u0440\u0430\u043d\u0438\u044f \u0442\u0438\u0440\u0430\u0436.",
    "step1": "1. \u041f\u043e\u043f\u044a\u043b\u043d\u0438 \u0444\u0438\u0448\u0430",
    "step2": "2. \u0418\u0437\u0431\u0435\u0440\u0438 \u0442\u0438\u0440\u0430\u0436",
    "step3": "3. \u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442",
    "ticket_tables": "\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u0432\u044a\u0432 \u0444\u0438\u0448\u0430",
    "load_demo": "\u0417\u0430\u0440\u0435\u0434\u0438 \u0434\u0435\u043c\u043e \u0444\u0438\u0448",
    "clear_all": "\u0418\u0437\u0447\u0438\u0441\u0442\u0438 \u0444\u0438\u0448\u0430",
    "clear_combo": "\u0418\u0437\u0447\u0438\u0441\u0442\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f\u0442\u0430",
    "combo": "\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f",
    "selected": "\u0418\u0437\u0431\u0440\u0430\u043d\u0438",
    "no_selected": "\u043d\u044f\u043c\u0430 \u0438\u0437\u0431\u0440\u0430\u043d\u0438 \u0447\u0438\u0441\u043b\u0430",
    "complete": "\u043f\u044a\u043b\u043d\u0430",
    "incomplete": "\u043d\u0435\u043f\u044a\u043b\u043d\u0430",
    "draw_source": "\u041a\u043e\u0439 \u0442\u0438\u0440\u0430\u0436 \u0434\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u0438\u043c?",
    "sample_draw": "\u0414\u0435\u043c\u043e \u0442\u0438\u0440\u0430\u0436 \u0441 2 \u0442\u0435\u0433\u043b\u0435\u043d\u0438\u044f",
    "latest_draw": "\u041f\u043e\u0441\u043b\u0435\u0434\u0435\u043d \u0442\u0438\u0440\u0430\u0436 \u043e\u0442 \u0434\u0430\u043d\u043d\u0438\u0442\u0435",
    "demo_draw_name": "\u0414\u0435\u043c\u043e \u0442\u0438\u0440\u0430\u0436",
    "demo_date": "\u0422\u0435\u0441\u0442",
    "drawing": "\u0422\u0435\u0433\u043b\u0435\u043d\u0435",
    "draw": "\u0422\u0438\u0440\u0430\u0436",
    "date": "\u0414\u0430\u0442\u0430",
    "numbers": "\u0427\u0438\u0441\u043b\u0430",
    "bonus": "\u0414\u043e\u043f\u044a\u043b\u043d\u0438\u0442\u0435\u043b\u043d\u043e",
    "year": "\u0413\u043e\u0434\u0438\u043d\u0430",
    "run": "\u041f\u0440\u043e\u0432\u0435\u0440\u0438 \u0444\u0438\u0448\u0430",
    "need_valid": "\u0412\u0441\u044f\u043a\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0442\u0440\u044f\u0431\u0432\u0430 \u0434\u0430 \u0438\u043c\u0430 \u0442\u043e\u0447\u043d\u043e 6 \u0447\u0438\u0441\u043b\u0430.",
    "no_complete_combo": "\u041f\u043e\u043f\u044a\u043b\u043d\u0438 \u043f\u043e\u043d\u0435 \u0435\u0434\u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0441 \u0442\u043e\u0447\u043d\u043e 6 \u0447\u0438\u0441\u043b\u0430.",
    "drawings": "\u0422\u0435\u0433\u043b\u0435\u043d\u0438\u044f",
    "checks": "\u041e\u0431\u0449\u043e \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438",
    "best": "\u041d\u0430\u0439-\u0434\u043e\u0431\u044a\u0440 \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442",
    "best_match": "\u041d\u0430\u0439-\u043c\u043d\u043e\u0433\u043e \u043f\u043e\u0437\u043d\u0430\u0442\u0438",
    "details": "\u041f\u043e\u043a\u0430\u0436\u0438 \u043f\u043e\u0434\u0440\u043e\u0431\u043d\u0430 \u0442\u0430\u0431\u043b\u0438\u0446\u0430",
    "my_numbers": "\u0422\u0432\u043e\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u0430",
    "drawn_numbers": "\u0418\u0437\u0442\u0435\u0433\u043b\u0435\u043d\u0438 \u0447\u0438\u0441\u043b\u0430",
    "matched_numbers": "\u041f\u043e\u0437\u043d\u0430\u0442\u0438 \u0447\u0438\u0441\u043b\u0430",
    "match_count": "\u0411\u0440\u043e\u0439 \u043f\u043e\u0437\u043d\u0430\u0442\u0438",
    "bonus_match": "\u041f\u043e\u0437\u043d\u0430\u0442\u043e \u0434\u043e\u043f\u044a\u043b\u043d\u0438\u0442\u0435\u043b\u043d\u043e",
    "result": "\u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442",
    "download_csv": "\u0421\u0432\u0430\u043b\u0438 CSV",
    "download_json": "\u0421\u0432\u0430\u043b\u0438 JSON",
    "missing_full_data": "\u0417\u0430 \u0442\u043e\u0437\u0438 \u0442\u0438\u0440\u0430\u0436 \u0438\u043c\u0430 \u0441\u0430\u043c\u043e \u043d\u0430\u043b\u0438\u0447\u043d\u043e\u0442\u043e \u0442\u0435\u0433\u043b\u0435\u043d\u0435. \u041f\u044a\u043b\u043d\u0438\u0442\u0435 \u0434\u0430\u043d\u043d\u0438 \u0449\u0435 \u0441\u0435 \u0434\u043e\u0431\u0430\u0432\u044f\u0442 \u0441\u043b\u0435\u0434 \u0438\u043c\u043f\u043e\u0440\u0442.",
    "error": "\u0413\u0440\u0435\u0448\u043a\u0430 \u043f\u0440\u0438 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430\u0442\u0430.",
}


def _rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def _load_checker() -> Any:
    spec = importlib.util.spec_from_file_location("v40_ticket_checker_runtime", TICKET_CHECKER_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(T["error"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _sync_ticket_tables(count: int) -> None:
    tables = st.session_state.get("v40_ticket_tables")
    if not isinstance(tables, list):
        tables = [[] for _ in range(count)]

    while len(tables) < count:
        tables.append([])

    if len(tables) > count:
        tables = tables[:count]

    st.session_state["v40_ticket_tables"] = tables


def _numbers_text(numbers: list[int]) -> str:
    return " ".join(str(x) for x in sorted(numbers)) if numbers else T["no_selected"]


def _toggle_number(table_index: int, number: int) -> None:
    tables = st.session_state["v40_ticket_tables"]
    current = set(int(x) for x in tables[table_index])

    if number in current:
        current.remove(number)
    elif len(current) < 6:
        current.add(number)

    tables[table_index] = sorted(current)
    st.session_state["v40_ticket_tables"] = tables
    st.session_state.pop("v40_ticket_results", None)
    _rerun()


def _clear_combo(table_index: int) -> None:
    tables = st.session_state["v40_ticket_tables"]
    tables[table_index] = []
    st.session_state["v40_ticket_tables"] = tables
    st.session_state.pop("v40_ticket_results", None)
    _rerun()


def _render_combo_card(table_index: int, numbers: list[int]) -> None:
    selected = set(int(x) for x in numbers)
    status = f"{len(selected)}/6"
    status_class = "complete" if len(selected) == 6 else "incomplete"

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="v40-combo-header {status_class}">
                <strong>{T['combo']} {table_index + 1}</strong>
                <span>{status}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for row_start in range(1, 50, 7):
            cols = st.columns(7, gap="small")
            for offset, number in enumerate(range(row_start, min(row_start + 7, 50))):
                is_selected = number in selected
                disabled = (not is_selected) and len(selected) >= 6
                label = "X" if is_selected else f"{number}"
                if cols[offset].button(
                    label,
                    key=f"v40_combo_{table_index}_{number}",
                    disabled=disabled,
                    use_container_width=False,
                ):
                    _toggle_number(table_index, number)

        st.markdown(
            f"""
            <div class="v40-selected-line">
                <strong>{T['selected']}:</strong> {_numbers_text(sorted(selected))}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            T["clear_combo"],
            key=f"v40_clear_combo_{table_index}",
            use_container_width=True,
        ):
            _clear_combo(table_index)


def _build_ticket_dataframe() -> tuple[pd.DataFrame, list[str]]:
    tables = st.session_state.get("v40_ticket_tables", [])
    rows = []
    errors = []

    for index, numbers in enumerate(tables, start=1):
        values = sorted(int(x) for x in numbers)

        # Real ticket behavior:
        # - 0/6 means empty combination, skip it
        # - 6/6 means valid combination, check it
        # - 1/6..5/6 means started but incomplete, warn the user
        if len(values) == 0:
            continue

        if len(values) != 6:
            errors.append(f"{T['combo']} {index}: {len(values)} / 6")
            continue

        rows.append(
            {
                "ticket_id": "visual_ticket",
                "ticket_table_no": index,
                "n1": values[0],
                "n2": values[1],
                "n3": values[2],
                "n4": values[3],
                "n5": values[4],
                "n6": values[5],
            }
        )

    return pd.DataFrame(rows), errors


def _ticket_builder() -> tuple[pd.DataFrame, list[str]]:
    st.markdown(f"## {T['step1']}")

    count = int(
        st.number_input(
            T["ticket_tables"],
            min_value=1,
            max_value=20,
            value=int(st.session_state.get("v40_ticket_table_count", 4)),
            step=1,
            key="v40_ticket_table_count",
        )
    )

    _sync_ticket_tables(count)

    a, b = st.columns(2)
    if a.button(T["load_demo"], key="v40_load_demo_ticket", use_container_width=True):
        st.session_state["v40_ticket_tables"] = [row[:] for row in DEMO_TICKET_TABLES]
        st.session_state["v40_ticket_table_count"] = len(DEMO_TICKET_TABLES)
        st.session_state.pop("v40_ticket_results", None)
        _rerun()

    if b.button(T["clear_all"], key="v40_clear_all_ticket", use_container_width=True):
        st.session_state["v40_ticket_tables"] = [[] for _ in range(count)]
        st.session_state.pop("v40_ticket_results", None)
        _rerun()

    tables = st.session_state["v40_ticket_tables"]

    for pair_start in range(0, len(tables), 2):
        cols = st.columns(2)
        for offset, table_index in enumerate(range(pair_start, min(pair_start + 2, len(tables)))):
            with cols[offset]:
                _render_combo_card(table_index, tables[table_index])

    return _build_ticket_dataframe()


def _combo(row: pd.Series) -> str:
    values = []
    for col in NUMBER_COLS:
        value = row.get(col, "")
        if pd.isna(value) or str(value).strip() == "":
            continue
        values.append(str(int(float(value))))
    return " ".join(values) if values else "\u2014"


def _draw_cards(draws: pd.DataFrame, is_demo: bool) -> None:
    if draws.empty:
        return

    for _, row in draws.iterrows():
        draw_label = T["demo_draw_name"] if is_demo else str(row.get("draw_number", ""))
        date_label = T["demo_date"] if is_demo else str(row.get("date", ""))
        drawing_label = str(int(float(row.get("drawing_no", 0))))
        numbers = _combo(row)
        bonus = str(row.get("bonus_number", "\u2014"))

        st.markdown(
            f"""
            <div class="v40-draw-card">
                <strong>{draw_label}</strong> ? {T['date']}: {date_label} ? {T['drawing']} {drawing_label}<br/>
                <span>{T['numbers']}: {numbers}</span><br/>
                <span>{T['bonus']}: {bonus}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _draw_input() -> tuple[pd.DataFrame, bool]:
    st.markdown(f"## {T['step2']}")

    source = st.radio(
        T["draw_source"],
        [T["sample_draw"], T["latest_draw"]],
        index=0,
        key="v40_draw_source",
    )

    if source == T["sample_draw"]:
        draws = _read_csv(SAMPLE_DRAW_EVENTS_PATH)
        _draw_cards(draws, is_demo=True)
        return draws, True

    draws = _read_csv(NORMALIZED_DRAW_EVENTS_PATH)

    if draws.empty:
        st.warning(T["missing_full_data"])
        return draws, False

    years = sorted([int(x) for x in draws["year"].dropna().unique()], reverse=True)
    year = st.selectbox(T["year"], years, index=0, key="v40_year")

    ydf = draws[draws["year"].astype(int) == int(year)].copy()
    draw_numbers = sorted([int(x) for x in ydf["draw_number"].dropna().unique()], reverse=True)

    draw_no = st.selectbox(T["draw"], draw_numbers, index=0, key="v40_draw_no")
    selected = ydf[ydf["draw_number"].astype(int) == int(draw_no)].copy()

    if len(selected) < 2:
        st.warning(T["missing_full_data"])

    _draw_cards(selected, is_demo=False)
    return selected, False


def _results_preview(df: pd.DataFrame, is_demo: bool) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    if is_demo and "draw_number" in out.columns:
        out["draw_number"] = T["demo_draw_name"]

    for col in ["chosen_numbers", "drawn_numbers", "bonus_number", "matched_numbers"]:
        if col in out.columns:
            out[col] = out[col].map(lambda value: str(value).strip() if str(value).strip() else "\u2014")

    if "bonus_match_bg" not in out.columns and "bonus_match" in out.columns:
        out["bonus_match_bg"] = out["bonus_match"].map(lambda x: "\u0434\u0430" if bool(x) else "\u043d\u0435")

    cols = [
        "ticket_table_no",
        "draw_number",
        "drawing_no",
        "chosen_numbers",
        "drawn_numbers",
        "bonus_number",
        "matched_numbers",
        "match_count",
        "bonus_match_bg",
        "result_label_bg",
    ]

    cols = [c for c in cols if c in out.columns]

    return out[cols].rename(
        columns={
            "ticket_table_no": T["combo"],
            "draw_number": T["draw"],
            "drawing_no": T["drawing"],
            "chosen_numbers": T["my_numbers"],
            "drawn_numbers": T["drawn_numbers"],
            "bonus_number": T["bonus"],
            "matched_numbers": T["matched_numbers"],
            "match_count": T["match_count"],
            "bonus_match_bg": T["bonus_match"],
            "result_label_bg": T["result"],
        }
    )


def _render_best_result(results: pd.DataFrame, is_demo: bool) -> None:
    if results.empty:
        return

    ranked = results.sort_values(
        by=["match_count", "bonus_match"],
        ascending=[False, False],
    ).head(3)

    st.markdown("### " + T["best"])

    for _, row in ranked.iterrows():
        draw_label = T["demo_draw_name"] if is_demo else str(row["draw_number"])
        bonus_text = "\u0434\u0430" if bool(row.get("bonus_match", False)) else "\u043d\u0435"

        st.markdown(
            f"""
            <div class="v40-result-card">
                <strong>{T['combo']} {int(row['ticket_table_no'])}</strong> ? {draw_label} ? {T['drawing']} {int(row['drawing_no'])}<br/>
                {T['match_count']}: <strong>{int(row['match_count'])}</strong> ? {T['matched_numbers']}: {row.get('matched_numbers') or "\u2014"} ? {T['bonus_match']}: {bonus_text}<br/>
                <span>{row.get('result_label_bg', '')}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_results(tickets: pd.DataFrame, draws: pd.DataFrame, results: pd.DataFrame, is_demo: bool) -> None:
    st.markdown(f"## {T['step3']}")

    tables = int(tickets["ticket_table_no"].nunique()) if "ticket_table_no" in tickets.columns else len(tickets)
    draw_count = int(len(draws))
    total = int(len(results))
    best = int(results["match_count"].max()) if not results.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(T["ticket_tables"], tables)
    c2.metric(T["drawings"], draw_count)
    c3.metric(T["checks"], total)
    c4.metric(T["best_match"], best)

    _render_best_result(results, is_demo)

    with st.expander(T["details"], expanded=False):
        st.dataframe(_results_preview(results, is_demo), use_container_width=True, hide_index=True)

    csv_data = results.to_csv(index=False).encode("utf-8-sig")
    json_data = json.dumps(results.to_dict(orient="records"), ensure_ascii=False, indent=2).encode("utf-8")

    d1, d2 = st.columns(2)
    d1.download_button(T["download_csv"], data=csv_data, file_name="ticket_check_result.csv", mime="text/csv")
    d2.download_button(T["download_json"], data=json_data, file_name="ticket_check_result.json", mime="application/json")


def render_ticket_checker_page() -> None:
    st.markdown(
        """
        <style>
        .v40-ticket-hero, .v40-ticket-note, .v40-result-card, .v40-draw-card {
            border: 1px solid rgba(212, 175, 55, 0.38);
            background: rgba(212, 175, 55, 0.08);
            border-radius: 14px;
            padding: 12px 14px;
            margin: 10px 0;
        }
        .v40-combo-header {
            border: 1px solid rgba(212, 175, 55, 0.58);
            background: linear-gradient(90deg, rgba(212, 175, 55, 0.12), rgba(100, 42, 90, 0.18));
            border-radius: 12px;
            padding: 8px 12px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #f3df9a;
        }
        .v40-combo-header.complete {
            border-color: rgba(92, 214, 148, 0.72);
            color: #9ff0c1;
        }
        .v40-combo-header.incomplete {
            border-color: rgba(212, 175, 55, 0.58);
        }
        .v40-selected-line {
            border: 1px solid rgba(212, 175, 55, 0.38);
            background: rgba(212, 175, 55, 0.06);
            border-radius: 10px;
            padding: 8px 10px;
            margin: 10px 0 8px;
        }
        .v40-result-card {
            background: rgba(255,255,255,0.035);
        }
        .v40-draw-card {
            background: rgba(255,255,255,0.035);
        }
        
        div[data-testid="stButton"] button {
            white-space: nowrap !important;
            min-height: 38px;
        }
        div[data-testid="stButton"] button p {
            white-space: nowrap !important;
            line-height: 1 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("\U0001F3AB " + T["title"])
    st.markdown(f"<div class='v40-ticket-hero'>{T['hero']}</div>", unsafe_allow_html=True)

    with st.expander(T["how"], expanded=False):
        st.markdown(T["how_text"])

    st.markdown(f"<div class='v40-ticket-note'>{T['note']}</div>", unsafe_allow_html=True)

    tickets, errors = _ticket_builder()

    st.divider()

    draws, is_demo = _draw_input()


    st.divider()

    can_check = (not errors) and (not draws.empty) and (not tickets.empty)

    if tickets.empty:
        st.info(T["no_complete_combo"])

    if errors:
        for error in errors:
            st.warning(error)
        st.info(T["need_valid"])

    if draws.empty:
        st.warning(T["missing_full_data"])

    if not can_check:
        st.session_state.pop("v40_ticket_results", None)

    if st.button(
        T["run"],
        key="v40_run_ticket_check",
        type="primary",
        use_container_width=True,
        disabled=not can_check,
    ):
        try:
            checker = _load_checker()
            results = checker.check_ticket_against_draws(tickets, draws)
            st.session_state["v40_ticket_results"] = results
            st.session_state["v40_ticket_results_is_demo"] = is_demo
        except Exception as exc:
            st.error(T["error"])
            st.exception(exc)
            return

    results = st.session_state.get("v40_ticket_results")
    if isinstance(results, pd.DataFrame):
        _render_results(
            tickets,
            draws,
            results,
            bool(st.session_state.get("v40_ticket_results_is_demo", is_demo)),
        )

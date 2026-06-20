from __future__ import annotations

import csv
import json
import math
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "historical_draws.csv"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
TOTAL_NUMBERS = 49
DRAW_SIZE = 6
TOTAL_COMBINATIONS = math.comb(TOTAL_NUMBERS, DRAW_SIZE)
EXPECTED_NUMBER_PROBABILITY = DRAW_SIZE / TOTAL_NUMBERS


st.set_page_config(
    page_title="Lottery Probability Model",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    :root {
        --bg: #090b10;
        --panel: rgba(20, 24, 33, 0.92);
        --panel-soft: rgba(29, 34, 47, 0.88);
        --gold: #d7b46a;
        --gold-soft: rgba(215, 180, 106, 0.18);
        --text: #f4efe2;
        --muted: #a8adba;
        --line: rgba(215, 180, 106, 0.22);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(215, 180, 106, 0.15), transparent 34rem),
            radial-gradient(circle at bottom right, rgba(79, 95, 130, 0.20), transparent 42rem),
            linear-gradient(135deg, #07090d 0%, #10131b 52%, #090b10 100%);
        color: var(--text);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(11, 13, 19, 0.98), rgba(16, 20, 29, 0.98));
        border-right: 1px solid var(--line);
    }

    h1, h2, h3 {
        letter-spacing: -0.02em;
    }

    .hero {
        padding: 2rem 2rem 1.75rem;
        border: 1px solid var(--line);
        border-radius: 28px;
        background:
            linear-gradient(135deg, rgba(215, 180, 106, 0.14), rgba(255, 255, 255, 0.03)),
            rgba(13, 16, 24, 0.92);
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.38);
        margin-bottom: 1.3rem;
    }

    .hero-kicker {
        color: var(--gold);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.22em;
        margin-bottom: 0.45rem;
    }

    .hero-title {
        font-size: clamp(2.05rem, 4vw, 4.2rem);
        line-height: 0.95;
        font-weight: 850;
        color: #fff8e8;
        margin: 0;
    }

    .hero-text {
        color: var(--muted);
        font-size: 1.03rem;
        max-width: 880px;
        margin-top: 1rem;
    }

    .warning-note {
        border: 1px solid rgba(215, 180, 106, 0.32);
        border-left: 5px solid var(--gold);
        background: rgba(215, 180, 106, 0.10);
        padding: 1rem 1.1rem;
        border-radius: 18px;
        color: #f6e7c0;
        margin: 1rem 0 1.3rem;
    }

    .metric-card {
        padding: 1.1rem 1.1rem;
        border: 1px solid var(--line);
        border-radius: 22px;
        background: var(--panel);
        min-height: 118px;
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.25);
    }

    .metric-label {
        color: var(--muted);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.35rem;
    }

    .metric-value {
        color: #fff8e8;
        font-size: 1.85rem;
        font-weight: 780;
        line-height: 1;
    }

    .metric-help {
        color: var(--muted);
        font-size: 0.86rem;
        margin-top: 0.45rem;
    }

    .ticket-card {
        border: 1px solid var(--line);
        border-radius: 24px;
        padding: 1.15rem;
        background: var(--panel);
        margin-bottom: 0.9rem;
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.22);
    }

    .ticket-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.85rem;
    }

    .ticket-rank {
        color: var(--gold);
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.82rem;
    }

    .ticket-confidence {
        color: #fff8e8;
        font-weight: 700;
        font-size: 0.96rem;
    }

    .balls {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin: 0.6rem 0 0.8rem;
    }

    .ball {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: #14100a;
        background: radial-gradient(circle at 30% 25%, #fff4c4, #d7b46a 55%, #8f692c 100%);
        border: 1px solid rgba(255, 243, 194, 0.50);
        box-shadow: 0 8px 22px rgba(0,0,0,0.35), inset 0 2px 6px rgba(255,255,255,0.35);
        font-weight: 850;
    }

    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.6rem;
    }

    .pill {
        border: 1px solid rgba(215, 180, 106, 0.24);
        background: rgba(215, 180, 106, 0.09);
        color: #ead7a2;
        padding: 0.28rem 0.6rem;
        border-radius: 999px;
        font-size: 0.78rem;
    }

    .section-card {
        border: 1px solid var(--line);
        border-radius: 24px;
        padding: 1.2rem;
        background: var(--panel-soft);
        margin-bottom: 1rem;
    }

    div[data-testid="stMetricValue"] {
        color: #fff8e8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(show_spinner=False)
def load_draws() -> list[dict[str, Any]]:
    if not DATA_PATH.exists():
        return []

    rows: list[dict[str, Any]] = []
    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            numbers = [int(row[f"n{i}"]) for i in range(1, 7)]
            rows.append(
                {
                    "year": int(row["year"]),
                    "draw_number": int(row["draw_number"]),
                    "draw_position": int(row.get("draw_position") or 1),
                    "numbers": numbers,
                    "sum": sum(numbers),
                }
            )
    return rows


@st.cache_data(show_spinner=False)
def load_models() -> dict[str, dict[str, Any]]:
    return {
        "frequency": load_json(MODELS_DIR / "lottery_frequency_model.json"),
        "cold": load_json(MODELS_DIR / "lottery_cold_model.json"),
        "middle": load_json(MODELS_DIR / "lottery_middle_model.json"),
        "gap": load_json(MODELS_DIR / "lottery_gap_model.json"),
        "combined": load_json(MODELS_DIR / "lottery_combined_model.json"),
    }


def draw_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "min_year": None,
            "max_year": None,
            "missing": [],
            "unique_full_rows": 0,
            "duplicate_full_rows": 0,
            "duplicate_draw_keys": 0,
        }

    years = Counter(row["year"] for row in rows)
    missing = [year for year in range(1958, 2026) if year not in years]
    full_keys = Counter(
        (
            row["year"],
            row["draw_number"],
            row["draw_position"],
            tuple(row["numbers"]),
        )
        for row in rows
    )
    draw_keys = Counter(
        (row["year"], row["draw_number"], row["draw_position"])
        for row in rows
    )

    return {
        "rows": len(rows),
        "min_year": min(years),
        "max_year": max(years),
        "missing": missing,
        "unique_full_rows": len(full_keys),
        "duplicate_full_rows": sum(1 for value in full_keys.values() if value > 1),
        "duplicate_draw_keys": sum(1 for value in draw_keys.values() if value > 1),
        "year_counts": dict(sorted(years.items())),
    }


def format_percent(value: float | int | None, *, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.{digits}f}%"


def ticket_html(numbers: list[int]) -> str:
    balls = "".join(f"<span class='ball'>{number}</span>" for number in numbers)
    return f"<div class='balls'>{balls}</div>"


def metric_card(label: str, value: str, help_text: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def combined_card(item: dict[str, Any], fallback_rank: int) -> None:
    numbers = item.get("numbers") or item.get("combination") or item.get("ticket") or []
    rank = item.get("relative_rank") or fallback_rank
    confidence = float(item.get("confidence_score") or item.get("final_score", 0) * 100)
    relative_probability = item.get("relative_model_probability")
    top_percent = item.get("relative_top_percent")
    sub_scores = item.get("sub_scores", {})
    structure = item.get("structure_details", {})

    st.markdown(
        f"""
        <div class="ticket-card">
            <div class="ticket-header">
                <div class="ticket-rank">Rank {rank}</div>
                <div class="ticket-confidence">Confidence {confidence:.2f}/100</div>
            </div>
            {ticket_html(numbers)}
            <div class="pill-row">
                <span class="pill">Model probability: {format_percent(relative_probability, digits=6)}</span>
                <span class="pill">Top: {top_percent:.3f}%</span>
                <span class="pill">Real jackpot odds: 1 in 13,983,816</span>
                <span class="pill">Sum: {structure.get('sum', sum(numbers) if numbers else 'n/a')}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Score details", expanded=False):
        if sub_scores:
            sub_df = pd.DataFrame(
                [{"signal": key.replace("_", " "), "score": value} for key, value in sub_scores.items()]
            )
            st.dataframe(sub_df, hide_index=True, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            st.json(item.get("pair_details", {}), expanded=False)
        with col2:
            st.json(item.get("triple_details", {}), expanded=False)


def model_numbers_table(model: dict[str, Any], score_key: str) -> pd.DataFrame:
    records = []
    for item in model.get("scored_numbers", [])[:20]:
        records.append(
            {
                "number": item.get("number"),
                "score": item.get(score_key),
                "empirical %": round(float(item.get("empirical_probability", 0)) * 100, 3),
                "expected %": round(float(item.get("theoretical_probability", item.get("baseline_probability", EXPECTED_NUMBER_PROBABILITY))) * 100, 3),
                "gap": item.get("recency_gap") or item.get("current_gap"),
                "status": item.get("status") or item.get("cold_status") or item.get("middle_status") or item.get("interval_status"),
            }
        )
    return pd.DataFrame(records)


def calculate_match_probabilities() -> pd.DataFrame:
    records = []
    for matches in range(DRAW_SIZE + 1):
        favorable = math.comb(DRAW_SIZE, matches) * math.comb(TOTAL_NUMBERS - DRAW_SIZE, DRAW_SIZE - matches)
        probability = favorable / TOTAL_COMBINATIONS
        odds = f"1 in {round(1 / probability):,}" if probability > 0 else "n/a"
        records.append(
            {
                "matches": matches,
                "probability %": probability * 100,
                "odds": odds,
            }
        )
    return pd.DataFrame(records)


def historical_number_stats(rows: list[dict[str, Any]]) -> pd.DataFrame:
    counts = Counter(number for row in rows for number in row["numbers"])
    total_draws = len(rows)
    latest_index: dict[int, int] = {}
    for index, row in enumerate(rows):
        for number in row["numbers"]:
            latest_index[number] = index

    records = []
    for number in range(1, 50):
        count = counts[number]
        empirical = count / total_draws if total_draws else 0
        gap = total_draws - 1 - latest_index.get(number, -1) if total_draws else None
        records.append(
            {
                "number": number,
                "times drawn": count,
                "empirical %": round(empirical * 100, 3),
                "expected %": round(EXPECTED_NUMBER_PROBABILITY * 100, 3),
                "difference %": round((empirical - EXPECTED_NUMBER_PROBABILITY) * 100, 3),
                "current gap": gap,
            }
        )
    return pd.DataFrame(records)


def show_dashboard(rows: list[dict[str, Any]], models: dict[str, dict[str, Any]]) -> None:
    summary = draw_summary(rows)
    combined = models["combined"]
    recommendations = combined.get("recommended_combinations", [])
    top = recommendations[0] if recommendations else {}

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">Bulgarian Toto 2 · 6/49 · Statistical Training App</div>
            <h1 class="hero-title">Lottery Probability Model</h1>
            <div class="hero-text">
                Visual dashboard for mathematical probability, official historical draws, statistical model signals,
                and final combined ranking. This is an analytical project, not a guaranteed prediction system.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="warning-note">
            Important: every exact 6-number combination still has the same fair jackpot odds: <b>1 in 13,983,816</b>.
            The model confidence is only a relative statistical score among generated candidates.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Historical draws", f"{summary['rows']:,}", "Clean records used for training")
    with col2:
        metric_card("Year range", f"{summary['min_year']}–{summary['max_year']}", f"Missing years: {len(summary['missing'])}")
    with col3:
        metric_card("Real jackpot odds", "1 in 13.98M", "Unchanged fair probability")
    with col4:
        confidence = top.get("confidence_score")
        metric_card("Top confidence", f"{confidence:.2f}/100" if confidence else "n/a", "Relative model score")

    st.markdown("### Best combined recommendation")
    if top:
        combined_card(top, 1)
    else:
        st.info("Run `python train_combined_model.py` to generate combined recommendations.")

    with st.expander("Dataset quality audit", expanded=False):
        st.write(
            {
                "rows": summary["rows"],
                "missing_years": summary["missing"],
                "unique_full_rows": summary["unique_full_rows"],
                "duplicate_full_rows": summary["duplicate_full_rows"],
                "duplicate_year_draw_position_keys": summary["duplicate_draw_keys"],
            }
        )
        year_df = pd.DataFrame(
            [{"year": year, "draws": count} for year, count in summary.get("year_counts", {}).items()]
        )
        st.bar_chart(year_df.set_index("year"))


def show_recommendations(models: dict[str, dict[str, Any]]) -> None:
    st.header("Final Combined Strategy")
    combined = models["combined"]
    recommendations = combined.get("recommended_combinations", [])

    if not combined:
        st.warning("Combined model file not found. Run `python train_combined_model.py` first.")
        return

    st.markdown(
        f"""
        <div class="section-card">
            <b>{combined.get('model_name', 'Final Combined Prediction Strategy Model')}</b><br>
            Training draws: <b>{combined.get('training_draws', 'unknown')}</b> ·
            Candidate combinations: <b>{combined.get('candidate_count', 'unknown')}</b> ·
            Real jackpot odds: <b>{combined.get('theoretical_jackpot_odds', '1 in 13983816')}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for index, item in enumerate(recommendations, start=1):
        combined_card(item, index)


def show_model_explorer(models: dict[str, dict[str, Any]]) -> None:
    st.header("Model Explorer")
    tab1, tab2, tab3, tab4 = st.tabs(["Hot / Frequency", "Cold + Gap", "Middle / Balanced", "Gap / Interval"])

    with tab1:
        model = models["frequency"]
        st.subheader(model.get("model_name", "Historical Frequency Probability Model"))
        if model:
            st.markdown(ticket_html(model.get("recommended_ticket", [])), unsafe_allow_html=True)
            st.dataframe(model_numbers_table(model, "model_score"), hide_index=True, use_container_width=True)
        else:
            st.info("Run `python train_model.py` first.")

    with tab2:
        model = models["cold"]
        st.subheader(model.get("model_name", "Cold + Gap-Aware Numbers Model"))
        if model:
            st.markdown(ticket_html(model.get("recommended_ticket", [])), unsafe_allow_html=True)
            st.dataframe(model_numbers_table(model, "cold_model_score"), hide_index=True, use_container_width=True)
        else:
            st.info("Run `python train_cold_model.py` first.")

    with tab3:
        model = models["middle"]
        st.subheader(model.get("model_name", "Middle / Balanced Numbers Model"))
        if model:
            st.markdown(ticket_html(model.get("recommended_ticket", [])), unsafe_allow_html=True)
            st.dataframe(model_numbers_table(model, "middle_model_score"), hide_index=True, use_container_width=True)
        else:
            st.info("Run `python train_middle_model.py` first.")

    with tab4:
        model = models["gap"]
        st.subheader(model.get("model_name", "Gap / Interval Next-Draw Probability Model"))
        if model:
            st.markdown(ticket_html(model.get("recommended_ticket", [])), unsafe_allow_html=True)
            st.dataframe(model_numbers_table(model, "combined_next_probability"), hide_index=True, use_container_width=True)
        else:
            st.info("Run `python train_gap_model.py` first.")


def show_historical(rows: list[dict[str, Any]]) -> None:
    st.header("Historical Statistics")
    if not rows:
        st.error("No historical data found in data/historical_draws.csv")
        return

    stats = historical_number_stats(rows)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Most frequent numbers")
        st.dataframe(stats.sort_values("times drawn", ascending=False).head(12), hide_index=True, use_container_width=True)
    with col2:
        st.subheader("Least frequent numbers")
        st.dataframe(stats.sort_values("times drawn", ascending=True).head(12), hide_index=True, use_container_width=True)

    st.subheader("Number frequency chart")
    chart_df = stats[["number", "times drawn"]].set_index("number")
    st.bar_chart(chart_df)

    st.subheader("Full number table")
    st.dataframe(stats, hide_index=True, use_container_width=True)


def show_probability_lab(models: dict[str, dict[str, Any]]) -> None:
    st.header("Probability Lab")
    st.markdown(
        "Choose a ticket and compare exact mathematical odds with model ranking context. "
        "This section does not change the fair lottery probability."
    )

    selected = st.multiselect(
        "Choose 6 numbers",
        options=list(range(1, 50)),
        default=[10, 14, 23, 27, 33, 36],
        max_selections=6,
    )

    if len(selected) == 6:
        numbers = sorted(selected)
        st.markdown(ticket_html(numbers), unsafe_allow_html=True)
        st.success(f"Ticket selected: {numbers}")
    else:
        st.warning("Select exactly 6 numbers.")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total combinations", f"{TOTAL_COMBINATIONS:,}")
        st.metric("Exact jackpot probability", f"{(1 / TOTAL_COMBINATIONS) * 100:.10f}%")
    with col2:
        st.metric("Jackpot odds", "1 in 13,983,816")
        st.metric("Single number baseline", f"{EXPECTED_NUMBER_PROBABILITY * 100:.2f}%")

    st.subheader("Exact match probabilities")
    probability_df = calculate_match_probabilities()
    st.dataframe(probability_df, hide_index=True, use_container_width=True)


def show_reports() -> None:
    st.header("Reports")

    if not REPORTS_DIR.exists():
        st.info("No reports folder found.")
        return

    report_files = sorted(REPORTS_DIR.glob("*.md"))
    if not report_files:
        st.info("No markdown reports found.")
        return

    report_rows = [
        {
            "file": path.name,
            "size_kb": round(path.stat().st_size / 1024, 1),
            "modified": path.stat().st_mtime,
        }
        for path in report_files
    ]

    st.caption(
        "Safe report viewer: reports are not rendered all at once, because large Markdown reports can freeze the browser."
    )

    with st.expander("Available reports", expanded=False):
        table = pd.DataFrame(report_rows).drop(columns=["modified"])
        st.dataframe(table, hide_index=True, use_container_width=True)

    selected = st.selectbox("Choose report", report_files, format_func=lambda path: path.name)

    selected_size_kb = selected.stat().st_size / 1024
    st.write(f"Selected file: `{selected.name}` · {selected_size_kb:.1f} KB")

    text = selected.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Report lines", f"{len(lines):,}")
    with col2:
        st.metric("Report size", f"{selected_size_kb:.1f} KB")
    with col3:
        st.metric("Preview mode", "Safe")

    max_lines = st.slider(
        "Preview first lines",
        min_value=50,
        max_value=min(max(len(lines), 50), 1000),
        value=min(250, max(len(lines), 50)),
        step=50,
    )

    preview = "\n".join(lines[:max_lines])

    st.download_button(
        "Download selected report",
        data=text.encode("utf-8"),
        file_name=selected.name,
        mime="text/markdown",
    )

    render_as_markdown = st.checkbox(
        "Render preview as Markdown",
        value=False,
        help="Keep this off for very large reports. Text preview is faster and safer.",
    )

    if render_as_markdown:
        st.markdown(preview)
    else:
        st.text_area("Report preview", preview, height=520)

    if len(lines) > max_lines:
        st.info(
            f"Showing {max_lines:,} of {len(lines):,} lines. Use the download button to open the full report."
        )


def _read_historical_csv_rows() -> tuple[list[str], list[dict[str, str]]]:
    """Read the historical draws CSV while preserving the existing columns."""
    if not DATA_PATH.exists():
        default_fields = [
            "draw_id",
            "date",
            "n1",
            "n2",
            "n3",
            "n4",
            "n5",
            "n6",
            "year",
            "draw_number",
            "draw_position",
            "source_url",
        ]
        return default_fields, []

    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]

    required_fields = [
        "draw_id",
        "date",
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
        "n6",
        "year",
        "draw_number",
        "draw_position",
        "source_url",
    ]

    for field in required_fields:
        if field not in fieldnames:
            fieldnames.append(field)
            for row in rows:
                row[field] = ""

    return fieldnames, rows


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _next_draw_id(rows: list[dict[str, str]]) -> int:
    if not rows:
        return 1
    return max(_safe_int(row.get("draw_id"), 0) for row in rows) + 1


def _next_draw_number_for_year(rows: list[dict[str, str]], year: int) -> int:
    year_draws = [_safe_int(row.get("draw_number"), 0) for row in rows if _safe_int(row.get("year"), 0) == year]
    if not year_draws:
        return 1
    return max(year_draws) + 1


def _backup_historical_csv() -> Path | None:
    if not DATA_PATH.exists():
        return None

    from datetime import datetime
    import shutil

    backup_dir = DATA_PATH.parent / "manual_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"historical_draws_before_manual_entry_{timestamp}.csv"
    shutil.copy2(DATA_PATH, backup_path)
    return backup_path


def _write_historical_csv(fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _append_manual_entry_log(new_row: dict[str, str]) -> None:
    from datetime import datetime

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = REPORTS_DIR / "manual_draw_entries.md"
    line = (
        f"- {datetime.now().isoformat(timespec='seconds')} | "
        f"year={new_row['year']} draw={new_row['draw_number']} position={new_row['draw_position']} | "
        f"numbers={new_row['n1']}, {new_row['n2']}, {new_row['n3']}, {new_row['n4']}, {new_row['n5']}, {new_row['n6']}\n"
    )

    if not log_path.exists():
        log_path.write_text("# Manual Draw Entries\n\n", encoding="utf-8")

    with log_path.open("a", encoding="utf-8") as file:
        file.write(line)


def show_update_draws() -> None:
    """Manual data entry page for newly published winning draws."""
    from datetime import date

    st.header("Update Draws")
    st.markdown(
        "Add a newly published winning combination to `data/historical_draws.csv`. "
        "After saving, retrain the models so the recommendations use the new draw."
    )

    st.markdown(
        """
        <div class="warning-note">
            Use this only for official winning numbers. The app validates range, uniqueness, and duplicate draw keys,
            but it cannot verify the result against the official source automatically.
        </div>
        """,
        unsafe_allow_html=True,
    )

    fieldnames, csv_rows = _read_historical_csv_rows()
    loaded_rows = load_draws()
    summary = draw_summary(loaded_rows)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Current rows", f"{summary['rows']:,}", "Before manual append")
    with col2:
        metric_card("Year range", f"{summary['min_year']}–{summary['max_year']}", "Current dataset")
    with col3:
        metric_card("Duplicate keys", str(summary["duplicate_draw_keys"]), "Should be 0")
    with col4:
        metric_card("Missing 1958–2025", str(len(summary["missing"])), "Should be 0")

    today = date.today()
    default_year = today.year
    default_draw_number = _next_draw_number_for_year(csv_rows, default_year)

    st.subheader("New winning draw")

    with st.form("manual_draw_entry_form", clear_on_submit=False):
        meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)

        with meta_col1:
            draw_date = st.date_input("Draw date", value=today)
        with meta_col2:
            year = st.number_input("Year", min_value=1958, max_value=2100, value=int(draw_date.year), step=1)
        with meta_col3:
            draw_number = st.number_input("Draw number / tirage", min_value=0, max_value=9999, value=int(default_draw_number), step=1)
        with meta_col4:
            draw_position = st.number_input("Draw position", min_value=1, max_value=10, value=1, step=1)

        st.caption("Enter the six winning numbers. They will be sorted before saving.")
        number_cols = st.columns(6)
        entered_numbers: list[int] = []
        defaults = [1, 2, 3, 4, 5, 6]
        for index, column in enumerate(number_cols, start=1):
            with column:
                entered_numbers.append(
                    int(st.number_input(f"N{index}", min_value=1, max_value=49, value=defaults[index - 1], step=1))
                )

        source_note = st.text_input(
            "Source note / URL",
            value="manual:official_result",
            help="Optional note such as official URL, draw page, or 'manual:official_result'.",
        )

        submitted = st.form_submit_button("Save new draw")

    if submitted:
        numbers = sorted(entered_numbers)
        errors: list[str] = []

        if len(numbers) != 6:
            errors.append("Exactly six numbers are required.")
        if len(set(numbers)) != 6:
            errors.append("The six numbers must be unique.")
        if any(number < 1 or number > 49 for number in numbers):
            errors.append("All numbers must be between 1 and 49.")

        draw_key = (str(int(year)), str(int(draw_number)), str(int(draw_position)))
        existing_draw_keys = {
            (
                str(_safe_int(row.get("year"), 0)),
                str(_safe_int(row.get("draw_number"), 0)),
                str(_safe_int(row.get("draw_position"), 1)),
            )
            for row in csv_rows
        }

        existing_full_rows = {
            (
                str(_safe_int(row.get("year"), 0)),
                str(_safe_int(row.get("draw_number"), 0)),
                str(_safe_int(row.get("draw_position"), 1)),
                tuple(_safe_int(row.get(f"n{i}"), 0) for i in range(1, 7)),
            )
            for row in csv_rows
        }

        new_full_key = (draw_key[0], draw_key[1], draw_key[2], tuple(numbers))

        if draw_key in existing_draw_keys:
            errors.append(
                f"A row already exists for year={draw_key[0]}, draw={draw_key[1]}, position={draw_key[2]}. "
                "Use another draw position only if the official draw has multiple positions."
            )

        if new_full_key in existing_full_rows:
            errors.append("This exact row already exists in the dataset.")

        if errors:
            for error in errors:
                st.error(error)
        else:
            new_row = {field: "" for field in fieldnames}
            new_row.update(
                {
                    "draw_id": str(_next_draw_id(csv_rows)),
                    "date": draw_date.isoformat(),
                    "year": str(int(year)),
                    "draw_number": str(int(draw_number)),
                    "draw_position": str(int(draw_position)),
                    "source_url": source_note.strip() or "manual:official_result",
                }
            )

            for index, number in enumerate(numbers, start=1):
                new_row[f"n{index}"] = str(number)

            backup_path = _backup_historical_csv()
            csv_rows.append(new_row)
            _write_historical_csv(fieldnames, csv_rows)
            _append_manual_entry_log(new_row)

            load_draws.clear()
            load_models.clear()

            st.success(f"Saved new draw: {numbers}")
            if backup_path is not None:
                st.caption(f"Backup created: `{backup_path}`")
            st.info("Now retrain the models from the terminal, then refresh the app.")

    st.subheader("Retrain after adding a draw")
    st.code(
        "python train_model.py\n"
        "python train_cold_model.py\n"
        "python train_middle_model.py\n"
        "python train_gap_model.py\n"
        "python train_combined_model.py\n"
        "python -m streamlit run streamlit_app.py",
        language="powershell",
    )

    st.subheader("Latest saved rows")
    if csv_rows:
        preview_rows = []
        for row in csv_rows[-12:]:
            preview_rows.append(
                {
                    "draw_id": row.get("draw_id"),
                    "date": row.get("date"),
                    "year": row.get("year"),
                    "draw": row.get("draw_number"),
                    "position": row.get("draw_position"),
                    "numbers": " ".join(row.get(f"n{i}", "") for i in range(1, 7)),
                    "source": row.get("source_url", ""),
                }
            )
        st.dataframe(pd.DataFrame(preview_rows), hide_index=True, use_container_width=True)
    else:
        st.info("No rows yet.")


rows = load_draws()
models = load_models()

with st.sidebar:
    st.markdown("## 🎯 Lottery App")
    st.caption("Statistical analysis for Bulgarian Toto 2 – 6/49")
    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Combined Recommendations",
            "Model Explorer",
            "Historical Statistics",
            "Probability Lab",
            "Reports",
        ],
    )
    st.divider()
    st.caption("Run from project root:")
    st.code("python -m streamlit run streamlit_app.py", language="powershell")

if page == "Dashboard":
    show_dashboard(rows, models)
elif page == "Combined Recommendations":
    show_recommendations(models)
elif page == "Model Explorer":
    show_model_explorer(models)
elif page == "Historical Statistics":
    show_historical(rows)
elif page == "Probability Lab":
    show_probability_lab(models)
elif page == "Update Draws":
    show_update_draws()
elif page == "Reports":
    show_reports()

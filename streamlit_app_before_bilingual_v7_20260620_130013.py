from __future__ import annotations

import csv
import json
import math
import shutil
from datetime import date
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



def get_scored_number(model: dict[str, Any], number: int) -> dict[str, Any]:
    for item in model.get("scored_numbers", []):
        if int(item.get("number", -1)) == int(number):
            return item
    return {}


def max_model_value(model: dict[str, Any], key: str, default: float = 1.0) -> float:
    values = []
    for item in model.get("scored_numbers", []):
        try:
            values.append(float(item.get(key, 0)))
        except (TypeError, ValueError):
            continue
    return max(values) if values else default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def classify_frequency_signal(item: dict[str, Any]) -> str:
    z_score = safe_float(item.get("z_score"))
    if z_score >= 1.0:
        return "HOT"
    if z_score <= -1.0:
        return "COLD_FREQ"
    return "NORMAL"


def ticket_structure_analysis(numbers: list[int]) -> dict[str, Any]:
    numbers = sorted(numbers)
    ticket_sum = sum(numbers)
    even_count = sum(1 for number in numbers if number % 2 == 0)
    odd_count = len(numbers) - even_count
    low_count = sum(1 for number in numbers if number <= 24)
    high_count = len(numbers) - low_count
    consecutive_pairs = sum(1 for left, right in zip(numbers, numbers[1:]) if right - left == 1)
    decade_buckets = Counter(number // 10 for number in numbers)
    last_digit_counts = Counter(number % 10 for number in numbers)

    # Broad, transparent structure score. It rewards combinations that are not too extreme.
    sum_score = max(0.0, 1.0 - abs(ticket_sum - 150) / 110)
    even_odd_score = 1.0 - abs(even_count - 3) / 3
    low_high_score = 1.0 - abs(low_count - 3) / 3
    consecutive_score = max(0.0, 1.0 - consecutive_pairs * 0.25)
    bucket_score = min(1.0, len(decade_buckets) / 4)
    last_digit_score = max(0.0, 1.0 - max(last_digit_counts.values()) * 0.14)

    structure_score = (
        0.22 * sum_score
        + 0.18 * even_odd_score
        + 0.18 * low_high_score
        + 0.14 * consecutive_score
        + 0.14 * bucket_score
        + 0.14 * last_digit_score
    )

    return {
        "sum": ticket_sum,
        "even_count": even_count,
        "odd_count": odd_count,
        "low_count": low_count,
        "high_count": high_count,
        "consecutive_pairs": consecutive_pairs,
        "used_decade_buckets": len(decade_buckets),
        "max_same_last_digit_count": max(last_digit_counts.values()),
        "sum_score": sum_score,
        "even_odd_score": even_odd_score,
        "low_high_score": low_high_score,
        "consecutive_score": consecutive_score,
        "bucket_score": bucket_score,
        "last_digit_score": last_digit_score,
        "structure_score": structure_score,
    }


def pair_and_triple_support(numbers: list[int], rows: list[dict[str, Any]]) -> dict[str, Any]:
    pair_counts: Counter[tuple[int, int]] = Counter()
    triple_counts: Counter[tuple[int, int, int]] = Counter()

    for row in rows:
        draw_numbers = sorted(row["numbers"])
        pair_counts.update(combinations(draw_numbers, 2))
        triple_counts.update(combinations(draw_numbers, 3))

    ticket_pairs = list(combinations(sorted(numbers), 2))
    ticket_triples = list(combinations(sorted(numbers), 3))

    pair_values = [pair_counts[pair] for pair in ticket_pairs]
    triple_values = [triple_counts[triple] for triple in ticket_triples]
    max_pair = max(pair_counts.values()) if pair_counts else 1
    max_triple = max(triple_counts.values()) if triple_counts else 1

    strong_pairs = sorted(
        [{"pair": list(pair), "count": pair_counts[pair]} for pair in ticket_pairs],
        key=lambda item: item["count"],
        reverse=True,
    )[:5]
    strong_triples = sorted(
        [{"triple": list(triple), "count": triple_counts[triple]} for triple in ticket_triples],
        key=lambda item: item["count"],
        reverse=True,
    )[:5]

    return {
        "pair_score": (sum(pair_values) / len(pair_values)) / max_pair if pair_values else 0,
        "triple_score": (sum(triple_values) / len(triple_values)) / max_triple if triple_values else 0,
        "pair_total_support": sum(pair_values),
        "pair_average_support": sum(pair_values) / len(pair_values) if pair_values else 0,
        "triple_total_support": sum(triple_values),
        "strong_pairs": strong_pairs,
        "strong_triples": strong_triples,
    }


def rolling_ticket_score(numbers: list[int], rows: list[dict[str, Any]], window: int = 20) -> dict[str, Any]:
    recent_rows = rows[-window:] if len(rows) >= window else rows
    if not recent_rows:
        return {"rolling_score": 0.0, "recent_hits": 0, "recent_rate": 0.0}

    selected = set(numbers)
    recent_hits = sum(1 for row in recent_rows for number in row["numbers"] if number in selected)
    recent_rate = recent_hits / (len(recent_rows) * DRAW_SIZE)
    expected_rate = len(selected) / TOTAL_NUMBERS
    rolling_score = max(0.0, 1.0 - abs(recent_rate - expected_rate) / max(expected_rate, 0.0001))
    return {
        "rolling_score": rolling_score,
        "recent_hits": recent_hits,
        "recent_rate": recent_rate,
        "window": len(recent_rows),
    }


def analyze_ticket(numbers: list[int], rows: list[dict[str, Any]], models: dict[str, dict[str, Any]]) -> dict[str, Any]:
    frequency = models.get("frequency", {})
    cold = models.get("cold", {})
    middle = models.get("middle", {})
    gap = models.get("gap", {})
    combined = models.get("combined", {})

    max_hot = max_model_value(frequency, "model_score")
    max_cold = max_model_value(cold, "cold_model_score")
    max_middle = max_model_value(middle, "middle_model_score")
    max_gap = max_model_value(gap, "combined_next_probability")

    number_rows = []
    hot_scores = []
    cold_scores = []
    middle_scores = []
    gap_scores = []

    stats = historical_number_stats(rows) if rows else pd.DataFrame()
    stats_by_number = {int(row["number"]): row for _, row in stats.iterrows()} if not stats.empty else {}

    for number in sorted(numbers):
        hot_item = get_scored_number(frequency, number)
        cold_item = get_scored_number(cold, number)
        middle_item = get_scored_number(middle, number)
        gap_item = get_scored_number(gap, number)
        historical = stats_by_number.get(number, {})

        hot_value = safe_float(hot_item.get("model_score"))
        cold_value = safe_float(cold_item.get("cold_model_score"))
        middle_value = safe_float(middle_item.get("middle_model_score"))
        gap_value = safe_float(gap_item.get("combined_next_probability"))

        hot_norm = hot_value / max_hot if max_hot else 0
        cold_norm = cold_value / max_cold if max_cold else 0
        middle_norm = middle_value / max_middle if max_middle else 0
        gap_norm = gap_value / max_gap if max_gap else 0

        hot_scores.append(hot_norm)
        cold_scores.append(cold_norm)
        middle_scores.append(middle_norm)
        gap_scores.append(gap_norm)

        number_rows.append(
            {
                "number": number,
                "frequency signal": classify_frequency_signal(hot_item),
                "hot score": round(hot_value, 4),
                "cold/gap status": cold_item.get("cold_status", "n/a"),
                "cold+gap score": round(cold_value, 4),
                "middle status": middle_item.get("middle_status", "n/a"),
                "middle score": round(middle_value, 4),
                "gap status": gap_item.get("interval_status", "n/a"),
                "next probability %": round(gap_value * 100, 3),
                "empirical %": historical.get("empirical %", "n/a"),
                "expected %": round(EXPECTED_NUMBER_PROBABILITY * 100, 3),
                "current gap": gap_item.get("current_gap") or hot_item.get("recency_gap") or historical.get("current gap"),
                "times drawn": historical.get("times drawn", "n/a"),
            }
        )

    pair_triple = pair_and_triple_support(numbers, rows)
    structure = ticket_structure_analysis(numbers)
    rolling = rolling_ticket_score(numbers, rows)

    sub_scores = {
        "hot_score": sum(hot_scores) / len(hot_scores) if hot_scores else 0,
        "cold_score": sum(cold_scores) / len(cold_scores) if cold_scores else 0,
        "middle_score": sum(middle_scores) / len(middle_scores) if middle_scores else 0,
        "gap_probability_score": sum(gap_scores) / len(gap_scores) if gap_scores else 0,
        "pair_score": pair_triple["pair_score"],
        "triple_score": pair_triple["triple_score"],
        "structure_score": structure["structure_score"],
        "rolling_window_score": rolling["rolling_score"],
    }

    weights = combined.get("weights", {}) or {
        "hot": 0.12,
        "cold": 0.12,
        "middle": 0.13,
        "gap": 0.18,
        "pair": 0.12,
        "triple": 0.04,
        "structure": 0.16,
        "rolling": 0.13,
    }
    final_score = (
        safe_float(weights.get("hot"), 0.12) * sub_scores["hot_score"]
        + safe_float(weights.get("cold"), 0.12) * sub_scores["cold_score"]
        + safe_float(weights.get("middle"), 0.13) * sub_scores["middle_score"]
        + safe_float(weights.get("gap"), 0.18) * sub_scores["gap_probability_score"]
        + safe_float(weights.get("pair"), 0.12) * sub_scores["pair_score"]
        + safe_float(weights.get("triple"), 0.04) * sub_scores["triple_score"]
        + safe_float(weights.get("structure"), 0.16) * sub_scores["structure_score"]
        + safe_float(weights.get("rolling"), 0.13) * sub_scores["rolling_window_score"]
    )

    exact_rank = None
    for item in combined.get("recommended_combinations", []):
        item_numbers = item.get("numbers") or item.get("combination") or []
        if sorted(item_numbers) == sorted(numbers):
            exact_rank = item
            break

    return {
        "numbers": sorted(numbers),
        "number_rows": number_rows,
        "sub_scores": sub_scores,
        "final_score": final_score,
        "confidence_score": final_score * 100,
        "structure": structure,
        "pair_triple": pair_triple,
        "rolling": rolling,
        "exact_rank": exact_rank,
    }


def show_ticket_analyzer(rows: list[dict[str, Any]], models: dict[str, dict[str, Any]]) -> None:
    st.header("Ticket Analyzer")
    st.markdown(
        "Enter any 6 numbers and the app will explain how the existing models read them: "
        "hot/frequency, cold + gap, middle/balanced, interval probability, pair/triple support, and structure."
    )

    st.markdown(
        """
        <div class="warning-note">
            This does <b>not</b> change the real jackpot probability. Every exact ticket still has fair odds of
            <b>1 in 13,983,816</b>. The score below is only a relative model-reading of your chosen numbers.
        </div>
        """,
        unsafe_allow_html=True,
    )

    default_ticket = [10, 14, 23, 27, 33, 36]
    selected = st.multiselect(
        "Choose exactly 6 numbers to analyze",
        options=list(range(1, 50)),
        default=default_ticket,
        max_selections=6,
        key="ticket_analyzer_numbers",
    )

    if len(selected) != 6:
        st.warning("Select exactly 6 unique numbers.")
        return

    numbers = sorted(int(number) for number in selected)
    analysis = analyze_ticket(numbers, rows, models)

    st.markdown(ticket_html(numbers), unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Model confidence", f"{analysis['confidence_score']:.2f}/100", "Relative score for this ticket")
    with col2:
        metric_card("Real jackpot odds", "1 in 13.98M", "Unchanged fair probability")
    with col3:
        metric_card("Ticket sum", str(analysis["structure"]["sum"]), "Structure feature")
    with col4:
        metric_card("Strongest pair support", str(analysis["pair_triple"]["strong_pairs"][0]["count"] if analysis["pair_triple"]["strong_pairs"] else 0), "Historical co-occurrence")

    exact_rank = analysis.get("exact_rank")
    if exact_rank:
        st.success(
            f"This exact ticket is present in the generated combined recommendations: "
            f"rank {exact_rank.get('relative_rank', 'n/a')} with confidence {safe_float(exact_rank.get('confidence_score')):.2f}/100."
        )
    else:
        st.info("This exact ticket is not in the saved top combined recommendations, so the score below is calculated live from the model signals.")

    st.subheader("Per-number model reading")
    number_df = pd.DataFrame(analysis["number_rows"])
    st.dataframe(number_df, hide_index=True, use_container_width=True)

    st.subheader("Ticket signal breakdown")
    signal_df = pd.DataFrame(
        [
            {"signal": key.replace("_", " "), "score 0-1": round(value, 4), "score %": round(value * 100, 2)}
            for key, value in analysis["sub_scores"].items()
        ]
    )
    st.dataframe(signal_df, hide_index=True, use_container_width=True)
    st.bar_chart(signal_df.set_index("signal")[["score %"]])

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Structure")
        st.write(
            {
                "sum": analysis["structure"]["sum"],
                "even/odd": f"{analysis['structure']['even_count']} / {analysis['structure']['odd_count']}",
                "low/high": f"{analysis['structure']['low_count']} / {analysis['structure']['high_count']}",
                "consecutive_pairs": analysis["structure"]["consecutive_pairs"],
                "structure_score": round(analysis["structure"]["structure_score"], 4),
            }
        )
    with col_b:
        st.subheader("Recent window")
        st.write(
            {
                "window_draws": analysis["rolling"]["window"],
                "recent_hits_for_ticket_numbers": analysis["rolling"]["recent_hits"],
                "recent_rate": format_percent(analysis["rolling"]["recent_rate"], digits=3),
                "rolling_score": round(analysis["rolling"]["rolling_score"], 4),
            }
        )

    col_p, col_t = st.columns(2)
    with col_p:
        st.subheader("Strongest pairs")
        st.dataframe(pd.DataFrame(analysis["pair_triple"]["strong_pairs"]), hide_index=True, use_container_width=True)
    with col_t:
        st.subheader("Strongest triples")
        st.dataframe(pd.DataFrame(analysis["pair_triple"]["strong_triples"]), hide_index=True, use_container_width=True)

def show_reports() -> None:
    st.header("Reports")
    if not REPORTS_DIR.exists():
        st.info("No reports folder found.")
        return

    report_files = sorted(REPORTS_DIR.glob("*.md"))
    if not report_files:
        st.info("No markdown reports found.")
        return

    selected = st.selectbox("Choose report", report_files, format_func=lambda path: path.name)
    text = selected.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    st.caption(f"Report size: {len(lines):,} lines. Preview mode protects the browser from freezing.")
    preview_lines = st.slider("Preview lines", min_value=50, max_value=min(max(len(lines), 50), 2000), value=min(len(lines), 250), step=50)
    preview = "\n".join(lines[:preview_lines])
    st.markdown(preview)

    if len(lines) > preview_lines:
        st.info(f"Showing first {preview_lines:,} lines only. Download the full report below.")

    st.download_button(
        label="Download full report",
        data=text.encode("utf-8"),
        file_name=selected.name,
        mime="text/markdown",
    )


def get_existing_draw_keys() -> set[tuple[int, int, int]]:
    keys: set[tuple[int, int, int]] = set()
    if not DATA_PATH.exists():
        return keys

    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                keys.add((int(row["year"]), int(row["draw_number"]), int(row.get("draw_position") or 1)))
            except (KeyError, TypeError, ValueError):
                continue
    return keys


def get_next_draw_id() -> int:
    if not DATA_PATH.exists():
        return 1

    max_id = 0
    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                max_id = max(max_id, int(row.get("draw_id") or 0))
            except ValueError:
                continue
    return max_id + 1


def backup_historical_draws() -> Path | None:
    if not DATA_PATH.exists():
        return None

    backup_dir = ROOT / "data" / "manual_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"historical_draws_before_manual_update_{date.today().isoformat()}.csv"

    if backup_path.exists():
        suffix = 2
        while True:
            candidate = backup_dir / f"historical_draws_before_manual_update_{date.today().isoformat()}_{suffix}.csv"
            if not candidate.exists():
                backup_path = candidate
                break
            suffix += 1

    shutil.copy2(DATA_PATH, backup_path)
    return backup_path


def append_manual_draw(
    *,
    draw_date: date,
    year: int,
    draw_number: int,
    draw_position: int,
    numbers: list[int],
    source_url: str,
) -> tuple[bool, str]:
    if len(numbers) != 6:
        return False, "Exactly 6 numbers are required."

    if len(set(numbers)) != 6:
        return False, "The 6 numbers must be unique."

    if any(number < 1 or number > 49 for number in numbers):
        return False, "All numbers must be between 1 and 49."

    key = (year, draw_number, draw_position)
    existing_keys = get_existing_draw_keys()
    if key in existing_keys:
        return False, f"Draw already exists for year={year}, draw_number={draw_number}, draw_position={draw_position}."

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
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

    if DATA_PATH.exists():
        backup_path = backup_historical_draws()
    else:
        backup_path = None

    numbers = sorted(numbers)
    row = {
        "draw_id": get_next_draw_id(),
        "date": draw_date.isoformat(),
        "n1": numbers[0],
        "n2": numbers[1],
        "n3": numbers[2],
        "n4": numbers[3],
        "n5": numbers[4],
        "n6": numbers[5],
        "year": year,
        "draw_number": draw_number,
        "draw_position": draw_position,
        "source_url": source_url.strip() or "manual_entry",
    }

    file_exists = DATA_PATH.exists() and DATA_PATH.stat().st_size > 0
    with DATA_PATH.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    load_draws.clear()
    load_models.clear()

    backup_text = f" Backup: {backup_path}" if backup_path else ""
    return True, f"Draw saved successfully: {numbers}.{backup_text}"


def show_update_draws(rows: list[dict[str, Any]]) -> None:
    st.header("Update Draws")
    st.markdown(
        "Add a new official winning draw manually after the latest Bulgarian Toto 2 – 6/49 results are published. "
        "The app validates the numbers and prevents duplicate year/draw/position records."
    )

    summary = draw_summary(rows)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current records", f"{summary['rows']:,}")
    with col2:
        st.metric("Year range", f"{summary['min_year']}–{summary['max_year']}")
    with col3:
        st.metric("Duplicate draw keys", summary["duplicate_draw_keys"])

    st.markdown("### Add new winning numbers")
    with st.form("manual_draw_form"):
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            draw_date = st.date_input("Draw date", value=date.today())
        with col_b:
            year = st.number_input("Year", min_value=1958, max_value=2100, value=date.today().year, step=1)
        with col_c:
            draw_number = st.number_input("Draw number", min_value=0, max_value=999, value=1, step=1)
        with col_d:
            draw_position = st.number_input("Draw position", min_value=1, max_value=10, value=1, step=1)

        st.caption("Enter the 6 winning numbers. They will be saved sorted ascending, as in the historical dataset.")
        number_cols = st.columns(6)
        numbers = []
        defaults = [1, 2, 3, 4, 5, 6]
        for index, column in enumerate(number_cols):
            with column:
                numbers.append(st.number_input(f"N{index + 1}", min_value=1, max_value=49, value=defaults[index], step=1))

        source_url = st.text_input("Source note / URL", value="manual_entry")
        submitted = st.form_submit_button("Save new draw")

    if submitted:
        ok, message = append_manual_draw(
            draw_date=draw_date,
            year=int(year),
            draw_number=int(draw_number),
            draw_position=int(draw_position),
            numbers=[int(number) for number in numbers],
            source_url=source_url,
        )
        if ok:
            st.success(message)
            st.info(
                "After adding new data, retrain the models from the terminal:\n\n"
                "python train_model.py\n"
                "python train_cold_model.py\n"
                "python train_middle_model.py\n"
                "python train_gap_model.py\n"
                "python train_combined_model.py"
            )
        else:
            st.error(message)

    st.markdown("### Recent records")
    if rows:
        recent = sorted(rows, key=lambda item: (item["year"], item["draw_number"], item["draw_position"]))[-12:]
        recent_df = pd.DataFrame(
            [
                {
                    "year": row["year"],
                    "draw_number": row["draw_number"],
                    "draw_position": row["draw_position"],
                    "numbers": " ".join(str(number) for number in row["numbers"]),
                }
                for row in reversed(recent)
            ]
        )
        st.dataframe(recent_df, hide_index=True, use_container_width=True)
    else:
        st.info("No records found yet.")


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
            "Ticket Analyzer",
            "Reports",
            "Update Draws",
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
elif page == "Ticket Analyzer":
    show_ticket_analyzer(rows, models)
elif page == "Reports":
    show_reports()
elif page == "Update Draws":
    show_update_draws(rows)

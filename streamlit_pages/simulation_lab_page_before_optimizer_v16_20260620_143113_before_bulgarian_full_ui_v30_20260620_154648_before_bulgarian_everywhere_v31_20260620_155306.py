from __future__ import annotations

import json
import math
import random
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import pandas as pd
import streamlit as st

DATA_PATH = Path("data/historical_draws.csv")
MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports")
TOTAL_COMBINATIONS = math.comb(49, 6)
EXPECTED_NUMBER_PROBABILITY = 6 / 49


def _t(bg: str, en: str, lang: str) -> str:
    return bg if lang == "Български" else en


@st.cache_data(show_spinner=False)
def _load_draws() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=["year", "draw_number", "draw_position", "n1", "n2", "n3", "n4", "n5", "n6"])
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    for col in ["year", "draw_number", "draw_position", "n1", "n2", "n3", "n4", "n5", "n6"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["n1", "n2", "n3", "n4", "n5", "n6"])
    for col in ["year", "draw_number", "draw_position", "n1", "n2", "n3", "n4", "n5", "n6"]:
        if col in df.columns:
            df[col] = df[col].astype(int)
    return df


@st.cache_data(show_spinner=False)
def _load_json_model(path: str) -> Dict[str, Any]:
    model_path = Path(path)
    if not model_path.exists():
        return {}
    try:
        with model_path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)
    except Exception:
        return {}


def _draw_number_lists(df: pd.DataFrame) -> List[List[int]]:
    if df.empty:
        return []
    return df[["n1", "n2", "n3", "n4", "n5", "n6"]].astype(int).values.tolist()


def _normalize_ticket(numbers: Iterable[int]) -> List[int]:
    return sorted(int(n) for n in numbers)


def _validate_ticket(numbers: Sequence[int]) -> Tuple[bool, str]:
    if len(numbers) != 6:
        return False, "Трябва да има точно 6 числа. / Exactly 6 numbers are required."
    if len(set(numbers)) != 6:
        return False, "Числата не трябва да се повтарят. / Numbers must be unique."
    if any(number < 1 or number > 49 for number in numbers):
        return False, "Всички числа трябва да са между 1 и 49. / All numbers must be between 1 and 49."
    return True, "OK"


def _parse_ticket_text(raw: str) -> List[int]:
    cleaned = raw.replace(";", ",").replace("|", ",").replace("/", ",")
    parts: List[str] = []
    for chunk in cleaned.split(","):
        parts.extend(chunk.strip().split())
    numbers: List[int] = []
    for part in parts:
        token = "".join(ch for ch in part if ch.isdigit())
        if token:
            numbers.append(int(token))
    return _normalize_ticket(numbers)


def _match_probabilities() -> Dict[int, float]:
    result: Dict[int, float] = {}
    for matches in range(7):
        result[matches] = math.comb(6, matches) * math.comb(43, 6 - matches) / TOTAL_COMBINATIONS
    return result


def _number_statistics(df: pd.DataFrame) -> Dict[int, Dict[str, float]]:
    draws = _draw_number_lists(df)
    total_draws = len(draws)
    counts = Counter(number for draw in draws for number in draw)
    last_seen: Dict[int, int] = {number: total_draws for number in range(1, 50)}
    for reverse_index, draw in enumerate(reversed(draws)):
        for number in draw:
            if last_seen[number] == total_draws:
                last_seen[number] = reverse_index

    intervals: Dict[int, List[int]] = {number: [] for number in range(1, 50)}
    last_position: Dict[int, int | None] = {number: None for number in range(1, 50)}
    for index, draw in enumerate(draws):
        for number in draw:
            if last_position[number] is not None:
                intervals[number].append(index - int(last_position[number]))
            last_position[number] = index

    values: Dict[int, Dict[str, float]] = {}
    for number in range(1, 50):
        count = counts[number]
        empirical = count / total_draws if total_draws else 0.0
        expected_count = total_draws * EXPECTED_NUMBER_PROBABILITY
        std = math.sqrt(total_draws * EXPECTED_NUMBER_PROBABILITY * (1 - EXPECTED_NUMBER_PROBABILITY)) if total_draws else 0.0
        z_score = (count - expected_count) / std if std else 0.0
        avg_interval = sum(intervals[number]) / len(intervals[number]) if intervals[number] else 49 / 6
        gap = last_seen[number] if total_draws else 0
        gap_ratio = gap / avg_interval if avg_interval else 0.0
        values[number] = {
            "count": float(count),
            "empirical": empirical,
            "expected": EXPECTED_NUMBER_PROBABILITY,
            "z_score": z_score,
            "gap": float(gap),
            "avg_interval": float(avg_interval),
            "gap_ratio": float(gap_ratio),
        }
    return values


def _co_occurrence_stats(df: pd.DataFrame) -> Tuple[Counter, Counter]:
    pair_counts: Counter = Counter()
    triple_counts: Counter = Counter()
    for draw in _draw_number_lists(df):
        ordered = tuple(sorted(draw))
        pair_counts.update(combinations(ordered, 2))
        triple_counts.update(combinations(ordered, 3))
    return pair_counts, triple_counts


def _structure_score(ticket: Sequence[int]) -> Tuple[float, Dict[str, Any]]:
    numbers = sorted(ticket)
    odd = sum(1 for number in numbers if number % 2)
    even = 6 - odd
    low = sum(1 for number in numbers if number <= 16)
    middle = sum(1 for number in numbers if 17 <= number <= 33)
    high = sum(1 for number in numbers if number >= 34)
    total_sum = sum(numbers)
    consecutive_pairs = sum(1 for a, b in zip(numbers, numbers[1:]) if b - a == 1)
    max_under_31 = sum(1 for number in numbers if number <= 31)

    score = 100.0
    if odd in (0, 6):
        score -= 22
    elif odd in (1, 5):
        score -= 8
    if 0 in (low, middle, high):
        score -= 12
    if total_sum < 95 or total_sum > 205:
        score -= 18
    elif total_sum < 115 or total_sum > 185:
        score -= 8
    if consecutive_pairs >= 3:
        score -= 20
    elif consecutive_pairs == 2:
        score -= 8
    if max_under_31 >= 5:
        score -= 10
    if numbers == list(range(numbers[0], numbers[0] + 6)):
        score -= 30

    details = {
        "odd": odd,
        "even": even,
        "low": low,
        "middle": middle,
        "high": high,
        "sum": total_sum,
        "consecutive_pairs": consecutive_pairs,
        "numbers_under_31": max_under_31,
    }
    return max(0.0, min(100.0, score)), details


def _human_pattern_risk(ticket: Sequence[int]) -> Tuple[str, float, List[str]]:
    numbers = sorted(ticket)
    risk = 0.0
    reasons: List[str] = []
    if all(number <= 31 for number in numbers):
        risk += 25
        reasons.append("Всички числа са до 31 — прилича на дати. / All numbers are <=31, date-like pattern.")
    if sum(1 for a, b in zip(numbers, numbers[1:]) if b - a == 1) >= 2:
        risk += 20
        reasons.append("Има много поредни числа. / Many consecutive numbers.")
    gaps = [b - a for a, b in zip(numbers, numbers[1:])]
    if len(set(gaps)) <= 2:
        risk += 18
        reasons.append("Разстоянията между числата са прекалено регулярни. / Very regular spacing.")
    if numbers in ([1, 2, 3, 4, 5, 6], [7, 14, 21, 28, 35, 42]):
        risk += 40
        reasons.append("Много популярен човешки pattern. / Very popular human pattern.")
    if risk < 20:
        label = "Нисък / Low"
    elif risk < 45:
        label = "Среден / Medium"
    else:
        label = "Висок / High"
    return label, min(100.0, risk), reasons


def _ticket_model_analysis(ticket: Sequence[int], df: pd.DataFrame) -> Dict[str, Any]:
    stats = _number_statistics(df)
    pair_counts, triple_counts = _co_occurrence_stats(df)
    total_draws = max(len(df), 1)

    hot_values = [stats[n]["empirical"] / EXPECTED_NUMBER_PROBABILITY for n in ticket]
    cold_values = [max(0.0, EXPECTED_NUMBER_PROBABILITY - stats[n]["empirical"]) / EXPECTED_NUMBER_PROBABILITY for n in ticket]
    gap_values = [min(stats[n]["gap_ratio"] / 2.5, 1.4) for n in ticket]
    middle_values = [max(0.0, 1 - abs(stats[n]["empirical"] - EXPECTED_NUMBER_PROBABILITY) / 0.012) for n in ticket]
    z_values = [stats[n]["z_score"] for n in ticket]

    pair_support_raw = sum(pair_counts[tuple(pair)] for pair in combinations(sorted(ticket), 2))
    triple_support_raw = sum(triple_counts[tuple(triple)] for triple in combinations(sorted(ticket), 3))
    pair_support = min(100.0, (pair_support_raw / (15 * max(total_draws / 117.6, 1))) * 100)
    triple_support = min(100.0, (triple_support_raw / (20 * max(total_draws / 18424, 0.1))) * 100)
    structure, structure_details = _structure_score(ticket)
    human_label, human_risk, human_reasons = _human_pattern_risk(ticket)

    hot_score = sum(hot_values) / len(hot_values) * 50
    cold_gap_score = (sum(cold_values) / len(cold_values) * 45) + (sum(gap_values) / len(gap_values) * 35)
    middle_score = sum(middle_values) / len(middle_values) * 100
    gap_score = sum(gap_values) / len(gap_values) * 75

    final_score = (
        hot_score * 0.15
        + cold_gap_score * 0.20
        + middle_score * 0.15
        + gap_score * 0.20
        + pair_support * 0.10
        + triple_support * 0.05
        + structure * 0.15
        - human_risk * 0.08
    )
    final_score = max(0.0, min(100.0, final_score))

    per_number = []
    for number in ticket:
        item = stats[number]
        if item["z_score"] > 1.8:
            category = "Hot / Горещо"
        elif item["z_score"] < -1.8:
            category = "Cold / Студено"
        elif item["gap_ratio"] >= 1.7:
            category = "Overdue / Отдавна непадало се"
        else:
            category = "Normal / Нормално"
        per_number.append({
            "Number": number,
            "Category": category,
            "Times drawn": int(item["count"]),
            "Empirical %": round(item["empirical"] * 100, 3),
            "Expected %": round(item["expected"] * 100, 3),
            "Z-score": round(item["z_score"], 3),
            "Current gap": int(item["gap"]),
            "Avg interval": round(item["avg_interval"], 2),
            "Gap ratio": round(item["gap_ratio"], 2),
        })

    return {
        "hot_score": hot_score,
        "cold_gap_score": cold_gap_score,
        "middle_score": middle_score,
        "gap_score": gap_score,
        "pair_support": pair_support,
        "triple_support": triple_support,
        "structure_score": structure,
        "structure_details": structure_details,
        "human_pattern_label": human_label,
        "human_pattern_risk": human_risk,
        "human_pattern_reasons": human_reasons,
        "final_score": final_score,
        "per_number": per_number,
        "avg_z_score": sum(z_values) / len(z_values),
    }


def _historical_replay(ticket: Sequence[int], df: pd.DataFrame) -> Dict[int, int]:
    distribution = Counter({matches: 0 for matches in range(7)})
    ticket_set = set(ticket)
    for draw in _draw_number_lists(df):
        matches = len(ticket_set.intersection(draw))
        distribution[matches] += 1
    return dict(distribution)


def _monte_carlo(ticket: Sequence[int], simulations: int, seed: int) -> Dict[int, int]:
    rng = random.Random(seed)
    ticket_set = set(ticket)
    distribution = Counter({matches: 0 for matches in range(7)})
    population = list(range(1, 50))
    for _ in range(simulations):
        draw = set(rng.sample(population, 6))
        distribution[len(ticket_set.intersection(draw))] += 1
    return dict(distribution)


def _load_model_recommendations() -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    model_files = [
        ("Advanced ensemble", MODELS_DIR / "lottery_advanced_ensemble_model.json"),
        ("Final combined", MODELS_DIR / "lottery_combined_model.json"),
        ("Hot / Frequency", MODELS_DIR / "lottery_frequency_model.json"),
        ("Cold + Gap", MODELS_DIR / "lottery_cold_model.json"),
        ("Middle / Balanced", MODELS_DIR / "lottery_middle_model.json"),
        ("Gap / Interval", MODELS_DIR / "lottery_gap_model.json"),
    ]
    for label, path in model_files:
        model = _load_json_model(str(path))
        if not model:
            continue
        recs = (
            model.get("recommended_combinations")
            or model.get("top_recommendations")
            or model.get("recommendations")
            or model.get("top_combinations")
            or []
        )
        if isinstance(recs, list) and recs:
            first = recs[0]
            if isinstance(first, dict):
                numbers = first.get("numbers") or first.get("combination") or first.get("ticket")
                score = first.get("confidence_score") or first.get("final_score") or first.get("confidence")
            else:
                numbers = first
                score = None
            if numbers:
                candidates.append({"Model": label, "Numbers": sorted(numbers), "Score": score})
                continue
        for key in ["recommended_ticket", "recommended_hot_ticket", "recommended_cold_ticket", "recommended_middle_ticket", "recommended_gap_ticket"]:
            if key in model and model[key]:
                candidates.append({"Model": label, "Numbers": sorted(model[key]), "Score": model.get("confidence_score")})
                break
    return candidates


def _ticket_to_html(numbers: Sequence[int], size: int = 46) -> str:
    balls = "".join(
        f"<span class='sim-ball' style='width:{size}px;height:{size}px;line-height:{size}px;font-size:{max(15, int(size*0.36))}px'>{number}</span>"
        for number in sorted(numbers)
    )
    return f"<div class='sim-balls'>{balls}</div>"


def _render_distribution(title: str, distribution: Dict[int, int], total: int, lang: str) -> None:
    st.markdown(f"#### {title}")
    rows = []
    for matches in range(7):
        count = int(distribution.get(matches, 0))
        rows.append({
            _t("Съвпадения", "Matches", lang): matches,
            _t("Брой", "Count", lang): count,
            _t("Процент", "Percent", lang): round((count / total * 100) if total else 0, 4),
        })
    result_df = pd.DataFrame(rows)
    st.dataframe(result_df, width="stretch", hide_index=True)
    chart_df = result_df.set_index(_t("Съвпадения", "Matches", lang))[[ _t("Процент", "Percent", lang) ]]
    st.bar_chart(chart_df, height=240)


def _render_metric_cards(ticket: Sequence[int], analysis: Dict[str, Any], lang: str) -> None:
    odds_pct = 100 / TOTAL_COMBINATIONS
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(_t("Реален шанс 6/6", "Real 6/6 odds", lang), f"1 / {TOTAL_COMBINATIONS:,}")
    col2.metric(_t("В проценти", "Percent", lang), f"{odds_pct:.8f}%")
    col3.metric(_t("Моделна оценка", "Model score", lang), f"{analysis['final_score']:.2f}/100")
    col4.metric(_t("Human pattern risk", "Human pattern risk", lang), analysis["human_pattern_label"])


def render_simulation_lab_page() -> None:
    st.markdown(
        """
        <style>
        .sim-hero {
            border: 1px solid rgba(212,175,55,.35);
            background: linear-gradient(145deg, rgba(15,15,18,.96), rgba(34,28,14,.82));
            border-radius: 22px;
            padding: 22px 24px;
            margin-bottom: 18px;
            box-shadow: 0 18px 48px rgba(0,0,0,.25);
        }
        .sim-balls {display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin:10px 0 16px;}
        .sim-ball {
            display:inline-block;
            text-align:center;
            border-radius:999px;
            background: radial-gradient(circle at 35% 25%, #fff4b8, #d4af37 48%, #8b6b18 100%);
            color:#111;
            font-weight:800;
            border:1px solid rgba(255,255,255,.45);
            box-shadow: 0 8px 24px rgba(212,175,55,.22);
        }
        .sim-note {
            border-left: 4px solid #d4af37;
            padding: 10px 14px;
            background: rgba(212,175,55,.08);
            border-radius: 10px;
            margin: 10px 0 18px;
        }
        .sim-card {
            border: 1px solid rgba(212,175,55,.22);
            border-radius: 18px;
            padding: 16px 18px;
            background: rgba(255,255,255,.035);
            margin-bottom: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    lang = st.sidebar.radio("Език / Language", ["Български", "English"], horizontal=True, key="sim_lab_lang")
    st.markdown(
        f"""
        <div class='sim-hero'>
            <h1>🎲 {_t('Симулация / Разиграй тото', 'Simulation / Play the Lottery', lang)}</h1>
            <p>{_t('Въведи 6 числа и виж реалната математическа вероятност, моделната оценка, Monte Carlo симулация, исторически replay и сравнение с моделните фишове.', 'Enter 6 numbers and see the real mathematical odds, model score, Monte Carlo simulation, historical replay, and comparison with model tickets.', lang)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = _load_draws()
    if df.empty:
        st.error(_t("Не са намерени исторически данни в data/historical_draws.csv.", "No historical data found in data/historical_draws.csv.", lang))
        return

    st.markdown(
        f"<div class='sim-note'>{_t('Важно: моделната оценка не променя реалния шанс. Всяка точна комбинация 6/49 остава с шанс 1 към 13,983,816.', 'Important: the model score does not change the real odds. Every exact 6/49 combination remains 1 in 13,983,816.', lang)}</div>",
        unsafe_allow_html=True,
    )

    default_ticket = [4, 17, 23, 34, 37, 42]
    model_recommendations = _load_model_recommendations()
    if model_recommendations:
        default_ticket = model_recommendations[0]["Numbers"]

    input_mode = st.radio(
        _t("Как да въведеш фиша?", "How do you want to enter the ticket?", lang),
        [_t("Избор от списък", "Pick from list", lang), _t("Текст", "Text", lang)],
        horizontal=True,
    )

    if input_mode.startswith("Избор") or input_mode.startswith("Pick"):
        ticket = st.multiselect(
            _t("Избери точно 6 числа", "Pick exactly 6 numbers", lang),
            options=list(range(1, 50)),
            default=default_ticket,
            max_selections=6,
        )
        ticket = _normalize_ticket(ticket)
    else:
        raw_ticket = st.text_input(
            _t("Въведи 6 числа, разделени със запетая или интервал", "Enter 6 numbers separated by comma or space", lang),
            value=", ".join(map(str, default_ticket)),
        )
        ticket = _parse_ticket_text(raw_ticket)

    is_valid, message = _validate_ticket(ticket)
    if not is_valid:
        st.warning(message)
        return

    st.markdown(_ticket_to_html(ticket, size=56), unsafe_allow_html=True)
    analysis = _ticket_model_analysis(ticket, df)
    _render_metric_cards(ticket, analysis, lang)

    tabs = st.tabs([
        _t("Провери моя фиш", "Check my ticket", lang),
        _t("Monte Carlo", "Monte Carlo", lang),
        _t("Виртуален тираж", "Virtual draw", lang),
        _t("Исторически replay", "Historical replay", lang),
        _t("Сравни с моделите", "Compare with models", lang),
    ])

    with tabs[0]:
        st.markdown(f"### {_t('Анализ по модели', 'Model analysis', lang)}")
        cols = st.columns(4)
        cols[0].metric("Hot / Frequency", f"{analysis['hot_score']:.2f}")
        cols[1].metric("Cold + Gap", f"{analysis['cold_gap_score']:.2f}")
        cols[2].metric("Middle / Balance", f"{analysis['middle_score']:.2f}")
        cols[3].metric("Gap / Interval", f"{analysis['gap_score']:.2f}")

        cols2 = st.columns(4)
        cols2[0].metric("Pair support", f"{analysis['pair_support']:.2f}")
        cols2[1].metric("Triple support", f"{analysis['triple_support']:.2f}")
        cols2[2].metric("Structure", f"{analysis['structure_score']:.2f}")
        cols2[3].metric("Human risk", f"{analysis['human_pattern_risk']:.2f}")

        st.markdown(f"#### {_t('Число по число', 'Number-by-number', lang)}")
        st.dataframe(pd.DataFrame(analysis["per_number"]), width="stretch", hide_index=True)

        if analysis["human_pattern_reasons"]:
            st.markdown(f"#### {_t('Причини за human-pattern risk', 'Human-pattern risk reasons', lang)}")
            for reason in analysis["human_pattern_reasons"]:
                st.write(f"- {reason}")
        else:
            st.success(_t("Няма силен човешки pattern. Това е добре за избягване на популярни фишове.", "No strong human pattern detected. This is good for avoiding popular ticket shapes.", lang))

        st.markdown(f"#### {_t('Структура на комбинацията', 'Combination structure', lang)}")
        st.json(analysis["structure_details"])

    with tabs[1]:
        simulations = st.select_slider(
            _t("Брой симулации", "Number of simulations", lang),
            options=[1_000, 10_000, 50_000, 100_000, 250_000],
            value=100_000,
        )
        seed = st.number_input(_t("Seed за повторяемост", "Seed for reproducibility", lang), min_value=1, max_value=999999, value=42, step=1)
        if st.button(_t("Симулирай", "Run simulation", lang), key="run_monte_carlo"):
            with st.spinner(_t("Симулацията се изпълнява...", "Running simulation...", lang)):
                distribution = _monte_carlo(ticket, int(simulations), int(seed))
            _render_distribution(_t("Monte Carlo резултат", "Monte Carlo result", lang), distribution, int(simulations), lang)

        theoretical = _match_probabilities()
        st.markdown(f"#### {_t('Теоретични вероятности', 'Theoretical probabilities', lang)}")
        theory_rows = []
        for matches, probability in theoretical.items():
            theory_rows.append({
                _t("Съвпадения", "Matches", lang): matches,
                _t("Вероятност %", "Probability %", lang): round(probability * 100, 8),
                _t("1 към", "1 in", lang): round(1 / probability) if probability else None,
            })
        st.dataframe(pd.DataFrame(theory_rows), width="stretch", hide_index=True)

    with tabs[2]:
        if st.button(_t("Изтегли виртуален тираж", "Draw a virtual ticket", lang), key="virtual_draw"):
            draw = sorted(random.sample(range(1, 50), 6))
            matches = sorted(set(ticket).intersection(draw))
            st.markdown(f"#### {_t('Твоят фиш', 'Your ticket', lang)}")
            st.markdown(_ticket_to_html(ticket, size=46), unsafe_allow_html=True)
            st.markdown(f"#### {_t('Виртуален тираж', 'Virtual draw', lang)}")
            st.markdown(_ticket_to_html(draw, size=46), unsafe_allow_html=True)
            st.metric(_t("Съвпадения", "Matches", lang), len(matches))
            if matches:
                st.write(_t("Съвпаднали числа:", "Matched numbers:", lang), matches)

    with tabs[3]:
        distribution = _historical_replay(ticket, df)
        _render_distribution(_t("Исторически replay срещу всички тегления", "Historical replay against all draws", lang), distribution, len(df), lang)
        best = max((matches for matches, count in distribution.items() if count > 0), default=0)
        st.info(_t(f"Най-добрият исторически резултат за този фиш е {best} съвпадения.", f"The best historical result for this ticket is {best} matches.", lang))

    with tabs[4]:
        st.markdown(f"### {_t('Сравнение с моделните фишове', 'Comparison with model tickets', lang)}")
        if not model_recommendations:
            st.warning(_t("Не са намерени моделни препоръки. Пусни training скриптовете първо.", "No model recommendations found. Run training scripts first.", lang))
        else:
            rows = []
            your_score = analysis["final_score"]
            rows.append({"Model": _t("Твоят фиш", "Your ticket", lang), "Numbers": ticket, "Live score": round(your_score, 2), "Overlap with your ticket": 6})
            for item in model_recommendations:
                model_ticket = item["Numbers"]
                model_analysis = _ticket_model_analysis(model_ticket, df)
                rows.append({
                    "Model": item["Model"],
                    "Numbers": model_ticket,
                    "Live score": round(model_analysis["final_score"], 2),
                    "Overlap with your ticket": len(set(ticket).intersection(model_ticket)),
                })
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            st.markdown("---")
            for item in model_recommendations[:6]:
                st.markdown(f"#### {item['Model']}")
                st.markdown(_ticket_to_html(item["Numbers"], size=42), unsafe_allow_html=True)


if __name__ == "__main__":
    st.set_page_config(page_title="Lottery Simulation Lab", layout="wide")
    render_simulation_lab_page()

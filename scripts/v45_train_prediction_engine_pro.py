from __future__ import annotations

import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"
HISTORICAL_PATH = ROOT / "data" / "historical_draws.csv"
MODEL_DIR = ROOT / "models" / "v45"
REPORTS_DIR = ROOT / "reports"

MODEL_JOBLIB = MODEL_DIR / "v45_number_score_model.joblib"
LATEST_SCORES_JSON = MODEL_DIR / "v45_latest_number_scores.json"
FINAL_TICKETS_JSON = MODEL_DIR / "v45_final_prediction_tickets.json"
MODEL_METADATA_JSON = MODEL_DIR / "v45_model_metadata.json"

SUMMARY_JSON = REPORTS_DIR / "v45_training_summary.json"
SUMMARY_MD = REPORTS_DIR / "v45_training_summary.md"
BACKTEST_CSV = REPORTS_DIR / "v45_backtest_results.csv"
BACKTEST_BY_MODEL_CSV = REPORTS_DIR / "v45_backtest_by_model.csv"
FEATURE_IMPORTANCE_CSV = REPORTS_DIR / "v45_feature_importance.csv"

NUMBER_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]
NUMBERS = list(range(1, 50))
EXPECTED_PROBABILITY = 6 / 49
RANDOM_SEED = 45

FEATURE_COLUMNS = [
    "number_scaled",
    "number_zone_scaled",
    "year_scaled",
    "draw_number_scaled",
    "drawing_no_scaled",
    "prior_frequency",
    "drawing_no_prior_frequency",
    "rolling_25_frequency",
    "rolling_50_frequency",
    "rolling_100_frequency",
    "rolling_250_frequency",
    "rolling_25_vs_250_trend",
    "current_gap_scaled",
    "gap_to_average_scaled",
    "gap_to_median_scaled",
    "average_gap_scaled",
    "median_gap_scaled",
    "frequency_zscore_scaled",
    "recent_presence_score",
]

MODEL_WARNING = (
    "Lottery draws are random. This model ranks historical/statistical signals; "
    "it is not a guarantee and does not prove future winning numbers."
)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    return text


def load_draw_events() -> pd.DataFrame:
    if CANONICAL_PATH.exists():
        df = pd.read_csv(CANONICAL_PATH)
        source = CANONICAL_PATH
    elif HISTORICAL_PATH.exists():
        df = pd.read_csv(HISTORICAL_PATH)
        source = HISTORICAL_PATH
        if "drawing_no" not in df.columns and "draw_position" in df.columns:
            df = df.rename(columns={"draw_position": "drawing_no"})
    else:
        raise FileNotFoundError("Missing lottery dataset. Expected data/v41_canonical_draw_events.csv or data/historical_draws.csv")

    if "drawing_no" not in df.columns:
        if "draw_position" in df.columns:
            df = df.rename(columns={"draw_position": "drawing_no"})
        else:
            df["drawing_no"] = 1

    required = {"year", "draw_number", "drawing_no", *NUMBER_COLS}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required dataset columns: {missing}")

    for col in ["year", "draw_number", "drawing_no", *NUMBER_COLS]:
        df[col] = pd.to_numeric(df[col], errors="raise").astype(int)

    if "date" not in df.columns:
        df["date"] = ""

    df = df.sort_values(["year", "draw_number", "drawing_no"]).reset_index(drop=True)
    df["event_index"] = range(len(df))
    df.attrs["source_path"] = str(source.relative_to(ROOT))
    return df


def validate_draw_events(df: pd.DataFrame) -> dict[str, Any]:
    duplicate_keys = int(df.duplicated(subset=["year", "draw_number", "drawing_no"]).sum())
    invalid_rows: list[dict[str, Any]] = []

    for idx, row in df.iterrows():
        numbers = [int(row[col]) for col in NUMBER_COLS]
        if len(set(numbers)) != 6 or not all(1 <= number <= 49 for number in numbers):
            invalid_rows.append(
                {
                    "row_index": int(idx),
                    "year": int(row["year"]),
                    "draw_number": int(row["draw_number"]),
                    "drawing_no": int(row["drawing_no"]),
                    "numbers": numbers,
                }
            )

    if duplicate_keys or invalid_rows:
        raise ValueError(
            "Dataset is not valid for v45 training. "
            f"duplicate_keys={duplicate_keys}, invalid_rows={len(invalid_rows)}"
        )

    drawing_counts = df["drawing_no"].value_counts().sort_index().to_dict()
    return {
        "total_events": int(len(df)),
        "year_min": int(df["year"].min()),
        "year_max": int(df["year"].max()),
        "drawing_no_counts": {str(int(k)): int(v) for k, v in drawing_counts.items()},
        "duplicate_keys": duplicate_keys,
        "invalid_rows": len(invalid_rows),
    }


def _empty_counter() -> Counter[int]:
    return Counter({number: 0 for number in NUMBERS})


def _safe_mean(values: list[int]) -> float:
    return float(statistics.mean(values)) if values else 49 / 6


def _safe_median(values: list[int]) -> float:
    return float(statistics.median(values)) if values else 49 / 6


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def build_feature_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict[int, set[int]], dict[int, dict[str, Any]], dict[str, Any]]:
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    max_draw_number = max(1, int(df["draw_number"].max()))
    max_drawing_no = max(1, int(df["drawing_no"].max()))

    total_seen = 0
    counts_all = _empty_counter()
    counts_by_drawing_no: dict[int, Counter[int]] = defaultdict(_empty_counter)
    drawing_events_seen: Counter[int] = Counter()
    last_seen: dict[int, int | None] = {number: None for number in NUMBERS}
    interval_history: dict[int, list[int]] = {number: [] for number in NUMBERS}
    interval_sum: dict[int, int] = {number: 0 for number in NUMBERS}
    interval_count: dict[int, int] = {number: 0 for number in NUMBERS}

    rolling_windows = {
        25: deque(maxlen=25),
        50: deque(maxlen=50),
        100: deque(maxlen=100),
        250: deque(maxlen=250),
    }
    rolling_counts = {window: _empty_counter() for window in rolling_windows}

    records: list[dict[str, Any]] = []
    targets: list[int] = []
    event_targets: dict[int, set[int]] = {}
    event_meta: dict[int, dict[str, Any]] = {}

    def rolling_frequency(number: int, window: int) -> float:
        current_len = len(rolling_windows[window])
        if current_len == 0:
            return 0.0
        return rolling_counts[window][number] / float(current_len)

    def make_features(row: pd.Series, number: int, event_index: int) -> dict[str, Any]:
        drawing_no = int(row["drawing_no"])
        year = int(row["year"])
        draw_number = int(row["draw_number"])

        prior_frequency = counts_all[number] / float(total_seen) if total_seen else 0.0
        same_drawing_seen = drawing_events_seen[drawing_no]
        drawing_no_prior_frequency = (
            counts_by_drawing_no[drawing_no][number] / float(same_drawing_seen)
            if same_drawing_seen
            else 0.0
        )

        rolling_25 = rolling_frequency(number, 25)
        rolling_50 = rolling_frequency(number, 50)
        rolling_100 = rolling_frequency(number, 100)
        rolling_250 = rolling_frequency(number, 250)
        trend = rolling_25 - rolling_250

        previous_seen = last_seen[number]
        current_gap = event_index + 1 if previous_seen is None else event_index - previous_seen
        if interval_count[number]:
            avg_gap = interval_sum[number] / float(interval_count[number])
        else:
            avg_gap = 49 / 6
        # Fast prior-only approximation. A true rolling median per row is too slow for desktop retraining.
        median_gap = avg_gap
        gap_to_avg = current_gap / avg_gap if avg_gap else 0.0
        gap_to_median = current_gap / median_gap if median_gap else 0.0

        expected_count = max(1e-9, total_seen * EXPECTED_PROBABILITY)
        std = math.sqrt(max(1e-9, total_seen * EXPECTED_PROBABILITY * (1 - EXPECTED_PROBABILITY)))
        zscore = (counts_all[number] - expected_count) / std if total_seen else 0.0

        zone = (number - 1) // 10
        if max_year == min_year:
            year_scaled = 0.0
        else:
            year_scaled = (year - min_year) / float(max_year - min_year)

        return {
            "event_index": int(event_index),
            "number": int(number),
            "number_scaled": number / 49.0,
            "number_zone_scaled": zone / 4.0,
            "year_scaled": year_scaled,
            "draw_number_scaled": draw_number / float(max_draw_number),
            "drawing_no_scaled": drawing_no / float(max_drawing_no),
            "prior_frequency": prior_frequency,
            "drawing_no_prior_frequency": drawing_no_prior_frequency,
            "rolling_25_frequency": rolling_25,
            "rolling_50_frequency": rolling_50,
            "rolling_100_frequency": rolling_100,
            "rolling_250_frequency": rolling_250,
            "rolling_25_vs_250_trend": trend,
            "current_gap_scaled": _clip(current_gap, 0, 300) / 300.0,
            "gap_to_average_scaled": _clip(gap_to_avg, 0, 5) / 5.0,
            "gap_to_median_scaled": _clip(gap_to_median, 0, 5) / 5.0,
            "average_gap_scaled": _clip(avg_gap, 0, 100) / 100.0,
            "median_gap_scaled": _clip(median_gap, 0, 100) / 100.0,
            "frequency_zscore_scaled": _clip(zscore, -5, 5) / 5.0,
            "recent_presence_score": (0.45 * rolling_25) + (0.35 * rolling_50) + (0.20 * rolling_100),
            "raw_current_gap": int(current_gap),
            "raw_average_gap": float(avg_gap),
            "raw_median_gap": float(median_gap),
            "raw_total_hits": int(counts_all[number]),
        }

    for _, row in df.iterrows():
        event_index = int(row["event_index"])
        current_numbers = {int(row[col]) for col in NUMBER_COLS}

        event_targets[event_index] = current_numbers
        event_meta[event_index] = {
            "year": int(row["year"]),
            "draw_number": int(row["draw_number"]),
            "drawing_no": int(row["drawing_no"]),
            "date": clean_text(row.get("date", "")),
        }

        for number in NUMBERS:
            records.append(make_features(row, number, event_index))
            targets.append(1 if number in current_numbers else 0)

        total_seen += 1
        drawing_no = int(row["drawing_no"])
        drawing_events_seen[drawing_no] += 1

        for number in current_numbers:
            previous_seen = last_seen[number]
            if previous_seen is not None:
                interval = event_index - previous_seen
                interval_history[number].append(interval)
                interval_sum[number] += interval
                interval_count[number] += 1
            last_seen[number] = event_index
            counts_all[number] += 1
            counts_by_drawing_no[drawing_no][number] += 1

        for window, history in rolling_windows.items():
            if len(history) == history.maxlen:
                oldest = history[0]
                for number in oldest:
                    rolling_counts[window][number] -= 1
            history.append(current_numbers)
            for number in current_numbers:
                rolling_counts[window][number] += 1

    feature_df = pd.DataFrame(records)
    target = pd.Series(targets, name="target")

    final_state = {
        "min_year": min_year,
        "max_year": max_year,
        "max_draw_number": max_draw_number,
        "max_drawing_no": max_drawing_no,
        "total_seen": int(total_seen),
        "counts_all": {str(k): int(v) for k, v in counts_all.items()},
        "counts_by_drawing_no": {str(k): {str(n): int(c) for n, c in v.items()} for k, v in counts_by_drawing_no.items()},
        "drawing_events_seen": {str(k): int(v) for k, v in drawing_events_seen.items()},
        "last_seen": {str(k): (None if v is None else int(v)) for k, v in last_seen.items()},
        "interval_history": {str(k): [int(x) for x in v] for k, v in interval_history.items()},
        "rolling_counts": {str(w): {str(n): int(c) for n, c in counts.items()} for w, counts in rolling_counts.items()},
        "rolling_lengths": {str(w): len(history) for w, history in rolling_windows.items()},
    }

    feature_df["gap_rhythm_score"] = (
        0.28 * feature_df["rolling_250_frequency"]
        + 0.22 * feature_df["recent_presence_score"]
        + 0.22 * feature_df["gap_to_average_scaled"]
        + 0.16 * feature_df["gap_to_median_scaled"]
        + 0.12 * feature_df["frequency_zscore_scaled"].clip(lower=0)
    )

    return feature_df, target, event_targets, event_meta, final_state


def _rank_percentile(group: pd.Series) -> pd.Series:
    return group.rank(method="average", pct=True)


def add_ensemble_score(feature_df: pd.DataFrame, columns: list[tuple[str, float]], output_col: str) -> None:
    """Add an event-local rank ensemble score.

    Each event has 49 rows, one per number. A vectorized rank calculation keeps
    the desktop refresh flow fast and avoids expensive pandas groupby ranks.
    """
    import numpy as np

    feature_df[output_col] = 0.0
    usable_columns = [(col, weight) for col, weight in columns if col in feature_df.columns]
    total_weight = sum(weight for _, weight in usable_columns)
    if total_weight <= 0:
        return

    event_sizes = feature_df.groupby("event_index", sort=False).size().to_numpy()
    if len(event_sizes) and np.all(event_sizes == 49):
        row_count = len(feature_df)
        event_count = row_count // 49
        final = np.zeros(row_count, dtype=float)
        for col, weight in usable_columns:
            values = feature_df[col].to_numpy(dtype=float).reshape(event_count, 49)
            order = np.argsort(values, axis=1)
            ranks = np.empty_like(order, dtype=float)
            rank_values = np.arange(1, 50, dtype=float) / 49.0
            rows = np.arange(event_count)[:, None]
            ranks[rows, order] = rank_values
            final += ranks.reshape(row_count) * (weight / total_weight)
        feature_df[output_col] = final
        return

    # Safe fallback for unusual frames.
    for event_index, indexes in feature_df.groupby("event_index", sort=False).groups.items():
        local = feature_df.loc[indexes]
        total = pd.Series(0.0, index=local.index)
        for col, weight in usable_columns:
            total += local[col].rank(method="average", pct=True) * (weight / total_weight)
        feature_df.loc[local.index, output_col] = total

def top_numbers_from_scores(scores: pd.DataFrame, score_col: str, top_n: int = 6) -> list[int]:
    ranked = scores.sort_values([score_col, "number"], ascending=[False, True])
    return [int(x) for x in ranked.head(top_n)["number"].tolist()]


def evaluate_score_column(
    feature_df: pd.DataFrame,
    event_targets: dict[int, set[int]],
    event_meta: dict[int, dict[str, Any]],
    test_events: list[int],
    score_col: str,
    model_name: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    import numpy as np

    rows: list[dict[str, Any]] = []
    hits: list[int] = []
    values = feature_df[score_col].to_numpy(dtype=float)

    fast_layout = len(feature_df) % 49 == 0
    for event_index in test_events:
        if fast_layout:
            start = event_index * 49
            end = start + 49
            block = values[start:end]
            if len(block) != 49:
                event_scores = feature_df.loc[feature_df["event_index"] == event_index, ["number", score_col]].copy()
                top6 = top_numbers_from_scores(event_scores, score_col, 6)
            else:
                safe_block = np.nan_to_num(block, nan=-1e9, neginf=-1e9, posinf=1e9)
                order = np.argsort(-safe_block, kind="mergesort")[:6]
                top6 = sorted(int(i + 1) for i in order)
        else:
            event_scores = feature_df.loc[feature_df["event_index"] == event_index, ["number", score_col]].copy()
            top6 = top_numbers_from_scores(event_scores, score_col, 6)

        actual = event_targets[event_index]
        matched = sorted(set(top6) & actual)
        hit_count = len(matched)
        hits.append(hit_count)
        meta = event_meta[event_index]
        rows.append(
            {
                "model": model_name,
                "event_index": event_index,
                "year": meta["year"],
                "draw_number": meta["draw_number"],
                "drawing_no": meta["drawing_no"],
                "date": meta.get("date", ""),
                "predicted_top6": " ".join(str(x) for x in top6),
                "actual_numbers": " ".join(str(x) for x in sorted(actual)),
                "matched_numbers": " ".join(str(x) for x in matched),
                "hit_count": hit_count,
            }
        )

    distribution = Counter(hits)
    metrics = {
        "model": model_name,
        "test_events": len(test_events),
        "average_hits_top6": float(statistics.mean(hits)) if hits else 0.0,
        "median_hits_top6": float(statistics.median(hits)) if hits else 0.0,
        "max_hits_top6": int(max(hits)) if hits else 0,
        "hit_distribution": {str(k): int(v) for k, v in sorted(distribution.items())},
        "events_with_3plus_hits": int(sum(1 for value in hits if value >= 3)),
        "events_with_4plus_hits": int(sum(1 for value in hits if value >= 4)),
        "events_with_5plus_hits": int(sum(1 for value in hits if value >= 5)),
        "events_with_6_hits": int(sum(1 for value in hits if value == 6)),
    }
    return metrics, rows

def evaluate_random_baseline(
    event_targets: dict[int, set[int]],
    event_meta: dict[int, dict[str, Any]],
    test_events: list[int],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    hits: list[int] = []
    for event_index in test_events:
        rng = random.Random(RANDOM_SEED + event_index)
        top6 = sorted(rng.sample(NUMBERS, 6))
        actual = event_targets[event_index]
        matched = sorted(set(top6) & actual)
        hit_count = len(matched)
        hits.append(hit_count)
        meta = event_meta[event_index]
        rows.append(
            {
                "model": "random_baseline",
                "event_index": event_index,
                "year": meta["year"],
                "draw_number": meta["draw_number"],
                "drawing_no": meta["drawing_no"],
                "date": meta.get("date", ""),
                "predicted_top6": " ".join(str(x) for x in top6),
                "actual_numbers": " ".join(str(x) for x in sorted(actual)),
                "matched_numbers": " ".join(str(x) for x in matched),
                "hit_count": hit_count,
            }
        )
    distribution = Counter(hits)
    return {
        "model": "random_baseline",
        "test_events": len(test_events),
        "average_hits_top6": float(statistics.mean(hits)) if hits else 0.0,
        "median_hits_top6": float(statistics.median(hits)) if hits else 0.0,
        "max_hits_top6": int(max(hits)) if hits else 0,
        "hit_distribution": {str(k): int(v) for k, v in sorted(distribution.items())},
        "events_with_3plus_hits": int(sum(1 for value in hits if value >= 3)),
        "events_with_4plus_hits": int(sum(1 for value in hits if value >= 4)),
        "events_with_5plus_hits": int(sum(1 for value in hits if value >= 5)),
        "events_with_6_hits": int(sum(1 for value in hits if value == 6)),
    }, rows


def train_sklearn_models(
    feature_df: pd.DataFrame,
    target: pd.Series,
    train_events: list[int],
    test_events: list[int],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Train fast per-number probability rankers.

    The project is a desktop Streamlit app, so this intentionally uses fast models.
    Heavy models can make the manual update flow feel broken on normal laptops.
    """
    status: dict[str, Any] = {"sklearn_available": False, "models": {}}

    try:
        import joblib
        from sklearn.linear_model import SGDClassifier
        from sklearn.naive_bayes import GaussianNB
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except Exception as exc:
        status["reason"] = f"sklearn_or_joblib_unavailable: {exc}"
        pd.DataFrame(
            [{"model": "none", "feature": "not_available", "importance": 0.0, "signed_value": 0.0, "source": "sklearn_unavailable"}]
        ).to_csv(FEATURE_IMPORTANCE_CSV, index=False, encoding="utf-8-sig")
        return status, []

    status["sklearn_available"] = True
    train_mask = feature_df["event_index"].isin(train_events)
    test_mask = feature_df["event_index"].isin(test_events)

    X_train = feature_df.loc[train_mask, FEATURE_COLUMNS]
    y_train = target.loc[train_mask]
    X_test = feature_df.loc[test_mask, FEATURE_COLUMNS]

    trained_models: list[tuple[str, Any, str]] = []

    try:
        try:
            classifier = SGDClassifier(
                loss="log_loss",
                alpha=0.0006,
                max_iter=800,
                tol=1e-3,
                class_weight="balanced",
                random_state=RANDOM_SEED,
            )
        except TypeError:
            classifier = SGDClassifier(
                loss="log",
                alpha=0.0006,
                max_iter=800,
                tol=1e-3,
                class_weight="balanced",
                random_state=RANDOM_SEED,
            )
        sgd_model = make_pipeline(StandardScaler(), classifier)
        sgd_model.fit(X_train, y_train)
        feature_df.loc[test_mask, "sgd_log_probability"] = sgd_model.predict_proba(X_test)[:, 1]
        trained_models.append(("sgd_log_probability", sgd_model, "sgd_logistic_probability"))
        status["models"]["sgd_logistic_probability"] = "trained"
    except Exception as exc:
        status["models"]["sgd_logistic_probability"] = f"skipped: {exc}"

    try:
        nb_model = GaussianNB()
        nb_model.fit(X_train, y_train)
        feature_df.loc[test_mask, "gaussian_nb_probability"] = nb_model.predict_proba(X_test)[:, 1]
        trained_models.append(("gaussian_nb_probability", nb_model, "gaussian_naive_bayes"))
        status["models"]["gaussian_naive_bayes"] = "trained"
    except Exception as exc:
        status["models"]["gaussian_naive_bayes"] = f"skipped: {exc}"

    if trained_models:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "model_name": "v45_prediction_engine_pro",
            "model_type": "per_number_binary_ranker",
            "feature_columns": FEATURE_COLUMNS,
            "models": {model_name: model for _, model, model_name in trained_models},
            "warning": MODEL_WARNING,
        }
        joblib.dump(payload, MODEL_JOBLIB)

        importance_rows: list[dict[str, Any]] = []
        for _, model, model_name in trained_models:
            if model_name == "sgd_logistic_probability":
                try:
                    estimator = model.named_steps.get("sgdclassifier")
                    coefs = estimator.coef_[0]
                    for feature, coef in zip(FEATURE_COLUMNS, coefs):
                        importance_rows.append(
                            {
                                "model": model_name,
                                "feature": feature,
                                "importance": float(abs(coef)),
                                "signed_value": float(coef),
                                "source": "absolute_sgd_logistic_coefficient",
                            }
                        )
                except Exception:
                    pass
        if importance_rows:
            pd.DataFrame(importance_rows).sort_values(
                ["model", "importance"], ascending=[True, False]
            ).to_csv(FEATURE_IMPORTANCE_CSV, index=False, encoding="utf-8-sig")
        else:
            pd.DataFrame(
                [{"model": "none", "feature": "not_available", "importance": 0.0, "signed_value": 0.0, "source": "fallback"}]
            ).to_csv(FEATURE_IMPORTANCE_CSV, index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame(
            [{"model": "none", "feature": "not_available", "importance": 0.0, "signed_value": 0.0, "source": "no_sklearn_model_trained"}]
        ).to_csv(FEATURE_IMPORTANCE_CSV, index=False, encoding="utf-8-sig")

    return status, trained_models

def build_next_features(final_state: dict[str, Any], latest_row: pd.Series) -> pd.DataFrame:
    min_year = int(final_state["min_year"])
    max_year = int(final_state["max_year"])
    max_draw_number = max(1, int(final_state["max_draw_number"]))
    max_drawing_no = max(1, int(final_state["max_drawing_no"]))
    total_seen = int(final_state["total_seen"])

    counts_all = {int(k): int(v) for k, v in final_state["counts_all"].items()}
    counts_by_drawing_no = {
        int(k): {int(n): int(c) for n, c in v.items()}
        for k, v in final_state["counts_by_drawing_no"].items()
    }
    drawing_events_seen = {int(k): int(v) for k, v in final_state["drawing_events_seen"].items()}
    last_seen = {int(k): (None if v is None else int(v)) for k, v in final_state["last_seen"].items()}
    interval_history = {int(k): [int(x) for x in v] for k, v in final_state["interval_history"].items()}
    rolling_counts = {
        int(w): {int(n): int(c) for n, c in counts.items()}
        for w, counts in final_state["rolling_counts"].items()
    }
    rolling_lengths = {int(w): max(1, int(v)) for w, v in final_state["rolling_lengths"].items()}

    next_year = int(latest_row["year"])
    next_draw_number = int(latest_row["draw_number"]) + 1
    next_drawing_no = 1
    next_event_index = total_seen

    rows: list[dict[str, Any]] = []
    for number in NUMBERS:
        prior_frequency = counts_all.get(number, 0) / float(max(1, total_seen))
        same_drawing_seen = drawing_events_seen.get(next_drawing_no, 0)
        drawing_no_prior_frequency = (
            counts_by_drawing_no.get(next_drawing_no, {}).get(number, 0) / float(same_drawing_seen)
            if same_drawing_seen
            else 0.0
        )
        rolling_25 = rolling_counts.get(25, {}).get(number, 0) / float(rolling_lengths.get(25, 1))
        rolling_50 = rolling_counts.get(50, {}).get(number, 0) / float(rolling_lengths.get(50, 1))
        rolling_100 = rolling_counts.get(100, {}).get(number, 0) / float(rolling_lengths.get(100, 1))
        rolling_250 = rolling_counts.get(250, {}).get(number, 0) / float(rolling_lengths.get(250, 1))

        previous_seen = last_seen.get(number)
        current_gap = next_event_index + 1 if previous_seen is None else next_event_index - previous_seen
        gaps = interval_history.get(number, [])
        avg_gap = _safe_mean(gaps)
        median_gap = _safe_median(gaps)
        gap_to_avg = current_gap / avg_gap if avg_gap else 0.0
        gap_to_median = current_gap / median_gap if median_gap else 0.0

        expected_count = max(1e-9, total_seen * EXPECTED_PROBABILITY)
        std = math.sqrt(max(1e-9, total_seen * EXPECTED_PROBABILITY * (1 - EXPECTED_PROBABILITY)))
        zscore = (counts_all.get(number, 0) - expected_count) / std if total_seen else 0.0
        zone = (number - 1) // 10
        year_scaled = 0.0 if max_year == min_year else (next_year - min_year) / float(max_year - min_year)

        rows.append(
            {
                "event_index": next_event_index,
                "number": number,
                "number_scaled": number / 49.0,
                "number_zone_scaled": zone / 4.0,
                "year_scaled": year_scaled,
                "draw_number_scaled": next_draw_number / float(max_draw_number),
                "drawing_no_scaled": next_drawing_no / float(max_drawing_no),
                "prior_frequency": prior_frequency,
                "drawing_no_prior_frequency": drawing_no_prior_frequency,
                "rolling_25_frequency": rolling_25,
                "rolling_50_frequency": rolling_50,
                "rolling_100_frequency": rolling_100,
                "rolling_250_frequency": rolling_250,
                "rolling_25_vs_250_trend": rolling_25 - rolling_250,
                "current_gap_scaled": _clip(current_gap, 0, 300) / 300.0,
                "gap_to_average_scaled": _clip(gap_to_avg, 0, 5) / 5.0,
                "gap_to_median_scaled": _clip(gap_to_median, 0, 5) / 5.0,
                "average_gap_scaled": _clip(avg_gap, 0, 100) / 100.0,
                "median_gap_scaled": _clip(median_gap, 0, 100) / 100.0,
                "frequency_zscore_scaled": _clip(zscore, -5, 5) / 5.0,
                "recent_presence_score": (0.45 * rolling_25) + (0.35 * rolling_50) + (0.20 * rolling_100),
                "raw_current_gap": int(current_gap),
                "raw_average_gap": float(avg_gap),
                "raw_median_gap": float(median_gap),
                "raw_total_hits": int(counts_all.get(number, 0)),
            }
        )

    next_df = pd.DataFrame(rows)
    next_df["gap_rhythm_score"] = (
        0.28 * next_df["rolling_250_frequency"]
        + 0.22 * next_df["recent_presence_score"]
        + 0.22 * next_df["gap_to_average_scaled"]
        + 0.16 * next_df["gap_to_median_scaled"]
        + 0.12 * next_df["frequency_zscore_scaled"].clip(lower=0)
    )
    return next_df


def score_next_with_models(next_df: pd.DataFrame) -> dict[str, str]:
    status: dict[str, str] = {}
    try:
        import joblib
    except Exception as exc:
        return {"joblib": f"unavailable: {exc}"}

    if not MODEL_JOBLIB.exists():
        return {"model_file": "not_created"}

    payload = joblib.load(MODEL_JOBLIB)
    models = payload.get("models", {})
    for model_name, model in models.items():
        try:
            col = "sgd_log_probability" if model_name == "sgd_logistic_probability" else f"{model_name}_probability"
            if model_name == "gaussian_naive_bayes":
                col = "gaussian_nb_probability"
            next_df[col] = model.predict_proba(next_df[FEATURE_COLUMNS])[:, 1]
            status[model_name] = "scored"
        except Exception as exc:
            status[model_name] = f"score_failed: {exc}"
    return status


def _combination_structure(numbers: list[int]) -> dict[str, Any]:
    numbers = sorted(int(n) for n in numbers)
    odd_count = sum(1 for n in numbers if n % 2)
    low_count = sum(1 for n in numbers if n <= 24)
    total_sum = sum(numbers)
    zones = Counter((n - 1) // 10 for n in numbers)
    consecutive_pairs = sum(1 for a, b in zip(numbers, numbers[1:]) if b == a + 1)
    max_zone_count = max(zones.values()) if zones else 0
    return {
        "odd_count": odd_count,
        "even_count": 6 - odd_count,
        "low_count": low_count,
        "high_count": 6 - low_count,
        "sum": total_sum,
        "consecutive_pairs": consecutive_pairs,
        "max_zone_count": max_zone_count,
        "zones": {str(k): int(v) for k, v in sorted(zones.items())},
    }


def _structure_penalty(numbers: tuple[int, ...]) -> float:
    s = _combination_structure(list(numbers))
    penalty = 0.0
    if not (2 <= s["odd_count"] <= 4):
        penalty += 0.09
    if not (2 <= s["low_count"] <= 4):
        penalty += 0.08
    if not (95 <= s["sum"] <= 205):
        penalty += 0.08
    if not (110 <= s["sum"] <= 190):
        penalty += 0.04
    if s["consecutive_pairs"] > 2:
        penalty += 0.06 * (s["consecutive_pairs"] - 2)
    if s["max_zone_count"] > 3:
        penalty += 0.07 * (s["max_zone_count"] - 3)
    return penalty


def _select_combinations(next_df: pd.DataFrame, score_col: str = "pro_ensemble_score", ticket_count: int = 4) -> list[dict[str, Any]]:
    scores = {int(row["number"]): float(row[score_col]) for _, row in next_df.iterrows()}
    top_pool = [int(x) for x in next_df.sort_values(score_col, ascending=False).head(22)["number"].tolist()]

    candidates: list[tuple[float, tuple[int, ...], dict[str, Any]]] = []
    for combo in combinations(sorted(top_pool), 6):
        base_score = sum(scores[n] for n in combo) / 6.0
        penalty = _structure_penalty(combo)
        final_score = base_score - penalty
        candidates.append((final_score, combo, _combination_structure(list(combo))))

    candidates.sort(key=lambda item: (-item[0], item[1]))
    selected: list[tuple[float, tuple[int, ...], dict[str, Any]]] = []
    for final_score, combo, structure in candidates:
        if any(len(set(combo) & set(chosen)) > 2 for _, chosen, _ in selected):
            continue
        selected.append((final_score, combo, structure))
        if len(selected) >= ticket_count:
            break

    if len(selected) < ticket_count:
        for item in candidates:
            if item not in selected:
                selected.append(item)
            if len(selected) >= ticket_count:
                break

    labels = [
        "primary_rule_aware_ml_ensemble",
        "coverage_low_overlap",
        "rhythm_weighted_alternative",
        "historical_signal_alternative",
    ]
    tickets: list[dict[str, Any]] = []
    for index, (final_score, combo, structure) in enumerate(selected, start=1):
        numbers = list(combo)
        tickets.append(
            {
                "ticket_index": index,
                "label": labels[index - 1] if index <= len(labels) else "coverage_alternative",
                "numbers": numbers,
                "average_score": float(final_score),
                "structure": structure,
                "number_details": _number_details_for_combo(next_df, numbers),
            }
        )
    return tickets


def _number_details_for_combo(next_df: pd.DataFrame, numbers: list[int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lookup = {int(row["number"]): row for _, row in next_df.iterrows()}
    for number in numbers:
        row = lookup[int(number)]
        reasons: list[str] = []
        if float(row.get("pro_ensemble_score", 0)) >= float(next_df["pro_ensemble_score"].quantile(0.75)):
            reasons.append("strong_ensemble_rank")
        if float(row.get("rolling_250_frequency", 0)) >= EXPECTED_PROBABILITY:
            reasons.append("above_expected_recent_frequency")
        if float(row.get("gap_to_average_scaled", 0)) >= 0.2:
            reasons.append("interesting_interval_profile")
        if "sgd_log_probability" in next_df.columns and float(row.get("sgd_log_probability", 0)) >= float(next_df["sgd_log_probability"].quantile(0.70)):
            reasons.append("ml_probability_support")
        rows.append(
            {
                "number": int(number),
                "pro_ensemble_score": float(row.get("pro_ensemble_score", 0)),
                "prior_frequency": float(row.get("prior_frequency", 0)),
                "rolling_250_frequency": float(row.get("rolling_250_frequency", 0)),
                "gap_rhythm_score": float(row.get("gap_rhythm_score", 0)),
                "sgd_log_probability": None if "sgd_log_probability" not in next_df.columns else float(row.get("sgd_log_probability", 0)),
                "gaussian_nb_probability": None if "gaussian_nb_probability" not in next_df.columns else float(row.get("gaussian_nb_probability", 0)),
                "current_gap": int(row.get("raw_current_gap", 0)),
                "average_gap": float(row.get("raw_average_gap", 0)),
                "median_gap": float(row.get("raw_median_gap", 0)),
                "total_hits": int(row.get("raw_total_hits", 0)),
                "reasons": reasons,
            }
        )
    return rows


def save_next_outputs(
    df: pd.DataFrame,
    next_df: pd.DataFrame,
    tickets: list[dict[str, Any]],
    dataset_audit: dict[str, Any],
    sklearn_status: dict[str, Any],
    model_metrics: list[dict[str, Any]],
) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    latest_row = df.iloc[-1]
    top_scores = []
    score_cols = [
        "prior_frequency",
        "rolling_250_frequency",
        "gap_rhythm_score",
        "sgd_log_probability",
        "gaussian_nb_probability",
        "pro_ensemble_score",
    ]
    for _, row in next_df.sort_values("pro_ensemble_score", ascending=False).iterrows():
        item = {
            "number": int(row["number"]),
            "rank": int(len(top_scores) + 1),
            "current_gap": int(row.get("raw_current_gap", 0)),
            "average_gap": float(row.get("raw_average_gap", 0)),
            "median_gap": float(row.get("raw_median_gap", 0)),
            "total_hits": int(row.get("raw_total_hits", 0)),
        }
        for col in score_cols:
            if col in next_df.columns:
                value = row.get(col)
                item[col] = None if pd.isna(value) else float(value)
        top_scores.append(item)

    latest_scores_payload = {
        "status": "v45_prediction_engine_pro_scores_ready",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset_audit,
        "latest_seen_event": {
            "year": int(latest_row["year"]),
            "draw_number": int(latest_row["draw_number"]),
            "drawing_no": int(latest_row["drawing_no"]),
            "date": clean_text(latest_row.get("date", "")),
            "numbers": [int(latest_row[col]) for col in NUMBER_COLS],
        },
        "next_event_assumption": {
            "year": int(latest_row["year"]),
            "draw_number": int(latest_row["draw_number"]) + 1,
            "drawing_no": 1,
        },
        "uses_bonus_number": False,
        "numbers": top_scores,
        "warning": MODEL_WARNING,
    }
    LATEST_SCORES_JSON.write_text(json.dumps(latest_scores_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    final_payload = {
        "status": "v45_prediction_engine_pro_tickets_ready",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "valid_draws": int(len(df)),
        "uses_bonus_number": False,
        "primary_numbers": tickets[0]["numbers"] if tickets else [],
        "ticket_combinations": tickets,
        "selection_rules": {
            "max_overlap_between_generated_tickets": 2,
            "preferred_odd_count": "2..4",
            "preferred_low_count_1_to_24": "2..4",
            "preferred_sum_range": "110..190 soft, 95..205 hard",
            "max_zone_concentration_soft": 3,
        },
        "model_metrics": model_metrics,
        "warning": MODEL_WARNING,
    }
    FINAL_TICKETS_JSON.write_text(json.dumps(final_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    metadata = {
        "model_name": "v45_prediction_engine_pro",
        "model_type": "per_number_binary_models_plus_rule_aware_selector",
        "feature_columns": FEATURE_COLUMNS,
        "dataset_source": df.attrs.get("source_path", ""),
        "dataset_audit": dataset_audit,
        "sklearn_status": sklearn_status,
        "outputs": [
            str(MODEL_JOBLIB.relative_to(ROOT)) if MODEL_JOBLIB.exists() else "",
            str(LATEST_SCORES_JSON.relative_to(ROOT)),
            str(FINAL_TICKETS_JSON.relative_to(ROOT)),
            str(SUMMARY_JSON.relative_to(ROOT)),
            str(BACKTEST_CSV.relative_to(ROOT)),
            str(BACKTEST_BY_MODEL_CSV.relative_to(ROOT)),
            str(FEATURE_IMPORTANCE_CSV.relative_to(ROOT)),
        ],
        "warning": MODEL_WARNING,
    }
    MODEL_METADATA_JSON.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def write_reports(summary: dict[str, Any], metrics: list[dict[str, Any]], backtest_rows: list[dict[str, Any]]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(backtest_rows).to_csv(BACKTEST_CSV, index=False, encoding="utf-8-sig")
    pd.DataFrame(metrics).to_csv(BACKTEST_BY_MODEL_CSV, index=False, encoding="utf-8-sig")

    best = summary.get("best_model_by_average_hits_top6", {})
    primary = summary.get("primary_numbers", [])
    lines = [
        "# v45 Prediction Engine Pro Training Summary",
        "",
        "Status: v45 training pipeline completed.",
        "",
        "## Safety note",
        "",
        "Lottery draws are random. These outputs are statistical rankings and rule-aware ticket suggestions, not guaranteed winning numbers.",
        "",
        "## Dataset",
        "",
        f"- Source: `{summary.get('dataset_source', '')}`",
        f"- Valid draw events: {summary.get('total_draw_events')}",
        f"- Years: {summary.get('year_min')}–{summary.get('year_max')}",
        f"- Train events: {summary.get('train_events')}",
        f"- Test events: {summary.get('test_events')}",
        f"- Bonus numbers used: {summary.get('uses_bonus_number')}",
        "",
        "## Best historical-check model",
        "",
        f"- Model: `{best.get('model', '-')}`",
        f"- Average hits in top 6: {best.get('average_hits_top6', 0):.4f}",
        f"- Max hits in top 6: {best.get('max_hits_top6', 0)}",
        "",
        "## Current primary rule-aware suggestion",
        "",
        f"- Numbers: **{' '.join(str(n) for n in primary)}**",
        "",
        "## Models compared",
        "",
    ]
    for item in metrics:
        lines.append(
            f"- `{item['model']}`: avg={item['average_hits_top6']:.4f}, max={item['max_hits_top6']}, 3+ events={item['events_with_3plus_hits']}"
        )
    lines.extend(
        [
            "",
            "## Output files",
            "",
            f"- `{LATEST_SCORES_JSON.relative_to(ROOT)}`",
            f"- `{FINAL_TICKETS_JSON.relative_to(ROOT)}`",
            f"- `{MODEL_METADATA_JSON.relative_to(ROOT)}`",
            f"- `{BACKTEST_CSV.relative_to(ROOT)}`",
            f"- `{BACKTEST_BY_MODEL_CSV.relative_to(ROOT)}`",
            f"- `{FEATURE_IMPORTANCE_CSV.relative_to(ROOT)}`",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_draw_events()
    dataset_audit = validate_draw_events(df)
    feature_df, target, event_targets, event_meta, final_state = build_feature_frame(df)

    total_events = int(df["event_index"].nunique())
    test_events_count = min(max(500, int(round(total_events * 0.2))), max(1, total_events - 300))
    train_cutoff = total_events - test_events_count
    train_events = list(range(0, train_cutoff))
    test_events = list(range(train_cutoff, total_events))

    all_metrics: list[dict[str, Any]] = []
    backtest_rows: list[dict[str, Any]] = []

    for score_col, model_name in [
        ("prior_frequency", "frequency_baseline"),
        ("rolling_250_frequency", "recency_250_baseline"),
        ("gap_rhythm_score", "gap_rhythm_statistical"),
    ]:
        metrics, rows = evaluate_score_column(feature_df, event_targets, event_meta, test_events, score_col, model_name)
        all_metrics.append(metrics)
        backtest_rows.extend(rows)

    random_metrics, random_rows = evaluate_random_baseline(event_targets, event_meta, test_events)
    all_metrics.append(random_metrics)
    backtest_rows.extend(random_rows)

    sklearn_status, trained_models = train_sklearn_models(feature_df, target, train_events, test_events)
    for score_col, _, model_name in trained_models:
        metrics, rows = evaluate_score_column(feature_df, event_targets, event_meta, test_events, score_col, model_name)
        all_metrics.append(metrics)
        backtest_rows.extend(rows)

    ensemble_cols = [
        ("prior_frequency", 0.14),
        ("rolling_250_frequency", 0.16),
        ("gap_rhythm_score", 0.22),
        ("sgd_log_probability", 0.30),
        ("gaussian_nb_probability", 0.18),
    ]
    add_ensemble_score(feature_df, ensemble_cols, "pro_ensemble_score")
    ensemble_metrics, ensemble_rows = evaluate_score_column(
        feature_df,
        event_targets,
        event_meta,
        test_events,
        "pro_ensemble_score",
        "v45_pro_ensemble",
    )
    all_metrics.append(ensemble_metrics)
    backtest_rows.extend(ensemble_rows)

    latest_row = df.iloc[-1]
    next_df = build_next_features(final_state, latest_row)
    next_model_status = score_next_with_models(next_df)
    add_ensemble_score(next_df, ensemble_cols, "pro_ensemble_score")
    tickets = _select_combinations(next_df, "pro_ensemble_score", ticket_count=4)

    best_model = sorted(all_metrics, key=lambda item: item["average_hits_top6"], reverse=True)[0]
    summary = {
        "status": "v45_training_pipeline_completed",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_source": df.attrs.get("source_path", ""),
        "total_draw_events": total_events,
        "year_min": dataset_audit["year_min"],
        "year_max": dataset_audit["year_max"],
        "train_events": len(train_events),
        "test_events": len(test_events),
        "uses_bonus_number": False,
        "bonus_model_trained": False,
        "feature_rows": int(len(feature_df)),
        "feature_columns": FEATURE_COLUMNS,
        "sklearn_status": sklearn_status,
        "next_model_status": next_model_status,
        "model_metrics": all_metrics,
        "best_model_by_average_hits_top6": best_model,
        "primary_numbers": tickets[0]["numbers"] if tickets else [],
        "ticket_count": len(tickets),
        "outputs": [
            str(MODEL_JOBLIB.relative_to(ROOT)) if MODEL_JOBLIB.exists() else "",
            str(LATEST_SCORES_JSON.relative_to(ROOT)),
            str(FINAL_TICKETS_JSON.relative_to(ROOT)),
            str(MODEL_METADATA_JSON.relative_to(ROOT)),
            str(SUMMARY_JSON.relative_to(ROOT)),
            str(SUMMARY_MD.relative_to(ROOT)),
            str(BACKTEST_CSV.relative_to(ROOT)),
            str(BACKTEST_BY_MODEL_CSV.relative_to(ROOT)),
            str(FEATURE_IMPORTANCE_CSV.relative_to(ROOT)),
        ],
        "warning": MODEL_WARNING,
    }

    save_next_outputs(df, next_df, tickets, dataset_audit, sklearn_status, all_metrics)
    write_reports(summary, all_metrics, backtest_rows)

    print("V45_STATUS", summary["status"])
    print("DATASET_EVENTS", total_events)
    print("FEATURE_ROWS", len(feature_df))
    print("TRAIN_EVENTS", len(train_events))
    print("TEST_EVENTS", len(test_events))
    print("PRIMARY_NUMBERS", summary["primary_numbers"])
    print("BEST_MODEL", best_model["model"], f"avg_hits={best_model['average_hits_top6']:.4f}")
    print("OUTPUT", FINAL_TICKETS_JSON.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

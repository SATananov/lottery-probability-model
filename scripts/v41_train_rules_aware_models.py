from __future__ import annotations

import json
import math
import statistics
from collections import Counter, deque, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

CANONICAL_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"

MODEL_DIR = ROOT / "models" / "v41"
REPORT_JSON = ROOT / "reports" / "v41_model_retraining_summary.json"
REPORT_MD = ROOT / "reports" / "v41_model_retraining_summary.md"
BACKTEST_CSV = ROOT / "reports" / "v41_model_backtest_events.csv"
PREDICTIONS_JSON = MODEL_DIR / "v41_latest_predictions.json"

FREQUENCY_MODEL_JSON = MODEL_DIR / "v41_frequency_main_numbers_model.json"
RECENCY_MODEL_JSON = MODEL_DIR / "v41_recency_main_numbers_model.json"
SGD_MODEL_PATH = MODEL_DIR / "v41_sgd_number_model.joblib"
SGD_MODEL_META_JSON = MODEL_DIR / "v41_sgd_number_model_metadata.json"

NUMBER_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]
NUMBERS = list(range(1, 50))

FEATURE_COLUMNS = [
    "number_scaled",
    "drawing_no_scaled",
    "year_scaled",
    "draw_number_scaled",
    "prior_frequency",
    "drawing_no_prior_frequency",
    "rolling_50_frequency",
    "rolling_250_frequency",
    "since_seen_scaled",
]


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "nat"}:
        return ""
    return text


def load_canonical_dataset() -> pd.DataFrame:
    if not CANONICAL_PATH.exists():
        raise FileNotFoundError(f"Missing canonical dataset: {CANONICAL_PATH}")

    df = pd.read_csv(CANONICAL_PATH)

    required = {
        "year",
        "draw_number",
        "drawing_no",
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
        "n6",
    }

    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for col in ["year", "draw_number", "drawing_no", *NUMBER_COLS]:
        df[col] = df[col].astype(int)

    df = df.sort_values(["year", "draw_number", "drawing_no"]).reset_index(drop=True)
    df["event_index"] = range(len(df))

    return df


def validate_dataset(df: pd.DataFrame) -> None:
    duplicate_keys = df.duplicated(subset=["year", "draw_number", "drawing_no"]).sum()
    if duplicate_keys:
        raise ValueError(f"Duplicate draw event keys found: {duplicate_keys}")

    for index, row in df.iterrows():
        numbers = [int(row[col]) for col in NUMBER_COLS]

        if len(numbers) != 6:
            raise ValueError(f"Invalid number count at row {index}: {numbers}")

        if len(set(numbers)) != 6:
            raise ValueError(f"Duplicate numbers at row {index}: {numbers}")

        if not all(1 <= number <= 49 for number in numbers):
            raise ValueError(f"Numbers outside 1..49 at row {index}: {numbers}")


def empty_counter() -> Counter[int]:
    return Counter({number: 0 for number in NUMBERS})


def build_feature_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict[int, set[int]], dict[int, dict[str, Any]], dict[str, Any]]:
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    max_draw_number = max(1, int(df["draw_number"].max()))
    max_drawing_no = max(1, int(df["drawing_no"].max()))

    total_events_seen = 0
    counts_all = empty_counter()

    drawing_events_seen: Counter[int] = Counter()
    counts_by_drawing_no: dict[int, Counter[int]] = defaultdict(empty_counter)

    last_seen: dict[int, int | None] = {number: None for number in NUMBERS}

    rolling_50: deque[set[int]] = deque(maxlen=50)
    rolling_250: deque[set[int]] = deque(maxlen=250)
    rolling_50_counts = empty_counter()
    rolling_250_counts = empty_counter()

    records: list[dict[str, Any]] = []
    targets: list[int] = []

    event_targets: dict[int, set[int]] = {}
    event_meta: dict[int, dict[str, Any]] = {}

    def make_features(row: pd.Series, number: int, event_index: int) -> dict[str, Any]:
        drawing_no = int(row["drawing_no"])
        year = int(row["year"])
        draw_number = int(row["draw_number"])

        if total_events_seen == 0:
            prior_frequency = 0.0
        else:
            prior_frequency = counts_all[number] / float(total_events_seen)

        if drawing_events_seen[drawing_no] == 0:
            drawing_no_prior_frequency = 0.0
        else:
            drawing_no_prior_frequency = counts_by_drawing_no[drawing_no][number] / float(drawing_events_seen[drawing_no])

        rolling_50_frequency = rolling_50_counts[number] / float(max(1, len(rolling_50)))
        rolling_250_frequency = rolling_250_counts[number] / float(max(1, len(rolling_250)))

        previous_seen = last_seen[number]
        if previous_seen is None:
            since_seen_scaled = 1.0
        else:
            since_seen_scaled = min(500, event_index - previous_seen) / 500.0

        if max_year == min_year:
            year_scaled = 0.0
        else:
            year_scaled = (year - min_year) / float(max_year - min_year)

        return {
            "event_index": int(event_index),
            "number": int(number),
            "number_scaled": number / 49.0,
            "drawing_no_scaled": drawing_no / float(max_drawing_no),
            "year_scaled": year_scaled,
            "draw_number_scaled": draw_number / float(max_draw_number),
            "prior_frequency": prior_frequency,
            "drawing_no_prior_frequency": drawing_no_prior_frequency,
            "rolling_50_frequency": rolling_50_frequency,
            "rolling_250_frequency": rolling_250_frequency,
            "since_seen_scaled": since_seen_scaled,
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

        total_events_seen += 1
        drawing_no = int(row["drawing_no"])
        drawing_events_seen[drawing_no] += 1

        for number in current_numbers:
            counts_all[number] += 1
            counts_by_drawing_no[drawing_no][number] += 1
            last_seen[number] = event_index

        if len(rolling_50) == rolling_50.maxlen:
            old = rolling_50[0]
            for number in old:
                rolling_50_counts[number] -= 1

        if len(rolling_250) == rolling_250.maxlen:
            old = rolling_250[0]
            for number in old:
                rolling_250_counts[number] -= 1

        rolling_50.append(current_numbers)
        rolling_250.append(current_numbers)

        for number in current_numbers:
            rolling_50_counts[number] += 1
            rolling_250_counts[number] += 1

    feature_df = pd.DataFrame(records)
    target = pd.Series(targets, name="target")

    final_state = {
        "min_year": min_year,
        "max_year": max_year,
        "max_draw_number": max_draw_number,
        "max_drawing_no": max_drawing_no,
        "total_events_seen": total_events_seen,
        "counts_all": dict(counts_all),
        "drawing_events_seen": dict(drawing_events_seen),
        "counts_by_drawing_no": {
            str(k): dict(v) for k, v in counts_by_drawing_no.items()
        },
        "last_seen": last_seen,
        "rolling_50_counts": dict(rolling_50_counts),
        "rolling_250_counts": dict(rolling_250_counts),
        "rolling_50_len": len(rolling_50),
        "rolling_250_len": len(rolling_250),
    }

    return feature_df, target, event_targets, event_meta, final_state


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
    rows: list[dict[str, Any]] = []
    hits: list[int] = []

    for event_index in test_events:
        event_scores = feature_df[feature_df["event_index"] == event_index][["number", score_col]].copy()
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


def try_train_sgd_model(
    feature_df: pd.DataFrame,
    target: pd.Series,
    train_events: list[int],
    test_events: list[int],
    event_targets: dict[int, set[int]],
    event_meta: dict[int, dict[str, Any]],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], bool, str]:
    try:
        import joblib
        from sklearn.linear_model import SGDClassifier
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except Exception as exc:
        return None, [], False, f"sklearn_or_joblib_unavailable: {exc}"

    train_mask = feature_df["event_index"].isin(train_events)
    test_mask = feature_df["event_index"].isin(test_events)

    X_train = feature_df.loc[train_mask, FEATURE_COLUMNS]
    y_train = target.loc[train_mask]

    X_test = feature_df.loc[test_mask, FEATURE_COLUMNS]

    try:
        classifier = SGDClassifier(
            loss="log_loss",
            alpha=0.0005,
            max_iter=1000,
            tol=1e-3,
            class_weight="balanced",
            random_state=41,
        )
    except TypeError:
        classifier = SGDClassifier(
            loss="log",
            alpha=0.0005,
            max_iter=1000,
            tol=1e-3,
            class_weight="balanced",
            random_state=41,
        )

    model = make_pipeline(StandardScaler(), classifier)
    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_test)[:, 1]
    feature_df.loc[test_mask, "sgd_probability"] = probabilities

    metrics, rows = evaluate_score_column(
        feature_df=feature_df,
        event_targets=event_targets,
        event_meta=event_meta,
        test_events=test_events,
        score_col="sgd_probability",
        model_name="sgd_number_classifier",
    )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, SGD_MODEL_PATH)

    metadata = {
        "model_name": "sgd_number_classifier",
        "model_type": "per_number_binary_classifier",
        "canonical_dataset": str(CANONICAL_PATH.relative_to(ROOT)),
        "feature_columns": FEATURE_COLUMNS,
        "uses_bonus_number": False,
        "uses_drawing_no": True,
        "train_events": len(train_events),
        "test_events": len(test_events),
        "metrics": metrics,
        "warning": "Lottery draws are random. This model provides ranking scores, not guaranteed predictions.",
    }

    SGD_MODEL_META_JSON.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    return metrics, rows, True, "trained"


def build_next_prediction_features(final_state: dict[str, Any], latest_row: pd.Series) -> pd.DataFrame:
    latest_year = int(latest_row["year"])
    latest_draw_number = int(latest_row["draw_number"])

    next_year = latest_year
    next_draw_number = latest_draw_number + 1
    next_drawing_no = 1

    min_year = int(final_state["min_year"])
    max_year = int(final_state["max_year"])
    max_draw_number = max(1, int(final_state["max_draw_number"]))
    max_drawing_no = max(1, int(final_state["max_drawing_no"]))

    total_events_seen = max(1, int(final_state["total_events_seen"]))

    counts_all = {int(k): int(v) for k, v in final_state["counts_all"].items()}
    drawing_events_seen = {int(k): int(v) for k, v in final_state["drawing_events_seen"].items()}

    raw_counts_by_drawing = final_state["counts_by_drawing_no"]
    counts_by_drawing_no = {
        int(k): {int(n): int(c) for n, c in value.items()}
        for k, value in raw_counts_by_drawing.items()
    }

    last_seen = {
        int(k): (None if v is None else int(v))
        for k, v in final_state["last_seen"].items()
    }

    rolling_50_counts = {int(k): int(v) for k, v in final_state["rolling_50_counts"].items()}
    rolling_250_counts = {int(k): int(v) for k, v in final_state["rolling_250_counts"].items()}

    rolling_50_len = max(1, int(final_state["rolling_50_len"]))
    rolling_250_len = max(1, int(final_state["rolling_250_len"]))

    event_index = int(final_state["total_events_seen"])

    rows = []

    for number in NUMBERS:
        if total_events_seen == 0:
            prior_frequency = 0.0
        else:
            prior_frequency = counts_all.get(number, 0) / float(total_events_seen)

        same_drawing_seen = drawing_events_seen.get(next_drawing_no, 0)
        if same_drawing_seen == 0:
            drawing_no_prior_frequency = 0.0
        else:
            drawing_no_prior_frequency = counts_by_drawing_no.get(next_drawing_no, {}).get(number, 0) / float(same_drawing_seen)

        previous_seen = last_seen.get(number)
        if previous_seen is None:
            since_seen_scaled = 1.0
        else:
            since_seen_scaled = min(500, event_index - previous_seen) / 500.0

        if max_year == min_year:
            year_scaled = 0.0
        else:
            year_scaled = (next_year - min_year) / float(max_year - min_year)

        rows.append(
            {
                "event_index": event_index,
                "number": number,
                "number_scaled": number / 49.0,
                "drawing_no_scaled": next_drawing_no / float(max_drawing_no),
                "year_scaled": year_scaled,
                "draw_number_scaled": next_draw_number / float(max_draw_number),
                "prior_frequency": prior_frequency,
                "drawing_no_prior_frequency": drawing_no_prior_frequency,
                "rolling_50_frequency": rolling_50_counts.get(number, 0) / float(rolling_50_len),
                "rolling_250_frequency": rolling_250_counts.get(number, 0) / float(rolling_250_len),
                "since_seen_scaled": since_seen_scaled,
            }
        )

    return pd.DataFrame(rows)


def save_json_models(df: pd.DataFrame, feature_df: pd.DataFrame, final_state: dict[str, Any]) -> None:
    total_events = max(1, int(final_state["total_events_seen"]))

    frequency_scores = {
        str(number): int(final_state["counts_all"].get(number, 0)) / float(total_events)
        for number in NUMBERS
    }

    rolling_250_len = max(1, int(final_state["rolling_250_len"]))
    recency_scores = {
        str(number): int(final_state["rolling_250_counts"].get(number, 0)) / float(rolling_250_len)
        for number in NUMBERS
    }

    frequency_model = {
        "model_name": "v41_frequency_main_numbers_model",
        "model_type": "frequency_baseline",
        "canonical_dataset": str(CANONICAL_PATH.relative_to(ROOT)),
        "uses_bonus_number": False,
        "uses_drawing_no": True,
        "total_draw_events": int(len(df)),
        "scores": frequency_scores,
        "top6": sorted(NUMBERS, key=lambda n: (-frequency_scores[str(n)], n))[:6],
        "warning": "Lottery draws are random. Scores are historical rankings, not guaranteed predictions.",
    }

    recency_model = {
        "model_name": "v41_recency_main_numbers_model",
        "model_type": "rolling_250_event_frequency",
        "canonical_dataset": str(CANONICAL_PATH.relative_to(ROOT)),
        "uses_bonus_number": False,
        "uses_drawing_no": True,
        "window_events": 250,
        "scores": recency_scores,
        "top6": sorted(NUMBERS, key=lambda n: (-recency_scores[str(n)], n))[:6],
        "warning": "Lottery draws are random. Scores are recency rankings, not guaranteed predictions.",
    }

    FREQUENCY_MODEL_JSON.write_text(json.dumps(frequency_model, ensure_ascii=False, indent=2), encoding="utf-8")
    RECENCY_MODEL_JSON.write_text(json.dumps(recency_model, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = load_canonical_dataset()
    validate_dataset(df)

    feature_df, target, event_targets, event_meta, final_state = build_feature_frame(df)

    total_events = int(df["event_index"].nunique())
    split_index = int(math.floor(total_events * 0.8))

    train_events = [int(x) for x in range(0, split_index)]
    test_events = [int(x) for x in range(split_index, total_events)]

    frequency_metrics, frequency_rows = evaluate_score_column(
        feature_df=feature_df,
        event_targets=event_targets,
        event_meta=event_meta,
        test_events=test_events,
        score_col="prior_frequency",
        model_name="frequency_baseline",
    )

    recency_metrics, recency_rows = evaluate_score_column(
        feature_df=feature_df,
        event_targets=event_targets,
        event_meta=event_meta,
        test_events=test_events,
        score_col="rolling_250_frequency",
        model_name="recency_250_baseline",
    )

    sgd_metrics, sgd_rows, sgd_trained, sgd_status = try_train_sgd_model(
        feature_df=feature_df,
        target=target,
        train_events=train_events,
        test_events=test_events,
        event_targets=event_targets,
        event_meta=event_meta,
    )

    save_json_models(df, feature_df, final_state)

    backtest_rows = frequency_rows + recency_rows + sgd_rows
    pd.DataFrame(backtest_rows).to_csv(BACKTEST_CSV, index=False, encoding="utf-8-sig")

    latest_row = df.iloc[-1]
    next_features = build_next_prediction_features(final_state, latest_row)

    prediction_sets = {
        "frequency_baseline": top_numbers_from_scores(next_features, "prior_frequency", 6),
        "recency_250_baseline": top_numbers_from_scores(next_features, "rolling_250_frequency", 6),
    }

    if sgd_trained:
        import joblib

        model = joblib.load(SGD_MODEL_PATH)
        next_features["sgd_probability"] = model.predict_proba(next_features[FEATURE_COLUMNS])[:, 1]
        prediction_sets["sgd_number_classifier"] = top_numbers_from_scores(next_features, "sgd_probability", 6)

    latest_predictions = {
        "status": "v41_predictions_generated_from_canonical_draw_events",
        "canonical_dataset": str(CANONICAL_PATH.relative_to(ROOT)),
        "uses_bonus_number": False,
        "latest_seen_event": {
            "year": int(latest_row["year"]),
            "draw_number": int(latest_row["draw_number"]),
            "drawing_no": int(latest_row["drawing_no"]),
            "numbers": [int(latest_row[col]) for col in NUMBER_COLS],
        },
        "prediction_sets": prediction_sets,
        "warning": "Lottery draws are random. These are ranking-based model outputs, not guaranteed winning numbers.",
    }

    PREDICTIONS_JSON.write_text(json.dumps(latest_predictions, ensure_ascii=False, indent=2), encoding="utf-8")

    model_metrics = [frequency_metrics, recency_metrics]
    if sgd_metrics is not None:
        model_metrics.append(sgd_metrics)

    best_model = sorted(model_metrics, key=lambda item: item["average_hits_top6"], reverse=True)[0]

    summary = {
        "status": "v41_model_retraining_completed",
        "canonical_dataset": str(CANONICAL_PATH.relative_to(ROOT)),
        "total_draw_events": total_events,
        "train_events": len(train_events),
        "test_events": len(test_events),
        "uses_bonus_number": False,
        "bonus_model_trained": False,
        "drawing_no_used": True,
        "models_created": [
            str(FREQUENCY_MODEL_JSON.relative_to(ROOT)),
            str(RECENCY_MODEL_JSON.relative_to(ROOT)),
            str(PREDICTIONS_JSON.relative_to(ROOT)),
        ],
        "sgd_model_trained": sgd_trained,
        "sgd_status": sgd_status,
        "sgd_model_path": str(SGD_MODEL_PATH.relative_to(ROOT)) if sgd_trained else "",
        "model_metrics": model_metrics,
        "best_model_by_average_hits_top6": best_model,
        "important_warning": "Lottery draws are random. Backtest metrics are evaluation diagnostics, not a guarantee of future outcomes.",
    }

    REPORT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# v41 Model Retraining Summary",
        "",
        "Status: v41 model retraining completed on canonical draw events.",
        "",
        "## Dataset",
        "",
        f"- Canonical dataset: `{summary['canonical_dataset']}`",
        f"- Total draw events: {summary['total_draw_events']}",
        f"- Train events: {summary['train_events']}",
        f"- Test events: {summary['test_events']}",
        f"- Uses drawing_no: {summary['drawing_no_used']}",
        f"- Bonus model trained: {summary['bonus_model_trained']}",
        "",
        "## Models",
        "",
        "- Frequency baseline",
        "- Recency 250-event baseline",
    ]

    if sgd_trained:
        lines.append("- SGD per-number classifier")
    else:
        lines.append(f"- SGD per-number classifier skipped: {sgd_status}")

    lines.extend(["", "## Metrics", ""])

    for metrics in model_metrics:
        lines.append(f"### {metrics['model']}")
        lines.append("")
        lines.append(f"- Average hits top 6: {metrics['average_hits_top6']:.4f}")
        lines.append(f"- Median hits top 6: {metrics['median_hits_top6']:.4f}")
        lines.append(f"- Max hits top 6: {metrics['max_hits_top6']}")
        lines.append(f"- Hit distribution: {metrics['hit_distribution']}")
        lines.append(f"- Events with 3+ hits: {metrics['events_with_3plus_hits']}")
        lines.append(f"- Events with 4+ hits: {metrics['events_with_4plus_hits']}")
        lines.append(f"- Events with 5+ hits: {metrics['events_with_5plus_hits']}")
        lines.append(f"- Events with 6 hits: {metrics['events_with_6_hits']}")
        lines.append("")

    lines.extend(
        [
            "## Important warning",
            "",
            "Lottery draws are random. These models produce ranking scores and diagnostics, not guaranteed winning numbers.",
            "",
            "Bonus-number modeling is intentionally blocked because bonus-number data is not available in the canonical dataset.",
        ]
    )

    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("DONE: v41 model retraining completed.")
    print("TOTAL_DRAW_EVENTS", summary["total_draw_events"])
    print("TRAIN_EVENTS", summary["train_events"])
    print("TEST_EVENTS", summary["test_events"])
    print("SGD_MODEL_TRAINED", summary["sgd_model_trained"])
    print("SGD_STATUS", summary["sgd_status"])
    print("BEST_MODEL", best_model["model"])
    print("BEST_AVERAGE_HITS_TOP6", best_model["average_hits_top6"])
    print("PREDICTIONS_JSON", PREDICTIONS_JSON)
    print("REPORT_JSON", REPORT_JSON)
    print("REPORT_MD", REPORT_MD)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

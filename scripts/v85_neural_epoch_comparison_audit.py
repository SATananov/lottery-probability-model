from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import numpy as np
except Exception as exc:
    raise SystemExit(
        "STOP: NumPy is required for Step 85. "
        "Run: python -m pip install -r requirements.txt"
    ) from exc


ROOT = Path(".")
DATA_CANDIDATES = [
    ROOT / "data" / "v41_canonical_draw_events.csv",
    ROOT / "data" / "historical_draws.csv",
    ROOT / "data" / "v40_normalized_draw_events.csv",
]

REPORT_CSV = ROOT / "reports" / "v85_neural_epoch_comparison.csv"
REPORT_JSON = ROOT / "reports" / "v85_neural_epoch_comparison_summary.json"
REPORT_MD = ROOT / "reports" / "v85_neural_epoch_comparison_summary.md"
MODEL_JSON = ROOT / "models" / "v85" / "v85_neural_epoch_comparison_model.json"

EPOCH_CHECKPOINTS = [90, 150, 300, 500]
HIDDEN_UNITS = 18
LEARNING_RATE = 0.035
RANDOM_SEED = 85
TEST_RATIO = 0.20
RECENT_SHORT = 50
RECENT_LONG = 250
EPS = 1e-7


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def find_dataset() -> Path:
    for path in DATA_CANDIDATES:
        if path.exists():
            return path
    raise SystemExit("STOP: No usable draw dataset found.")


def candidate_number_columns(rows: List[Dict[str, str]]) -> List[str]:
    if not rows:
        raise SystemExit("STOP: Dataset has no rows.")

    explicit_candidates = [
        ["n1", "n2", "n3", "n4", "n5", "n6"],
        ["num1", "num2", "num3", "num4", "num5", "num6"],
        ["number1", "number2", "number3", "number4", "number5", "number6"],
        ["number_1", "number_2", "number_3", "number_4", "number_5", "number_6"],
        ["ball1", "ball2", "ball3", "ball4", "ball5", "ball6"],
    ]

    available = set(rows[0].keys())

    for cols in explicit_candidates:
        if all(col in available for col in cols):
            return cols

    numeric_cols = []
    sample = rows[: min(len(rows), 200)]

    for col in rows[0].keys():
        values = []
        ok = True
        for row in sample:
            raw = str(row.get(col, "")).strip()
            if raw == "":
                ok = False
                break
            try:
                value = int(float(raw))
            except Exception:
                ok = False
                break
            values.append(value)

        if ok and values and all(1 <= value <= 49 for value in values):
            numeric_cols.append(col)

    if len(numeric_cols) < 6:
        raise SystemExit(
            "STOP: Could not detect 6 lottery number columns. "
            f"Candidate numeric columns: {numeric_cols}"
        )

    return numeric_cols[:6]


def sort_key(row: Dict[str, str], index: int) -> Tuple:
    def value(name: str, default: int = 0) -> int:
        raw = str(row.get(name, "")).strip()
        if raw == "":
            return default
        try:
            return int(float(raw))
        except Exception:
            return default

    # Keep tuple element types stable across all rows.
    # Some rows have a date string, many historic rows do not.
    # Returning mixed first elements like (date_string, ...) and (year_int, ...)
    # breaks Python sorting, so we normalize the sort key.
    year = value("year", 0)
    date = str(row.get("date", row.get("draw_date", ""))).strip()

    drawing_no = value(
        "drawing_no",
        value("draw_no", value("draw_number", index)),
    )

    draw_position = value(
        "draw_position",
        value("position", drawing_no),
    )

    return (
        int(year),
        str(date),
        int(drawing_no),
        int(draw_position),
        int(index),
    )

def load_draws() -> Tuple[Path, List[List[int]]]:
    path = find_dataset()
    rows = read_rows(path)
    cols = candidate_number_columns(rows)

    valid = []

    for idx, row in enumerate(rows):
        nums = []
        ok = True

        for col in cols:
            raw = str(row.get(col, "")).strip()
            if raw == "":
                ok = False
                break
            try:
                value = int(float(raw))
            except Exception:
                ok = False
                break

            if value < 1 or value > 49:
                ok = False
                break

            nums.append(value)

        if not ok:
            continue

        if len(nums) != 6 or len(set(nums)) != 6:
            continue

        valid.append((sort_key(row, idx), sorted(nums)))

    valid.sort(key=lambda item: item[0])
    draws = [nums for _, nums in valid]

    if len(draws) < 500:
        raise SystemExit(f"STOP: Not enough valid draws for Step 85: {len(draws)}")

    return path, draws


def build_samples(draws: List[List[int]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, int]]:
    cumulative = np.zeros(50, dtype=np.float32)
    last_seen = np.full(50, -1, dtype=np.int32)
    recent_short: List[List[int]] = []
    recent_long: List[List[int]] = []

    features = []
    targets = []
    event_ids = []

    for event_idx, nums in enumerate(draws):
        target_set = set(nums)

        short_counts = np.zeros(50, dtype=np.float32)
        for past in recent_short:
            for n in past:
                short_counts[n] += 1.0

        long_counts = np.zeros(50, dtype=np.float32)
        for past in recent_long:
            for n in past:
                long_counts[n] += 1.0

        history_size = max(event_idx, 1)
        short_size = max(len(recent_short), 1)
        long_size = max(len(recent_long), 1)

        for number in range(1, 50):
            gap = event_idx - last_seen[number] if last_seen[number] >= 0 else RECENT_LONG + 1
            gap_scaled = min(gap, RECENT_LONG + 1) / float(RECENT_LONG + 1)

            feature_row = [
                number / 49.0,
                1.0 if number % 2 else 0.0,
                1.0 if number <= 24 else 0.0,
                (number % 10) / 9.0,
                cumulative[number] / history_size,
                short_counts[number] / short_size,
                long_counts[number] / long_size,
                gap_scaled,
            ]

            features.append(feature_row)
            targets.append(1.0 if number in target_set else 0.0)
            event_ids.append(event_idx)

        for n in nums:
            cumulative[n] += 1.0
            last_seen[n] = event_idx

        recent_short.append(nums)
        recent_long.append(nums)

        if len(recent_short) > RECENT_SHORT:
            recent_short.pop(0)

        if len(recent_long) > RECENT_LONG:
            recent_long.pop(0)

    X = np.asarray(features, dtype=np.float32)
    y = np.asarray(targets, dtype=np.float32).reshape(-1, 1)
    event_ids_array = np.asarray(event_ids, dtype=np.int32)

    meta = {
        "samples": int(X.shape[0]),
        "features": int(X.shape[1]),
        "events": int(len(draws)),
    }

    return X, y, event_ids_array, meta


def standardize_train_test(
    X: np.ndarray,
    event_ids: np.ndarray,
    split_event: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    train_mask = event_ids < split_event
    test_mask = event_ids >= split_event

    mean = X[train_mask].mean(axis=0, keepdims=True)
    std = X[train_mask].std(axis=0, keepdims=True)
    std = np.where(std < 1e-6, 1.0, std)

    X_scaled = (X - mean) / std

    return X_scaled.astype(np.float32), train_mask, test_mask, mean.astype(np.float32), std.astype(np.float32)


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -40, 40)))


def init_weights(input_dim: int, hidden_units: int) -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(RANDOM_SEED)
    return {
        "W1": rng.normal(0, 0.15, size=(input_dim, hidden_units)).astype(np.float32),
        "b1": np.zeros((1, hidden_units), dtype=np.float32),
        "W2": rng.normal(0, 0.15, size=(hidden_units, 1)).astype(np.float32),
        "b2": np.zeros((1, 1), dtype=np.float32),
    }


def forward(X: np.ndarray, weights: Dict[str, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    hidden = np.tanh(X @ weights["W1"] + weights["b1"])
    pred = sigmoid(hidden @ weights["W2"] + weights["b2"])
    return hidden, pred


def weighted_loss(y_true: np.ndarray, y_pred: np.ndarray, pos_weight: float, neg_weight: float) -> float:
    weights = np.where(y_true > 0.5, pos_weight, neg_weight)
    loss = -weights * (
        y_true * np.log(y_pred + EPS)
        + (1.0 - y_true) * np.log(1.0 - y_pred + EPS)
    )
    return float(loss.mean())


def train_step(
    X: np.ndarray,
    y: np.ndarray,
    weights: Dict[str, np.ndarray],
    pos_weight: float,
    neg_weight: float,
    lr: float,
) -> float:
    hidden, pred = forward(X, weights)
    sample_weights = np.where(y > 0.5, pos_weight, neg_weight)

    grad_output = (pred - y) * sample_weights / X.shape[0]

    grad_W2 = hidden.T @ grad_output
    grad_b2 = grad_output.sum(axis=0, keepdims=True)

    grad_hidden = grad_output @ weights["W2"].T
    grad_z1 = grad_hidden * (1.0 - hidden * hidden)

    grad_W1 = X.T @ grad_z1
    grad_b1 = grad_z1.sum(axis=0, keepdims=True)

    weights["W2"] -= lr * grad_W2.astype(np.float32)
    weights["b2"] -= lr * grad_b2.astype(np.float32)
    weights["W1"] -= lr * grad_W1.astype(np.float32)
    weights["b1"] -= lr * grad_b1.astype(np.float32)

    return weighted_loss(y, pred, pos_weight, neg_weight)


def evaluate_top6(
    X: np.ndarray,
    y: np.ndarray,
    event_ids: np.ndarray,
    mask: np.ndarray,
    weights: Dict[str, np.ndarray],
) -> Dict[str, float]:
    _, pred = forward(X[mask], weights)
    y_part = y[mask].reshape(-1)
    ids_part = event_ids[mask]

    hits = []
    unique_events = np.unique(ids_part)

    for event_id in unique_events:
        local_idx = np.where(ids_part == event_id)[0]
        scores = pred[local_idx].reshape(-1)
        targets = y_part[local_idx]

        if len(scores) != 49:
            continue

        top6_idx = np.argsort(scores)[-6:]
        hits.append(float(targets[top6_idx].sum()))

    if not hits:
        return {
            "avg_hits_top6": 0.0,
            "max_hits_top6": 0.0,
            "events_evaluated": 0,
        }

    return {
        "avg_hits_top6": float(np.mean(hits)),
        "max_hits_top6": float(np.max(hits)),
        "events_evaluated": int(len(hits)),
    }


def latest_top_numbers(
    X: np.ndarray,
    event_ids: np.ndarray,
    weights: Dict[str, np.ndarray],
) -> List[int]:
    latest_event = int(event_ids.max())
    idx = np.where(event_ids == latest_event)[0]
    _, pred = forward(X[idx], weights)

    if len(pred) != 49:
        return []

    scores = pred.reshape(-1)
    top = np.argsort(scores)[-6:][::-1]
    return [int(i + 1) for i in top]


def main() -> None:
    dataset_path, draws = load_draws()
    X_raw, y, event_ids, sample_meta = build_samples(draws)

    split_event = int(len(draws) * (1.0 - TEST_RATIO))
    X, train_mask, test_mask, _, _ = standardize_train_test(X_raw, event_ids, split_event)

    X_train = X[train_mask]
    y_train = y[train_mask]

    positive_rate = float(y_train.mean())
    pos_weight = float(0.5 / max(positive_rate, EPS))
    neg_weight = float(0.5 / max(1.0 - positive_rate, EPS))

    weights = init_weights(X.shape[1], HIDDEN_UNITS)

    results = []
    loss_start = None
    current_loss = None

    max_epoch = max(EPOCH_CHECKPOINTS)

    for epoch in range(1, max_epoch + 1):
        current_loss = train_step(
            X_train,
            y_train,
            weights,
            pos_weight=pos_weight,
            neg_weight=neg_weight,
            lr=LEARNING_RATE,
        )

        if epoch == 1:
            loss_start = current_loss

        if epoch in EPOCH_CHECKPOINTS:
            train_eval = evaluate_top6(X, y, event_ids, train_mask, weights)
            test_eval = evaluate_top6(X, y, event_ids, test_mask, weights)
            top_numbers = latest_top_numbers(X, event_ids, weights)

            result = {
                "epochs": int(epoch),
                "train_loss": float(current_loss),
                "loss_start": float(loss_start or current_loss),
                "loss_delta": float((loss_start or current_loss) - current_loss),
                "train_avg_hits_top6": train_eval["avg_hits_top6"],
                "train_max_hits_top6": train_eval["max_hits_top6"],
                "test_avg_hits_top6": test_eval["avg_hits_top6"],
                "test_max_hits_top6": test_eval["max_hits_top6"],
                "test_events_evaluated": test_eval["events_evaluated"],
                "latest_top6_numbers": top_numbers,
            }
            results.append(result)

            print(
                "EPOCH",
                epoch,
                "loss=",
                round(result["train_loss"], 6),
                "test_avg_hits_top6=",
                round(result["test_avg_hits_top6"], 6),
                "test_max=",
                result["test_max_hits_top6"],
                "top6=",
                top_numbers,
            )

    best = max(
        results,
        key=lambda item: (
            item["test_avg_hits_top6"],
            item["test_max_hits_top6"],
            -item["epochs"],
        ),
    )

    REPORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)

    with REPORT_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "epochs",
            "train_loss",
            "loss_start",
            "loss_delta",
            "train_avg_hits_top6",
            "train_max_hits_top6",
            "test_avg_hits_top6",
            "test_max_hits_top6",
            "test_events_evaluated",
            "latest_top6_numbers",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in results:
            csv_row = dict(row)
            csv_row["latest_top6_numbers"] = " ".join(str(n) for n in row["latest_top6_numbers"])
            writer.writerow(csv_row)

    summary = {
        "step": "85",
        "name": "Neural Epoch Comparison Audit",
        "status": "OK",
        "safe_wording": "This is a statistical training audit, not a prediction guarantee.",
        "dataset": dataset_path.as_posix(),
        "valid_draws": int(len(draws)),
        "train_draws": int(split_event),
        "test_draws": int(len(draws) - split_event),
        "train_samples": int(train_mask.sum()),
        "test_samples": int(test_mask.sum()),
        "features": int(sample_meta["features"]),
        "hidden_units": int(HIDDEN_UNITS),
        "learning_rate": float(LEARNING_RATE),
        "random_seed": int(RANDOM_SEED),
        "epoch_checkpoints": EPOCH_CHECKPOINTS,
        "best_epochs_by_test_avg_hits": int(best["epochs"]),
        "best_test_avg_hits_top6": float(best["test_avg_hits_top6"]),
        "best_test_max_hits_top6": float(best["test_max_hits_top6"]),
        "results": results,
        "recommendation": (
            "Keep the current neural setup unless a higher epoch checkpoint improves "
            "test-period performance without only improving training loss."
        ),
    }

    REPORT_JSON.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    MODEL_JSON.write_text(
        json.dumps(
            {
                "step": "85",
                "model_type": "neural_epoch_comparison_audit",
                "active_model_replacement": False,
                "best_epochs_by_test_avg_hits": int(best["epochs"]),
                "best_latest_top6_numbers": best["latest_top6_numbers"],
                "results": results,
                "safe_wording": "Statistical audit only. Lottery outcomes are random and no winning result is guaranteed.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    md_lines = [
        "# Step 85 — Neural Epoch Comparison Audit",
        "",
        "**Status:** OK",
        "",
        "This audit compares neural training checkpoints without replacing the active model automatically.",
        "",
        "**Important:** Lottery outcomes are random. This is statistical analysis only, not a winning guarantee.",
        "",
        "## Configuration",
        "",
        f"- Dataset: `{dataset_path.as_posix()}`",
        f"- Valid draws: **{len(draws)}**",
        f"- Train draws: **{split_event}**",
        f"- Test draws: **{len(draws) - split_event}**",
        f"- Train samples: **{int(train_mask.sum())}**",
        f"- Test samples: **{int(test_mask.sum())}**",
        f"- Hidden units: **{HIDDEN_UNITS}**",
        f"- Learning rate: **{LEARNING_RATE}**",
        f"- Epoch checkpoints: **{', '.join(str(e) for e in EPOCH_CHECKPOINTS)}**",
        "",
        "## Results",
        "",
        "| Epochs | Train loss | Test avg hits top 6 | Test max hits top 6 | Latest top 6 numbers |",
        "|---:|---:|---:|---:|---|",
    ]

    for row in results:
        nums = ", ".join(str(n) for n in row["latest_top6_numbers"])
        md_lines.append(
            f"| {row['epochs']} | {row['train_loss']:.6f} | "
            f"{row['test_avg_hits_top6']:.6f} | {row['test_max_hits_top6']:.0f} | {nums} |"
        )

    md_lines.extend(
        [
            "",
            "## Best checkpoint",
            "",
            f"- Best by test average hits top 6: **{best['epochs']} epochs**",
            f"- Test avg hits top 6: **{best['test_avg_hits_top6']:.6f}**",
            f"- Test max hits top 6: **{best['test_max_hits_top6']:.0f}**",
            "",
            "## Recommendation",
            "",
            "Use this audit as evidence before changing the active neural configuration. "
            "Do not increase epochs only because training loss becomes lower; the test-period result matters more.",
            "",
        ]
    )

    REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8", newline="\n")

    print("")
    print("DONE: Step 85 Neural Epoch Comparison Audit")
    print("Best epochs:", best["epochs"])
    print("Report:", REPORT_MD.as_posix())


if __name__ == "__main__":
    main()

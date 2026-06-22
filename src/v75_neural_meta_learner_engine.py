from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_CANDIDATES = [
    ROOT / "data" / "v41_canonical_draw_events.csv",
    ROOT / "data" / "v40_normalized_draw_events.csv",
    ROOT / "data" / "historical_draws.csv",
]

MODEL_DIR = ROOT / "models" / "v75"
REPORTS_DIR = ROOT / "reports"

MODEL_PATH = MODEL_DIR / "v75_neural_meta_learner_model.json"
NUMBER_SCORES_CSV = REPORTS_DIR / "v75_neural_meta_number_scores.csv"
CANDIDATE_TICKETS_CSV = REPORTS_DIR / "v75_neural_candidate_tickets.csv"
CANDIDATE_TICKETS_JSON = REPORTS_DIR / "v75_neural_candidate_tickets.json"
SUMMARY_JSON = REPORTS_DIR / "v75_neural_meta_learner_summary.json"
SUMMARY_MD = REPORTS_DIR / "v75_neural_meta_learner_summary.md"

MIN_NUMBER = 1
MAX_NUMBER = 49
NUMBERS_PER_TICKET = 6
WARMUP_DRAWS = 100
HIDDEN_UNITS = 18
EPOCHS = 90
LEARNING_RATE = 0.035
RANDOM_SEED = 75


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.ndarray,)):
        return value.tolist()
    return str(value)


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def _read_dataset() -> tuple[pd.DataFrame, Path]:
    for path in DATA_CANDIDATES:
        if path.exists():
            return pd.read_csv(path), path
    raise FileNotFoundError("Не е намерен основен dataset файл.")


def _detect_main_number_columns(df: pd.DataFrame) -> list[str]:
    exact_groups = [
        [f"number_{i}" for i in range(1, 7)],
        [f"n{i}" for i in range(1, 7)],
        [f"num{i}" for i in range(1, 7)],
        [f"main_{i}" for i in range(1, 7)],
        [f"ball{i}" for i in range(1, 7)],
        [f"main_number_{i}" for i in range(1, 7)],
    ]
    lower_to_original = {str(c).lower(): c for c in df.columns}
    for group in exact_groups:
        if all(col in lower_to_original for col in group):
            return [lower_to_original[col] for col in group]

    excluded_markers = [
        "year", "date", "draw", "tiraj", "тираж", "bonus", "extra",
        "sum", "id", "index", "position",
    ]
    candidates: list[str] = []
    for col in df.columns:
        lower = str(col).lower()
        if any(marker in lower for marker in excluded_markers):
            continue
        series = pd.to_numeric(df[col], errors="coerce")
        valid_ratio = series.between(MIN_NUMBER, MAX_NUMBER).mean()
        if valid_ratio > 0.95:
            candidates.append(col)

    if len(candidates) >= 6:
        return candidates[:6]

    raise ValueError(
        "Не успях да открия 6 колони с основни числа. "
        "Очаквам number_1..number_6, n1..n6 или 6 числови колони в диапазон 1–49."
    )


def _sort_draws(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    date_col = next((c for c in df.columns if str(c).lower() in {"date", "draw_date", "дата"}), None)
    draw_col = next((c for c in df.columns if str(c).lower() in {"draw", "draw_no", "draw_number", "drawing_no", "тираж"}), None)

    sort_cols = []
    if date_col:
        df["_sort_date"] = pd.to_datetime(df[date_col], errors="coerce")
        sort_cols.append("_sort_date")
    if draw_col:
        df["_sort_draw"] = pd.to_numeric(df[draw_col], errors="coerce")
        sort_cols.append("_sort_draw")

    if sort_cols:
        df = df.sort_values(sort_cols, kind="mergesort").reset_index(drop=True)

    return df


def load_draw_sets() -> tuple[list[set[int]], pd.DataFrame, Path, list[str]]:
    df, source_path = _read_dataset()
    df = _sort_draws(df)
    number_cols = _detect_main_number_columns(df)

    draw_sets: list[set[int]] = []
    valid_rows = []
    for _, row in df.iterrows():
        nums = []
        for col in number_cols:
            val = pd.to_numeric(row[col], errors="coerce")
            if pd.isna(val):
                nums = []
                break
            nums.append(int(val))
        if len(nums) == NUMBERS_PER_TICKET and len(set(nums)) == NUMBERS_PER_TICKET and all(MIN_NUMBER <= n <= MAX_NUMBER for n in nums):
            draw_sets.append(set(nums))
            valid_rows.append(row)

    clean_df = pd.DataFrame(valid_rows).reset_index(drop=True)
    if len(draw_sets) < 300:
        raise ValueError(f"Твърде малко валидни тиражи за Step 75: {len(draw_sets)}")

    return draw_sets, clean_df, source_path, number_cols


@dataclass
class FeaturePack:
    x: np.ndarray
    y: np.ndarray
    draw_index: np.ndarray
    numbers: np.ndarray
    feature_names: list[str]


def _count_in_window(draw_sets: list[set[int]], start: int, end: int, number: int) -> int:
    if start < 0:
        start = 0
    return sum(1 for i in range(start, end) if number in draw_sets[i])


def _last_seen_gap(draw_sets: list[set[int]], end: int, number: int) -> int:
    for i in range(end - 1, -1, -1):
        if number in draw_sets[i]:
            return end - i
    return end + 1


def _features_for_number(draw_sets: list[set[int]], end: int, number: int, total_counts: dict[int, int] | None = None) -> list[float]:
    if total_counts is None:
        total_counts = {n: 0 for n in range(MIN_NUMBER, MAX_NUMBER + 1)}
        for i in range(end):
            for n in draw_sets[i]:
                total_counts[n] += 1

    historical_freq = total_counts.get(number, 0) / max(1, end)
    expected_freq = NUMBERS_PER_TICKET / (MAX_NUMBER - MIN_NUMBER + 1)

    last25 = _count_in_window(draw_sets, end - 25, end, number) / 25
    last50 = _count_in_window(draw_sets, end - 50, end, number) / 50
    last100 = _count_in_window(draw_sets, end - 100, end, number) / 100

    gap = _last_seen_gap(draw_sets, end, number)
    gap_scaled = min(gap, 120) / 120
    overdue_signal = min(max((gap - (1 / expected_freq)) / 80, -1), 1)

    recent_trend = last25 - last100
    parity = number % 2
    low_high = 1 if number <= 24 else 0
    decade = min(number // 10, 4) / 4
    edge_distance = min(number - MIN_NUMBER, MAX_NUMBER - number) / 24
    normalized_number = number / MAX_NUMBER

    return [
        normalized_number,
        float(parity),
        float(low_high),
        decade,
        edge_distance,
        historical_freq,
        historical_freq - expected_freq,
        last25,
        last50,
        last100,
        gap_scaled,
        overdue_signal,
        recent_trend,
    ]


def build_feature_pack(draw_sets: list[set[int]]) -> FeaturePack:
    feature_names = [
        "номер",
        "четност",
        "ниско_високо",
        "десетица",
        "разстояние_от_край",
        "историческа_честота",
        "отклонение_от_очакваното",
        "честота_последни_25",
        "честота_последни_50",
        "честота_последни_100",
        "gap_от_последна_поява",
        "overdue_сигнал",
        "кратък_тренд",
    ]

    x_rows = []
    y_rows = []
    draw_index = []
    numbers = []

    total_counts = {n: 0 for n in range(MIN_NUMBER, MAX_NUMBER + 1)}
    for i in range(WARMUP_DRAWS):
        for n in draw_sets[i]:
            total_counts[n] += 1

    for t in range(WARMUP_DRAWS, len(draw_sets)):
        if t > WARMUP_DRAWS:
            for n in draw_sets[t - 1]:
                total_counts[n] += 1

        for number in range(MIN_NUMBER, MAX_NUMBER + 1):
            x_rows.append(_features_for_number(draw_sets, t, number, total_counts))
            y_rows.append(1 if number in draw_sets[t] else 0)
            draw_index.append(t)
            numbers.append(number)

    return FeaturePack(
        x=np.asarray(x_rows, dtype=np.float64),
        y=np.asarray(y_rows, dtype=np.float64).reshape(-1, 1),
        draw_index=np.asarray(draw_index, dtype=np.int64),
        numbers=np.asarray(numbers, dtype=np.int64),
        feature_names=feature_names,
    )


def _relu(z: np.ndarray) -> np.ndarray:
    return np.maximum(0, z)


def _sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -40, 40)
    return 1.0 / (1.0 + np.exp(-z))


def train_mlp(feature_pack: FeaturePack) -> dict[str, Any]:
    x = feature_pack.x
    y = feature_pack.y

    unique_draws = np.unique(feature_pack.draw_index)
    split_draw = unique_draws[int(len(unique_draws) * 0.8)]

    train_mask = feature_pack.draw_index < split_draw
    test_mask = ~train_mask

    x_train = x[train_mask]
    y_train = y[train_mask]
    x_test = x[test_mask]
    y_test = y[test_mask]

    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0)
    std[std == 0] = 1.0

    x_train_n = (x_train - mean) / std
    x_test_n = (x_test - mean) / std

    rng = np.random.default_rng(RANDOM_SEED)
    input_dim = x_train_n.shape[1]
    w1 = rng.normal(0, 0.13, size=(input_dim, HIDDEN_UNITS))
    b1 = np.zeros((1, HIDDEN_UNITS))
    w2 = rng.normal(0, 0.13, size=(HIDDEN_UNITS, 1))
    b2 = np.zeros((1, 1))

    positive_rate = float(y_train.mean())
    pos_weight = float((1.0 - positive_rate) / max(positive_rate, 1e-9))
    sample_weights = np.where(y_train > 0.5, pos_weight, 1.0)
    sample_weights = sample_weights / sample_weights.mean()

    losses = []
    n = x_train_n.shape[0]

    for _epoch in range(EPOCHS):
        z1 = x_train_n @ w1 + b1
        h1 = _relu(z1)
        logits = h1 @ w2 + b2
        pred = _sigmoid(logits)

        eps = 1e-9
        loss = -np.mean(sample_weights * (y_train * np.log(pred + eps) + (1 - y_train) * np.log(1 - pred + eps)))
        losses.append(float(loss))

        dz2 = (pred - y_train) * sample_weights / n
        dw2 = h1.T @ dz2
        db2 = dz2.sum(axis=0, keepdims=True)

        dh1 = dz2 @ w2.T
        dz1 = dh1 * (z1 > 0)
        dw1 = x_train_n.T @ dz1
        db1 = dz1.sum(axis=0, keepdims=True)

        w1 -= LEARNING_RATE * dw1
        b1 -= LEARNING_RATE * db1
        w2 -= LEARNING_RATE * dw2
        b2 -= LEARNING_RATE * db2

    test_scores = _sigmoid(_relu(x_test_n @ w1 + b1) @ w2 + b2).reshape(-1)
    test_pred_binary = (test_scores >= 0.5).astype(int)
    y_test_flat = y_test.reshape(-1).astype(int)

    accuracy = float((test_pred_binary == y_test_flat).mean())
    top6_metrics = evaluate_top6_by_draw(
        draw_indices=feature_pack.draw_index[test_mask],
        numbers=feature_pack.numbers[test_mask],
        scores=test_scores,
        y_true=y_test_flat,
    )

    return {
        "weights": {
            "mean": mean.tolist(),
            "std": std.tolist(),
            "w1": w1.tolist(),
            "b1": b1.tolist(),
            "w2": w2.tolist(),
            "b2": b2.tolist(),
        },
        "metrics": {
            "train_samples": int(x_train.shape[0]),
            "test_samples": int(x_test.shape[0]),
            "train_draws": int(len(np.unique(feature_pack.draw_index[train_mask]))),
            "test_draws": int(len(np.unique(feature_pack.draw_index[test_mask]))),
            "positive_rate": positive_rate,
            "balanced_loss_start": float(losses[0]) if losses else None,
            "balanced_loss_end": float(losses[-1]) if losses else None,
            "binary_accuracy": accuracy,
            **top6_metrics,
        },
    }


def predict_scores(x: np.ndarray, weights: dict[str, Any]) -> np.ndarray:
    mean = np.asarray(weights["mean"], dtype=np.float64)
    std = np.asarray(weights["std"], dtype=np.float64)
    w1 = np.asarray(weights["w1"], dtype=np.float64)
    b1 = np.asarray(weights["b1"], dtype=np.float64)
    w2 = np.asarray(weights["w2"], dtype=np.float64)
    b2 = np.asarray(weights["b2"], dtype=np.float64)

    xn = (x - mean) / std
    return _sigmoid(_relu(xn @ w1 + b1) @ w2 + b2).reshape(-1)


def evaluate_top6_by_draw(draw_indices: np.ndarray, numbers: np.ndarray, scores: np.ndarray, y_true: np.ndarray) -> dict[str, Any]:
    hits = []
    for draw_id in np.unique(draw_indices):
        mask = draw_indices == draw_id
        draw_numbers = numbers[mask]
        draw_scores = scores[mask]
        draw_true = y_true[mask]
        order = np.argsort(-draw_scores)[:NUMBERS_PER_TICKET]
        selected_numbers = set(int(n) for n in draw_numbers[order])
        actual_numbers = set(int(draw_numbers[i]) for i, val in enumerate(draw_true) if val == 1)
        hits.append(len(selected_numbers & actual_numbers))

    if not hits:
        return {"avg_hits_top6": 0.0, "max_hits_top6": 0, "hit_distribution_top6": {}}

    distribution = {str(i): int(hits.count(i)) for i in range(0, 7)}
    return {
        "avg_hits_top6": float(np.mean(hits)),
        "max_hits_top6": int(max(hits)),
        "hit_distribution_top6": distribution,
    }


def score_next_draw(draw_sets: list[set[int]], weights: dict[str, Any], feature_names: list[str]) -> pd.DataFrame:
    end = len(draw_sets)
    total_counts = {n: 0 for n in range(MIN_NUMBER, MAX_NUMBER + 1)}
    for draw in draw_sets:
        for n in draw:
            total_counts[n] += 1

    rows = []
    features = []
    for number in range(MIN_NUMBER, MAX_NUMBER + 1):
        row_features = _features_for_number(draw_sets, end, number, total_counts)
        features.append(row_features)
        rows.append({"number": number})

    x_next = np.asarray(features, dtype=np.float64)
    scores = predict_scores(x_next, weights)

    for row, score, feats in zip(rows, scores, features):
        row["neural_score"] = float(score)
        for name, value in zip(feature_names, feats):
            row[name] = float(value)

    df = pd.DataFrame(rows)
    df = df.sort_values("neural_score", ascending=False).reset_index(drop=True)
    df["rank"] = np.arange(1, len(df) + 1)
    return df


def _ticket_is_balanced(nums: list[int]) -> bool:
    nums = sorted(nums)
    odds = sum(n % 2 for n in nums)
    lows = sum(n <= 24 for n in nums)
    total = sum(nums)
    if odds < 2 or odds > 4:
        return False
    if lows < 2 or lows > 4:
        return False
    if total < 95 or total > 205:
        return False
    consecutive_pairs = sum(1 for a, b in zip(nums, nums[1:]) if b == a + 1)
    if consecutive_pairs > 2:
        return False
    return True


def build_candidate_tickets(scores_df: pd.DataFrame, count: int = 8) -> list[dict[str, Any]]:
    rng = np.random.default_rng(RANDOM_SEED)
    pool = scores_df.head(24).copy()
    numbers = pool["number"].astype(int).to_numpy()
    weights = pool["neural_score"].astype(float).to_numpy()
    weights = weights - weights.min() + 0.001
    weights = weights / weights.sum()

    tickets: list[list[int]] = []
    attempts = 0
    while len(tickets) < count and attempts < 5000:
        attempts += 1
        picked = sorted(int(n) for n in rng.choice(numbers, size=NUMBERS_PER_TICKET, replace=False, p=weights))
        if not _ticket_is_balanced(picked):
            continue
        if picked in tickets:
            continue
        tickets.append(picked)

    if not tickets:
        tickets.append(sorted(int(n) for n in scores_df.head(NUMBERS_PER_TICKET)["number"].tolist()))

    cursor = 0
    while len(tickets) < count and cursor <= 20:
        candidate = sorted(int(n) for n in scores_df.iloc[cursor:cursor + NUMBERS_PER_TICKET]["number"].tolist())
        cursor += 1
        if len(candidate) == NUMBERS_PER_TICKET and candidate not in tickets:
            tickets.append(candidate)

    score_map = dict(zip(scores_df["number"].astype(int), scores_df["neural_score"].astype(float)))
    result = []
    for idx, nums in enumerate(tickets[:count], start=1):
        result.append({
            "ticket_id": idx,
            "numbers": nums,
            "neural_ticket_score": round(float(sum(score_map.get(n, 0.0) for n in nums) / NUMBERS_PER_TICKET), 6),
            "odd_count": int(sum(n % 2 for n in nums)),
            "low_count": int(sum(n <= 24 for n in nums)),
            "sum": int(sum(nums)),
        })
    return result


def build_markdown(summary: dict[str, Any], top_numbers: list[int], tickets: list[dict[str, Any]]) -> str:
    metrics = summary["metrics"]
    lines = [
        "# Step 75 — Невронна лаборатория",
        "",
        "Този слой обучава лека невронна meta-мрежа върху историческите тиражи и оценява числата като статистически сигнал.",
        "",
        "**Важно:** това не е гаранция за печалба и не доказва, че бъдещите тегления могат да бъдат предвидени. Лотарията остава случайна игра.",
        "",
        "## Резюме",
        "",
        f"- Статус: **{summary['status']}**",
        f"- Dataset: `{summary['dataset_source']}`",
        f"- Валидни тиражи: **{summary['valid_draws']}**",
        f"- Train draw прозорец: **{metrics['train_draws']}**",
        f"- Test draw прозорец: **{metrics['test_draws']}**",
        f"- Средно познати числа в top 6 при тест: **{metrics['avg_hits_top6']:.3f}**",
        f"- Максимум познати числа в top 6 при тест: **{metrics['max_hits_top6']}**",
        f"- Top neural числа за следващ анализ: **{', '.join(map(str, top_numbers))}**",
        "",
        "## Кандидат фишове",
        "",
    ]
    for ticket in tickets:
        lines.append(
            f"- Фиш {ticket['ticket_id']}: **{', '.join(map(str, ticket['numbers']))}** "
            f"(оценка {ticket['neural_ticket_score']:.4f})"
        )

    lines.extend([
        "",
        "## Метод",
        "",
        "Мрежата използва историческа честота, краткосрочна честота, gap/overdue сигнал, тренд, позиция на числото и баланс характеристики.",
        "Обучението е времево подредено: моделът тренира върху по-старите тиражи и се проверява върху по-новите, за да се намали рискът от leakage.",
    ])
    return "\n".join(lines) + "\n"


def build_neural_meta_learner() -> dict[str, Any]:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    draw_sets, _clean_df, source_path, number_cols = load_draw_sets()
    feature_pack = build_feature_pack(draw_sets)
    trained = train_mlp(feature_pack)

    scores_df = score_next_draw(draw_sets, trained["weights"], feature_pack.feature_names)
    tickets = build_candidate_tickets(scores_df)

    top_numbers = [int(n) for n in scores_df.head(NUMBERS_PER_TICKET)["number"].tolist()]
    top20 = [int(n) for n in scores_df.head(20)["number"].tolist()]

    state_payload = {
        "dataset_source": str(source_path.relative_to(ROOT)),
        "valid_draws": len(draw_sets),
        "number_columns": [str(c) for c in number_cols],
        "top_numbers": top_numbers,
        "top20": top20,
        "metrics": trained["metrics"],
        "tickets": tickets,
    }
    state_hash = hashlib.sha256(json.dumps(state_payload, ensure_ascii=False, sort_keys=True, default=_json_default).encode("utf-8")).hexdigest()[:16]

    summary = {
        "step": 75,
        "name": "Невронна лаборатория",
        "status": "Готово",
        "kind": "neural_meta_learner",
        "dataset_source": str(source_path.relative_to(ROOT)),
        "valid_draws": int(len(draw_sets)),
        "number_columns": [str(c) for c in number_cols],
        "feature_count": int(feature_pack.x.shape[1]),
        "hidden_units": HIDDEN_UNITS,
        "epochs": EPOCHS,
        "random_seed": RANDOM_SEED,
        "metrics": trained["metrics"],
        "top_numbers": top_numbers,
        "top20_numbers": top20,
        "candidate_tickets": tickets,
        "state_hash": state_hash,
        "safe_note": "Статистически neural meta-layer. Не е гаранция за печалба и не отменя случайността на лотарията.",
    }

    model_payload = {
        "step": 75,
        "name": "Невронна лаборатория",
        "kind": "lightweight_numpy_mlp",
        "status": "Готово",
        "dataset_source": str(source_path.relative_to(ROOT)),
        "valid_draws": int(len(draw_sets)),
        "feature_names": feature_pack.feature_names,
        "weights": trained["weights"],
        "metrics": trained["metrics"],
        "state_hash": state_hash,
        "safe_note": summary["safe_note"],
    }

    write_json_if_changed(MODEL_PATH, model_payload)
    scores_df.to_csv(NUMBER_SCORES_CSV, index=False, encoding="utf-8")
    pd.DataFrame(tickets).to_csv(CANDIDATE_TICKETS_CSV, index=False, encoding="utf-8")
    write_json_if_changed(CANDIDATE_TICKETS_JSON, {"tickets": tickets, "state_hash": state_hash})
    write_json_if_changed(SUMMARY_JSON, summary)
    write_text_if_changed(SUMMARY_MD, build_markdown(summary, top_numbers, tickets))

    return summary


def load_summary() -> dict[str, Any]:
    if not SUMMARY_JSON.exists():
        return {}
    return json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))


if __name__ == "__main__":
    summary = build_neural_meta_learner()
    metrics = summary["metrics"]
    print("STEP75_BUILD_OK")
    print("STATUS", summary["status"])
    print("VALID_DRAWS", summary["valid_draws"])
    print("AVG_HITS_TOP6", round(float(metrics["avg_hits_top6"]), 4))
    print("MAX_HITS_TOP6", metrics["max_hits_top6"])
    print("TOP_NUMBERS", ",".join(map(str, summary["top_numbers"])))

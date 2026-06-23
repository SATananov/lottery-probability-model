from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

TOTAL_NUMBERS = 49
DRAW_SIZE = 6
TOTAL_COMBINATIONS = math.comb(TOTAL_NUMBERS, DRAW_SIZE)
BASELINE_NUMBER_PROBABILITY = DRAW_SIZE / TOTAL_NUMBERS

DATA_PATH = Path("data") / "historical_draws.csv"
CONFIG_PATH = Path("configs") / "ml_extensions_config.json"
MODEL_PATH = Path("models") / "lottery_ml_extensions_model.json"
MODEL_VERSION_DIR = Path("models") / "versions"
REPORT_DIR = Path("reports")
MODEL_CARD_PATH = REPORT_DIR / "ml_extensions_model_card.md"
MAIN_REPORT_PATH = REPORT_DIR / "ml_extensions_report.md"
CLASSIFICATION_REPORT_PATH = REPORT_DIR / "ml_classification_report.md"
CLUSTERING_REPORT_PATH = REPORT_DIR / "ml_clustering_report.md"
DIMENSION_REPORT_PATH = REPORT_DIR / "ml_dimensionality_reduction_report.md"
BACKTEST_REPORT_PATH = REPORT_DIR / "ml_extensions_backtest_report.md"

DEFAULT_CONFIG: dict[str, Any] = {
    "random_seed": 20260620,
    "candidate_count": 1200,
    "portfolio_size": 15,
    "cluster_count": 5,
    "backtest_draws": 20,
    "backtest_candidate_count": 200,
    "recent_window": 80,
    "score_weights": {
        "frequency": 0.16,
        "cold_gap": 0.18,
        "middle_balance": 0.14,
        "pair_support": 0.12,
        "triple_support": 0.06,
        "structure": 0.14,
        "human_pattern": 0.10,
        "time_decay": 0.10,
    },
}

FEATURE_NAMES = [
    "sum",
    "odd_count",
    "low_count",
    "middle_count",
    "high_count",
    "span",
    "consecutive_pairs",
    "numbers_under_31",
    "frequency_score",
    "cold_gap_score",
    "middle_balance_score",
    "pair_support",
    "triple_support",
    "structure_score",
    "human_pattern_score",
    "time_decay_score",
]


class MLExtensionError(Exception):
    """Raised when the optional ML extension flow cannot run."""


def ensure_dirs() -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_VERSION_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    ensure_dirs()
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
        return dict(DEFAULT_CONFIG)
    loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    config = dict(DEFAULT_CONFIG)
    for key, value in loaded.items():
        if isinstance(value, dict) and isinstance(config.get(key), dict):
            nested = dict(config[key])
            nested.update(value)
            config[key] = nested
        else:
            config[key] = value
    return config


def read_draws(path: Path = DATA_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Historical dataset not found: {path}")
    draws: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"year", "draw_number", "draw_position", "n1", "n2", "n3", "n4", "n5", "n6"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing CSV columns: {sorted(missing)}")
        for index, row in enumerate(reader, start=1):
            numbers = sorted(int(row[f"n{i}"]) for i in range(1, 7))
            if len(numbers) != 6 or len(set(numbers)) != 6 or any(n < 1 or n > 49 for n in numbers):
                raise ValueError(f"Invalid draw numbers at row {index}: {row}")
            draws.append(
                {
                    "index": index,
                    "date": row.get("date", ""),
                    "year": int(row["year"]),
                    "draw_number": int(row["draw_number"]),
                    "draw_position": int(row["draw_position"]),
                    "numbers": numbers,
                }
            )
    if not draws:
        raise ValueError("Historical dataset is empty.")
    return draws


def number_counts(draws: list[dict[str, Any]]) -> Counter[int]:
    return Counter(n for draw in draws for n in draw["numbers"])


def number_last_seen_gaps(draws: list[dict[str, Any]]) -> dict[int, int]:
    last_seen = {n: -1 for n in range(1, TOTAL_NUMBERS + 1)}
    for idx, draw in enumerate(draws):
        for number in draw["numbers"]:
            last_seen[number] = idx
    final_idx = len(draws) - 1
    return {number: final_idx - pos if pos >= 0 else len(draws) for number, pos in last_seen.items()}


def pair_counts(draws: list[dict[str, Any]]) -> Counter[tuple[int, int]]:
    counter: Counter[tuple[int, int]] = Counter()
    for draw in draws:
        for pair in combinations(draw["numbers"], 2):
            counter[tuple(pair)] += 1
    return counter


def triple_counts(draws: list[dict[str, Any]]) -> Counter[tuple[int, int, int]]:
    counter: Counter[tuple[int, int, int]] = Counter()
    for draw in draws:
        for triple in combinations(draw["numbers"], 3):
            counter[tuple(triple)] += 1
    return counter


def recent_weighted_counts(draws: list[dict[str, Any]], half_life: float = 80.0) -> dict[int, float]:
    weighted = {n: 0.0 for n in range(1, TOTAL_NUMBERS + 1)}
    final_idx = len(draws) - 1
    for idx, draw in enumerate(draws):
        age = max(final_idx - idx, 0)
        weight = 0.5 ** (age / half_life)
        for number in draw["numbers"]:
            weighted[number] += weight
    return weighted


def normalize(values: dict[int, float], default: float = 0.5) -> dict[int, float]:
    raw = [values.get(n, 0.0) for n in range(1, TOTAL_NUMBERS + 1)]
    low = min(raw)
    high = max(raw)
    if math.isclose(low, high):
        return {n: default for n in range(1, TOTAL_NUMBERS + 1)}
    return {n: (values.get(n, low) - low) / (high - low) for n in range(1, TOTAL_NUMBERS + 1)}


def statistics_context(draws: list[dict[str, Any]]) -> dict[str, Any]:
    counts = number_counts(draws)
    gaps = number_last_seen_gaps(draws)
    pairs = pair_counts(draws)
    triples = triple_counts(draws)
    recent = recent_weighted_counts(draws)

    frequency_norm = normalize({n: float(counts.get(n, 0)) for n in range(1, 50)})
    gap_norm = normalize({n: float(gaps.get(n, 0)) for n in range(1, 50)})
    recent_norm = normalize(recent)

    expected = len(draws) * BASELINE_NUMBER_PROBABILITY
    deviation_norm = normalize({n: -abs(counts.get(n, 0) - expected) for n in range(1, 50)})
    cold_norm = normalize({n: max(expected - counts.get(n, 0), 0.0) + 0.15 * gaps.get(n, 0) for n in range(1, 50)})

    return {
        "draw_count": len(draws),
        "counts": counts,
        "gaps": gaps,
        "pairs": pairs,
        "triples": triples,
        "frequency_norm": frequency_norm,
        "gap_norm": gap_norm,
        "recent_norm": recent_norm,
        "middle_norm": deviation_norm,
        "cold_norm": cold_norm,
    }


def combo_structure(numbers: list[int]) -> dict[str, int]:
    nums = sorted(numbers)
    return {
        "odd": sum(1 for n in nums if n % 2),
        "even": sum(1 for n in nums if n % 2 == 0),
        "low": sum(1 for n in nums if n <= 16),
        "middle": sum(1 for n in nums if 17 <= n <= 33),
        "high": sum(1 for n in nums if n >= 34),
        "sum": sum(nums),
        "span": nums[-1] - nums[0],
        "consecutive_pairs": sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1),
        "numbers_under_31": sum(1 for n in nums if n <= 31),
    }


def human_pattern_score(numbers: list[int]) -> float:
    struct = combo_structure(numbers)
    nums = sorted(numbers)
    score = 1.0
    if struct["numbers_under_31"] >= 5:
        score -= 0.35
    if struct["consecutive_pairs"] >= 2:
        score -= 0.25
    if len({n % 10 for n in nums}) <= 3:
        score -= 0.15
    if struct["sum"] < 95 or struct["sum"] > 205:
        score -= 0.15
    if struct["odd"] in {0, 1, 5, 6}:
        score -= 0.10
    return max(0.0, min(1.0, score))


def structure_balance_score(numbers: list[int]) -> float:
    struct = combo_structure(numbers)
    score = 1.0
    score -= min(abs(struct["odd"] - 3) * 0.12, 0.36)
    score -= min(abs(struct["low"] - 2) * 0.08, 0.24)
    score -= min(abs(struct["middle"] - 2) * 0.08, 0.24)
    score -= min(abs(struct["high"] - 2) * 0.08, 0.24)
    if not (100 <= struct["sum"] <= 200):
        score -= 0.18
    if struct["consecutive_pairs"] > 1:
        score -= 0.12 * (struct["consecutive_pairs"] - 1)
    return max(0.0, min(1.0, score))


def combo_features(numbers: list[int], context: dict[str, Any]) -> dict[str, float]:
    nums = sorted(int(n) for n in numbers)
    struct = combo_structure(nums)
    pairs: Counter[tuple[int, int]] = context["pairs"]
    triples: Counter[tuple[int, int, int]] = context["triples"]
    pair_values = [pairs.get(tuple(pair), 0) for pair in combinations(nums, 2)]
    triple_values = [triples.get(tuple(triple), 0) for triple in combinations(nums, 3)]
    max_pair = max(context["pairs"].values() or [1])
    max_triple = max(context["triples"].values() or [1])

    return {
        "sum": float(struct["sum"]),
        "odd_count": float(struct["odd"]),
        "low_count": float(struct["low"]),
        "middle_count": float(struct["middle"]),
        "high_count": float(struct["high"]),
        "span": float(struct["span"]),
        "consecutive_pairs": float(struct["consecutive_pairs"]),
        "numbers_under_31": float(struct["numbers_under_31"]),
        "frequency_score": sum(context["frequency_norm"][n] for n in nums) / DRAW_SIZE,
        "cold_gap_score": sum((context["cold_norm"][n] + context["gap_norm"][n]) / 2 for n in nums) / DRAW_SIZE,
        "middle_balance_score": sum(context["middle_norm"][n] for n in nums) / DRAW_SIZE,
        "pair_support": (sum(pair_values) / len(pair_values)) / max_pair if pair_values else 0.0,
        "triple_support": (sum(triple_values) / len(triple_values)) / max_triple if triple_values else 0.0,
        "structure_score": structure_balance_score(nums),
        "human_pattern_score": human_pattern_score(nums),
        "time_decay_score": sum(context["recent_norm"][n] for n in nums) / DRAW_SIZE,
    }


def composite_score(features: dict[str, float], weights: dict[str, float]) -> float:
    return 100.0 * (
        weights["frequency"] * features["frequency_score"]
        + weights["cold_gap"] * features["cold_gap_score"]
        + weights["middle_balance"] * features["middle_balance_score"]
        + weights["pair_support"] * features["pair_support"]
        + weights["triple_support"] * features["triple_support"]
        + weights["structure"] * features["structure_score"]
        + weights["human_pattern"] * features["human_pattern_score"]
        + weights["time_decay"] * features["time_decay_score"]
    )


def standardize(feature_rows: list[dict[str, float]], names: list[str] = FEATURE_NAMES) -> tuple[list[list[float]], dict[str, float], dict[str, float]]:
    if not feature_rows:
        return [], {}, {}
    means: dict[str, float] = {}
    stds: dict[str, float] = {}
    for name in names:
        values = [row.get(name, 0.0) for row in feature_rows]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / max(len(values) - 1, 1)
        std = math.sqrt(variance) or 1.0
        means[name] = mean
        stds[name] = std
    matrix = [[(row.get(name, 0.0) - means[name]) / stds[name] for name in names] for row in feature_rows]
    return matrix, means, stds


def apply_standardize(features: dict[str, float], means: dict[str, float], stds: dict[str, float], names: list[str] = FEATURE_NAMES) -> list[float]:
    return [(features.get(name, 0.0) - means.get(name, 0.0)) / (stds.get(name, 1.0) or 1.0) for name in names]


def euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def train_centroid_classifier(feature_rows: list[dict[str, float]], scores: list[float]) -> dict[str, Any]:
    if not feature_rows:
        return {"classes": [], "centroids": {}, "feature_means": {}, "feature_stds": {}}
    ordered = sorted(scores)
    q1 = ordered[int(len(ordered) * 0.33)]
    q2 = ordered[int(len(ordered) * 0.66)]

    labels = []
    for score in scores:
        if score >= q2:
            labels.append("силен статистически фиш")
        elif score >= q1:
            labels.append("нормален статистически фиш")
        else:
            labels.append("слаб статистически фиш")

    matrix, means, stds = standardize(feature_rows)
    grouped: dict[str, list[list[float]]] = defaultdict(list)
    for vector, label in zip(matrix, labels):
        grouped[label].append(vector)

    centroids = {}
    for label, vectors in grouped.items():
        centroids[label] = [sum(vector[i] for vector in vectors) / len(vectors) for i in range(len(FEATURE_NAMES))]

    return {
        "type": "nearest_centroid_classifier",
        "target": "слаб / нормален / силен статистически фиш",
        "classes": sorted(centroids),
        "score_quantiles": {"q33": round(q1, 4), "q66": round(q2, 4)},
        "feature_names": FEATURE_NAMES,
        "feature_means": means,
        "feature_stds": stds,
        "centroids": centroids,
    }


def classify_features(features: dict[str, float], classifier: dict[str, Any]) -> dict[str, Any]:
    centroids = classifier.get("centroids", {})
    if not centroids:
        return {"class": "неизвестно", "confidence": 0.0}
    vector = apply_standardize(features, classifier.get("feature_means", {}), classifier.get("feature_stds", {}), classifier.get("feature_names", FEATURE_NAMES))
    distances = {label: euclidean(vector, centroid) for label, centroid in centroids.items()}
    best = min(distances, key=distances.get)
    sorted_distances = sorted(distances.values())
    if len(sorted_distances) > 1:
        confidence = max(0.0, min(1.0, 1.0 - sorted_distances[0] / (sorted_distances[1] + 1.0e-9)))
    else:
        confidence = 1.0
    return {"class": best, "confidence": round(confidence * 100, 2), "distances": {k: round(v, 4) for k, v in distances.items()}}


def kmeans(matrix: list[list[float]], k: int, seed: int, iterations: int = 40) -> tuple[list[int], list[list[float]]]:
    rng = random.Random(seed)
    if not matrix:
        return [], []
    k = max(1, min(k, len(matrix)))
    centroids = [matrix[i][:] for i in rng.sample(range(len(matrix)), k)]
    assignments = [0] * len(matrix)
    for _ in range(iterations):
        changed = False
        for i, vector in enumerate(matrix):
            best = min(range(k), key=lambda idx: euclidean(vector, centroids[idx]))
            if assignments[i] != best:
                assignments[i] = best
                changed = True
        new_centroids: list[list[float]] = []
        for cluster_idx in range(k):
            vectors = [vector for vector, assigned in zip(matrix, assignments) if assigned == cluster_idx]
            if not vectors:
                new_centroids.append(matrix[rng.randrange(len(matrix))][:])
            else:
                new_centroids.append([sum(vector[j] for vector in vectors) / len(vectors) for j in range(len(matrix[0]))])
        centroids = new_centroids
        if not changed:
            break
    return assignments, centroids


def label_cluster(feature_rows: list[dict[str, float]]) -> str:
    if not feature_rows:
        return "празен клъстер"
    avg = {name: sum(row.get(name, 0.0) for row in feature_rows) / len(feature_rows) for name in FEATURE_NAMES}
    if avg["human_pattern_score"] < 0.55:
        return "по-човешки / рискови фишове"
    if avg["cold_gap_score"] >= max(avg["frequency_score"], avg["middle_balance_score"]):
        return "студено-интервални фишове"
    if avg["frequency_score"] >= max(avg["cold_gap_score"], avg["middle_balance_score"]):
        return "честотни фишове"
    if avg["structure_score"] > 0.75 and avg["middle_balance_score"] > 0.55:
        return "балансирани фишове"
    return "смесени статистически фишове"


def train_cluster_model(feature_rows: list[dict[str, float]], k: int, seed: int) -> dict[str, Any]:
    matrix, means, stds = standardize(feature_rows)
    assignments, centroids = kmeans(matrix, k, seed)
    grouped: dict[int, list[dict[str, float]]] = defaultdict(list)
    for row, cluster in zip(feature_rows, assignments):
        grouped[cluster].append(row)
    summaries = []
    for idx in sorted(grouped):
        rows = grouped[idx]
        avg_score = sum(row.get("final_score", 0.0) for row in rows) / len(rows)
        summaries.append({
            "cluster": idx,
            "label": label_cluster(rows),
            "size": len(rows),
            "average_score": round(avg_score, 4),
            "avg_frequency_score": round(sum(row.get("frequency_score", 0.0) for row in rows) / len(rows), 4),
            "avg_cold_gap_score": round(sum(row.get("cold_gap_score", 0.0) for row in rows) / len(rows), 4),
            "avg_structure_score": round(sum(row.get("structure_score", 0.0) for row in rows) / len(rows), 4),
            "avg_human_pattern_score": round(sum(row.get("human_pattern_score", 0.0) for row in rows) / len(rows), 4),
        })
    return {
        "type": "kmeans_from_scratch",
        "cluster_count": len(centroids),
        "feature_names": FEATURE_NAMES,
        "feature_means": means,
        "feature_stds": stds,
        "centroids": centroids,
        "cluster_summaries": summaries,
    }


def assign_cluster(features: dict[str, float], cluster_model: dict[str, Any]) -> int:
    centroids = cluster_model.get("centroids", [])
    if not centroids:
        return -1
    vector = apply_standardize(features, cluster_model.get("feature_means", {}), cluster_model.get("feature_stds", {}), cluster_model.get("feature_names", FEATURE_NAMES))
    return int(min(range(len(centroids)), key=lambda idx: euclidean(vector, centroids[idx])))


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def mat_vec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [dot(row, vector) for row in matrix]


def norm(vector: list[float]) -> float:
    return math.sqrt(sum(x * x for x in vector)) or 1.0


def power_iteration(covariance: list[list[float]], seed: int, iterations: int = 80) -> list[float]:
    rng = random.Random(seed)
    vector = [rng.uniform(-1.0, 1.0) for _ in covariance]
    vector_norm = norm(vector)
    vector = [x / vector_norm for x in vector]
    for _ in range(iterations):
        next_vector = mat_vec(covariance, vector)
        next_norm = norm(next_vector)
        vector = [x / next_norm for x in next_vector]
    return vector


def covariance_matrix(matrix: list[list[float]]) -> list[list[float]]:
    if not matrix:
        return []
    rows = len(matrix)
    cols = len(matrix[0])
    cov = [[0.0 for _ in range(cols)] for _ in range(cols)]
    for i in range(cols):
        for j in range(cols):
            cov[i][j] = sum(row[i] * row[j] for row in matrix) / max(rows - 1, 1)
    return cov


def deflate(covariance: list[list[float]], vector: list[float], eigenvalue: float) -> list[list[float]]:
    size = len(covariance)
    return [[covariance[i][j] - eigenvalue * vector[i] * vector[j] for j in range(size)] for i in range(size)]


def pca_2d(feature_rows: list[dict[str, float]], seed: int) -> dict[str, Any]:
    matrix, means, stds = standardize(feature_rows)
    if not matrix:
        return {"type": "pca_from_scratch", "points": []}
    cov = covariance_matrix(matrix)
    pc1 = power_iteration(cov, seed + 11)
    eigen1 = dot(pc1, mat_vec(cov, pc1))
    cov2 = deflate(cov, pc1, eigen1)
    pc2 = power_iteration(cov2, seed + 23)
    eigen2 = max(0.0, dot(pc2, mat_vec(cov2, pc2)))
    total_variance = sum(cov[i][i] for i in range(len(cov))) or 1.0
    points = []
    for row, vector in zip(feature_rows, matrix):
        points.append({
            "numbers": row.get("numbers", []),
            "x": round(dot(vector, pc1), 4),
            "y": round(dot(vector, pc2), 4),
            "score": round(row.get("final_score", 0.0), 4),
        })
    return {
        "type": "pca_from_scratch",
        "feature_names": FEATURE_NAMES,
        "feature_means": means,
        "feature_stds": stds,
        "components": [pc1, pc2],
        "explained_variance_ratio": [round(eigen1 / total_variance, 4), round(eigen2 / total_variance, 4)],
        "points": points,
    }


def generate_candidate_combinations(draws: list[dict[str, Any]], config: dict[str, Any]) -> list[list[int]]:
    rng = random.Random(int(config["random_seed"]))
    target_count = int(config["candidate_count"])
    recent_window = int(config.get("recent_window", 80))
    context = statistics_context(draws)
    frequent = [n for n, _ in number_counts(draws).most_common(18)]
    cold = sorted(range(1, 50), key=lambda n: (context["cold_norm"][n], context["gap_norm"][n]), reverse=True)[:18]
    middle = sorted(range(1, 50), key=lambda n: context["middle_norm"][n], reverse=True)[:18]
    recent_draws = draws[-recent_window:] if recent_window > 0 else draws
    recent_numbers = [n for n, _ in number_counts(recent_draws).most_common(18)]
    pools = [frequent, cold, middle, recent_numbers, list(range(1, 50))]

    candidates: set[tuple[int, ...]] = set()
    # Include existing top model recommendations if available.
    for model_name in [
        "lottery_advanced_ensemble_model.json",
        "lottery_combined_model.json",
        "lottery_frequency_model.json",
        "lottery_cold_model.json",
        "lottery_middle_model.json",
        "lottery_gap_model.json",
    ]:
        path = Path("models") / model_name
        if path.exists():
            try:
                model = json.loads(path.read_text(encoding="utf-8-sig"))
                for key in ["recommended_ticket", "recommended_numbers"]:
                    value = model.get(key)
                    if isinstance(value, list) and len(value) >= 6:
                        candidates.add(tuple(sorted(int(x) for x in value[:6])))
                for key in ["recommended_combinations", "portfolio_recommendations"]:
                    values = model.get(key)
                    if isinstance(values, list):
                        for item in values[:30]:
                            numbers = item.get("numbers") if isinstance(item, dict) else item
                            if isinstance(numbers, list) and len(numbers) >= 6:
                                candidates.add(tuple(sorted(int(x) for x in numbers[:6])))
            except Exception:
                pass

    attempts = 0
    while len(candidates) < target_count and attempts < target_count * 20:
        attempts += 1
        pool = rng.choice(pools)
        combo = sorted(rng.sample(pool if len(pool) >= 6 else list(range(1, 50)), 6))
        if len(set(combo)) == 6:
            candidates.add(tuple(combo))
    return [list(item) for item in sorted(candidates)]


def score_candidates(draws: list[dict[str, Any]], candidates: list[list[int]], config: dict[str, Any]) -> list[dict[str, Any]]:
    context = statistics_context(draws)
    weights = config["score_weights"]
    rows = []
    for numbers in candidates:
        features = combo_features(numbers, context)
        score = composite_score(features, weights)
        row = dict(features)
        row["numbers"] = sorted(numbers)
        row["final_score"] = score
        rows.append(row)
    rows.sort(key=lambda row: row["final_score"], reverse=True)
    return rows


def train_ml_extensions(draws: list[dict[str, Any]] | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_dirs()
    config = config or load_config()
    draws = draws or read_draws()
    candidates = generate_candidate_combinations(draws, config)
    scored = score_candidates(draws, candidates, config)

    classifier = train_centroid_classifier(scored, [row["final_score"] for row in scored])
    cluster_model = train_cluster_model(scored, int(config["cluster_count"]), int(config["random_seed"]))
    reduction = pca_2d(scored[: min(400, len(scored))], int(config["random_seed"]))

    recommendations = []
    for rank, row in enumerate(scored[: int(config["portfolio_size"])], start=1):
        classification = classify_features(row, classifier)
        cluster_id = assign_cluster(row, cluster_model)
        cluster_label = next((item["label"] for item in cluster_model["cluster_summaries"] if item["cluster"] == cluster_id), "неизвестен клъстер")
        recommendations.append(
            {
                "rank": rank,
                "numbers": row["numbers"],
                "confidence_score": round(row["final_score"], 2),
                "classification": classification["class"],
                "classification_confidence": classification["confidence"],
                "cluster": cluster_id,
                "cluster_label": cluster_label,
                "relative_model_probability": round(row["final_score"] / sum(item["final_score"] for item in scored[:100]) * 100, 6) if scored[:100] else 0.0,
                "theoretical_jackpot_odds": f"1 към {TOTAL_COMBINATIONS}",
                "feature_summary": {
                    key: round(row.get(key, 0.0), 4)
                    for key in [
                        "frequency_score",
                        "cold_gap_score",
                        "middle_balance_score",
                        "pair_support",
                        "triple_support",
                        "structure_score",
                        "human_pattern_score",
                        "time_decay_score",
                    ]
                },
            }
        )

    model = {
        "model_name": "Lottery ML Extensions Ensemble",
        "model_version": "1.0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "training_draws": len(draws),
        "candidate_count": len(scored),
        "important_note": "Това е статистическо ранкиране, класификация, клъстеризация и редукция на размерността за анализ. Не променя реалния шанс за джакпот.",
        "theoretical_jackpot_odds": f"1 към {TOTAL_COMBINATIONS}",
        "implemented_course_topics": [
            "Feature Engineering",
            "Time Series / rolling historical order",
            "Classification",
            "Unsupervised Learning / Clustering",
            "Dimensionality Reduction",
            "Testing / Backtesting",
            "Machine Learning Tools: конфигурация, карта на модела и версионирани артефакти",
        ],
        "configuration": config,
        "classifier": classifier,
        "cluster_model": cluster_model,
        "dimensionality_reduction": {k: v for k, v in reduction.items() if k != "points"},
        "projection_points_sample": reduction.get("points", [])[:60],
        "recommended_combinations": recommendations,
    }
    return model


def save_model(model: dict[str, Any]) -> None:
    ensure_dirs()
    MODEL_PATH.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version_path = MODEL_VERSION_DIR / f"lottery_ml_extensions_model_v1_{stamp}.json"
    version_path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")


def write_reports(model: dict[str, Any]) -> None:
    ensure_dirs()
    recs = model.get("recommended_combinations", [])
    cluster_summaries = model.get("cluster_model", {}).get("cluster_summaries", [])
    evr = model.get("dimensionality_reduction", {}).get("explained_variance_ratio", [])

    MAIN_REPORT_PATH.write_text(
        "\n".join(
            [
                "# Отчет за МЛ разширенията",
                "",
                "Този отчет добавя класификация, клъстеризация, редукция на размерността и МЛ инструменти към lottery проекта.",
                "Проектът остава статистически анализ. Реалният шанс за точна 6/49 комбинация не се променя.",
                "",
                f"Обучени тиражи: {model.get('training_draws')}",
                f"Кандидат-комбинации: {model.get('candidate_count')}",
                f"Реален шанс за точна комбинация: {model.get('theoretical_jackpot_odds')}",
                "",
                "## Топ МЛ препоръки",
                "",
                *[
                    f"- Ранг {item['rank']}: {item['numbers']} | оценка={item['confidence_score']}/100 | клас={item['classification']} | клъстер={item['cluster_label']}"
                    for item in recs[:10]
                ],
            ]
        ),
        encoding="utf-8",
    )

    CLASSIFICATION_REPORT_PATH.write_text(
        "\n".join(
            [
                "# Отчет за класификация",
                "",
                "Метод: nearest-centroid classifier върху engineered features.",
                "Цел: слаб / нормален / силен статистически фиш.",
                "Това не е гаранция за печалба, а разбираема класификация на комбинации.",
                "",
                "## Класове",
                *[f"- {label}" for label in model.get("classifier", {}).get("classes", [])],
                "",
                "## Прагове на оценката",
                json.dumps(model.get("classifier", {}).get("score_quantiles", {}), ensure_ascii=False, indent=2),
            ]
        ),
        encoding="utf-8",
    )

    CLUSTERING_REPORT_PATH.write_text(
        "\n".join(
            [
                "# Отчет за клъстеризация",
                "",
                "Метод: k-means from scratch върху standardized engineered features.",
                "Цел: групиране на комбинации по статистически профил.",
                "",
                "## Обобщение на клъстерите",
                *[
                    f"- Клъстер {item['cluster']}: {item['label']} | брой={item['size']} | средна оценка={item['average_score']}"
                    for item in cluster_summaries
                ],
            ]
        ),
        encoding="utf-8",
    )

    DIMENSION_REPORT_PATH.write_text(
        "\n".join(
            [
                "# Отчет за редукция на размерността",
                "",
                "Метод: PCA from scratch върху standardized engineered features.",
                "Цел: 2D карта за визуално сравнение на комбинации.",
                "",
                f"Обяснена вариация: {evr}",
                "",
                "Първата ос обикновено събира обща статистическа сила на фиша, а втората отделя структурни/интервални разлики.",
            ]
        ),
        encoding="utf-8",
    )

    MODEL_CARD_PATH.write_text(
        "\n".join(
            [
                "# Карта на модела — Lottery ML Extensions Ensemble",
                "",
                "## Цел",
                "Образователен статистически модел за анализ на Българско тото 2 — 6/49.",
                "",
                "## Приложени техники",
                "- Feature engineering / инженеринг на характеристики",
                "- Анализ във времеви ред",
                "- Класификация",
                "- Клъстеризация",
                "- Редукция на размерността",
                "- Историческа проверка / testing",
                "- Конфигурация и версионирани артефакти",
                "",
                "## Ограничения",
                "Лотарийните тегления са случайни. Всяка точна 6-числова комбинация остава с един и същ реален шанс: 1 към 13,983,816.",
                "Моделната оценка е относително статистическо класиране, не реално обещание за печалба.",
                "",
                "## Данни",
                f"Обучени тиражи: {model.get('training_draws')}",
                "Източник на данни: data/historical_draws.csv, поддържан като исторически dataset.",
            ]
        ),
        encoding="utf-8",
    )


def run_backtest(draws: list[dict[str, Any]] | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    draws = draws or read_draws()
    n = int(config.get("backtest_draws", 60))
    candidate_count = int(config.get("backtest_candidate_count", 900))
    start = max(30, len(draws) - n)
    results = []
    for idx in range(start, len(draws)):
        train_draws = draws[:idx]
        actual = set(draws[idx]["numbers"])
        local_config = dict(config)
        local_config["candidate_count"] = candidate_count
        model = train_ml_extensions(train_draws, local_config)
        recs = model.get("recommended_combinations", [])
        if not recs:
            continue
        prediction = set(recs[0]["numbers"])
        matches = len(actual & prediction)
        results.append(
            {
                "draw_index": idx + 1,
                "year": draws[idx]["year"],
                "draw_number": draws[idx]["draw_number"],
                "actual": sorted(actual),
                "predicted": sorted(prediction),
                "matches": matches,
                "classification": recs[0].get("classification"),
                "score": recs[0].get("confidence_score"),
            }
        )
    distribution = Counter(item["matches"] for item in results)
    average_matches = sum(item["matches"] for item in results) / len(results) if results else 0.0
    summary = {
        "tested_draws": len(results),
        "average_matches": round(average_matches, 4),
        "hit_rate_ge_2": round(sum(1 for item in results if item["matches"] >= 2) / len(results) * 100, 2) if results else 0.0,
        "hit_rate_ge_3": round(sum(1 for item in results if item["matches"] >= 3) / len(results) * 100, 2) if results else 0.0,
        "distribution": {str(k): distribution.get(k, 0) for k in range(7)},
        "details": results,
    }
    ensure_dirs()
    BACKTEST_REPORT_PATH.write_text(
        "\n".join(
            [
                "# Отчет от историческа проверка на МЛ разширенията",
                "",
                f"Тествани тиражи: {summary['tested_draws']}",
                f"Средни съвпадения: {summary['average_matches']}",
                f">=2 matches: {summary['hit_rate_ge_2']}%",
                f">=3 matches: {summary['hit_rate_ge_3']}%",
                "",
                "Това е историческа проверка, не доказателство, че бъдещи тегления са предсказуеми.",
                "",
                "## Последни тествани тиражи",
                *[
                    f"- Тираж {item['draw_number']} ({item['year']}): реални={item['actual']}, препоръчани={item['predicted']} ({item['matches']} съвпадения)"
                    for item in results[-20:]
                ],
            ]
        ),
        encoding="utf-8",
    )
    return summary


def train_save_report() -> dict[str, Any]:
    config = load_config()
    draws = read_draws()
    model = train_ml_extensions(draws, config)
    backtest = run_backtest(draws, config)
    model["backtest_summary"] = {k: v for k, v in backtest.items() if k != "details"}
    save_model(model)
    write_reports(model)
    return model


if __name__ == "__main__":
    trained = train_save_report()
    print("Lottery ML extensions trained")
    print("----------------------------------------")
    print(f"Training draws: {trained['training_draws']}")
    print(f"Candidate combinations: {trained['candidate_count']}")
    print("Top recommendations:")
    for item in trained.get("recommended_combinations", [])[:10]:
        print(
            f"Rank {item['rank']}: {item['numbers']} | score={item['confidence_score']}/100 | "
            f"клас={item['classification']} | клъстер={item['cluster_label']}"
        )

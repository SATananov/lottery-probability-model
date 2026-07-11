from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NUMBER_COLUMNS = [f"n{i}" for i in range(1, 7)]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _latest_row(draws: pd.DataFrame) -> pd.Series:
    ordered = draws.copy()
    ordered["_year"] = pd.to_numeric(ordered.get("year", 0), errors="coerce").fillna(0).astype(int)
    draw_series = ordered["draw_number"] if "draw_number" in ordered.columns else ordered.get("draw_no", 0)
    ordered["_draw"] = pd.to_numeric(draw_series, errors="coerce").fillna(0).astype(int)
    ordered["_date"] = ordered.get("date", "").fillna("").astype(str)
    return ordered.sort_values(["_year", "_draw", "_date"]).iloc[-1]


def _safe_plot(plot_path: Path, build_plot) -> None:
    try:
        import matplotlib.pyplot as plt

        plot_path.parent.mkdir(parents=True, exist_ok=True)
        fig = plt.figure(figsize=(12, 7))
        build_plot(plt)
        fig.tight_layout()
        fig.savefig(plot_path, dpi=100)
        plt.close(fig)
    except Exception:
        # Plots are useful diagnostics but are not freshness blockers.
        pass


def generate_python_compatible_r_reports(
    *,
    project_root: Path | str = ROOT,
    simulations: int = 100,
    seed: int = 42,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Generate the base statistical artifacts when Rscript is unavailable.

    The calculations mirror the project's base-R scripts closely enough for the
    downstream feature layer. The report records that this compatibility path was
    used; it does not claim that R itself executed.
    """

    root = Path(project_root).resolve()
    data_path = root / "data" / "historical_draws.csv"
    out_dir = root / "reports" / "r"
    plot_dir = out_dir / "plots"
    if not data_path.exists():
        raise FileNotFoundError(f"Historical dataset not found: {data_path}")

    draws = pd.read_csv(data_path)
    missing = [column for column in NUMBER_COLUMNS if column not in draws.columns]
    if missing:
        raise ValueError(f"Historical dataset is missing number columns: {missing}")

    number_frame = draws[NUMBER_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if number_frame.isna().any().any():
        raise ValueError("Historical dataset contains non-numeric lottery values.")
    numbers_matrix = number_frame.astype(int).to_numpy()
    latest = _latest_row(draws)
    latest_numbers = [int(latest[column]) for column in NUMBER_COLUMNS]
    latest_date = str(latest.get("date", "") or "")
    latest_draw_number = int(latest.get("draw_number", latest.get("draw_no", 0)) or 0)
    latest_year = int(latest.get("year", latest_date[:4] if latest_date else 0) or 0)

    invalid_cells = int(np.sum((numbers_matrix < 1) | (numbers_matrix > 49)))
    duplicate_rows = int(sum(len(set(row.tolist())) != 6 for row in numbers_matrix))
    missing_dates = int(draws.get("date", pd.Series([""] * len(draws))).fillna("").astype(str).eq("").sum())

    audit_rows = [
        {"metric": "rows", "value": str(len(draws))},
        {"metric": "latest_date", "value": latest_date},
        {"metric": "latest_draw_number", "value": str(latest_draw_number)},
        {"metric": "latest_numbers", "value": ", ".join(map(str, latest_numbers))},
        {"metric": "invalid_number_cells", "value": str(invalid_cells)},
        {"metric": "rows_with_duplicate_numbers", "value": str(duplicate_rows)},
        {"metric": "missing_date_values", "value": str(missing_dates)},
    ]

    draw_sums = numbers_matrix.sum(axis=1)
    draw_numbers = (
        pd.to_numeric(draws["draw_number"], errors="coerce").fillna(0).astype(int)
        if "draw_number" in draws.columns
        else pd.to_numeric(draws["draw_no"], errors="coerce").fillna(0).astype(int)
    )
    draw_sum_rows = [
        {"date": str(date or ""), "draw_number": int(draw_number), "draw_sum": int(total)}
        for date, draw_number, total in zip(draws.get("date", [""] * len(draws)), draw_numbers, draw_sums)
    ]

    flat_numbers = numbers_matrix.reshape(-1)
    counts = np.bincount(flat_numbers, minlength=50)[1:50].astype(int)
    expected_uniform_count = float(counts.sum() / 49.0)
    frequency_rows = [
        {
            "number": number,
            "frequency": int(counts[number - 1]),
            "frequency_share": float(counts[number - 1] / counts.sum()),
            "expected_uniform_count": expected_uniform_count,
            "diff_from_expected": float(counts[number - 1] - expected_uniform_count),
        }
        for number in range(1, 50)
    ]
    frequency_rows.sort(key=lambda row: (-row["frequency"], row["number"]))
    for rank, row in enumerate(frequency_rows, start=1):
        row["rank_desc"] = rank
    hot_rows = frequency_rows[:10]
    cold_rows = sorted(frequency_rows, key=lambda row: (row["frequency"], row["number"]))[:10]

    gap_rows: list[dict[str, Any]] = []
    row_count = len(numbers_matrix)
    for number in range(1, 50):
        hit_index = np.where(np.any(numbers_matrix == number, axis=1))[0] + 1  # R uses one-based indices.
        if not len(hit_index):
            gap_rows.append({
                "number": number,
                "appearances": 0,
                "current_gap": "",
                "average_gap": "",
                "max_gap": "",
                "gap_ratio": "",
            })
            continue
        gaps = np.diff(hit_index)
        current_gap = int(row_count - hit_index[-1])
        average_gap = float(gaps.mean()) if len(gaps) else ""
        max_gap = int(gaps.max()) if len(gaps) else ""
        ratio = float(current_gap / average_gap) if average_gap not in {"", 0.0} else ""
        gap_rows.append({
            "number": number,
            "appearances": int(len(hit_index)),
            "current_gap": current_gap,
            "average_gap": average_gap,
            "max_gap": max_gap,
            "gap_ratio": ratio,
        })
    gap_rows.sort(key=lambda row: (-(row["current_gap"] if row["current_gap"] != "" else -1), row["number"]))

    odd_count = (numbers_matrix % 2 == 1).sum(axis=1)
    even_count = 6 - odd_count
    low_count = (numbers_matrix <= 24).sum(axis=1)
    high_count = 6 - low_count
    spread = numbers_matrix.max(axis=1) - numbers_matrix.min(axis=1)
    pattern_rows = [
        {
            "date": str(date or ""),
            "draw_number": int(draw_number),
            "draw_sum": int(total),
            "odd_count": int(odd),
            "even_count": int(even),
            "low_count": int(low),
            "high_count": int(high),
            "spread": int(row_spread),
        }
        for date, draw_number, total, odd, even, low, high, row_spread in zip(
            draws.get("date", [""] * len(draws)),
            draw_numbers,
            draw_sums,
            odd_count,
            even_count,
            low_count,
            high_count,
            spread,
        )
    ]

    chi_square = float(np.sum((counts - expected_uniform_count) ** 2 / expected_uniform_count))
    try:
        from scipy.stats import chi2

        chi_p = float(chi2.sf(chi_square, 48))
    except Exception:
        chi_p = ""
    distribution_rows = [
        {"test": "chi_square_uniform_number_frequency", "statistic": chi_square, "p_value": chi_p, "note": "Chi-square test against uniform number frequency."},
        {"test": "draw_sum_mean", "statistic": float(np.mean(draw_sums)), "p_value": "", "note": "Average sum of six numbers."},
        {"test": "draw_sum_sd", "statistic": float(np.std(draw_sums, ddof=1)), "p_value": "", "note": "Standard deviation of draw sums."},
        {"test": "odd_count_mean", "statistic": float(np.mean(odd_count)), "p_value": "", "note": "Average odd count."},
        {"test": "low_count_mean", "statistic": float(np.mean(low_count)), "p_value": "", "note": "Average low count where low <= 24."},
        {"test": "spread_mean", "statistic": float(np.mean(spread)), "p_value": "", "note": "Average spread between max and min number."},
    ]

    pair_counter: Counter[tuple[int, int]] = Counter()
    for row in numbers_matrix:
        pair_counter.update(combinations(sorted(int(value) for value in row), 2))
    pair_rows = [
        {"pair_a": a, "pair_b": b, "pair": f"{a}-{b}", "frequency": count}
        for (a, b), count in sorted(pair_counter.items(), key=lambda item: (-item[1], item[0]))
    ]

    rng = np.random.default_rng(seed)
    simulation_matrix = np.zeros((int(simulations), 49), dtype=int)
    for simulation_index in range(int(simulations)):
        random_keys = rng.random((row_count, 49))
        sampled = np.argpartition(random_keys, kth=5, axis=1)[:, :6]
        simulation_matrix[simulation_index] = np.bincount(sampled.reshape(-1), minlength=49)
    simulated_mean = simulation_matrix.mean(axis=0)
    simulated_p05 = np.quantile(simulation_matrix, 0.05, axis=0)
    simulated_p95 = np.quantile(simulation_matrix, 0.95, axis=0)
    monte_rows = [
        {
            "number": number,
            "real_frequency": int(counts[number - 1]),
            "simulated_mean": float(simulated_mean[number - 1]),
            "simulated_p05": float(simulated_p05[number - 1]),
            "simulated_p95": float(simulated_p95[number - 1]),
            "above_p95": bool(counts[number - 1] > simulated_p95[number - 1]),
            "below_p05": bool(counts[number - 1] < simulated_p05[number - 1]),
        }
        for number in range(1, 50)
    ]

    above_band = [row["number"] for row in monte_rows if row["above_p95"]]
    below_band = [row["number"] for row in monte_rows if row["below_p05"]]
    top_hot = [row["number"] for row in frequency_rows[:10]]
    top_gap = [row["number"] for row in gap_rows[:10]]
    summary_lines = [
        "# R Statistical Summary",
        "",
        f"Dataset rows: {len(draws)}",
        f"Latest draw date: {latest_date}",
        f"Latest numbers: {', '.join(map(str, latest_numbers))}",
        "",
        "## Frequency",
        "",
        f"Top frequent numbers: {', '.join(map(str, top_hot))}",
        "",
        "## Gap analysis",
        "",
        f"Largest current gap numbers: {', '.join(map(str, top_gap))}",
        "",
        "## Distribution test",
        "",
        f"Chi-square statistic: {round(chi_square, 4)}",
        f"Chi-square p-value: {format(chi_p, '.4g') if isinstance(chi_p, float) else 'n/a'}",
        "",
        "## Monte Carlo baseline",
        "",
        f"Numbers above simulated 95% band: {', '.join(map(str, above_band)) if above_band else 'none'}",
        f"Numbers below simulated 5% band: {', '.join(map(str, below_band)) if below_band else 'none'}",
        "",
        "## Interpretation",
        "",
        "The statistical layer provides additional visibility over the lottery dataset.",
        "It is intended for validation, diagnostics, visualization, and model review.",
        "It does not guarantee future lottery outcomes.",
    ]

    if write_outputs:
        out_dir.mkdir(parents=True, exist_ok=True)
        plot_dir.mkdir(parents=True, exist_ok=True)
        _write_csv(out_dir / "r_data_audit.csv", audit_rows, ["metric", "value"])
        _write_csv(out_dir / "r_draw_sum_history.csv", draw_sum_rows, ["date", "draw_number", "draw_sum"])
        _write_csv(out_dir / "r_frequency_statistics.csv", frequency_rows, ["number", "frequency", "frequency_share", "expected_uniform_count", "diff_from_expected", "rank_desc"])
        _write_csv(out_dir / "r_hot_numbers.csv", hot_rows, ["number", "frequency", "frequency_share", "expected_uniform_count", "diff_from_expected", "rank_desc"])
        _write_csv(out_dir / "r_cold_numbers.csv", cold_rows, ["number", "frequency", "frequency_share", "expected_uniform_count", "diff_from_expected", "rank_desc"])
        _write_csv(out_dir / "r_gap_statistics.csv", gap_rows, ["number", "appearances", "current_gap", "average_gap", "max_gap", "gap_ratio"])
        _write_csv(out_dir / "r_pattern_analysis.csv", pattern_rows, ["date", "draw_number", "draw_sum", "odd_count", "even_count", "low_count", "high_count", "spread"])
        _write_csv(out_dir / "r_distribution_tests.csv", distribution_rows, ["test", "statistic", "p_value", "note"])
        _write_csv(out_dir / "r_pair_analysis.csv", pair_rows, ["pair_a", "pair_b", "pair", "frequency"])
        _write_csv(out_dir / "r_monte_carlo_baseline.csv", monte_rows, ["number", "real_frequency", "simulated_mean", "simulated_p05", "simulated_p95", "above_p95", "below_p05"])
        (out_dir / "r_statistical_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

        _safe_plot(plot_dir / "draw_sum_distribution.png", lambda plt: plt.hist(draw_sums, bins=30))
        _safe_plot(plot_dir / "number_frequency.png", lambda plt: plt.bar(np.arange(1, 50), counts))
        top_gap_rows = gap_rows[:15]
        _safe_plot(plot_dir / "largest_current_gaps.png", lambda plt: plt.barh([str(row["number"]) for row in top_gap_rows], [row["current_gap"] for row in top_gap_rows]))
        _safe_plot(plot_dir / "odd_count_distribution.png", lambda plt: plt.bar(*np.unique(odd_count, return_counts=True)))
        _safe_plot(plot_dir / "low_count_distribution.png", lambda plt: plt.bar(*np.unique(low_count, return_counts=True)))
        top_pair_rows = pair_rows[:25]
        _safe_plot(plot_dir / "top_pairs.png", lambda plt: plt.barh([row["pair"] for row in top_pair_rows], [row["frequency"] for row in top_pair_rows]))

        def monte_plot(plt):
            x = np.arange(1, 50)
            plt.plot(x, counts, marker="o", linestyle="None")
            plt.plot(x, simulated_mean, linestyle="--")
            plt.plot(x, simulated_p05, linestyle=":")
            plt.plot(x, simulated_p95, linestyle=":")

        _safe_plot(plot_dir / "monte_carlo_frequency_baseline.png", monte_plot)

    return {
        "generated_at_utc": utc_now(),
        "runner": "python_compatibility",
        "latest_draw": {
            "year": latest_year,
            "draw_number": latest_draw_number,
            "date": latest_date,
            "numbers": latest_numbers,
        },
        "dataset_rows": len(draws),
        "invalid_number_cells": invalid_cells,
        "rows_with_duplicate_numbers": duplicate_rows,
        "simulations": int(simulations),
        "seed": int(seed),
        "heavy_ml_retraining_performed": False,
        "output_directory": str(out_dir.relative_to(root)).replace("\\", "/"),
    }

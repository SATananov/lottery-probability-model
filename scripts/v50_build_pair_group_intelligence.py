
from __future__ import annotations

import itertools
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_CANDIDATES = [
    ROOT / "data" / "v41_canonical_draw_events.csv",
    ROOT / "data" / "historical_draws.csv",
]

MODEL_DIR = ROOT / "models" / "v50"
REPORTS_DIR = ROOT / "reports"

PAIR_CSV = REPORTS_DIR / "v50_pair_scores.csv"
GROUP_CSV = REPORTS_DIR / "v50_group_scores.csv"
SUMMARY_JSON = REPORTS_DIR / "v50_pair_group_summary.json"
SUMMARY_MD = REPORTS_DIR / "v50_pair_group_summary.md"
MODEL_JSON = MODEL_DIR / "v50_pair_group_intelligence.json"


def T(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


def _find_data_path() -> Path:
    for path in DATA_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("No draw dataset found.")


def _extract_numbers_from_row(row: pd.Series) -> list[int]:
    column_sets = [
        [f"n{i}" for i in range(1, 7)],
        [f"num{i}" for i in range(1, 7)],
        [f"number_{i}" for i in range(1, 7)],
        [f"main_{i}" for i in range(1, 7)],
        [f"ball_{i}" for i in range(1, 7)],
    ]

    normalized = {str(col).lower(): col for col in row.index}

    for columns in column_sets:
        if all(col in normalized for col in columns):
            values = []
            for col in columns:
                try:
                    values.append(int(row[normalized[col]]))
                except Exception:
                    return []
            cleaned = sorted(set(values))
            if len(cleaned) == 6 and all(1 <= n <= 49 for n in cleaned):
                return cleaned

    text_columns = [
        "numbers",
        "main_numbers",
        "combination",
        "draw_numbers",
        "winning_numbers",
        "nums",
    ]

    for col in text_columns:
        if col in normalized:
            raw = str(row[normalized[col]])
            values = [int(x) for x in re.findall(r"\d+", raw)]
            cleaned = sorted(set(n for n in values if 1 <= n <= 49))
            if len(cleaned) >= 6:
                return cleaned[:6]

    values = []
    for value in row.values:
        try:
            n = int(value)
        except Exception:
            continue
        if 1 <= n <= 49:
            values.append(n)

    cleaned = sorted(set(values))
    if len(cleaned) >= 6:
        return cleaned[:6]

    return []


def _load_draws() -> tuple[Path, list[list[int]]]:
    path = _find_data_path()
    df = pd.read_csv(path)

    draws: list[list[int]] = []
    for _, row in df.iterrows():
        numbers = _extract_numbers_from_row(row)
        if len(numbers) == 6:
            draws.append(numbers)

    if not draws:
        raise ValueError("No valid 6-number draw rows found.")

    return path, draws


def _safe_norm(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return float(value) / float(max_value)


def _build_pair_scores(draws: list[list[int]], recent_window: int = 250) -> pd.DataFrame:
    total = len(draws)
    recent_start = max(0, total - recent_window)

    counts: Counter[tuple[int, int]] = Counter()
    recent_counts: Counter[tuple[int, int]] = Counter()
    last_seen: dict[tuple[int, int], int] = {}

    for idx, draw in enumerate(draws, start=1):
        for pair in itertools.combinations(sorted(draw), 2):
            counts[pair] += 1
            last_seen[pair] = idx
            if idx > recent_start:
                recent_counts[pair] += 1

    all_pairs = list(itertools.combinations(range(1, 50), 2))
    max_count = max(counts.values()) if counts else 1
    max_recent = max(recent_counts.values()) if recent_counts else 1
    max_gap = total

    rows = []
    for pair in all_pairs:
        count = counts.get(pair, 0)
        recent = recent_counts.get(pair, 0)
        seen_at = last_seen.get(pair, 0)
        gap = total - seen_at if seen_at else total

        frequency_score = _safe_norm(count, max_count)
        recency_score = _safe_norm(recent, max_recent)
        overdue_score = _safe_norm(gap, max_gap)

        # Main score prefers pairs that have real history and recent activity.
        score = (0.50 * frequency_score) + (0.35 * recency_score) + (0.15 * (1.0 - overdue_score))

        # Watchlist score is different: historically present but currently overdue.
        watch_score = (0.60 * frequency_score) + (0.40 * overdue_score)

        rows.append(
            {
                "pair": f"{pair[0]}-{pair[1]}",
                "n1": pair[0],
                "n2": pair[1],
                "count": count,
                "recent_count": recent,
                "last_seen_index": seen_at,
                "gap": gap,
                "frequency_score": round(frequency_score, 6),
                "recency_score": round(recency_score, 6),
                "overdue_score": round(overdue_score, 6),
                "pair_score": round(score, 6),
                "watch_score": round(watch_score, 6),
            }
        )

    return pd.DataFrame(rows).sort_values(["pair_score", "count"], ascending=False)


def _build_group_scores(draws: list[list[int]], recent_window: int = 250) -> pd.DataFrame:
    total = len(draws)
    recent_start = max(0, total - recent_window)

    counts: Counter[tuple[int, int, int]] = Counter()
    recent_counts: Counter[tuple[int, int, int]] = Counter()
    last_seen: dict[tuple[int, int, int], int] = {}

    for idx, draw in enumerate(draws, start=1):
        for group in itertools.combinations(sorted(draw), 3):
            counts[group] += 1
            last_seen[group] = idx
            if idx > recent_start:
                recent_counts[group] += 1

    max_count = max(counts.values()) if counts else 1
    max_recent = max(recent_counts.values()) if recent_counts else 1
    max_gap = total

    rows = []
    for group, count in counts.items():
        recent = recent_counts.get(group, 0)
        seen_at = last_seen.get(group, 0)
        gap = total - seen_at if seen_at else total

        frequency_score = _safe_norm(count, max_count)
        recency_score = _safe_norm(recent, max_recent)
        overdue_score = _safe_norm(gap, max_gap)

        score = (0.55 * frequency_score) + (0.30 * recency_score) + (0.15 * (1.0 - overdue_score))

        rows.append(
            {
                "group": f"{group[0]}-{group[1]}-{group[2]}",
                "n1": group[0],
                "n2": group[1],
                "n3": group[2],
                "count": count,
                "recent_count": recent,
                "last_seen_index": seen_at,
                "gap": gap,
                "frequency_score": round(frequency_score, 6),
                "recency_score": round(recency_score, 6),
                "overdue_score": round(overdue_score, 6),
                "group_score": round(score, 6),
            }
        )

    return pd.DataFrame(rows).sort_values(["group_score", "count"], ascending=False)


def _write_outputs(data_path: Path, draws: list[list[int]], pair_df: pd.DataFrame, group_df: pd.DataFrame) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    pair_df.to_csv(PAIR_CSV, index=False, encoding="utf-8")
    group_df.to_csv(GROUP_CSV, index=False, encoding="utf-8")

    top_pairs = pair_df.head(20).to_dict(orient="records")
    watch_pairs = pair_df.sort_values(["watch_score", "gap"], ascending=False).head(20).to_dict(orient="records")
    top_groups = group_df.head(20).to_dict(orient="records")

    summary = {
        "status": "v50_pair_group_intelligence_completed",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "data_path": str(data_path.relative_to(ROOT)),
        "total_draw_events": len(draws),
        "total_pairs": int(len(pair_df)),
        "observed_groups": int(len(group_df)),
        "recent_window": 250,
        "top_pairs": top_pairs[:10],
        "watch_pairs": watch_pairs[:10],
        "top_groups": top_groups[:10],
        "warning": "Statistical analysis only. Lottery draws remain random and there is no winning guarantee.",
    }

    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    model = {
        "version": "v50",
        "type": "pair_group_intelligence",
        "pair_score_file": str(PAIR_CSV.relative_to(ROOT)),
        "group_score_file": str(GROUP_CSV.relative_to(ROOT)),
        "top_pairs": top_pairs,
        "watch_pairs": watch_pairs,
        "top_groups": top_groups,
        "warning": summary["warning"],
    }
    MODEL_JSON.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# V50 Pair & Group Intelligence",
        "",
        f"Data source: `{summary['data_path']}`",
        f"Total valid draw events: **{summary['total_draw_events']}**",
        f"Total possible pairs analyzed: **{summary['total_pairs']}**",
        f"Observed triples/groups analyzed: **{summary['observed_groups']}**",
        "",
        "Important: this is statistical analysis only. It is not a guarantee of winnings.",
        "",
        "## Top pair signals",
    ]

    for item in top_pairs[:10]:
        md.append(f"- {item['pair']} -> score {item['pair_score']}, count {item['count']}, recent {item['recent_count']}")

    md.append("")
    md.append("## Watchlist pair signals")
    for item in watch_pairs[:10]:
        md.append(f"- {item['pair']} -> watch {item['watch_score']}, gap {item['gap']}, count {item['count']}")

    md.append("")
    md.append("## Top group signals")
    for item in top_groups[:10]:
        md.append(f"- {item['group']} -> score {item['group_score']}, count {item['count']}, recent {item['recent_count']}")

    SUMMARY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> None:
    data_path, draws = _load_draws()
    pair_df = _build_pair_scores(draws)
    group_df = _build_group_scores(draws)
    _write_outputs(data_path, draws, pair_df, group_df)

    print("V50_STATUS v50_pair_group_intelligence_completed")
    print("DATA_SOURCE", str(data_path.relative_to(ROOT)))
    print("DRAW_EVENTS", len(draws))
    print("PAIR_ROWS", len(pair_df))
    print("GROUP_ROWS", len(group_df))
    print("OUTPUT", str(MODEL_JSON.relative_to(ROOT)))


if __name__ == "__main__":
    main()

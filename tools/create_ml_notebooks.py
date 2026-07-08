from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"


def md(text: str) -> dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().splitlines()],
    }


def code(text: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in text.strip().splitlines()],
    }


def notebook(cells: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_notebook(filename: str, cells: list[dict[str, Any]]) -> None:
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    path = NOTEBOOKS_DIR / filename
    path.write_text(json.dumps(notebook(cells), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created: {path.relative_to(PROJECT_ROOT)}")


COMMON_SETUP = r'''
from pathlib import Path
from itertools import combinations
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

pd.set_option("display.max_columns", 80)
pd.set_option("display.width", 160)

PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / "data").exists():
    PROJECT_ROOT = PROJECT_ROOT.parent

DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
MODELS_DIR = PROJECT_ROOT / "models"


def read_csv_safe(path, **kwargs):
    path = Path(path)
    if not path.exists():
        print(f"Missing file: {path}")
        return pd.DataFrame()
    return pd.read_csv(path, **kwargs)


def number_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in ["n1", "n2", "n3", "n4", "n5", "n6"] if col in df.columns]


def parse_numbers_text(value) -> list[int]:
    if pd.isna(value):
        return []
    parts = str(value).replace(";", ",").replace("|", ",").split(",")
    nums = []
    for part in parts:
        part = part.strip()
        if part.isdigit():
            nums.append(int(part))
    return nums


def extract_ticket_numbers(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if len(number_columns(df)) == 6:
        return df.copy()
    text_col = next((c for c in df.columns if "numbers" in c.lower() or "числа" in c.lower()), None)
    if text_col is None:
        return df.copy()
    out = df.copy()
    parsed = out[text_col].apply(parse_numbers_text)
    for i in range(6):
        out[f"n{i+1}"] = parsed.apply(lambda nums: nums[i] if len(nums) > i else np.nan)
    return out


def show_latest_draw(df: pd.DataFrame) -> None:
    if df.empty:
        print("No draw data loaded.")
        return
    latest = df.tail(1).iloc[0]
    nums = [int(latest[col]) for col in number_columns(df)]
    print("Rows:", len(df))
    print("Latest date:", latest.get("date", "n/a"))
    print("Draw number:", latest.get("draw_number", latest.get("draw_no", "n/a")))
    print("Numbers:", nums)


def file_status(paths):
    rows = []
    for path in paths:
        path = Path(path)
        rows.append({
            "file": str(path.relative_to(PROJECT_ROOT)) if str(path).startswith(str(PROJECT_ROOT)) else str(path),
            "exists": path.exists(),
            "size_kb": round(path.stat().st_size / 1024, 2) if path.exists() else 0,
        })
    return pd.DataFrame(rows)


draws = read_csv_safe(DATA_DIR / "historical_draws.csv")
normalized = read_csv_safe(DATA_DIR / "v40_normalized_draw_events.csv")
canonical = read_csv_safe(DATA_DIR / "v41_canonical_draw_events.csv")
show_latest_draw(draws)
'''


def create_readme() -> None:
    text = """# Lottery Probability Model — ML Notebooks

Тази папка съдържа обяснителни и аналитични notebooks за ML/статистическите модели в проекта.

## Стартиране

```powershell
cd "C:\\Users\\stana\\Desktop\\lottery-probability-model"
python -m pip install -r requirements-notebooks.txt
jupyter notebook
```

Във VS Code можеш директно да отвориш `.ipynb` файловете.

## Препоръчителен ред

1. `00_project_overview.ipynb`
2. `01_data_overview_and_quality.ipynb`
3. `02_frequency_model.ipynb`
4. `03_gap_model.ipynb`
5. `04_pattern_balance_model.ipynb`
6. `05_combined_strategy.ipynb`
7. `06_ml_extensions.ipynb`
8. `07_model_comparison.ipynb`
9. `08_ensemble_and_weighting.ipynb`
10. `09_ticket_builder_and_portfolio.ipynb`
11. `10_backtest_and_performance.ipynb`
12. `11_explainability_and_conclusions.ipynb`

## Важно

Тези notebooks са за анализ, визуализация и обяснение. Те не гарантират печалба. Лотарийните тегления остават случайни събития.
"""
    (NOTEBOOKS_DIR / "README.md").write_text(text, encoding="utf-8")
    print(f"Created: {(NOTEBOOKS_DIR / 'README.md').relative_to(PROJECT_ROOT)}")


def main() -> None:
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

    write_notebook("00_project_overview.ipynb", [
        md("""
# 00 — Project Overview

Този notebook дава ясен преглед на Lottery Probability Model: данни, модели, отчети, Streamlit UI и крайния процес за изграждане на фишове.

Проектът не е система за гарантирана печалба. Той е аналитична система, която комбинира статистически сигнали, backtest резултати, model weighting и portfolio construction.
"""),
        code(COMMON_SETUP),
        md("""
## Основни файлове

- `data/historical_draws.csv` — основен исторически dataset.
- `data/v40_normalized_draw_events.csv` — нормализирани draw events.
- `data/v41_canonical_draw_events.csv` — canonical draw events за model layer.
- `reports/*.csv` — резултати от модели, backtests, ticket builders, audits и dashboard snapshots.
- `streamlit_app.py` + `app.py` — потребителският UI.
"""),
        code("""
files = [
    DATA_DIR / "historical_draws.csv",
    DATA_DIR / "v40_normalized_draw_events.csv",
    DATA_DIR / "v41_canonical_draw_events.csv",
    REPORTS_DIR / "v117_real_ticket_pack_builder_cards.csv",
    REPORTS_DIR / "v118_model_system_ticket_pack.csv",
    REPORTS_DIR / "v118_full_system_price_table.csv",
    PROJECT_ROOT / "streamlit_app.py",
    PROJECT_ROOT / "app.py",
]
file_status(files)
"""),
        md("""
## Общ pipeline

1. Исторически данни.
2. Нормализация и canonical event layer.
3. Статистически модели — frequency, gap, balance, pair/group logic.
4. ML extensions — classification, clustering, dimensionality reduction, meta learner.
5. Backtest и сравнение.
6. Ensemble / weighting.
7. Ticket builder и portfolio construction.
8. Streamlit UI за реална употреба.
"""),
        code("""
report_files = sorted(REPORTS_DIR.glob("*.csv"))
model_dirs = sorted([p for p in MODELS_DIR.glob("v*") if p.is_dir()])
pd.DataFrame({
    "metric": ["CSV report files", "Model/version folders", "Draw rows"],
    "value": [len(report_files), len(model_dirs), len(draws)],
})
"""),
    ])

    write_notebook("01_data_overview_and_quality.ipynb", [
        md("""
# 01 — Data Overview and Quality

Този notebook проверява качеството на основните данни: брой редове, последен тираж, липсващи стойности, валидност на числата и базови разпределения.
"""),
        code(COMMON_SETUP),
        md("## Последни тиражи"),
        code("draws.tail(10)"),
        md("## Синхрон между основните dataset файлове"),
        code("""
summary = []
for name, df in [("historical_draws", draws), ("v40_normalized", normalized), ("v41_canonical", canonical)]:
    if df.empty:
        summary.append({"dataset": name, "rows": 0, "latest_date": None, "latest_draw": None, "latest_numbers": None})
        continue
    latest = df.tail(1).iloc[0]
    nums = [int(latest[c]) for c in number_columns(df)]
    summary.append({
        "dataset": name,
        "rows": len(df),
        "latest_date": latest.get("date"),
        "latest_draw": latest.get("draw_number", latest.get("draw_no")),
        "latest_numbers": nums,
    })
pd.DataFrame(summary)
"""),
        md("## Липсващи стойности"),
        code("draws.isna().sum().sort_values(ascending=False).to_frame('missing_values')"),
        md("## Валидност на числата 1–49"),
        code("""
num_cols = number_columns(draws)
rows = []
for col in num_cols:
    rows.append({
        "column": col,
        "min": int(draws[col].min()),
        "max": int(draws[col].max()),
        "invalid_below_1": int((draws[col] < 1).sum()),
        "invalid_above_49": int((draws[col] > 49).sum()),
    })
pd.DataFrame(rows)
"""),
        md("## Дублирани числа в един тираж"),
        code("""
def has_duplicate_numbers(row):
    nums = [int(row[col]) for col in num_cols]
    return len(nums) != len(set(nums))

duplicate_rows = draws[draws.apply(has_duplicate_numbers, axis=1)]
print("Rows with duplicate numbers:", len(duplicate_rows))
duplicate_rows.head()
"""),
        md("## Честотно разпределение"),
        code("""
all_numbers = draws[num_cols].to_numpy().ravel()
freq = pd.Series(all_numbers).value_counts().sort_index()
freq_df = freq.rename_axis("number").reset_index(name="count")
display(freq_df.head())
ax = freq.plot(kind="bar", figsize=(14, 5), title="Frequency of numbers 1–49")
ax.set_xlabel("Number")
ax.set_ylabel("Count")
plt.show()
"""),
        md("## Разпределение на сумите"),
        code("""
draw_sums = draws[num_cols].sum(axis=1)
ax = draw_sums.plot(kind="hist", bins=30, figsize=(10, 5), title="Distribution of draw sums")
ax.set_xlabel("Sum of six numbers")
plt.show()
draw_sums.describe().to_frame("sum_stats")
"""),
    ])

    write_notebook("02_frequency_model.ipynb", [
        md("""
# 02 — Frequency Model

Frequency model гледа колко често се появява всяко число в историческите данни. Това е статистически сигнал, не гаранция.
"""),
        code(COMMON_SETUP),
        md("## Frequency table"),
        code("""
num_cols = number_columns(draws)
all_numbers = draws[num_cols].to_numpy().ravel()
frequency = (
    pd.Series(all_numbers)
    .value_counts()
    .reindex(range(1, 50), fill_value=0)
    .sort_index()
    .rename_axis("number")
    .reset_index(name="frequency")
)
frequency["frequency_share"] = frequency["frequency"] / frequency["frequency"].sum()
frequency["rank_desc"] = frequency["frequency"].rank(ascending=False, method="dense").astype(int)
frequency.sort_values("frequency", ascending=False).head(15)
"""),
        md("## Top и cold numbers"),
        code("""
top_numbers = frequency.sort_values("frequency", ascending=False).head(10)
cold_numbers = frequency.sort_values("frequency", ascending=True).head(10)
display(top_numbers)
display(cold_numbers)
ax = top_numbers.set_index("number")["frequency"].plot(kind="bar", figsize=(10, 4), title="Top 10 most frequent numbers")
ax.set_xlabel("Number")
ax.set_ylabel("Frequency")
plt.show()
ax = cold_numbers.set_index("number")["frequency"].plot(kind="bar", figsize=(10, 4), title="Top 10 coldest numbers")
ax.set_xlabel("Number")
ax.set_ylabel("Frequency")
plt.show()
"""),
        md("## Rolling frequency за топ числа"),
        code("""
selected_numbers = top_numbers["number"].head(5).tolist()
window = 200
binary = pd.DataFrame(index=draws.index)
for number in selected_numbers:
    binary[number] = draws[num_cols].eq(number).any(axis=1).astype(int)
rolling = binary.rolling(window=window, min_periods=20).mean()
ax = rolling.plot(figsize=(12, 5), title=f"Rolling appearance rate, window={window}")
ax.set_xlabel("Draw index")
ax.set_ylabel("Rolling rate")
plt.show()
"""),
    ])

    write_notebook("03_gap_model.ipynb", [
        md("""
# 03 — Gap Model

Gap model гледа разстоянието между появяванията на всяко число: current gap, average gap и overdue/underdue сигнали.
"""),
        code(COMMON_SETUP),
        md("## Gap statistics"),
        code("""
num_cols = number_columns(draws)
records = []
for number in range(1, 50):
    hit_indices = draws.index[draws[num_cols].eq(number).any(axis=1)].tolist()
    if not hit_indices:
        records.append({"number": number, "appearances": 0, "current_gap": np.nan, "avg_gap": np.nan, "max_gap": np.nan})
        continue
    gaps = np.diff(hit_indices)
    current_gap = len(draws) - 1 - hit_indices[-1]
    records.append({
        "number": number,
        "appearances": len(hit_indices),
        "current_gap": current_gap,
        "avg_gap": float(np.mean(gaps)) if len(gaps) else np.nan,
        "max_gap": int(np.max(gaps)) if len(gaps) else np.nan,
    })
gap_df = pd.DataFrame(records)
gap_df["gap_ratio"] = gap_df["current_gap"] / gap_df["avg_gap"]
gap_df.sort_values("gap_ratio", ascending=False).head(15)
"""),
        md("## Най-голям current gap"),
        code("""
overdue = gap_df.sort_values("current_gap", ascending=False).head(12)
display(overdue)
ax = overdue.set_index("number")["current_gap"].plot(kind="bar", figsize=(10, 4), title="Numbers with largest current gap")
ax.set_xlabel("Number")
ax.set_ylabel("Current gap")
plt.show()
"""),
        md("## Current gap спрямо average gap"),
        code("""
plot_df = gap_df.dropna(subset=["avg_gap", "current_gap"]).set_index("number")[["current_gap", "avg_gap"]]
ax = plot_df.plot(kind="bar", figsize=(15, 5), title="Current gap vs average gap")
ax.set_xlabel("Number")
ax.set_ylabel("Gap")
plt.show()
"""),
    ])

    write_notebook("04_pattern_balance_model.ipynb", [
        md("""
# 04 — Pattern Balance Model

Този notebook разглежда структурния баланс на тиражите: odd/even, low/high, sum, spread и consecutive pairs.
"""),
        code(COMMON_SETUP),
        md("## Pattern features"),
        code("""
num_cols = number_columns(draws)
patterns = draws.copy()
patterns["sum"] = patterns[num_cols].sum(axis=1)
patterns["odd_count"] = patterns[num_cols].apply(lambda row: sum(int(x) % 2 == 1 for x in row), axis=1)
patterns["even_count"] = 6 - patterns["odd_count"]
patterns["low_count"] = patterns[num_cols].apply(lambda row: sum(int(x) <= 24 for x in row), axis=1)
patterns["high_count"] = 6 - patterns["low_count"]
patterns["spread"] = patterns[num_cols].max(axis=1) - patterns[num_cols].min(axis=1)

def consecutive_pairs(row):
    nums = sorted(int(x) for x in row)
    return sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1)
patterns["consecutive_pairs"] = patterns[num_cols].apply(consecutive_pairs, axis=1)
patterns[["date", "draw_number", "sum", "odd_count", "even_count", "low_count", "high_count", "spread", "consecutive_pairs"]].tail(10)
"""),
        md("## Distributions"),
        code("""
odd_counts = patterns["odd_count"].value_counts().sort_index()
ax = odd_counts.plot(kind="bar", figsize=(8, 4), title="Odd count distribution")
ax.set_xlabel("Odd numbers in draw")
ax.set_ylabel("Draw count")
plt.show()
low_counts = patterns["low_count"].value_counts().sort_index()
ax = low_counts.plot(kind="bar", figsize=(8, 4), title="Low count distribution, low <= 24")
ax.set_xlabel("Low numbers in draw")
ax.set_ylabel("Draw count")
plt.show()
ax = patterns["sum"].plot(kind="hist", bins=30, figsize=(10, 4), title="Draw sum distribution")
ax.set_xlabel("Sum")
plt.show()
patterns[["sum", "spread", "odd_count", "low_count", "consecutive_pairs"]].describe()
"""),
    ])

    write_notebook("05_combined_strategy.ipynb", [
        md("""
# 05 — Combined Strategy

Тук комбинираме няколко прости сигнала: frequency score, gap score и recent activity score. Целта е прозрачен score layer.
"""),
        code(COMMON_SETUP),
        md("## Build combined number score"),
        code("""
num_cols = number_columns(draws)
all_numbers = draws[num_cols].to_numpy().ravel()
frequency = pd.Series(all_numbers).value_counts().reindex(range(1, 50), fill_value=0)
frequency_score = (frequency - frequency.min()) / (frequency.max() - frequency.min())
gap_records = []
for number in range(1, 50):
    hit_indices = draws.index[draws[num_cols].eq(number).any(axis=1)].tolist()
    current_gap = len(draws) - 1 - hit_indices[-1] if hit_indices else len(draws)
    gap_records.append((number, current_gap))
gap = pd.Series(dict(gap_records))
gap_score = (gap - gap.min()) / (gap.max() - gap.min())
recent_window = min(100, len(draws))
recent_numbers = draws.tail(recent_window)[num_cols].to_numpy().ravel()
recent_frequency = pd.Series(recent_numbers).value_counts().reindex(range(1, 50), fill_value=0)
recent_score = (recent_frequency - recent_frequency.min()) / (recent_frequency.max() - recent_frequency.min())
combined = pd.DataFrame({
    "number": range(1, 50),
    "frequency_score": frequency_score.values,
    "gap_score": gap_score.values,
    "recent_score": recent_score.values,
})
combined["combined_score"] = 0.45 * combined["frequency_score"] + 0.35 * combined["gap_score"] + 0.20 * combined["recent_score"]
combined.sort_values("combined_score", ascending=False).head(15)
"""),
        code("""
top = combined.sort_values("combined_score", ascending=False).head(15)
ax = top.set_index("number")[["frequency_score", "gap_score", "recent_score", "combined_score"]].plot(kind="bar", figsize=(13, 5), title="Top combined strategy scores")
ax.set_xlabel("Number")
ax.set_ylabel("Score")
plt.show()
"""),
        md("""
## Извод

Combined strategy е полезна, защото прави единна таблица от няколко сигнала. Но теглата са аналитичен избор и трябва да се сравняват с backtest.
"""),
    ])

    write_notebook("06_ml_extensions.ipynb", [
        md("""
# 06 — ML Extensions

Този notebook показва ML extensions: feature matrix, PCA visualization и clustering върху draw pattern features. При лотарийни данни ML моделите трябва да се интерпретират внимателно.
"""),
        code(COMMON_SETUP),
        md("## Feature matrix"),
        code("""
num_cols = number_columns(draws)
features = pd.DataFrame({
    "sum": draws[num_cols].sum(axis=1),
    "mean": draws[num_cols].mean(axis=1),
    "std": draws[num_cols].std(axis=1),
    "min": draws[num_cols].min(axis=1),
    "max": draws[num_cols].max(axis=1),
    "spread": draws[num_cols].max(axis=1) - draws[num_cols].min(axis=1),
    "odd_count": draws[num_cols].apply(lambda row: sum(int(x) % 2 == 1 for x in row), axis=1),
    "low_count": draws[num_cols].apply(lambda row: sum(int(x) <= 24 for x in row), axis=1),
})
features.tail()
"""),
        md("## PCA visualization"),
        code("""
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    scaled = StandardScaler().fit_transform(features)
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(scaled)
    pca_df = pd.DataFrame(coords, columns=["pc1", "pc2"])
    ax = pca_df.plot(kind="scatter", x="pc1", y="pc2", figsize=(8, 6), title="PCA view of draw pattern features")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    plt.show()
    print("Explained variance ratio:", pca.explained_variance_ratio_)
except Exception as exc:
    print("PCA section skipped:", exc)
"""),
        md("## Clustering example"),
        code("""
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    scaled = StandardScaler().fit_transform(features)
    model = KMeans(n_clusters=4, random_state=42, n_init="auto")
    clusters = model.fit_predict(scaled)
    cluster_summary = features.copy()
    cluster_summary["cluster"] = clusters
    display(cluster_summary.groupby("cluster").mean().round(2))
    ax = cluster_summary["cluster"].value_counts().sort_index().plot(kind="bar", figsize=(8, 4), title="Cluster distribution")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Draw count")
    plt.show()
except Exception as exc:
    print("Clustering section skipped:", exc)
"""),
    ])

    write_notebook("07_model_comparison.ipynb", [
        md("""
# 07 — Model Comparison

Този notebook търси налични comparison/backtest/performance CSV файлове и показва как да се сравняват моделите.
"""),
        code(COMMON_SETUP),
        md("## Available comparison/backtest files"),
        code("""
candidate_files = sorted(set(
    list(REPORTS_DIR.glob("*comparison*.csv"))
    + list(REPORTS_DIR.glob("*backtest*.csv"))
    + list(REPORTS_DIR.glob("*performance*.csv"))
    + list(REPORTS_DIR.glob("*reliability*.csv"))
))
pd.DataFrame({
    "file": [str(path.relative_to(PROJECT_ROOT)) for path in candidate_files],
    "size_kb": [round(path.stat().st_size / 1024, 2) for path in candidate_files],
}).head(80)
"""),
        md("## Preview selected files"),
        code("""
for path in candidate_files[:10]:
    print("\n===", path.name, "===")
    df = read_csv_safe(path)
    print("shape:", df.shape)
    display(df.head())
"""),
        md("## Reliability scores"),
        code("""
reliability = read_csv_safe(REPORTS_DIR / "v63_model_reliability_scores.csv")
if not reliability.empty:
    display(reliability.head(20))
    numeric_cols = reliability.select_dtypes(include="number").columns.tolist()
    label_col = next((c for c in reliability.columns if "model" in c.lower() or "label" in c.lower()), reliability.columns[0])
    score_col = next((c for c in numeric_cols if "score" in c.lower()), numeric_cols[-1] if numeric_cols else None)
    if score_col:
        ax = reliability.head(20).set_index(label_col)[score_col].plot(kind="bar", figsize=(12, 5), title=f"Model reliability by {score_col}")
        ax.set_xlabel("Model")
        ax.set_ylabel(score_col)
        plt.show()
else:
    print("No v63_model_reliability_scores.csv found.")
"""),
    ])

    write_notebook("08_ensemble_and_weighting.ipynb", [
        md("""
# 08 — Ensemble and Weighting

Тук гледаме model weights, reliability scores и weighted ensemble outputs.
"""),
        code(COMMON_SETUP),
        md("## Model weights"),
        code("""
weights = read_csv_safe(REPORTS_DIR / "v65_model_weights.csv")
weights
"""),
        code("""
if not weights.empty:
    numeric_cols = weights.select_dtypes(include="number").columns.tolist()
    label_col = next((c for c in weights.columns if "model" in c.lower() or "label" in c.lower()), weights.columns[0])
    preferred = [c for c in ["adaptive_weight_percent", "reliability_score", "adjusted_score"] if c in weights.columns]
    for metric in preferred or numeric_cols[:3]:
        ax = weights.set_index(label_col)[metric].plot(kind="bar", figsize=(11, 4), title=f"Model weighting: {metric}")
        ax.set_xlabel("Model")
        ax.set_ylabel(metric)
        plt.show()
else:
    print("No model weights file found.")
"""),
        md("## Weighted ensemble scores"),
        code("""
ensemble = read_csv_safe(REPORTS_DIR / "v66_weighted_smart_ensemble_scores.csv")
display(ensemble.head(20))
if not ensemble.empty and "weighted_score" in ensemble.columns:
    top = ensemble.sort_values("weighted_score", ascending=False).head(15)
    ax = top.set_index("number")["weighted_score"].plot(kind="bar", figsize=(10, 4), title="Top weighted ensemble numbers")
    ax.set_xlabel("Number")
    ax.set_ylabel("weighted_score")
    plt.show()
"""),
    ])

    write_notebook("09_ticket_builder_and_portfolio.ipynb", [
        md("""
# 09 — Ticket Builder and Portfolio

Този notebook разглежда как се изграждат фишове и портфолио от комбинации: 3 фиша × 4 реда = 12 комбинации, цена, coverage и pair overlap.
"""),
        code(COMMON_SETUP),
        md("## v117 real ticket pack"),
        code("""
v117_cards = read_csv_safe(REPORTS_DIR / "v117_real_ticket_pack_builder_cards.csv")
v117_cards
"""),
        md("## v118 model system ticket pack"),
        code("""
v118_pack = read_csv_safe(REPORTS_DIR / "v118_model_system_ticket_pack.csv")
v118_pack
"""),
        md("## Price table"),
        code("""
price_table = read_csv_safe(REPORTS_DIR / "v118_full_system_price_table.csv")
price_table
"""),
        md("## Ticket pack structure and coverage"),
        code("""
ticket_df = extract_ticket_numbers(v118_pack)
ncols = number_columns(ticket_df)
summary = pd.DataFrame({
    "metric": ["physical_tickets", "lines_total", "lines_per_ticket", "total_price_eur"],
    "value": [
        ticket_df["ticket_no"].nunique() if "ticket_no" in ticket_df.columns else None,
        len(ticket_df),
        ticket_df.groupby("ticket_no").size().to_dict() if "ticket_no" in ticket_df.columns else None,
        ticket_df["price_eur"].sum() if "price_eur" in ticket_df.columns else None,
    ],
})
display(summary)
display(ticket_df.head(12))
if len(ncols) == 6:
    all_ticket_numbers = ticket_df[ncols].to_numpy().ravel()
    coverage = pd.Series(all_ticket_numbers).value_counts().sort_index().rename_axis("number").reset_index(name="count")
    display(coverage)
    ax = coverage.set_index("number")["count"].plot(kind="bar", figsize=(12, 4), title="Ticket pack number coverage")
    ax.set_xlabel("Number")
    ax.set_ylabel("Count in ticket pack")
    plt.show()
"""),
        md("## Pair overlap analysis"),
        code("""
if len(ncols) == 6:
    pair_counter = Counter()
    for _, row in ticket_df.iterrows():
        nums = sorted(int(row[col]) for col in ncols)
        for pair in combinations(nums, 2):
            pair_counter[pair] += 1
    pair_df = pd.DataFrame([{"pair": f"{a}-{b}", "count": count} for (a, b), count in pair_counter.items()]).sort_values("count", ascending=False)
    display(pair_df.head(20))
    ax = pair_df.head(20).set_index("pair")["count"].plot(kind="bar", figsize=(12, 4), title="Top repeated pairs in ticket pack")
    ax.set_xlabel("Pair")
    ax.set_ylabel("Count")
    plt.show()
else:
    print("Pair analysis skipped.")
"""),
    ])

    write_notebook("10_backtest_and_performance.ipynb", [
        md("""
# 10 — Backtest and Performance

Този notebook събира наличните backtest/performance reports и ги показва като таблици и графики.
"""),
        code(COMMON_SETUP),
        md("## Backtest files inventory"),
        code("""
backtest_files = sorted(set(
    list(REPORTS_DIR.glob("*backtest*.csv"))
    + list(REPORTS_DIR.glob("*performance*.csv"))
    + list(REPORTS_DIR.glob("*result*.csv"))
))
pd.DataFrame({
    "file": [str(path.relative_to(PROJECT_ROOT)) for path in backtest_files],
    "size_kb": [round(path.stat().st_size / 1024, 2) for path in backtest_files],
}).head(100)
"""),
        md("## Latest ticket pack result"),
        code("""
latest_result = read_csv_safe(REPORTS_DIR / "v73_latest_ticket_pack_result.csv")
latest_result
"""),
        md("## Ticket pack performance history"),
        code("""
history = read_csv_safe(REPORTS_DIR / "v73_ticket_pack_performance_history.csv")
display(history.head())
if not history.empty and "best_hit_count" in history.columns:
    ax = history["best_hit_count"].plot(figsize=(12, 4), title="Performance history: best_hit_count")
    ax.set_xlabel("Row")
    ax.set_ylabel("best_hit_count")
    plt.show()
"""),
        md("## Strategy backtest"),
        code("""
strategy = read_csv_safe(REPORTS_DIR / "v92_strategy_backtest_results.csv")
display(strategy.head(20))
if not strategy.empty and "average_best_hits" in strategy.columns:
    label_col = "strategy_label" if "strategy_label" in strategy.columns else strategy.columns[0]
    ax = strategy.set_index(label_col)["average_best_hits"].plot(kind="bar", figsize=(14, 5), title="Strategy backtest: average_best_hits")
    ax.set_xlabel("Strategy")
    ax.set_ylabel("average_best_hits")
    plt.show()
"""),
    ])

    write_notebook("11_explainability_and_conclusions.ipynb", [
        md("""
# 11 — Explainability and Conclusions

Този notebook събира обяснимостта на проекта: защо дадени числа/фишове са избрани, какви предупреждения има и какво реално може да се заключи.
"""),
        code(COMMON_SETUP),
        md("## Number explanations"),
        code("""
explanations = read_csv_safe(REPORTS_DIR / "v76_number_explanations.csv")
explanations.head(30)
"""),
        md("## Ticket validation"),
        code("""
validation = read_csv_safe(REPORTS_DIR / "v76_ticket_validation.csv")
validation.head(30)
"""),
        md("## Warnings"),
        code("""
warning_files = sorted(set(list(REPORTS_DIR.glob("*warning*.csv")) + list(REPORTS_DIR.glob("*warnings*.csv"))))
for path in warning_files:
    print("\n===", path.name, "===")
    df = read_csv_safe(path)
    print("shape:", df.shape)
    display(df.head(20))
"""),
        md("""
## Финален извод

Този проект трябва да се разглежда като аналитична система, не като гаранция за печалба.

Силни страни:

- централизирани данни;
- ясни проверки;
- няколко независими модела;
- ensemble/weighting слой;
- backtest и performance history;
- portfolio подход за фишове;
- Streamlit UI за по-лесна реална употреба.

Ограничения:

- лотарийните тегления са случайни;
- историческите patterns не гарантират бъдещи резултати;
- ML моделите могат да създадат илюзия за предсказуемост;
- най-важното е контрол, яснота и дисциплина при интерпретацията.
"""),
    ])

    create_readme()
    print("\nDone. Open the notebooks folder in VS Code or run:")
    print("python -m pip install -r requirements-notebooks.txt")
    print("jupyter notebook")


if __name__ == "__main__":
    main()

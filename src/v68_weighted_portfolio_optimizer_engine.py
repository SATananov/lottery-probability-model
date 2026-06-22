from __future__ import annotations

from pathlib import Path
import csv
import itertools
import json
from collections import Counter
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v68"

SOURCE_TICKETS_PATH = REPORTS_DIR / "v67_weighted_ticket_builder_tickets.csv"
SOURCE_SCORES_PATH = REPORTS_DIR / "v66_weighted_smart_ensemble_scores.csv"

NUMBER_MIN = 1
NUMBER_MAX = 49
TICKET_SIZE = 6


def as_float(value, default=0.0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return float(text.replace("%", "").replace(",", "."))
    except (TypeError, ValueError):
        return default


def as_int(value, default=None):
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(float(text.replace(",", ".")))
    except (TypeError, ValueError):
        return default


def read_csv_rows(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_ticket_numbers(row):
    values = []

    for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        value = as_int(row.get(key))
        if value is not None:
            values.append(value)

    if len(values) < TICKET_SIZE:
        text = str(row.get("numbers", ""))
        for part in text.replace(";", ",").replace(" ", ",").split(","):
            value = as_int(part)
            if value is not None:
                values.append(value)

    clean = sorted({value for value in values if NUMBER_MIN <= value <= NUMBER_MAX})

    if len(clean) != TICKET_SIZE:
        return None

    return tuple(clean)


def load_tickets():
    rows = read_csv_rows(SOURCE_TICKETS_PATH)
    if not rows:
        raise FileNotFoundError(
            "Missing reports/v67_weighted_ticket_builder_tickets.csv. "
            "Run Step 67 first: python scripts/v67_build_weighted_ticket_builder.py"
        )

    tickets = []
    seen = set()

    for index, row in enumerate(rows, start=1):
        numbers = parse_ticket_numbers(row)
        if not numbers:
            continue

        if numbers in seen:
            continue

        seen.add(numbers)
        tickets.append({
            "ticket_id": as_int(row.get("ticket_id"), index),
            "strategy": row.get("strategy", ""),
            "strategy_label": row.get("strategy_label", ""),
            "numbers": numbers,
            "average_weighted_score": as_float(row.get("average_weighted_score"), 0.0),
            "balance_status": row.get("balance_status", ""),
            "risk_note": row.get("risk_note", ""),
        })

    if len(tickets) < 2:
        raise RuntimeError("Step 68 needs at least 2 valid Step 67 tickets.")

    return tickets


def load_weighted_scores():
    rows = read_csv_rows(SOURCE_SCORES_PATH)
    if not rows:
        raise FileNotFoundError(
            "Missing reports/v66_weighted_smart_ensemble_scores.csv. "
            "Run Step 66 first: python scripts/v66_build_weighted_smart_ensemble.py"
        )

    scores = {}

    for row in rows:
        number = as_int(row.get("number"))
        if number is None or not (NUMBER_MIN <= number <= NUMBER_MAX):
            continue

        scores[number] = {
            "number": number,
            "rank": as_int(row.get("rank"), 999),
            "weighted_score_percent": as_float(row.get("weighted_score_percent"), 0.0),
            "source_count": as_int(row.get("source_count"), 0),
            "status": row.get("status", ""),
            "top_sources": row.get("top_sources", ""),
        }

    if len(scores) != 49:
        raise RuntimeError(f"Expected 49 Step 66 scores, got {len(scores)}.")

    return scores


def overlap_between(left, right):
    return len(set(left).intersection(set(right)))


def ticket_pair_counter(tickets):
    counter = Counter()
    for ticket in tickets:
        for pair in itertools.combinations(ticket["numbers"], 2):
            counter[pair] += 1
    return counter


def ticket_triple_counter(tickets):
    counter = Counter()
    for ticket in tickets:
        for triple in itertools.combinations(ticket["numbers"], 3):
            counter[triple] += 1
    return counter


def number_group(number):
    if number <= 9:
        return "01-09"
    if number <= 19:
        return "10-19"
    if number <= 29:
        return "20-29"
    if number <= 39:
        return "30-39"
    return "40-49"


def coverage_status(number, covered_count, score_row):
    rank = score_row["rank"]

    if covered_count == 0 and rank <= 10:
        return "непокрит top 10 сигнал"
    if covered_count == 0 and rank <= 20:
        return "непокрит top 20 сигнал"
    if covered_count == 0:
        return "непокрит резервен сигнал"
    if covered_count >= 4 and rank <= 20:
        return "силен сигнал с висока експозиция"
    if covered_count >= 4:
        return "висока експозиция"
    if covered_count >= 2 and rank <= 20:
        return "добре покрит силен сигнал"
    if covered_count >= 1 and rank <= 20:
        return "покрит силен сигнал"
    return "покрит резервен сигнал"


def recommendation_level(portfolio_score):
    if portfolio_score >= 80:
        return "много добър статистически портфейл"
    if portfolio_score >= 68:
        return "добър статистически портфейл"
    if portfolio_score >= 55:
        return "приемлив портфейл с нужда от наблюдение"
    return "портфейл с нужда от подобрение"


def build_recommendations(summary_core, undercovered_top, repeated_pairs, repeated_triples):
    recommendations = []

    if summary_core["unique_numbers_covered"] < 20:
        recommendations.append(
            "Портфолиото покрива сравнително малко уникални числа. Следваща оптимизация може да увеличи diversity."
        )

    if summary_core["max_ticket_overlap"] >= 5:
        recommendations.append(
            "Има много високо припокриване между поне два фиша. Добре е да се намали overlap."
        )
    elif summary_core["max_ticket_overlap"] == 4:
        recommendations.append(
            "Има умерено високо припокриване между фишове. При Step 69 може да се добави по-строг overlap control."
        )

    if undercovered_top:
        recommendations.append(
            "Има силни Step 66 числа, които не са покрити в портфолиото: "
            + ", ".join(str(item["number"]) for item in undercovered_top[:8])
            + "."
        )

    if repeated_pairs:
        recommendations.append(
            "Има повторени двойки. Това не е грешка, но portfolio optimizer може да намали повторенията."
        )

    if repeated_triples:
        recommendations.append(
            "Има повторени тройки. Това повишава концентрацията и може да се оптимизира."
        )

    if not recommendations:
        recommendations.append(
            "Портфолиото има добър баланс между покритие, overlap и weighted score. Няма критични структурни предупреждения."
        )

    return recommendations


def build_weighted_portfolio_optimizer():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    tickets = load_tickets()
    scores = load_weighted_scores()

    occurrence = Counter()
    group_occurrence = Counter()

    for ticket in tickets:
        for number in ticket["numbers"]:
            occurrence[number] += 1
            group_occurrence[number_group(number)] += 1

    pair_counter = ticket_pair_counter(tickets)
    triple_counter = ticket_triple_counter(tickets)

    repeated_pairs = [
        {
            "pair": f"{pair[0]},{pair[1]}",
            "n1": pair[0],
            "n2": pair[1],
            "count": count,
        }
        for pair, count in pair_counter.items()
        if count > 1
    ]

    repeated_pairs.sort(key=lambda item: (-item["count"], item["n1"], item["n2"]))

    repeated_triples = [
        {
            "triple": f"{triple[0]},{triple[1]},{triple[2]}",
            "n1": triple[0],
            "n2": triple[1],
            "n3": triple[2],
            "count": count,
        }
        for triple, count in triple_counter.items()
        if count > 1
    ]

    repeated_triples.sort(key=lambda item: (-item["count"], item["n1"], item["n2"], item["n3"]))

    pair_overlaps = []
    max_overlap_value = 0
    overlap_values = []

    for left, right in itertools.combinations(tickets, 2):
        overlap = overlap_between(left["numbers"], right["numbers"])
        max_overlap_value = max(max_overlap_value, overlap)
        overlap_values.append(overlap)
        pair_overlaps.append({
            "ticket_a": left["ticket_id"],
            "ticket_b": right["ticket_id"],
            "overlap": overlap,
            "shared_numbers": ",".join(str(n) for n in sorted(set(left["numbers"]).intersection(set(right["numbers"])))),
        })

    average_overlap = sum(overlap_values) / len(overlap_values) if overlap_values else 0.0

    coverage_rows = []

    for number in range(NUMBER_MIN, NUMBER_MAX + 1):
        score_row = scores[number]
        covered_count = occurrence[number]
        exposure = covered_count / len(tickets)

        coverage_rows.append({
            "number": number,
            "step66_rank": score_row["rank"],
            "weighted_score_percent": round(score_row["weighted_score_percent"], 3),
            "source_count": score_row["source_count"],
            "covered_count": covered_count,
            "coverage_percent": round(exposure * 100.0, 2),
            "number_group": number_group(number),
            "coverage_status": coverage_status(number, covered_count, score_row),
            "step66_status": score_row["status"],
        })

    coverage_rows.sort(key=lambda item: (item["step66_rank"], item["number"]))

    covered_numbers = {number for number, count in occurrence.items() if count > 0}
    unique_numbers_covered = len(covered_numbers)
    coverage_percent = (unique_numbers_covered / 49.0) * 100.0

    top10 = {row["number"] for row in coverage_rows if row["step66_rank"] <= 10}
    top20 = {row["number"] for row in coverage_rows if row["step66_rank"] <= 20}
    covered_top10 = len(top10.intersection(covered_numbers))
    covered_top20 = len(top20.intersection(covered_numbers))

    undercovered_top = [
        row for row in coverage_rows
        if row["step66_rank"] <= 20 and row["covered_count"] == 0
    ]

    ticket_analysis_rows = []

    for ticket in tickets:
        ticket_numbers = ticket["numbers"]
        avg_step66_score = sum(scores[n]["weighted_score_percent"] for n in ticket_numbers) / len(ticket_numbers)

        overlaps_with_others = [
            overlap_between(ticket_numbers, other["numbers"])
            for other in tickets
            if other["ticket_id"] != ticket["ticket_id"]
        ]

        max_overlap = max(overlaps_with_others) if overlaps_with_others else 0
        avg_overlap = sum(overlaps_with_others) / len(overlaps_with_others) if overlaps_with_others else 0.0

        ticket_unique_help = sum(1 for n in ticket_numbers if occurrence[n] == 1)
        top20_numbers = sum(1 for n in ticket_numbers if scores[n]["rank"] <= 20)

        portfolio_contribution = (
            avg_step66_score * 0.55
            + ticket_unique_help * 5.0
            + top20_numbers * 3.0
            - max_overlap * 4.0
        )

        ticket_analysis_rows.append({
            "ticket_id": ticket["ticket_id"],
            "strategy_label": ticket["strategy_label"],
            "numbers": ",".join(str(n) for n in ticket_numbers),
            "average_step66_score": round(avg_step66_score, 3),
            "average_step67_score": round(ticket["average_weighted_score"], 3),
            "unique_help_count": ticket_unique_help,
            "top20_numbers_count": top20_numbers,
            "max_overlap_with_other_ticket": max_overlap,
            "average_overlap_with_other_tickets": round(avg_overlap, 3),
            "portfolio_contribution_score": round(portfolio_contribution, 3),
            "balance_status": ticket["balance_status"],
            "risk_note": ticket["risk_note"],
        })

    ticket_analysis_rows.sort(
        key=lambda item: (
            -item["portfolio_contribution_score"],
            -item["average_step66_score"],
            item["ticket_id"],
        )
    )

    avg_ticket_score = (
        sum(row["average_step66_score"] for row in ticket_analysis_rows) / len(ticket_analysis_rows)
        if ticket_analysis_rows
        else 0.0
    )

    coverage_score = min(100.0, coverage_percent)
    top20_coverage_score = (covered_top20 / 20.0) * 100.0
    diversity_score = max(0.0, 100.0 - average_overlap * 18.0 - max(0, max_overlap_value - 3) * 12.0)
    repetition_score = max(0.0, 100.0 - len(repeated_pairs) * 2.5 - len(repeated_triples) * 8.0)

    portfolio_score = (
        coverage_score * 0.25
        + top20_coverage_score * 0.25
        + avg_ticket_score * 0.25
        + diversity_score * 0.15
        + repetition_score * 0.10
    )

    summary_core = {
        "tickets_analyzed": len(tickets),
        "unique_numbers_covered": unique_numbers_covered,
        "coverage_percent": round(coverage_percent, 2),
        "covered_top10_numbers": covered_top10,
        "covered_top20_numbers": covered_top20,
        "average_ticket_step66_score": round(avg_ticket_score, 3),
        "average_ticket_overlap": round(average_overlap, 3),
        "max_ticket_overlap": max_overlap_value,
        "repeated_pairs_count": len(repeated_pairs),
        "repeated_triples_count": len(repeated_triples),
        "coverage_score": round(coverage_score, 3),
        "top20_coverage_score": round(top20_coverage_score, 3),
        "diversity_score": round(diversity_score, 3),
        "repetition_score": round(repetition_score, 3),
        "portfolio_score": round(portfolio_score, 3),
        "portfolio_status": recommendation_level(portfolio_score),
    }

    recommendations = build_recommendations(
        summary_core=summary_core,
        undercovered_top=undercovered_top,
        repeated_pairs=repeated_pairs,
        repeated_triples=repeated_triples,
    )

    summary = {
        "step": "68",
        "name": "Weighted Portfolio Optimizer",
        "source_tickets": "reports/v67_weighted_ticket_builder_tickets.csv",
        "source_scores": "reports/v66_weighted_smart_ensemble_scores.csv",
        **summary_core,
        "undercovered_top20_numbers": [
            {
                "number": row["number"],
                "step66_rank": row["step66_rank"],
                "weighted_score_percent": row["weighted_score_percent"],
            }
            for row in undercovered_top
        ],
        "recommendations": recommendations,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_reports": [
            "reports/v68_weighted_portfolio_summary.json",
            "reports/v68_weighted_portfolio_summary.md",
            "reports/v68_weighted_portfolio_tickets.csv",
            "reports/v68_weighted_portfolio_coverage.csv",
            "reports/v68_weighted_portfolio_overlaps.csv",
            "reports/v68_weighted_portfolio_repeated_pairs.csv",
            "reports/v68_weighted_portfolio_repeated_triples.csv",
            "models/v68/v68_weighted_portfolio_optimizer_model.json",
        ],
        "safe_note": "This is a statistical portfolio optimizer. It is not a winning guarantee or a promise of future lottery results.",
    }

    write_csv(
        REPORTS_DIR / "v68_weighted_portfolio_tickets.csv",
        ticket_analysis_rows,
        [
            "ticket_id",
            "strategy_label",
            "numbers",
            "average_step66_score",
            "average_step67_score",
            "unique_help_count",
            "top20_numbers_count",
            "max_overlap_with_other_ticket",
            "average_overlap_with_other_tickets",
            "portfolio_contribution_score",
            "balance_status",
            "risk_note",
        ],
    )

    write_csv(
        REPORTS_DIR / "v68_weighted_portfolio_coverage.csv",
        coverage_rows,
        [
            "number",
            "step66_rank",
            "weighted_score_percent",
            "source_count",
            "covered_count",
            "coverage_percent",
            "number_group",
            "coverage_status",
            "step66_status",
        ],
    )

    write_csv(
        REPORTS_DIR / "v68_weighted_portfolio_overlaps.csv",
        pair_overlaps,
        ["ticket_a", "ticket_b", "overlap", "shared_numbers"],
    )

    write_csv(
        REPORTS_DIR / "v68_weighted_portfolio_repeated_pairs.csv",
        repeated_pairs,
        ["pair", "n1", "n2", "count"],
    )

    write_csv(
        REPORTS_DIR / "v68_weighted_portfolio_repeated_triples.csv",
        repeated_triples,
        ["triple", "n1", "n2", "n3", "count"],
    )

    write_json(REPORTS_DIR / "v68_weighted_portfolio_summary.json", summary)

    model_payload = {
        "summary": summary,
        "ticket_analysis": ticket_analysis_rows,
        "coverage": coverage_rows,
        "overlaps": pair_overlaps,
        "repeated_pairs": repeated_pairs,
        "repeated_triples": repeated_triples,
        "group_occurrence": dict(sorted(group_occurrence.items())),
        "formula": {
            "coverage_score": "unique_numbers_covered / 49 * 100",
            "top20_coverage_score": "covered top 20 Step 66 numbers / 20 * 100",
            "diversity_score": "100 - average_overlap*18 - high_max_overlap_penalty",
            "repetition_score": "100 - repeated_pairs*2.5 - repeated_triples*8",
            "portfolio_score": "0.25*coverage + 0.25*top20_coverage + 0.25*avg_ticket_score + 0.15*diversity + 0.10*repetition",
        },
        "safe_note": summary["safe_note"],
    }

    write_json(MODELS_DIR / "v68_weighted_portfolio_optimizer_model.json", model_payload)

    md = [
        "# Step 68 — Weighted Portfolio Optimizer",
        "",
        "This report evaluates the Step 67 ticket set as one statistical portfolio.",
        "",
        "**Important:** This is a portfolio analysis tool. It is not a prediction and not a winning guarantee.",
        "",
        f"Tickets analyzed: **{summary['tickets_analyzed']}**",
        f"Unique numbers covered: **{summary['unique_numbers_covered']} / 49**",
        f"Coverage: **{summary['coverage_percent']}%**",
        f"Covered top 10 Step 66 numbers: **{summary['covered_top10_numbers']} / 10**",
        f"Covered top 20 Step 66 numbers: **{summary['covered_top20_numbers']} / 20**",
        f"Average ticket Step 66 score: **{summary['average_ticket_step66_score']}%**",
        f"Average ticket overlap: **{summary['average_ticket_overlap']}**",
        f"Max ticket overlap: **{summary['max_ticket_overlap']}**",
        f"Repeated pairs: **{summary['repeated_pairs_count']}**",
        f"Repeated triples: **{summary['repeated_triples_count']}**",
        f"Portfolio score: **{summary['portfolio_score']} / 100**",
        f"Portfolio status: **{summary['portfolio_status']}**",
        "",
        "## Recommendations",
        "",
    ]

    for item in recommendations:
        md.append(f"- {item}")

    md.extend([
        "",
        "## Ticket contribution analysis",
        "",
        "| Ticket | Strategy | Numbers | Avg Step 66 score | Unique help | Top20 count | Max overlap | Portfolio contribution |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ])

    for row in ticket_analysis_rows:
        md.append(
            f"| {row['ticket_id']} | {row['strategy_label']} | {row['numbers']} | "
            f"{row['average_step66_score']}% | {row['unique_help_count']} | "
            f"{row['top20_numbers_count']} | {row['max_overlap_with_other_ticket']} | "
            f"{row['portfolio_contribution_score']} |"
        )

    md.extend([
        "",
        "## Under-covered top Step 66 numbers",
        "",
    ])

    if undercovered_top:
        for row in undercovered_top:
            md.append(
                f"- Number {row['number']} — Step 66 rank {row['step66_rank']}, "
                f"score {row['weighted_score_percent']}%"
            )
    else:
        md.append("- No under-covered top 20 Step 66 numbers.")

    md.extend([
        "",
        "## Safety note",
        "",
        "Lottery draws are random. This step only evaluates structure, coverage and overlap inside a statistical reference portfolio.",
    ])

    (REPORTS_DIR / "v68_weighted_portfolio_summary.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    return summary


if __name__ == "__main__":
    result = build_weighted_portfolio_optimizer()
    print("STEP68_OK")
    print("TICKETS_ANALYZED", result["tickets_analyzed"])
    print("UNIQUE_NUMBERS_COVERED", result["unique_numbers_covered"])
    print("PORTFOLIO_SCORE", result["portfolio_score"])
    print("PORTFOLIO_STATUS", result["portfolio_status"])

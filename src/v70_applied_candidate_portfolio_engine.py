from __future__ import annotations

from pathlib import Path
import csv
import itertools
import json
from collections import Counter
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v70"

STEP66_SCORES_PATH = REPORTS_DIR / "v66_weighted_smart_ensemble_scores.csv"
STEP67_ORIGINAL_TICKETS_PATH = REPORTS_DIR / "v67_weighted_ticket_builder_tickets.csv"
STEP69_SUMMARY_PATH = REPORTS_DIR / "v69_portfolio_improvement_summary.json"
STEP69_CANDIDATE_TICKETS_PATH = REPORTS_DIR / "v69_candidate_portfolio_tickets.csv"
STEP69_MODEL_PATH = ROOT / "models" / "v69" / "v69_portfolio_improvement_model.json"
HISTORICAL_DRAWS_PATH = ROOT / "data" / "historical_draws.csv"

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


def as_bool(value):
    return str(value).strip().lower() in {"true", "1", "yes", "да"}


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


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_ticket(numbers):
    clean = sorted({int(n) for n in numbers if NUMBER_MIN <= int(n) <= NUMBER_MAX})
    if len(clean) != TICKET_SIZE:
        return None
    return tuple(clean)


def parse_ticket_numbers(row):
    values = []

    for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        value = as_int(row.get(key))
        if value is not None:
            values.append(value)

    if len(values) < TICKET_SIZE:
        text = str(row.get("numbers", ""))
        for part in text.replace(";", ",").replace("·", ",").replace(" ", ",").split(","):
            value = as_int(part)
            if value is not None:
                values.append(value)

    return normalize_ticket(values)


def load_original_tickets():
    rows = read_csv_rows(STEP67_ORIGINAL_TICKETS_PATH)
    if not rows:
        raise FileNotFoundError("Missing reports/v67_weighted_ticket_builder_tickets.csv. Run Step 67 first.")

    tickets = []
    seen = set()

    for index, row in enumerate(rows, start=1):
        numbers = parse_ticket_numbers(row)
        if not numbers or numbers in seen:
            continue

        seen.add(numbers)
        tickets.append({
            "ticket_id": as_int(row.get("ticket_id"), index),
            "strategy": row.get("strategy", ""),
            "strategy_label": row.get("strategy_label", ""),
            "numbers": numbers,
            "source": "step67_original",
        })

    if len(tickets) < 2:
        raise RuntimeError("Step 70 needs at least 2 original Step 67 tickets.")

    return tickets


def load_candidate_tickets():
    rows = read_csv_rows(STEP69_CANDIDATE_TICKETS_PATH)
    if not rows:
        raise FileNotFoundError("Missing reports/v69_candidate_portfolio_tickets.csv. Run Step 69 first.")

    tickets = []
    seen = set()

    for index, row in enumerate(rows, start=1):
        numbers = parse_ticket_numbers(row)
        if not numbers or numbers in seen:
            continue

        seen.add(numbers)
        tickets.append({
            "ticket_id": as_int(row.get("ticket_id"), index),
            "strategy": "",
            "strategy_label": row.get("strategy_label", ""),
            "numbers": numbers,
            "average_step66_score_from_step69": as_float(row.get("average_step66_score"), 0.0),
            "changed": as_bool(row.get("changed")),
            "source": "step69_candidate",
        })

    if len(tickets) < 2:
        raise RuntimeError("Step 70 needs at least 2 candidate Step 69 tickets.")

    return tickets


def load_scores():
    rows = read_csv_rows(STEP66_SCORES_PATH)
    if not rows:
        raise FileNotFoundError("Missing reports/v66_weighted_smart_ensemble_scores.csv. Run Step 66 first.")

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


def load_historical_ticket_set():
    rows = read_csv_rows(HISTORICAL_DRAWS_PATH)
    tickets = set()

    for row in rows:
        values = []

        for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
            value = as_int(row.get(key))
            if value is not None:
                values.append(value)

        if len(values) < 6:
            for key in ["number_1", "number_2", "number_3", "number_4", "number_5", "number_6"]:
                value = as_int(row.get(key))
                if value is not None:
                    values.append(value)

        ticket = normalize_ticket(values[:6])
        if ticket:
            tickets.add(ticket)

    return tickets


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


def pair_counter(tickets):
    counter = Counter()
    for ticket in tickets:
        for pair in itertools.combinations(ticket["numbers"], 2):
            counter[pair] += 1
    return counter


def triple_counter(tickets):
    counter = Counter()
    for ticket in tickets:
        for triple in itertools.combinations(ticket["numbers"], 3):
            counter[triple] += 1
    return counter


def overlap_between(left, right):
    return len(set(left).intersection(set(right)))


def portfolio_status(score):
    if score >= 80:
        return "много добър статистически портфейл"
    if score >= 68:
        return "добър статистически портфейл"
    if score >= 55:
        return "приемлив портфейл с нужда от наблюдение"
    return "портфейл с нужда от подобрение"


def evaluate_portfolio(tickets, scores, historical_set):
    occurrence = Counter()
    group_occurrence = Counter()

    for ticket in tickets:
        for number in ticket["numbers"]:
            occurrence[number] += 1
            group_occurrence[number_group(number)] += 1

    covered_numbers = {number for number, count in occurrence.items() if count > 0}
    unique_numbers_covered = len(covered_numbers)
    coverage_percent = unique_numbers_covered / 49.0 * 100.0

    top10 = {number for number, row in scores.items() if row["rank"] <= 10}
    top20 = {number for number, row in scores.items() if row["rank"] <= 20}

    covered_top10 = len(top10.intersection(covered_numbers))
    covered_top20 = len(top20.intersection(covered_numbers))

    overlaps = []
    max_overlap = 0

    for left, right in itertools.combinations(tickets, 2):
        overlap = overlap_between(left["numbers"], right["numbers"])
        max_overlap = max(max_overlap, overlap)
        overlaps.append(overlap)

    average_overlap = sum(overlaps) / len(overlaps) if overlaps else 0.0

    repeated_pairs = [
        pair for pair, count in pair_counter(tickets).items()
        if count > 1
    ]

    repeated_triples = [
        triple for triple, count in triple_counter(tickets).items()
        if count > 1
    ]

    ticket_scores = []
    historical_matches = 0

    for ticket in tickets:
        avg_score = sum(scores[number]["weighted_score_percent"] for number in ticket["numbers"]) / 6.0
        ticket_scores.append(avg_score)

        if ticket["numbers"] in historical_set:
            historical_matches += 1

    average_ticket_score = sum(ticket_scores) / len(ticket_scores) if ticket_scores else 0.0

    coverage_score = min(100.0, coverage_percent)
    top20_coverage_score = covered_top20 / 20.0 * 100.0
    diversity_score = max(0.0, 100.0 - average_overlap * 18.0 - max(0, max_overlap - 3) * 12.0)
    repetition_score = max(0.0, 100.0 - len(repeated_pairs) * 2.5 - len(repeated_triples) * 8.0)

    portfolio_score = (
        coverage_score * 0.25
        + top20_coverage_score * 0.25
        + average_ticket_score * 0.25
        + diversity_score * 0.15
        + repetition_score * 0.10
    )

    undercovered_top20 = [
        {
            "number": number,
            "step66_rank": scores[number]["rank"],
            "weighted_score_percent": round(scores[number]["weighted_score_percent"], 3),
        }
        for number in sorted(top20, key=lambda n: scores[n]["rank"])
        if number not in covered_numbers
    ]

    return {
        "tickets_analyzed": len(tickets),
        "unique_numbers_covered": unique_numbers_covered,
        "coverage_percent": round(coverage_percent, 3),
        "covered_top10_numbers": covered_top10,
        "covered_top20_numbers": covered_top20,
        "average_ticket_step66_score": round(average_ticket_score, 3),
        "average_ticket_overlap": round(average_overlap, 3),
        "max_ticket_overlap": max_overlap,
        "repeated_pairs_count": len(repeated_pairs),
        "repeated_triples_count": len(repeated_triples),
        "historical_exact_matches": historical_matches,
        "portfolio_score": round(portfolio_score, 3),
        "portfolio_status": portfolio_status(portfolio_score),
        "undercovered_top20_numbers": undercovered_top20,
        "group_occurrence": dict(sorted(group_occurrence.items())),
    }


def build_ticket_rows(tickets, scores, historical_set):
    rows = []

    for ticket in tickets:
        numbers = ticket["numbers"]
        avg_score = sum(scores[number]["weighted_score_percent"] for number in numbers) / 6.0

        odd_count = sum(1 for number in numbers if number % 2 == 1)
        low_count = sum(1 for number in numbers if number <= 24)

        rows.append({
            "ticket_id": ticket["ticket_id"],
            "strategy_label": ticket.get("strategy_label", ""),
            "numbers": ",".join(str(number) for number in numbers),
            "n1": numbers[0],
            "n2": numbers[1],
            "n3": numbers[2],
            "n4": numbers[3],
            "n5": numbers[4],
            "n6": numbers[5],
            "average_step66_score": round(avg_score, 3),
            "odd_count": odd_count,
            "even_count": 6 - odd_count,
            "low_count": low_count,
            "high_count": 6 - low_count,
            "number_range": max(numbers) - min(numbers),
            "sum_numbers": sum(numbers),
            "historical_exact_match": bool(numbers in historical_set),
            "safe_note": "Приложен статистически кандидат портфейл, не гаранция за печалба.",
        })

    return rows


def build_comparison_rows(original_tickets, candidate_tickets, scores):
    original_by_id = {ticket["ticket_id"]: ticket for ticket in original_tickets}
    candidate_by_id = {ticket["ticket_id"]: ticket for ticket in candidate_tickets}

    rows = []

    for ticket_id in sorted(set(original_by_id) | set(candidate_by_id)):
        original = original_by_id.get(ticket_id)
        candidate = candidate_by_id.get(ticket_id)

        original_numbers = original["numbers"] if original else tuple()
        candidate_numbers = candidate["numbers"] if candidate else tuple()

        removed = sorted(set(original_numbers) - set(candidate_numbers))
        added = sorted(set(candidate_numbers) - set(original_numbers))

        original_avg = (
            sum(scores[number]["weighted_score_percent"] for number in original_numbers) / 6.0
            if len(original_numbers) == 6 else 0.0
        )
        candidate_avg = (
            sum(scores[number]["weighted_score_percent"] for number in candidate_numbers) / 6.0
            if len(candidate_numbers) == 6 else 0.0
        )

        rows.append({
            "ticket_id": ticket_id,
            "strategy_label": (candidate or original or {}).get("strategy_label", ""),
            "original_numbers": ",".join(str(number) for number in original_numbers),
            "candidate_numbers": ",".join(str(number) for number in candidate_numbers),
            "removed_numbers": ",".join(str(number) for number in removed),
            "added_numbers": ",".join(str(number) for number in added),
            "changed": bool(removed or added),
            "original_average_step66_score": round(original_avg, 3),
            "candidate_average_step66_score": round(candidate_avg, 3),
            "average_score_delta": round(candidate_avg - original_avg, 3),
        })

    return rows


def build_applied_changes_rows(comparison_rows):
    rows = []

    for row in comparison_rows:
        if not row["changed"]:
            continue

        rows.append({
            "ticket_id": row["ticket_id"],
            "strategy_label": row["strategy_label"],
            "removed_numbers": row["removed_numbers"],
            "added_numbers": row["added_numbers"],
            "original_numbers": row["original_numbers"],
            "applied_numbers": row["candidate_numbers"],
            "average_score_delta": row["average_score_delta"],
            "safe_note": "Приложена статистическа промяна от Step 69 candidate portfolio.",
        })

    return rows


def decision_note(original_metrics, candidate_metrics):
    score_delta = candidate_metrics["portfolio_score"] - original_metrics["portfolio_score"]
    top20_delta = candidate_metrics["covered_top20_numbers"] - original_metrics["covered_top20_numbers"]
    unique_delta = candidate_metrics["unique_numbers_covered"] - original_metrics["unique_numbers_covered"]
    pair_delta = candidate_metrics["repeated_pairs_count"] - original_metrics["repeated_pairs_count"]
    triple_delta = candidate_metrics["repeated_triples_count"] - original_metrics["repeated_triples_count"]

    if (
        top20_delta >= 0
        and unique_delta >= 0
        and pair_delta <= 0
        and triple_delta <= 0
        and score_delta >= -1.5
    ):
        return "candidate portfolio accepted as improved статистическа референция"

    if score_delta >= 0:
        return "candidate portfolio accepted because overall portfolio score improved"

    return "candidate portfolio applied for review, but needs monitoring"


def build_applied_candidate_portfolio():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    original_tickets = load_original_tickets()
    candidate_tickets = load_candidate_tickets()
    scores = load_scores()
    historical_set = load_historical_ticket_set()

    if not STEP69_SUMMARY_PATH.exists():
        raise FileNotFoundError("Missing reports/v69_portfolio_improvement_summary.json. Run Step 69 first.")

    step69_summary = read_json(STEP69_SUMMARY_PATH)
    step69_model = read_json(STEP69_MODEL_PATH) if STEP69_MODEL_PATH.exists() else {}

    original_metrics = evaluate_portfolio(original_tickets, scores, historical_set)
    candidate_metrics = evaluate_portfolio(candidate_tickets, scores, historical_set)

    applied_ticket_rows = build_ticket_rows(candidate_tickets, scores, historical_set)
    comparison_rows = build_comparison_rows(original_tickets, candidate_tickets, scores)
    applied_changes = build_applied_changes_rows(comparison_rows)

    summary = {
        "step": "70",
        "name": "Apply Candidate Portfolio",
        "source_original_portfolio": "reports/v67_weighted_ticket_builder_tickets.csv",
        "source_candidate_portfolio": "reports/v69_candidate_portfolio_tickets.csv",
        "source_suggestions": "reports/v69_portfolio_improvement_summary.json",
        "applied_portfolio_tickets": len(applied_ticket_rows),
        "applied_changes_count": len(applied_changes),
        "original_portfolio_score": original_metrics["portfolio_score"],
        "applied_portfolio_score": candidate_metrics["portfolio_score"],
        "portfolio_score_delta": round(candidate_metrics["portfolio_score"] - original_metrics["portfolio_score"], 3),
        "original_top20_coverage": original_metrics["covered_top20_numbers"],
        "applied_top20_coverage": candidate_metrics["covered_top20_numbers"],
        "original_unique_numbers": original_metrics["unique_numbers_covered"],
        "applied_unique_numbers": candidate_metrics["unique_numbers_covered"],
        "original_repeated_pairs": original_metrics["repeated_pairs_count"],
        "applied_repeated_pairs": candidate_metrics["repeated_pairs_count"],
        "original_repeated_triples": original_metrics["repeated_triples_count"],
        "applied_repeated_triples": candidate_metrics["repeated_triples_count"],
        "applied_historical_exact_matches": candidate_metrics["historical_exact_matches"],
        "decision": decision_note(original_metrics, candidate_metrics),
        "undercovered_top20_after_apply": candidate_metrics["undercovered_top20_numbers"],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_reports": [
            "reports/v70_applied_candidate_portfolio_summary.json",
            "reports/v70_applied_candidate_portfolio_summary.md",
            "reports/v70_applied_candidate_portfolio_tickets.csv",
            "reports/v70_applied_candidate_portfolio_tickets.json",
            "reports/v70_original_vs_candidate_portfolio.csv",
            "reports/v70_applied_candidate_portfolio_changes.csv",
            "models/v70/v70_applied_candidate_portfolio_model.json",
        ],
        "safe_note": "This is an applied статистическа референция portfolio. It is not a гаранция за печалба or a promise of future lottery results.",
    }

    write_csv(
        REPORTS_DIR / "v70_applied_candidate_portfolio_tickets.csv",
        applied_ticket_rows,
        [
            "ticket_id",
            "strategy_label",
            "numbers",
            "n1",
            "n2",
            "n3",
            "n4",
            "n5",
            "n6",
            "average_step66_score",
            "odd_count",
            "even_count",
            "low_count",
            "high_count",
            "number_range",
            "sum_numbers",
            "historical_exact_match",
            "safe_note",
        ],
    )
    write_json(REPORTS_DIR / "v70_applied_candidate_portfolio_tickets.json", applied_ticket_rows)

    write_csv(
        REPORTS_DIR / "v70_original_vs_candidate_portfolio.csv",
        comparison_rows,
        [
            "ticket_id",
            "strategy_label",
            "original_numbers",
            "candidate_numbers",
            "removed_numbers",
            "added_numbers",
            "changed",
            "original_average_step66_score",
            "candidate_average_step66_score",
            "average_score_delta",
        ],
    )

    write_csv(
        REPORTS_DIR / "v70_applied_candidate_portfolio_changes.csv",
        applied_changes,
        [
            "ticket_id",
            "strategy_label",
            "removed_numbers",
            "added_numbers",
            "original_numbers",
            "applied_numbers",
            "average_score_delta",
            "safe_note",
        ],
    )

    write_json(REPORTS_DIR / "v70_applied_candidate_portfolio_summary.json", summary)

    model_payload = {
        "summary": summary,
        "original_metrics": original_metrics,
        "applied_metrics": candidate_metrics,
        "applied_tickets": applied_ticket_rows,
        "comparison": comparison_rows,
        "applied_changes": applied_changes,
        "step69_summary_reference": {
            "baseline_portfolio_score": step69_summary.get("baseline_portfolio_score"),
            "candidate_portfolio_score": step69_summary.get("candidate_portfolio_score"),
            "candidate_changes_applied": step69_summary.get("candidate_changes_applied"),
            "suggestions_generated": step69_summary.get("suggestions_generated"),
        },
        "step69_applied_suggestions": step69_model.get("applied_suggestions", []),
        "safe_note": summary["safe_note"],
    }

    write_json(MODELS_DIR / "v70_applied_candidate_portfolio_model.json", model_payload)

    md = [
        "# Step 70 — Apply Candidate Portfolio",
        "",
        "This report turns the Step 69 candidate portfolio into a separate applied статистическа референция portfolio.",
        "",
        "**Important:** This does not overwrite Step 67. It creates a v70 applied portfolio layer. It is not a prediction and not a гаранция за печалба.",
        "",
        f"Applied portfolio tickets: **{summary['applied_portfolio_tickets']}**",
        f"Applied changes: **{summary['applied_changes_count']}**",
        f"Original portfolio score: **{summary['original_portfolio_score']} / 100**",
        f"Applied portfolio score: **{summary['applied_portfolio_score']} / 100**",
        f"Portfolio score delta: **{summary['portfolio_score_delta']}**",
        f"Original top20 coverage: **{summary['original_top20_coverage']} / 20**",
        f"Applied top20 coverage: **{summary['applied_top20_coverage']} / 20**",
        f"Original repeated pairs: **{summary['original_repeated_pairs']}**",
        f"Applied repeated pairs: **{summary['applied_repeated_pairs']}**",
        f"Original repeated triples: **{summary['original_repeated_triples']}**",
        f"Applied repeated triples: **{summary['applied_repeated_triples']}**",
        f"Decision: **{summary['decision']}**",
        "",
        "## Applied changes",
        "",
        "| Ticket | Strategy | Removed | Added | Original | Applied | Avg score delta |",
        "|---:|---|---|---|---|---|---:|",
    ]

    if applied_changes:
        for row in applied_changes:
            md.append(
                f"| {row['ticket_id']} | {row['strategy_label']} | {row['removed_numbers']} | "
                f"{row['added_numbers']} | {row['original_numbers']} | {row['applied_numbers']} | "
                f"{row['average_score_delta']} |"
            )
    else:
        md.append("| - | - | - | - | - | - | - |")

    md.extend([
        "",
        "## Applied portfolio tickets",
        "",
        "| Ticket | Strategy | Numbers | Avg Step 66 score | Historical exact match |",
        "|---:|---|---|---:|---|",
    ])

    for row in applied_ticket_rows:
        md.append(
            f"| {row['ticket_id']} | {row['strategy_label']} | {row['numbers']} | "
            f"{row['average_step66_score']}% | {row['historical_exact_match']} |"
        )

    md.extend([
        "",
        "## Safety note",
        "",
        "Lottery draws are random. This step only applies a статистическа референция candidate portfolio for review and future comparison.",
    ])

    (REPORTS_DIR / "v70_applied_candidate_portfolio_summary.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    return summary


if __name__ == "__main__":
    result = build_applied_candidate_portfolio()
    print("STEP70_OK")
    print("APPLIED_TICKETS", result["applied_portfolio_tickets"])
    print("APPLIED_CHANGES", result["applied_changes_count"])
    print("ORIGINAL_SCORE", result["original_portfolio_score"])
    print("APPLIED_SCORE", result["applied_portfolio_score"])
    print("DECISION", result["decision"])

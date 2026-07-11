from __future__ import annotations

from pathlib import Path
import csv
import itertools
import json
from collections import Counter
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v69"

STEP66_SCORES_PATH = REPORTS_DIR / "v66_weighted_smart_ensemble_scores.csv"
STEP67_TICKETS_PATH = REPORTS_DIR / "v67_weighted_ticket_builder_tickets.csv"
STEP68_SUMMARY_PATH = REPORTS_DIR / "v68_weighted_portfolio_summary.json"
STEP68_COVERAGE_PATH = REPORTS_DIR / "v68_weighted_portfolio_coverage.csv"
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
        for part in text.replace(";", ",").replace(" ", ",").split(","):
            value = as_int(part)
            if value is not None:
                values.append(value)

    return normalize_ticket(values)


def load_step67_tickets():
    rows = read_csv_rows(STEP67_TICKETS_PATH)
    if not rows:
        raise FileNotFoundError(
            "Missing reports/v67_weighted_ticket_builder_tickets.csv. "
            "Run Step 67 first."
        )

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
            "average_weighted_score": as_float(row.get("average_weighted_score"), 0.0),
            "balance_status": row.get("balance_status", ""),
            "risk_note": row.get("risk_note", ""),
        })

    if len(tickets) < 2:
        raise RuntimeError("Step 69 needs at least 2 Step 67 tickets.")

    return tickets


def load_step66_scores():
    rows = read_csv_rows(STEP66_SCORES_PATH)
    if not rows:
        raise FileNotFoundError(
            "Missing reports/v66_weighted_smart_ensemble_scores.csv. "
            "Run Step 66 first."
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
        raise RuntimeError(f"Expected 49 Step 66 score rows, got {len(scores)}.")

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


def ticket_pairs(ticket):
    return list(itertools.combinations(ticket, 2))


def ticket_triples(ticket):
    return list(itertools.combinations(ticket, 3))


def pair_counter(tickets):
    counter = Counter()
    for ticket in tickets:
        for pair in ticket_pairs(ticket["numbers"]):
            counter[pair] += 1
    return counter


def triple_counter(tickets):
    counter = Counter()
    for ticket in tickets:
        for triple in ticket_triples(ticket["numbers"]):
            counter[triple] += 1
    return counter


def overlap_between(left, right):
    return len(set(left).intersection(set(right)))


def evaluate_portfolio(tickets, scores):
    occurrence = Counter()
    groups = Counter()

    for ticket in tickets:
        for number in ticket["numbers"]:
            occurrence[number] += 1
            groups[number_group(number)] += 1

    covered_numbers = {number for number, count in occurrence.items() if count > 0}
    unique_numbers_covered = len(covered_numbers)
    coverage_percent = unique_numbers_covered / 49.0 * 100.0

    top10 = {number for number, row in scores.items() if row["rank"] <= 10}
    top20 = {number for number, row in scores.items() if row["rank"] <= 20}

    covered_top10 = len(top10.intersection(covered_numbers))
    covered_top20 = len(top20.intersection(covered_numbers))

    overlap_values = []
    max_overlap = 0

    for left, right in itertools.combinations(tickets, 2):
        overlap = overlap_between(left["numbers"], right["numbers"])
        overlap_values.append(overlap)
        max_overlap = max(max_overlap, overlap)

    average_overlap = sum(overlap_values) / len(overlap_values) if overlap_values else 0.0

    repeated_pairs = [
        {"pair": pair, "count": count}
        for pair, count in pair_counter(tickets).items()
        if count > 1
    ]

    repeated_triples = [
        {"triple": triple, "count": count}
        for triple, count in triple_counter(tickets).items()
        if count > 1
    ]

    ticket_scores = []
    for ticket in tickets:
        avg_score = sum(scores[number]["weighted_score_percent"] for number in ticket["numbers"]) / 6.0
        ticket_scores.append(avg_score)

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
        "unique_numbers_covered": unique_numbers_covered,
        "coverage_percent": round(coverage_percent, 3),
        "covered_top10_numbers": covered_top10,
        "covered_top20_numbers": covered_top20,
        "average_ticket_step66_score": round(average_ticket_score, 3),
        "average_ticket_overlap": round(average_overlap, 3),
        "max_ticket_overlap": max_overlap,
        "repeated_pairs_count": len(repeated_pairs),
        "repeated_triples_count": len(repeated_triples),
        "portfolio_score": round(portfolio_score, 3),
        "undercovered_top20_numbers": undercovered_top20,
        "repeated_pairs": repeated_pairs,
        "repeated_triples": repeated_triples,
        "group_occurrence": dict(sorted(groups.items())),
    }


def make_ticket_object(source_ticket, new_numbers):
    return {
        **source_ticket,
        "numbers": tuple(sorted(new_numbers)),
    }


def replacement_reason(target_number, remove_number, before, after, scores):
    parts = []

    target_rank = scores[target_number]["rank"]
    remove_rank = scores[remove_number]["rank"]

    if target_rank <= 20:
        parts.append(f"покрива непокрит top20 сигнал {target_number}")

    if target_rank < remove_rank:
        parts.append(f"заменя по-слаб rank {remove_rank} с по-силен rank {target_rank}")

    if after["repeated_pairs_count"] < before["repeated_pairs_count"]:
        parts.append("намалява повторените двойки")

    if after["repeated_triples_count"] < before["repeated_triples_count"]:
        parts.append("намалява повторените тройки")

    if after["unique_numbers_covered"] > before["unique_numbers_covered"]:
        parts.append("увеличава уникалното покритие")

    if after["covered_top20_numbers"] > before["covered_top20_numbers"]:
        parts.append("увеличава top20 покритието")

    if not parts:
        parts.append("структурна алтернатива за наблюдение")

    return "; ".join(parts)


def recommendation_strength(expected_gain, after, before):
    if expected_gain >= 12 and after["portfolio_score"] >= before["portfolio_score"]:
        return "силна препоръка"
    if expected_gain >= 6:
        return "добра препоръка"
    if expected_gain >= 1:
        return "умерена препоръка"
    return "само за наблюдение"


def build_candidate_suggestions(tickets, scores, historical_set, limit=60):
    before = evaluate_portfolio(tickets, scores)
    undercovered = before["undercovered_top20_numbers"]

    if undercovered:
        target_numbers = [item["number"] for item in undercovered]
    else:
        target_numbers = [
            number
            for number, row in sorted(scores.items(), key=lambda item: item[1]["rank"])
            if number not in {n for ticket in tickets for n in ticket["numbers"]}
        ][:8]

    candidates = []

    for target_number in target_numbers:
        target_score = scores[target_number]["weighted_score_percent"]

        for ticket_index, ticket in enumerate(tickets):
            current_numbers = list(ticket["numbers"])

            if target_number in current_numbers:
                continue

            for remove_number in current_numbers:
                candidate_numbers = sorted(set(current_numbers) - {remove_number} | {target_number})

                if len(candidate_numbers) != 6:
                    continue

                candidate_tuple = tuple(candidate_numbers)
                if candidate_tuple in historical_set:
                    continue

                candidate_tickets = list(tickets)
                candidate_tickets[ticket_index] = make_ticket_object(ticket, candidate_tuple)

                after = evaluate_portfolio(candidate_tickets, scores)

                removed_score = scores[remove_number]["weighted_score_percent"]
                raw_score_delta = target_score - removed_score
                portfolio_delta = after["portfolio_score"] - before["portfolio_score"]
                unique_gain = after["unique_numbers_covered"] - before["unique_numbers_covered"]
                top20_gain = after["covered_top20_numbers"] - before["covered_top20_numbers"]
                pair_reduction = before["repeated_pairs_count"] - after["repeated_pairs_count"]
                triple_reduction = before["repeated_triples_count"] - after["repeated_triples_count"]
                max_overlap_reduction = before["max_ticket_overlap"] - after["max_ticket_overlap"]

                expected_gain = (
                    portfolio_delta
                    + top20_gain * 12.0
                    + unique_gain * 4.0
                    + pair_reduction * 1.6
                    + triple_reduction * 6.0
                    + max_overlap_reduction * 3.0
                    + raw_score_delta * 0.08
                )

                reason = replacement_reason(target_number, remove_number, before, after, scores)

                candidates.append({
                    "rank": 0,
                    "ticket_id": ticket["ticket_id"],
                    "strategy_label": ticket["strategy_label"],
                    "current_numbers": ",".join(str(n) for n in ticket["numbers"]),
                    "suggested_numbers": ",".join(str(n) for n in candidate_tuple),
                    "remove_number": remove_number,
                    "add_number": target_number,
                    "remove_step66_rank": scores[remove_number]["rank"],
                    "add_step66_rank": scores[target_number]["rank"],
                    "remove_step66_score": round(removed_score, 3),
                    "add_step66_score": round(target_score, 3),
                    "portfolio_score_before": before["portfolio_score"],
                    "portfolio_score_after": after["portfolio_score"],
                    "portfolio_score_delta": round(portfolio_delta, 3),
                    "unique_coverage_before": before["unique_numbers_covered"],
                    "unique_coverage_after": after["unique_numbers_covered"],
                    "top20_coverage_before": before["covered_top20_numbers"],
                    "top20_coverage_after": after["covered_top20_numbers"],
                    "repeated_pairs_before": before["repeated_pairs_count"],
                    "repeated_pairs_after": after["repeated_pairs_count"],
                    "repeated_triples_before": before["repeated_triples_count"],
                    "repeated_triples_after": after["repeated_triples_count"],
                    "max_overlap_before": before["max_ticket_overlap"],
                    "max_overlap_after": after["max_ticket_overlap"],
                    "expected_gain_score": round(expected_gain, 3),
                    "recommendation_strength": recommendation_strength(expected_gain, after, before),
                    "reason": reason,
                    "safe_note": "Статистическа препоръка за подобрение, не гаранция за печалба.",
                })

    candidates.sort(
        key=lambda item: (
            -item["expected_gain_score"],
            -item["top20_coverage_after"],
            item["repeated_pairs_after"],
            item["repeated_triples_after"],
            -item["portfolio_score_after"],
            item["ticket_id"],
        )
    )

    for index, item in enumerate(candidates, start=1):
        item["rank"] = index

    return candidates[:limit]


def build_candidate_portfolio(tickets, scores, suggestions, historical_set, max_changes=4):
    current = [dict(ticket) for ticket in tickets]
    applied = []
    used_ticket_ids = set()
    used_added_numbers = set()

    baseline = evaluate_portfolio(current, scores)
    current_metrics = baseline

    for suggestion in suggestions:
        if len(applied) >= max_changes:
            break

        ticket_id = suggestion["ticket_id"]
        add_number = suggestion["add_number"]

        if ticket_id in used_ticket_ids:
            continue

        if add_number in used_added_numbers:
            continue

        ticket_index = next(
            (index for index, ticket in enumerate(current) if ticket["ticket_id"] == ticket_id),
            None,
        )

        if ticket_index is None:
            continue

        new_numbers = tuple(as_int(part) for part in str(suggestion["suggested_numbers"]).split(","))
        new_numbers = normalize_ticket(new_numbers)

        if not new_numbers or new_numbers in historical_set:
            continue

        trial = list(current)
        trial[ticket_index] = make_ticket_object(current[ticket_index], new_numbers)
        trial_metrics = evaluate_portfolio(trial, scores)

        if (
            trial_metrics["covered_top20_numbers"] >= current_metrics["covered_top20_numbers"]
            and trial_metrics["portfolio_score"] >= current_metrics["portfolio_score"] - 1.5
            and trial_metrics["repeated_triples_count"] <= current_metrics["repeated_triples_count"] + 1
        ):
            current = trial
            current_metrics = trial_metrics
            used_ticket_ids.add(ticket_id)
            used_added_numbers.add(add_number)
            applied.append(suggestion)

    candidate_rows = []

    for ticket in current:
        avg_score = sum(scores[number]["weighted_score_percent"] for number in ticket["numbers"]) / 6.0
        candidate_rows.append({
            "ticket_id": ticket["ticket_id"],
            "strategy_label": ticket["strategy_label"],
            "numbers": ",".join(str(n) for n in ticket["numbers"]),
            "average_step66_score": round(avg_score, 3),
            "changed": any(item["ticket_id"] == ticket["ticket_id"] for item in applied),
            "safe_note": "Кандидат портфолио за преглед, не гаранция за печалба.",
        })

    return {
        "candidate_tickets": candidate_rows,
        "applied_suggestions": applied,
        "before_metrics": baseline,
        "after_metrics": current_metrics,
    }


def build_portfolio_improvement_suggestions():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    tickets = load_step67_tickets()
    scores = load_step66_scores()
    historical_set = load_historical_ticket_set()

    if not STEP68_SUMMARY_PATH.exists():
        raise FileNotFoundError("Missing reports/v68_weighted_portfolio_summary.json. Run Step 68 first.")

    step68_summary = read_json(STEP68_SUMMARY_PATH)
    coverage_rows = read_csv_rows(STEP68_COVERAGE_PATH)

    baseline_metrics = evaluate_portfolio(tickets, scores)
    suggestions = build_candidate_suggestions(tickets, scores, historical_set)
    candidate_portfolio = build_candidate_portfolio(tickets, scores, suggestions, historical_set)

    summary = {
        "step": "69",
        "name": "Portfolio Improvement Suggestions",
        "source_tickets": "reports/v67_weighted_ticket_builder_tickets.csv",
        "source_scores": "reports/v66_weighted_smart_ensemble_scores.csv",
        "source_portfolio": "reports/v68_weighted_portfolio_summary.json",
        "suggestions_generated": len(suggestions),
        "candidate_changes_applied": len(candidate_portfolio["applied_suggestions"]),
        "baseline_portfolio_score": baseline_metrics["portfolio_score"],
        "candidate_portfolio_score": candidate_portfolio["after_metrics"]["portfolio_score"],
        "portfolio_score_delta": round(
            candidate_portfolio["after_metrics"]["portfolio_score"] - baseline_metrics["portfolio_score"],
            3,
        ),
        "baseline_top20_coverage": baseline_metrics["covered_top20_numbers"],
        "candidate_top20_coverage": candidate_portfolio["after_metrics"]["covered_top20_numbers"],
        "baseline_unique_numbers": baseline_metrics["unique_numbers_covered"],
        "candidate_unique_numbers": candidate_portfolio["after_metrics"]["unique_numbers_covered"],
        "baseline_repeated_pairs": baseline_metrics["repeated_pairs_count"],
        "candidate_repeated_pairs": candidate_portfolio["after_metrics"]["repeated_pairs_count"],
        "baseline_repeated_triples": baseline_metrics["repeated_triples_count"],
        "candidate_repeated_triples": candidate_portfolio["after_metrics"]["repeated_triples_count"],
        "undercovered_top20_before": baseline_metrics["undercovered_top20_numbers"],
        "undercovered_top20_after": candidate_portfolio["after_metrics"]["undercovered_top20_numbers"],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_reports": [
            "reports/v69_portfolio_improvement_summary.json",
            "reports/v69_portfolio_improvement_summary.md",
            "reports/v69_portfolio_improvement_suggestions.csv",
            "reports/v69_candidate_portfolio_tickets.csv",
            "reports/v69_candidate_portfolio_tickets.json",
            "models/v69/v69_portfolio_improvement_model.json",
        ],
        "safe_note": "These are statistical improvement suggestions. They do not guarantee a win or future lottery results.",
    }

    suggestion_fields = [
        "rank",
        "ticket_id",
        "strategy_label",
        "current_numbers",
        "suggested_numbers",
        "remove_number",
        "add_number",
        "remove_step66_rank",
        "add_step66_rank",
        "remove_step66_score",
        "add_step66_score",
        "portfolio_score_before",
        "portfolio_score_after",
        "portfolio_score_delta",
        "unique_coverage_before",
        "unique_coverage_after",
        "top20_coverage_before",
        "top20_coverage_after",
        "repeated_pairs_before",
        "repeated_pairs_after",
        "repeated_triples_before",
        "repeated_triples_after",
        "max_overlap_before",
        "max_overlap_after",
        "expected_gain_score",
        "recommendation_strength",
        "reason",
        "safe_note",
    ]

    write_csv(REPORTS_DIR / "v69_portfolio_improvement_suggestions.csv", suggestions, suggestion_fields)

    candidate_fields = [
        "ticket_id",
        "strategy_label",
        "numbers",
        "average_step66_score",
        "changed",
        "safe_note",
    ]

    write_csv(
        REPORTS_DIR / "v69_candidate_portfolio_tickets.csv",
        candidate_portfolio["candidate_tickets"],
        candidate_fields,
    )
    write_json(REPORTS_DIR / "v69_candidate_portfolio_tickets.json", candidate_portfolio["candidate_tickets"])

    write_json(REPORTS_DIR / "v69_portfolio_improvement_summary.json", summary)

    model_payload = {
        "summary": summary,
        "baseline_metrics": baseline_metrics,
        "candidate_metrics": candidate_portfolio["after_metrics"],
        "suggestions": suggestions,
        "candidate_portfolio": candidate_portfolio["candidate_tickets"],
        "applied_suggestions": candidate_portfolio["applied_suggestions"],
        "step68_summary_reference": {
            "portfolio_score": step68_summary.get("portfolio_score"),
            "portfolio_status": step68_summary.get("portfolio_status"),
            "undercovered_top20_numbers": step68_summary.get("undercovered_top20_numbers", []),
        },
        "coverage_reference_rows": coverage_rows,
        "safe_note": summary["safe_note"],
    }

    write_json(MODELS_DIR / "v69_portfolio_improvement_model.json", model_payload)

    md = [
        "# Step 69 — Portfolio Improvement Suggestions",
        "",
        "This report proposes concrete statistical improvements for the Step 67 ticket portfolio, using Step 66 scores and Step 68 portfolio analysis.",
        "",
        "**Important:** These are improvement suggestions only. They are not predictions or guarantees of a win.",
        "",
        f"Suggestions generated: **{summary['suggestions_generated']}**",
        f"Candidate changes applied: **{summary['candidate_changes_applied']}**",
        f"Baseline portfolio score: **{summary['baseline_portfolio_score']} / 100**",
        f"Candidate portfolio score: **{summary['candidate_portfolio_score']} / 100**",
        f"Portfolio score delta: **{summary['portfolio_score_delta']}**",
        f"Baseline top20 coverage: **{summary['baseline_top20_coverage']} / 20**",
        f"Candidate top20 coverage: **{summary['candidate_top20_coverage']} / 20**",
        f"Baseline unique numbers: **{summary['baseline_unique_numbers']}**",
        f"Candidate unique numbers: **{summary['candidate_unique_numbers']}**",
        f"Baseline repeated pairs: **{summary['baseline_repeated_pairs']}**",
        f"Candidate repeated pairs: **{summary['candidate_repeated_pairs']}**",
        f"Baseline repeated triples: **{summary['baseline_repeated_triples']}**",
        f"Candidate repeated triples: **{summary['candidate_repeated_triples']}**",
        "",
        "## Top suggestions",
        "",
        "| Rank | Ticket | Replace | Add | Current | Suggested | Expected gain | Strength | Reason |",
        "|---:|---:|---:|---:|---|---|---:|---|---|",
    ]

    for item in suggestions[:15]:
        md.append(
            f"| {item['rank']} | {item['ticket_id']} | {item['remove_number']} | "
            f"{item['add_number']} | {item['current_numbers']} | {item['suggested_numbers']} | "
            f"{item['expected_gain_score']} | {item['recommendation_strength']} | {item['reason']} |"
        )

    md.extend([
        "",
        "## Candidate portfolio",
        "",
        "| Ticket | Strategy | Numbers | Avg Step 66 score | Changed |",
        "|---:|---|---|---:|---|",
    ])

    for row in candidate_portfolio["candidate_tickets"]:
        md.append(
            f"| {row['ticket_id']} | {row['strategy_label']} | {row['numbers']} | "
            f"{row['average_step66_score']}% | {row['changed']} |"
        )

    md.extend([
        "",
        "## Safety note",
        "",
        "Lottery draws are random. This step only suggests structural/statistical improvements to a reference portfolio.",
    ])

    (REPORTS_DIR / "v69_portfolio_improvement_summary.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    return summary


if __name__ == "__main__":
    result = build_portfolio_improvement_suggestions()
    print("STEP69_OK")
    print("SUGGESTIONS_GENERATED", result["suggestions_generated"])
    print("CANDIDATE_CHANGES", result["candidate_changes_applied"])
    print("BASELINE_SCORE", result["baseline_portfolio_score"])
    print("CANDIDATE_SCORE", result["candidate_portfolio_score"])

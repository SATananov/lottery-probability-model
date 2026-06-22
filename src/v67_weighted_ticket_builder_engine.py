from __future__ import annotations

from pathlib import Path
import csv
import itertools
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v67"

SOURCE_SCORES_PATH = REPORTS_DIR / "v66_weighted_smart_ensemble_scores.csv"
HISTORICAL_DRAWS_PATH = ROOT / "data" / "historical_draws.csv"

NUMBER_MIN = 1
NUMBER_MAX = 49
TICKET_SIZE = 6

TICKET_STRATEGIES = [
    {
        "strategy": "balanced_weighted",
        "label": "Балансиран претеглен фиш",
        "pool_size": 24,
        "description": "Търси силен среден score, но с контрол върху odd/even, low/high, range и десетилетия.",
    },
    {
        "strategy": "high_confidence",
        "label": "Фиш с висока претеглена оценка",
        "pool_size": 16,
        "description": "Предпочита най-силните числа от Step 66, с минимален структурен контрол.",
    },
    {
        "strategy": "diversified_weighted",
        "label": "Диверсифициран претеглен фиш",
        "pool_size": 30,
        "description": "Намалява припокриването с предишните фишове и пази по-широко покритие.",
    },
    {
        "strategy": "odd_even_balanced",
        "label": "Балансиран фиш по нечетни/четни числа",
        "pool_size": 28,
        "description": "Търси 3/3 или 2/4 баланс между четни и нечетни числа.",
    },
    {
        "strategy": "low_high_balanced",
        "label": "Балансиран фиш по ниски/високи числа",
        "pool_size": 28,
        "description": "Търси баланс между ниски числа 1–24 и високи числа 25–49.",
    },
    {
        "strategy": "spread_balanced",
        "label": "Разпределен range фиш",
        "pool_size": 32,
        "description": "Предпочита по-широк диапазон и поне няколко различни десетични групи.",
    },
    {
        "strategy": "conservative_core",
        "label": "Консервативно ядро",
        "pool_size": 22,
        "description": "Държи се близо до top weighted числата, но избягва прекалено концентриран фиш.",
    },
    {
        "strategy": "exploratory_weighted",
        "label": "Разширен статистически фиш",
        "pool_size": 36,
        "description": "Позволява малко по-широк пул, за да не се повтарят само най-очевидните числа.",
    },
]


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


def normalize_ticket(numbers):
    clean = sorted({int(n) for n in numbers if NUMBER_MIN <= int(n) <= NUMBER_MAX})
    if len(clean) != TICKET_SIZE:
        return None
    return tuple(clean)


def load_weighted_scores():
    rows = read_csv_rows(SOURCE_SCORES_PATH)
    if not rows:
        raise FileNotFoundError(
            "Missing reports/v66_weighted_smart_ensemble_scores.csv. "
            "Run Step 66 first: python scripts/v66_build_weighted_smart_ensemble.py"
        )

    parsed = []
    for row in rows:
        number = as_int(row.get("number"))
        if number is None or not (NUMBER_MIN <= number <= NUMBER_MAX):
            continue

        parsed.append({
            "number": number,
            "rank": as_int(row.get("rank"), 999),
            "weighted_score_percent": as_float(row.get("weighted_score_percent"), 0.0),
            "weighted_score": as_float(row.get("weighted_score"), 0.0),
            "source_count": as_int(row.get("source_count"), 0),
            "status": row.get("status", ""),
            "top_sources": row.get("top_sources", ""),
        })

    parsed.sort(
        key=lambda item: (
            -item["weighted_score_percent"],
            -item["source_count"],
            item["rank"],
            item["number"],
        )
    )

    if len(parsed) != 49:
        raise RuntimeError(f"Expected 49 weighted numbers from Step 66, got {len(parsed)}.")

    return parsed


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


def ticket_metrics(ticket, score_map):
    numbers = list(ticket)
    scores = [score_map.get(number, 0.0) for number in numbers]

    odd_count = sum(1 for number in numbers if number % 2 == 1)
    even_count = TICKET_SIZE - odd_count

    low_count = sum(1 for number in numbers if number <= 24)
    high_count = TICKET_SIZE - low_count

    ranges = max(numbers) - min(numbers)
    total_sum = sum(numbers)

    decades = set()
    for number in numbers:
        if number <= 9:
            decades.add("01-09")
        elif number <= 19:
            decades.add("10-19")
        elif number <= 29:
            decades.add("20-29")
        elif number <= 39:
            decades.add("30-39")
        else:
            decades.add("40-49")

    consecutive_pairs = sum(
        1 for left, right in zip(numbers, numbers[1:])
        if right - left == 1
    )

    max_gap = max(
        [right - left for left, right in zip(numbers, numbers[1:])] or [0]
    )

    average_score = sum(scores) / len(scores) if scores else 0.0

    return {
        "average_weighted_score": round(average_score, 3),
        "total_weighted_score": round(sum(scores), 3),
        "min_number": min(numbers),
        "max_number": max(numbers),
        "number_range": ranges,
        "sum_numbers": total_sum,
        "odd_count": odd_count,
        "even_count": even_count,
        "low_count": low_count,
        "high_count": high_count,
        "decade_count": len(decades),
        "consecutive_pairs": consecutive_pairs,
        "max_gap": max_gap,
    }


def structural_bonus(metrics):
    bonus = 0.0

    if 2 <= metrics["odd_count"] <= 4:
        bonus += 8.0
    else:
        bonus -= 10.0

    if 2 <= metrics["low_count"] <= 4:
        bonus += 8.0
    else:
        bonus -= 10.0

    if 110 <= metrics["sum_numbers"] <= 190:
        bonus += 7.0
    else:
        bonus -= 8.0

    if metrics["number_range"] >= 24:
        bonus += 7.0
    else:
        bonus -= 8.0

    if metrics["decade_count"] >= 4:
        bonus += 6.0
    elif metrics["decade_count"] == 3:
        bonus += 2.0
    else:
        bonus -= 6.0

    if metrics["consecutive_pairs"] == 0:
        bonus += 4.0
    elif metrics["consecutive_pairs"] == 1:
        bonus += 1.0
    else:
        bonus -= 7.0

    return bonus


def strategy_bonus(strategy, ticket, metrics):
    name = strategy["strategy"]
    bonus = 0.0

    if name == "high_confidence":
        bonus += metrics["average_weighted_score"] * 0.15

    elif name == "diversified_weighted":
        bonus += metrics["decade_count"] * 4.0
        bonus += min(metrics["number_range"], 35) * 0.25

    elif name == "odd_even_balanced":
        if metrics["odd_count"] == 3:
            bonus += 18.0
        elif metrics["odd_count"] in {2, 4}:
            bonus += 8.0
        else:
            bonus -= 25.0

    elif name == "low_high_balanced":
        if metrics["low_count"] == 3:
            bonus += 18.0
        elif metrics["low_count"] in {2, 4}:
            bonus += 8.0
        else:
            bonus -= 25.0

    elif name == "spread_balanced":
        if metrics["number_range"] >= 30:
            bonus += 14.0
        if metrics["decade_count"] >= 4:
            bonus += 10.0
        if metrics["consecutive_pairs"] > 1:
            bonus -= 15.0

    elif name == "conservative_core":
        top_half = sum(1 for number in ticket if number <= 24)
        if top_half:
            bonus += 2.0

    elif name == "exploratory_weighted":
        if metrics["decade_count"] >= 4:
            bonus += 8.0
        if metrics["number_range"] >= 28:
            bonus += 8.0

    return bonus


def max_overlap(ticket, existing_tickets):
    if not existing_tickets:
        return 0
    ticket_set = set(ticket)
    return max(len(ticket_set.intersection(set(other))) for other in existing_tickets)


def overlap_penalty(overlap):
    if overlap >= 5:
        return 80.0
    if overlap == 4:
        return 35.0
    if overlap == 3:
        return 8.0
    return 0.0


def balance_status(metrics, historical_exact_match, max_previous_overlap):
    issues = []

    if historical_exact_match:
        issues.append("точно историческо повторение")

    if not (2 <= metrics["odd_count"] <= 4):
        issues.append("небалансирани четни/нечетни")

    if not (2 <= metrics["low_count"] <= 4):
        issues.append("небалансирани ниски/високи")

    if metrics["number_range"] < 20:
        issues.append("тесен диапазон")

    if metrics["decade_count"] < 3:
        issues.append("малко групи")

    if metrics["consecutive_pairs"] > 1:
        issues.append("много поредни числа")

    if max_previous_overlap >= 5:
        issues.append("много голямо припокриване с друг фиш")
    elif max_previous_overlap == 4:
        issues.append("умерено припокриване с друг фиш")

    if not issues:
        return "добър структурен баланс", "Контролиран статистически фиш."

    if len(issues) <= 2:
        return "умерен риск", "Наблюдение: " + "; ".join(issues)

    return "по-висок структурен риск", "Риск: " + "; ".join(issues)


def combination_score(ticket, strategy, score_map, existing_tickets, historical_set):
    metrics = ticket_metrics(ticket, score_map)
    historical_exact_match = ticket in historical_set
    previous_overlap = max_overlap(ticket, existing_tickets)

    score = metrics["average_weighted_score"]
    score += structural_bonus(metrics)
    score += strategy_bonus(strategy, ticket, metrics)
    score -= overlap_penalty(previous_overlap)

    if historical_exact_match:
        score -= 1000.0

    return score


def select_best_ticket(strategy, ranked_numbers, score_map, existing_tickets, historical_set):
    pool_size = min(strategy["pool_size"], len(ranked_numbers))
    pool = [item["number"] for item in ranked_numbers[:pool_size]]

    best_ticket = None
    best_score = None

    for combo in itertools.combinations(pool, TICKET_SIZE):
        ticket = normalize_ticket(combo)
        if not ticket:
            continue

        if ticket in existing_tickets:
            continue

        score = combination_score(ticket, strategy, score_map, existing_tickets, historical_set)

        if best_score is None or score > best_score:
            best_score = score
            best_ticket = ticket

    if not best_ticket:
        fallback = normalize_ticket(pool[:TICKET_SIZE])
        if not fallback:
            raise RuntimeError(f"Could not build ticket for strategy {strategy['strategy']}.")
        return fallback

    return best_ticket


def build_weighted_ticket_builder():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    ranked_numbers = load_weighted_scores()
    score_map = {
        item["number"]: item["weighted_score_percent"]
        for item in ranked_numbers
    }

    historical_set = load_historical_ticket_set()

    tickets = []
    existing = []

    for ticket_id, strategy in enumerate(TICKET_STRATEGIES, start=1):
        ticket = select_best_ticket(
            strategy=strategy,
            ranked_numbers=ranked_numbers,
            score_map=score_map,
            existing_tickets=existing,
            historical_set=historical_set,
        )

        existing.append(ticket)

        metrics = ticket_metrics(ticket, score_map)
        previous_overlap = max_overlap(ticket, existing[:-1])
        historical_exact_match = ticket in historical_set
        status, risk_note = balance_status(metrics, historical_exact_match, previous_overlap)

        item = {
            "ticket_id": ticket_id,
            "strategy": strategy["strategy"],
            "strategy_label": strategy["label"],
            "numbers": ",".join(str(number) for number in ticket),
            "n1": ticket[0],
            "n2": ticket[1],
            "n3": ticket[2],
            "n4": ticket[3],
            "n5": ticket[4],
            "n6": ticket[5],
            "average_weighted_score": metrics["average_weighted_score"],
            "total_weighted_score": metrics["total_weighted_score"],
            "min_number": metrics["min_number"],
            "max_number": metrics["max_number"],
            "number_range": metrics["number_range"],
            "sum_numbers": metrics["sum_numbers"],
            "odd_count": metrics["odd_count"],
            "even_count": metrics["even_count"],
            "low_count": metrics["low_count"],
            "high_count": metrics["high_count"],
            "decade_count": metrics["decade_count"],
            "consecutive_pairs": metrics["consecutive_pairs"],
            "max_gap": metrics["max_gap"],
            "max_overlap_with_previous": previous_overlap,
            "historical_exact_match": bool(historical_exact_match),
            "balance_status": status,
            "risk_note": risk_note,
            "safe_note": "Статистически генерирана комбинация, не гаранция за печалба.",
            "strategy_description": strategy["description"],
        }

        tickets.append(item)

    fieldnames = [
        "ticket_id",
        "strategy",
        "strategy_label",
        "numbers",
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
        "n6",
        "average_weighted_score",
        "total_weighted_score",
        "min_number",
        "max_number",
        "number_range",
        "sum_numbers",
        "odd_count",
        "even_count",
        "low_count",
        "high_count",
        "decade_count",
        "consecutive_pairs",
        "max_gap",
        "max_overlap_with_previous",
        "historical_exact_match",
        "balance_status",
        "risk_note",
        "safe_note",
        "strategy_description",
    ]

    write_csv(REPORTS_DIR / "v67_weighted_ticket_builder_tickets.csv", tickets, fieldnames)
    write_json(REPORTS_DIR / "v67_weighted_ticket_builder_tickets.json", tickets)

    top_ticket = max(tickets, key=lambda item: item["average_weighted_score"]) if tickets else {}

    summary = {
        "step": "67",
        "name": "Weighted Ticket Builder Integration",
        "source_scores": "reports/v66_weighted_smart_ensemble_scores.csv",
        "tickets_generated": len(tickets),
        "strategies_used": [strategy["strategy"] for strategy in TICKET_STRATEGIES],
        "top_average_weighted_score_ticket_id": top_ticket.get("ticket_id"),
        "top_average_weighted_score": top_ticket.get("average_weighted_score", 0.0),
        "historical_exact_matches": sum(1 for item in tickets if item["historical_exact_match"]),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_reports": [
            "reports/v67_weighted_ticket_builder_summary.json",
            "reports/v67_weighted_ticket_builder_summary.md",
            "reports/v67_weighted_ticket_builder_tickets.csv",
            "reports/v67_weighted_ticket_builder_tickets.json",
            "models/v67/v67_weighted_ticket_builder_model.json",
        ],
        "safe_note": "This is a weighted statistical ticket builder. It is not a гаранция за печалба or a promise of future lottery results.",
    }

    model_payload = {
        "summary": summary,
        "source_top_numbers": ranked_numbers[:25],
        "tickets": tickets,
        "strategy_definitions": TICKET_STRATEGIES,
        "rules": {
            "ticket_size": TICKET_SIZE,
            "number_range": "1..49",
            "source": "Step 66 weighted smart ensemble scores",
            "historical_exact_match_policy": "avoid exact historical draw combinations when historical data can be parsed",
            "portfolio_overlap_policy": "penalize 4+ and strongly penalize 5+ overlaps with previously generated tickets",
        },
        "safe_note": summary["safe_note"],
    }

    write_json(REPORTS_DIR / "v67_weighted_ticket_builder_summary.json", summary)
    write_json(MODELS_DIR / "v67_weighted_ticket_builder_model.json", model_payload)

    md = [
        "# Step 67 — Weighted Ticket Builder Integration",
        "",
        "This report turns Step 66 weighted number scores into a small portfolio of статистическа референция tickets.",
        "",
        "**Important:** These combinations are not predictions and not гаранция за печалбаs.",
        "",
        f"Tickets generated: **{summary['tickets_generated']}**",
        f"Best average претеглена оценка ticket: **#{summary['top_average_weighted_score_ticket_id']}**",
        f"Best average претеглена оценка: **{summary['top_average_weighted_score']}%**",
        f"Historical exact matches: **{summary['historical_exact_matches']}**",
        "",
        "## Generated tickets",
        "",
        "| ID | Strategy | Numbers | Avg score | Odd/Even | Low/High | Range | Status |",
        "|---:|---|---|---:|---|---|---:|---|",
    ]

    for ticket in tickets:
        md.append(
            f"| {ticket['ticket_id']} | {ticket['strategy_label']} | {ticket['numbers']} | "
            f"{ticket['average_weighted_score']}% | {ticket['odd_count']}/{ticket['even_count']} | "
            f"{ticket['low_count']}/{ticket['high_count']} | {ticket['number_range']} | {ticket['balance_status']} |"
        )

    md.extend([
        "",
        "## Safety note",
        "",
        "Lottery draws are random. This step only converts weighted statistical signals into structured референтни комбинации.",
    ])

    (REPORTS_DIR / "v67_weighted_ticket_builder_summary.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    return summary


if __name__ == "__main__":
    result = build_weighted_ticket_builder()
    print("STEP67_OK")
    print("TICKETS_GENERATED", result["tickets_generated"])
    print("TOP_TICKET_ID", result["top_average_weighted_score_ticket_id"])
    print("TOP_AVG_SCORE", result["top_average_weighted_score"])

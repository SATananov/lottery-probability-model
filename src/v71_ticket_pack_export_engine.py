from __future__ import annotations

from pathlib import Path
import csv
import html
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v71"

STEP70_SUMMARY_PATH = REPORTS_DIR / "v70_applied_candidate_portfolio_summary.json"
STEP70_TICKETS_PATH = REPORTS_DIR / "v70_applied_candidate_portfolio_tickets.csv"
STEP70_CHANGES_PATH = REPORTS_DIR / "v70_applied_candidate_portfolio_changes.csv"

SAFE_NOTE_BG = "Статистически reference пакет. Не е прогноза и не е гаранция за печалба."
SAFE_NOTE_EN = "Statistical reference pack only. Not a prediction and not a winning guarantee."


def as_float(value, default=0.0):
    try:
        text = str(value).strip()
        if not text:
            return default
        return float(text.replace("%", "").replace(",", "."))
    except (TypeError, ValueError):
        return default


def as_int(value, default=0):
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


def parse_numbers(row):
    values = []
    for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        value = as_int(row.get(key), None)
        if value is not None:
            values.append(value)

    if len(values) < 6:
        text = str(row.get("numbers", ""))
        for part in text.replace(";", ",").replace("·", ",").replace(" ", ",").split(","):
            value = as_int(part, None)
            if value is not None:
                values.append(value)

    clean = sorted({value for value in values if 1 <= value <= 49})
    if len(clean) != 6:
        return []
    return clean


def load_step70_tickets():
    rows = read_csv_rows(STEP70_TICKETS_PATH)
    if not rows:
        raise FileNotFoundError(
            "Missing reports/v70_applied_candidate_portfolio_tickets.csv. "
            "Run Step 70 first."
        )

    tickets = []

    for index, row in enumerate(rows, start=1):
        numbers = parse_numbers(row)
        if len(numbers) != 6:
            continue

        tickets.append({
            "ticket_id": as_int(row.get("ticket_id"), index),
            "strategy_label": row.get("strategy_label", ""),
            "numbers": numbers,
            "numbers_display": " ".join(f"{number:02d}" for number in numbers),
            "numbers_csv": ",".join(str(number) for number in numbers),
            "average_step66_score": round(as_float(row.get("average_step66_score"), 0.0), 3),
            "odd_count": as_int(row.get("odd_count"), 0),
            "even_count": as_int(row.get("even_count"), 0),
            "low_count": as_int(row.get("low_count"), 0),
            "high_count": as_int(row.get("high_count"), 0),
            "number_range": as_int(row.get("number_range"), 0),
            "sum_numbers": as_int(row.get("sum_numbers"), 0),
            "historical_exact_match": str(row.get("historical_exact_match", "")).lower() in {"true", "1", "yes"},
            "safe_note": SAFE_NOTE_BG,
        })

    if len(tickets) < 6:
        raise RuntimeError(f"Expected at least 6 applied tickets from Step 70, got {len(tickets)}.")

    return tickets


def build_txt(summary, tickets, changes):
    lines = [
        "LOTTERY PROBABILITY MODEL — STEP 71 TICKET PACK",
        "ПАКЕТ ЗА ИГРА — СТАТИСТИЧЕСКИ РЕФЕРЕНТЕН ПАКЕТ",
        "",
        f"Източник: Step 70 приложен кандидат портфейл",
        f"Приложена оценка на портфейла: {summary.get('applied_portfolio_score', 0)} / 100",
        f"Top 20 покритие: {summary.get('applied_top20_coverage', 0)} / 20",
        f"Уникални числа: {summary.get('applied_unique_numbers', 0)}",
        f"Повторени двойки: {summary.get('applied_repeated_pairs', 0)}",
        f"Повторени тройки: {summary.get('applied_repeated_triples', 0)}",
        f"Исторически точни повторения: {summary.get('applied_historical_exact_matches', 0)}",
        "",
        SAFE_NOTE_BG,
        "",
        "ФИШОВЕ",
        "",
    ]

    for ticket in tickets:
        lines.append(
            f"Фиш {ticket['ticket_id']}: {ticket['numbers_display']} "
            f"| оценка {ticket['average_step66_score']} "
            f"| {ticket['strategy_label']}"
        )

    if changes:
        lines.extend(["", "ПРИЛОЖЕНИ ПРОМЕНИ", ""])
        for change in changes:
            lines.append(
                f"Фиш {change.get('ticket_id')}: махнати [{change.get('removed_numbers', '')}], "
                f"добавени [{change.get('added_numbers', '')}]"
            )

    lines.extend(["", SAFE_NOTE_EN, ""])
    return "\n".join(lines)


def build_markdown(summary, tickets, changes):
    lines = [
        "# Step 71 — Пакет за игра",
        "",
        "## Пакет за игра",
        "",
        f"**Приложена оценка на портфейла:** {summary.get('applied_portfolio_score', 0)} / 100",
        f"**Top 20 покритие:** {summary.get('applied_top20_coverage', 0)} / 20",
        f"**Уникални числа:** {summary.get('applied_unique_numbers', 0)}",
        f"**Повторени двойки:** {summary.get('applied_repeated_pairs', 0)}",
        f"**Повторени тройки:** {summary.get('applied_repeated_triples', 0)}",
        f"**Исторически точни повторения:** {summary.get('applied_historical_exact_matches', 0)}",
        "",
        f"**Важно:** {SAFE_NOTE_BG}",
        "",
        "## Фишове",
        "",
        "| Фиш | Числа | Средна Step 66 оценка | Стратегия |",
        "|---:|---|---:|---|",
    ]

    for ticket in tickets:
        lines.append(
            f"| {ticket['ticket_id']} | {ticket['numbers_display']} | "
            f"{ticket['average_step66_score']} | {ticket['strategy_label']} |"
        )

    lines.extend(["", "## Приложени промени", ""])

    if changes:
        lines.extend([
            "| Фиш | Махнати | Добавени | Оригинал | Приложен |",
            "|---:|---|---|---|---|",
        ])
        for change in changes:
            lines.append(
                f"| {change.get('ticket_id')} | {change.get('removed_numbers', '')} | "
                f"{change.get('added_numbers', '')} | {change.get('original_numbers', '')} | "
                f"{change.get('applied_numbers', '')} |"
            )
    else:
        lines.append("Няма приложени промени.")

    lines.extend(["", "## Важна бележка", "", SAFE_NOTE_EN, ""])
    return "\n".join(lines)


def build_html(summary, tickets, changes):
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")

    ticket_rows = []
    for ticket in tickets:
        ticket_rows.append(
            "<tr>"
            f"<td>{ticket['ticket_id']}</td>"
            f"<td class='numbers'>{html.escape(ticket['numbers_display'])}</td>"
            f"<td>{ticket['average_step66_score']}</td>"
            f"<td>{html.escape(ticket['strategy_label'])}</td>"
            "</tr>"
        )

    change_rows = []
    for change in changes:
        change_rows.append(
            "<tr>"
            f"<td>{html.escape(str(change.get('ticket_id', '')))}</td>"
            f"<td>{html.escape(str(change.get('removed_numbers', '')))}</td>"
            f"<td>{html.escape(str(change.get('added_numbers', '')))}</td>"
            f"<td>{html.escape(str(change.get('original_numbers', '')))}</td>"
            f"<td>{html.escape(str(change.get('applied_numbers', '')))}</td>"
            "</tr>"
        )

    changes_html = "\n".join(change_rows) if change_rows else "<tr><td colspan='5'>Няма приложени промени.</td></tr>"

    return f"""<!doctype html>
<html lang="bg">
<head>
  <meta charset="utf-8">
  <title>Step 71 — Пакет за игра</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 32px;
      color: #111;
      background: #fff;
    }}
    .header {{
      border-bottom: 2px solid #111;
      padding-bottom: 12px;
      margin-bottom: 24px;
    }}
    h1 {{
      margin: 0 0 8px 0;
      font-size: 28px;
    }}
    .note {{
      border: 1px solid #999;
      padding: 12px;
      margin: 16px 0;
      background: #f7f7f7;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin: 16px 0;
    }}
    .metric {{
      border: 1px solid #ccc;
      padding: 10px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
    }}
    th, td {{
      border: 1px solid #bbb;
      padding: 8px;
      text-align: left;
    }}
    th {{
      background: #eee;
    }}
    .numbers {{
      font-weight: bold;
      font-size: 18px;
      letter-spacing: 1px;
    }}
    .footer {{
      margin-top: 28px;
      font-size: 12px;
      color: #555;
    }}
    @media print {{
      body {{ margin: 18mm; }}
      .note {{ break-inside: avoid; }}
      table {{ break-inside: auto; }}
      tr {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <div class="header">
    <h1>Пакет за игра — Step 71</h1>
    <div>Източник: Step 70 приложен кандидат портфейл</div>
    <div>Генерирано: {html.escape(generated)}</div>
  </div>

  <div class="note"><strong>Важно:</strong> {html.escape(SAFE_NOTE_BG)}</div>

  <div class="metrics">
    <div class="metric"><strong>Приложена оценка</strong><br>{summary.get('applied_portfolio_score', 0)} / 100</div>
    <div class="metric"><strong>Top 20 покритие</strong><br>{summary.get('applied_top20_coverage', 0)} / 20</div>
    <div class="metric"><strong>Уникални числа</strong><br>{summary.get('applied_unique_numbers', 0)}</div>
    <div class="metric"><strong>Повторени двойки</strong><br>{summary.get('applied_repeated_pairs', 0)}</div>
    <div class="metric"><strong>Повторени тройки</strong><br>{summary.get('applied_repeated_triples', 0)}</div>
    <div class="metric"><strong>Исторически повторения</strong><br>{summary.get('applied_historical_exact_matches', 0)}</div>
  </div>

  <h2>Фишове</h2>
  <table>
    <thead>
      <tr>
        <th>Фиш</th>
        <th>Числа</th>
        <th>Средна Step 66 оценка</th>
        <th>Стратегия</th>
      </tr>
    </thead>
    <tbody>
      {''.join(ticket_rows)}
    </tbody>
  </table>

  <h2>Приложени промени</h2>
  <table>
    <thead>
      <tr>
        <th>Фиш</th>
        <th>Махнати</th>
        <th>Добавени</th>
        <th>Оригинал</th>
        <th>Приложен</th>
      </tr>
    </thead>
    <tbody>
      {changes_html}
    </tbody>
  </table>

  <div class="footer">{html.escape(SAFE_NOTE_EN)}</div>
</body>
</html>
"""


def build_ticket_pack_export():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if not STEP70_SUMMARY_PATH.exists():
        raise FileNotFoundError("Missing reports/v70_applied_candidate_portfolio_summary.json. Run Step 70 first.")

    step70_summary = read_json(STEP70_SUMMARY_PATH)
    tickets = load_step70_tickets()
    changes = read_csv_rows(STEP70_CHANGES_PATH)

    export_rows = []
    for ticket in tickets:
        export_rows.append({
            "ticket_id": ticket["ticket_id"],
            "numbers": ticket["numbers_csv"],
            "numbers_display": ticket["numbers_display"],
            "average_step66_score": ticket["average_step66_score"],
            "strategy_label": ticket["strategy_label"],
            "odd_count": ticket["odd_count"],
            "even_count": ticket["even_count"],
            "low_count": ticket["low_count"],
            "high_count": ticket["high_count"],
            "number_range": ticket["number_range"],
            "sum_numbers": ticket["sum_numbers"],
            "historical_exact_match": ticket["historical_exact_match"],
            "safe_note": ticket["safe_note"],
        })

    write_csv(
        REPORTS_DIR / "v71_ticket_pack.csv",
        export_rows,
        [
            "ticket_id",
            "numbers",
            "numbers_display",
            "average_step66_score",
            "strategy_label",
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

    summary = {
        "step": "71",
        "name": "Export / Print Ticket Pack",
        "source_applied_portfolio": "reports/v70_applied_candidate_portfolio_tickets.csv",
        "source_summary": "reports/v70_applied_candidate_portfolio_summary.json",
        "tickets_exported": len(tickets),
        "changes_included": len(changes),
        "applied_portfolio_score": step70_summary.get("applied_portfolio_score"),
        "applied_top20_coverage": step70_summary.get("applied_top20_coverage"),
        "applied_unique_numbers": step70_summary.get("applied_unique_numbers"),
        "applied_repeated_pairs": step70_summary.get("applied_repeated_pairs"),
        "applied_repeated_triples": step70_summary.get("applied_repeated_triples"),
        "applied_historical_exact_matches": step70_summary.get("applied_historical_exact_matches"),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_reports": [
            "reports/v71_ticket_pack_summary.json",
            "reports/v71_ticket_pack_summary.md",
            "reports/v71_ticket_pack.csv",
            "reports/v71_ticket_pack.json",
            "reports/v71_ticket_pack.txt",
            "reports/v71_ticket_pack_printable.md",
            "reports/v71_ticket_pack_printable.html",
            "models/v71/v71_ticket_pack_export_model.json",
        ],
        "safe_note": SAFE_NOTE_EN,
    }

    pack_json = {
        "summary": summary,
        "tickets": tickets,
        "changes": changes,
        "safe_note_bg": SAFE_NOTE_BG,
        "safe_note_en": SAFE_NOTE_EN,
    }

    write_json(REPORTS_DIR / "v71_ticket_pack_summary.json", summary)
    write_json(REPORTS_DIR / "v71_ticket_pack.json", pack_json)
    write_json(MODELS_DIR / "v71_ticket_pack_export_model.json", pack_json)

    txt = build_txt(step70_summary, tickets, changes)
    markdown = build_markdown(step70_summary, tickets, changes)
    html_text = build_html(step70_summary, tickets, changes)

    (REPORTS_DIR / "v71_ticket_pack.txt").write_text(txt, encoding="utf-8")
    (REPORTS_DIR / "v71_ticket_pack_printable.md").write_text(markdown, encoding="utf-8")
    (REPORTS_DIR / "v71_ticket_pack_summary.md").write_text(markdown, encoding="utf-8")
    (REPORTS_DIR / "v71_ticket_pack_printable.html").write_text(html_text, encoding="utf-8")

    return summary


if __name__ == "__main__":
    result = build_ticket_pack_export()
    print("STEP71_OK")
    print("TICKETS_EXPORTED", result["tickets_exported"])
    print("CHANGES_INCLUDED", result["changes_included"])
    print("APPLIED_SCORE", result["applied_portfolio_score"])

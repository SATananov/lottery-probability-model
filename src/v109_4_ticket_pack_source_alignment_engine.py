from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v109_2_ticket_pack_4line_engine import LINES_PER_TICKET, build_suggested_ticket_cards

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v109_4"
SUMMARY_JSON = REPORTS_DIR / "v109_4_ticket_pack_source_alignment_summary.json"
SUMMARY_MD = REPORTS_DIR / "v109_4_ticket_pack_source_alignment_summary.md"
CHECKLIST_CSV = REPORTS_DIR / "v109_4_ticket_pack_source_alignment_checklist.csv"
MODEL_JSON = MODELS_DIR / "v109_4_ticket_pack_source_alignment_model.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _numbers_key(line: dict[str, Any]) -> tuple[int, ...]:
    return tuple(sorted(int(number) for number in (line.get("numbers") or [])))


def _card_line_count(card: dict[str, Any]) -> int:
    return len(card.get("lines") or [])


def build_step() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    final_cards = build_suggested_ticket_cards(2, package_mode="final_plan_only")
    extended_cards = build_suggested_ticket_cards(3, package_mode="extended")

    checklist: list[dict[str, str]] = []

    def add_check(name: str, passed: bool, details_bg: str, blocking: str = "yes") -> None:
        checklist.append({"check": name, "status": "OK" if passed else "FAIL", "blocking": blocking, "details_bg": details_bg})

    add_check("final_plan_only_has_two_tickets", len(final_cards) == 2, f"final_cards={len(final_cards)}")
    add_check("final_plan_tickets_have_four_lines", all(_card_line_count(card) == LINES_PER_TICKET for card in final_cards), json.dumps([_card_line_count(card) for card in final_cards], ensure_ascii=False))
    add_check("extended_has_three_tickets", len(extended_cards) == 3, f"extended_cards={len(extended_cards)}")
    add_check("extended_tickets_have_four_lines", all(_card_line_count(card) == LINES_PER_TICKET for card in extended_cards), json.dumps([_card_line_count(card) for card in extended_cards], ensure_ascii=False))
    add_check("third_ticket_is_marked_supplementary", len(extended_cards) >= 3 and extended_cards[2].get("package_scope") == "supplementary", f"third_scope={(extended_cards[2].get('package_scope') if len(extended_cards) >= 3 else 'missing')}")

    all_lines = []
    for card in extended_cards:
        all_lines.extend(card.get("lines") or [])
    unique_count = len({_numbers_key(line) for line in all_lines})
    add_check("extended_lines_are_unique", unique_count == len(all_lines), f"unique={unique_count}, total={len(all_lines)}", blocking="no")

    blocking_failures = sum(1 for item in checklist if item["blocking"] == "yes" and item["status"] != "OK")
    status = "TICKET_PACK_SOURCES_ALIGNED" if blocking_failures == 0 else "CHECK_REQUIRED"

    summary = {
        "step": "109.4",
        "name": "Ticket Pack Source Alignment",
        "status": status,
        "blocking_failures": blocking_failures,
        "lines_per_ticket": LINES_PER_TICKET,
        "final_plan_only": {
            "tickets": len(final_cards),
            "total_lines": sum(_card_line_count(card) for card in final_cards),
            "explanation_bg": "Само видимият финален план: 2 фиша по 4 комбинации от 8 реда.",
        },
        "extended_package": {
            "tickets": len(extended_cards),
            "total_lines": sum(_card_line_count(card) for card in extended_cards),
            "explanation_bg": "2 фиша от финалния план + 1 допълващ фиш извън финалната таблица.",
        },
        "checklist": checklist,
        "generated_at_utc": utc_now(),
    }

    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "status", "blocking", "details_bg"])
        writer.writeheader()
        writer.writerows(checklist)

    md_lines = [
        "# Step 109.4 — Ticket Pack Source Alignment",
        "",
        f"- Status: `{status}`",
        f"- Blocking failures: `{blocking_failures}`",
        f"- Само финален план: `{summary['final_plan_only']['tickets']}` фиша / `{summary['final_plan_only']['total_lines']}` комбинации",
        f"- Разширен пакет: `{summary['extended_package']['tickets']}` фиша / `{summary['extended_package']['total_lines']}` комбинации",
        "",
        "## Проверки",
        "",
    ]
    for item in checklist:
        md_lines.append(f"- `{item['status']}` — {item['check']}: {item['details_bg']}")
    SUMMARY_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"STEP_109_4_STATUS {status}")
    print(f"BLOCKING_FAILURES {blocking_failures}")
    print(f"FINAL_PLAN_TICKETS {summary['final_plan_only']['tickets']}")
    print(f"FINAL_PLAN_LINES {summary['final_plan_only']['total_lines']}")
    print(f"EXTENDED_TICKETS {summary['extended_package']['tickets']}")
    print(f"EXTENDED_LINES {summary['extended_package']['total_lines']}")
    return summary


if __name__ == "__main__":
    build_step()

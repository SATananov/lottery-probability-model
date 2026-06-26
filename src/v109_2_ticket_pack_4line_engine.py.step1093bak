from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.v109_sqlite_journal_engine import (
    connect,
    export_csv_mirrors,
    format_numbers,
    initialize_database,
    active_plan_metadata,
    ticket_pack_candidates,
    write_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v109_2"
SUMMARY_JSON = REPORTS_DIR / "v109_2_ticket_pack_4line_journal_summary.json"
SUMMARY_MD = REPORTS_DIR / "v109_2_ticket_pack_4line_journal_summary.md"
CHECKLIST_CSV = REPORTS_DIR / "v109_2_ticket_pack_4line_journal_checklist.csv"
MODEL_JSON = MODELS_DIR / "v109_2_ticket_pack_4line_journal_model.json"

LINES_PER_TICKET = 4
DEFAULT_TICKET_COUNT = 3


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _line_key(numbers: list[int]) -> tuple[int, ...]:
    return tuple(sorted(int(number) for number in numbers))


def _normalize_candidate(item: dict[str, Any], source_group: str, display_role: str | None = None) -> dict[str, Any]:
    nums = [int(number) for number in item.get("numbers", [])]
    nums = sorted(nums)
    return {
        "line_no": int(item.get("line_no") or 0),
        "source_ticket_id": str(item.get("source_ticket_id") or item.get("line_no") or ""),
        "role": display_role or str(item.get("role") or "комбинация"),
        "numbers": nums,
        "numbers_text": format_numbers(nums),
        "decision_score": float(item.get("decision_score") or 0.0),
        "risk_level": str(item.get("risk_level") or ""),
        "source_group": source_group,
        "note": str(item.get("note") or ""),
    }


def _unique_extend(target: list[dict[str, Any]], source: list[dict[str, Any]], seen: set[tuple[int, ...]], limit: int | None = None) -> None:
    for item in source:
        nums = item.get("numbers") or []
        if len(nums) != 6:
            continue
        key = _line_key(nums)
        if key in seen:
            continue
        target.append(item)
        seen.add(key)
        if limit is not None and len(target) >= limit:
            return


def _decorate_card(card_index: int, title: str, subtitle: str, strategy: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
    clean_lines: list[dict[str, Any]] = []
    for index, line in enumerate(lines[:LINES_PER_TICKET], start=1):
        line_copy = dict(line)
        line_copy["line_no"] = index
        clean_lines.append(line_copy)
    return {
        "ticket_no": card_index,
        "title": title,
        "subtitle": subtitle,
        "strategy": strategy,
        "line_count": len(clean_lines),
        "lines": clean_lines,
    }


def build_suggested_ticket_cards(ticket_count: int = DEFAULT_TICKET_COUNT) -> list[dict[str, Any]]:
    """Build user-facing physical ticket cards.

    One physical Bulgarian lottery ticket is treated as four combinations/lines.
    The function returns up to three cards, each with four lines where possible.
    It does not change the database and does not promise any result.
    """
    requested = max(1, min(int(ticket_count or DEFAULT_TICKET_COUNT), DEFAULT_TICKET_COUNT))

    export_candidates = [_normalize_candidate(item, "Финален модел") for item in ticket_pack_candidates("all_export")]
    active_candidates = [_normalize_candidate(item, "Активен план", "активен план") for item in ticket_pack_candidates("active_plan_all_11")]

    seen: set[tuple[int, ...]] = set()
    ordered_export: list[dict[str, Any]] = []
    _unique_extend(ordered_export, export_candidates, seen)

    cards: list[dict[str, Any]] = []

    first_lines = ordered_export[:LINES_PER_TICKET]
    if len(first_lines) < LINES_PER_TICKET:
        _unique_extend(first_lines, active_candidates, seen, LINES_PER_TICKET)
    cards.append(
        _decorate_card(
            1,
            "Фиш 1 — Основен модел",
            "Най-високо класираните редове от финалния пакет.",
            "основен модел",
            first_lines,
        )
    )

    second_lines = ordered_export[LINES_PER_TICKET:LINES_PER_TICKET * 2]
    if len(second_lines) < LINES_PER_TICKET:
        _unique_extend(second_lines, active_candidates, seen, LINES_PER_TICKET)
    cards.append(
        _decorate_card(
            2,
            "Фиш 2 — Резервен модел",
            "Алтернативни редове от резервния/наблюдавания слой.",
            "резервен модел",
            second_lines,
        )
    )

    third_lines: list[dict[str, Any]] = []
    _unique_extend(third_lines, active_candidates, seen, LINES_PER_TICKET)
    if len(third_lines) < LINES_PER_TICKET:
        _unique_extend(third_lines, export_candidates, seen, LINES_PER_TICKET)
    cards.append(
        _decorate_card(
            3,
            "Фиш 3 — Разширено покритие",
            "Допълнителен фиш от активния системен план за по-широк профил.",
            "разширено покритие",
            third_lines,
        )
    )

    return cards[:requested]


def parse_numbers_text(value: str) -> list[int]:
    text = str(value or "").strip()
    for char in [";", "|", "-", "\n", "\t"]:
        text = text.replace(char, ",")
    parts: list[str] = []
    for chunk in text.replace(" ", ",").split(","):
        chunk = chunk.strip()
        if chunk:
            parts.append(chunk)
    numbers: list[int] = []
    for part in parts:
        try:
            numbers.append(int(float(part)))
        except Exception:
            return []
    return sorted(numbers)


def validate_numbers(numbers: list[int]) -> tuple[bool, str]:
    if len(numbers) != 6:
        return False, "Трябва да има точно 6 числа."
    if len(set(numbers)) != 6:
        return False, "В един ред не трябва да има повторени числа."
    if not all(1 <= number <= 49 for number in numbers):
        return False, "Всички числа трябва да са между 1 и 49."
    return True, "OK"


def normalize_cards_from_ui(cards: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    normalized_cards: list[dict[str, Any]] = []
    issues: list[str] = []
    for card in cards:
        clean_lines: list[dict[str, Any]] = []
        for index, line in enumerate(card.get("lines", []), start=1):
            numbers = line.get("numbers") or parse_numbers_text(line.get("numbers_text", ""))
            numbers = sorted(int(number) for number in numbers)
            valid, message = validate_numbers(numbers)
            if not valid:
                issues.append(f"{card.get('title', 'Фиш')} · Комбинация {index}: {message}")
                continue
            line_copy = dict(line)
            line_copy["line_no"] = index
            line_copy["numbers"] = numbers
            line_copy["numbers_text"] = format_numbers(numbers)
            clean_lines.append(line_copy)
        card_copy = dict(card)
        card_copy["lines"] = clean_lines
        card_copy["line_count"] = len(clean_lines)
        normalized_cards.append(card_copy)
        if len(clean_lines) != LINES_PER_TICKET:
            issues.append(f"{card.get('title', 'Фиш')} трябва да има {LINES_PER_TICKET} валидни комбинации.")
    return normalized_cards, issues


def save_ticket_cards_as_played(
    cards: list[dict[str, Any]],
    play_date: str,
    target_draw_date: str,
    target_draw_number: str = "",
    note: str = "",
) -> dict[str, Any]:
    initialize_database()
    cards, issues = normalize_cards_from_ui(cards)
    if issues:
        return {"inserted": 0, "existing": 0, "issues": issues, "ticket_ids": []}

    metadata = active_plan_metadata()
    price = float(metadata.get("price_per_line_eur") or 0.9)
    inserted = 0
    existing = 0
    ticket_ids: list[int] = []
    pack_payload = {
        "play_date": play_date,
        "target_draw_date": target_draw_date,
        "target_draw_number": target_draw_number,
        "cards": [
            {
                "ticket_no": card.get("ticket_no"),
                "strategy": card.get("strategy"),
                "lines": [line.get("numbers") for line in card.get("lines", [])],
            }
            for card in cards
        ],
    }
    pack_key = hashlib.sha256(json.dumps(pack_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]

    with connect() as conn:
        for card in cards:
            lines = card.get("lines", [])
            if len(lines) != LINES_PER_TICKET:
                continue
            ticket_payload = {
                "pack_key": pack_key,
                "ticket_no": card.get("ticket_no"),
                "play_date": play_date,
                "target_draw_date": target_draw_date,
                "target_draw_number": target_draw_number,
                "lines": [line.get("numbers") for line in lines],
            }
            ticket_key = hashlib.sha256(json.dumps(ticket_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:24]
            row = conn.execute("SELECT id FROM played_tickets WHERE ticket_key = ?", (ticket_key,)).fetchone()
            if row:
                existing += 1
                ticket_ids.append(int(row["id"]))
                continue
            total_price = round(price * len(lines), 2)
            full_note = note.strip()
            card_title = str(card.get("title") or f"Фиш {card.get('ticket_no')}")
            card_note = f"Пакет {pack_key}. {card_title}. {full_note}".strip()
            cur = conn.execute(
                """
                INSERT INTO played_tickets(
                    ticket_key, saved_at_utc, play_date, target_draw_date, target_draw_number,
                    mode, plan_id, plan_source, strategy_type, budget_eur, price_per_line_eur,
                    total_price_eur, line_count, status, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_key,
                    utc_now(),
                    play_date,
                    target_draw_date,
                    target_draw_number,
                    "ticket_pack_4_lines",
                    metadata.get("plan_id") or "",
                    card_title,
                    card.get("strategy") or metadata.get("strategy_type") or "",
                    metadata.get("budget_eur") or 0.0,
                    price,
                    total_price,
                    len(lines),
                    "PLAYED_WAITING_RESULT",
                    card_note,
                ),
            )
            ticket_id = int(cur.lastrowid)
            ticket_ids.append(ticket_id)
            for line in lines:
                nums = [int(number) for number in line.get("numbers", [])]
                conn.execute(
                    """
                    INSERT INTO played_ticket_lines(
                        ticket_id, line_no, source_ticket_id, role,
                        n1, n2, n3, n4, n5, n6, numbers_text,
                        price_eur, played, note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ticket_id,
                        int(line.get("line_no") or 0),
                        str(line.get("source_ticket_id") or ""),
                        str(line.get("role") or card.get("strategy") or "комбинация"),
                        nums[0], nums[1], nums[2], nums[3], nums[4], nums[5],
                        format_numbers(nums),
                        price,
                        1,
                        str(line.get("note") or ""),
                    ),
                )
            inserted += 1
    export_csv_mirrors()
    write_artifacts(sync_latest_draw=True, evaluate_open=False)
    return {
        "inserted": inserted,
        "existing": existing,
        "issues": [],
        "ticket_ids": ticket_ids,
        "pack_key": pack_key,
        "tickets": len(cards),
        "lines_per_ticket": LINES_PER_TICKET,
        "total_lines": sum(len(card.get("lines", [])) for card in cards),
        "total_price_eur": round(price * sum(len(card.get("lines", [])) for card in cards), 2),
    }


def build_step_summary() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    initialize_database()
    cards = build_suggested_ticket_cards(DEFAULT_TICKET_COUNT)

    checks: list[dict[str, Any]] = []

    def add_check(name: str, passed: bool, details_bg: str, blocking: str = "yes") -> None:
        checks.append({"check": name, "status": "OK" if passed else "FAIL", "blocking": blocking, "details_bg": details_bg})

    add_check("cards_created", len(cards) >= 1, f"cards={len(cards)}")
    add_check("three_ticket_suggestion_available", len(cards) == DEFAULT_TICKET_COUNT, f"cards={len(cards)}")
    add_check("each_ticket_has_four_lines", all(len(card.get("lines", [])) == LINES_PER_TICKET for card in cards), json.dumps([len(card.get("lines", [])) for card in cards], ensure_ascii=False))
    all_numbers_valid = True
    for card in cards:
        for line in card.get("lines", []):
            valid, _ = validate_numbers(line.get("numbers") or [])
            all_numbers_valid = all_numbers_valid and valid
    add_check("all_suggested_lines_valid", all_numbers_valid, "валидирани са 6 числа между 1 и 49 без повторение")

    blocking_failures = sum(1 for item in checks if item["blocking"] == "yes" and item["status"] != "OK")
    status = "TICKET_PACK_READY" if blocking_failures == 0 else "CHECK_REQUIRED"

    summary = {
        "step": "109.2",
        "name": "Ticket Pack = 4 Lines",
        "status": status,
        "blocking_failures": blocking_failures,
        "ticket_count": len(cards),
        "lines_per_ticket": LINES_PER_TICKET,
        "total_suggested_lines": sum(len(card.get("lines", [])) for card in cards),
        "suggested_cards": cards,
        "safe_note_bg": "Един реален фиш се третира като 4 комбинации. Това е дневник и организация на играта, не гаранция за печалба.",
        "generated_at_utc": utc_now(),
        "checks": checks,
    }

    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps({
        "step": summary["step"],
        "status": summary["status"],
        "blocking_failures": summary["blocking_failures"],
        "ticket_count": summary["ticket_count"],
        "lines_per_ticket": summary["lines_per_ticket"],
        "total_suggested_lines": summary["total_suggested_lines"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "status", "blocking", "details_bg"])
        writer.writeheader()
        writer.writerows(checks)

    lines = [
        "# Step 109.2 — Ticket Pack = 4 Lines",
        "",
        f"- Status: `{summary['status']}`",
        f"- Blocking failures: `{summary['blocking_failures']}`",
        f"- Фишове: `{summary['ticket_count']}`",
        f"- Комбинации във фиш: `{summary['lines_per_ticket']}`",
        f"- Общо предложени комбинации: `{summary['total_suggested_lines']}`",
        "",
        "## Проверки",
        "",
    ]
    for check in checks:
        lines.append(f"- `{check['status']}` — {check['check']}: {check['details_bg']}")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return summary


def print_summary(summary: dict[str, Any]) -> None:
    print(f"STEP_109_2_STATUS {summary.get('status')}")
    print(f"BLOCKING_FAILURES {summary.get('blocking_failures')}")
    print(f"TICKETS {summary.get('ticket_count')}")
    print(f"LINES_PER_TICKET {summary.get('lines_per_ticket')}")
    print(f"TOTAL_LINES {summary.get('total_suggested_lines')}")

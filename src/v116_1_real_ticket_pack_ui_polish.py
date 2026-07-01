from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

LINES_PER_PHYSICAL_TICKET = 4

STATUS_LABELS_BG = {
    "PLAYED_WAITING_RESULT": "Игран — чака резултат",
    "PLAYED": "Игран",
    "PLANNED": "Планиран",
    "EVALUATED": "Проверен",
    "WAITING_RESULT": "Чака резултат",
    "PENDING": "Чака резултат",
    "CHECK_REQUIRED": "Нужна е проверка",
}

ROLE_LABELS_BG = {
    "main": "основна комбинация",
    "main line": "основна комбинация",
    "основна комбинация": "основна комбинация",
    "reserve": "резервна комбинация",
    "резервна комбинация": "резервна комбинация",
    "active plan": "активен план",
    "активен план": "активен план",
    "watch only": "само наблюдение",
    "само наблюдение": "само наблюдение",
}


def status_label(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "—"
    return STATUS_LABELS_BG.get(raw, raw.replace("_", " ").title())


def role_label(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "комбинация"
    return ROLE_LABELS_BG.get(raw.lower(), raw)


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        text = str(value).strip()
        if not text:
            return default
        return int(float(text))
    except Exception:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        text = str(value).replace("\u00a0", " ").replace("EUR", "").replace("€", "").strip()
        if not text:
            return default
        text = text.replace(" ", "").replace(",", ".")
        keep = "".join(ch for ch in text if ch.isdigit() or ch in ".-")
        if keep in {"", ".", "-"}:
            return default
        return float(keep)
    except Exception:
        return default


def format_eur(value: Any) -> str:
    return f"{safe_float(value):,.2f} EUR".replace(",", " ")


def numbers_from_any(value: Any) -> list[int]:
    if isinstance(value, list):
        raw_values = value
    else:
        text = str(value or "").replace(";", ",").replace("|", ",").replace("-", ",")
        raw_values = [part for part in text.replace(" ", ",").split(",") if str(part).strip()]
    numbers: list[int] = []
    for item in raw_values:
        number = safe_int(item, 0)
        if 1 <= number <= 49 and number not in numbers:
            numbers.append(number)
    return numbers[:6]


def numbers_text(numbers: Iterable[Any]) -> str:
    values = [safe_int(value) for value in numbers]
    values = [value for value in values if 1 <= value <= 49]
    return ", ".join(str(value) for value in values) if values else "—"


def ticket_display_name(position: int) -> str:
    return f"Фиш {position}"


def normalize_ticket_rows(tickets: Any, lines: Any, results: Any) -> list[dict[str, Any]]:
    """Return user-facing ticket cards from pandas-like DataFrames.

    The function deliberately keeps database ids as internal metadata only.
    UI pages should show physical ticket order (Фиш 1, Фиш 2, ...), not raw ids.
    """
    if tickets is None or getattr(tickets, "empty", True):
        return []

    cards: list[dict[str, Any]] = []
    for index, (_, ticket) in enumerate(tickets.iterrows(), start=1):
        ticket_id = safe_int(ticket.get("id"), 0)
        if lines is not None and not getattr(lines, "empty", True) and "ticket_id" in lines.columns:
            ticket_lines = lines[lines["ticket_id"].apply(safe_int) == ticket_id].copy()
        else:
            ticket_lines = []
        if hasattr(ticket_lines, "empty") and not ticket_lines.empty and "line_no" in ticket_lines.columns:
            ticket_lines = ticket_lines.sort_values("line_no")

        clean_lines: list[dict[str, Any]] = []
        if hasattr(ticket_lines, "iterrows"):
            for _, line in ticket_lines.iterrows():
                number_values = []
                for n in range(1, 7):
                    if f"n{n}" in line:
                        number_values.append(line.get(f"n{n}"))
                if len(number_values) == 6 and all(safe_int(value) for value in number_values):
                    nums = [safe_int(value) for value in number_values]
                else:
                    nums = numbers_from_any(line.get("numbers_text"))
                clean_lines.append({
                    "line_no": safe_int(line.get("line_no"), len(clean_lines) + 1),
                    "role": role_label(line.get("role")),
                    "numbers": nums,
                    "numbers_text": numbers_text(nums),
                })

        if results is not None and not getattr(results, "empty", True) and "ticket_id" in results.columns:
            ticket_results = results[results["ticket_id"].apply(safe_int) == ticket_id].copy()
        else:
            ticket_results = []
        result_summary = "Чака проверка"
        best_hits = 0
        total_hits = 0
        matched = "—"
        if hasattr(ticket_results, "empty") and not ticket_results.empty:
            result_row = ticket_results.iloc[-1]
            best_hits = safe_int(result_row.get("best_hits"), 0)
            total_hits = safe_int(result_row.get("total_hits"), 0)
            matched = str(result_row.get("matched_numbers_text") or "—")
            result_summary = f"Проверен · най-добра комбинация {best_hits} числа · общо попадения {total_hits}"

        cards.append({
            "display_name": ticket_display_name(index),
            "internal_id": ticket_id,
            "play_date": str(ticket.get("play_date") or "—"),
            "target_draw_date": str(ticket.get("target_draw_date") or "—"),
            "target_draw_number": str(ticket.get("target_draw_number") or "—"),
            "status": status_label(ticket.get("status")),
            "total_price_eur": safe_float(ticket.get("total_price_eur"), 0.0),
            "total_price_label": format_eur(ticket.get("total_price_eur")),
            "line_count": len(clean_lines) or safe_int(ticket.get("line_count"), 0),
            "note": str(ticket.get("note") or ""),
            "lines": clean_lines,
            "result_summary": result_summary,
            "best_hits": best_hits,
            "total_hits": total_hits,
            "matched_numbers_text": matched,
        })
    return cards


def build_copy_text(cards: list[dict[str, Any]]) -> str:
    if not cards:
        return "Няма записани реално играни фишове."
    parts: list[str] = []
    for card in cards:
        parts.append(f"{card.get('display_name')} — {card.get('line_count', 0)} комбинации — {card.get('total_price_label', '—')}")
        for line in card.get("lines", []):
            parts.append(f"  Ред {line.get('line_no')}: {line.get('numbers_text')}")
        parts.append("")
    return "\n".join(parts).strip()


def build_ui_snapshot(cards: list[dict[str, Any]]) -> dict[str, Any]:
    ticket_count = len(cards)
    line_count = sum(safe_int(card.get("line_count"), 0) for card in cards)
    total_price = sum(safe_float(card.get("total_price_eur"), 0.0) for card in cards)
    bad_cards = [card for card in cards if safe_int(card.get("line_count"), 0) not in {0, LINES_PER_PHYSICAL_TICKET}]
    return {
        "status": "REAL_TICKET_PACK_UI_POLISH_READY",
        "ticket_count": ticket_count,
        "line_count": line_count,
        "lines_per_physical_ticket": LINES_PER_PHYSICAL_TICKET,
        "total_price_eur": round(total_price, 2),
        "bad_count": len(bad_cards),
        "user_facing_rules_bg": [
            "В страниците се показва реалният фиш като 4 комбинации.",
            "Скриват се сурови технически полета от основния изглед.",
            "Фишовете се номерират като Фиш 1, Фиш 2, Фиш 3 вместо със сурови database ids.",
            "Добавен е текст за удобно преписване/копиране на реалния пакет.",
        ],
    }

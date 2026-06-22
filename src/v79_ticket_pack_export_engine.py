from __future__ import annotations

from pathlib import Path
import ast
import csv
import hashlib
import json
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
V79_MODELS_DIR = MODELS_DIR / "v79"

V78_SUMMARY_JSON = REPORTS_DIR / "v78_final_play_plan_summary.json"
V78_SELECTED_TICKETS_CSV = REPORTS_DIR / "v78_selected_ticket_plan.csv"
V78_PLAY_ACTIONS_CSV = REPORTS_DIR / "v78_play_plan_actions.csv"
V78_PLAY_WARNINGS_CSV = REPORTS_DIR / "v78_play_plan_warnings.csv"

V79_SUMMARY_JSON = REPORTS_DIR / "v79_ticket_pack_export_summary.json"
V79_SUMMARY_MD = REPORTS_DIR / "v79_ticket_pack_export_summary.md"
V79_EXPORT_TICKETS_CSV = REPORTS_DIR / "v79_export_ticket_pack.csv"
V79_EXECUTION_CHECKLIST_CSV = REPORTS_DIR / "v79_execution_checklist.csv"
V79_COPY_TEXT_TXT = REPORTS_DIR / "v79_ticket_pack_copy_text.txt"
V79_EXPORT_JSON = REPORTS_DIR / "v79_ticket_pack_export.json"
V79_MODEL_JSON = V79_MODELS_DIR / "v79_ticket_pack_export_model.json"

SAFE_NOTE = (
    "Step 79 подготвя финалния пакет за копиране, печат и дисциплинирано изпълнение. "
    "Това не е гаранция за печалба и не променя случайността на лотарията."
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        text = str(value).strip().replace("%", "").replace(",", ".")
        if not text:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value).strip().replace(",", ".")
        if not text:
            return default
        return int(float(text))
    except (TypeError, ValueError):
        return default


def _parse_numbers(value: Any) -> list[int]:
    if isinstance(value, list):
        return sorted(_as_int(item) for item in value)
    text = str(value or "").strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return sorted(_as_int(item) for item in parsed)
    except (SyntaxError, ValueError):
        pass
    return sorted(_as_int(item) for item in re.findall(r"\d+", text))


def _numbers_display(value: Any) -> str:
    numbers = _parse_numbers(value)
    return ", ".join(f"{number:02d}" for number in numbers)


def _numbers_compact(value: Any) -> str:
    numbers = _parse_numbers(value)
    return ",".join(str(number) for number in numbers)


def _state_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _export_status(role: str, risk: str) -> str:
    if role == "основен фиш":
        return "за игра"
    if role == "резервен фиш":
        return "резерва"
    if role == "само наблюдение":
        return "само наблюдение"
    if role == "изключен":
        return "изключен"
    if "висок" in risk:
        return "изключен"
    return "за преглед"


def _execution_note(row: dict[str, Any]) -> str:
    role = str(row.get("plan_role", ""))
    risk = str(row.get("risk_level", ""))
    score = _as_float(row.get("decision_score"))

    notes: list[str] = []
    if role == "основен фиш":
        notes.append("включен във финалния пакет")
    elif role == "резервен фиш":
        notes.append("пази като резервен вариант")
    elif role == "само наблюдение":
        notes.append("не влиза в основния пакет")
    elif role == "изключен":
        notes.append("не използвай във финалния пакет")
    else:
        notes.append("изисква ръчна проверка")

    if score < 60:
        notes.append("оценката е под силната зона")
    if risk in {"повишен риск", "висок риск"}:
        notes.append("има повишено внимание")

    return "; ".join(notes)


def build_ticket_pack_export_center() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    V79_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    v78_summary = _read_json(V78_SUMMARY_JSON, {})
    selected_rows = _read_csv(V78_SELECTED_TICKETS_CSV)
    action_rows = _read_csv(V78_PLAY_ACTIONS_CSV)
    warning_rows = _read_csv(V78_PLAY_WARNINGS_CSV)

    selected_rows = sorted(
        selected_rows,
        key=lambda row: (
            _as_int(row.get("plan_rank"), 999),
            -_as_float(row.get("decision_score")),
            str(row.get("ticket_id")),
        ),
    )

    export_rows: list[dict[str, Any]] = []
    for row in selected_rows:
        role = str(row.get("plan_role", ""))
        risk = str(row.get("risk_level", ""))
        export_rows.append({
            "export_order": _as_int(row.get("plan_rank"), len(export_rows) + 1),
            "ticket_id": row.get("ticket_id", ""),
            "numbers_display": _numbers_display(row.get("numbers")),
            "numbers_compact": _numbers_compact(row.get("numbers")),
            "plan_role": role,
            "export_status": _export_status(role, risk),
            "decision_score": round(_as_float(row.get("decision_score")), 3),
            "risk_level": risk,
            "execution_note": _execution_note(row),
            "safe_note": SAFE_NOTE,
        })

    active_rows = [row for row in export_rows if row["export_status"] == "за игра"]
    reserve_rows = [row for row in export_rows if row["export_status"] == "резерва"]
    watch_rows = [row for row in export_rows if row["export_status"] == "само наблюдение"]
    excluded_rows = [row for row in export_rows if row["export_status"] == "изключен"]

    checklist = [
        {
            "order": 1,
            "check_item": "Провери дали използваш последния clean checkpoint",
            "status": "задължително",
            "details": "Не смесвай стари отчети с нов финален план.",
            "safe_note": SAFE_NOTE,
        },
        {
            "order": 2,
            "check_item": "Играй само основните фишове, ако няма ръчна причина за промяна",
            "status": "задължително",
            "details": f"Основни фишове в пакета: {len(active_rows)}.",
            "safe_note": SAFE_NOTE,
        },
        {
            "order": 3,
            "check_item": "Резервните фишове не се добавят автоматично",
            "status": "контрол",
            "details": "Резервите са за сравнение или замяна, не за хаотично разширяване.",
            "safe_note": SAFE_NOTE,
        },
        {
            "order": 4,
            "check_item": "След реален тираж първо сравни резултата срещу пакета",
            "status": "след тираж",
            "details": "Преди Add Draw save използвай checker/result сравнение, после обнови dataset-а.",
            "safe_note": SAFE_NOTE,
        },
        {
            "order": 5,
            "check_item": "Не приемай анализа като обещание",
            "status": "важно",
            "details": "Това е статистически workflow, а не предсказване на печеливш тираж.",
            "safe_note": SAFE_NOTE,
        },
    ]

    copy_lines = [
        "ФИНАЛЕН ПАКЕТ — Step 79",
        "Важно: статистическа организация, не гаранция за печалба.",
        "",
        "ОСНОВНИ ФИШОВЕ:",
    ]

    if active_rows:
        for row in active_rows:
            copy_lines.append(
                f"Фиш {row['ticket_id']}: {row['numbers_display']} "
                f"(оценка {row['decision_score']}, риск: {row['risk_level']})"
            )
    else:
        copy_lines.append("Няма основни фишове.")

    copy_lines.extend(["", "РЕЗЕРВНИ ФИШОВЕ:"])
    if reserve_rows:
        for row in reserve_rows:
            copy_lines.append(
                f"Фиш {row['ticket_id']}: {row['numbers_display']} "
                f"(оценка {row['decision_score']}, риск: {row['risk_level']})"
            )
    else:
        copy_lines.append("Няма резервни фишове.")

    copy_lines.extend(["", "КОНТРОЛНИ БЕЛЕЖКИ:"])
    for item in checklist:
        copy_lines.append(f"{item['order']}. {item['check_item']} — {item['details']}")

    V79_COPY_TEXT_TXT.write_text("\n".join(copy_lines) + "\n", encoding="utf-8")

    summary = {
        "step": 79,
        "name": "Експорт и изпълнение",
        "status": "OK",
        "valid_draws": v78_summary.get("valid_draws", 0),
        "latest_date": v78_summary.get("latest_date", ""),
        "latest_draw_no": v78_summary.get("latest_draw_no", ""),
        "latest_numbers": v78_summary.get("latest_numbers", ""),
        "source_step": "78",
        "next_step": "74",
        "candidate_tickets": len(export_rows),
        "play_tickets": len(active_rows),
        "reserve_tickets": len(reserve_rows),
        "watch_tickets": len(watch_rows),
        "excluded_tickets": len(excluded_rows),
        "checklist_items": len(checklist),
        "warning_items_from_step78": len(warning_rows),
        "action_items_from_step78": len(action_rows),
        "best_ticket_id": active_rows[0].get("ticket_id", "") if active_rows else "",
        "best_numbers": active_rows[0].get("numbers_compact", "") if active_rows else "",
        "copy_text_path": str(V79_COPY_TEXT_TXT.relative_to(ROOT)).replace("\\", "/"),
        "safe_note": SAFE_NOTE,
    }

    payload = {
        "summary": summary,
        "export_ticket_pack": export_rows,
        "execution_checklist": checklist,
        "copy_text": copy_lines,
        "source_v78_summary": v78_summary,
        "state_hash": "",
    }
    state_hash = _state_hash(payload)
    summary["state_hash"] = state_hash
    payload["state_hash"] = state_hash

    _write_csv(V79_EXPORT_TICKETS_CSV, export_rows, [
        "export_order",
        "ticket_id",
        "numbers_display",
        "numbers_compact",
        "plan_role",
        "export_status",
        "decision_score",
        "risk_level",
        "execution_note",
        "safe_note",
    ])
    _write_csv(V79_EXECUTION_CHECKLIST_CSV, checklist, [
        "order",
        "check_item",
        "status",
        "details",
        "safe_note",
    ])
    _write_json(V79_SUMMARY_JSON, summary)
    _write_json(V79_EXPORT_JSON, {
        "summary": summary,
        "export_ticket_pack": export_rows,
        "execution_checklist": checklist,
        "copy_text": copy_lines,
    })
    _write_json(V79_MODEL_JSON, payload)

    md = [
        "# Step 79 — Експорт и изпълнение",
        "",
        f"Статус: **{summary['status']}**",
        f"Валидни тиражи: **{summary['valid_draws']}**",
        f"Последен тираж: **{summary['latest_date']}** — **{summary['latest_numbers']}**",
        f"Кандидат фишове: **{summary['candidate_tickets']}**",
        f"Фишове за игра: **{summary['play_tickets']}**",
        f"Резервни фишове: **{summary['reserve_tickets']}**",
        f"Фишове само за наблюдение: **{summary['watch_tickets']}**",
        "",
        "**Важно:** Step 79 е слой за експорт, копиране и дисциплина. Не е гаранция за печалба.",
        "",
        "## Пакет за игра",
        "",
        "| Ред | Фиш | Числа | Роля | Статус | Оценка | Риск | Бележка |",
        "|---:|---:|---|---|---|---:|---|---|",
    ]

    for row in export_rows:
        md.append(
            f"| {row['export_order']} | {row['ticket_id']} | {row['numbers_display']} | "
            f"{row['plan_role']} | {row['export_status']} | {row['decision_score']} | "
            f"{row['risk_level']} | {row['execution_note']} |"
        )

    md.extend([
        "",
        "## Checklist",
        "",
        "| Ред | Проверка | Статус | Детайли |",
        "|---:|---|---|---|",
    ])

    for row in checklist:
        md.append(f"| {row['order']} | {row['check_item']} | {row['status']} | {row['details']} |")

    V79_SUMMARY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


def load_summary() -> dict[str, Any]:
    payload = _read_json(V79_SUMMARY_JSON, {})
    if isinstance(payload, dict) and payload:
        return payload
    return build_ticket_pack_export_center()

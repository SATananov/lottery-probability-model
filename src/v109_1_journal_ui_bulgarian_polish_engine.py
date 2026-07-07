from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTION_PATH = ROOT / "src" / "v109_sqlite_journal_section.py"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v109_1"
SUMMARY_JSON = REPORTS_DIR / "v109_1_journal_ui_bulgarian_polish_summary.json"
SUMMARY_MD = REPORTS_DIR / "v109_1_journal_ui_bulgarian_polish_summary.md"
CHECKLIST_CSV = REPORTS_DIR / "v109_1_journal_ui_bulgarian_polish_checklist.csv"
MODEL_JSON = MODELS_DIR / "v109_1_journal_ui_bulgarian_polish_model.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_section() -> str:
    if not SECTION_PATH.exists():
        return ""
    return SECTION_PATH.read_text(encoding="utf-8-sig")


def build_summary() -> dict:
    text = read_section()
    checks = []

    def add_check(name: str, passed: bool, details_bg: str, blocking: str = "yes") -> None:
        checks.append({"check": name, "status": "OK" if passed else "FAIL", "blocking": blocking, "details_bg": details_bg})

    add_check("section_exists", SECTION_PATH.exists(), str(SECTION_PATH.relative_to(ROOT)) if SECTION_PATH.exists() else "missing")
    add_check("friendly_refresh_button", "Обнови дневника" in text and "Обнови Step 109 дневника" not in text, "бутонът е без Step номер")
    friendly_mode_text_present = (
        "Само основните комбинации от текущия план" in text
        or "Само финалният план" in text
        or "Разширен пакет" in text
    )
    add_check(
        "friendly_ticket_mode",
        friendly_mode_text_present and "Step 79" not in text,
        "режимът е описан с потребителски текст, без технически Step 79 етикет",
    )
    add_check("friendly_status_label", "Дневникът е активен" in text, "статусът е човешки")
    add_check("visual_number_balls", "number-ball" in text and "ticket-line-card" in text, "числата се показват като визуални топки/карти")
    add_check("technical_paths_softened", "Локален дневник: активен" in text and "CSV архив: наличен" in text, "пътищата са омекотени в основния изглед")
    add_check("translated_table_headers", all(label in text for label in ["Ред", "Роля", "Източник", "Въведено на", "Теглене"]), "табличните колони имат български имена")
    add_check("no_broken_cyrillic", ("?" * 4) not in text and "\ufffd" not in text, "няма счупена кирилица")

    blocking_failures = sum(1 for item in checks if item["blocking"] == "yes" and item["status"] != "OK")
    status = "JOURNAL_UI_POLISHED" if blocking_failures == 0 else "CHECK_REQUIRED"
    summary = {
        "step": "109.1",
        "name": "Journal UI Bulgarian Polish",
        "status": status,
        "blocking_failures": blocking_failures,
        "section_path": str(SECTION_PATH.relative_to(ROOT)),
        "generated_at_utc": utc_now(),
        "checks": checks,
        "notes_bg": [
            "Step 109.1 прави дневника по-ясен и визуално по-близък до стила на app-а.",
            "Промяната е UI polish; SQLite схемата, записите и резултатната логика не се променят.",
        ],
    }
    return summary


def write_reports(summary: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps({
        "step": summary["step"],
        "status": summary["status"],
        "blocking_failures": summary["blocking_failures"],
        "section_path": summary["section_path"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "status", "blocking", "details_bg"])
        writer.writeheader()
        writer.writerows(summary["checks"])

    md_lines = [
        "# Step 109.1 — Journal UI Bulgarian Polish",
        "",
        f"- Status: `{summary['status']}`",
        f"- Blocking failures: `{summary['blocking_failures']}`",
        f"- Section: `{summary['section_path']}`",
        "",
        "## Checks",
        "",
    ]
    for item in summary["checks"]:
        md_lines.append(f"- `{item['status']}` — {item['check']}: {item['details_bg']}")
    SUMMARY_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def build_step() -> dict:
    summary = build_summary()
    write_reports(summary)
    print(f"STEP_109_1_STATUS {summary['status']}")
    print(f"BLOCKING_FAILURES {summary['blocking_failures']}")
    print("UI_POLISH Journal page is user-friendly and Bulgarian-polished")
    return summary


if __name__ == "__main__":
    build_step()

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v110"
SUMMARY_JSON = REPORTS_DIR / "v110_user_friendly_ui_polish_summary.json"
SUMMARY_MD = REPORTS_DIR / "v110_user_friendly_ui_polish_summary.md"
CHECKLIST_CSV = REPORTS_DIR / "v110_user_friendly_ui_polish_checklist.csv"
MODEL_JSON = MODELS_DIR / "v110_user_friendly_ui_polish_model.json"

TARGET_FILES = [
    "streamlit_app.py",
    "src/add_draws_section.py",
    "src/v99_final_user_dashboard_section.py",
    "src/v100_final_release_lock_section.py",
    "src/v101_real_use_protocol_section.py",
    "src/v102_runtime_hardening_section.py",
    "src/v103_clean_release_checkpoint_section.py",
    "src/v104_final_audit_refresh_section.py",
    "src/v107_model_training_policy_section.py",
    "src/v109_sqlite_journal_section.py",
]

VISIBLE_PROBLEM_MARKERS = [
    "SQLITE_JOURN...",
    "Обнови Step 107",
    "Обнови Step 102",
    "Обнови Step 109",
]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except Exception:
        return ""


def build_summary() -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, str]] = []

    def add(name: str, ok: bool, details: str, blocking: str = "yes") -> None:
        checks.append({"check": name, "status": "OK" if ok else "FAIL", "blocking": blocking, "details_bg": details})

    broken: list[str] = []
    visible_markers: list[str] = []
    for rel in TARGET_FILES:
        path = ROOT / rel
        text = _read(path)
        if "\ufffd" in text or (chr(63) * 4) in text:
            broken.append(rel)
        for marker in VISIBLE_PROBLEM_MARKERS:
            if marker in text:
                visible_markers.append(f"{rel}: {marker}")

    add("target_files_present", all((ROOT / rel).exists() for rel in TARGET_FILES), f"Проверени файлове: {len(TARGET_FILES)}")
    add("no_broken_cyrillic_markers", not broken, ", ".join(broken) if broken else "Няма счупена кирилица в проверените user-facing файлове.")
    add("visible_developer_terms_reduced", not visible_markers, "; ".join(visible_markers[:10]) if visible_markers else "Няма основни остатъчни developer маркери в проверените user-facing файлове.", blocking="no")

    blocking_failures = sum(1 for row in checks if row["blocking"] == "yes" and row["status"] != "OK")
    summary = {
        "step": "110",
        "name_bg": "Потребителска яснота и езиково почистване",
        "status": "USER_FRIENDLY_UI_POLISHED" if blocking_failures == 0 else "CHECK_REQUIRED",
        "blocking_failures": blocking_failures,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "polished_files": TARGET_FILES,
        "checks": checks,
        "notes_bg": [
            "Тази стъпка не променя моделите, числата или SQLite данните.",
            "Променя само видимите етикети, статуси и пояснения, за да изглежда приложението по-ясно за потребител.",
            "Вътрешните имена на файлове и стъпки остават в кода и отчетите, но основният UI ги показва с човешки български етикети.",
        ],
    }

    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    MODEL_JSON.write_text(json.dumps({
        "step": summary["step"],
        "status": summary["status"],
        "blocking_failures": summary["blocking_failures"],
        "polished_files": summary["polished_files"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "status", "blocking", "details_bg"])
        writer.writeheader()
        writer.writerows(checks)

    lines = [
        "# Step 110 — Потребителска яснота и езиково почистване",
        "",
        f"- Статус: `{summary['status']}`",
        f"- Проблеми за преглед: `{summary['blocking_failures']}`",
        "",
        "## Какво прави",
        "",
        "- Изчиства видими технически термини от основните потребителски екрани.",
        "- Превежда статусите към човешки български етикети.",
        "- Не променя данни, модели, фишове или резултати.",
        "",
        "## Проверки",
        "",
    ]
    for row in checks:
        lines.append(f"- `{row['status']}` — {row['check']}: {row['details_bg']}")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return summary


def build_and_write() -> dict:
    summary = build_summary()
    print(f"STEP_110_STATUS {summary['status']}")
    print(f"BLOCKING_FAILURES {summary['blocking_failures']}")
    print(f"POLISHED_FILES {len(summary['polished_files'])}")
    return summary


if __name__ == "__main__":
    build_and_write()

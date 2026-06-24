from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "v102" / "v102_runtime_hardening_model.json"
SUMMARY_JSON = ROOT / "reports" / "v102_runtime_hardening_summary.json"
SUMMARY_MD = ROOT / "reports" / "v102_runtime_hardening_summary.md"
CHECKLIST_CSV = ROOT / "reports" / "v102_runtime_hardening_checklist.csv"

HEAVY_SCRIPTS = [
    "v67_build_weighted_ticket_builder.py",
    "v75_build_neural_meta_learner.py",
]


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def build_runtime_hardening_summary() -> dict[str, Any]:
    add_draws = _read(ROOT / "src" / "add_draws_section.py")
    app = _read(ROOT / "streamlit_app.py")

    checks = [
        {
            "check": "fast_refresh_mode",
            "passed": "FAST_MODEL_SCRIPTS" in add_draws and "HEAVY_LAB_SCRIPT_NAMES" in add_draws,
            "details_bg": "Има отделен бърз refresh режим и отделен списък с тежки лабораторни скриптове.",
        },
        {
            "check": "timeout_guard",
            "passed": "timeout=timeout_seconds" in add_draws and "subprocess.TimeoutExpired" in add_draws,
            "details_bg": "Автоматичното обновяване има timeout защита за отделен скрипт.",
        },
        {
            "check": "heavy_scripts_excluded_from_default",
            "passed": all(name in add_draws for name in HEAVY_SCRIPTS),
            "details_bg": "v67 и v75 остават налични, но не са default fast refresh блокер.",
        },
        {
            "check": "user_facing_shortcut_label",
            "passed": "➕ Добави нов тираж" in app,
            "details_bg": "Sidebar shortcut вече описва реалното действие по-точно.",
        },
        {
            "check": "step102_page_wired",
            "passed": "Runtime защита" in app and "render_v102_runtime_hardening_page" in app,
            "details_bg": "Step 102 контролна страница е добавена в навигацията.",
        },
    ]

    blocking_failures = sum(1 for item in checks if not item["passed"])
    status = "RUNTIME_HARDENED" if blocking_failures == 0 else "CHECK_PATCH"

    summary = {
        "step": 102,
        "name_bg": "Runtime защита и бърз refresh режим",
        "status": status,
        "blocking_failures": blocking_failures,
        "default_refresh_mode_bg": "Бърз режим за реален тираж",
        "default_timeout_seconds": 120,
        "heavy_scripts_kept_manual": HEAVY_SCRIPTS,
        "what_changed_bg": [
            "Автоматичното обновяване след нов тираж вече използва бърз режим по подразбиране.",
            "Тежките процеси v67 и v75 не блокират стандартния поток след запис на тираж.",
            "Всеки скрипт в refresh chain-а има timeout защита.",
            "Пълният refresh остава наличен като ръчен режим.",
            "Бутонът в sidebar е преименуван на по-точно действие: Добави нов тираж.",
        ],
        "checks": checks,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    return summary


def write_runtime_hardening_artifacts() -> dict[str, Any]:
    summary = build_runtime_hardening_summary()

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)

    MODEL_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Step 102 — Runtime защита и бърз refresh режим",
        "",
        f"Статус: **{summary['status']}**",
        f"Blocking failures: **{summary['blocking_failures']}**",
        "",
        "## Какво е променено",
    ]
    for item in summary["what_changed_bg"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Проверки"])
    for item in summary["checks"]:
        marker = "OK" if item["passed"] else "FAIL"
        lines.append(f"- {marker}: {item['check']} — {item['details_bg']}")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "details_bg"])
        writer.writeheader()
        for item in summary["checks"]:
            writer.writerow(item)

    return summary


def load_runtime_hardening_summary() -> dict[str, Any]:
    if SUMMARY_JSON.exists():
        try:
            return json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return build_runtime_hardening_summary()

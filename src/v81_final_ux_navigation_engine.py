from __future__ import annotations

from pathlib import Path
import ast
import csv
import json
from datetime import datetime, timezone
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
V81_MODELS_DIR = MODELS_DIR / "v81"

SUMMARY_JSON = REPORTS_DIR / "v81_final_ux_navigation_summary.json"
SUMMARY_MD = REPORTS_DIR / "v81_final_ux_navigation_summary.md"
GROUPS_CSV = REPORTS_DIR / "v81_navigation_groups.csv"
PAGES_CSV = REPORTS_DIR / "v81_navigation_page_audit.csv"
LABELS_CSV = REPORTS_DIR / "v81_streamlit_label_audit.csv"
MODEL_JSON = V81_MODELS_DIR / "v81_final_ux_navigation_model.json"

SAFE_NOTE = (
    "Step 81 подрежда финалната навигация и проверява UX структурата на приложението. "
    "Това е организационен и визуален контролен слой, не прогноза и не гаранция за печалба."
)

EXPECTED_FINAL_GROUPS = [
    "🏠 Начало и отчети",
    "🎫 Фишове и генератори",
    "📊 Исторически анализи",
    "🧠 Модели и обучение",
    "⚖️ Тегла и портфолио",
    "✅ Финален план за игра",
    "🛡️ Система и контрол",
]

FINAL_FLOW_LABELS = [
    "Обяснимост и валидация",
    "Решение и препоръка",
    "Финален план",
    "Експорт и изпълнение",
    "Финален системен одит",
    "Финален UX контрол",
    "Контрол на синхрона",
]

SYSTEM_CONTROL_EXPECTED_ORDER = [
    "Обновяване на анализите",
    "Финален системен одит",
    "Финален UX контрол",
    "Контрол на синхрона",
]


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _dedent(text: str) -> str:
    lines = text.splitlines()
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return text
    indents = [len(line) - len(line.lstrip()) for line in non_empty]
    min_indent = min(indents)
    return "\n".join(line[min_indent:] if len(line) >= min_indent else line for line in lines)


def _extract_navigation_groups(app_text: str) -> dict[str, list[str]]:
    start_marker = "# STEP64_GROUPED_NAVIGATION_START"
    end_marker = "# STEP64_GROUPED_NAVIGATION_END"
    if start_marker not in app_text or end_marker not in app_text:
        return {}
    block = app_text.split(start_marker, 1)[1].split(end_marker, 1)[0]
    assignment_start = block.find("navigation_groups =")
    if assignment_start < 0:
        return {}
    literal_part = block[assignment_start:]
    stop = literal_part.find("\n    used_navigation_pages")
    if stop >= 0:
        literal_part = literal_part[:stop]
    try:
        module = ast.parse(_dedent(literal_part))
        for node in module.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "navigation_groups":
                        value = ast.literal_eval(node.value)
                        return {str(k): [str(item) for item in v] for k, v in value.items()}
    except Exception:
        return {}
    return {}


def _extract_literal_page_keys(app_text: str) -> set[str]:
    keys: set[str] = set()
    try:
        tree = ast.parse(app_text)
    except SyntaxError:
        return keys
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if not any(isinstance(target, ast.Name) and target.id == "pages" for target in node.targets):
                continue
            if isinstance(node.value, ast.Dict):
                for key in node.value.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        keys.add(key.value)
    return keys


def build_final_ux_navigation_center() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    V81_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    streamlit_path = ROOT / "streamlit_app.py"
    app_text = streamlit_path.read_text(encoding="utf-8-sig") if streamlit_path.exists() else ""
    groups = _extract_navigation_groups(app_text)
    literal_page_keys = _extract_literal_page_keys(app_text)
    group_rows: list[dict[str, Any]] = []
    page_rows: list[dict[str, Any]] = []
    label_rows: list[dict[str, Any]] = []
    seen_pages: dict[str, list[str]] = {}
    for group_order, (group_name, pages) in enumerate(groups.items(), start=1):
        group_rows.append({
            "group_order": group_order,
            "group_name": group_name,
            "pages_count": len(pages),
            "expected_group": group_name in EXPECTED_FINAL_GROUPS,
            "status": "OK" if group_name in EXPECTED_FINAL_GROUPS and pages else "Провери",
            "safe_note": SAFE_NOTE,
        })
        for page_order, page in enumerate(pages, start=1):
            seen_pages.setdefault(page, []).append(group_name)
            page_rows.append({
                "group_name": group_name,
                "page_order": page_order,
                "page_label": page,
                "literal_page_key_found": page in literal_page_keys or page in app_text,
                "duplicate_groups": " | ".join(seen_pages.get(page, [])),
                "status": "OK" if (page in literal_page_keys or page in app_text) else "Провери",
                "safe_note": SAFE_NOTE,
            })
    duplicates = {page: group_list for page, group_list in seen_pages.items() if len(group_list) > 1}
    expected_group_missing = [group for group in EXPECTED_FINAL_GROUPS if group not in groups]
    for label in FINAL_FLOW_LABELS:
        count = app_text.count(label)
        label_rows.append({
            "label": label,
            "count_in_streamlit_app": count,
            "status": "OK" if count >= 1 else "Провери",
            "safe_note": SAFE_NOTE,
        })
    system_group_pages = groups.get("🛡️ Система и контрол", [])
    system_order_ok = all(label in system_group_pages for label in SYSTEM_CONTROL_EXPECTED_ORDER)
    if system_order_ok:
        actual_positions = [system_group_pages.index(label) for label in SYSTEM_CONTROL_EXPECTED_ORDER]
        system_order_ok = actual_positions == sorted(actual_positions)
    issues = []
    issues.extend([f"Липсва навигационна група: {group}" for group in expected_group_missing])
    issues.extend([f"Повторена страница: {page}" for page in duplicates])
    if not system_order_ok:
        issues.append("Системната група не е в очаквания ред: обновяване -> Step 80 -> Step 81 -> Step 74")
    for row in page_rows:
        if row["status"] != "OK":
            issues.append(f"Страница без открит ключ: {row['page_label']}")
    for row in label_rows:
        if row["status"] != "OK":
            issues.append(f"Липсва Streamlit label: {row['label']}")
    summary = {
        "step": "81",
        "name": "Финален UX контрол",
        "status": "OK" if not issues else "Има нужда от преглед",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "groups_count": len(groups),
        "navigation_pages_count": sum(len(pages) for pages in groups.values()),
        "literal_page_keys_detected": len(literal_page_keys),
        "expected_groups_missing": expected_group_missing,
        "duplicate_pages_count": len(duplicates),
        "system_control_order_ok": system_order_ok,
        "issues_found": len(issues),
        "issues_preview": issues[:25],
        "generated_reports": [
            "reports/v81_final_ux_navigation_summary.json",
            "reports/v81_final_ux_navigation_summary.md",
            "reports/v81_navigation_groups.csv",
            "reports/v81_navigation_page_audit.csv",
            "reports/v81_streamlit_label_audit.csv",
            "models/v81/v81_final_ux_navigation_model.json",
        ],
        "safe_note": SAFE_NOTE,
    }
    _write_csv(GROUPS_CSV, group_rows, ["group_order", "group_name", "pages_count", "expected_group", "status", "safe_note"])
    _write_csv(PAGES_CSV, page_rows, ["group_name", "page_order", "page_label", "literal_page_key_found", "duplicate_groups", "status", "safe_note"])
    _write_csv(LABELS_CSV, label_rows, ["label", "count_in_streamlit_app", "status", "safe_note"])
    _write_json(SUMMARY_JSON, summary)
    _write_json(MODEL_JSON, {"summary": summary, "groups": group_rows, "pages": page_rows, "labels": label_rows, "navigation_groups": groups})
    md = [
        "# Step 81 — Финален UX контрол",
        "",
        f"Статус: **{summary['status']}**",
        f"Навигационни групи: **{summary['groups_count']}**",
        f"Страници в групите: **{summary['navigation_pages_count']}**",
        f"Повторени страници: **{summary['duplicate_pages_count']}**",
        f"Системен ред OK: **{summary['system_control_order_ok']}**",
        f"Намерени проблеми: **{summary['issues_found']}**",
        "",
        "**Важно:** Step 81 е UX/навигационен контрол. Той не е прогноза и не е гаранция за печалба.",
        "",
        "## Финални групи",
        "",
        "| Ред | Група | Страници | Статус |",
        "|---:|---|---:|---|",
    ]
    for row in group_rows:
        md.append(f"| {row['group_order']} | {row['group_name']} | {row['pages_count']} | {row['status']} |")
    if issues:
        md.extend(["", "## Нужда от преглед", ""])
        for issue in issues[:25]:
            md.append(f"- {issue}")
    else:
        md.extend(["", "## Финален резултат", "", "Навигацията е подредена и основните UX labels са налични."])
    SUMMARY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = build_final_ux_navigation_center()
    print("STEP81_BUILD_OK")
    print("STATUS", result.get("status"))
    print("GROUPS_CHECKED", result.get("groups_count"))
    print("NAVIGATION_PAGES", result.get("navigation_pages_count"))
    print("DUPLICATE_PAGES", result.get("duplicate_pages_count"))
    print("SYSTEM_ORDER_OK", result.get("system_control_order_ok"))
    print("ISSUES_FOUND", result.get("issues_found"))

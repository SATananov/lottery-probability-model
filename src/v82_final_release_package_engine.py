from __future__ import annotations

from pathlib import Path
import csv
import json
from datetime import datetime, timezone
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
DATA_DIR = ROOT / "data"
V82_MODELS_DIR = MODELS_DIR / "v82"

SUMMARY_JSON = REPORTS_DIR / "v82_final_release_summary.json"
SUMMARY_MD = REPORTS_DIR / "v82_final_release_summary.md"
MANIFEST_CSV = REPORTS_DIR / "v82_release_file_manifest.csv"
CHECKLIST_CSV = REPORTS_DIR / "v82_release_readiness_checklist.csv"
EXCLUSIONS_CSV = REPORTS_DIR / "v82_clean_zip_exclusion_plan.csv"
MODEL_JSON = V82_MODELS_DIR / "v82_final_release_package_model.json"

SAFE_NOTE = (
    "Step 82 е финален release и clean package контролен слой. "
    "Той подготвя приложението за стабилен ZIP checkpoint и не е прогноза или гаранция за печалба."
)

DATASET_EXPECTATIONS = {
    "data/historical_draws.csv": {
        "rows": 10058,
        "rows_2026": 49,
        "latest_date": "2026-06-21",
        "latest_numbers": "6,13,16,19,42,44",
    },
    "data/v40_normalized_draw_events.csv": {
        "rows": 10058,
        "rows_2026": 49,
        "latest_date": "2026-06-21",
        "latest_numbers": "6,13,16,19,42,44",
    },
    "data/v41_canonical_draw_events.csv": {
        "rows": 10058,
        "rows_2026": 49,
        "latest_date": "2026-06-21",
        "latest_numbers": "6,13,16,19,42,44",
    },
}

REQUIRED_RELEASE_FILES = [
    "streamlit_app.py",
    "README.md",
    "requirements.txt",
    ".gitignore",
    "data/historical_draws.csv",
    "data/v40_normalized_draw_events.csv",
    "data/v41_canonical_draw_events.csv",
    "models/model_registry.json",
    "models/v79/v79_ticket_pack_export_model.json",
    "models/v80/v80_final_system_audit_model.json",
    "models/v81/v81_final_ux_navigation_model.json",
    "reports/v79_ticket_pack_export_summary.json",
    "reports/v80_final_system_audit_summary.json",
    "reports/v81_final_ux_navigation_summary.json",
    "scripts/v79_build_ticket_pack_export_center.py",
    "scripts/v80_build_final_system_audit_center.py",
    "scripts/v81_build_final_ux_navigation_center.py",
    "scripts/v82_build_final_release_package_center.py",
    "src/v79_ticket_pack_export_engine.py",
    "src/v80_final_system_audit_engine.py",
    "src/v81_final_ux_navigation_engine.py",
    "src/v82_final_release_package_engine.py",
]

UNWANTED_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    ".ipynb_checkpoints",
    ".vscode/.ropeproject",
    ".mypy_cache",
    ".ruff_cache",
    ".DS_Store",
    "Thumbs.db",
]

ZIP_EXCLUSION_PLAN = [
    {"pattern": ".git/", "reason": "Git history не се включва в clean release ZIP."},
    {"pattern": "__pycache__/", "reason": "Python cache артефакт."},
    {"pattern": ".pytest_cache/", "reason": "Test cache артефакт."},
    {"pattern": ".ipynb_checkpoints/", "reason": "Jupyter cache артефакт."},
    {"pattern": "*.zip", "reason": "Не допускаме nested ZIP вътре в release ZIP."},
    {"pattern": "*.tmp", "reason": "Временни файлове."},
    {"pattern": "*.temp", "reason": "Временни файлове."},
    {"pattern": "*.bak", "reason": "Backup файлове."},
    {"pattern": "apply_step*.py", "reason": "Helper patch файловете се чистят преди commit/release."},
    {"pattern": "fix_*.py / apply_*.ps1", "reason": "Еднократни помощни скриптове не са част от продукта."},
]

FINAL_SYNC_EXPECTATIONS = [
    {"name": "82 -> 74", "step": "82", "expected": ["82", "74"]},
    {"name": "81 -> 82 -> 74", "step": "81", "expected": ["81", "82", "74"]},
    {"name": "79 -> 80 -> 81 -> 82 -> 74", "step": "79", "expected": ["79", "80", "81", "82", "74"]},
    {"name": "75 -> 76 -> 77 -> 78 -> 79 -> 80 -> 81 -> 82 -> 74", "step": "75", "expected": ["75", "76", "77", "78", "79", "80", "81", "82", "74"]},
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


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _detect_csv_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            return [str(item) for item in (reader.fieldnames or [])]
    except Exception:
        return []


def _normalize_numbers(row: dict[str, str]) -> str:
    candidate_sets = [
        ["n1", "n2", "n3", "n4", "n5", "n6"],
        ["number_1", "number_2", "number_3", "number_4", "number_5", "number_6"],
        ["num1", "num2", "num3", "num4", "num5", "num6"],
    ]
    for keys in candidate_sets:
        if all(key in row and str(row.get(key, "")).strip() for key in keys):
            try:
                return ",".join(str(int(float(str(row[key]).strip()))) for key in keys)
            except Exception:
                return ",".join(str(row.get(key, "")).strip() for key in keys)
    if "numbers" in row and str(row.get("numbers", "")).strip():
        raw = str(row.get("numbers", "")).strip()
        cleaned = raw.replace("[", "").replace("]", "").replace(";", ",").replace(" ", "")
        return cleaned
    return ""


def _detect_date(row: dict[str, str]) -> str:
    for key in ["date", "draw_date", "Дата", "data"]:
        if key in row and str(row.get(key, "")).strip():
            return str(row.get(key, "")).strip()[:10]
    year = str(row.get("year", row.get("Година", ""))).strip()
    month = str(row.get("month", row.get("Месец", ""))).strip()
    day = str(row.get("day", row.get("Ден", ""))).strip()
    if year and month and day:
        try:
            return f"{int(float(year)):04d}-{int(float(month)):02d}-{int(float(day)):02d}"
        except Exception:
            return ""
    return ""


def _dataset_stats(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "exists": path.exists(),
        "rows": 0,
        "rows_2026": 0,
        "latest_date": "",
        "latest_numbers": "",
        "parse_ok": False,
    }
    if not path.exists():
        return result
    rows: list[dict[str, str]] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = [dict(row) for row in reader]
    except Exception as exc:
        result["error"] = str(exc)
        return result
    result["parse_ok"] = True
    result["rows"] = len(rows)
    for row in rows:
        detected_date = _detect_date(row)
        if detected_date.startswith("2026-"):
            result["rows_2026"] += 1
    dated_rows = [(row, _detect_date(row)) for row in rows]
    dated_rows = [(row, date) for row, date in dated_rows if date]
    if dated_rows:
        row, date = sorted(dated_rows, key=lambda item: item[1])[-1]
        result["latest_date"] = date
        result["latest_numbers"] = _normalize_numbers(row)
    return result


RELEASE_MANIFEST_INCLUDE_ROOTS = [
    ".gitignore",
    "streamlit_app.py",
    "README.md",
    "requirements.txt",
    "configs",
    "data",
    "src",
    "scripts",
    "models",
    "reports",
]

RELEASE_EXCLUDED_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ipynb_checkpoints",
    ".mypy_cache",
    ".ruff_cache",
    ".vscode/.ropeproject",
}

RELEASE_EXCLUDED_FILE_NAMES = {
    ".DS_Store",
    "Thumbs.db",
}

RELEASE_EXCLUDED_SUFFIXES = {
    ".zip",
    ".pyc",
    ".pyo",
    ".tmp",
    ".temp",
    ".bak",
    ".backup",
    ".patch",
}


def _is_release_excluded(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/").strip("/")
    lower = normalized.lower()
    parts = normalized.split("/")
    name = parts[-1] if parts else lower

    if any(part in RELEASE_EXCLUDED_DIR_NAMES for part in parts):
        return True

    if normalized in RELEASE_EXCLUDED_DIR_NAMES:
        return True

    if name in RELEASE_EXCLUDED_FILE_NAMES:
        return True

    if any(lower.endswith(suffix) for suffix in RELEASE_EXCLUDED_SUFFIXES):
        return True

    helper_prefixes = ("apply_", "fix_", "patch_")
    helper_suffixes = (".py", ".ps1")
    if name.startswith(helper_prefixes) and lower.endswith(helper_suffixes):
        return True

    return False


def _file_manifest_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for item in RELEASE_MANIFEST_INCLUDE_ROOTS:
        path = ROOT / item

        if path.is_file():
            rel = path.relative_to(ROOT).as_posix()
            if _is_release_excluded(rel):
                continue
            rows.append({
                "path": rel,
                "kind": "file",
                "size_bytes": path.stat().st_size,
                "release_relevant": True,
                "note": "Included in release manifest",
            })

        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if not child.is_file():
                    continue

                rel = child.relative_to(ROOT).as_posix()
                if _is_release_excluded(rel):
                    continue

                rows.append({
                    "path": rel,
                    "kind": "file",
                    "size_bytes": child.stat().st_size,
                    "release_relevant": True,
                    "note": "Included in release manifest",
                })

    return rows

def _quality_scan() -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    issues: list[str] = []

    if (ROOT / "gitignore").exists():
        rows.append({
            "path": "gitignore",
            "matched_patterns": "legacy_gitignore_name",
            "status": "Преименувай на .gitignore",
            "safe_note": SAFE_NOTE,
        })
        issues.append("Legacy root gitignore exists. Use .gitignore instead.")

    if not (ROOT / ".gitignore").exists():
        rows.append({
            "path": ".gitignore",
            "matched_patterns": "missing_gitignore",
            "status": "Липсва",
            "safe_note": SAFE_NOTE,
        })
        issues.append("Missing .gitignore file.")

    for row in _file_manifest_rows():
        rel = str(row.get("path", ""))
        if _is_release_excluded(rel):
            rows.append({
                "path": rel,
                "matched_patterns": "excluded_release_artifact",
                "status": "Изключи от release manifest",
                "safe_note": SAFE_NOTE,
            })
            issues.append(f"Excluded artifact leaked into release manifest: {rel}")

    return rows, issues

def build_final_release_package_center() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    V82_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    issues: list[str] = []
    checklist_rows: list[dict[str, Any]] = []

    for rel_path in REQUIRED_RELEASE_FILES:
        exists = (ROOT / rel_path).exists()
        checklist_rows.append({
            "check": f"Required file: {rel_path}",
            "status": "OK" if exists else "Липсва",
            "details": "Наличен" if exists else "Файлът липсва",
            "safe_note": SAFE_NOTE,
        })
        if not exists:
            issues.append(f"Липсва release файл: {rel_path}")

    dataset_results: dict[str, dict[str, Any]] = {}
    for rel_path, expected in DATASET_EXPECTATIONS.items():
        stats = _dataset_stats(ROOT / rel_path)
        dataset_results[rel_path] = stats
        status = "OK"
        details: list[str] = []
        if not stats.get("exists"):
            status = "Липсва"
            details.append("dataset липсва")
        elif not stats.get("parse_ok"):
            status = "Провери"
            details.append("CSV parse проблем")
        for key, expected_value in expected.items():
            actual = stats.get(key)
            if str(actual) != str(expected_value):
                status = "Провери"
                details.append(f"{key}: expected {expected_value}, actual {actual}")
        checklist_rows.append({
            "check": f"Dataset expectation: {rel_path}",
            "status": status,
            "details": "; ".join(details) if details else "10058 rows / 49 rows за 2026 / latest draw OK",
            "safe_note": SAFE_NOTE,
        })
        if status != "OK":
            issues.append(f"Dataset expectation failed: {rel_path} — {'; '.join(details)}")

    for rel_path in [
        "reports/v80_final_system_audit_summary.json",
        "reports/v81_final_ux_navigation_summary.json",
    ]:
        summary = _read_json(ROOT / rel_path)
        status = str(summary.get("status", ""))
        issues_found = int(summary.get("issues_found", 999)) if str(summary.get("issues_found", "")).isdigit() else summary.get("issues_found", 999)
        ok = status == "OK" and int(issues_found) == 0
        checklist_rows.append({
            "check": f"Upstream audit OK: {rel_path}",
            "status": "OK" if ok else "Провери",
            "details": f"status={status}; issues_found={issues_found}",
            "safe_note": SAFE_NOTE,
        })
        if not ok:
            issues.append(f"Upstream audit not OK: {rel_path}")

    streamlit_text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8-sig") if (ROOT / "streamlit_app.py").exists() else ""
    required_labels = [
        "Финален системен одит",
        "Финален UX контрол",
        "Финален release пакет",
        "Контрол на синхрона",
    ]
    for label in required_labels:
        count = streamlit_text.count(label)
        ok = count >= 1
        checklist_rows.append({
            "check": f"Streamlit label: {label}",
            "status": "OK" if ok else "Липсва",
            "details": f"count={count}",
            "safe_note": SAFE_NOTE,
        })
        if not ok:
            issues.append(f"Липсва Streamlit label: {label}")

    quality_rows, quality_issues = _quality_scan()
    issues.extend(quality_issues)
    manifest_rows = _file_manifest_rows()
    exclusion_rows = [{**row, "safe_note": SAFE_NOTE} for row in ZIP_EXCLUSION_PLAN]

    _write_csv(MANIFEST_CSV, manifest_rows, ["path", "kind", "size_bytes", "release_relevant", "note"])
    _write_csv(CHECKLIST_CSV, checklist_rows, ["check", "status", "details", "safe_note"])
    _write_csv(EXCLUSIONS_CSV, exclusion_rows, ["pattern", "reason", "safe_note"])

    total_release_size = sum(int(row.get("size_bytes", 0)) for row in manifest_rows)
    summary = {
        "step": "82",
        "name": "Финален release пакет",
        "status": "OK" if not issues else "Има нужда от преглед",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "required_files_checked": len(REQUIRED_RELEASE_FILES),
        "datasets_checked": len(DATASET_EXPECTATIONS),
        "manifest_files_count": len(manifest_rows),
        "manifest_size_bytes": total_release_size,
        "checklist_items": len(checklist_rows),
        "unwanted_release_files": len(quality_rows),
        "sync_expectations": FINAL_SYNC_EXPECTATIONS,
        "issues_found": len(issues),
        "issues_preview": issues[:30],
        "dataset_results": dataset_results,
        "generated_reports": [
            "reports/v82_final_release_summary.json",
            "reports/v82_final_release_summary.md",
            "reports/v82_release_file_manifest.csv",
            "reports/v82_release_readiness_checklist.csv",
            "reports/v82_clean_zip_exclusion_plan.csv",
            "models/v82/v82_final_release_package_model.json",
        ],
        "safe_note": SAFE_NOTE,
    }
    _write_json(SUMMARY_JSON, summary)
    _write_json(MODEL_JSON, {
        "summary": summary,
        "checklist": checklist_rows,
        "dataset_results": dataset_results,
        "clean_zip_exclusion_plan": exclusion_rows,
    })

    md = [
        "# Step 82 — Финален release пакет",
        "",
        f"Статус: **{summary['status']}**",
        f"Проверени задължителни файлове: **{summary['required_files_checked']}**",
        f"Проверени datasets: **{summary['datasets_checked']}**",
        f"Файлове в release manifest: **{summary['manifest_files_count']}**",
        f"Нежелани release файлове: **{summary['unwanted_release_files']}**",
        f"Намерени проблеми: **{summary['issues_found']}**",
        "",
        "## Очаквана финална sync логика",
        "",
        "- 82 -> 74",
        "- 81 -> 82 -> 74",
        "- 79 -> 80 -> 81 -> 82 -> 74",
        "- 75 -> 76 -> 77 -> 78 -> 79 -> 80 -> 81 -> 82 -> 74",
        "",
        "## Clean ZIP принцип",
        "",
        "Release ZIP трябва да съдържа активното приложение, datasets, models, reports, scripts и src, но без Git history, cache, backup, temp и helper patch файлове.",
        "",
        "**Важно:** Step 82 е release контролен слой. Той не е прогноза и не е гаранция за печалба.",
    ]
    if issues:
        md.extend(["", "## Елементи за преглед", ""])
        md.extend([f"- {issue}" for issue in issues[:50]])
    SUMMARY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = build_final_release_package_center()
    print("STEP82_BUILD_OK")
    print("STATUS", result.get("status"))
    print("REQUIRED_FILES_CHECKED", result.get("required_files_checked"))
    print("DATASETS_CHECKED", result.get("datasets_checked"))
    print("MANIFEST_FILES", result.get("manifest_files_count"))
    print("UNWANTED_RELEASE_FILES", result.get("unwanted_release_files"))
    print("ISSUES_FOUND", result.get("issues_found"))

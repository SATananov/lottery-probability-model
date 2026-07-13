from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

ROOT_DOC_MOVES = {
    "ADVANCED_METHODS.md": "docs/ADVANCED_METHODS.md",
    "AUTHORSHIP_AND_TOOLING.md": "docs/AUTHORSHIP_AND_TOOLING.md",
    "PROJECT_CONTEXT.md": "docs/PROJECT_CONTEXT.md",
    "README_UI.md": "docs/README_UI.md",
}
CURRENT_METADATA = {
    "CLEAN_ZIP_MANIFEST_STEP151.md",
    "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP151.md",
}
TEXT_SUFFIXES = {
    ".md", ".py", ".json", ".csv", ".txt", ".yml", ".yaml", ".toml",
    ".ini", ".cfg", ".ps1", ".bat", ".sql", ".html", ".css", ".js", ".ipynb",
}
SKIP_PREFIXES = (
    ".git/", ".venv/", "venv/", ".r-lib/", "reports/runtime/",
    "data/user_journal_exports/",
)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}


def _signature(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def latest_draw_state(root: Path = ROOT) -> dict[str, Any]:
    path = root / "data/historical_draws.csv"
    if not path.is_file():
        return {"ok": False, "reason": "missing_historical_draws"}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {"ok": False, "reason": "empty_historical_draws"}
    row = rows[-1]
    numbers = [int(row[f"n{i}"]) for i in range(1, 7)]
    draw_number = int(row.get("draw_number") or row.get("draw_no") or 0)
    year = int(row.get("year") or str(row.get("date", ""))[:4] or 0)
    return {
        "ok": True,
        "row_count": len(rows),
        "date": row.get("date", ""),
        "year": year,
        "draw_number": draw_number,
        "draw_key": f"{year}-{draw_number}" if year and draw_number else "",
        "numbers": numbers,
        "numbers_text": ", ".join(str(number) for number in numbers),
        "source": row.get("source", ""),
    }


def step148_state(root: Path = ROOT) -> dict[str, Any]:
    status = _read_json(root / "models/v148_prospective_forward_test_status.json")
    return {
        "status": status.get("status"),
        "protocol_id": status.get("protocol_id"),
        "eligible_settled_draws": status.get("eligible_settled_draws"),
        "target_settled_draws": status.get("target_settled_draws"),
        "remaining_draws": status.get("remaining_draws"),
        "active_lock_id": status.get("active_lock_id"),
        "active_expected_draw_key": status.get("active_expected_draw_key"),
        "production_promotion_approved": status.get("production_promotion_approved"),
    }


def legacy_root_manifests(root: Path = ROOT) -> list[str]:
    found: list[str] = []
    for pattern in (
        "CLEAN_ZIP_MANIFEST_STEP*.md",
        "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP*.md",
    ):
        for path in root.glob(pattern):
            if path.name not in CURRENT_METADATA:
                found.append(path.name)
    return sorted(set(found))


def stale_root_docs(root: Path = ROOT) -> list[str]:
    return sorted(name for name in ROOT_DOC_MOVES if (root / name).exists())


def missing_documentation(root: Path = ROOT) -> list[str]:
    expected = ["docs/README.md", "docs/STEP_HISTORY.md", *ROOT_DOC_MOVES.values()]
    return sorted(rel for rel in expected if not (root / rel).is_file())


def _iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root).as_posix()
        if any(rel.startswith(prefix) for prefix in SKIP_PREFIXES):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        yield path, rel


def stale_document_references(root: Path = ROOT) -> list[dict[str, Any]]:
    patterns = {
        name: re.compile(rf"(?<!docs/){re.escape(name)}")
        for name in ROOT_DOC_MOVES
    }
    failures: list[dict[str, Any]] = []
    for path, rel in _iter_text_files(root):
        if rel in {
            "release-manifest.json",
            "models/v151_repository_root_cleanup_policy.json",
            "src/v151_repository_root_cleanup_engine.py",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        for name, pattern in patterns.items():
            for match in pattern.finditer(text):
                failures.append({
                    "path": rel,
                    "line": text.count("\n", 0, match.start()) + 1,
                    "reference": name,
                })
    return failures


def root_inventory(root: Path = ROOT) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        name = path.name
        if name == ".git":
            category = "local_git_metadata"
        elif path.is_dir():
            category = "project_directory"
        elif name in {"README.md", "release-manifest.json"}:
            category = "root_project_metadata"
        elif name in CURRENT_METADATA:
            category = "current_release_metadata"
        elif name in {"app.py", "streamlit_app.py"}:
            category = "application_entrypoint"
        elif name.lower().endswith(".bat"):
            category = "windows_launcher"
        elif name.startswith("train_") or name in {
            "predict_next_draw.py", "audit_dataset.py", "run_advanced_backtest.py",
            "show_advanced_recommendations.py",
        }:
            category = "operator_or_training_entrypoint"
        elif path.suffix.lower() in {".ico", ".png"}:
            category = "application_asset"
        elif path.suffix.lower() == ".md":
            category = "root_markdown"
        else:
            category = "root_support_file"
        rows.append({
            "name": name,
            "type": "directory" if path.is_dir() else "file",
            "category": category,
            "size_bytes": "" if path.is_dir() else path.stat().st_size,
        })
    return rows


def readme_checks(root: Path, draw: dict[str, Any], forward: dict[str, Any]) -> dict[str, bool]:
    readme_path = root / "README.md"
    guide_path = root / "docs/README_UI.md"
    readme = readme_path.read_text(encoding="utf-8-sig") if readme_path.is_file() else ""
    guide = guide_path.read_text(encoding="utf-8-sig") if guide_path.is_file() else ""
    progress = f"{forward.get('eligible_settled_draws')}/{forward.get('target_settled_draws')}"
    return {
        "readme_latest_date": draw.get("date") in readme,
        "readme_latest_draw": f"тираж `{draw.get('draw_number')}`" in readme,
        "readme_latest_numbers": draw.get("numbers_text") in readme,
        "readme_dataset_rows": f"`{draw.get('row_count')}` реда" in readme,
        "readme_docs_index": "docs/README.md" in readme,
        "readme_step_history": "docs/STEP_HISTORY.md" in readme,
        "readme_forward_progress": progress in readme,
        "readme_expected_draw": str(forward.get("active_expected_draw_key")) in readme,
        "ui_guide_latest_date": draw.get("date") in guide,
        "ui_guide_latest_draw": f"тираж {draw.get('draw_number')}" in guide,
        "ui_guide_latest_numbers": draw.get("numbers_text") in guide,
        "ui_guide_dataset_rows": str(draw.get("row_count")) in guide,
    }


def audit_repository(root: Path = ROOT) -> dict[str, Any]:
    draw = latest_draw_state(root)
    forward = step148_state(root)
    root_docs = stale_root_docs(root)
    legacy = legacy_root_manifests(root)
    missing_docs = missing_documentation(root)
    stale_refs = stale_document_references(root)
    readme = readme_checks(root, draw, forward) if draw.get("ok") else {}
    checks = {
        "latest_draw_available": bool(draw.get("ok")),
        "latest_draw_is_2026_54": draw.get("draw_key") == "2026-54",
        "latest_numbers_match": draw.get("numbers") == [16, 29, 35, 37, 44, 47],
        "dataset_rows_match_checkpoint": draw.get("row_count") == 10064,
        "step148_has_settlement": int(forward.get("eligible_settled_draws") or 0) >= 1,
        "step148_expected_draw_is_2026_55": forward.get("active_expected_draw_key") == "2026-55",
        "step148_production_remains_blocked": forward.get("production_promotion_approved") is False,
        "legacy_root_manifests_removed": not legacy,
        "root_docs_moved": not root_docs,
        "documentation_complete": not missing_docs,
        "documentation_references_current": not stale_refs,
        "readme_and_ui_guide_current": bool(readme) and all(readme.values()),
    }
    core: dict[str, Any] = {
        "step": "151",
        "name": "Repository Root Cleanup & Post-Draw Documentation Sync",
        "latest_draw": draw,
        "prospective_forward_test": forward,
        "legacy_root_manifests": legacy,
        "stale_root_docs": root_docs,
        "missing_documentation": missing_docs,
        "stale_document_references": stale_refs,
        "readme_checks": readme,
        "privacy": {
            "personal_journal_database": "local_only_excluded",
            "personal_journal_exports": "local_only_excluded",
        },
        "checks": checks,
        "root_inventory": root_inventory(root),
    }
    signature_payload = dict(core)
    signature_payload.pop("root_inventory", None)
    core["result_signature_sha256"] = _signature(signature_payload)
    core["ok"] = all(checks.values())
    core["checked_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return core


def write_audit_artifacts(root: Path = ROOT) -> dict[str, Any]:
    result = audit_repository(root)
    model_path = root / "models/v151_repository_root_cleanup_status.json"
    report_json = root / "reports/v151_repository_root_cleanup_summary.json"
    report_md = root / "reports/v151_repository_root_cleanup_summary.md"
    inventory_csv = root / "reports/v151_root_inventory.csv"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    report_json.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    model_path.write_text(payload, encoding="utf-8", newline="\n")
    report_json.write_text(payload, encoding="utf-8", newline="\n")
    with inventory_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "type", "category", "size_bytes"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(result["root_inventory"])
    draw = result["latest_draw"]
    forward = result["prospective_forward_test"]
    checks = "\n".join(
        f"- {'PASS' if passed else 'FAIL'} — `{name}`"
        for name, passed in result["checks"].items()
    )
    report_md.write_text(
        f"""# Step 151 — Repository Root Cleanup & Post-Draw Documentation Sync

## Резултат

- Статус: **{'PASS' if result['ok'] else 'FAIL'}**
- Последен тираж: `{draw.get('draw_key')}` от `{draw.get('date')}`
- Числа: `{draw.get('numbers_text')}`
- Редове в основния набор: `{draw.get('row_count')}`
- Step 148 прогрес: `{forward.get('eligible_settled_draws')}/{forward.get('target_settled_draws')}`
- Активен следващ тираж: `{forward.get('active_expected_draw_key')}`
- Остарели root manifest файлове: `{len(result['legacy_root_manifests'])}`
- Документи, останали в root: `{len(result['stale_root_docs'])}`
- Невалидни стари препратки: `{len(result['stale_document_references'])}`
- Signature SHA-256: `{result['result_signature_sha256']}`

## Проверки

{checks}

## Граници

Стъпката подрежда root директорията и синхронизира документацията след официалния тираж. Не променя историческите числа, моделните алгоритми, scoring логиката, Step 148 ledger веригата или личния SQLite дневник.
""",
        encoding="utf-8", newline="\n",
    )
    return result

from __future__ import annotations

import ast
import hashlib
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "models/v151_2_2_runtime_import_compatibility_policy.json"
STATUS_PATH = ROOT / "models/v151_2_2_runtime_import_compatibility_status.json"
SUMMARY_JSON_PATH = ROOT / "reports/v151_2_2_runtime_import_compatibility_summary.json"
SUMMARY_MD_PATH = ROOT / "reports/v151_2_2_runtime_import_compatibility_summary.md"
REPORT_PATH = ROOT / "reports/STEP_151_2_2_RUNTIME_IMPORT_COMPATIBILITY_HOTFIX.md"

CHECKPOINT = "Step 151.2.2"
CHECKPOINT_TITLE = "Runtime Import Compatibility Hotfix"

REQUIRED_FILES = (
    "src/v150_ui_language_integrity_engine.py",
    "src/v150_1_deep_ui_integrity_engine.py",
    "src/v151_2_2_runtime_import_compatibility_engine.py",
    "scripts/verify_step_151_2_2.py",
    "tools/finalize_step_151_2_2_release.py",
    "tools/apply_step_151_2_2_runtime_import_hotfix.ps1",
    "reports/STEP_151_2_2_RUNTIME_IMPORT_COMPATIBILITY_HOTFIX.md",
)
GENERATED_FILES = (
    "models/v151_2_2_runtime_import_compatibility_policy.json",
    "models/v151_2_2_runtime_import_compatibility_status.json",
    "reports/v151_2_2_runtime_import_compatibility_summary.json",
    "reports/v151_2_2_runtime_import_compatibility_summary.md",
)


def _signature(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _imports_from(tree: ast.AST, module: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            names.update(alias.name for alias in node.names)
    return names


def policy_payload() -> dict[str, Any]:
    return {
        "step": "151.2.2",
        "name": CHECKPOINT_TITLE,
        "scope": "restore Streamlit startup compatibility after the dynamic Step 148 integrity migration",
        "required_api": "protected_step148_status",
        "forbidden_legacy_import": "PROTECTED_STEP148_HASHES",
        "display_only": True,
        "production_scoring_changed": False,
        "historical_draw_data_changed": False,
        "personal_journal_used": False,
    }


def audit_runtime_import_compatibility() -> dict[str, Any]:
    failures: list[str] = []
    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).is_file()]
    failures.extend(f"missing:{rel}" for rel in missing)

    base_path = ROOT / "src/v150_ui_language_integrity_engine.py"
    deep_path = ROOT / "src/v150_1_deep_ui_integrity_engine.py"
    base_source = base_path.read_text(encoding="utf-8-sig")
    deep_source = deep_path.read_text(encoding="utf-8-sig")
    base_tree = ast.parse(base_source)
    deep_tree = ast.parse(deep_source)
    imported = _imports_from(deep_tree, "src.v150_ui_language_integrity_engine")

    checks = {
        "public_dynamic_step148_api_present": any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "protected_step148_status"
            for node in ast.walk(base_tree)
        ),
        "deep_engine_imports_public_api": "protected_step148_status" in imported,
        "legacy_hash_constant_not_imported": "PROTECTED_STEP148_HASHES" not in imported,
        "legacy_hash_constant_not_referenced": "PROTECTED_STEP148_HASHES" not in deep_source,
        "deep_status_delegates_to_dynamic_api": "return protected_step148_status()" in deep_source,
    }

    runtime: dict[str, Any] = {}
    try:
        base_module = importlib.import_module("src.v150_ui_language_integrity_engine")
        deep_module = importlib.import_module("src.v150_1_deep_ui_integrity_engine")
        importlib.import_module("src.v150_2_plain_language_integrity_engine")
        importlib.import_module("src.v150_3_version_label_integrity_engine")
        protected = deep_module._protected_status()
        runtime = {
            "base_import_ok": True,
            "deep_import_ok": True,
            "downstream_imports_ok": True,
            "public_api_callable": callable(getattr(base_module, "protected_step148_status", None)),
            "protected_status_is_object": isinstance(protected, dict),
            "protected_status_all_ok": protected.get("all_ok") is True if isinstance(protected, dict) else False,
            "protected_status_file_count": len(protected.get("files", [])) if isinstance(protected, dict) else 0,
            "protected_status_failures": protected.get("failures", []) if isinstance(protected, dict) else ["not_dict"],
        }
    except Exception as exc:
        runtime = {
            "base_import_ok": False,
            "deep_import_ok": False,
            "downstream_imports_ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
        failures.append(f"runtime_import:{type(exc).__name__}:{exc}")

    failures.extend(f"check:{key}" for key, passed in checks.items() if not passed)
    for key in ("base_import_ok", "deep_import_ok", "downstream_imports_ok", "public_api_callable", "protected_status_is_object", "protected_status_all_ok"):
        if runtime.get(key) is not True:
            failures.append(f"runtime:{key}")

    core = {
        "step": "151.2.2",
        "name": CHECKPOINT_TITLE,
        "missing_files": missing,
        "checks": checks,
        "runtime": runtime,
        "display_only": True,
        "production_scoring_changed": False,
        "historical_draw_data_changed": False,
        "personal_journal_used": False,
        "failures": failures,
    }
    core["result_signature_sha256"] = _signature(core)
    core["ok"] = not failures
    core["checked_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return core


def write_artifacts() -> dict[str, Any]:
    POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    POLICY_PATH.write_text(json.dumps(policy_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    result = audit_runtime_import_compatibility()
    STATUS_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    SUMMARY_JSON_PATH.write_text(json.dumps({"report_type": "step151_2_2_runtime_import_compatibility", "summary": result}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    SUMMARY_MD_PATH.write_text(
        "# Step 151.2.2 — Runtime Import Compatibility Hotfix\n\n"
        f"- Status: **{'OK' if result['ok'] else 'CHECK REQUIRED'}**\n"
        f"- Runtime import failures: **{len(result['failures'])}**\n"
        f"- Dynamic Step 148 protected files checked: **{result.get('runtime', {}).get('protected_status_file_count', 0)}**\n"
        "- Production scoring changed: **No**\n"
        "- Historical draw data changed: **No**\n"
        "- Personal journal used: **No**\n",
        encoding="utf-8",
        newline="\n",
    )
    return result

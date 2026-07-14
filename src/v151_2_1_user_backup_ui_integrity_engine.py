from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SECTION_PATH = ROOT / "src/v103_clean_release_checkpoint_section.py"
POLICY_PATH = ROOT / "models/v151_2_1_user_backup_ui_policy.json"
STATUS_PATH = ROOT / "models/v151_2_1_user_backup_ui_status.json"
SUMMARY_JSON_PATH = ROOT / "reports/v151_2_1_user_backup_ui_summary.json"
SUMMARY_MD_PATH = ROOT / "reports/v151_2_1_user_backup_ui_summary.md"
REPORT_PATH = ROOT / "reports/STEP_151_2_1_USER_FACING_BACKUP_UI_AND_TECHNICAL_DETAILS_SEPARATION_CLOSURE.md"

CHECKPOINT = "Step 151.2.1"
CHECKPOINT_TITLE = "User-Facing Backup UI & Technical Details Separation Closure"

REQUIRED_FILES = (
    "src/v103_clean_release_checkpoint_section.py",
    "src/v151_2_1_user_backup_ui_integrity_engine.py",
    "scripts/verify_step_151_2_1.py",
    "tools/finalize_step_151_2_1_release.py",
    "tools/apply_step_151_2_1_user_backup_ui.ps1",
    "reports/STEP_151_2_1_USER_FACING_BACKUP_UI_AND_TECHNICAL_DETAILS_SEPARATION_CLOSURE.md",
)

GENERATED_FILES = (
    "models/v151_2_1_user_backup_ui_policy.json",
    "models/v151_2_1_user_backup_ui_status.json",
    "reports/v151_2_1_user_backup_ui_summary.json",
    "reports/v151_2_1_user_backup_ui_summary.md",
)

RAW_TECHNICAL_METHODS = {"code", "json", "exception"}
FORBIDDEN_NORMAL_TOKENS = (
    "tracked",
    "forbidden",
    "checkpoint",
    "metadata report",
    "git status --short",
    "python .\\scripts",
    ".git",
    "__pycache__",
    "nested zip",
)


def _signature(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        return _call_name(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _contains_call(node: ast.AST, function_name: str) -> bool:
    return any(isinstance(item, ast.Call) and _call_name(item) == function_name for item in ast.walk(node))


def _literal_text(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            item.value if isinstance(item, ast.Constant) and isinstance(item.value, str) else ""
            for item in node.values
        )
    if isinstance(node, ast.Call) and _call_name(node) == "ui_text" and node.args:
        return _literal_text(node.args[0])
    return ""


def _is_technical_expander(node: ast.With) -> bool:
    for item in node.items:
        call = item.context_expr
        if not isinstance(call, ast.Call) or _call_name(call) != "expander" or not call.args:
            continue
        text = _literal_text(call.args[0]).lower()
        if "техничес" in text or "technical" in text:
            return True
    return False


class _SectionVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.technical_depth = 0
        self.raw_outputs: list[dict[str, Any]] = []
        self.unguarded_raw_outputs: list[dict[str, Any]] = []
        self.normal_literals: list[dict[str, Any]] = []
        self.user_checks_guarded_incorrectly = False
        self.technical_checks_unguarded = False

    def _visit_statements(self, statements: list[ast.stmt], *, technical: bool) -> None:
        previous = self.technical_depth
        if technical:
            self.technical_depth += 1
        try:
            for statement in statements:
                self.visit(statement)
        finally:
            self.technical_depth = previous

    def visit_If(self, node: ast.If) -> Any:
        technical_guard = _contains_call(node.test, "technical_details_enabled")
        self.visit(node.test)
        self._visit_statements(node.body, technical=technical_guard)
        self._visit_statements(node.orelse, technical=False)
        return None

    def visit_With(self, node: ast.With) -> Any:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars:
                self.visit(item.optional_vars)
        self._visit_statements(node.body, technical=_is_technical_expander(node))
        return None

    def visit_Call(self, node: ast.Call) -> Any:
        method = _call_name(node)
        expression = ast.unparse(node) if hasattr(ast, "unparse") else method
        if method in RAW_TECHNICAL_METHODS:
            row = {"line": node.lineno, "method": method, "expression": expression, "guarded": self.technical_depth > 0}
            self.raw_outputs.append(row)
            if self.technical_depth == 0:
                self.unguarded_raw_outputs.append(row)

        if method == "dataframe" and node.args:
            first = node.args[0]
            first_name = _call_name(first)
            if first_name == "_checks_df" and self.technical_depth == 0:
                self.technical_checks_unguarded = True
            if first_name == "_user_checks_df" and self.technical_depth > 0:
                self.user_checks_guarded_incorrectly = True

        if method in {
            "title", "header", "subheader", "markdown", "caption", "info", "warning", "success", "error", "button"
        } and node.args and self.technical_depth == 0:
            text = _literal_text(node.args[0])
            if text:
                self.normal_literals.append({"line": node.lineno, "method": method, "text": text})

        self.generic_visit(node)
        return None


def policy_payload() -> dict[str, Any]:
    return {
        "step": "151.2.1",
        "name": CHECKPOINT_TITLE,
        "scope": "Step 103 backup page user copy and technical-output separation",
        "normal_mode": {
            "user_facing_title": "Резервно копие на приложението",
            "raw_git_status_visible": False,
            "terminal_command_visible": False,
            "raw_internal_checks_visible": False,
            "friendly_preflight_checks_visible": True,
        },
        "technical_mode": {
            "controlled_by": "v150_show_technical_details",
            "raw_git_status_available": True,
            "terminal_command_available": True,
            "raw_internal_checks_available": True,
        },
        "display_only": True,
        "production_scoring_changed": False,
        "historical_draw_data_changed": False,
        "personal_journal_used": False,
    }


def audit_user_backup_ui() -> dict[str, Any]:
    source = SECTION_PATH.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    visitor = _SectionVisitor()
    visitor.visit(tree)

    normal_text = "\n".join(row["text"] for row in visitor.normal_literals).lower()
    forbidden_hits = [token for token in FORBIDDEN_NORMAL_TOKENS if token in normal_text]
    missing_files = [rel for rel in REQUIRED_FILES if not (ROOT / rel).is_file()]

    checks = {
        "required_files_present": not missing_files,
        "user_facing_backup_title": "Резервно копие на приложението" in source,
        "purpose_explained": "Създава чист архив на приложението" in source,
        "backup_contents_explained": "Какво ще получиш" in source,
        "friendly_preflight_table_present": "_user_checks_df(summary)" in source,
        "raw_preflight_table_available_in_technical_mode": "_checks_df(summary)" in source,
        "create_button_user_facing": "Създай резервно копие" in source,
        "create_button_has_stable_key": 'key="v103_create_backup"' in source,
        "create_button_disabled_until_ready": "disabled=not can_create" in source,
        "technical_toggle_used": source.count("technical_details_enabled(st)") >= 3,
        "all_raw_outputs_guarded": not visitor.unguarded_raw_outputs,
        "raw_checks_guarded": not visitor.technical_checks_unguarded,
        "friendly_checks_visible_normally": not visitor.user_checks_guarded_incorrectly,
        "normal_copy_has_no_raw_technical_tokens": not forbidden_hits,
        "legacy_developer_title_removed": 'st.title("Чист архив на проекта")' not in source,
        "legacy_terminal_section_removed_from_normal_flow": 'st.subheader("Команда за терминала")' not in source,
        "raw_result_dump_removed_from_normal_flow": "st.write(result)" not in source,
    }

    core = {
        "step": "151.2.1",
        "name": CHECKPOINT_TITLE,
        "section": SECTION_PATH.relative_to(ROOT).as_posix(),
        "missing_files": missing_files,
        "checks": checks,
        "raw_technical_outputs": visitor.raw_outputs,
        "unguarded_raw_technical_outputs": visitor.unguarded_raw_outputs,
        "forbidden_normal_copy_hits": forbidden_hits,
        "normal_literal_count": len(visitor.normal_literals),
        "display_only": True,
        "production_scoring_changed": False,
        "historical_draw_data_changed": False,
        "personal_journal_used": False,
    }
    core["result_signature_sha256"] = _signature(core)
    core["ok"] = all(checks.values())
    core["checked_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return core


def write_artifacts() -> dict[str, Any]:
    POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    POLICY_PATH.write_text(
        json.dumps(policy_payload(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    result = audit_user_backup_ui()
    STATUS_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    SUMMARY_JSON_PATH.write_text(
        json.dumps({"report_type": "step151_2_1_user_backup_ui", "summary": result}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    SUMMARY_MD_PATH.write_text(
        "# Step 151.2.1 — User-Facing Backup UI\n\n"
        f"- Status: **{'OK' if result['ok'] else 'CHECK REQUIRED'}**\n"
        f"- Raw technical outputs found: **{len(result['raw_technical_outputs'])}**\n"
        f"- Unguarded raw technical outputs: **{len(result['unguarded_raw_technical_outputs'])}**\n"
        f"- Forbidden technical tokens in normal copy: **{len(result['forbidden_normal_copy_hits'])}**\n"
        "- Production scoring changed: **No**\n"
        "- Historical draw data changed: **No**\n"
        "- Personal journal used: **No**\n",
        encoding="utf-8",
        newline="\n",
    )
    return result

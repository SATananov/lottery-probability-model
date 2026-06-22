from __future__ import annotations

from pathlib import Path
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models" / "v72"

CORE_REFRESH_STEPS = [
    {
        "step": "41",
        "name": "Правилово-съзнати модели",
        "script": "scripts/v41_train_rules_aware_models.py",
        "outputs": ["models/v41", "reports/v41_model_retraining_summary.json"],
    },
    {
        "step": "42",
        "name": "Комбиниран позитивен/негативен анализ",
        "script": "scripts/v42_build_combined_positive_negative_foundation.py",
        "outputs": ["models/v42", "reports"],
    },
    {
        "step": "43.1",
        "name": "Интервален ритъм",
        "script": "scripts/v43_1_refine_interval_rhythm_foundation.py",
        "outputs": ["models/v43_1", "reports/v43_1_interval_rhythm_refined_summary.json"],
    },
    {
        "step": "44.1",
        "name": "Финален ensemble фиш foundation",
        "script": "scripts/v44_1_refine_final_ensemble_ticket_foundation.py",
        "outputs": ["models/v44_1", "reports/v44_1_final_ensemble_ticket_summary.json"],
    },
    {
        "step": "45",
        "name": "Прогнозно табло Pro",
        "script": "scripts/v45_train_prediction_engine_pro.py",
        "outputs": ["models/v45", "reports/v45_training_summary.json"],
    },
    {
        "step": "50",
        "name": "Анализ на двойки и групи",
        "script": "scripts/v50_build_pair_group_intelligence.py",
        "outputs": ["models/v50", "reports/v50_pair_group_summary.json"],
    },
    {
        "step": "51",
        "name": "Интелигентна оценка на портфейл от фишове",
        "script": "scripts/v51_build_ticket_portfolio_intelligence.py",
        "outputs": ["models/v51", "reports/v51_ticket_portfolio_summary.json"],
    },
    {
        "step": "53",
        "name": "Анализ на покритието на фишовете",
        "script": "scripts/v53_build_ticket_coverage_intelligence.py",
        "outputs": ["models/v53", "reports/v53_ticket_coverage_summary.json"],
    },
    {
        "step": "54",
        "name": "Анализ на баланса на комбинациите",
        "script": "scripts/v54_build_pattern_balance_engine.py",
        "outputs": ["models/v54", "reports/v54_pattern_balance_summary.json"],
    },
    {
        "step": "55",
        "name": "Профил на число",
        "script": "scripts/v55_build_number_profile_center.py",
        "outputs": ["models/v55", "reports/v55_number_profile_summary.json"],
    },
    {
        "step": "56",
        "name": "Търсене на подобни исторически тиражи",
        "script": "scripts/v56_build_draw_similarity_search.py",
        "outputs": ["models/v56", "reports/v56_draw_similarity_summary.json"],
    },
    {
        "step": "57",
        "name": "Горещи, студени и стабилни числа",
        "script": "scripts/v57_build_hot_cold_stable_center.py",
        "outputs": ["models/v57", "reports/v57_hot_cold_stable_summary.json"],
    },
    {
        "step": "58",
        "name": "Умна обединена оценка 2",
        "script": "scripts/v58_build_smart_ensemble_score_2.py",
        "outputs": ["models/v58", "reports/v58_smart_ensemble_summary.json"],
    },
    {
        "step": "59",
        "name": "Умен генератор на фишове 2",
        "script": "scripts/v59_build_smart_ticket_builder_2.py",
        "outputs": ["models/v59", "reports/v59_smart_ticket_builder_2_summary.json"],
    },
    {
        "step": "60",
        "name": "Финален export на генератора на фишове 2",
        "script": "scripts/v60_build_ticket_builder_2_polish_export.py",
        "outputs": ["models/v60", "reports/v60_ticket_builder_2_polish_export_summary.json"],
    },
]

WEIGHTED_REFRESH_STEPS = [
    {
        "step": "61",
        "name": "Анализ на нов тираж",
        "script": "scripts/v61_build_draw_result_analyzer.py",
        "outputs": ["models/v61", "reports/v61_draw_result_analyzer_summary.json"],
    },
    {
        "step": "62",
        "name": "История на моделите",
        "script": "scripts/v62_build_model_performance_tracker.py",
        "outputs": ["models/v62", "reports/v62_model_performance_summary.json"],
    },
    {
        "step": "63",
        "name": "Надеждност на моделите",
        "script": "scripts/v63_build_model_reliability_dashboard.py",
        "outputs": ["models/v63", "reports/v63_model_reliability_summary.json"],
    },
    {
        "step": "65",
        "name": "Умно тегло на моделите",
        "script": "scripts/v65_build_model_weighting_center.py",
        "outputs": ["models/v65", "reports/v65_model_weighting_summary.json"],
    },
    {
        "step": "66",
        "name": "Претеглен ensemble анализ",
        "script": "scripts/v66_build_weighted_smart_ensemble.py",
        "outputs": ["models/v66", "reports/v66_weighted_smart_ensemble_summary.json"],
    },
    {
        "step": "67",
        "name": "Умен генератор с тегла",
        "script": "scripts/v67_build_weighted_ticket_builder.py",
        "outputs": ["models/v67", "reports/v67_weighted_ticket_builder_summary.json"],
    },
    {
        "step": "68",
        "name": "Умен оптимизатор на портфейл",
        "script": "scripts/v68_build_weighted_portfolio_optimizer.py",
        "outputs": ["models/v68", "reports/v68_weighted_portfolio_summary.json"],
    },
    {
        "step": "69",
        "name": "Подобряване на портфолио",
        "script": "scripts/v69_build_portfolio_improvement_suggestions.py",
        "outputs": ["models/v69", "reports/v69_portfolio_improvement_summary.json"],
    },
    {
        "step": "70",
        "name": "Приложен подобрен портфейл",
        "script": "scripts/v70_build_applied_candidate_portfolio.py",
        "outputs": ["models/v70", "reports/v70_applied_candidate_portfolio_summary.json"],
    },
    {
        "step": "71",
        "name": "Пакет за игра",
        "script": "scripts/v71_build_ticket_pack_export.py",
        "outputs": ["models/v71", "reports/v71_ticket_pack_summary.json"],
    },
    {
        "step": "73",
        "name": "Представяне на пакета",
        "script": "scripts/v73_build_ticket_pack_performance_tracker.py",
        "outputs": ["models/v73", "reports/v73_ticket_pack_performance_summary.json"],
    },
]


def _exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def _mtime(rel_path: str) -> str:
    path = ROOT / rel_path
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def _run_script(script: str) -> tuple[bool, str]:
    path = ROOT / script

    if not path.exists():
        return False, f"Missing script: {script}"

    completed = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )

    output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    return completed.returncode == 0, output.strip()


def _clean_output_text(value: str) -> str:
    text = str(value or "")
    # Keep generated reports readable even if a Windows console returns broken bytes.
    text = text.replace("\ufffd", "")
    text = text.replace(chr(0xFFFD), "")
    while "    " in text:
        text = text.replace("    ", " ")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip()).strip()


def _step_status(step: dict[str, object]) -> dict[str, object]:
    outputs = list(step.get("outputs", []))
    script = str(step.get("script", ""))

    return {
        "step": step.get("step", ""),
        "name": step.get("name", ""),
        "script": script,
        "script_exists": _exists(script),
        "outputs": "; ".join(outputs),
        "outputs_ok": all(_exists(str(path)) for path in outputs),
        "latest_output_mtime": _mtime(str(outputs[-1])) if outputs else "",
        "run_status": "planned",
        "run_ok": "",
        "run_output_tail": "",
    }


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_pipeline_refresh_plan(run_pipeline: bool = False, include_core: bool = False) -> dict[str, object]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    steps = []
    if include_core:
        steps.extend(CORE_REFRESH_STEPS)
    steps.extend(WEIGHTED_REFRESH_STEPS)

    rows = []
    all_ok = True
    stopped_at = ""

    for step in steps:
        row = _step_status(step)

        if run_pipeline:
            ok, output = _run_script(str(step["script"]))
            row["run_status"] = "OK" if ok else "ERROR"
            row["run_ok"] = bool(ok)
            row["run_output_tail"] = _clean_output_text(output[-3000:])

            # Re-check outputs after running.
            row["outputs_ok"] = all(_exists(str(path)) for path in step.get("outputs", []))
            outputs = list(step.get("outputs", []))
            row["latest_output_mtime"] = _mtime(str(outputs[-1])) if outputs else ""

            if not ok:
                all_ok = False
                stopped_at = str(step["script"])
                rows.append(row)
                break

        rows.append(row)

    missing_scripts = [row["script"] for row in rows if not row["script_exists"]]
    missing_outputs = [row["script"] for row in rows if not row["outputs_ok"]]

    summary = {
        "step": "72",
        "name": "Интеграция за пълно обновяване на статистическия pipeline",
        "mode": "run" if run_pipeline else "audit",
        "include_core": include_core,
        "steps_planned": len(steps),
        "steps_reported": len(rows),
        "all_scripts_present": len(missing_scripts) == 0,
        "all_outputs_present": len(missing_outputs) == 0,
        "run_pipeline": run_pipeline,
        "run_ok": bool(all_ok) if run_pipeline else "",
        "stopped_at": stopped_at,
        "weighted_steps": [step["step"] for step in WEIGHTED_REFRESH_STEPS],
        "core_steps_included": [step["step"] for step in CORE_REFRESH_STEPS] if include_core else [],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_reports": [
            "reports/v72_pipeline_refresh_summary.json",
            "reports/v72_pipeline_refresh_summary.md",
            "reports/v72_pipeline_refresh_plan.csv",
            "models/v72/v72_pipeline_refresh_model.json",
        ],
        "safe_note": "Този pipeline обновява само статистически файлове. Не е предсказание и не е гаранция за печалба.",
    }

    fieldnames = [
        "step",
        "name",
        "script",
        "script_exists",
        "outputs",
        "outputs_ok",
        "latest_output_mtime",
        "run_status",
        "run_ok",
        "run_output_tail",
    ]

    _write_csv(REPORTS_DIR / "v72_pipeline_refresh_plan.csv", rows, fieldnames)
    _write_json(REPORTS_DIR / "v72_pipeline_refresh_summary.json", summary)
    _write_json(MODELS_DIR / "v72_pipeline_refresh_model.json", {"summary": summary, "steps": rows})

    md = [
        "# Step 72 — Обновяване на статистическия pipeline",
        "",
        f"Режим: **{summary['mode']}**",
        f"Включени основни стъпки: **{summary['include_core']}**",
        f"Планирани стъпки: **{summary['steps_planned']}**",
        f"Всички скриптове са налични: **{summary['all_scripts_present']}**",
        f"Всички артефакти са налични: **{summary['all_outputs_present']}**",
        "",
        "**Важно:** Това е статистическо обновяване. Не е предсказание и не е гаранция за печалба.",
        "",
        "## Стъпки",
        "",
        "| Стъпка | Име | Скрипт | Скрипт OK | Артефакти OK | Статус |",
        "|---:|---|---|---|---|---|",
    ]

    for row in rows:
        md.append(
            f"| {row['step']} | {row['name']} | `{row['script']}` | "
            f"{row['script_exists']} | {row['outputs_ok']} | {row['run_status']} |"
        )

    (REPORTS_DIR / "v72_pipeline_refresh_summary.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    return summary


if __name__ == "__main__":
    result = build_pipeline_refresh_plan(run_pipeline=False, include_core=False)
    print("STEP72_OK")
    print("MODE", result["mode"])
    print("STEPS_PLANNED", result["steps_planned"])
    print("ALL_SCRIPTS_PRESENT", result["all_scripts_present"])
    print("ALL_OUTPUTS_PRESENT", result["all_outputs_present"])


GIT_SYNC_PATHS = ["data", "models", "reports"]


def _run_git_command(args: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )

    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": (completed.stdout or "").strip(),
        "stderr": (completed.stderr or "").strip(),
        "command": "git " + " ".join(args),
    }


def git_status_short() -> dict[str, object]:
    repo_check = _run_git_command(["rev-parse", "--is-inside-work-tree"])

    if not repo_check["ok"]:
        return {
            "ok": False,
            "status": "",
            "message": "Тази папка не изглежда като Git repository.",
            "details": repo_check,
        }

    status = _run_git_command(["status", "--short"])

    return {
        "ok": bool(status["ok"]),
        "status": status["stdout"],
        "message": "OK" if status["ok"] else "Git status failed.",
        "details": status,
    }


def git_sync_data_models_reports(commit_message: str | None = None) -> dict[str, object]:
    message = (commit_message or "").strip()
    if not message:
        message = "Refresh lottery data models and reports after pipeline update"

    repo_check = _run_git_command(["rev-parse", "--is-inside-work-tree"])
    if not repo_check["ok"]:
        return {
            "ok": False,
            "status": "not_git_repo",
            "message": "Тази папка не изглежда като Git repository.",
            "steps": [repo_check],
        }

    before_status = _run_git_command(["status", "--short"])
    add_result = _run_git_command(["add", "--", *GIT_SYNC_PATHS])
    staged_result = _run_git_command(["diff", "--cached", "--name-only"])

    steps = [before_status, add_result, staged_result]

    if not add_result["ok"]:
        return {
            "ok": False,
            "status": "git_add_failed",
            "message": "Git add failed.",
            "steps": steps,
        }

    staged_files = [
        line.strip()
        for line in str(staged_result["stdout"]).splitlines()
        if line.strip()
    ]

    if not staged_files:
        after_status = _run_git_command(["status", "--short"])
        return {
            "ok": True,
            "status": "nothing_to_commit",
            "message": "Няма промени в data/models/reports за commit.",
            "staged_files": [],
            "steps": steps + [after_status],
            "after_status": after_status["stdout"],
        }

    commit_result = _run_git_command(["commit", "-m", message])
    steps.append(commit_result)

    if not commit_result["ok"]:
        return {
            "ok": False,
            "status": "commit_failed",
            "message": "Git commit failed.",
            "staged_files": staged_files,
            "steps": steps,
        }

    push_result = _run_git_command(["push"])
    steps.append(push_result)

    if not push_result["ok"]:
        return {
            "ok": False,
            "status": "push_failed",
            "message": "Commit е направен, но git push failed. Провери GitHub authentication/remote.",
            "staged_files": staged_files,
            "steps": steps,
        }

    head_result = _run_git_command(["rev-parse", "--short", "HEAD"])
    after_status = _run_git_command(["status", "--short"])

    return {
        "ok": True,
        "status": "pushed",
        "message": "Промените в data/models/reports са commit-нати и push-нати към GitHub.",
        "commit": head_result["stdout"],
        "staged_files": staged_files,
        "after_status": after_status["stdout"],
        "steps": steps + [head_result, after_status],
    }


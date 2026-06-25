from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "v107" / "v107_model_training_policy_refresh_control_model.json"
SUMMARY_JSON = ROOT / "reports" / "v107_model_training_policy_refresh_control_summary.json"
SUMMARY_MD = ROOT / "reports" / "v107_model_training_policy_refresh_control_summary.md"
CHECKLIST_CSV = ROOT / "reports" / "v107_model_training_policy_refresh_control_checklist.csv"
POLICY_CSV = ROOT / "reports" / "v107_model_training_policy_refresh_control_table.csv"

DATA_FILES = {
    "historical": ROOT / "data" / "historical_draws.csv",
    "normalized": ROOT / "data" / "v40_normalized_draw_events.csv",
    "canonical": ROOT / "data" / "v41_canonical_draw_events.csv",
}

HEAVY_LAB_SCRIPTS = [
    "v67_build_weighted_ticket_builder.py",
    "v75_build_neural_meta_learner.py",
    "v85_neural_epoch_comparison_audit.py",
]

AUTO_FAST_STEPS = [
    "v40_create_normalized_draw_events.py",
    "v41_build_canonical_draw_events.py",
    "v95_build_active_plan_auto_evaluation.py",
    "v97_build_real_draw_lifecycle.py",
    "v98_build_active_plan_result_history.py",
    "v99_build_final_user_dashboard.py",
    "v100_build_final_release_lock.py",
    "v101_build_real_use_protocol.py",
    "v106_2_build_post_draw_historical_schema_sync.py",
    "v106_1_build_post_draw_dataset_sync.py",
    "v106_build_post_draw_status_sync.py",
    "v107_build_model_training_policy_refresh_control.py",
]

PERIODIC_STATISTICAL_STEPS = [
    "v42_build_combined_positive_negative_foundation.py",
    "v43_1_refine_interval_rhythm_foundation.py",
    "v44_1_refine_final_ensemble_ticket_foundation.py",
    "v45_train_prediction_engine_pro.py",
    "v50_build_pair_group_intelligence.py",
    "v51_build_ticket_portfolio_intelligence.py",
    "v53_build_ticket_coverage_intelligence.py",
    "v54_build_pattern_balance_engine.py",
    "v55_build_number_profile_center.py",
    "v56_build_draw_similarity_search.py",
    "v57_build_hot_cold_stable_center.py",
    "v58_build_smart_ensemble_score_2.py",
    "v59_build_smart_ticket_builder_2.py",
    "v65_build_model_weighting_center.py",
    "v66_build_weighted_smart_ensemble.py",
    "v68_build_weighted_portfolio_optimizer.py",
    "v69_build_portfolio_improvement_suggestions.py",
    "v70_build_applied_candidate_portfolio.py",
    "v71_build_ticket_pack_export.py",
    "v73_build_ticket_pack_performance_tracker.py",
    "v74_build_model_dependency_sync_center.py",
    "v76_build_explainability_validation_center.py",
    "v77_build_decision_recommendation_center.py",
    "v78_build_final_play_plan_center.py",
    "v79_build_ticket_pack_export_center.py",
    "v80_build_final_system_audit_center.py",
    "v81_build_final_ux_navigation_center.py",
    "v82_build_final_release_package_center.py",
    "v94_build_active_budget_plan_tracker.py",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def pick(row: dict[str, str], keys: list[str], default: str = "") -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def extract_numbers(row: dict[str, str]) -> list[int]:
    columns = ["n1", "n2", "n3", "n4", "n5", "n6"]
    values = [safe_int(row.get(col)) for col in columns]
    if all(value is not None for value in values):
        return sorted(int(value) for value in values)

    numbers_text = pick(row, ["numbers", "draw_numbers", "combination"], "")
    if numbers_text:
        cleaned = numbers_text.replace("[", "").replace("]", "").replace(";", ",").replace("|", ",").replace(" ", ",")
        parsed = [safe_int(part) for part in cleaned.split(",") if part.strip()]
        parsed = [int(value) for value in parsed if value is not None]
        if len(parsed) >= 6:
            return sorted(parsed[:6])
    return []


def latest_draw(rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return {"date": None, "draw_no": None, "draw_position": None, "numbers": []}

    def sort_key(row: dict[str, str]):
        return (
            pick(row, ["date", "draw_date"], ""),
            safe_int(pick(row, ["year"], "0"), 0) or 0,
            safe_int(pick(row, ["draw_number", "draw_no", "draw_id"], "0"), 0) or 0,
            safe_int(pick(row, ["draw_position", "drawing_no", "position"], "0"), 0) or 0,
        )

    row = max(rows, key=sort_key)
    return {
        "date": pick(row, ["date", "draw_date"], None),
        "draw_no": pick(row, ["draw_number", "draw_no", "draw_id"], None),
        "draw_position": pick(row, ["draw_position", "drawing_no", "position"], None),
        "numbers": extract_numbers(row),
    }


def classify_training_need(real_result_rows: int) -> dict[str, Any]:
    if real_result_rows < 5:
        return {
            "level": "NO_RETRAIN_NOW",
            "label_bg": "Не обучавай тежки модели сега",
            "message_bg": "Има твърде малко нови реални резултати. След всеки тираж правим само бърз синхрон, оценка и dashboard refresh.",
            "recommended_action_bg": "Изчакай поне 5 реални резултата преди лек статистически refresh.",
            "next_threshold_bg": f"Остават {5 - real_result_rows} реални резултата до първа препоръка за лек refresh.",
        }
    if real_result_rows < 10:
        return {
            "level": "LIGHT_STATISTICAL_REFRESH_OPTIONAL",
            "label_bg": "Може лек статистически refresh",
            "message_bg": "Има достатъчно нови резултати за ръчно обновяване на леки статистически отчети, но тежките лаборатории остават ръчни.",
            "recommended_action_bg": "Пусни само подбрани леки статистически builder-и, ако искаш междинен преглед.",
            "next_threshold_bg": f"Остават {10 - real_result_rows} реални резултата до препоръчителен по-широк refresh.",
        }
    if real_result_rows < 20:
        return {
            "level": "STATISTICAL_REFRESH_RECOMMENDED",
            "label_bg": "Препоръчителен статистически refresh",
            "message_bg": "Има натрупани нови резултати. Подходящо е да се обновят статистическите score модели и отчетите.",
            "recommended_action_bg": "Пусни ръчен статистически refresh, без neural/lab-heavy процеси по подразбиране.",
            "next_threshold_bg": f"Остават {20 - real_result_rows} реални резултата до ръчен heavy/lab преглед.",
        }
    return {
        "level": "MANUAL_HEAVY_REVIEW_ALLOWED",
        "label_bg": "Време е за ръчен лабораторен преглед",
        "message_bg": "Има достатъчно нови реални резултати за сериозен ръчен преглед и сравнение на тежките модели.",
        "recommended_action_bg": "Планирай ръчно пускане на heavy/lab модели и сравни резултатите преди промяна на активния план.",
        "next_threshold_bg": "След heavy/lab преглед заключи нов checkpoint само ако backtest/forward-test показва смислено подобрение.",
    }


def build_policy_table(real_result_rows: int) -> list[dict[str, Any]]:
    return [
        {
            "group_bg": "След всеки реален тираж",
            "cadence_bg": "Автоматично / бърз режим",
            "scripts_bg": ", ".join(AUTO_FAST_STEPS),
            "decision_bg": "Винаги да се пуска",
            "reason_bg": "Синхронизира dataset-ите, оценява активния план и обновява lifecycle/dashboard статусите.",
        },
        {
            "group_bg": "Лек статистически refresh",
            "cadence_bg": "Ръчно след 5–10 реални резултата",
            "scripts_bg": ", ".join(PERIODIC_STATISTICAL_STEPS),
            "decision_bg": "Не е нужен след всеки един тираж" if real_result_rows < 5 else "Може да се планира ръчно",
            "reason_bg": "Един нов тираж почти не променя стабилно статистическата картина при над 10 000 реда история.",
        },
        {
            "group_bg": "Тежки лабораторни модели",
            "cadence_bg": "Само ръчно / лабораторно",
            "scripts_bg": ", ".join(HEAVY_LAB_SCRIPTS),
            "decision_bg": "Да не се пуска автоматично",
            "reason_bg": "Тези процеси са бавни и могат да блокират app-а; използват се само за отделен експеримент и сравнение.",
        },
        {
            "group_bg": "Активен план",
            "cadence_bg": "След нов checkpoint или доказана нужда",
            "scripts_bg": "v77, v78, v94, v95, v98, v99, v100, v101",
            "decision_bg": "Не сменяй плана само заради един слаб/силен тираж",
            "reason_bg": "Лотарията е случайна. Единичният резултат не е достатъчна причина за промяна на стратегията.",
        },
    ]


def build_summary() -> dict[str, Any]:
    rows_by_name = {name: read_csv_rows(path) for name, path in DATA_FILES.items()}
    row_counts = {name: len(rows) for name, rows in rows_by_name.items()}
    latest = latest_draw(rows_by_name["historical"])

    v98 = read_json(ROOT / "reports" / "v98_active_plan_result_history_summary.json")
    v102 = read_json(ROOT / "reports" / "v102_runtime_hardening_summary.json")
    v106 = read_json(ROOT / "reports" / "v106_post_draw_status_sync_summary.json")
    add_draws = (ROOT / "src" / "add_draws_section.py").read_text(encoding="utf-8-sig", errors="replace") if (ROOT / "src" / "add_draws_section.py").exists() else ""
    app = (ROOT / "streamlit_app.py").read_text(encoding="utf-8-sig", errors="replace") if (ROOT / "streamlit_app.py").exists() else ""

    real_result_rows = safe_int(v98.get("real_result_rows"), 0) or 0
    policy = classify_training_need(real_result_rows)
    policy_table = build_policy_table(real_result_rows)

    datasets_synced = len(set(row_counts.values())) == 1 and row_counts.get("historical", 0) > 0
    latest_valid = len(latest.get("numbers", [])) == 6 and all(1 <= n <= 49 for n in latest.get("numbers", []))

    checks = [
        {
            "check": "datasets_synced",
            "passed": datasets_synced,
            "blocking": "yes",
            "details_bg": f"historical={row_counts.get('historical')}, normalized={row_counts.get('normalized')}, canonical={row_counts.get('canonical')}",
        },
        {
            "check": "latest_draw_valid",
            "passed": latest_valid,
            "blocking": "yes",
            "details_bg": f"latest={latest.get('date')} {latest.get('numbers')}",
        },
        {
            "check": "runtime_hardening_active",
            "passed": v102.get("status") == "RUNTIME_HARDENED",
            "blocking": "yes",
            "details_bg": f"Step102={v102.get('status')}",
        },
        {
            "check": "post_draw_sync_active",
            "passed": v106.get("status") == "POST_DRAW_SYNCED",
            "blocking": "yes",
            "details_bg": f"Step106={v106.get('status')}",
        },
        {
            "check": "heavy_labs_not_default",
            "passed": "HEAVY_LAB_SCRIPT_NAMES" in add_draws and "FAST_MODEL_SCRIPTS" in add_draws and all(name in add_draws for name in ["v67_build_weighted_ticket_builder.py", "v75_build_neural_meta_learner.py"]),
            "blocking": "yes",
            "details_bg": "v67/v75 са отделени от fast refresh режима.",
        },
        {
            "check": "step107_page_wired",
            "passed": "Политика за обучение" in app and "render_v107_model_training_policy_page" in app,
            "blocking": "yes",
            "details_bg": "Step 107 е достъпен в навигацията.",
        },
        {
            "check": "step107_refresh_chain_wired",
            "passed": "v107_build_model_training_policy_refresh_control.py" in add_draws,
            "blocking": "yes",
            "details_bg": "Step 107 се обновява след бъдещ Add Draw fast refresh.",
        },
    ]

    blocking_failures = sum(1 for item in checks if item.get("blocking") == "yes" and not item.get("passed"))
    status = "TRAINING_POLICY_READY" if blocking_failures == 0 else "CHECK_REQUIRED"

    return {
        "step": 107,
        "name_bg": "Политика за обучение и refresh control",
        "status": status,
        "blocking_failures": blocking_failures,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "row_counts": row_counts,
            "dataset_rows": row_counts.get("historical", 0),
            "datasets_synced": datasets_synced,
            "latest_draw": latest,
        },
        "real_result_rows_since_active_plan": real_result_rows,
        "policy_decision": policy,
        "thresholds": {
            "auto_every_draw_bg": "dataset sync + active plan result + lifecycle/dashboard refresh",
            "light_statistical_refresh_after_real_results": 5,
            "recommended_statistical_refresh_after_real_results": 10,
            "manual_heavy_lab_review_after_real_results": 20,
        },
        "policy_table": policy_table,
        "checks": checks,
        "safe_note_bg": "Step 107 не обучава модели. Той дефинира кога кое се обновява, за да няма тежко обучение след всеки единичен тираж.",
    }


def write_artifacts() -> dict[str, Any]:
    summary = build_summary()
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)

    MODEL_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with CHECKLIST_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "passed", "blocking", "details_bg"])
        writer.writeheader()
        writer.writerows(summary["checks"])

    with POLICY_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["group_bg", "cadence_bg", "scripts_bg", "decision_bg", "reason_bg"])
        writer.writeheader()
        writer.writerows(summary["policy_table"])

    lines = [
        "# Step 107 — Политика за обучение и refresh control",
        "",
        f"Статус: **{summary['status']}**",
        f"Blocking failures: **{summary['blocking_failures']}**",
        f"Dataset rows: **{summary['dataset']['dataset_rows']}**",
        f"Real result rows since active plan: **{summary['real_result_rows_since_active_plan']}**",
        "",
        "## Текуща препоръка",
        "",
        f"**{summary['policy_decision']['label_bg']}**",
        "",
        summary["policy_decision"]["message_bg"],
        "",
        f"Препоръчано действие: {summary['policy_decision']['recommended_action_bg']}",
        "",
        "## Прагове",
        "",
    ]
    for key, value in summary["thresholds"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Политика по групи", ""])
    for row in summary["policy_table"]:
        lines.append(f"- **{row['group_bg']}** — {row['cadence_bg']}. {row['decision_bg']}")
    lines.extend(["", "## Проверки", ""])
    for item in summary["checks"]:
        marker = "OK" if item["passed"] else "FAIL"
        lines.append(f"- {marker}: `{item['check']}` — {item['details_bg']}")
    lines.extend(["", summary["safe_note_bg"]])

    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def load_summary() -> dict[str, Any]:
    if SUMMARY_JSON.exists():
        try:
            return json.loads(SUMMARY_JSON.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
    return build_summary()

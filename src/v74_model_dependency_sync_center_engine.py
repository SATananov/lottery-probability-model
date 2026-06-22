from __future__ import annotations

from pathlib import Path
import csv
import json
import hashlib
from datetime import datetime, timezone
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
V74_MODELS_DIR = MODELS_DIR / "v74"

SUMMARY_PATH = REPORTS_DIR / "v74_model_dependency_summary.json"
SUMMARY_MD_PATH = REPORTS_DIR / "v74_model_dependency_summary.md"
MAP_PATH = REPORTS_DIR / "v74_model_dependency_map.csv"
STATUS_PATH = REPORTS_DIR / "v74_model_sync_status.csv"
REGISTRY_PATH = MODELS_DIR / "model_registry.json"
MODEL_PATH = V74_MODELS_DIR / "v74_model_dependency_sync_center_model.json"

SAFE_NOTE = (
    "Step 74 е контролен слой за синхрон между dataset-и, модели, отчети и pipeline стъпки. "
    "Той не е прогноза и не е гаранция за печалба."
)

PRIMARY_DATASETS = [
    "data/historical_draws.csv",
    "data/v40_normalized_draw_events.csv",
    "data/v41_canonical_draw_events.csv",
]

MODEL_NODES: list[dict[str, Any]] = [
    {
        "step": "41",
        "label": "Правилово-съзнати модели",
        "category": "Базов модел",
        "script": "scripts/v41_train_rules_aware_models.py",
        "datasets": ["data/v41_canonical_draw_events.csv"],
        "inputs": ["data/v41_canonical_draw_events.csv"],
        "outputs": ["models/v41/v41_latest_predictions.json", "reports/v41_model_retraining_summary.json"],
        "feeds": ["Step 62", "Step 65", "Step 66"],
        "role": "Дава rules-aware прогнозни сигнали върху основните числа.",
        "ensemble_source": True,
    },
    {
        "step": "42",
        "label": "Комбиниран позитивен/негативен анализ",
        "category": "Комбиниран анализ",
        "script": "scripts/v42_build_combined_positive_negative_foundation.py",
        "datasets": ["data/v41_canonical_draw_events.csv"],
        "inputs": ["data/v41_canonical_draw_events.csv"],
        "outputs": ["models/v42/v42_combined_prediction.json", "reports/v42_combined_positive_negative_summary.json"],
        "feeds": ["Step 62", "Step 65", "Step 66"],
        "role": "Комбинира позитивни и негативни статистически сигнали.",
        "ensemble_source": True,
    },
    {
        "step": "43.1",
        "label": "Интервален ритъм",
        "category": "Интервален анализ",
        "script": "scripts/v43_1_refine_interval_rhythm_foundation.py",
        "datasets": ["data/v41_canonical_draw_events.csv"],
        "inputs": ["data/v41_canonical_draw_events.csv"],
        "outputs": ["models/v43_1/v43_1_interval_rhythm_refined_prediction.json", "reports/v43_1_interval_rhythm_refined_summary.json"],
        "feeds": ["Step 44.1", "Step 58"],
        "role": "Следи ритъм на поява, интервали и закъснели числа.",
        "ensemble_source": False,
    },
    {
        "step": "44.1",
        "label": "Финален ensemble фиш foundation",
        "category": "Ensemble",
        "script": "scripts/v44_1_refine_final_ensemble_ticket_foundation.py",
        "datasets": ["data/v41_canonical_draw_events.csv"],
        "inputs": ["models/v42/v42_combined_prediction.json", "models/v43_1/v43_1_interval_rhythm_refined_prediction.json"],
        "outputs": ["models/v44_1/v44_1_final_ensemble_ticket_prediction.json", "reports/v44_1_final_ensemble_ticket_summary.json"],
        "feeds": ["Step 62", "Step 65", "Step 66"],
        "role": "Обединява по-ранни сигнали във финален ensemble фиш.",
        "ensemble_source": True,
    },
    {
        "step": "45",
        "label": "Прогнозно табло Pro",
        "category": "ML модел",
        "script": "scripts/v45_train_prediction_engine_pro.py",
        "datasets": ["data/v41_canonical_draw_events.csv"],
        "inputs": ["data/v41_canonical_draw_events.csv"],
        "outputs": ["models/v45/v45_model_metadata.json", "reports/v45_training_summary.json"],
        "feeds": ["Step 62", "Step 65", "Step 66"],
        "role": "Тренира prediction engine с feature matrix и backtest.",
        "ensemble_source": True,
    },
    {
        "step": "50",
        "label": "Анализ на двойки и групи",
        "category": "Групова статистика",
        "script": "scripts/v50_build_pair_group_intelligence.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["data/historical_draws.csv"],
        "outputs": ["models/v50/v50_pair_group_intelligence.json", "reports/v50_pair_group_summary.json"],
        "feeds": ["Step 51", "Step 62", "Step 65"],
        "role": "Анализира двойки, групи и съвместни появи.",
        "ensemble_source": False,
    },
    {
        "step": "51",
        "label": "Интелигентна оценка на портфейл от фишове",
        "category": "Портфолио",
        "script": "scripts/v51_build_ticket_portfolio_intelligence.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["models/v50/v50_pair_group_intelligence.json", "data/historical_draws.csv"],
        "outputs": ["models/v51/v51_ticket_portfolio_intelligence.json", "reports/v51_ticket_portfolio_summary.json"],
        "feeds": ["Step 62", "Step 65", "Step 66"],
        "role": "Оценява фишове и портфолио чрез покритие и групова логика.",
        "ensemble_source": True,
    },
    {
        "step": "55",
        "label": "Профил на число",
        "category": "Профилиране",
        "script": "scripts/v55_build_number_profile_center.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["data/historical_draws.csv"],
        "outputs": ["models/v55/v55_number_profile_manifest.json", "reports/v55_number_profile_summary.json"],
        "feeds": ["Step 56", "Step 57", "Step 58"],
        "role": "Профилира всяко число по честота, интервали, двойки и стабилност.",
        "ensemble_source": False,
    },
    {
        "step": "56",
        "label": "Подобни исторически тиражи",
        "category": "Similarity search",
        "script": "scripts/v56_build_draw_similarity_search.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["data/historical_draws.csv", "reports/v55_number_profiles.json"],
        "outputs": ["models/v56/v56_draw_similarity_manifest.json", "reports/v56_draw_similarity_summary.json"],
        "feeds": ["UI анализ"],
        "role": "Сравнява комбинации с исторически тиражи.",
        "ensemble_source": False,
    },
    {
        "step": "57",
        "label": "Горещи, студени и стабилни числа",
        "category": "Сигнален център",
        "script": "scripts/v57_build_hot_cold_stable_center.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["data/historical_draws.csv", "reports/v55_number_profile_summary.json"],
        "outputs": ["models/v57/v57_hot_cold_stable_manifest.json", "reports/v57_hot_cold_stable_summary.json"],
        "feeds": ["Step 58", "Step 62", "Step 65", "Step 66"],
        "role": "Извлича hot/cold/stable сигнали за числа.",
        "ensemble_source": True,
    },
    {
        "step": "58",
        "label": "Умна обединена оценка 2",
        "category": "Smart ensemble",
        "script": "scripts/v58_build_smart_ensemble_score_2.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["models/v57/v57_hot_cold_stable_manifest.json", "reports/v55_number_profile_summary.json"],
        "outputs": ["models/v58/v58_smart_ensemble_manifest.json", "reports/v58_smart_ensemble_summary.json"],
        "feeds": ["Step 59", "Step 62", "Step 65", "Step 66"],
        "role": "Обединява профили, hot/cold/stable и pattern сигнали.",
        "ensemble_source": True,
    },
    {
        "step": "59",
        "label": "Умен генератор на фишове 2",
        "category": "Генератор",
        "script": "scripts/v59_build_smart_ticket_builder_2.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["reports/v58_smart_ensemble_scores_sample.json"],
        "outputs": ["models/v59/v59_smart_ticket_builder_2_manifest.json", "reports/v59_smart_ticket_builder_2_summary.json"],
        "feeds": ["Step 60", "Step 62", "Step 65"],
        "role": "Генерира кандидат комбинации по различни стратегии.",
        "ensemble_source": True,
    },
    {
        "step": "61",
        "label": "Анализ на нов тираж",
        "category": "Проверка след тираж",
        "script": "scripts/v61_build_draw_result_analyzer.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["data/historical_draws.csv", "models/v41/v41_latest_predictions.json", "reports/v58_smart_ensemble_scores_sample.json"],
        "outputs": ["models/v61/v61_draw_result_analyzer_manifest.json", "reports/v61_draw_result_analyzer_summary.json"],
        "feeds": ["Step 62", "Step 63"],
        "role": "Проверява сигналите срещу последния реален тираж.",
        "ensemble_source": False,
    },
    {
        "step": "62",
        "label": "История на моделите",
        "category": "Performance tracker",
        "script": "scripts/v62_build_model_performance_tracker.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["reports/v61_draw_result_analyzer_summary.json"],
        "outputs": ["models/v62/v62_model_performance_tracker_model.json", "reports/v62_model_performance_summary.json"],
        "feeds": ["Step 63"],
        "role": "Събира история на представянето на моделите.",
        "ensemble_source": False,
    },
    {
        "step": "63",
        "label": "Надеждност на моделите",
        "category": "Reliability",
        "script": "scripts/v63_build_model_reliability_dashboard.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["reports/v62_model_performance_summary.json"],
        "outputs": ["models/v63/v63_model_reliability_dashboard_model.json", "reports/v63_model_reliability_summary.json", "reports/v63_model_reliability_scores.csv"],
        "feeds": ["Step 65"],
        "role": "Изчислява reliability score за следените модели.",
        "ensemble_source": False,
    },
    {
        "step": "65",
        "label": "Умно тегло на моделите",
        "category": "Adaptive weighting",
        "script": "scripts/v65_build_model_weighting_center.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["reports/v63_model_reliability_scores.csv"],
        "outputs": ["models/v65/v65_model_weighting_center_model.json", "reports/v65_model_weighting_summary.json", "reports/v65_model_weights.csv"],
        "feeds": ["Step 66"],
        "role": "Превръща надеждността в адаптивни тегла.",
        "ensemble_source": False,
    },
    {
        "step": "66",
        "label": "Претеглен ensemble анализ",
        "category": "Weighted ensemble",
        "script": "scripts/v66_build_weighted_smart_ensemble.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["reports/v65_model_weights.csv"],
        "outputs": ["models/v66/v66_weighted_smart_ensemble_model.json", "reports/v66_weighted_smart_ensemble_summary.json", "reports/v66_weighted_smart_ensemble_scores.csv"],
        "feeds": ["Step 67", "Step 68", "Step 69"],
        "role": "Обединява активните сигнали според адаптивните тегла.",
        "ensemble_source": False,
    },
    {
        "step": "67",
        "label": "Умен генератор с тегла",
        "category": "Weighted ticket builder",
        "script": "scripts/v67_build_weighted_ticket_builder.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["reports/v66_weighted_smart_ensemble_scores.csv"],
        "outputs": ["models/v67/v67_weighted_ticket_builder_model.json", "reports/v67_weighted_ticket_builder_summary.json", "reports/v67_weighted_ticket_builder_tickets.csv"],
        "feeds": ["Step 68"],
        "role": "Строи фишове върху Step 66 weighted scores.",
        "ensemble_source": False,
    },
    {
        "step": "68",
        "label": "Умен оптимизатор на портфейл",
        "category": "Portfolio optimizer",
        "script": "scripts/v68_build_weighted_portfolio_optimizer.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["reports/v67_weighted_ticket_builder_tickets.csv", "reports/v66_weighted_smart_ensemble_scores.csv"],
        "outputs": ["models/v68/v68_weighted_portfolio_optimizer_model.json", "reports/v68_weighted_portfolio_summary.json", "reports/v68_weighted_portfolio_tickets.csv"],
        "feeds": ["Step 69"],
        "role": "Оценява портфейл, покритие, повторения и концентрация.",
        "ensemble_source": False,
    },
    {
        "step": "69",
        "label": "Подобряване на портфолио",
        "category": "Improvement suggestions",
        "script": "scripts/v69_build_portfolio_improvement_suggestions.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["reports/v68_weighted_portfolio_summary.json", "reports/v66_weighted_smart_ensemble_scores.csv"],
        "outputs": ["models/v69/v69_portfolio_improvement_model.json", "reports/v69_portfolio_improvement_summary.json", "reports/v69_candidate_portfolio_tickets.csv"],
        "feeds": ["Step 70"],
        "role": "Предлага подобрения без да презаписва основния пакет.",
        "ensemble_source": False,
    },
    {
        "step": "70",
        "label": "Приложен подобрен портфейл",
        "category": "Applied portfolio",
        "script": "scripts/v70_build_applied_candidate_portfolio.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["reports/v69_candidate_portfolio_tickets.csv"],
        "outputs": ["models/v70/v70_applied_candidate_portfolio_model.json", "reports/v70_applied_candidate_portfolio_summary.json", "reports/v70_applied_candidate_portfolio_tickets.csv"],
        "feeds": ["Step 71"],
        "role": "Фиксира подобрения пакет като отделна статистическа референция.",
        "ensemble_source": False,
    },
    {
        "step": "71",
        "label": "Пакет за игра",
        "category": "Ticket pack export",
        "script": "scripts/v71_build_ticket_pack_export.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["reports/v70_applied_candidate_portfolio_tickets.csv"],
        "outputs": ["models/v71/v71_ticket_pack_export_model.json", "reports/v71_ticket_pack_summary.json", "reports/v71_ticket_pack.csv"],
        "feeds": ["Step 73"],
        "role": "Подготвя printable/export пакет за игра с физически фишове.",
        "ensemble_source": False,
    },
    {
        "step": "73",
        "label": "Представяне на пакета",
        "category": "Performance after draw",
        "script": "scripts/v73_build_ticket_pack_performance_tracker.py",
        "datasets": ["data/historical_draws.csv"],
        "inputs": ["reports/v71_ticket_pack.csv"],
        "outputs": ["models/v73/v73_ticket_pack_performance_tracker_model.json", "reports/v73_ticket_pack_performance_summary.json", "reports/v73_ticket_pack_performance_history.csv"],
        "feeds": ["Step 74"],
        "role": "Проверява активния пакет срещу реални тиражи преди dataset refresh.",
        "ensemble_source": False,
    },
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_text_if_changed(path: Path, content: str, encoding: str = "utf-8") -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            if path.read_text(encoding=encoding) == content:
                return False
        except UnicodeError:
            pass
    path.write_text(content, encoding=encoding)
    return True


def _stable_json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


def _state_hash(data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    import io

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    content = "\ufeff" + output.getvalue()
    _write_text_if_changed(path, content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    _write_text_if_changed(path, _stable_json_text(data) + "\n", encoding="utf-8")


def rel_exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def rel_mtime(rel_path: str) -> float:
    path = ROOT / rel_path
    if not path.exists():
        return 0.0
    return path.stat().st_mtime


def rel_mtime_iso(rel_path: str) -> str:
    ts = rel_mtime(rel_path)
    if not ts:
        return ""
    return datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def max_mtime(paths: list[str]) -> float:
    times = [rel_mtime(path) for path in paths if rel_exists(path)]
    return max(times) if times else 0.0


def dataset_info(rel_path: str) -> dict[str, Any]:
    path = ROOT / rel_path
    rows = read_csv_rows(path)
    info: dict[str, Any] = {
        "path": rel_path,
        "exists": path.exists(),
        "rows": len(rows),
        "latest_date": "",
        "latest_year": "",
        "latest_draw_no": "",
        "latest_numbers": "",
        "mtime": rel_mtime_iso(rel_path),
    }
    if not rows:
        return info

    latest = rows[-1]
    info["latest_date"] = latest.get("date", "")
    info["latest_year"] = latest.get("year", "")
    info["latest_draw_no"] = latest.get("draw_no", latest.get("draw_number", ""))
    numbers = []
    for key in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        value = str(latest.get(key, "")).strip()
        if value:
            numbers.append(value)
    info["latest_numbers"] = ",".join(numbers)
    return info


def compare_primary_datasets(dataset_infos: list[dict[str, Any]]) -> dict[str, Any]:
    existing = [item for item in dataset_infos if item.get("exists")]
    row_counts = sorted({item.get("rows") for item in existing})
    latest_keys = sorted({
        (item.get("latest_date"), item.get("latest_draw_no"), item.get("latest_numbers"))
        for item in existing
    })
    return {
        "datasets_checked": len(dataset_infos),
        "datasets_existing": len(existing),
        "row_counts": row_counts,
        "latest_draw_signatures": [" | ".join(str(part) for part in key) for key in latest_keys],
        "rows_synced": len(row_counts) == 1 and len(existing) == len(dataset_infos),
        "latest_draw_synced": len(latest_keys) == 1 and len(existing) == len(dataset_infos),
    }


def node_status(node: dict[str, Any]) -> dict[str, Any]:
    script = str(node.get("script", ""))
    outputs = [str(item) for item in node.get("outputs", [])]
    inputs = [str(item) for item in node.get("inputs", [])]
    datasets = [str(item) for item in node.get("datasets", [])]
    dependencies = sorted(set(inputs + datasets))

    script_exists = rel_exists(script)
    missing_inputs = [path for path in dependencies if not rel_exists(path)]
    missing_outputs = [path for path in outputs if not rel_exists(path)]

    latest_input_ts = max_mtime(dependencies)
    latest_output_ts = max_mtime(outputs)
    stale = bool(latest_input_ts and latest_output_ts and latest_output_ts + 1 < latest_input_ts)

    if not script_exists or missing_inputs or missing_outputs:
        sync_status = "Липсва файл"
        status_rank = 0
    elif stale:
        sync_status = "Нужно обновяване"
        status_rank = 1
    else:
        sync_status = "Синхронизиран"
        status_rank = 2

    return {
        "step": node.get("step", ""),
        "label": node.get("label", ""),
        "category": node.get("category", ""),
        "script": script,
        "script_exists": script_exists,
        "datasets": "; ".join(datasets),
        "inputs": "; ".join(inputs),
        "outputs": "; ".join(outputs),
        "outputs_present": len(missing_outputs) == 0,
        "dependencies_present": len(missing_inputs) == 0,
        "missing_inputs": "; ".join(missing_inputs),
        "missing_outputs": "; ".join(missing_outputs),
        "latest_input_mtime": datetime.fromtimestamp(latest_input_ts).isoformat(timespec="seconds") if latest_input_ts else "",
        "latest_output_mtime": datetime.fromtimestamp(latest_output_ts).isoformat(timespec="seconds") if latest_output_ts else "",
        "sync_status": sync_status,
        "status_rank": status_rank,
        "feeds": "; ".join(node.get("feeds", [])),
        "role": node.get("role", ""),
        "ensemble_source": bool(node.get("ensemble_source", False)),
        "safe_note": SAFE_NOTE,
    }


def dependency_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node in nodes:
        current = f"Step {node.get('step')}"
        for dataset in node.get("datasets", []):
            rows.append({"from": dataset, "to": current, "type": "dataset", "description": "Dataset вход"})
        for dependency in node.get("inputs", []):
            if dependency in node.get("datasets", []):
                continue
            rows.append({"from": dependency, "to": current, "type": "artifact", "description": "Входен model/report artifact"})
        for feed in node.get("feeds", []):
            rows.append({"from": current, "to": feed, "type": "feeds", "description": "Изходът помага на следващ слой"})
    return rows


def build_model_dependency_sync_center() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    V74_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    dataset_infos = [dataset_info(path) for path in PRIMARY_DATASETS]
    dataset_sync = compare_primary_datasets(dataset_infos)
    statuses = [node_status(node) for node in MODEL_NODES]
    edges = dependency_edges(MODEL_NODES)

    synced_count = sum(1 for row in statuses if row["sync_status"] == "Синхронизиран")
    stale_count = sum(1 for row in statuses if row["sync_status"] == "Нужно обновяване")
    missing_count = sum(1 for row in statuses if row["sync_status"] == "Липсва файл")
    ensemble_sources = sum(1 for row in statuses if row.get("ensemble_source"))

    pipeline_chain = [
        "Данни от тиражи",
        "Базови модели и статистики",
        "Историческа проверка и performance",
        "Надеждност на моделите",
        "Адаптивни тегла",
        "Weighted ensemble",
        "Генератор на фишове",
        "Portfolio optimizer",
        "Пакет за игра",
        "Проверка след реален тираж",
        "Model Dependency & Sync Center",
    ]

    all_synced = dataset_sync["rows_synced"] and dataset_sync["latest_draw_synced"] and missing_count == 0 and stale_count == 0

    summary: dict[str, Any] = {
        "step": "74",
        "name": "Контрол на синхрона между моделите",
        "status": "Синхронизиран" if all_synced else "Има нужда от преглед",
        "all_synced": all_synced,
        "models_checked": len(statuses),
        "synced_models": synced_count,
        "stale_models": stale_count,
        "missing_models": missing_count,
        "ensemble_sources": ensemble_sources,
        "datasets": dataset_infos,
        "dataset_sync": dataset_sync,
        "pipeline_chain": pipeline_chain,
        "generated_at": "",
        "state_hash": "",
        "generated_reports": [
            "reports/v74_model_dependency_summary.json",
            "reports/v74_model_dependency_summary.md",
            "reports/v74_model_dependency_map.csv",
            "reports/v74_model_sync_status.csv",
            "models/model_registry.json",
            "models/v74/v74_model_dependency_sync_center_model.json",
        ],
        "safe_note": SAFE_NOTE,
    }

    stable_payload = {
        "summary_without_runtime": {
            key: value
            for key, value in summary.items()
            if key not in {"generated_at", "state_hash"}
        },
        "sync_status": statuses,
        "dependency_edges": edges,
    }
    state_hash = _state_hash(stable_payload)
    existing_summary = _read_json_if_exists(SUMMARY_PATH)
    if existing_summary.get("state_hash") == state_hash and existing_summary.get("generated_at"):
        generated_at = str(existing_summary.get("generated_at"))
    else:
        generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summary["generated_at"] = generated_at
    summary["state_hash"] = state_hash

    registry = {
        "summary": summary,
        "primary_datasets": dataset_infos,
        "models": MODEL_NODES,
        "sync_status": statuses,
        "dependency_edges": edges,
    }

    write_csv(STATUS_PATH, statuses, [
        "step", "label", "category", "script", "script_exists", "datasets", "inputs", "outputs",
        "outputs_present", "dependencies_present", "missing_inputs", "missing_outputs",
        "latest_input_mtime", "latest_output_mtime", "sync_status", "feeds", "role", "ensemble_source", "safe_note",
    ])
    write_csv(MAP_PATH, edges, ["from", "to", "type", "description"])
    write_json(SUMMARY_PATH, summary)
    write_json(REGISTRY_PATH, registry)
    write_json(MODEL_PATH, registry)

    md = [
        "# Step 74 — Контрол на синхрона между моделите",
        "",
        f"Статус: **{summary['status']}**",
        f"Проверени модели/слоеве: **{summary['models_checked']}**",
        f"Синхронизирани: **{summary['synced_models']}**",
        f"Нуждаят се от обновяване: **{summary['stale_models']}**",
        f"Липсващи: **{summary['missing_models']}**",
        f"Ensemble източници: **{summary['ensemble_sources']}**",
        "",
        "**Важно:** Step 74 е контролен и диагностичен слой. Той не е прогноза и не е гаранция за печалба.",
        "",
        "## Dataset синхрон",
        "",
        "| Dataset | Редове | Последна дата | Последен тираж | Последни числа |",
        "|---|---:|---|---|---|",
    ]
    for item in dataset_infos:
        md.append(f"| `{item['path']}` | {item['rows']} | {item['latest_date']} | {item['latest_draw_no']} | {item['latest_numbers']} |")

    md.extend(["", "## Синхрон на моделите", "", "| Step | Име | Категория | Статус | Помага на |", "|---:|---|---|---|---|"])
    for row in statuses:
        md.append(f"| {row['step']} | {row['label']} | {row['category']} | {row['sync_status']} | {row['feeds']} |")

    md.extend(["", "## Pipeline логика", ""])
    for index, item in enumerate(pipeline_chain, start=1):
        md.append(f"{index}. {item}")

    _write_text_if_changed(SUMMARY_MD_PATH, "\n".join(md) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = build_model_dependency_sync_center()
    print("STEP74_BUILD_OK")
    print("STATUS", result.get("status"))
    print("MODELS_CHECKED", result.get("models_checked"))
    print("SYNCED_MODELS", result.get("synced_models"))
    print("STALE_MODELS", result.get("stale_models"))
    print("MISSING_MODELS", result.get("missing_models"))

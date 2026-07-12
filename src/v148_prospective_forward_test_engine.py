from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import random
import statistics
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from src.v144_reproducible_experiment_registry_engine import (
    canonical_hash,
    dataset_descriptor,
    dataset_sha256,
    load_draws,
    sha256_file,
)
from src.v145_experimental_neural_dynamics_engine import (
    DRAW_SIZE,
    TOTAL_NUMBERS,
    _binary_draw,
    _build_reservoir,
    _package_metrics,
    _score_package,
    _uniform_random_package,
    _update_state,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "models" / "v148_prospective_forward_test_policy.json"
STATUS_PATH = ROOT / "models" / "v148_prospective_forward_test_status.json"
LEDGER_PATH = ROOT / "data" / "prospective_forward_test_ledger.jsonl"
SUMMARY_JSON_PATH = ROOT / "reports" / "v148_forward_test_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v148_forward_test_summary.md"
LEDGER_INDEX_CSV_PATH = ROOT / "reports" / "v148_forward_test_ledger_index.csv"
SETTLEMENTS_CSV_PATH = ROOT / "reports" / "v148_forward_test_settlements.csv"
ACTIVE_PACKAGES_CSV_PATH = ROOT / "reports" / "v148_active_locked_evaluation_packages.csv"
FORWARD_TEST_DIR = ROOT / "reports" / "forward_tests" / "v148"
STEP146_POLICY_PATH = ROOT / "models" / "v146_controlled_neural_robustness_policy.json"
STEP146_STATUS_PATH = ROOT / "models" / "v146_controlled_neural_robustness_status.json"
STEP147_STATUS_PATH = ROOT / "models" / "v147_experimental_evidence_decision_status.json"

METHOD_KEYS = (
    "neural_dynamics_frozen_ensemble",
    "frequency_walk_forward",
    "recency_weighted_walk_forward",
    "recent_window_frequency",
    "frequency_recency_blend",
)

SAFE_NOTE_BG = (
    "Step 148 е prospective research protocol. Заключените evaluation packages не са production препоръки "
    "или реални фишове. Протоколът не доказва предвидимост и не гарантира печалба."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _write_json_if_changed(path: Path, payload: dict[str, Any]) -> None:
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if path.is_file() and path.read_bytes() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def _write_text_if_changed(path: Path, text: str) -> None:
    data = text.encode("utf-8")
    if path.is_file() and path.read_bytes() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def _write_csv_if_changed(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    _write_text_if_changed(path, buffer.getvalue())


def _normalize_scores(scores: np.ndarray) -> np.ndarray:
    values = np.nan_to_num(np.asarray(scores, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)
    minimum = float(np.min(values))
    maximum = float(np.max(values))
    if maximum - minimum <= 1e-12:
        return np.ones_like(values)
    return (values - minimum) / (maximum - minimum)


def _seed_from_text(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16) % (2**31 - 1)


def _draw_key(draw: dict[str, Any]) -> str:
    return f"{int(draw.get('year', 0))}-{int(draw.get('draw_number', 0))}"


def _expected_next_draw_key(draws: list[dict[str, Any]]) -> str:
    latest = draws[-1]
    return f"{int(latest['year'])}-{int(latest['draw_number']) + 1}"


def _policy_source() -> dict[str, Any]:
    step146_policy = _load_json(STEP146_POLICY_PATH)
    step146_status = _load_json(STEP146_STATUS_PATH)
    step147_status = _load_json(STEP147_STATUS_PATH)
    if step146_status.get("status") != "completed":
        raise ValueError("Step 146 status is not completed")
    if step147_status.get("status") != "completed":
        raise ValueError("Step 147 status is not completed")
    if step147_status.get("production_promotion_approved") is not False:
        raise ValueError("Step 147 production promotion must remain blocked")
    if step147_status.get("current_neural_configuration_action") != "pause_and_archive":
        raise ValueError("Step 147 neural configuration is not paused and archived")

    frozen = dict(step146_policy.get("default_configuration") or {})
    required = {
        "seeds", "package_size", "random_trials_per_run", "frequency_pool_size", "recency_decay",
        "recent_window_draws", "blend_frequency_weight", "reservoir_size", "leak_rate",
        "spectral_radius", "input_scale", "bias_scale", "ridge_alpha", "score_power",
    }
    missing = sorted(required - set(frozen))
    if missing:
        raise ValueError(f"Step 146 frozen configuration is incomplete: {missing}")

    code_paths = [
        ROOT / "src/v145_experimental_neural_dynamics_engine.py",
        ROOT / "src/v146_controlled_neural_robustness_engine.py",
        ROOT / "src/v148_prospective_forward_test_engine.py",
    ]
    frozen_code_locks = {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in code_paths}
    source_locks = {
        "step146_experiment_id": step146_status.get("experiment_id"),
        "step146_configuration_sha256": step146_status.get("configuration_sha256"),
        "step146_result_signature_sha256": step146_status.get("result_signature_sha256"),
        "step147_decision_id": step147_status.get("decision_id"),
        "step147_result_signature_sha256": step147_status.get("result_signature_sha256"),
        "forward_scoring_code_sha256": canonical_hash(frozen_code_locks),
    }
    protocol_core = {
        "target_settled_draws": 30,
        "milestones": [10, 20, 30],
        "one_active_lock_at_a_time": True,
        "score_before_learn": True,
        "learn_after_score_with_frozen_algorithm": True,
        "draws_without_predraw_lock_are_excluded": True,
        "automatic_production_promotion": False,
        "evaluation_package_size": int(frozen["package_size"]),
        "uniform_random_trials": 50,
        "methods": list(METHOD_KEYS) + ["uniform_random_mean"],
    }
    protocol_id = f"PFT-148-{canonical_hash({'source_locks': source_locks, 'protocol': protocol_core})[:20]}"
    return {
        "step": 148,
        "name": "Prospective Forward-Test Lock & Untouched Future Draw Ledger",
        "protocol_id": protocol_id,
        "protocol": protocol_core,
        "frozen_configuration": frozen,
        "frozen_source_locks": source_locks,
        "frozen_code_locks": frozen_code_locks,
        "guardrails": {
            "historical_backfill": "forbidden",
            "forecast_lock_after_target_publication": "invalid",
            "same_configuration_retuning": "forbidden",
            "parameter_changes_during_protocol": "forbidden",
            "score_before_learn": "required",
            "missing_predraw_lock": "draw_excluded",
            "ledger_mutation": "detected_by_sha256_chain",
            "personal_journal_access": "forbidden",
            "production_pipeline_access": "forbidden",
            "real_ticket_generation": "forbidden",
            "final_promotion": "requires_new_research_decision_after_30_eligible_draws",
        },
        "safe_note_bg": SAFE_NOTE_BG,
    }


def ensure_policy() -> dict[str, Any]:
    expected = _policy_source()
    if POLICY_PATH.is_file():
        current = _load_json(POLICY_PATH)
        if current != expected:
            raise ValueError("Stored Step 148 policy differs from frozen Step 146/147 source locks")
    else:
        _write_json_if_changed(POLICY_PATH, expected)
    return expected


def _event_hash(event: dict[str, Any]) -> str:
    return canonical_hash({key: value for key, value in event.items() if key != "event_sha256"})


def load_ledger() -> list[dict[str, Any]]:
    if not LEDGER_PATH.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(LEDGER_PATH.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"Ledger row {line_number} is not a JSON object")
        rows.append(value)
    return rows


def verify_ledger(events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = load_ledger() if events is None else events
    failures: list[str] = []
    previous = "GENESIS"
    seen_hashes: set[str] = set()
    lock_ids: set[str] = set()
    settled_lock_ids: set[str] = set()
    protocol_ids: set[str] = set()

    for index, event in enumerate(rows, start=1):
        if int(event.get("event_index", -1)) != index:
            failures.append(f"event_index:{index}")
        if event.get("previous_event_sha256") != previous:
            failures.append(f"previous_hash:{index}")
        calculated = _event_hash(event)
        if event.get("event_sha256") != calculated:
            failures.append(f"event_hash:{index}")
        if calculated in seen_hashes:
            failures.append(f"duplicate_event_hash:{index}")
        seen_hashes.add(calculated)
        previous = calculated
        event_type = event.get("event_type")
        protocol_id = str(event.get("protocol_id") or "")
        if protocol_id:
            protocol_ids.add(protocol_id)
        if event_type == "forecast_locked":
            lock_id = str(event.get("lock_id") or "")
            if not lock_id or lock_id in lock_ids:
                failures.append(f"invalid_lock_id:{index}")
            lock_ids.add(lock_id)
            artifact_path = ROOT / str(event.get("artifact_path") or "")
            if not artifact_path.is_file():
                failures.append(f"missing_lock_artifact:{lock_id}")
            elif sha256_file(artifact_path) != event.get("artifact_sha256"):
                failures.append(f"lock_artifact_hash:{lock_id}")
            else:
                artifact = _load_json(artifact_path)
                if artifact.get("lock_id") != lock_id:
                    failures.append(f"lock_artifact_id:{lock_id}")
                if canonical_hash(artifact.get("forecast_commitment") or {}) != event.get("forecast_signature_sha256"):
                    failures.append(f"forecast_signature:{lock_id}")
        elif event_type == "forecast_settled":
            lock_id = str(event.get("lock_id") or "")
            if lock_id not in lock_ids or lock_id in settled_lock_ids:
                failures.append(f"invalid_settlement_reference:{index}")
            settled_lock_ids.add(lock_id)
        elif event_type != "protocol_initialized":
            failures.append(f"unknown_event_type:{index}:{event_type}")

    active = sorted(lock_ids - settled_lock_ids)
    if len(active) > 1:
        failures.append("multiple_active_locks")
    if len(protocol_ids) > 1:
        failures.append("multiple_protocol_ids")
    if rows and rows[0].get("event_type") != "protocol_initialized":
        failures.append("first_event_not_protocol_initialized")
    return {
        "ok": not failures,
        "failures": failures,
        "event_count": len(rows),
        "last_event_sha256": previous,
        "lock_count": len(lock_ids),
        "settled_count": len(settled_lock_ids),
        "active_lock_ids": active,
        "protocol_ids": sorted(protocol_ids),
    }


def _append_event(event: dict[str, Any]) -> dict[str, Any]:
    rows = load_ledger()
    chain = verify_ledger(rows)
    if not chain["ok"]:
        raise ValueError("Ledger chain is invalid: " + "; ".join(chain["failures"]))
    full = dict(event)
    full["event_index"] = len(rows) + 1
    full["previous_event_sha256"] = chain["last_event_sha256"]
    full["event_sha256"] = _event_hash(full)
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(full, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return full


def _initialize_protocol(policy: dict[str, Any], draws: list[dict[str, Any]]) -> dict[str, Any]:
    events = load_ledger()
    if events:
        return events[0]
    dataset = dataset_descriptor(draws)
    event = {
        "event_type": "protocol_initialized",
        "protocol_id": policy["protocol_id"],
        "created_at_utc": utc_now(),
        "policy_path": POLICY_PATH.relative_to(ROOT).as_posix(),
        "policy_sha256": sha256_file(POLICY_PATH),
        "initial_dataset": dataset,
        "target_settled_draws": policy["protocol"]["target_settled_draws"],
        "milestones": policy["protocol"]["milestones"],
        "frozen_source_locks": policy["frozen_source_locks"],
        "production_promotion": "blocked",
        "safe_note_bg": SAFE_NOTE_BG,
    }
    return _append_event(event)


def _neural_scores(draws: list[dict[str, Any]], config: dict[str, Any], seed: int) -> np.ndarray:
    run_config = dict(config)
    run_config["seed"] = int(seed)
    parameters = _build_reservoir(run_config)
    size = int(config["reservoir_size"])
    feature_size = size + 1
    leak = float(config["leak_rate"])
    ridge = float(config["ridge_alpha"])
    state = np.zeros(size, dtype=np.float64)
    state = _update_state(state, draws[0]["numbers"], parameters, leak)
    gram = np.zeros((feature_size, feature_size), dtype=np.float64)
    targets = np.zeros((feature_size, TOTAL_NUMBERS), dtype=np.float64)
    for index in range(1, len(draws)):
        feature = np.concatenate(([1.0], state))
        target = _binary_draw(draws[index]["numbers"])
        gram += np.outer(feature, feature)
        targets += np.outer(feature, target)
        state = _update_state(state, draws[index]["numbers"], parameters, leak)
    identity = np.eye(feature_size, dtype=np.float64)
    identity[0, 0] = 0.0
    coefficients = np.linalg.solve(gram + ridge * identity, targets)
    raw = np.concatenate(([1.0], state)) @ coefficients
    return 1.0 / (1.0 + np.exp(-np.clip(raw, -40.0, 40.0)))


def build_score_vectors(draws: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, np.ndarray]:
    frequency = np.zeros(TOTAL_NUMBERS, dtype=np.float64)
    recency = np.zeros(TOTAL_NUMBERS, dtype=np.float64)
    recent = np.zeros(TOTAL_NUMBERS, dtype=np.float64)
    queue: deque[np.ndarray] = deque(maxlen=int(config["recent_window_draws"]))
    decay = float(config["recency_decay"])
    for draw in draws:
        binary = _binary_draw(draw["numbers"])
        frequency += binary
        recency = decay * recency + binary
        if len(queue) == queue.maxlen:
            recent -= queue[0]
        queue.append(binary)
        recent += binary
    blend_weight = float(config["blend_frequency_weight"])
    blend = blend_weight * _normalize_scores(frequency) + (1.0 - blend_weight) * _normalize_scores(recency)
    seed_scores = [_neural_scores(draws, config, int(seed)) for seed in config["seeds"]]
    neural = np.mean(np.stack(seed_scores, axis=0), axis=0)
    return {
        "neural_dynamics_frozen_ensemble": neural,
        "frequency_walk_forward": frequency,
        "recency_weighted_walk_forward": recency,
        "recent_window_frequency": recent,
        "frequency_recency_blend": blend,
    }


def build_forecast_commitment(
    draws: list[dict[str, Any]],
    policy: dict[str, Any],
    *,
    target_sequence_index: int | None = None,
    expected_draw_key: str | None = None,
    source_dataset_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = policy["frozen_configuration"]
    dataset = dict(source_dataset_identity) if source_dataset_identity is not None else dataset_descriptor(draws)
    target_index = int(target_sequence_index or (len(draws) + 1))
    target_key = str(expected_draw_key or _expected_next_draw_key(draws))
    lock_core = {
        "protocol_id": policy["protocol_id"],
        "source_dataset_sha256": dataset["sha256"],
        "source_dataset_rows": dataset["row_count"],
        "source_latest_draw": dataset["latest_draw"],
        "target_sequence_index": target_index,
        "expected_draw_key": target_key,
        "frozen_source_locks": policy["frozen_source_locks"],
        "frozen_configuration_sha256": canonical_hash(config),
    }
    lock_id = f"LOCK-148-{canonical_hash(lock_core)[:24]}"
    vectors = build_score_vectors(draws, config)
    methods: dict[str, Any] = {}
    package_size = int(policy["protocol"]["evaluation_package_size"])
    pool_size = int(config["frequency_pool_size"])
    score_power = float(config["score_power"])
    for method_index, method in enumerate(METHOD_KEYS, start=1):
        scores = vectors[method]
        seed = _seed_from_text(f"{lock_id}:{method}:{method_index}")
        package = _score_package(scores, package_size, seed, score_power, pool_size)
        ranking = [index + 1 for index in sorted(range(TOTAL_NUMBERS), key=lambda i: (-float(scores[i]), i))]
        rounded_scores = [round(float(value), 12) for value in scores]
        methods[method] = {
            "ranking": ranking,
            "evaluation_package": package,
            "score_vector_sha256": canonical_hash(rounded_scores),
            "package_sha256": canonical_hash(package),
            "package_seed": seed,
        }
    random_trials: list[dict[str, Any]] = []
    for trial in range(int(policy["protocol"]["uniform_random_trials"])):
        seed = _seed_from_text(f"{lock_id}:uniform_random:{trial + 1}")
        package = _uniform_random_package(package_size, seed)
        random_trials.append({"trial": trial + 1, "seed": seed, "evaluation_package": package})
    return {
        **lock_core,
        "lock_id": lock_id,
        "methods": methods,
        "uniform_random_trials": random_trials,
        "guardrails": {
            "evaluation_only": True,
            "production_recommendation": False,
            "real_ticket": False,
            "score_before_learn": True,
            "parameters_frozen": True,
        },
    }


def _lock_artifact_path(lock_id: str) -> Path:
    return FORWARD_TEST_DIR / f"{lock_id}.json"


def active_lock(events: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    rows = load_ledger() if events is None else events
    locks = {str(event.get("lock_id")): event for event in rows if event.get("event_type") == "forecast_locked"}
    settled = {str(event.get("lock_id")) for event in rows if event.get("event_type") == "forecast_settled"}
    active_ids = [lock_id for lock_id in locks if lock_id not in settled]
    if len(active_ids) > 1:
        raise ValueError("Ledger contains multiple active locks")
    return locks.get(active_ids[0]) if active_ids else None


def lock_next_draw_forecast(*, locked_at_utc: str | None = None) -> dict[str, Any]:
    policy = ensure_policy()
    draws = load_draws()
    _initialize_protocol(policy, draws)
    events = load_ledger()
    chain = verify_ledger(events)
    if not chain["ok"]:
        raise ValueError("Ledger chain is invalid: " + "; ".join(chain["failures"]))
    existing = active_lock(events)
    if existing is not None:
        refresh_reports()
        return {"ok": True, "created": False, "reason": "active_lock_exists", "lock_event": existing}
    if chain["settled_count"] >= int(policy["protocol"]["target_settled_draws"]):
        refresh_reports()
        return {"ok": True, "created": False, "reason": "protocol_complete", "lock_event": None}

    commitment = build_forecast_commitment(draws, policy)
    artifact = {
        "step": 148,
        "artifact_type": "prospective_locked_evaluation_forecast",
        "lock_id": commitment["lock_id"],
        "locked_at_utc": locked_at_utc or utc_now(),
        "forecast_commitment": commitment,
        "safe_note_bg": SAFE_NOTE_BG,
    }
    artifact_path = _lock_artifact_path(commitment["lock_id"])
    _write_json_if_changed(artifact_path, artifact)
    event = _append_event(
        {
            "event_type": "forecast_locked",
            "protocol_id": policy["protocol_id"],
            "lock_id": commitment["lock_id"],
            "locked_at_utc": artifact["locked_at_utc"],
            "source_dataset_sha256": commitment["source_dataset_sha256"],
            "source_dataset_rows": commitment["source_dataset_rows"],
            "source_latest_draw": commitment["source_latest_draw"],
            "target_sequence_index": commitment["target_sequence_index"],
            "expected_draw_key": commitment["expected_draw_key"],
            "forecast_signature_sha256": canonical_hash(commitment),
            "artifact_path": artifact_path.relative_to(ROOT).as_posix(),
            "artifact_sha256": sha256_file(artifact_path),
            "production_promotion": "blocked",
        }
    )
    refresh_reports()
    return {"ok": True, "created": True, "reason": "forecast_locked", "lock_event": event}


def _settlement_for_lock(lock_event: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    artifact_path = ROOT / str(lock_event["artifact_path"])
    artifact = _load_json(artifact_path)
    commitment = artifact["forecast_commitment"]
    method_results: dict[str, Any] = {}
    for method in METHOD_KEYS:
        package = commitment["methods"][method]["evaluation_package"]
        best, total = _package_metrics(package, actual["numbers"])
        method_results[method] = {"best_hits": best, "total_hits": total}
    random_results: list[dict[str, Any]] = []
    for trial in commitment["uniform_random_trials"]:
        best, total = _package_metrics(trial["evaluation_package"], actual["numbers"])
        random_results.append({"trial": trial["trial"], "best_hits": best, "total_hits": total})
    return {
        "actual_draw_event_id": actual.get("draw_event_id"),
        "actual_draw_key": _draw_key(actual),
        "actual_date": actual.get("date", ""),
        "actual_numbers": list(actual["numbers"]),
        "method_results": method_results,
        "uniform_random_mean_best_hits": round(statistics.fmean(row["best_hits"] for row in random_results), 9),
        "uniform_random_mean_total_hits": round(statistics.fmean(row["total_hits"] for row in random_results), 9),
        "uniform_random_trials": len(random_results),
        "random_result_signature_sha256": canonical_hash(random_results),
    }


def settle_available_locked_forecast(*, auto_lock_next: bool = True, settled_at_utc: str | None = None) -> dict[str, Any]:
    policy = ensure_policy()
    draws = load_draws()
    events = load_ledger()
    chain = verify_ledger(events)
    if not chain["ok"]:
        raise ValueError("Ledger chain is invalid: " + "; ".join(chain["failures"]))
    lock_event = active_lock(events)
    if lock_event is None:
        locked = lock_next_draw_forecast()
        return {"ok": True, "settled": False, "reason": "no_active_lock", "lock_result": locked}
    target_index = int(lock_event["target_sequence_index"])
    if len(draws) < target_index:
        refresh_reports()
        return {"ok": True, "settled": False, "reason": "target_not_in_dataset", "lock_event": lock_event}
    actual = draws[target_index - 1]
    actual_key = _draw_key(actual)
    if actual_key != lock_event.get("expected_draw_key"):
        raise ValueError(
            f"Locked expected draw {lock_event.get('expected_draw_key')} but dataset sequence contains {actual_key}; "
            "manual protocol review is required"
        )
    settlement = _settlement_for_lock(lock_event, actual)
    skipped_after_target = max(0, len(draws) - target_index)
    event = _append_event(
        {
            "event_type": "forecast_settled",
            "protocol_id": policy["protocol_id"],
            "lock_id": lock_event["lock_id"],
            "settled_at_utc": settled_at_utc or utc_now(),
            "target_sequence_index": target_index,
            "expected_draw_key": lock_event["expected_draw_key"],
            "source_forecast_signature_sha256": lock_event["forecast_signature_sha256"],
            "settlement": settlement,
            "settlement_signature_sha256": canonical_hash(settlement),
            "unlocked_draws_after_target_excluded": skipped_after_target,
            "score_before_learn_confirmed": True,
            "production_promotion": "blocked",
        }
    )
    next_lock = None
    if auto_lock_next and verify_ledger()["settled_count"] < int(policy["protocol"]["target_settled_draws"]):
        next_lock = lock_next_draw_forecast()
    refresh_reports()
    return {"ok": True, "settled": True, "reason": "forecast_settled", "settlement_event": event, "next_lock": next_lock}


def _event_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        settlement = event.get("settlement") or {}
        rows.append(
            {
                "event_index": event.get("event_index"),
                "event_type": event.get("event_type"),
                "event_sha256": event.get("event_sha256"),
                "previous_event_sha256": event.get("previous_event_sha256"),
                "protocol_id": event.get("protocol_id"),
                "lock_id": event.get("lock_id", ""),
                "event_time_utc": event.get("created_at_utc") or event.get("locked_at_utc") or event.get("settled_at_utc") or "",
                "expected_draw_key": event.get("expected_draw_key", ""),
                "actual_draw_key": settlement.get("actual_draw_key", ""),
                "target_sequence_index": event.get("target_sequence_index", ""),
            }
        )
    return rows


def _settlement_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") != "forecast_settled":
            continue
        settlement = event.get("settlement") or {}
        row: dict[str, Any] = {
            "eligible_draw_number": len(rows) + 1,
            "lock_id": event.get("lock_id"),
            "draw_key": settlement.get("actual_draw_key"),
            "date": settlement.get("actual_date"),
            "actual_numbers": " ".join(str(value) for value in settlement.get("actual_numbers", [])),
            "uniform_random_mean_best_hits": settlement.get("uniform_random_mean_best_hits"),
            "unlocked_draws_after_target_excluded": event.get("unlocked_draws_after_target_excluded", 0),
        }
        for method in METHOD_KEYS:
            result = (settlement.get("method_results") or {}).get(method, {})
            row[f"{method}_best_hits"] = result.get("best_hits")
            row[f"{method}_total_hits"] = result.get("total_hits")
        rows.append(row)
    return rows


def _aggregate_settlements(rows: list[dict[str, Any]]) -> dict[str, Any]:
    aggregates: dict[str, Any] = {}
    for method in METHOD_KEYS:
        values = [float(row[f"{method}_best_hits"]) for row in rows if row.get(f"{method}_best_hits") not in (None, "")]
        aggregates[method] = {
            "eligible_draws": len(values),
            "average_best_hits": round(statistics.fmean(values), 9) if values else None,
            "best_hits_distribution": {str(hit): sum(value == hit for value in values) for hit in range(DRAW_SIZE + 1)},
        }
    random_values = [float(row["uniform_random_mean_best_hits"]) for row in rows if row.get("uniform_random_mean_best_hits") not in (None, "")]
    aggregates["uniform_random_mean"] = {
        "eligible_draws": len(random_values),
        "average_best_hits": round(statistics.fmean(random_values), 9) if random_values else None,
    }
    return aggregates


def refresh_reports() -> dict[str, Any]:
    policy = ensure_policy()
    events = load_ledger()
    chain = verify_ledger(events)
    if not chain["ok"]:
        raise ValueError("Ledger chain is invalid: " + "; ".join(chain["failures"]))
    settlements = _settlement_rows(events)
    active = active_lock(events)
    target = int(policy["protocol"]["target_settled_draws"])
    settled_count = len(settlements)
    milestones = [int(value) for value in policy["protocol"]["milestones"]]
    next_milestone = next((value for value in milestones if settled_count < value), None)
    completed = settled_count >= target
    latest_event_time = ""
    if events:
        latest = events[-1]
        latest_event_time = latest.get("created_at_utc") or latest.get("locked_at_utc") or latest.get("settled_at_utc") or ""
    summary = {
        "step": 148,
        "status": "completed" if completed else "active",
        "protocol_id": policy["protocol_id"],
        "policy_sha256": sha256_file(POLICY_PATH),
        "ledger_path": LEDGER_PATH.relative_to(ROOT).as_posix(),
        "ledger_event_count": len(events),
        "ledger_last_event_sha256": chain["last_event_sha256"],
        "ledger_integrity_ok": chain["ok"],
        "target_settled_draws": target,
        "eligible_settled_draws": settled_count,
        "remaining_draws": max(0, target - settled_count),
        "milestones": milestones,
        "next_milestone": next_milestone,
        "active_lock": None if active is None else {
            "lock_id": active.get("lock_id"),
            "locked_at_utc": active.get("locked_at_utc"),
            "expected_draw_key": active.get("expected_draw_key"),
            "target_sequence_index": active.get("target_sequence_index"),
            "source_dataset_sha256": active.get("source_dataset_sha256"),
            "source_dataset_rows": active.get("source_dataset_rows"),
            "forecast_signature_sha256": active.get("forecast_signature_sha256"),
            "artifact_path": active.get("artifact_path"),
        },
        "aggregate_results": _aggregate_settlements(settlements),
        "frozen_source_locks": policy["frozen_source_locks"],
        "last_protocol_event_at_utc": latest_event_time,
        "decision": {
            "production_promotion": "blocked",
            "automatic_promotion": False,
            "final_research_decision_required_after_draws": target,
            "current_neural_configuration": "frozen_evaluation_only",
        },
        "guardrails": policy["guardrails"],
        "production_integration_enabled": False,
        "real_ticket_generation_enabled": False,
        "personal_journal_used": False,
        "historical_backfill_performed": False,
        "safe_note_bg": SAFE_NOTE_BG,
    }
    deterministic = {key: value for key, value in summary.items() if key != "last_protocol_event_at_utc"}
    summary["result_signature_sha256"] = canonical_hash(deterministic)
    _write_json_if_changed(SUMMARY_JSON_PATH, summary)

    status = {
        "step": 148,
        "status": summary["status"],
        "protocol_id": summary["protocol_id"],
        "policy_sha256": summary["policy_sha256"],
        "result_signature_sha256": summary["result_signature_sha256"],
        "ledger_event_count": summary["ledger_event_count"],
        "ledger_integrity_ok": summary["ledger_integrity_ok"],
        "eligible_settled_draws": settled_count,
        "target_settled_draws": target,
        "remaining_draws": summary["remaining_draws"],
        "active_lock_id": (summary["active_lock"] or {}).get("lock_id"),
        "active_expected_draw_key": (summary["active_lock"] or {}).get("expected_draw_key"),
        "production_promotion_approved": False,
        "automatic_production_promotion": False,
        "production_integration_enabled": False,
        "real_ticket_generation_enabled": False,
        "personal_journal_used": False,
        "historical_backfill_performed": False,
        "safe_note_bg": SAFE_NOTE_BG,
    }
    _write_json_if_changed(STATUS_PATH, status)

    event_rows = _event_rows(events)
    _write_csv_if_changed(
        LEDGER_INDEX_CSV_PATH,
        event_rows,
        [
            "event_index", "event_type", "event_sha256", "previous_event_sha256", "protocol_id", "lock_id",
            "event_time_utc", "expected_draw_key", "actual_draw_key", "target_sequence_index",
        ],
    )
    settlement_fields = [
        "eligible_draw_number", "lock_id", "draw_key", "date", "actual_numbers", "uniform_random_mean_best_hits",
        "unlocked_draws_after_target_excluded",
    ]
    for method in METHOD_KEYS:
        settlement_fields.extend([f"{method}_best_hits", f"{method}_total_hits"])
    _write_csv_if_changed(SETTLEMENTS_CSV_PATH, settlements, settlement_fields)

    active_rows: list[dict[str, Any]] = []
    if active is not None:
        artifact = _load_json(ROOT / active["artifact_path"])
        commitment = artifact["forecast_commitment"]
        for method in METHOD_KEYS:
            for line_number, combo in enumerate(commitment["methods"][method]["evaluation_package"], start=1):
                active_rows.append(
                    {
                        "lock_id": active["lock_id"],
                        "expected_draw_key": active["expected_draw_key"],
                        "method": method,
                        "evaluation_line": line_number,
                        "numbers": " ".join(str(value) for value in combo),
                    }
                )
    _write_csv_if_changed(
        ACTIVE_PACKAGES_CSV_PATH,
        active_rows,
        ["lock_id", "expected_draw_key", "method", "evaluation_line", "numbers"],
    )

    aggregate = summary["aggregate_results"]
    lines = [
        "# Step 148 — Prospective Forward-Test Lock & Untouched Future Draw Ledger",
        "",
        f"- Protocol ID: `{summary['protocol_id']}`",
        f"- Status: **{summary['status'].upper()}**",
        f"- Eligible settled draws: **{settled_count} / {target}**",
        f"- Remaining draws: **{summary['remaining_draws']}**",
        f"- Next milestone: **{next_milestone if next_milestone is not None else 'complete'}**",
        f"- Ledger events: **{len(events)}**",
        f"- Ledger integrity: **{'PASS' if chain['ok'] else 'FAIL'}**",
        f"- Production promotion: **BLOCKED**",
        "",
        "## Active pre-draw lock",
        "",
    ]
    if active is None:
        lines.append("No active lock.")
    else:
        lines.extend(
            [
                f"- Lock ID: `{active['lock_id']}`",
                f"- Locked at UTC: `{active['locked_at_utc']}`",
                f"- Expected draw: **{active['expected_draw_key']}**",
                f"- Source dataset rows: **{active['source_dataset_rows']}**",
                f"- Forecast signature: `{active['forecast_signature_sha256']}`",
            ]
        )
    lines.extend(["", "## Prospective aggregate results", "", "| Method | Draws | Average best hits |", "|---|---:|---:|"])
    for method in (*METHOD_KEYS, "uniform_random_mean"):
        row = aggregate[method]
        value = row.get("average_best_hits")
        lines.append(f"| {method} | {row.get('eligible_draws', 0)} | {'—' if value is None else f'{value:.6f}'} |")
    lines.extend(
        [
            "",
            "## Protocol protections",
            "",
            "- Forecasts are committed before the target draw enters the canonical dataset.",
            "- Ledger events form an append-only SHA-256 chain.",
            "- Draws without a valid pre-draw lock are excluded rather than backfilled.",
            "- The Step 146 configuration is frozen; no parameter tuning is allowed.",
            "- Results are scored before the observed draw can be used for the next lock.",
            "- No automatic production promotion is possible after any milestone.",
            "",
            SAFE_NOTE_BG,
            "",
        ]
    )
    _write_text_if_changed(SUMMARY_MD_PATH, "\n".join(lines))
    return summary


def initialize_step148() -> dict[str, Any]:
    policy = ensure_policy()
    draws = load_draws()
    protocol_event = _initialize_protocol(policy, draws)
    lock_result = lock_next_draw_forecast()
    summary = refresh_reports()
    return {"ok": True, "protocol_event": protocol_event, "lock_result": lock_result, "summary": summary}


def deterministic_forecast_signature_for_active_lock() -> str:
    policy = ensure_policy()
    events = load_ledger()
    active = active_lock(events)
    if active is None:
        return ""
    source_rows = int(active["source_dataset_rows"])
    draws = load_draws()
    if len(draws) < source_rows:
        raise ValueError("Current dataset is shorter than the active lock source dataset")
    source_draws = draws[:source_rows]
    source_identity = {
        "path": "data/v41_canonical_draw_events.csv",
        "sha256": str(active["source_dataset_sha256"]),
        "row_count": source_rows,
        "first_draw": _draw_key(source_draws[0]),
        "latest_draw": _draw_key(source_draws[-1]),
        "latest_draw_date": source_draws[-1].get("date", ""),
    }
    commitment = build_forecast_commitment(
        source_draws,
        policy,
        target_sequence_index=int(active["target_sequence_index"]),
        expected_draw_key=str(active["expected_draw_key"]),
        source_dataset_identity=source_identity,
    )
    return canonical_hash(commitment)

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "v90" / "v90_selector_source_expansion_model.json"
SUMMARY_JSON_PATH = ROOT / "reports" / "v90_selector_source_expansion_summary.json"
SUMMARY_MD_PATH = ROOT / "reports" / "v90_selector_source_expansion_summary.md"
CANDIDATES_CSV_PATH = ROOT / "reports" / "v90_expanded_selector_candidates.csv"
INVENTORY_CSV_PATH = ROOT / "reports" / "v90_selector_source_inventory.csv"

TOTAL_NUMBERS = 49
DRAW_SIZE = 6

TEXT_NUMBER_KEYS = (
    "numbers",
    "combination",
    "selected_numbers",
    "main_numbers",
    "ticket_numbers",
    "numbers_compact",
    "numbers_display",
    "field_numbers",
)

NUMBER_FIELD_GROUPS = (
    ("n1", "n2", "n3", "n4", "n5", "n6"),
    ("number_1", "number_2", "number_3", "number_4", "number_5", "number_6"),
    ("main_1", "main_2", "main_3", "main_4", "main_5", "main_6"),
)


def _t(value: str) -> str:
    return value.encode("utf-8").decode("unicode_escape")


TRUSTED_SOURCE_SPECS: tuple[dict[str, str], ...] = (
    {
        "path": "models/v44_1/v44_1_final_ensemble_ticket_prediction.json",
        "label": _t(r"\u0424\u0438\u043d\u0430\u043b\u0435\u043d \u0430\u043d\u0441\u0430\u043c\u0431\u043b\u043e\u0432 \u0444\u0438\u0448"),
        "group": _t(r"\u0424\u0438\u043d\u0430\u043b\u043d\u0438 \u0444\u0438\u0448\u043e\u0432\u0435"),
    },
    {
        "path": "models/v45/v45_final_prediction_tickets.json",
        "label": _t(r"\u0424\u0438\u043d\u0430\u043b\u043d\u0438 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u043d\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438"),
        "group": _t(r"\u0424\u0438\u043d\u0430\u043b\u043d\u0438 \u0444\u0438\u0448\u043e\u0432\u0435"),
    },
    {
        "path": "reports/v59_smart_ticket_builder_2_sample.csv",
        "label": _t(r"\u0418\u043d\u0442\u0435\u043b\u0438\u0433\u0435\u043d\u0442\u0435\u043d \u0433\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440 2"),
        "group": _t(r"\u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440\u0438"),
    },
    {
        "path": "reports/v60_ticket_builder_2_export_sample.csv",
        "label": _t(r"\u0415\u043a\u0441\u043f\u043e\u0440\u0442 \u043e\u0442 \u0438\u043d\u0442\u0435\u043b\u0438\u0433\u0435\u043d\u0442\u043d\u0438\u044f \u0433\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440"),
        "group": _t(r"\u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440\u0438"),
    },
    {
        "path": "reports/v67_weighted_ticket_builder_tickets.csv",
        "label": _t(r"\u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440 \u0441 \u043f\u0440\u0435\u0442\u0435\u0433\u043b\u0435\u043d\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0438"),
        "group": _t(r"\u041f\u0440\u0435\u0442\u0435\u0433\u043b\u0435\u043d\u0438 \u043c\u043e\u0434\u0435\u043b\u0438"),
    },
    {
        "path": "reports/v68_weighted_portfolio_tickets.csv",
        "label": _t(r"\u041e\u043f\u0442\u0438\u043c\u0438\u0437\u0438\u0440\u0430\u043d \u043f\u043e\u0440\u0442\u0444\u0435\u0439\u043b \u0441 \u043f\u0440\u0435\u0442\u0435\u0433\u043b\u0435\u043d\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0438"),
        "group": _t(r"\u041f\u0440\u0435\u0442\u0435\u0433\u043b\u0435\u043d\u0438 \u043c\u043e\u0434\u0435\u043b\u0438"),
    },
    {
        "path": "reports/v69_candidate_portfolio_tickets.csv",
        "label": _t(r"\u041f\u043e\u0434\u043e\u0431\u0440\u0435\u043d \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442 \u043f\u043e\u0440\u0442\u0444\u0435\u0439\u043b"),
        "group": _t(r"\u041f\u043e\u0440\u0442\u0444\u0435\u0439\u043b\u0438"),
    },
    {
        "path": "reports/v70_applied_candidate_portfolio_tickets.csv",
        "label": _t(r"\u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d \u043f\u043e\u0434\u043e\u0431\u0440\u0435\u043d \u043f\u043e\u0440\u0442\u0444\u0435\u0439\u043b"),
        "group": _t(r"\u041f\u043e\u0440\u0442\u0444\u0435\u0439\u043b\u0438"),
    },
    {
        "path": "reports/v71_ticket_pack.csv",
        "label": _t(r"\u041f\u0430\u043a\u0435\u0442 \u0437\u0430 \u0438\u0433\u0440\u0430"),
        "group": _t(r"\u041f\u0430\u043a\u0435\u0442\u0438 \u0437\u0430 \u0438\u0433\u0440\u0430"),
    },
    {
        "path": "reports/v75_neural_candidate_tickets.csv",
        "label": _t(r"\u041d\u0435\u0432\u0440\u043e\u043d\u043d\u0438 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438"),
        "group": _t(r"\u041d\u0435\u0432\u0440\u043e\u043d\u043d\u0438 \u0441\u0438\u0433\u043d\u0430\u043b\u0438"),
    },
    {
        "path": "reports/v78_selected_ticket_plan.csv",
        "label": _t(r"\u0424\u0438\u043d\u0430\u043b\u0435\u043d \u043f\u043b\u0430\u043d \u0437\u0430 \u0438\u0433\u0440\u0430"),
        "group": _t(r"\u0424\u0438\u043d\u0430\u043b\u043d\u0438 \u0444\u0438\u0448\u043e\u0432\u0435"),
    },
    {
        "path": "reports/v79_export_ticket_pack.csv",
        "label": _t(r"\u0415\u043a\u0441\u043f\u043e\u0440\u0442\u0435\u043d \u043f\u0430\u043a\u0435\u0442 \u0437\u0430 \u0438\u0433\u0440\u0430"),
        "group": _t(r"\u041f\u0430\u043a\u0435\u0442\u0438 \u0437\u0430 \u0438\u0433\u0440\u0430"),
    },
    {
        "path": "reports/v84_model_source_candidates.csv",
        "label": _t(r"\u0421\u043d\u0430\u043f\u0448\u043e\u0442 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u043d\u0438 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u0438"),
        "group": _t(r"\u041c\u043e\u0434\u0435\u043b\u043d\u0438 \u0441\u043d\u0430\u043f\u0448\u043e\u0442\u0438"),
    },
    {
        "path": "models/v88/v88_anti_zero_coverage_model.json",
        "label": _t(r"\u0417\u0430\u0449\u0438\u0442\u0435\u043d \u0444\u0438\u0448 \u0441 \u0448\u0438\u0440\u043e\u043a\u043e \u043f\u043e\u043a\u0440\u0438\u0442\u0438\u0435"),
        "group": _t(r"\u0417\u0430\u0449\u0438\u0442\u043d\u0438 \u043f\u0430\u043a\u0435\u0442\u0438"),
        "preferred_key": "candidate",
    },
)


def _source_id(path: Path, preferred_key: str = "") -> str:
    rel = path.relative_to(ROOT).as_posix()
    if preferred_key:
        rel = f"{rel}:{preferred_key}"
    clean = re.sub(r"[^A-Za-z0-9]+", "_", rel).strip("_").lower()
    return clean[:100]


def safe_comb(n: int, k: int) -> int:
    if n < 0 or k < 0 or k > n:
        return 0
    try:
        return math.comb(n, k)
    except ValueError:
        return 0


def calculate_empty_risk(unique_covered_numbers: int) -> dict[str, float]:
    unique = max(0, min(TOTAL_NUMBERS, int(unique_covered_numbers)))
    denominator = safe_comb(TOTAL_NUMBERS, DRAW_SIZE)
    numerator = safe_comb(TOTAL_NUMBERS - unique, DRAW_SIZE)
    empty = numerator / denominator if denominator else 0.0
    return {
        "empty_risk_percent": empty * 100.0,
        "at_least_one_hit_percent": (1.0 - empty) * 100.0,
    }


def _parse_int(value: Any) -> int | None:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if 1 <= number <= TOTAL_NUMBERS else None


def normalize_combination(value: Any) -> list[int]:
    if isinstance(value, str):
        raw_values = re.findall(r"\d+", value)
    elif isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        return []

    numbers: list[int] = []
    seen: set[int] = set()
    for item in raw_values:
        number = _parse_int(item)
        if number is not None and number not in seen:
            seen.add(number)
            numbers.append(number)

    clean = sorted(numbers)
    return clean if len(clean) == DRAW_SIZE else []


def _dedupe_combinations(combinations: list[list[int]]) -> list[list[int]]:
    result: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    for combo in combinations:
        clean = normalize_combination(combo)
        key = tuple(clean)
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _preferred_payload(payload: Any, preferred_key: str) -> Any:
    if not preferred_key:
        return payload
    current = payload
    for part in preferred_key.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _extract_from_payload(payload: Any) -> list[list[int]]:
    results: list[list[int]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for keys in NUMBER_FIELD_GROUPS:
                if all(key in value for key in keys):
                    combo = normalize_combination([value.get(key) for key in keys])
                    if combo:
                        results.append(combo)

            for key in TEXT_NUMBER_KEYS:
                if key in value:
                    maybe = value.get(key)
                    combo = normalize_combination(maybe)
                    if combo:
                        results.append(combo)
                    elif isinstance(maybe, (dict, list, tuple)):
                        walk(maybe)

            for nested in value.values():
                if isinstance(nested, (dict, list, tuple)):
                    walk(nested)

        elif isinstance(value, (list, tuple)):
            combo = normalize_combination(value)
            if combo:
                results.append(combo)
            for item in value:
                if isinstance(item, (dict, list, tuple)):
                    walk(item)

    walk(payload)
    return _dedupe_combinations(results)


def _extract_from_csv(path: Path) -> list[list[int]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return []

    combinations: list[list[int]] = []

    for row in rows:
        for keys in NUMBER_FIELD_GROUPS:
            if all(key in row and str(row.get(key, "")).strip() for key in keys):
                combo = normalize_combination([row.get(key) for key in keys])
                if combo:
                    combinations.append(combo)

        for key in TEXT_NUMBER_KEYS:
            if key in row and str(row.get(key, "")).strip():
                combo = normalize_combination(row.get(key))
                if combo:
                    combinations.append(combo)

    return _dedupe_combinations(combinations)


def _extract_from_path(path: Path, preferred_key: str = "") -> list[list[int]]:
    if path.suffix.lower() == ".csv":
        return _extract_from_csv(path)
    payload = _load_json(path)
    payload = _preferred_payload(payload, preferred_key)
    return _extract_from_payload(payload)


def _unique_numbers(combinations: list[list[int]]) -> set[int]:
    return {number for combo in combinations for number in combo}


def _candidate_from_spec(spec: dict[str, str]) -> dict[str, Any] | None:
    rel = spec["path"]
    path = ROOT / rel
    if not path.exists():
        return None
    preferred_key = spec.get("preferred_key", "")
    combos = _dedupe_combinations(_extract_from_path(path, preferred_key))
    if not combos:
        return None

    if len(combos) > 8:
        combos = combos[:8]

    unique_count = len(_unique_numbers(combos))
    risk = calculate_empty_risk(unique_count)

    return {
        "package_id": _source_id(path, preferred_key),
        "package_label": spec["label"],
        "source_group": spec.get("group", ""),
        "source_path": rel,
        "source_kind": "trusted_ticket_source",
        "preferred_key": preferred_key,
        "combinations": combos,
        "total_combinations": len(combos),
        "unique_covered_numbers": unique_count,
        "empty_risk_percent": round(risk["empty_risk_percent"], 6),
        "at_least_one_hit_percent": round(risk["at_least_one_hit_percent"], 6),
    }


def load_expanded_candidate_packages() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[tuple[int, ...], ...]] = set()

    for spec in TRUSTED_SOURCE_SPECS:
        candidate = _candidate_from_spec(spec)
        if not candidate:
            continue
        signature = tuple(tuple(combo) for combo in candidate["combinations"])
        if signature in seen:
            continue
        seen.add(signature)
        candidates.append(candidate)

    candidates.sort(
        key=lambda item: (
            int(item.get("unique_covered_numbers", 0)),
            int(item.get("total_combinations", 0)),
            -float(item.get("empty_risk_percent", 100.0)),
        ),
        reverse=True,
    )
    return candidates


def build_source_expansion_model() -> dict[str, Any]:
    candidates = load_expanded_candidate_packages()
    return {
        "step": 90,
        "status": "OK",
        "title_bg": _t(r"\u0420\u0430\u0437\u0448\u0438\u0440\u0435\u043d\u0430 \u0438\u043d\u0442\u0435\u0433\u0440\u0430\u0446\u0438\u044f \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u043d\u0438\u0442\u0435 \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442\u0438"),
        "candidate_count": len(candidates),
        "source_count": len(TRUSTED_SOURCE_SPECS),
        "trusted_source_count": len(TRUSTED_SOURCE_SPECS),
        "candidates": candidates,
        "safe_note_bg": _t(r"\u0422\u043e\u0432\u0430 \u0435 \u0441\u0442\u0440\u043e\u0433\u043e \u043f\u043e\u0434\u0431\u0440\u0430\u043d \u0441\u043f\u0438\u0441\u044a\u043a \u043e\u0442 \u0440\u0435\u0430\u043b\u043d\u0438 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442-\u0444\u0438\u0448\u043e\u0432\u0435. \u041d\u0435 \u0435 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430 \u0438 \u043d\u0435 \u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f."),
    }


def save_source_expansion_outputs(model: dict[str, Any]) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    MODEL_PATH.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "step": model["step"],
        "status": model["status"],
        "candidate_count": model["candidate_count"],
        "source_count": model["source_count"],
        "safe_note_bg": model["safe_note_bg"],
    }
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with CANDIDATES_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "package_id",
            "package_label",
            "source_group",
            "source_kind",
            "source_path",
            "preferred_key",
            "total_combinations",
            "unique_covered_numbers",
            "empty_risk_percent",
            "at_least_one_hit_percent",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in model["candidates"]:
            writer.writerow({key: candidate.get(key, "") for key in fieldnames})

    with INVENTORY_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "package_label",
            "source_group",
            "source_path",
            "preferred_key",
            "total_combinations",
            "unique_covered_numbers",
            "empty_risk_percent",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in model["candidates"]:
            writer.writerow({key: candidate.get(key, "") for key in fieldnames})

    lines = [
        f"# {model['title_bg']}",
        "",
        f"- {_t(r'\u041f\u043e\u0434\u0431\u0440\u0430\u043d\u0438 \u0438\u0437\u0442\u043e\u0447\u043d\u0438\u0446\u0438')}: **{model['source_count']}**",
        f"- {_t(r'\u041d\u0430\u043c\u0435\u0440\u0435\u043d\u0438 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442-\u0444\u0438\u0448\u043e\u0432\u0435')}: **{model['candidate_count']}**",
        "",
        model["safe_note_bg"],
    ]
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_and_save() -> dict[str, Any]:
    model = build_source_expansion_model()
    save_source_expansion_outputs(model)
    return model


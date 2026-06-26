from __future__ import annotations

from pathlib import Path
import csv
import json
import re
import html

import streamlit as st
from src.v89_1_user_menu_final_selection_integration import render_v89_1_user_menu_final_selection

try:
    import pandas as pd
except Exception:
    pd = None

ROOT = Path(__file__).resolve().parents[1]

def U(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")

PAGE_NAME = U(r"\u041f\u043e\u0442\u0440\u0435\u0431\u0438\u0442\u0435\u043b\u0441\u043a\u043e \u043c\u0435\u043d\u044e")

UI = {
    "title": PAGE_NAME,
    "caption": U(r"\u0421\u0438\u043d\u0442\u0435\u0437\u0438\u0440\u0430\u043d \u043f\u043e\u0433\u043b\u0435\u0434 \u0437\u0430 \u0441\u043b\u0435\u0434\u0432\u0430\u0449 \u0442\u0438\u0440\u0430\u0436, \u0444\u0438\u0448\u043e\u0432\u0435\u0442\u0435 \u0438 \u0430\u043a\u0442\u0438\u0432\u043d\u0438\u0442\u0435 \u043c\u043e\u0434\u0435\u043b\u0438. \u0422\u043e\u0432\u0430 \u0435 \u043f\u043e\u0442\u0440\u0435\u0431\u0438\u0442\u0435\u043b\u0441\u043a\u0438 \u0435\u043a\u0440\u0430\u043d \u2014 \u043f\u043e-\u044f\u0441\u0435\u043d, \u043f\u043e-\u043f\u043e\u0434\u0440\u0435\u0434\u0435\u043d \u0438 \u0431\u0435\u0437 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438 \u0448\u0443\u043c."),
    "quick_path": U(r"\u0411\u044a\u0440\u0437 \u043f\u044a\u0442 \u0437\u0430 \u043f\u043e\u0442\u0440\u0435\u0431\u0438\u0442\u0435\u043b\u044f"),
    "quick_1_title": U(r"\u0421\u043b\u0435\u0434\u0432\u0430\u0449 \u0442\u0438\u0440\u0430\u0436"),
    "quick_1_text": U(r"\u0422\u0443\u043a \u0432\u0438\u0436\u0434\u0430\u0448 \u043e\u0441\u043d\u043e\u0432\u043d\u0438\u044f \u0438 \u0440\u0435\u0437\u0435\u0440\u0432\u043d\u0438\u044f \u0444\u0438\u0448 \u0437\u0430 \u0438\u0433\u0440\u0430."),
    "quick_2_title": U(r"\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043d\u0430 \u0444\u0438\u0448"),
    "quick_2_text": U(r"\u0418\u0437\u043f\u043e\u043b\u0437\u0432\u0430\u0439 \u0441\u0435\u043a\u0446\u0438\u044f\u0442\u0430 \u0437\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430, \u0430\u043a\u043e \u0438\u0441\u043a\u0430\u0448 \u0434\u0430 \u0441\u0440\u0430\u0432\u043d\u0438\u0448 \u0444\u0438\u0448 \u0441 \u0440\u0435\u0430\u043b\u0435\u043d \u0442\u0438\u0440\u0430\u0436."),
    "quick_3_title": U(r"\u0410\u043d\u0430\u043b\u0438\u0437 \u0438 \u043c\u043e\u0434\u0435\u043b\u0438"),
    "quick_3_text": U(r"\u0410\u043a\u043e \u0438\u0441\u043a\u0430\u0448 \u0434\u0430 \u0432\u0438\u0434\u0438\u0448 \u0437\u0430\u0449\u043e \u0441\u0430 \u0438\u0437\u0431\u0440\u0430\u043d\u0438 \u0442\u0435\u0437\u0438 \u0447\u0438\u0441\u043b\u0430, \u043e\u0442\u0432\u043e\u0440\u0438 \u0430\u043d\u0430\u043b\u0438\u0437\u0438\u0442\u0435 \u0438 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435."),

    "main_ticket": U(r"\u041e\u0441\u043d\u043e\u0432\u0435\u043d \u0444\u0438\u0448"),
    "reserve_ticket": U(r"\u0420\u0435\u0437\u0435\u0440\u0432\u0435\u043d \u0444\u0438\u0448"),
    "ticket_note": U(r"\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438\u0442\u0435 \u0441\u0430 \u043f\u043e\u0434\u0440\u0435\u0434\u0435\u043d\u0438 \u0432\u0438\u0437\u0443\u0430\u043b\u043d\u043e \u043a\u0430\u0442\u043e \u0444\u0438\u0448 \u0437\u0430 \u043f\u0440\u0435\u0433\u043b\u0435\u0434. \u0422\u043e\u0432\u0430 \u043d\u0435 \u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430."),
    "model_numbers": U(r"\u0427\u0438\u0441\u043b\u0430 \u043e\u0442 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435"),
    "active_models": U(r"\u0410\u043a\u0442\u0438\u0432\u043d\u0438 \u043c\u043e\u0434\u0435\u043b\u0438"),
    "latest_draw": U(r"\u041f\u043e\u0441\u043b\u0435\u0434\u0435\u043d \u0442\u0438\u0440\u0430\u0436"),
    "dataset_rows": U(r"\u0420\u0435\u0434\u043e\u0432\u0435 \u0432 \u043d\u0430\u0431\u043e\u0440\u0430"),
    "registry_models": U(r"\u0420\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u0430\u043d\u0438 \u043c\u043e\u0434\u0435\u043b\u0438"),
    "active_count": U(r"\u0410\u043a\u0442\u0438\u0432\u043d\u0438 \u0441\u043b\u043e\u0435\u0432\u0435"),
    "safe": U(r"\u0412\u0430\u0436\u043d\u043e: \u0442\u043e\u0437\u0438 \u0435\u043a\u0440\u0430\u043d \u0435 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0430 \u0438 \u043f\u043e\u043c\u043e\u0449\u043d\u0430 \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0430. \u0422\u043e\u0439 \u043d\u0435 \u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430."),
    "no_ticket": U(r"\u041d\u0435 \u0441\u0430 \u043d\u0430\u043c\u0435\u0440\u0435\u043d\u0438 \u0433\u043e\u0442\u043e\u0432\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u0437\u0430 \u0444\u0438\u0448. \u041c\u043e\u0436\u0435\u0448 \u0434\u0430 \u0433\u0438 \u0432\u0438\u0434\u0438\u0448 \u0432 \u201e\u0424\u0438\u043d\u0430\u043b\u0435\u043d \u043f\u043b\u0430\u043d\u201c \u0438\u043b\u0438 \u0432 \u0441\u0432\u044a\u0440\u0437\u0430\u043d\u0438\u0442\u0435 \u043f\u0440\u0435\u0434\u0438\u043a\u0442\u0438\u0432\u043d\u0438 \u0441\u0435\u043a\u0446\u0438\u0438."),
    "sources": U(r"\u0418\u0437\u0442\u043e\u0447\u043d\u0438\u0446\u0438 \u0437\u0430 \u043f\u043e\u043a\u0430\u0437\u0430\u043d\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u0430"),
    "combo": U(r"\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f"),
    "model_strip_note": U(r"\u0412\u043e\u0434\u0435\u0449\u0438 \u0447\u0438\u0441\u043b\u0430 \u043e\u0442 \u0440\u0430\u0437\u043b\u0438\u0447\u043d\u0438\u0442\u0435 \u0430\u043a\u0442\u0438\u0432\u043d\u0438 \u043c\u043e\u0434\u0435\u043b\u0438. \u0422\u043e\u0432\u0430 \u0435 \u043f\u043e\u043c\u043e\u0449\u0435\u043d \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0441\u0438\u0433\u043d\u0430\u043b, \u043d\u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f."),
}

V86_SUMMARY_PATH = ROOT / "reports" / "v86_model_registry_summary.json"
V106_SUMMARY_PATH = ROOT / "reports" / "v106_post_draw_status_sync_summary.json"
V107_SUMMARY_PATH = ROOT / "reports" / "v107_model_training_policy_refresh_control_summary.json"
CANONICAL_DATA_PATH = ROOT / "data" / "v41_canonical_draw_events.csv"
HISTORICAL_DATA_PATH = ROOT / "data" / "historical_draws.csv"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"

CSS = """
<style>
.v87-grid-quick {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
    margin: 0.5rem 0 1rem 0;
}
.v87-quick-card {
    border: 1px solid rgba(120,120,120,0.25);
    border-radius: 16px;
    padding: 16px 16px 14px 16px;
    background: linear-gradient(180deg, rgba(32,36,42,0.94), rgba(24,28,34,0.94));
    box-shadow: 0 8px 20px rgba(0,0,0,0.16);
}
.v87-quick-title {
    font-weight: 700;
    font-size: 1rem;
    margin-bottom: 8px;
}
.v87-quick-text {
    font-size: 0.92rem;
    line-height: 1.45;
    opacity: 0.95;
}
.v87-ticket-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    margin-top: 0.5rem;
}
.v87-ticket-card {
    border: 1px solid rgba(120,120,120,0.22);
    border-radius: 18px;
    background: linear-gradient(180deg, rgba(28,30,36,0.98), rgba(18,20,24,0.98));
    padding: 16px;
    box-shadow: 0 10px 24px rgba(0,0,0,0.18);
}
.v87-ticket-title {
    font-weight: 700;
    font-size: 1rem;
    margin-bottom: 6px;
}
.v87-ticket-note {
    font-size: 0.88rem;
    opacity: 0.86;
    margin-bottom: 12px;
}
.v87-ticket-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}
.v87-ticket-label {
    min-width: 110px;
    font-size: 0.88rem;
    opacity: 0.90;
    font-weight: 600;
}
.v87-number-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
}
.v87-number-box {
    width: 52px;
    height: 52px;
    min-width: 52px;
    border-radius: 999px;
    background:
        radial-gradient(circle at 32% 24%, rgba(255, 246, 176, 0.98) 0%, rgba(244, 210, 84, 0.98) 34%, rgba(184, 144, 24, 0.98) 72%, rgba(120, 91, 10, 0.98) 100%);
    color: #090909;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    font-size: 1.05rem;
    line-height: 1;
    letter-spacing: 0.01em;
    border: 1px solid rgba(255, 232, 129, 0.72);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.45),
        inset 0 -10px 16px rgba(91, 67, 5, 0.28),
        0 8px 18px rgba(212, 175, 55, 0.20),
        0 0 0 1px rgba(212, 175, 55, 0.10);
    text-shadow: 0 1px 0 rgba(255, 255, 255, 0.28);
}
.v87-model-card {
    border: 1px solid rgba(120,120,120,0.22);
    border-radius: 16px;
    background: linear-gradient(180deg, rgba(24,28,34,0.96), rgba(18,22,28,0.96));
    padding: 14px 16px;
    margin-bottom: 12px;
}
.v87-model-title {
    font-weight: 700;
    margin-bottom: 6px;
}
.v87-model-source {
    font-size: 0.82rem;
    opacity: 0.82;
    margin-top: 8px;
}

@media (max-width: 640px) {
    .v87-number-box {
        width: 44px;
        height: 44px;
        min-width: 44px;
        font-size: 0.95rem;
    }
    .v87-number-strip {
        gap: 8px;
    }
}

@media (max-width: 980px) {
    .v87-grid-quick,
    .v87-ticket-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""

def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None

def _read_csv_rows(path: Path):
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _safe_int_for_live_status(value, default=None):
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def _pick_for_live_status(row, names, default=""):
    if not isinstance(row, dict):
        return default
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def _numbers_from_live_row(row):
    if not isinstance(row, dict):
        return []
    column_sets = [
        ["n1", "n2", "n3", "n4", "n5", "n6"],
        ["num1", "num2", "num3", "num4", "num5", "num6"],
        ["number_1", "number_2", "number_3", "number_4", "number_5", "number_6"],
        ["ball1", "ball2", "ball3", "ball4", "ball5", "ball6"],
        ["number1", "number2", "number3", "number4", "number5", "number6"],
    ]
    for columns in column_sets:
        values = [_safe_int_for_live_status(row.get(col)) for col in columns]
        if all(value is not None for value in values):
            values = [int(value) for value in values]
            if len(values) == 6 and len(set(values)) == 6 and all(1 <= n <= 49 for n in values):
                return sorted(values)

    text_value = _pick_for_live_status(row, ["numbers", "draw_numbers", "combination"], "")
    if text_value:
        cleaned = (
            text_value.replace("[", "")
            .replace("]", "")
            .replace(";", ",")
            .replace("|", ",")
            .replace(" ", ",")
        )
        values = []
        for part in cleaned.split(","):
            number = _safe_int_for_live_status(part)
            if number is not None:
                values.append(int(number))
        if len(values) >= 6:
            values = values[:6]
            if len(set(values)) == 6 and all(1 <= n <= 49 for n in values):
                return sorted(values)
    return []


def _latest_snapshot_from_csv(path: Path):
    rows = _read_csv_rows(path)
    if not rows:
        return None

    def sort_key(row):
        date = _pick_for_live_status(row, ["date", "draw_date"], "")
        year = _safe_int_for_live_status(_pick_for_live_status(row, ["year"], ""), 0) or 0
        draw_no = _safe_int_for_live_status(
            _pick_for_live_status(row, ["draw_number", "draw_no", "draw_id", "drawing_no"], ""),
            0,
        ) or 0
        return (date, year, draw_no)

    latest = max(rows, key=sort_key)
    return {
        "dataset_rows": len(rows),
        "latest_draw_date": _pick_for_live_status(latest, ["date", "draw_date"], "-"),
        "latest_draw_no": _pick_for_live_status(latest, ["draw_number", "draw_no", "draw_id", "drawing_no"], "-"),
        "latest_numbers": _numbers_from_live_row(latest),
        "source": path.relative_to(ROOT).as_posix(),
    }


def _load_live_user_menu_status():
    v107 = _load_json(V107_SUMMARY_PATH) or {}
    v107_dataset = v107.get("dataset") if isinstance(v107, dict) else None
    if isinstance(v107_dataset, dict):
        latest = v107_dataset.get("latest_draw") or {}
        row_counts = v107_dataset.get("row_counts") or {}
        dataset_rows = v107_dataset.get("dataset_rows") or row_counts.get("historical")
        latest_date = latest.get("date") if isinstance(latest, dict) else None
        latest_numbers = latest.get("numbers") if isinstance(latest, dict) else None
        if dataset_rows and latest_date:
            return {
                "dataset_rows": dataset_rows,
                "latest_draw_date": latest_date,
                "latest_draw_no": latest.get("draw_no") if isinstance(latest, dict) else "-",
                "latest_numbers": latest_numbers or [],
                "source": "reports/v107_model_training_policy_refresh_control_summary.json",
            }

    v106 = _load_json(V106_SUMMARY_PATH) or {}
    v106_dataset = v106.get("dataset") if isinstance(v106, dict) else None
    if isinstance(v106_dataset, dict):
        dataset_rows = v106_dataset.get("rows")
        latest_date = v106_dataset.get("latest_date")
        latest_numbers = v106_dataset.get("latest_numbers") or []
        if dataset_rows and latest_date:
            return {
                "dataset_rows": dataset_rows,
                "latest_draw_date": latest_date,
                "latest_draw_no": "-",
                "latest_numbers": latest_numbers,
                "source": "reports/v106_post_draw_status_sync_summary.json",
            }

    for path in [CANONICAL_DATA_PATH, HISTORICAL_DATA_PATH]:
        snapshot = _latest_snapshot_from_csv(path)
        if snapshot:
            return snapshot

    return {}

def _as_int_list(value):
    if not isinstance(value, (list, tuple)):
        return None
    numbers = []
    for item in value:
        try:
            n = int(str(item).strip())
        except Exception:
            return None
        if not (1 <= n <= 49):
            return None
        numbers.append(n)
    if len(numbers) != 6:
        return None
    if len(set(numbers)) != 6:
        return None
    return numbers

def _extract_combos_from_text(text):
    found = []
    if not text:
        return found
    for raw in re.findall(r'(?:(?:^|[^0-9])((?:[1-9]|[1-4][0-9])(?:[,\s;/\-]+(?:[1-9]|[1-4][0-9])){5})(?:[^0-9]|$))', str(text)):
        parts = re.split(r'[,;\s/\-]+', raw.strip())
        if len(parts) == 6:
            try:
                nums = [int(p) for p in parts]
            except Exception:
                continue
            if all(1 <= x <= 49 for x in nums) and len(set(nums)) == 6:
                found.append(nums)
    return found

def _walk_for_combos(obj, out):
    if len(out) >= 24:
        return
    direct = _as_int_list(obj)
    if direct is not None:
        out.append(direct)
        return

    if isinstance(obj, dict):
        for key, value in obj.items():
            if len(out) >= 24:
                return
            _walk_for_combos(value, out)
            if isinstance(value, str):
                for combo in _extract_combos_from_text(value):
                    out.append(combo)
                    if len(out) >= 24:
                        return
    elif isinstance(obj, list):
        for item in obj:
            if len(out) >= 24:
                return
            _walk_for_combos(item, out)
    elif isinstance(obj, str):
        for combo in _extract_combos_from_text(obj):
            out.append(combo)
            if len(out) >= 24:
                return

def _dedupe_combos(combos):
    cleaned = []
    seen = set()
    for combo in combos:
        key = tuple(combo)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(combo)
    return cleaned

def _json_files_for_prefix(prefix):
    files = []
    for base in [REPORTS_DIR, MODELS_DIR]:
        if not base.exists():
            continue
        for path in sorted(base.rglob(f"{prefix}*.json")):
            files.append(path)
    return files

def _discover_ticket_combos():
    prefixes = ["v78", "v73", "v71", "v70", "v45", "v66", "v75", "v44_1"]
    collected = []
    sources = []
    for prefix in prefixes:
        for path in _json_files_for_prefix(prefix):
            data = _load_json(path)
            if not data:
                continue
            combos = []
            _walk_for_combos(data, combos)
            combos = _dedupe_combos(combos)
            if combos:
                for combo in combos:
                    collected.append(combo)
                sources.append(path.relative_to(ROOT).as_posix())
                if len(_dedupe_combos(collected)) >= 8:
                    final = _dedupe_combos(collected)[:8]
                    return final, sources
    return _dedupe_combos(collected)[:8], sources

def _normalize_number_strip(values):
    if not isinstance(values, (list, tuple)):
        return None
    numbers = []
    for item in values:
        try:
            n = int(str(item).strip())
        except Exception:
            return None
        if not (1 <= n <= 49):
            return None
        numbers.append(n)
    if not numbers:
        return None
    unique = []
    seen = set()
    for n in numbers:
        if n in seen:
            continue
        seen.add(n)
        unique.append(n)
    return unique[:8]

def _walk_for_named_numbers(obj, preferred_keys):
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_norm = str(key).strip().lower()
            if key_norm in preferred_keys:
                nums = _normalize_number_strip(value)
                if nums:
                    return nums
            result = _walk_for_named_numbers(value, preferred_keys)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = _walk_for_named_numbers(item, preferred_keys)
            if result:
                return result
    return None

def _derive_from_combos(combos):
    freq = {}
    for combo in combos:
        for n in combo:
            freq[n] = freq.get(n, 0) + 1
    ranked = sorted(freq.items(), key=lambda item: (-item[1], item[0]))
    return [n for n, _ in ranked[:8]]

def _discover_model_strips():
    config = [
        ("v45", U(r"\u041f\u0440\u043e\u0433\u043d\u043e\u0437\u043d\u043e \u0442\u0430\u0431\u043b\u043e"), {"primary_numbers", "recommended_numbers", "top_numbers", "best_numbers", "numbers", "main_numbers"}),
        ("v66", U(r"\u041f\u0440\u0435\u0442\u0435\u0433\u043b\u0435\u043d \u043e\u0431\u0435\u0434\u0438\u043d\u0435\u043d \u043c\u043e\u0434\u0435\u043b"), {"top_numbers", "recommended_numbers", "numbers", "best_numbers"}),
        ("v75", U(r"\u041d\u0435\u0432\u0440\u043e\u043d\u0435\u043d \u043c\u0435\u0442\u0430 \u043c\u043e\u0434\u0435\u043b"), {"primary_numbers", "recommended_numbers", "numbers", "best_numbers"}),
        ("v41", U(r"\u0410\u043d\u0430\u043b\u0438\u0437 \u043f\u043e \u043f\u0440\u0430\u0432\u0438\u043b\u0430\u0442\u0430"), {"primary_numbers", "recommended_numbers", "numbers", "main_numbers"}),
    ]
    rows = []
    for prefix, label, keys in config:
        found = None
        source = None
        for path in _json_files_for_prefix(prefix):
            data = _load_json(path)
            if not data:
                continue
            found = _walk_for_named_numbers(data, keys)
            if not found:
                combos = []
                _walk_for_combos(data, combos)
                combos = _dedupe_combos(combos)
                if combos:
                    found = _derive_from_combos(combos)
            if found:
                source = path.relative_to(ROOT).as_posix()
                break
        if found:
            rows.append({
                "label": label,
                "numbers": found[:8],
                "source": source or ""
            })
    return rows

def _ticket_html(title, combos):
    safe_title = html.escape(title)
    rows_html = ""
    for index, combo in enumerate(combos, start=1):
        nums = "".join(f'<div class="v87-number-box">{int(n)}</div>' for n in combo)
        rows_html += (
            f'<div class="v87-ticket-row">'
            f'<div class="v87-ticket-label">{html.escape(UI["combo"])} {index}</div>'
            f'<div class="v87-number-strip">{nums}</div>'
            f'</div>'
        )
    return (
        f'<div class="v87-ticket-card">'
        f'<div class="v87-ticket-title">{safe_title}</div>'
        f'<div class="v87-ticket-note">{html.escape(UI["ticket_note"])}</div>'
        f'{rows_html}'
        f'</div>'
    )

def _model_strip_html(label, numbers, source):
    nums = "".join(f'<div class="v87-number-box">{int(n)}</div>' for n in numbers)
    return (
        f'<div class="v87-model-card">'
        f'<div class="v87-model-title">{html.escape(label)}</div>'
        f'<div class="v87-number-strip">{nums}</div>'
        f'</div>'
    )

def _quick_cards_html():
    cards = [
        (UI["quick_1_title"], UI["quick_1_text"]),
        (UI["quick_2_title"], UI["quick_2_text"]),
        (UI["quick_3_title"], UI["quick_3_text"]),
    ]
    inner = ""
    for title, text in cards:
        inner += (
            f'<div class="v87-quick-card">'
            f'<div class="v87-quick-title">{html.escape(title)}</div>'
            f'<div class="v87-quick-text">{html.escape(text)}</div>'
            f'</div>'
        )
    return f'<div class="v87-grid-quick">{inner}</div>'

def render_v87_synthesized_user_menu_section():
    st.markdown(CSS, unsafe_allow_html=True)
    st.title(UI["title"])
    # STEP89_1_USER_MENU_FINAL_SELECTION_START
    render_v89_1_user_menu_final_selection()
    st.markdown('---')
    # STEP89_1_USER_MENU_FINAL_SELECTION_END

    st.caption(UI["caption"])

    summary = _load_json(V86_SUMMARY_PATH) or {}
    live_status = _load_live_user_menu_status()
    dataset_rows = live_status.get("dataset_rows") or summary.get("dataset_rows", 0)
    latest_draw = live_status.get("latest_draw_date") or summary.get("latest_draw_date", "-")
    registered_models = summary.get("models_registered", 0)
    active_models = summary.get("active_models", 0)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(UI["dataset_rows"], dataset_rows)
    m2.metric(UI["latest_draw"], latest_draw)
    m3.metric(UI["registry_models"], registered_models)
    m4.metric(UI["active_count"], active_models)

    st.subheader(UI["quick_path"])
    st.markdown(_quick_cards_html(), unsafe_allow_html=True)

    combos, combo_sources = _discover_ticket_combos()
    st.subheader(UI["main_ticket"])

    if combos:
        main_combos = combos[:4]
        reserve_combos = combos[4:8]
        grid_html = '<div class="v87-ticket-grid">'
        grid_html += _ticket_html(UI["main_ticket"], main_combos)
        if reserve_combos:
            grid_html += _ticket_html(UI["reserve_ticket"], reserve_combos)
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)
    else:
        st.info(UI["no_ticket"])

    st.subheader(UI["model_numbers"])
    st.caption(UI["model_strip_note"])
    strips = _discover_model_strips()
    if strips:
        for row in strips:
            st.markdown(_model_strip_html(row["label"], row["numbers"], row["source"]), unsafe_allow_html=True)
    else:
        st.info(U(r"\u041d\u0435 \u0441\u0430 \u043d\u0430\u043c\u0435\u0440\u0435\u043d\u0438 \u0432\u0438\u0437\u0443\u0430\u043b\u043d\u0438 \u0447\u0438\u0441\u043b\u0430 \u043e\u0442 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435."))

    active_names = summary.get("active_model_names", []) or []
    if active_names:
        st.subheader(UI["active_models"])
        for name in active_names:
            st.markdown(f"- {name}")

    if combo_sources:
        with st.expander(UI["sources"], expanded=False):
            for item in combo_sources:
                st.markdown(f"- `{item}`")

    st.markdown("---")
    st.info(UI["safe"])

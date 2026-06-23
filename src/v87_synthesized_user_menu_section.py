from __future__ import annotations

from pathlib import Path
import csv
import json
import re
import html

import streamlit as st

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
    gap: 10px;
    margin-bottom: 10px;
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
    gap: 8px;
}
.v87-number-box {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(180deg, rgba(245,245,245,0.98), rgba(226,232,240,0.98));
    color: #111827;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.95rem;
    border: 1px solid rgba(148,163,184,0.45);
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
    st.caption(UI["caption"])

    summary = _load_json(V86_SUMMARY_PATH) or {}
    dataset_rows = summary.get("dataset_rows", 0)
    latest_draw = summary.get("latest_draw_date", "-")
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

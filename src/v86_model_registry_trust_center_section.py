from __future__ import annotations

from pathlib import Path
import csv
import json

import streamlit as st

try:
    import pandas as pd
except Exception:
    pd = None

from src.v86_model_registry_trust_center_engine import build_model_registry_trust_center

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "reports" / "v86_model_registry_summary.json"
CSV_PATH = ROOT / "reports" / "v86_model_registry_models.csv"


def U(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


UI = {
    "title": U(r"\u0420\u0435\u0433\u0438\u0441\u0442\u044a\u0440 \u0438 \u0434\u043e\u0432\u0435\u0440\u0438\u0435 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435"),
    "caption": U(r"\u041f\u043e\u043a\u0430\u0437\u0432\u0430 \u044f\u0441\u043d\u0438\u0442\u0435 \u0438\u043c\u0435\u043d\u0430, \u0432\u044a\u0442\u0440\u0435\u0448\u043d\u0438\u0442\u0435 \u043a\u043e\u0434\u043e\u0432\u0435, \u0440\u043e\u043b\u044f\u0442\u0430 \u0438 \u0441\u0442\u0430\u0442\u0443\u0441\u0430 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435. \u0422\u043e\u0432\u0430 \u043d\u0435 \u0435 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430 \u0438 \u043d\u0435 \u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430."),
    "refresh": U(r"\u041e\u0431\u043d\u043e\u0432\u0438 \u0440\u0435\u0433\u0438\u0441\u0442\u044a\u0440\u0430"),
    "updated": U(r"\u0420\u0435\u0433\u0438\u0441\u0442\u044a\u0440\u044a\u0442 \u0435 \u043e\u0431\u043d\u043e\u0432\u0435\u043d."),
    "dataset_rows": U(r"\u0420\u0435\u0434\u043e\u0432\u0435 \u0432 \u043d\u0430\u0431\u043e\u0440\u0430 \u0434\u0430\u043d\u043d\u0438"),
    "last_draw": U(r"\u041f\u043e\u0441\u043b\u0435\u0434\u0435\u043d \u0442\u0438\u0440\u0430\u0436"),
    "registered": U(r"\u041c\u043e\u0434\u0435\u043b\u0438"),
    "active": U(r"\u0410\u043a\u0442\u0438\u0432\u043d\u0438"),
    "audit": U(r"\u0421\u0430\u043c\u043e \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),
    "latest_numbers": U(r"\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0438 \u0447\u0438\u0441\u043b\u0430 \u0432 dataset-\u0430"),
    "active_names": U(r"\u0410\u043a\u0442\u0438\u0432\u043d\u0438 \u043c\u043e\u0434\u0435\u043b\u0438 / \u0441\u043b\u043e\u0435\u0432\u0435"),
    "audit_names": U(r"\u041c\u043e\u0434\u0435\u043b\u0438 \u0441\u0430\u043c\u043e \u0437\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),
    "table_title": U(r"\u041c\u043e\u0434\u0435\u043b\u0438 \u0441 \u044f\u0441\u043d\u0438 \u0438\u043c\u0435\u043d\u0430"),
    "empty": U(r"\u041d\u044f\u043c\u0430 \u043d\u0430\u043b\u0438\u0447\u043d\u0438 \u0437\u0430\u043f\u0438\u0441\u0438 \u0432 \u0440\u0435\u0433\u0438\u0441\u0442\u044a\u0440\u0430."),
    "expander": U(r"\u041a\u0430\u043a \u0434\u0430 \u0447\u0435\u0442\u0435\u043c \u0432\u044a\u0442\u0440\u0435\u0448\u043d\u0438\u0442\u0435 \u043a\u043e\u0434\u043e\u0432\u0435"),
    "safe": U(r"\u0412\u0430\u0436\u043d\u043e: \u0442\u043e\u0437\u0438 \u0440\u0435\u0433\u0438\u0441\u0442\u044a\u0440 \u043d\u0435 \u043a\u0430\u0437\u0432\u0430 \u043a\u043e\u0438 \u0447\u0438\u0441\u043b\u0430 \u0449\u0435 \u0441\u0435 \u043f\u0430\u0434\u043d\u0430\u0442. \u0422\u043e\u0439 \u043f\u043e\u043a\u0430\u0437\u0432\u0430 \u043a\u043e\u0438 \u043c\u043e\u0434\u0435\u043b\u0438 \u0441\u0430 \u043d\u0430\u043b\u0438\u0447\u043d\u0438, \u043a\u043e\u0438 \u0441\u0430 \u0430\u043a\u0442\u0438\u0432\u043d\u0438 \u0438 \u043a\u043e\u0438 \u0441\u0430 \u0441\u0430\u043c\u043e \u0437\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430.")
}

LABELS = {
    "model_name_bg": U(r"\u0418\u043c\u0435 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0430"),
    "code": U(r"\u0412\u044a\u0442\u0440\u0435\u0448\u0435\u043d \u043a\u043e\u0434"),
    "category_bg": U(r"\u0413\u0440\u0443\u043f\u0430"),
    "mode_bg": U(r"\u0420\u0435\u0436\u0438\u043c"),
    "lifecycle_bg": U(r"\u0421\u0442\u0430\u0442\u0443\u0441"),
    "health_status_bg": U(r"\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),
    "draw_reference": U(r"\u0414\u0430\u043d\u043d\u0438 / \u0442\u0438\u0440\u0430\u0436\u0438"),
    "files": U(r"\u0424\u0430\u0439\u043b\u043e\u0432\u0435"),
    "role_bg": U(r"\u0420\u043e\u043b\u044f"),
    "status_note_bg": U(r"\u0411\u0435\u043b\u0435\u0436\u043a\u0430")
}


def _load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_rows(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _display_rows(rows):
    if not rows:
        st.info(UI["empty"])
        return

    visible = []
    for row in rows:
        visible.append({
            LABELS["model_name_bg"]: row.get("model_name_bg", ""),
            LABELS["code"]: row.get("code", ""),
            LABELS["category_bg"]: row.get("category_bg", ""),
            LABELS["mode_bg"]: row.get("mode_bg", ""),
            LABELS["lifecycle_bg"]: row.get("lifecycle_bg", ""),
            LABELS["health_status_bg"]: row.get("health_status_bg", ""),
            LABELS["draw_reference"]: row.get("draw_reference", ""),
            LABELS["files"]: f"{row.get('artifacts_present', '')}/{row.get('artifacts_expected', '')}",
            LABELS["role_bg"]: row.get("role_bg", ""),
            LABELS["status_note_bg"]: row.get("status_note_bg", "")
        })

    if pd is not None:
        st.dataframe(pd.DataFrame(visible), width="stretch", hide_index=True)
    else:
        st.table(visible)


def render_v86_model_registry_trust_center_section():
    st.title(UI["title"])
    st.caption(UI["caption"])

    if st.button(UI["refresh"]):
        build_model_registry_trust_center()
        st.success(UI["updated"])
        st.rerun()

    if not SUMMARY_PATH.exists() or not CSV_PATH.exists():
        build_model_registry_trust_center()

    summary = _load_json(SUMMARY_PATH)
    rows = _load_rows(CSV_PATH)

    if not summary:
        st.warning(U(r"\u041b\u0438\u043f\u0441\u0432\u0430 \u0440\u0435\u0433\u0438\u0441\u0442\u044a\u0440. \u041e\u0431\u043d\u043e\u0432\u0438 \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u0430\u0442\u0430."))
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(UI["dataset_rows"], summary.get("dataset_rows", 0))
    c2.metric(UI["last_draw"], summary.get("latest_draw_date", "-"))
    c3.metric(UI["registered"], summary.get("models_registered", 0))
    c4.metric(UI["active"], summary.get("active_models", 0))
    c5.metric(UI["audit"], summary.get("audit_only_models", 0))

    latest_numbers = summary.get("latest_numbers", "")
    if latest_numbers:
        st.info(f"{UI['latest_numbers']}: {latest_numbers}")

    active_names = summary.get("active_model_names", []) or []
    audit_names = summary.get("audit_only_model_names", []) or []

    if active_names:
        st.success(f"{UI['active_names']}: " + ", ".join(active_names))

    if audit_names:
        st.warning(f"{UI['audit_names']}: " + ", ".join(audit_names))

    st.subheader(UI["table_title"])
    _display_rows(rows)

    with st.expander(UI["expander"], expanded=False):
        st.markdown(
            U(r"""
- \u041a\u043e\u0434\u043e\u0432\u0435\u0442\u0435 \u043a\u0430\u0442\u043e `v41`, `v65` \u0438 `v75` \u0441\u0430 \u0432\u044a\u0442\u0440\u0435\u0448\u043d\u0438 \u043d\u043e\u043c\u0435\u0440\u0430 \u043d\u0430 \u0435\u0442\u0430\u043f\u0438.
- \u0417\u0430 \u043f\u043e\u0442\u0440\u0435\u0431\u0438\u0442\u0435\u043b\u044f \u0432\u043e\u0434\u0435\u0449\u043e \u0435 \u0438\u043c\u0435\u0442\u043e, \u0440\u043e\u043b\u044f\u0442\u0430 \u0438 \u0441\u0442\u0430\u0442\u0443\u0441\u044a\u0442 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0430.
- \u0410\u043a\u0442\u0438\u0432\u0435\u043d \u0441\u043b\u043e\u0439 \u043e\u0437\u043d\u0430\u0447\u0430\u0432\u0430, \u0447\u0435 \u0443\u0447\u0430\u0441\u0442\u0432\u0430 \u0432 \u0442\u0435\u043a\u0443\u0449\u0430\u0442\u0430 \u043e\u0446\u0435\u043d\u043a\u0430.
- \u0421\u0430\u043c\u043e \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043e\u0437\u043d\u0430\u0447\u0430\u0432\u0430, \u0447\u0435 \u0441\u043b\u043e\u044f\u0442 \u043d\u0435 \u0441\u043c\u0435\u043d\u044f \u0430\u043a\u0442\u0438\u0432\u043d\u0438\u044f \u043c\u043e\u0434\u0435\u043b.
- \u041a\u043e\u043d\u0442\u0440\u043e\u043b\u0435\u043d \u0441\u043b\u043e\u0439 \u0441\u043b\u0435\u0434\u0438 \u043d\u0430\u0434\u0435\u0436\u0434\u043d\u043e\u0441\u0442, snapshot \u0438\u043b\u0438 \u0441\u0438\u043d\u0445\u0440\u043e\u043d.
""")
        )

    st.markdown(UI["safe"])

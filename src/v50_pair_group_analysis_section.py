
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
PAIR_CSV = ROOT / "reports" / "v50_pair_scores.csv"
GROUP_CSV = ROOT / "reports" / "v50_group_scores.csv"
SUMMARY_JSON = ROOT / "reports" / "v50_pair_group_summary.json"
V45_TICKETS = ROOT / "models" / "v45" / "v45_final_prediction_tickets.json"


def T(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _load_pro_combinations() -> list[list[int]]:
    data = _read_json(V45_TICKETS)
    combos: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()

    def add(values: Any) -> None:
        if not isinstance(values, list):
            return
        try:
            cleaned = sorted({int(x) for x in values if 1 <= int(x) <= 49})
        except Exception:
            return
        if len(cleaned) != 6:
            return
        key = tuple(cleaned)
        if key not in seen:
            seen.add(key)
            combos.append(cleaned)

    def walk(obj: Any) -> None:
        if isinstance(obj, list):
            add(obj)
            for item in obj:
                walk(item)
        elif isinstance(obj, dict):
            for key in ["numbers", "combination", "ticket", "primary_numbers", "main_numbers"]:
                if key in obj:
                    add(obj.get(key))
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    walk(value)

    walk(data)
    return combos


def _pair_key(a: int, b: int) -> str:
    x, y = sorted([a, b])
    return f"{x}-{y}"


def _group_key(values: list[int]) -> str:
    return "-".join(str(x) for x in sorted(values))


def _evaluate_combo(combo: list[int], pair_df: pd.DataFrame, group_df: pd.DataFrame) -> dict[str, Any]:
    pair_scores = {}
    if not pair_df.empty and "pair" in pair_df.columns:
        pair_scores = dict(zip(pair_df["pair"], pair_df.get("pair_score", pd.Series([0] * len(pair_df)))))

    group_scores = {}
    if not group_df.empty and "group" in group_df.columns:
        group_scores = dict(zip(group_df["group"], group_df.get("group_score", pd.Series([0] * len(group_df)))))

    pairs = [_pair_key(a, b) for a, b in __import__("itertools").combinations(combo, 2)]
    groups = [_group_key(list(g)) for g in __import__("itertools").combinations(combo, 3)]

    pair_values = [float(pair_scores.get(p, 0.0)) for p in pairs]
    group_values = [float(group_scores.get(g, 0.0)) for g in groups]

    strong_pairs = sum(1 for value in pair_values if value >= 0.65)
    strong_groups = sum(1 for value in group_values if value >= 0.65)

    return {
        T("\\u041a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u044f"): " ".join(str(n) for n in combo),
        T("\\u0421\\u0440\\u0435\\u0434\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438"): round(sum(pair_values) / len(pair_values), 4) if pair_values else 0.0,
        T("\\u0421\\u0438\\u043b\\u043d\\u0438 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438"): strong_pairs,
        T("\\u0421\\u0440\\u0435\\u0434\\u043d\\u0430 \\u043e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u043d\\u0430 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438"): round(sum(group_values) / len(group_values), 4) if group_values else 0.0,
        T("\\u0421\\u0438\\u043b\\u043d\\u0438 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438"): strong_groups,
    }


def _rename_pair_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "pair": T("\\u0414\\u0432\\u043e\\u0439\\u043a\\u0430"),
        "count": T("\\u0411\\u0440\\u043e\\u0439 \\u043f\\u043e\\u044f\\u0432\\u0438"),
        "recent_count": T("\\u0421\\u043a\\u043e\\u0440\\u043e\\u0448\\u043d\\u0438 \\u043f\\u043e\\u044f\\u0432\\u0438"),
        "gap": T("\\u0418\\u043d\\u0442\\u0435\\u0440\\u0432\\u0430\\u043b"),
        "pair_score": T("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430"),
        "watch_score": T("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430 \\u0437\\u0430 \\u043d\\u0430\\u0431\\u043b\\u044e\\u0434\\u0435\\u043d\\u0438\\u0435"),
    }
    cols = [col for col in ["pair", "count", "recent_count", "gap", "pair_score", "watch_score"] if col in df.columns]
    return df[cols].rename(columns=rename)


def _rename_group_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "group": T("\\u0422\\u0440\\u043e\\u0439\\u043a\\u0430"),
        "count": T("\\u0411\\u0440\\u043e\\u0439 \\u043f\\u043e\\u044f\\u0432\\u0438"),
        "recent_count": T("\\u0421\\u043a\\u043e\\u0440\\u043e\\u0448\\u043d\\u0438 \\u043f\\u043e\\u044f\\u0432\\u0438"),
        "gap": T("\\u0418\\u043d\\u0442\\u0435\\u0440\\u0432\\u0430\\u043b"),
        "group_score": T("\\u041e\\u0446\\u0435\\u043d\\u043a\\u0430"),
    }
    cols = [col for col in ["group", "count", "recent_count", "gap", "group_score"] if col in df.columns]
    return df[cols].rename(columns=rename)


def render() -> None:
    st.title(T("\\u0410\\u043d\\u0430\\u043b\\u0438\\u0437 \\u043d\\u0430 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438 \\u0438 \\u0433\\u0440\\u0443\\u043f\\u0438"))

    st.caption(
        T(
            "\\u0422\\u0443\\u043a \\u0441\\u0435 \\u0433\\u043b\\u0435\\u0434\\u0430\\u0442 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u0447\\u0435\\u0441\\u043a\\u0438 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438 \\u0438 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438 \\u043e\\u0442 \\u0447\\u0438\\u0441\\u043b\\u0430. \\u0422\\u043e\\u0432\\u0430 \\u0435 \\u0434\\u043e\\u043f\\u044a\\u043b\\u043d\\u0438\\u0442\\u0435\\u043b\\u0435\\u043d \\u0441\\u0438\\u0433\\u043d\\u0430\\u043b, \\u043d\\u0435 \\u0433\\u0430\\u0440\\u0430\\u043d\\u0446\\u0438\\u044f."
        )
    )

    st.warning(
        T(
            "\\u041b\\u043e\\u0442\\u0430\\u0440\\u0438\\u0439\\u043d\\u0438\\u0442\\u0435 \\u0442\\u0435\\u0433\\u043b\\u0435\\u043d\\u0438\\u044f \\u0441\\u0430 \\u0441\\u043b\\u0443\\u0447\\u0430\\u0439\\u043d\\u0438. \\u0414\\u0432\\u043e\\u0439\\u043a\\u0438\\u0442\\u0435 \\u0438 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438\\u0442\\u0435 \\u043f\\u043e\\u043c\\u0430\\u0433\\u0430\\u0442 \\u0437\\u0430 \\u043f\\u043e-\\u0434\\u043e\\u0431\\u0440\\u0430 \\u0441\\u0442\\u0440\\u0443\\u043a\\u0442\\u0443\\u0440\\u0430, \\u043d\\u043e \\u043d\\u0435 \\u043f\\u0440\\u0435\\u0434\\u0441\\u043a\\u0430\\u0437\\u0432\\u0430\\u0442 \\u0441\\u044a\\u0441 \\u0441\\u0438\\u0433\\u0443\\u0440\\u043d\\u043e\\u0441\\u0442."
        )
    )

    pair_df = _read_csv(PAIR_CSV)
    group_df = _read_csv(GROUP_CSV)
    summary = _read_json(SUMMARY_JSON)

    if pair_df.empty or group_df.empty:
        st.info(T("\\u041f\\u0443\\u0441\\u043d\\u0438 `python scripts/v50_build_pair_group_intelligence.py`, \\u0437\\u0430 \\u0434\\u0430 \\u0441\\u0435 \\u0441\\u044a\\u0437\\u0434\\u0430\\u0434\\u0430\\u0442 v50 \\u043e\\u0442\\u0447\\u0435\\u0442\\u0438\\u0442\\u0435."))
        return

    c1, c2, c3 = st.columns(3)
    c1.metric(T("\\u0412\\u0430\\u043b\\u0438\\u0434\\u043d\\u0438 \\u0442\\u0438\\u0440\\u0430\\u0436\\u0438"), str(summary.get("total_draw_events", "-")))
    c2.metric(T("\\u0414\\u0432\\u043e\\u0439\\u043a\\u0438"), str(summary.get("total_pairs", len(pair_df))))
    c3.metric(T("\\u041d\\u0430\\u0431\\u043b\\u044e\\u0434\\u0430\\u0432\\u0430\\u043d\\u0438 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438"), str(summary.get("observed_groups", len(group_df))))

    tabs = st.tabs(
        [
            T("\\u0422\\u043e\\u043f \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438"),
            T("\\u0414\\u0432\\u043e\\u0439\\u043a\\u0438 \\u0437\\u0430 \\u043d\\u0430\\u0431\\u043b\\u044e\\u0434\\u0435\\u043d\\u0438\\u0435"),
            T("\\u0422\\u0440\\u043e\\u0439\\u043a\\u0438"),
            T("Pro \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438"),
            T("\\u041a\\u0430\\u043a \\u0441\\u0435 \\u0438\\u0437\\u043f\\u043e\\u043b\\u0437\\u0432\\u0430"),
        ]
    )

    with tabs[0]:
        st.subheader(T("\\u041d\\u0430\\u0439-\\u0441\\u0438\\u043b\\u043d\\u0438 \\u0434\\u0432\\u043e\\u0439\\u043a\\u0438 \\u043f\\u043e \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0438\\u0440\\u0430\\u043d \\u0441\\u0438\\u0433\\u043d\\u0430\\u043b"))
        st.dataframe(_rename_pair_columns(pair_df.head(100)), hide_index=True, width="stretch")

    with tabs[1]:
        st.subheader(T("\\u0414\\u0432\\u043e\\u0439\\u043a\\u0438 \\u0441 \\u0438\\u0441\\u0442\\u043e\\u0440\\u0438\\u044f, \\u043d\\u043e \\u0441 \\u043f\\u043e-\\u0434\\u044a\\u043b\\u044a\\u0433 \\u0438\\u043d\\u0442\\u0435\\u0440\\u0432\\u0430\\u043b"))
        watch = pair_df.sort_values(["watch_score", "gap"], ascending=False)
        st.dataframe(_rename_pair_columns(watch.head(100)), hide_index=True, width="stretch")

    with tabs[2]:
        st.subheader(T("\\u041d\\u0430\\u0439-\\u0441\\u0438\\u043b\\u043d\\u0438 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438"))
        st.dataframe(_rename_group_columns(group_df.head(100)), hide_index=True, width="stretch")

    with tabs[3]:
        combos = _load_pro_combinations()
        if not combos:
            st.info(T("\\u041d\\u044f\\u043c\\u0430 \\u043d\\u0430\\u043b\\u0438\\u0447\\u043d\\u0438 Pro \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438."))
        else:
            rows = [_evaluate_combo(combo, pair_df, group_df) for combo in combos]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    with tabs[4]:
        st.markdown(
            T(
                """
- \\u0414\\u0432\\u043e\\u0439\\u043a\\u0438\\u0442\\u0435 \\u0441\\u0430 \\u043f\\u043e-\\u0441\\u0442\\u0430\\u0431\\u0438\\u043b\\u0435\\u043d \\u0441\\u0438\\u0433\\u043d\\u0430\\u043b \\u043e\\u0442 \\u0442\\u0440\\u043e\\u0439\\u043a\\u0438\\u0442\\u0435, \\u0437\\u0430\\u0449\\u043e\\u0442\\u043e \\u0441\\u0430 \\u043f\\u043e-\\u043c\\u0430\\u043b\\u043a\\u043e.
- \\u0422\\u0440\\u043e\\u0439\\u043a\\u0438\\u0442\\u0435 \\u0441\\u0430 \\u043f\\u043e-\\u0441\\u043b\\u0430\\u0431 \\u0441\\u0438\\u0433\\u043d\\u0430\\u043b \\u0438 \\u043d\\u0435 \\u0442\\u0440\\u044f\\u0431\\u0432\\u0430 \\u0434\\u0430 \\u0432\\u043e\\u0434\\u044f\\u0442 \\u0438\\u0437\\u0431\\u043e\\u0440\\u0430 \\u0441\\u0430\\u043c\\u0438.
- \\u041d\\u0430\\u0439-\\u043f\\u043e\\u043b\\u0435\\u0437\\u043d\\u043e \\u0435 \\u0442\\u0435\\u0437\\u0438 \\u0434\\u0430\\u043d\\u043d\\u0438 \\u0434\\u0430 \\u0441\\u0435 \\u043f\\u043e\\u043b\\u0437\\u0432\\u0430\\u0442 \\u043a\\u0430\\u0442\\u043e \\u0434\\u043e\\u043f\\u044a\\u043b\\u043d\\u0438\\u0442\\u0435\\u043b\\u0435\\u043d \\u0441\\u043b\\u043e\\u0439 \\u043a\\u044a\\u043c \\u0433\\u0435\\u043d\\u0435\\u0440\\u0430\\u0442\\u043e\\u0440\\u0430 \\u043d\\u0430 \\u043a\\u043e\\u043c\\u0431\\u0438\\u043d\\u0430\\u0446\\u0438\\u0438.
- \\u0426\\u0435\\u043b\\u0442\\u0430 \\u0435 \\u043f\\u043e-\\u0434\\u043e\\u0431\\u0440\\u0430 \\u0441\\u0442\\u0440\\u0443\\u043a\\u0442\\u0443\\u0440\\u0430, \\u043d\\u0435 \\u043e\\u0431\\u0435\\u0449\\u0430\\u043d\\u0438\\u0435 \\u0437\\u0430 \\u043f\\u0435\\u0447\\u0430\\u043b\\u0431\\u0430.
"""
            )
        )

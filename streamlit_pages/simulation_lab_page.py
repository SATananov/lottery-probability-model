
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Iterable

import streamlit as st


def render_simulation_lab_page() -> None:
    lang = st.session_state.get("language", "bg")

    def tx(bg: str, en: str) -> str:
        return bg if lang == "bg" else en

    def rerun_page() -> None:
        if hasattr(st, "rerun"):
            st.rerun()
        elif hasattr(st, "experimental_rerun"):
            st.experimental_rerun()

    def combo_key(index: int) -> str:
        return f"v39_simulation_live_combo_{index}"

    def get_combo(index: int) -> list[int]:
        st.session_state.setdefault(combo_key(index), [])
        values = st.session_state.get(combo_key(index), [])
        return sorted([int(value) for value in values])

    def set_combo(index: int, values: Iterable[int]) -> None:
        st.session_state[combo_key(index)] = sorted([int(value) for value in values])
        st.session_state["v39_simulation_live_show_result"] = False
        st.session_state.pop("v39_simulation_live_drawn_numbers", None)

    def toggle_number(index: int, number: int) -> None:
        selected = set(get_combo(index))

        if number in selected:
            selected.remove(number)
            set_combo(index, selected)
            rerun_page()
            return

        if len(selected) >= 6:
            st.session_state["v39_simulation_live_message"] = tx(
                "\u0412 \u0435\u0434\u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u043c\u043e\u0436\u0435 \u0434\u0430 \u0438\u043c\u0430 \u0442\u043e\u0447\u043d\u043e 6 \u0447\u0438\u0441\u043b\u0430. \u041f\u044a\u0440\u0432\u043e \u043c\u0430\u0445\u043d\u0438 \u0435\u0434\u043d\u043e \u0447\u0438\u0441\u043b\u043e.",
                "One combination can contain exactly 6 numbers. Remove one number first.",
            )
            rerun_page()
            return

        selected.add(number)
        set_combo(index, selected)
        rerun_page()

    def fmt_numbers(values: Iterable[int]) -> str:
        numbers = sorted([int(value) for value in values])
        return ", ".join(str(value) for value in numbers) if numbers else "\u2014"

    def chips(values: Iterable[int], matched: Iterable[int] | None = None, drawn: bool = False) -> str:
        numbers = sorted([int(value) for value in values])
        matched_set = set(matched or [])

        if not numbers:
            empty_text = tx("\u043d\u044f\u043c\u0430 \u0438\u0437\u0431\u0440\u0430\u043d\u0438 \u0447\u0438\u0441\u043b\u0430", "no selected numbers")
            return f'<span class="v39-empty">{empty_text}</span>'

        html = ""

        for value in numbers:
            css_class = "v39-chip"
            if drawn:
                css_class += " v39-chip-drawn"
            if value in matched_set:
                css_class += " v39-chip-match"

            html += f'<span class="{css_class}">{value}</span>'

        return html


    # V39_MODEL_TICKET_GENERATOR_START
    def _v39_normalize_model_combo(value):
        if isinstance(value, dict):
            for key in ["numbers", "combination", "ticket", "values", "selected_numbers"]:
                if key in value:
                    combo = _v39_normalize_model_combo(value.get(key))
                    if combo:
                        return combo
            return []

        if not isinstance(value, (list, tuple)):
            return []

        numbers = []
        for item in value:
            try:
                number = int(item)
            except Exception:
                continue

            if 1 <= number <= 49:
                numbers.append(number)

        unique = sorted(set(numbers))
        return unique if len(unique) == 6 else []

    def _v39_collect_model_combos(obj, source, found, depth=0):
        if depth > 8 or len(found) >= 80:
            return

        combo = _v39_normalize_model_combo(obj)
        if combo:
            found.append({"numbers": combo, "source": source})
            return

        if isinstance(obj, dict):
            preferred_keys = [
                "recommended_prediction",
                "recommended_combinations",
                "portfolio_predictions",
                "main_recommendation",
                "final_recommendation",
                "best_combination",
                "model_ticket",
                "ticket",
                "numbers",
                "combination",
            ]

            for key in preferred_keys:
                if key in obj:
                    _v39_collect_model_combos(obj.get(key), source, found, depth + 1)

            for key, value in obj.items():
                if key in preferred_keys:
                    continue
                if isinstance(value, (dict, list, tuple)):
                    _v39_collect_model_combos(value, source, found, depth + 1)

            return

        if isinstance(obj, (list, tuple)):
            for item in obj:
                _v39_collect_model_combos(item, source, found, depth + 1)

    def _v39_model_json_paths():
        roots = [
            Path("models"),
            Path("models") / "versions",
            Path("reports"),
        ]

        paths = []
        for root in roots:
            if root.exists():
                paths.extend(list(root.glob("*.json")))

        def priority(path):
            name = path.name.lower()
            score = 0

            if "prediction" in name:
                score += 50
            if "combined" in name:
                score += 45
            if "ensemble" in name:
                score += 35
            if "hot" in name or "frequency" in name:
                score += 30
            if "balanced" in name:
                score += 25
            if "v39" in name:
                score += 20
            if "v36" in name:
                score += 15

            try:
                modified = path.stat().st_mtime
            except Exception:
                modified = 0

            return (score, modified)

        unique = []
        seen = set()

        for path in sorted(paths, key=priority, reverse=True):
            resolved = str(path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            unique.append(path)

        return unique

    def _v39_generate_model_ticket():
        candidates = []

        for path in _v39_model_json_paths():
            try:
                with path.open("r", encoding="utf-8-sig") as file:
                    payload = json.load(file)
            except Exception:
                continue

            source = path.stem.replace("_", " ").replace("-", " ")
            local_found = []
            _v39_collect_model_combos(payload, source, local_found)

            for item in local_found:
                combo = _v39_normalize_model_combo(item.get("numbers"))
                if combo:
                    candidates.append({"numbers": combo, "source": item.get("source") or source})

        final_ticket = []
        seen = set()

        for item in candidates:
            combo = _v39_normalize_model_combo(item.get("numbers"))
            signature = tuple(combo)

            if not combo or signature in seen:
                continue

            seen.add(signature)
            final_ticket.append(item)

            if len(final_ticket) >= 4:
                break

        return final_ticket

    def _v39_apply_model_ticket():
        ticket = _v39_generate_model_ticket()

        if not ticket:
            st.session_state["v39_simulation_live_message"] = tx(
                "\u041d\u0435 \u0443\u0441\u043f\u044f\u0445 \u0434\u0430 \u043d\u0430\u043c\u0435\u0440\u044f \u0433\u043e\u0442\u043e\u0432\u0438 \u043c\u043e\u0434\u0435\u043b\u043d\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u0432 JSON \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435.",
                "Could not find ready model combinations in the JSON models.",
            )
            return

        for index in range(1, 5):
            if index <= len(ticket):
                set_combo(index, ticket[index - 1]["numbers"])
            else:
                set_combo(index, [])

        st.session_state["v39_simulation_live_message"] = tx(
            "\u0413\u0435\u043d\u0435\u0440\u0438\u0440\u0430\u043d \u0435 \u043c\u043e\u0434\u0435\u043b\u0435\u043d \u0444\u0438\u0448. \u0427\u0438\u0441\u043b\u0430\u0442\u0430 \u0441\u0430 \u043c\u0430\u0440\u043a\u0438\u0440\u0430\u043d\u0438 \u0441 X \u0432 \u0442\u0430\u0431\u043b\u0438\u0446\u0438\u0442\u0435.",
            "A model ticket was generated. The numbers are marked with X in the tables.",
        )
    # V39_MODEL_TICKET_GENERATOR_END


    def render_css() -> None:
        st.markdown(
            """
            <style>
            div[data-testid="stButton"] > button {
                border: 1px solid rgba(245,216,108,0.34) !important;
                background: rgba(255,255,255,0.035) !important;
                color: rgba(255,255,255,0.88) !important;
                border-radius: 8px !important;
                min-height: 34px !important;
                padding: 0.18rem 0.25rem !important;
                font-size: 0.84rem !important;
                font-weight: 850 !important;
                box-shadow: none !important;
            }

            div[data-testid="stButton"] > button:hover {
                border-color: rgba(245,216,108,0.82) !important;
                background: rgba(245,216,108,0.12) !important;
                color: #f8e6a0 !important;
            }

            div[data-testid="stButton"] > button[kind="primary"] {
                border-color: rgba(236,0,140,0.95) !important;
                background: rgba(236,0,140,0.18) !important;
                color: #f7d66d !important;
                font-weight: 950 !important;
            }

            .v39-sim-shell {
                border: 1px solid rgba(245,216,108,0.25);
                border-radius: 18px;
                padding: 18px;
                background:
                    radial-gradient(circle at top left, rgba(245,216,108,0.10), transparent 32%),
                    rgba(255,255,255,0.025);
                margin: 12px 0 20px 0;
            }

            .v39-sim-title {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 16px;
                border: 1px solid rgba(245,216,108,0.25);
                border-radius: 14px;
                padding: 14px 16px;
                background: rgba(0,0,0,0.20);
                margin-bottom: 18px;
            }

            .v39-sim-title-main {
                color: #f5ead4;
                font-size: 1.16rem;
                font-weight: 950;
            }

            .v39-sim-title-sub {
                color: rgba(255,255,255,0.64);
                font-size: 0.90rem;
                margin-top: 3px;
            }

            .v39-combo-head {
                border: 1px solid rgba(245,216,108,0.30);
                border-radius: 12px;
                background: linear-gradient(180deg, rgba(245,216,108,0.12), rgba(236,0,140,0.07));
                color: #f4d36c;
                text-align: center;
                font-weight: 950;
                padding: 8px 10px;
                font-size: 0.98rem;
                margin-bottom: 10px;
            }

            .v39-combo-count {
                color: rgba(255,255,255,0.64);
                font-weight: 760;
                font-size: 0.86rem;
            }

            .v39-selected-row {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
                margin: 10px 0 10px 0;
                padding: 10px 12px;
                border-radius: 12px;
                border: 1px solid rgba(245,216,108,0.22);
                background: rgba(245,216,108,0.065);
            }

            .v39-selected-label {
                color: #f4d36c;
                font-weight: 950;
                margin-right: 2px;
            }

            .v39-chip {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 32px;
                height: 30px;
                padding: 0 8px;
                border-radius: 999px;
                background: linear-gradient(180deg, #f2d66a, #c89b18);
                color: #111;
                font-weight: 950;
                border: 1px solid rgba(255,230,140,0.55);
                box-shadow: 0 0 10px rgba(245,216,108,0.14);
            }

            .v39-chip-drawn {
                background: linear-gradient(180deg, #f6e7a8, #d5a927);
            }

            .v39-chip-match {
                background: linear-gradient(180deg, #56f0a6, #0f9f61);
                color: #06140c;
                border-color: rgba(100,255,180,0.75);
                box-shadow: 0 0 14px rgba(64,255,160,0.18);
            }

            .v39-empty {
                color: rgba(255,255,255,0.58);
                font-weight: 750;
            }

            .v39-summary-box {
                border: 1px solid rgba(245,216,108,0.22);
                background: rgba(255,255,255,0.035);
                border-radius: 14px;
                padding: 14px 16px;
                margin: 16px 0;
            }

            .v39-summary-line {
                margin: 7px 0;
                color: rgba(255,255,255,0.86);
            }

            .v39-summary-line strong {
                color: #f4d36c;
            }

            .v39-result-card {
                border: 1px solid rgba(245,216,108,0.22);
                background: rgba(255,255,255,0.03);
                border-radius: 14px;
                padding: 14px 16px;
                margin: 14px 0;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def render_combo(index: int) -> None:
        values = get_combo(index)
        combo_label = tx("\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f", "Combination")
        selected_label = tx("\u0418\u0437\u0431\u0440\u0430\u043d\u0438", "Selected")
        clear_label = tx("\u0418\u0437\u0447\u0438\u0441\u0442\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f\u0442\u0430", "Clear combination")

        with st.container(border=True):
            st.markdown(
                f"""
                <div class="v39-combo-head">
                    {combo_label} {index}
                    <span class="v39-combo-count"> · {len(values)}/6</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            for row in range(7):
                columns = st.columns(7, gap="small")

                for col in range(7):
                    number = row * 7 + col + 1
                    selected = number in values
                    label = "\u2715" if selected else str(number)
                    button_type = "primary" if selected else "secondary"

                    if columns[col].button(
                        label,
                        key=f"v39_sim_cell_{index}_{number}",
                        type=button_type,
                        width="stretch",
                    ):
                        toggle_number(index, number)

            st.markdown(
                f"""
                <div class="v39-selected-row">
                    <span class="v39-selected-label">{selected_label}:</span>
                    {chips(values)}
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(clear_label, key=f"v39_sim_clear_{index}", width="stretch"):
                set_combo(index, [])
                rerun_page()

    def detect_number_columns(df):
        candidates = [
            ["n1", "n2", "n3", "n4", "n5", "n6"],
            ["num1", "num2", "num3", "num4", "num5", "num6"],
            ["number1", "number2", "number3", "number4", "number5", "number6"],
        ]

        for columns in candidates:
            if all(column in df.columns for column in columns):
                return columns

        numeric_columns = []

        for column in df.columns:
            lowered = str(column).lower()

            if lowered in ["year", "draw", "draw_id", "date", "month", "day"]:
                continue

            try:
                sample = df[column].dropna().head(30).astype(int)
                if len(sample) > 0 and sample.between(1, 49).all():
                    numeric_columns.append(column)
            except Exception:
                pass

        return numeric_columns[:6] if len(numeric_columns) >= 6 else []

    def historical_draw():
        try:
            import pandas as pd
        except Exception:
            return None

        root = Path.cwd()
        csv_files = sorted(root.rglob("*.csv"))

        for csv_file in csv_files:
            lower_path = str(csv_file).lower()
            if ".venv" in lower_path or "__pycache__" in lower_path or ".v39_local_backups" in lower_path:
                continue

            try:
                df = pd.read_csv(csv_file, encoding="utf-8-sig")
            except Exception:
                try:
                    df = pd.read_csv(csv_file)
                except Exception:
                    continue

            columns = detect_number_columns(df)

            if not columns:
                continue

            rows = []

            for _, row in df.iterrows():
                numbers = []

                for column in columns:
                    try:
                        value = int(row[column])
                        if 1 <= value <= 49:
                            numbers.append(value)
                    except Exception:
                        pass

                if len(set(numbers)) == 6:
                    rows.append(sorted(numbers))

            if rows:
                return random.choice(rows)

        return None

    def create_draw(mode: str, historical_mode: str):
        if mode == historical_mode:
            drawn = historical_draw()

            if drawn:
                return drawn, tx("\u0440\u0435\u0430\u043b\u0435\u043d \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0442\u0438\u0440\u0430\u0436", "real historical draw")

            return sorted(random.sample(range(1, 50), 6)), tx(
                "\u0441\u043b\u0443\u0447\u0430\u0435\u043d \u0442\u0438\u0440\u0430\u0436, \u0437\u0430\u0449\u043e\u0442\u043e \u043d\u044f\u043c\u0430 \u043d\u0430\u043b\u0438\u0447\u043d\u0430 \u0438\u0441\u0442\u043e\u0440\u0438\u044f",
                "random draw because historical data is unavailable",
            )

        return sorted(random.sample(range(1, 50), 6)), tx("\u0441\u043b\u0443\u0447\u0430\u0435\u043d \u0432\u0438\u0440\u0442\u0443\u0430\u043b\u0435\u043d \u0442\u0438\u0440\u0430\u0436", "random virtual draw")

    def completed_combos():
        return [(index, get_combo(index)) for index in range(1, 5) if len(get_combo(index)) == 6]

    def incomplete_combos():
        return [(index, get_combo(index)) for index in range(1, 5) if 0 < len(get_combo(index)) < 6]

    def match_text(count: int) -> str:
        if count == 6:
            return tx("\u041f\u044a\u043b\u043d\u043e \u0441\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u0435 \u0432 \u0441\u0438\u043c\u0443\u043b\u0430\u0446\u0438\u044f\u0442\u0430.", "Full match in the simulation.")
        if count == 5:
            return tx("\u0418\u0437\u043a\u043b\u044e\u0447\u0438\u0442\u0435\u043b\u043d\u043e \u0441\u0438\u043b\u0435\u043d \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442.", "Very strong simulation result.")
        if count == 4:
            return tx("\u041c\u043d\u043e\u0433\u043e \u0434\u043e\u0431\u044a\u0440 \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442 \u0432 \u0442\u0430\u0437\u0438 \u0441\u0438\u043c\u0443\u043b\u0430\u0446\u0438\u044f.", "Very good result in this simulation.")
        if count == 3:
            return tx("\u0414\u043e\u0431\u044a\u0440 \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442 \u0432 \u0441\u0438\u043c\u0443\u043b\u0430\u0446\u0438\u044f\u0442\u0430.", "Good result in the simulation.")
        if count in [1, 2]:
            return tx("\u0418\u043c\u0430 \u0447\u0430\u0441\u0442\u0438\u0447\u043d\u0438 \u0441\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u044f.", "There are partial matches.")
        return tx("\u041d\u044f\u043c\u0430 \u0441\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u044f \u0432 \u0442\u043e\u0432\u0430 \u0440\u0430\u0437\u0438\u0433\u0440\u0430\u0432\u0430\u043d\u0435.", "There are no matches in this simulation.")

    render_css()

    st.markdown("## " + tx("\u0421\u0438\u043c\u0443\u043b\u0430\u0446\u0438\u044f / \u0420\u0430\u0437\u0438\u0433\u0440\u0430\u0439 \u0442\u043e\u0442\u043e", "Simulation / Play Toto"))

    st.markdown(
        '<div class="warning-soft">'
        + tx(
            "\u041f\u043e\u043f\u044a\u043b\u043d\u0438 \u0434\u0438\u0433\u0438\u0442\u0430\u043b\u0435\u043d \u0444\u0438\u0448 6/49 \u0441 \u0434\u043e 4 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438. \u041c\u0430\u0440\u043a\u0438\u0440\u0430\u0439 \u0447\u0438\u0441\u043b\u0430, \u043f\u043e\u0441\u043b\u0435 \u0440\u0430\u0437\u0438\u0433\u0440\u0430\u0439 \u0442\u0438\u0440\u0430\u0436. \u0422\u043e\u0432\u0430 \u0435 \u0441\u0438\u043c\u0443\u043b\u0430\u0446\u0438\u044f, \u043d\u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f.",
            "Fill a digital 6/49 ticket with up to 4 combinations. Mark numbers, then play a draw. This is a simulation, not a guarantee.",
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    message = st.session_state.pop("v39_simulation_live_message", None)
    if message:
        st.warning(message)

    mode_random = tx("\u0421\u043b\u0443\u0447\u0430\u0435\u043d \u0432\u0438\u0440\u0442\u0443\u0430\u043b\u0435\u043d \u0442\u0438\u0440\u0430\u0436", "Random virtual draw")
    mode_historical = tx("\u0420\u0435\u0430\u043b\u0435\u043d \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0442\u0438\u0440\u0430\u0436", "Real historical draw")

    mode = st.radio(
        tx("\u041a\u0430\u043a \u0434\u0430 \u0441\u0435 \u0440\u0430\u0437\u0438\u0433\u0440\u0430\u0435?", "How should it be played?"),
        [mode_random, mode_historical],
        horizontal=True,
        key="v39_simulation_live_mode",
    )

    st.markdown(
        f"""
        <div class="v39-sim-shell">
            <div class="v39-sim-title">
                <div>
                    <div class="v39-sim-title-main">{tx('\u0414\u0438\u0433\u0438\u0442\u0430\u043b\u0435\u043d \u0444\u0438\u0448 6/49', 'Digital 6/49 ticket')}</div>
                    <div class="v39-sim-title-sub">{tx('\u0415\u0434\u0438\u043d \u0444\u0438\u0448 \u0441 4 \u043e\u0442\u0434\u0435\u043b\u043d\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438', 'One ticket with 4 separate combinations')}</div>
                </div>
                <div class="v39-sim-title-main">\u25ce 6/49</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


    # V39_MODEL_TICKET_BUTTON_START
    model_button_col, model_hint_col = st.columns([1, 2])

    with model_button_col:
        if st.button(
            tx("\U0001f3af \u0413\u0435\u043d\u0435\u0440\u0438\u0440\u0430\u0439 \u0444\u0438\u0448 \u043e\u0442 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435", "\U0001f3af Generate ticket from models"),
            key="v39_generate_ticket_from_models",
            type="primary",
            width="stretch",
        ):
            _v39_apply_model_ticket()
            rerun_page()

    with model_hint_col:
        st.caption(
            tx(
                "\u0411\u0443\u0442\u043e\u043d\u044a\u0442 \u043f\u043e\u043f\u044a\u043b\u0432\u0430 \u0441\u044a\u0449\u0438\u044f \u0444\u0438\u0448 \u0441 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u043e\u0442 \u043d\u0430\u043b\u0438\u0447\u043d\u0438\u0442\u0435 JSON \u043c\u043e\u0434\u0435\u043b\u0438. \u041c\u043e\u0436\u0435\u0448 \u0434\u0430 \u0433\u0438 \u043f\u0440\u043e\u043c\u0435\u043d\u044f\u0448 \u0440\u044a\u0447\u043d\u043e.",
                "The button fills the same ticket with combinations from the available JSON models. You can still edit them manually.",
            )
        )
    # V39_MODEL_TICKET_BUTTON_END


    left_top, right_top = st.columns(2)
    with left_top:
        render_combo(1)
    with right_top:
        render_combo(2)

    left_bottom, right_bottom = st.columns(2)
    with left_bottom:
        render_combo(3)
    with right_bottom:
        render_combo(4)

    st.markdown("### " + tx("\u041e\u0431\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u043d\u0430 \u0444\u0438\u0448\u0430", "Ticket summary"))

    summary_lines = ""
    combo_label = tx("\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f", "Combination")

    for index in range(1, 5):
        values = get_combo(index)

        if len(values) == 0:
            status = tx("\u043d\u044f\u043c\u0430 \u0438\u0437\u0431\u0440\u0430\u043d\u0438 \u0447\u0438\u0441\u043b\u0430", "no selected numbers")
        elif len(values) < 6:
            status = tx(
                f"\u0438\u0437\u0431\u0440\u0430\u043d\u0438 {len(values)} \u043e\u0442 6: {fmt_numbers(values)}",
                f"{len(values)} of 6 selected: {fmt_numbers(values)}",
            )
        else:
            status = fmt_numbers(values)

        summary_lines += f'<div class="v39-summary-line"><strong>{combo_label} {index}:</strong> {status}</div>'

    st.markdown(f'<div class="v39-summary-box">{summary_lines}</div>', unsafe_allow_html=True)

    play_col, clear_col = st.columns(2)

    with play_col:
        if st.button(
            tx("\u0420\u0430\u0437\u0438\u0433\u0440\u0430\u0439 \u0442\u0438\u0440\u0430\u0436", "Play draw"),
            key="v39_simulation_live_play",
            type="primary",
            width="stretch",
        ):
            if not completed_combos():
                st.session_state["v39_simulation_live_message"] = tx(
                    "\u0417\u0430 \u0440\u0430\u0437\u0438\u0433\u0440\u0430\u0432\u0430\u043d\u0435 \u0435 \u043d\u0443\u0436\u043d\u0430 \u043f\u043e\u043d\u0435 \u0435\u0434\u043d\u0430 \u043f\u044a\u043b\u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0441 6 \u0447\u0438\u0441\u043b\u0430.",
                    "At least one complete 6-number combination is needed to play.",
                )
                st.session_state["v39_simulation_live_show_result"] = False
                rerun_page()

            drawn, source = create_draw(mode, mode_historical)
            st.session_state["v39_simulation_live_drawn_numbers"] = drawn
            st.session_state["v39_simulation_live_source"] = source
            st.session_state["v39_simulation_live_show_result"] = True
            rerun_page()

    with clear_col:
        if st.button(
            tx("\u0418\u0437\u0447\u0438\u0441\u0442\u0438 \u0446\u0435\u043b\u0438\u044f \u0444\u0438\u0448", "Clear whole ticket"),
            key="v39_simulation_live_clear_all",
            width="stretch",
        ):
            for index in range(1, 5):
                set_combo(index, [])
            st.session_state["v39_simulation_live_show_result"] = False
            st.session_state.pop("v39_simulation_live_drawn_numbers", None)
            rerun_page()

    if not st.session_state.get("v39_simulation_live_show_result", False):
        st.info(
            tx(
                "\u041c\u0430\u0440\u043a\u0438\u0440\u0430\u0439 \u0435\u0434\u043d\u0430 \u0438\u043b\u0438 \u043f\u043e\u0432\u0435\u0447\u0435 \u043f\u044a\u043b\u043d\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u0438 \u043d\u0430\u0442\u0438\u0441\u043d\u0438 \u201e\u0420\u0430\u0437\u0438\u0433\u0440\u0430\u0439 \u0442\u0438\u0440\u0430\u0436\u201c.",
                "Mark one or more complete combinations and click 'Play draw'.",
            )
        )
        return

    drawn_numbers = st.session_state.get("v39_simulation_live_drawn_numbers", [])
    draw_source = st.session_state.get("v39_simulation_live_source", "")

    st.markdown("## " + tx("\u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442 \u043e\u0442 \u0440\u0430\u0437\u0438\u0433\u0440\u0430\u0432\u0430\u043d\u0435\u0442\u043e", "Simulation result"))

    drawn_label = tx("\u0418\u0437\u0442\u0435\u0433\u043b\u0435\u043d\u0438 \u0447\u0438\u0441\u043b\u0430", "Drawn numbers")
    draw_type_label = tx("\u0422\u0438\u043f \u0442\u0438\u0440\u0430\u0436", "Draw type")

    st.markdown(
        f"""
        <div class="v39-result-card">
            <div class="v39-selected-row">
                <span class="v39-selected-label">{drawn_label}:</span>
                {chips(drawn_numbers, drawn=True)}
            </div>
            <div class="v39-summary-line"><strong>{draw_type_label}:</strong> {draw_source}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for index, values in completed_combos():
        matches = sorted(set(values) & set(drawn_numbers))
        count = len(matches)

        st.markdown("### " + tx(f"\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f {index}", f"Combination {index}"))

        your_numbers_label = tx("\u0422\u0432\u043e\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u0430", "Your numbers")
        matches_label = tx("\u0421\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u044f", "Matches")
        matched_numbers_label = tx("\u0421\u044a\u0432\u043f\u0430\u0434\u043d\u0430\u043b\u0438 \u0447\u0438\u0441\u043b\u0430", "Matched numbers")

        st.markdown(
            f"""
            <div class="v39-result-card">
                <div class="v39-selected-row">
                    <span class="v39-selected-label">{your_numbers_label}:</span>
                    {chips(values, matched=matches)}
                </div>
                <div class="v39-summary-line"><strong>{matches_label}:</strong> {count} / 6</div>
                <div class="v39-summary-line"><strong>{matched_numbers_label}:</strong> {fmt_numbers(matches)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if count >= 3:
            st.success(match_text(count))
        elif count > 0:
            st.info(match_text(count))
        else:
            st.warning(match_text(count))

    for index, values in incomplete_combos():
        st.warning(
            tx(
                f"\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f {index} \u0438\u043c\u0430 {len(values)} \u043e\u0442 6 \u0447\u0438\u0441\u043b\u0430 \u0438 \u043d\u0435 \u0443\u0447\u0430\u0441\u0442\u0432\u0430 \u0432 \u0440\u0430\u0437\u0438\u0433\u0440\u0430\u0432\u0430\u043d\u0435\u0442\u043e.",
                f"Combination {index} has {len(values)} of 6 numbers and is not included in the simulation.",
            )
        )

    st.info(
        tx(
            "\u0422\u043e\u0432\u0430 \u0435 \u0441\u0438\u043c\u0443\u043b\u0430\u0446\u0438\u044f. \u0422\u044f \u043d\u0435 \u043f\u0440\u043e\u043c\u0435\u043d\u044f \u0440\u0435\u0430\u043b\u043d\u0438\u044f \u0448\u0430\u043d\u0441 \u0437\u0430 \u0442\u043e\u0447\u043d\u0430 6/49 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f: 1:13,983,816.",
            "This is a simulation. It does not change the real odds for an exact 6/49 combination: 1:13,983,816.",
        )
    )

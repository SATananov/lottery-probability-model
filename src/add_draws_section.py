from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st
from src.v110_user_friendly_ui_helpers import friendly_status

from src.v73_ticket_pack_performance_tracker_engine import evaluate_current_pack_against_draw
from src.v95_active_plan_auto_evaluation_engine import evaluate_active_plan_against_pending_draw
from src.v96_add_draw_controlled_flow_engine import load_add_draw_controlled_flow_summary
from src.v97_real_draw_lifecycle_engine import load_real_draw_lifecycle_summary
from src.v143_2_official_draw_github_sync_audit_engine import (
    capture_git_snapshot,
    synchronize_official_draw_outputs,
)
from src.v143_2_official_draw_github_sync_section import (
    render_git_sync_preflight,
    render_git_sync_result,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "historical_draws.csv"

NUMBER_COLS = [f"n{i}" for i in range(1, 7)]

MODEL_SCRIPTS = [
    ROOT / "scripts" / "v40_create_normalized_draw_events.py",
    ROOT / "scripts" / "v41_build_canonical_draw_events.py",
    ROOT / "scripts" / "v41_train_rules_aware_models.py",
    ROOT / "scripts" / "v42_build_combined_positive_negative_foundation.py",
    ROOT / "scripts" / "v43_1_refine_interval_rhythm_foundation.py",
    ROOT / "scripts" / "v44_1_refine_final_ensemble_ticket_foundation.py",
    ROOT / "scripts" / "v45_train_prediction_engine_pro.py",
    ROOT / "scripts" / "v50_build_pair_group_intelligence.py",
    ROOT / "scripts" / "v51_build_ticket_portfolio_intelligence.py",
    ROOT / "scripts" / "v53_build_ticket_coverage_intelligence.py",
    ROOT / "scripts" / "v54_build_pattern_balance_engine.py",
    ROOT / "scripts" / "v55_build_number_profile_center.py",
    ROOT / "scripts" / "v56_build_draw_similarity_search.py",
    ROOT / "scripts" / "v57_build_hot_cold_stable_center.py",
    ROOT / "scripts" / "v58_build_smart_ensemble_score_2.py",
    ROOT / "scripts" / "v59_build_smart_ticket_builder_2.py",
    ROOT / "scripts" / "v60_build_ticket_builder_2_polish_export.py",
    ROOT / "scripts" / "v61_build_draw_result_analyzer.py",
    ROOT / "scripts" / "v62_build_model_performance_tracker.py",
    ROOT / "scripts" / "v63_build_model_reliability_dashboard.py",
    ROOT / "scripts" / "v65_build_model_weighting_center.py",
    ROOT / "scripts" / "v66_build_weighted_smart_ensemble.py",
    ROOT / "scripts" / "v67_build_weighted_ticket_builder.py",
    ROOT / "scripts" / "v68_build_weighted_portfolio_optimizer.py",
    ROOT / "scripts" / "v69_build_portfolio_improvement_suggestions.py",
    ROOT / "scripts" / "v70_build_applied_candidate_portfolio.py",
    ROOT / "scripts" / "v71_build_ticket_pack_export.py",
    ROOT / "scripts" / "v73_build_ticket_pack_performance_tracker.py",
    ROOT / "scripts" / "v75_build_neural_meta_learner.py",
    ROOT / "scripts" / "v76_build_explainability_validation_center.py",
    ROOT / "scripts" / "v77_build_decision_recommendation_center.py",
    ROOT / "scripts" / "v78_build_final_play_plan_center.py",
    ROOT / "scripts" / "v79_build_ticket_pack_export_center.py",
    ROOT / "scripts" / "v80_build_final_system_audit_center.py",
    ROOT / "scripts" / "v81_build_final_ux_navigation_center.py",
    ROOT / "scripts" / "v82_build_final_release_package_center.py",
    ROOT / "scripts" / "v74_build_model_dependency_sync_center.py",
    ROOT / "scripts" / "v94_build_active_budget_plan_tracker.py",
    ROOT / "scripts" / "v95_build_active_plan_auto_evaluation.py",
    ROOT / "scripts" / "v96_build_add_draw_controlled_flow.py",
    ROOT / "scripts" / "v97_build_real_draw_lifecycle.py",
    ROOT / "scripts" / "v98_build_active_plan_result_history.py",
    ROOT / "scripts" / "v99_build_final_user_dashboard.py",
    ROOT / "scripts" / "v100_build_final_release_lock.py",
    ROOT / "scripts" / "v101_build_real_use_protocol.py",
    ROOT / "scripts" / "v106_2_build_post_draw_historical_schema_sync.py",
    ROOT / "scripts" / "v106_1_build_post_draw_dataset_sync.py",
    ROOT / "scripts" / "v106_build_post_draw_status_sync.py",
    ROOT / "scripts" / "v107_build_model_training_policy_refresh_control.py",
    ROOT / "scripts" / "v109_build_sqlite_played_tickets_journal.py",
    ROOT / "scripts" / "v109_1_build_journal_ui_bulgarian_polish.py",
    ROOT / "scripts" / "v117_build_real_ticket_pack_builder.py",
    ROOT / "scripts" / "v118_build_model_system_ticket_builder.py",
    ROOT / "scripts" / "v102_build_runtime_hardening.py",
    ROOT / "scripts" / "v103_build_clean_release_checkpoint.py",
    ROOT / "scripts" / "v104_build_final_audit_refresh.py",
]

HEAVY_LAB_SCRIPT_NAMES = {
    "v67_build_weighted_ticket_builder.py",
    "v75_build_neural_meta_learner.py",
}

DEFAULT_REFRESH_TIMEOUT_SECONDS = 120

FAST_MODEL_SCRIPTS = [
    script for script in MODEL_SCRIPTS if script.name not in HEAVY_LAB_SCRIPT_NAMES
]

HEAVY_LAB_SCRIPTS = [
    script for script in MODEL_SCRIPTS if script.name in HEAVY_LAB_SCRIPT_NAMES
]


def refresh_mode_label_to_value(label: str) -> str:
    if str(label).strip().startswith("Пълен"):
        return "full"
    if str(label).strip().startswith("Само"):
        return "heavy"
    return "fast"


def run_command(args: list[str], timeout_seconds: int | None = None) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            args,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        output = (stdout or "") + ("\n" + stderr if stderr else "")
        timeout_text = (
            f"Прекъснато след {timeout_seconds} секунди. "
            "Скриптът е твърде тежък за автоматичния refresh и трябва да се пуска ръчно."
        )
        return False, (timeout_text + "\n" + output.strip()).strip()
    except FileNotFoundError as exc:
        return False, f"Командата не е намерена: {exc}"

    output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    return completed.returncode == 0, output.strip()


def _load_next_ticket_pack_summary() -> dict[str, Any]:
    path = ROOT / "reports" / "v117_real_ticket_pack_builder_summary.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _numbers_text(numbers: Any) -> str:
    if not isinstance(numbers, list):
        return "—"
    values = []
    for value in numbers:
        try:
            values.append(str(int(value)))
        except Exception:
            continue
    return ", ".join(values) if values else "—"


def _show_next_ticket_pack_ready() -> None:
    summary = _load_next_ticket_pack_summary()
    if not summary:
        st.warning("Тиражът е записан, но готовият фиш пакет още не е намерен. Отвори 'Готов фиш пакет' и натисни 'Обнови пакета'.")
        return

    latest_draw = summary.get("latest_dataset_draw") or {}
    latest_date = summary.get("latest_dataset_draw_date") or latest_draw.get("date") or "—"
    next_target = summary.get("next_target_draw_date") or "следващ тираж"
    st.success(
        "Новият пакет за следващия тираж е готов. "
        f"Последен въведен тираж: {latest_date}; целеви тираж: {next_target}."
    )
    cols = st.columns(4)
    cols[0].metric("Фишове", summary.get("ticket_count", 0))
    cols[1].metric("Комбинации", summary.get("total_lines", 0))
    cols[2].metric("Цена", summary.get("total_price_label", "—"))
    cols[3].metric("Последни числа", _numbers_text(latest_draw.get("numbers")))

    cards = summary.get("cards") or []
    if cards:
        with st.expander("Покажи първия готов фиш", expanded=True):
            first_card = cards[0]
            st.write(first_card.get("title") or "Фиш 1")
            for line in first_card.get("lines", []) or []:
                st.write(f"Ред {line.get('line_no', '—')}: {line.get('numbers_text') or _numbers_text(line.get('numbers'))}")

    if st.button("Отвори готовия фиш пакет", width="stretch", key="add_draw_open_ready_ticket_pack"):
        st.session_state["_pending_navigation_group"] = "✅ Финален план за игра"
        st.session_state["_pending_navigation_page"] = "Готов фиш пакет"
        st.rerun()


def read_dataset() -> tuple[list[dict[str, str]], list[str]]:
    if not DATA_PATH.exists():
        fieldnames = ["date", "year", "draw_no", "draw_position", *NUMBER_COLS, "bonus_number", "source"]
        return [], fieldnames

    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]
        fieldnames = list(reader.fieldnames or [])

    if not fieldnames:
        fieldnames = ["date", "year", "draw_no", "draw_position", *NUMBER_COLS, "bonus_number", "source"]

    return rows, fieldnames


def ensure_columns(fieldnames: list[str]) -> list[str]:
    for column in ["draw_id", "date", "year", "draw_number", "draw_no", "draw_position", *NUMBER_COLS, "bonus_number", "source_url", "source"]:
        if column not in fieldnames:
            fieldnames.append(column)
    return fieldnames




def _finalize_rows_for_v40_v41(rows: list[dict[str, str]], fieldnames: list[str]) -> list[dict[str, str]]:
    existing_ids: list[int] = []
    for row in rows:
        try:
            value = int(float(str(row.get("draw_id", "")).strip()))
        except (TypeError, ValueError):
            continue
        if value > 0:
            existing_ids.append(value)
    next_id = (max(existing_ids) if existing_ids else 0) + 1

    for row in rows:
        for column in fieldnames:
            row.setdefault(column, "")
        if not str(row.get("draw_number", "")).strip() and str(row.get("draw_no", "")).strip():
            row["draw_number"] = str(row.get("draw_no", "")).strip()
        if not str(row.get("draw_no", "")).strip() and str(row.get("draw_number", "")).strip():
            row["draw_no"] = str(row.get("draw_number", "")).strip()
        if not str(row.get("draw_position", "")).strip():
            row["draw_position"] = "1"
        row.setdefault("source_url", "")
        try:
            valid_id = int(float(str(row.get("draw_id", "")).strip())) > 0
        except (TypeError, ValueError):
            valid_id = False
        if not valid_id:
            row["draw_id"] = str(next_id)
            next_id += 1
    return rows

def normalize_numbers(values: list[Any]) -> list[int]:
    numbers: list[int] = []
    for value in values:
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue

        if 1 <= number <= 49:
            numbers.append(number)

    return sorted(numbers)


def validate_draw(numbers: list[int], bonus: int | None, label: str) -> list[str]:
    errors: list[str] = []

    if len(numbers) != 6:
        errors.append(f"{label}: трябва да има точно 6 основни числа.")

    if len(set(numbers)) != len(numbers):
        errors.append(f"{label}: основните числа не трябва да се повтарят.")

    if not all(1 <= number <= 49 for number in numbers):
        errors.append(f"{label}: всички основни числа трябва да са между 1 и 49.")

    if bonus is not None:
        if not (1 <= bonus <= 49):
            errors.append(f"{label}: допълнителното число трябва да е между 1 и 49.")
        if bonus in numbers:
            errors.append(f"{label}: допълнителното число не трябва да повтаря основно число.")

    return errors


def build_row(
    fieldnames: list[str],
    draw_date: date,
    year: int,
    draw_no: int,
    draw_position: int,
    numbers: list[int],
    bonus: int | None,
    source: str,
) -> dict[str, str]:
    row = {field: "" for field in fieldnames}

    row["date"] = draw_date.isoformat()
    row["year"] = str(year)
    row["draw_no"] = str(draw_no)
    row["draw_number"] = str(draw_no)
    row["draw_position"] = str(draw_position)
    row["bonus_number"] = "" if bonus is None else str(bonus)
    row["source"] = source.strip()
    row["source_url"] = ""

    for column, number in zip(NUMBER_COLS, sorted(numbers)):
        row[column] = str(number)

    return row


def same_draw(row: dict[str, str], year: int, draw_no: int, position: int) -> bool:
    return (
        str(row.get("year", "")).strip() == str(year)
        and str(row.get("draw_no", "")).strip() == str(draw_no)
        and str(row.get("draw_position", "")).strip() == str(position)
    )


def save_draws(
    draw_date: date,
    year: int,
    draw_no: int,
    payloads: list[tuple[int, list[int], int | None]],
    source: str,
    replace_existing: bool,
) -> int:
    rows, fieldnames = read_dataset()
    fieldnames = ensure_columns(fieldnames)

    if replace_existing:
        positions = {position for position, _, _ in payloads}
        rows = [
            row
            for row in rows
            if not any(same_draw(row, year, draw_no, position) for position in positions)
        ]

    new_rows = [
        build_row(
            fieldnames=fieldnames,
            draw_date=draw_date,
            year=year,
            draw_no=draw_no,
            draw_position=position,
            numbers=numbers,
            bonus=bonus,
            source=source,
        )
        for position, numbers, bonus in payloads
    ]

    rows.extend(new_rows)
    rows = _finalize_rows_for_v40_v41(rows, fieldnames)

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return len(new_rows)


def parse_uploaded_rows(uploaded_file: Any) -> list[dict[str, Any]]:
    if uploaded_file is None:
        return []

    raw = uploaded_file.getvalue().decode("utf-8-sig", errors="replace")
    name = uploaded_file.name.lower()

    if name.endswith(".json"):
        payload = json.loads(raw)
        if isinstance(payload, dict):
            for key in ["draws", "rows", "data"]:
                if isinstance(payload.get(key), list):
                    return [row for row in payload[key] if isinstance(row, dict)]
            return [payload]
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        return []

    reader = csv.DictReader(raw.splitlines())
    return [dict(row) for row in reader]


def import_uploaded_rows(uploaded_file: Any, replace_existing: bool) -> int:
    uploaded_rows = parse_uploaded_rows(uploaded_file)
    if not uploaded_rows:
        return 0

    rows, fieldnames = read_dataset()
    fieldnames = ensure_columns(fieldnames)

    imported: list[dict[str, str]] = []

    for item in uploaded_rows:
        try:
            year = int(item.get("year", ""))
            draw_no = int(item.get("draw_no", item.get("draw_number", "")))
            position = int(item.get("draw_position", item.get("drawing_no", "1")))
        except (TypeError, ValueError):
            continue

        raw_date = str(item.get("date", f"{year}-01-01")).replace("/", "-")
        try:
            draw_date = date.fromisoformat(raw_date)
        except ValueError:
            draw_date = date(year, 1, 1)

        numbers = normalize_numbers([item.get(column) for column in NUMBER_COLS])

        bonus_raw = item.get("bonus_number", item.get("bonus", item.get("additional_number", "")))
        try:
            bonus = int(bonus_raw) if str(bonus_raw).strip() else None
        except (TypeError, ValueError):
            bonus = None

        if validate_draw(numbers, bonus, f"Теглене {position}"):
            continue

        imported.append(
            build_row(
                fieldnames=fieldnames,
                draw_date=draw_date,
                year=year,
                draw_no=draw_no,
                draw_position=position,
                numbers=numbers,
                bonus=bonus,
                source=str(item.get("source", "Импорт")),
            )
        )

    if not imported:
        return 0

    if replace_existing:
        keys = {(row["year"], row["draw_no"], row["draw_position"]) for row in imported}
        rows = [
            row for row in rows
            if (row.get("year", ""), row.get("draw_no", ""), row.get("draw_position", "")) not in keys
        ]

    rows.extend(imported)

    with DATA_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return len(imported)


def refresh_models(
    refresh_mode: str = "fast",
    timeout_seconds: int = DEFAULT_REFRESH_TIMEOUT_SECONDS,
) -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []

    if refresh_mode == "full":
        scripts = MODEL_SCRIPTS
    elif refresh_mode == "heavy":
        scripts = HEAVY_LAB_SCRIPTS
    else:
        scripts = FAST_MODEL_SCRIPTS

    for script in scripts:
        if not script.exists():
            results.append((script.name, False, "Файлът липсва."))
            continue

        script_timeout = max(30, int(timeout_seconds or DEFAULT_REFRESH_TIMEOUT_SECONDS))
        ok, output = run_command([sys.executable, str(script)], timeout_seconds=script_timeout)
        results.append((script.name, ok, output[-2000:]))

    if refresh_mode == "fast" and HEAVY_LAB_SCRIPTS:
        skipped = ", ".join(script.name for script in HEAVY_LAB_SCRIPTS)
        results.append((
            "heavy_lab_refresh",
            True,
            "Бързият режим пропусна тежките лабораторни скриптове: " + skipped,
        ))

    return results


def sync_to_github(
    year: int,
    draw_no: int,
    *,
    baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the Step 143.2 controlled commit, push and remote confirmation."""

    return synchronize_official_draw_outputs(
        year=year,
        draw_no=draw_no,
        baseline=baseline,
        repo_root=ROOT,
    )


def bonus_options() -> list[int | None]:
    return [None, *list(range(1, 50))]


def bonus_label(value: int | None) -> str:
    return "Няма" if value is None else str(value)


def draw_block(position: int) -> tuple[list[int], int | None]:
    st.markdown(f"### \u0422\u0435\u0433\u043b\u0435\u043d\u0435 {position}")
    st.caption(
        "\u0412\u044a\u0432\u0435\u0434\u0438 6 \u043e\u0441\u043d\u043e\u0432\u043d\u0438 \u0447\u0438\u0441\u043b\u0430 \u0432 \u043e\u0442\u0434\u0435\u043b\u043d\u0438 \u043a\u043b\u0435\u0442\u043a\u0438. "
        "\u0422\u0430\u043a\u0430 \u0441\u0435 \u0438\u0437\u0431\u044f\u0433\u0432\u0430\u0442 \u0433\u0440\u0435\u0448\u043a\u0438 \u0441\u044a\u0441 \u0437\u0430\u043f\u0435\u0442\u0430\u0438, \u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0438 \u0438 \u0440\u0430\u0437\u043c\u0435\u0441\u0442\u0432\u0430\u043d\u0435."
    )

    number_cols = st.columns(6)
    raw_values: list[str] = []

    for index, column in enumerate(number_cols, start=1):
        with column:
            value = st.text_input(
                f"\u0427\u0438\u0441\u043b\u043e {index}",
                value="",
                max_chars=2,
                key=f"add_draw_number_cell_{position}_{index}",
                placeholder="1-49",
            )
            raw_values.append(value.strip())

    filled_values = [value for value in raw_values if value]
    cell_errors: list[str] = []
    numbers: list[int] = []

    for index, value in enumerate(raw_values, start=1):
        if not value:
            continue

        try:
            number = int(value)
        except ValueError:
            cell_errors.append(
                f"\u0422\u0435\u0433\u043b\u0435\u043d\u0435 {position}, \u0447\u0438\u0441\u043b\u043e {index}: "
                "\u0432\u044a\u0432\u0435\u0434\u0438 \u0441\u0430\u043c\u043e \u0447\u0438\u0441\u043b\u043e."
            )
            continue

        if not 1 <= number <= 49:
            cell_errors.append(
                f"\u0422\u0435\u0433\u043b\u0435\u043d\u0435 {position}, \u0447\u0438\u0441\u043b\u043e {index}: "
                "\u0447\u0438\u0441\u043b\u043e\u0442\u043e \u0442\u0440\u044f\u0431\u0432\u0430 \u0434\u0430 \u0435 \u043c\u0435\u0436\u0434\u0443 1 \u0438 49."
            )
            continue

        numbers.append(number)

    for error in cell_errors:
        st.error(error)

    if filled_values and not cell_errors:
        if len(numbers) < 6:
            st.caption(
                f"\u041f\u043e\u043f\u044a\u043b\u043d\u0435\u043d\u0438 \u0441\u0430 {len(numbers)} "
                "\u043e\u0442 6 \u043e\u0441\u043d\u043e\u0432\u043d\u0438 \u0447\u0438\u0441\u043b\u0430."
            )
        elif len(set(numbers)) != len(numbers):
            st.warning(
                "\u0418\u043c\u0430 \u043f\u043e\u0432\u0442\u043e\u0440\u0435\u043d\u043e \u043e\u0441\u043d\u043e\u0432\u043d\u043e \u0447\u0438\u0441\u043b\u043e. "
                "\u041f\u0440\u043e\u0432\u0435\u0440\u0438 \u043a\u043b\u0435\u0442\u043a\u0438\u0442\u0435 \u043f\u0440\u0435\u0434\u0438 \u0437\u0430\u043f\u0438\u0441."
            )
        elif len(numbers) == 6:
            st.success(
                "\u041e\u0441\u043d\u043e\u0432\u043d\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u0430 \u0441\u0430 \u043f\u043e\u043f\u044a\u043b\u043d\u0435\u043d\u0438 \u043a\u043e\u0440\u0435\u043a\u0442\u043d\u043e."
            )

    bonus = st.selectbox(
        f"\u0414\u043e\u043f\u044a\u043b\u043d\u0438\u0442\u0435\u043b\u043d\u043e \u0447\u0438\u0441\u043b\u043e \u2014 \u0442\u0435\u0433\u043b\u0435\u043d\u0435 {position}",
        options=bonus_options(),
        format_func=bonus_label,
        key=f"add_draw_bonus_{position}",
    )

    return numbers, bonus

def render() -> None:
    st.title("Добавяне на тираж")
    st.caption("Записва един тираж с едно или две тегления. Всяко теглене има 6 основни числа и отделно допълнително число.")

    auto_update = st.checkbox(
        "Автоматично обнови анализите след запис",
        value=True,
        key="add_draw_auto_update_models",
        help=(
            "По подразбиране се използва бърз режим, който пропуска тежките лабораторни скриптове "
            "и не позволява един бавен процес да блокира приложението."
        ),
    )

    if auto_update:
        refresh_mode_label = st.selectbox(
            "Режим на обновяване след запис",
            options=[
                "Бърз режим за реален тираж",
                "Пълен режим с тежки лаборатории",
                "Само тежки лаборатории",
            ],
            index=0,
            key="add_draw_refresh_mode",
            help=(
                "Бързият режим е препоръчителен за реално добавяне на тираж. "
                "Пълният режим може да отнеме много време, защото включва тежки генератори и обучение."
            ),
        )
        refresh_mode = refresh_mode_label_to_value(refresh_mode_label)
        refresh_timeout_seconds = int(st.number_input(
            "Максимално време за един скрипт",
            min_value=30,
            max_value=900,
            value=DEFAULT_REFRESH_TIMEOUT_SECONDS,
            step=30,
            key="add_draw_refresh_timeout_seconds",
            help="Ако отделен скрипт надвиши това време, refresh-ът продължава и показва предупреждение.",
        ))
        if refresh_mode == "fast":
            st.caption(
                "Бързият режим пропуска тежките лабораторни процеси. "
                "Те остават налични за ръчно стартиране от съответните контролни страници."
            )
        else:
            st.warning(
                "Избран е режим за пълно преизчисляване. Използвай го ръчно, когато е необходимо "
                "цялостно обновяване, а не след всеки нов тираж."
            )
    else:
        refresh_mode = "fast"
        refresh_timeout_seconds = DEFAULT_REFRESH_TIMEOUT_SECONDS

    auto_github = st.checkbox(
        "Синхронизирай новите данни и модели в GitHub",
        value=True,
        key="add_draw_sync_github",
        help=(
            "Системата подготвя само разрешените файлове с данни, модели и отчети, "
            "качва записа към текущия Git клон и проверява съвпадението с GitHub."
        ),
    )
    git_sync_baseline = capture_git_snapshot(ROOT)
    render_git_sync_preflight(git_sync_baseline, enabled=auto_github)

    # step96_controlled_flow_marker
    controlled_flow = load_add_draw_controlled_flow_summary()
    controlled_steps = controlled_flow.get("workflow_steps", []) or []
    controlled_snapshot = controlled_flow.get("current_snapshot", {}) or {}

    st.markdown("#### Контролиран ред при добавяне на тираж")
    st.caption(controlled_flow.get("intro_bg", ""))

    flow_lines = []
    for item in controlled_steps:
        flow_lines.append(
            f"**{item.get('step_order', '')}. {item.get('title_bg', '')}** — "
            f"{item.get('description_bg', '')}  \\n"
            f"_Контрол:_ {item.get('guard_bg', '')}"
        )

    if flow_lines:
        st.markdown("\n\n".join(flow_lines))

    lifecycle = load_real_draw_lifecycle_summary()
    lifecycle_state = lifecycle.get("current_state", {}) or {}
    lifecycle_plan = lifecycle_state.get("active_plan", {}) or {}
    st.markdown("#### Реален цикъл на нов тираж")
    st.caption(lifecycle.get("next_user_action_bg", ""))
    lifecycle_cols = st.columns(4)
    lifecycle_cols[0].metric("Състояние", friendly_status(lifecycle.get("status")))
    lifecycle_cols[1].metric("Редове в данните", int(lifecycle_state.get("dataset_rows", 0)))
    lifecycle_cols[2].metric("Преди запис", friendly_status((lifecycle_state.get("step95", {}) or {}).get("status")))
    lifecycle_cols[3].metric("План", f"{lifecycle_plan.get('strategy_type', '-')} / {lifecycle_plan.get('combination_count', 0)}")

    if controlled_snapshot.get("active_plan_available"):
        active_plan_cost_text = controlled_snapshot.get("active_plan_cost_text")
        if not active_plan_cost_text:
            try:
                active_plan_cost_text = f"{float(controlled_snapshot.get('active_plan_cost_eur', 0.0)):.2f}"
            except (TypeError, ValueError):
                active_plan_cost_text = "0.00"

        active_plan_label = controlled_snapshot.get("active_plan_label_bg") or "бюджетен план"
        st.info(
            f"Активният {active_plan_label} е наличен: "
            f"{controlled_snapshot.get('active_plan_type', '')}, "
            f"{controlled_snapshot.get('active_plan_combinations', 0)} комбинации, "
            f"{active_plan_cost_text} EUR. "
            "Системата ще го провери със същите въведени числа преди запис."
        )
    else:
        st.warning(
            "Няма активен бюджетен план. Проверката на активния план ще бъде пропусната, докато не се запази план от Бюджетния съветник."
        )

    evaluate_pack_before_save = st.checkbox(
        "Оцени текущия пакет преди запис на тиража",
        value=True,
        key="add_draw_evaluate_pack_before_save",
        help=(
            "Първо проверява активния пакет срещу въведените числа "
            "и записва история на представянето. След това тиражът се записва в данните."
        ),
    )

    evaluate_active_budget_plan_before_save = st.checkbox(
        "Провери активния бюджетен план преди запис на тиража",
        value=True,
        key="add_draw_evaluate_active_budget_plan_before_save",
        help=(
            "Взема същите въведени числа от тази страница и проверява активния план "
            "преди dataset-ът да бъде обновен. Така няма второ въвеждане и няма backfit."
        ),
    )

    replace_existing = st.checkbox(
        "Замени съществуващо теглене, ако вече го има",
        value=True,
        key="add_draw_replace_existing",
    )

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Качи файл",
        type=["txt", "csv", "json"],
        key="add_draw_upload_file",
    )

    if uploaded_file is not None:
        st.info("Файловият импорт очаква колони date/year/draw_no/draw_position/n1..n6/bonus_number.")
        if st.button("Импортирай файла", key="add_draw_import_file_btn"):
            try:
                count = import_uploaded_rows(uploaded_file, replace_existing=replace_existing)
            except Exception as exc:
                st.error(f"Грешка при импорт: {exc}")
                return

            if count:
                st.success(f"Импортирани са {count} тегления.")
            else:
                st.warning("Не бяха намерени валидни редове за импорт.")

    st.markdown("---")

    col_date, col_year, col_draw_no = st.columns(3)

    with col_date:
        draw_date = st.date_input("Дата", value=date.today(), key="add_draw_date")

    with col_year:
        year = int(
            st.number_input(
                "Година",
                min_value=1958,
                max_value=2100,
                value=date.today().year,
                step=1,
                key="add_draw_year",
            )
        )

    with col_draw_no:
        draw_no = int(
            st.number_input(
                "Номер на тираж",
                min_value=1,
                max_value=9999,
                value=1,
                step=1,
                key="add_draw_number",
            )
        )

    include_second = st.checkbox(
        "Добави второ теглене към същия тираж",
        value=False,
        key="add_draw_include_second",
    )

    draw1_numbers, draw1_bonus = draw_block(1)

    if include_second:
        draw2_numbers, draw2_bonus = draw_block(2)
    else:
        draw2_numbers, draw2_bonus = [], None

    source_note = st.text_input(
        "Източник / бележка",
        value="Ръчно въвеждане",
        key="add_draw_source_note",
    )

    if st.button("Запази тиража", width="stretch", key="add_draw_save_btn"):
        if auto_github and not git_sync_baseline.get("can_sync"):
            st.error(
                "Step 143.2 блокира автоматичната GitHub синхронизация преди запис. "
                "Изчисти посочения Git проблем или изключи GitHub отметката, за да запишеш само локално."
            )
            return

        payloads: list[tuple[int, list[int], int | None]] = [(1, draw1_numbers, draw1_bonus)]
        errors = validate_draw(draw1_numbers, draw1_bonus, "Теглене 1")

        if include_second:
            payloads.append((2, draw2_numbers, draw2_bonus))
            errors.extend(validate_draw(draw2_numbers, draw2_bonus, "Теглене 2"))

        if errors:
            for error in errors:
                st.error(error)
            return


        pre_save_evaluations = []
        if evaluate_pack_before_save:
            st.info("Оценявам текущия пакет преди запис в данните.")

            for position, numbers, _bonus in payloads:
                try:
                    evaluation = evaluate_current_pack_against_draw(
                        numbers,
                        draw_date=draw_date.isoformat(),
                        draw_number=f"{draw_no}-{position}",
                        source="add_draw_pre_save",
                        persist=True,
                    )
                    pre_save_evaluations.append(evaluation)
                    history = evaluation["history_row"]
                    st.success(
                        f"Пакетът е проверен — теглене {position}: "
                        f"най-добър фиш {history['best_ticket_id']} с "
                        f"{history['best_hit_count']} попадения; "
                        f"пакетът покрива {history['package_unique_hits']} от 6 числа."
                    )
                except Exception as exc:
                    st.error(
                        "Оценката на пакета не успя. Тиражът не беше записан, "
                        f"за да не се наруши правилният процес преди обновяване: {exc}"
                    )
                    return

        if evaluate_active_budget_plan_before_save:
            st.info("Проверявам активния план срещу въведените числа преди запис в данните.")

            for position, numbers, _bonus in payloads:
                try:
                    evaluation = evaluate_active_plan_against_pending_draw(
                        numbers,
                        draw_date=draw_date.isoformat(),
                        year=year,
                        draw_no=draw_no,
                        draw_position=position,
                        persist=True,
                        source="add_draw_pre_save",
                    )
                except Exception as exc:
                    st.error(
                        "Проверката на активния план не успя. "
                        f"Тиражът не беше записан, за да не се наруши редът преди обновяване: {exc}"
                    )
                    return

                status = evaluation.get("status", "UNKNOWN")
                message = evaluation.get("message_bg", "")
                if status == "EVALUATED":
                    summary = evaluation.get("summary", {}) or {}
                    already_recorded = bool(evaluation.get("already_recorded"))
                    suffix = " Историята вече имаше запис за този план и тираж." if already_recorded else ""
                    st.success(
                        f"Активният план е проверен — теглене {position}: "
                        f"най-добра комбинация с {summary.get('best_hit_count', 0)} попадения; "
                        f"комбинации 3+ = {summary.get('rows_with_3_plus', 0)}; "
                        f"комбинации 4+ = {summary.get('rows_with_4_plus', 0)}."
                        + suffix
                    )
                elif status == "NO_ACTIVE_PLAN":
                    st.info(message or "Няма активен бюджетен план за проверка.")
                elif status == "DRAW_NOT_AFTER_ACTIVE_PLAN":
                    st.warning(message or "Въведеният тираж не е след активния план; Step 95 не записва реален резултат.")
                else:
                    st.warning(message or f"Статус на проверката: {friendly_status(status)}")

        try:
            saved_count = save_draws(
                draw_date=draw_date,
                year=year,
                draw_no=draw_no,
                payloads=payloads,
                source=source_note,
                replace_existing=replace_existing,
            )
        except Exception as exc:
            st.error(f"Грешка при запис в dataset-а: {exc}")
            return

        st.success(f"Записани са {saved_count} тегления към тираж {draw_no} / {year}.")

        if auto_update:
            with st.spinner("Обновяване на анализите в избрания режим..."):
                model_results = refresh_models(
                    refresh_mode=refresh_mode,
                    timeout_seconds=refresh_timeout_seconds,
                )

            for script_name, ok, output in model_results:
                if ok:
                    st.success(f"{script_name}: OK")
                else:
                    st.warning(f"{script_name}: проблем или липсващ файл")
                if output:
                    with st.expander(f"Изход: {script_name}"):
                        st.code(output)

            _show_next_ticket_pack_ready()
        else:
            st.warning("Тиражът е записан, но автоматичното обновяване е изключено. Пусни обновяване или отвори 'Готов фиш пакет' и натисни 'Обнови пакета'.")

        if auto_github:
            with st.spinner("Git запис, качване и потвърждение в GitHub по Step 143.2..."):
                sync_result = sync_to_github(
                    year=year,
                    draw_no=draw_no,
                    baseline=git_sync_baseline,
                )
            render_git_sync_result(sync_result)

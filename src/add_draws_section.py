from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "historical_draws.csv"

NUMBER_COLS = [f"n{i}" for i in range(1, 7)]

MODEL_SCRIPTS = [
    ROOT / "scripts" / "v41_train_rules_aware_models.py",
    ROOT / "scripts" / "v42_build_combined_positive_negative_foundation.py",
    ROOT / "scripts" / "v43_1_refine_interval_rhythm_foundation.py",
    ROOT / "scripts" / "v44_1_refine_final_ensemble_ticket_foundation.py",
    ROOT / "scripts" / "v45_train_prediction_engine_pro.py",
    ROOT / "scripts" / "v50_build_pair_group_intelligence.py",
]


def run_command(args: list[str]) -> tuple[bool, str]:
    completed = subprocess.run(
        args,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    return completed.returncode == 0, output.strip()


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
    for column in ["date", "year", "draw_no", "draw_position", *NUMBER_COLS, "bonus_number", "source"]:
        if column not in fieldnames:
            fieldnames.append(column)
    return fieldnames


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
    row["draw_position"] = str(draw_position)
    row["bonus_number"] = "" if bonus is None else str(bonus)
    row["source"] = source.strip()

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


def refresh_models() -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []

    for script in MODEL_SCRIPTS:
        if not script.exists():
            results.append((script.name, False, "Файлът липсва."))
            continue

        ok, output = run_command([sys.executable, str(script)])
        results.append((script.name, ok, output[-2000:]))

    return results


def sync_to_github(year: int, draw_no: int) -> tuple[bool, str]:
    paths_to_add = [
        "data/historical_draws.csv",
        "models/v41",
        "models/v42",
        "models/v43_1",
        "models/v44_1",
        "models/v45",
        "models/v50",
        "reports",
    ]

    ok, output = run_command(["git", "add", *paths_to_add])
    if not ok:
        return False, output

    ok, staged = run_command(["git", "diff", "--cached", "--name-only"])
    if not ok:
        return False, staged

    if not staged.strip():
        return True, "Няма нови промени за синхронизация."

    message = f"Update draw {draw_no} {year} and refresh models"
    ok, commit_output = run_command(["git", "commit", "-m", message])
    if not ok:
        return False, commit_output

    ok, push_output = run_command(["git", "push"])
    if not ok:
        return False, push_output

    return True, commit_output + "\n" + push_output


def bonus_options() -> list[int | None]:
    return [None, *list(range(1, 50))]


def bonus_label(value: int | None) -> str:
    return "Няма" if value is None else str(value)


def draw_block(position: int) -> tuple[list[int], int | None]:
    st.markdown(f"### Теглене {position}")

    numbers = st.multiselect(
        f"Основни числа — теглене {position}",
        options=list(range(1, 50)),
        default=[],
        max_selections=6,
        key=f"add_draw_numbers_{position}",
    )

    bonus = st.selectbox(
        f"Допълнително число — теглене {position}",
        options=bonus_options(),
        format_func=bonus_label,
        key=f"add_draw_bonus_{position}",
    )

    return normalize_numbers(numbers), bonus


def render() -> None:
    st.title("Добавяне на тираж")
    st.caption("Записва един тираж с едно или две тегления. Всяко теглене има 6 основни числа и отделно допълнително число.")

    auto_update = st.checkbox(
        "Автоматично обнови моделите след запис",
        value=True,
        key="add_draw_auto_update_models",
    )

    auto_github = st.checkbox(
        "Синхронизирай новите данни и модели в GitHub",
        value=True,
        key="add_draw_sync_github",
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
        value=True,
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

    if st.button("Запази тиража", use_container_width=True, key="add_draw_save_btn"):
        payloads: list[tuple[int, list[int], int | None]] = [(1, draw1_numbers, draw1_bonus)]
        errors = validate_draw(draw1_numbers, draw1_bonus, "Теглене 1")

        if include_second:
            payloads.append((2, draw2_numbers, draw2_bonus))
            errors.extend(validate_draw(draw2_numbers, draw2_bonus, "Теглене 2"))

        if errors:
            for error in errors:
                st.error(error)
            return

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
            with st.spinner("Обновяване на моделите..."):
                model_results = refresh_models()

            for script_name, ok, output in model_results:
                if ok:
                    st.success(f"{script_name}: OK")
                else:
                    st.warning(f"{script_name}: проблем или липсващ файл")
                if output:
                    with st.expander(f"Изход: {script_name}"):
                        st.code(output)

        if auto_github:
            with st.spinner("Синхронизация към GitHub..."):
                ok, output = sync_to_github(year=year, draw_no=draw_no)

            if ok:
                st.success("Данните, моделите и отчетите са синхронизирани към GitHub.")
            else:
                st.error("GitHub синхронизацията не успя.")
            if output:
                with st.expander("GitHub изход"):
                    st.code(output)

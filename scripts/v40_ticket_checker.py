from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

NUMBER_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]

REQUIRED_TICKET_COLS = ["ticket_table_no", *NUMBER_COLS]
REQUIRED_DRAW_COLS = ["draw_number", "date", "drawing_no", *NUMBER_COLS, "bonus_number"]


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def resolve_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def to_int_or_blank(value: Any) -> int | None:
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        return int(float(text))
    except ValueError:
        return None


def read_csv_checked(path: Path, required_cols: list[str], label: str) -> pd.DataFrame:
    if not path.exists():
        fail(f"Missing {label} file: {path}")

    df = pd.read_csv(path)

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        fail(f"{label} file is missing required columns: {missing}")

    return df


def validate_six(row: pd.Series, label: str) -> list[int]:
    numbers = []

    for col in NUMBER_COLS:
        value = to_int_or_blank(row[col])
        if value is None:
            fail(f"{label} has blank/non-numeric value in {col}.")

        if value < 1 or value > 49:
            fail(f"{label} has number outside 1..49 in {col}: {value}")

        numbers.append(value)

    if len(set(numbers)) != 6:
        fail(f"{label} has repeated numbers inside one 6-number combination: {numbers}")

    return sorted(numbers)


def prize_group_bg(match_count: int) -> str:
    if match_count == 6:
        return "I група / 6 познати числа"
    if match_count == 5:
        return "II група / 5 познати числа"
    if match_count == 4:
        return "III група / 4 познати числа"
    if match_count == 3:
        return "IV група / 3 познати числа"
    return "няма печеливша група по основните 6 числа"


def yes_no_bg(value: bool) -> str:
    return "да" if value else "не"


def numbers_to_text(numbers: list[int]) -> str:
    return " ".join(str(x) for x in numbers)


def display_or_dash(value: Any) -> str:
    text = str(value).strip()
    return text if text else "—"


def check_ticket_against_draws(tickets: pd.DataFrame, draws: pd.DataFrame) -> pd.DataFrame:
    results: list[dict[str, Any]] = []

    for _, ticket_row in tickets.iterrows():
        table_no = int(to_int_or_blank(ticket_row["ticket_table_no"]) or 0)
        ticket_label = f"таблица от фиш {table_no}"
        chosen_numbers = validate_six(ticket_row, ticket_label)
        chosen_set = set(chosen_numbers)

        ticket_id = str(ticket_row.get("ticket_id", "sample_ticket")).strip() or "sample_ticket"

        for _, draw_row in draws.iterrows():
            draw_number = int(to_int_or_blank(draw_row["draw_number"]) or 0)
            drawing_no = int(to_int_or_blank(draw_row["drawing_no"]) or 0)
            draw_label = f"тираж {draw_number}, теглене {drawing_no}"

            drawn_numbers = validate_six(draw_row, draw_label)
            drawn_set = set(drawn_numbers)

            bonus_number = to_int_or_blank(draw_row.get("bonus_number", None))
            if bonus_number is not None and (bonus_number < 1 or bonus_number > 49):
                fail(f"{draw_label} has bonus_number outside 1..49: {bonus_number}")

            matched = sorted(chosen_set.intersection(drawn_set))
            match_count = len(matched)

            bonus_match = bool(
                bonus_number is not None and bonus_number in chosen_set
            )

            results.append(
                {
                    "ticket_id": ticket_id,
                    "ticket_table_no": table_no,
                    "chosen_numbers": numbers_to_text(chosen_numbers),
                    "draw_number": draw_number,
                    "date": str(draw_row["date"]),
                    "drawing_no": drawing_no,
                    "drawn_numbers": numbers_to_text(drawn_numbers),
                    "bonus_number": "" if bonus_number is None else bonus_number,
                    "matched_numbers": numbers_to_text(matched),
                    "match_count": match_count,
                    "bonus_match": bonus_match,
                    "bonus_match_bg": yes_no_bg(bonus_match),
                    "result_label_bg": prize_group_bg(match_count),
                }
            )

    return pd.DataFrame(results)


def render_markdown(results: pd.DataFrame, tickets_path: Path, draws_path: Path) -> str:
    lines = []

    lines.append("# v40.1.1 Проверка на фиш — примерен отчет")
    lines.append("")
    lines.append(f"Файл с таблици от фиш: `{tickets_path.relative_to(ROOT)}`")
    lines.append(f"Файл с резултати от тегления: `{draws_path.relative_to(ROOT)}`")
    lines.append("")
    lines.append(
        "Този отчет проверява всяка таблица от фиша срещу всяко отделно теглене в избрания тираж."
    )
    lines.append("")
    lines.append("## Резултати")
    lines.append("")
    lines.append("| Таблица | Тираж | Теглене | Избрани числа | Изтеглени числа | Допълнително число | Познати числа | Брой познати | Познато допълнително число | Резултат |")
    lines.append("|---:|---:|---:|---|---|---:|---|---:|---|---|")

    for _, row in results.iterrows():
        lines.append(
            "| "
            f"{row['ticket_table_no']} | "
            f"{row['draw_number']} | "
            f"{row['drawing_no']} | "
            f"{display_or_dash(row['chosen_numbers'])} | "
            f"{display_or_dash(row['drawn_numbers'])} | "
            f"{display_or_dash(row['bonus_number'])} | "
            f"{display_or_dash(row['matched_numbers'])} | "
            f"{row['match_count']} | "
            f"{row['bonus_match_bg']} | "
            f"{row['result_label_bg']} |"
        )

    lines.append("")
    lines.append("## Обяснение")
    lines.append("- Един реален фиш може да има няколко таблици, като всяка таблица съдържа свои 6 избрани числа.")
    lines.append("- Един тираж може да има повече от едно теглене, затова всяка таблица трябва да се провери срещу всяко теглене поотделно.")
    lines.append("- Допълнителното число се следи отделно и не се смесва с броя познати по основните 6 числа.")
    lines.append("- Този примерен отчет служи само за проверка на логиката; примерните данни не са официален тираж.")
    lines.append("")
    lines.append("## Логика на проверката")
    lines.append("```text")
    lines.append("брой проверки = брой таблици във фиша × брой тегления в тиража")
    lines.append("```")
    lines.append("")
    lines.append(f"В този пример: **{results['ticket_table_no'].nunique()} таблици × {results['drawing_no'].nunique()} тегления = {len(results)} проверки**.")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Проверява няколко таблици от фиш срещу едно или повече тегления от 6/49."
    )
    parser.add_argument(
        "--tickets",
        default="data/v40_sample_ticket_tables.csv",
        help="CSV с ticket_table_no,n1,n2,n3,n4,n5,n6",
    )
    parser.add_argument(
        "--draws",
        default="data/v40_sample_draw_event_result.csv",
        help="CSV с draw_number,date,drawing_no,n1,n2,n3,n4,n5,n6,bonus_number",
    )
    parser.add_argument(
        "--out-prefix",
        default="reports/v40_ticket_checker_sample",
        help="Output prefix без разширение.",
    )

    args = parser.parse_args()

    tickets_path = resolve_path(args.tickets)
    draws_path = resolve_path(args.draws)
    out_prefix = resolve_path(args.out_prefix)

    tickets = read_csv_checked(tickets_path, REQUIRED_TICKET_COLS, "tickets")
    draws = read_csv_checked(draws_path, REQUIRED_DRAW_COLS, "draw events")

    results = check_ticket_against_draws(tickets, draws)

    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    csv_path = out_prefix.with_suffix(".csv")
    json_path = out_prefix.with_suffix(".json")
    md_path = out_prefix.with_suffix(".md")

    results.to_csv(csv_path, index=False, encoding="utf-8")

    json_payload = {
        "status": "PASS",
        "version": "v40.1.1_ticket_checker_bulgarian_polish",
        "tickets_file": str(tickets_path.relative_to(ROOT)),
        "draws_file": str(draws_path.relative_to(ROOT)),
        "ticket_tables": int(tickets["ticket_table_no"].nunique()),
        "draw_events": int(len(draws)),
        "result_rows": int(len(results)),
        "max_match_count": int(results["match_count"].max()) if not results.empty else 0,
        "logic_bg": "Всяка таблица от фиша се проверява срещу всяко отделно теглене.",
        "results": results.to_dict(orient="records"),
    }

    json_path.write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md_path.write_text(
        render_markdown(results, tickets_path, draws_path),
        encoding="utf-8",
    )

    print("DONE: v40.1.1 ticket checker Bulgarian polish executed.")
    print(f"TICKET_TABLES: {len(tickets)}")
    print(f"DRAW_EVENTS: {len(draws)}")
    print(f"RESULT_ROWS: {len(results)}")
    print(f"MAX_MATCH_COUNT: {json_payload['max_match_count']}")
    print(f"REPORT_CSV: {csv_path}")
    print(f"REPORT_JSON: {json_path}")
    print(f"REPORT_MD: {md_path}")


if __name__ == "__main__":
    main()

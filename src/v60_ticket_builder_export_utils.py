from __future__ import annotations

import json
from typing import Any

import pandas as pd


def result_to_copy_text(result: dict[str, Any]) -> str:
    tickets = result.get("selected_tickets", [])

    return "\n".join(
        ", ".join(str(number) for number in ticket)
        for ticket in tickets
    )


def result_to_dataframe(result: dict[str, Any]) -> pd.DataFrame:
    rows = []

    for index, row in enumerate(result.get("selected_rows", []), start=1):
        rows.append(
            {
                "ticket_index": index,
                "combination": row.get("combination_text", ""),
                "final_score": row.get("final_score", 0.0),
                "band": row.get("band", ""),
                "pattern_score": row.get("pattern_score", 0.0),
                "coverage_score": row.get("coverage_score", 0.0),
                "number_profile_score": row.get("number_profile_score", 0.0),
                "hot_cold_balance_score": row.get("hot_cold_balance_score", 0.0),
                "similarity_context_score": row.get("similarity_context_score", 0.0),
            }
        )

    return pd.DataFrame(rows)


def result_to_export_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "module": "Smart Ticket Builder 2",
        "step": "60_polish_export",
        "strategy": result.get("strategy"),
        "seed": result.get("seed"),
        "total_draws": result.get("total_draws"),
        "selected_count": result.get("selected_count"),
        "average_final_score": result.get("average_final_score"),
        "best_score": result.get("best_score"),
        "weakest_score": result.get("weakest_score"),
        "coverage_score": result.get("coverage_score"),
        "selected_tickets": result.get("selected_tickets", []),
        "selected_rows": result.get("selected_rows", []),
        "warnings": result.get("warnings", []),
        "recommendations": result.get("recommendations", []),
        "safety_note_bg": result.get("safety_note_bg"),
    }


def result_to_json_text(result: dict[str, Any]) -> str:
    return json.dumps(result_to_export_payload(result), ensure_ascii=False, indent=2)


def result_to_csv_bytes(result: dict[str, Any]) -> bytes:
    df = result_to_dataframe(result)
    return df.to_csv(index=False).encode("utf-8-sig")


def result_to_json_bytes(result: dict[str, Any]) -> bytes:
    return result_to_json_text(result).encode("utf-8")


def result_to_txt_bytes(result: dict[str, Any]) -> bytes:
    lines = [
        "Smart Ticket Builder 2",
        "Статистически помощник, не предсказание и не гаранция за печалба.",
        "",
        f"Стратегия: {result.get('strategy')}",
        f"Seed: {result.get('seed')}",
        f"Анализирани тиражи: {result.get('total_draws')}",
        f"Избрани комбинации: {result.get('selected_count')}",
        f"Средна оценка: {result.get('average_final_score')}",
        f"Покритие: {result.get('coverage_score')}",
        "",
        "Предложен фиш:",
        result_to_copy_text(result),
        "",
        "Предупреждения:",
    ]

    for warning in result.get("warnings", []):
        lines.append(f"- {warning}")

    lines.append("")
    lines.append("Препоръки:")

    for recommendation in result.get("recommendations", []):
        lines.append(f"- {recommendation}")

    lines.append("")
    lines.append(str(result.get("safety_note_bg", "")))

    return ("\n".join(lines) + "\n").encode("utf-8")

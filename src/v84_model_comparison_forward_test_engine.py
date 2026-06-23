from __future__ import annotations

from pathlib import Path
import csv
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
V84_MODEL_DIR = MODELS_DIR / "v84"

SNAPSHOT_CSV = DATA_DIR / "v84_model_forward_test_snapshots.csv"
CANDIDATES_CSV = REPORTS_DIR / "v84_model_source_candidates.csv"
RESULTS_CSV = REPORTS_DIR / "v84_model_comparison_results.csv"
SUMMARY_JSON = REPORTS_DIR / "v84_model_comparison_summary.json"
SUMMARY_MD = REPORTS_DIR / "v84_model_comparison_summary.md"
MODEL_JSON = V84_MODEL_DIR / "v84_model_comparison_forward_test_model.json"

SAFE_NOTE = (
    "Step 84 сравнява модели по заключени преди тиража комбинации. "
    "Това е реална проверка във времето. "
    "Не е прогноза и не е гаранция за печалба."
)

MODEL_SOURCE_CONFIG = [
    {
        "model_key": "ml_laboratory",
        "model_label": "МЛ лаборатория",
        "tokens": ["v39", "machine_learning", "ml_"],
        "priority": 10,
    },
    {
        "model_key": "neural_meta",
        "model_label": "Невронна лаборатория",
        "tokens": ["v75", "neural"],
        "priority": 20,
    },
    {
        "model_key": "weighted_ensemble",
        "model_label": "Претеглен комбиниран анализ",
        "tokens": ["v66", "v67", "weighted"],
        "priority": 30,
    },
    {
        "model_key": "portfolio_optimizer",
        "model_label": "Умен оптимизатор на пакет",
        "tokens": ["v68", "portfolio"],
        "priority": 40,
    },
    {
        "model_key": "final_play_plan",
        "model_label": "Финален план",
        "tokens": ["v78", "final_play_plan"],
        "priority": 50,
    },
    {
        "model_key": "ticket_pack",
        "model_label": "Пакет за игра",
        "tokens": ["v79", "ticket_pack"],
        "priority": 60,
    },
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _numbers_to_text(numbers: list[int]) -> str:
    return ",".join(str(number) for number in sorted(numbers))


def _numbers_from_text(value: str) -> list[int]:
    numbers: list[int] = []
    for part in re_split_numbers(value):
        if not part:
            continue
        try:
            number = int(part)
        except ValueError:
            continue
        if 1 <= number <= 49:
            numbers.append(number)
    unique = sorted(set(numbers))
    return unique[:6] if len(unique) >= 6 else unique


def re_split_numbers(value: str) -> list[str]:
    current = ""
    parts: list[str] = []
    for ch in str(value):
        if ch.isdigit():
            current += ch
        else:
            if current:
                parts.append(current)
                current = ""
    if current:
        parts.append(current)
    return parts


def _valid_ticket(numbers: list[int]) -> bool:
    return len(numbers) == 6 and len(set(numbers)) == 6 and all(1 <= number <= 49 for number in numbers)


def _collect_json_tickets(data: Any, source_path: str, max_items: int = 50) -> list[list[int]]:
    tickets: list[list[int]] = []

    def walk(value: Any) -> None:
        if len(tickets) >= max_items:
            return

        if isinstance(value, list):
            if value and all(isinstance(item, int) for item in value):
                candidate = sorted(set(int(item) for item in value))
                if _valid_ticket(candidate):
                    tickets.append(candidate)
                    return

            for item in value:
                walk(item)

        elif isinstance(value, dict):
            preferred_keys = [
                "numbers",
                "ticket",
                "combination",
                "numbers_sorted",
                "main_numbers",
                "selected_numbers",
                "active_ticket",
                "recommended_numbers",
            ]

            for key in preferred_keys:
                if key in value:
                    raw = value.get(key)
                    if isinstance(raw, list):
                        candidate = sorted(set(int(item) for item in raw if isinstance(item, int)))
                        if _valid_ticket(candidate):
                            tickets.append(candidate)
                    elif isinstance(raw, str):
                        candidate = _numbers_from_text(raw)
                        if _valid_ticket(candidate):
                            tickets.append(candidate)

            n_keys = [f"n{i}" for i in range(1, 7)]
            if all(key in value for key in n_keys):
                candidate = []
                for key in n_keys:
                    try:
                        candidate.append(int(value[key]))
                    except Exception:
                        candidate = []
                        break
                candidate = sorted(set(candidate))
                if _valid_ticket(candidate):
                    tickets.append(candidate)

            for item in value.values():
                walk(item)

    walk(data)

    unique: list[list[int]] = []
    seen: set[str] = set()
    for ticket in tickets:
        key = _numbers_to_text(ticket)
        if key not in seen:
            seen.add(key)
            unique.append(ticket)

    return unique[:max_items]


def _collect_csv_tickets(path: Path, max_items: int = 50) -> list[list[int]]:
    rows = _read_csv(path)
    tickets: list[list[int]] = []

    for row in rows:
        if len(tickets) >= max_items:
            break

        n_keys = [f"n{i}" for i in range(1, 7)]
        if all(key in row for key in n_keys):
            candidate = []
            for key in n_keys:
                try:
                    candidate.append(int(str(row[key]).strip()))
                except Exception:
                    candidate = []
                    break
            candidate = sorted(set(candidate))
            if _valid_ticket(candidate):
                tickets.append(candidate)
                continue

        for key in ["numbers", "ticket", "combination", "numbers_sorted", "main_numbers", "selected_numbers"]:
            if key in row:
                candidate = _numbers_from_text(str(row.get(key, "")))
                if _valid_ticket(candidate):
                    tickets.append(candidate)
                    break

    unique: list[list[int]] = []
    seen: set[str] = set()
    for ticket in tickets:
        key = _numbers_to_text(ticket)
        if key not in seen:
            seen.add(key)
            unique.append(ticket)

    return unique[:max_items]


def _path_matches_tokens(path: Path, tokens: list[str]) -> bool:
    text = path.as_posix().lower()
    return any(token.lower() in text for token in tokens)


def discover_current_model_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    searchable_files: list[Path] = []
    for root in [MODELS_DIR, REPORTS_DIR]:
        if root.exists():
            searchable_files.extend(sorted(root.rglob("*.json")))
            searchable_files.extend(sorted(root.rglob("*.csv")))

    for config in MODEL_SOURCE_CONFIG:
        model_key = str(config["model_key"])
        model_label = str(config["model_label"])
        tokens = list(config["tokens"])
        priority = int(config["priority"])

        model_tickets: list[dict[str, Any]] = []

        for path in searchable_files:
            if not _path_matches_tokens(path, tokens):
                continue

            rel = path.relative_to(ROOT).as_posix()
            tickets: list[list[int]] = []

            if path.suffix.lower() == ".json":
                try:
                    data = json.loads(path.read_text(encoding="utf-8-sig"))
                    tickets = _collect_json_tickets(data, rel, max_items=8)
                except Exception:
                    tickets = []

            elif path.suffix.lower() == ".csv":
                try:
                    tickets = _collect_csv_tickets(path, max_items=8)
                except Exception:
                    tickets = []

            for ticket in tickets:
                model_tickets.append({
                    "model_key": model_key,
                    "model_label": model_label,
                    "ticket_label": f"{model_label} комбинация #{len(model_tickets) + 1}",
                    "numbers": _numbers_to_text(ticket),
                    "source_file": rel,
                    "source_priority": priority,
                    "safe_note": SAFE_NOTE,
                })

            if len(model_tickets) >= 8:
                break

        candidates.extend(model_tickets[:8])

    return candidates


def _latest_draw() -> dict[str, Any]:
    path = DATA_DIR / "historical_draws.csv"
    rows = _read_csv(path)
    if not rows:
        return {"draw_index": 0, "draw_date": "-", "numbers": [], "draw_id": "-"}

    latest = rows[-1]
    numbers: list[int] = []
    for key in [f"n{i}" for i in range(1, 7)]:
        try:
            numbers.append(int(str(latest.get(key, "")).strip()))
        except ValueError:
            pass

    draw_date = latest.get("date") or latest.get("draw_date") or latest.get("Дата") or "-"
    draw_id = latest.get("drawing_no") or latest.get("draw_no") or latest.get("draw_id") or str(len(rows))

    return {
        "draw_index": len(rows),
        "draw_date": draw_date,
        "draw_id": draw_id,
        "numbers": sorted(numbers),
    }


def build_model_comparison_forward_test_center() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    V84_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    candidates = discover_current_model_candidates()
    snapshots = _read_csv(SNAPSHOT_CSV)
    latest = _latest_draw()

    results = evaluate_snapshot_rows(snapshots, latest)
    summary_rows = summarize_results(results)

    _write_csv(
        CANDIDATES_CSV,
        candidates,
        ["model_key", "model_label", "ticket_label", "numbers", "source_file", "source_priority", "safe_note"],
    )

    _write_csv(
        RESULTS_CSV,
        results,
        [
            "snapshot_id",
            "snapshot_created_at",
            "model_key",
            "model_label",
            "ticket_label",
            "numbers",
            "target_draw_index",
            "target_draw_date",
            "target_numbers",
            "hits_count",
            "hit_numbers",
            "result_bucket",
            "source_file",
            "safe_note",
        ],
    )

    summary = {
        "step": "84",
        "title": "Сравнение на модели / реална проверка във времето",
        "status": "OK",
        "generated_at": _now_iso(),
        "safe_note": SAFE_NOTE,
        "current_candidates": len(candidates),
        "snapshots_recorded": len({row.get("snapshot_id", "") for row in snapshots if row.get("snapshot_id", "")}),
        "snapshot_rows_recorded": len(snapshots),
        "locked_snapshot_records": len({row.get("snapshot_id", "") for row in snapshots if row.get("snapshot_id", "")}),
        "evaluated_rows": len(results),
        "models_compared": len(summary_rows),
        "latest_draw_index": latest["draw_index"],
        "latest_draw_date": latest["draw_date"],
        "latest_numbers": _numbers_to_text(latest["numbers"]) if latest["numbers"] else "-",
        "summary_rows": summary_rows,
        "outputs": [
            "models/v84/v84_model_comparison_forward_test_model.json",
            "reports/v84_model_comparison_summary.json",
            "reports/v84_model_comparison_summary.md",
            "reports/v84_model_source_candidates.csv",
            "reports/v84_model_comparison_results.csv",
            "data/v84_model_forward_test_snapshots.csv",
        ],
    }

    model = {
        "summary": summary,
        "current_candidates": candidates,
        "results": results,
        "model_summary": summary_rows,
    }

    _write_json(SUMMARY_JSON, summary)
    _write_json(MODEL_JSON, model)
    _write_summary_md(summary, summary_rows)

    return summary


def _write_summary_md(summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Step 84 — Сравнение на модели",
        "",
        f"Статус: **{summary.get('status')}**",
        "",
        SAFE_NOTE,
        "",
        "## Последен тираж",
        "",
        f"- Индекс: **{summary.get('latest_draw_index')}**",
        f"- Дата: **{summary.get('latest_draw_date')}**",
        f"- Числа: **{summary.get('latest_numbers')}**",
        "",
        "## Обобщение по модели",
        "",
        "| Модел | Проверени комбинации | Средно познати | Най-добър резултат | % с 2+ | % с 3+ | % с 4+ |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    if rows:
        for row in rows:
            lines.append(
                f"| {row['model_label']} | {row['tickets_evaluated']} | "
                f"{row['average_hits']} | {row['max_hits']} | "
                f"{row['pct_at_least_2']} | {row['pct_at_least_3']} | {row['pct_at_least_4']} |"
            )
    else:
        lines.append("| Няма записани заключени записи | 0 | 0 | 0 | 0 | 0 | 0 |")

    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def create_snapshot_from_current_candidates(snapshot_name: str = "") -> dict[str, Any]:
    candidates = discover_current_model_candidates()
    existing = _read_csv(SNAPSHOT_CSV)

    snapshot_id = f"v84-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
    created_at = _now_iso()
    latest = _latest_draw()

    new_rows: list[dict[str, Any]] = []

    for candidate in candidates:
        row = {
            "snapshot_id": snapshot_id,
            "snapshot_name": snapshot_name or "Текущ заключен запис преди тираж",
            "snapshot_created_at": created_at,
            "dataset_draw_index_at_snapshot": latest["draw_index"],
            "dataset_latest_draw_date_at_snapshot": latest["draw_date"],
            "model_key": candidate["model_key"],
            "model_label": candidate["model_label"],
            "ticket_label": candidate["ticket_label"],
            "numbers": candidate["numbers"],
            "source_file": candidate["source_file"],
            "status": "чака реален тираж",
            "safe_note": SAFE_NOTE,
        }
        new_rows.append(row)

    all_rows = [*existing, *new_rows]

    _write_csv(
        SNAPSHOT_CSV,
        all_rows,
        [
            "snapshot_id",
            "snapshot_name",
            "snapshot_created_at",
            "dataset_draw_index_at_snapshot",
            "dataset_latest_draw_date_at_snapshot",
            "model_key",
            "model_label",
            "ticket_label",
            "numbers",
            "source_file",
            "status",
            "safe_note",
        ],
    )

    build_model_comparison_forward_test_center()

    return {
        "snapshot_id": snapshot_id,
        "rows_added": len(new_rows),
        "candidates_found": len(candidates),
        "safe_note": SAFE_NOTE,
    }


def add_manual_snapshot_row(model_label: str, numbers_text: str, snapshot_name: str = "") -> dict[str, Any]:
    numbers = _numbers_from_text(numbers_text)
    if not _valid_ticket(numbers):
        return {
            "status": "error",
            "message": "Трябва да въведеш точно 6 различни числа между 1 и 49.",
        }

    existing = _read_csv(SNAPSHOT_CSV)
    snapshot_id = f"manual-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
    created_at = _now_iso()
    latest = _latest_draw()

    row = {
        "snapshot_id": snapshot_id,
        "snapshot_name": snapshot_name or "Ръчен заключен запис преди тираж",
        "snapshot_created_at": created_at,
        "dataset_draw_index_at_snapshot": latest["draw_index"],
        "dataset_latest_draw_date_at_snapshot": latest["draw_date"],
        "model_key": "manual",
        "model_label": model_label.strip() or "Ръчно въведен модел",
        "ticket_label": model_label.strip() or "Ръчно въведена комбинация",
        "numbers": _numbers_to_text(numbers),
        "source_file": "manual_ui_entry",
        "status": "чака реален тираж",
        "safe_note": SAFE_NOTE,
    }

    _write_csv(
        SNAPSHOT_CSV,
        [*existing, row],
        [
            "snapshot_id",
            "snapshot_name",
            "snapshot_created_at",
            "dataset_draw_index_at_snapshot",
            "dataset_latest_draw_date_at_snapshot",
            "model_key",
            "model_label",
            "ticket_label",
            "numbers",
            "source_file",
            "status",
            "safe_note",
        ],
    )

    build_model_comparison_forward_test_center()

    return {
        "status": "OK",
        "snapshot_id": snapshot_id,
        "numbers": row["numbers"],
    }


def evaluate_snapshot_rows(snapshots: list[dict[str, str]], latest: dict[str, Any]) -> list[dict[str, Any]]:
    target_numbers = sorted(int(number) for number in latest.get("numbers", []) if isinstance(number, int))
    if not _valid_ticket(target_numbers):
        return []

    results: list[dict[str, Any]] = []

    for row in snapshots:
        numbers = _numbers_from_text(str(row.get("numbers", "")))
        if not _valid_ticket(numbers):
            continue

        snapshot_index_raw = str(row.get("dataset_draw_index_at_snapshot", "0")).strip()
        try:
            snapshot_index = int(snapshot_index_raw)
        except ValueError:
            snapshot_index = 0

        # Only evaluate snapshots created before a newer draw exists.
        if int(latest["draw_index"]) <= snapshot_index:
            continue

        hits = sorted(set(numbers).intersection(target_numbers))
        hits_count = len(hits)

        if hits_count >= 4:
            bucket = "4+ познати"
        elif hits_count == 3:
            bucket = "3 познати"
        elif hits_count == 2:
            bucket = "2 познати"
        elif hits_count == 1:
            bucket = "1 познато"
        else:
            bucket = "0 познати"

        results.append({
            "snapshot_id": row.get("snapshot_id", ""),
            "snapshot_created_at": row.get("snapshot_created_at", ""),
            "model_key": row.get("model_key", ""),
            "model_label": row.get("model_label", ""),
            "ticket_label": row.get("ticket_label", ""),
            "numbers": _numbers_to_text(numbers),
            "target_draw_index": latest["draw_index"],
            "target_draw_date": latest["draw_date"],
            "target_numbers": _numbers_to_text(target_numbers),
            "hits_count": hits_count,
            "hit_numbers": _numbers_to_text(hits) if hits else "-",
            "result_bucket": bucket,
            "source_file": row.get("source_file", ""),
            "safe_note": SAFE_NOTE,
        })

    return results


def summarize_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}

    for row in results:
        key = str(row.get("model_label", "Неизвестен модел"))
        grouped.setdefault(key, []).append(row)

    summary: list[dict[str, Any]] = []

    for model_label, rows in sorted(grouped.items()):
        hits = [int(row.get("hits_count", 0)) for row in rows]
        total = len(hits)

        if total == 0:
            continue

        avg = sum(hits) / total
        at_least_2 = sum(1 for value in hits if value >= 2)
        at_least_3 = sum(1 for value in hits if value >= 3)
        at_least_4 = sum(1 for value in hits if value >= 4)

        summary.append({
            "model_label": model_label,
            "tickets_evaluated": total,
            "average_hits": round(avg, 3),
            "max_hits": max(hits),
            "pct_at_least_2": round((at_least_2 / total) * 100, 2),
            "pct_at_least_3": round((at_least_3 / total) * 100, 2),
            "pct_at_least_4": round((at_least_4 / total) * 100, 2),
        })

    summary.sort(
        key=lambda row: (
            float(row["average_hits"]),
            float(row["pct_at_least_3"]),
            float(row["pct_at_least_2"]),
            int(row["max_hits"]),
        ),
        reverse=True,
    )

    return summary


if __name__ == "__main__":
    result = build_model_comparison_forward_test_center()
    print("STEP84_STATUS", result.get("status"))
    print("CANDIDATES", result.get("current_candidates"))
    print("LOCKED_RECORDS", result.get("locked_snapshot_records"))
    print("SNAPSHOT_ROWS", result.get("snapshot_rows_recorded"))
    print("EVALUATED_ROWS", result.get("evaluated_rows"))

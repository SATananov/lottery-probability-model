from __future__ import annotations

from pathlib import Path
import csv
import html
import io

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_CSV = ROOT / "data" / "v84_model_forward_test_snapshots.csv"

SAFE_NOTE = (
    "Това са визуални фишове, заредени от заключения запис преди тиража. "
    "Заключеният запис пази какво са дали моделите преди реалния тираж. "
    "Това е статистическа проверка, не гаранция за печалба."
)


def _load_rows() -> list[dict[str, str]]:
    if not SNAPSHOT_CSV.exists():
        return []

    with SNAPSHOT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _numbers_from_text(value: str) -> list[int]:
    parts: list[str] = []
    current = ""

    for ch in str(value):
        if ch.isdigit():
            current += ch
        else:
            if current:
                parts.append(current)
                current = ""

    if current:
        parts.append(current)

    numbers: list[int] = []
    for part in parts:
        try:
            number = int(part)
        except ValueError:
            continue

        if 1 <= number <= 49:
            numbers.append(number)

    return sorted(set(numbers))


def _valid_ticket(numbers: list[int]) -> bool:
    return len(numbers) == 6 and len(set(numbers)) == 6 and all(1 <= n <= 49 for n in numbers)


def _locked_record_label(snapshot_id: str, rows: list[dict[str, str]]) -> str:
    matching = [row for row in rows if row.get("snapshot_id") == snapshot_id]
    if not matching:
        return snapshot_id

    created = matching[0].get("snapshot_created_at", "-")
    draw_index = matching[0].get("dataset_draw_index_at_snapshot", "-")
    return f"{created} · тиражи в данните: {draw_index} · {len(matching)} комбинации"


def _field_grid_html(numbers: list[int], field_title: str) -> str:
    selected = set(numbers)
    cells: list[str] = []

    for number in range(1, 50):
        cls = "v841-cell v841-selected" if number in selected else "v841-cell"
        cells.append(f'<div class="{cls}">{number}</div>')

    safe_title = html.escape(field_title)
    safe_numbers = ", ".join(str(n) for n in numbers) if numbers else "празно"

    return f"""
<div class="v841-field">
  <div class="v841-field-title">{safe_title}</div>
  <div class="v841-field-numbers">Числа: <strong>{safe_numbers}</strong></div>
  <div class="v841-grid">{''.join(cells)}</div>
</div>
"""


def _physical_slip_html(slip_index: int, rows: list[dict[str, str]]) -> str:
    fields: list[str] = []

    for offset, row in enumerate(rows, start=1):
        numbers = _numbers_from_text(row.get("numbers", ""))
        if not _valid_ticket(numbers):
            continue

        ticket_label = row.get("ticket_label") or f"Комбинация {offset}"
        fields.append(_field_grid_html(numbers, f"Поле {offset} · {ticket_label}"))

    while len(fields) < 4:
        fields.append(_field_grid_html([], f"Поле {len(fields) + 1} · празно"))

    model_labels = sorted({row.get("model_label", "-") for row in rows if row.get("model_label")})
    basis_label = ", ".join(model_labels) if model_labels else "заключен запис"
    safe_basis = html.escape(f"{basis_label} · заключен запис преди тиража")

    return f"""
<div class="v841-slip">
  <div class="v841-slip-title">Фиш за игра #{slip_index}</div>
  <div class="v841-slip-sub">Един фиш съдържа 4 полета. Всяко поле е отделна комбинация от 6 числа.</div>
  <div class="v841-fields">
    {''.join(fields)}
  </div>
  <div class="v841-source">Основа: {safe_basis}</div>
</div>
"""


def _css() -> str:
    return """
<style>
.v841-help {
  opacity: 0.86;
  font-size: 0.95rem;
  line-height: 1.45;
  margin-bottom: 0.8rem;
}
.v841-slip {
  border: 1px solid rgba(212, 175, 55, 0.32);
  border-radius: 18px;
  padding: 0.9rem;
  margin: 0.9rem 0 1.25rem 0;
  background: linear-gradient(180deg, rgba(212,175,55,0.07), rgba(255,255,255,0.015));
}
.v841-slip-title {
  font-size: 1.1rem;
  font-weight: 850;
  color: #f3d371;
  margin-bottom: 0.2rem;
}
.v841-slip-sub {
  opacity: 0.78;
  font-size: 0.88rem;
  margin-bottom: 0.75rem;
}
.v841-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(280px, 1fr));
  gap: 0.75rem;
}
.v841-field {
  border: 1px solid rgba(212, 175, 55, 0.24);
  border-radius: 14px;
  padding: 0.65rem;
  background: rgba(255,255,255,0.018);
}
.v841-field-title {
  font-size: 0.95rem;
  font-weight: 800;
  color: #f3d371;
  margin-bottom: 0.15rem;
}
.v841-field-numbers {
  opacity: 0.92;
  font-size: 0.84rem;
  margin-bottom: 0.5rem;
}
.v841-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(26px, 1fr));
  gap: 0.22rem;
}
.v841-cell {
  min-height: 25px;
  border: 1px solid rgba(212, 175, 55, 0.30);
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 700;
  background: rgba(255,255,255,0.025);
}
.v841-selected {
  border-color: rgba(255, 209, 102, 0.95);
  background: rgba(212, 175, 55, 0.32);
  color: #ffe08a;
  box-shadow: 0 0 0 1px rgba(212,175,55,0.32), 0 0 12px rgba(212,175,55,0.18);
}
.v841-source {
  margin-top: 0.65rem;
  font-size: 0.78rem;
  opacity: 0.56;
  word-break: break-word;
}
@media (max-width: 900px) {
  .v841-fields {
    grid-template-columns: 1fr;
  }
}
@media print {
  body {
    background: #ffffff !important;
    color: #000000 !important;
  }
  .v841-slip {
    break-inside: avoid;
    page-break-inside: avoid;
    border-color: #999999;
  }
}
</style>
"""


def _export_text(rows: list[dict[str, str]]) -> str:
    lines = [
        "Фишове от заключения запис преди тиража",
        "Важно: 1 реален фиш = 4 полета. Всяко поле е комбинация от 6 числа.",
        "Статистически тест, не гаранция за печалба.",
        "",
    ]

    slip_index = 1
    for start in range(0, len(rows), 4):
        chunk = rows[start:start + 4]
        lines.append(f"Фиш за игра #{slip_index}")

        for offset, row in enumerate(chunk, start=1):
            numbers = _numbers_from_text(row.get("numbers", ""))
            if not _valid_ticket(numbers):
                continue

            label = row.get("ticket_label") or f"Поле {offset}"
            lines.append(f"  Поле {offset} — {label}")
            lines.append("  Числа: " + ", ".join(str(n) for n in numbers))

        lines.append("")
        slip_index += 1

    return "\n".join(lines).strip() + "\n"


def _export_csv(rows: list[dict[str, str]]) -> str:
    output = io.StringIO()
    fieldnames = [
        "slip_number",
        "field_number",
        "model_label",
        "ticket_label",
        "numbers",
        "source_file",
        "snapshot_id",
        "snapshot_created_at",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()

    for index, row in enumerate(rows):
        slip_number = (index // 4) + 1
        field_number = (index % 4) + 1
        numbers = _numbers_from_text(row.get("numbers", ""))

        writer.writerow({
            "slip_number": slip_number,
            "field_number": field_number,
            "model_label": row.get("model_label", ""),
            "ticket_label": row.get("ticket_label", ""),
            "numbers": ", ".join(str(n) for n in numbers),
            "source_file": row.get("source_file", ""),
            "snapshot_id": row.get("snapshot_id", ""),
            "snapshot_created_at": row.get("snapshot_created_at", ""),
        })

    return output.getvalue()


def _export_html(rows: list[dict[str, str]], selected_model: str) -> str:
    slips_html: list[str] = []

    for slip_index, start in enumerate(range(0, len(rows), 4), start=1):
        chunk = rows[start:start + 4]
        slips_html.append(_physical_slip_html(slip_index, chunk))

    safe_model = html.escape(selected_model)

    return f"""<!doctype html>
<html lang="bg">
<head>
<meta charset="utf-8">
<title>Реални фишове от заключения запис</title>
{_css()}
<style>
body {{
  margin: 24px;
  background: #0e0e10;
  color: #f8f5ef;
  font-family: Arial, sans-serif;
}}
.print-note {{
  border: 1px solid rgba(212, 175, 55, 0.35);
  border-radius: 14px;
  padding: 12px 14px;
  margin-bottom: 18px;
  background: rgba(212,175,55,0.08);
}}
@media print {{
  body {{
    margin: 12mm;
    background: #ffffff !important;
    color: #000000 !important;
  }}
  .print-note {{
    border-color: #999999;
    background: #ffffff;
  }}
  .v841-cell,
  .v841-field,
  .v841-slip {{
    border-color: #777777 !important;
  }}
  .v841-selected {{
    color: #000000 !important;
    background: #dddddd !important;
    border: 2px solid #000000 !important;
    box-shadow: none !important;
  }}
  .v841-slip-title,
  .v841-field-title {{
    color: #000000 !important;
  }}
}}
</style>
</head>
<body>
  <h1>Реални фишове от заключения запис</h1>
  <div class="print-note">
    <strong>Модел:</strong> {safe_model}<br>
    1 реален фиш = 4 полета. Всяко поле е комбинация от 6 числа.<br>
    Това е статистически тест, не гаранция за печалба.
  </div>
  {''.join(slips_html)}
</body>
</html>
"""


def render_v84_1_final_plan_snapshot_slips() -> None:
    rows = _load_rows()

    st.markdown(_css(), unsafe_allow_html=True)

    with st.expander("Визуални фишове от заключения запис", expanded=True):
        st.markdown(
            '<div class="v841-help">'
            "Тук виждаш фишовете като реален игрови лист: "
            "<strong>1 фиш = 4 полета</strong>, а всяко поле съдържа 6 числа. "
            "По подразбиране избери „Финален план“, защото това са практическите фишове за игра."
            "</div>",
            unsafe_allow_html=True,
        )

        if not rows:
            st.info(
                "Няма заключен запис преди тиража. "
                "Първо отиди в „Сравнение на модели“ и натисни „Запази запис преди тираж“."
            )
            return

        snapshot_ids = sorted(
            {row.get("snapshot_id", "") for row in rows if row.get("snapshot_id")},
            key=lambda sid: max(
                [row.get("snapshot_created_at", "") for row in rows if row.get("snapshot_id") == sid] or [""]
            ),
            reverse=True,
        )

        if not snapshot_ids:
            st.info("Файлът със заключения запис е наличен, но няма валидни записи.")
            return

        selected_snapshot = st.selectbox(
            "Заключен запис",
            snapshot_ids,
            format_func=lambda sid: _locked_record_label(sid, rows),
            key="v84_1_final_snapshot_id",
        )

        snapshot_rows = [row for row in rows if row.get("snapshot_id") == selected_snapshot]
        model_labels = sorted({row.get("model_label", "-") for row in snapshot_rows})

        default_index = model_labels.index("Финален план") if "Финален план" in model_labels else 0

        selected_model = st.selectbox(
            "Модел",
            model_labels,
            index=default_index,
            key="v84_1_final_model_label",
        )

        model_rows = [
            row for row in snapshot_rows
            if row.get("model_label", "-") == selected_model
            and _valid_ticket(_numbers_from_text(row.get("numbers", "")))
        ]

        model_rows.sort(key=lambda row: (row.get("ticket_label", ""), row.get("numbers", "")))

        if not model_rows:
            st.warning("Няма валидни 6-числови комбинации за избрания модел.")
            return

        max_count = min(8, len(model_rows))
        count = st.selectbox(
            "Брой комбинации за показване",
            list(range(1, max_count + 1)),
            index=max_count - 1,
            key="v84_1_final_ticket_count",
        )

        selected_rows = model_rows[:count]
        physical_slips_count = (len(selected_rows) + 3) // 4

        st.info(
            f"{SAFE_NOTE} Показани са {len(selected_rows)} комбинации, "
            f"разпределени в {physical_slips_count} реални фиша."
        )

        txt_data = _export_text(selected_rows).encode("utf-8-sig")
        csv_data = _export_csv(selected_rows).encode("utf-8-sig")
        html_data = _export_html(selected_rows, selected_model).encode("utf-8")

        export_cols = st.columns(3)

        with export_cols[0]:
            st.download_button(
                "Свали TXT",
                data=txt_data,
                file_name="realni_fishove_ot_zakliuchen_zapis.txt",
                mime="text/plain",
                key="v84_1_final_download_txt",
            )

        with export_cols[1]:
            st.download_button(
                "Свали CSV",
                data=csv_data,
                file_name="realni_fishove_ot_zakliuchen_zapis.csv",
                mime="text/csv",
                key="v84_1_final_download_csv",
            )

        with export_cols[2]:
            st.download_button(
                "Свали HTML за печат",
                data=html_data,
                file_name="realni_fishove_ot_zakliuchen_zapis.html",
                mime="text/html",
                key="v84_1_final_download_html",
            )

        for slip_index, start in enumerate(range(0, len(selected_rows), 4), start=1):
            chunk = selected_rows[start:start + 4]
            st.markdown(_physical_slip_html(slip_index, chunk), unsafe_allow_html=True)

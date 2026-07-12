from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.v150_global_ui_polish import ui_text
from src.v150_ui_language_integrity_engine import (
    REPORT_CSV_PATH,
    STATUS_JSON_PATH,
    run_ui_language_integrity_audit,
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _load_csv(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _t(bg: str, en: str) -> str:
    return ui_text(bg, en, st)


def render_v150_ui_language_integrity_section() -> None:
    st.title(_t("Контрол на езика и интерфейса", "Language and Interface Control"))
    st.caption(
        _t(
            "Глобална проверка на менюта, страници, бутони, таблици, статуси, кирилица и технически подробности.",
            "Global validation of menus, pages, buttons, tables, statuses, Cyrillic text and technical details.",
        )
    )
    st.info(
        _t(
            "Потребителският режим показва разбираеми наименования. Вътрешните идентификатори, подписи и UTC полета се виждат само при включени „Технически подробности“.",
            "User mode shows readable labels. Internal identifiers, signatures and UTC fields are visible only when Technical details are enabled.",
        )
    )

    status = _load_json(STATUS_JSON_PATH)
    columns = st.columns(6)
    columns[0].metric(_t("Проверени UI редове", "UI rows checked"), int(status.get("ui_literal_rows", 0)))
    columns[1].metric(_t("Уникални текстове", "Unique texts"), int(status.get("unique_ui_literals", 0)))
    columns[2].metric(
        _t("Английски остатъци в BG режим", "English residues in BG mode"),
        int(status.get("forbidden_bulgarian_residual_rows", 0)),
    )
    columns[3].metric(_t("Смесен видим език", "Mixed visible language"), int(status.get("mixed_language_rows", 0)))
    columns[4].metric(_t("Проблеми с кирилицата", "Cyrillic issues"), int(status.get("mojibake_findings", 0)))
    columns[5].metric(
        _t("Защитеното заключване", "Protected forward lock"),
        _t("НЕПРОМЕНЕНО", "UNCHANGED") if (status.get("protected_step148_files") or {}).get("all_ok") else _t("ПРОБЛЕМ", "ISSUE"),
    )

    if status.get("ok"):
        st.success(_t("Глобалната проверка на интерфейса е успешна.", "The global interface validation passed."))
    else:
        st.error(_t("Има елементи за преглед в глобалната проверка на интерфейса.", "The global interface validation found items requiring review."))

    if st.button(_t("Обнови проверката на интерфейса", "Refresh interface validation"), type="primary", use_container_width=True):
        result = run_ui_language_integrity_audit(write_outputs=True)
        st.success(_t("Проверката е обновена.", "Validation refreshed.")) if result.get("ok") else st.warning(
            _t("Проверката е обновена, но има елементи за преглед.", "Validation refreshed, but some items require review.")
        )
        st.rerun()

    st.markdown(_t("### Покритие", "### Coverage"))
    coverage_rows = [
        {
            "area": _t("Меню и групи", "Menu and groups"),
            "status": bool(status.get("research_navigation_group_present")),
        },
        {
            "area": _t("Страници и модули", "Pages and modules"),
            "status": bool(status.get("research_page_labels_present")),
        },
        {
            "area": _t("Таблици и статуси", "Tables and statuses"),
            "status": bool(status.get("technical_table_columns_hidden_by_default")),
        },
        {
            "area": _t("Кирилица и UTF-8", "Cyrillic and UTF-8"),
            "status": int(status.get("mojibake_findings", 1)) == 0,
        },
        {
            "area": _t("Активна проспективна проверка", "Active prospective evaluation"),
            "status": bool((status.get("protected_step148_files") or {}).get("all_ok")),
        },
    ]
    st.dataframe(pd.DataFrame(coverage_rows), use_container_width=True, hide_index=True)

    with st.expander(_t("Подробен одит на видимите текстове", "Detailed visible-text audit"), expanded=False):
        rows = _load_csv(REPORT_CSV_PATH)
        if rows:
            display = pd.DataFrame(rows)
            if "bg_pass" in display.columns:
                display = display[display["bg_pass"].astype(str).str.lower().isin({"false", "0", "no"})]
            if display.empty:
                st.success(_t("Няма остатъчни забранени термини в българския режим.", "No forbidden residual terms remain in Bulgarian mode."))
            else:
                st.dataframe(display, use_container_width=True, hide_index=True)
        else:
            st.info(_t("Няма генериран подробен одит.", "No detailed audit has been generated."))

    st.markdown(_t("### Правила за показване", "### Display rules"))
    st.markdown(
        _t(
            "- Българският режим не показва смесени английски наименования в нормалния изглед.\n"
            "- Английският режим запазва английските наименования на основните потребителски елементи.\n"
            "- Вътрешните идентификатори, SHA-256 подписи, пътища и UTC полета са скрити по подразбиране.\n"
            "- Техническите данни остават достъпни чрез отделния превключвател в страничното меню.\n"
            "- Бутонът за внедряване и служебните Streamlit елементи са скрити от потребителския изглед.\n"
            "- Активното заключване за бъдещия тираж и замразеният оценяващ код не се променят.",
            "- Bulgarian mode avoids mixed English labels in the normal view.\n"
            "- English mode preserves English labels for the main user-facing elements.\n"
            "- Internal identifiers, SHA-256 signatures, paths and UTC fields are hidden by default.\n"
            "- Technical data remains available through the dedicated sidebar toggle.\n"
            "- The Deploy button and service Streamlit chrome are hidden from the user view.\n"
            "- The active future-draw lock and frozen scoring code remain unchanged.",
        )
    )

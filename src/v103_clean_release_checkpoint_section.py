from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.v103_clean_release_checkpoint_engine import (
    build_clean_release_summary,
    create_clean_release_checkpoint,
)
from src.v150_global_ui_polish import technical_details_enabled, ui_text


def _checks_df(summary: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(summary.get("checks", []))


def _user_status(summary: dict[str, Any]) -> str:
    status = str(summary.get("status", ""))
    labels = {
        "READY_FOR_CLEAN_ZIP": ui_text("Готово за резервно копие", "Ready for backup", st),
        "WAITING_FOR_CLEAN_GIT_STATUS": ui_text(
            "Първо запиши промените в GitHub",
            "Save the changes to GitHub first",
            st,
        ),
        "BLOCKED": ui_text("Нужна е проверка", "Review required", st),
    }
    return labels.get(status, ui_text("Нужна е проверка", "Review required", st))


def _user_checks_df(summary: dict[str, Any]) -> pd.DataFrame:
    labels = {
        "git_available": (
            ui_text("Връзка с хранилището", "Repository connection", st),
            ui_text(
                "Приложението разпознава файловете, които принадлежат към проекта.",
                "The application recognizes the files that belong to the project.",
                st,
            ),
        ),
        "working_tree_clean_before_zip": (
            ui_text("Промените са записани", "Changes are saved", st),
            ui_text(
                "Резервното копие се създава след commit и синхронизация с GitHub.",
                "The backup is created after committing and synchronizing with GitHub.",
                st,
            ),
        ),
        "forbidden_tracked_files": (
            ui_text("Без временни файлове", "No temporary files", st),
            ui_text(
                "В архива няма кешове, временни файлове или вложени ZIP архиви.",
                "The archive contains no caches, temporary files, or nested ZIP archives.",
                st,
            ),
        ),
        "tracked_zip_strategy": (
            ui_text("Само файловете на проекта", "Project files only", st),
            ui_text(
                "Включват се само файловете, които са част от приложението.",
                "Only files that are part of the application are included.",
                st,
            ),
        ),
    }
    rows: list[dict[str, str]] = []
    for item in summary.get("checks", []):
        key = str(item.get("check", ""))
        label, explanation = labels.get(
            key,
            (
                ui_text("Проверка на архива", "Archive check", st),
                ui_text("Проверката защитава резервното копие.", "This check protects the backup.", st),
            ),
        )
        passed = bool(item.get("passed"))
        rows.append(
            {
                ui_text("Проверка", "Check", st): label,
                ui_text("Резултат", "Result", st): ui_text("Готово", "Ready", st)
                if passed
                else ui_text("Нужно действие", "Action required", st),
                ui_text("Какво означава", "What it means", st): explanation,
            }
        )
    return pd.DataFrame(rows)


def render_v103_clean_release_checkpoint_section() -> None:
    st.title(ui_text("Резервно копие на приложението", "Application backup", st))
    st.caption(
        ui_text(
            "Създава чист архив на приложението, който можеш да запазиш като резервно копие "
            "или да използваш при преместване на друг компютър.",
            "Creates a clean application archive that you can keep as a backup or use when moving to another computer.",
            st,
        )
    )

    # The live summary does not write reports and therefore does not make Git status dirty.
    summary = build_clean_release_summary()
    git_status = str(summary.get("git_status_short", ""))
    blocking_failures = int(summary.get("blocking_failures", 0))
    can_create = not git_status and blocking_failures == 0

    c1, c2, c3 = st.columns(3)
    c1.metric(ui_text("Състояние", "Status", st), _user_status(summary))
    c2.metric(
        ui_text("Файлове за архивиране", "Files to archive", st),
        int(summary.get("tracked_file_count", 0)),
    )
    c3.metric(ui_text("Нужни действия", "Required actions", st), 0 if can_create else 1)

    if git_status:
        st.warning(
            ui_text(
                "Има промени, които още не са записани в GitHub. Първо завърши синхронизацията, "
                "за да съвпадат приложението, репото и резервното копие.",
                "Some changes have not yet been saved to GitHub. Complete synchronization first so the application, "
                "repository, and backup match.",
                st,
            )
        )
    elif blocking_failures:
        st.error(
            ui_text(
                "Архивът още не е готов. Прегледай проверките по-долу.",
                "The archive is not ready yet. Review the checks below.",
                st,
            )
        )
    else:
        st.success(
            ui_text(
                "Всички промени са записани и приложението е готово за резервно копие.",
                "All changes are saved and the application is ready for backup.",
                st,
            )
        )

    st.markdown(ui_text("### Какво ще получиш", "### What you will get", st))
    st.info(
        ui_text(
            "Един ZIP архив с файловете на приложението, без Git историята, кешове и временни файлове. "
            "Твоят локален дневник на фишовете не се включва.",
            "A ZIP archive with the application files, without Git history, caches, or temporary files. "
            "Your local ticket journal is not included.",
            st,
        )
    )

    if st.button(
        ui_text("Създай резервно копие", "Create backup", st),
        width="stretch",
        type="primary",
        disabled=not can_create,
        key="v103_create_backup",
    ):
        try:
            result = create_clean_release_checkpoint()
        except Exception as exc:  # noqa: BLE001
            st.error(
                ui_text(
                    "Резервното копие не беше създадено. Отвори „Технически подробности“ за причината.",
                    "The backup was not created. Open Technical details for the reason.",
                    st,
                )
            )
            if technical_details_enabled(st):
                st.exception(exc)
        else:
            zip_path = Path(str(result.get("zip_path", "")))
            st.success(
                ui_text(
                    f"Резервното копие е създадено успешно: {zip_path.name or 'ZIP архив'}",
                    f"The backup was created successfully: {zip_path.name or 'ZIP archive'}",
                    st,
                )
            )
            if technical_details_enabled(st):
                with st.expander(ui_text("Технически резултат", "Technical result", st), expanded=True):
                    st.code(str(zip_path), language="text")
                    st.json(result)

    st.markdown(ui_text("### Проверки преди архивиране", "### Checks before archiving", st))
    st.dataframe(_user_checks_df(summary), width="stretch", hide_index=True)

    if technical_details_enabled(st):
        with st.expander(ui_text("Технически подробности", "Technical details", st), expanded=True):
            st.caption(
                ui_text(
                    "Този раздел е предназначен за диагностика и поддръжка на проекта.",
                    "This section is intended for project diagnostics and maintenance.",
                    st,
                )
            )
            st.markdown(ui_text("#### Git статус", "#### Git status", st))
            st.code(git_status or "git status --short: clean", language="text")

            st.markdown(ui_text("#### Команда за терминала", "#### Terminal command", st))
            st.code(
                str(summary.get("recommended_command", "python .\\scripts\\v103_create_clean_release_checkpoint.py")),
                language="powershell",
            )

            st.markdown(ui_text("#### Пълни технически проверки", "#### Full technical checks", st))
            st.dataframe(_checks_df(summary), width="stretch", hide_index=True)

            forbidden_preview = summary.get("forbidden_tracked_preview") or []
            if forbidden_preview:
                st.markdown(ui_text("#### Файлове за технически преглед", "#### Files for technical review", st))
                st.code("\n".join(map(str, forbidden_preview)), language="text")

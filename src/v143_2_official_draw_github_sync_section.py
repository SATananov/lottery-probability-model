from __future__ import annotations

from typing import Any

import streamlit as st

from src.v143_2_official_draw_github_sync_audit_engine import (
    load_latest_runtime_audit,
    retry_push_and_confirm,
)

STATUS_LABELS_BG = {
    "ready": "Готово",
    "ready_with_unrelated_changes": "Готово с изключени промени",
    "not_git_repo": "Липсва Git хранилище",
    "detached_head": "Няма активен клон",
    "origin_missing": "Липсва GitHub връзка",
    "preexisting_staged_changes": "Има предварително подготвени файлове",
    "preexisting_sync_scope_changes": "Има неприключени промени",
    "nothing_to_commit_remote_confirmed": "Няма нови промени; GitHub е потвърден",
    "remote_confirmed": "Качването е потвърдено",
    "git_add_failed": "Подготовката на файловете не успя",
    "unsafe_staged_files": "Засечени са неразрешени файлове",
    "nothing_staged": "Няма подготвени промени",
    "commit_failed": "Git записът не успя",
    "local_commit_pending_push": "Локалният запис чака качване",
    "remote_confirmation_failed": "GitHub потвърждението не успя",
    "remote_mismatch": "Локалният и GitHub записът се различават",
    "no_pending_push_audit": "Няма чакащо качване",
    "retry_head_mismatch": "Текущият запис е различен",
    "retry_branch_mismatch": "Текущият клон е различен",
}


def _status_label(value: Any) -> str:
    status = str(value or "unknown")
    return STATUS_LABELS_BG.get(status, status)


def _short_sha(value: Any) -> str:
    text = str(value or "").strip()
    return text[:10] if text else "—"


def render_git_sync_preflight(snapshot: dict[str, Any], *, enabled: bool) -> None:
    st.markdown("#### Контрол на GitHub синхронизацията")
    columns = st.columns(4)
    columns[0].metric("Статус", _status_label(snapshot.get("status")))
    columns[1].metric("Клон", snapshot.get("branch") or "—")
    columns[2].metric("Локален запис", _short_sha(snapshot.get("local_head")))
    columns[3].metric("Изключени промени", len(snapshot.get("unrelated_paths") or []))

    if not enabled:
        st.info("Автоматичната GitHub синхронизация е изключена. Тиражът и резултатите от обновяването ще останат локални.")
    elif snapshot.get("can_sync"):
        if snapshot.get("status") == "ready_with_unrelated_changes":
            st.warning(snapshot.get("message_bg", ""))
        else:
            st.success(snapshot.get("message_bg", ""))
    else:
        st.error(snapshot.get("message_bg", "Автоматичната GitHub синхронизация не е готова."))
        st.caption("Можеш да изключиш GitHub отметката и да запишеш тиража само локално.")

    with st.expander("Какво ще бъде включено и изключено", expanded=False):
        st.write("Автоматичният Git запис включва само:")
        st.code(
            "data/historical_draws.csv\n"
            "data/v40_normalized_draw_events.csv\n"
            "data/v41_canonical_draw_events.csv\n"
            "models/\nreports/"
        )
        st.write("Личният дневник, тайните настройки, резервните копия и локалните отчети от проверката не се добавят.")
        if snapshot.get("unrelated_paths"):
            st.write("Текущи изключени локални промени:")
            st.code("\n".join(snapshot.get("unrelated_paths") or []))

    latest = load_latest_runtime_audit()
    if latest:
        st.caption(
            "Последна проверка: "
            f"{_status_label(latest.get('status'))} · "
            f"локално {_short_sha(latest.get('local_commit_sha'))} · "
            f"GitHub {_short_sha(latest.get('remote_commit_sha'))}"
        )
        if latest.get("status") in {"local_commit_pending_push", "remote_confirmation_failed", "remote_mismatch"}:
            if st.button("Повтори качването и проверката в GitHub", key="v143_2_retry_git_push"):
                with st.spinner("Повтарям качването и проверявам GitHub записа..."):
                    retry_result = retry_push_and_confirm()
                render_git_sync_result(retry_result)


def render_git_sync_result(result: dict[str, Any]) -> None:
    status = str(result.get("status") or "unknown")
    message = str(result.get("message_bg") or status)
    if result.get("ok"):
        st.success(message)
    elif status in {"local_commit_pending_push", "remote_confirmation_failed", "remote_mismatch"}:
        st.warning(message)
    else:
        st.error(message)

    columns = st.columns(4)
    columns[0].metric("Клон", result.get("branch") or "—")
    columns[1].metric("Локален запис", _short_sha(result.get("local_commit_sha")))
    columns[2].metric("GitHub запис", _short_sha(result.get("remote_commit_sha")))
    columns[3].metric("GitHub потвърждение", "Да" if result.get("remote_confirmed") else "Не")

    included = result.get("staged_files") or result.get("candidate_files") or []
    excluded = result.get("excluded_changed_files") or []
    with st.expander("Подробности от Step 143.2 проверката", expanded=not bool(result.get("ok"))):
        st.write(f"Включени файлове: {len(included)}")
        if included:
            st.code("\n".join(included))
        st.write(f"Изключени локални файлове: {len(excluded)}")
        if excluded:
            st.code("\n".join(excluded))
        if result.get("audit_json_path"):
            st.caption(f"Локален отчет от проверката: {result.get('audit_json_path')}")

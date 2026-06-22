from __future__ import annotations

from pathlib import Path
import csv
import json

import streamlit as st

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

from src.v74_model_dependency_sync_center_engine import build_model_dependency_sync_center
from src.v74_selective_sync_actions import (
    available_sync_models,
    build_sync_plan,
    run_sync_plan,
)
from src.v74_git_sync_actions import commit_and_push_model_outputs, git_status_short

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "reports" / "v74_model_dependency_summary.json"
STATUS_PATH = ROOT / "reports" / "v74_model_sync_status.csv"
MAP_PATH = ROOT / "reports" / "v74_model_dependency_map.csv"
LATEST_SELECTIVE_SYNC_PATH = ROOT / "reports" / "v74_1_latest_selective_sync_result.json"

CATEGORY_BG = {
    "Smart ensemble": "Умно обединяване",
    "Performance tracker": "История на представянето",
    "Reliability": "Надеждност",
    "Adaptive weighting": "Адаптивно тегло",
    "Weighted ensemble": "Претеглен ансамбъл",
    "Weighted ticket builder": "Генератор с тегла",
    "Portfolio optimizer": "Оптимизатор на портфейл",
    "Improvement suggestion": "Предложения за подобрение",
    "Applied portfolio": "Приложен портфейл",
    "Ticket pack export": "Пакет за игра",
    "Performance after draw": "Проверка след тираж",
}


def _bg_category(value: str) -> str:
    return CATEGORY_BG.get(str(value), str(value))


def _load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _show_table(rows, columns):
    if not rows:
        st.info("Няма данни за показване.")
        return
    shown = []
    for row in rows:
        item = {}
        for label, key in columns:
            value = row.get(key, "")
            if key == "category":
                value = _bg_category(value)
            item[label] = value
        shown.append(item)
    if pd is not None:
        st.dataframe(pd.DataFrame(shown), use_container_width=True, hide_index=True)
    else:
        st.table(shown)


def _show_plan(plan):
    if not plan:
        st.info("Няма избрани действия.")
        return
    rows = []
    for item in plan:
        rows.append({
            "Ред": item.get("order", ""),
            "Стъпка": f"Step {item.get('step', '')}",
            "Модел / слой": item.get("label", ""),
            "Категория": _bg_category(item.get("category", "")),
            "Script": item.get("script", ""),
            "Наличен": "Да" if item.get("script_exists") else "Не",
        })
    if pd is not None:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.table(rows)


def _show_run_result(result):
    if not result:
        return
    status = result.get("status", "")
    if status == "OK":
        st.success(
            f"Синхронизацията мина успешно: {result.get('successful_actions', 0)} от "
            f"{result.get('planned_actions', 0)} действия."
        )
    else:
        st.error(
            f"Синхронизацията спря с проблем: {result.get('successful_actions', 0)} успешни, "
            f"{result.get('failed_actions', 0)} проблемни действия."
        )

    with st.expander("Последен log от синхронизацията", expanded=status != "OK"):
        for row in result.get("results", []) or []:
            st.markdown(f"**Step {row.get('step')} — {row.get('label')}** — {row.get('status')}")
            stdout = str(row.get("stdout_tail", "") or "").strip()
            stderr = str(row.get("stderr_tail", "") or "").strip()
            if stdout:
                st.code(stdout, language="text")
            if stderr:
                st.code(stderr, language="text")



def _show_git_result(result):
    if not result:
        return
    status = result.get("status", "")
    if status == "OK":
        st.success(result.get("message", "GitHub sync мина успешно."))
    elif status == "Няма промени":
        st.info(result.get("message", "Няма промени за качване."))
    else:
        st.error(result.get("message", "GitHub sync спря с проблем."))

    latest_commit = str(result.get("latest_commit", "") or "").strip()
    if latest_commit:
        st.caption(f"Последен commit: {latest_commit}")

    remaining = str(result.get("remaining_status", "") or "").strip()
    if remaining:
        with st.expander("Оставащи локални промени след GitHub sync"):
            st.code(remaining, language="text")

    with st.expander("GitHub sync log", expanded=status not in {"OK", "Няма промени"}):
        for step in result.get("steps", []) or []:
            st.markdown(f"**{step.get('name', 'git')}** — code {step.get('returncode')}")
            stdout = str(step.get("stdout", "") or "").strip()
            stderr = str(step.get("stderr", "") or "").strip()
            if stdout:
                st.code(stdout[-3000:], language="text")
            if stderr:
                st.code(stderr[-3000:], language="text")

def render_v74_model_dependency_sync_center_section():
    st.title("Контрол на синхрона")
    st.caption(
        "Показва и управлява дали dataset-ите, моделите, отчетите и pipeline стъпките са подравнени. "
        "Това е контролен център, не прогноза и не гаранция за печалба."
    )

    summary = _load_json(SUMMARY_PATH)
    if not summary:
        st.warning("Липсва Step 74 report. Пусни: python scripts/v74_build_model_dependency_sync_center.py")
        return

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Статус", summary.get("status", "-"))
    col2.metric("Проверени", summary.get("models_checked", 0))
    col3.metric("Синхронизирани", summary.get("synced_models", 0))
    col4.metric("За обновяване", summary.get("stale_models", 0))
    col5.metric("Липсващи", summary.get("missing_models", 0))

    dataset_sync = summary.get("dataset_sync", {}) or {}
    if dataset_sync.get("rows_synced") and dataset_sync.get("latest_draw_synced"):
        st.success("Главните dataset-и са синхронизирани по редове и последен тираж.")
    else:
        st.warning("Има разминаване между главните dataset-и. Провери data refresh flow-а.")

    st.subheader("Управление на синхрона")
    st.info(
        "Оттук можеш да обновиш само избран модел, избрания модел заедно със зависимите след него, "
        "или цялата верига. Така не е нужно да търсиш и пускаш скриптовете един по един."
    )

    models = available_sync_models()
    model_options = [item["display"] for item in models]
    model_by_display = {item["display"]: item for item in models}

    selected_display = st.selectbox(
        "Избери модел / слой за синхронизация",
        model_options,
        index=max(0, len(model_options) - 2),
        key="v74_1_selected_model",
    )
    selected_model = model_by_display[selected_display]

    mode_label = st.radio(
        "Режим на обновяване",
        [
            "Само избрания модел",
            "Избрания модел + зависимите след него",
            "Цялата верига от модели",
        ],
        index=1,
        horizontal=False,
        key="v74_1_sync_mode_label",
    )
    mode_map = {
        "Само избрания модел": "selected_only",
        "Избрания модел + зависимите след него": "selected_and_downstream",
        "Цялата верига от модели": "full_chain",
    }
    mode = mode_map[mode_label]

    try:
        plan = build_sync_plan(selected_model["step"], mode=mode)
    except Exception as exc:  # pragma: no cover
        st.error(f"Не мога да построя план за синхронизация: {exc}")
        plan = []

    st.markdown("**План за изпълнение**")
    _show_plan(plan)

    btn1, btn2, btn3 = st.columns([1, 1, 1])
    run_selected = btn1.button("Синхронизирай по плана", type="primary", key="v74_1_run_plan")
    run_full = btn2.button("Синхронизирай цялата верига", key="v74_1_run_full_chain")
    refresh_audit = btn3.button("Само провери синхрона", key="v74_refresh_button")

    if refresh_audit:
        with st.spinner("Проверявам синхрона между моделите..."):
            result = build_model_dependency_sync_center()
        st.success("Step 74 audit е обновен.")
        st.json(result)

    if run_selected or run_full:
        run_mode = "full_chain" if run_full else mode
        run_plan = build_sync_plan(selected_model["step"], mode=run_mode)
        with st.spinner("Синхронизирам моделите по избрания план..."):
            result = run_sync_plan(run_plan)
        _show_run_result(result)

    latest_result = _load_json(LATEST_SELECTIVE_SYNC_PATH)
    if latest_result:
        with st.expander("Последна записана синхронизация"):
            st.write(f"Статус: **{latest_result.get('status', '-')}**")
            st.write(
                f"Изпълнени действия: **{latest_result.get('executed_actions', 0)}** / "
                f"{latest_result.get('planned_actions', 0)}"
            )
            st.write(f"Генерирано: {latest_result.get('generated_at', '')}")

    st.subheader("GitHub синхрон")
    st.caption(
        "След локална синхронизация можеш оттук да commit-неш и push-неш обновените models/reports/data artifacts. "
        "Бутонът не заменя проверката на логовете, но спестява ръчното търсене на git командите."
    )
    current_git_status = git_status_short()
    if current_git_status:
        with st.expander("Локални промени за преглед", expanded=False):
            st.code(current_git_status, language="text")
    else:
        st.success("Няма локални промени за качване към GitHub.")

    commit_message = st.text_input(
        "Съобщение за GitHub запис",
        value="Sync model dependency center outputs",
        key="v74_2_git_commit_message",
    )
    if st.button("Запиши и качи models/reports/data в GitHub", key="v74_2_git_commit_push"):
        with st.spinner("Комитвам и качвам обновените artifacts към GitHub..."):
            git_result = commit_and_push_model_outputs(commit_message=commit_message)
        _show_git_result(git_result)

    st.subheader("Главни dataset-и")
    dataset_rows = []
    for item in summary.get("datasets", []) or []:
        dataset_rows.append({
            "path": item.get("path", ""),
            "rows": item.get("rows", ""),
            "latest_date": item.get("latest_date", ""),
            "latest_draw_no": item.get("latest_draw_no", ""),
            "latest_numbers": item.get("latest_numbers", ""),
            "mtime": item.get("mtime", ""),
        })
    _show_table(dataset_rows, [
        ("Dataset", "path"),
        ("Редове", "rows"),
        ("Последна дата", "latest_date"),
        ("Последен тираж", "latest_draw_no"),
        ("Последни числа", "latest_numbers"),
        ("Последна промяна", "mtime"),
    ])

    st.subheader("Синхрон на моделите")
    status_rows = _load_csv(STATUS_PATH)
    _show_table(status_rows, [
        ("Стъпка", "step"),
        ("Име", "label"),
        ("Категория", "category"),
        ("Статус", "sync_status"),
        ("Помага на", "feeds"),
        ("Роля", "role"),
    ])

    st.subheader("Карта на зависимостите")
    edge_rows = _load_csv(MAP_PATH)
    _show_table(edge_rows[:200], [
        ("От", "from"),
        ("Към", "to"),
        ("Тип", "type"),
        ("Описание", "description"),
    ])

    with st.expander("Как да се чете този център"):
        st.markdown(
            """
- **Синхронизиран** означава, че входните dataset-и/артефакти и изходите са налични и изходите не изглеждат по-стари от входовете.
- **Нужно обновяване** означава, че входен файл е по-нов от изхода и е добре да се пусне обновяване.
- **Липсва файл** означава липсващ script, input или output artifact.
- **Само избрания модел** пуска само конкретната стъпка и после обновява Step 74 audit.
- **Избрания модел + зависимите след него** пуска избрания слой и всички следващи слоеве, които зависят от него.
- **Цялата верига** пуска всички регистрирани model/report build стъпки по ред.
- Моделите не се учат сляпо един от друг. Те си помагат чрез сигнали, reliability, тегла, ensemble и portfolio логика.
- Истината за обновяване остава реалният тираж, не прогнозата на друг модел.
"""
        )

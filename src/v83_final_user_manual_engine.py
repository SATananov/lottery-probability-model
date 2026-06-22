from __future__ import annotations

from pathlib import Path
import csv
import json
from datetime import datetime, timezone
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"
DATA_DIR = ROOT / "data"
V83_MODELS_DIR = MODELS_DIR / "v83"

SUMMARY_JSON = REPORTS_DIR / "v83_final_user_manual_summary.json"
SUMMARY_MD = REPORTS_DIR / "v83_final_user_manual_summary.md"
GUIDE_SECTIONS_CSV = REPORTS_DIR / "v83_app_guide_sections.csv"
WORKFLOW_CSV = REPORTS_DIR / "v83_recommended_workflow.csv"
SAFE_CHECKLIST_CSV = REPORTS_DIR / "v83_safe_usage_checklist.csv"
MODEL_JSON = V83_MODELS_DIR / "v83_final_user_manual_model.json"

SAFE_NOTE = (
    "Step 83 е финален потребителски помощен слой. "
    "Той обяснява как да се използва приложението дисциплинирано и безопасно. "
    "Не е прогноза, не е обещание и не е гаранция за печалба."
)


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _latest_draw_info() -> dict[str, Any]:
    path = DATA_DIR / "historical_draws.csv"
    if not path.exists():
        return {"draws": 0, "latest_draw_date": "-", "latest_numbers": "-"}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = [dict(row) for row in csv.DictReader(f)]
    if not rows:
        return {"draws": 0, "latest_draw_date": "-", "latest_numbers": "-"}
    latest = rows[-1]
    number_keys = [key for key in ["n1", "n2", "n3", "n4", "n5", "n6"] if key in latest]
    numbers = [str(latest.get(key, "")).strip() for key in number_keys if str(latest.get(key, "")).strip()]
    latest_date = latest.get("date") or latest.get("draw_date") or latest.get("Дата") or "-"
    return {
        "draws": len(rows),
        "latest_draw_date": latest_date,
        "latest_numbers": ", ".join(numbers) if numbers else "-",
    }


def _guide_sections() -> list[dict[str, Any]]:
    return [
        {"section_order": 1, "section": "Какво представлява приложението", "purpose": "Показва статистически анализи върху исторически тиражи 6/49 и помага за дисциплиниран избор на комбинации.", "user_action": "Използвай го като помощник за анализ, не като система за сигурна печалба.", "safe_note": SAFE_NOTE},
        {"section_order": 2, "section": "Какво не представлява приложението", "purpose": "Не предсказва бъдещ тираж и не отменя случайността на лотарията.", "user_action": "Не увеличавай залога само защото даден модул показва висока оценка.", "safe_note": SAFE_NOTE},
        {"section_order": 3, "section": "Добавяне на нов тираж", "purpose": "Въвежда нови реални числа и синхронизира наборите от данни и зависимите модели.", "user_action": "Първо провери числата внимателно, после пускай обновяването.", "safe_note": SAFE_NOTE},
        {"section_order": 4, "section": "Анализ на нов тираж", "purpose": "Сравнява новия тираж с предишни модели, пакети и статистически сигнали.", "user_action": "Използвай резултата за наблюдение на модела, не за обещание за следващия тираж.", "safe_note": SAFE_NOTE},
        {"section_order": 5, "section": "Исторически анализи", "purpose": "Показват честоти, интервали, сходни тиражи, двойки, групи и профили на числа.", "user_action": "Гледай ги като контекст и проверка на структурата.", "safe_note": SAFE_NOTE},
        {"section_order": 6, "section": "Генератори и портфолио", "purpose": "Създават и оценяват комбинации чрез различни статистически слоеве.", "user_action": "Избирай малък, дисциплиниран пакет, без да гониш прекалено много комбинации.", "safe_note": SAFE_NOTE},
        {"section_order": 7, "section": "Финален план", "purpose": "Събира препоръки, резерви и действия в практичен план за използване.", "user_action": "Следвай финалния план само като организирана статистическа помощ.", "safe_note": SAFE_NOTE},
        {"section_order": 8, "section": "Експорт и изпълнение", "purpose": "Подготвя финалния пакет за копиране, печат или ръчна проверка.", "user_action": "Преди реално пускане провери всяка комбинация ръчно.", "safe_note": SAFE_NOTE},
        {"section_order": 9, "section": "Системни проверки", "purpose": "Проверяват верига за синхронизация, готовност на финалния пакет, UX, опис на файловете, съгласуваност на данните и техническа чистота.", "user_action": "Пускай ги след важни промени, особено след добавяне на тираж.", "safe_note": SAFE_NOTE},
        {"section_order": 10, "section": "Добра дисциплина", "purpose": "Помага да се избегне емоционално преследване на загуби и прекомерно доверие в модел.", "user_action": "Определи лимит предварително и не го променяй според моментен резултат.", "safe_note": SAFE_NOTE},
    ]


def _workflow_rows() -> list[dict[str, Any]]:
    return [
        {"step_order": 1, "page": "Добавяне на тираж", "when_to_use": "Когато има нов официален тираж.", "expected_result": "Наборите от данни и моделните артефакти се обновяват.", "caution": "Въведи числата точно. Bonus не се смесва с основните 6 числа."},
        {"step_order": 2, "page": "Анализ на нов тираж", "when_to_use": "След въвеждане или преди сравнение с предишни пакети.", "expected_result": "Виждаш как последният тираж се отнася към исторически сигнали.", "caution": "Това е анализ след тиража, не обещание за бъдещ резултат."},
        {"step_order": 3, "page": "История на моделите", "when_to_use": "Когато искаш да следиш представянето във времето.", "expected_result": "Получаваш историческа картина за стабилност/слабости.", "caution": "Единичен добър резултат не доказва надеждност."},
        {"step_order": 4, "page": "Умно тегло на моделите", "when_to_use": "Когато искаш адаптивно претегляне според надеждност.", "expected_result": "Моделите получават различна тежест според отчетени сигнали.", "caution": "Тежестта е статистическа, не гарантира печалба."},
        {"step_order": 5, "page": "Умен генератор с тегла", "when_to_use": "Когато подготвяш кандидат комбинации.", "expected_result": "Получаваш структурирани кандидати с претеглена оценка.", "caution": "Не генерирай прекалено голям пакет без лимит."},
        {"step_order": 6, "page": "Умен оптимизатор на портфейл", "when_to_use": "Когато искаш по-добро покритие и по-малко повтаряемост.", "expected_result": "Портфолиото се оценява за покритие, повторения и баланс.", "caution": "По-добър баланс не означава сигурен резултат."},
        {"step_order": 7, "page": "Решение и препоръка", "when_to_use": "Когато искаш финално филтриране преди план.", "expected_result": "Системата предлага дисциплинирана препоръка.", "caution": "Приемай препоръката като помощен избор, не като предсказание."},
        {"step_order": 8, "page": "Финален план", "when_to_use": "Когато подготвяш реалния пакет.", "expected_result": "Получаваш активни фишове, резерви и действия.", "caution": "Пази фиксиран бюджет и не променяй плана емоционално."},
        {"step_order": 9, "page": "Експорт и изпълнение", "when_to_use": "Когато трябва да копираш или отпечаташ пакета.", "expected_result": "Имаш чист контролен списък за изпълнение и текст за копиране.", "caution": "Провери ръчно всяко число преди използване."},
        {"step_order": 10, "page": "Финален release пакет / Контрол на синхрона", "when_to_use": "След по-големи промени или преди чист ZIP.", "expected_result": "Проверяваш дали app/reports/models са синхронизирани.", "caution": "Не прави чист ZIP при нечист Git статус или неуспешни проверки."},
    ]


def _safe_checklist_rows() -> list[dict[str, Any]]:
    return [
        {"check_order": 1, "check_item": "Лотарията остава случайна", "recommended_behavior": "Приемай всички оценки като статистически помощни сигнали.", "risk_if_ignored": "Прекомерно доверие в модел или погрешно усещане за сигурност."},
        {"check_order": 2, "check_item": "Няма гаранция за печалба", "recommended_behavior": "Не използвай думи като сигурно, гарантирано или задължително.", "risk_if_ignored": "Нереалистични очаквания."},
        {"check_order": 3, "check_item": "Фиксиран бюджет", "recommended_behavior": "Определи лимит преди избора и не го променяй след това.", "risk_if_ignored": "Емоционално преследване на загуби."},
        {"check_order": 4, "check_item": "Ръчна проверка на числата", "recommended_behavior": "Провери всяка комбинация преди пускане или архивиране.", "risk_if_ignored": "Грешен фиш, дублирана таблица или сгрешено число."},
        {"check_order": 5, "check_item": "Bonus числото се държи отделно", "recommended_behavior": "Не смесвай bonus с основните 6 числа при анализ.", "risk_if_ignored": "Изкривяване на статистиката."},
        {"check_order": 6, "check_item": "След нов тираж се пуска синхрон", "recommended_behavior": "След Add Draw използвай refresh/верига за синхронизация според приложението.", "risk_if_ignored": "Остарели модели и отчети."},
        {"check_order": 7, "check_item": "Clean ZIP само при чист статус", "recommended_behavior": "Първо commit/push и празен git status, после архив.", "risk_if_ignored": "Непълен или несинхронизиран checkpoint."},
    ]


def build_final_user_manual_center() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    V83_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    latest = _latest_draw_info()
    v82_summary = _read_json(REPORTS_DIR / "v82_final_release_summary.json")
    v81_summary = _read_json(REPORTS_DIR / "v81_final_ux_navigation_summary.json")

    guide_sections = _guide_sections()
    workflow_rows = _workflow_rows()
    safe_checklist = _safe_checklist_rows()

    issues: list[str] = []
    for rel in ["streamlit_app.py", "reports/v82_final_release_summary.json", "reports/v81_final_ux_navigation_summary.json", "data/historical_draws.csv"]:
        if not (ROOT / rel).exists():
            issues.append(f"Missing required input: {rel}")

    if not any(row["section"] == "Какво не представлява приложението" for row in guide_sections):
        issues.append("Missing safe negative-definition guide section.")

    if not any("гаранция" in (row["check_item"] + " " + row["recommended_behavior"]).lower() for row in safe_checklist):
        issues.append("Safe checklist does not mention guarantee limits.")

    status = "OK" if not issues else "Има нужда от преглед"

    summary = {
        "step": "83",
        "title": "Final User Manual / App Guide Center",
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "safe_note": SAFE_NOTE,
        "dataset_rows": latest["draws"],
        "latest_draw_date": latest["latest_draw_date"],
        "latest_numbers": latest["latest_numbers"],
        "guide_sections_count": len(guide_sections),
        "workflow_steps_count": len(workflow_rows),
        "safe_checklist_count": len(safe_checklist),
        "issues_found": len(issues),
        "issues_preview": issues[:10],
        "v82_release_status": v82_summary.get("status", "-"),
        "v82_unwanted_release_files": v82_summary.get("unwanted_release_files", "-"),
        "v81_ux_status": v81_summary.get("status", "-"),
        "outputs": [
            "models/v83/v83_final_user_manual_model.json",
            "reports/v83_final_user_manual_summary.json",
            "reports/v83_final_user_manual_summary.md",
            "reports/v83_app_guide_sections.csv",
            "reports/v83_recommended_workflow.csv",
            "reports/v83_safe_usage_checklist.csv",
        ],
    }

    _write_csv(GUIDE_SECTIONS_CSV, guide_sections, ["section_order", "section", "purpose", "user_action", "safe_note"])
    _write_csv(WORKFLOW_CSV, workflow_rows, ["step_order", "page", "when_to_use", "expected_result", "caution"])
    _write_csv(SAFE_CHECKLIST_CSV, safe_checklist, ["check_order", "check_item", "recommended_behavior", "risk_if_ignored"])

    model = {
        "summary": summary,
        "guide_sections": guide_sections,
        "recommended_workflow": workflow_rows,
        "safe_usage_checklist": safe_checklist,
    }

    _write_json(SUMMARY_JSON, summary)
    _write_json(MODEL_JSON, model)

    md_lines = [
        "# Step 83 — Ръководство и помощ за приложението",
        "",
        f"Статус: **{status}**",
        "",
        SAFE_NOTE,
        "",
        "## Обхват",
        "",
        f"- Dataset редове: **{latest['draws']}**",
        f"- Последен тираж: **{latest['latest_draw_date']}**",
        f"- Последни числа: **{latest['latest_numbers']}**",
        f"- Раздели в ръководството: **{len(guide_sections)}**",
        f"- Стъпки в последователността: **{len(workflow_rows)}**",
        f"- Точки за безопасно използване: **{len(safe_checklist)}**",
        "",
        "## Препоръчителна последователност",
        "",
        "| Ред | Страница | Кога се използва | Внимание |",
        "|---:|---|---|---|",
    ]

    for row in workflow_rows:
        md_lines.append(f"| {row['step_order']} | {row['page']} | {row['when_to_use']} | {row['caution']} |")

    md_lines.extend(["", "## Безопасно използване", ""])
    for row in safe_checklist:
        md_lines.append(f"- **{row['check_item']}** — {row['recommended_behavior']}")

    if issues:
        md_lines.extend(["", "## Елементи за преглед", ""])
        md_lines.extend([f"- {issue}" for issue in issues])

    SUMMARY_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return summary


if __name__ == "__main__":
    result = build_final_user_manual_center()
    print("STEP83_STATUS", result.get("status"))
    print("GUIDE_SECTIONS", result.get("guide_sections_count"))
    print("WORKFLOW_STEPS", result.get("workflow_steps_count"))
    print("SAFE_CHECKS", result.get("safe_checklist_count"))

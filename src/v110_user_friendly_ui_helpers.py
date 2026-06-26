from __future__ import annotations

from typing import Any

STATUS_LABELS = {
    "UNKNOWN": "Няма данни",
    "OK": "OK",
    "READY": "Готово",
    "CHECK_REQUIRED": "Нужна е проверка",
    "WAITING_NEXT_DRAW": "Чака следващ тираж",
    "WAITING_NEXT_REAL_DRAW": "Чака следващ реален тираж",
    "READY_WAITING_NEXT_DRAW": "Готово — чака следващ тираж",
    "V1_LOCKED_WAITING_NEXT_DRAW": "Заключено — чака следващ тираж",
    "HAS_HISTORY": "Има история",
    "RUNTIME_HARDENED": "Защитата е активна",
    "CLEAN_ZIP_CREATED": "Чистият архив е създаден",
    "READY_FOR_CLEAN_ZIP": "Готово за чист архив",
    "WAITING_FOR_CLEAN_GIT_STATUS": "Чака чист Git статус",
    "FINAL_AUDIT_REFRESHED": "Финалната проверка е обновена",
    "POST_DRAW_SYNCED": "Синхронизирано след тираж",
    "POST_DRAW_DATASETS_SYNCED": "Данните са синхронизирани",
    "TRAINING_POLICY_READY": "Политиката е готова",
    "USER_MENU_LIVE_STATUS_SYNCED": "Менюто е актуално",
    "SQLITE_JOURNAL_READY": "Дневникът е активен",
    "JOURNAL_UI_POLISHED": "Дневникът е изчистен визуално",
    "TICKET_PACK_READY": "Пакетът с фишове е готов",
    "TICKET_SOURCE_CLARIFIED": "Източниците са изяснени",
    "TICKET_PACK_SOURCES_ALIGNED": "Фишовете са подравнени с финалния план",
    "USER_FRIENDLY_UI_POLISHED": "Потребителският изглед е изчистен",
}

PAGE_LABELS = {
    "Runtime защита": "Защита при обновяване",
    "Clean ZIP checkpoint": "Чист архив на проекта",
    "Финален одит след Step 102": "Финална проверка на проекта",
    "Финален UX контрол": "Потребителски контрол",
    "Финален пакет за предаване": "Архивен пакет",
    "Прогнозно табло Pro": "Прогнозно табло",
    "МЛ лаборатория": "Лаборатория с модели",
    "Невронна лаборатория": "Тежка моделна лаборатория",
    "Контрол на синхрона": "Контрол на файловете и моделите",
    "Регистър на модели": "Регистър на моделите",
    "Пакет за игра": "Пакет от комбинации",
    "Представяне на пакета": "История на пакета",
    "Интеграция на моделните резултати": "Източници на моделите",
}

COLUMN_LABELS = {
    "status": "Статус",
    "step_status": "Статус",
    "blocking_failures": "Проблеми за преглед",
    "dataset_rows": "Редове в данните",
    "historical_rows": "Исторически редове",
    "normalized_rows": "Нормализирани редове",
    "canonical_rows": "Канонични редове",
    "latest_draw": "Последен тираж",
    "latest_date": "Последна дата",
    "latest_numbers": "Последни числа",
    "step": "Стъпка",
    "check": "Проверка",
    "blocking": "Блокираща",
    "details_bg": "Детайли",
    "name": "Име",
    "description": "Описание",
    "script": "Скрипт",
    "file": "Файл",
    "path": "Път",
    "source": "Източник",
    "source_ticket_id": "Източник",
    "line_no": "Комбинация",
    "draw_key": "Ключ на тиража",
    "drawing_position": "Теглене",
    "entered_at_utc": "Въведено на",
    "generated_at_utc": "Обновено на",
    "recommendation": "Препоръка",
    "recommendation_bg": "Препоръка",
    "heavy_training_status": "Тежко обучение",
    "training_recommendation": "Препоръка за обучение",
    "policy_decision": "Решение",
}

VALUE_LABELS = {
    "yes": "Да",
    "no": "Не",
    "true": "Да",
    "false": "Не",
    "PASS": "OK",
    "FAIL": "Проблем",
}


def friendly_status(value: Any) -> str:
    if value is None:
        return "Няма данни"
    text = str(value).strip()
    if not text:
        return "Няма данни"
    return STATUS_LABELS.get(text, text.replace("_", " ").capitalize())


def friendly_page_label(page: Any) -> str:
    text = str(page)
    return PAGE_LABELS.get(text, text)


def friendly_step_name(name: Any) -> str:
    text = str(name or "")
    replacements = {
        "Step 95": "Проверка преди запис",
        "Step 97": "Реален цикъл",
        "Step 98": "История на плана",
        "Step 99": "Финално табло",
        "Step 100": "Финално заключване",
        "Step 101": "Протокол за употреба",
        "Step 102": "Защита при обновяване",
        "Step 103": "Чист архив",
        "Step 104": "Финална проверка",
        "Step 107": "Политика за обучение",
        "Step 108": "Актуално меню",
        "Step 109": "Дневник на фишовете",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def polish_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value
    for old, new in {
        "Blocking failures": "Проблеми за преглед",
        "Dataset": "Данни",
        "dataset": "данни",
        "Runtime": "Защита при обновяване",
        "Clean ZIP checkpoint": "Чист архив на проекта",
        "heavy/lab": "тежки лабораторни",
        "heavy": "тежко",
        "lab": "лаборатория",
    }.items():
        text = text.replace(old, new)
    return friendly_step_name(text)


def polish_dataframe(df: Any) -> Any:
    if df is None or not hasattr(df, "copy"):
        return df
    try:
        if df.empty:
            return df
        out = df.copy()
        out = out.rename(columns={col: COLUMN_LABELS.get(str(col), str(col)) for col in out.columns})
        for col in out.columns:
            try:
                out[col] = out[col].map(
                    lambda value: friendly_status(value)
                    if isinstance(value, str) and value in STATUS_LABELS
                    else VALUE_LABELS.get(str(value), polish_text(value))
                )
            except Exception:
                pass
        return out
    except Exception:
        return df

from __future__ import annotations

from typing import Any

BG_COLUMN_LABELS = {
    # Generic technical columns
    "Step": "Стъпка",
    "step": "Стъпка",
    "Name": "Име",
    "name": "Име",
    "Script": "Скрипт",
    "script": "Скрипт",
    "Script OK": "Скрипт OK",
    "script_exists": "Скрипт OK",
    "Outputs": "Артефакти",
    "outputs": "Артефакти",
    "Outputs OK": "Артефакти OK",
    "outputs_ok": "Артефакти OK",
    "Run status": "Статус на изпълнение",
    "Run статус": "Статус на изпълнение",
    "run_status": "Статус на изпълнение",
    "run_ok": "Изпълнение OK",
    "run_output_tail": "Последен технически изход",
    "latest_output_mtime": "Последна промяна",
    "mode": "Режим",
    "status": "Статус",
    "decision": "Решение",
    "message": "Съобщение",
    "file": "Файл",
    "path": "Път",
    "source": "Източник",
    "rank": "Ранг",
    "group": "Група",
    "category": "Категория",
    "band": "Оценъчна група",
    "label": "Етикет",
    "description": "Описание",
    "recommendation": "Препоръка",
    "warning": "Предупреждение",
    "note": "Бележка",
    "created_at": "Създадено на",
    "updated_at": "Обновено на",
    "generated_at": "Генерирано на",

    # Draw / lottery columns
    "draw_id": "ID на тираж",
    "draw_event_id": "ID на теглене",
    "draw_no": "Тираж №",
    "drawing_no": "Тираж №",
    "draw_number": "Тираж №",
    "draw_date": "Дата на тиража",
    "date": "Дата",
    "year": "Година",
    "event_date": "Дата на теглене",
    "main_numbers": "Основни числа",
    "numbers": "Числа",
    "numbers_display": "Числа",
    "bonus_number": "Допълнително число",
    "bonus": "Допълнително число",
    "number": "Число",
    "n1": "Число 1",
    "n2": "Число 2",
    "n3": "Число 3",
    "n4": "Число 4",
    "n5": "Число 5",
    "n6": "Число 6",

    # Ticket / portfolio columns
    "ticket_id": "Комбинация",
    "combination_id": "Комбинация",
    "physical_ticket_id": "Физически фиш",
    "combination_in_ticket": "Комбинация във фиша",
    "combination_label": "Комбинация",
    "ticket": "Комбинация",
    "ticket_index": "Комбинация",
    "ticket_numbers": "Числа в комбинацията",
    "ticket_count": "Брой комбинации",
    "tickets": "Комбинации",
    "strategy": "Стратегия",
    "strategy_label": "Стратегия",
    "portfolio_score": "Оценка на портфейла",
    "portfolio_contribution_score": "Принос към портфейла",
    "candidate_score": "Оценка на кандидата",
    "candidate_numbers": "Кандидат числа",
    "applied_score": "Приложена оценка",
    "applied_numbers": "Приложени числа",
    "original_score": "Оригинална оценка",
    "original_numbers": "Оригинални числа",
    "score_delta": "Промяна в оценката",
    "delta": "Промяна",
    "changed": "Променен",
    "change_type": "Тип промяна",
    "replacement_count": "Брой замени",
    "removed_number": "Премахнато число",
    "added_number": "Добавено число",
    "historical_exact_match": "Историческо повторение",
    "exact_match": "Точно съвпадение",
    "hit_count": "Познати числа",
    "hits": "Познати числа",
    "matched_numbers": "Познати числа",
    "unique_hits": "Уникални познати числа",
    "unique_numbers": "Уникални числа",
    "unique_help_count": "Уникален принос",
    "coverage": "Покритие",
    "coverage_percent": "Покритие %",
    "covered_count": "Покритие",
    "top10_coverage": "Top 10 покритие",
    "top20_coverage": "Top 20 покритие",
    "top20_numbers_count": "Top 20 числа",
    "repeated_pairs": "Повторени двойки",
    "repeated_triples": "Повторени тройки",
    "max_overlap": "Максимално припокриване",
    "max_overlap_with_other_ticket": "Максимално припокриване",
    "overlap_count": "Брой припокривания",
    "pair": "Двойка",
    "triple": "Тройка",
    "pair_count": "Брой двойки",
    "triple_count": "Брой тройки",

    # Model / scoring columns
    "model": "Модел",
    "model_name": "Модел",
    "source_model": "Източник / модел",
    "best_model": "Най-добър модел",
    "weight": "Тегло",
    "model_weight": "Тегло на модела",
    "weight_percent": "Тегло %",
    "weighted_score": "Претеглена оценка",
    "weighted_score_percent": "Претеглена оценка %",
    "average_score": "Средна оценка",
    "average_step66_score": "Средна Step 66 оценка",
    "score": "Оценка",
    "final_score": "Финална оценка",
    "profile_score": "Профилна оценка",
    "reliability_score": "Оценка за надеждност",
    "consistency_score": "Оценка за постоянство",
    "avg_hits": "Средно познати числа",
    "max_hits": "Макс. познати числа",
    "hit_rate": "Процент познаваемост",
    "hit_rate_1_plus": "1+ познати",
    "hit_rate_2_plus": "2+ познати",
    "hit_rate_3_plus": "3+ познати",
    "hit_rate_4_plus": "4+ познати",
    "frequency": "Честота",
    "frequency_percent": "Честота %",
    "expected_count": "Очакван брой",
    "actual_count": "Реален брой",
    "difference": "Разлика",
    "last_seen": "Последно появяване",
    "draws_since_last_seen": "Тиражи от последно появяване",
    "avg_interval": "Среден интервал",
    "median_interval": "Медианен интервал",
    "max_interval": "Максимален интервал",
    "recent_count": "Скорошна активност",
    "stability": "Стабилност",

    # Pattern / balance columns
    "odd_count": "Нечетни",
    "even_count": "Четни",
    "low_count": "Ниски",
    "high_count": "Високи",
    "number_range": "Диапазон",
    "sum": "Сума",
    "sum_band": "Група по сума",
    "gaps": "Разстояния",
    "longest_consecutive_run": "Най-дълга поредица",
    "consecutive_pairs": "Последователни двойки",
    "pattern_score": "Оценка на структурата",
    "balance_status": "Баланс",
    "number_group": "Група на числото",
}

BG_VALUE_LABELS = {
    "true": "Да",
    "false": "Не",
    "yes": "Да",
    "no": "Не",
    "none": "Няма",
    "missing": "Липсва",
    "ok": "OK",
    "error": "Грешка",
    "planned": "Планирано",
    "manual_preview": "Ръчна проверка",
    "add_draw_pre_save": "Проверка преди запис на тираж",
    "ready_for_next_draw_evaluation": "Готово за следваща проверка",
    "run": "Изпълнение",
    "audit": "Проверка",
    "high": "Високо",
    "medium": "Средно",
    "low": "Ниско",
    "stable": "Стабилно",
    "hot": "Горещо",
    "cold": "Студено",
    "candidate portfolio accepted as improved статистическа референция": "Кандидат портфейлът е приет като подобрена статистическа референция",
    "applied статистическа референция portfolio": "Приложен статистически референтен портфейл",
    "improved статистическа референция": "Подобрена статистическа референция",
}


def _translate_column_name(column: Any) -> Any:
    text = str(column)
    return BG_COLUMN_LABELS.get(text, column)


def _translate_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    raw = value.strip()
    if not raw:
        return value
    key = raw.lower()
    return BG_VALUE_LABELS.get(key, value)



def _v1164_unique_columns(columns):
    seen = {}
    result = []
    for column in columns:
        base = str(column)
        count = seen.get(base, 0) + 1
        seen[base] = count
        result.append(base if count == 1 else f"{base} ({count})")
    return result


def localize_table(data: Any) -> Any:
    """Return a display-only Bulgarian version of common table columns/values.

    The function intentionally does not change source CSV/JSON files. It only adjusts
    what Streamlit shows to the user.
    """
    if data is None:
        return data

    try:
        import pandas as pd  # type: ignore
    except Exception:  # pragma: no cover
        pd = None

    if pd is not None and isinstance(data, pd.DataFrame):
        df = data.copy()
        df = df.rename(columns={column: _translate_column_name(column) for column in df.columns})
        df.columns = _v1164_unique_columns(df.columns)
        try:
            return df.map(_translate_value)
        except AttributeError:  # older pandas
            return df.applymap(_translate_value)

    if isinstance(data, list):
        localized = []
        changed = False
        for item in data:
            if isinstance(item, dict):
                localized.append({_translate_column_name(k): _translate_value(v) for k, v in item.items()})
                changed = True
            else:
                localized.append(item)
        return localized if changed else data

    if isinstance(data, dict):
        return {_translate_column_name(k): _translate_value(v) for k, v in data.items()}

    return data


def install_streamlit_bg_table_patch(st_module: Any | None = None) -> None:
    """Patch Streamlit table renderers so displayed tables use Bulgarian labels."""
    if st_module is None:
        import streamlit as st_module  # type: ignore

    if getattr(st_module, "_bg_table_patch_installed", False):
        return

    for attr_name in ("dataframe", "table", "data_editor"):
        original = getattr(st_module, attr_name, None)
        if original is None:
            continue

        def make_wrapper(func):
            def wrapper(data=None, *args, **kwargs):
                return func(localize_table(data), *args, **kwargs)
            return wrapper

        setattr(st_module, f"_bg_original_{attr_name}", original)
        setattr(st_module, attr_name, make_wrapper(original))

    setattr(st_module, "_bg_table_patch_installed", True)

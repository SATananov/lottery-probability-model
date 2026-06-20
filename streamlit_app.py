from __future__ import annotations

import csv
import json
import math
import random
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import streamlit as st

# === LOTTERY BULGARIAN UI FINAL CLEAN V36 START ===
# Final Bulgarian display layer. It changes only visible Streamlit text and dataframe headers.
try:
    import inspect as _bg34_inspect
except Exception:  # pragma: no cover
    _bg34_inspect = None


def _bg34_is_bulgarian() -> bool:
    """Use the app language key instead of scanning all session values."""
    try:
        return st.session_state.get("language", "bg") == "bg"
    except Exception:
        return True


_BG34_EXACT = {
    # navigation and page labels
    "Simulation / Simulation": "Симулация",
    "Симулация / Simulation": "Симулация",
    "🎲 Симулация / Simulation": "🎲 Симулация",
    "Dashboard": "Табло",
    "Recommendations": "Препоръки",
    "Combined Model": "Комбиниран модел",
    "Combined model": "Комбиниран модел",
    "Advanced Lab": "Разширена лаборатория",
    "Ticket Analyzer": "Анализ на фиш",
    "Historical Statistics": "Историческа статистика",
    "Probability Lab": "Вероятности",
    "Reports": "Отчети",
    "Report": "Отчет",
    "Update Draws": "Добавяне на тираж",
    "Prediction": "Прогноза",
    "Prediction Engine": "Прогнозен модул",
    "Прогноза": "Прогноза",
    "Прогнозен статистически модул": "Прогнозен статистически модул",
    "Menu": "Меню",
    "Language": "Език",

    # model names and cards
    "Горещ / честотен модел": "Горещ / честотен модел",
    "Hot / frequency model": "Горещ / честотен модел",
    "Hot / frequency": "Горещ / честотен модел",
    "Студен + интервален модел": "Студен + интервален модел",
    "Cold + gap model": "Студен + интервален модел",
    "Cold + gap": "Студен + интервален модел",
    "Среден / балансиран модел": "Среден / балансиран модел",
    "Среден / балансиран модел": "Среден / балансиран модел",
    "Middle / balanced model": "Среден / балансиран модел",
    "Middle / balanced": "Среден / балансиран модел",
    "Интервален модел": "Интервален модел",
    "Gap / interval model": "Интервален модел",
    "Gap / interval": "Интервален модел",
    "Финален комбиниран модел": "Финален комбиниран модел",
    "Финален комбиниран модел": "Финален комбиниран модел",
    "Финален комбиниран модел модел": "Финален комбиниран модел",
    "Разширен ансамбъл": "Разширен ансамбъл",
    "Разширен ансамблов модел": "Разширен ансамблов модел",
    "Разширен ансамбъл модел": "Разширен ансамблов модел",
    "Frequency stability": "Честотна стабилност",
    "frequency_stability": "Честотна стабилност",
    "Случайно генерирана комбинация": "Случайно генерирана комбинация",
    "Best combined recommendation": "Най-добра комбинирана препоръка",
    "Recommendations from all models": "Препоръки от всички модели",
    "Топ препоръки": "Топ препоръки",
    "Диверсифицирано портфолио": "Диверсифицирано портфолио",
    "Проверка за честност / хи-квадрат check": "Проверка за честност / хи-квадрат",
    "Проверка за честност / хи-квадрат test": "Проверка за честност / хи-квадрат",
    "Проверка за честност / хи-квадрат проверка": "Проверка за честност / хи-квадрат",
    "Historical check": "Историческа проверка",
    "Run historical check": "Пусни историческа проверка",

    # simulation / analyzer
    "Монте Карло": "Монте Карло",
    "Историческа проверка": "Историческа проверка",
    "Исторически replay": "Историческа проверка",
    "Check my ticket": "Провери моя фиш",
    "Virtual draw": "Виртуален тираж",
    "Compare with models": "Сравни с моделите",
    "Generate model numbers": "Генерирай моделни числа",
    "Generate model tickets": "Генерирай моделни фишове",
    "Риск от човешки шаблон": "Риск от човешки шаблон",
    "Human-pattern risk": "Риск от човешки шаблон",
    "Човешки риск": "Човешки риск",
    "Подкрепа по двойки": "Подкрепа по двойки",
    "Подкрепа по тройки": "Подкрепа по тройки",
    "Structure": "Структура",
    "Number-by-number": "Число по число",
    "Model analysis": "Анализ по модели",
    "Model score": "Моделна оценка",
    "Model confidence": "Моделна оценка",
    "Относителна моделна вероятност": "Относителна моделна вероятност",
    "относителна оценка": "относителна оценка",
    "Low / Low": "Нисък",
    "Нисък / Low": "Нисък",
    "Medium / Medium": "Среден",
    "Среден / Medium": "Среден",
    "High / High": "Висок",
    "Висок / High": "Висок",

    # reports and historical checking
    "Backtesting": "Историческа проверка",
    "backtesting": "историческа проверка",
    "Backtest": "Историческа проверка",
    "backtest": "историческа проверка",
    "Report from backtesting": "Отчет от историческа проверка",
    "Отчет от backtesting": "Отчет от историческа проверка",
    "Advanced backtesting engine": "Разширен модул за историческа проверка",
    "Recent tested draws": "Последни тествани тиражи",
    "Tested draws": "Тествани тиражи",
    "Best strategy": "Най-добра стратегия",
    "Average matches": "Средни съвпадения",
    "Редове за преглед": "Редове за преглед",
    "Download report": "Свали отчета",
    "Download full report": "Свали пълния отчет",
    "Report written to": "Отчетът е записан в",
    "Not proof": "Не е доказателство",

    # probability and dataframe columns
    "Общ брой комбинации C(49, 6)": "Общ брой комбинации C(49, 6)",
    "Real exact-combination odds": "Реален шанс за точна комбинация",
    "Real chance for exact combination": "Реален шанс за точна комбинация",
    "Real 6/6 odds": "Реален шанс 6/6",
    "matches": "Съвпадения",
    "Matches": "Съвпадения",
    "probability_%": "Вероятност %",
    "Probability %": "Вероятност %",
    "1_in": "1 към",
    "number": "Число",
    "Number": "Число",
    "count": "Брой",
    "Count": "Брой",
    "empirical_%": "Емпиричен %",
    "Empirical %": "Емпиричен %",
    "expected_%": "Очакван %",
    "Expected %": "Очакван %",
    "z_score": "Z-score",
    "Z-score": "Z-score",
    "gap": "Интервал",
    "Gap": "Интервал",
    "avg_interval": "Среден интервал",
    "Avg interval": "Среден интервал",
    "current_gap": "Текущ интервал",
    "Current gap": "Текущ интервал",
    "gap_ratio": "Коефициент на интервал",
    "Gap ratio": "Коефициент на интервал",
    "category": "Категория",
    "Category": "Категория",
    "status": "Статус",
    "Status": "Статус",
    "times_drawn": "Появявания",
    "Times drawn": "Появявания",
    "Draw": "Тираж",
    "Actual": "Реални числа",
    "Actual numbers": "Реални числа",
    "Advanced": "Разширен модел",
    "Advanced ticket": "Фиш на разширения модел",
    "Advanced фиш": "Фиш на разширения модел",
    "Advanced matches": "Съвпадения на разширения модел",
    "Advanced съвпадения": "Съвпадения на разширения модел",
    "Random": "Случаен модел",
    "Random ticket": "Случаен фиш",
    "Random фиш": "Случаен фиш",
    "Random matches": "Съвпадения на случаен фиш",
    "Random съвпадения": "Съвпадения на случаен фиш",
    "Strategy": "Стратегия",
    "Code": "Код",
    "Average": "Средно",
    "Mean matches": "Средни съвпадения",
    "Percent": "Процент",
    "Score": "Оценка",
    "Hot": "Горещ сигнал",
    "Cold+Gap": "Студен + интервал",
    "Middle": "Баланс",
    "Pair": "Двойки",
    "Triple": "Тройки",
    "Sum": "Сума",
    "Odd/Even": "Нечетни/четни",
    "Low/Mid/High": "Ниски/средни/високи",

    # update / upload
    "Upload": "Качи файл",
    "Browse files": "Избери файл",
    "Drag and drop file here": "Пусни файла тук",
    "Limit 200MB per file": "Лимит 200MB на файл",
    "Upload draw": "Качи тираж",
    "Upload draw from file": "Качи тираж от файл",
    "Date": "Дата",
    "Draw date": "Дата на теглене",
    "Year": "Година",
    "Draw number": "Номер на тираж",
    "Draw position": "Позиция на теглене",
    "Position / draw": "Позиция / теглене",
    "Numbers": "Числа",
    "Source / note": "Източник / бележка",
    "Source / note / URL": "Източник / бележка / URL",
    "Ръчно въвеждане": "Ръчно въвеждане",
    "Save new draw": "Запази новия тираж",
    "Delete year": "Година за изтриване",
    "Delete draw number": "Номер на тираж за изтриване",
    "Delete position": "Позиция за изтриване",
    "Delete selected draw": "Изтрий избрания тираж",
    "Delete specific draw": "Изтрий конкретен тираж",
    "Correction / delete draw": "Корекция / изтриване на тираж",
    "Automatically retrain models after saving": "Автоматично обнови моделите след запис",
    "Refresh data": "Обнови данните",
    "Retraining models...": "Моделите се обновяват...",
    "Refresh the page to see updated recommendations.": "Обнови страницата, за да видиш новите препоръки.",
    "No matching draw found.": "Не е намерен такъв тираж.",
    "Could not detect exactly 6 unique valid numbers.": "Не успях да разчета точно 6 различни валидни числа.",
    "This year + draw number + position already exists.": "Тази година + номер на тираж + позиция вече съществува.",
    "Detected numbers": "Разчетени числа",
    "Saved draw": "Записан тираж",
    "Deleted draw": "Изтрит тираж",
    "Backup": "Резервно копие",
    "Restored backup": "Възстановено резервно копие",

    # model file labels shown in cards
    "models/lottery_advanced_ensemble_model.json": "Разширен ансамблов модел",
    "models/lottery_combined_model.json": "Финален комбиниран модел",
    "models/lottery_frequency_model.json": "Горещ / честотен модел",
    "models/lottery_cold_model.json": "Студен + интервален модел",
    "models/lottery_middle_model.json": "Среден / балансиран модел",
    "models/lottery_gap_model.json": "Интервален модел",
    "lottery_advanced_ensemble_model.json": "Разширен ансамблов модел",
    "lottery_combined_model.json": "Финален комбиниран модел",
    "lottery_frequency_model.json": "Горещ / честотен модел",
    "lottery_cold_model.json": "Студен + интервален модел",
    "lottery_middle_model.json": "Среден / балансиран модел",
    "lottery_gap_model.json": "Интервален модел",

    # generic widget text
    "Choose options": "Избери числа",
    "Choose an option": "Избери опция",
    "No options to select.": "Няма опции за избор.",
    "You can only select up to 6 options. Remove an option first.": "Можеш да избереш най-много 6 числа. Премахни едно число първо.",
    "This is a statistical ranking, not a guaranteed prediction.": "Това е статистическо класиране, не сигурно предсказване.",
    "No numbers available": "Няма налични числа",
}

_BG34_REPLACE = [
    ("🎲 Симулация / Simulation", "🎲 Симулация"),
    ("Симулация / Simulation", "Симулация"),
    ("Simulation / Simulation", "Симулация"),
    ("Монте Карло", "Монте Карло"),
    ("Историческа проверка", "Историческа проверка"),
    ("Исторически replay", "Историческа проверка"),
    ("Риск от човешки шаблон", "Риск от човешки шаблон"),
    ("Човешки риск", "Човешки риск"),
    ("Нисък / Low", "Нисък"),
    ("Low / Low", "Нисък"),
    ("Среден / Medium", "Среден"),
    ("Medium / Medium", "Среден"),
    ("Висок / High", "Висок"),
    ("High / High", "Висок"),
    ("Горещ / честотен модел", "Горещ / честотен модел"),
    ("Hot / frequency", "Горещ / честотен модел"),
    ("Студен + интервален модел", "Студен + интервален модел"),
    ("Cold + gap", "Студен + интервален модел"),
    ("Среден / балансиран модел", "Среден / балансиран модел"),
    ("Среден / балансиран модел", "Среден / балансиран модел"),
    ("Middle / balanced", "Среден / балансиран модел"),
    ("Интервален модел", "Интервален модел"),
    ("Gap / interval", "Интервален модел"),
    ("Подкрепа по двойки", "Подкрепа по двойки"),
    ("Подкрепа по тройки", "Подкрепа по тройки"),
    ("Относителна моделна вероятност", "Относителна моделна вероятност"),
    ("относителна оценка:", "относителна оценка:"),
    ("относителна оценка=", "относителна оценка="),
    ("Проверка за честност / хи-квадрат check", "Проверка за честност / хи-квадрат"),
    ("Проверка за честност / хи-квадрат test", "Проверка за честност / хи-квадрат"),
    ("Проверка за честност / хи-квадрат проверка", "Проверка за честност / хи-квадрат"),
    ("Historical check", "Историческа проверка"),
    ("Run historical check", "Пусни историческа проверка"),
    ("Отчет от историческа проверка", "Отчет от историческа проверка"),
    ("Отчет от историческа проверка", "Отчет от историческа проверка"),
    ("Advanced backtesting engine", "Разширен модул за историческа проверка"),
    ("историческа проверка", "историческа проверка"),
    ("Историческа проверка", "Историческа проверка"),
    ("историческа проверка", "историческа проверка"),
    ("Историческа проверка", "Историческа проверка"),
    ("Редове за преглед", "Редове за преглед"),
    ("Общ брой комбинации C(49, 6)", "Общ брой комбинации C(49, 6)"),
    ("Случайно генерирана комбинация", "Случайно генерирана комбинация"),
    ("Финален комбиниран модел", "Финален комбиниран модел"),
    ("Финален комбиниран модел модел", "Финален комбиниран модел"),
    ("Финален комбиниран модел", "Финален комбиниран модел"),
    ("Разширен ансамблов модел", "Разширен ансамблов модел"),
    ("Разширен ансамбъл модел", "Разширен ансамблов модел"),
    ("Разширен ансамбъл", "Разширен ансамбъл"),
    ("Most frequent", "Най-често теглени числа"),
    ("Least frequent", "Най-рядко теглени числа"),
    ("models/lottery_advanced_ensemble_model.json", "Разширен ансамблов модел"),
    ("models/lottery_combined_model.json", "Финален комбиниран модел"),
    ("models/lottery_frequency_model.json", "Горещ / честотен модел"),
    ("models/lottery_cold_model.json", "Студен + интервален модел"),
    ("models/lottery_middle_model.json", "Среден / балансиран модел"),
    ("models/lottery_gap_model.json", "Интервален модел"),
    ("lottery_advanced_ensemble_model.json", "Разширен ансамблов модел"),
    ("lottery_combined_model.json", "Финален комбиниран модел"),
    ("lottery_frequency_model.json", "Горещ / честотен модел"),
    ("lottery_cold_model.json", "Студен + интервален модел"),
    ("lottery_middle_model.json", "Среден / балансиран модел"),
    ("lottery_gap_model.json", "Интервален модел"),
    ("probability_%", "Вероятност %"),
    ("1_in", "1 към"),
    ("1 in ", "1 към "),
    ("Choose options", "Избери числа"),
    ("Choose an option", "Избери опция"),
    ("Browse files", "Избери файл"),
    ("Ръчно въвеждане", "Ръчно въвеждане"),
    ("Delete year", "Година за изтриване"),
    ("Delete draw number", "Номер на тираж за изтриване"),
    ("Delete position", "Позиция за изтриване"),
]


def _bg34_text(value):
    if not _bg34_is_bulgarian() or not isinstance(value, str):
        return value
    if value in _BG34_EXACT:
        return _BG34_EXACT[value]
    out = value
    for src, dst in _BG34_REPLACE:
        out = out.replace(src, dst)
    return out


def _bg34_translate_dataframe(data):
    if not _bg34_is_bulgarian() or not isinstance(data, pd.DataFrame):
        return data
    try:
        df = data.copy()
        df = df.rename(columns={col: _bg34_text(str(col)) for col in df.columns})
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].map(lambda x: _bg34_text(x) if isinstance(x, str) else x)
        return df
    except Exception:
        return data


def _bg34_css():
    if not _bg34_is_bulgarian():
        return
    st.markdown("""
<style>
div[data-testid="stFileUploader"] button div p { font-size: 0 !important; }
div[data-testid="stFileUploader"] button div p::after { content: "Качи файл"; font-size: 14px !important; }
div[data-testid="stFileUploader"] small { font-size: 0 !important; }
div[data-testid="stFileUploader"] small::after { content: "до 200MB на файл"; font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)


if not getattr(st, "_lottery_bulgarian_final_clean_v36", False):
    st._lottery_bulgarian_final_clean_v36 = True

    _bg34_orig_markdown = st.markdown
    _bg34_orig_write = st.write
    _bg34_orig_caption = st.caption
    _bg34_orig_info = st.info
    _bg34_orig_success = st.success
    _bg34_orig_warning = st.warning
    _bg34_orig_error = st.error
    _bg34_orig_title = st.title
    _bg34_orig_header = st.header
    _bg34_orig_subheader = st.subheader
    _bg34_orig_metric = st.metric
    _bg34_orig_button = st.button
    _bg34_orig_checkbox = st.checkbox
    _bg34_orig_radio = st.radio
    _bg34_orig_tabs = st.tabs
    _bg34_orig_selectbox = st.selectbox
    _bg34_orig_slider = st.slider
    _bg34_orig_select_slider = st.select_slider
    _bg34_orig_multiselect = st.multiselect
    _bg34_orig_text_input = st.text_input
    _bg34_orig_number_input = st.number_input
    _bg34_orig_file_uploader = st.file_uploader
    _bg34_orig_download_button = st.download_button
    _bg34_orig_dataframe = st.dataframe
    _bg34_orig_table = st.table

    def _bg34_markdown(body, *args, **kwargs):
        return _bg34_orig_markdown(_bg34_text(body), *args, **kwargs)
    def _bg34_write(*args, **kwargs):
        args = tuple(_bg34_text(a) if isinstance(a, str) else a for a in args)
        return _bg34_orig_write(*args, **kwargs)
    def _bg34_caption(body, *args, **kwargs):
        return _bg34_orig_caption(_bg34_text(body), *args, **kwargs)
    def _bg34_info(body, *args, **kwargs):
        return _bg34_orig_info(_bg34_text(body), *args, **kwargs)
    def _bg34_success(body, *args, **kwargs):
        return _bg34_orig_success(_bg34_text(body), *args, **kwargs)
    def _bg34_warning(body, *args, **kwargs):
        return _bg34_orig_warning(_bg34_text(body), *args, **kwargs)
    def _bg34_error(body, *args, **kwargs):
        return _bg34_orig_error(_bg34_text(body), *args, **kwargs)
    def _bg34_title(body, *args, **kwargs):
        return _bg34_orig_title(_bg34_text(body), *args, **kwargs)
    def _bg34_header(body, *args, **kwargs):
        return _bg34_orig_header(_bg34_text(body), *args, **kwargs)
    def _bg34_subheader(body, *args, **kwargs):
        return _bg34_orig_subheader(_bg34_text(body), *args, **kwargs)
    def _bg34_metric(label, value, delta=None, *args, **kwargs):
        return _bg34_orig_metric(_bg34_text(label), _bg34_text(value), _bg34_text(delta), *args, **kwargs)
    def _bg34_button(label, *args, **kwargs):
        return _bg34_orig_button(_bg34_text(label), *args, **kwargs)
    def _bg34_checkbox(label, *args, **kwargs):
        return _bg34_orig_checkbox(_bg34_text(label), *args, **kwargs)
    def _bg34_radio(label, options, *args, **kwargs):
        return _bg34_orig_radio(_bg34_text(label), options, *args, **kwargs)
    def _bg34_tabs(tabs, *args, **kwargs):
        return _bg34_orig_tabs([_bg34_text(t) if isinstance(t, str) else t for t in tabs], *args, **kwargs)
    def _bg34_selectbox(label, options, *args, **kwargs):
        return _bg34_orig_selectbox(_bg34_text(label), options, *args, **kwargs)
    def _bg34_slider(label, *args, **kwargs):
        return _bg34_orig_slider(_bg34_text(label), *args, **kwargs)
    def _bg34_select_slider(label, *args, **kwargs):
        return _bg34_orig_select_slider(_bg34_text(label), *args, **kwargs)
    def _bg34_multiselect(label, options, *args, **kwargs):
        _bg34_css()
        if _bg34_is_bulgarian() and _bg34_inspect is not None:
            try:
                if "placeholder" in _bg34_inspect.signature(_bg34_orig_multiselect).parameters:
                    kwargs.setdefault("placeholder", "Избери числа")
            except Exception:
                pass
        return _bg34_orig_multiselect(_bg34_text(label), options, *args, **kwargs)
    def _bg34_text_input(label, *args, **kwargs):
        if "value" in kwargs and isinstance(kwargs.get("value"), str):
            kwargs["value"] = _bg34_text(kwargs["value"])
        if "placeholder" in kwargs and isinstance(kwargs.get("placeholder"), str):
            kwargs["placeholder"] = _bg34_text(kwargs["placeholder"])
        return _bg34_orig_text_input(_bg34_text(label), *args, **kwargs)
    def _bg34_number_input(label, *args, **kwargs):
        return _bg34_orig_number_input(_bg34_text(label), *args, **kwargs)
    def _bg34_file_uploader(label, *args, **kwargs):
        _bg34_css()
        return _bg34_orig_file_uploader(_bg34_text(label), *args, **kwargs)
    def _bg34_download_button(label, *args, **kwargs):
        return _bg34_orig_download_button(_bg34_text(label), *args, **kwargs)
    def _bg34_dataframe_widget(data=None, *args, **kwargs):
        return _bg34_orig_dataframe(_bg34_translate_dataframe(data), *args, **kwargs)
    def _bg34_table_widget(data=None, *args, **kwargs):
        return _bg34_orig_table(_bg34_translate_dataframe(data), *args, **kwargs)

    st.markdown = _bg34_markdown
    st.write = _bg34_write
    st.caption = _bg34_caption
    st.info = _bg34_info
    st.success = _bg34_success
    st.warning = _bg34_warning
    st.error = _bg34_error
    st.title = _bg34_title
    st.header = _bg34_header
    st.subheader = _bg34_subheader
    st.metric = _bg34_metric
    st.button = _bg34_button
    st.checkbox = _bg34_checkbox
    st.radio = _bg34_radio
    st.tabs = _bg34_tabs
    st.selectbox = _bg34_selectbox
    st.slider = _bg34_slider
    st.select_slider = _bg34_select_slider
    st.multiselect = _bg34_multiselect
    st.text_input = _bg34_text_input
    st.number_input = _bg34_number_input
    st.file_uploader = _bg34_file_uploader
    st.download_button = _bg34_download_button
    st.dataframe = _bg34_dataframe_widget
    st.table = _bg34_table_widget
# === LOTTERY BULGARIAN UI FINAL CLEAN V34 END ===


# === LOTTERY REPORTS VISUAL CLEAN V34 START ===
# Visual Bulgarian renderer for advanced historical-check reports.
try:
    import re as _lr34_re
except Exception:  # pragma: no cover
    _lr34_re = None


def _lr34_nums(raw):
    numbers = []
    for token in str(raw or "").replace(",", " ").split():
        token = "".join(ch for ch in token if ch.isdigit())
        if token:
            try:
                numbers.append(int(token))
            except Exception:
                pass
    return numbers


def _lr34_balls(numbers, size=34):
    parts = ["<div style='display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0 8px;'>"]
    for n in numbers or []:
        parts.append(
            "<span style='display:inline-flex;align-items:center;justify-content:center;"
            f"width:{size}px;height:{size}px;border-radius:999px;"
            "background:radial-gradient(circle at 35% 25%, #fff4b8, #d4af37 48%, #8b6b18 100%);"
            "color:#111;font-weight:800;font-size:14px;"
            "border:1px solid rgba(255,255,255,.45);"
            "box-shadow:0 6px 18px rgba(212,175,55,.18);'>"
            f"{n}</span>"
        )
    parts.append("</div>")
    _lr34_original_markdown("".join(parts), unsafe_allow_html=True)


def _lr34_strategy_label(name):
    labels = {
        "advanced": "Разширен ансамбъл",
        "time_decay": "Модел с времево затихване",
        "bayesian": "Бейсово изглаждане",
        "gap": "Интервален модел",
        "frequency_stability": "Честотна стабилност",
        "random": "Случаен базов модел",
    }
    return labels.get(str(name), str(name).replace("_", " "))


def _lr34_parse_strategy_rows(text_value):
    if not _lr34_re:
        return []
    rows = []
    pattern = _lr34_re.compile(r"^\s*([A-Za-z_]+):\s*avg=([0-9.]+),\s*>=3=([0-9.]+)%,\s*>=4=([0-9.]+)%", _lr34_re.M)
    for name, avg, ge3, ge4 in pattern.findall(text_value):
        rows.append({
            "Стратегия": _lr34_strategy_label(name),
            "Средни съвпадения": float(avg),
            ">=3 съвпадения %": float(ge3),
            ">=4 съвпадения %": float(ge4),
        })
    return rows


def _lr34_parse_recent_draws(text_value):
    if not _lr34_re:
        return []
    rows = []
    pattern = _lr34_re.compile(
        r"Draw\s+(\d+)\s*\(([^)]*)\):\s*"
        r"actual=\[([^\]]*)\],\s*"
        r"advanced=\[([^\]]*)\]\s*\((\d+)\s+matches?\),\s*"
        r"random=\[([^\]]*)\]\s*\((\d+)\s+matches?\)",
        _lr34_re.I,
    )
    for draw, date_value, actual, advanced, adv_matches, random_ticket, rnd_matches in pattern.findall(text_value):
        rows.append({
            "Тираж": int(draw),
            "Дата": date_value.strip() or "-",
            "Реални числа": _lr34_nums(actual),
            "Фиш на разширения модел": _lr34_nums(advanced),
            "Съвпадения на разширения модел": int(adv_matches),
            "Случаен фиш": _lr34_nums(random_ticket),
            "Съвпадения на случаен фиш": int(rnd_matches),
        })
    return rows


def _lr34_render_report(text_value):
    if not isinstance(text_value, str):
        return False
    if "actual=[" not in text_value and "Recent tested draws" not in text_value and "Advanced backtesting engine" not in text_value:
        return False

    _lr34_original_markdown("## Отчет от историческа проверка")
    tested = None
    best_strategy = None
    if _lr34_re:
        tested_match = _lr34_re.search(r"Tested draws:\s*(\d+)", text_value)
        best_match = _lr34_re.search(r"Best strategy:\s*([A-Za-z_]+)", text_value)
        if tested_match:
            tested = int(tested_match.group(1))
        if best_match:
            best_strategy = best_match.group(1)

    cols = st.columns(3)
    cols[0].metric("Тествани тиражи", tested if tested is not None else "-")
    cols[1].metric("Най-добра стратегия", _lr34_strategy_label(best_strategy) if best_strategy else "-")
    cols[2].metric("Важно", "Не е доказателство", help="Историческата проверка гледа назад във времето и не гарантира бъдещи резултати.")

    strategy_rows = _lr34_parse_strategy_rows(text_value)
    if strategy_rows:
        _lr34_original_markdown("### Сравнение на стратегиите")
        strategy_df = pd.DataFrame(strategy_rows)
        st.dataframe(strategy_df, width="stretch", hide_index=True)
        try:
            st.bar_chart(strategy_df.set_index("Стратегия")[["Средни съвпадения"]], height=260)
        except Exception:
            pass

    if best_strategy:
        st.info(
            f"Най-добрата стратегия в тази историческа проверка е: {_lr34_strategy_label(best_strategy)}. "
            "Това е проверка на модела, не доказателство, че бъдещи тегления са предсказуеми."
        )

    recent_rows = _lr34_parse_recent_draws(text_value)
    if recent_rows:
        _lr34_original_markdown("### Последни тествани тиражи")
        table_rows = []
        for row in recent_rows:
            table_rows.append({
                "Тираж": row["Тираж"],
                "Дата": row["Дата"],
                "Реални числа": ", ".join(map(str, row["Реални числа"])),
                "Фиш на разширения модел": ", ".join(map(str, row["Фиш на разширения модел"])),
                "Съвпадения на разширения модел": row["Съвпадения на разширения модел"],
                "Случаен фиш": ", ".join(map(str, row["Случаен фиш"])),
                "Съвпадения на случаен фиш": row["Съвпадения на случаен фиш"],
            })
        st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)

        with st.expander("Виж последните тиражи визуално", expanded=False):
            for row in recent_rows[:20]:
                _lr34_original_markdown(f"#### Тираж {row['Тираж']} {'' if row['Дата'] == '-' else row['Дата']}")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.caption("Реални числа")
                    _lr34_balls(row["Реални числа"])
                with c2:
                    st.caption(f"Фиш на разширения модел — {row['Съвпадения на разширения модел']} съвпадения")
                    _lr34_balls(row["Фиш на разширения модел"])
                with c3:
                    st.caption(f"Случаен фиш — {row['Съвпадения на случаен фиш']} съвпадения")
                    _lr34_balls(row["Случаен фиш"])
                st.divider()

    st.download_button("Свали оригиналния отчет", data=text_value, file_name="advanced_backtest_report.md", mime="text/markdown")
    return True


if not getattr(st, "_lottery_reports_visual_clean_v34", False):
    st._lottery_reports_visual_clean_v34 = True
    _lr34_original_markdown = st.markdown
    _lr34_original_write = st.write
    _lr34_original_code = st.code

    def _lr34_markdown(body, *args, **kwargs):
        try:
            if isinstance(body, str) and _lr34_render_report(body):
                return
        except Exception:
            pass
        return _lr34_original_markdown(body, *args, **kwargs)

    def _lr34_write(*args, **kwargs):
        try:
            if len(args) == 1 and isinstance(args[0], str) and _lr34_render_report(args[0]):
                return
        except Exception:
            pass
        return _lr34_original_write(*args, **kwargs)

    def _lr34_code(body, *args, **kwargs):
        try:
            if isinstance(body, str) and _lr34_render_report(body):
                return
        except Exception:
            pass
        return _lr34_original_code(body, *args, **kwargs)

    st.markdown = _lr34_markdown
    st.write = _lr34_write
    st.code = _lr34_code
# === LOTTERY REPORTS VISUAL CLEAN V34 END ===


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "historical_draws.csv"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
BACKUP_DIR = ROOT / "data" / "manual_backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

THEORETICAL_ODDS_TEXT = "1 към 13,983,816"
EXPECTED_NUMBER_PROB = 6 / 49

TRANSLATIONS = {
    "bg": {
        "language": "Език",
        "app_title": "Лотарийна статистическа лаборатория 6/49",
        "app_caption": "Анализ, модели, историческа проверка и визуални препоръки. Не гарантира печалба.",
        "menu": "Меню",
        "dashboard": "Табло",
        "recommendations": "Препоръки",
        "combined": "Комбиниран модел",
        "advanced_lab": "Разширена лаборатория",
        "ml_lab": "МЛ лаборатория",
        "ml_extensions": "МЛ разширения: класификация, клъстери и 2D карта",
        "prediction": "Прогноза",
        "ticket_analyzer": "Анализ на фиш",
        "history": "Историческа статистика",
        "probability_lab": "Вероятности",
        "reports": "Отчети",
        "update_draws": "Добавяне на тираж",
        "draws": "Тегления",
        "years": "Години",
        "missing": "Липсващи години",
        "duplicates": "Дубликати",
        "main_recommendation": "Основна препоръка",
        "model_score": "Моделна оценка",
        "real_odds": "Реален шанс за точна комбинация",
        "not_prediction": "Това е статистическо класиране, не сигурно предсказване.",
        "top_recommendations": "Топ препоръки",
        "all_models": "Препоръки от всички модели",
        "hot_model": "Горещ / честотен модел",
        "cold_model": "Студен + интервален модел",
        "middle_model": "Среден / балансиран модел",
        "gap_model": "Интервален модел",
        "combined_model": "Финален комбиниран модел",
        "advanced_model": "Разширен ансамблов модел",
        "train_advanced": "Обучи разширения ансамбъл",
        "run_backtest": "Пусни историческа проверка",
        "no_model": "Моделът още не е наличен. Пусни скрипта за обучение.",
        "numbers": "Числа",
        "confidence": "Оценка",
        "rank": "Ранг",
        "details": "Детайли",
        "refresh": "Обнови данните",
        "select_numbers": "Избери 6 числа",
        "analyze_ticket": "Анализирай фиша",
        "ticket_warning": "Избери точно 6 различни числа от 1 до 49.",
        "save_draw": "Запази новия тираж",
        "auto_retrain": "Автоматично обнови моделите след запис",
        "year": "Година",
        "draw_number": "Номер на тираж",
        "draw_position": "Позиция / теглене",
        "draw_date": "Дата",
        "source": "Източник / бележка",
        "upload_draw": "Качи тираж от файл",
        "upload_button": "Разчети качения файл",
        "delete_draw": "Изтрий конкретен тираж",
        "undo": "Върни последната ръчна промяна",
        "retrain_log": "Лог от обновяване на моделите",
        "portfolio": "Диверсифицирано портфолио",
        "fairness": "Проверка за честност / хи-квадрат",
        "backtest": "Историческа проверка",
        "status_hot": "Горещо",
        "status_cold": "Студено",
        "status_middle": "Балансирано",
        "status_overdue": "Отдавна не е излизало",
        "term_help": "Речник",
    },
    "en": {
        "language": "Language",
        "app_title": "Lottery Statistical Laboratory 6/49",
        "app_caption": "Analysis, models, backtesting and visual recommendations. It does not guarantee a win.",
        "menu": "Menu",
        "dashboard": "Dashboard",
        "recommendations": "Recommendations",
        "combined": "Combined Model",
        "advanced_lab": "Advanced Lab",
        "ml_lab": "ML Laboratory",
        "ml_extensions": "ML extensions: classification, clusters and 2D map",
        "prediction": "Prediction",
        "ticket_analyzer": "Ticket Analyzer",
        "history": "Historical Statistics",
        "probability_lab": "Probability Lab",
        "reports": "Reports",
        "update_draws": "Update Draws",
        "draws": "Draws",
        "years": "Years",
        "missing": "Missing years",
        "duplicates": "Duplicates",
        "main_recommendation": "Main recommendation",
        "model_score": "Model score",
        "real_odds": "Real odds for exact combination",
        "not_prediction": "This is a statistical ranking, not a guaranteed prediction.",
        "top_recommendations": "Top recommendations",
        "all_models": "Recommendations from all models",
        "hot_model": "Hot / frequency model",
        "cold_model": "Cold + gap model",
        "middle_model": "Middle / balanced model",
        "gap_model": "Gap / interval model",
        "combined_model": "Final combined model",
        "advanced_model": "Advanced ensemble model",
        "train_advanced": "Train advanced ensemble",
        "run_backtest": "Run backtest",
        "no_model": "Model not available yet. Run the training script.",
        "numbers": "Numbers",
        "confidence": "Score",
        "rank": "Rank",
        "details": "Details",
        "refresh": "Refresh data",
        "select_numbers": "Select 6 numbers",
        "analyze_ticket": "Analyze ticket",
        "ticket_warning": "Choose exactly 6 unique numbers from 1 to 49.",
        "save_draw": "Save new draw",
        "auto_retrain": "Automatically retrain models after saving",
        "year": "Year",
        "draw_number": "Draw number",
        "draw_position": "Position / draw",
        "draw_date": "Date",
        "source": "Source / note",
        "upload_draw": "Upload draw from file",
        "upload_button": "Read uploaded file",
        "delete_draw": "Delete selected draw",
        "undo": "Undo last manual change",
        "retrain_log": "Retraining log",
        "portfolio": "Diversified portfolio",
        "fairness": "Fairness / chi-square test",
        "backtest": "Backtesting",
        "status_hot": "Hot",
        "status_cold": "Cold",
        "status_middle": "Balanced",
        "status_overdue": "Overdue",
        "term_help": "Glossary",
    },
}

st.set_page_config(
    page_title="Lottery 6/49 Lab",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# V15_HIDE_NATIVE_STREAMLIT_NAV_START
try:
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        [data-testid="stSidebarNavItems"] {display: none !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )
except Exception:
    pass
# V15_HIDE_NATIVE_STREAMLIT_NAV_END


# V13_SIMULATION_LAB_HOOK_START
try:
    from streamlit_pages.simulation_lab_page import render_simulation_lab_page as _render_v13_simulation_lab_page
except Exception as _v13_simulation_import_error:
    _render_v13_simulation_lab_page = None
else:
    _v13_simulation_import_error = None


def _v13_sidebar_button(label: str, key: str) -> bool:
    try:
        return st.sidebar.button(label, width="stretch", key=key)
    except TypeError:
        return st.sidebar.button(label, width="stretch", key=key)


def _v13_simulation_lab_hook() -> None:
    if "v13_simulation_lab_active" not in st.session_state:
        st.session_state["v13_simulation_lab_active"] = False

    st.sidebar.markdown("---")
    if _v13_sidebar_button("🎲 Симулация", "v13_open_simulation_lab"):
        st.session_state["v13_simulation_lab_active"] = True
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

    if st.session_state.get("v13_simulation_lab_active"):
        if _v13_sidebar_button("← Назад към основното меню", "v13_close_simulation_lab"):
            st.session_state["v13_simulation_lab_active"] = False
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()

        if _render_v13_simulation_lab_page is None:
            st.error("Симулационната лаборатория не може да бъде заредена.")
            st.exception(_v13_simulation_import_error)
        else:
            _render_v13_simulation_lab_page()
        st.stop()


_v13_simulation_lab_hook()
# V13_SIMULATION_LAB_HOOK_END


st.markdown(
    """
    <style>
    :root {
      --bg-card: rgba(18, 18, 20, 0.78);
      --border-gold: rgba(212, 175, 55, 0.48);
      --gold: #D4AF37;
      --ivory: #F8F5EF;
      --muted: rgba(248,245,239,0.68);
      --danger: #ff6b6b;
      --ok: #7bd88f;
    }
    .main .block-container { padding-top: 1.2rem; padding-bottom: 3rem; }
    .hero-box {
      border: 1px solid var(--border-gold);
      border-radius: 22px;
      padding: 22px 24px;
      background: radial-gradient(circle at top left, rgba(212,175,55,0.15), rgba(14,14,16,0.88) 42%, rgba(14,14,16,0.96));
      box-shadow: 0 20px 70px rgba(0,0,0,0.35);
      margin-bottom: 18px;
    }
    .hero-title { font-size: 2.1rem; line-height: 1.1; font-weight: 800; color: var(--ivory); margin: 0; }
    .hero-subtitle { color: var(--muted); margin-top: 8px; font-size: 1.02rem; }
    .model-card {
      border: 1px solid rgba(212,175,55,0.34);
      background: linear-gradient(145deg, rgba(20,20,23,0.94), rgba(5,5,7,0.98));
      border-radius: 20px;
      padding: 18px 18px 16px;
      margin: 10px 0 16px;
      box-shadow: 0 16px 42px rgba(0,0,0,0.28);
    }
    .model-title { color: var(--gold); font-size: 1.12rem; font-weight: 800; margin-bottom: 8px; }
    .model-meta { color: var(--muted); font-size: .92rem; margin-bottom: 8px; }
    .number-row { display: flex; flex-wrap: wrap; gap: 9px; margin: 12px 0; }
    .number-pill {
      min-width: 44px; height: 44px; border-radius: 999px;
      display: inline-flex; align-items:center; justify-content:center;
      font-weight: 800; color: #0E0E10;
      background: linear-gradient(180deg, #f7df84, #d4af37 56%, #8d6f1b);
      border: 1px solid rgba(255,255,255,0.28);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.4), 0 8px 20px rgba(212,175,55,0.18);
      letter-spacing: .01em;
    }
    .rank-card {
      border: 1px solid rgba(255,255,255,0.09);
      border-radius: 16px;
      padding: 14px 14px 12px;
      background: rgba(255,255,255,0.035);
      margin: 8px 0;
    }
    .score-badge {
      display: inline-block;
      padding: 5px 10px;
      border-radius: 999px;
      border: 1px solid rgba(212,175,55,0.4);
      color: var(--ivory);
      background: rgba(212,175,55,0.11);
      font-size: .88rem;
      margin-right: 6px;
    }
    .warning-soft {
      border-left: 3px solid var(--gold);
      background: rgba(212,175,55,0.08);
      border-radius: 12px;
      padding: 11px 13px;
      color: var(--muted);
      margin: 10px 0 14px;
    }
    .small-muted { color: var(--muted); font-size: .9rem; }
    .ok-text { color: var(--ok); font-weight: 700; }
    .danger-text { color: var(--danger); font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)


def language() -> str:
    default_lang = st.session_state.get("language", "bg")
    return st.sidebar.radio(
        TRANSLATIONS[default_lang]["language"],
        options=["bg", "en"],
        index=0 if default_lang == "bg" else 1,
        format_func=lambda value: "Български" if value == "bg" else "English",
        key="language",
    )


LANG = language()
T = TRANSLATIONS[LANG]


def tr(key: str) -> str:
    return T.get(key, key)


@st.cache_data(show_spinner=False)
def load_draws() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    for col in ["year", "draw_number", "draw_position", "n1", "n2", "n3", "n4", "n5", "n6"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


@st.cache_data(show_spinner=False)
def load_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf-8-sig") as file:
            return json.load(file)
    except Exception:
        return {}


def model_json(filename: str) -> Dict[str, Any]:
    return load_json(str(MODELS_DIR / filename))


def numbers_from_row(row: pd.Series) -> List[int]:
    nums = []
    for col in ["n1", "n2", "n3", "n4", "n5", "n6"]:
        if col in row and pd.notna(row[col]):
            nums.append(int(row[col]))
    return nums


def format_number_pills(numbers: Iterable[Any]) -> str:
    clean = []
    for number in numbers or []:
        try:
            clean.append(int(number))
        except Exception:
            pass
    clean = sorted(clean)
    if not clean:
        return '<div class="small-muted">Няма налични числа</div>'
    return '<div class="number-row">' + ''.join(f'<span class="number-pill">{n}</span>' for n in clean) + '</div>'


def render_ticket_card(title: str, numbers: List[int], score: Optional[float] = None, meta: str = "", explanation: str = "") -> None:
    score_html = ""
    if score is not None:
        try:
            score_html = f'<span class="score-badge">{tr("model_score")}: {float(score):.2f}/100</span>'
        except Exception:
            score_html = f'<span class="score-badge">{tr("model_score")}: {score}</span>'
    st.markdown(
        f"""
        <div class="model-card">
          <div class="model-title">{title}</div>
          <div class="model-meta">{meta}</div>
          {format_number_pills(numbers)}
          <div>{score_html}<span class="score-badge">{tr("real_odds")}: {THEORETICAL_ODDS_TEXT}</span></div>
          <div class="small-muted" style="margin-top:10px;">{explanation or tr("not_prediction")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_recommendation_list(title: str, recs: List[Dict[str, Any]], limit: int = 10) -> None:
    st.markdown(f"### {title}")
    if not recs:
        st.info(tr("no_model"))
        return
    for idx, item in enumerate(recs[:limit], start=1):
        numbers = item.get("numbers") or item.get("combination") or item.get("ticket") or []
        score = (
            item.get("confidence_score")
            or item.get("confidence")
            or item.get("final_score")
            or item.get("prediction_score")
            or item.get("score")
        )
        rank = item.get("rank") or item.get("относителна оценка_rank") or idx
        rel_prob = item.get("относителна оценка_model_probability") or item.get("относителна оценка_probability")
        meta_parts = []
        if score is not None:
            try:
                meta_parts.append(f'{tr("confidence")}: {float(score):.2f}/100')
            except Exception:
                meta_parts.append(f'{tr("confidence")}: {score}')
        if rel_prob is not None:
            try:
                meta_parts.append(f"относителна оценка: {float(rel_prob):.6f}%")
            except Exception:
                meta_parts.append(f"относителна оценка: {rel_prob}")
        meta = " · ".join(meta_parts)
        st.markdown(
            f"""
            <div class="rank-card">
              <div class="model-title">{tr("rank")} {rank}</div>
              {format_number_pills(numbers)}
              <div class="small-muted">{meta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def extract_single_ticket(model: Dict[str, Any]) -> List[int]:
    if not model:
        return []
    for key in [
        "recommended_ticket",
        "recommended_numbers",
        "ticket",
        "numbers",
        "combination",
        "recommended_gap_ticket",
        "recommended_cold_ticket",
        "recommended_middle_ticket",
        "recommended_hot_ticket",
    ]:
        value = model.get(key)
        if isinstance(value, list) and len(value) >= 6:
            return sorted([int(v) for v in value[:6]])
    # Fallback: take first 6 numbers from top scored entries.
    for key in [
        "top_numbers",
        "top_scored_numbers",
        "top_underrepresented_numbers",
        "top_balanced_numbers",
        "top_next_draw_probability_numbers",
        "number_scores",
    ]:
        values = model.get(key)
        if isinstance(values, list):
            nums = []
            for item in values:
                if isinstance(item, dict):
                    number = item.get("number") or item.get("n")
                else:
                    number = item[0] if isinstance(item, (list, tuple)) and item else None
                if number is not None:
                    try:
                        nums.append(int(number))
                    except Exception:
                        pass
                if len(nums) == 6:
                    return sorted(nums)
    return []


def extract_recommendations(model: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not model:
        return []
    for key in ["recommended_combinations", "top_predictions", "portfolio_predictions", "top_recommendations", "recommendations", "top_combinations"]:
        value = model.get(key)
        if isinstance(value, list):
            result = []
            for idx, item in enumerate(value, start=1):
                if isinstance(item, dict):
                    normalized = dict(item)
                else:
                    normalized = {"numbers": item}
                normalized.setdefault("rank", idx)
                result.append(normalized)
            return result
    ticket = extract_single_ticket(model)
    if ticket:
        return [{"rank": 1, "numbers": ticket, "confidence_score": model.get("confidence_score") or model.get("score")}]
    return []


def main_recommendation(model: Dict[str, Any]) -> Tuple[List[int], Optional[float]]:
    recs = extract_recommendations(model)
    if recs:
        item = recs[0]
        numbers = item.get("numbers") or item.get("combination") or item.get("ticket") or []
        score = item.get("confidence_score") or item.get("confidence") or item.get("final_score") or item.get("prediction_score") or item.get("score")
        return sorted([int(x) for x in numbers]) if numbers else [], score
    return extract_single_ticket(model), model.get("confidence_score") or model.get("score") if model else None


def get_model_cards() -> List[Tuple[str, str, str, str]]:
    return [
        (tr("advanced_model"), "lottery_advanced_ensemble_model.json", "advanced", "Комбинира времево затихване, бейсово изглаждане, проверка за честност, съвместна поява, портфолио и историческа проверка."),
        (tr("ml_extensions") if "ml_extensions" in T else "МЛ разширения: класификация, клъстери и 2D карта", "lottery_ml_extensions_model.json", "ml_extensions", "Добавя класификация, клъстеризация, редукция на размерността и карта на модела и допълнителна историческа проверка."),
        ("Прогнозен статистически модул", "lottery_prediction_model.json", "prediction", "Обобщава всички налични сигнали в статистическа прогноза за следващ неизвестен тираж. Не е гаранция."),
        (tr("combined_model"), "lottery_combined_model.json", "combined", "Финално претеглено класиране от основните модели."),
        (tr("hot_model"), "lottery_frequency_model.json", "hot", "Числа с по-силен исторически честотен сигнал."),
        (tr("cold_model"), "lottery_cold_model.json", "cold", "Числа, повлияни от по-слаба представеност и текущ интервал."),
        (tr("middle_model"), "lottery_middle_model.json", "middle", "Числа близо до очакваната честота и балансирано поведение."),
        (tr("gap_model"), "lottery_gap_model.json", "gap", "Числа с по-силен интервален сигнал."),
    ]


def get_dataset_metrics() -> Dict[str, Any]:
    df = load_draws()
    if df.empty:
        return {"rows": 0, "year_min": None, "year_max": None, "missing": [], "dup_full": 0, "dup_keys": 0}
    years = sorted(df["year"].dropna().astype(int).unique().tolist()) if "year" in df.columns else []
    missing = [y for y in range(1958, 2026) if y not in years]
    key_cols = [c for c in ["year", "draw_number", "draw_position"] if c in df.columns]
    num_cols = [c for c in ["n1", "n2", "n3", "n4", "n5", "n6"] if c in df.columns]
    dup_keys = int(df.duplicated(subset=key_cols).sum()) if key_cols else 0
    dup_full = int(df.duplicated(subset=key_cols + num_cols).sum()) if key_cols and num_cols else 0
    return {
        "rows": len(df),
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "missing": missing,
        "dup_full": dup_full,
        "dup_keys": dup_keys,
    }


def render_header() -> None:
    st.markdown(
        f"""
        <div class="hero-box">
          <div class="hero-title">🎯 {tr("app_title")}</div>
          <div class="hero-subtitle">{tr("app_caption")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_dashboard() -> None:
    render_header()
    metrics = get_dataset_metrics()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(tr("draws"), f'{metrics["rows"]:,}')
    col2.metric(tr("years"), f'{metrics["year_min"]}–{metrics["year_max"]}')
    col3.metric(tr("missing"), len(metrics["missing"]))
    col4.metric(tr("duplicates"), metrics["dup_keys"] + metrics["dup_full"])

    st.markdown(f'<div class="warning-soft">{tr("not_prediction")} {tr("real_odds")}: <b>{THEORETICAL_ODDS_TEXT}</b>.</div>', unsafe_allow_html=True)

    advanced = model_json("lottery_advanced_ensemble_model.json")
    combined = model_json("lottery_combined_model.json")
    adv_numbers, adv_score = main_recommendation(advanced)
    comb_numbers, comb_score = main_recommendation(combined)

    c1, c2 = st.columns(2)
    with c1:
        render_ticket_card(tr("main_recommendation") + " · " + tr("advanced_model"), adv_numbers, adv_score, tr("advanced_model"), tr("not_prediction"))
    with c2:
        render_ticket_card(tr("main_recommendation") + " · " + tr("combined_model"), comb_numbers, comb_score, tr("combined_model"), tr("not_prediction"))

    st.markdown("### " + tr("all_models"))
    cols = st.columns(3)
    for i, (title, filename, _, explanation) in enumerate(get_model_cards()[2:]):
        with cols[i % 3]:
            model = model_json(filename)
            numbers, score = main_recommendation(model)
            render_ticket_card(title, numbers, score, filename, explanation)


def page_recommendations() -> None:
    render_header()
    st.markdown("## " + tr("all_models"))
    st.markdown(f'<div class="warning-soft">{tr("not_prediction")} {tr("real_odds")}: <b>{THEORETICAL_ODDS_TEXT}</b>.</div>', unsafe_allow_html=True)

    for title, filename, kind, explanation in get_model_cards():
        model = model_json(filename)
        numbers, score = main_recommendation(model)
        render_ticket_card(title, numbers, score, filename, explanation)
        recs = extract_recommendations(model)
        if kind in {"advanced", "combined"} and recs:
            with st.expander(tr("top_recommendations"), expanded=(kind == "advanced")):
                render_recommendation_list(title, recs, limit=10)
        else:
            top_df = top_numbers_dataframe(model)
            if not top_df.empty:
                with st.expander(tr("details"), expanded=False):
                    st.dataframe(top_df, width="stretch", hide_index=True)


def top_numbers_dataframe(model: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    if not model:
        return pd.DataFrame()
    for key, label in [
        ("top_numbers", "top"),
        ("top_scored_numbers", "top"),
        ("top_underrepresented_numbers", "cold"),
        ("top_balanced_numbers", "middle"),
        ("top_next_draw_probability_numbers", "gap"),
        ("number_scores", "score"),
    ]:
        values = model.get(key)
        if isinstance(values, list):
            for item in values[:20]:
                if isinstance(item, dict):
                    row = dict(item)
                    row.setdefault("signal", label)
                    rows.append(row)
                elif isinstance(item, (list, tuple)) and item:
                    rows.append({"number": item[0], "value": item[1] if len(item) > 1 else None, "signal": label})
            break
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    preferred = [c for c in ["number", "score", "cold_score", "middle_score", "next_prob", "empirical_probability", "expected_probability", "gap", "z_score", "status", "signal"] if c in df.columns]
    return df[preferred] if preferred else df


def page_combined() -> None:
    render_header()
    model = model_json("lottery_combined_model.json")
    numbers, score = main_recommendation(model)
    render_ticket_card(tr("combined_model"), numbers, score, tr("combined_model"), tr("not_prediction"))
    render_recommendation_list(tr("top_recommendations"), extract_recommendations(model), 15)


def run_script(script_name: str) -> Tuple[bool, str]:
    script = ROOT / script_name
    if not script.exists():
        return False, f"Missing script: {script_name}"
    process = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (process.stdout or "") + ("\n" + process.stderr if process.stderr else "")
    return process.returncode == 0, output.strip()


def page_advanced_lab() -> None:
    render_header()
    st.markdown("## " + tr("advanced_lab"))
    c1, c2 = st.columns(2)
    with c1:
        if st.button(tr("train_advanced"), width="stretch"):
            with st.spinner("Обучава разширения ансамбъл..."):
                ok, output = run_script("train_advanced_model.py")
            st.success("Готово" if ok else "Неуспешно")
            st.code(output[-4000:] if output else "Няма изход")
            st.cache_data.clear()
    with c2:
        if st.button(tr("run_backtest"), width="stretch"):
            with st.spinner("Изпълнява историческа проверка..."):
                ok, output = run_script("run_advanced_backtest.py")
            st.success("Готово" if ok else "Неуспешно")
            st.code(output[-4000:] if output else "Няма изход")
            st.cache_data.clear()

    model = model_json("lottery_advanced_ensemble_model.json")
    numbers, score = main_recommendation(model)
    render_ticket_card(tr("main_recommendation") + " · " + tr("advanced_model"), numbers, score, tr("advanced_model"), tr("not_prediction"))
    tabs = st.tabs([tr("top_recommendations"), tr("portfolio"), tr("fairness"), tr("backtest")])
    with tabs[0]:
        render_recommendation_list(tr("top_recommendations"), extract_recommendations(model), 15)
    with tabs[1]:
        portfolio = model.get("portfolio") or model.get("diversified_portfolio") or model.get("portfolio_combinations") or []
        render_recommendation_list(tr("portfolio"), portfolio, 15)
    with tabs[2]:
        fairness = model.get("fairness_test") or model.get("chi_square") or model.get("fairness") or {}
        if fairness:
            st.json(fairness, expanded=False)
        else:
            st.info("Все още няма записани резултати от проверката за честност в модела.")
    with tabs[3]:
        render_report_file(REPORTS_DIR / "advanced_backtest_report.md")


def compute_number_stats(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    nums = []
    for _, row in df.iterrows():
        nums.extend(numbers_from_row(row))
    counts = Counter(nums)
    total_draws = len(df)
    rows = []
    for n in range(1, 50):
        count = counts.get(n, 0)
        empirical = count / total_draws if total_draws else 0
        expected_count = total_draws * EXPECTED_NUMBER_PROB
        sigma = math.sqrt(total_draws * EXPECTED_NUMBER_PROB * (1 - EXPECTED_NUMBER_PROB)) if total_draws else 1
        z = (count - expected_count) / sigma if sigma else 0
        last_idx = None
        for idx in range(len(df) - 1, -1, -1):
            if n in numbers_from_row(df.iloc[idx]):
                last_idx = idx
                break
        gap = len(df) - 1 - last_idx if last_idx is not None else len(df)
        if z > 1.0:
            status = tr("status_hot")
        elif z < -1.0:
            status = tr("status_cold")
        else:
            status = tr("status_middle")
        rows.append({"number": n, "count": count, "empirical_%": empirical * 100, "expected_%": EXPECTED_NUMBER_PROB * 100, "z_score": z, "gap": gap, "status": status})
    return pd.DataFrame(rows)



def _prediction_reason_html(reasons: List[str]) -> str:
    if not reasons:
        return '<div class="small-muted">Няма записано обяснение.</div>'
    items = ''.join(f'<li>{reason}</li>' for reason in reasons)
    return f'<ul class="small-muted" style="margin-top:8px;">{items}</ul>'


def render_prediction_card(item: Dict[str, Any], title: str = "Прогнозна комбинация") -> None:
    numbers = item.get("numbers", []) if isinstance(item, dict) else []
    score = item.get("prediction_score") or item.get("confidence_score") or item.get("score") if isinstance(item, dict) else None
    classification = item.get("classification", "-") if isinstance(item, dict) else "-"
    cluster = item.get("cluster_label", "-") if isinstance(item, dict) else "-"
    rel = item.get("relative_model_probability") if isinstance(item, dict) else None
    try:
        score_text = f'<span class="score-badge">Моделна оценка: {float(score):.2f}/100</span>' if score is not None else ""
    except Exception:
        score_text = f'<span class="score-badge">Моделна оценка: {score}</span>' if score is not None else ""
    try:
        rel_text = f'<span class="score-badge">Относителна моделна тежест: {float(rel):.6f}%</span>' if rel is not None else ""
    except Exception:
        rel_text = f'<span class="score-badge">Относителна моделна тежест: {rel}</span>' if rel is not None else ""
    st.markdown(
        f"""
        <div class="model-card">
          <div class="model-title">{title}</div>
          {format_number_pills(numbers)}
          <div>{score_text}{rel_text}<span class="score-badge">Реален шанс: {THEORETICAL_ODDS_TEXT}</span></div>
          <div class="small-muted" style="margin-top:10px;">Клас: {classification} · Клъстер: {cluster}</div>
          {_prediction_reason_html(item.get("reasons", []) if isinstance(item, dict) else [])}
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_prediction() -> None:
    render_header()
    st.markdown("## Прогноза")
    st.markdown(
        '<div class="warning-soft"><b>Важно:</b> прогнозата е статистическо класиране на кандидат-комбинации. Тя не променя реалния шанс за точна комбинация 6/49 и не е гаранция за бъдещ тираж.</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Генерирай нова прогноза", width="stretch"):
            with st.spinner("Изчислява прогнозния модул..."):
                ok, output = run_script("predict_next_draw.py")
            st.success("Готово" if ok else "Неуспешно")
            st.code(output[-5000:] if output else "Няма изход")
            st.cache_data.clear()
    with c2:
        if st.button("Покажи отчета за прогнозата", width="stretch"):
            render_report_file(REPORTS_DIR / "prediction_report.md")

    model = model_json("lottery_prediction_model.json")
    if not model:
        st.info("Прогнозният модул още не е наличен. Натисни 'Генерирай нова прогноза'.")
        return

    best = model.get("recommended_prediction", {})
    render_prediction_card(best, "Основна прогноза за следващия тираж")

    context = model.get("latest_draw_context", {})
    check = model.get("historical_check_summary", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Обучени тиражи", f"{model.get('training_draws', 0):,}")
    c2.metric("Кандидати", f"{model.get('candidate_count', 0):,}")
    c3.metric("Последен тираж", f"{context.get('latest_year', '-')}/{context.get('latest_draw_number', '-')}")
    c4.metric("Най-добра историческа стратегия", check.get("best_strategy", "-"))

    tabs = st.tabs(["Топ прогнози", "Портфолио", "Защо тези числа", "Отчети"])

    with tabs[0]:
        st.markdown("### Топ прогнозни комбинации")
        for item in model.get("recommended_combinations", [])[:15]:
            render_prediction_card(item, f"Ранг {item.get('rank')}")

    with tabs[1]:
        st.markdown("### Диверсифицирано портфолио")
        st.caption("Тук комбинациите са подбрани така, че да не се припокриват прекалено много една с друга.")
        for item in model.get("portfolio_predictions", [])[:10]:
            render_prediction_card(item, f"Портфолио {item.get('portfolio_rank')}")

    with tabs[2]:
        st.markdown("### Обяснение на прогнозата")
        st.write("Модулът комбинира честотен сигнал, студен/интервален сигнал, баланс, двойки, тройки, структура, риск от човешки шаблон, последни тиражи и резултатите от историческата проверка.")
        features = best.get("feature_summary", {}) if isinstance(best, dict) else {}
        if features:
            st.dataframe(pd.DataFrame([features]), width="stretch", hide_index=True)
        methodology = model.get("methodology", [])
        if methodology:
            st.markdown("#### Методология")
            st.markdown("\n".join(f"- {item}" for item in methodology))

    with tabs[3]:
        reports = [
            ("prediction_report.md", "Отчет за прогнозата"),
            ("prediction_model_card.md", "Карта на прогнозния модул"),
            ("prediction_methodology_report.md", "Методология"),
        ]
        labels = dict(reports)
        selected = st.selectbox("Отчет", [name for name, _ in reports], format_func=lambda name: labels.get(name, name), key="prediction_report_select")
        render_report_file(REPORTS_DIR / selected)

def page_ticket_analyzer() -> None:
    render_header()
    st.markdown("## " + tr("ticket_analyzer"))
    selected = st.multiselect(tr("select_numbers"), options=list(range(1, 50)), max_selections=6)
    if st.button(tr("analyze_ticket"), width="stretch"):
        if len(set(selected)) != 6:
            st.error(tr("ticket_warning"))
            return
        df = load_draws()
        stats = compute_number_stats(df)
        ticket = sorted(selected)
        render_ticket_card("Вашият фиш", ticket, None, tr("real_odds") + ": " + THEORETICAL_ODDS_TEXT, tr("not_prediction"))
        if not stats.empty:
            view = stats[stats["number"].isin(ticket)].sort_values("number")
            st.dataframe(view, width="stretch", hide_index=True)
            avg_z = view["z_score"].mean()
            avg_gap = view["gap"].mean()
            c1, c2, c3 = st.columns(3)
            c1.metric("Среден Z-score", f"{avg_z:.2f}")
            c2.metric("Среден интервал", f"{avg_gap:.1f}")
            c3.metric(tr("real_odds"), THEORETICAL_ODDS_TEXT)


def page_history() -> None:
    render_header()
    df = load_draws()
    st.markdown("## " + tr("history"))
    if df.empty:
        st.warning("Няма заредени исторически данни.")
        return
    stats = compute_number_stats(df)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Най-често теглени числа")
        st.dataframe(stats.sort_values("count", ascending=False).head(12), width="stretch", hide_index=True)
    with c2:
        st.markdown("### Най-рядко теглени числа")
        st.dataframe(stats.sort_values("count", ascending=True).head(12), width="stretch", hide_index=True)
    st.markdown("### Графика на честотата на числата")
    st.bar_chart(stats.set_index("number")["count"], width="stretch")


def combinations_count(n: int, k: int) -> int:
    return math.comb(n, k)


def probability_exact_matches(matches: int) -> float:
    return (math.comb(6, matches) * math.comb(43, 6 - matches)) / math.comb(49, 6)


def page_probability_lab() -> None:
    render_header()
    st.markdown("## " + tr("probability_lab"))
    total = combinations_count(49, 6)
    st.metric("Общ брой комбинации C(49, 6)", f"{total:,}")
    rows = []
    for k in range(0, 7):
        p = probability_exact_matches(k)
        rows.append({"matches": k, "probability_%": p * 100, "1_in": round(1 / p) if p else None})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    ticket = sorted(random.sample(range(1, 50), 6))
    render_ticket_card("Случайно генерирана комбинация", ticket, None, "", tr("not_prediction"))

def render_report_file(path: Path) -> None:
    if not path.exists():
        st.info(f"Отчетът не е намерен: {path.name}")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    limit = st.slider("Редове за преглед", 20, min(max(len(lines), 20), 800), min(120, max(len(lines), 20)), key=f"slider_{path.name}")
    st.markdown("\n".join(lines[:limit]))
    st.download_button("Свали отчета", data=text, file_name=path.name, mime="text/markdown", key=f"download_{path.name}")


def page_reports() -> None:
    render_header()
    st.markdown("## " + tr("reports"))
    files = sorted(REPORTS_DIR.glob("*.md")) if REPORTS_DIR.exists() else []
    if not files:
        st.info("Няма намерени отчети.")
        return
    report_labels = {
        "prediction_report.md": "Отчет за прогнозата",
        "prediction_model_card.md": "Карта на прогнозния модул",
        "prediction_methodology_report.md": "Методология на прогнозата",
        "advanced_backtest_report.md": "Отчет от историческа проверка",
        "ml_extensions_backtest_report.md": "МЛ отчет от историческа проверка",
        "backtest_report.md": "Честотен отчет от историческа проверка",
        "combined_backtest_report.md": "Комбиниран отчет от историческа проверка",
        "cold_backtest_report.md": "Студен модел — историческа проверка",
        "gap_backtest_report.md": "Интервален модел — историческа проверка",
        "middle_backtest_report.md": "Балансиран модел — историческа проверка",
    }
    selected = st.selectbox("Отчет", files, format_func=lambda p: report_labels.get(p.name, p.name))
    render_report_file(selected)




def page_ml_lab() -> None:
    render_header()
    st.markdown("## МЛ лаборатория")
    st.markdown(
        '<div class="warning-soft">Тази секция добавя класификация, клъстеризация, редукция на размерността и карта на модела и историческа проверка. Това не променя реалния шанс за точна 6/49 комбинация.</div>',
        unsafe_allow_html=True,
    )

    col_train, col_report = st.columns(2)
    with col_train:
        if st.button("Обучи МЛ разширенията", width="stretch"):
            with st.spinner("Обучава класификация, клъстеризация и 2D карта..."):
                ok, output = run_script("train_ml_extensions.py")
            st.success("Готово" if ok else "Неуспешно")
            st.code(output[-4000:] if output else "Няма изход")
            st.cache_data.clear()
    with col_report:
        if st.button("Покажи картата на модела", width="stretch"):
            render_report_file(REPORTS_DIR / "ml_extensions_model_card.md")

    model = model_json("lottery_ml_extensions_model.json")
    if not model:
        st.info("МЛ моделът още не е наличен. Натисни 'Обучи МЛ разширенията'.")
        return

    recs = extract_recommendations(model)
    numbers, score = main_recommendation(model)
    render_ticket_card(
        "Основна МЛ препоръка",
        numbers,
        score,
        "Класификация + клъстеризация + 2D карта",
        "Моделна оценка за статистическо сравнение. Не е гаранция за бъдещ тираж.",
    )

    summary = model.get("backtest_summary", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Обучени тиражи", f"{model.get('training_draws', 0):,}")
    c2.metric("Кандидат-комбинации", f"{model.get('candidate_count', 0):,}")
    c3.metric("Историческа проверка — средно", summary.get("average_matches", "-"))
    c4.metric(">=2 съвпадения", f"{summary.get('hit_rate_ge_2', 0)}%")

    tabs = st.tabs([
        "Топ МЛ препоръки",
        "Класификация",
        "Клъстери",
        "2D карта",
        "Отчети",
    ])

    with tabs[0]:
        st.markdown("### Топ МЛ препоръки")
        for item in recs[:15]:
            numbers = item.get("numbers", [])
            score = item.get("confidence_score")
            classification = item.get("classification", "-")
            cluster_label = item.get("cluster_label", "-")
            html = f"""
                <div class="rank-card">
                  <div class="model-title">Ранг {item.get('rank')}</div>
                  {format_number_pills(numbers)}
                  <div class="small-muted">Оценка: {score}/100 · Клас: {classification} · Клъстер: {cluster_label}</div>
                </div>
                """
            st.markdown(html, unsafe_allow_html=True)

    with tabs[1]:
        classifier = model.get("classifier", {})
        st.markdown("### Класификация на фишове")
        st.markdown("Класификаторът групира фишовете като слаб, нормален или силен статистически фиш според изчислените характеристики.")
        classes = classifier.get("classes", [])
        if classes:
            st.dataframe(pd.DataFrame({"Класове": classes}), width="stretch", hide_index=True)
        quantiles = classifier.get("score_quantiles", {})
        if quantiles:
            st.dataframe(pd.DataFrame([{"Праг 33%": quantiles.get("q33"), "Праг 66%": quantiles.get("q66")}]), width="stretch", hide_index=True)

    with tabs[2]:
        st.markdown("### Клъстери на комбинации")
        clusters = model.get("cluster_model", {}).get("cluster_summaries", [])
        if clusters:
            df_clusters = pd.DataFrame(clusters).rename(columns={
                "cluster": "Клъстер",
                "label": "Име",
                "size": "Брой",
                "average_score": "Средна оценка",
                "avg_frequency_score": "Среден честотен сигнал",
                "avg_cold_gap_score": "Среден интервален сигнал",
                "avg_structure_score": "Средна структура",
                "avg_human_pattern_score": "Среден риск от шаблон",
            })
            st.dataframe(df_clusters, width="stretch", hide_index=True)
        else:
            st.info("Няма записани клъстери.")

    with tabs[3]:
        st.markdown("### 2D карта на комбинациите")
        reduction = model.get("dimensionality_reduction", {})
        evr = reduction.get("explained_variance_ratio", [])

        if evr and len(evr) >= 2:
            axis_x_pct = float(evr[0]) * 100
            axis_y_pct = float(evr[1]) * 100
            total_pct = (float(evr[0]) + float(evr[1])) * 100

            c1, c2, c3 = st.columns(3)
            c1.metric("Ос X обяснява", f"{axis_x_pct:.2f}%")
            c2.metric("Ос Y обяснява", f"{axis_y_pct:.2f}%")
            c3.metric("Общо 2D покритие", f"{total_pct:.2f}%")

            st.caption(
                "Това показва каква част от вътрешната информация на модела е запазена "
                "при свиването на комбинациите до 2D карта. По-висок процент означава "
                "по-ясна визуална картина, но не означава по-висок шанс за печалба."
            )
        else:
            st.caption("Няма записани стойности за обяснена вариация.")

        points = model.get("projection_points_sample", [])
        if points:
            chart_df = pd.DataFrame(points)

            for col in ["x", "y", "score"]:
                if col in chart_df.columns:
                    chart_df[col] = pd.to_numeric(chart_df[col], errors="coerce")

            chart_df = chart_df.dropna(subset=["x", "y"])

            if "numbers" in chart_df.columns:
                chart_df["Комбинация"] = chart_df["numbers"].apply(
                    lambda x: ", ".join(map(str, x)) if isinstance(x, list) else str(x)
                )
            else:
                chart_df["Комбинация"] = ""

            chart_df = chart_df.rename(
                columns={
                    "x": "Ос X",
                    "y": "Ос Y",
                    "score": "Оценка",
                }
            )

            st.markdown("#### Визуална карта")
            st.caption(
                "Всяка точка е една комбинация. Близките точки имат сходна структура според модела. "
                "Цветът/оценката показва колко силна е комбинацията според текущия модел."
            )

            try:
                import altair as alt

                chart = (
                    alt.Chart(chart_df)
                    .mark_circle(size=95, opacity=0.78)
                    .encode(
                        x=alt.X("Ос X:Q", title="Ос X"),
                        y=alt.Y("Ос Y:Q", title="Ос Y"),
                        color=alt.Color("Оценка:Q", title="Оценка"),
                        tooltip=[
                            alt.Tooltip("Комбинация:N", title="Числа"),
                            alt.Tooltip("Оценка:Q", title="Оценка", format=".4f"),
                            alt.Tooltip("Ос X:Q", title="Ос X", format=".4f"),
                            alt.Tooltip("Ос Y:Q", title="Ос Y", format=".4f"),
                        ],
                    )
                    .interactive()
                    .properties(height=460)
                )

                st.altair_chart(chart, use_container_width=True)
            except Exception:
                st.scatter_chart(chart_df, x="Ос X", y="Ос Y", size="Оценка", height=460)

            st.markdown("#### Данни зад картата")
            table_cols = [col for col in ["Комбинация", "Ос X", "Ос Y", "Оценка"] if col in chart_df.columns]
            st.dataframe(chart_df[table_cols], width="stretch", hide_index=True)
        else:
            st.info("Няма записани точки за 2D карта.")

    with tabs[4]:
        report_files = [
            "ml_extensions_report.md",
            "ml_classification_report.md",
            "ml_clustering_report.md",
            "ml_dimensionality_reduction_report.md",
            "ml_extensions_backtest_report.md",
            "ml_extensions_model_card.md",
        ]
        report_labels = {
            "ml_extensions_report.md": "Общ отчет за МЛ разширенията",
            "ml_classification_report.md": "Отчет за класификация",
            "ml_clustering_report.md": "Отчет за клъстеризация",
            "ml_dimensionality_reduction_report.md": "Отчет за 2D карта",
            "ml_extensions_backtest_report.md": "Отчет от историческа проверка",
            "ml_extensions_model_card.md": "Карта на модела",
        }
        selected = st.selectbox("МЛ отчет", report_files, format_func=lambda name: report_labels.get(name, name))
        render_report_file(REPORTS_DIR / selected)


def parse_uploaded_numbers(raw: str) -> List[int]:
    numbers = [int(x) for x in re.findall(r"\b\d{1,2}\b", raw)]
    valid = [n for n in numbers if 1 <= n <= 49]
    for i in range(0, max(len(valid) - 5, 0)):
        chunk = valid[i:i + 6]
        if len(chunk) == 6 and len(set(chunk)) == 6:
            return sorted(chunk)
    return []


def backup_csv(prefix: str) -> Optional[Path]:
    if not DATA_PATH.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"{prefix}_{stamp}.csv"
    shutil.copy2(DATA_PATH, backup)
    return backup


def read_csv_rows() -> Tuple[List[Dict[str, str]], List[str]]:
    if not DATA_PATH.exists():
        fields = ["date", "year", "draw_number", "draw_position", "n1", "n2", "n3", "n4", "n5", "n6", "source"]
        return [], fields
    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    for field in ["date", "year", "draw_number", "draw_position", "n1", "n2", "n3", "n4", "n5", "n6", "source"]:
        if field not in fields:
            fields.append(field)
            for row in rows:
                row.setdefault(field, "")
    return rows, fields


def write_csv_rows(rows: List[Dict[str, Any]], fields: List[str]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def retrain_all_models() -> List[Tuple[str, bool, str]]:
    scripts = [
        "train_model.py",
        "train_cold_model.py",
        "train_middle_model.py",
        "train_gap_model.py",
        "train_combined_model.py",
        "train_advanced_model.py",
        "train_ml_extensions.py",
        "predict_next_draw.py",
    ]
    results = []
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    log_lines = ["# Manual Update Retrain Log", ""]
    for script in scripts:
        if not (ROOT / script).exists():
            continue
        ok, output = run_script(script)
        results.append((script, ok, output))
        log_lines.append(f"## {script}")
        log_lines.append("PASS" if ok else "FAIL")
        log_lines.append("```text")
        log_lines.append(output[-3000:] if output else "No output")
        log_lines.append("```")
        log_lines.append("")
    (REPORTS_DIR / "manual_update_retrain_log.md").write_text("\n".join(log_lines), encoding="utf-8")
    st.cache_data.clear()
    return results


def page_update_draws() -> None:
    render_header()
    st.markdown("## " + tr("update_draws"))
    auto_retrain = st.checkbox(tr("auto_retrain"), value=True)

    st.markdown("### " + tr("upload_draw"))
    uploaded = st.file_uploader("TXT / CSV / JSON", type=["txt", "csv", "json"])
    if uploaded and st.button(tr("upload_button"), width="stretch"):
        raw = uploaded.read().decode("utf-8", errors="replace")
        parsed = parse_uploaded_numbers(raw)
        if parsed:
            st.session_state["uploaded_numbers"] = parsed
            st.success(f"Разчетени числа: {parsed}")
        else:
            st.error("Не успях да разчета точно 6 различни валидни числа.")

    detected = st.session_state.get("uploaded_numbers", [])
    default_numbers = detected if detected else [1, 2, 3, 4, 5, 6]

    c1, c2, c3 = st.columns(3)
    draw_date = c1.date_input(tr("draw_date"), value=date.today())
    year = c2.number_input(tr("year"), min_value=1958, max_value=2100, value=int(draw_date.year))
    draw_number = c3.number_input(tr("draw_number"), min_value=0, max_value=9999, value=1)
    position = st.number_input(tr("draw_position"), min_value=1, max_value=20, value=1)
    numbers = st.multiselect(tr("numbers"), options=list(range(1, 50)), default=default_numbers[:6], max_selections=6)
    source = st.text_input(tr("source"), value="Ръчно въвеждане")

    if st.button(tr("save_draw"), width="stretch"):
        nums = sorted([int(n) for n in numbers])
        if len(nums) != 6 or len(set(nums)) != 6:
            st.error(tr("ticket_warning"))
        else:
            rows, fields = read_csv_rows()
            key = (str(int(year)), str(int(draw_number)), str(int(position)))
            exists = any((str(r.get("year")), str(r.get("draw_number")), str(r.get("draw_position"))) == key for r in rows)
            if exists:
                st.error("Тази година + номер на тираж + позиция вече съществува.")
            else:
                backup = backup_csv("before_manual_add")
                row = {field: "" for field in fields}
                row.update({
                    "date": str(draw_date),
                    "year": int(year),
                    "draw_number": int(draw_number),
                    "draw_position": int(position),
                    "n1": nums[0], "n2": nums[1], "n3": nums[2], "n4": nums[3], "n5": nums[4], "n6": nums[5],
                    "source": source,
                })
                rows.append(row)
                write_csv_rows(rows, fields)
                st.success(f"Записан тираж {year}/{draw_number}/{position}. Резервно копие: {backup.name if backup else 'няма'}")
                if auto_retrain:
                    with st.spinner("Моделите се обновяват..."):
                        results = retrain_all_models()
                    for script, ok, output in results:
                        st.write(("✅" if ok else "❌") + " " + script)
                    st.info("Обнови страницата, за да видиш новите препоръки.")

    st.divider()
    st.markdown("### Корекция / изтриване на тираж")
    c1, c2, c3 = st.columns(3)
    del_year = c1.number_input("Година за изтриване", min_value=1958, max_value=2100, value=int(date.today().year))
    del_draw = c2.number_input("Номер на тираж за изтриване", min_value=0, max_value=9999, value=1)
    del_pos = c3.number_input("Позиция за изтриване", min_value=1, max_value=20, value=1)
    if st.button(tr("delete_draw"), width="stretch"):
        rows, fields = read_csv_rows()
        key = (str(int(del_year)), str(int(del_draw)), str(int(del_pos)))
        new_rows = [r for r in rows if (str(r.get("year")), str(r.get("draw_number")), str(r.get("draw_position"))) != key]
        if len(new_rows) == len(rows):
            st.warning("Не е намерен такъв тираж.")
        else:
            backup = backup_csv("before_manual_delete")
            write_csv_rows(new_rows, fields)
            st.success(f"Изтрит тираж {key}. Резервно копие: {backup.name if backup else 'няма'}")
            if auto_retrain:
                with st.spinner("Моделите се обновяват..."):
                    retrain_all_models()
                st.info("Обнови страницата, за да видиш новите препоръки.")

    backups = sorted(BACKUP_DIR.glob("*.csv"), reverse=True)
    if backups:
        if st.button(tr("undo"), width="stretch"):
            latest = backups[0]
            shutil.copy2(latest, DATA_PATH)
            st.success(f"Възстановено резервно копие: {latest.name}")
            if auto_retrain:
                with st.spinner("Моделите се обновяват..."):
                    retrain_all_models()
                st.info("Обнови страницата, за да видиш новите препоръки.")


def page_glossary() -> None:
    with st.expander(tr("term_help"), expanded=False):
        st.markdown(
            """
            **Горещо** — число с по-силен честотен сигнал в историята.  
            **Студено** — число под очакваната честота или с по-слаб честотен сигнал.  
            **Интервал** — колко тиража са минали от последното излизане.  
            **Отдавна не е излизало** — текущият gap е по-голям от обичайния интервал.  
            **Балансирано** — близо до очакваната честота.  
            **Моделна оценка** — моделна оценка за ранкинг, не процент шанс за джакпот.
            """
        )


def main() -> None:
    page_glossary()
    pages = {
        tr("dashboard"): page_dashboard,
        tr("recommendations"): page_recommendations,
        tr("combined"): page_combined,
        tr("advanced_lab"): page_advanced_lab,
        tr("ml_lab"): page_ml_lab,
        tr("prediction"): page_prediction,
        tr("ticket_analyzer"): page_ticket_analyzer,
        tr("history"): page_history,
        tr("probability_lab"): page_probability_lab,
        tr("reports"): page_reports,
        tr("update_draws"): page_update_draws,
    }
    choice = st.sidebar.radio(tr("menu"), list(pages.keys()))
    if st.sidebar.button(tr("refresh")):
        st.cache_data.clear()
        st.rerun()
    pages[choice]()


if __name__ == "__main__":
    main()

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
from src.bg_ui_helpers import install_streamlit_bg_table_patch
install_streamlit_bg_table_patch(st)
from src.v53_ticket_coverage_section import render_v53_ticket_coverage_section
from src.v54_pattern_balance_section import render_v54_pattern_balance_section
from src.v55_number_profile_section import render_v55_number_profile_section
from src.v56_draw_similarity_section import render_v56_draw_similarity_section
from src.v57_hot_cold_stable_section import render_v57_hot_cold_stable_section
from src.v58_smart_ensemble_score_section import render_v58_smart_ensemble_score_section
from src.v59_smart_ticket_builder_2_section import render_v59_smart_ticket_builder_2_section
from src.v61_draw_result_analyzer_section import render_v61_draw_result_analyzer_section
from src.v62_model_performance_tracker_section import render_v62_model_performance_tracker_section
from src.v63_model_reliability_dashboard_section import render_v63_model_reliability_dashboard_section
from src.v65_model_weighting_section import render_v65_model_weighting_section
from src.v66_weighted_smart_ensemble_section import render_v66_weighted_smart_ensemble_section
from src.v67_weighted_ticket_builder_section import render_v67_weighted_ticket_builder_section
from src.v68_weighted_portfolio_optimizer_section import render_v68_weighted_portfolio_optimizer_section
from src.v69_portfolio_improvement_section import render_v69_portfolio_improvement_section
from src.v70_applied_candidate_portfolio_section import render_v70_applied_candidate_portfolio_section
from src.v71_ticket_pack_export_section import render_v71_ticket_pack_export_section
from src.v73_ticket_pack_performance_tracker_section import render_v73_ticket_pack_performance_tracker_section
from src.v72_pipeline_refresh_section import render_v72_pipeline_refresh_section
from src.v74_model_dependency_sync_center_section import render_v74_model_dependency_sync_center_section
from src.v75_neural_meta_learner_section import render_v75_neural_meta_learner_section
from src.v76_explainability_validation_section import render_v76_explainability_validation_section
from src.v77_decision_recommendation_section import render_v77_decision_recommendation_section
from src.v78_final_play_plan_section import render_v78_final_play_plan_section
from src.v79_ticket_pack_export_section import render_v79_ticket_pack_export_section
from src.v80_final_system_audit_section import render_v80_final_system_audit_section
from src.v81_final_ux_navigation_section import render_v81_final_ux_navigation_section
from src.v82_final_release_package_section import render_v82_final_release_package_section
from src.v83_final_user_manual_section import render_v83_final_user_manual_section
from src.v84_model_comparison_forward_test_section import render_v84_model_comparison_forward_test_section
from src.v86_model_registry_trust_center_section import render_v86_model_registry_trust_center_section
from src.v87_synthesized_user_menu_section import render_v87_synthesized_user_menu_section
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
    "Ticket Analyzer": "Анализ на комбинация",
    "Historical Statistics": "Историческа статистика",
    "Вероятностна лаборатория": "Вероятности",
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
    "Generate model tickets": "Генерирай моделни комбинации",
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
    "Вероятност %": "Вероятност %",
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
    "Advanced ticket": "Комбинация на разширения модел",
    "Advanced фиш": "Комбинация на разширения модел",
    "Advanced matches": "Съвпадения на разширения модел",
    "Advanced съвпадения": "Съвпадения на разширения модел",
    "Random": "Случаен модел",
    "Random ticket": "Случайна комбинация",
    "Random фиш": "Случайна комбинация",
    "Random matches": "Съвпадения на случайна комбинация",
    "Random съвпадения": "Съвпадения на случайна комбинация",
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
    return None
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
            "Комбинация на разширения модел": _lr34_nums(advanced),
            "Съвпадения на разширения модел": int(adv_matches),
            "Случайна комбинация": _lr34_nums(random_ticket),
            "Съвпадения на случайна комбинация": int(rnd_matches),
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
        tested_match = _lr34_re.search(r"Проверени тиражи:\s*(\d+)", text_value)
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
                "Комбинация на разширения модел": ", ".join(map(str, row["Комбинация на разширения модел"])),
                "Съвпадения на разширения модел": row["Съвпадения на разширения модел"],
                "Случайна комбинация": ", ".join(map(str, row["Случайна комбинация"])),
                "Съвпадения на случайна комбинация": row["Съвпадения на случайна комбинация"],
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
                    st.caption(f"Комбинация на разширения модел — {row['Съвпадения на разширения модел']} съвпадения")
                    _lr34_balls(row["Комбинация на разширения модел"])
                with c3:
                    st.caption(f"Случайна комбинация — {row['Съвпадения на случайна комбинация']} съвпадения")
                    _lr34_balls(row["Случайна комбинация"])
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
        "ticket_analyzer": "Анализ на комбинация",
        "history": "Историческа статистика",
        "v41_history_analysis": "Анализ на минали тегления",
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
        "app_caption": "Analysis, models, historical checks and visual recommendations. It does not guarantee a win.",
        "menu": "Menu",
        "dashboard": "Dashboard",
        "recommendations": "Recommendations",
        "combined": "Combined Model",
        "advanced_lab": "Advanced Lab",
        "ml_lab": "ML Laboratory",
        "ml_extensions": "ML extensions: classification, clusters and 2D map",
        "prediction": "Prediction",
        "ticket_analyzer": "Анализ на комбинация",
        "history": "Historical Statistics",
        "v41_history_analysis": "Historical Draw Analysis",
        "probability_lab": "Вероятностна лаборатория",
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
        "advanced_model": "Разширен обединен модел",
        "train_advanced": "Train разширен обединен модел",
        "run_backtest": "Пусни историческа проверка",
        "no_model": "Model not available yet. Run the training script.",
        "numbers": "Numbers",
        "confidence": "Score",
        "rank": "Ранг",
        "details": "Детайли",
        "refresh": "Обнови данните",
        "select_numbers": "Избери 6 числа",
        "analyze_ticket": "Анализирай комбинацията",
        "ticket_warning": "Избери точно 6 различни числа от 1 до 49.",
        "save_draw": "Запиши нов тираж",
        "auto_retrain": "Автоматично обнови моделите след запис",
        "year": "Година",
        "draw_number": "Тираж №",
        "draw_position": "Позиция / теглене",
        "draw_date": "Дата",
        "source": "Източник / бележка",
        "upload_draw": "Качи тираж от файл",
        "upload_button": "Прочети качения файл",
        "delete_draw": "Изтрий избрания тираж",
        "undo": "Отмени последната ръчна промяна",
        "retrain_log": "Лог от обновяването",
        "portfolio": "Диверсифициран портфейл",
        "fairness": "Проверка за равномерност / chi-square",
        "backtest": "Историческа проверка",
        "status_hot": "Горещи",
        "status_cold": "Студени",
        "status_middle": "Балансирани",
        "status_overdue": "Отдавна не е излизало",
        "term_help": "Речник",
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
def _v13_sidebar_button(label: str, key: str) -> bool:
    try:
        return st.sidebar.button(label, key=key, width="stretch")
    except TypeError:
        return st.sidebar.button(label, key=key)
def _v13_simulation_lab_hook() -> None:
    if "v13_simulation_lab_active" not in st.session_state:
        st.session_state["v13_simulation_lab_active"] = False
    if _v13_sidebar_button("\U0001f3b2 \u0421\u0438\u043c\u0443\u043b\u0430\u0446\u0438\u044f", "v13_open_simulation_lab"):
        st.session_state["v13_simulation_lab_active"] = True
        if hasattr(st, "rerun"):
            st.rerun()
        elif hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
    if st.session_state.get("v13_simulation_lab_active"):
        if _v13_sidebar_button("\u2190 \u041d\u0430\u0437\u0430\u0434 \u043a\u044a\u043c \u043e\u0441\u043d\u043e\u0432\u043d\u043e\u0442\u043e \u043c\u0435\u043d\u044e", "v13_close_simulation_lab"):
            st.session_state["v13_simulation_lab_active"] = False
            if hasattr(st, "rerun"):
                st.rerun()
            elif hasattr(st, "experimental_rerun"):
                st.experimental_rerun()
        try:
            import importlib
            module = importlib.import_module("streamlit_pages.simulation_lab_page")
            module = importlib.reload(module)
            module.render_simulation_lab_page()
        except Exception as exc:
            st.error("\u0413\u0440\u0435\u0448\u043a\u0430 \u043f\u0440\u0438 \u0437\u0430\u0440\u0435\u0436\u0434\u0430\u043d\u0435 \u043d\u0430 \u0441\u0438\u043c\u0443\u043b\u0430\u0446\u0438\u044f\u0442\u0430.")
            st.exception(exc)
        st.stop()
_v13_simulation_lab_hook()
# V13_SIMULATION_LAB_HOOK_END
# V40_TICKET_CHECKER_UI_HOOK_START
def _v40_ticket_checker_sidebar_button(label: str, key: str) -> bool:
    try:
        return st.sidebar.button(label, key=key, width="stretch")
    except TypeError:
        return st.sidebar.button(label, key=key)
def _v40_ticket_checker_hook() -> None:
    ticket_label = "\U0001F3AB \u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043d\u0430 \u0444\u0438\u0448"
    back_label = "\u2190 \u041d\u0430\u0437\u0430\u0434 \u043a\u044a\u043c \u043e\u0441\u043d\u043e\u0432\u043d\u043e\u0442\u043e \u043c\u0435\u043d\u044e"
    load_error = "\u0413\u0440\u0435\u0448\u043a\u0430 \u043f\u0440\u0438 \u0437\u0430\u0440\u0435\u0436\u0434\u0430\u043d\u0435 \u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430\u0442\u0430 \u043d\u0430 \u0444\u0438\u0448."
    if "v40_ticket_checker_active" not in st.session_state:
        st.session_state["v40_ticket_checker_active"] = False
    if _v40_ticket_checker_sidebar_button(ticket_label, "v40_open_ticket_checker"):
        st.session_state["v40_ticket_checker_active"] = True
        if hasattr(st, "rerun"):
            st.rerun()
        elif hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
    if st.session_state.get("v40_ticket_checker_active"):
        if _v40_ticket_checker_sidebar_button(back_label, "v40_close_ticket_checker"):
            st.session_state["v40_ticket_checker_active"] = False
            if hasattr(st, "rerun"):
                st.rerun()
            elif hasattr(st, "experimental_rerun"):
                st.experimental_rerun()
        try:
            import importlib
            module = importlib.import_module("streamlit_pages.ticket_checker_page")
            module = importlib.reload(module)
            module.render_ticket_checker_page()
        except Exception as exc:
            st.error(load_error)
            st.exception(exc)
        st.stop()
_v40_ticket_checker_hook()
# V40_TICKET_CHECKER_UI_HOOK_END
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
def _v39_apply_wide_layout_patch() -> None:
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 96% !important;
            padding-top: 1.25rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }
        @media (min-width: 1400px) {
            .main .block-container {
                max-width: 98% !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
def render_header() -> None:
    _v39_apply_wide_layout_patch()
    st.markdown(
        f"""
        <div class="hero-box">
          <div class="hero-title">🎯 {tr("app_title")}</div>
          <div class="hero-subtitle">{tr("app_caption")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# STEP87_7_USER_FRIENDLY_MODEL_SOURCE_START
def _step87_7_user_model_source(filename: str) -> str:
    def u(value: str) -> str:
        return value.encode("ascii").decode("unicode_escape")

    mapping = {
        "lottery_prediction_model.json": u(r"\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0435\u043d \u0441\u043b\u043e\u0439"),
        "lottery_prediction_model_v36.json": u(r"\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0435\u043d \u0441\u043b\u043e\u0439"),
        "prediction_model.json": u(r"\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0435\u043d \u0441\u043b\u043e\u0439"),
        "prediction_engine_model.json": u(r"\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0435\u043d \u0441\u043b\u043e\u0439"),
        "lottery_combined_model.json": u(r"\u0424\u0438\u043d\u0430\u043b\u0435\u043d \u043a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u0441\u043b\u043e\u0439"),
        "lottery_frequency_model.json": u(r"\u0427\u0435\u0441\u0442\u043e\u0442\u0435\u043d \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0441\u043b\u043e\u0439"),
        "lottery_cold_model.json": u(r"\u0418\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0435\u043d \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0441\u043b\u043e\u0439"),
        "lottery_advanced_ensemble_model.json": u(r"\u0420\u0430\u0437\u0448\u0438\u0440\u0435\u043d \u0430\u043d\u0441\u0430\u043c\u0431\u043b\u043e\u0432 \u0441\u043b\u043e\u0439"),
        "lottery_ml_extensions_model.json": u(r"\u041c\u041b \u043f\u043e\u043c\u043e\u0449\u0435\u043d \u0441\u043b\u043e\u0439"),
    }

    value = str(filename or "").strip()
    if value in mapping:
        return mapping[value]
    if value.endswith(".json"):
        return u(r"\u041c\u043e\u0434\u0435\u043b\u0435\u043d \u0438\u0437\u0442\u043e\u0447\u043d\u0438\u043a")
    return value
# STEP87_7_USER_FRIENDLY_MODEL_SOURCE_END


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
            render_ticket_card(title, numbers, score, _step87_7_user_model_source(filename), explanation)
def page_recommendations() -> None:
    render_header()
    st.markdown("## " + tr("all_models"))
    st.markdown(f'<div class="warning-soft">{tr("not_prediction")} {tr("real_odds")}: <b>{THEORETICAL_ODDS_TEXT}</b>.</div>', unsafe_allow_html=True)
    for title, filename, kind, explanation in get_model_cards():
        model = model_json(filename)
        numbers, score = main_recommendation(model)
        render_ticket_card(title, numbers, score, _step87_7_user_model_source(filename), explanation)
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
def _v39_adv_lang():
    try:
        return st.session_state.get("language", globals().get("LANG", "bg"))
    except Exception:
        return globals().get("LANG", "bg")
def _v39_adv_text(bg, en):
    return bg if _v39_adv_lang() == "bg" else en
def _v39_adv_odds():
    return "1:13,983,816"
def _v39_adv_find_script(kind):
    candidates = [
        "train_advanced_ensemble.py",
        "train_advanced_model.py",
        "train_advanced_statistical_ensemble.py",
        "train_advanced_lab.py",
        "advanced_ensemble_train.py",
    ] if kind == "train" else [
        "run_advanced_backtest.py",
        "advanced_backtest.py",
        "backtest_advanced_model.py",
        "run_advanced_lab_backtest.py",
    ]
    for name in candidates:
        p = ROOT / name
        if p.exists():
            return p
        p = ROOT / "scripts" / name
        if p.exists():
            return p
    words = ["advanced", "train"] if kind == "train" else ["advanced", "backtest"]
    for p in ROOT.rglob("*.py"):
        rel = str(p.relative_to(ROOT)).lower().replace("\\", "/")
        if ".venv/" in rel or "__pycache__" in rel or ".v39_local_backups" in rel:
            continue
        if all(word in p.name.lower() for word in words):
            return p
    return None
def _v39_adv_run(kind):
    import subprocess
    import sys
    script = _v39_adv_find_script(kind)
    if script is None:
        return False, _v39_adv_text(
            "\u041d\u0435 \u0435 \u043d\u0430\u043c\u0435\u0440\u0435\u043d \u043f\u043e\u0434\u0445\u043e\u0434\u044f\u0449 Python \u0441\u043a\u0440\u0438\u043f\u0442 \u0437\u0430 \u0442\u0430\u0437\u0438 \u043e\u043f\u0435\u0440\u0430\u0446\u0438\u044f.",
            "No suitable Python script was found for this operation.",
        )
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode == 0, output.strip()
def _v39_adv_sanitize_output(output):
    if not output:
        return _v39_adv_text("\u041d\u044f\u043c\u0430 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438 \u0438\u0437\u0445\u043e\u0434.", "No technical output.")
    clean = str(output).replace(chr(0xFFFD), "?")
    clean = re.sub(r"\?{3,}", _v39_adv_text("[\u043d\u0435\u0440\u0430\u0437\u0447\u0435\u0442\u0435\u043d \u0442\u0435\u043a\u0441\u0442]", "[unreadable text]"), clean)
    return clean
def _v39_adv_parse_int(output, label):
    try:
        match = re.search(label + r"\s*:\s*([0-9,]+)", output or "", flags=re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    except Exception:
        pass
    return None
def _v39_adv_parse_float(output, label):
    try:
        match = re.search(label + r"\s*:\s*([0-9.]+)", output or "", flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    except Exception:
        pass
    return None
def _v39_adv_load_model():
    import json
    if not MODELS_DIR.exists():
        return {}
    preferred = [
        "lottery_advanced_model.json",
        "lottery_advanced_ensemble_model.json",
        "advanced_statistical_ensemble_model.json",
        "advanced_model.json",
    ]
    for name in preferred:
        p = MODELS_DIR / name
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    for p in MODELS_DIR.glob("*advanced*.json"):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
    return {}
def _v39_adv_recommendations(model):
    for key in [
        "recommendations",
        "top_recommendations",
        "advanced_recommendations",
        "ranked_recommendations",
        "top_advanced_recommendations",
    ]:
        value = model.get(key)
        if isinstance(value, list):
            return value
    return []
def _v39_adv_numbers(item):
    if isinstance(item, dict):
        for key in ["numbers", "combination", "ticket", "values"]:
            value = item.get(key)
            if isinstance(value, list):
                return value
    if isinstance(item, list):
        return item
    return []
def _v39_adv_score(item):
    if isinstance(item, dict):
        for key in ["confidence", "confidence_score", "score", "model_score"]:
            if key in item:
                return item.get(key)
    return None
def _v39_adv_model_value(model, *keys):
    for key in keys:
        value = model.get(key)
        if value is not None:
            return value
    return None
def _v39_adv_render_metrics(training_draws, candidate_count, fairness=None):
    c1, c2 = st.columns(2)
    c1.metric(_v39_adv_text("\u041e\u0431\u0443\u0447\u0435\u043d\u0438 \u0442\u0438\u0440\u0430\u0436\u0438", "Training draws"), f"{int(training_draws):,}" if training_draws else "-")
    c2.metric(_v39_adv_text("\u041a\u0430\u043d\u0434\u0438\u0434\u0430\u0442-\u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438", "Candidate combinations"), f"{int(candidate_count):,}" if candidate_count else "-")
    odds_label = _v39_adv_text("\u0420\u0435\u0430\u043b\u0435\u043d \u0448\u0430\u043d\u0441", "Real odds")
    st.markdown(f"**{odds_label}:** `{_v39_adv_odds()}`")
    if fairness is not None:
        st.caption(
            _v39_adv_text(
                f"Fairness p-value: {fairness}. \u0422\u043e\u0432\u0430 \u0435 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430, \u043d\u0435 \u043e\u0431\u0435\u0449\u0430\u043d\u0438\u0435 \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430.",
                f"Fairness p-value: {fairness}. This is a statistical check, not a promise of winning.",
            )
        )
def _v39_adv_render_overview(model):
    st.markdown("### " + _v39_adv_text("\u041a\u0430\u043a\u0432\u043e \u043f\u0440\u0430\u0432\u0438 \u0440\u0430\u0437\u0448\u0438\u0440\u0435\u043d\u0430\u0442\u0430 \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f", "What the Advanced Lab Does"))
    st.markdown(
        _v39_adv_text(
            "\u0420\u0430\u0437\u0448\u0438\u0440\u0435\u043d\u0430\u0442\u0430 \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f \u0435 \u043f\u043e-\u0442\u0435\u0436\u044a\u043a \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0430\u043d\u0441\u0430\u043c\u0431\u044a\u043b. \u0422\u044f \u043a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430 \u043d\u044f\u043a\u043e\u043b\u043a\u043e \u0432\u0438\u0434\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438 \u0432\u044a\u0440\u0445\u0443 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438\u0442\u0435 \u0442\u0438\u0440\u0430\u0436\u0438 \u0438 \u043a\u043b\u0430\u0441\u0438\u0440\u0430 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442-\u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438. \u0422\u043e\u0432\u0430 \u0435 \u0430\u043d\u0430\u043b\u0438\u0437, \u043d\u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430.",
            "Лабораторията използва по-тежък обединен статистически анализ. It combines several checks over the historical draws and ranks candidate combinations. This is analysis, not a guarantee of winning.",
        )
    )
    training_draws = _v39_adv_model_value(model, "training_draws", "dataset_rows", "rows")
    candidate_count = _v39_adv_model_value(model, "candidate_count", "candidate_combinations")
    fairness = _v39_adv_model_value(model, "fairness_p_value", "fairness_pvalue")
    _v39_adv_render_metrics(training_draws, candidate_count, fairness)
def _v39_adv_render_top(model):
    recs = _v39_adv_recommendations(model)
    if not recs:
        return
    st.markdown("### " + _v39_adv_text("\u0422\u043e\u043f \u0440\u0430\u0437\u0448\u0438\u0440\u0435\u043d\u0438 \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0438", "Top Advanced Recommendations"))
    for idx, item in enumerate(recs[:10], start=1):
        numbers = _v39_adv_numbers(item)
        score = _v39_adv_score(item)
        try:
            score_text = f"{float(score):.2f}/100" if score is not None else "-"
        except Exception:
            score_text = str(score)
        st.markdown(
            f"""
            <div class="rank-card">
              <div class="model-title">{_v39_adv_text("\u0420\u0430\u043d\u0433", "Rank")} {idx}</div>
              {format_number_pills(numbers)}
              <div class="small-muted">{_v39_adv_text("\u041c\u043e\u0434\u0435\u043b\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430", "Model score")}: {score_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
def page_advanced_lab() -> None:
    render_header()
    st.markdown("## " + _v39_adv_text("\u0420\u0430\u0437\u0448\u0438\u0440\u0435\u043d\u0430 \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f", "Advanced Laboratory"))
    st.markdown(
        '<div class="warning-soft">'
        + _v39_adv_text(
            "\u0422\u0430\u0437\u0438 \u0441\u0435\u043a\u0446\u0438\u044f \u0438\u0437\u043f\u043e\u043b\u0437\u0432\u0430 \u0440\u0430\u0437\u0448\u0438\u0440\u0435\u043d \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0430\u043d\u0441\u0430\u043c\u0431\u044a\u043b \u0438 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430. \u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442\u0438\u0442\u0435 \u0441\u0430 \u0437\u0430 \u0430\u043d\u0430\u043b\u0438\u0437 \u0438 \u0441\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u0435, \u043d\u0435 \u0441\u0430 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430.",
            "This section uses an разширен обединен статистически анализ and historical checks. The results are for analysis and comparison, not a guarantee of winning.",
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    col_train, col_check = st.columns(2)
    with col_train:
        if st.button(
            _v39_adv_text("\u041f\u0440\u0435\u0438\u0437\u0447\u0438\u0441\u043b\u0438 \u0440\u0430\u0437\u0448\u0438\u0440\u0435\u043d\u0438\u044f \u043c\u043e\u0434\u0435\u043b", "Recalculate Advanced Model"),
            width="stretch",
            key="v39_advanced_recalculate_model",
        ):
            with st.spinner(_v39_adv_text("\u041f\u0440\u0435\u0438\u0437\u0447\u0438\u0441\u043b\u044f\u0432\u0430\u043d\u0435...", "Recalculating...")):
                ok, output = _v39_adv_run("train")
            st.cache_data.clear()
            training_draws = _v39_adv_parse_int(output, "Training draws")
            candidate_count = _v39_adv_parse_int(output, "Candidate combinations")
            fairness = _v39_adv_parse_float(output, "Fairness p-value")
            if ok:
                st.success(_v39_adv_text("\u0420\u0430\u0437\u0448\u0438\u0440\u0435\u043d\u0438\u044f\u0442 \u043c\u043e\u0434\u0435\u043b \u0435 \u043f\u0440\u0435\u0438\u0437\u0447\u0438\u0441\u043b\u0435\u043d \u0443\u0441\u043f\u0435\u0448\u043d\u043e.", "The advanced model was recalculated successfully."))
                _v39_adv_render_metrics(training_draws, candidate_count, fairness)
                st.info(_v39_adv_text("\u0422\u043e\u043f \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0438\u0442\u0435 \u0441\u0430 \u043e\u0431\u043d\u043e\u0432\u0435\u043d\u0438 \u043f\u043e \u0442\u0435\u043a\u0443\u0449\u0438\u044f \u043d\u0430\u0431\u043e\u0440 \u043e\u0442 \u0434\u0430\u043d\u043d\u0438. \u0422\u043e\u0432\u0430 \u0435 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u043e \u043a\u043b\u0430\u0441\u0438\u0440\u0430\u043d\u0435, \u043d\u0435 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430 \u0441\u044a\u0441 \u0441\u0438\u0433\u0443\u0440\u043d\u043e\u0441\u0442.", "The top recommendations were updated using the current dataset. This is a statistical ranking, not a certain prediction."))
            else:
                st.error(_v39_adv_text("\u041f\u0440\u0435\u0438\u0437\u0447\u0438\u0441\u043b\u044f\u0432\u0430\u043d\u0435\u0442\u043e \u043d\u0435 \u0443\u0441\u043f\u044f.", "Recalculation failed."))
            with st.expander(_v39_adv_text("\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438 \u0434\u0435\u0442\u0430\u0439\u043b\u0438", "Technical details"), expanded=False):
                st.code(_v39_adv_sanitize_output(output)[-5000:])
        st.caption(_v39_adv_text("\u041f\u0440\u0435\u0438\u0437\u0447\u0438\u0441\u043b\u044f\u0432\u0430 \u043f\u043e-\u0442\u0435\u0436\u044a\u043a \u0430\u043d\u0441\u0430\u043c\u0431\u044a\u043b \u0432\u044a\u0440\u0445\u0443 \u0442\u0435\u043a\u0443\u0449\u0438\u044f \u043d\u0430\u0431\u043e\u0440 \u043e\u0442 \u0434\u0430\u043d\u043d\u0438.", "Recalculates a heavier ensemble using the current dataset."))
    with col_check:
        if st.button(
            _v39_adv_text("\u041f\u0443\u0441\u043d\u0438 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430", "Run Historical Check"),
            width="stretch",
            key="v39_advanced_run_backtest",
        ):
            with st.spinner(_v39_adv_text("\u0418\u0437\u043f\u044a\u043b\u043d\u044f\u0432\u0430\u043d\u0435...", "Running...")):
                ok, output = _v39_adv_run("backtest")
            if ok:
                st.success(_v39_adv_text("\u0418\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430\u0442\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0435 \u0437\u0430\u0432\u044a\u0440\u0448\u0435\u043d\u0430 \u0443\u0441\u043f\u0435\u0448\u043d\u043e.", "The historical check completed successfully."))
                st.info(_v39_adv_text("\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430\u0442\u0430 \u0441\u0440\u0430\u0432\u043d\u044f\u0432\u0430 \u043a\u0430\u043a \u0431\u0438 \u0441\u0435 \u0434\u044a\u0440\u0436\u0430\u043b \u043c\u043e\u0434\u0435\u043b\u044a\u0442 \u0432\u044a\u0440\u0445\u0443 \u043c\u0438\u043d\u0430\u043b\u0438 \u0442\u0438\u0440\u0430\u0436\u0438. \u0422\u043e\u0432\u0430 \u043d\u0435 \u0434\u043e\u043a\u0430\u0437\u0432\u0430 \u0431\u044a\u0434\u0435\u0449\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430.", "The check compares how the model would have behaved on past draws. It does not prove future winnings."))
            else:
                st.error(_v39_adv_text("\u0418\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430\u0442\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043d\u0435 \u0443\u0441\u043f\u044f.", "The historical check failed."))
            with st.expander(_v39_adv_text("\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438 \u0434\u0435\u0442\u0430\u0439\u043b\u0438", "Technical details"), expanded=False):
                st.code(_v39_adv_sanitize_output(output)[-5000:])
        st.caption(_v39_adv_text("\u041f\u0440\u043e\u0432\u0435\u0440\u044f\u0432\u0430 \u043c\u043e\u0434\u0435\u043b\u0430 \u043d\u0430\u0437\u0430\u0434 \u0432\u044a\u0432 \u0432\u0440\u0435\u043c\u0435\u0442\u043e \u0432\u044a\u0440\u0445\u0443 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0442\u0438\u0440\u0430\u0436\u0438.", "Checks the model backwards on historical draws."))
    model = _v39_adv_load_model()
    if not model:
        st.info(_v39_adv_text("\u0412\u0441\u0435 \u043e\u0449\u0435 \u043d\u044f\u043c\u0430 \u043d\u0430\u043c\u0435\u0440\u0435\u043d \u0440\u0430\u0437\u0448\u0438\u0440\u0435\u043d \u043c\u043e\u0434\u0435\u043b. \u041d\u0430\u0442\u0438\u0441\u043d\u0438 \u201e\u041f\u0440\u0435\u0438\u0437\u0447\u0438\u0441\u043b\u0438 \u0440\u0430\u0437\u0448\u0438\u0440\u0435\u043d\u0438\u044f \u043c\u043e\u0434\u0435\u043b\u201c.", "No advanced model was found yet. Click 'Recalculate Advanced Model'."))
        return
    _v39_adv_render_overview(model)
    _v39_adv_render_top(model)
    report = REPORTS_DIR / "advanced_backtest_report.md"
    if report.exists():
        with st.expander(_v39_adv_text("\u041e\u0442\u0447\u0435\u0442 \u043e\u0442 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430\u0442\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430", "Historical Check Report"), expanded=False):
            render_report_file(report)
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
_V39_PRED_GENERATE_SCRIPT = 'predict_next_draw.py'
_V39_PRED_GENERATE_SCRIPT = ''
def _v39_pred_lang():
    try:
        return st.session_state.get("language", globals().get("LANG", "bg"))
    except Exception:
        return globals().get("LANG", "bg")
def _v39_pred_text(bg, en):
    return bg if _v39_pred_lang() == "bg" else en
def _v39_pred_odds():
    return "1:13,983,816"
def _v39_pred_sanitize_output(output):
    if not output:
        return _v39_pred_text("\u041d\u044f\u043c\u0430 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438 \u0438\u0437\u0445\u043e\u0434.", "No technical output.")
    clean = str(output).replace(chr(0xFFFD), "?")
    clean = re.sub(r"\?{3,}", _v39_pred_text("[\u043d\u0435\u0440\u0430\u0437\u0447\u0435\u0442\u0435\u043d \u0442\u0435\u043a\u0441\u0442]", "[unreadable text]"), clean)
    return clean
def _v39_pred_is_bad_script_path(p):
    rel = str(p.relative_to(ROOT)).lower().replace("\\", "/")
    name = p.name.lower()
    blocked_parts = [
        ".venv/",
        "__pycache__",
        ".v39_local_backups",
        "backup",
        "test",
        "tests/",
        "smoke",
        "validate",
        "checker",
        "audit",
        "streamlit_app.py",
    ]
    return any(part in rel or part in name for part in blocked_parts)
def _v39_pred_find_script():
    known_names = [
        "prediction_engine_v36.py",
        "run_prediction_engine_v36.py",
        "generate_prediction_v36.py",
        "generate_predictions_v36.py",
        "generate_prediction.py",
        "generate_predictions.py",
        "run_prediction.py",
        "run_predictions.py",
        "create_prediction.py",
        "train_prediction_engine.py",
    ]
    if _V39_PRED_GENERATE_SCRIPT:
        known_names.insert(0, _V39_PRED_GENERATE_SCRIPT)
    seen = set()
    candidates = []
    for name in known_names:
        if not name or name in seen:
            continue
        seen.add(name)
        for p in [ROOT / name, ROOT / "scripts" / name, ROOT / "src" / name]:
            if p.exists() and p.is_file() and not _v39_pred_is_bad_script_path(p):
                candidates.append(p)
    for p in ROOT.rglob("*.py"):
        if not p.is_file() or _v39_pred_is_bad_script_path(p):
            continue
        name = p.name.lower()
        if (
            "prediction" in name
            or "forecast" in name
            or "predict" in name
            or "v36" in name
        ):
            if p not in candidates:
                candidates.append(p)
    # Prefer files that look like real generators, not helpers.
    def rank(p):
        name = p.name.lower()
        score = 0
        if "v36" in name:
            score -= 30
        if "engine" in name:
            score -= 20
        if "generate" in name:
            score -= 15
        if "prediction" in name:
            score -= 10
        if "run" in name:
            score -= 5
        if "train" in name:
            score += 5
        return score, len(str(p))
    candidates = sorted(candidates, key=rank)
    return candidates[0] if candidates else None
def _v39_pred_run_generate():
    model = _v39_pred_load_model()
    if model:
        return True, _v39_pred_text(
            "\u0417\u0430\u0440\u0435\u0434\u0435\u043d\u0430 \u0435 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0430\u0442\u0430 \u0437\u0430\u043f\u0430\u0437\u0435\u043d\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430.",
            "The latest saved prediction was loaded.",
        )
    return False, _v39_pred_text(
        "\u041d\u044f\u043c\u0430 \u043d\u0430\u043c\u0435\u0440\u0435\u043d\u0430 \u0437\u0430\u043f\u0430\u0437\u0435\u043d\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430.",
        "No saved prediction was found.",
    )
def _v39_pred_load_json(p):
    import json
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
def _v39_pred_load_model():
    if not MODELS_DIR.exists():
        return {}
    preferred = [
        "lottery_prediction_model.json",
        "lottery_prediction_model_v36.json",
        "prediction_model.json",
        "prediction_engine_model.json",
    ]
    for name in preferred:
        p = MODELS_DIR / name
        if p.exists():
            model = _v39_pred_load_json(p)
            if model:
                return model
    candidates = list(MODELS_DIR.glob("*prediction*.json"))
    versions = MODELS_DIR / "versions"
    if versions.exists():
        candidates.extend(list(versions.glob("*prediction*.json")))
    candidates = sorted(candidates, key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    for p in candidates:
        model = _v39_pred_load_json(p)
        if model:
            return model
    return {}
def _v39_pred_model_value(model, *keys):
    if not isinstance(model, dict):
        return None
    for key in keys:
        value = model.get(key)
        if value is not None:
            return value
    return None
def _v39_pred_is_ticket(value):
    if not isinstance(value, list) or len(value) != 6:
        return False
    try:
        nums = [int(x) for x in value]
    except Exception:
        return False
    return len(set(nums)) == 6 and all(1 <= n <= 49 for n in nums)
def _v39_pred_find_first_ticket(obj):
    if _v39_pred_is_ticket(obj):
        return sorted([int(x) for x in obj])
    if isinstance(obj, dict):
        priority_keys = [
            "numbers",
            "combination",
            "ticket",
            "values",
            "main_prediction",
            "main_recommendation",
            "best_prediction",
            "best_recommendation",
            "prediction",
            "recommendation",
            "top_prediction",
            "top_recommendation",
        ]
        for key in priority_keys:
            if key in obj:
                found = _v39_pred_find_first_ticket(obj.get(key))
                if found:
                    return found
        for value in obj.values():
            found = _v39_pred_find_first_ticket(value)
            if found:
                return found
    if isinstance(obj, list):
        for value in obj:
            found = _v39_pred_find_first_ticket(value)
            if found:
                return found
    return []
def _v39_pred_find_first_score(obj):
    preferred_keys = [
        "model_score",
        "prediction_score",
        "score",
        "confidence_score",
        "confidence",
        "final_score",
        "overall_score",
        "rating",
        "statistical_score",
    ]
    def normalize(value):
        try:
            num = float(value)
        except Exception:
            return None
        if 0 < num <= 1:
            return num * 100
        return num
    if isinstance(obj, dict):
        for key in preferred_keys:
            if key in obj:
                num = normalize(obj.get(key))
                if num is not None:
                    return num
        for key, value in obj.items():
            lowered = str(key).lower()
            if any(word in lowered for word in ["score", "confidence", "rating"]):
                num = normalize(value)
                if num is not None:
                    return num
        for value in obj.values():
            found = _v39_pred_find_first_score(value)
            if found is not None:
                return found
    if isinstance(obj, list):
        for value in obj:
            found = _v39_pred_find_first_score(value)
            if found is not None:
                return found
    return None
def _v39_pred_recommendations(model):
    if not isinstance(model, dict):
        return []
    for key in [
        "recommendations",
        "top_recommendations",
        "prediction",
        "predictions",
        "ranked_recommendations",
        "top_predictions",
        "main_prediction",
        "main_recommendation",
        "best_prediction",
        "best_recommendation",
    ]:
        value = model.get(key)
        if isinstance(value, list) and value:
            return value
        if isinstance(value, dict):
            return [value]
    ticket = _v39_pred_find_first_ticket(model)
    if ticket:
        return [{"numbers": ticket, "score": _v39_pred_find_first_score(model)}]
    return []
def _v39_pred_numbers(item):
    if isinstance(item, dict):
        for key in ["numbers", "combination", "ticket", "values"]:
            value = item.get(key)
            if isinstance(value, list):
                return sorted([int(x) for x in value]) if _v39_pred_is_ticket(value) else value
    if isinstance(item, list):
        return sorted([int(x) for x in item]) if _v39_pred_is_ticket(item) else item
    return []
def _v39_pred_score(item):
    if isinstance(item, dict):
        for key in ["score", "confidence", "confidence_score", "model_score"]:
            if key in item:
                return item.get(key)
    return None
def _v39_pred_report_score():
    candidates = [
        REPORTS_DIR / "prediction_report.md",
        REPORTS_DIR / "prediction_model_card.md",
        REPORTS_DIR / "prediction_methodology_report.md",
    ]
    patterns = [
        r"\u041c\u043e\u0434\u0435\u043b\u043d\u0430\s+\u043e\u0446\u0435\u043d\u043a\u0430\s*[:\-]\s*([0-9]+(?:\.[0-9]+)?)",
        r"Model\s+score\s*[:\-]\s*([0-9]+(?:\.[0-9]+)?)",
        r"score\s*[:\-]\s*([0-9]+(?:\.[0-9]+)?)",
        r"confidence\s*[:\-]\s*([0-9]+(?:\.[0-9]+)?)",
    ]
    for p in candidates:
        if not p.exists():
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for pattern in patterns:
            match = re.search(pattern, content, flags=re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    if 0 < value <= 1:
                        value *= 100
                    return value
                except Exception:
                    pass
    return None
def _v39_pred_main_result(model):
    recs = _v39_pred_recommendations(model)
    main = recs[0] if recs else {}
    numbers = _v39_pred_numbers(main)
    score = _v39_pred_score(main)
    if not numbers:
        numbers = _v39_pred_find_first_ticket(model)
    if score is None:
        score = _v39_pred_find_first_score(model)
    if score is None:
        score = _v39_pred_report_score()
    return numbers, score
def _v39_pred_score_text(score):
    try:
        return f"{float(score):.2f}/100" if score is not None else "-"
    except Exception:
        return str(score)
def _v39_pred_render_metrics(model):
    training_draws = _v39_pred_model_value(model, "training_draws", "dataset_rows", "rows")
    candidate_count = _v39_pred_model_value(model, "candidate_count", "candidate_combinations")
    c1, c2 = st.columns(2)
    c1.metric(_v39_pred_text("\u041e\u0431\u0443\u0447\u0435\u043d\u0438 \u0442\u0438\u0440\u0430\u0436\u0438", "Training draws"), f"{int(training_draws):,}" if training_draws else "-")
    c2.metric(_v39_pred_text("\u041a\u0430\u043d\u0434\u0438\u0434\u0430\u0442-\u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438", "Candidate combinations"), f"{int(candidate_count):,}" if candidate_count else "-")
    odds_label = _v39_pred_text("\u0420\u0435\u0430\u043b\u0435\u043d \u0448\u0430\u043d\u0441", "Real odds")
    st.markdown(f"**{odds_label}:** `{_v39_pred_odds()}`")
def _v39_pred_render_recommendation(model, title=None):
    numbers, score = _v39_pred_main_result(model)
    if title is None:
        title = _v39_pred_text("\u041f\u0440\u0435\u043f\u043e\u0440\u044a\u0447\u0430\u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f", "Recommended Combination")
    st.markdown("### " + title)
    if numbers:
        st.markdown(format_number_pills(numbers), unsafe_allow_html=True)
    else:
        st.info(_v39_pred_text(
            "\u041d\u0435 \u0441\u0430 \u043d\u0430\u043c\u0435\u0440\u0435\u043d\u0438 \u0447\u0438\u0441\u043b\u0430 \u0432 \u0437\u0430\u043f\u0438\u0441\u0430\u043d\u0438\u044f \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0435\u043d \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442.",
            "No numbers were found in the saved prediction result.",
        ))
    score_label = _v39_pred_text("\u041c\u043e\u0434\u0435\u043b\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430", "Model score")
    st.markdown(f"**{score_label}:** `{_v39_pred_score_text(score)}`")
def _v39_pred_render_plain_explanation(model):
    numbers, score = _v39_pred_main_result(model)
    st.markdown("### " + _v39_pred_text(
        "\u041e\u0431\u044f\u0441\u043d\u0435\u043d\u0438\u0435 \u043d\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430\u0442\u0430",
        "Prediction Explanation",
    ))
    st.markdown(_v39_pred_text(
        "\u0422\u043e\u0432\u0430 \u043d\u0435 \u0435 \u043e\u0431\u0435\u0449\u0430\u043d\u0438\u0435, \u0447\u0435 \u0447\u0438\u0441\u043b\u0430\u0442\u0430 \u0449\u0435 \u0441\u0435 \u043f\u0430\u0434\u043d\u0430\u0442. \u041f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u0435\u0442\u043e \u043f\u0440\u043e\u0441\u0442\u043e \u043a\u043b\u0430\u0441\u0438\u0440\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u0435\u043d\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u043f\u043e \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043a\u0440\u0438\u0442\u0435\u0440\u0438\u0438.",
        "This is not a promise that the numbers will be drawn. The app simply ranks checked combinations using statistical criteria.",
    ))
    _v39_pred_render_metrics(model)
    _v39_pred_render_recommendation(model)
    st.info(_v39_pred_text(
        "\u041c\u043e\u0434\u0435\u043b\u043d\u0430\u0442\u0430 \u043e\u0446\u0435\u043d\u043a\u0430 \u0435 \u0441\u0430\u043c\u043e \u0437\u0430 \u0441\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u0435 \u043c\u0435\u0436\u0434\u0443 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442-\u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438. \u0420\u0435\u0430\u043b\u043d\u0438\u044f\u0442 \u0448\u0430\u043d\u0441 \u043e\u0441\u0442\u0430\u0432\u0430 1:13,983,816.",
        "The model score is only for comparing candidate combinations. The real odds remain 1:13,983,816.",
    ))
def page_prediction() -> None:
    render_header()
    st.markdown("## " + _v39_pred_text("\u041f\u0440\u043e\u0433\u043d\u043e\u0437\u0430", "Prediction"))
    st.markdown(
        '<div class="warning-soft">'
        + _v39_pred_text(
            "\u0412\u0430\u0436\u043d\u043e: \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430\u0442\u0430 \u0435 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u043e \u043a\u043b\u0430\u0441\u0438\u0440\u0430\u043d\u0435 \u043d\u0430 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442-\u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438. \u0422\u044f \u043d\u0435 \u043f\u0440\u043e\u043c\u0435\u043d\u044f \u0440\u0435\u0430\u043b\u043d\u0438\u044f \u0448\u0430\u043d\u0441 \u0437\u0430 \u0442\u043e\u0447\u043d\u0430 6/49 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0438 \u043d\u0435 \u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f \u0437\u0430 \u0431\u044a\u0434\u0435\u0449 \u0442\u0438\u0440\u0430\u0436.",
            "Important: the prediction is a statistical ranking of candidate combinations. It does not change the real odds of an exact 6/49 combination and does not guarantee a future draw.",
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    generated_now = False
    col_generate, col_explain = st.columns(2)
    with col_generate:
        if st.button(
            _v39_pred_text("\u0417\u0430\u0440\u0435\u0434\u0438 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0430\u0442\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430", "Load Latest Prediction"),
            width="stretch",
            key="v39_generate_prediction_button",
        ):
            with st.spinner(_v39_pred_text("\u0417\u0430\u0440\u0435\u0436\u0434\u0430\u043d\u0435...", "Loading...")):
                ok, output = _v39_pred_run_generate()
            st.cache_data.clear()
            model = _v39_pred_load_model()
            generated_now = True
            if ok:
                st.success(_v39_pred_text(
                    "\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0430\u0442\u0430 \u0437\u0430\u043f\u0430\u0437\u0435\u043d\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430 \u0435 \u0437\u0430\u0440\u0435\u0434\u0435\u043d\u0430 \u0443\u0441\u043f\u0435\u0448\u043d\u043e.",
                    "The latest saved prediction was loaded successfully.",
                ))
                _v39_pred_render_metrics(model)
                _v39_pred_render_recommendation(model)
                st.info(_v39_pred_text(
                    "\u0420\u0435\u0437\u0443\u043b\u0442\u0430\u0442\u044a\u0442 \u0435 \u043e\u0431\u043d\u043e\u0432\u0435\u043d \u043f\u043e \u0442\u0435\u043a\u0443\u0449\u0438\u044f \u043d\u0430\u0431\u043e\u0440 \u043e\u0442 \u0434\u0430\u043d\u043d\u0438. \u0422\u043e\u0432\u0430 \u0435 \u043c\u043e\u0434\u0435\u043b\u043d\u043e \u043a\u043b\u0430\u0441\u0438\u0440\u0430\u043d\u0435, \u043d\u0435 \u043e\u0431\u0435\u0449\u0430\u043d\u0438\u0435 \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430.",
                    "The result was updated using the current dataset. This is model-based ranking, not a promise of winning.",
                ))
            else:
                fallback_model = _v39_pred_load_model()
                if fallback_model:
                    st.warning(_v39_pred_text(
                        "\u041d\u043e\u0432\u043e\u0442\u043e \u0433\u0435\u043d\u0435\u0440\u0438\u0440\u0430\u043d\u0435 \u043d\u0435 \u0443\u0441\u043f\u044f, \u043d\u043e \u0435 \u0437\u0430\u0440\u0435\u0434\u0435\u043d\u0430 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0430\u0442\u0430 \u0437\u0430\u043f\u0430\u0437\u0435\u043d\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430.",
                        "New generation failed, but the latest saved prediction was loaded."
                    ))
                    _v39_pred_render_metrics(fallback_model)
                    _v39_pred_render_recommendation(fallback_model)
                    st.info(_v39_pred_text(
                        "\u041f\u043e\u043a\u0430\u0437\u0430\u043d\u0430\u0442\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0438\u0434\u0432\u0430 \u043e\u0442 \u043d\u0430\u0439-\u043d\u043e\u0432\u0438\u044f \u0437\u0430\u043f\u0430\u0437\u0435\u043d \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0435\u043d \u043c\u043e\u0434\u0435\u043b.",
                        "The shown combination comes from the latest saved prediction model."
                    ))
                else:
                    st.error(_v39_pred_text("\u0413\u0435\u043d\u0435\u0440\u0438\u0440\u0430\u043d\u0435\u0442\u043e \u043d\u0435 \u0443\u0441\u043f\u044f.", "Generation failed."))
            with st.expander(_v39_pred_text("\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438 \u0434\u0435\u0442\u0430\u0439\u043b\u0438", "Technical details"), expanded=False):
                st.code(_v39_pred_sanitize_output(output)[-5000:])
        st.caption(_v39_pred_text(
            "\u0417\u0430\u0440\u0435\u0436\u0434\u0430 \u043d\u0430\u0439-\u043d\u043e\u0432\u0430\u0442\u0430 \u0437\u0430\u043f\u0430\u0437\u0435\u043d\u0430 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430.",
            "Loads the latest saved statistical prediction.",
        ))
    with col_explain:
        if st.button(
            _v39_pred_text("\u041e\u0431\u044f\u0441\u043d\u0438 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430\u0442\u0430", "Explain Prediction"),
            width="stretch",
            key="v39_explain_prediction_button",
        ):
            st.session_state["v39_prediction_explain_visible"] = not st.session_state.get("v39_prediction_explain_visible", False)
        st.caption(_v39_pred_text(
            "\u041e\u0431\u044f\u0441\u043d\u044f\u0432\u0430 \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442\u0430 \u043d\u0430 \u043d\u043e\u0440\u043c\u0430\u043b\u0435\u043d \u0435\u0437\u0438\u043a, \u0431\u0435\u0437 \u0442\u0435\u0445\u043d\u0438\u0447\u043d\u0438 \u0442\u0435\u0440\u043c\u0438\u043d\u0438.",
            "Explains the result in plain language without technical wording.",
        ))
    model = _v39_pred_load_model()
    if st.session_state.get("v39_prediction_explain_visible", False):
        _v39_pred_render_plain_explanation(model)
    elif not generated_now:
        if model:
            _v39_pred_render_metrics(model)
            _v39_pred_render_recommendation(model)
        else:
            st.info(_v39_pred_text(
                "\u0412\u0441\u0435 \u043e\u0449\u0435 \u043d\u044f\u043c\u0430 \u043d\u0430\u043c\u0435\u0440\u0435\u043d \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0435\u043d \u0440\u0435\u0437\u0443\u043b\u0442\u0430\u0442. \u041d\u0430\u0442\u0438\u0441\u043d\u0438 \u201e\u0417\u0430\u0440\u0435\u0434\u0438 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0430\u0442\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u0430\u201c.",
                "No prediction result was found yet. Click 'Load Latest Prediction'.",
            ))
def report_language() -> str:
    try:
        return st.session_state.get("language", "bg")
    except Exception:
        return "bg"
def localized_2026_partial_update_report() -> str:
    if report_language() == "en":
        return """# Partial 2026 Toto 6/49 Data Update
This report describes the locally provided 2026 Toto 6/49 statistics package added to the project.
- Added 2026 rows: 48
- 2026 data range: 2026-01-04 to 2026-06-18
- Final dataset rows: 10057
- Final year range: 1958-2026
- Duplicate year/draw/position keys: 0
- Repeated full number combinations in the whole dataset: 6
Important: 2026 is a partial year and currently includes draws up to 2026-06-18. These data points update the model training dataset, but they do not change the theoretical lottery odds.
"""
    return """# \u0427\u0430\u0441\u0442\u0438\u0447\u043d\u0430 \u0430\u043a\u0442\u0443\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u044f \u043d\u0430 \u0434\u0430\u043d\u043d\u0438\u0442\u0435 \u0437\u0430 2026 \u0433. \u2014 \u0422\u043e\u0442\u043e 6/49
\u0422\u043e\u0437\u0438 \u043e\u0442\u0447\u0435\u0442 \u043e\u043f\u0438\u0441\u0432\u0430 \u0434\u043e\u0431\u0430\u0432\u044f\u043d\u0435\u0442\u043e \u043d\u0430 \u043b\u043e\u043a\u0430\u043b\u043d\u043e \u043f\u0440\u0435\u0434\u043e\u0441\u0442\u0430\u0432\u0435\u043d\u0438\u044f \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u0430\u043a\u0435\u0442 \u0437\u0430 \u0442\u0438\u0440\u0430\u0436\u0438\u0442\u0435 \u043d\u0430 \u0422\u043e\u0442\u043e 6/49 \u043f\u0440\u0435\u0437 2026 \u0433.
- \u0414\u043e\u0431\u0430\u0432\u0435\u043d\u0438 \u0440\u0435\u0434\u043e\u0432\u0435 \u0437\u0430 2026 \u0433.: 48
- \u041f\u0435\u0440\u0438\u043e\u0434 \u043d\u0430 \u0434\u0430\u043d\u043d\u0438\u0442\u0435 \u0437\u0430 2026 \u0433.: 2026-01-04 \u0434\u043e 2026-06-18
- \u041a\u0440\u0430\u0435\u043d \u0431\u0440\u043e\u0439 \u0440\u0435\u0434\u043e\u0432\u0435 \u0432 \u043d\u0430\u0431\u043e\u0440\u0430 \u043e\u0442 \u0434\u0430\u043d\u043d\u0438: 10057
- \u041a\u0440\u0430\u0435\u043d \u0434\u0438\u0430\u043f\u0430\u0437\u043e\u043d \u043d\u0430 \u0433\u043e\u0434\u0438\u043d\u0438\u0442\u0435: 1958\u20132026
- \u0414\u0443\u0431\u043b\u0438\u0440\u0430\u043d\u0438 \u043a\u043b\u044e\u0447\u043e\u0432\u0435 \u0433\u043e\u0434\u0438\u043d\u0430/\u0442\u0438\u0440\u0430\u0436/\u043f\u043e\u0437\u0438\u0446\u0438\u044f: 0
- \u041f\u043e\u0432\u0442\u043e\u0440\u0435\u043d\u0438 \u043f\u044a\u043b\u043d\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u043e\u0442 \u0447\u0438\u0441\u043b\u0430 \u0432 \u0446\u0435\u043b\u0438\u044f \u043d\u0430\u0431\u043e\u0440 \u043e\u0442 \u0434\u0430\u043d\u043d\u0438: 6
\u0412\u0430\u0436\u043d\u043e: 2026 \u0433. \u0435 \u0447\u0430\u0441\u0442\u0438\u0447\u043d\u0430 \u0433\u043e\u0434\u0438\u043d\u0430 \u0438 \u043a\u044a\u043c \u043c\u043e\u043c\u0435\u043d\u0442\u0430 \u0432\u043a\u043b\u044e\u0447\u0432\u0430 \u0442\u0438\u0440\u0430\u0436\u0438 \u0434\u043e 2026-06-18. \u0422\u0435\u0437\u0438 \u0434\u0430\u043d\u043d\u0438 \u043e\u0431\u043d\u043e\u0432\u044f\u0432\u0430\u0442 \u043d\u0430\u0431\u043e\u0440\u0430 \u043e\u0442 \u0434\u0430\u043d\u043d\u0438 \u0437\u0430 \u043e\u0431\u0443\u0447\u0435\u043d\u0438\u0435 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435, \u043d\u043e \u043d\u0435 \u043f\u0440\u043e\u043c\u0435\u043d\u044f\u0442 \u0442\u0435\u043e\u0440\u0435\u0442\u0438\u0447\u043d\u0438\u0442\u0435 \u0432\u0435\u0440\u043e\u044f\u0442\u043d\u043e\u0441\u0442\u0438 \u0432 \u043b\u043e\u0442\u0430\u0440\u0438\u044f\u0442\u0430.
"""

# STEP87_8_REPORT_DISPLAY_POLISH_START
def _step87_8_u(raw: str) -> str:
    return raw.encode("ascii").decode("unicode_escape")


def _step87_8_report_label_mapping() -> dict:
    return {
        "2026_partial_update_report.md": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043e\u0431\u043d\u043e\u0432\u044f\u0432\u0430\u043d\u0435 \u043d\u0430 \u0434\u0430\u043d\u043d\u0438\u0442\u0435 \u0437\u0430 2026"),
        "historical_report.md": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u043e\u0442 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),

        "advanced_ensemble_report.md": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0440\u0430\u0437\u0448\u0438\u0440\u0435\u043d \u0430\u043d\u0441\u0430\u043c\u0431\u044a\u043b"),
        "advanced_backtest_report.md": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u043e\u0442 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),

        "backtest_report.md": _step87_8_u(r"\u0427\u0435\u0441\u0442\u043e\u0442\u0435\u043d \u043e\u0442\u0447\u0435\u0442 \u043e\u0442 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),
        "frequency_model_report.md": _step87_8_u(r"\u0427\u0435\u0441\u0442\u043e\u0442\u0435\u043d \u043e\u0442\u0447\u0435\u0442 \u043e\u0442 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),

        "cold_model_report.md": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0435\u043d \u043c\u043e\u0434\u0435\u043b"),
        "cold_backtest_report.md": _step87_8_u(r"\u0421\u0442\u0443\u0434\u0435\u043d \u043c\u043e\u0434\u0435\u043b \u2014 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),

        "combined_model_report.md": _step87_8_u(r"\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u043e\u0442\u0447\u0435\u0442 \u043e\u0442 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),
        "combined_backtest_report.md": _step87_8_u(r"\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u043e\u0442\u0447\u0435\u0442 \u043e\u0442 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),

        "gap_backtest_report.md": _step87_8_u(r"\u0418\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0435\u043d \u043c\u043e\u0434\u0435\u043b \u2014 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),
        "middle_backtest_report.md": _step87_8_u(r"\u0411\u0430\u043b\u0430\u043d\u0441\u0438\u0440\u0430\u043d \u043c\u043e\u0434\u0435\u043b \u2014 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),

        "ml_extensions_report.md": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u041c\u041b \u0440\u0430\u0437\u0448\u0438\u0440\u0435\u043d\u0438\u044f"),
        "ml_extensions_backtest_report.md": _step87_8_u(r"\u041c\u041b \u043e\u0442\u0447\u0435\u0442 \u043e\u0442 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"),

        "prediction_report.md": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u043d\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u043d\u0438\u044f \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0441\u043b\u043e\u0439"),
        "prediction_model_card.md": _step87_8_u(r"\u041a\u0430\u0440\u0442\u0430 \u043d\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u043d\u0438\u044f \u043c\u043e\u0434\u0435\u043b"),
        "prediction_methodology_report.md": _step87_8_u(r"\u041c\u0435\u0442\u043e\u0434\u043e\u043b\u043e\u0433\u0438\u044f \u043d\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u043d\u0438\u044f \u043c\u043e\u0434\u0435\u043b"),
        "combined_strategy_report.md": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d\u0430 \u0441\u0442\u0440\u0430\u0442\u0435\u0433\u0438\u044f"),
        "data_audit_report.md": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043d\u0430 \u0434\u0430\u043d\u043d\u0438\u0442\u0435"),
        "data_import_report.md": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0438\u043c\u043f\u043e\u0440\u0442 \u043d\u0430 \u0434\u0430\u043d\u043d\u0438"),
        "gap_model_report.md": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0435\u043d \u043c\u043e\u0434\u0435\u043b"),
        "middle_model_report.md": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0431\u0430\u043b\u0430\u043d\u0441\u0438\u0440\u0430\u043d \u043c\u043e\u0434\u0435\u043b"),
        "ml_classification_report.md": _step87_8_u(r"\u041c\u041b \u043e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043a\u043b\u0430\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f"),
        "ml_clustering_report.md": _step87_8_u(r"\u041c\u041b \u043e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043a\u043b\u044a\u0441\u0442\u0435\u0440\u0438\u0437\u0430\u0446\u0438\u044f"),
        "ml_dimensionality_reduction_report.md": _step87_8_u(r"\u041c\u041b \u043e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0440\u0435\u0434\u0443\u043a\u0446\u0438\u044f \u043d\u0430 \u0440\u0430\u0437\u043c\u0435\u0440\u043d\u043e\u0441\u0442\u0442\u0430"),
        "ml_2d_map_report.md": _step87_8_u(r"\u041c\u041b \u043e\u0442\u0447\u0435\u0442 \u0437\u0430 2D \u043a\u0430\u0440\u0442\u0430"),
    }


def _step87_8_report_display_name(value) -> str:
    import re as _re

    try:
        name = value.name
    except Exception:
        name = str(value or "")

    name = str(name).replace("\\", "/").split("/")[-1].strip()
    labels = _step87_8_report_label_mapping()

    if name in labels:
        return labels[name]

    stem = name
    if stem.endswith(".md"):
        stem = stem[:-3]
    if stem.endswith(".json"):
        return _step87_8_u(r"\u041c\u043e\u0434\u0435\u043b\u0435\u043d \u0438\u0437\u0442\u043e\u0447\u043d\u0438\u043a")

    exact_topics = {
        "decision_recommendation": _step87_8_u(r"\u0420\u0435\u0448\u0435\u043d\u0438\u0435 \u0438 \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0430"),
        "final_play_plan": _step87_8_u(r"\u0424\u0438\u043d\u0430\u043b\u0435\u043d \u043f\u043b\u0430\u043d \u0437\u0430 \u0438\u0433\u0440\u0430"),
        "ticket_pack_export": _step87_8_u(r"\u0415\u043a\u0441\u043f\u043e\u0440\u0442 \u0438 \u0438\u0437\u043f\u044a\u043b\u043d\u0435\u043d\u0438\u0435 \u043d\u0430 \u043f\u0430\u043a\u0435\u0442\u0430"),
        "final_system_audit": _step87_8_u(r"\u0424\u0438\u043d\u0430\u043b\u0435\u043d \u0441\u0438\u0441\u0442\u0435\u043c\u0435\u043d \u043e\u0434\u0438\u0442"),
        "final_ux_navigation": _step87_8_u(r"\u0424\u0438\u043d\u0430\u043b\u043d\u0430 UX \u043d\u0430\u0432\u0438\u0433\u0430\u0446\u0438\u044f"),
        "final_release": _step87_8_u(r"\u0424\u0438\u043d\u0430\u043b\u0435\u043d release \u043f\u0430\u043a\u0435\u0442"),
        "final_user_manual": _step87_8_u(r"\u0424\u0438\u043d\u0430\u043b\u043d\u043e \u043f\u043e\u0442\u0440\u0435\u0431\u0438\u0442\u0435\u043b\u0441\u043a\u043e \u0440\u044a\u043a\u043e\u0432\u043e\u0434\u0441\u0442\u0432\u043e"),
        "model_comparison": _step87_8_u(r"\u0421\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u0435 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435"),
        "neural_epoch_comparison": _step87_8_u(r"\u0421\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u0435 \u043d\u0430 \u043d\u0435\u0432\u0440\u043e\u043d\u043d\u0438 \u0435\u043f\u043e\u0445\u0438"),
        "model_registry": _step87_8_u(r"\u0420\u0435\u0433\u0438\u0441\u0442\u044a\u0440 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435"),
        "combined_strategy": _step87_8_u(r"\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d\u0430 \u0441\u0442\u0440\u0430\u0442\u0435\u0433\u0438\u044f"),
        "data_audit": _step87_8_u(r"\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043d\u0430 \u0434\u0430\u043d\u043d\u0438\u0442\u0435"),
        "data_import": _step87_8_u(r"\u0418\u043c\u043f\u043e\u0440\u0442 \u043d\u0430 \u0434\u0430\u043d\u043d\u0438"),
        "gap_model": _step87_8_u(r"\u0418\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0435\u043d \u043c\u043e\u0434\u0435\u043b"),
        "middle_model": _step87_8_u(r"\u0411\u0430\u043b\u0430\u043d\u0441\u0438\u0440\u0430\u043d \u043c\u043e\u0434\u0435\u043b"),
        "ml_classification": _step87_8_u(r"\u041c\u041b \u043a\u043b\u0430\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f"),
        "ml_clustering": _step87_8_u(r"\u041c\u041b \u043a\u043b\u044a\u0441\u0442\u0435\u0440\u0438\u0437\u0430\u0446\u0438\u044f"),
        "ml_dimensionality_reduction": _step87_8_u(r"\u041c\u041b \u0440\u0435\u0434\u0443\u043a\u0446\u0438\u044f \u043d\u0430 \u0440\u0430\u0437\u043c\u0435\u0440\u043d\u043e\u0441\u0442\u0442\u0430"),
    }

    topic = stem

    version_match = _re.match(r"^v\d+_(.+?)_summary$", topic)
    if version_match:
        topic = version_match.group(1)
        if topic in exact_topics:
            return _step87_8_u(r"\u041e\u0431\u043e\u0431\u0449\u0435\u043d \u043e\u0442\u0447\u0435\u0442 \u2014 ") + exact_topics[topic]

    suffixes = [
        "_summary",
        "_report",
        "_backtest",
        "_model_card",
        "_methodology",
    ]

    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            if topic.endswith(suffix):
                topic = topic[: -len(suffix)]
                changed = True

    if topic in exact_topics:
        return _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u2014 ") + exact_topics[topic]

    phrase_map = {
        "dimensionality_reduction": _step87_8_u(r"\u0440\u0435\u0434\u0443\u043a\u0446\u0438\u044f \u043d\u0430 \u0440\u0430\u0437\u043c\u0435\u0440\u043d\u043e\u0441\u0442\u0442\u0430"),
        "decision_recommendation": _step87_8_u(r"\u0440\u0435\u0448\u0435\u043d\u0438\u0435 \u0438 \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0430"),
        "final_play_plan": _step87_8_u(r"\u0444\u0438\u043d\u0430\u043b\u0435\u043d \u043f\u043b\u0430\u043d \u0437\u0430 \u0438\u0433\u0440\u0430"),
        "ticket_pack": _step87_8_u(r"\u043f\u0430\u043a\u0435\u0442 \u0444\u0438\u0448\u043e\u0432\u0435"),
        "model_registry": _step87_8_u(r"\u0440\u0435\u0433\u0438\u0441\u0442\u044a\u0440 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435"),
        "system_audit": _step87_8_u(r"\u0441\u0438\u0441\u0442\u0435\u043c\u0435\u043d \u043e\u0434\u0438\u0442"),
        "data_audit": _step87_8_u(r"\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043d\u0430 \u0434\u0430\u043d\u043d\u0438\u0442\u0435"),
        "data_import": _step87_8_u(r"\u0438\u043c\u043f\u043e\u0440\u0442 \u043d\u0430 \u0434\u0430\u043d\u043d\u0438"),
    }

    for old, new in phrase_map.items():
        topic = topic.replace(old, new.replace(" ", "_"))

    token_map = {
        "v": "",
        "final": _step87_8_u(r"\u0444\u0438\u043d\u0430\u043b\u0435\u043d"),
        "play": _step87_8_u(r"\u0438\u0433\u0440\u0430"),
        "plan": _step87_8_u(r"\u043f\u043b\u0430\u043d"),
        "decision": _step87_8_u(r"\u0440\u0435\u0448\u0435\u043d\u0438\u0435"),
        "recommendation": _step87_8_u(r"\u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0430"),
        "ticket": _step87_8_u(r"\u0444\u0438\u0448"),
        "pack": _step87_8_u(r"\u043f\u0430\u043a\u0435\u0442"),
        "export": _step87_8_u(r"\u0435\u043a\u0441\u043f\u043e\u0440\u0442"),
        "system": _step87_8_u(r"\u0441\u0438\u0441\u0442\u0435\u043c\u0435\u043d"),
        "audit": _step87_8_u(r"\u043e\u0434\u0438\u0442"),
        "ux": "UX",
        "navigation": _step87_8_u(r"\u043d\u0430\u0432\u0438\u0433\u0430\u0446\u0438\u044f"),
        "release": "release",
        "user": _step87_8_u(r"\u043f\u043e\u0442\u0440\u0435\u0431\u0438\u0442\u0435\u043b\u0441\u043a\u043e"),
        "manual": _step87_8_u(r"\u0440\u044a\u043a\u043e\u0432\u043e\u0434\u0441\u0442\u0432\u043e"),
        "model": _step87_8_u(r"\u043c\u043e\u0434\u0435\u043b"),
        "comparison": _step87_8_u(r"\u0441\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u0435"),
        "neural": _step87_8_u(r"\u043d\u0435\u0432\u0440\u043e\u043d\u043d\u0438"),
        "epoch": _step87_8_u(r"\u0435\u043f\u043e\u0445\u0438"),
        "registry": _step87_8_u(r"\u0440\u0435\u0433\u0438\u0441\u0442\u044a\u0440"),
        "combined": _step87_8_u(r"\u043a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d"),
        "strategy": _step87_8_u(r"\u0441\u0442\u0440\u0430\u0442\u0435\u0433\u0438\u044f"),
        "data": _step87_8_u(r"\u0434\u0430\u043d\u043d\u0438"),
        "import": _step87_8_u(r"\u0438\u043c\u043f\u043e\u0440\u0442"),
        "gap": _step87_8_u(r"\u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0435\u043d"),
        "middle": _step87_8_u(r"\u0431\u0430\u043b\u0430\u043d\u0441\u0438\u0440\u0430\u043d"),
        "classification": _step87_8_u(r"\u043a\u043b\u0430\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f"),
        "clustering": _step87_8_u(r"\u043a\u043b\u044a\u0441\u0442\u0435\u0440\u0438\u0437\u0430\u0446\u0438\u044f"),
        "ml": _step87_8_u(r"\u041c\u041b"),
    }

    words = []
    for part in topic.replace("-", "_").split("_"):
        if not part:
            continue
        words.append(token_map.get(part, part))

    cleaned = " ".join(words).strip()
    if not cleaned:
        return name

    cleaned = cleaned[:1].upper() + cleaned[1:]
    return _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u2014 ") + cleaned


def _step87_8_polish_report_text(content: str) -> str:
    import re as _re

    display_text = str(content or "")

    def repl_filename(match):
        return _step87_8_report_display_name(match.group(0))

    display_text = _re.sub(r"\b[A-Za-z0-9][A-Za-z0-9_\-]*\.md\b", repl_filename, display_text)
    display_text = _re.sub(r"\b[A-Za-z0-9][A-Za-z0-9_\-]*\.json\b", repl_filename, display_text)

    report_prefix = _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442: ")

    title_map = {
        "combined strategy report": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d\u0430 \u0441\u0442\u0440\u0430\u0442\u0435\u0433\u0438\u044f"),
        "data audit report": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043d\u0430 \u0434\u0430\u043d\u043d\u0438\u0442\u0435"),
        "data import report": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0438\u043c\u043f\u043e\u0440\u0442 \u043d\u0430 \u0434\u0430\u043d\u043d\u0438"),
        "gap model report": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0435\u043d \u043c\u043e\u0434\u0435\u043b"),
        "middle model report": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0431\u0430\u043b\u0430\u043d\u0441\u0438\u0440\u0430\u043d \u043c\u043e\u0434\u0435\u043b"),
        "ml classification report": _step87_8_u(r"\u041c\u041b \u043e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043a\u043b\u0430\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f"),
        "ml clustering report": _step87_8_u(r"\u041c\u041b \u043e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043a\u043b\u044a\u0441\u0442\u0435\u0440\u0438\u0437\u0430\u0446\u0438\u044f"),
        "ml dimensionality reduction report": _step87_8_u(r"\u041c\u041b \u043e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0440\u0435\u0434\u0443\u043a\u0446\u0438\u044f \u043d\u0430 \u0440\u0430\u0437\u043c\u0435\u0440\u043d\u043e\u0441\u0442\u0442\u0430"),
        "ml 2d map report": _step87_8_u(r"\u041c\u041b \u043e\u0442\u0447\u0435\u0442 \u0437\u0430 2D \u043a\u0430\u0440\u0442\u0430"),
        "advanced ensemble report": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0440\u0430\u0437\u0448\u0438\u0440\u0435\u043d \u0430\u043d\u0441\u0430\u043c\u0431\u044a\u043b"),
        "cold model report": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0435\u043d \u043c\u043e\u0434\u0435\u043b"),
        "frequency model report": _step87_8_u(r"\u0427\u0435\u0441\u0442\u043e\u0442\u0435\u043d \u043e\u0442\u0447\u0435\u0442"),
        "combined model report": _step87_8_u(r"\u041a\u043e\u043c\u0431\u0438\u043d\u0438\u0440\u0430\u043d \u043e\u0442\u0447\u0435\u0442"),
        "model refresh report": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043e\u0431\u043d\u043e\u0432\u044f\u0432\u0430\u043d\u0435 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435"),
        "training report": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043e\u0431\u0443\u0447\u0435\u043d\u0438\u0435"),
        "validation report": _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u0432\u0430\u043b\u0438\u0434\u0430\u0446\u0438\u044f"),
        "model card": _step87_8_u(r"\u041a\u0430\u0440\u0442\u0430 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0430"),
        "prediction model card": _step87_8_u(r"\u041a\u0430\u0440\u0442\u0430 \u043d\u0430 \u043f\u0440\u043e\u0433\u043d\u043e\u0437\u043d\u0438\u044f \u043c\u043e\u0434\u0435\u043b"),
    }

    for old, new in title_map.items():
        display_text = display_text.replace(report_prefix + old, new)

    for old, new in title_map.items():
        display_text = display_text.replace(old, new)

    return display_text

# STEP87_8_REPORT_DISPLAY_POLISH_END


def render_report_file(path: Path) -> None:
    lang = st.session_state.get("language", globals().get("LANG", "bg"))

    try:
        raw_text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        st.error(_step87_8_u(r"\u041d\u0435 \u043c\u043e\u0436\u0435 \u0434\u0430 \u0441\u0435 \u043e\u0442\u0432\u043e\u0440\u0438 \u043e\u0442\u0447\u0435\u0442\u044a\u0442") + f": {exc}")
        return

    title = _step87_8_report_display_name(path)
    display_text = _step87_8_polish_report_text(raw_text)

    st.markdown(f"### {title}")

    if not display_text.strip():
        empty_message = _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442\u044a\u0442 \u0435 \u043f\u0440\u0430\u0437\u0435\u043d.") if lang == "bg" else "The report is empty."
        st.info(empty_message)
    else:
        st.markdown(display_text)

    download_label = _step87_8_u(r"\u0421\u0432\u0430\u043b\u0438 \u043e\u0442\u0447\u0435\u0442\u0430") if lang == "bg" else "Download report"
    st.download_button(
        download_label,
        data=raw_text,
        file_name=path.name,
        mime="text/markdown",
    )


def page_reports() -> None:
    render_header()
    st.markdown("## " + tr("reports"))

    files = sorted(REPORTS_DIR.glob("*.md")) if REPORTS_DIR.exists() else []

    if not files:
        st.info(_step87_8_u(r"\u041d\u044f\u043c\u0430 \u043d\u0430\u043c\u0435\u0440\u0435\u043d\u0438 \u043e\u0442\u0447\u0435\u0442\u0438."))
        return

    selected = st.selectbox(
        _step87_8_u(r"\u041e\u0442\u0447\u0435\u0442"),
        files,
        format_func=_step87_8_report_display_name,
    )

    render_report_file(selected)

def _v39_ml_lang() -> str:
    try:
        return st.session_state.get("language", globals().get("LANG", "bg"))
    except Exception:
        return globals().get("LANG", "bg")
def _v39_ml_text(bg: str, en: str) -> str:
    return bg if _v39_ml_lang() == "bg" else en
def _v39_ml_odds_text() -> str:
    return _v39_ml_text("1:13,983,816", "1:13,983,816")
def _v39_ml_placeholder(kind: str) -> str:
    if kind == "cluster":
        return _v39_ml_text("\u043d\u0435\u0440\u0430\u0437\u0447\u0435\u0442\u0435\u043d \u043a\u043b\u044a\u0441\u0442\u0435\u0440", "unreadable cluster")
    return _v39_ml_text("\u043d\u0435\u0440\u0430\u0437\u0447\u0435\u0442\u0435\u043d \u043a\u043b\u0430\u0441", "unreadable class")
def _v39_ml_translate_value(value: Any) -> str:
    s = str(value or "").strip()
    if not s or chr(0xFFFD) in s or ("?" * 4) in s or chr(0xFFFD) in s:
        return s
    bg_to_en = {
        "\u0441\u0438\u043b\u0435\u043d \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0444\u0438\u0448": "strong statistical ticket",
        "\u043d\u043e\u0440\u043c\u0430\u043b\u0435\u043d \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0444\u0438\u0448": "normal statistical ticket",
        "\u0441\u043b\u0430\u0431 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0444\u0438\u0448": "weak statistical ticket",
        "\u0447\u0435\u0441\u0442\u043e\u0442\u043d\u0438 \u0444\u0438\u0448\u043e\u0432\u0435": "frequency-based tickets",
        "\u0431\u0430\u043b\u0430\u043d\u0441\u0438\u0440\u0430\u043d\u0438 \u0444\u0438\u0448\u043e\u0432\u0435": "balanced tickets",
        "\u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u043d\u0438 \u0444\u0438\u0448\u043e\u0432\u0435": "gap-based tickets",
        "\u0441\u0442\u0440\u0443\u043a\u0442\u0443\u0440\u043d\u0438 \u0444\u0438\u0448\u043e\u0432\u0435": "structure-based tickets",
    }
    en_to_bg = {v: k for k, v in bg_to_en.items()}
    if _v39_ml_lang() == "en":
        return bg_to_en.get(s, s)
    return en_to_bg.get(s, s)
def _v39_ml_clean_label(value: Any, kind: str = "class") -> str:
    s = str(value or "").strip()
    if not s or chr(0xFFFD) in s or ("?" * 4) in s or chr(0xFFFD) in s:
        return _v39_ml_placeholder(kind)
    return _v39_ml_translate_value(s)
def _v39_ml_sanitize_output(output: str) -> str:
    if not output:
        return _v39_ml_text("\u041d\u044f\u043c\u0430 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438 \u0438\u0437\u0445\u043e\u0434.", "No technical output.")
    clean = str(output).replace(chr(0xFFFD), "?")
    class_placeholder = _v39_ml_placeholder("class")
    cluster_placeholder = _v39_ml_placeholder("cluster")
    clean = re.sub(r"class=\?+", f"class={class_placeholder}", clean)
    clean = re.sub(r"cluster=\?+", f"cluster={cluster_placeholder}", clean)
    clean = re.sub(r"class=[^|\n]*\?[^|\n]*", f"class={class_placeholder}", clean)
    clean = re.sub(r"cluster=[^|\n]*\?[^|\n]*", f"cluster={cluster_placeholder}", clean)
    return clean
def _v39_ml_extract_output_int(output: str, label: str) -> Optional[int]:
    try:
        match = re.search(label + r"\s*:\s*([0-9,]+)", output or "", flags=re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    except Exception:
        pass
    return None
def _v39_ml_render_model_explanation() -> None:
    st.markdown("### " + _v39_ml_text("\u041a\u0430\u043a \u0440\u0430\u0431\u043e\u0442\u0438 \u041c\u041b \u043c\u043e\u0434\u0435\u043b\u044a\u0442", "How the ML Model Works"))
    st.markdown(
        _v39_ml_text(
            """
**\u0426\u0435\u043b:** \u043e\u0431\u0440\u0430\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u043d \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043c\u043e\u0434\u0435\u043b \u0437\u0430 \u0430\u043d\u0430\u043b\u0438\u0437 \u043d\u0430 \u0411\u044a\u043b\u0433\u0430\u0440\u0441\u043a\u043e \u0442\u043e\u0442\u043e 6/49.
**\u041a\u0430\u043a\u0432\u043e \u0438\u0437\u043f\u043e\u043b\u0437\u0432\u0430:** \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438 \u0442\u0438\u0440\u0430\u0436\u0438, \u0447\u0435\u0441\u0442\u043e\u0442\u0438, \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438, \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0445\u0430\u0440\u0430\u043a\u0442\u0435\u0440\u0438\u0441\u0442\u0438\u043a\u0438 \u0438 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430.
**\u0422\u0435\u0445\u043d\u0438\u043a\u0438:** \u0438\u043d\u0436\u0435\u043d\u0435\u0440\u0438\u043d\u0433 \u043d\u0430 \u0445\u0430\u0440\u0430\u043a\u0442\u0435\u0440\u0438\u0441\u0442\u0438\u043a\u0438, \u0430\u043d\u0430\u043b\u0438\u0437 \u0432\u044a\u0432 \u0432\u0440\u0435\u043c\u0435\u0432\u0438 \u0440\u0435\u0434, \u043a\u043b\u0430\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f, \u043a\u043b\u044a\u0441\u0442\u0435\u0440\u0438\u0437\u0430\u0446\u0438\u044f, \u0440\u0435\u0434\u0443\u043a\u0446\u0438\u044f \u043d\u0430 \u0440\u0430\u0437\u043c\u0435\u0440\u043d\u043e\u0441\u0442\u0442\u0430 \u0438 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430.
**\u041a\u0430\u043a\u0432\u043e \u043e\u0437\u043d\u0430\u0447\u0430\u0432\u0430 \u043e\u0446\u0435\u043d\u043a\u0430\u0442\u0430:** \u043e\u0442\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u043d\u043e \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u043e \u043a\u043b\u0430\u0441\u0438\u0440\u0430\u043d\u0435 \u043c\u0435\u0436\u0434\u0443 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442-\u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438.
**\u041e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u0435:** \u0432\u0441\u044f\u043a\u0430 6-\u0447\u0438\u0441\u043b\u043e\u0432\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u043e\u0441\u0442\u0430\u0432\u0430 \u0441 \u0440\u0435\u0430\u043b\u0435\u043d \u0448\u0430\u043d\u0441 1 \u043a\u044a\u043c 13,983,816. \u041c\u043e\u0434\u0435\u043b\u044a\u0442 \u043d\u0435 \u0433\u0430\u0440\u0430\u043d\u0442\u0438\u0440\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430 \u0438 \u043d\u0435 \u043f\u0440\u0435\u0434\u0432\u0438\u0436\u0434\u0430 \u0431\u044a\u0434\u0435\u0449 \u0442\u0438\u0440\u0430\u0436 \u0441\u044a\u0441 \u0441\u0438\u0433\u0443\u0440\u043d\u043e\u0441\u0442.
""",
            """
**Purpose:** educational statistical model for Bulgarian Toto 6/49 analysis.
**Inputs:** historical draws, frequencies, combinations, statistical features, and historical checks.
**Techniques:** feature engineering, time-series analysis, classification, clustering, dimensionality reduction, and backtesting.
**Score meaning:** relative statistical ranking between candidate combinations.
**Limitation:** every 6-number combination still has real odds of 1 in 13,983,816. The model does not guarantee a win and does not predict a future draw with certainty.
""",
        )
    )
def _v39_ml_render_main_card(numbers: List[int], score: Optional[float]) -> None:
    title = _v39_ml_text("\u041e\u0441\u043d\u043e\u0432\u043d\u0430 \u041c\u041b \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0430", "Main ML Recommendation")
    meta = _v39_ml_text("\u041a\u043b\u0430\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f + \u043a\u043b\u044a\u0441\u0442\u0435\u0440\u0438\u0437\u0430\u0446\u0438\u044f + 2D \u043a\u0430\u0440\u0442\u0430", "Classification + clustering + 2D map")
    score_label = _v39_ml_text("\u041c\u043e\u0434\u0435\u043b\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430", "Model score")
    odds_label = _v39_ml_text("\u0420\u0435\u0430\u043b\u0435\u043d \u0448\u0430\u043d\u0441 \u0437\u0430 \u0442\u043e\u0447\u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f", "Real odds for the exact combination")
    explanation = _v39_ml_text(
        "\u041c\u043e\u0434\u0435\u043b\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430 \u0437\u0430 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u043e \u0441\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u0435. \u041d\u0435 \u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f \u0437\u0430 \u0431\u044a\u0434\u0435\u0449 \u0442\u0438\u0440\u0430\u0436.",
        "Model score for statistical comparison. It is not a guarantee for a future draw.",
    )
    try:
        score_text = f"{float(score):.2f}/100" if score is not None else "-"
    except Exception:
        score_text = str(score)
    st.markdown(
        f"""
        <div class="model-card">
          <div class="model-title">{title}</div>
          <div class="model-meta">{meta}</div>
          {format_number_pills(numbers)}
          <div><span class="score-badge">{score_label}: {score_text}</span><span class="score-badge">{odds_label}: {_v39_ml_odds_text()}</span></div>
          <div class="small-muted" style="margin-top:10px;">{explanation}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
def page_ml_lab() -> None:
    render_header()
    st.markdown("## " + _v39_ml_text("\u041c\u041b \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f", "ML Laboratory"))
    st.markdown(
        '<div class="warning-soft">' + _v39_ml_text(
            "\u0422\u0430\u0437\u0438 \u0441\u0435\u043a\u0446\u0438\u044f \u0434\u043e\u0431\u0430\u0432\u044f \u043a\u043b\u0430\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f, \u043a\u043b\u044a\u0441\u0442\u0435\u0440\u0438\u0437\u0430\u0446\u0438\u044f, 2D \u043a\u0430\u0440\u0442\u0430 \u0438 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430. \u0422\u043e\u0432\u0430 \u043d\u0435 \u043f\u0440\u043e\u043c\u0435\u043d\u044f \u0440\u0435\u0430\u043b\u043d\u0438\u044f \u0448\u0430\u043d\u0441 \u0437\u0430 \u0442\u043e\u0447\u043d\u0430 6/49 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f.",
            "This section adds classification, clustering, a 2D model map, and historical checks. It does not change the real odds of an exact 6/49 combination.",
        ) + '</div>',
        unsafe_allow_html=True,
    )
    col_train, col_report = st.columns([1.45, 0.55])
    with col_train:
        train_label = _v39_ml_text("\u041f\u0440\u0435\u0438\u0437\u0447\u0438\u0441\u043b\u0438 \u041c\u041b \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0438\u0442\u0435", "Recalculate ML Recommendations")
        if st.button(train_label, width="stretch", key="v39_recalculate_ml_recommendations"):
            with st.spinner(_v39_ml_text("\u041f\u0440\u0435\u0438\u0437\u0447\u0438\u0441\u043b\u044f\u0432\u0430 \u041c\u041b \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0438\u0442\u0435...", "Recalculating ML recommendations...")):
                ok, output = run_script("train_ml_extensions.py")
            st.cache_data.clear()
            refreshed_model = model_json("lottery_ml_extensions_model.json")
            training_draws = refreshed_model.get("training_draws") or _v39_ml_extract_output_int(output, "Training draws") or 0
            candidate_count = refreshed_model.get("candidate_count") or _v39_ml_extract_output_int(output, "Candidate combinations") or 0
            if ok:
                st.success(_v39_ml_text("\u041c\u041b \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0438\u0442\u0435 \u0441\u0430 \u043f\u0440\u0435\u0438\u0437\u0447\u0438\u0441\u043b\u0435\u043d\u0438 \u0443\u0441\u043f\u0435\u0448\u043d\u043e.", "ML recommendations recalculated successfully."))
                c1, c2 = st.columns(2)
                c1.metric(_v39_ml_text("\u041e\u0431\u0443\u0447\u0435\u043d\u0438 \u0442\u0438\u0440\u0430\u0436\u0438", "Training draws"), f"{int(training_draws):,}" if training_draws else "-")
                c2.metric(_v39_ml_text("\u041a\u0430\u043d\u0434\u0438\u0434\u0430\u0442-\u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438", "Candidate combinations"), f"{int(candidate_count):,}" if candidate_count else "-")
                real_odds_label = _v39_ml_text("\u0420\u0435\u0430\u043b\u0435\u043d \u0448\u0430\u043d\u0441", "Real odds")
                st.markdown(f"**{real_odds_label}:** `{_v39_ml_odds_text()}`")
                st.info(_v39_ml_text("\u0422\u043e\u043f \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0438\u0442\u0435 \u0441\u0430 \u043e\u0431\u043d\u043e\u0432\u0435\u043d\u0438 \u043f\u043e \u0442\u0435\u043a\u0443\u0449\u0438\u0442\u0435 \u0434\u0430\u043d\u043d\u0438. \u0422\u043e\u0432\u0430 \u0435 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u043e \u043a\u043b\u0430\u0441\u0438\u0440\u0430\u043d\u0435, \u043d\u0435 \u0433\u0430\u0440\u0430\u043d\u0446\u0438\u044f \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430.", "Top recommendations were updated using the current data. This is a statistical ranking, not a guarantee of winning."))
            else:
                st.error(_v39_ml_text("\u041f\u0440\u0435\u0438\u0437\u0447\u0438\u0441\u043b\u044f\u0432\u0430\u043d\u0435\u0442\u043e \u043d\u0435 \u0443\u0441\u043f\u044f.", "Recalculation failed."))
            with st.expander(_v39_ml_text("\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438 \u0434\u0435\u0442\u0430\u0439\u043b\u0438", "Technical details"), expanded=False):
                st.code(_v39_ml_sanitize_output(output)[-4000:])
        st.caption(_v39_ml_text(
            "\u041f\u0440\u0435\u0438\u0437\u0447\u0438\u0441\u043b\u044f\u0432\u0430 \u041c\u041b \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0438\u0442\u0435 \u0432\u044a\u0440\u0445\u0443 \u0442\u0435\u043a\u0443\u0449\u0438\u044f \u043d\u0430\u0431\u043e\u0440 \u043e\u0442 \u0434\u0430\u043d\u043d\u0438. \u041d\u0435 \u043f\u0440\u043e\u043c\u0435\u043d\u044f \u0440\u0435\u0430\u043b\u043d\u0438\u044f \u043c\u0430\u0442\u0435\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0448\u0430\u043d\u0441 \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430.",
            "Recalculates the ML recommendations using the current dataset. It does not change the real mathematical lottery odds.",
        ))
    with col_report:
        map_label = _v39_ml_text("\u041a\u0430\u043a \u0440\u0430\u0431\u043e\u0442\u0438 \u041c\u041b \u043c\u043e\u0434\u0435\u043b\u044a\u0442", "How the ML Model Works")
        if st.button(map_label, width="stretch", key="v39_toggle_ml_model_explanation"):
            st.session_state["v39_show_ml_model_explanation"] = not st.session_state.get("v39_show_ml_model_explanation", False)
        st.caption(_v39_ml_text(
            "\u041f\u043e\u043a\u0430\u0437\u0432\u0430 \u0440\u0430\u0437\u0431\u0438\u0440\u0430\u0435\u043c\u043e \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u043d\u0430 \u0442\u0435\u0445\u043d\u0438\u043a\u0438\u0442\u0435, \u0446\u0435\u043b\u0442\u0430 \u0438 \u043e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u044f\u0442\u0430 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0430.",
            "Shows a clear explanation of the model purpose, techniques, and limitations.",
        ))
    if st.session_state.get("v39_show_ml_model_explanation", False):
        _v39_ml_render_model_explanation()
    model = model_json("lottery_ml_extensions_model.json")
    if not model:
        st.info(_v39_ml_text("\u041c\u041b \u043c\u043e\u0434\u0435\u043b\u044a\u0442 \u043e\u0449\u0435 \u043d\u0435 \u0435 \u043d\u0430\u043b\u0438\u0447\u0435\u043d. \u041d\u0430\u0442\u0438\u0441\u043d\u0438 '\u041f\u0440\u0435\u0438\u0437\u0447\u0438\u0441\u043b\u0438 \u041c\u041b \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0438\u0442\u0435'.", "The ML model is not available yet. Click 'Recalculate ML Recommendations'."))
        return
    recs = extract_recommendations(model)
    numbers, score = main_recommendation(model)
    _v39_ml_render_main_card(numbers, score)
    summary = model.get("backtest_summary", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(_v39_ml_text("\u041e\u0431\u0443\u0447\u0435\u043d\u0438 \u0442\u0438\u0440\u0430\u0436\u0438", "Training draws"), f"{model.get('training_draws', 0):,}")
    c2.metric(_v39_ml_text("\u041a\u0430\u043d\u0434\u0438\u0434\u0430\u0442-\u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438", "Candidate combinations"), f"{model.get('candidate_count', 0):,}")
    c3.metric(_v39_ml_text("\u0418\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u2014 \u0441\u0440\u0435\u0434\u043d\u043e", "Historical check \u00b7 average"), summary.get("average_matches", "-"))
    c4.metric(_v39_ml_text(">=2 \u0441\u044a\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u044f", ">=2 matches"), f"{summary.get('hit_rate_ge_2', 0)}%")
    tabs = st.tabs([
        _v39_ml_text("\u0422\u043e\u043f \u041c\u041b \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0438", "Top ML Recommendations"),
        _v39_ml_text("\u041a\u043b\u0430\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f", "Classification"),
        _v39_ml_text("\u041a\u043b\u044a\u0441\u0442\u0435\u0440\u0438", "Clusters"),
        _v39_ml_text("2D \u043a\u0430\u0440\u0442\u0430", "2D Map"),
        _v39_ml_text("\u041e\u0442\u0447\u0435\u0442\u0438", "Reports"),
    ])
    with tabs[0]:
        st.markdown("### " + _v39_ml_text("\u0422\u043e\u043f \u041c\u041b \u043f\u0440\u0435\u043f\u043e\u0440\u044a\u043a\u0438", "Top ML Recommendations"))
        for item in recs[:15]:
            item_numbers = item.get("numbers", [])
            item_score = item.get("confidence_score")
            classification = _v39_ml_clean_label(item.get("classification", "-"), "class")
            cluster_label = _v39_ml_clean_label(item.get("cluster_label", "-"), "cluster")
            try:
                score_text = f"{float(item_score):.2f}/100"
            except Exception:
                score_text = f"{item_score}/100"
            html = f"""
                <div class="rank-card">
                  <div class="model-title">{_v39_ml_text("\u0420\u0430\u043d\u0433", "Rank")} {item.get('rank')}</div>
                  {format_number_pills(item_numbers)}
                  <div class="small-muted">{_v39_ml_text("\u041e\u0446\u0435\u043d\u043a\u0430", "Score")}: {score_text} \u00b7 {_v39_ml_text("\u041a\u043b\u0430\u0441", "Class")}: {classification} \u00b7 {_v39_ml_text("\u041a\u043b\u044a\u0441\u0442\u0435\u0440", "Cluster")}: {cluster_label}</div>
                </div>
                """
            st.markdown(html, unsafe_allow_html=True)
    with tabs[1]:
        classifier = model.get("classifier", {})
        st.markdown("### " + _v39_ml_text("\u041a\u043b\u0430\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f \u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438", "Класификация на комбинации"))
        st.markdown(_v39_ml_text(
            "\u041a\u043b\u0430\u0441\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u044a\u0442 \u0433\u0440\u0443\u043f\u0438\u0440\u0430 \u0444\u0438\u0448\u043e\u0432\u0435\u0442\u0435 \u043a\u0430\u0442\u043e \u0441\u043b\u0430\u0431, \u043d\u043e\u0440\u043c\u0430\u043b\u0435\u043d \u0438\u043b\u0438 \u0441\u0438\u043b\u0435\u043d \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0444\u0438\u0448 \u0441\u043f\u043e\u0440\u0435\u0434 \u0438\u0437\u0447\u0438\u0441\u043b\u0435\u043d\u0438\u0442\u0435 \u0445\u0430\u0440\u0430\u043a\u0442\u0435\u0440\u0438\u0441\u0442\u0438\u043a\u0438.",
            "The classifier groups tickets as weak, normal, or strong statistical tickets based on calculated features.",
        ))
        classes = [_v39_ml_clean_label(value, "class") for value in classifier.get("classes", [])]
        if classes:
            st.dataframe(pd.DataFrame({_v39_ml_text("\u041a\u043b\u0430\u0441\u043e\u0432\u0435", "Classes"): classes}), width="stretch", hide_index=True)
        quantiles = classifier.get("score_quantiles", {})
        if quantiles:
            st.dataframe(pd.DataFrame([{
                _v39_ml_text("\u041f\u0440\u0430\u0433 33%", "33% threshold"): quantiles.get("q33"),
                _v39_ml_text("\u041f\u0440\u0430\u0433 66%", "66% threshold"): quantiles.get("q66"),
            }]), width="stretch", hide_index=True)
    with tabs[2]:
        st.markdown("### " + _v39_ml_text("\u041a\u043b\u044a\u0441\u0442\u0435\u0440\u0438 \u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438", "Combination Clusters"))
        clusters = model.get("cluster_model", {}).get("cluster_summaries", [])
        if clusters:
            df_clusters = pd.DataFrame(clusters).copy()
            if "label" in df_clusters.columns:
                df_clusters["label"] = df_clusters["label"].apply(lambda value: _v39_ml_clean_label(value, "cluster"))
            df_clusters = df_clusters.rename(columns={
                "cluster": _v39_ml_text("\u041a\u043b\u044a\u0441\u0442\u0435\u0440", "Cluster"),
                "label": _v39_ml_text("\u0418\u043c\u0435", "Name"),
                "size": _v39_ml_text("\u0411\u0440\u043e\u0439", "Count"),
                "average_score": _v39_ml_text("\u0421\u0440\u0435\u0434\u043d\u0430 \u043e\u0446\u0435\u043d\u043a\u0430", "Average score"),
                "avg_frequency_score": _v39_ml_text("\u0421\u0440\u0435\u0434\u0435\u043d \u0447\u0435\u0441\u0442\u043e\u0442\u0435\u043d \u0441\u0438\u0433\u043d\u0430\u043b", "Average frequency signal"),
                "avg_cold_gap_score": _v39_ml_text("\u0421\u0440\u0435\u0434\u0435\u043d \u0438\u043d\u0442\u0435\u0440\u0432\u0430\u043b\u0435\u043d \u0441\u0438\u0433\u043d\u0430\u043b", "Average gap signal"),
                "avg_structure_score": _v39_ml_text("\u0421\u0440\u0435\u0434\u043d\u0430 \u0441\u0442\u0440\u0443\u043a\u0442\u0443\u0440\u0430", "Average structure"),
                "avg_human_pattern_score": _v39_ml_text("\u0421\u0440\u0435\u0434\u0435\u043d \u0440\u0438\u0441\u043a \u043e\u0442 \u0448\u0430\u0431\u043b\u043e\u043d", "Average pattern risk"),
            })
            st.dataframe(df_clusters, width="stretch", hide_index=True)
        else:
            st.info(_v39_ml_text("\u041d\u044f\u043c\u0430 \u0437\u0430\u043f\u0438\u0441\u0430\u043d\u0438 \u043a\u043b\u044a\u0441\u0442\u0435\u0440\u0438.", "No saved clusters."))
    with tabs[3]:
        st.markdown("### " + _v39_ml_text("2D \u043a\u0430\u0440\u0442\u0430 \u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438\u0442\u0435", "2D Map of Combinations"))
        reduction = model.get("dimensionality_reduction", {})
        evr = reduction.get("explained_variance_ratio", [])
        if evr and len(evr) >= 2:
            axis_x_pct = float(evr[0]) * 100
            axis_y_pct = float(evr[1]) * 100
            total_pct = (float(evr[0]) + float(evr[1])) * 100
            c1, c2, c3 = st.columns(3)
            c1.metric(_v39_ml_text("\u041e\u0441 X \u043e\u0431\u044f\u0441\u043d\u044f\u0432\u0430", "Axis X explains"), f"{axis_x_pct:.2f}%")
            c2.metric(_v39_ml_text("\u041e\u0441 Y \u043e\u0431\u044f\u0441\u043d\u044f\u0432\u0430", "Axis Y explains"), f"{axis_y_pct:.2f}%")
            c3.metric(_v39_ml_text("\u041e\u0431\u0449\u043e 2D \u043f\u043e\u043a\u0440\u0438\u0442\u0438\u0435", "Total 2D coverage"), f"{total_pct:.2f}%")
            st.caption(_v39_ml_text(
                "\u0422\u043e\u0432\u0430 \u043f\u043e\u043a\u0430\u0437\u0432\u0430 \u043a\u0430\u043a\u0432\u0430 \u0447\u0430\u0441\u0442 \u043e\u0442 \u0432\u044a\u0442\u0440\u0435\u0448\u043d\u0430\u0442\u0430 \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0430 \u0435 \u0437\u0430\u043f\u0430\u0437\u0435\u043d\u0430 \u043f\u0440\u0438 \u0441\u0432\u0438\u0432\u0430\u043d\u0435\u0442\u043e \u0434\u043e 2D \u043a\u0430\u0440\u0442\u0430. \u0422\u043e\u0432\u0430 \u043d\u0435 \u043e\u0437\u043d\u0430\u0447\u0430\u0432\u0430 \u043f\u043e-\u0432\u0438\u0441\u043e\u043a \u0448\u0430\u043d\u0441 \u0437\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430.",
                "This shows how much of the model's internal information is preserved when combinations are reduced to a 2D map. It does not mean higher odds of winning.",
            ))
        else:
            st.caption(_v39_ml_text("\u041d\u044f\u043c\u0430 \u0437\u0430\u043f\u0438\u0441\u0430\u043d\u0438 \u0441\u0442\u043e\u0439\u043d\u043e\u0441\u0442\u0438 \u0437\u0430 \u043e\u0431\u044f\u0441\u043d\u0435\u043d\u0430 \u0432\u0430\u0440\u0438\u0430\u0446\u0438\u044f.", "No explained-variance values saved."))
        points = model.get("projection_points_sample", [])
        if points:
            chart_df = pd.DataFrame(points)
            for col in ["x", "y", "score"]:
                if col in chart_df.columns:
                    chart_df[col] = pd.to_numeric(chart_df[col], errors="coerce")
            chart_df = chart_df.dropna(subset=["x", "y"])
            combo_col = _v39_ml_text("\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f", "Combination")
            score_col = _v39_ml_text("\u041e\u0446\u0435\u043d\u043a\u0430", "Score")
            x_col = _v39_ml_text("\u041e\u0441 X", "Axis X")
            y_col = _v39_ml_text("\u041e\u0441 Y", "Axis Y")
            chart_df[combo_col] = chart_df.get("numbers", "").apply(lambda value: ", ".join(map(str, value)) if isinstance(value, list) else str(value)) if "numbers" in chart_df.columns else ""
            chart_df = chart_df.rename(columns={"x": x_col, "y": y_col, "score": score_col})
            st.markdown("#### " + _v39_ml_text("\u0412\u0438\u0437\u0443\u0430\u043b\u043d\u0430 \u043a\u0430\u0440\u0442\u0430", "Visual Map"))
            st.caption(_v39_ml_text(
                "\u0412\u0441\u044f\u043a\u0430 \u0442\u043e\u0447\u043a\u0430 \u0435 \u0435\u0434\u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f. \u0411\u043b\u0438\u0437\u043a\u0438\u0442\u0435 \u0442\u043e\u0447\u043a\u0438 \u0438\u043c\u0430\u0442 \u0441\u0445\u043e\u0434\u043d\u0430 \u0441\u0442\u0440\u0443\u043a\u0442\u0443\u0440\u0430 \u0441\u043f\u043e\u0440\u0435\u0434 \u043c\u043e\u0434\u0435\u043b\u0430.",
                "Each point is one combination. Nearby points have a similar structure according to the model.",
            ))
            try:
                import altair as alt
                chart = (
                    alt.Chart(chart_df)
                    .mark_circle(size=95, opacity=0.78)
                    .encode(
                        x=alt.X(f"{x_col}:Q", title=x_col),
                        y=alt.Y(f"{y_col}:Q", title=y_col),
                        color=alt.Color(f"{score_col}:Q", title=score_col),
                        tooltip=[
                            alt.Tooltip(f"{combo_col}:N", title=combo_col),
                            alt.Tooltip(f"{score_col}:Q", title=score_col, format=".4f"),
                            alt.Tooltip(f"{x_col}:Q", title=x_col, format=".4f"),
                            alt.Tooltip(f"{y_col}:Q", title=y_col, format=".4f"),
                        ],
                    )
                    .interactive()
                    .properties(height=460)
                )
                try:
                    st.altair_chart(chart, width="stretch")
                except TypeError:
                    st.altair_chart(chart, use_container_width=True)
            except Exception:
                st.scatter_chart(chart_df, x=x_col, y=y_col, size=score_col, height=460)
            st.markdown("#### " + _v39_ml_text("\u0414\u0430\u043d\u043d\u0438 \u0437\u0430\u0434 \u043a\u0430\u0440\u0442\u0430\u0442\u0430", "Data Behind the Map"))
            table_cols = [col for col in [combo_col, x_col, y_col, score_col] if col in chart_df.columns]
            st.dataframe(chart_df[table_cols], width="stretch", hide_index=True)
        else:
            st.info(_v39_ml_text("\u041d\u044f\u043c\u0430 \u0437\u0430\u043f\u0438\u0441\u0430\u043d\u0438 \u0442\u043e\u0447\u043a\u0438 \u0437\u0430 2D \u043a\u0430\u0440\u0442\u0430.", "No saved points for the 2D map."))
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
            "ml_extensions_report.md": _v39_ml_text("\u041e\u0431\u0449 \u043e\u0442\u0447\u0435\u0442 \u0437\u0430 \u041c\u041b \u0440\u0430\u0437\u0448\u0438\u0440\u0435\u043d\u0438\u044f\u0442\u0430", "General ML extensions report"),
            "ml_classification_report.md": _v39_ml_text("\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043a\u043b\u0430\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f", "Classification report"),
            "ml_clustering_report.md": _v39_ml_text("\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 \u043a\u043b\u044a\u0441\u0442\u0435\u0440\u0438\u0437\u0430\u0446\u0438\u044f", "Clustering report"),
            "ml_dimensionality_reduction_report.md": _v39_ml_text("\u041e\u0442\u0447\u0435\u0442 \u0437\u0430 2D \u043a\u0430\u0440\u0442\u0430", "2D map report"),
            "ml_extensions_backtest_report.md": _v39_ml_text("\u041e\u0442\u0447\u0435\u0442 \u043e\u0442 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430", "Отчет от историческа проверка"),
            "ml_extensions_model_card.md": _v39_ml_text("\u041a\u0430\u0440\u0442\u0430 \u043d\u0430 \u043c\u043e\u0434\u0435\u043b\u0430", "Model card"),
        }
        selected = st.selectbox(_v39_ml_text("\u041c\u041b \u043e\u0442\u0447\u0435\u0442", "ML report"), report_files, format_func=lambda name: report_labels.get(name, name), key="v39_ml_report_select")
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
def _v39_git_lang() -> str:
    try:
        return st.session_state.get("language", globals().get("LANG", "bg"))
    except Exception:
        return globals().get("LANG", "bg")
def _v39_git_text(bg: str, en: str) -> str:
    return bg if _v39_git_lang() == "bg" else en
def _v39_git_run(args: List[str]) -> Tuple[bool, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        return completed.returncode == 0, output.strip()
    except Exception as exc:
        return False, str(exc)
def _v39_git_collect_sync_paths() -> List[str]:
    paths: List[Path] = []
    app_file = ROOT / "streamlit_app.py"
    if app_file.exists():
        paths.append(app_file)
    if DATA_PATH.exists():
        paths.append(DATA_PATH)
    if MODELS_DIR.exists():
        for item in MODELS_DIR.rglob("*.json"):
            if item.is_file():
                paths.append(item)
    if REPORTS_DIR.exists():
        allowed_suffixes = {".md", ".json", ".csv", ".svg", ".png"}
        for item in REPORTS_DIR.rglob("*"):
            if not item.is_file():
                continue
            if item.suffix.lower() not in allowed_suffixes:
                continue
            lowered_name = item.name.lower()
            lowered_path = str(item).lower()
            if "backup" in lowered_name or "backup" in lowered_path:
                continue
            if ".bak" in lowered_name or ".tmp" in lowered_name:
                continue
            paths.append(item)
    clean_paths: List[str] = []
    seen = set()
    for item in paths:
        try:
            rel = str(item.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
        except Exception:
            continue
        lowered = rel.lower()
        if "backup" in lowered or ".v39_local_backups" in lowered or "__pycache__" in lowered:
            continue
        if rel not in seen:
            seen.add(rel)
            clean_paths.append(rel)
    return sorted(clean_paths)
def _v39_git_filtered_status() -> str:
    ok, output = _v39_git_run(["status", "--short"])
    if not ok:
        return output or "git status failed"
    visible_lines: List[str] = []
    for line in output.splitlines():
        lowered = line.lower()
        if "backup" in lowered or ".v39_local_backups" in lowered or "__pycache__" in lowered:
            continue
        visible_lines.append(line)
    return "\n".join(visible_lines).strip()
def _v39_git_sync(commit_message: str) -> Tuple[bool, str]:
    repo_ok, repo_output = _v39_git_run(["rev-parse", "--is-inside-work-tree"])
    if not repo_ok:
        return False, "Git repository was not detected.\n" + repo_output
    sync_paths = _v39_git_collect_sync_paths()
    if not sync_paths:
        return False, "No sync paths were found."
    add_ok, add_output = _v39_git_run(["add", "--", *sync_paths])
    if not add_ok:
        return False, "git add failed:\n" + add_output
    diff_check = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    if diff_check.returncode == 0:
        return True, _v39_git_text(
            "\u041d\u044f\u043c\u0430 \u043d\u043e\u0432\u0438 \u043f\u0440\u043e\u043c\u0435\u043d\u0438 \u0437\u0430 \u043a\u0430\u0447\u0432\u0430\u043d\u0435 \u0432 GitHub.",
            "There are no new changes to upload to GitHub.",
        )
    commit_ok, commit_output = _v39_git_run(["commit", "-m", commit_message])
    if not commit_ok:
        return False, "git commit failed:\n" + commit_output
    push_ok, push_output = _v39_git_run(["push"])
    if not push_ok:
        return False, "git push failed:\n" + push_output
    final_output = "\n\n".join(
        part for part in [
            "git commit:",
            commit_output,
            "git push:",
            push_output,
        ]
        if part
    )
    return True, final_output
def _v39_render_github_sync_panel() -> None:
    st.markdown("### " + _v39_git_text("GitHub \u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u044f", "GitHub Sync"))
    st.caption(
        _v39_git_text(
            "\u0421\u043b\u0435\u0434 \u043a\u0430\u0442\u043e \u0434\u043e\u0431\u0430\u0432\u0438\u0448 \u0442\u0438\u0440\u0430\u0436 \u0438 \u043c\u043e\u0434\u0435\u043b\u0438\u0442\u0435 \u0441\u0435 \u043e\u0431\u043d\u043e\u0432\u044f\u0442, \u0442\u0443\u043a \u043c\u043e\u0436\u0435\u0448 \u0441 \u0435\u0434\u0438\u043d \u0431\u0443\u0442\u043e\u043d \u0434\u0430 \u0437\u0430\u043f\u0438\u0448\u0435\u0448 \u0438 \u043a\u0430\u0447\u0438\u0448 \u043f\u0440\u043e\u043c\u0435\u043d\u0438\u0442\u0435 \u0432 GitHub.",
            "After adding a draw and recalculating the models, you can save and upload the changes to GitHub with one button.",
        )
    )
    status_text = _v39_git_filtered_status()
    if status_text:
        with st.expander(_v39_git_text("\u041f\u0440\u043e\u043c\u0435\u043d\u0438, \u043a\u043e\u0438\u0442\u043e \u0449\u0435 \u0441\u0435 \u043a\u0430\u0447\u0430\u0442", "Changes that can be uploaded"), expanded=False):
            st.code(status_text)
    else:
        st.success(
            _v39_git_text(
                "\u041d\u044f\u043c\u0430 \u0432\u0438\u0434\u0438\u043c\u0438 \u043f\u0440\u043e\u043c\u0435\u043d\u0438 \u0437\u0430 GitHub.",
                "There are no visible GitHub changes.",
            )
        )
    default_message = "Update lottery data and model artifacts"
    commit_message = st.text_input(
        _v39_git_text("\u0421\u044a\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u0437\u0430 GitHub commit", "GitHub commit message"),
        value=default_message,
        key="v39_github_commit_message",
    )
    if st.button(
        _v39_git_text("\u041a\u0430\u0447\u0438 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435\u0442\u043e \u0432 GitHub", "Upload update to GitHub"),
        width="stretch",
        key="v39_upload_update_to_github",
    ):
        message = commit_message.strip() or default_message
        with st.spinner(_v39_git_text("\u041a\u0430\u0447\u0432\u0430\u043d\u0435 \u0432 GitHub...", "Uploading to GitHub...")):
            ok, output = _v39_git_sync(message)
        if ok:
            st.success(
                _v39_git_text(
                    "\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435\u0442\u043e \u0435 \u0437\u0430\u043f\u0438\u0441\u0430\u043d\u043e \u0438 \u043a\u0430\u0447\u0435\u043d\u043e \u0432 GitHub.",
                    "The update was committed and uploaded to GitHub.",
                )
            )
        else:
            st.error(
                _v39_git_text(
                    "\u041d\u0435 \u0443\u0441\u043f\u044f\u0445 \u0434\u0430 \u043a\u0430\u0447\u0430 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435\u0442\u043e \u0432 GitHub.",
                    "The update could not be uploaded to GitHub.",
                )
            )
        with st.expander(_v39_git_text("\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438 GitHub \u0438\u0437\u0445\u043e\u0434", "Technical GitHub output"), expanded=False):
            st.code(output[-5000:] if output else "")
def page_update_draws():
    from importlib import reload
    import src.add_draws_section as add_draws_section
    reload(add_draws_section)
    add_draws_section.render()

# ADD_DRAW_SIDEBAR_SHORTCUT_START
def _open_add_draw_from_sidebar_shortcut() -> None:
    target_group = "✅ Финален план за игра"
    target_page = "Добавяне на тираж"
    st.session_state["_pending_navigation_group"] = target_group
    st.session_state["_pending_navigation_page"] = target_page
    st.session_state["selected_page"] = target_page
    st.session_state["page"] = target_page
    st.session_state["current_page"] = target_page
    st.session_state["main_section"] = target_group
    st.rerun()
# ADD_DRAW_SIDEBAR_SHORTCUT_END
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
def page_ticket_analyzer() -> None:
    render_header()
    lang = st.session_state.get("language", globals().get("LANG", "bg"))
    def tx(bg: str, en: str) -> str:
        return bg if lang == "bg" else en
    def rerun_page() -> None:
        if hasattr(st, "rerun"):
            st.rerun()
        elif hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
    def combo_key(index: int) -> str:
        return f"v39_ticket_slip_combo_{index}"
    def get_combo(index: int) -> list[int]:
        st.session_state.setdefault(combo_key(index), [])
        values = st.session_state.get(combo_key(index), [])
        return sorted([int(x) for x in values])
    def set_combo(index: int, values) -> None:
        st.session_state[combo_key(index)] = sorted([int(x) for x in values])
        st.session_state["v39_ticket_slip_show_analysis"] = False
    def toggle_number(index: int, number: int) -> None:
        selected = set(get_combo(index))
        if number in selected:
            selected.remove(number)
            set_combo(index, selected)
            rerun_page()
            return
        if len(selected) >= 6:
            st.session_state["v39_ticket_slip_message"] = tx(
                "\u0412 \u0435\u0434\u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u043c\u043e\u0436\u0435 \u0434\u0430 \u0438\u043c\u0430 \u0442\u043e\u0447\u043d\u043e 6 \u0447\u0438\u0441\u043b\u0430. \u041f\u044a\u0440\u0432\u043e \u043c\u0430\u0445\u043d\u0438 \u0435\u0434\u043d\u043e \u0447\u0438\u0441\u043b\u043e.",
                "One combination can contain exactly 6 numbers. Remove one number first.",
            )
            rerun_page()
            return
        selected.add(number)
        set_combo(index, selected)
        rerun_page()
    def fmt_numbers(values) -> str:
        values = sorted([int(x) for x in values])
        return ", ".join(str(x) for x in values) if values else "\u2014"
    def selected_chips(values) -> str:
        values = sorted([int(x) for x in values])
        if not values:
            return f'<span class="v39-empty">{tx("\u043d\u044f\u043c\u0430 \u0438\u0437\u0431\u0440\u0430\u043d\u0438 \u0447\u0438\u0441\u043b\u0430", "no selected numbers")}</span>'
        chips = ""
        for value in values:
            chips += f'<span class="v39-chip">{value}</span>'
        return chips
    def build_ticket_explanation(values, zone):
        values = sorted([int(x) for x in values])
        total = sum(values)
        even = sum(1 for number in values if number % 2 == 0)
        odd = 6 - even
        low = sum(1 for number in values if 1 <= number <= 16)
        middle_band = sum(1 for number in values if 17 <= number <= 33)
        high = sum(1 for number in values if 34 <= number <= 49)
        parts = []
        if zone:
            hot_count = len(zone.get("hot", []))
            middle_count = len(zone.get("middle", []))
            cold_count = len(zone.get("cold", []))
            kind = zone.get("kind", "")
            parts.append(
                tx(
                    f"**\u041e\u0431\u0449 \u0438\u0437\u0432\u043e\u0434:** \u0442\u0430\u0437\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0435 **{kind}**.",
                    f"**Overall:** this combination is **{kind}**.",
                )
            )
            parts.append(
                tx(
                    f"**\u0417\u043e\u043d\u043e\u0432 \u0430\u043d\u0430\u043b\u0438\u0437:** {hot_count} \u0447\u0438\u0441\u043b\u0430 \u0441\u0430 \u0432 \u0433\u043e\u0440\u0435\u0449\u0430\u0442\u0430 \u0437\u043e\u043d\u0430, {middle_count} \u0441\u0430 \u0432 \u0441\u0440\u0435\u0434\u043d\u0430\u0442\u0430 \u0437\u043e\u043d\u0430 \u0438 {cold_count} \u0441\u0430 \u0432 \u0441\u0442\u0443\u0434\u0435\u043d\u0430\u0442\u0430 \u0437\u043e\u043d\u0430.",
                    f"**Zone analysis:** {hot_count} numbers are in the hot zone, {middle_count} are in the middle zone, and {cold_count} are in the cold zone.",
                )
            )
            if hot_count >= 3:
                parts.append(
                    tx(
                        "\u0422\u043e\u0432\u0430 \u043e\u0437\u043d\u0430\u0447\u0430\u0432\u0430, \u0447\u0435 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f\u0442\u0430 \u0435 \u043f\u043e-\u0431\u043b\u0438\u0437\u043e \u0434\u043e \u043f\u043e-\u0430\u043a\u0442\u0438\u0432\u043d\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u0430 \u0432 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430\u0442\u0430 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430.",
                        "This means the combination is closer to the more active numbers in the historical statistics.",
                    )
                )
            elif cold_count >= 3:
                parts.append(
                    tx(
                        "\u0422\u043e\u0432\u0430 \u043e\u0437\u043d\u0430\u0447\u0430\u0432\u0430, \u0447\u0435 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f\u0442\u0430 \u0435 \u043f\u043e-\u0431\u043b\u0438\u0437\u043e \u0434\u043e \u043f\u043e-\u0441\u043b\u0430\u0431\u043e \u0430\u043a\u0442\u0438\u0432\u043d\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u0430 \u0432 \u0442\u0435\u043a\u0443\u0449\u0430\u0442\u0430 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430.",
                        "This means the combination is closer to the less active numbers in the current statistics.",
                    )
                )
            elif middle_count >= 3:
                parts.append(
                    tx(
                        "\u0422\u043e\u0432\u0430 \u043e\u0437\u043d\u0430\u0447\u0430\u0432\u0430, \u0447\u0435 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f\u0442\u0430 \u0438\u043c\u0430 \u043f\u043e-\u0443\u043c\u0435\u0440\u0435\u043d \u043f\u0440\u043e\u0444\u0438\u043b \u0438 \u043d\u0435 \u0435 \u043f\u0440\u0435\u043a\u0430\u043b\u0435\u043d\u043e \u043a\u0440\u0430\u0439\u043d\u0430.",
                        "This means the combination has a more moderate profile and is not too extreme.",
                    )
                )
            else:
                parts.append(
                    tx(
                        "\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f\u0442\u0430 \u0435 \u0441\u043c\u0435\u0441\u0435\u043d\u0430 \u2014 \u0438\u043c\u0430 \u0447\u0438\u0441\u043b\u0430 \u043e\u0442 \u0440\u0430\u0437\u043b\u0438\u0447\u043d\u0438 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0437\u043e\u043d\u0438.",
                        "The combination is mixed — it has numbers from different statistical zones.",
                    )
                )
        else:
            parts.append(
                tx(
                    "**\u041e\u0431\u0449 \u0438\u0437\u0432\u043e\u0434:** \u0437\u043e\u043d\u043e\u0432\u0438\u044f\u0442 \u0430\u043d\u0430\u043b\u0438\u0437 \u043d\u0435 \u0435 \u043d\u0430\u043b\u0438\u0447\u0435\u043d, \u043d\u043e \u043e\u0441\u043d\u043e\u0432\u043d\u0438\u0442\u0435 \u043f\u043e\u043a\u0430\u0437\u0430\u0442\u0435\u043b\u0438 \u043f\u043e-\u0434\u043e\u043b\u0443 \u0434\u0430\u0432\u0430\u0442 \u043e\u0440\u0438\u0435\u043d\u0442\u0438\u0440 \u0437\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f\u0442\u0430.",
                    "**Overall:** zone analysis is not available, but the basic indicators below still describe the combination.",
                )
            )
        if even in [2, 3, 4]:
            parts.append(
                tx(
                    f"**\u0427\u0435\u0442\u043d\u0438/\u043d\u0435\u0447\u0435\u0442\u043d\u0438:** \u0431\u0430\u043b\u0430\u043d\u0441\u044a\u0442 \u0435 {even}/{odd}, \u043a\u043e\u0435\u0442\u043e \u0435 \u043d\u043e\u0440\u043c\u0430\u043b\u043d\u043e \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u043e \u0440\u0430\u0437\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0435.",
                    f"**Even/odd:** the balance is {even}/{odd}, which is a normal statistical distribution.",
                )
            )
        else:
            parts.append(
                tx(
                    f"**\u0427\u0435\u0442\u043d\u0438/\u043d\u0435\u0447\u0435\u0442\u043d\u0438:** \u0431\u0430\u043b\u0430\u043d\u0441\u044a\u0442 \u0435 {even}/{odd}, \u043a\u043e\u0435\u0442\u043e \u0435 \u043f\u043e-\u043a\u0440\u0430\u0439\u043d\u043e \u0440\u0430\u0437\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0435.",
                    f"**Even/odd:** the balance is {even}/{odd}, which is a more extreme distribution.",
                )
            )
        if low > 0 and middle_band > 0 and high > 0:
            parts.append(
                tx(
                    f"**\u041d\u0438\u0441\u043a\u0438/\u0441\u0440\u0435\u0434\u043d\u0438/\u0432\u0438\u0441\u043e\u043a\u0438:** \u0440\u0430\u0437\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0435\u0442\u043e \u0435 {low}/{middle_band}/{high}, \u0442\u043e\u0435\u0441\u0442 \u0438\u043c\u0430 \u0447\u0438\u0441\u043b\u0430 \u043e\u0442 \u0432\u0441\u0438\u0447\u043a\u0438 \u043e\u0441\u043d\u043e\u0432\u043d\u0438 \u0434\u0438\u0430\u043f\u0430\u0437\u043e\u043d\u0438.",
                    f"**Low/middle/high:** the distribution is {low}/{middle_band}/{high}, so it includes numbers from all main ranges.",
                )
            )
        else:
            parts.append(
                tx(
                    f"**\u041d\u0438\u0441\u043a\u0438/\u0441\u0440\u0435\u0434\u043d\u0438/\u0432\u0438\u0441\u043e\u043a\u0438:** \u0440\u0430\u0437\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0435\u0442\u043e \u0435 {low}/{middle_band}/{high}, \u0442\u043e\u0435\u0441\u0442 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f\u0442\u0430 \u0435 \u043f\u043e-\u043a\u043e\u043d\u0446\u0435\u043d\u0442\u0440\u0438\u0440\u0430\u043d\u0430 \u0432 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d \u0434\u0438\u0430\u043f\u0430\u0437\u043e\u043d.",
                    f"**Low/middle/high:** the distribution is {low}/{middle_band}/{high}, so the combination is more concentrated in one range.",
                )
            )
        if 110 <= total <= 190:
            parts.append(
                tx(
                    f"**\u0421\u0443\u043c\u0430:** \u043e\u0431\u0449\u0430\u0442\u0430 \u0441\u0443\u043c\u0430 \u0435 {total}, \u043a\u043e\u0435\u0442\u043e \u0435 \u0443\u043c\u0435\u0440\u0435\u043d \u0447\u0438\u0441\u043b\u043e\u0432 \u043f\u0440\u043e\u0444\u0438\u043b.",
                    f"**Sum:** the total is {total}, which is a moderate number profile.",
                )
            )
        elif total < 110:
            parts.append(
                tx(
                    f"**\u0421\u0443\u043c\u0430:** \u043e\u0431\u0449\u0430\u0442\u0430 \u0441\u0443\u043c\u0430 \u0435 {total}, \u043a\u043e\u0435\u0442\u043e \u043f\u0440\u0430\u0432\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f\u0442\u0430 \u043f\u043e-\u043d\u0438\u0441\u043a\u0430 \u043a\u0430\u0442\u043e \u0447\u0438\u0441\u043b\u043e\u0432 \u043f\u0440\u043e\u0444\u0438\u043b.",
                    f"**Sum:** the total is {total}, which makes the combination lower in number profile.",
                )
            )
        else:
            parts.append(
                tx(
                    f"**\u0421\u0443\u043c\u0430:** \u043e\u0431\u0449\u0430\u0442\u0430 \u0441\u0443\u043c\u0430 \u0435 {total}, \u043a\u043e\u0435\u0442\u043e \u043f\u0440\u0430\u0432\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f\u0442\u0430 \u043f\u043e-\u0432\u0438\u0441\u043e\u043a\u0430 \u043a\u0430\u0442\u043e \u0447\u0438\u0441\u043b\u043e\u0432 \u043f\u0440\u043e\u0444\u0438\u043b.",
                    f"**Sum:** the total is {total}, which makes the combination higher in number profile.",
                )
            )
        parts.append(
            tx(
                "**\u0412\u0430\u0436\u043d\u043e:** \u0442\u043e\u0432\u0430 \u0435 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u043e \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435. \u0422\u043e \u043d\u0435 \u043f\u0440\u043e\u043c\u0435\u043d\u044f \u0440\u0435\u0430\u043b\u043d\u0438\u044f \u0448\u0430\u043d\u0441 \u0437\u0430 \u0442\u043e\u0447\u043d\u0430 6/49 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f: **1:13,983,816**.",
                "**Important:** this is a statistical description. It does not change the real odds for an exact 6/49 combination: **1:13,983,816**.",
            )
        )
        return "\n\n".join(parts)
    def render_page_css() -> None:
        st.markdown(
            """
            <style>
            div[data-testid="stButton"] > button {
                border: 1px solid rgba(245, 216, 108, 0.36) !important;
                background: rgba(255, 255, 255, 0.035) !important;
                color: rgba(255,255,255,0.88) !important;
                border-radius: 8px !important;
                min-height: 34px !important;
                padding: 0.18rem 0.25rem !important;
                font-size: 0.84rem !important;
                font-weight: 800 !important;
                box-shadow: none !important;
            }
            div[data-testid="stButton"] > button:hover {
                border-color: rgba(245, 216, 108, 0.82) !important;
                background: rgba(245, 216, 108, 0.12) !important;
                color: #f8e6a0 !important;
            }
            div[data-testid="stButton"] > button[kind="primary"] {
                border-color: rgba(236, 0, 140, 0.95) !important;
                background: rgba(236, 0, 140, 0.18) !important;
                color: #f7d66d !important;
                font-weight: 950 !important;
            }
            .v39-slip-wrap {
                border: 1px solid rgba(245, 216, 108, 0.25);
                border-radius: 18px;
                padding: 18px;
                background:
                    radial-gradient(circle at top left, rgba(245,216,108,0.11), transparent 30%),
                    rgba(255,255,255,0.025);
                margin: 12px 0 18px 0;
            }
            .v39-slip-title {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 14px;
                border: 1px solid rgba(245, 216, 108, 0.25);
                border-radius: 14px;
                padding: 14px 16px;
                background: rgba(0,0,0,0.20);
                margin-bottom: 14px;
            }
            .v39-slip-title-main {
                color: #f5ead4;
                font-size: 1.15rem;
                font-weight: 900;
                letter-spacing: 0.2px;
            }
            .v39-slip-title-sub {
                color: rgba(255,255,255,0.62);
                font-size: 0.9rem;
                margin-top: 3px;
            }
            .v39-combo-head {
                border: 1px solid rgba(245,216,108,0.28);
                border-bottom: 0;
                border-radius: 14px 14px 0 0;
                background: linear-gradient(180deg, rgba(245,216,108,0.13), rgba(236,0,140,0.08));
                color: #f4d36c;
                text-align: center;
                font-weight: 900;
                padding: 9px 10px;
                font-size: 0.98rem;
                margin-top: 4px;
            }
            .v39-combo-count {
                color: rgba(255,255,255,0.64);
                font-weight: 700;
                font-size: 0.86rem;
            }
            .v39-selected-row {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
                margin: 10px 0 12px 0;
                padding: 10px 12px;
                border-radius: 12px;
                border: 1px solid rgba(245,216,108,0.22);
                background: rgba(245,216,108,0.065);
            }
            .v39-selected-label {
                color: #f4d36c;
                font-weight: 900;
                margin-right: 2px;
            }
            .v39-chip {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 32px;
                height: 30px;
                padding: 0 8px;
                border-radius: 999px;
                background: linear-gradient(180deg, #f2d66a, #c89b18);
                color: #111;
                font-weight: 900;
                border: 1px solid rgba(255,230,140,0.55);
                box-shadow: 0 0 10px rgba(245,216,108,0.14);
            }
            .v39-empty {
                color: rgba(255,255,255,0.58);
                font-weight: 700;
            }
            .v39-slip-summary {
                border: 1px solid rgba(245,216,108,0.22);
                background: rgba(255,255,255,0.035);
                border-radius: 14px;
                padding: 14px 16px;
                margin-top: 16px;
            }
            .v39-summary-line {
                margin: 7px 0;
                color: rgba(255,255,255,0.86);
            }
            .v39-summary-line strong {
                color: #f4d36c;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    def render_combo(index: int) -> None:
        values = get_combo(index)
        count_text = f"{len(values)}/6"
        combo_label = tx("\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f", "Combination")
        selected_label = tx("\u0418\u0437\u0431\u0440\u0430\u043d\u0438", "Selected")
        clear_label = tx("\u0418\u0437\u0447\u0438\u0441\u0442\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f\u0442\u0430", "Clear combination")
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="v39-combo-head">
                    {combo_label} {index}
                    <span class="v39-combo-count"> · {count_text}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            for row in range(7):
                columns = st.columns(7, gap="small")
                for col in range(7):
                    number = row * 7 + col + 1
                    selected = number in values
                    label = "\u2715" if selected else str(number)
                    button_type = "primary" if selected else "secondary"
                    if columns[col].button(
                        label,
                        key=f"v39_ticket_cell_{index}_{number}",
                        type=button_type,
                        width="stretch",
                    ):
                        toggle_number(index, number)
            st.markdown(
                f"""
                <div class="v39-selected-row">
                    <span class="v39-selected-label">{selected_label}:</span>
                    {selected_chips(values)}
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(clear_label, key=f"v39_ticket_clear_{index}", width="stretch"):
                set_combo(index, [])
                rerun_page()
    def detect_number_columns(df):
        candidates = [
            ["n1", "n2", "n3", "n4", "n5", "n6"],
            ["num1", "num2", "num3", "num4", "num5", "num6"],
            ["number1", "number2", "number3", "number4", "number5", "number6"],
        ]
        for columns in candidates:
            if all(column in df.columns for column in columns):
                return columns
        numeric_columns = []
        for column in df.columns:
            lowered = str(column).lower()
            if lowered in ["year", "draw", "draw_id", "date", "month", "day"]:
                continue
            try:
                sample = df[column].dropna().head(30).astype(int)
                if len(sample) > 0 and sample.between(1, 49).all():
                    numeric_columns.append(column)
            except Exception:
                pass
        return numeric_columns[:6] if len(numeric_columns) >= 6 else []
    def calculate_zones(numbers):
        try:
            df = load_data()
        except Exception:
            return None
        if df is None or getattr(df, "empty", True):
            return None
        columns = detect_number_columns(df)
        if not columns:
            return None
        frequency = {number: 0 for number in range(1, 50)}
        for _, row in df.iterrows():
            for column in columns:
                try:
                    value = int(row[column])
                    if 1 <= value <= 49:
                        frequency[value] += 1
                except Exception:
                    pass
        ordered = sorted(range(1, 50), key=lambda number: (-frequency[number], number))
        hot_set = set(ordered[:16])
        middle_set = set(ordered[16:33])
        cold_set = set(ordered[33:])
        hot = sorted([number for number in numbers if number in hot_set])
        middle = sorted([number for number in numbers if number in middle_set])
        cold = sorted([number for number in numbers if number in cold_set])
        if len(hot) >= 3 and len(cold) <= 1:
            kind = tx("\u0411\u043b\u0438\u0437\u043e \u0434\u043e \u0433\u043e\u0440\u0435\u0449\u0430\u0442\u0430 \u0437\u043e\u043d\u0430", "Close to the hot zone")
            explanation = tx(
                "\u0422\u0430\u0437\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0435 \u043f\u043e-\u0431\u043b\u0438\u0437\u043e \u0434\u043e \u0433\u043e\u0440\u0435\u0449\u0430\u0442\u0430 \u0437\u043e\u043d\u0430, \u0437\u0430\u0449\u043e\u0442\u043e \u043f\u043e\u0432\u0435\u0447\u0435 \u0447\u0438\u0441\u043b\u0430 \u0441\u0430 \u0441\u0440\u0435\u0434 \u043f\u043e-\u0430\u043a\u0442\u0438\u0432\u043d\u0438\u0442\u0435 \u0432 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430\u0442\u0430 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430.",
                "This combination is closer to the hot zone because more numbers are among the more active ones in the historical statistics.",
            )
        elif len(cold) >= 3 and len(hot) <= 1:
            kind = tx("\u0411\u043b\u0438\u0437\u043e \u0434\u043e \u0441\u0442\u0443\u0434\u0435\u043d\u0430\u0442\u0430 \u0437\u043e\u043d\u0430", "Close to the cold zone")
            explanation = tx(
                "\u0422\u0430\u0437\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0435 \u043f\u043e-\u0431\u043b\u0438\u0437\u043e \u0434\u043e \u0441\u0442\u0443\u0434\u0435\u043d\u0430\u0442\u0430 \u0437\u043e\u043d\u0430, \u0437\u0430\u0449\u043e\u0442\u043e \u043f\u043e\u0432\u0435\u0447\u0435 \u0447\u0438\u0441\u043b\u0430 \u0441\u0430 \u0441\u0440\u0435\u0434 \u043f\u043e-\u0441\u043b\u0430\u0431\u043e \u0430\u043a\u0442\u0438\u0432\u043d\u0438\u0442\u0435.",
                "This combination is closer to the cold zone because more numbers are among the less active ones.",
            )
        elif len(hot) >= 1 and len(middle) >= 1 and len(cold) >= 1:
            kind = tx("\u0421\u043c\u0435\u0441\u0435\u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f", "Mixed combination")
            explanation = tx(
                "\u0427\u0438\u0441\u043b\u0430\u0442\u0430 \u0441\u0430 \u0440\u0430\u0437\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438 \u043c\u0435\u0436\u0434\u0443 \u0433\u043e\u0440\u0435\u0449\u0430, \u0441\u0440\u0435\u0434\u043d\u0430 \u0438 \u0441\u0442\u0443\u0434\u0435\u043d\u0430 \u0437\u043e\u043d\u0430.",
                "The numbers are distributed across the hot, middle, and cold zones.",
            )
        else:
            kind = tx("\u0411\u0430\u043b\u0430\u043d\u0441\u0438\u0440\u0430\u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f", "Balanced combination")
            explanation = tx(
                "\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f\u0442\u0430 \u0435 \u0441\u0440\u0430\u0432\u043d\u0438\u0442\u0435\u043b\u043d\u043e \u0431\u0430\u043b\u0430\u043d\u0441\u0438\u0440\u0430\u043d\u0430 \u0441\u043f\u0440\u044f\u043c\u043e \u0437\u043e\u043d\u0438\u0442\u0435.",
                "The combination is relatively balanced across the zones.",
            )
        return {
            "hot": hot,
            "middle": middle,
            "cold": cold,
            "kind": kind,
            "explanation": explanation,
        }
    render_page_css()
    st.markdown("## " + tx("\u0410\u043d\u0430\u043b\u0438\u0437 \u043d\u0430 \u0444\u0438\u0448", "Ticket analysis"))
    st.markdown(
        '<div class="warning-soft">'
        + tx(
            "\u0422\u043e\u0432\u0430 \u0435 \u0435\u0434\u0438\u043d \u0444\u0438\u0448 6/49 \u0441 4 \u043e\u0442\u0434\u0435\u043b\u043d\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438. \u041c\u0430\u0440\u043a\u0438\u0440\u0430\u0439 \u0434\u043e 6 \u0447\u0438\u0441\u043b\u0430 \u0432\u044a\u0432 \u0432\u0441\u044f\u043a\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f. \u0410\u043d\u0430\u043b\u0438\u0437\u044a\u0442 \u043d\u0435 \u0433\u0430\u0440\u0430\u043d\u0442\u0438\u0440\u0430 \u043f\u0435\u0447\u0430\u043b\u0431\u0430.",
            "This is one 6/49 ticket with 4 separate combinations. Mark up to 6 numbers in each combination. The analysis does not guarantee a win.",
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    message = st.session_state.pop("v39_ticket_slip_message", None)
    if message:
        st.warning(message)
    title_main = tx("\u0424\u0438\u0448 6/49", "6/49 ticket")
    title_sub = tx("\u0415\u0434\u0438\u043d \u0444\u0438\u0448 \u0441 4 \u043e\u0442\u0434\u0435\u043b\u043d\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438", "One ticket with 4 separate combinations")
    st.markdown(
        f"""
        <div class="v39-slip-wrap">
            <div class="v39-slip-title">
                <div>
                    <div class="v39-slip-title-main">{title_main}</div>
                    <div class="v39-slip-title-sub">{title_sub}</div>
                </div>
                <div class="v39-slip-title-main">\u25ce 6/49</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    top_left, top_right = st.columns(2)
    with top_left:
        render_combo(1)
    with top_right:
        render_combo(2)
    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        render_combo(3)
    with bottom_right:
        render_combo(4)
    st.markdown("### " + tx("\u041e\u0431\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u043d\u0430 \u0444\u0438\u0448\u0430", "Ticket summary"))
    summary_lines = ""
    for index in range(1, 5):
        values = get_combo(index)
        if len(values) == 0:
            status = tx("\u043d\u044f\u043c\u0430 \u0438\u0437\u0431\u0440\u0430\u043d\u0438 \u0447\u0438\u0441\u043b\u0430", "no selected numbers")
        elif len(values) < 6:
            status = tx(
                f"\u0438\u0437\u0431\u0440\u0430\u043d\u0438 {len(values)} \u043e\u0442 6: {fmt_numbers(values)}",
                f"{len(values)} of 6 selected: {fmt_numbers(values)}",
            )
        else:
            status = fmt_numbers(values)
        combo_label = tx("\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f", "Combination")
        summary_lines += f'<div class="v39-summary-line"><strong>{combo_label} {index}:</strong> {status}</div>'
    st.markdown(
        f"""
        <div class="v39-slip-summary">
            {summary_lines}
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_analyze, col_clear = st.columns(2)
    with col_analyze:
        if st.button(
            tx("\u0410\u043d\u0430\u043b\u0438\u0437\u0438\u0440\u0430\u0439 \u0444\u0438\u0448\u0430", "Analyze ticket"),
            key="v39_ticket_analyze_whole",
            type="primary",
            width="stretch",
        ):
            st.session_state["v39_ticket_slip_show_analysis"] = True
            rerun_page()
    with col_clear:
        if st.button(
            tx("\u0418\u0437\u0447\u0438\u0441\u0442\u0438 \u0446\u0435\u043b\u0438\u044f \u0444\u0438\u0448", "Clear whole ticket"),
            key="v39_ticket_clear_whole",
            width="stretch",
        ):
            for index in range(1, 5):
                set_combo(index, [])
            st.session_state["v39_ticket_slip_show_analysis"] = False
            rerun_page()
    if not st.session_state.get("v39_ticket_slip_show_analysis", False):
        st.info(
            tx(
                "\u041c\u0430\u0440\u043a\u0438\u0440\u0430\u0439 \u0435\u0434\u043d\u0430 \u0438\u043b\u0438 \u043f\u043e\u0432\u0435\u0447\u0435 \u043f\u044a\u043b\u043d\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u0438 \u043d\u0430\u0442\u0438\u0441\u043d\u0438 \u201e\u0410\u043d\u0430\u043b\u0438\u0437\u0438\u0440\u0430\u0439 \u0444\u0438\u0448\u0430\u201c.",
                "Mark one or more complete combinations and click 'Analyze ticket'.",
            )
        )
        return
    completed = [(index, get_combo(index)) for index in range(1, 5) if len(get_combo(index)) == 6]
    incomplete = [(index, get_combo(index)) for index in range(1, 5) if 0 < len(get_combo(index)) < 6]
    st.markdown("## " + tx("\u0410\u043d\u0430\u043b\u0438\u0437 \u043d\u0430 \u0444\u0438\u0448\u0430", "Ticket analysis result"))
    st.metric(tx("\u041f\u043e\u043f\u044a\u043b\u043d\u0435\u043d\u0438 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438", "Completed combinations"), f"{len(completed)} / 4")
    for index, values in incomplete:
        st.warning(
            tx(
                f"\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f {index} \u0438\u043c\u0430 {len(values)} \u043e\u0442 6 \u0447\u0438\u0441\u043b\u0430 \u0438 \u043d\u044f\u043c\u0430 \u0434\u0430 \u0431\u044a\u0434\u0435 \u0430\u043d\u0430\u043b\u0438\u0437\u0438\u0440\u0430\u043d\u0430, \u0434\u043e\u043a\u0430\u0442\u043e \u043d\u0435 \u0441\u0435 \u043f\u043e\u043f\u044a\u043b\u043d\u0438.",
                f"Combination {index} has {len(values)} of 6 numbers and will not be analyzed until completed.",
            )
        )
    if not completed:
        st.error(
            tx(
                "\u041d\u044f\u043c\u0430 \u043d\u0438\u0442\u043e \u0435\u0434\u043d\u0430 \u043f\u044a\u043b\u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0437\u0430 \u0430\u043d\u0430\u043b\u0438\u0437.",
                "There is no complete combination to analyze.",
            )
        )
        return
    for index, values in completed:
        combo_title = tx(f"\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f {index}", f"Combination {index}")
        st.markdown("### " + combo_title)
        st.markdown(
            f"""
            <div class="v39-selected-row">
                <span class="v39-selected-label">{tx('\u0427\u0438\u0441\u043b\u0430', 'Numbers')}:</span>
                {selected_chips(values)}
            </div>
            """,
            unsafe_allow_html=True,
        )
        total = sum(values)
        even = sum(1 for number in values if number % 2 == 0)
        odd = 6 - even
        low = sum(1 for number in values if 1 <= number <= 16)
        middle_band = sum(1 for number in values if 17 <= number <= 33)
        high = sum(1 for number in values if 34 <= number <= 49)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(tx("\u0421\u0443\u043c\u0430", "Sum"), total)
        c2.metric(tx("\u0427\u0435\u0442\u043d\u0438 / \u043d\u0435\u0447\u0435\u0442\u043d\u0438", "Even / odd"), f"{even} / {odd}")
        c3.metric(tx("\u041d\u0438\u0441\u043a\u0438 / \u0441\u0440\u0435\u0434\u043d\u0438 / \u0432\u0438\u0441\u043e\u043a\u0438", "Low / middle / high"), f"{low} / {middle_band} / {high}")
        c4.metric(tx("\u0420\u0435\u0430\u043b\u0435\u043d \u0448\u0430\u043d\u0441", "Real odds"), "1:13,983,816")
        zone = calculate_zones(values)
        st.markdown("#### " + tx("\u041e\u0431\u044f\u0441\u043d\u0435\u043d\u0438\u0435", "Explanation"))
        st.info(build_ticket_explanation(values, zone))
        if zone:
            z1, z2, z3, z4 = st.columns(4)
            z1.metric(tx("\u0413\u043e\u0440\u0435\u0449\u0430 \u0437\u043e\u043d\u0430", "Hot zone"), len(zone["hot"]))
            z2.metric(tx("\u0421\u0440\u0435\u0434\u043d\u0430 \u0437\u043e\u043d\u0430", "Middle zone"), len(zone["middle"]))
            z3.metric(tx("\u0421\u0442\u0443\u0434\u0435\u043d\u0430 \u0437\u043e\u043d\u0430", "Cold zone"), len(zone["cold"]))
            z4.metric(tx("\u0422\u0438\u043f", "Type"), zone["kind"])
            hot_label = tx("\u0413\u043e\u0440\u0435\u0449\u0430 \u0437\u043e\u043d\u0430", "Hot zone")
            middle_label = tx("\u0421\u0440\u0435\u0434\u043d\u0430 \u0437\u043e\u043d\u0430", "Middle zone")
            cold_label = tx("\u0421\u0442\u0443\u0434\u0435\u043d\u0430 \u0437\u043e\u043d\u0430", "Cold zone")
            st.markdown(
                f"**{hot_label}:** {fmt_numbers(zone['hot'])}  \n"
                f"**{middle_label}:** {fmt_numbers(zone['middle'])}  \n"
                f"**{cold_label}:** {fmt_numbers(zone['cold'])}"
            )
            st.success(zone["explanation"])
    st.info(
        tx(
            "\u0412\u0441\u0438\u0447\u043a\u0438 \u0442\u0435\u0437\u0438 \u0438\u0437\u0432\u043e\u0434\u0438 \u0441\u0430 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u0447\u0435\u0441\u043a\u0438. \u0422\u0435 \u043d\u0435 \u043f\u0440\u043e\u043c\u0435\u043d\u044f\u0442 \u0440\u0435\u0430\u043b\u043d\u0438\u044f \u0448\u0430\u043d\u0441 \u0437\u0430 \u0442\u043e\u0447\u043d\u0430 6/49 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f: 1:13,983,816.",
            "All these conclusions are statistical. They do not change the real odds for an exact 6/49 combination: 1:13,983,816.",
        )
    )
def page_probability_lab():
    from importlib import reload
    import src.probability_lab_section as probability_lab_section
    reload(probability_lab_section)
    probability_lab_section.render()
# HISTORY_LOAD_DATA_COMPAT_START
def load_data():
    """Compatibility loader for the Historical Statistics page.
    Reads the active historical 6/49 dataset.
    This is analysis data only and does not guarantee lottery winnings.
    """
    data_path = Path("data") / "historical_draws.csv"
    if not data_path.exists():
        fallback_path = Path(__file__).resolve().parent / "data" / "historical_draws.csv"
        if fallback_path.exists():
            data_path = fallback_path
    if not data_path.exists():
        raise FileNotFoundError("Missing data/historical_draws.csv")
    df = pd.read_csv(data_path)
    # Normalize common numeric columns without changing the source file.
    numeric_candidates = [
        "year",
        "draw",
        "draw_no",
        "draw_number",
        "drawing_no",
        "draw_position",
        "position",
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
        "n6",
        "num1",
        "num2",
        "num3",
        "num4",
        "num5",
        "num6",
        "number_1",
        "number_2",
        "number_3",
        "number_4",
        "number_5",
        "number_6",
        "bonus",
        "bonus_number",
    ]
    for column in numeric_candidates:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    if "date" in df.columns:
        df["date"] = df["date"].astype(str)
    return df
# HISTORY_LOAD_DATA_COMPAT_END
# BG_TEXT_RUNTIME_HELPER_START
def _bg(hex_text: str) -> str:
    return bytes.fromhex(hex_text).decode("utf-8")
# BG_TEXT_RUNTIME_HELPER_END
# HISTORY_RECENT_DRAWS_DISPLAY_START
def _format_history_recent_draws(df, rows: int = 10):
    if df is None or len(df) == 0:
        return pd.DataFrame()
    work = df.copy()
    for column in [
        "draw_id", "year", "draw_number", "draw_no", "draw",
        "draw_position", "drawing_no", "position",
        "n1", "n2", "n3", "n4", "n5", "n6",
        "num1", "num2", "num3", "num4", "num5", "num6",
        "number_1", "number_2", "number_3", "number_4", "number_5", "number_6",
    ]:
        if column in work.columns:
            work[column] = pd.to_numeric(work[column], errors="coerce")
    number_sets = [
        ["n1", "n2", "n3", "n4", "n5", "n6"],
        ["num1", "num2", "num3", "num4", "num5", "num6"],
        ["number_1", "number_2", "number_3", "number_4", "number_5", "number_6"],
    ]
    number_columns = []
    for columns in number_sets:
        if all(column in work.columns for column in columns):
            number_columns = columns
            break
    sort_columns = [
        column for column in [
            "year", "draw_number", "draw_no", "draw",
            "draw_position", "drawing_no", "position", "draw_id"
        ]
        if column in work.columns
    ]
    recent = work.sort_values(sort_columns, na_position="first").tail(rows).copy() if sort_columns else work.tail(rows).copy()
    display = pd.DataFrame(index=recent.index)
    if "date" in recent.columns:
        display[_bg("d094d0b0d182d0b0")] = (
            recent["date"]
            .astype(str)
            .replace({"None": "-", "nan": "-", "NaT": "-", "": "-"})
        )
    if "year" in recent.columns:
        display[_bg("d093d0bed0b4d0b8d0bdd0b0")] = recent["year"].apply(
            lambda value: "-" if pd.isna(value) else str(int(value))
        )
    draw_column = next((column for column in ["draw_number", "draw_no", "draw"] if column in recent.columns), None)
    if draw_column:
        display[_bg("d0a2d0b8d180d0b0d0b620e28496")] = recent[draw_column].apply(
            lambda value: "-" if pd.isna(value) else str(int(value))
        )
    position_column = next((column for column in ["draw_position", "drawing_no", "position"] if column in recent.columns), None)
    if position_column:
        display[_bg("d0a2d0b5d0b3d0bbd0b5d0bdd0b5")] = recent[position_column].apply(
            lambda value: "-" if pd.isna(value) else str(int(value))
        )
    if number_columns:
        def format_numbers(row):
            values = []
            for column in number_columns:
                value = row.get(column)
                if pd.isna(value):
                    continue
                values.append(str(int(value)))
            return " - ".join(values)
        display[_bg("d09ad0bed0bcd0b1d0b8d0bdd0b0d186d0b8d18f")] = recent.apply(format_numbers, axis=1)
    return display.reset_index(drop=True)
# HISTORY_RECENT_DRAWS_DISPLAY_END
def page_history() -> None:
    st.title(_bg("d098d181d182d0bed180d0b8d187d0b5d181d0bad0b020d181d182d0b0d182d0b8d181d182d0b8d0bad0b0"))
    st.info(
        _bg("d0a2d0b0d0b7d0b820d181d0b5d0bad186d0b8d18f20d0bfd0bed0bad0b0d0b7d0b2d0b020d0bed181d0bdd0bed0b2d0bdd0b020d0b8d181d182d0bed180d0b8d187d0b5d181d0bad0b020d181d182d0b0d182d0b8d181d182d0b8d0bad0b020d0bed18220d0bdd0b0d0b1d0bed180d0b020d0bed18220d0b4d0b0d0bdd0bdd0b82e20d0a2d18f20d0b520d0b7d0b020d0b0d0bdd0b0d0bbd0b8d0b72c20d0bdd0b520d0b7d0b020d0b3d0b0d180d0b0d0bdd186d0b8d18f20d0b7d0b020d0bfd0b5d187d0b0d0bbd0b1d0b02e")
    )
    try:
        data = load_data()
    except Exception as exc:
        st.error(f'{_bg("d094d0b0d0bdd0bdd0b8d182d0b520d0bdd0b520d0bcd0bed0b3d0b0d18220d0b4d0b020d181d0b520d0b7d0b0d180d0b5d0b4d18fd182")}: {exc}')
        return
    if data is None or len(data) == 0:
        st.warning(_bg("d09dd18fd0bcd0b020d0bdd0b0d0bbd0b8d187d0bdd0b820d0b8d181d182d0bed180d0b8d187d0b5d181d0bad0b820d0b4d0b0d0bdd0bdd0b820d0b7d0b020d0bfd0bed0bad0b0d0b7d0b2d0b0d0bdd0b52e"))
        return
    year_series = pd.to_numeric(data["year"], errors="coerce") if "year" in data.columns else None
    total_draws = len(data)
    first_year = int(year_series.min()) if year_series is not None and not year_series.dropna().empty else "-"
    last_year = int(year_series.max()) if year_series is not None and not year_series.dropna().empty else "-"
    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
    metric_col_1.metric(_bg("d09ed0b1d18920d0b1d180d0bed0b920d182d0b8d180d0b0d0b6d0b8"), f"{total_draws:,}")
    metric_col_2.metric(_bg("d09fd18ad180d0b2d0b020d0b3d0bed0b4d0b8d0bdd0b0"), first_year)
    metric_col_3.metric(_bg("d09fd0bed181d0bbd0b5d0b4d0bdd0b020d0b3d0bed0b4d0b8d0bdd0b0"), last_year)
    st.subheader(_bg("d09fd0bed181d0bbd0b5d0b4d0bdd0b820d182d0b8d180d0b0d0b6d0b8"))
    recent_display = _format_history_recent_draws(data, rows=10)
    if recent_display.empty:
        st.warning(_bg("d09dd18fd0bcd0b020d0b4d0bed181d182d0b0d182d18ad187d0bdd0be20d0b4d0b0d0bdd0bdd0b820d0b7d0b020d0bfd0bed181d0bbd0b5d0b4d0bdd0b820d182d0b8d180d0b0d0b6d0b82e"))
    else:
        st.dataframe(recent_display, hide_index=True, use_container_width=True)
    st.info(
        _bg("d098d181d182d0bed180d0b8d187d0b5d181d0bad0b0d182d0b020d181d182d0b0d182d0b8d181d182d0b8d0bad0b020d0bfd0bed0bcd0b0d0b3d0b020d0b7d0b020d181d180d0b0d0b2d0bdd0b5d0bdd0b8d0b520d0b820d0bed0b1d183d187d0b5d0bdd0b8d0b52c20d0bdd0be20d0bdd0b520d0bfd180d0b5d0b4d181d0bad0b0d0b7d0b2d0b020d0b1d18ad0b4d0b5d18920d182d0b8d180d0b0d0b620d0b820d0bdd0b520d0b3d0b0d180d0b0d0bdd182d0b8d180d0b020d0bfd0b5d187d0b0d0bbd0b1d0b02e")
    )
# V41_RULES_AWARE_STREAMLIT_HOOK_START
def page_v41_rules_aware_analysis() -> None:
    """Render the user-friendly rules-aware historical analysis section."""
    try:
        import importlib
        module = importlib.import_module("src.v41_rules_aware_analysis_section")
        module = importlib.reload(module)
        module.render_v41_rules_aware_analysis()
    except Exception as exc:
        st.warning(f"Историческият анализ не може да бъде показан в момента: {exc}")
# V41_RULES_AWARE_STREAMLIT_HOOK_END
# V42_COMBINED_ANALYSIS_STREAMLIT_HOOK_START
def _v42_bg(hex_text: str) -> str:
    return bytes.fromhex(hex_text).decode("utf-8")
def page_v42_combined_analysis() -> None:
    try:
        import importlib
        module = importlib.import_module("src.v42_combined_analysis_section")
        module = importlib.reload(module)
        module.render_v42_combined_analysis()
    except Exception as exc:
        st.warning(f'{_v42_bg("d094d0b0d0bdd0bdd0b8d182d0b520d0bdd0b02076343220d0bdd0b520d0bcd0bed0b3d0b0d18220d0b4d0b020d181d0b520d0b7d0b0d180d0b5d0b4d18fd182")}: {exc}')
def _rhythm_bg(hex_text: str) -> str:
    return bytes.fromhex(hex_text).decode("utf-8")
def page_interval_rhythm_analysis() -> None:
    import importlib
    module = importlib.import_module("src.v43_interval_rhythm_analysis_section")
    importlib.reload(module)
    module.render_interval_rhythm_analysis()
FINAL_ENSEMBLE_LABEL = "\u0424\u0438\u043d\u0430\u043b\u0435\u043d \u043e\u0431\u043e\u0431\u0449\u0435\u043d \u0430\u043d\u0430\u043b\u0438\u0437"
def page_final_ensemble_analysis():
    from importlib import reload
    import src.v44_final_ensemble_analysis_section as final_ensemble_section
    reload(final_ensemble_section)
    final_ensemble_section.render()
PREDICTION_DASHBOARD_PRO_LABEL = "Прогнозно табло Pro"
def page_prediction_dashboard_pro() -> None:
    from importlib import reload
    import src.v45_prediction_dashboard_pro_section as prediction_dashboard_pro_section
    reload(prediction_dashboard_pro_section)
    prediction_dashboard_pro_section.render()
STRATEGY_LAB_LABEL = "\u0421\u0442\u0440\u0430\u0442\u0435\u0433\u0438\u0447\u0435\u0441\u043a\u0430 \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f"
def page_strategy_lab() -> None:
    from importlib import reload
    import src.strategy_lab_section as strategy_lab_section
    reload(strategy_lab_section)
    strategy_lab_section.render()
BACKTESTING_CENTER_LABEL = "\u0426\u0435\u043d\u0442\u044a\u0440 \u0437\u0430 \u0438\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430"
def page_backtesting_center() -> None:
    from importlib import reload
    import src.backtesting_center_section as backtesting_center_section
    reload(backtesting_center_section)
    backtesting_center_section.render()
TICKET_BUILDER_LABEL = "\u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440 \u043d\u0430 \u043a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438"
def page_ticket_builder() -> None:
    from importlib import reload
    import src.ticket_builder_section as ticket_builder_section
    reload(ticket_builder_section)
    ticket_builder_section.render()
TRAINING_CENTER_LABEL = "\u0426\u0435\u043d\u0442\u044a\u0440 \u0437\u0430 \u043e\u0431\u0443\u0447\u0435\u043d\u0438\u0435"
def page_training_center() -> None:
    from importlib import reload
    import src.training_center_section as training_center_section
    reload(training_center_section)
    training_center_section.render()
PAIR_GROUP_LABEL = "\u0410\u043d\u0430\u043b\u0438\u0437 \u043d\u0430 \u0434\u0432\u043e\u0439\u043a\u0438 \u0438 \u0433\u0440\u0443\u043f\u0438"
def page_pair_group_analysis() -> None:
    from importlib import reload
    import src.v50_pair_group_analysis_section as pair_group_analysis_section
    reload(pair_group_analysis_section)
    pair_group_analysis_section.render()
TICKET_PORTFOLIO_LABEL = "Оценка на пакет"
def page_ticket_portfolio() -> None:
    from importlib import reload
    import src.v51_ticket_portfolio_section as ticket_portfolio_section
    reload(ticket_portfolio_section)
    ticket_portfolio_section.render()
def _rhythm_bg(hex_text: str) -> str:
    return bytes.fromhex(hex_text).decode("utf-8")
# V42_COMBINED_ANALYSIS_STREAMLIT_HOOK_END

# STEP88_ANTI_ZERO_COVERAGE_WRAPPER_START
def render_v88_anti_zero_coverage_section() -> None:
    from src.v88_anti_zero_coverage_section import render_v88_anti_zero_coverage_section as _render
    return _render()
# STEP88_ANTI_ZERO_COVERAGE_WRAPPER_END


# STEP89_FINAL_STATISTICAL_SELECTOR_WRAPPER_START
def render_v89_final_statistical_portfolio_selector_section() -> None:
    from src.v89_final_statistical_portfolio_selector_section import render_v89_final_statistical_portfolio_selector_section as _render
    return _render()
# STEP89_FINAL_STATISTICAL_SELECTOR_WRAPPER_END


# STEP90_SELECTOR_SOURCE_EXPANSION_WRAPPER_START
def render_v90_selector_source_expansion_section() -> None:
    from src.v90_selector_source_expansion_section import render_v90_selector_source_expansion_section as _render
    return _render()
# STEP90_SELECTOR_SOURCE_EXPANSION_WRAPPER_END

# STEP91_BUDGET_AWARE_SYSTEM_BUILDER_WRAPPER_START
def render_v91_budget_aware_system_builder_page() -> None:
    from src.v91_budget_aware_system_builder_section import render_v91_budget_aware_system_builder_section as _render
    return _render()
# STEP91_BUDGET_AWARE_SYSTEM_BUILDER_WRAPPER_END

# STEP92_SYSTEM_STRATEGY_BACKTEST_WRAPPER_START
def render_v92_system_strategy_backtest_center_page() -> None:
    from src.v92_system_strategy_backtest_center_section import render_v92_system_strategy_backtest_center_section as _render
    return _render()
# STEP92_SYSTEM_STRATEGY_BACKTEST_WRAPPER_END

# STEP93_BUDGET_ADVISOR_WRAPPER_START
def render_v93_budget_advisor_page() -> None:
    from src.v93_budget_advisor_section import render_v93_budget_advisor_section as _render
    return _render()
# STEP93_BUDGET_ADVISOR_WRAPPER_END

# STEP94_ACTIVE_BUDGET_PLAN_TRACKER_WRAPPER_START
def render_v94_active_budget_plan_tracker_page() -> None:
    from src.v94_active_budget_plan_tracker_section import render_v94_active_budget_plan_tracker_section as _render
    return _render()
# STEP94_ACTIVE_BUDGET_PLAN_TRACKER_WRAPPER_END

# STEP97_REAL_DRAW_LIFECYCLE_WRAPPER_START
def render_v97_real_draw_lifecycle_page() -> None:
    from src.v97_real_draw_lifecycle_section import render_v97_real_draw_lifecycle_section as _render
    return _render()
# STEP97_REAL_DRAW_LIFECYCLE_WRAPPER_END

# STEP98_ACTIVE_PLAN_RESULT_HISTORY_WRAPPER_START
def render_v98_active_plan_result_history_page() -> None:
    from src.v98_active_plan_result_history_section import render_v98_active_plan_result_history_section as _render
    return _render()
# STEP98_ACTIVE_PLAN_RESULT_HISTORY_WRAPPER_END

# STEP99_FINAL_USER_DASHBOARD_WRAPPER_START
def render_v99_final_user_dashboard_page() -> None:
    from src.v99_final_user_dashboard_section import render_v99_final_user_dashboard_section as _render
    return _render()
# STEP99_FINAL_USER_DASHBOARD_WRAPPER_END

# STEP100_FINAL_RELEASE_LOCK_WRAPPER_START
def render_v100_final_release_lock_page() -> None:
    from src.v100_final_release_lock_section import render_v100_final_release_lock_section as _render
    return _render()
# STEP100_FINAL_RELEASE_LOCK_WRAPPER_END
# STEP101_REAL_USE_PROTOCOL_WRAPPER_START
def render_v101_real_use_protocol_page() -> None:
    from src.v101_real_use_protocol_section import render_v101_real_use_protocol_section as _render
    return _render()
# STEP101_REAL_USE_PROTOCOL_WRAPPER_END

# STEP102_RUNTIME_HARDENING_WRAPPER_START
def render_v102_runtime_hardening_page() -> None:
    from src.v102_runtime_hardening_section import render_v102_runtime_hardening_section as _render
    return _render()
# STEP102_RUNTIME_HARDENING_WRAPPER_END

# STEP103_CLEAN_RELEASE_CHECKPOINT_WRAPPER_START
def render_v103_clean_release_checkpoint_page() -> None:
    from src.v103_clean_release_checkpoint_section import render_v103_clean_release_checkpoint_section as _render
    return _render()
# STEP103_CLEAN_RELEASE_CHECKPOINT_WRAPPER_END

# STEP104_FINAL_AUDIT_REFRESH_WRAPPER_START
def render_v104_final_audit_refresh_page() -> None:
    from src.v104_final_audit_refresh_section import render_v104_final_audit_refresh_section as _render
    return _render()
# STEP104_FINAL_AUDIT_REFRESH_WRAPPER_END

# STEP107_MODEL_TRAINING_POLICY_WRAPPER_START
def render_v107_model_training_policy_page() -> None:
    from src.v107_model_training_policy_section import render_v107_model_training_policy_section as _render
    return _render()
# STEP107_MODEL_TRAINING_POLICY_WRAPPER_END

# STEP109_SQLITE_JOURNAL_WRAPPER_START
def render_v109_sqlite_journal_page() -> None:
    from src.v109_sqlite_journal_section import render_v109_sqlite_journal_section as _render
    return _render()
# STEP109_SQLITE_JOURNAL_WRAPPER_END


# STEP111_PRIZE_WINNER_HISTORY_WRAPPER_START
def render_v111_prize_winner_history_page() -> None:
    from src.v111_prize_winner_history_section import render_v111_prize_winner_history_section as _render
    return _render()
# STEP111_PRIZE_WINNER_HISTORY_WRAPPER_END

# STEP110_USER_FRIENDLY_UI_POLISH_WRAPPER_START
def render_v110_user_friendly_ui_polish_page() -> None:
    from src.v110_user_friendly_ui_polish_section import render_v110_user_friendly_ui_polish_section as _render
    return _render()
# STEP110_USER_FRIENDLY_UI_POLISH_WRAPPER_END



# STEP111_7_HISTORICAL_PRIZE_ARCHIVE_HARVESTER_WRAPPER_START
def render_v111_7_historical_prize_archive_page() -> None:
    from src.v111_7_historical_prize_archive_section import render_v111_7_historical_prize_archive_section as _render
    return _render()
# STEP111_7_HISTORICAL_PRIZE_ARCHIVE_HARVESTER_WRAPPER_END

def main() -> None:
    page_glossary()
    pages = {

        "Потребителско меню": render_v87_synthesized_user_menu_section,
        "Финално табло": render_v99_final_user_dashboard_page,
        "Финално заключване": render_v100_final_release_lock_page,
        "Протокол за реална употреба": render_v101_real_use_protocol_page,
        "Runtime защита": render_v102_runtime_hardening_page,
        "Clean ZIP checkpoint": render_v103_clean_release_checkpoint_page,
        "Финален одит след Step 102": render_v104_final_audit_refresh_page,
        "Политика за обучение": render_v107_model_training_policy_page,
        "Потребителска яснота": render_v110_user_friendly_ui_polish_page,
        "Защита от празен фиш": render_v88_anti_zero_coverage_section,
        "Финален статистически избор": render_v89_final_statistical_portfolio_selector_section,
        "Интеграция на моделните резултати": render_v90_selector_source_expansion_section,
        "Системни фишове": render_v91_budget_aware_system_builder_page,
        "Тест на системни стратегии": render_v92_system_strategy_backtest_center_page,
        "Бюджетен съветник": render_v93_budget_advisor_page,
        "План и резултат": render_v94_active_budget_plan_tracker_page,
        "Реален цикъл на тираж": render_v97_real_draw_lifecycle_page,
        "История на активния план": render_v98_active_plan_result_history_page,
        "Дневник на фишовете": render_v109_sqlite_journal_page,
        "Исторически архив на печалби": render_v111_7_historical_prize_archive_page,
        "История на печалбите": render_v111_prize_winner_history_page,

        tr("dashboard"): page_dashboard,
        tr("recommendations"): page_recommendations,
        tr("combined"): page_combined,
        tr("advanced_lab"): page_advanced_lab,
        tr("ml_lab"): page_ml_lab,
        tr("prediction"): page_prediction,
        tr("ticket_analyzer"): page_ticket_analyzer,
        tr("history"): page_history,
        tr("v41_history_analysis"): page_v41_rules_aware_analysis,
        _v42_bg("d09ad0bed0bcd0b1d0b8d0bdd0b8d180d0b0d0bd20d0b0d0bdd0b0d0bbd0b8d0b7"): page_v42_combined_analysis,
        _rhythm_bg("d090d0bdd0b0d0bbd0b8d0b720d0bfd0be20d180d0b8d182d18ad0bc20d0bdd0b020d0bfd0bed18fd0b2d18fd0b2d0b0d0bdd0b5"): page_interval_rhythm_analysis,
        FINAL_ENSEMBLE_LABEL: page_final_ensemble_analysis,
        PREDICTION_DASHBOARD_PRO_LABEL: page_prediction_dashboard_pro,
        STRATEGY_LAB_LABEL: page_strategy_lab,
        BACKTESTING_CENTER_LABEL: page_backtesting_center,
        TICKET_BUILDER_LABEL: page_ticket_builder,
        TRAINING_CENTER_LABEL: page_training_center,
        PAIR_GROUP_LABEL: page_pair_group_analysis,
        TICKET_PORTFOLIO_LABEL: page_ticket_portfolio,
        tr("probability_lab"): page_probability_lab,
        tr("reports"): page_reports,
        tr("update_draws"): page_update_draws,
        "Покритие на комбинациите": render_v53_ticket_coverage_section,
        "Баланс на комбинациите": render_v54_pattern_balance_section,
        "Профил на число": render_v55_number_profile_section,
        "Горещи, студени и стабилни числа": render_v57_hot_cold_stable_section,
        "Обединена оценка": render_v58_smart_ensemble_score_section,
        "Интелигентен генератор 2": render_v59_smart_ticket_builder_2_section,
        "Анализ на нов тираж": render_v61_draw_result_analyzer_section,
        "История на моделите": render_v62_model_performance_tracker_section,
        "Надеждност на моделите": render_v63_model_reliability_dashboard_section,
        "Умно тегло на моделите": render_v65_model_weighting_section,
        "Претеглен комбиниран анализ": render_v66_weighted_smart_ensemble_section,
        "Умен генератор с тегла": render_v67_weighted_ticket_builder_section,
        "Умен оптимизатор на пакет": render_v68_weighted_portfolio_optimizer_section,
        "Подобряване на пакет": render_v69_portfolio_improvement_section,
        "Приложен подобрен пакет": render_v70_applied_candidate_portfolio_section,
        "Пакет за игра": render_v71_ticket_pack_export_section,
        "Представяне на пакета": render_v73_ticket_pack_performance_tracker_section,
        "Обновяване на анализите": render_v72_pipeline_refresh_section,
        "Контрол на синхрона": render_v74_model_dependency_sync_center_section,
        "Невронна лаборатория": render_v75_neural_meta_learner_section,
        "Обяснимост и валидация": render_v76_explainability_validation_section,
        "Решение и препоръка": render_v77_decision_recommendation_section,
        "Финален план": render_v78_final_play_plan_section,

        "Експорт и изпълнение": render_v79_ticket_pack_export_section,
        "Финален системен одит": render_v80_final_system_audit_section,
        "Финален UX контрол": render_v81_final_ux_navigation_section,
        "Финален пакет за предаване": render_v82_final_release_package_section,
        "Ръководство за апа": render_v83_final_user_manual_section,
"Сравнение на модели": render_v84_model_comparison_forward_test_section,
"Регистър на модели": render_v86_model_registry_trust_center_section,

        "Подобни исторически тиражи": render_v56_draw_similarity_section,
    }
    from src.v110_user_friendly_ui_helpers import friendly_page_label as _v110_page_label
    # STEP64_GROUPED_NAVIGATION_START
    navigation_groups = {
        '🏠 Начало и отчети': [

            'Потребителско меню',
            'Финално табло',
            'Финално заключване',
            'Протокол за реална употреба',
            'Runtime защита',
            'Clean ZIP checkpoint',
            'Финален одит след Step 102',
            'Потребителска яснота',

            'Табло',
            'Препоръки',
            'Прогноза',
            'Прогнозно табло Pro',
            'Отчети',
        ],
        '🎫 Комбинации и фишове': [
            'Анализ на комбинация',
            'Оценка на пакет',
            'Генератор на комбинации',
            'Интелигентен генератор 2',
            'Покритие на комбинациите',
            'Баланс на комбинациите',
            'Системни фишове',
            'Тест на системни стратегии',
            'Бюджетен съветник',
            'План и резултат',
            'Обединена оценка',
        ],
        '📊 Исторически анализи': [
            'Историческа статистика',
            'Исторически архив на печалби',
            'История на печалбите',
            'Анализ на минали тегления',
            'Подобни исторически тиражи',
            'Център за историческа проверка',
            'Профил на число',
            'Горещи, студени и стабилни числа',
            'Анализ по ритъм на появяване',
            'Анализ на двойки и групи',
        ],
        '🧠 Модели и обучение': [
            'Комбиниран модел',
            'Комбиниран анализ',
            'Разширена лаборатория',
            'МЛ лаборатория',
            'Център за обучение',
            'Политика за обучение',
            'Стратегическа лаборатория',
            'Вероятности',
            'Финален обобщен анализ',
            'Невронна лаборатория',
        ],
        '⚖️ Тегла и портфолио': [
            'История на моделите',
            'Надеждност на моделите',
            'Умно тегло на моделите',
            'Претеглен комбиниран анализ',
            'Умен генератор с тегла',
            'Умен оптимизатор на пакет',
            'Подобряване на пакет',
            'Приложен подобрен пакет',
            'Пакет за игра',
            'Представяне на пакета',
            'Защита от празен фиш',
            'Финален статистически избор',
            'Интеграция на моделните резултати',
        ],
        '✅ Финален план за игра': [
            'Добавяне на тираж',
            'Реален цикъл на тираж',
            'История на активния план',
            'Дневник на фишовете',
            'Анализ на нов тираж',
            'Обяснимост и валидация',
            'Решение и препоръка',
            'Финален план',

            'Експорт и изпълнение',
        ],
        '🛡️ Система и контрол': [
            'Обновяване на анализите',
            'Финален системен одит',
            'Финален UX контрол',
            'Финален пакет за предаване',
        'Ръководство за апа',
'Сравнение на модели',
'Регистър на модели',

            'Контрол на синхрона',
        ],
    }
    used_navigation_pages = set()
    visible_navigation_groups = {}
    for group_name, group_pages in navigation_groups.items():
        available_pages = [page for page in group_pages if page in pages]
        if available_pages:
            visible_navigation_groups[group_name] = available_pages
            used_navigation_pages.update(available_pages)
    other_pages = [page for page in pages.keys() if page not in used_navigation_pages]
    if other_pages:
        visible_navigation_groups['🗂️ Други'] = other_pages
    if not visible_navigation_groups:
        visible_navigation_groups['📋 Всички страници'] = list(pages.keys())
    # STEP105_ADD_DRAW_NAVIGATION_PERSISTENCE_FIX_START
    navigation_group_options = list(visible_navigation_groups.keys())
    pending_navigation_group = st.session_state.pop("_pending_navigation_group", None)
    pending_navigation_page = st.session_state.pop("_pending_navigation_page", None)

    if pending_navigation_group in navigation_group_options:
        st.session_state["nav_group_select"] = pending_navigation_group
    if st.session_state.get("nav_group_select") not in navigation_group_options:
        st.session_state["nav_group_select"] = navigation_group_options[0]

    selected_navigation_group = st.sidebar.selectbox(
        'Главен раздел',
        navigation_group_options,
        key="nav_group_select",
    )
    available_navigation_pages = visible_navigation_groups.get(selected_navigation_group, list(pages.keys()))
    if not available_navigation_pages:
        available_navigation_pages = list(pages.keys())

    if pending_navigation_page in available_navigation_pages:
        st.session_state["nav_page_radio"] = pending_navigation_page
    if st.session_state.get("nav_page_radio") not in available_navigation_pages:
        st.session_state["nav_page_radio"] = available_navigation_pages[0]

    choice = st.sidebar.radio('Страница', available_navigation_pages, key="nav_page_radio", format_func=_v110_page_label)
    st.session_state["selected_page"] = choice
    st.session_state["page"] = choice
    st.session_state["current_page"] = choice
    # STEP105_ADD_DRAW_NAVIGATION_PERSISTENCE_FIX_END
    # STEP64_GROUPED_NAVIGATION_END
    if st.sidebar.button("➕ Добави нов тираж", use_container_width=True, key="sidebar_add_draw_shortcut_btn"):
        st.cache_data.clear()
        _open_add_draw_from_sidebar_shortcut()
    pages[choice]()
if __name__ == "__main__":
    main()

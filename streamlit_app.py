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

# === LOTTERY BULGARIAN UI STABLE V32 START ===
# Stable Bulgarian display layer. It translates visible UI text only.
try:
    import pandas as _bg32_pd
    import inspect as _bg32_inspect
except Exception:  # pragma: no cover
    _bg32_pd = None
    _bg32_inspect = None


def _bg32_is_bulgarian() -> bool:
    try:
        values = [str(v) for v in st.session_state.values()]
        if any(v == "English" for v in values):
            return False
        if any(v == "Български" for v in values):
            return True
    except Exception:
        pass
    return True


_BG32_REPLACE = [
    ("Симулация / Simulation", "Симулация"),
    ("Simulation / Simulation", "Симулация"),
    ("Monte Carlo", "Монте Карло"),
    ("Historical replay", "Историческа проверка"),
    ("Исторически replay", "Историческа проверка"),
    ("backtesting", "историческа проверка"),
    ("Backtesting", "Историческа проверка"),
    ("backtest", "историческа проверка"),
    ("Backtest", "Историческа проверка"),
    ("Human pattern risk", "Риск от човешки шаблон"),
    ("Human-pattern risk", "Риск от човешки шаблон"),
    ("Human risk", "Човешки риск"),
    ("Low / Low", "Нисък"),
    ("Нисък / Low", "Нисък"),
    ("Medium / Medium", "Среден"),
    ("High / High", "Висок"),
    ("Hot / Frequency", "Горещ / честотен модел"),
    ("Hot / frequency", "Горещ / честотен модел"),
    ("Cold + Gap", "Студен + интервален модел"),
    ("Cold + gap", "Студен + интервален модел"),
    ("Middle / Balance", "Среден / балансиран модел"),
    ("Middle / Balanced", "Среден / балансиран модел"),
    ("Middle / balanced", "Среден / балансиран модел"),
    ("Gap / Interval", "Интервален модел"),
    ("Gap / interval", "Интервален модел"),
    ("Pair support", "Подкрепа по двойки"),
    ("Triple support", "Подкрепа по тройки"),
    ("Structure", "Структура"),
    ("Number-by-number", "Число по число"),
    ("Model analysis", "Анализ по модели"),
    ("Model", "Модел"),
    ("Numbers", "Числа"),
    ("Live score", "Текуща оценка"),
    ("Overlap with your ticket", "Съвпадения с твоя фиш"),
    ("Relative model probability", "Относителна моделна вероятност"),
    ("relative:", "относителна оценка:"),
    ("relative=", "относителна оценка="),
    ("relative", "относителна оценка"),
    ("Fairness / chi-square check", "Проверка за честност / хи-квадрат"),
    ("Fairness / chi-square test", "Проверка за честност / хи-квадрат"),
    ("Top recommendations", "Топ препоръки"),
    ("Diversified portfolio", "Диверсифицирано портфолио"),
    ("Historical check", "Историческа проверка"),
    ("Run historical check", "Пусни историческа проверка"),
    ("Random generated combination", "Случайно генерирана комбинация"),
    ("Final combined model", "Финален комбиниран модел"),
    ("Final combined", "Финален комбиниран модел"),
    ("Advanced ensemble model", "Разширен ансамблов модел"),
    ("Advanced ensemble", "Разширен ансамбъл"),
    ("Most frequent", "Най-често теглени числа"),
    ("Least frequent", "Най-рядко теглени числа"),
    ("Total combinations C(49, 6)", "Общ брой комбинации C(49, 6)"),
    ("probability_%", "Вероятност %"),
    ("1_in", "1 към"),
    ("1 in ", "1 към "),
    ("number", "Число"),
    ("count", "Брой"),
    ("empirical_%", "Емпиричен %"),
    ("expected_%", "Очакван %"),
    ("z_score", "Z-score"),
    ("avg_interval", "Среден интервал"),
    ("current_gap", "Текущ интервал"),
    ("gap_ratio", "Коефициент на интервал"),
    ("category", "Категория"),
    ("status", "Статус"),
    ("Choose options", "Избери числа"),
    ("Choose an option", "Избери опция"),
    ("Browse files", "Избери файл"),
    ("Upload", "Качи файл"),
    ("Manual entry", "Ръчно въвеждане"),
    ("Delete year", "Година за изтриване"),
    ("Delete draw number", "Номер на тираж за изтриване"),
    ("Delete position", "Позиция за изтриване"),
    ("This is a statistical ranking, not a guaranteed prediction.", "Това е статистическо класиране, не сигурно предсказване."),
]


def _bg32_text(value):
    if not _bg32_is_bulgarian() or not isinstance(value, str):
        return value
    out = value
    for src, dst in _BG32_REPLACE:
        out = out.replace(src, dst)
    return out


def _bg32_translate_dataframe(data):
    if not _bg32_is_bulgarian() or _bg32_pd is None:
        return data
    try:
        if not isinstance(data, _bg32_pd.DataFrame):
            return data
        df = data.copy()
        df = df.rename(columns={col: _bg32_text(str(col)) for col in df.columns})
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].map(lambda x: _bg32_text(x) if isinstance(x, str) else x)
        return df
    except Exception:
        return data


if not getattr(st, "_lottery_bulgarian_ui_stable_v32", False):
    st._lottery_bulgarian_ui_stable_v32 = True
    _bg32_orig_markdown = st.markdown
    _bg32_orig_write = st.write
    _bg32_orig_caption = st.caption
    _bg32_orig_info = st.info
    _bg32_orig_success = st.success
    _bg32_orig_warning = st.warning
    _bg32_orig_error = st.error
    _bg32_orig_title = st.title
    _bg32_orig_header = st.header
    _bg32_orig_subheader = st.subheader
    _bg32_orig_metric = st.metric
    _bg32_orig_button = st.button
    _bg32_orig_checkbox = st.checkbox
    _bg32_orig_radio = st.radio
    _bg32_orig_tabs = st.tabs
    _bg32_orig_selectbox = st.selectbox
    _bg32_orig_slider = st.slider
    _bg32_orig_select_slider = st.select_slider
    _bg32_orig_multiselect = st.multiselect
    _bg32_orig_text_input = st.text_input
    _bg32_orig_number_input = st.number_input
    _bg32_orig_file_uploader = st.file_uploader
    _bg32_orig_download_button = st.download_button
    _bg32_orig_dataframe = st.dataframe
    _bg32_orig_table = st.table

    def _bg32_markdown(body, *args, **kwargs): return _bg32_orig_markdown(_bg32_text(body), *args, **kwargs)
    def _bg32_write(*args, **kwargs): return _bg32_orig_write(*tuple(_bg32_text(a) if isinstance(a, str) else a for a in args), **kwargs)
    def _bg32_caption(body, *args, **kwargs): return _bg32_orig_caption(_bg32_text(body), *args, **kwargs)
    def _bg32_info(body, *args, **kwargs): return _bg32_orig_info(_bg32_text(body), *args, **kwargs)
    def _bg32_success(body, *args, **kwargs): return _bg32_orig_success(_bg32_text(body), *args, **kwargs)
    def _bg32_warning(body, *args, **kwargs): return _bg32_orig_warning(_bg32_text(body), *args, **kwargs)
    def _bg32_error(body, *args, **kwargs): return _bg32_orig_error(_bg32_text(body), *args, **kwargs)
    def _bg32_title(body, *args, **kwargs): return _bg32_orig_title(_bg32_text(body), *args, **kwargs)
    def _bg32_header(body, *args, **kwargs): return _bg32_orig_header(_bg32_text(body), *args, **kwargs)
    def _bg32_subheader(body, *args, **kwargs): return _bg32_orig_subheader(_bg32_text(body), *args, **kwargs)
    def _bg32_metric(label, value, delta=None, *args, **kwargs): return _bg32_orig_metric(_bg32_text(label), _bg32_text(value), _bg32_text(delta), *args, **kwargs)
    def _bg32_button(label, *args, **kwargs): return _bg32_orig_button(_bg32_text(label), *args, **kwargs)
    def _bg32_checkbox(label, *args, **kwargs): return _bg32_orig_checkbox(_bg32_text(label), *args, **kwargs)
    def _bg32_radio(label, options, *args, **kwargs): return _bg32_orig_radio(_bg32_text(label), options, *args, **kwargs)
    def _bg32_tabs(tabs, *args, **kwargs): return _bg32_orig_tabs([_bg32_text(t) if isinstance(t, str) else t for t in tabs], *args, **kwargs)
    def _bg32_selectbox(label, options, *args, **kwargs): return _bg32_orig_selectbox(_bg32_text(label), options, *args, **kwargs)
    def _bg32_slider(label, *args, **kwargs): return _bg32_orig_slider(_bg32_text(label), *args, **kwargs)
    def _bg32_select_slider(label, *args, **kwargs): return _bg32_orig_select_slider(_bg32_text(label), *args, **kwargs)
    def _bg32_multiselect(label, options, *args, **kwargs):
        if _bg32_is_bulgarian() and _bg32_inspect is not None:
            try:
                if "placeholder" in _bg32_inspect.signature(_bg32_orig_multiselect).parameters:
                    kwargs.setdefault("placeholder", "Избери числа")
            except Exception:
                pass
        return _bg32_orig_multiselect(_bg32_text(label), options, *args, **kwargs)
    def _bg32_text_input(label, *args, **kwargs):
        if "value" in kwargs and isinstance(kwargs.get("value"), str): kwargs["value"] = _bg32_text(kwargs["value"])
        if "placeholder" in kwargs and isinstance(kwargs.get("placeholder"), str): kwargs["placeholder"] = _bg32_text(kwargs["placeholder"])
        return _bg32_orig_text_input(_bg32_text(label), *args, **kwargs)
    def _bg32_number_input(label, *args, **kwargs): return _bg32_orig_number_input(_bg32_text(label), *args, **kwargs)
    def _bg32_file_uploader(label, *args, **kwargs): return _bg32_orig_file_uploader(_bg32_text(label), *args, **kwargs)
    def _bg32_download_button(label, *args, **kwargs): return _bg32_orig_download_button(_bg32_text(label), *args, **kwargs)
    def _bg32_dataframe_widget(data=None, *args, **kwargs): return _bg32_orig_dataframe(_bg32_translate_dataframe(data), *args, **kwargs)
    def _bg32_table_widget(data=None, *args, **kwargs): return _bg32_orig_table(_bg32_translate_dataframe(data), *args, **kwargs)

    st.markdown = _bg32_markdown
    st.write = _bg32_write
    st.caption = _bg32_caption
    st.info = _bg32_info
    st.success = _bg32_success
    st.warning = _bg32_warning
    st.error = _bg32_error
    st.title = _bg32_title
    st.header = _bg32_header
    st.subheader = _bg32_subheader
    st.metric = _bg32_metric
    st.button = _bg32_button
    st.checkbox = _bg32_checkbox
    st.radio = _bg32_radio
    st.tabs = _bg32_tabs
    st.selectbox = _bg32_selectbox
    st.slider = _bg32_slider
    st.select_slider = _bg32_select_slider
    st.multiselect = _bg32_multiselect
    st.text_input = _bg32_text_input
    st.number_input = _bg32_number_input
    st.file_uploader = _bg32_file_uploader
    st.download_button = _bg32_download_button
    st.dataframe = _bg32_dataframe_widget
    st.table = _bg32_table_widget
# === LOTTERY BULGARIAN UI STABLE V32 END ===


# === LOTTERY REPORTS VISUAL V23 START ===
# Safe Bulgarian renderer for advanced историческа проверка reports.
# This block avoids raw English markdown lines in the Reports page.
try:
    import re as _lr23_re
    import pandas as _lr23_pd
except Exception:  # pragma: no cover
    _lr23_re = None
    _lr23_pd = None


def _lr23_nums(raw):
    numbers = []
    for token in str(raw or "").replace(",", " ").split():
        token = "".join(ch for ch in token if ch.isdigit())
        if token:
            try:
                numbers.append(int(token))
            except Exception:
                pass
    return numbers


def _lr23_strategy_label(name):
    labels = {
        "advanced": "Разширен ансамбъл",
        "time_decay": "Time-decay модел",
        "bayesian": "Bayesian smoothing",
        "gap": "Gap / интервален модел",
        "frequency_stability": "Честотна стабилност",
        "random": "Случаен baseline",
    }
    return labels.get(str(name), str(name).replace("_", " "))


def _lr23_markdown_safe(body, *args, **kwargs):
    try:
        return _lr23_original_markdown(body, *args, **kwargs)
    except NameError:
        return st.markdown(body, *args, **kwargs)


def _lr23_balls(numbers, size=34):
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
    _lr23_markdown_safe("".join(parts), unsafe_allow_html=True)


def _lr23_parse_strategy_rows(text_value):
    if not _lr23_re:
        return []
    rows = []
    pattern = _lr23_re.compile(
        r"^\s*([A-Za-z_]+):\s*avg=([0-9.]+),\s*>=3=([0-9.]+)%,\s*>=4=([0-9.]+)%",
        _lr23_re.M,
    )
    for name, avg, ge3, ge4 in pattern.findall(text_value):
        rows.append({
            "Стратегия": _lr23_strategy_label(name),
            "Код": name,
            "Средни съвпадения": float(avg),
            ">=3 съвпадения %": float(ge3),
            ">=4 съвпадения %": float(ge4),
        })
    return rows


def _lr23_parse_recent_draws(text_value):
    if not _lr23_re:
        return []
    rows = []
    pattern = _lr23_re.compile(
        r"Draw\s+(\d+)\s*\(([^)]*)\):\s*"
        r"actual=\[([^\]]*)\],\s*"
        r"advanced=\[([^\]]*)\]\s*\((\d+)\s+matches?\),\s*"
        r"random=\[([^\]]*)\]\s*\((\d+)\s+matches?\)",
        _lr23_re.I,
    )
    for draw, date, actual, advanced, adv_matches, random_ticket, rnd_matches in pattern.findall(text_value):
        rows.append({
            "Тираж": int(draw),
            "Дата": date.strip() or "-",
            "Реални числа": _lr23_nums(actual),
            "Advanced фиш": _lr23_nums(advanced),
            "Advanced съвпадения": int(adv_matches),
            "Random фиш": _lr23_nums(random_ticket),
            "Random съвпадения": int(rnd_matches),
        })
    return rows


def _lr23_render_report(text_value):
    if not isinstance(text_value, str):
        return False
    if "actual=[" not in text_value and "Recent tested draws" not in text_value and "Advanced историческа проверка engine" not in text_value:
        return False

    _lr23_markdown_safe("## Отчет от историческа проверка")

    tested = None
    best_strategy = None
    if _lr23_re:
        tested_match = _lr23_re.search(r"Tested draws:\s*(\d+)", text_value)
        if tested_match:
            tested = int(tested_match.group(1))
        best_match = _lr23_re.search(r"Best strategy:\s*([A-Za-z_]+)", text_value)
        if best_match:
            best_strategy = best_match.group(1)

    cols = st.columns(3)
    cols[0].metric("Тествани тиражи", tested if tested is not None else "-")
    cols[1].metric("Най-добра стратегия", _lr23_strategy_label(best_strategy) if best_strategy else "-")
    cols[2].metric("Важно", "Не е доказателство", help="Историческа проверка-ът е проверка назад във времето, не гаранция за бъдещи тегления.")

    strategy_rows = _lr23_parse_strategy_rows(text_value)
    if strategy_rows and _lr23_pd is not None:
        _lr23_markdown_safe("### Сравнение на стратегиите")
        strategy_df = _lr23_pd.DataFrame(strategy_rows)
        st.dataframe(strategy_df, width="stretch", hide_index=True)
        try:
            chart_df = strategy_df.set_index("Стратегия")[["Средни съвпадения"]]
            st.bar_chart(chart_df, height=260)
        except Exception:
            pass

    if best_strategy:
        st.info(
            "Най-добрата стратегия в този историческа проверка е: "
            f"{_lr23_strategy_label(best_strategy)}. "
            "Това е проверка на модела, не доказателство, че бъдещи тегления са предсказуеми."
        )

    recent_rows = _lr23_parse_recent_draws(text_value)
    if recent_rows:
        _lr23_markdown_safe("### Последни тествани тиражи")
        if _lr23_pd is not None:
            table_rows = []
            for row in recent_rows:
                table_rows.append({
                    "Тираж": row["Тираж"],
                    "Дата": row["Дата"],
                    "Реални числа": ", ".join(map(str, row["Реални числа"])),
                    "Advanced фиш": ", ".join(map(str, row["Advanced фиш"])),
                    "Advanced съвпадения": row["Advanced съвпадения"],
                    "Random фиш": ", ".join(map(str, row["Random фиш"])),
                    "Random съвпадения": row["Random съвпадения"],
                })
            st.dataframe(_lr23_pd.DataFrame(table_rows), width="stretch", hide_index=True)

        with st.expander("Виж последните тиражи визуално", expanded=False):
            for row in recent_rows[:20]:
                _lr23_markdown_safe(f"#### Тираж {row['Тираж']} {'' if row['Дата'] == '-' else row['Дата']}")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.caption("Реални числа")
                    _lr23_balls(row["Реални числа"])
                with c2:
                    st.caption(f"Advanced фиш — {row['Advanced съвпадения']} съвпадения")
                    _lr23_balls(row["Advanced фиш"])
                with c3:
                    st.caption(f"Random фиш — {row['Random съвпадения']} съвпадения")
                    _lr23_balls(row["Random фиш"])
                st.divider()

    st.download_button(
        "Свали оригиналния отчет",
        data=text_value,
        file_name="advanced_backtest_report.md",
        mime="text/markdown",
    )
    return True


if not getattr(st, "_lottery_reports_visual_v23", False):
    st._lottery_reports_visual_v23 = True
    _lr23_original_markdown = st.markdown
    _lr23_original_write = st.write
    _lr23_original_code = st.code

    def _lr23_markdown(body, *args, **kwargs):
        try:
            if isinstance(body, str) and _lr23_render_report(body):
                return
        except Exception:
            pass
        return _lr23_original_markdown(body, *args, **kwargs)

    def _lr23_write(*args, **kwargs):
        try:
            if len(args) == 1 and isinstance(args[0], str) and _lr23_render_report(args[0]):
                return
        except Exception:
            pass
        return _lr23_original_write(*args, **kwargs)

    def _lr23_code(body, *args, **kwargs):
        try:
            if isinstance(body, str) and _lr23_render_report(body):
                return
        except Exception:
            pass
        return _lr23_original_code(body, *args, **kwargs)

    st.markdown = _lr23_markdown
    st.write = _lr23_write
    st.code = _lr23_code
# === LOTTERY REPORTS VISUAL V23 END ===

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
        "top_recommendations": "Top recommendations",
        "all_models": "Препоръки от всички модели",
        "hot_model": "Горещ / честотен модел",
        "cold_model": "Студен + интервален модел",
        "middle_model": "Среден / балансиран модел",
        "gap_model": "Интервален модел",
        "combined_model": "Финален комбиниран модел",
        "advanced_model": "Разширен ансамблов модел",
        "train_advanced": "Обучи разширения ансамбъл",
        "run_backtest": "Пусни историческа проверка",
        "no_model": "Моделът още не е наличен. Пусни training скрипта.",
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
        "portfolio": "Diversified portfolio",
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
        "backtest": "Историческа проверка",
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
            st.error("Simulation Lab could not be loaded.")
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
        return '<div class="small-muted">No numbers available</div>'
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
            or item.get("score")
        )
        rank = item.get("rank") or item.get("relative_rank") or idx
        rel_prob = item.get("relative_model_probability") or item.get("relative_probability")
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
    for key in ["recommended_combinations", "top_recommendations", "recommendations", "top_combinations"]:
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
        score = item.get("confidence_score") or item.get("confidence") or item.get("final_score") or item.get("score")
        return sorted([int(x) for x in numbers]) if numbers else [], score
    return extract_single_ticket(model), model.get("confidence_score") or model.get("score") if model else None


def get_model_cards() -> List[Tuple[str, str, str, str]]:
    return [
        (tr("advanced_model"), "lottery_advanced_ensemble_model.json", "advanced", "Advanced methods: time-decay, Bayesian smoothing, fairness, co-occurrence, portfolio and историческа проверка signals."),
        (tr("combined_model"), "lottery_combined_model.json", "combined", "Final weighted ranking using the original model family."),
        (tr("hot_model"), "lottery_frequency_model.json", "hot", "Numbers with stronger historical frequency / stability signal."),
        (tr("cold_model"), "lottery_cold_model.json", "cold", "Numbers influenced by underrepresentation and current gap."),
        (tr("middle_model"), "lottery_middle_model.json", "middle", "Numbers close to expected frequency and balanced behavior."),
        (tr("gap_model"), "lottery_gap_model.json", "gap", "Numbers with stronger interval / overdue signal."),
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
        render_ticket_card(tr("main_recommendation") + " · " + tr("advanced_model"), adv_numbers, adv_score, "Advanced ensemble", tr("not_prediction"))
    with c2:
        render_ticket_card(tr("main_recommendation") + " · " + tr("combined_model"), comb_numbers, comb_score, "Final combined", tr("not_prediction"))

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
    render_ticket_card(tr("combined_model"), numbers, score, "models/lottery_combined_model.json", tr("not_prediction"))
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
    render_ticket_card(tr("main_recommendation") + " · " + tr("advanced_model"), numbers, score, "models/lottery_advanced_ensemble_model.json", tr("not_prediction"))
    tabs = st.tabs([tr("top_recommendations"), tr("portfolio"), tr("fairness"), tr("историческа проверка")])
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
    st.metric("Total combinations C(49, 6)", f"{total:,}")
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
    selected = st.selectbox("Отчет", files, format_func=lambda p: p.name)
    render_report_file(selected)


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
            st.success(f"Detected numbers: {parsed}")
        else:
            st.error("Could not detect exactly 6 unique valid numbers.")

    detected = st.session_state.get("uploaded_numbers", [])
    default_numbers = detected if detected else [1, 2, 3, 4, 5, 6]

    c1, c2, c3 = st.columns(3)
    draw_date = c1.date_input(tr("draw_date"), value=date.today())
    year = c2.number_input(tr("year"), min_value=1958, max_value=2100, value=int(draw_date.year))
    draw_number = c3.number_input(tr("draw_number"), min_value=0, max_value=9999, value=1)
    position = st.number_input(tr("draw_position"), min_value=1, max_value=20, value=1)
    numbers = st.multiselect(tr("numbers"), options=list(range(1, 50)), default=default_numbers[:6], max_selections=6)
    source = st.text_input(tr("source"), value="Manual entry")

    if st.button(tr("save_draw"), width="stretch"):
        nums = sorted([int(n) for n in numbers])
        if len(nums) != 6 or len(set(nums)) != 6:
            st.error(tr("ticket_warning"))
        else:
            rows, fields = read_csv_rows()
            key = (str(int(year)), str(int(draw_number)), str(int(position)))
            exists = any((str(r.get("year")), str(r.get("draw_number")), str(r.get("draw_position"))) == key for r in rows)
            if exists:
                st.error("This year + draw number + position already exists.")
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
                st.success(f"Saved draw {year}/{draw_number}/{position}. Backup: {backup.name if backup else 'none'}")
                if auto_retrain:
                    with st.spinner("Retraining models..."):
                        results = retrain_all_models()
                    for script, ok, output in results:
                        st.write(("✅" if ok else "❌") + " " + script)
                    st.info("Refresh the page to see updated recommendations.")

    st.divider()
    st.markdown("### Корекция / изтриване на тираж")
    c1, c2, c3 = st.columns(3)
    del_year = c1.number_input("Delete year", min_value=1958, max_value=2100, value=int(date.today().year))
    del_draw = c2.number_input("Delete draw number", min_value=0, max_value=9999, value=1)
    del_pos = c3.number_input("Delete position", min_value=1, max_value=20, value=1)
    if st.button(tr("delete_draw"), width="stretch"):
        rows, fields = read_csv_rows()
        key = (str(int(del_year)), str(int(del_draw)), str(int(del_pos)))
        new_rows = [r for r in rows if (str(r.get("year")), str(r.get("draw_number")), str(r.get("draw_position"))) != key]
        if len(new_rows) == len(rows):
            st.warning("No matching draw found.")
        else:
            backup = backup_csv("before_manual_delete")
            write_csv_rows(new_rows, fields)
            st.success(f"Deleted draw {key}. Backup: {backup.name if backup else 'none'}")
            if auto_retrain:
                with st.spinner("Retraining models..."):
                    retrain_all_models()
                st.info("Refresh the page to see updated recommendations.")

    backups = sorted(BACKUP_DIR.glob("*.csv"), reverse=True)
    if backups:
        if st.button(tr("undo"), width="stretch"):
            latest = backups[0]
            shutil.copy2(latest, DATA_PATH)
            st.success(f"Restored backup: {latest.name}")
            if auto_retrain:
                with st.spinner("Retraining models..."):
                    retrain_all_models()
                st.info("Refresh the page to see updated recommendations.")


def page_glossary() -> None:
    with st.expander(tr("term_help"), expanded=False):
        st.markdown(
            """
            **Hot / Горещо** — число с по-силен честотен сигнал в историята.  
            **Cold / Студено** — число под очакваната честота или с по-слаб честотен сигнал.  
            **Gap / Интервал** — колко тиража са минали от последното излизане.  
            **Overdue / Отдавна не е излизало** — текущият gap е по-голям от обичайния интервал.  
            **Среден / балансиран моделd / Балансирано** — близо до очакваната честота.  
            **Confidence / Оценка** — моделна оценка за ранкинг, не процент шанс за джакпот.
            """
        )


def main() -> None:
    page_glossary()
    pages = {
        tr("dashboard"): page_dashboard,
        tr("recommendations"): page_recommendations,
        tr("combined"): page_combined,
        tr("advanced_lab"): page_advanced_lab,
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

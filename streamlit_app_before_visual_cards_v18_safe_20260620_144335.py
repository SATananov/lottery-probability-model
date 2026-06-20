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

# --- VISUAL JSON CARDS V17 START ---
# Converts raw st.json(...) outputs into readable visual cards/tables.
# This keeps the app understandable for non-technical users.
_ORIGINAL_ST_JSON_V17 = getattr(st, "json", None)

_VISUAL_LABELS_V17 = {
    "odd": "Нечетни",
    "even": "Четни",
    "low": "Ниски числа",
    "middle": "Средни числа",
    "high": "Високи числа",
    "sum": "Сбор",
    "consecutive_pairs": "Поредни двойки",
    "numbers_under_31": "Числа под 31",
    "numbers": "Числа",
    "combination": "Комбинация",
    "ticket": "Фиш",
    "confidence_score": "Моделна оценка",
    "confidence": "Моделна оценка",
    "final_score": "Краен score",
    "relative_model_probability": "Относителна моделна вероятност",
    "relative_probability": "Относителна вероятност",
    "hot_score": "Hot score / честотен сигнал",
    "cold_score": "Cold + gap score",
    "middle_score": "Middle / баланс score",
    "gap_score": "Gap / интервал score",
    "pair_score": "Двойки score",
    "triple_score": "Тройки score",
    "structure_score": "Структурен score",
    "human_pattern_risk": "Human pattern risk",
    "times_drawn": "Пъти изтеглено",
    "empirical_probability": "Емпирична вероятност",
    "expected_probability": "Очаквана вероятност",
    "gap": "Текущ gap",
    "avg_interval": "Среден интервал",
    "gap_ratio": "Gap ratio",
    "status": "Статус",
    "rank": "Ранг",
}

_VISUAL_HELP_V17 = {
    "odd": "Брой нечетни числа във фиша.",
    "even": "Брой четни числа във фиша.",
    "low": "Колко числа са в ниския диапазон.",
    "middle": "Колко числа са в средния диапазон.",
    "high": "Колко числа са във високия диапазон.",
    "sum": "Сборът на всички 6 числа. Нормалните фишове обикновено не са нито прекалено ниски, нито прекалено високи.",
    "consecutive_pairs": "Колко поредни двойки има, например 22–23 или 34–35.",
    "numbers_under_31": "Брой числа до 31. Много такива числа може да означава по-човешки фиш, защото хората често играят дати.",
    "human_pattern_risk": "Оценка дали фишът прилича на човешки избор, например рождени дати, поредици или красиви модели.",
    "confidence_score": "Това е моделна оценка за ранкинг, не реален процент за печалба.",
    "relative_model_probability": "Относителна оценка вътре в модела, не реален шанс за джакпот.",
}


def _visual_css_v17() -> None:
    st.markdown(
        """
        <style>
        .vj-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 10px 0 20px 0; }
        .vj-card { border: 1px solid rgba(226, 190, 103, 0.28); background: linear-gradient(145deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025)); border-radius: 18px; padding: 16px 16px 14px 16px; box-shadow: 0 12px 28px rgba(0,0,0,0.18); }
        .vj-label { color: rgba(255,255,255,0.70); font-size: 0.83rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 7px; }
        .vj-value { color: #fff8e8; font-size: 1.7rem; font-weight: 800; line-height: 1.12; }
        .vj-help { color: rgba(255,255,255,0.62); font-size: 0.9rem; margin-top: 8px; line-height: 1.35; }
        .vj-good { color: #79e6a2; font-weight: 700; }
        .vj-warn { color: #ffd36a; font-weight: 700; }
        .vj-balls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 8px 0 14px 0; }
        .vj-ball { width: 44px; height: 44px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: radial-gradient(circle at 30% 25%, #fff6ce, #d6a73f 62%, #7a5a19); color: #17140c; font-weight: 900; font-size: 1.05rem; box-shadow: inset 0 2px 3px rgba(255,255,255,0.75), 0 8px 18px rgba(0,0,0,0.35); }
        .vj-note { border-left: 4px solid #d9b461; background: rgba(217,180,97,0.10); border-radius: 14px; padding: 12px 14px; color: #fff4d6; margin: 10px 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _label_v17(key) -> str:
    key_text = str(key)
    return _VISUAL_LABELS_V17.get(key_text, key_text.replace("_", " ").title())


def _format_value_v17(value) -> str:
    if isinstance(value, float):
        if abs(value) < 1 and value != 0:
            return f"{value:.6f}"
        return f"{value:.2f}"
    if isinstance(value, bool):
        return "Да" if value else "Не"
    if value is None:
        return "—"
    return str(value)


def _is_number_list_v17(value) -> bool:
    return isinstance(value, (list, tuple)) and len(value) > 0 and all(isinstance(x, int) or (isinstance(x, str) and str(x).isdigit()) for x in value)


def _balls_html_v17(numbers) -> str:
    balls = "".join(f'<span class="vj-ball">{int(n)}</span>' for n in numbers)
    return f'<div class="vj-balls">{balls}</div>'


def _structure_message_v17(data: dict) -> str:
    messages = []
    odd = data.get("odd")
    even = data.get("even")
    if isinstance(odd, int) and isinstance(even, int):
        if abs(odd - even) <= 2:
            messages.append("<span class='vj-good'>Четни/нечетни: добър баланс.</span>")
        else:
            messages.append("<span class='vj-warn'>Четни/нечетни: по-небалансирана структура.</span>")
    total = data.get("sum")
    if isinstance(total, (int, float)):
        if 100 <= total <= 200:
            messages.append("<span class='vj-good'>Сборът е в нормална зона.</span>")
        else:
            messages.append("<span class='vj-warn'>Сборът е по-краен и заслужава внимание.</span>")
    pairs = data.get("consecutive_pairs")
    if isinstance(pairs, int):
        if pairs == 0:
            messages.append("<span class='vj-good'>Няма поредни двойки.</span>")
        elif pairs <= 1:
            messages.append("<span class='vj-warn'>Има една поредна двойка.</span>")
        else:
            messages.append("<span class='vj-warn'>Има повече поредни числа.</span>")
    under_31 = data.get("numbers_under_31")
    if isinstance(under_31, int):
        if under_31 <= 3:
            messages.append("<span class='vj-good'>Нормален риск от човешки избор по дати.</span>")
        else:
            messages.append("<span class='vj-warn'>Повече числа под 31 — възможен по-човешки фиш.</span>")
    return "<br>".join(messages)


def _render_dict_cards_v17(data: dict) -> None:
    _visual_css_v17()

    number_keys = ["numbers", "combination", "ticket"]
    for key in number_keys:
        if key in data and _is_number_list_v17(data[key]):
            st.markdown(_balls_html_v17(data[key]), unsafe_allow_html=True)
            break

    # Special readable summary for combination structure.
    if {"odd", "even", "low", "middle", "high", "sum"}.issubset(set(data.keys())):
        st.markdown("#### Структура на комбинацията")
        summary = _structure_message_v17(data)
        if summary:
            st.markdown(f'<div class="vj-note">{summary}</div>', unsafe_allow_html=True)

    cards = []
    nested = []
    for key, value in data.items():
        if _is_number_list_v17(value):
            continue
        if isinstance(value, dict) or (isinstance(value, list) and value and isinstance(value[0], dict)):
            nested.append((key, value))
            continue
        help_text = _VISUAL_HELP_V17.get(str(key), "")
        cards.append(
            f"""
            <div class="vj-card">
                <div class="vj-label">{_label_v17(key)}</div>
                <div class="vj-value">{_format_value_v17(value)}</div>
                {f'<div class="vj-help">{help_text}</div>' if help_text else ''}
            </div>
            """
        )

    if cards:
        st.markdown('<div class="vj-grid">' + "".join(cards) + '</div>', unsafe_allow_html=True)

    for key, value in nested:
        with st.expander(_label_v17(key), expanded=False):
            _visual_json_v17(value)


def _render_list_cards_v17(data: list) -> None:
    _visual_css_v17()
    if not data:
        st.info("Няма данни за показване.")
        return
    if all(_is_number_list_v17(item) for item in data):
        for index, numbers in enumerate(data, start=1):
            st.markdown(f"**Rank {index}**", unsafe_allow_html=True)
            st.markdown(_balls_html_v17(numbers), unsafe_allow_html=True)
        return
    if all(isinstance(item, dict) for item in data):
        # Show compact table first, then cards for the first few rows if they contain tickets/numbers.
        try:
            import pandas as _pd
            table_rows = []
            for item in data:
                table_rows.append({ _label_v17(k): (", ".join(map(str, v)) if _is_number_list_v17(v) else v) for k, v in item.items() if not isinstance(v, (dict, list)) or _is_number_list_v17(v) })
            if table_rows:
                try:
                    st.dataframe(_pd.DataFrame(table_rows), width="stretch")
                except TypeError:
                    st.dataframe(_pd.DataFrame(table_rows), use_container_width=True)
        except Exception:
            pass
        for index, item in enumerate(data[:5], start=1):
            with st.expander(f"Детайл {index}", expanded=index == 1):
                _render_dict_cards_v17(item)
        if len(data) > 5:
            st.caption(f"Показани са първите 5 от общо {len(data)} записа.")
        return
    if _ORIGINAL_ST_JSON_V17:
        _ORIGINAL_ST_JSON_V17(data)
    else:
        st.write(data)


def _visual_json_v17(body=None, expanded=True, **kwargs) -> None:
    """Drop-in replacement for st.json that renders readable visual cards."""
    if isinstance(body, dict):
        _render_dict_cards_v17(body)
        return
    if isinstance(body, list):
        _render_list_cards_v17(body)
        return
    if _ORIGINAL_ST_JSON_V17:
        _ORIGINAL_ST_JSON_V17(body, expanded=expanded, **kwargs)
    else:
        st.write(body)


# Monkey-patch Streamlit JSON rendering for the whole app.
st.json = _visual_json_v17
# --- VISUAL JSON CARDS V17 END ---


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "historical_draws.csv"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
BACKUP_DIR = ROOT / "data" / "manual_backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

THEORETICAL_ODDS_TEXT = "1 in 13,983,816"
EXPECTED_NUMBER_PROB = 6 / 49

TRANSLATIONS = {
    "bg": {
        "language": "Език",
        "app_title": "Лотарийна статистическа лаборатория 6/49",
        "app_caption": "Анализ, модели, backtesting и визуални препоръки. Не гарантира печалба.",
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
        "top_recommendations": "Топ препоръки",
        "all_models": "Препоръки от всички модели",
        "hot_model": "Hot / честотен модел",
        "cold_model": "Cold + gap модел",
        "middle_model": "Middle / балансиран модел",
        "gap_model": "Gap / интервален модел",
        "combined_model": "Final combined модел",
        "advanced_model": "Advanced ensemble модел",
        "train_advanced": "Обучи разширения ансамбъл",
        "run_backtest": "Пусни backtesting",
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
        "portfolio": "Диверсифицирано портфолио",
        "fairness": "Fairness / chi-square проверка",
        "backtest": "Backtesting",
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
        "run_backtest": "Run backtesting",
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
        return st.sidebar.button(label, use_container_width=True, key=key)


def _v13_simulation_lab_hook() -> None:
    if "v13_simulation_lab_active" not in st.session_state:
        st.session_state["v13_simulation_lab_active"] = False

    st.sidebar.markdown("---")
    if _v13_sidebar_button("🎲 Симулация / Simulation", "v13_open_simulation_lab"):
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
                meta_parts.append(f"relative: {float(rel_prob):.6f}%")
            except Exception:
                meta_parts.append(f"relative: {rel_prob}")
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
        (tr("advanced_model"), "lottery_advanced_ensemble_model.json", "advanced", "Advanced methods: time-decay, Bayesian smoothing, fairness, co-occurrence, portfolio and backtesting signals."),
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
            with st.spinner("Training advanced model..."):
                ok, output = run_script("train_advanced_model.py")
            st.success("Done" if ok else "Failed")
            st.code(output[-4000:] if output else "No output")
            st.cache_data.clear()
    with c2:
        if st.button(tr("run_backtest"), width="stretch"):
            with st.spinner("Running backtest..."):
                ok, output = run_script("run_advanced_backtest.py")
            st.success("Done" if ok else "Failed")
            st.code(output[-4000:] if output else "No output")
            st.cache_data.clear()

    model = model_json("lottery_advanced_ensemble_model.json")
    numbers, score = main_recommendation(model)
    render_ticket_card(tr("main_recommendation") + " · " + tr("advanced_model"), numbers, score, "models/lottery_advanced_ensemble_model.json", tr("not_prediction"))
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
            st.info("No fairness results saved in the model file yet.")
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
        render_ticket_card("Вашият фиш / Your ticket", ticket, None, tr("real_odds") + ": " + THEORETICAL_ODDS_TEXT, tr("not_prediction"))
        if not stats.empty:
            view = stats[stats["number"].isin(ticket)].sort_values("number")
            st.dataframe(view, width="stretch", hide_index=True)
            avg_z = view["z_score"].mean()
            avg_gap = view["gap"].mean()
            c1, c2, c3 = st.columns(3)
            c1.metric("Average z-score", f"{avg_z:.2f}")
            c2.metric("Average gap", f"{avg_gap:.1f}")
            c3.metric(tr("real_odds"), THEORETICAL_ODDS_TEXT)


def page_history() -> None:
    render_header()
    df = load_draws()
    st.markdown("## " + tr("history"))
    if df.empty:
        st.warning("No historical data loaded.")
        return
    stats = compute_number_stats(df)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Most frequent")
        st.dataframe(stats.sort_values("count", ascending=False).head(12), width="stretch", hide_index=True)
    with c2:
        st.markdown("### Least frequent")
        st.dataframe(stats.sort_values("count", ascending=True).head(12), width="stretch", hide_index=True)
    st.markdown("### Number frequency chart")
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
    render_ticket_card("Random generated combination", ticket, None, "", tr("not_prediction"))


def render_report_file(path: Path) -> None:
    if not path.exists():
        st.info(f"Report not found: {path.name}")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    limit = st.slider("Preview lines", 20, min(max(len(lines), 20), 800), min(120, max(len(lines), 20)), key=f"slider_{path.name}")
    st.markdown("\n".join(lines[:limit]))
    st.download_button("Download report", data=text, file_name=path.name, mime="text/markdown", key=f"download_{path.name}")


def page_reports() -> None:
    render_header()
    st.markdown("## " + tr("reports"))
    files = sorted(REPORTS_DIR.glob("*.md")) if REPORTS_DIR.exists() else []
    if not files:
        st.info("No reports found.")
        return
    selected = st.selectbox("Report", files, format_func=lambda p: p.name)
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
            **Middle / Balanced / Балансирано** — близо до очакваната честота.  
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

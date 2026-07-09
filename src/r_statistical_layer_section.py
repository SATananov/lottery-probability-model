
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
REPORTS_R_DIR = ROOT / "reports" / "r"
PLOTS_DIR = REPORTS_R_DIR / "plots"
SUMMARY_MD = REPORTS_R_DIR / "r_statistical_summary.md"

CSV_REPORTS = [
    ("Одит на данните", REPORTS_R_DIR / "r_data_audit.csv"),
    ("Честоти на числата", REPORTS_R_DIR / "r_frequency_statistics.csv"),
    ("Интервали / gaps", REPORTS_R_DIR / "r_gap_statistics.csv"),
    ("Тестове на разпределението", REPORTS_R_DIR / "r_distribution_tests.csv"),
    ("Monte Carlo baseline", REPORTS_R_DIR / "r_monte_carlo_baseline.csv"),
    ("Анализ на двойки", REPORTS_R_DIR / "r_pair_analysis.csv"),
    ("Анализ на модели / pattern", REPORTS_R_DIR / "r_pattern_analysis.csv"),
]

PLOT_REPORTS = [
    ("Честота на числата", PLOTS_DIR / "number_frequency.png"),
    ("Най-големи текущи интервали", PLOTS_DIR / "largest_current_gaps.png"),
    ("Monte Carlo честотен baseline", PLOTS_DIR / "monte_carlo_frequency_baseline.png"),
    ("Разпределение на сумата", PLOTS_DIR / "draw_sum_distribution.png"),
    ("Разпределение по нечетни числа", PLOTS_DIR / "odd_count_distribution.png"),
    ("Разпределение по ниски числа", PLOTS_DIR / "low_count_distribution.png"),
    ("Топ двойки", PLOTS_DIR / "top_pairs.png"),
]


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except Exception:
            pass
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(path)


def render_r_statistical_layer_section() -> None:
    st.title("R статистически слой")
    st.caption(
        "Независим R слой за статистическа проверка: честоти, gaps, разпределения, "
        "двойки и Monte Carlo baseline. Страницата чете готовите файлове от reports/r."
    )

    st.info(
        "R не прави лотарията предвидима. Той служи като независима проверка, "
        "диагностика на данните и контролен статистически слой към Python моделите."
    )

    if SUMMARY_MD.exists():
        st.subheader("Обобщение")
        st.markdown(SUMMARY_MD.read_text(encoding="utf-8", errors="replace"))
    else:
        st.warning(f"Липсва summary файл: `{_relative(SUMMARY_MD)}`")

    st.subheader("Ключови графики")
    found_plot = False
    for title, path in PLOT_REPORTS:
        if path.exists():
            found_plot = True
            st.markdown(f"#### {title}")
            st.image(str(path), use_container_width=True)
            st.caption(_relative(path))

    if not found_plot:
        st.warning("Не са намерени R PNG графики в `reports/r/plots/`.")

    st.subheader("CSV отчети")
    for title, path in CSV_REPORTS:
        with st.expander(title, expanded=False):
            if not path.exists():
                st.warning(f"Липсва файл: `{_relative(path)}`")
                continue

            df = _read_csv(path)
            if df.empty:
                st.warning(f"Файлът е празен или не може да бъде прочетен: `{_relative(path)}`")
                continue

            st.caption(_relative(path))
            st.dataframe(df, use_container_width=True)

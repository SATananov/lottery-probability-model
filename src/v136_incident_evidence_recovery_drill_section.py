from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from src.v136_incident_evidence_recovery_drill_engine import (
    DRILL_CONFIRMATION, build_recovery_drill_plan, run_recovery_drill, write_recovery_drill_status,
)


def render_v136_incident_evidence_recovery_drill_section() -> None:
    st.subheader('Recovery drill & restore validation')
    st.caption('Изолирана проверка дали архивиран evidence bundle може да бъде възстановен и повторно валидиран без production restore.')
    plan = build_recovery_drill_plan()
    a, b = st.columns(2)
    a.metric('Архивирани bundle-и', plan['candidate_count'])
    b.metric('Допустими за drill', plan['eligible_count'])
    if plan['candidates']:
        st.dataframe(pd.DataFrame(plan['candidates']), hide_index=True, use_container_width=True)
    eligible = [row for row in plan['candidates'] if row['eligible']]
    if not eligible:
        st.info('Няма допустими VERIFIED архивирани bundle-и за recovery drill.')
        return
    selected = st.selectbox('Bundle за recovery drill', eligible, format_func=lambda row: row['name'])
    phrase = st.text_input('Recovery drill confirmation phrase', key='v136_drill_confirmation')
    retain = st.checkbox('Запази изолираната staging копия за ръчен преглед', value=False)
    if st.button('Стартирай изолиран recovery drill', use_container_width=True):
        try:
            result = run_recovery_drill(Path(selected['path']), confirmation=phrase, retain_staging_copy=retain)
            write_recovery_drill_status(result)
            if result['drill_verdict'] == 'passed':
                st.success('Recovery drill PASSED. Bundle-ът е възстановим и целостта му е потвърдена.')
            else:
                st.error('Recovery drill FAILED.')
            st.json(result)
        except (PermissionError, RuntimeError, FileNotFoundError) as exc:
            st.error(str(exc))
    st.caption(f'Точна фраза: `{DRILL_CONFIRMATION}`')
    st.warning('Този модул никога не връща автоматично ZIP в production/export папките и не променя registry историята.')

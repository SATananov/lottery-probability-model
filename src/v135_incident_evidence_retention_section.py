from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v135_incident_evidence_retention_engine import (
    ARCHIVE_CONFIRMATION,
    CLEANUP_CONFIRMATION,
    apply_archive_plan,
    apply_cleanup_plan,
    build_retention_plan,
    write_default_policy,
    write_retention_status,
)


def render_v135_incident_evidence_retention_section() -> None:
    st.subheader('Retention, archive & safe cleanup')
    st.caption('Fail-closed политика: preview по подразбиране, архивира само стари VERIFIED bundle-и и никога не променя append-only registry историята.')

    write_default_policy()
    if st.button('Обнови retention preview', use_container_width=True, key='v135_preview'):
        plan = build_retention_plan()
        write_retention_status(plan)
        st.session_state['v135_retention_plan'] = plan

    plan = st.session_state.get('v135_retention_plan') or build_retention_plan()
    counts = plan['counts']
    a, b, c, d = st.columns(4)
    a.metric('Active', counts['active'])
    b.metric('Protected', counts['protected'])
    c.metric('To archive', counts['archive_candidates'])
    d.metric('To clean', counts['cleanup_candidates'])

    policy = plan['policy']
    st.info(
        f"Active retention: {policy['retention_days_active']} дни · "
        f"Archive cleanup: {policy['archive_cleanup_days']} дни · "
        f"Minimum active verified: {policy['minimum_active_verified_bundles']}"
    )

    with st.expander('Archive candidates', expanded=bool(plan['archive_candidates'])):
        if plan['archive_candidates']:
            st.dataframe(pd.DataFrame(plan['archive_candidates']), hide_index=True, use_container_width=True)
        else:
            st.caption('Няма bundle-и, допустими за архивиране.')
    with st.expander('Protected evidence'):
        if plan['protected']:
            st.dataframe(pd.DataFrame(plan['protected']), hide_index=True, use_container_width=True)
        else:
            st.caption('Няма защитени активни записи.')
    with st.expander('Expired archive cleanup candidates', expanded=bool(plan['cleanup_candidates'])):
        if plan['cleanup_candidates']:
            st.dataframe(pd.DataFrame(plan['cleanup_candidates']), hide_index=True, use_container_width=True)
        else:
            st.caption('Няма изтекли архивни копия за почистване.')

    st.warning('Прилагането мести или изтрива само точно показаните ZIP копия след повторна SHA-256 проверка. Registry JSONL не се променя.')
    archive_phrase = st.text_input('Archive confirmation phrase', key='v135_archive_confirmation')
    if st.button('Приложи архивиране', disabled=not plan['archive_candidates'], use_container_width=True, key='v135_apply_archive'):
        try:
            result = apply_archive_plan(plan, confirmation=archive_phrase)
            st.success(f"Архивирани bundle-и: {result['item_count']}")
            st.session_state['v135_retention_plan'] = build_retention_plan()
        except (PermissionError, RuntimeError) as exc:
            st.error(str(exc))
    st.caption(f'Точна фраза: `{ARCHIVE_CONFIRMATION}`')

    cleanup_phrase = st.text_input('Cleanup confirmation phrase', key='v135_cleanup_confirmation')
    if st.button('Изтрий изтеклите архивни копия', disabled=not plan['cleanup_candidates'], use_container_width=True, key='v135_apply_cleanup'):
        try:
            result = apply_cleanup_plan(plan, confirmation=cleanup_phrase)
            st.success(f"Изтрити архивни копия: {result['item_count']}")
            st.session_state['v135_retention_plan'] = build_retention_plan()
        except (PermissionError, RuntimeError) as exc:
            st.error(str(exc))
    st.caption(f'Точна фраза: `{CLEANUP_CONFIRMATION}`')

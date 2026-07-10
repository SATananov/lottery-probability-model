from __future__ import annotations

import streamlit as st

from src.v132_production_incident_evidence_engine import build_incident_evidence, build_incident_evidence_zip


def render_v132_production_incident_evidence_section(*, timeout_seconds: int = 30) -> None:
    st.subheader('Incident evidence export')
    st.caption('Създава безопасен диагностичен ZIP без activation token, тайни и промяна на production състоянието.')

    live_evidence = st.checkbox(
        'Включи нова read-only live БСТ проверка в evidence bundle',
        value=False,
        key='v132_live_evidence_check',
    )
    if st.button('Подготви incident evidence bundle', use_container_width=True, key='v132_build_evidence'):
        evidence = build_incident_evidence(
            live_bst_check=live_evidence,
            timeout_seconds=timeout_seconds,
            write_outputs=False,
        )
        st.session_state['v132_incident_evidence'] = evidence

    evidence = st.session_state.get('v132_incident_evidence')
    if not evidence:
        st.info('Bundle още не е подготвен. Действието е read-only.')
        return

    snapshot = evidence['operations_snapshot']
    a, b, c = st.columns(3)
    a.metric('Bundle ID', evidence['bundle_id'])
    b.metric('Health', snapshot['health'].upper())
    c.metric('Secrets redacted', 'Да' if evidence['secrets_redacted'] else 'Не')

    archive_bytes = build_incident_evidence_zip(evidence)
    st.download_button(
        'Изтегли incident evidence ZIP',
        data=archive_bytes,
        file_name=f"{evidence['bundle_id']}.zip",
        mime='application/zip',
        use_container_width=True,
    )
    with st.expander('Преглед на операторското резюме'):
        st.markdown(evidence['operator_summary_md'])
    st.success('Evidence bundle е подготвен без production mutation и без тежко ML retraining.')

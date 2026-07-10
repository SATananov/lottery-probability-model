from __future__ import annotations

import streamlit as st

from src.v133_incident_evidence_integrity_engine import MAX_ARCHIVE_BYTES, inspect_incident_evidence_zip


def render_v133_incident_evidence_integrity_section() -> None:
    st.subheader('Evidence integrity inspector')
    st.caption('Проверява ZIP checksum-и, bundle identity, безопасни пътища и липса на изложени тайни. Не разархивира върху диска.')

    uploaded = st.file_uploader(
        'Избери Step 132 incident evidence ZIP',
        type=['zip'],
        key='v133_evidence_zip',
        help=f'Максимален размер: {MAX_ARCHIVE_BYTES // (1024 * 1024)} MB',
    )
    if uploaded is None:
        st.info('Качи incident evidence ZIP, за да бъде проверен локално и read-only.')
        return

    archive_bytes = uploaded.getvalue()
    if st.button('Провери целостта на evidence bundle', use_container_width=True, key='v133_verify_evidence'):
        st.session_state['v133_integrity_result'] = inspect_incident_evidence_zip(
            archive_bytes,
            source_name=uploaded.name,
            write_outputs=False,
        )

    result = st.session_state.get('v133_integrity_result')
    if not result:
        return

    verdict = result['verdict']
    a, b, c = st.columns(3)
    a.metric('Verdict', verdict.upper())
    b.metric('Bundle ID', result.get('bundle_id') or 'unknown')
    c.metric('Failed checks', result['failed_check_count'])

    if verdict == 'verified':
        st.success('Evidence bundle е криптографски и структурно потвърден спрямо manifest-а.')
    else:
        st.error('Evidence bundle не премина проверката. Не го използвай като доверено incident доказателство.')

    st.code(result['archive_sha256'], language=None)
    st.dataframe(result['checks'], hide_index=True, use_container_width=True)
    with st.expander('Пълен integrity report'):
        st.markdown(result['summary_md'])

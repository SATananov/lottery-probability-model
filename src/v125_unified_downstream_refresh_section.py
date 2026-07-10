from __future__ import annotations
import streamlit as st
from src.v125_unified_downstream_refresh_engine import PIPELINE, run_unified_downstream_refresh


def render_v125_unified_downstream_refresh_section() -> None:
    st.title('Обновяване по цялата верига')
    st.caption('Step 125 — синхронизира downstream данните и оперативните решения след нов официален тираж. Не преобучава тежките ML модели.')
    st.info('Ред: historical → normalized → canonical → R → Step 121 → Decision Center → ticket packs → freshness check.')
    for index, stage in enumerate(PIPELINE, start=1):
        st.write(f"{index}. **{stage['name']}**")
    timeout = st.slider('Timeout за отделен етап (секунди)', 60, 1800, 900, 60)
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Покажи план', use_container_width=True):
            st.session_state['v125_report'] = run_unified_downstream_refresh(plan_only=True)
    with col2:
        if st.button('Стартирай безопасното обновяване', type='primary', use_container_width=True):
            with st.spinner('Обновяване по веригата...'):
                st.session_state['v125_report'] = run_unified_downstream_refresh(timeout_seconds=timeout)
    report = st.session_state.get('v125_report')
    if not report:
        return
    if report.get('status') == 'completed':
        st.success('Всички оперативни downstream етапи приключиха успешно.')
    elif report.get('status') == 'planned':
        st.info('Планът е готов. Не са направени промени.')
    else:
        st.error('Веригата спря безопасно. Следващите етапи са блокирани до отстраняване на грешката.')
    for row in report.get('stages', []):
        icon = '✅' if row.get('ok') else ('⏸️' if row.get('status') in {'planned','blocked'} else '❌')
        with st.expander(f"{icon} {row.get('name')} — {row.get('status')}"):
            st.write(row.get('message',''))
            if row.get('output_tail'):
                st.code(row['output_tail'])

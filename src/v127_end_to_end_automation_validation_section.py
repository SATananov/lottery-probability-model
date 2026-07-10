from __future__ import annotations

import streamlit as st

from src.v127_end_to_end_automation_validation_engine import run_end_to_end_validation


def render_v127_end_to_end_automation_validation_section() -> None:
    st.title('End-to-End проверка на автоматизацията')
    st.caption('Step 127 — контролирана симулация на следващ официален тираж в изолиран test sandbox. Реалните данни не се променят.')
    st.info('Сценарият доказва: detect → safe ingest → downstream refresh simulation → freshness synced → duplicate protection → rollback → production isolation.')
    st.warning('Това е тестова симулация. Не се свързва с БСТ, не добавя реален тираж и не стартира тежко ML обучение.')

    if st.button('Стартирай пълната изолирана проверка', type='primary', use_container_width=True):
        with st.spinner('Изпълнява се end-to-end тестът в изолирана временна среда...'):
            st.session_state['v127_report'] = run_end_to_end_validation(write_outputs=True)

    report = st.session_state.get('v127_report')
    if not report:
        return
    if report.get('status') == 'validated':
        st.success(f"Цялата контролирана верига е потвърдена със симулиран тираж {report.get('simulated_draw_key')}.")
    else:
        st.error('Един или повече етапи на end-to-end проверката не преминаха.')

    c1, c2, c3 = st.columns(3)
    c1.metric('Симулиран тираж', report.get('simulated_draw_key', '—'))
    c2.metric('Неуспешни етапи', report.get('failed_stage_count', 0))
    c3.metric('Реалните данни са непроменени', 'Да' if report.get('production_data_unchanged') else 'Не')

    for row in report.get('stages', []):
        icon = '✅' if row.get('ok') else '❌'
        with st.expander(f"{icon} {row.get('name')}"):
            st.write(row.get('message', ''))
            details = {k: v for k, v in row.items() if k not in {'id', 'name', 'status', 'ok', 'message'}}
            if details:
                st.json(details)

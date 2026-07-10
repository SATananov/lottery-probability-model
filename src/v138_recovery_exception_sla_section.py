from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v138_recovery_exception_sla_engine import (
    ACK_CONFIRMATION,
    build_exception_follow_up_queue,
    record_follow_up_event,
    write_exception_follow_up_status,
)


def render_v138_recovery_exception_sla_section() -> None:
    st.subheader('Recovery exception SLA, escalation & follow-up queue')
    st.caption('Подрежда отворените Step 137 exceptions по риск и срок, без автоматично затваряне или промяна на evidence данните.')
    status = build_exception_follow_up_queue()
    write_exception_follow_up_status(status)
    a, b, c, d = st.columns(4)
    a.metric('Open', status['open_count'])
    b.metric('Overdue', status['overdue_count'])
    c.metric('Due soon', status['due_soon_count'])
    d.metric('Critical', status['critical_count'])
    if status['rows']:
        st.dataframe(pd.DataFrame(status['rows']), hide_index=True, use_container_width=True)
    else:
        st.info('Все още няма reconciliation exceptions за SLA проследяване.')
        return
    if not status['action_queue']:
        st.success('Няма отворени exceptions за follow-up.')
        return
    selected = st.selectbox(
        'Exception за операторски follow-up',
        status['action_queue'],
        format_func=lambda row: f"{row['exception_id']} · {row['priority'].upper()} · {row['sla_state'].upper()} · {row['bundle_id']}",
    )
    note = st.text_area('Операторска follow-up бележка', key='v138_operator_note')
    phrase = st.text_input('Escalation acknowledgement confirmation phrase', key='v138_ack_confirmation')
    if st.button('Потвърди escalation follow-up', use_container_width=True):
        try:
            event = record_follow_up_event(selected, operator_note=note, confirmation=phrase)
            st.success('Follow-up събитието е записано append-only. Exception-ът остава отворен до Step 137 closure.')
            st.json(event)
        except (PermissionError, ValueError) as exc:
            st.error(str(exc))
    st.caption(f'Точна фраза: `{ACK_CONFIRMATION}`')
    st.warning('Тази операция не затваря exception, не променя recovery audit и не докосва evidence ZIP файлове.')

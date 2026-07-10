from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v137_recovery_drill_audit_reconciliation_engine import (
    CLOSE_CONFIRMATION,
    build_reconciliation_status,
    close_reconciliation_exception,
    write_reconciliation_status,
)


def render_v137_recovery_drill_audit_reconciliation_section() -> None:
    st.subheader('Recovery drill reconciliation & exception closure')
    st.caption('Съпоставя Step 136 drill audit-а с Step 134 registry и открива chain-of-custody несъответствия.')
    status = build_reconciliation_status()
    write_reconciliation_status(status)
    a, b, c, d = st.columns(4)
    a.metric('Drill събития', status['drill_count'])
    b.metric('Reconciled', status['reconciled_count'])
    c.metric('Open exceptions', status['open_exception_count'])
    d.metric('Closed exceptions', status['closed_exception_count'])
    if status['rows']:
        st.dataframe(pd.DataFrame(status['rows']), hide_index=True, use_container_width=True)
    else:
        st.info('Все още няма recovery drill audit събития за reconciliation.')
        return
    if not status['open_exceptions']:
        st.success('Няма отворени reconciliation exceptions.')
        return
    selected = st.selectbox(
        'Отворено изключение',
        status['open_exceptions'],
        format_func=lambda row: f"{row['exception_id']} · {row['bundle_id']} · {', '.join(row['exception_codes'])}",
    )
    note = st.text_area('Операторска бележка за затваряне', key='v137_operator_note')
    phrase = st.text_input('Exception closure confirmation phrase', key='v137_close_confirmation')
    if st.button('Затвори reconciliation exception', use_container_width=True):
        try:
            event = close_reconciliation_exception(selected, operator_note=note, confirmation=phrase)
            st.success('Exception-ът е затворен с append-only операторски audit запис.')
            st.json(event)
        except (PermissionError, ValueError) as exc:
            st.error(str(exc))
    st.caption(f'Точна фраза: `{CLOSE_CONFIRMATION}`')
    st.warning('Затварянето не поправя и не променя evidence ZIP, registry или recovery drill audit. То документира операторското решение.')

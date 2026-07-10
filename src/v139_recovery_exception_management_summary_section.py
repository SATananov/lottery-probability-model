from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from src.v139_recovery_exception_management_summary_engine import (
    build_recovery_exception_management_summary,
    management_summary_csv,
    management_summary_markdown,
    write_recovery_exception_management_summary,
)


def render_v139_recovery_exception_management_summary_section() -> None:
    st.subheader('Recovery exception reporting & management summary')
    st.caption('Read-only управленски преглед на recovery drills, exceptions, SLA нарушения и действията, които изискват внимание.')
    status = build_recovery_exception_management_summary()
    write_recovery_exception_management_summary(status)

    health = status['management_health']
    if health == 'GREEN':
        st.success('Management health: GREEN — няма отворени recovery risks, които изискват незабавно действие.')
    elif health == 'AMBER':
        st.warning('Management health: AMBER — има отворени или наближаващи SLA случаи за проследяване.')
    else:
        st.error('Management health: RED — има overdue, critical или failed recovery drill случаи.')

    a, b, c, d, e = st.columns(5)
    a.metric('Open', status['open_exception_count'])
    b.metric('Closed', status['closed_exception_count'])
    c.metric('Overdue', status['overdue_exception_count'])
    d.metric('Critical', status['critical_open_count'])
    e.metric('Failed drills', status['latest_failed_drill_count'])

    st.markdown('#### Какво изисква внимание')
    if status['attention_required']:
        st.dataframe(pd.DataFrame(status['attention_required']), hide_index=True, use_container_width=True)
    else:
        st.success('Няма management actions, които изискват незабавно внимание.')

    st.markdown('#### Последни recovery drill резултати')
    if status['latest_drills']:
        st.dataframe(pd.DataFrame(status['latest_drills']), hide_index=True, use_container_width=True)
    else:
        st.info('Все още няма recovery drill audit записи.')

    st.markdown('#### Exception status')
    if status['exception_rows']:
        st.dataframe(pd.DataFrame(status['exception_rows']), hide_index=True, use_container_width=True)
    else:
        st.info('Няма recovery exceptions.')

    json_bytes = json.dumps(status, ensure_ascii=False, indent=2).encode('utf-8')
    md_bytes = management_summary_markdown(status).encode('utf-8')
    csv_bytes = management_summary_csv(status).encode('utf-8-sig')
    x, y, z = st.columns(3)
    x.download_button('JSON management summary', data=json_bytes, file_name='step139_recovery_exception_management_summary.json', mime='application/json', use_container_width=True)
    y.download_button('Markdown management summary', data=md_bytes, file_name='step139_recovery_exception_management_summary.md', mime='text/markdown', use_container_width=True)
    z.download_button('CSV attention queue', data=csv_bytes, file_name='step139_recovery_exception_attention_queue.csv', mime='text/csv', use_container_width=True)
    st.caption('Step 139 не acknowledge-ва и не затваря exceptions. Оперативните действия остават в Step 137 и Step 138.')

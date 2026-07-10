from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from src.v140_production_operations_module_closure_engine import (
    build_module_closure_status,
    module_closure_markdown,
    write_module_closure_status,
)


def render_v140_production_operations_module_closure_section() -> None:
    st.subheader('Production operations module closure')
    st.caption('Финална read-only QA проверка за комплектност на Step 131–140 и официално затваряне на модула.')
    status = build_module_closure_status()
    write_module_closure_status(status)

    if status['closure_ready']:
        st.success('MODULE CLOSED — Production Operations / Incident Evidence / Recovery Governance е комплектен и финално проверен.')
    else:
        st.error(f"CLOSURE BLOCKED — липсват {status['missing_component_count']} задължителни компонента.")

    a, b, c = st.columns(3)
    a.metric('Компоненти', f"{status['present_component_count']}/{status['required_component_count']}")
    b.metric('Липсващи', status['missing_component_count'])
    c.metric('Step range', status['step_range'])

    group_rows = [
        {
            'Група': group['group'],
            'Налични': group['present_count'],
            'Задължителни': group['required_count'],
            'Статус': 'PASS' if group['complete'] else 'BLOCKED',
        }
        for group in status['component_groups']
    ]
    st.dataframe(pd.DataFrame(group_rows), hide_index=True, use_container_width=True)

    if status['missing_components']:
        st.markdown('#### Липсващи компоненти')
        st.code('\n'.join(status['missing_components']))

    st.markdown('#### Closure boundaries')
    for boundary in status['read_only_boundaries']:
        st.write(f'• {boundary}')

    x, y = st.columns(2)
    x.download_button(
        'JSON closure status',
        data=json.dumps(status, ensure_ascii=False, indent=2).encode('utf-8'),
        file_name='step140_production_operations_module_closure.json',
        mime='application/json',
        use_container_width=True,
    )
    y.download_button(
        'Markdown closure report',
        data=module_closure_markdown(status).encode('utf-8'),
        file_name='step140_production_operations_module_closure.md',
        mime='text/markdown',
        use_container_width=True,
    )
    st.caption('Step 140 не изпълнява activation, ingestion, restore, cleanup, downstream refresh или ML retraining.')

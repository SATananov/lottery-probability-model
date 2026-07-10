from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v134_incident_evidence_registry_engine import (
    load_registry_events,
    rebuild_registry_status,
    registry_events_csv,
)


def render_v134_incident_evidence_registry_section() -> None:
    st.subheader('Evidence registry & verification history')
    st.caption('Append-only история на CREATED, VERIFIED и INVALID събития. Пази metadata и SHA-256, но не пази ZIP съдържание или тайни.')

    try:
        events = load_registry_events()
        status = rebuild_registry_status(write_outputs=False)
    except ValueError as exc:
        st.error(f'Registry журналът е невалиден: {exc}')
        return

    a, b, c, d = st.columns(4)
    a.metric('Bundles', status['bundle_count'])
    b.metric('Events', status['event_count'])
    c.metric('Verified', status['verified_count'])
    d.metric('Invalid', status['invalid_count'])

    if not events:
        st.info('Registry-то е празно. Създай Step 132 bundle или провери ZIP чрез Step 133.')
        return

    event_types = sorted({str(item.get('event_type')) for item in events})
    selected = st.multiselect('Event type', event_types, default=event_types, key='v134_event_type_filter')
    filtered = [item for item in reversed(events) if item.get('event_type') in selected]
    st.dataframe(pd.DataFrame(filtered), hide_index=True, use_container_width=True)
    st.download_button(
        'Изтегли registry history CSV',
        data=registry_events_csv(filtered),
        file_name='incident_evidence_registry_history.csv',
        mime='text/csv',
        use_container_width=True,
    )
    with st.expander('Bundle status snapshot'):
        st.dataframe(pd.DataFrame(status['bundles']), hide_index=True, use_container_width=True)

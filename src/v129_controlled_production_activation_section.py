from __future__ import annotations

import streamlit as st

from src.v129_controlled_production_activation_engine import (
    build_preflight,
    execute_one_time_activation,
    issue_one_time_activation_token,
    run_dry_run,
)


def render_v129_controlled_production_activation_section() -> None:
    st.title('Контролирано production активиране и dry-run')
    st.caption('Step 129 — dry-run, финален preflight, operator summary и еднократно activation разрешение за конкретен тираж.')

    st.info('Dry-run не записва тираж и не стартира downstream refresh. Реалното активиране остава блокирано, докато всички Step 128 guardrails не са готови и няма валидиран нов тираж.')

    if st.button('Изпълни production dry-run', type='primary', use_container_width=True):
        with st.spinner('Финален preflight без промени по данните...'):
            st.session_state['v129_dry_run'] = run_dry_run()

    report = st.session_state.get('v129_dry_run')
    if not report:
        preflight = build_preflight()
        st.subheader('Текущ operator summary')
        st.code(preflight['operator_summary'])
        for name, ok in preflight['checks'].items():
            st.write(('✅' if ok else '⛔') + ' ' + name)
        return

    if report['preflight_ready']:
        st.success(report['message'])
    else:
        st.warning(report['message'])

    preflight = report['preflight']
    c1, c2, c3 = st.columns(3)
    c1.metric('Target draw', preflight.get('target_draw_key') or '—')
    c2.metric('Local draw', preflight.get('local_draw_key') or '—')
    c3.metric('Preflight', 'READY' if preflight.get('ready') else 'BLOCKED')
    st.code(preflight['operator_summary'])

    st.subheader('Финални проверки')
    for name, ok in preflight['checks'].items():
        st.write(('✅' if ok else '⛔') + ' ' + name)

    if preflight.get('ready'):
        if st.button('Издай еднократен activation token', use_container_width=True):
            token = issue_one_time_activation_token(preflight)
            st.session_state['v129_activation_token'] = token
            st.success('Издаден е еднократен token с кратка валидност за конкретния target draw.')

        token = st.session_state.get('v129_activation_token', '')
        if token:
            st.code(token)
            typed = st.text_input('Постави еднократния activation token за финално активиране', type='password')
            confirm = st.checkbox('Потвърждавам, че operator summary и target draw са прегледани.')
            if st.button('Активирай еднократно production веригата', type='primary', use_container_width=True,
                         disabled=not confirm):
                with st.spinner('Guarded production activation...'):
                    result = execute_one_time_activation(typed)
                if result.get('status') == 'completed':
                    st.success(result.get('message'))
                    st.session_state.pop('v129_activation_token', None)
                else:
                    st.error(result.get('message'))
                st.json(result)
    else:
        st.caption('Activation token не може да бъде издаден, докато preflight е блокиран.')

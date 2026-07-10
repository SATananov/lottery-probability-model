from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v130_production_activation_audit_recovery_engine import (
    RECOVERY_PHRASE,
    build_console_snapshot,
    build_recovery_preflight,
    execute_recovery,
)


def render_v130_production_activation_audit_recovery_section() -> None:
    st.title('Production activation audit и recovery')
    st.caption('Step 130 — история на activation опитите, checkpoint inspector, recovery/rollback controls и операторско доказателство.')
    st.warning('Recovery променя production source of truth само след избран backup, операторска идентичност и точна потвърждаваща фраза. Първо изпълни dry-run.')

    snapshot = build_console_snapshot()
    c1, c2, c3 = st.columns(3)
    c1.metric('Audit събития', snapshot['history_count'])
    c2.metric('Налични backups', snapshot['backup_count'])
    c3.metric('Primary = mirror', 'Да' if snapshot['checkpoint']['current_mirror_equal'] else 'Не')

    tab_history, tab_checkpoint, tab_recovery = st.tabs(['Activation история', 'Checkpoint inspector', 'Recovery / rollback'])

    with tab_history:
        history = snapshot['history']
        if not history:
            st.info('Все още няма записани activation или recovery събития.')
        else:
            rows = [{k: v for k, v in item.items() if k != 'raw'} for item in history]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            selected_index = st.number_input('Покажи суровото доказателство за ред №', min_value=1, max_value=len(history), value=1)
            st.json(history[int(selected_index) - 1]['raw'])

    with tab_checkpoint:
        inspector = snapshot['checkpoint']
        st.subheader('Last-success checkpoint')
        st.json(inspector['checkpoint'])
        st.subheader('One-time activation token state')
        st.json(inspector['token_state'])
        st.code(f"Checkpoint: {inspector['checkpoint_path']}\nPrimary SHA256: {inspector['current_primary_sha256']}\nMirror SHA256: {inspector['current_mirror_sha256']}")

    with tab_recovery:
        backups = snapshot['backups']
        if not backups:
            st.info('Няма Step 124 ingestion backups. Recovery не може да бъде изпълнен.')
            return
        labels = {f"{b['backup_id']} · latest {b['latest_draw_key'] or '—'} · rows {b['row_count']}": b['backup_id'] for b in backups}
        selected_label = st.selectbox('Избери backup', list(labels))
        backup_id = labels[selected_label]
        preflight = build_recovery_preflight(backup_id)
        st.json(preflight)

        if st.button('Изпълни recovery dry-run', use_container_width=True):
            result = execute_recovery(backup_id, 'dry_run_operator', '', dry_run=True)
            st.session_state['v130_recovery_dry_run'] = result
        dry = st.session_state.get('v130_recovery_dry_run')
        if dry:
            (st.success if dry.get('status') == 'dry_run_ready' else st.error)(dry.get('message'))

        st.divider()
        operator = st.text_input('Оператор — име или локален идентификатор')
        phrase = st.text_input(f'Въведи точно: {RECOVERY_PHRASE}', type='password')
        confirm = st.checkbox('Потвърждавам, че прегледах backup ID, latest draw и checkpoint състоянието.')
        if st.button('Възстанови production данните от избрания backup', type='primary', use_container_width=True, disabled=not confirm):
            result = execute_recovery(backup_id, operator, phrase, dry_run=False)
            if result.get('status') == 'recovered':
                st.success(result.get('message'))
            else:
                st.error(result.get('message'))
            st.json(result)

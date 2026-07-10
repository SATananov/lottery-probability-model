from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v131_production_operations_dashboard_engine import build_operations_snapshot


def _yes_no(value: bool) -> str:
    return 'Да' if value else 'Не'


def _render_bst_guidance(snapshot: dict) -> None:
    bst = snapshot['bst']
    state = bst.get('operational_state') or {}
    label = state.get('label_bg') or 'Неизвестно'
    title = state.get('title_bg') or label
    action = state.get('operator_action_bg') or ''
    severity = state.get('severity') or 'info'
    renderer = {
        'success': st.success,
        'warning': st.warning,
        'error': st.error,
        'info': st.info,
    }.get(severity, st.info)
    renderer(f"{title}. {action}".strip())


def render_v131_production_operations_dashboard_section() -> None:
    st.title('Production Operations Dashboard')
    st.caption('Централен оперативен преглед за БСТ, тиражи, защити, свежест, activation и recovery.')

    c1, c2 = st.columns([1, 2])
    with c1:
        timeout = st.slider('Timeout към БСТ (секунди)', 5, 60, 30)
    with c2:
        st.write('')
        st.write('')
        live = st.button('Обнови dashboard с live БСТ проверка', use_container_width=True)

    snapshot = build_operations_snapshot(live_bst_check=live, timeout_seconds=timeout)
    health = snapshot['health']
    banner = {'healthy': st.success, 'attention': st.warning, 'critical': st.error}[health]
    banner(f"Production health: {health.upper()}")

    bst_state = snapshot['bst'].get('operational_state') or {}
    a, b, c, d = st.columns(4)
    a.metric('Локален тираж', snapshot['bst']['local_draw_key'])
    b.metric('Официален тираж', snapshot['bst']['official_draw_key'])
    c.metric('БСТ състояние', bst_state.get('label_bg') or 'Неизвестно')
    d.metric('Извън синхрон', snapshot['freshness']['out_of_sync_count'])

    _render_bst_guidance(snapshot)

    tab_health, tab_freshness, tab_activation, tab_recovery = st.tabs([
        'Health summary', 'Downstream freshness', 'Последен activation', 'Recovery readiness'
    ])

    with tab_health:
        rows = [
            {'Проверка': 'BST connectivity', 'Статус': _yes_no(snapshot['checks']['bst_connectivity'])},
            {'Проверка': 'Production lock включен', 'Статус': _yes_no(snapshot['checks']['production_locked'])},
            {'Проверка': 'Operator consent валиден', 'Статус': _yes_no(snapshot['checks']['operator_consent_valid'])},
            {'Проверка': 'One-time token активен', 'Статус': _yes_no(snapshot['checks']['token_active'])},
            {'Проверка': 'Last-success checkpoint', 'Статус': _yes_no(snapshot['checks']['checkpoint_exists'])},
            {'Проверка': 'Primary = mirror', 'Статус': _yes_no(snapshot['checks']['primary_mirror_equal'])},
            {'Проверка': 'Downstream напълно свеж', 'Статус': _yes_no(snapshot['checks']['downstream_fresh'])},
            {'Проверка': 'Recovery готовност', 'Статус': _yes_no(snapshot['checks']['recovery_ready'])},
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        bst = snapshot['bst']
        if bst.get('failure_stage'):
            st.warning(
                f"Live BST failure stage: {bst['failure_stage']} · "
                f"{bst.get('error_type') or 'UnknownError'} · {bst.get('message') or ''}"
            )
        st.json({'bst': bst, 'guardrails': snapshot['guardrails']})

    with tab_freshness:
        sources = snapshot['freshness']['sources']
        if sources:
            st.dataframe(pd.DataFrame(sources), hide_index=True, use_container_width=True)
        else:
            st.info('Няма freshness данни.')

    with tab_activation:
        latest = snapshot['activation']['latest_event']
        if latest:
            st.json(latest)
        else:
            st.info('Все още няма activation събития.')

    with tab_recovery:
        r = snapshot['recovery']
        x, y, z = st.columns(3)
        x.metric('Backups', r['backup_count'])
        y.metric('Recovery ready', _yes_no(r['ready']))
        z.metric('Primary = mirror', _yes_no(r['primary_mirror_equal']))
        if r['backups']:
            st.dataframe(pd.DataFrame(r['backups']), hide_index=True, use_container_width=True)
        else:
            st.info('Няма Step 124 ingestion backups. Recovery ще стане готов след първото реално ingestion събитие.')

    st.info('Dashboard-ът е read-only. Не прилага тираж, не отключва production и не стартира тежко ML retraining.')

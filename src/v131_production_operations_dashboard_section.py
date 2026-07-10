from __future__ import annotations

import pandas as pd
import streamlit as st

from src.v131_production_operations_dashboard_engine import build_operations_snapshot
from src.v132_production_incident_evidence_section import render_v132_production_incident_evidence_section
from src.v133_incident_evidence_integrity_section import render_v133_incident_evidence_integrity_section
from src.v134_incident_evidence_registry_section import render_v134_incident_evidence_registry_section
from src.v135_incident_evidence_retention_section import render_v135_incident_evidence_retention_section
from src.v136_incident_evidence_recovery_drill_section import render_v136_incident_evidence_recovery_drill_section
from src.v137_recovery_drill_audit_reconciliation_section import render_v137_recovery_drill_audit_reconciliation_section
from src.v138_recovery_exception_sla_section import render_v138_recovery_exception_sla_section
from src.v139_recovery_exception_management_summary_section import render_v139_recovery_exception_management_summary_section
from src.v140_production_operations_module_closure_section import render_v140_production_operations_module_closure_section


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

    tab_health, tab_freshness, tab_activation, tab_recovery, tab_evidence = st.tabs([
        'Health summary', 'Downstream freshness', 'Последен activation', 'Recovery readiness', 'Incident evidence'
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

    with tab_evidence:
        evidence_export_tab, evidence_verify_tab, evidence_registry_tab, evidence_retention_tab, evidence_recovery_tab, evidence_reconciliation_tab, evidence_follow_up_tab, evidence_management_tab, evidence_closure_tab = st.tabs(['Създаване на bundle', 'Проверка на целостта', 'Registry history', 'Retention & archive', 'Recovery drill', 'Drill reconciliation', 'Exception follow-up', 'Management summary', 'Module closure'])
        with evidence_export_tab:
            render_v132_production_incident_evidence_section(timeout_seconds=timeout)
        with evidence_verify_tab:
            render_v133_incident_evidence_integrity_section()
        with evidence_registry_tab:
            render_v134_incident_evidence_registry_section()
        with evidence_retention_tab:
            render_v135_incident_evidence_retention_section()
        with evidence_recovery_tab:
            render_v136_incident_evidence_recovery_drill_section()
        with evidence_reconciliation_tab:
            render_v137_recovery_drill_audit_reconciliation_section()
        with evidence_follow_up_tab:
            render_v138_recovery_exception_sla_section()
        with evidence_management_tab:
            render_v139_recovery_exception_management_summary_section()
        with evidence_closure_tab:
            render_v140_production_operations_module_closure_section()

    st.info('Dashboard-ът е read-only. Не прилага тираж, не отключва production и не стартира тежко ML retraining.')

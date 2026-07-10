from __future__ import annotations

import streamlit as st

from src.v128_production_auto_apply_guardrails_engine import (
    CONSENT_PHRASE, DEFAULT_CONFIG, grant_operator_consent, guardrail_readiness,
    load_checkpoint, load_config,
    revoke_operator_consent, run_guarded_production_automation, save_config,
)


def render_v128_production_guardrails_section() -> None:
    st.title('Production Auto-Apply готовност и защити')
    st.caption('Step 128 — production lock, изрично операторско съгласие, last-success checkpoint, retry policy и защита срещу повторно прилагане.')

    config = load_config()
    checkpoint = load_checkpoint()
    readiness = guardrail_readiness(config, checkpoint)

    c1, c2, c3 = st.columns(3)
    c1.metric('Production lock', 'LOCKED' if config['production_locked'] else 'UNLOCKED')
    c2.metric('Операторско съгласие', 'VALID' if readiness['checks']['operator_consent_valid'] else 'MISSING/EXPIRED')
    c3.metric('Last success', checkpoint.get('last_success_draw_key') or '—')

    with st.form('v128_guardrail_settings'):
        production_locked = st.checkbox('Production lock', value=config['production_locked'])
        consent_hours = st.slider('Валидност на съгласието (часове)', 1, 72, int(config['consent_valid_hours']))
        retries = st.slider('Максимален брой опити', 1, 5, int(config['max_retry_attempts']))
        backoff = st.slider('Начален retry backoff (секунди)', 0, 60, int(config['retry_backoff_seconds']))
        same_draw = st.checkbox('Блокирай повторно прилагане на тираж от last-success checkpoint', value=config['block_same_draw_reapply'])
        if st.form_submit_button('Запази guardrail настройките', type='primary', use_container_width=True):
            save_config({**DEFAULT_CONFIG, **config, 'production_locked': production_locked,
                         'consent_valid_hours': consent_hours, 'max_retry_attempts': retries,
                         'retry_backoff_seconds': backoff, 'block_same_draw_reapply': same_draw})
            st.success('Guardrail настройките са запазени.')
            st.rerun()

    st.warning('Production lock трябва да остане включен, докато не се потвърди реален нов тираж. Отключването само по себе си не е достатъчно — изисква се и валидно операторско съгласие.')

    phrase = st.text_input('Въведи точната фраза за изрично съгласие', type='password')
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Дай операторско съгласие', use_container_width=True):
            try:
                grant_operator_consent(phrase)
                st.success('Операторското съгласие е записано с ограничена валидност.')
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    with col2:
        if st.button('Отмени съгласието и заключи', use_container_width=True):
            revoke_operator_consent()
            st.success('Съгласието е отменено и production lock е включен.')
            st.rerun()

    with st.expander('Фраза за съгласие и правила'):
        st.code(CONSENT_PHRASE)
        st.write('Фразата не се пази като чист текст; записва се само SHA-256 отпечатък и timestamp.')

    st.subheader('Readiness проверки')
    for name, ok in readiness['checks'].items():
        st.write(('✅' if ok else '⛔') + ' ' + name)

    if checkpoint:
        with st.expander('Last-success checkpoint'):
            st.json(checkpoint)

    if st.button('Изпълни guarded production проверка', type='primary', use_container_width=True,
                 disabled=not readiness['ready']):
        with st.spinner('Guarded production изпълнение...'):
            report = run_guarded_production_automation(trigger='operator_guarded_run', force_check=True)
        if report.get('status') == 'completed':
            st.success(report.get('message'))
        else:
            st.warning(report.get('message'))
        st.json(report)

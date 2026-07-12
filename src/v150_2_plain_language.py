from __future__ import annotations

from typing import Any, Iterable, Mapping

from src.v150_global_ui_polish import translate_value


GATE_LABELS_BG: dict[str, str] = {
    "evidence_chain_complete": "Всички необходими експерименти са включени в оценката",
    "source_statuses_complete": "Всички използвани експерименти са завършени",
    "source_signatures_match": "Резултатите и техните контролни подписи съвпадат",
    "dataset_identity_consistent": "Всички сравнения използват един и същ набор от данни",
    "future_data_leakage_absent": "При оценката не са използвани бъдещи данни",
    "production_integration_absent": "Изследователският модел няма връзка с работната верига",
    "robust_superiority_demonstrated": "Доказано е устойчиво превъзходство спрямо базовите модели",
    "all_neural_promotion_gates_passed": "Изпълнени са всички условия за допускане на невронния модел",
    "all_mean_advantages_positive": "Средният резултат е по-добър при всяко сравнение",
    "all_confidence_intervals_above_zero": "Всички доверителни интервали потвърждават положително предимство",
    "all_sign_tests_significant": "Всички статистически проверки потвърждават значимо предимство",
    "all_seed_positive_rates_sufficient": "Резултатът е положителен при достатъчно начални стойности",
    "all_fold_positive_rates_sufficient": "Резултатът е положителен при достатъчно исторически периоди",
    "neural_seed_spread_within_limit": "Разликите между началните стойности са в допустими граници",
    "minimum_design_size_met": "Използвани са достатъчно изпълнения и исторически периоди",
}

NEXT_REQUIREMENTS_BG: dict[str, str] = {
    "materially_new_hypothesis": "Да се изследва съществено нова хипотеза, а не малка промяна на същия модел.",
    "preregistered_primary_metric_and_gate": "Основният показател и условията за успех да бъдат определени предварително.",
    "untouched_or_future_validation_period": "Да се използва нов исторически или бъдещ период, който не е участвал в настройването.",
    "untouched_or_future_non_overlapping_period": "Да се използва нов и неприпокриващ се исторически или бъдещ период.",
    "baseline_first_comparison": "Новият модел първо да се сравни с простите базови модели.",
    "baseline_model_first_comparison": "Новият модел първо да се сравни с простите базови модели.",
    "score_before_learn_chronology": "Всеки тираж да бъде оценен, преди да бъде добавен към данните за следващото обучение.",
    "no_personal_journal_access": "Личният дневник и реално изиграните фишове да не се използват.",
    "no_production_pipeline_access": "Експериментът да остане отделен от работната верига.",
    "no_real_ticket_generation": "Експериментът да не създава комбинации за реална игра.",
}

EVIDENCE_SCOPE_BG: dict[str, str] = {
    "single_holdout_baseline": "Единична независима проверка на базов модел",
    "single_holdout_neural": "Единична независима проверка на невронния модел",
    "multi_seed_multi_period_neural": "Проверка на невронния модел с няколко начални стойности и периода",
}

EVIDENCE_OUTCOME_BG: dict[str, str] = {
    "negative": "Няма положително предимство",
    "positive_but_not_robust": "Има малко положително предимство, но то не е устойчиво",
    "robust_negative": "Устойчиво по-слаб резултат",
    "robust_positive": "Устойчиво по-добър резултат",
    "inconclusive": "Няма достатъчно доказателства",
}

DECISION_VALUE_BG: dict[str, str] = {
    "blocked": "Не е допуснат",
    "blocked_without_robust_superiority": "Не е допуснат без доказано устойчиво превъзходство",
    "pause_and_archive": "Спрян и архивиран",
    "forbidden": "Забранено",
    "materially_new_preregistered_hypothesis": "Нова предварително определена изследователска хипотеза",
}


def plain_label(key: Any, *, language: str = "bg") -> str:
    raw = str(key)
    if language == "bg":
        return GATE_LABELS_BG.get(raw, NEXT_REQUIREMENTS_BG.get(raw, translate_value(raw, language="bg", show_technical=False)))
    return raw.replace("_", " ").strip().capitalize()


def requirement_text(key: Any, *, language: str = "bg") -> str:
    raw = str(key)
    if language == "bg":
        return NEXT_REQUIREMENTS_BG.get(raw, plain_label(raw, language="bg"))
    return raw.replace("_", " ").strip().capitalize()


def evidence_scope_text(value: Any, *, language: str = "bg") -> str:
    raw = str(value)
    if language == "bg":
        return EVIDENCE_SCOPE_BG.get(raw, translate_value(raw, language="bg", show_technical=False))
    return raw.replace("_", " ").strip().capitalize()


def evidence_outcome_text(value: Any, *, language: str = "bg") -> str:
    raw = str(value)
    if language == "bg":
        return EVIDENCE_OUTCOME_BG.get(raw, translate_value(raw, language="bg", show_technical=False))
    return raw.replace("_", " ").strip().capitalize()


def decision_value_text(value: Any, *, language: str = "bg") -> str:
    raw = str(value)
    if language == "bg":
        return DECISION_VALUE_BG.get(raw, translate_value(raw, language="bg", show_technical=False))
    return raw.replace("_", " ").strip().capitalize()


def decision_reason_text(decision: Mapping[str, Any], *, language: str = "bg") -> str:
    if language != "bg":
        return str(decision.get("reason") or "No decision has been recorded yet.")
    promotion = str(decision.get("production_promotion") or "blocked")
    action = str(decision.get("current_neural_configuration") or "pause_and_archive")
    if promotion == "blocked" and action == "pause_and_archive":
        return (
            "Нито едно от сравненията в етапи 144–146 не показва устойчиво положително превъзходство. "
            "Затова текущата невронна конфигурация е спряна и архивирана, а включването ѝ в работния режим остава блокирано."
        )
    return "Решението е изведено от натрупаните експериментални доказателства и действащите защити."


def _number(value: Any, digits: int = 4) -> str:
    if value in (None, ""):
        return "Няма данни"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def evidence_user_rows(rows: Iterable[Mapping[str, Any]], *, language: str = "bg") -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        if language == "bg":
            output.append({
                "Етап": row.get("step"),
                "Какво е проверено": evidence_scope_text(row.get("evidence_scope"), language="bg"),
                "Изследван модел": translate_value(row.get("candidate"), language="bg", show_technical=False),
                "Сравнителен модел": translate_value(row.get("comparator"), language="bg", show_technical=False),
                "Средна разлика": _number(row.get("mean_advantage")),
                "Извод": evidence_outcome_text(row.get("evidence_outcome"), language="bg"),
                "Устойчиво превъзходство": "Да" if str(row.get("robust_superiority_demonstrated")).lower() == "true" else "Не",
            })
        else:
            output.append({
                "Step": row.get("step"),
                "Evaluation scope": evidence_scope_text(row.get("evidence_scope"), language="en"),
                "Candidate model": translate_value(row.get("candidate"), language="en", show_technical=False),
                "Comparator": translate_value(row.get("comparator"), language="en", show_technical=False),
                "Mean difference": _number(row.get("mean_advantage")),
                "Outcome": evidence_outcome_text(row.get("evidence_outcome"), language="en"),
                "Robust superiority": "Yes" if str(row.get("robust_superiority_demonstrated")).lower() == "true" else "No",
            })
    return output


def robustness_user_rows(baselines: Mapping[str, Any], *, language: str = "bg") -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for key, value in baselines.items():
        if not isinstance(value, Mapping):
            continue
        mean = float(value.get("mean_advantage") or 0.0)
        lower = value.get("bootstrap_ci_lower")
        upper = value.get("bootstrap_ci_upper")
        robust_positive = bool(lower is not None and float(lower) > 0)
        if language == "bg":
            conclusion = (
                "Устойчиво по-добър резултат" if robust_positive
                else "Малко предимство без достатъчно доказателства" if mean > 0
                else "Няма предимство"
            )
            output.append({
                "Сравнителен модел": translate_value(value.get("baseline", key), language="bg", show_technical=False),
                "Изпълнения": int(value.get("units") or 0),
                "Средна разлика": _number(mean),
                "Победи": int(value.get("wins") or 0),
                "Равенства": int(value.get("ties") or 0),
                "Загуби": int(value.get("losses") or 0),
                "Извод": conclusion,
            })
        else:
            output.append({
                "Comparator": translate_value(value.get("baseline", key), language="en", show_technical=False),
                "Runs": int(value.get("units") or 0),
                "Mean difference": _number(mean),
                "Wins": int(value.get("wins") or 0),
                "Ties": int(value.get("ties") or 0),
                "Losses": int(value.get("losses") or 0),
                "Conclusion": "Robust positive" if robust_positive else "Not robust",
            })
    return output


def paired_user_rows(paired: Mapping[str, Any], *, language: str = "bg") -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for value in paired.values():
        if not isinstance(value, Mapping):
            continue
        mean = float(value.get("mean_best_hits_difference") or 0.0)
        if language == "bg":
            output.append({
                "Сравнителен модел": translate_value(value.get("baseline"), language="bg", show_technical=False),
                "Проверени тиражи": int(value.get("draws") or 0),
                "Средна разлика": _number(mean),
                "Победи": int(value.get("wins") or 0),
                "Равенства": int(value.get("ties") or 0),
                "Загуби": int(value.get("losses") or 0),
                "Извод": "Невронният модел е средно по-добър" if mean > 0 else "Невронният модел не показва предимство",
            })
        else:
            output.append({
                "Comparator": translate_value(value.get("baseline"), language="en", show_technical=False),
                "Draws": int(value.get("draws") or 0),
                "Mean difference": _number(mean),
                "Wins": int(value.get("wins") or 0),
                "Ties": int(value.get("ties") or 0),
                "Losses": int(value.get("losses") or 0),
                "Conclusion": "Positive" if mean > 0 else "No advantage",
            })
    return output

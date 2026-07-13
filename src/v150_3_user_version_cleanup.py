from __future__ import annotations

import re
from typing import Any

# Internal model / workflow version identifiers are useful for developers but are
# not meaningful to a normal user.  They are removed or converted to plain
# language in normal mode and remain untouched when technical details are on.

_EXACT_BG: dict[str, str] = {
    "V1 workflow е заключен като готов за следващ реален тираж.":
        "Работният процес е заключен и е готов за следващия реален тираж.",
    "V1 работен процес е заключен като готов за следващ реален тираж.":
        "Работният процес е заключен и е готов за следващия реален тираж.",
    "Финално заключване v1": "Финално заключване",
    "Финално заключване V1": "Финално заключване",
    "V1 lock е активен": "Финалното заключване е активно",
    "V1 lock": "Финално заключване",
    "V1 checkpoint": "заключена контролна точка",
    "V1_LOCKED_WAITING_NEXT_DRAW": "Заключено — очаква следващия реален тираж",
    "Версия 1 е заключена и очаква следващия тираж":
        "Заключено — очаква следващия реален тираж",
    "Пълен refresh v41 → v71": "Пълно обновяване на моделите",
    "Пълен refresh v41 → v51": "Обновяване на оценката на фиша",
    "Прогнозен статистически модул v36": "Прогнозен статистически модул",
    "Версия на анализа: V41": "Текущ анализ по действащите правила",
    "Бързият режим пропуска v67 и v75, защото са тежки лабораторни процеси.":
        "Бързият режим пропуска тежките лабораторни процеси.",
    "Тежките процеси v67 и v75 не блокират стандартния поток след запис на тираж.":
        "Тежките лабораторни процеси не блокират стандартния поток след запис на тираж.",
}

_EXACT_EN: dict[str, str] = {
    "V1 workflow is locked and ready for the next real draw.":
        "The workflow is locked and ready for the next real draw.",
    "V1 lock": "Final lock",
    "V1 checkpoint": "locked checkpoint",
}

_VERSION_TOKEN_RE = re.compile(r"(?i)(?<![A-Za-z0-9_])v\d+(?:[._]\d+)*(?![A-Za-z0-9_])")
_VERSION_SUFFIX_RE = re.compile(r"\s*[—–-]\s*v\d+(?:[._]\d+)*\b", re.IGNORECASE)
_VERSION_PAREN_RE = re.compile(r"\s*\(\s*v\d+(?:[._]\d+)*\s*\)", re.IGNORECASE)
_ACTIVE_PLAN_RE = re.compile(
    r"(?i)^\s*v\d+(?:[._]\d+)*\s+активен(?:\s+\d{8}T\d+(?:Z|[+-]\d{2}:?\d{2})?)?\s*$"
)
_VERSION_RANGE_RE = re.compile(
    r"(?i)\bv\d+(?:[._]\d+)*\s*(?:→|->|до)\s*v\d+(?:[._]\d+)*\b"
)


def contains_internal_version_label(value: Any) -> bool:
    return isinstance(value, str) and bool(_VERSION_TOKEN_RE.search(value))


def _looks_like_path_or_machine_identifier(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if re.search(r"[\\/]", stripped):
        return True
    if re.fullmatch(r"[A-Za-z0-9_.-]+\.(?:py|json|csv|md|txt|zip|log|db|sql)", stripped, re.IGNORECASE):
        return True
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", stripped) and "_" in stripped:
        return True
    return False


def clean_user_version_labels(
    value: Any,
    *,
    language: str = "bg",
    show_technical: bool = False,
) -> Any:
    """Return a user-facing string without internal Vxx identifiers.

    Technical mode intentionally keeps the original text so developers can still
    inspect exact model and workflow versions.
    """
    if not isinstance(value, str) or show_technical:
        return value

    text = value
    stripped = text.strip()
    if not stripped:
        return text
    if "<style" in stripped.lower() or "</style>" in stripped.lower():
        return text
    if _looks_like_path_or_machine_identifier(stripped):
        return text

    exact = _EXACT_EN if language == "en" else _EXACT_BG
    if stripped in exact:
        replacement = exact[stripped]
        prefix = text[: len(text) - len(text.lstrip())]
        suffix = text[len(text.rstrip()):]
        return prefix + replacement + suffix

    if language == "bg":
        if _ACTIVE_PLAN_RE.fullmatch(stripped):
            return "Активният план е наличен"

        # High-value phrases that otherwise become cryptic after only removing Vxx.
        text = re.sub(r"(?i)\bV1\s+(?:workflow|работен процес)\b", "работният процес", text)
        text = re.sub(r"(?i)\bV1\s+lock\b", "финалното заключване", text)
        text = re.sub(r"(?i)\bV1\s+checkpoint\b", "заключената контролна точка", text)
        text = re.sub(
            r"(?i)\b(?:бързият режим|стандартният режим)\s+пропуска\s+v\d+(?:[._]\d+)*\s+и\s+v\d+(?:[._]\d+)*",
            "Бързият режим пропуска тежките лабораторни процеси",
            text,
        )
        text = re.sub(
            r"(?i)\bтежките процеси\s+v\d+(?:[._]\d+)*\s+и\s+v\d+(?:[._]\d+)*",
            "тежките лабораторни процеси",
            text,
        )
        text = _VERSION_RANGE_RE.sub("пълната моделна верига", text)
    else:
        text = re.sub(r"(?i)\bV1\s+workflow\b", "the workflow", text)
        text = re.sub(r"(?i)\bV1\s+lock\b", "the final lock", text)
        text = re.sub(r"(?i)\bV1\s+checkpoint\b", "the locked checkpoint", text)
        text = _VERSION_RANGE_RE.sub("the full model chain", text)

    text = _VERSION_SUFFIX_RE.sub("", text)
    text = _VERSION_PAREN_RE.sub("", text)

    # Remove remaining standalone Vxx labels from prose.  File paths, code and
    # machine identifiers have already been excluded above.
    text = _VERSION_TOKEN_RE.sub("", text)

    # Repair common remnants after removing the identifier.
    cleanup = {
        "  ": " ",
        " :": ":",
        " ,": ",",
        " .": ".",
        "—  ": "— ",
        "-  ": "- ",
        "версия  е": "версията е",
        "Версия  е": "Версията е",
        "модул  ": "модул ",
        "оценката  ": "оценката ",
        "активен  ": "активен ",
    }
    for bad, good in cleanup.items():
        while bad in text:
            text = text.replace(bad, good)

    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([—–-])\s*([—–-])", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.strip()

    # Avoid returning an empty label after removing a bare identifier.
    if not text:
        return "Вътрешна версия" if language == "bg" else "Internal version"
    return text

from __future__ import annotations

import re
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Iterable, Mapping

from src.v150_3_user_version_cleanup import clean_user_version_labels


# Step 150 is intentionally a display-only layer. It must never mutate source
# data, model files, experiment registries or the prospective forward-test ledger.

BG_EXACT: dict[str, str] = {
    # Research navigation and pages
    "Експериментален neural dynamics sandbox": "Лаборатория за невронна динамика",
    "Контролирана neural robustness проверка": "Проверка за устойчивост на невронния модел",
    "Research decision gate": "Решение за изследователските модели",
    "Проспективен forward test": "Проспективна проверка",
    "Регистър на възпроизводимите експерименти": "Регистър на възпроизводимите експерименти",
    "Neural dynamics": "Невронна динамика",
    "Neural": "Невронен модел",
    "Frequency": "Честотен модел",
    "Recency": "Модел на скорошната активност",
    "Uniform random": "Случаен модел",
    "Random mean": "Среден резултат — случаен модел",
    "Random": "Случаен модел",
    "Promotion gate": "Условия за допускане",
    "Promotion": "Допускане",
    "Production": "Работен режим",
    "Neural config": "Невронна конфигурация",
    "Runs": "Изпълнения",
    "Evidence редове": "Сравнения с доказателства",
    "Robust positive": "Устойчиво положителни",
    "Robust negative": "Устойчиво отрицателни",
    "Decision gate": "Условия за решение",
    "Обединена evidence матрица": "Обединена матрица на доказателствата",
    "Разрешена следваща research посока": "Допустима следваща изследователска посока",
    "Активни заключени evaluation packages": "Активни заключени пакети за оценяване",
    "SHA-256 ledger": "Технически дневник с SHA-256 подписи",
    "Ledger events": "Събития в защитения дневник",
    "Integrity": "Цялост",
    "Следващ milestone": "Следваща контролна точка",
    "Натрупани prospective резултати": "Натрупани проспективни резултати",
    "Последен dataset тираж": "Последен тираж в данните",
    "Holdout тиражи": "Тиражи за независима проверка",
    "Frequency средно": "Среден резултат — честотен модел",
    "Random средно": "Среден резултат — случаен модел",
    "Frequency pool": "Размер на честотния набор",
    "Random seed": "Начална стойност за повторяемост",
    "Random baseline опити": "Опити със случаен базов модел",
    "Случайни baseline опити": "Опити със случаен базов модел",
    "Candidate pool": "Размер на набора кандидати",
    "Recency decay": "Коефициент за скорошна активност",
    "Reservoir size": "Размер на невронния резервоар",
    "Leak rate": "Коефициент на пропускане",
    "Spectral radius": "Спектрален радиус",
    "Ridge alpha": "Коефициент за регуляризация",
    "Score power": "Степен на оценката",
    "Paired comparison": "Сравнение по двойки",
    "Holdout по тиражи": "Резултати по тиражи за независима проверка",
    "Сравнение с baselines и 95% confidence intervals": "Сравнение с базовите модели и 95% доверителни интервали",
    "Стабилност по random seed": "Стабилност по начална стойност",
    "Promotion gate": "Условия за допускане",
    "Production lock": "Заключване на работния режим",
    "Last success": "Последно успешно изпълнение",
    "Last-success checkpoint": "Последна успешна контролна точка",
    "Target draw": "Целеви тираж",
    "Local draw": "Локален тираж",
    "Preflight": "Предварителна проверка",
    "Readiness проверки": "Проверки за готовност",
    "Primary = mirror": "Основни и огледални данни съвпадат",
    "Backup": "Резервно копие",
    "Backups": "Резервни копия",
    "Rollback": "Връщане назад",
    "Recovery ready": "Готовност за възстановяване",
    "Activation история": "История на активиранията",
    "Checkpoint inspector": "Преглед на контролната точка",
    "Recovery / rollback": "Възстановяване / връщане назад",
    "Production Operations Dashboard": "Оперативно табло",
    "Health summary": "Обобщено състояние",
    "Downstream freshness": "Актуалност на зависимите слоеве",
    "Последен activation": "Последно активиране",
    "Recovery readiness": "Готовност за възстановяване",
    "Incident evidence": "Доказателства при инцидент",
    "Bundle ID": "Идентификатор на пакета",
    "Health": "Състояние",
    "Secrets redacted": "Тайните са заличени",
    "Verdict": "Резултат",
    "Failed checks": "Непреминали проверки",
    "Open": "Отворено",
    "Overdue": "Просрочено",
    "Critical": "Критично",
    "Default timeout": "Стандартно време за изчакване",
    "Tracked файлове": "Проследявани файлове",
    "Encoding markers": "Проблеми с кодирането",
    "Dataset проверки": "Проверки на данните",
    "Dataset редове": "Редове в данните",
    "Snapshot": "Моментно състояние",
    "Git status е clean. Няма чакащи локални промени.": "Git състоянието е чисто. Няма чакащи локални промени.",
    "Git технически детайли": "Технически подробности за Git",
    "Output files": "Създадени файлове",
    "CSV отчети": "Отчети във формат CSV",
    "Checklist CSV не може да бъде прочетен.": "Контролният CSV файл не може да бъде прочетен.",
    "Последен sync summary": "Последно обобщение на синхронизацията",
    "Последен sync checklist": "Последен контролен списък за синхронизация",
    "Step 120 summary": "Обобщение на обновяването на данните",
    "Step 120 checklist": "Контролен списък за обновяването на данните",
    "Step 121 summary": "Обобщение на R характеристиките",
    "Step 124 summary": "Обобщение на безопасното прилагане",
    "Detection статус": "Статус на проверката",
    "Audit събития": "Събития от проверките",
    "Production Auto-Apply готовност и защити": "Готовност и защити за автоматично прилагане",
    "Контролирано production активиране и dry-run": "Контролирано активиране и пробно изпълнение",
    "Production activation audit и recovery": "Проверка на активирането и възстановяване",
    "Incident evidence export": "Износ на доказателства при инцидент",
    "Evidence integrity inspector": "Проверка на целостта на доказателствата",
    "Evidence registry & verification history": "Регистър и история на проверките на доказателствата",
    "historical_draws": "Исторически тиражи",
    "v40_normalized": "Нормализирани данни",
    "v41_canonical": "Канонични данни",
    "Налични backups": "Налични резервни копия",
    "Bundles": "Пакети",
    "Сценарият доказва: detect → safe ingest → downstream refresh simulation → freshness synced → duplicate protection → rollback → production isolation.": "Сценарият доказва: откриване → безопасно прилагане → симулация на обновяването на зависимите слоеве → потвърдена актуалност → защита от дублиране → връщане назад → изолация от работния режим.",
    "Липсва Step 68 report/model. Пусни: python scripts/v68_build_weighted_portfolio_optimizer.py": "Липсват отчетът и моделът за етап 68. Изпълни: `python scripts/v68_build_weighted_portfolio_optimizer.py`",
    "Липсва Step 69 report/model. Пусни: python scripts/v69_build_portfolio_improvement_suggestions.py": "Липсват отчетът и моделът за етап 69. Изпълни: `python scripts/v69_build_portfolio_improvement_suggestions.py`",
    "Липсва Step 70 report/model. Пусни: python scripts/v70_build_applied_candidate_portfolio.py": "Липсват отчетът и моделът за етап 70. Изпълни: `python scripts/v70_build_applied_candidate_portfolio.py`",
    "Липсва Step 72 audit report. Пусни: python scripts/v72_build_pipeline_refresh_plan.py": "Липсва отчетът за проверка на етап 72. Изпълни: `python scripts/v72_build_pipeline_refresh_plan.py`",
    "Липсва Step 74 report. Пусни: python scripts/v74_build_model_dependency_sync_center.py": "Липсва отчетът за етап 74. Изпълни: `python scripts/v74_build_model_dependency_sync_center.py`",
    "Контролен център за datasets, артефакти, sync планове, Python compile, JSON/CSV parse и кирилица.": "Контролен център за наборите от данни, артефактите, плановете за синхронизация, компилацията на Python, прочитането на JSON/CSV и кирилицата.",
    "Проверявам datasets, артефакти, sync планове и файлово качество...": "Проверявам наборите от данни, артефактите, плановете за синхронизация и качеството на файловете...",
    "Чета reports/r и генерирам feature таблици...": "Чета файловете в `reports/r` и генерирам таблици с характеристики...",
    "Файловият импорт очаква колони date/year/draw_no/draw_position/n1..n6/bonus_number.": "Файловият импорт очаква колоните `date/year/draw_no/draw_position/n1..n6/bonus_number`.",
    "БСТ prize latest": "Последни данни за печалбите от БСТ",
    "Препоръчителен начален режим: автоматична проверка ON, auto-apply OFF. Включи пълната автоматизация след реален успешен нов тираж.": "Препоръчителен начален режим: автоматична проверка ВКЛ., автоматично прилагане ИЗКЛ. Включи пълната автоматизация след реално успешно обработен нов тираж.",
    "Потвърждавам: commit и push само на data/, models/ и reports/": "Потвърждавам: запис и качване в Git само на `data/`, `models/` и `reports/`",
    "Има локални промени. Този бутон commit-ва само data/, models/ и reports/.": "Има локални промени. Този бутон записва в Git само `data/`, `models/` и `reports/`.",
    "Тази опция пуска core scripts v41–v60 плюс претеглена верига 74. Използвай я след добавяне на нов тираж, когато искаш пълно обновяване.": "Тази опция пуска основните скриптове v41–v60 и претеглената верига 74. Използвай я след добавяне на нов тираж, когато искаш пълно обновяване.",
    "Events": "Събития",
    "Protected evidence": "Защитени доказателства",
    # Common statuses / values
    "PASS": "ПРЕМИНАТО",
    "FAIL": "НЕПРЕМИНАТО",
    "BLOCKED": "БЛОКИРАНО",
    "READY": "ГОТОВО",
    "COMPLETED": "ЗАВЪРШЕНО",
    "completed": "Завършен",
    "blocked": "Блокирано",
    "unknown": "Няма данни",
    "UNKNOWN": "НЯМА ДАННИ",
    "true": "Да",
    "false": "Не",
    "True": "Да",
    "False": "Не",
    "yes": "Да",
    "no": "Не",
    "positive_but_not_robust": "Положително, но неустойчиво",
    "robust_negative": "Устойчиво отрицателно",
    "negative": "Отрицателно",
    "positive": "Положително",
    "pause_and_archive": "Пауза и архивиране",
    "CREATED": "СЪЗДАДЕНО",
    "VERIFIED": "ПОТВЪРДЕНО",
    "INVALID": "НЕВАЛИДНО",
    "Created": "Създадени",
    "Verified": "Потвърдени",
    "Invalid": "Невалидни",
    "Active": "Активни",
    "Protected": "Защитени",
    "To archive": "За архив",
    "To clean": "За почистване",
    "Expired archive cleanup candidates": "Кандидати за почистване на изтекъл архив",
    "Event type": "Тип на събитието",
    "GREEN": "ЗЕЛЕНО",
    "AMBER": "ЖЪЛТО",
    "RED": "ЧЕРВЕНО",
    "ON": "ВКЛ.",
    "OFF": "ИЗКЛ.",
    "research_only": "Само за изследване",
    "waiting_future_draw": "Изчаква бъдещ тираж",
    "active": "Активно",
    "settled": "Оценено",
    "excluded": "Изключено",
    # Streamlit / generic
    "Choose an option": "Избери опция",
    "Choose options": "Избери опции",
    "Browse files": "Избери файл",
    "Drag and drop file here": "Пусни файла тук",
    "Limit 200MB per file": "Лимит 200 MB на файл",
    "R feature интеграция": "Интеграция на R характеристики",
    "### R-blended number scores": "### Оценки на числата, смесени с R",
    "### R feature ticket pack": "### Пакет с комбинации от R характеристики",
    "Генерирай R features": "Генерирай R характеристики",
    "Генерирай R ticket pack": "Генерирай пакет с комбинации от R",
    "Още няма генерирани R blended scores.": "Все още няма генерирани оценки, смесени с R.",
    "Още няма генериран R ticket pack.": "Все още няма генериран пакет с комбинации от R.",
    "R feature таблиците са генерирани.": "Таблиците с R характеристики са генерирани.",
    "Контролен checklist": "Контролен списък",
    "Създай clean ZIP checkpoint": "Създай чист ZIP архив",
    "Clean ZIP checkpoint е създаден с актуален metadata report вътре в архива.": "Чистият ZIP архив е създаден с актуален отчет с метаданни.",
    "Актуален release audit след runtime hardening и clean ZIP checkpoint слоя.": "Актуална проверка на изданието след защитата на работната среда и слоя за чист ZIP архив.",
    "Изпълни production dry-run": "Изпълни пробна проверка на работния режим",
    "Текущ operator summary": "Текущо операторско обобщение",
    "Издай еднократен activation token": "Издай еднократен код за активиране",
    "Постави еднократния activation token за финално активиране": "Постави еднократния код за финално активиране",
    "Потвърждавам, че operator summary и target draw са прегледани.": "Потвърждавам, че операторското обобщение и целевият тираж са прегледани.",
    "Активирай еднократно production веригата": "Активирай еднократно работната верига",
    "One-time activation token state": "Състояние на еднократния код за активиране",
    "Изпълни recovery dry-run": "Изпълни пробна проверка за възстановяване",
    "Registry history": "История на регистъра",
    "Retention & archive": "Съхранение и архив",
    "Recovery drill": "Тренировка за възстановяване",
    "Drill reconciliation": "Съпоставка след тренировката",
    "Exception follow-up": "Последваща проверка на изключенията",
    "Management summary": "Управленско обобщение",
    "Module closure": "Завършване на модула",
    "Deploy": "",
}

# Long phrases are applied before shorter technical terms.
BG_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("frequency-recency", "честотен и скорошен"),
    ("auto-apply", "автоматично прилагане"),
    ("append-only", "само с добавяне"),
    ("end-to-end", "цялостна"),
    ("post-draw", "след тиража"),
    ("prior-only", "само от предходни данни"),
    ("chain-of-custody", "проследима верига на съхранение"),
    ("official source of truth и journal mirror", "официалния основен източник и локалното огледално копие на дневника"),
    ("source of truth", "основен източник на данни"),
    ("Decision Center", "център за решения"),
    ("freshness check", "проверка на актуалността"),
    ("ticket packs", "пакети с комбинации"),
    ("model-signal", "моделен сигнал"),
    ("model-weight", "тегло на модел"),
    ("analysis modules", "аналитични модули"),
    ("recovery risks", "рискове при възстановяване"),
    ("management actions", "управленски действия"),
    ("Open exceptions", "Отворени изключения"),
    ("Due soon", "С наближаващ срок"),
    ("Failed drills", "Непреминали тренировки"),
    ("Step range", "Обхват на етапите"),
    ("Closure boundaries", "Граници на приключването"),
    ("MODULE CLOSED", "МОДУЛЪТ Е ЗАВЪРШЕН"),
    ("CLOSURE BLOCKED", "ЗАВЪРШВАНЕТО Е БЛОКИРАНО"),
    ("Management health", "Управленско състояние"),
    ("Output files", "Създадени файлове"),
    ("feature generation", "генериране на характеристики"),
    ("ticket pack generation", "генериране на пакет с комбинации"),
    ("uniform-random", "равномерно случаен"),
    ("Monte Carlo", "Монте Карло"),
    ("downstream", "зависим"),
    ("Timeout", "Време за изчакване"),
    ("timeout", "време за изчакване"),
    ("backup", "резервно копие"),
    ("staging", "подготвителна среда"),
    ("optional", "по избор"),
    ("rerun", "повторно изпълнение"),
    ("journal", "дневник"),
    ("mirror", "огледално копие"),
    ("official", "официален"),
    ("historical", "исторически"),
    ("canonical", "каноничен"),
    ("normalized", "нормализиран"),
    ("generation", "генериране"),
    ("portfolio", "портфейл"),
    ("overlap", "припокриване"),
    ("lifecycle", "жизнен цикъл"),
    ("incident", "инцидент"),
    ("exceptions", "изключения"),
    ("exception", "изключение"),
    ("reconciliation", "съпоставка"),
    ("follow-up", "последващо действие"),
    ("escalation", "ескалация"),
    ("acknowledgement", "потвърждение"),
    ("confirmation phrase", "фраза за потвърждение"),
    ("closure", "приключване"),
    ("retention", "съхранение"),
    ("archive", "архив"),
    ("cleanup", "почистване"),
    ("registry", "регистър"),
    ("preview", "предварителен преглед"),
    ("latest", "последен"),
    ("health", "състояние"),
    ("management", "управление"),
    ("operations", "операции"),
    ("governance", "управление"),
    ("module", "модул"),
    ("Budget Advisor", "Съветник за бюджет"),
    ("last-success", "последно успешно изпълнение"),
    ("Fail-closed", "блокиране при несигурност"),
    ("Anti-backfit", "защита от донастройване назад"),
    ("pre-save", "преди запис"),
    ("repeated pairs", "повтарящи се двойки"),
    ("repeated triples", "повтарящи се тройки"),
    ("pairs/triples", "двойки/тройки"),
    ("checksum", "контролна сума"),
    ("failure stage", "етап на грешката"),
    ("attention queue", "списък за внимание"),
    ("Meta Learner", "мета модел"),
    ("neural Meta Learner", "невронния мета модел"),
    ("model files", "моделни файлове"),
    ("report/model", "отчет/модел"),
    ("score/model", "оценъчни/моделни"),
    ("commit/push", "запис и качване в Git"),
    ("commit and push", "запис и качване в Git"),
    ("git add", "добавяне в Git"),
    ("commit", "запис в Git"),
    ("push", "качване"),
    ("export", "износ"),
    ("top20", "водещите 20"),
    ("top 20", "водещите 20"),
    ("top 10", "водещите 10"),
    ("top", "водещ"),
    ("last success", "последно успешно изпълнение"),
    ("Guarded", "Защитено"),
    ("guarded", "защитено"),
    ("snapshot", "моментно състояние"),
    ("safe", "безопасно"),
    ("candidates", "кандидати"),
    ("candidate", "кандидат"),
    ("restore", "възстановяване"),
    ("drills", "тренировки"),
    ("drill", "тренировка"),
    ("Closed", "Затворени"),
    ("queue", "списък"),
    ("applied", "приложен"),
    ("workflow", "работен процес"),
    ("protocol", "протокол"),
    ("screenshots", "екранни снимки"),
    ("detection", "откриване"),
    ("test sandbox", "изолирана тестова среда"),
    ("policy", "правило"),
    ("controls", "контроли"),
    ("freshness", "актуалност"),
    ("mutation", "промяна"),
    ("identity", "идентичност"),
    ("integrity", "цялост"),
    ("validation", "проверка"),
    ("Reconciled", "Съпоставени"),
    ("reporting", "отчитане"),
    ("attention", "внимание"),
    ("acknowledge", "потвърждава"),
    ("overdue", "просрочени"),
    ("critical", "критични"),
    ("failed", "неуспешни"),
    ("repair", "поправка"),
    ("hit", "попадение"),
    ("repeated", "повтарящи се"),
    ("pairs", "двойки"),
    ("triples", "тройки"),
    ("vs", "спрямо"),
    ("note", "бележка"),
    ("print", "печат"),
    ("core", "основни"),
    ("script", "скрипт"),
    ("input", "вход"),
    ("output", "изход"),
    ("build", "изграждане"),
    ("meta-network", "мета мрежа"),
    ("meta", "мета"),
    ("decision", "решение"),
    ("chain", "верига"),
    ("labels", "етикети"),
    ("replay", "повторно проиграване"),
    ("operational", "оперативен"),
    ("backfit", "донастройване назад"),
    ("map", "карта"),
    ("R-blended", "смесен с R"),
    ("Minimum active verified", "Минимален брой активни потвърдени"),
    ("hit rate", "дял на попаденията"),
    ("core scripts", "основните скриптове"),
    ("git commands", "Git команди"),
    ("PASSED", "ПРЕМИНАТО"),
    ("GREEN", "ЗЕЛЕНО"),
    ("AMBER", "ЖЪЛТО"),
    ("RED", "ЧЕРВЕНО"),
    ("backtest", "историческа проверка"),
    ("Forbidden tracked", "Забранени проследявани"),
    ("prize", "печалби"),
    ("Events", "Събития"),
    ("Protected", "Защитени"),
    ("CREATED", "СЪЗДАДЕНО"),
    ("VERIFIED", "ПОТВЪРДЕНО"),
    ("INVALID", "НЕВАЛИДНО"),
    ("Step", "Етап"),
    ("code", "код"),
    ("model", "модел"),
    ("clean", "чист"),
    ("Python-readable", "четими от Python"),
    ("R-blended number scores", "оценки на числата, смесени с R"),
    ("R blended scores", "оценки, смесени с R"),
    ("number scores", "оценки на числата"),
    ("prize history", "историята на печалбите"),
    ("historical/canonical", "историческия/каноничния"),
    ("retrain-ва", "преобучава"),
    ("retrain", "преобучи"),
    ("Clean ZIP", "чист ZIP архив"),
    ("clean ZIP", "чист ZIP архив"),
    ("metadata report", "отчет с метаданни"),
    ("metadata", "метаданни"),
    ("nested ZIP", "вложени ZIP"),
    ("helper patch", "помощни поправки"),
    ("cache", "кеш"),
    ("activation token", "код за активиране"),
    ("token", "код"),
    ("checkpoint inspector", "преглед на контролната точка"),
    ("backup ID", "идентификатора на резервното копие"),
    ("latest draw", "последния тираж"),
    ("ingestion backups", "резервни копия от прилагането"),
    ("ingestion", "прилагане"),
    ("Registry history", "история на регистъра"),
    ("Recovery drill", "тренировка за възстановяване"),
    ("Management summary", "управленско обобщение"),
    ("The frequency baseline does not exceed the random-trial mean on this historical holdout.",
     "Честотният базов модел не превъзхожда средния резултат на случайния модел върху този исторически период за независима проверка."),
    ("Neural dynamics sandbox versus frequency, recency and uniform-random baselines",
     "Лаборатория за невронна динамика спрямо честотен, скорошен и случаен базов модел"),
    ("Walk-forward frequency baseline versus uniform-random baseline",
     "Последователна историческа проверка на честотния спрямо случайния базов модел"),
    ("multi-seed", "с няколко начални стойности"),
    ("multi-period", "с няколко исторически периода"),
    ("confidence intervals", "доверителни интервали"),
    ("confidence interval", "доверителен интервал"),
    ("paired sign tests", "свързани знакови тестове"),
    ("uniform-random", "случаен"),
    ("uniform random", "случаен модел"),
    ("random-trial mean", "средния резултат на случайния модел"),
    ("frequency-recency blend", "смесен честотен и скорошен модел"),
    ("recent-window frequency", "честотен модел в скорошен прозорец"),
    ("recency-weighted", "претеглен по скорошна активност"),
    ("frequency baseline", "честотен базов модел"),
    ("recency baseline", "базов модел на скорошната активност"),
    ("random baseline", "случаен базов модел"),
    ("baseline experiments", "експерименти с базови модели"),
    ("baselines", "базови модели"),
    ("baseline", "базов модел"),
    ("neural dynamics", "невронна динамика"),
    ("neural reservoir", "невронен резервоар"),
    ("neural configuration", "невронна конфигурация"),
    ("neural config", "невронна конфигурация"),
    ("neural", "невронен"),
    ("research-only", "само за изследване"),
    ("research only", "само за изследване"),
    ("research decision", "изследователско решение"),
    ("research", "изследователски"),
    ("production pipeline", "работната верига"),
    ("production promotion", "допускане до работния режим"),
    ("production", "работен режим"),
    ("walk-forward", "последователна историческа проверка"),
    ("forward test", "проспективна проверка"),
    ("forward-test", "проспективна проверка"),
    ("prospective", "проспективен"),
    ("holdout", "независима проверка"),
    ("dataset hash", "подпис на данните"),
    ("dataset", "данните"),
    ("configuration hash", "подпис на конфигурацията"),
    ("configuration", "конфигурация"),
    ("code hash", "подпис на кода"),
    ("result signature", "подпис на резултата"),
    ("split policy", "правило за разделяне"),
    ("artifacts", "артефакти"),
    ("artifact", "артефакт"),
    ("evaluation packages", "пакети за оценяване"),
    ("evaluation package", "пакет за оценяване"),
    ("evaluation", "оценяване"),
    ("append-only ledger", "дневник само с добавяне"),
    ("ledger", "защитен дневник"),
    ("pre-draw lock", "заключване преди тиража"),
    ("lock operation", "операцията по заключване"),
    ("lock", "заключване"),
    ("settlement", "оценяване"),
    ("milestone", "контролна точка"),
    ("scoring", "оценяване"),
    ("scores", "оценки"),
    ("score", "оценка"),
    ("random seeds", "начални стойности"),
    ("random seed", "начална стойност"),
    ("seed", "начална стойност"),
    ("frequency", "честотен модел"),
    ("recency", "скорошна активност"),
    ("random", "случаен"),
    ("robustness", "устойчивост"),
    ("robust superiority", "устойчиво превъзходство"),
    ("robust", "устойчив"),
    ("evidence", "доказателства"),
    ("decision gate", "условия за решение"),
    ("promotion gate", "условия за допускане"),
    ("promotion", "допускане"),
    ("pipeline", "верига"),
    ("refresh", "обновяване"),
    ("sync", "синхронизация"),
    ("checkpoint", "контролна точка"),
    ("runtime", "работна среда"),
    ("release", "издание"),
    ("audit", "проверка"),
    ("summary", "обобщение"),
    ("checklist", "контролен списък"),
    ("status", "статус"),
    ("report", "отчет"),
    ("history", "история"),
    ("read-only", "само за преглед"),
    ("dry-run", "пробно изпълнение"),
    ("preflight", "предварителна проверка"),
    ("operator", "оператор"),
    ("activation", "активиране"),
    ("recovery", "възстановяване"),
    ("rollback", "връщане назад"),
    ("retry", "повторен опит"),
    ("backoff", "изчакване между опитите"),
    ("guardrail", "защита"),
    ("guardrails", "защити"),
    ("live", "в реално време"),
    ("dashboard", "табло"),
    ("bundle", "пакет"),
    ("manifest", "опис на файловете"),
    ("source of truth", "основен източник на данни"),
    ("target draw", "целеви тираж"),
    ("heavy ML retraining", "тежко преобучение на моделите"),
    ("ML retraining", "преобучение на моделите"),
    ("retraining", "преобучение"),
    ("features", "характеристики"),
    ("feature", "характеристика"),
    ("gaps", "интервали"),
    ("gap", "интервал"),
    ("features", "характеристики"),
    ("ticket pack", "пакет с комбинации"),
    ("ticket", "комбинация"),
    ("app", "приложението"),
)

# Exact Bulgarian-to-English translations for navigation and the Step 144–150 pages.
EN_EXACT: dict[str, str] = {
    "Език": "Language",
    "Главен раздел": "Main section",
    "Страница": "Page",
    "Български": "Bulgarian",
    "Технически подробности": "Technical details",
    "Показвай вътрешни идентификатори, подписи и UTC полета": "Show internal identifiers, signatures and UTC fields",
    "Регистър на възпроизводимите експерименти": "Reproducible Experiment Registry",
    "Лаборатория за невронна динамика": "Neural Dynamics Laboratory",
    "Проверка за устойчивост на невронния модел": "Neural Model Robustness Check",
    "Решение за изследователските модели": "Research Model Decision",
    "Проспективна проверка": "Prospective Evaluation",
    "Контрол на езика и интерфейса": "Language and Interface Control",
    "🔬 Изследователски проверки": "🔬 Research Evaluation",
    "🛡️ Система и контрол": "🛡️ System and Control",
    "🗂️ Други": "🗂️ Other",
    "Последен тираж в данните": "Latest draw in data",
    "Тиражи за независима проверка": "Independent evaluation draws",
    "Среден резултат — честотен модел": "Average result — frequency model",
    "Среден резултат — случаен модел": "Average result — random model",
    "Регистрирани експерименти": "Registered experiments",
    "Последен резултат": "Latest result",
    "Технически подробности и криптографски подписи": "Technical details and cryptographic signatures",
    "Методологични защити": "Methodological safeguards",
    "Архитектура и технически параметри": "Architecture and technical parameters",
    "Сравнение по двойки": "Paired comparison",
    "Резултати по тиражи за независима проверка": "Per-draw independent evaluation results",
    "Сравнение с базовите модели и 95% доверителни интервали": "Baseline comparison and 95% confidence intervals",
    "Стабилност по начална стойност": "Stability by random seed",
    "Стабилност по исторически период": "Stability by historical period",
    "Условия за допускане": "Promotion criteria",
    "Условия за решение": "Decision criteria",
    "Обединена матрица на доказателствата": "Combined evidence matrix",
    "Допустима следваща изследователска посока": "Permitted next research direction",
    "Протоколни защити": "Protocol safeguards",
    "Активни заключени пакети за оценяване": "Active locked evaluation packages",
    "Технически дневник с SHA-256 подписи": "Technical SHA-256 ledger",
    "Натрупани проспективни резултати": "Accumulated prospective results",
    "Оценени бъдещи тиражи": "Evaluated future draws",
    "Защити": "Safeguards",
    "Завършен": "Completed",
    "Блокирано": "Blocked",
    "ПРЕМИНАТО": "PASS",
    "НЕПРЕМИНАТО": "FAIL",
    "БЛОКИРАНО": "BLOCKED",
}

EN_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("Лотарийна статистическа лаборатория", "Lottery Statistical Laboratory"),
    ("изследователски", "research"),
    ("изследване", "research"),
    ("невронна динамика", "neural dynamics"),
    ("невронен модел", "neural model"),
    ("честотен модел", "frequency model"),
    ("модел на скорошната активност", "recency model"),
    ("случаен модел", "random model"),
    ("базов модел", "baseline"),
    ("независима проверка", "independent evaluation"),
    ("доверителен интервал", "confidence interval"),
    ("доверителни интервали", "confidence intervals"),
    ("устойчивост", "robustness"),
    ("доказателства", "evidence"),
    ("проспективна проверка", "prospective evaluation"),
    ("работния режим", "production mode"),
    ("работен режим", "production mode"),
    ("работната верига", "production pipeline"),
    ("верига", "pipeline"),
    ("данните", "dataset"),
    ("обновяване", "refresh"),
    ("синхронизация", "synchronization"),
    ("контролна точка", "checkpoint"),
    ("проверка", "check"),
    ("отчет", "report"),
    ("обобщение", "summary"),
    ("контролен списък", "checklist"),
    ("заключване", "lock"),
    ("оценяване", "settlement"),
    ("пакети за оценяване", "evaluation packages"),
    ("защитен дневник", "ledger"),
    ("артефакти", "artifacts"),
    ("артефакт", "artifact"),
    ("начална стойност", "random seed"),
    ("конфигурация", "configuration"),
    ("резултат", "result"),
    ("статус", "status"),
    ("тираж", "draw"),
    ("тиражи", "draws"),
    ("числа", "numbers"),
    ("комбинации", "combinations"),
)

FIELD_LABELS_BG: dict[str, str] = {
    "experiment_id": "Идентификатор",
    "decision_id": "Идентификатор на решението",
    "lock_id": "Идентификатор на заключването",
    "protocol_id": "Идентификатор на протокола",
    "event_id": "Идентификатор на събитието",
    "event_index": "Пореден номер",
    "event_type": "Тип събитие",
    "title": "Наименование",
    "status": "Статус",
    "created_at_utc": "Създадено на",
    "last_evaluated_at_utc": "Последно оценено на",
    "locked_at_utc": "Заключено на",
    "settled_at_utc": "Оценено на",
    "generated_at_utc": "Генерирано на",
    "dataset_sha256": "Подпис на данните",
    "configuration_sha256": "Подпис на конфигурацията",
    "result_signature_sha256": "Подпис на резултата",
    "code_sha256": "Подпис на кода",
    "event_hash": "Подпис на събитието",
    "previous_event_sha256": "Подпис на предишното събитие",
    "source_summary": "Източник на обобщението",
    "source_experiments": "Изходни експерименти",
    "evidence_rows": "Сравнения с доказателства",
    "production_promotion": "Допускане до работния режим",
    "current_neural_configuration": "Текуща невронна конфигурация",
    "candidate": "Изследван метод",
    "comparator": "Сравнителен метод",
    "mean_advantage": "Средна разлика",
    "ci_lower": "Долна граница на 95% интервал",
    "ci_upper": "Горна граница на 95% интервал",
    "p_value": "p-стойност",
    "positive_seed_rate": "Положителен дял по начални стойности",
    "positive_fold_rate": "Положителен дял по периоди",
    "source_promotion_gate_passed": "Изходното условие е преминато",
    "evidence_outcome": "Извод от доказателствата",
    "robust_superiority_demonstrated": "Показано устойчиво превъзходство",
    "production_eligible": "Допустимо за работния режим",
    "method": "Метод",
    "strategy": "Стратегия",
    "baseline": "Базов модел",
    "seed": "Начална стойност",
    "fold": "Исторически период",
    "fold_id": "Исторически период",
    "run_id": "Изпълнение",
    "run_index": "Изпълнение №",
    "draw_key": "Тираж",
    "expected_draw_key": "Очакван тираж",
    "source_latest_draw_key": "Последен изходен тираж",
    "eligible_draws": "Оценени тиражи",
    "average_best_hits": "Среден най-добър резултат",
    "average_best_hits_mean": "Среден най-добър резултат",
    "best_hits": "Най-добър резултат",
    "package_index": "Пакет №",
    "line_index": "Комбинация №",
    "numbers": "Числа",
    "target_numbers": "Изтеглени числа",
    "matched_numbers": "Познати числа",
    "hits": "Познати числа",
    "eligible": "Допустим",
    "exclusion_reason": "Причина за изключване",
    "integrity_ok": "Цялостта е потвърдена",
    "promotion_gate_passed": "Условията за допускане са преминати",
    "interpretation": "Обяснение",
    "reason": "Причина",
    "requirement": "Изискване",
    "passed": "Преминато",
}

FIELD_LABELS_EN: dict[str, str] = {
    key: key.replace("_", " ").title() for key in FIELD_LABELS_BG
}

FIELD_WORDS_BG: dict[str, str] = {
    "id": "идентификатор", "at": "на", "utc": "UTC", "sha256": "SHA-256",
    "created": "създадено", "updated": "обновено", "generated": "генерирано",
    "latest": "последен", "draw": "тираж", "draws": "тиражи", "number": "число",
    "numbers": "числа", "count": "брой", "mean": "средно", "average": "средно",
    "best": "най-добър", "hits": "познати числа", "score": "оценка", "status": "статус",
    "result": "резултат", "source": "източник", "target": "целеви", "method": "метод",
    "model": "модел", "frequency": "честотен", "recency": "скорошна активност",
    "random": "случаен", "neural": "невронен", "baseline": "базов модел",
    "comparison": "сравнение", "advantage": "разлика", "lower": "долна граница",
    "upper": "горна граница", "rate": "дял", "fold": "исторически период",
    "seed": "начална стойност", "run": "изпълнение", "eligible": "допустим",
    "event": "събитие", "type": "тип", "previous": "предишен", "hash": "подпис",
    "path": "път", "file": "файл", "title": "наименование", "description": "описание",
    "policy": "правило", "decision": "решение", "production": "работен режим",
    "promotion": "допускане", "evidence": "доказателства", "robust": "устойчив",
    "configuration": "конфигурация", "dataset": "данни", "code": "код",
    "signature": "подпис", "artifact": "артефакт", "package": "пакет",
    "line": "комбинация", "index": "номер", "value": "стойност", "message": "съобщение",
}

VALUE_LABELS_BG: dict[str, str] = {
    **{key.lower(): value for key, value in BG_EXACT.items() if isinstance(key, str)},
    "frequency_walk_forward": "Честотен модел",
    "recency_weighted_walk_forward": "Модел на скорошната активност",
    "recent_window_frequency": "Честотен модел в скорошен прозорец",
    "frequency_recency_blend": "Смесен честотен и скорошен модел",
    "neural_dynamics_reservoir": "Невронна динамика",
    "uniform_random_mean": "Среден резултат — случаен модел",
    "protocol_initialized": "Протоколът е инициализиран",
    "forecast_locked": "Прогнозата е заключена",
    "forecast_settled": "Прогнозата е оценена",
    "draw_excluded": "Тиражът е изключен",
    "single_holdout_baseline": "Единична независима проверка на базов модел",
    "single_holdout_neural": "Единична независима проверка на невронен модел",
    "multi_seed_multi_period_neural": "Невронна проверка с няколко начални стойности и периода",
}


# Step 150.1 extends the display dictionary to dynamic report values and the
# complete table-header inventory.  The source files remain unchanged; only
# values passed to Streamlit are localized.
BG_EXACT.update({
    "The neural-dynamics sandbox did not pass the promotion gate on this historical holdout. It remains research-only and is not connected to ticket generation.":
        "Лабораторията за невронна динамика не изпълни условията за допускане в този исторически период за независима проверка. Моделът остава само за изследване и не участва в генерирането на комбинации.",
    "The neural robustness experiment did not pass every multi-seed, multi-period confidence and stability gate. The model remains research-only and isolated from ticket generation.":
        "Проверката за устойчивост на невронния модел не изпълни всички изисквания за доверителност и стабилност при различните начални стойности и исторически периоди. Моделът остава само за изследване и е отделен от генерирането на комбинации.",
    "No experiment has been run.": "Все още няма изпълнен експеримент.",
    "No data": "Няма данни",
    "None": "Няма данни",
    "nan": "Няма данни",
    "Active": "Активен",
    "ACTIVE": "АКТИВЕН",
    "Passed": "Преминато",
    "Failed": "Непреминато",
    "Pending": "Очаква обработка",
    "Settled": "Оценено",
    "Unsettled": "Неоценено",
})

BG_EXACT.update({
    'Държи се близо до top weighted числата, но избягва прекалено концентриран фиш.': 'Следва водещите претеглени числа, но избягва прекалено концентриран фиш.',
    'покрива непокрит top20 сигнал 16; заменя по-слаб rank 19 с по-силен rank 15; намалява повторените двойки; увеличава уникалното покритие; увеличава top20 покритието': 'покрива непокрит сигнал 16 от водещите 20; заменя по-слабото число на позиция 19 с по-силното на позиция 15; намалява повторените двойки; увеличава уникалното покритие и покритието на водещите 20 числа',
    'покрива непокрит top20 сигнал 43; заменя по-слаб rank 19 с по-силен rank 18; намалява повторените двойки; увеличава уникалното покритие; увеличава top20 покритието': 'покрива непокрит сигнал 43 от водещите 20; заменя по-слабото число на позиция 19 с по-силното на позиция 18; намалява повторените двойки; увеличава уникалното покритие и покритието на водещите 20 числа',
    'Next rerun opens the add-draw page through normal navigation state.': 'При следващото обновяване страницата за добавяне на тираж се отваря чрез нормалното състояние на навигацията.',
    'Other app layers can still read the current selected page.': 'Останалите слоеве на приложението могат да прочетат текущо избраната страница.',
    'Shortcut does not render the page directly after sidebar widgets are already created.': 'Бързият достъп не визуализира страницата директно, след като елементите в страничното меню вече са създадени.',
    'The selected main section persists across Streamlit reruns.': 'Избраният главен раздел се запазва при повторно изпълнение на Streamlit.',
    'The selected page persists while the user types in draw input fields.': 'Избраната страница се запазва, докато потребителят въвежда данни за тиража.',
    'navigation group selectbox has stable key': 'Полето за избор на навигационна група има постоянен ключ.',
    'sidebar shortcut stores pending add-draw page': 'Бързият достъп в страничното меню запазва предстоящото отваряне на страницата за добавяне на тираж.',
    'sidebar shortcut stores pending navigation group': 'Бързият достъп в страничното меню запазва предстоящата навигационна група.',
    'Финален контролен слой за проверка на model artifacts, dependency map и sync status.': 'Финален контролен слой за проверка на моделните артефакти, картата на зависимостите и състоянието на синхронизацията.',
    'Финален пакет за предаване readiness и clean ZIP контролен слой след Step 81.': 'Финален контролен слой за готовността на пакета за предаване и чистия ZIP архив след етап 81.',
    '48 реда, 1 snapshot, 6 групи x 8 комбинации.': '48 реда, 1 моментно състояние и 6 групи по 8 комбинации.',
    'A new official draw updates the model dataset layer, but heavy ML retraining remains a deliberate manual step.': 'Нов официален тираж обновява слоя с моделни данни, но тежкото преобучение на моделите остава съзнателна ръчна стъпка.',
    'Adaptive weighting is a statistical signal-management layer. It does not guarantee a win or future lottery results.': 'Адаптивното претегляне е статистически слой за управление на сигналите. То не гарантира печалба или бъдещи лотарийни резултати.',
    'At each holdout point, the neural readout, frequency scores and recency scores use only strictly earlier draws.': 'Във всяка точка на независимата проверка невронният модел, честотните оценки и оценките за скорошна активност използват само по-ранни тиражи.',
    'Dataset row count се увеличава само след успешен запис или replace на съществуващо теглене.': 'Броят на редовете в данните се увеличава само след успешен запис или замяна на съществуващо теглене.',
    'Each target draw is scored before it is added to the expanding training state.': 'Всеки целеви тираж се оценява, преди да бъде добавен към разширяващото се обучаващо състояние.',
    'Git tracked file list is available for clean ZIP creation.': 'Списъкът с проследяваните от Git файлове е наличен за създаване на чист ZIP архив.',
    'GitHub sync и dependency контролът потвърждават, че app, reports и models са в синхрон.': 'Синхронизацията с GitHub и контролът на зависимостите потвърждават, че приложението, отчетите и моделите са синхронизирани.',
    'Historical model reliability dashboard only. This is not a prediction guarantee.': 'Таблото показва само историческата надеждност на моделите. То не е гаранция за бъдеща прогноза.',
    'Historical post-draw model performance tracking only. This is not a prediction guarantee.': 'Проследяването показва само историческото представяне на моделите след тиража. То не е гаранция за бъдеща прогноза.',
    'Sidebar shortcut вече описва реалното действие по-точно.': 'Бързият достъп в страничното меню вече описва реалното действие по-точно.',
    'Step 102 runtime защита е активна в Add Draw refresh flow.': 'Защитата на работната среда от етап 102 е активна в процеса за обновяване след добавяне на тираж.',
    'Step 107 се обновява след бъдещ Add Draw fast refresh.': 'Етап 107 се обновява след бъдещо бързо обновяване при добавяне на тираж.',
    'Streamlit label: Финален пакет за предаване': 'Наименование в Streamlit: Финален пакет за предаване',
    'These are statistical improvement suggestions. They do not guarantee a win or future lottery results.': 'Това са статистически предложения за подобрение. Те не гарантират печалба или бъдещи лотарийни резултати.',
    'This component statistically optimizes a portfolio of ticket combinations. It does not guarantee a win or future lottery results.': 'Този компонент оптимизира статистически портфейл от комбинации. Той не гарантира печалба или бъдещи лотарийни резултати.',
    'This is a statistical analysis artifact, not a winning guarantee. Lottery draws are random.': 'Това е артефакт от статистически анализ, а не гаранция за печалба. Лотарийните тиражи са случайни.',
    'This is a weighted statistical ensemble layer. It does not guarantee a win or future lottery results.': 'Това е претеглен статистически ансамблов слой. Той не гарантира печалба или бъдещи лотарийни резултати.',
    'This is a weighted statistical ticket builder. It does not guarantee a win or future lottery results.': 'Това е претеглен статистически модул за изграждане на фишове. Той не гарантира печалба или бъдещи лотарийни резултати.',
    'This is an applied statistical reference portfolio. It does not guarantee a win or future lottery results.': 'Това е приложен статистически референтен портфейл. Той не гарантира печалба или бъдещи лотарийни резултати.',
    'Tracked files do not include .git, cache, helper patch files, nested ZIPs, or temp artifacts.': 'Проследяваните файлове не включват `.git`, кешове, помощни поправки, вложени ZIP архиви или временни артефакти.',
    'ZIP creation uses tracked project files only, so .git and cache folders are excluded by design.': 'ZIP архивът се създава само от проследяваните проектни файлове, затова `.git` и кеш папките са изключени по замисъл.',
    'candidate portfolio accepted as improved статистическа референция': 'кандидат-портфейлът е приет като подобрена статистическа референция',
    'post-draw analyzer; used for reliability context, not direct score source': 'анализатор след тиража; използва се за контекст на надеждността, а не като директен източник на оценки',
    'v67 и v75 остават налични, но не са default fast refresh блокер.': 'v67 и v75 остават налични, но не блокират стандартното бързо обновяване.',
    'Валидни 6 различни числа между 1 и 49; bonus не се смесва с основните числа.': 'Валидни са 6 различни числа между 1 и 49; допълнителното число не се смесва с основните числа.',
    'Всички важни build scripts трябва да минават без грешка.': 'Всички важни скриптове за изграждане трябва да завършват без грешка.',
    'Запиши тиража и пусни refresh chain-а след save.': 'Запиши тиража и стартирай веригата за обновяване след записа.',
    'Най-добър резултат: 90 epochs. 500 не е активен.': 'Най-добър резултат: 90 епохи. Вариантът с 500 епохи не е активен.',
    'Няма основни остатъчни developer маркери в проверените user-facing файлове.': 'Няма основни остатъчни технически маркери във файловете, видими за потребителя.',
    'Няма счупена кирилица в проверените user-facing файлове.': 'Няма повредена кирилица във файловете, видими за потребителя.',
    'Сравнява 90, 150, 300 и 500 epochs. Не сменя активния модел.': 'Сравнява 90, 150, 300 и 500 епохи. Не сменя активния модел.',
    'Създава се clean ZIP от committed Git state и се проверява строго.': 'Създава се чист ZIP архив от записаното в Git състояние и се проверява строго.',
    'Add Draw reads active_plan_label_bg instead of hard-coded budget-plan text.': 'Страницата за добавяне на тираж използва динамичното българско наименование на активния план вместо вграден текст.',
    'All simulated operational layers are synchronized.': 'Всички симулирани оперативни слоеве са синхронизирани.',
    'At each holdout point, only strictly earlier draws are available to the frequency baseline.': 'Във всяка точка на независимата проверка честотният базов модел използва само по-ранни тиражи.',
    'Average spread between max and min number.': 'Среден диапазон между най-голямото и най-малкото число.',
    'Canonical данни has valid main draw events and no duplicate keys. Bonus numbers are unavailable and must not be invented.': 'Каноничните данни съдържат валидни основни тегления без дублирани ключове. Допълнителните числа не са налични и не трябва да се измислят.',
    'Chi-square test against uniform number frequency.': 'Хи-квадрат тест спрямо равномерна честота на числата.',
    'Controlled multi-seed, multi-period neural robustness validation': 'Контролирана проверка на устойчивостта на невронния модел с няколко начални стойности и исторически периода',
    'Each saved real ticket should have 4 combinations.': 'Всеки запазен реален фиш трябва да съдържа 4 комбинации.',
    'Experimental Evidence Synthesis & Research Decision Gate': 'Обобщаване на експерименталните доказателства и решение за изследователските модели',
    'Fallback режимът разчита печалбите по категории.': 'Резервният режим разчита печалбите по категории.',
    'Forced failure restored both sandbox source files.': 'Принудителната грешка възстанови и двата изходни файла в изолираната тестова среда.',
    'Four combinations are generated for a full ticket with 4 x 6 numbers. Repetition is limited and combinations are diversified. They are statistical suggestions, not predictions with a guarantee.': 'За пълен фиш се генерират 4 комбинации по 6 числа. Повторенията са ограничени, а комбинациите са разнообразени. Това са статистически предложения, а не гарантирани прогнози.',
    'Global Bulgarian UI, Table Localization & Technical Detail Separation': 'Глобален български интерфейс, локализация на таблиците и отделяне на техническите подробности',
    'Hotfix слой: синхронизира визуалния Add Draw статус с реалния готов фиш пакет. Не променя числата и не обещава печалба.': 'Поправката синхронизира видимото състояние при добавяне на тираж с действително готовия пакет с фишове. Не променя числата и не обещава печалба.',
    'Lottery draws are random. Backtest metrics are evaluation diagnostics, not a guarantee of future outcomes.': 'Лотарийните тиражи са случайни. Показателите от историческата проверка са диагностични оценки, а не гаранция за бъдещи резултати.',
    'Lottery draws are random. Scores are historical rankings, not guaranteed predictions.': 'Лотарийните тиражи са случайни. Оценките са исторически класирания, а не гарантирани прогнози.',
    'Lottery draws are random. Scores are recency rankings, not guaranteed predictions.': 'Лотарийните тиражи са случайни. Оценките са класирания по скорошна активност, а не гарантирани прогнози.',
    'Lottery draws are random. These are ranking-based model outputs, not guaranteed winning numbers.': 'Лотарийните тиражи са случайни. Това са моделни резултати за класиране, а не гарантирани печеливши числа.',
    'Lottery draws are random. This model provides ranking scores, not guaranteed predictions.': 'Лотарийните тиражи са случайни. Моделът предоставя оценки за класиране, а не гарантирани прогнози.',
    'Main UI uses Bulgarian labels and hides raw ids from card titles.': 'Основният интерфейс използва български наименования и скрива вътрешните идентификатори от заглавията на картите.',
    'No comparison in the Step 144–146 evidence chain demonstrates robust positive superiority. The current neural configuration is therefore paused and archived; production promotion remains blocked.': 'Нито едно сравнение във веригата от доказателства за етапи 144–146 не показва устойчиво положително превъзходство. Затова текущата невронна конфигурация е спряна и архивирана, а допускането до работния режим остава блокирано.',
    'No strong evidence against fair-looking number frequencies.': 'Не са открити убедителни доказателства срещу привидно равномерното разпределение на честотите на числата.',
    'Opening the Step 103 Streamlit page builds a live summary without dirtying tracked report files.': 'Отварянето на страницата за етап 103 в Streamlit създава актуално обобщение, без да променя проследяваните отчетни файлове.',
    'Played package can be copied as plain text.': 'Изиграният пакет може да бъде копиран като обикновен текст.',
    'Ranks numbers that are historically below expected frequency, have larger recency gaps, and are cold in the recent window.': 'Класира числа, които исторически са под очакваната честота, имат по-големи интервали от последната поява и са неактивни в скорошния прозорец.',
    'Real project draw files were not changed.': 'Реалните файлове с тиражи в проекта не са променени.',
    'Repository Hygiene, Privacy & Authorship Transparency': 'Хигиена на хранилището, поверителност и прозрачност на авторството',
    'Simulated newer official draw 2026-54 detected.': 'Открит е симулиран по-нов официален тираж 2026-54.',
    'Statistical analysis only. Lottery draws remain random and there is no winning guarantee.': 'Само статистически анализ. Лотарийните тиражи остават случайни и няма гаранция за печалба.',
    'Statistical audit only. Lottery outcomes are random and no winning result is guaranteed.': 'Само статистическа проверка. Лотарийните резултати са случайни и не се гарантира печеливш резултат.',
    'Step 106 е post-draw синхронен слой. Той не променя прогнозната математика, а обновява отчетите след реално записан тираж, за да няма остарели статуси като REVIEW или 10058.': 'Етап 106 е слой за синхронизация след тиража. Той не променя прогнозната математика, а обновява отчетите след реално записан тираж, за да няма остарели състояния като „За преглед“ или стар брой редове.',
    'Step 120 refreshes model datasets after БСТ sync. Heavy ML retraining remains manual.': 'Етап 120 обновява моделните данни след синхронизация с БСТ. Тежкото преобучение на моделите остава ръчно.',
    'Step 147 е research governance слой. Той обобщава исторически експерименти, не прогнозира бъдещи тиражи, не генерира реални фишове и не включва experimental модел в production pipeline.': 'Етап 147 е слой за управление на изследванията. Той обобщава исторически експерименти, не прогнозира бъдещи тиражи, не генерира реални фишове и не включва експериментален модел в работната верига.',
    'The report inside the ZIP can show CLEAN_ZIP_CREATED for the exact current commit.': 'Отчетът в ZIP архива може да покаже „Чистият ZIP е създаден“ за точния текущ запис в Git.',
    'The terminal create script reports whether metadata was written inside the ZIP and the working tree stayed clean.': 'Скриптът за създаване в терминала отчита дали метаданните са записани в ZIP архива и дали работното дърво е останало чисто.',
    'This is a statistical training audit, not a prediction guarantee.': 'Това е статистическа проверка на обучението, а не гаранция за прогноза.',
    'This is a statistical training baseline. It identifies numbers near the historical middle, but it does not guarantee future lottery results.': 'Това е статистически базов модел за обучение. Той определя числа близо до историческата среда, но не гарантира бъдещи лотарийни резултати.',
    'This is a training baseline, not a guarantee. Lottery draws should still be treated as random unless historical backtesting demonstrates a stable signal.': 'Това е базов модел за обучение, а не гаранция. Лотарийните тиражи трябва да се приемат за случайни, освен ако историческата проверка не покаже устойчив сигнал.',
    'This is a transparent statistical training model. It ranks numbers using historical frequency, recent frequency, and recency gaps. It does not prove or guarantee future outcomes.': 'Това е прозрачен статистически модел за обучение. Той класира числата според историческата честота, скорошната честота и интервалите от последната поява. Не доказва и не гарантира бъдещи резултати.',
    'This model does not change the real lottery jackpot probability. It gives a relative statistical confidence score among generated candidates.': 'Този модел не променя реалната вероятност за джакпот. Той дава относителна статистическа оценка на увереността между генерираните кандидати.',
    'Открит е marker за тираж 47, но липсва година за надеждно сравнение.': 'Открит е маркер за тираж 47, но липсва година за надеждно сравнение.',
    'Статистически neural meta-layer. Не е гаранция за печалба и не отменя случайността на лотарията.': 'Статистически невронен мета слой. Не е гаранция за печалба и не отменя случайността на лотарията.',
    'Страница без подробно заглавие се разчита чрез fallback режим.': 'Страница без подробно заглавие се разчита чрез резервен режим.',
    'Това е изолиран исторически sandbox експеримент. Neural-dynamics моделът не е включен в production pipeline, не създава реални фишове и не доказва предвидимост на бъдещи случайни тиражи.': 'Това е изолиран исторически експеримент. Моделът с невронна динамика не е включен в работната верига, не създава реални фишове и не доказва предвидимост на бъдещи случайни тиражи.',
})

FIELD_LABELS_BG.update({
    # Universal user-facing fields
    "date": "Дата", "year": "Година", "draw_no": "Номер на тиража",
    "drawing_no": "Номер на тегленето", "draw_number": "Номер на тиража",
    "draw_position": "Позиция на тегленето", "bonus_number": "Допълнително число",
    "source": "Източник", "source_label": "Наименование на източника",
    "source_url": "Адрес на източника", "data_status": "Състояние на данните",
    "note": "Бележка", "note_bg": "Бележка", "safe_note": "Бележка за безопасност",
    "details": "Подробности", "details_bg": "Подробности", "check": "Проверка",
    "blocking": "Блокиращо", "area": "Област", "phase": "Етап",
    "action": "Действие", "order": "Ред", "step": "Етап", "exists": "Наличен",
    "label": "Наименование", "name": "Наименование", "model_name": "Модел",
    "model_label": "Наименование на модела", "model_key": "Ключ на модела",
    "strategy_label": "Наименование на стратегията", "strategy_type": "Тип стратегия",
    "ticket_id": "Идентификатор на фиша", "ticket_label": "Наименование на фиша",
    "line_no": "Номер на комбинацията", "role_bg": "Роля", "role": "Роля",
    "text": "Текст", "numbers_text": "Изтеглени числа", "file": "Файл",
    "path": "Път", "version": "Версия", "format": "Формат", "message": "Съобщение",
    "page": "Страница", "section": "Раздел", "purpose": "Предназначение",
    "output": "Изход", "outputs": "Изходи", "input": "Вход", "inputs": "Входове",
    "artifact": "Артефакт", "artifacts": "Артефакти", "validation": "Проверка",
    "verdict": "Заключение", "category": "Категория", "type": "Тип",
    "mode": "Режим", "flag": "Маркер", "present": "Наличен", "ok": "Изрядно",
    # Draw and prize fields
    "draw_date": "Дата на тиража", "draw_year": "Година на тиража",
    "jackpot_eur": "Джакпот (EUR)", "imported_at_utc": "Импортирано на",
    "winners_6": "Печеливши с 6 числа", "winners_5": "Печеливши с 5 числа",
    "winners_4": "Печеливши с 4 числа", "winners_3": "Печеливши с 3 числа",
    "prize_6_eur": "Печалба за 6 числа (EUR)", "prize_5_eur": "Печалба за 5 числа (EUR)",
    "prize_4_eur": "Печалба за 4 числа (EUR)", "prize_3_eur": "Печалба за 3 числа (EUR)",
    "total_6_eur": "Общо за 6 числа (EUR)", "total_5_eur": "Общо за 5 числа (EUR)",
    "total_4_eur": "Общо за 4 числа (EUR)", "total_3_eur": "Общо за 3 числа (EUR)",
    # Common statistics and ticket structure
    "rank": "Класиране", "sum": "Сума", "odd_count": "Нечетни числа",
    "even_count": "Четни числа", "low_count": "Ниски числа", "high_count": "Високи числа",
    "hit_count": "Брой попадения", "match_count": "Брой съвпадения",
    "combination": "Комбинация", "combination_count": "Брой комбинации",
    "combination_index": "Номер на комбинацията", "unique_covered_numbers": "Уникално покрити числа",
    "coverage_percent": "Покритие (%)", "empty_risk_percent": "Риск от нулев резултат (%)",
    "average_interval": "Среден интервал", "current_gap": "Текущ интервал",
    "average_gap": "Среден интервал", "gap_ratio": "Коефициент на интервала",
    "overdue_score": "Оценка за просрочване", "appearances": "Появявания",
    "recent_25": "Появявания в последните 25 тиража",
    "recent_50": "Появявания в последните 50 тиража",
    "recent_100": "Появявания в последните 100 тиража",
    "probability": "Вероятност", "probability_percent": "Вероятност (%)",
    "weight": "Тегло", "strength": "Сила", "stability": "Устойчивост",
    "cost": "Цена", "price": "Цена", "budget": "Бюджет",
    # Historical evaluation fields
    "draws": "Тиражи", "draws_tested": "Проверени тиражи", "units": "Изпълнения",
    "mean_best_hits_difference": "Средна разлика в най-добрия резултат",
    "difference": "Разлика", "mean_difference": "Средна разлика",
    "wins": "Победи", "ties": "Равенства", "losses": "Загуби",
    "two_sided_sign_test_p_value": "p-стойност от двустранен знаков тест",
    "confidence_level": "Ниво на доверие",
    "bootstrap_ci_lower": "Долна граница на доверителния интервал",
    "bootstrap_ci_upper": "Горна граница на доверителния интервал",
    "max_best_hits": "Най-висок резултат", "median_best_hits": "Медианен резултат",
    "at_least_2_percent": "Поне 2 попадения (%)", "at_least_3_percent": "Поне 3 попадения (%)",
    "at_least_4_percent": "Поне 4 попадения (%)", "at_least_5_percent": "Поне 5 попадения (%)",
    "exact_6_count": "Точни 6 попадения", "uniform_random_mean_best_hits": "Среден резултат на случайния модел",
    "seed_advantages": "Разлики по начални стойности", "fold_advantages": "Разлики по исторически периоди",
    "best_hits_distribution": "Разпределение на резултатите",
    # Model output columns
    "neural_dynamics_reservoir": "Невронен модел",
    "neural_dynamics_frozen_ensemble": "Замразен ансамбъл с невронна динамика",
    "frequency_walk_forward": "Честотен модел",
    "recency_weighted_walk_forward": "Модел на скорошната активност",
    "recent_window_frequency": "Честотен модел в скорошен прозорец",
    "frequency_recency_blend": "Смесен честотен и скорошен модел",
    "uniform_random_mean": "Среден резултат — случаен модел",
})

FIELD_WORDS_BG.update({
    "safe": "безопасност", "note": "бележка", "check": "проверка",
    "ticket": "фиш", "tickets": "фишове", "details": "подробности", "bg": "",
    "blocking": "блокиращо", "date": "дата", "year": "година", "label": "наименование",
    "low": "ниски", "high": "високи", "odd": "нечетни", "even": "четни",
    "combination": "комбинация", "combinations": "комбинации", "drawing": "теглене",
    "no": "номер", "position": "позиция", "bonus": "допълнително", "rank": "класиране",
    "unique": "уникални", "covered": "покрити", "text": "текст", "role": "роля",
    "order": "ред", "sum": "сума", "interval": "интервал", "overdue": "просрочване",
    "appearances": "появявания", "recent": "последни", "window": "прозорец",
    "walk": "последователна", "forward": "историческа проверка", "weighted": "претеглен",
    "blend": "смесен", "minus": "минус", "uniform": "равномерно", "dynamics": "динамика",
    "reservoir": "резервоар", "units": "изпълнения", "confidence": "доверие",
    "level": "ниво", "bootstrap": "статистически", "ci": "доверителен интервал",
    "wins": "победи", "ties": "равенства", "losses": "загуби",
    "two": "двустранен", "sided": "", "sign": "знаков", "test": "тест",
    "p": "p", "value": "стойност", "none": "няма данни", "active": "активен",
    "winners": "печеливши", "prize": "печалба", "total": "общо", "jackpot": "джакпот",
    "imported": "импортирано", "data": "данни", "key": "ключ", "name": "наименование",
    "exists": "наличен", "role": "роля", "tested": "проверени", "max": "най-висок",
    "least": "поне", "exact": "точни", "percent": "%", "risk": "риск",
    "empty": "нулев резултат", "plan": "план", "saved": "запазен", "physical": "хартиен",
    "price": "цена", "budget": "бюджет", "cost": "цена", "strategy": "стратегия",
    "description": "описание", "purpose": "предназначение", "section": "раздел",
    "page": "страница", "format": "формат", "message": "съобщение", "action": "действие",
    "blocking": "блокиращо", "reason": "причина", "passed": "преминато",
})

FIELD_LABELS_BG.update({
    "band": "Диапазон", "actual_numbers": "Действително изтеглени числа",
    "combined_score": "Комбинирана оценка", "reliability_score": "Оценка за надеждност",
    "last_seen_index": "Последна поява", "pair": "Двойка", "profile_score": "Оценка на профила",
    "draws_since_last_seen": "Тиражи от последната поява",
    "interval_stability_score": "Оценка за устойчивост на интервала",
    "final_score": "Крайна оценка", "pattern_score": "Оценка на шаблона",
    "coverage_score": "Оценка на покритието", "number_profile_score": "Оценка на профила на числата",
    "hot_cold_balance_score": "Оценка на баланса между активни и неактивни числа",
    "similarity_context_score": "Оценка на сходството", "number_range": "Диапазон на числата",
    "historical_exact_match": "Точно историческо съвпадение",
    "explainability_score": "Оценка за обяснимост", "spread": "Разпределение",
    "warning": "Предупреждение", "recommendation_level": "Ниво на препоръката",
    "size_bytes": "Размер (байтове)", "metric": "Показател", "frequency_share": "Дял на честотата",
    "expected_uniform_count": "Очакван брой при равномерно разпределение",
    "diff_from_expected": "Разлика спрямо очакваното", "rank_desc": "Класиране",
    "share_of_all_drawn_numbers": "Дял от всички изтеглени числа",
    "ticket_table_no": "Номер на таблицата на фиша", "area_bg": "Област", "phase_bg": "Етап",
    "r_blended_score": "Оценка, комбинирана с R",
    "latest_draw_repeat_flag": "Повторение от последния тираж",
    "latest_draw_neighbor_flag": "Съседно число спрямо последния тираж",
    "r_current_gap": "Текущ интервал според R",
    "r_monte_carlo_observed": "Наблюдавана стойност от Монте Карло",
    "r_monte_carlo_expected": "Очаквана стойност от Монте Карло",
    "r_monte_carlo_deviation": "Отклонение от Монте Карло",
    "trial": "Опит", "runs": "Изпълнения", "predicted_top6": "Прогнозирани водещи 6 числа",
    "frequency_ratio": "Коефициент на честотата", "median_interval": "Медианен интервал",
    "consecutive_pairs": "Последователни двойки",
    "appearance_vs_expected_ratio": "Съотношение между наблюдавано и очаквано",
    "main_group": "Основна група", "categories": "Категории",
    "current_gap_ratio": "Коефициент на текущия интервал",
    "matching_numbers_text": "Съвпадащи числа", "matching_numbers": "Съвпадащи числа",
    "tracked_draws": "Проследени тиражи", "hit_rate_2_plus": "Дял с поне 2 попадения",
    "hit_rate_3_plus": "Дял с поне 3 попадения", "consistency_score": "Оценка за последователност",
    "balance_status": "Състояние на баланса", "changed": "Променено",
    "removed_numbers": "Премахнати числа", "added_numbers": "Добавени числа",
    "original_numbers": "Първоначални числа", "average_score_delta": "Средна промяна на оценката",
    "combination_in_ticket": "Комбинация във фиша", "numbers_display": "Числа",
    "latest_output_mtime": "Последна промяна на изхода", "main_reasons": "Основни причини",
    "caution_notes": "Бележки за внимание", "top10_overlap": "Припокриване с водещите 10",
    "structure_score": "Оценка на структурата", "check_item": "Елемент за проверка",
    "kind": "Вид", "group_name": "Име на групата",
    "at_least_one_hit_percent": "Поне едно попадение (%)",
    "model_strength_score": "Оценка на силата на модела", "source_group": "Група на източника",
    "preferred_key": "Предпочитан ключ", "mode_label": "Наименование на режима",
    "price_per_combination_eur": "Цена на комбинация (EUR)", "advisor_score": "Оценка на съветника",
    "saved_after_draw_date": "Запазено след тиража от", "missing_numbers": "Липсващи числа",
    "is_empty": "Без попадения", "has_3_plus": "Има поне 3 попадения",
    "has_4_plus": "Има поне 4 попадения", "evaluated_at_utc": "Оценено на",
    "best_combination_indexes": "Номера на най-добрите комбинации",
    "best_matching_numbers": "Най-добре съвпадащи числа",
    "total_hits_across_rows": "Общо попадения във всички комбинации",
    "rows_with_hits": "Комбинации с попадения", "rows_with_3_plus": "Комбинации с поне 3 попадения",
    "rows_with_4_plus": "Комбинации с поне 4 попадения", "verdict_bg": "Заключение",
    "guard_bg": "Защита", "validation_errors": "Грешки при проверката",
    "rules_version": "Версия на правилата", "parser_format": "Формат на прочитане",
    "why_bg": "Причина", "expected_result_bg": "Очакван резултат", "relative_path": "Относителен път",
})

FIELD_WORDS_BG.update({
    "band": "диапазон", "actual": "действителни", "combined": "комбиниран",
    "reliability": "надеждност", "last": "последен", "seen": "поява", "pair": "двойка",
    "profile": "профил", "since": "от", "stability": "устойчивост", "final": "краен",
    "pattern": "шаблон", "coverage": "покритие", "hot": "активни", "cold": "неактивни",
    "balance": "баланс", "similarity": "сходство", "context": "контекст", "range": "диапазон",
    "match": "съвпадение", "matching": "съвпадащи", "explainability": "обяснимост",
    "spread": "разпределение", "warning": "предупреждение", "recommendation": "препоръка",
    "size": "размер", "bytes": "байтове", "metric": "показател", "share": "дял",
    "expected": "очакван", "diff": "разлика", "from": "спрямо", "desc": "низходящо",
    "all": "всички", "drawn": "изтеглени", "table": "таблица", "area": "област",
    "phase": "етап", "blended": "комбиниран", "repeat": "повторение", "neighbor": "съседно",
    "current": "текущ", "observed": "наблюдаван", "deviation": "отклонение",
    "trial": "опит", "runs": "изпълнения", "predicted": "прогнозирани", "median": "медианен",
    "consecutive": "последователни", "appearance": "поява", "main": "основни",
    "categories": "категории", "tracked": "проследени", "plus": "или повече",
    "consistency": "последователност", "changed": "променено", "removed": "премахнати",
    "added": "добавени", "original": "първоначални", "delta": "промяна", "in": "в",
    "display": "показване", "mtime": "време на промяна", "reasons": "причини",
    "caution": "внимание", "notes": "бележки", "structure": "структура", "item": "елемент",
    "kind": "вид", "group": "група", "one": "едно", "preferred": "предпочитан",
    "mode": "режим", "per": "за", "advisor": "съветник", "after": "след",
    "missing": "липсващи", "is": "е", "has": "има", "evaluated": "оценено",
    "indexes": "номера", "across": "във всички", "rows": "комбинации", "verdict": "заключение",
    "guard": "защита", "errors": "грешки", "rules": "правила", "parser": "прочитане",
    "why": "причина", "relative": "относителен", "of": "от", "to": "до",
    "before": "преди", "after": "след", "with": "с", "above": "над",
})

FIELD_WORDS_BG.update({
    "next": "следващ", "top6": "водещи 6", "rhythm": "ритъм", "absence": "отсъствие",
    "probability": "вероятност", "ensemble": "ансамбъл", "signal": "сигнал", "ratio": "коефициент",
    "system": "система", "min": "минимален", "remaining": "оставащ", "balanced": "балансиран",
    "groups": "групи", "remove": "премахни", "add": "добави", "outputs": "изходи",
    "ok": "изрядно", "present": "наличен", "bucket": "група", "train": "обучение",
    "loss": "загуба", "avg": "средно", "simulated": "симулиран", "pack": "пакет",
    "frozen": "замразен", "vote": "глас", "std": "стандартно отклонение", "safety": "безопасност",
    "consensus": "съгласие", "strong": "силни", "strength": "сила", "query": "заявка",
    "adaptive": "адаптивен", "weight": "тегло", "decade": "десетилетие", "triple": "тройка",
    "other": "други", "duplicate": "дубликат", "steps": "етапи", "when": "кога",
    "real": "реален", "p05": "5-и персентил", "p95": "95-и персентил",
    "included": "включен", "cadence": "периодичност", "scripts": "скриптове", "lines": "комбинации",
    "global": "общ", "training": "обучаващи", "initial": "начални", "first": "първи",
    "scope": "обхват", "time": "време", "sequence": "последователност", "unlocked": "незаключени",
    "chosen": "избрани", "difference": "разлика", "coefficient": "коефициент", "variation": "вариация",
    "p25": "25-и персентил", "p75": "75-и персентил", "p90": "90-и персентил",
    "survived": "преминали", "intervals": "интервали", "for": "за", "due": "дължимост",
    "closeness": "близост", "regularity": "регулярност", "support": "подкрепа", "beyond": "извън",
    "agreement": "съгласие", "distribution": "разпределение", "importance": "важност",
    "signed": "със знак", "watch": "наблюдение", "combo": "комбинация", "span": "обхват",
    "pct": "%", "activity": "активност", "valid": "валиден", "different": "различни",
    "factor": "коефициент", "base": "базова", "adjusted": "коригирана", "sources": "източници",
    "shared": "общи", "help": "помощ", "contribution": "принос", "suggested": "предложени",
    "gain": "подобрение", "tail": "опашка", "datasets": "набори от данни",
    "dependencies": "зависимости", "inputs": "входове", "feeds": "източници", "percentile": "персентил",
    "short": "кратък", "trend": "тенденция", "adjacent": "съседни", "warnings": "предупреждения",
    "discipline": "дисциплина", "compact": "компактен", "execution": "изпълнение",
    "parse": "прочитане", "keys": "ключове", "pages": "страници", "literal": "текст",
    "found": "намерен", "relevant": "относим", "user": "потребител", "use": "употреба",
    "recommended": "препоръчано", "behavior": "поведение", "if": "ако", "ignored": "игнориран",
    "priority": "приоритет", "epochs": "епохи", "start": "начало", "en": "английски",
    "reference": "референтен", "primary": "основен", "quality": "качество", "anti": "защита от",
    "zero": "нулев", "conservative": "консервативен", "aggressive": "агресивен",
    "selected": "избран", "possible": "възможен", "full": "пълен", "pool": "набор",
    "matches": "съвпадения", "trials": "опити", "option": "вариант", "row": "ред",
    "efficiency": "ефективност", "owner": "собственик", "rule": "правило",
    "performance": "представяне", "ready": "готов", "copies": "копия", "redundant": "излишни",
    "paths": "пътища", "widget": "елемент", "bulgarian": "български", "english": "английски",
    "forbidden": "забранени", "tokens": "термини", "unexpected": "неочаквани",
    "ascii": "латиница", "words": "думи", "pass": "преминато", "statistic": "статистика",
    "below": "под", "option": "вариант", "category": "категория",
})

VALUE_LABELS_BG.update({
    "neural_dynamics_frozen_ensemble": "Замразен ансамбъл с невронна динамика",
    "active": "Активен", "inactive": "Неактивен", "passed": "Преминато",
    "failed": "Непреминато", "pending": "Очаква обработка", "settled": "Оценено",
    "unsettled": "Неоценено", "ready": "Готово", "not_ready": "Не е готово",
    "none": "Няма данни", "nan": "Няма данни", "null": "Няма данни",
})

VALUE_LABELS_BG.update({
    'normal': 'Нормално',
    'middle': 'Средна група',
    'planned': 'Планирано',
    'watch_zone': 'Зона за наблюдение',
    'late': 'Закъсняло',
    'under_expected': 'Под очакваното',
    'over_expected': 'Над очакваното',
    'python_compile': 'Компилация на Python',
    'early': 'Ранно',
    'normal_interval': 'Нормален интервал',
    'refreshed_in_test_sandbox': 'Обновено в изолирана тестова среда',
    'strongly_overdue': 'Силно просрочено',
    'above_middle': 'Над средната група',
    'below_middle': 'Под средната група',
    'download_failed': 'Изтеглянето е неуспешно',
    'ml_laboratory': 'Лаборатория за машинно обучение',
    'portfolio_optimizer': 'Оптимизатор на портфейла',
    'final_play_plan': 'Финален план за игра',
    'official_unavailable': 'Официалният източник не е достъпен',
    'v1_locked_waiting_next_draw': 'Версия 1 е заключена и очаква следващия тираж',
    'v50_pair_group_intelligence': 'Анализ на двойки и групи — v50',
    'dry_run_blocked': 'Пробното изпълнение е блокирано',
    'behind': 'Изостава',
    'ready_waiting_next_draw': 'Готово — очаква следващия тираж',
    'sgd_number_classifier': 'SGD класификатор на числа',
    'v41_latest_predictions': 'Последни прогнози — v41',
    'v42_combined_prediction': 'Комбинирана прогноза — v42',
    'v45_final_prediction_tickets': 'Финални прогнозни фишове — v45',
    'v51_ticket_portfolio_intelligence': 'Анализ на портфейла от фишове — v51',
    'v57_hot_cold_stable': 'Активни, неактивни и устойчиви числа — v57',
    'v58_smart_ensemble': 'Интелигентен ансамбъл — v58',
    'v59_smart_ticket_builder_2': 'Интелигентен модул за фишове — v59',
    'local_optional': 'Само локално — по избор',
    'informational': 'Информационно',
    'check_required': 'Необходима е проверка',
    'diversified_weighted': 'Разнообразен претеглен вариант',
    'exploratory_weighted': 'Изследователски претеглен вариант',
    'urlerror': 'Грешка при достъп до адрес',
    'runtimeerror': 'Грешка при изпълнение',
    'runtime_hardening_active': 'Защитата на работната среда е активна',
    'datasets_synced': 'Наборите от данни са синхронизирани',
    'prize_winner_import_ready': 'Импортът на печалби и печеливши е готов',
    'coverage_diversified': 'Покритието е разнообразено',
    'v45_pro_ensemble': 'Разширен ансамбъл — v45',
    'historical_signal_alternative': 'Алтернативен исторически сигнал',
    'primary_rule_aware_ml_ensemble': 'Основен ML ансамбъл, съобразен с правилата',
    'rhythm_weighted_alternative': 'Алтернатива, претеглена по ритъм',
    'add_draw_pre_save_real_result': 'Реален резултат преди запис при добавяне на тираж',
    'control': 'Контрол',
    'model_data_synced': 'Моделните данни са синхронизирани',
    'not_automatic': 'Не е автоматично',
    'up_to_date': 'Актуално',
    'inserted': 'Добавено',
    'already_synced': 'Вече е синхронизирано',
    'waiting_next_real_draw': 'Очаква следващия реален тираж',
    'runtime_hardened': 'Работната среда е защитена',
    'fast_refresh_mode': 'Режим за бързо обновяване',
    'heavy_scripts_excluded_from_default': 'Тежките скриптове са изключени от стандартния режим',
    'user_facing_shortcut_label': 'Потребителско наименование за бърз достъп',
    'step102_page_wired': 'Страницата за етап 102 е свързана',
    'waiting_for_clean_git_status': 'Очаква чисто Git състояние',
    'git_available': 'Git е наличен',
    'working_tree_clean_before_zip': 'Работното дърво е чисто преди ZIP архива',
    'forbidden_tracked_files': 'Забранени проследявани файлове',
    'post_draw_datasets_synced': 'Данните след тиража са синхронизирани',
    'dataset_rows_synced': 'Редовете в данните са синхронизирани',
    'post_draw_status_sync_active': 'Синхронизацията на състоянията след тиража е активна',
    'active_text_encoding': 'Активно текстово кодиране',
    'old_audit_superseded': 'Старата проверка е заменена',
    'navigation_persistent': 'Навигацията се запазва',
    'derived_datasets_match_historical': 'Производните данни съвпадат с историческите',
    'latest_draw_propagated': 'Последният тираж е разпространен',
    'v76_refreshed_to_current_dataset': 'v76 е обновен към текущите данни',
    'v106_post_draw_synced': 'v106 е синхронизиран след тиража',
    'dataset_files_exist': 'Файловете с данни са налични',
    'post_draw_row_counts_synced': 'Броят на редовете след тиража е синхронизиран',
    'latest_draw_has_six_numbers': 'Последният тираж съдържа шест числа',
    'datasets_synced_after_draw': 'Данните са синхронизирани след тиража',
    'history_available': 'Историята е налична',
    'explainability_refreshed': 'Обяснимостта е обновена',
    'post_draw_sync_active': 'Синхронизацията след тиража е активна',
    'heavy_labs_not_default': 'Тежките лаборатории не са в стандартния режим',
    'step107_page_wired': 'Страницата за етап 107 е свързана',
    'step107_refresh_chain_wired': 'Веригата за обновяване на етап 107 е свързана',
    'user_menu_uses_live_status_loader': 'Потребителското меню използва актуално зареждане на състоянието',
    'user_menu_not_bound_to_v86_dataset_metrics': 'Потребителското меню не зависи от показателите на v86',
    'post_draw_sync_green': 'Синхронизацията след тиража е успешна',
    'friendly_refresh_button': 'Разбираем бутон за обновяване',
    'friendly_ticket_mode': 'Разбираем режим за фишове',
    'friendly_status_label': 'Разбираемо наименование на състоянието',
    'visual_number_balls': 'Визуални топки с числа',
    'technical_paths_softened': 'Техническите пътища са представени разбираемо',
    'translated_table_headers': 'Заглавията на таблиците са преведени',
    'no_broken_cyrillic': 'Няма повредена кирилица',
    'cards_created': 'Картите са създадени',
    'three_ticket_suggestion_available': 'Налично е предложение с три фиша',
    'each_ticket_has_four_lines': 'Всеки фиш съдържа четири комбинации',
    'dataset_context_available': 'Контекстът на данните е наличен',
    'latest_draw_available': 'Последният тираж е наличен',
    'step107_policy_available': 'Правилото за етап 107 е налично',
    'final_plan_only_has_two_tickets': 'Финалният план съдържа само два фиша',
    'final_plan_tickets_have_four_lines': 'Фишовете във финалния план съдържат по четири комбинации',
    'extended_has_three_tickets': 'Разширеният план съдържа три фиша',
    'extended_tickets_have_four_lines': 'Фишовете в разширения план съдържат по четири комбинации',
    'third_ticket_is_marked_supplementary': 'Третият фиш е отбелязан като допълнителен',
    'third_scope=supplementary': 'Обхват на третия фиш: допълнителен',
    'extended_lines_are_unique': 'Комбинациите в разширения план са уникални',
    'draw_entries_table_ready': 'Таблицата с въведени тиражи е готова',
    'csv_exports_written': 'CSV файловете за износ са записани',
    'target_files_present': 'Целевите файлове са налични',
    'no_broken_cyrillic_markers': 'Няма маркери за повредена кирилица',
    'visible_developer_terms_reduced': 'Видимите технически термини са намалени',
    'importer_ready': 'Импортирането е готово',
    'play_decision_ready': 'Решението за игра е готово',
    'played_pack_lock_ready': 'Заключването на изиграния пакет е готово',
    'requested_ticket_count': 'Заявен брой фишове',
    'all_lines_have_valid_numbers': 'Всички комбинации съдържат валидни числа',
    'no_duplicate_combinations_inside_pack': 'В пакета няма дублирани комбинации',
    'copy_text_available': 'Текстът за копиране е наличен',
    'model_numbers_available': 'Моделните числа са налични',
    'core_has_requested_size': 'Основният набор е с желания размер',
    'default_real_pack_shape': 'Стандартна структура на реалния пакет',
    'current_pack_link_available': 'Връзката към текущия пакет е налична',
    'combined_positive_negative_foundation': 'Основа с комбинирани положителни и отрицателни сигнали',
    'gap_rhythm_statistical': 'Статистически модел на интервали и ритъм',
    'sgd_logistic_probability': 'Логистична вероятност със SGD',
    'gaussian_naive_bayes': 'Гаусов наивен Байес',
    'overdue_watchlist_numbers': 'Числа за наблюдение поради просрочване',
    'final_refined_rhythm_numbers': 'Финални числа с прецизиран ритъм',
    'cyrillic_mojibake_scan': 'Проверка за повредена кирилица',
    'nearest_centroid_classifier': 'Класификатор по най-близък центроид',
    'kmeans_from_scratch': 'K-means реализация от основата',
    'pca_from_scratch': 'PCA реализация от основата',
    'validated': 'Потвърдено',
    'rolled_back': 'Върнато назад',
    'out_of_sync': 'Не е синхронизирано',
    'unavailable': 'Не е налично',
    'manual_only': 'Само ръчно',
    'deduplicated_and_future_duplicates_suppressed': 'Дубликатите са премахнати и бъдещите дубликати са ограничени',
    'metadata_finalized': 'Метаданните са финализирани',
    'zip_metadata_injected_inside_archive': 'Метаданните са добавени в ZIP архива',
    'ui_no_disk_write_on_render': 'Интерфейсът не записва на диска при визуализиране',
    'create_script_reports_clean_tree_state': 'Скриптът за създаване отчита чисто работно дърво',
    'final_audit_refreshed': 'Финалната проверка е обновена',
    'post_draw_synced': 'Синхронизирано след тиража',
    'user_menu_live_status_synced': 'Актуалното състояние в потребителското меню е синхронизирано',
    'journal_ui_polished': 'Интерфейсът на дневника е подобрен',
    'ticket_source_clarified': 'Източникът на фиша е изяснен',
    'ticket_pack_sources_aligned': 'Източниците на пакета с фишове са съгласувани',
    'disabled': 'Изключено',
    'user_friendly_ui_polished': 'Потребителският интерфейс е подобрен',
    'full_historical_draws_view_ready': 'Пълният изглед на историческите тиражи е готов',
    'data_reality_center_ready': 'Центърът за реалното състояние на данните е готов',
    'prize_import_parser_fixed': 'Прочитането на данните за печалбите е поправено',
    'sample_draw_parsed': 'Примерният тираж е прочетен',
    'sample_numbers_parsed': 'Примерните числа са прочетени',
    'sample_winners_parsed': 'Примерните печеливши са прочетени',
    'sample_jackpot_parsed': 'Примерният джакпот е прочетен',
    'cyrillic_safe': 'Кирилицата е защитена',
    'prize_import_live_fallback_ready': 'Резервното импортиране на печалби в реално време е готово',
    'title_page_parsed': 'Основната страница е прочетена',
    'fallback_page_parsed': 'Резервната страница е прочетена',
    'fallback_numbers': 'Числа от резервния източник',
    'fallback_winners': 'Печеливши от резервния източник',
    'prize_import_table_parser_fixed': 'Прочитането на таблицата с печалби е поправено',
    'prize_import_captcha_safe_manual_ready': 'Ръчното импортиране при CAPTCHA е готово',
    'winner_rows': 'Редове с печеливши',
    'has_six_event': 'Има събитие с шест числа',
    'official_only_prize_source_ready': 'Официалният източник на печалби е готов',
    'main_prize_winner_history': 'Основна история на печалбите и печелившите',
    'export_prize_winner_history': 'Изнесена история на печалбите и печелившите',
    'prize_statistics_ready': 'Статистиката на печалбите е готова',
    'jackpot_cycle_ready': 'Анализът на цикъла на джакпота е готов',
    'real_ticket_pack_ui_polish_ready': 'Интерфейсът на реалния пакет с фишове е готов',
    'v96_add_draw_snapshot_uses_12_lines': 'Моментното състояние на v96 използва 12 комбинации',
    'v96_add_draw_snapshot_uses_10_80': 'Моментното състояние на v96 използва диапазона 10–80',
    'v97_lifecycle_plan_uses_12_lines': 'Планът на жизнения цикъл v97 използва 12 комбинации',
    'v97_lifecycle_plan_uses_10_80': 'Планът на жизнения цикъл v97 използва диапазона 10–80',
    'add_draw_info_label_is_generic_pack_label': 'Информационното наименование при добавяне на тираж е общо за пакета',
    'model_system_ticket_builder_ready': 'Системният модул за моделни фишове е готов',
    'audit_only_no_model_retrain': 'Само проверка — без преобучение на моделите',
    'canonical_dataset_built_no_model_retrain': 'Каноничните данни са изградени без преобучение на моделите',
    'trained': 'Обучено',
    'training_ready_review_required_no_retrain': 'Готово за обучение; необходим е преглед; без автоматично преобучение',
    'interval_rhythm_refined_foundation': 'Прецизирана основа за интервали и ритъм',
    'final_ensemble_ticket_foundation': 'Основа за финален ансамблов фиш',
    'v50_pair_group_intelligence_completed': 'Анализът на двойки и групи v50 е завършен',
    'v51_ticket_portfolio_intelligence_completed': 'Анализът на портфейла от фишове v51 е завършен',
    'step150_ui_language_integrity_summary': 'Обобщение на езиковата цялост на интерфейса — етап 150',
    'prospective_locked_evaluation_forecast': 'Заключена проспективна прогноза за оценяване',
    'reproducible_baseline': 'Възпроизводим базов модел',
    'research_only_neural_dynamics_sandbox': 'Изследователска лаборатория за невронна динамика',
    'research_only_neural_robustness_validation': 'Изследователска проверка на устойчивостта на невронния модел',
    'v41_predictions_generated_from_canonical_draw_events': 'Прогнозите v41 са генерирани от каноничните тиражи',
    'rolling_250_event_frequency': 'Плъзгаща честота за 250 тиража',
    'per_number_binary_classifier': 'Двоичен класификатор за всяко число',
    'v45_prediction_engine_pro_tickets_ready': 'Фишовете от разширения прогнозен модул v45 са готови',
    'v45_prediction_engine_pro_scores_ready': 'Оценките от разширения прогнозен модул v45 са готови',
    'v45_prediction_engine_pro': 'Разширен прогнозен модул v45',
    'per_number_binary_models_plus_rule_aware_selector': 'Двоични модели за всяко число и селектор, съобразен с правилата',
    'pair_group_intelligence': 'Анализ на двойки и групи',
    'ticket_portfolio_intelligence': 'Анализ на портфейла от фишове',
    'neural_epoch_comparison_audit': 'Проверка на невронния модел по епохи',
    'known_from_v39_dataset_bonus_missing': 'Известно от данните v39; допълнителното число липсва',
    'sample_not_official': 'Пример — не е официален',
    'available_without_bonus': 'Налично без допълнително число',
    'real_ticket_pack_cards': 'Карти на реалния пакет с фишове',
    'four_lines_per_ticket_rule': 'Правило за четири комбинации във фиш',
    'technical_fields_softened': 'Техническите полета са представени разбираемо',
    'raw_source_alias_removed': 'Дублиращото име на суровия източник е премахнато',
})



# Step 150.1 deep dynamic localization: runtime values from JSON/CSV and
# historical modules can bypass literal-only translation. These exact mappings
# keep normal-user mode natural while raw technical data remains available from
# the technical-details switch.
BG_EXACT.update({
    "Ranks numbers by recurrence intervals. For each number, the model compares the current gap since its last appearance with its average historical interval, estimates an interval hazard probability, and combines it with the fair 6/49 baseline and empirical frequency.":
        "Подрежда числата според интервалите между появяванията им. За всяко число моделът сравнява текущия интервал със средния исторически интервал и комбинира резултата с базовата вероятност за 6/49 и наблюдаваната честота.",
    "The fair mathematical chance for any single number to appear in the next 6/49 draw is still 6/49. This model is a statistical training estimate based on historical intervals, not a guarantee.":
        "Математическата вероятност отделно число да се появи в следващ тираж 6/49 остава 6/49. Моделът дава статистическа оценка според историческите интервали, а не гаранция.",
    "Ranks numbers whose historical frequency, recent frequency, and recency gap are closest to the expected fair 6/49 behavior.":
        "Подрежда числата, чиито историческа честота, скорошна честота и интервал от последната поява са най-близо до очакваното поведение при 6/49.",
    "Проверява dataset синхрон, Step 76–79 артефакти, sync планове, compile, JSON/CSV parse и кирилица преди финалния sync контрол.":
        "Проверява синхронизацията на данните, артефактите от етапи 76–79, плановете за синхронизация, компилацията, прочитането на JSON/CSV и кирилицата преди финалната проверка.",
    "Проверява данни синхрон, Step 76–79 артефакти, sync планове, compile, JSON/CSV parse и кирилица преди финалния sync контрол.":
        "Проверява синхронизацията на данните, артефактите от етапи 76–79, плановете за синхронизация, компилацията, прочитането на JSON/CSV и кирилицата преди финалната проверка.",
    "Ready to run.": "Готово за изпълнение.",
    "Sandbox artifact advanced to 2026-54.": "Тестовият артефакт е преместен към тираж 2026-54.",
    "The selected main section persists across Streamlit reruns.": "Избраният главен раздел се запазва при повторно изпълнение на приложението.",
    "page radio has stable key": "Изборът на страница използва постоянен вътрешен ключ",
    "choice is mirrored in session state": "Изборът се запазва в текущата потребителска сесия",
    "Step 105 marker present": "Маркерът за етап 105 е наличен",
    "Patch is auditable in streamlit_app.py.": "Промяната може да бъде проверена в основния файл на приложението.",
    "Ред от active plan v94.": "Ред от активния план v94.",
    "Lottery draws are random. This model ranks historical/statistical signals; it is not a guarantee and does not prove future winning numbers.":
        "Лотарийните тиражи са случайни. Моделът подрежда исторически и статистически сигнали; той не е гаранция и не доказва кои числа ще бъдат изтеглени в бъдеще.",
    "no parseable score source files found": "Не са намерени източници с оценки, които могат да бъдат прочетени.",
    "Final User Manual / App Guide Center": "Ръководство за потребителя и работа с приложението",
    "Търси силен среден score, но с контрол върху odd/even, low/high, range и десетилетия.":
        "Търси силна средна оценка, като контролира баланса между четни и нечетни, ниски и високи числа, общия диапазон и десетилетията.",
    "UI can render physical ticket cards.": "Интерфейсът може да показва карти на хартиените фишове.",
    "Included in списък на файловете": "Включено в списъка на файловете",
    "Average sum of six numbers.": "Средна сума на шестте числа.",
    "Standard deviation of draw sums.": "Стандартно отклонение на сумите в тиражите.",
    "Average odd count.": "Среден брой нечетни числа.",
    "Average low count where low <= 24.": "Среден брой ниски числа, където ниско число е до 24 включително.",
    "<urlopen error [Errno -3] Temporary failure in name resolution>": "Временен проблем при свързването с външния източник.",
    "Dataset expectation:": "Очакван файл с данни:",
    "Upstream audit OK:": "Предходната проверка е успешна:",
    "Streamlit label:": "Наименование в приложението:",
    "Required file:": "Задължителен файл:",
    "Test cache артефакт.": "Артефакт от тестовия кеш.",
})

VALUE_LABELS_BG.update({
    "synced": "Синхронизирано",
    "read_only_detection": "Проверка само за четене",
    "dry_run": "Пробно изпълнение",
    "reduced": "Ограничен режим",
    "verified_2026_manual_screenshots": "Потвърдено чрез ръчно прегледани изображения за 2026 г.",
    "sqlite_db_exists": "Локалната SQLite база е налична",
    "global_streamlit_ui_menus_pages_widgets_tables_statuses_and_research_technical_detail_separation":
        "Глобално езиково покритие на менюта, страници, елементи, таблици, статуси и технически подробности",
    "personal_local_journal_removed_from_public_tree": "Личният локален дневник е премахнат от публичното дърво",
    "timestamp_only_model_snapshot_removed": "Премахнато е моделно копие, различаващо се само по времевия печат",
    "exact_duplicate_launcher": "Премахнат е идентичен стартиращ файл",
})

FIELD_LABELS_BG.update({
    "difference": "Разлика",
    "units": "Изпълнения",
    "confidence level": "Ниво на доверие",
    "bootstrap ci lower": "Долна граница на 95% доверителния интервал",
    "bootstrap ci upper": "Горна граница на 95% доверителния интервал",
    "wins": "Победи", "ties": "Равенства", "losses": "Загуби",
    "event_sha256": "SHA-256 подпис на събитието",
    "events_with_3plus_hits": "Тиражи с поне 3 попадения",
    "events_with_4plus_hits": "Тиражи с поне 4 попадения",
    "events_with_5plus_hits": "Тиражи с поне 5 попадения",
    "count_in_streamlit_app": "Брой в приложението",
    "r_monte_carlo_score": "Оценка от Монте Карло в R",
    "z_score_vs_average_interval": "Z-оценка спрямо средния интервал",
    "number_a": "Число А", "number_b": "Число Б",
    "pair_a": "Двойка А", "pair_b": "Двойка Б",
    "ticket_a": "Фиш А", "ticket_b": "Фиш Б",
    "n1": "Число 1", "n2": "Число 2", "n3": "Число 3",
    "n4": "Число 4", "n5": "Число 5", "n6": "Число 6",
    "missing_inputs": "Липсващи входни данни",
})



# Step 150.2: plain-language Bulgarian labels for dynamic research and audit values.
BG_EXACT.update({
    "No comparison in the Step 144–146 evidence chain demonstrates robust positive superiority. The current neural configuration is therefore paused and archived; production promotion remains blocked.":
        "Нито едно сравнение в етапи 144–146 не показва устойчиво положително превъзходство. Затова текущият невронен модел е спрян и архивиран, а включването му в работния режим остава блокирано.",
    "The neural robustness experiment passed every exploratory stability gate. Automatic production promotion remains disabled; independent confirmation would still be required.":
        "Проверката за устойчивост изпълни всички изследователски условия. Автоматично включване в работния режим не се извършва; необходима е независима потвърждаваща проверка.",
    "The neural robustness experiment did not pass every multi-seed, multi-period confidence and stability gate. The model remains research-only and isolated from ticket generation.":
        "Проверката за устойчивост не изпълни всички условия при различните начални стойности и исторически периоди. Моделът остава само за изследване и е отделен от създаването на комбинации.",
    "The neural-dynamics sandbox did not pass the promotion gate on this historical holdout. It remains research-only and is not connected to ticket generation.":
        "Невронният модел не изпълни условията в този независим исторически период. Той остава само за изследване и не участва в създаването на комбинации.",
    "The neural-dynamics sandbox passed the exploratory comparison gate on this historical holdout. It remains research-only and requires independent confirmation before any production consideration.":
        "Невронният модел показа положителен резултат в този независим исторически период. Той остава само за изследване и изисква независима потвърждаваща проверка преди работна употреба.",
})

VALUE_LABELS_BG.update({
    "evidence_chain_complete": "Всички необходими експерименти са включени в оценката",
    "source_statuses_complete": "Всички използвани експерименти са завършени",
    "source_signatures_match": "Контролните подписи на резултатите съвпадат",
    "dataset_identity_consistent": "Всички сравнения използват един и същ набор от данни",
    "future_data_leakage_absent": "Не са използвани бъдещи данни",
    "production_integration_absent": "Няма връзка с работната верига",
    "robust_superiority_demonstrated": "Доказано е устойчиво превъзходство",
    "all_neural_promotion_gates_passed": "Всички условия за допускане на невронния модел са изпълнени",
    "all_mean_advantages_positive": "Средният резултат е по-добър при всяко сравнение",
    "all_confidence_intervals_above_zero": "Всички доверителни интервали потвърждават положително предимство",
    "all_sign_tests_significant": "Всички статистически проверки потвърждават значимо предимство",
    "all_seed_positive_rates_sufficient": "Резултатът е положителен при достатъчно начални стойности",
    "all_fold_positive_rates_sufficient": "Резултатът е положителен при достатъчно исторически периоди",
    "neural_seed_spread_within_limit": "Разликите между началните стойности са в допустими граници",
    "minimum_design_size_met": "Използвани са достатъчно изпълнения и исторически периоди",
    "materially_new_hypothesis": "Съществено нова изследователска хипотеза",
    "preregistered_primary_metric_and_gate": "Предварително определени основен показател и условия за успех",
    "untouched_or_future_validation_period": "Нов неизползван исторически или бъдещ период",
    "untouched_or_future_non_overlapping_period": "Нов и неприпокриващ се исторически или бъдещ период",
    "baseline_first_comparison": "Първо сравнение с простите базови модели",
    "baseline_model_first_comparison": "Първо сравнение с простите базови модели",
    "score_before_learn_chronology": "Оценяване преди добавяне към следващото обучение",
    "no_personal_journal_access": "Без достъп до личния дневник",
    "no_production_pipeline_access": "Без достъп до работната верига",
    "no_real_ticket_generation": "Без създаване на комбинации за реална игра",
    "single_holdout_baseline": "Единична независима проверка на базов модел",
    "single_holdout_neural": "Единична независима проверка на невронния модел",
    "multi_seed_multi_period_neural": "Проверка с няколко начални стойности и исторически периода",
    "positive_but_not_robust": "Положително, но неустойчиво предимство",
    "robust_negative": "Устойчиво по-слаб резултат",
    "robust_positive": "Устойчиво по-добър резултат",
    "pause_and_archive": "Спрян и архивиран",
    "blocked_without_robust_superiority": "Блокиран без доказано устойчиво превъзходство",
    "materially_new_preregistered_hypothesis": "Нова предварително определена изследователска хипотеза",
})

FIELD_LABELS_BG.update({
    "evidence_chain_complete": "Всички необходими експерименти са включени в оценката",
    "source_statuses_complete": "Всички използвани експерименти са завършени",
    "source_signatures_match": "Контролните подписи на резултатите съвпадат",
    "dataset_identity_consistent": "Всички сравнения използват един и същ набор от данни",
    "future_data_leakage_absent": "Не са използвани бъдещи данни",
    "production_integration_absent": "Няма връзка с работната верига",
    "robust_superiority_demonstrated": "Доказано устойчиво превъзходство",
    "all_neural_promotion_gates_passed": "Всички условия за допускане са изпълнени",
    "evidence_scope": "Какво е проверено",
    "candidate": "Изследван модел",
    "comparator": "Сравнителен модел",
    "mean_advantage": "Средна разлика",
    "ci_lower": "Долна граница на доверителния интервал",
    "ci_upper": "Горна граница на доверителния интервал",
    "positive_seed_rate": "Положителен дял по начални стойности",
    "positive_fold_rate": "Положителен дял по исторически периоди",
    "source_promotion_gate_passed": "Условията в източниковия експеримент са изпълнени",
    "evidence_outcome": "Извод от доказателствата",
    "production_eligible": "Допустим за работна употреба",
    "source_summary": "Източников отчет",
    "promotion_requirements": "Условия за допускане",
    "next_experiment_requirements": "Условия за следващ експеримент",
    "materially_new_hypothesis": "Съществено нова изследователска хипотеза",
    "preregistered_primary_metric_and_gate": "Предварително определени основен показател и условия за успех",
    "untouched_or_future_validation_period": "Нов неизползван исторически или бъдещ период",
    "untouched_or_future_non_overlapping_period": "Нов и неприпокриващ се исторически или бъдещ период",
    "baseline_first_comparison": "Първо сравнение с простите базови модели",
    "baseline_model_first_comparison": "Първо сравнение с простите базови модели",
    "score_before_learn_chronology": "Оценяване преди добавяне към следващото обучение",
    "no_personal_journal_access": "Без достъп до личния дневник",
    "no_production_pipeline_access": "Без достъп до работната верига",
    "no_real_ticket_generation": "Без създаване на комбинации за реална игра",
})

FIELD_WORDS_BG.update({
    "complete": "завършено", "consistent": "съгласувано", "absent": "няма",
    "signatures": "контролни подписи", "statuses": "състояния", "future": "бъдещи",
    "leakage": "използване на бъдещи данни", "integration": "връзка", "gates": "условия",
    "materially": "съществено", "hypothesis": "хипотеза", "preregistered": "предварително определен",
    "primary": "основен", "metric": "показател", "gate": "условие", "untouched": "неизползван",
    "non": "не", "overlapping": "припокриващ се", "period": "период", "first": "първо",
    "comparison": "сравнение", "validation": "проверка", "learn": "обучение", "chronology": "последователност",
    "access": "достъп", "real": "реална", "ticket": "фиш", "generation": "създаване",
    "demonstrated": "доказано", "superiority": "превъзходство", "all": "всички",
})

TECHNICAL_COLUMN_MARKERS: tuple[str, ...] = (
    "sha256", "_hash", "hash_", "signature", "previous_event", "configuration_",
    "dataset_", "code_", "artifact_path", "source_summary", "created_at_utc",
    "updated_at_utc", "generated_at_utc", "last_evaluated_at_utc", "locked_at_utc",
    "settled_at_utc", "event_id", "experiment_id", "decision_id", "protocol_id", "lock_id",
    "seed_advantages", "fold_advantages", "best_hits_distribution", "target_sequence_index",
    "source_dataset_rows", "forecast_signature", "artifact_",
    "p_value", "sign_test", "ci_lower", "ci_upper", "confidence_level",
    "positive_seed_rate", "positive_fold_rate", "source_promotion_gate",
    "source_summary", "raw_", "command", "code_file", "policy_sha",
)

FORBIDDEN_BG_UI_TOKENS: tuple[str, ...] = (
    "dataset", "holdout", "frequency", "random", "recency", "neural", "research",
    "production", "pipeline", "baseline", "forward test", "walk-forward", "robustness",
    "evidence", "promotion gate", "decision gate", "status", "summary", "checklist",
    "runtime", "release", "refresh", "sync", "checkpoint", "activation", "recovery",
    "rollback", "dry-run", "preflight", "operator", "bundle", "ledger", "settlement",
    "downstream", "timeout", "backup", "staging", "optional", "rerun", "journal",
    "mirror", "historical", "canonical", "normalized", "generation", "portfolio",
    "incident", "exception", "reconciliation", "follow-up", "closure", "retention",
    "archive", "cleanup", "registry", "preview", "management health", "operations",
    "governance", "source of truth", "decision center", "freshness check", "post-draw",
    "append-only", "end-to-end", "auto-apply",
)



USER_ASCII_ALLOWLIST: frozenset[str] = frozenset({
    "api", "bst", "captcha", "csv", "eur", "bgn", "git", "github", "html", "id",
    "json", "jsonl", "jupyter", "markdown", "ml", "numpy", "ok", "pca", "png",
    "python", "qa", "r", "readme", "sgd", "sha", "sha-256", "sha256", "sql",
    "sqlite", "streamlit", "txt", "ui", "url", "utc", "ux", "zip", "p", "z",
})


def unexpected_user_ascii_words(text: Any) -> list[str]:
    """Return untranslated Latin words that should not appear in Bulgarian user mode."""
    visible = re.sub(r"<[^>]+>", " ", str(text))
    visible = re.sub(r"`[^`]*`", " ", visible)
    visible = re.sub(r"https?://\S+", " ", visible, flags=re.IGNORECASE)
    visible = re.sub(r"(?:(?:[A-Za-z]:)?[\\/])?[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)+", " ", visible)
    result: set[str] = set()
    for raw in re.findall(r"\b[A-Za-z][A-Za-z0-9+.-]{1,}\b", visible):
        word = raw.strip(".-")
        lowered = word.lower()
        if not word or lowered in USER_ASCII_ALLOWLIST:
            continue
        if re.fullmatch(r"(?:v|V|n|N)\d+(?:_\d+)*", word):
            continue
        if re.fullmatch(r"[A-Fa-f0-9]{8,}", word):
            continue
        result.add(word)
    return sorted(result, key=str.lower)


def _generic_bg_field_label(raw: str) -> str:
    normalized = re.sub(r"[\s./-]+", "_", raw.lower()).strip("_")
    tokens = set(token for token in normalized.split("_") if token)
    if tokens & {"reason", "message", "description", "details", "note", "interpretation", "warning"}:
        return "Обяснение"
    if tokens & {"status", "state", "health", "verdict", "outcome", "result"}:
        return "Състояние"
    if tokens & {"date", "time", "year", "month", "day", "utc", "timestamp"}:
        return "Дата и час"
    if tokens & {"count", "rows", "units", "draws", "runs", "entries", "total"}:
        return "Брой"
    if tokens & {"model", "strategy", "candidate", "comparator", "baseline", "method"}:
        return "Модел или метод"
    if tokens & {"score", "rate", "ratio", "share", "percent", "probability", "mean", "average", "difference"}:
        return "Оценка"
    if tokens & {"check", "gate", "passed", "complete", "consistent", "match", "absent", "requirement"}:
        return "Условие за проверка"
    if tokens & {"path", "file", "hash", "sha256", "signature", "command", "code", "id", "key"}:
        return "Техническа информация"
    return "Показател"


def _safe_bg_dynamic_text(translated: str, raw: str, field_name: Any | None = None) -> str:
    if not unexpected_user_ascii_words(translated):
        return translated
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_./-]{1,160}", raw) and not re.search(r"[/\\]", raw):
        return _generic_bg_field_label(str(field_name or raw))
    if field_name is not None:
        label = _generic_bg_field_label(str(field_name))
        if label == "Обяснение":
            return "Подробното техническо описание е достъпно в раздел „Технически подробности“."
        if label == "Състояние":
            return "Необходима е техническа проверка"
    if len(raw) >= 48 or " " in raw:
        return "Подробното техническо описание е достъпно в раздел „Технически подробности“."
    return "Техническа стойност"

def current_language(st_module: Any | None = None) -> str:
    try:
        if st_module is None:
            import streamlit as st_module  # type: ignore
        return str(st_module.session_state.get("language", "bg"))
    except Exception:
        return "bg"


def ui_text(bg: str, en: str, st_module: Any | None = None) -> str:
    return en if current_language(st_module) == "en" else bg


def technical_details_enabled(st_module: Any | None = None) -> bool:
    try:
        if st_module is None:
            import streamlit as st_module  # type: ignore
        return bool(st_module.session_state.get("v150_show_technical_details", False))
    except Exception:
        return False


def _translate_plain_segment(text: str, language: str, show_technical: bool) -> str:
    text = clean_user_version_labels(text, language=language, show_technical=show_technical)
    if language == "en":
        if text in EN_EXACT:
            return EN_EXACT[text]
        out = text
        for src, dst in sorted(EN_REPLACEMENTS, key=lambda item: len(item[0]), reverse=True):
            out = out.replace(src, dst)
        return out

    if text in BG_EXACT:
        return BG_EXACT[text]
    out = text
    if not show_technical:
        out = re.sub(r"(?i)\bStep\s+\d+(?:\.\d+)*\s*[—–:-]\s*", "", out)
    for src, dst in sorted(BG_REPLACEMENTS, key=lambda item: len(item[0]), reverse=True):
        pattern = re.escape(src)
        if src and src[0].isalnum() and src[-1].isalnum():
            pattern = rf"(?<!\w){pattern}(?!\w)"
        out = re.sub(pattern, dst, out, flags=re.IGNORECASE)
    out = re.sub(r"(?i)\bStep\s+(\d+(?:\.\d+)*)\b", r"Етап \1", out)
    # Clean accidental mixed-language suffixes and doubled words.
    cleanup = (
        ("приложението-ът", "приложението"),
        ("app-ът", "приложението"),
        ("контролен списък-а", "контролния списък"),
        ("контролен контролен списък", "контролен списък"),
        ("характеристикаs", "характеристики"),
        ("оценкаs", "оценки"),
        ("отчетs", "отчети"),
        ("данните слоя", "слоя с данни"),
        ("данните обновяване", "обновяване на данните"),
        ("издание ZIP", "чист ZIP архив"),
        ("издание проверка", "проверка на изданието"),
        ("работна среда поведението", "поведението на приложението"),
        ("работен режим заключване", "заключване на работния режим"),
        ("работен режим веригата", "работната верига"),
        ("работен режим данните", "работните данни"),
        ("работен режим състоянието", "състоянието на работния режим"),
        ("оператор обобщение", "операторско обобщение"),
        ("активиране разрешение", "разрешение за активиране"),
        ("активиране опитите", "опитите за активиране"),
        ("активиране събития", "събития за активиране"),
        ("възстановяване събития", "събития за възстановяване"),
        ("предварителна проверка е блокиран", "предварителната проверка е блокирана"),
        ("защита настройките", "настройките за защита"),
        ("повторен опит изчакване между опитите", "изчакване между повторните опити"),
        ("в реално време БСТ", "БСТ в реално време"),
        ("табло-ът", "таблото"),
        ("доказателства пакет", "пакет с доказателства"),
        ("само за преглед в реално време", "проверка в реално време само за преглед"),
        ("auto-приложениетоly", "автоматично прилагане"),
        ("пакет с комбинацииs", "пакети с комбинации"),
        ("приложениетоend-only", "само с добавяне"),
        ("характеристика generation", "генериране на характеристики"),
        ("BзаключванеED", "БЛОКИРАНО"),
        ("синхронизацияed", "синхронизирано"),
        ("пакет-и", "пакети"),
        ("чист чист ZIP", "чист ZIP"),
        ("зависим модули", "зависими модули"),
        ("зависим слоеве", "зависими слоеве"),
        ("зависим етапи", "зависими етапи"),
        ("зависим верига", "зависима верига"),
        ("зависим обновяване", "обновяване на зависимите слоеве"),
        ("Създавам резервно копие, подготвителна среда", "Създавам резервно копие и подготвям временна среда"),
        ("само с добавяне история на регистъра", "история на регистъра само с добавяне"),
        ("дневник огледално копие", "огледално копие на дневника"),
        ("характеристика таблици", "таблици с характеристики"),
        ("приложението-а", "приложението"),
        ("данните-ът", "наборът от данни"),
        ("оценка/model", "оценъчни/моделни"),
        ("архив & безопасно", "архив и безопасно"),
        ("възстановяване &", "възстановяване и"),
        ("ескалация &", "ескалация и"),
        ("отчитане &", "отчитане и"),
        ("тренировки,", "тренировки,"),
        ("само с добавяне регистър историята", "историята на регистъра само с добавяне"),
        ("само с добавяне история", "история само с добавяне"),
        ("архив почистване", "почистване на архива"),
        ("Active съхранение", "Активно съхранение"),
        ("Minimum active verified", "Минимален брой активни потвърдени"),
        ("пакет статус", "статус на пакета"),
        ("Етап 136 тренировка проверка-а", "проверката на тренировката от етап 136"),
        ("запис в Git-ва", "записва в Git"),
        ("запис в Git-неш", "запишеш в Git"),
        ("качване-неш", "качиш"),
        ("Етап —", "Етап —"),
        ("пакет-ът", "пакетът"),
        ("git командите", "Git командите"),
        ("безопасно бележка", "безопасна бележка"),
        ("износ файлове", "файлове за износ"),
        ("тренировка за възстановяване случаи", "случаи от тренировките за възстановяване"),
    )
    for bad, good in cleanup:
        out = out.replace(bad, good)
    out = re.sub(r"\s+&\s+", " и ", out)
    out = re.sub(r"\b(модел|режим|проверка|оценяване|данните)\s+\1\b", r"\1", out, flags=re.IGNORECASE)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = clean_user_version_labels(out, language=language, show_technical=show_technical)
    return out


def translate_text(value: Any, *, language: str | None = None, show_technical: bool | None = None) -> Any:
    if not isinstance(value, str):
        return value
    language = language or current_language()
    show_technical = technical_details_enabled() if show_technical is None else show_technical
    if not value:
        return value
    if "<style" in value.lower() or "</style>" in value.lower():
        return value

    stripped = value.strip()
    # Never corrupt file paths, commands, hashes or machine identifiers. They are
    # hidden from normal tables by default and remain available in technical mode.
    if re.fullmatch(r"(?:[A-Za-z]:[\\/]|/)?[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)+(?:[.:][A-Za-z0-9_.-]+)?", stripped):
        return value
    if re.fullmatch(r"[A-Fa-f0-9]{32,}", stripped):
        return value

    # Natural prefix localization while preserving the referenced path/value.
    if language == "bg":
        prefix_map = {
            "Required file:": "Задължителен файл:",
            "Dataset expectation:": "Очакван файл с данни:",
            "Upstream audit OK:": "Предходната проверка е успешна:",
            "Streamlit label:": "Наименование в приложението:",
        }
        for source_prefix, target_prefix in prefix_map.items():
            if stripped.startswith(source_prefix):
                return target_prefix + stripped[len(source_prefix):]
        count_match = re.fullmatch(r"count=(\d+)", stripped, flags=re.IGNORECASE)
        if count_match:
            return f"Брой: {count_match.group(1)}"

    # Keep HTML tags and inline code/path fragments untouched while translating visible text.
    html_parts = re.split(r"(<[^>]+>)", value)
    translated_html: list[str] = []
    for part in html_parts:
        if part.startswith("<") and part.endswith(">"):
            translated_html.append(part)
            continue
        code_parts = re.split(r"(`[^`]*`)", part)
        for code_part in code_parts:
            if code_part.startswith("`") and code_part.endswith("`"):
                translated_html.append(code_part)
            else:
                translated_html.append(_translate_plain_segment(code_part, language, show_technical))
    return "".join(translated_html)


def is_technical_value(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    raw = value.strip()
    if not raw:
        return False
    if re.fullmatch(r"[A-Fa-f0-9]{32,}", raw):
        return True
    if re.fullmatch(r"(?:[A-Za-z]:[\\/]|/)?[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)+", raw):
        return True
    if re.fullmatch(r"(?:EXP|DEC|LOCK|PFT)-[A-Za-z0-9-]+", raw):
        return True
    return False


def translate_value(
    value: Any, *, language: str | None = None, show_technical: bool | None = None, field_name: Any | None = None
) -> Any:
    language = language or current_language()
    show_technical = technical_details_enabled() if show_technical is None else show_technical
    # Recursive localization is required for st.json and nested table cells.
    if isinstance(value, Mapping):
        return {
            humanize_field_name(k, language=language): translate_value(v, language=language, show_technical=show_technical, field_name=k)
            for k, v in value.items()
            if show_technical or not is_technical_column(k)
        }
    if isinstance(value, (list, tuple)):
        return [translate_value(item, language=language, show_technical=show_technical) for item in value]
    if value is None:
        return "Няма данни" if language == "bg" else "No data"
    if isinstance(value, bool):
        return ("Да" if value else "Не") if language == "bg" else ("Yes" if value else "No")
    try:
        import math
        if isinstance(value, float) and math.isnan(value):
            return "Няма данни" if language == "bg" else "No data"
    except Exception:
        pass
    if not isinstance(value, str):
        return value
    raw = value.strip()
    if not raw:
        return value
    if not show_technical and is_technical_value(raw):
        return "Техническа стойност" if language == "bg" else "Technical value"
    if language == "bg":
        mapped = VALUE_LABELS_BG.get(raw.lower())
        if mapped is not None:
            return clean_user_version_labels(mapped, language=language, show_technical=show_technical)
        if raw.startswith("<urlopen error"):
            return "Временен проблем при свързването с външния източник."
        # Hide raw paths from normal-user checks while preserving their meaning.
        technical_prefixes = {
            "Required file:": "Проверка за задължителен проектен файл",
            "Dataset expectation:": "Проверка на очаквания файл с данни",
            "Upstream audit OK:": "Предходната проверка е успешна",
        }
        if not show_technical:
            for prefix, friendly in technical_prefixes.items():
                if raw.startswith(prefix):
                    return friendly
        # Internal enum-like values are labels, not prose.
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_./-]{1,120}", raw) and not re.search(r"[/\\]", raw):
            candidate = humanize_field_name(raw, language=language)
            if candidate != raw:
                return candidate
    translated = str(translate_text(value, language=language, show_technical=show_technical))
    if language == "bg" and not show_technical:
        return _safe_bg_dynamic_text(translated, raw, field_name)
    return translated


def humanize_field_name(name: Any, *, language: str | None = None) -> str:
    language = language or current_language()
    raw = str(name).strip()
    if language == "bg":
        normalized = re.sub(r"[\s./-]+", "_", raw.lower()).strip("_")
        for key in (raw, raw.lower(), normalized):
            if key in FIELD_LABELS_BG:
                return FIELD_LABELS_BG[key]
        tokens = [token for token in re.split(r"[_\s./-]+", raw) if token]
        words: list[str] = []
        for token in tokens:
            if token.lower() in FIELD_WORDS_BG:
                translated = FIELD_WORDS_BG[token.lower()]
            elif re.fullmatch(r"(?:v|V|step)\d+(?:_\d+)*", token):
                translated = token.replace("step", "етап ").replace("Step", "Етап ")
            else:
                translated = translate_text(token, language="bg", show_technical=False)
            if str(translated).strip():
                words.append(str(translated).strip())
        result = " ".join(words).strip() or raw
        result = re.sub(r"\s{2,}", " ", result)
        if unexpected_user_ascii_words(result):
            result = _generic_bg_field_label(raw)
        return result[:1].upper() + result[1:] if result else raw
    if raw in FIELD_LABELS_EN:
        return FIELD_LABELS_EN[raw]
    return raw.replace("_", " ").strip().title()


def is_technical_column(name: Any) -> bool:
    normalized = str(name).strip().lower()
    return any(marker in normalized for marker in TECHNICAL_COLUMN_MARKERS)


def _format_timestamp(value: Any, field_name: str) -> Any:
    if not isinstance(value, str) or not ("_at" in field_name or field_name.endswith("_utc")):
        return value
    candidate = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
        return parsed.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return value


def localize_table(data: Any, *, language: str | None = None, show_technical: bool | None = None) -> Any:
    language = language or current_language()
    show_technical = technical_details_enabled() if show_technical is None else show_technical
    try:
        import pandas as pd  # type: ignore
    except Exception:
        pd = None

    if pd is not None and isinstance(data, pd.DataFrame):
        original = data.copy()
        columns = list(original.columns)
        if not show_technical:
            visible = [col for col in columns if not is_technical_column(col)]
            if visible:
                original = original.loc[:, visible]
                columns = visible
        rename_map = {col: humanize_field_name(col, language=language) for col in columns}
        result = original.rename(columns=rename_map)
        for source_col, display_col in rename_map.items():
            try:
                result[display_col] = result[display_col].map(
                    lambda item, field=str(source_col): translate_value(_format_timestamp(item, field), language=language, show_technical=show_technical, field_name=field)
                )
            except Exception:
                pass
        # Ensure translated labels stay unique.
        seen: dict[str, int] = {}
        unique: list[str] = []
        for column in result.columns:
            base = str(column)
            seen[base] = seen.get(base, 0) + 1
            unique.append(base if seen[base] == 1 else f"{base} ({seen[base]})")
        result.columns = unique
        return result

    if isinstance(data, list):
        output = []
        for item in data:
            if isinstance(item, Mapping):
                output.append({
                    humanize_field_name(k, language=language): translate_value(v, language=language, show_technical=show_technical, field_name=k)
                    for k, v in item.items() if show_technical or not is_technical_column(k)
                })
            else:
                output.append(translate_value(item, language=language, show_technical=show_technical))
        return output
    if isinstance(data, Mapping):
        return {
            humanize_field_name(k, language=language): translate_value(v, language=language, show_technical=show_technical, field_name=k)
            for k, v in data.items() if show_technical or not is_technical_column(k)
        }
    return translate_value(data, language=language, show_technical=show_technical)


def residual_bg_tokens(text: str) -> list[str]:
    visible = re.sub(r"<[^>]+>", " ", text)
    visible = re.sub(r"`[^`]*`", " ", visible)
    lowered = visible.lower()
    return sorted({token for token in FORBIDDEN_BG_UI_TOKENS if token in lowered})


def inject_global_css(st_module: Any) -> None:
    css = """
    <style>
    [data-testid="stAppDeployButton"],
    [data-testid="stToolbar"],
    [data-testid="stToolbarActions"],
    [data-testid="stHeaderActionElements"],
    .stDeployButton,
    header button[aria-label="Deploy"],
    header button[title="Deploy"],
    header a[href*="share.streamlit.io"],
    #MainMenu,
    footer { display: none !important; }
    [data-testid="stMetricLabel"] { line-height: 1.25; white-space: normal !important; }
    [data-testid="stMetricValue"] { overflow: visible !important; }
    [data-testid="stMetricValue"] > div {
        font-size: clamp(1.55rem, 2.6vw, 2.65rem) !important;
        line-height: 1.08 !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }
    [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
    .v150-tech-note {
        border-left: 3px solid rgba(212,175,55,.75);
        background: rgba(212,175,55,.07);
        border-radius: 10px;
        padding: .75rem .9rem;
        margin: .5rem 0 1rem;
        color: rgba(248,245,239,.78);
    }
    </style>
    """
    original = getattr(st_module, "_v150_original_markdown", None) or getattr(st_module, "markdown", None)
    if original is not None:
        try:
            original(css, unsafe_allow_html=True)
        except Exception:
            pass


def _translate_options(options: Iterable[Any], format_func: Callable[[Any], Any] | None, language: str) -> Callable[[Any], Any]:
    def formatter(value: Any) -> Any:
        rendered = format_func(value) if format_func is not None else value
        # LOTTERY_NUMERIC_SELECTBOX_FORMAT_FIX_V1
        if isinstance(rendered, str):
            return translate_text(rendered, language=language)
        return str(rendered)
    return formatter


def _wrap_module_method(st_module: Any, name: str, wrapper_factory: Callable[[Callable[..., Any]], Callable[..., Any]]) -> None:
    original = getattr(st_module, name, None)
    if original is None or getattr(original, "_v150_wrapped", False):
        return
    wrapped = wrapper_factory(original)
    setattr(wrapped, "_v150_wrapped", True)
    setattr(st_module, f"_v150_original_{name}", original)
    setattr(st_module, name, wrapped)


def _text_first_factory(st_module: Any, name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            language = current_language(st_module)
            args_list = list(args)
            if args_list and isinstance(args_list[0], str):
                args_list[0] = translate_text(args_list[0], language=language)
            for key in ("label", "placeholder", "help"):
                if isinstance(kwargs.get(key), str):
                    kwargs[key] = translate_text(kwargs[key], language=language)
            return original(*args_list, **kwargs)
        return wrapped
    return factory


def _choice_factory(st_module: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(label: Any, options: Any, *args: Any, **kwargs: Any) -> Any:
            language = current_language(st_module)
            original_format = kwargs.get("format_func")
            kwargs["format_func"] = _translate_options(options, original_format, language)
            if isinstance(label, str):
                label = translate_text(label, language=language)
            if isinstance(kwargs.get("help"), str):
                kwargs["help"] = translate_text(kwargs["help"], language=language)
            return original(label, options, *args, **kwargs)
        return wrapped
    return factory


def _data_factory(st_module: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(data: Any = None, *args: Any, **kwargs: Any) -> Any:
            language = current_language(st_module)
            show_technical = technical_details_enabled(st_module)
            localized = localize_table(data, language=language, show_technical=show_technical)
            column_config = kwargs.get("column_config")
            if isinstance(column_config, dict):
                kwargs["column_config"] = {
                    humanize_field_name(key, language=language): value
                    for key, value in column_config.items()
                    if show_technical or not is_technical_column(key)
                }
            return original(localized, *args, **kwargs)
        return wrapped
    return factory



def _json_factory(st_module: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(body: Any = None, *args: Any, **kwargs: Any) -> Any:
            language = current_language(st_module)
            show_technical = technical_details_enabled(st_module)
            if show_technical:
                return original(body, *args, **kwargs)
            localized = localize_table(body, language=language, show_technical=False)
            return original(localized, *args, **kwargs)
        return wrapped
    return factory


def _dg_json_factory(st_module: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(self: Any, body: Any = None, *args: Any, **kwargs: Any) -> Any:
            language = current_language(st_module)
            show_technical = technical_details_enabled(st_module)
            if show_technical:
                return original(self, body, *args, **kwargs)
            localized = localize_table(body, language=language, show_technical=False)
            return original(self, localized, *args, **kwargs)
        return wrapped
    return factory


def _dg_text_factory(st_module: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
            language = current_language(st_module)
            args_list = list(args)
            if args_list and isinstance(args_list[0], str):
                args_list[0] = translate_text(args_list[0], language=language)
            for key in ("label", "placeholder", "help"):
                if isinstance(kwargs.get(key), str):
                    kwargs[key] = translate_text(kwargs[key], language=language)
            return original(self, *args_list, **kwargs)
        return wrapped
    return factory


def _dg_choice_factory(st_module: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(self: Any, label: Any, options: Any, *args: Any, **kwargs: Any) -> Any:
            language = current_language(st_module)
            original_format = kwargs.get("format_func")
            kwargs["format_func"] = _translate_options(options, original_format, language)
            if isinstance(label, str):
                label = translate_text(label, language=language)
            if isinstance(kwargs.get("help"), str):
                kwargs["help"] = translate_text(kwargs["help"], language=language)
            return original(self, label, options, *args, **kwargs)
        return wrapped
    return factory


def _dg_data_factory(st_module: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(self: Any, data: Any = None, *args: Any, **kwargs: Any) -> Any:
            language = current_language(st_module)
            show_technical = technical_details_enabled(st_module)
            localized = localize_table(data, language=language, show_technical=show_technical)
            column_config = kwargs.get("column_config")
            if isinstance(column_config, dict):
                kwargs["column_config"] = {
                    humanize_field_name(key, language=language): value
                    for key, value in column_config.items()
                    if show_technical or not is_technical_column(key)
                }
            return original(self, localized, *args, **kwargs)
        return wrapped
    return factory

def _install_on_object(obj: Any, st_module: Any) -> None:
    if obj is None or getattr(obj, "_v150_object_patch", False):
        return
    text_methods = (
        "title", "header", "subheader", "markdown", "caption", "info", "warning", "success", "error",
        "button", "checkbox", "toggle", "text_input", "text_area", "number_input", "slider", "select_slider",
        "file_uploader", "download_button", "form_submit_button", "expander", "date_input", "time_input", "toast",
    )
    for name in text_methods:
        original = getattr(obj, name, None)
        if original is None or getattr(original, "_v150_wrapped", False):
            continue
        wrapped = _text_first_factory(st_module, name)(original)
        setattr(wrapped, "_v150_wrapped", True)
        try:
            setattr(obj, name, wrapped)
        except Exception:
            pass
    for name in ("radio", "selectbox", "multiselect", "segmented_control", "pills"):
        original = getattr(obj, name, None)
        if original is None or getattr(original, "_v150_wrapped", False):
            continue
        wrapped = _choice_factory(st_module)(original)
        setattr(wrapped, "_v150_wrapped", True)
        try:
            setattr(obj, name, wrapped)
        except Exception:
            pass
    for name in ("dataframe", "table", "data_editor"):
        original = getattr(obj, name, None)
        if original is None or getattr(original, "_v150_wrapped", False):
            continue
        wrapped = _data_factory(st_module)(original)
        setattr(wrapped, "_v150_wrapped", True)
        try:
            setattr(obj, name, wrapped)
        except Exception:
            pass
    try:
        setattr(obj, "_v150_object_patch", True)
    except Exception:
        pass


def install_global_ui_polish(st_module: Any | None = None) -> None:
    if st_module is None:
        import streamlit as st_module  # type: ignore
    if getattr(st_module, "_v150_global_ui_polish_installed", False):
        return

    # Prevent the two legacy partial localization patches from wrapping the new layer again.
    setattr(st_module, "_lottery_bulgarian_final_clean_v36", True)
    setattr(st_module, "_bg_table_patch_installed", True)

    text_methods = (
        "title", "header", "subheader", "markdown", "caption", "info", "warning", "success", "error",
        "button", "checkbox", "toggle", "text_input", "text_area", "number_input", "slider", "select_slider",
        "file_uploader", "download_button", "form_submit_button", "expander", "date_input", "time_input", "toast",
        "spinner",
    )
    for name in text_methods:
        _wrap_module_method(st_module, name, _text_first_factory(st_module, name))

    for name in ("radio", "selectbox", "multiselect", "segmented_control", "pills"):
        _wrap_module_method(st_module, name, _choice_factory(st_module))

    for name in ("dataframe", "table", "data_editor"):
        _wrap_module_method(st_module, name, _data_factory(st_module))
    _wrap_module_method(st_module, "json", _json_factory(st_module))

    # Special widgets with more than one visible text argument.
    original_metric = getattr(st_module, "metric", None)
    if original_metric is not None and not getattr(original_metric, "_v150_wrapped", False):
        @wraps(original_metric)
        def metric(label: Any, value: Any, delta: Any = None, *args: Any, **kwargs: Any) -> Any:
            language = current_language(st_module)
            return original_metric(
                translate_text(label, language=language),
                translate_value(value, language=language, show_technical=technical_details_enabled(st_module)),
                translate_value(delta, language=language, show_technical=technical_details_enabled(st_module)),
                *args,
                **kwargs,
            )
        metric._v150_wrapped = True  # type: ignore[attr-defined]
        st_module._v150_original_metric = original_metric
        st_module.metric = metric

    original_tabs = getattr(st_module, "tabs", None)
    if original_tabs is not None and not getattr(original_tabs, "_v150_wrapped", False):
        @wraps(original_tabs)
        def tabs(labels: Iterable[Any], *args: Any, **kwargs: Any) -> Any:
            language = current_language(st_module)
            return original_tabs([translate_text(label, language=language) if isinstance(label, str) else label for label in labels], *args, **kwargs)
        tabs._v150_wrapped = True  # type: ignore[attr-defined]
        st_module._v150_original_tabs = original_tabs
        st_module.tabs = tabs

    original_write = getattr(st_module, "write", None)
    if original_write is not None and not getattr(original_write, "_v150_wrapped", False):
        @wraps(original_write)
        def write(*args: Any, **kwargs: Any) -> Any:
            language = current_language(st_module)
            localized = [translate_text(item, language=language) if isinstance(item, str) else localize_table(item, language=language) for item in args]
            return original_write(*localized, **kwargs)
        write._v150_wrapped = True  # type: ignore[attr-defined]
        st_module._v150_original_write = original_write
        st_module.write = write

    # Sidebar and column/container widgets use DeltaGenerator methods rather than module-level functions.
    try:
        from streamlit.delta_generator import DeltaGenerator  # type: ignore
        for name in text_methods:
            original = getattr(DeltaGenerator, name, None)
            if original is None or getattr(original, "_v150_wrapped", False):
                continue
            wrapped = _dg_text_factory(st_module)(original)
            setattr(wrapped, "_v150_wrapped", True)
            setattr(DeltaGenerator, name, wrapped)
        for name in ("radio", "selectbox", "multiselect", "segmented_control", "pills"):
            original = getattr(DeltaGenerator, name, None)
            if original is None or getattr(original, "_v150_wrapped", False):
                continue
            wrapped = _dg_choice_factory(st_module)(original)
            setattr(wrapped, "_v150_wrapped", True)
            setattr(DeltaGenerator, name, wrapped)
        for name in ("dataframe", "table", "data_editor"):
            original = getattr(DeltaGenerator, name, None)
            if original is None or getattr(original, "_v150_wrapped", False):
                continue
            wrapped = _dg_data_factory(st_module)(original)
            setattr(wrapped, "_v150_wrapped", True)
            setattr(DeltaGenerator, name, wrapped)
        original_dg_json = getattr(DeltaGenerator, "json", None)
        if original_dg_json is not None and not getattr(original_dg_json, "_v150_wrapped", False):
            wrapped = _dg_json_factory(st_module)(original_dg_json)
            setattr(wrapped, "_v150_wrapped", True)
            setattr(DeltaGenerator, "json", wrapped)

        original_dg_metric = getattr(DeltaGenerator, "metric", None)
        if original_dg_metric is not None and not getattr(original_dg_metric, "_v150_wrapped", False):
            @wraps(original_dg_metric)
            def dg_metric(self: Any, label: Any, value: Any, delta: Any = None, *args: Any, **kwargs: Any) -> Any:
                language = current_language(st_module)
                return original_dg_metric(
                    self,
                    translate_text(label, language=language),
                    translate_value(value, language=language, show_technical=technical_details_enabled(st_module)),
                    translate_value(delta, language=language, show_technical=technical_details_enabled(st_module)),
                    *args,
                    **kwargs,
                )
            dg_metric._v150_wrapped = True  # type: ignore[attr-defined]
            setattr(DeltaGenerator, "metric", dg_metric)

        original_dg_tabs = getattr(DeltaGenerator, "tabs", None)
        if original_dg_tabs is not None and not getattr(original_dg_tabs, "_v150_wrapped", False):
            @wraps(original_dg_tabs)
            def dg_tabs(self: Any, labels: Iterable[Any], *args: Any, **kwargs: Any) -> Any:
                language = current_language(st_module)
                return original_dg_tabs(self, [translate_text(label, language=language) if isinstance(label, str) else label for label in labels], *args, **kwargs)
            dg_tabs._v150_wrapped = True  # type: ignore[attr-defined]
            setattr(DeltaGenerator, "tabs", dg_tabs)

        original_dg_write = getattr(DeltaGenerator, "write", None)
        if original_dg_write is not None and not getattr(original_dg_write, "_v150_wrapped", False):
            @wraps(original_dg_write)
            def dg_write(self: Any, *args: Any, **kwargs: Any) -> Any:
                language = current_language(st_module)
                localized = [translate_text(item, language=language) if isinstance(item, str) else localize_table(item, language=language) for item in args]
                return original_dg_write(self, *localized, **kwargs)
            dg_write._v150_wrapped = True  # type: ignore[attr-defined]
            setattr(DeltaGenerator, "write", dg_write)
    except Exception:
        # Tests and older Streamlit versions may not expose DeltaGenerator here.
        pass

    _install_on_object(getattr(st_module, "sidebar", None), st_module)
    setattr(st_module, "_v150_global_ui_polish_installed", True)
    inject_global_css(st_module)

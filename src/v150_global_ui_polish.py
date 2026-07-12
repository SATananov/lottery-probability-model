from __future__ import annotations

import re
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Iterable, Mapping


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

TECHNICAL_COLUMN_MARKERS: tuple[str, ...] = (
    "sha256", "_hash", "hash_", "signature", "previous_event", "configuration_",
    "dataset_", "code_", "artifact_path", "source_summary", "created_at_utc",
    "updated_at_utc", "generated_at_utc", "last_evaluated_at_utc", "locked_at_utc",
    "settled_at_utc", "event_id", "experiment_id", "decision_id", "protocol_id", "lock_id",
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


def translate_value(value: Any, *, language: str | None = None) -> Any:
    if not isinstance(value, str):
        return value
    language = language or current_language()
    raw = value.strip()
    if not raw:
        return value
    if language == "bg":
        mapped = VALUE_LABELS_BG.get(raw.lower())
        if mapped is not None:
            return mapped
    return translate_text(value, language=language)


def humanize_field_name(name: Any, *, language: str | None = None) -> str:
    language = language or current_language()
    raw = str(name)
    if language == "bg":
        if raw in FIELD_LABELS_BG:
            return FIELD_LABELS_BG[raw]
        words = [FIELD_WORDS_BG.get(token.lower(), token) for token in re.split(r"[_\s]+", raw) if token]
        result = " ".join(words).strip()
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
                    lambda item, field=str(source_col): translate_value(_format_timestamp(item, field), language=language)
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
                output.append({humanize_field_name(k, language=language): translate_value(v, language=language) for k, v in item.items() if show_technical or not is_technical_column(k)})
            else:
                output.append(translate_value(item, language=language))
        return output
    if isinstance(data, Mapping):
        return {humanize_field_name(k, language=language): translate_value(v, language=language) for k, v in data.items() if show_technical or not is_technical_column(k)}
    return data


def residual_bg_tokens(text: str) -> list[str]:
    visible = re.sub(r"<[^>]+>", " ", text)
    visible = re.sub(r"`[^`]*`", " ", visible)
    lowered = visible.lower()
    return sorted({token for token in FORBIDDEN_BG_UI_TOKENS if token in lowered})


def inject_global_css(st_module: Any) -> None:
    css = """
    <style>
    [data-testid="stAppDeployButton"],
    [data-testid="stToolbarActions"],
    #MainMenu,
    footer { display: none !important; }
    [data-testid="stMetricLabel"] { line-height: 1.25; }
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
        return translate_text(rendered, language=language) if isinstance(rendered, str) else rendered
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

    # Special widgets with more than one visible text argument.
    original_metric = getattr(st_module, "metric", None)
    if original_metric is not None and not getattr(original_metric, "_v150_wrapped", False):
        @wraps(original_metric)
        def metric(label: Any, value: Any, delta: Any = None, *args: Any, **kwargs: Any) -> Any:
            language = current_language(st_module)
            return original_metric(
                translate_text(label, language=language),
                translate_value(value, language=language),
                translate_value(delta, language=language),
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

        original_dg_metric = getattr(DeltaGenerator, "metric", None)
        if original_dg_metric is not None and not getattr(original_dg_metric, "_v150_wrapped", False):
            @wraps(original_dg_metric)
            def dg_metric(self: Any, label: Any, value: Any, delta: Any = None, *args: Any, **kwargs: Any) -> Any:
                language = current_language(st_module)
                return original_dg_metric(
                    self,
                    translate_text(label, language=language),
                    translate_value(value, language=language),
                    translate_value(delta, language=language),
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

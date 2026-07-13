# История на завършените стъпки

Всички пътища в този документ са спрямо основната директория на проекта.

## Step 141

Step 141 добавя:

- проверка за чиста Python среда;
- синхронизиран README и release metadata;
- директно декларирана `altair` dependency;
- граници за съвместимост за пакетите за изпълнение и фиксиран `scikit-learn==1.8.0` за наличните моделни артефакти;
- премахване на локалната `.r-lib` библиотека и излишните checkpoint manifests;
- проверка за временни файлове и нежелани служебни обозначения от използвани инструменти;
- нов manifest на чистия ZIP архив с SHA-256 checksums.

Подробности: `reports/STEP_141_CLEAN_ENVIRONMENT_AND_DOCUMENTATION_SYNC.md`.

## Step 143

След успешно прилагане на нов официален тираж проектът автоматично обновява R статистическия анализ, статистическите характеристики, решението за игра и двата фиш пакета. Финалната проверката за актуалност потвърждава синхронизацията.

Тежкото ML преобучение не се изпълнява автоматично и остава отделна ръчна операция.

Подробности: `reports/STEP_143_AUTOMATIC_LIGHTWEIGHT_DOWNSTREAM_REFRESH_AFTER_OFFICIAL_DRAW.md`.

## Step 143.1

Step 143.1 подобрява описанието на личния експериментален контекст, езиковата последователност и целостта на release пакета. Коригирани са видимо повредени смесени изречения в генератори и артефакти, а verification пътищата на Step 122 и Step 125 са направени read-only при тестово изпълнение.

Добавен е и критичен research note за непрекъснати невронни динамични системи. Методът не е внедрен в проекта и е оставен само като възможна бъдеща експериментална посока.

Подробности:

- `docs/PROJECT_CONTEXT.md`
- `reports/STEP_143_1_PERSONAL_PROJECT_DOCUMENTATION_LANGUAGE_AND_RELEASE_INTEGRITY.md`
- `reports/RESEARCH_NOTE_NEURAL_DYNAMICAL_SYSTEMS_REFERENCE.md`

## Step 143.2

Step 143.2 добавя контролиран audit за GitHub синхронизацията след нов официален тираж. Преди запис се заснема Git baseline, staging се ограничава до одобрения `data/models/reports` scope, а личният дневник, secrets, backups и несвързани локални промени не се включват.

След push локалният `HEAD` се сравнява с SHA, върнат от remote branch-а. Резултатът се пази като локален runtime audit в `reports/runtime/v143_2_git_sync/`; тази директория е изключена от Git, за да не оставя working tree мръсен след успешен sync.

Подробности: `reports/STEP_143_2_OFFICIAL_DRAW_GITHUB_SYNC_VALIDATION_AND_AUDIT.md`.

Read-only проверка от терминала:

```powershell
python tools/check_official_draw_github_sync.py
```

При локален commit с неуспешен push:

```powershell
python tools/check_official_draw_github_sync.py --retry-push
```

## Step 143.3

Step 143.3 добавя финално downstream обновяване до **нулеви блокери**. Операцията се приема за успешна само когато Step 122 потвърди `overall_status = synced` и `blocking_out_of_sync_count = 0`.

Статистическият слой вече се стартира през cross-platform launcher. При наличен `Rscript` се използват оригиналните R скриптове; при липса се използва ясно обозначен детерминиран Python compatibility runner. Тежките ML модели не се преобучават, а личният SQLite дневник се защитава чрез byte-for-byte snapshot и restore.

Команди:

```powershell
python .\tools\run_downstream_zero_blocker_closure.py --strict
python .\scripts\verify_step_143_3.py
```

Подробности: `reports/STEP_143_3_FINAL_DOWNSTREAM_FRESHNESS_REPAIR_AND_ZERO_BLOCKER_CLOSURE.md`.

## Step 144

Step 144 добавя регистър на възпроизводимите експерименти и начална baseline лаборатория. Всеки експеримент заключва dataset SHA-256, последен тираж, configuration, random seed, walk-forward split, code hash, среда, резултати, artifacts и заключение.

Първият експеримент сравнява frequency baseline с множество uniform-random baseline опити върху хронологичен holdout. Target тиражът се добавя в историята едва след оценяването му, което защитава от future-data leakage.

Команди:

```powershell
python .\tools\run_reproducible_baseline_experiment.py
python .\tools\run_reproducible_baseline_experiment.py --read-only
python .\scripts\verify_step_144.py
```

Подробности: `reports/STEP_144_REPRODUCIBLE_EXPERIMENT_REGISTRY_AND_BASELINE_LABORATORY.md`.

## Step 145

Step 145 добавя изолиран neural dynamics sandbox. Реализацията използва детерминиран leaky reservoir с walk-forward ridge readout и го сравнява срещу frequency, recency-weighted и uniform-random baselines при еднакъв брой комбинации.

Експериментът е research-only. Той не е свързан с production pipeline или с генератора на реални фишове. Първият регистриран резултат не преминава promotion gate и е запазен като отрицателно експериментално доказателство.

Команди:

```powershell
python .\tools\run_experimental_neural_dynamics.py
python .\tools\run_experimental_neural_dynamics.py --read-only
python .\scripts\verify_step_145.py
```

Подробности: `reports/STEP_145_EXPERIMENTAL_NEURAL_DYNAMICS_SANDBOX_AND_BASELINE_COMPARISON.md`.

## Step 145.1

Step 145.1 поправя release metadata и volatile runtime артефактите. Всички finalizer-и от Step 143.3 нататък използват единен release policy, който изключва `.git`, локални среди, caches, runtime storage, secrets, ZIP/log/backup файлове и build artifacts. Manifest проверката вече отказва забранени пътища и валидира size, SHA-256, duplicates, stale и unlisted записи.

Step 122, Step 123 и Step 126 пазят текущите timestamps и diagnostics в Git-ignored `reports/runtime/v145_1_artifact_integrity/`. Tracked operational snapshots се обновяват само при реална semantic промяна, а идентична startup проверка вече не добавя нов canonical audit ред. Dataset SHA за Step 144/145 е стабилизиран между Windows CRLF и Linux LF checkout, без промяна на запазените experiment signatures.

Команди:

```powershell
python .\scripts\verify_step_145_1.py
python .\tools\finalize_step_145_1_release.py --verify-only
python .\tools\finalize_step_145_1_release.py --build-zip
```

Подробности: `reports/STEP_145_1_CLEAN_RELEASE_METADATA_RUNTIME_ARTIFACT_INTEGRITY_REPAIR.md`.

## Step 146

Step 146 разширява neural dynamics sandbox-а с контролирана robustness проверка: 3 неприпокриващи се исторически walk-forward периода по 120 тиража и 5 random seeds, или общо 15 runs. Добавени са recent-window frequency и frequency–recency blend baselines, 95% bootstrap confidence intervals, exact sign tests и stability проверки по seed и период.

Първият регистриран Step 146 резултат е сравнително стабилен между seed-овете, но не показва устойчиво превъзходство. Neural mean е `2.012222`, а uniform-random mean е `2.073611`; 95% CI на neural-minus-random разликата е изцяло под нулата. Promotion gate остава блокиран и няма production интеграция.

Команди:

```powershell
python .\tools\run_controlled_neural_robustness.py
python .\tools\run_controlled_neural_robustness.py --read-only
python .\scripts\verify_step_146.py
python .\tools\finalize_step_146_release.py --verify-only
```

Подробности: `reports/STEP_146_CONTROLLED_NEURAL_EXPERIMENT_EXPANSION_AND_ROBUSTNESS_VALIDATION.md`.


## Step 147

Step 147 обединява експерименталните доказателства от Step 144–146 в отделен research decision registry и machine-readable evidence matrix. Слоят проверява source signatures, dataset identity, leakage guardrails и promotion gates, без да преизпълнява тежко обучение и без да използва production pipeline или личния дневник.

Официалното решение е: production promotion остава `BLOCKED`, текущата neural конфигурация е `PAUSE_AND_ARCHIVE`, а повторно настройване върху вече видените holdout периоди е забранено. Следващ експеримент е допустим само при материално нова предварително регистрирана хипотеза, ясна primary metric/gate рамка и нов или недокоснат validation период.

## Step 148

Step 148 започва истински prospective forward-test прозорец върху бъдещи официални тиражи. Step 146 алгоритъмът, random seeds и параметрите са замразени, а Step 147 production block остава активен. Преди следващият тираж да влезе в canonical dataset се записва pre-draw lock с dataset SHA-256, target sequence, evaluation packages и immutable forecast signature.

Ledger-ът е append-only по operating policy и всеки event е свързан с предишния чрез SHA-256. Тиражи без валиден предварителен lock се изключват и никога не се backfill-ват. Протоколът цели 30 допустими бъдещи тиража с междинни milestone отчети след 10 и 20 и финален research decision след 30. Няма автоматично production promotion.

Команди:

```powershell
python .\tools\lock_next_draw_forecast.py
python .\tools\settle_locked_draw_forecast.py
python .\scripts\verify_step_148.py
python .\tools\finalize_step_148_release.py --verify-only
```

Подробности: `reports/STEP_148_PROSPECTIVE_FORWARD_TEST_LOCK_AND_UNTOUCHED_FUTURE_DRAW_LEDGER.md`.

## Step 149

Step 149 почиства текущото repository дърво без пренаписване на Git историята. Личният journal е изключен от tracking и release пакетите; raw source aliases и timestamp-only model snapshots са консолидирани; големите row-level Markdown backtest таблици са заменени с компактни възпроизводими summaries; добавена е ясна декларация за авторство и инструментална прозрачност.

Историческите `.r-lib`, journal и backup blobs остават предмет на отделна, изрично одобрена Step 149.1 операция за history rewrite.

## Step 150

Step 150 прилага глобално потребителско почистване върху целия Streamlit интерфейс. Единният display-only слой обхваща страничното меню, всички страници и модули, стандартните widgets, колоните/контейнерите и таблиците. Българският режим показва човешки наименования без смесени английски developer термини, а status/method стойностите и snake_case колоните се превеждат само за визуализация.

Вътрешните ID, SHA-256 подписи, UTC полета, configuration/code identities и artifact paths са скрити по подразбиране и могат да бъдат върнати чрез превключвателя **„Технически подробности“**. Изследователските страници 144–148 са преместени в отделна група **„Изследователски проверки“** и техническите им блокове са прибрани в затворени секции. `Deploy` и служебният Streamlit chrome са скрити от нормалния потребителски изглед.

Стъпката не променя данните, моделното обучение, production scoring или активния Step 148 lock за `2026-54`.

Команди:

```powershell
python .\tools\audit_ui_language_integrity.py
python .\scripts\verify_step_150.py
python .\tools\finalize_step_150_release.py --verify-only
```

Подробности: `reports/STEP_150_GLOBAL_BULGARIAN_UI_TABLE_LOCALIZATION_AND_TECHNICAL_DETAIL_SEPARATION.md`.

## Step 150.1 — Задълбочена локализация на динамичния интерфейс

След визуална проверка на всички изследователски и операторски страници е добавен втори глобален езиков слой. Той превежда динамичните стойности от JSON/CSV, всички заглавия на таблици, вътрешните имена на методи и липсващите стойности. Техническите идентификатори, SHA-256 подписи, пътища и UTC полета остават достъпни чрез „Технически подробности“, но са скрити в нормалния потребителски изглед. Промяната е само визуална и не променя моделите, оценяването или активното заключване за бъдещ тираж.

## Step 150.2 — Ясен български потребителски език

Step 150.2 премахва остатъчните смесени и машинно звучащи текстове от нормалния потребителски изглед. Условията за решение, изискванията за следващ експеримент и изводите от сравненията вече се показват като пълни и ясни български изречения. Таблиците в изследователските етапи 145–147 са разделени на кратко потребителско обобщение и отделна секция за статистически и технически подробности.

Глобалният визуален слой вече блокира непознати английски динамични стойности в български режим, локализира всички открити ключове и заглавия и проверява активните UI файлове със строго UTF-8 декодиране. Промяната е само визуална и не засяга моделите, оценяването, личния дневник или активното заключване за бъдещ тираж.

Команди:

```powershell
python .\tools\audit_plain_language_ui.py
python .\scripts\verify_step_150_2.py
python .\tools\finalize_step_150_2_release.py --verify-only
```

Подробности: `reports/STEP_150_2_PLAIN_BULGARIAN_USER_LANGUAGE_AND_COMPLETE_TECHNICAL_SEPARATION.md`.

## Step 150.3 — Премахване на вътрешните V-номера от потребителския изглед

Step 150.3 премахва вътрешните означения като `V1`, `v41`, `v94` и сходните номера на разработки от нормалния потребителски интерфейс. Те се заменят с ясни понятия като „работен процес“, „финално заключване“, „активен план“ и „пълно обновяване на моделите“. Точните версии, файлови пътища и машинни идентификатори остават достъпни само при включени **„Технически подробности“**.

Промяната е глобална и обхваща съобщения, метрики, таблици, динамични JSON/CSV стойности и обяснителни полета във всички активни модули. Тя е само визуална и не засяга моделите, оценяването, личния дневник или активното заключване за бъдещ тираж.

Команди:

```powershell
python .\tools\audit_user_version_labels.py
python .\scripts\verify_step_150_3.py
python .\tools\finalize_step_150_3_release.py --verify-only
```

Подробности: `reports/STEP_150_3_USER_FRIENDLY_INTERNAL_VERSION_LABEL_CLEANUP.md`.

## Step 151 — Repository Root Cleanup & Post-Draw Documentation Sync

Step 151 подрежда основната директория след официалния тираж `2026-54`. Остарелите междинни CLEAN manifest файлове са премахнати от текущото дърво, като историята им остава в Git. Помощната документация е преместена в `docs/`, а `README.md` и ръководството за интерфейса са синхронизирани с `10064` реда, тираж `54` и активен следващ тираж `2026-55`.

Стъпката е документационна и release-oriented. Тя не променя данните, моделите, scoring алгоритмите, Step 148 ledger-а или личния journal.


# Step 143.2 — Official Draw → GitHub Sync Validation & Audit

## Цел

Step 143.2 доказва какво се случва след локално добавяне на официален тираж. Системата вече не приема, че успешният `git push` е достатъчен. Тя проверява конкретния локален commit срещу SHA на текущия remote branch.

## Контролиран процес

1. Преди запис се заснема read-only Git baseline.
2. Автоматичният sync се блокира при предварително staged файлове.
3. Автоматичният sync се блокира при неприключени промени в неговия собствен scope.
4. След тиража се определят файловете, създадени или променени от refresh веригата.
5. Staging се ограничава до одобрения data/models/reports scope.
6. Личният дневник, secrets, backups и други локални файлове остават изключени.
7. Създава се commit за конкретния тираж.
8. Commit-ът се push-ва към текущия branch на `origin`.
9. `git ls-remote` връща remote SHA и той се сравнява с локалния `HEAD`.
10. Локален runtime audit записва резултата, без да замърсява Git working tree.

## Разрешен sync scope

```text
data/historical_draws.csv
data/v40_normalized_draw_events.csv
data/v41_canonical_draw_events.csv
models/
reports/
```

Runtime audit директорията `reports/runtime/v143_2_git_sync/` е изключена от този scope.

## Защитени локални данни

Автоматично не се добавят:

```text
data/user_journal.db
data/user_journal_exports/
data/manual_backups/
.env
.env.*
.streamlit/secrets.toml
reports/runtime/v143_2_git_sync/
```

Ако някой от тези файлове е променен, той се показва като изключен локален файл, но не влиза в commit-а.

## Статуси

- `remote_confirmed` — локалният и remote commit SHA съвпадат.
- `nothing_to_commit_remote_confirmed` — няма нов commit, но текущият HEAD е потвърден remote.
- `local_commit_pending_push` — commit има локално, но push не е завършил.
- `remote_confirmation_failed` — remote SHA не може да бъде прочетен.
- `remote_mismatch` — remote branch сочи към друг commit.
- `preexisting_staged_changes` — автоматичният commit е блокиран заради предварително staged файлове.
- `preexisting_sync_scope_changes` — data/models/reports съдържат стари неприключени промени.

## Граници

Step 143.2 не променя математическата логика, не преобучава тежки модели и не твърди, че GitHub е резервно копие на личния дневник. Runtime audit-ът е локална оперативна следа; Git remote commit е независимото потвърждение за качените публични project artifacts.

## Release manifest policy

`release-manifest.json` и CLEAN checkpoint manifest файловете не са live operational artifacts. Те не се обновяват при всеки тираж и не се включват в автоматичния draw commit. Регенерират се само при затваряне на нов FULL CLEAN checkpoint, след като working tree е прегледан и потвърден.

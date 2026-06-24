# Step 103 — Clean ZIP checkpoint

Статус: **WAITING_FOR_CLEAN_GIT_STATUS**
Commit: `467090e`
Tracked files: **909**
Forbidden tracked files: **0**

## Препоръчано действие

След като `git status --short` е празен:

```powershell
python .\scripts\v103_create_clean_release_checkpoint.py
```

## Бележки

- Normal folder ZIP is not safe for this project because it can include .git, __pycache__, .pyc and helper scripts.
- The clean checkpoint script uses git tracked files only and refuses to create the ZIP while git status is not clean.
- Run the clean ZIP script after committing Step 103/104.

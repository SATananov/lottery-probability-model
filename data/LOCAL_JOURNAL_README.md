# Local journal privacy

`data/user_journal.db` and `data/user_journal_exports/` contain personal play history. They are created and used locally, ignored by Git, and excluded from release manifests and clean ZIP archives.

The application initializes a new empty SQLite database automatically on first use. `data/user_journal_schema.sql` documents the public schema without including personal rows.

When replacing the project from a clean ZIP, restore your own journal files only from a trusted local backup after `.git` and `.venv` are restored.

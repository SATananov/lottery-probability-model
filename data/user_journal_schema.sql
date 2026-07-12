PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS journal_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_draw_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_key TEXT NOT NULL UNIQUE,
    draw_date TEXT NOT NULL,
    draw_number TEXT,
    drawing_position TEXT,
    n1 INTEGER NOT NULL, n2 INTEGER NOT NULL, n3 INTEGER NOT NULL,
    n4 INTEGER NOT NULL, n5 INTEGER NOT NULL, n6 INTEGER NOT NULL,
    numbers_text TEXT NOT NULL,
    entered_at_utc TEXT NOT NULL,
    source TEXT NOT NULL,
    note TEXT
);

CREATE TABLE IF NOT EXISTS played_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_key TEXT NOT NULL UNIQUE,
    saved_at_utc TEXT NOT NULL,
    play_date TEXT NOT NULL,
    target_draw_date TEXT,
    target_draw_number TEXT,
    mode TEXT NOT NULL,
    plan_id TEXT,
    plan_source TEXT,
    strategy_type TEXT,
    budget_eur REAL,
    price_per_line_eur REAL,
    total_price_eur REAL,
    line_count INTEGER NOT NULL,
    status TEXT NOT NULL,
    note TEXT
);

CREATE TABLE IF NOT EXISTS played_ticket_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    line_no INTEGER NOT NULL,
    source_ticket_id TEXT,
    role TEXT,
    n1 INTEGER NOT NULL, n2 INTEGER NOT NULL, n3 INTEGER NOT NULL,
    n4 INTEGER NOT NULL, n5 INTEGER NOT NULL, n6 INTEGER NOT NULL,
    numbers_text TEXT NOT NULL,
    price_eur REAL,
    played INTEGER NOT NULL DEFAULT 1,
    note TEXT,
    FOREIGN KEY(ticket_id) REFERENCES played_tickets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS played_ticket_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    draw_entry_id INTEGER NOT NULL,
    evaluated_at_utc TEXT NOT NULL,
    best_hits INTEGER NOT NULL,
    total_hits INTEGER NOT NULL,
    rows_with_hits INTEGER NOT NULL,
    rows_with_3_plus INTEGER NOT NULL,
    rows_with_4_plus INTEGER NOT NULL,
    matched_numbers_text TEXT NOT NULL,
    best_line_no INTEGER,
    note TEXT,
    UNIQUE(ticket_id, draw_entry_id),
    FOREIGN KEY(ticket_id) REFERENCES played_tickets(id) ON DELETE CASCADE,
    FOREIGN KEY(draw_entry_id) REFERENCES user_draw_entries(id) ON DELETE CASCADE
);

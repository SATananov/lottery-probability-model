# Step 131.1 — Live BST Timeout Interface Repair

The Step 131 dashboard called `detect_latest_official_draw()` with the unsupported keyword `timeout_seconds`.
The Step 123 detection engine accepts `timeout`.

The repair changes the call to `timeout=timeout_seconds` and adds a mocked live-branch regression assertion.

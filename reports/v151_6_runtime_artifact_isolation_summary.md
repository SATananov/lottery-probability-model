# Step 151.6 — Runtime Volatile Artifact Isolation and Clean Startup

- Normal Step 123 detection writes only under ignored `reports/runtime/`.
- Normal Step 126 startup automation writes only under ignored `reports/runtime/`.
- The seven committed detection/startup snapshots remain unchanged during application startup.
- Runtime state is read before the committed release snapshot.
- Publishing a tracked snapshot requires an explicit `publish_snapshot=True` call.
- No draw data, R output, Step 148 state or heavy model is changed.

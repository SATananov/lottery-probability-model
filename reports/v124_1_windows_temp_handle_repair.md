# Step 124.1 — Windows Temporary File Handle Repair

The original Step 124 implementation created temporary promotion files with
`tempfile.mkstemp()` but did not close the returned OS-level descriptors.
Windows therefore rejected replacement and cleanup with `WinError 32`.

The repair stores both descriptors and paths, closes the descriptors with
`os.close()`, then performs copy, atomic replacement, cleanup, and rollback.

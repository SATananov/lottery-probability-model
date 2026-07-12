from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "reports" / "runtime" / "v145_1_artifact_integrity"
DEFAULT_VOLATILE_KEYS = {
    "generated_at_utc",
    "checked_at_utc",
    "started_at_utc",
    "finished_at_utc",
}


def _normalized(value: Any, volatile_keys: set[str]) -> Any:
    if isinstance(value, dict):
        return {
            key: _normalized(child, volatile_keys)
            for key, child in sorted(value.items())
            if key not in volatile_keys
        }
    if isinstance(value, list):
        return [_normalized(child, volatile_keys) for child in value]
    return value


def semantic_signature(payload: Any, *, volatile_keys: Iterable[str] = ()) -> str:
    keys = set(DEFAULT_VOLATILE_KEYS)
    keys.update(volatile_keys)
    normalized = _normalized(payload, keys)
    encoded = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        Path(tmp_name).unlink(missing_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def write_text(path: Path, text: str) -> None:
    _atomic_write_text(path, text)


def canonical_json_needs_update(
    path: Path,
    payload: dict[str, Any],
    *,
    volatile_keys: Iterable[str] = (),
) -> bool:
    existing = load_json(path)
    if not existing:
        return True
    return semantic_signature(existing, volatile_keys=volatile_keys) != semantic_signature(
        payload, volatile_keys=volatile_keys
    )


def persist_json_pair(
    *,
    component: str,
    payload: dict[str, Any],
    canonical_paths: Iterable[Path],
    volatile_keys: Iterable[str] = (),
) -> bool:
    """Always update ignored runtime state; update tracked snapshots only on semantic change."""
    runtime_path = RUNTIME_ROOT / f"{component}.json"
    write_json(runtime_path, payload)
    canonical_paths = tuple(canonical_paths)
    changed = any(
        canonical_json_needs_update(path, payload, volatile_keys=volatile_keys)
        for path in canonical_paths
    )
    if changed:
        for path in canonical_paths:
            write_json(path, payload)
    return changed


def append_jsonl_if_signature_changed(
    path: Path,
    payload: dict[str, Any],
    *,
    signature_path: Path,
    volatile_keys: Iterable[str] = (),
) -> bool:
    signature = semantic_signature(payload, volatile_keys=volatile_keys)
    previous = signature_path.read_text(encoding="utf-8").strip() if signature_path.exists() else ""
    if signature == previous:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    write_text(signature_path, signature + "\n")
    return True

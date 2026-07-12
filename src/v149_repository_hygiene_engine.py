from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence, TypeVar

ROOT = Path(__file__).resolve().parents[1]
VOLATILE_MODEL_KEYS = {
    "created_at",
    "created_at_utc",
    "generated_at",
    "generated_at_utc",
    "saved_at",
    "saved_at_utc",
    "timestamp",
    "trained_at",
    "trained_at_utc",
}
T = TypeVar("T")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def head_tail_sample(rows: Sequence[T], *, head: int = 3, tail: int = 3) -> list[T]:
    if len(rows) <= head + tail:
        return list(rows)
    return list(rows[:head]) + list(rows[-tail:])


def _without_volatile_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_volatile_fields(item)
            for key, item in value.items()
            if key not in VOLATILE_MODEL_KEYS
        }
    if isinstance(value, list):
        return [_without_volatile_fields(item) for item in value]
    return value


def semantic_payload_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        _without_volatile_fields(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def write_semantic_version_snapshot(
    payload: dict[str, Any],
    *,
    directory: Path,
    filename_prefix: str,
    timestamp_format: str = "%Y%m%d_%H%M%S",
) -> tuple[Path, bool]:
    """Write a model snapshot only when its semantic payload is new.

    Volatile creation timestamps are ignored for duplicate detection. Existing
    distinct states are retained; timestamp-only duplicates are not created.
    """
    directory.mkdir(parents=True, exist_ok=True)
    target_hash = semantic_payload_sha256(payload)
    for path in sorted(directory.glob(f"{filename_prefix}_*.json")):
        try:
            existing = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if isinstance(existing, dict) and semantic_payload_sha256(existing) == target_hash:
            return path, False

    stamp = datetime.now().strftime(timestamp_format)
    destination = directory / f"{filename_prefix}_{stamp}.json"
    if destination.exists():
        destination = directory / f"{filename_prefix}_{stamp}_{target_hash[:8]}.json"
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination, True


def deterministic_status_signature(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "result_signature_sha256"}
    canonical = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def exact_duplicate_groups(
    root: Path = ROOT,
    *,
    excluded_prefixes: Iterable[str] = (
        ".git/",
        ".venv/",
        "venv/",
        "reports/runtime/",
        "data/user_journal_exports/",
    ),
    excluded_paths: Iterable[str] = ("data/user_journal.db",),
) -> list[dict[str, Any]]:
    excluded_prefixes = tuple(excluded_prefixes)
    excluded_paths = set(excluded_paths)
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        if any(part in {".git", ".venv", "venv", ".r-lib", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        if path.suffix.lower() in {".pyc", ".pyo", ".zip", ".log", ".tmp", ".bak", ".backup"}:
            continue
        if relative in excluded_paths or relative.startswith(excluded_prefixes):
            continue
        if path.parent == root and (
            relative == "release-manifest.json"
            or (relative.startswith("CLEAN_ZIP_MANIFEST_STEP") and relative.endswith(".md"))
            or (relative.startswith("FULL_CLEAN_CHECKPOINT_MANIFEST_STEP") and relative.endswith(".md"))
        ):
            continue
        groups[sha256_file(path)].append(path)

    results: list[dict[str, Any]] = []
    for digest, paths in groups.items():
        if len(paths) < 2:
            continue
        size = paths[0].stat().st_size
        results.append(
            {
                "sha256": digest,
                "file_size_bytes": size,
                "copies": len(paths),
                "redundant_bytes": size * (len(paths) - 1),
                "paths": [path.relative_to(root).as_posix() for path in sorted(paths)],
            }
        )
    return sorted(results, key=lambda row: (row["redundant_bytes"], row["copies"]), reverse=True)


def repository_inventory(root: Path = ROOT) -> dict[str, Any]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        if any(part in {".git", ".venv", "venv", ".r-lib", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        if path.suffix.lower() in {".pyc", ".pyo", ".zip", ".log", ".tmp", ".bak", ".backup"}:
            continue
        if relative == "data/user_journal.db" or relative.startswith("data/user_journal_exports/") or relative.startswith("reports/runtime/"):
            continue
        if path.parent == root and (
            relative == "release-manifest.json"
            or (relative.startswith("CLEAN_ZIP_MANIFEST_STEP") and relative.endswith(".md"))
            or (relative.startswith("FULL_CLEAN_CHECKPOINT_MANIFEST_STEP") and relative.endswith(".md"))
        ):
            continue
        files.append(path)
    duplicate_groups = exact_duplicate_groups(root)
    return {
        "file_count": len(files),
        "size_bytes": sum(path.stat().st_size for path in files),
        "python_file_count": sum(path.suffix.lower() == ".py" for path in files),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_file_count": sum(int(row["copies"]) for row in duplicate_groups),
        "duplicate_redundant_bytes": sum(int(row["redundant_bytes"]) for row in duplicate_groups),
    }

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v151_4_controlled_prize_history_data_sync_engine import run_controlled_sync


def _configure_utf8_stream(stream: Any) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, OSError, ValueError):
            pass


def _emit_result(result: dict[str, Any]) -> None:
    text = json.dumps(result, ensure_ascii=False, indent=2)
    try:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
    except UnicodeEncodeError:
        # Last-resort fallback for legacy Windows code pages.
        sys.stdout.write(json.dumps(result, ensure_ascii=True, indent=2) + "\n")
        sys.stdout.flush()


def main() -> int:
    _configure_utf8_stream(sys.stdout)
    _configure_utf8_stream(sys.stderr)

    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()
    result = run_controlled_sync(
        plan_only=args.plan_only,
        timeout_seconds=args.timeout_seconds,
        write_outputs=True,
    )
    _emit_result(result)
    if args.plan_only:
        return 0 if result.get("status") == "planned" else 1
    return 0 if result.get("status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

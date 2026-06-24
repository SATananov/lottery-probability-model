from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v102_runtime_hardening_engine import write_runtime_hardening_artifacts


def main() -> None:
    summary = write_runtime_hardening_artifacts()
    print("STEP_102_STATUS", summary.get("status", "UNKNOWN"))
    print("BLOCKING_FAILURES", summary.get("blocking_failures", 0))
    print("DEFAULT_TIMEOUT_SECONDS", summary.get("default_timeout_seconds", 0))
    print("DEFAULT_REFRESH_MODE", summary.get("default_refresh_mode_bg", ""))


if __name__ == "__main__":
    main()

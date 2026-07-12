from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v149_repository_hygiene_engine import exact_duplicate_groups, repository_inventory


def main() -> int:
    payload = repository_inventory(ROOT)
    payload["largest_duplicate_groups"] = exact_duplicate_groups(ROOT)[:10]
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

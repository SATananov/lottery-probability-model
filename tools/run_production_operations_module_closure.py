from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v140_production_operations_module_closure_engine import (
    build_module_closure_status,
    module_closure_markdown,
    write_module_closure_status,
)


def main() -> int:
    parser = argparse.ArgumentParser(description='Step 140 production operations module closure check.')
    parser.add_argument('--write', action='store_true', help='Write closure status JSON and Markdown summary.')
    parser.add_argument('--json', action='store_true', help='Print JSON instead of Markdown.')
    args = parser.parse_args()

    status = build_module_closure_status()
    if args.write:
        write_module_closure_status(status)
    print(json.dumps(status, ensure_ascii=False, indent=2) if args.json else module_closure_markdown(status))
    return 0 if status['closure_ready'] else 2


if __name__ == '__main__':
    raise SystemExit(main())

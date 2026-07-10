from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v139_recovery_exception_management_summary_engine import (
    build_recovery_exception_management_summary,
    management_summary_csv,
    management_summary_markdown,
    write_recovery_exception_management_summary,
)


def main() -> None:
    parser = argparse.ArgumentParser(description='Build the read-only Step 139 recovery exception management summary.')
    parser.add_argument('--format', choices=('json', 'markdown', 'csv'), default='json')
    parser.add_argument('--write-status', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()

    status = build_recovery_exception_management_summary()
    if args.write_status:
        write_recovery_exception_management_summary(status)
    if args.format == 'markdown':
        content = management_summary_markdown(status)
    elif args.format == 'csv':
        content = management_summary_csv(status)
    else:
        content = json.dumps(status, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding='utf-8')
    else:
        print(content)


if __name__ == '__main__':
    main()

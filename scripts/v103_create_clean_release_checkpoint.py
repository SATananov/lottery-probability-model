from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v103_clean_release_checkpoint_engine import create_clean_release_checkpoint


def main() -> None:
    result = create_clean_release_checkpoint(require_clean_status=True)
    print("CLEAN_ZIP_CREATED", result["zip_path"])
    print("INCLUDED_FILES", result["included_files"])
    print("SKIPPED_FILES", result["skipped_files"])
    print("COMMIT", result["commit"])


if __name__ == "__main__":
    main()

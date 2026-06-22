from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v82_final_release_package_engine import build_final_release_package_center


if __name__ == "__main__":
    result = build_final_release_package_center()
    print("STEP82_BUILD_OK")
    print("STATUS", result.get("status"))
    print("REQUIRED_FILES_CHECKED", result.get("required_files_checked"))
    print("DATASETS_CHECKED", result.get("datasets_checked"))
    print("MANIFEST_FILES", result.get("manifest_files_count"))
    print("UNWANTED_RELEASE_FILES", result.get("unwanted_release_files"))
    print("ISSUES_FOUND", result.get("issues_found"))

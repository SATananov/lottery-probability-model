from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")

    require("частен локален експеримент" in readme.lower(), "README private-experiment note missing")
    require("2026-07-09" in readme and "10063" in readme, "README dataset state is not synchronized")
    require("altair" in requirements.lower(), "altair is not declared directly")
    require((ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.11", "Python version policy missing")
    require((ROOT / "tools" / "verify_clean_environment.py").exists(), "Clean environment verifier missing")
    require(not (ROOT / ".r-lib").exists(), "Bundled .r-lib must not be present")
    old_manifests = [p for p in ROOT.glob("CLEAN_ZIP_MANIFEST_STEP*.md") if int(re.search(r"STEP(\d+)", p.name).group(1)) < 141]
    require(not old_manifests, "Old root checkpoint manifests remain")

    # Text attribution cleanup is validated during release packaging.

    print("STEP_141_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

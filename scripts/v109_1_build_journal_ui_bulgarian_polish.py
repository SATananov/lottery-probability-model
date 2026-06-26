from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v109_1_journal_ui_bulgarian_polish_engine import build_step


if __name__ == "__main__":
    build_step()

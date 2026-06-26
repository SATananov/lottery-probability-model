from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v108_user_menu_live_status_sync_engine import build_step

if __name__ == "__main__":
    build_step()

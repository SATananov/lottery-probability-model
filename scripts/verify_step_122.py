from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v122_unified_official_draw_freshness_engine import build_freshness_report


report = build_freshness_report(write_outputs=False)
by_key = {source["key"]: source for source in report["sources"]}
assert report["official_latest_draw"]["draw_number"] == 53
assert by_key["canonical"]["status"] == "synced"
assert by_key["r_layer"]["status"] == "behind"
assert by_key["step121"]["status"] == "behind"
assert by_key["decision"]["status"] == "behind"
assert report["heavy_model_retraining_performed"] is False
print("STEP_122_VERIFY_OK")

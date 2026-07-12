from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v122_unified_official_draw_freshness_engine import build_freshness_report


report = build_freshness_report(write_outputs=False)
by_key = {source["key"]: source for source in report["sources"]}
assert int(report["official_latest_draw"]["draw_number"]) > 0
assert by_key["official"]["status"] == "synced"
assert by_key["canonical"]["status"] == "synced"
assert by_key["models"]["status"] == "informational"
assert by_key["models"]["draw_delta"] is None
blocking = [
    source for source in report["sources"]
    if source["key"] != "official" and source["status"] not in {"synced", "informational", "local_optional"}
]
assert report["blocking_out_of_sync_count"] == len(blocking)
assert report["overall_status"] == ("synced" if not blocking else "out_of_sync")
assert report["heavy_model_retraining_performed"] is False
print("STEP_122_VERIFY_OK")

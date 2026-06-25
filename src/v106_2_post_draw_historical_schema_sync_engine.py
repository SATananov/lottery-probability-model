from __future__ import annotations

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "reports" / "v106_2_post_draw_historical_schema_sync_summary.json"

def build_post_draw_historical_schema_sync():
    ns = runpy.run_path(str(ROOT / "scripts" / "v106_2_build_post_draw_historical_schema_sync.py"))
    return ns["build_step"]()

def load_post_draw_historical_schema_sync_summary():
    return json.loads(SUMMARY.read_text(encoding="utf-8-sig")) if SUMMARY.exists() else {}

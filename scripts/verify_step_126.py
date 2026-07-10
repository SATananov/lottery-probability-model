from __future__ import annotations
import tempfile
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.v126_startup_automation_engine import cache_is_fresh, run_startup_automation, save_config


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="step126_verify_") as tmp:
        root = Path(tmp)
        config_path = root / "config.json"
        cfg = save_config({
            "auto_check_enabled": True,
            "auto_apply_enabled": False,
            "auto_refresh_enabled": False,
            "cache_minutes": 30,
            "network_timeout_seconds": 9,
            "downstream_timeout_seconds": 120,
        }, config_path)
        assert cfg["auto_check_enabled"] is True
        assert cfg["auto_refresh_enabled"] is False

        calls = {"detect": 0, "ingest": 0, "refresh": 0}
        def detector(**kwargs):
            calls["detect"] += 1
            return {
                "checked_at_utc": "2026-07-10T05:00:00+00:00",
                "status": "update_available",
                "local_latest_draw": {"year": 2026, "draw_number": 53, "draw_key": "2026-53"},
                "official_latest_draw": {"year": 2026, "draw_number": 54, "draw_key": "2026-54", "date": "2026-07-12", "numbers": [1,2,3,4,5,6]},
            }
        def ingestor(record, **kwargs):
            calls["ingest"] += 1
            assert record["draw_key"] == "2026-54"
            return {"status": "inserted", "inserted": True}
        def refresher(**kwargs):
            calls["refresh"] += 1
            return {"status": "completed", "heavy_ml_retraining_performed": False}

        report = run_startup_automation(
            trigger="operator_run",
            force_check=True,
            config={**cfg, "auto_apply_enabled": True, "auto_refresh_enabled": True},
            detector=detector,
            ingestor=ingestor,
            refresher=refresher,
            write_outputs=False,
            previous_status={},
        )
        assert report["status"] == "completed", report
        assert calls == {"detect": 1, "ingest": 1, "refresh": 1}, calls
        assert report["heavy_ml_retraining_performed"] is False

        cached = run_startup_automation(
            trigger="startup",
            force_check=False,
            config=cfg,
            detector=detector,
            write_outputs=False,
            previous_status={"checked_at_utc": "2099-01-01T00:00:00+00:00", "status": "up_to_date"},
        )
        assert cached["status"] == "cached", cached
        assert calls["detect"] == 1, calls
        assert cache_is_fresh({"checked_at_utc": "2099-01-01T00:00:00+00:00"}, 30)

    print("STEP_126_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

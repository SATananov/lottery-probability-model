from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.r_statistical_layer_compat_engine import generate_python_compatible_r_reports

STATUS_JSON = ROOT / "models" / "v143_3_statistical_layer_runner_status.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def find_rscript() -> Path | None:
    explicit = os.environ.get("RSCRIPT_PATH", "").strip()
    if explicit and Path(explicit).is_file():
        return Path(explicit)
    located = shutil.which("Rscript") or shutil.which("Rscript.exe")
    if located:
        return Path(located)
    candidates: list[Path] = []
    for base in (Path(r"C:\Program Files\R"), Path(r"C:\Program Files (x86)\R")):
        if base.exists():
            candidates.extend(base.glob("R-*/*/Rscript.exe"))
            candidates.extend(base.glob("R-*/bin/Rscript.exe"))
            candidates.extend(base.glob("R-*/bin/x64/Rscript.exe"))
    return sorted(candidates, reverse=True)[0] if candidates else None


def run_r_layer(rscript: Path, timeout_seconds: int) -> dict:
    commands = [
        [str(rscript), "r/install_packages.R"],
        [str(rscript), "r/run_all_r_reports.R"],
    ]
    outputs: list[str] = []
    for command in commands:
        done = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
        outputs.append(((done.stdout or "") + ("\n" + done.stderr if done.stderr else "")).strip())
        if done.returncode != 0:
            raise RuntimeError(f"R statistical command failed with exit code {done.returncode}: {' '.join(command)}\n{outputs[-1][-3000:]}")
    return {
        "runner": "rscript",
        "rscript": str(rscript),
        "output_tail": "\n".join(outputs)[-5000:],
    }


def validate_latest_draw() -> dict:
    from src.v122_unified_official_draw_freshness_engine import build_freshness_report

    freshness = build_freshness_report(write_outputs=False)
    source = next(item for item in freshness["sources"] if item["key"] == "r_layer")
    if source.get("status") != "synced":
        raise RuntimeError(f"Statistical layer is not synchronized after refresh: {source.get('status')} — {source.get('message')}")
    return {
        "official_latest_draw": freshness.get("official_latest_draw"),
        "r_layer": source,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-platform statistical-layer refresh for Step 143.3")
    parser.add_argument("--mode", choices=["auto", "r", "python"], default=os.environ.get("LPM_R_LAYER_MODE", "auto"))
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--simulations", type=int, default=100)
    parser.add_argument("--no-status-write", action="store_true")
    args = parser.parse_args()

    started = utc_now()
    rscript = find_rscript()
    fallback_reason = ""
    try:
        if args.mode in {"auto", "r"} and rscript:
            execution = run_r_layer(rscript, args.timeout)
        elif args.mode == "r":
            raise RuntimeError("Rscript was requested but could not be found.")
        else:
            if args.mode == "auto" and not rscript:
                fallback_reason = "Rscript was not found; the deterministic Python compatibility runner was used."
            execution = generate_python_compatible_r_reports(simulations=args.simulations, write_outputs=True)

        validation = validate_latest_draw()
        report = {
            "step": "143.3",
            "name": "Cross-platform Statistical Layer Runner",
            "started_at_utc": started,
            "finished_at_utc": utc_now(),
            "status": "completed",
            "requested_mode": args.mode,
            "runner": execution.get("runner"),
            "fallback_reason": fallback_reason,
            "execution": execution,
            "validation": validation,
            "heavy_ml_retraining_performed": False,
        }
        if not args.no_status_write:
            STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
            STATUS_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        report = {
            "step": "143.3",
            "name": "Cross-platform Statistical Layer Runner",
            "started_at_utc": started,
            "finished_at_utc": utc_now(),
            "status": "failed",
            "requested_mode": args.mode,
            "runner": "rscript" if rscript and args.mode != "python" else "python_compatibility",
            "error": str(exc),
            "heavy_ml_retraining_performed": False,
        }
        if not args.no_status_write:
            STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
            STATUS_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

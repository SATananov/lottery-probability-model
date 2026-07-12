from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v147_experimental_evidence_decision_engine import run_experimental_evidence_decision


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Step 147 experimental evidence research decision")
    parser.add_argument("--read-only", action="store_true", help="Evaluate without changing project files")
    args = parser.parse_args()
    report = run_experimental_evidence_decision(write_outputs=not args.read_only)
    print(json.dumps({
        "ok": True,
        "decision_id": report["decision_id"],
        "production_promotion": report["decision"]["production_promotion"],
        "current_neural_configuration": report["decision"]["current_neural_configuration"],
        "result_signature_sha256": report["reproducibility"]["result_signature_sha256"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

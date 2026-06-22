from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.v75_neural_meta_learner_engine import build_neural_meta_learner

if __name__ == "__main__":
    summary = build_neural_meta_learner()
    metrics = summary["metrics"]
    print("STEP75_BUILD_OK")
    print("STATUS", summary["status"])
    print("VALID_DRAWS", summary["valid_draws"])
    print("AVG_HITS_TOP6", round(float(metrics["avg_hits_top6"]), 4))
    print("MAX_HITS_TOP6", metrics["max_hits_top6"])
    print("TOP_NUMBERS", ",".join(map(str, summary["top_numbers"])))

import json
from pathlib import Path

model_path = Path("models/lottery_advanced_ensemble_model.json")

if not model_path.exists():
    print("Advanced model file not found.")
    print("Run first: python train_advanced_model.py")
    raise SystemExit(1)

with model_path.open("r", encoding="utf-8-sig") as file:
    model = json.load(file)

recommendations = model.get("recommended_combinations", [])

print("Advanced recommendations")
print("-" * 40)

if not recommendations:
    print("No advanced recommendations found.")
    raise SystemExit(0)

for index, item in enumerate(recommendations[:10], start=1):
    numbers = item.get("numbers") or item.get("combination") or []
    confidence = item.get("confidence_score", 0)
    print(f"Rank {index}: {numbers} - confidence {confidence:.2f}/100")

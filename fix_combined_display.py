from pathlib import Path
import json

app_path = Path("app.py")
text = app_path.read_text(encoding="utf-8-sig")

combined_function = r'''

def print_trained_combined_model() -> None:
    """
    Print the final combined prediction strategy model if it exists.
    """
    from pathlib import Path
    import json

    model_path = Path("models/lottery_combined_model.json")

    print("Final combined prediction strategy model")
    print("-" * 40)

    if not model_path.exists():
        print("Combined model not found. Run: python train_combined_model.py")
        print()
        return

    with model_path.open("r", encoding="utf-8") as file:
        model = json.load(file)

    print(f"Model: {model.get('model_name', 'Final Combined Prediction Strategy Model v1.0')}")
    print(f"Training draws: {model.get('training_draws', 'unknown')}")
    print(f"Candidate combinations: {model.get('candidate_combinations', 'unknown')}")
    print(f"Theoretical jackpot odds: {model.get('theoretical_jackpot_odds', '1 in 13983816')}")

    recommendations = (
        model.get("top_recommendations")
        or model.get("recommendations")
        or model.get("top_combinations")
        or []
    )

    if not recommendations:
        print("No combined recommendations found in the model file.")
        print()
        return

    print("Top combined recommendations:")

    for index, item in enumerate(recommendations[:10], start=1):
        combination = item.get("combination") or item.get("numbers") or item.get("ticket") or []

        confidence = (
            item.get("confidence_score")
            or item.get("confidence")
            or item.get("final_score")
            or 0
        )

        relative_probability = (
            item.get("relative_model_probability")
            or item.get("relative_probability")
            or 0
        )

        top_percent = (
            item.get("top_percent")
            or item.get("relative_rank")
            or item.get("percentile")
            or ""
        )

        if isinstance(confidence, (int, float)):
            confidence_text = f"{confidence:.2f}"
        else:
            confidence_text = str(confidence)

        if isinstance(relative_probability, (int, float)):
            relative_probability_text = f"{relative_probability:.6f}%"
        else:
            relative_probability_text = str(relative_probability)

        if isinstance(top_percent, (int, float)):
            top_percent_text = f"{top_percent:.2f}%"
        else:
            top_percent_text = str(top_percent)

        print(
            f"Rank {index:2d}: {combination} | "
            f"confidence={confidence_text}/100 | "
            f"relative_model_probability={relative_probability_text} | "
            f"top={top_percent_text}"
        )

    print()
'''

if "def print_trained_combined_model()" not in text:
    text = text.replace("def main() -> None:", combined_function + "\n\ndef main() -> None:", 1)

if "print_trained_combined_model()" not in text.split("def main() -> None:", 1)[-1]:
    if "    print_trained_gap_model()\n" in text:
        text = text.replace(
            "    print_trained_gap_model()\n",
            "    print_trained_gap_model()\n    print_trained_combined_model()\n",
            1,
        )
    else:
        text = text.replace(
            "def main() -> None:\n",
            "def main() -> None:\n    print_trained_combined_model()\n",
            1,
        )

app_path.write_text(text, encoding="utf-8")
print("app.py updated: combined model display added.")

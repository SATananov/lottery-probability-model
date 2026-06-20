from src.cold_number_model import load_cold_model
from src.frequency_model import load_model
from src.gap_interval_model import load_gap_model
from src.generator import generate_random_combination
from src.historical_analysis import analyze_historical_draws, load_historical_draws
from src.middle_number_model import load_middle_model
from src.probability import get_jackpot_probability, get_exact_match_probability
from src.scoring_model import generate_scored_combination, get_top_scored_numbers
from src.simulation import simulate_ticket


def print_jackpot_probability() -> None:
    jackpot = get_jackpot_probability()

    print("Jackpot probability for 6/49")
    print("-" * 40)
    print(f"Total combinations: {jackpot['total_combinations']:,}")
    print(f"Odds: {jackpot['odds']}")
    print(f"Probability: {jackpot['probability_percent']:.10f}%")
    print()


def print_match_probabilities() -> None:
    print("Exact match probabilities")
    print("-" * 40)

    for matches in range(7):
        result = get_exact_match_probability(matches)

        print(
            f"{matches} matches: "
            f"{result['probability_percent']:.8f}% "
            f"({result['odds']})"
        )

    print()


def print_random_combination() -> None:
    combination = generate_random_combination()

    print("Random generated combination")
    print("-" * 40)
    print(combination)
    print()


def print_simulation() -> None:
    ticket = [3, 11, 18, 27, 34, 49]
    simulations = 100_000

    result = simulate_ticket(ticket, simulations)

    print("Simulation result")
    print("-" * 40)
    print(f"Ticket: {result['ticket']}")
    print(f"Simulations: {result['simulations']:,}")

    for matches, count in result["results"].items():
        percent = (count / simulations) * 100
        print(f"{matches} matches: {count:,} times ({percent:.4f}%)")

    print()


def print_historical_analysis() -> None:
    print("Historical analysis")
    print("-" * 40)

    summary = analyze_historical_draws()

    print(f"Historical draws loaded: {summary['draw_count']}")
    print(f"Report written to: {summary['report_path']}")

    hot_numbers = ", ".join(
        f"{number} ({count})"
        for number, count in summary["hot_numbers"]
    )
    cold_numbers = ", ".join(
        f"{number} ({count})"
        for number, count in summary["cold_numbers"]
    )
    overdue_numbers = ", ".join(
        f"{number} ({gap})"
        for number, gap in summary["overdue_numbers"]
    )

    print(f"Most frequent numbers: {hot_numbers}")
    print(f"Least frequent numbers: {cold_numbers}")
    print(f"Most overdue numbers: {overdue_numbers}")
    print()


def print_training_scoring_model() -> None:
    print("Training baseline scoring model")
    print("-" * 40)
    print("This is not a prediction model. It is a transparent training score.")

    draws = load_historical_draws()
    top_scores = get_top_scored_numbers(draws, limit=10)
    scored_combination = generate_scored_combination(draws)

    for number, score in top_scores:
        print(f"Number {number}: score {score:.4f}")

    print(f"Sample scored combination: {scored_combination}")
    print()


def print_trained_frequency_model() -> None:
    print("Trained historical frequency model")
    print("-" * 40)

    try:
        model = load_model()
    except FileNotFoundError:
        print("No trained frequency model found yet.")
        print("Run this first: python train_model.py")
        print()
        return

    print(f"Model: {model['model_name']} v{model['model_version']}")
    print(f"Training draws: {model['training_draws']}")
    print(f"Recommended hot/frequency ticket: {model['recommended_ticket']}")
    print("Top scored numbers:")

    for item in model["scored_numbers"][:10]:
        print(
            f"Number {item['number']:>2}: "
            f"score={item['model_score']:.4f}, "
            f"empirical={item['empirical_probability']:.2%}, "
            f"expected={item['theoretical_probability']:.2%}, "
            f"z={item['z_score']:.2f}, "
            f"status={item['status']}"
        )

    print()


def print_trained_cold_model() -> None:
    print("Trained cold numbers model")
    print("-" * 40)

    try:
        model = load_cold_model()
    except FileNotFoundError:
        print("No trained cold model found yet.")
        print("Run this first: python train_cold_model.py")
        print()
        return

    print(f"Model: {model['model_name']} v{model['model_version']}")
    print(f"Training draws: {model['training_draws']}")
    print(f"Recommended cold ticket: {model['recommended_ticket']}")
    print("Top underrepresented numbers:")

    for item in model["scored_numbers"][:10]:
        print(
            f"Number {item['number']:>2}: "
            f"cold_score={item['cold_model_score']:.4f}, "
            f"empirical={item['empirical_probability']:.2%}, "
            f"expected={item['theoretical_probability']:.2%}, "
            f"deficit={item['deficit_probability']:.2%}, "
            f"gap={item['recency_gap']}, "
            f"status={item['cold_status']}"
        )

    print()


def print_trained_middle_model() -> None:
    print("Trained middle / balanced numbers model")
    print("-" * 40)

    try:
        model = load_middle_model()
    except FileNotFoundError:
        print("No trained middle model found yet.")
        print("Run this first: python train_middle_model.py")
        print()
        return

    print(f"Model: {model['model_name']} v{model['model_version']}")
    print(f"Training draws: {model['training_draws']}")
    print(f"Recommended middle ticket: {model['recommended_ticket']}")
    print("Top balanced numbers:")

    for item in model["scored_numbers"][:10]:
        print(
            f"Number {item['number']:>2}: "
            f"middle_score={item['middle_model_score']:.4f}, "
            f"empirical={item['empirical_probability']:.2%}, "
            f"expected={item['theoretical_probability']:.2%}, "
            f"difference={item['difference_from_theoretical']:.2%}, "
            f"z={item['z_score']:.2f}, "
            f"gap={item['recency_gap']}, "
            f"status={item['middle_status']}"
        )

    print()



def print_trained_gap_model() -> None:
    print("Trained gap / interval probability model")
    print("-" * 40)

    try:
        model = load_gap_model()
    except FileNotFoundError:
        print("No trained gap model found yet.")
        print("Run this first: python train_gap_model.py")
        print()
        return

    print(f"Model: {model['model_name']} v{model['model_version']}")
    print(f"Training draws: {model['training_draws']}")
    print(f"Baseline next-draw probability per number: {model['baseline_next_draw_probability']:.2%}")
    print(f"Recommended gap ticket: {model['recommended_ticket']}")
    print("Top next-draw probability numbers:")

    for item in model["scored_numbers"][:10]:
        print(
            f"Number {item['number']:>2}: "
            f"next_prob={item['combined_next_probability']:.2%}, "
            f"baseline={item['baseline_probability']:.2%}, "
            f"hazard={item['interval_hazard_probability']:.2%}, "
            f"empirical={item['empirical_probability']:.2%}, "
            f"gap={item['current_gap']}, "
            f"avg_interval={item['average_interval']:.2f}, "
            f"gap_ratio={item['gap_ratio']:.2f}, "
            f"status={item['interval_status']}"
        )

    print()




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

    candidate_count = (
        model.get("candidate_count")
        or model.get("candidate_combinations")
        or model.get("candidates")
        or "unknown"
    )

    if isinstance(candidate_count, int):
        candidate_count_text = f"{candidate_count:,}"
    else:
        candidate_count_text = str(candidate_count)

    print(f"Model: {model.get('model_name', 'Final Combined Prediction Strategy Model v1.0')}")
    print(f"Training draws: {model.get('training_draws', 'unknown')}")
    print(f"Candidate combinations: {candidate_count_text}")
    print(f"Theoretical jackpot odds: {model.get('theoretical_jackpot_odds', '1 in 13983816')}")

    recommendations = (
        model.get("recommended_combinations")
        or model.get("top_recommendations")
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
        combination = item.get("numbers") or item.get("combination") or item.get("ticket") or []

        confidence = (
            item.get("confidence_score")
            if item.get("confidence_score") is not None
            else item.get("confidence")
        )
        if confidence is None:
            confidence = item.get("final_score", 0)
            if isinstance(confidence, (int, float)) and confidence <= 1:
                confidence *= 100

        relative_probability = (
            item.get("relative_model_probability")
            or item.get("relative_probability")
            or 0
        )

        top_percent = (
            item.get("relative_top_percent")
            or item.get("top_percent")
            or item.get("percentile")
            or ""
        )

        if isinstance(confidence, (int, float)):
            confidence_text = f"{confidence:.2f}"
        else:
            confidence_text = str(confidence)

        if isinstance(relative_probability, (int, float)):
            relative_probability_text = f"{relative_probability:.6%}"
        else:
            relative_probability_text = str(relative_probability)

        if isinstance(top_percent, (int, float)):
            top_percent_text = f"{top_percent:.2f}%"
        else:
            top_percent_text = str(top_percent)

        rank = item.get("relative_rank") or index

        print(
            f"Rank {rank:>2}: {combination} | "
            f"confidence={confidence_text}/100 | "
            f"relative_model_probability={relative_probability_text} | "
            f"top={top_percent_text}"
        )

    print()


def print_ml_extensions_model() -> None:
    """Print optional ML extension model summary if it exists."""
    from pathlib import Path
    import json

    model_path = Path("models/lottery_ml_extensions_model.json")

    print("ML extensions: classification, clustering and dimensionality reduction")
    print("-" * 40)

    if not model_path.exists():
        print("ML extensions model not found. Run: python train_ml_extensions.py")
        print()
        return

    with model_path.open("r", encoding="utf-8") as file:
        model = json.load(file)

    print(f"Model: {model.get('model_name', 'Lottery ML Extensions Ensemble')}")
    print(f"Training draws: {model.get('training_draws', 'unknown')}")
    print(f"Candidate combinations: {model.get('candidate_count', 'unknown')}")
    print(f"Backtest summary: {model.get('backtest_summary', {})}")
    print("Top ML recommendations:")

    for item in model.get("recommended_combinations", [])[:10]:
        print(
            f"Rank {item.get('rank')}: {item.get('numbers')} | "
            f"score={item.get('confidence_score')}/100 | "
            f"class={item.get('classification')} | "
            f"cluster={item.get('cluster_label')}"
        )

    print()


def main() -> None:
    print_jackpot_probability()
    print_match_probabilities()
    print_random_combination()
    print_simulation()
    print_historical_analysis()
    print_training_scoring_model()
    print_trained_frequency_model()
    print_trained_cold_model()
    print_trained_middle_model()
    print_trained_gap_model()
    print_trained_combined_model()
    print_ml_extensions_model()


if __name__ == "__main__":
    main()


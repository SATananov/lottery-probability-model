from src.combined_strategy_model import (
    DEFAULT_COMBINED_BACKTEST_REPORT_PATH,
    DEFAULT_COMBINED_MODEL_PATH,
    DEFAULT_COMBINED_REPORT_PATH,
    load_combined_model,
    run_combined_backtest,
    save_combined_model,
    train_combined_strategy_model,
    write_combined_backtest_report,
    write_combined_report,
)


def main() -> None:
    model = train_combined_strategy_model(candidate_count=20_000, top_limit=20)
    save_combined_model(model)
    write_combined_report(model)

    backtest = run_combined_backtest(candidate_count=5_000)
    write_combined_backtest_report(backtest)

    reloaded_model = load_combined_model()

    print("Final Combined Prediction Strategy Model")
    print("-" * 40)
    print(f"Training draws: {reloaded_model['training_draws']}")
    print(f"Candidate combinations: {reloaded_model['candidate_count']:,}")
    print(f"Model saved to: {DEFAULT_COMBINED_MODEL_PATH}")
    print(f"Report saved to: {DEFAULT_COMBINED_REPORT_PATH}")
    print(f"Backtest report saved to: {DEFAULT_COMBINED_BACKTEST_REPORT_PATH}")
    print(f"Theoretical jackpot odds: {reloaded_model['theoretical_jackpot_odds']}")
    print()

    print("Top combined recommendations")
    print("-" * 40)

    for item in reloaded_model["recommended_combinations"][:10]:
        print(
            f"Rank {item['relative_rank']:>2}: {item['numbers']} | "
            f"confidence={item['confidence_score']:.2f}/100 | "
            f"relative_model_probability={item['relative_model_probability']:.6%} | "
            f"top={item['relative_top_percent']:.2f}%"
        )

    print()
    print("Backtest")
    print("-" * 40)
    print(f"Проверени тиражи: {backtest['tested_draws']}")
    print(f"Combined average matches: {backtest['combined_average_matches']:.4f}")
    print(f"Random average matches: {backtest['random_average_matches']:.4f}")
    print(backtest["message"])


if __name__ == "__main__":
    main()

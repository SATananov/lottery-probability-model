from src.gap_interval_model import (
    DEFAULT_DATA_PATH,
    DEFAULT_GAP_BACKTEST_REPORT_PATH,
    DEFAULT_GAP_MODEL_PATH,
    DEFAULT_GAP_REPORT_PATH,
    load_draws,
    run_gap_backtest,
    save_gap_model,
    train_gap_interval_model,
    write_gap_backtest_report,
    write_gap_model_report,
)


def main() -> None:
    draws = load_draws(DEFAULT_DATA_PATH)

    model = train_gap_interval_model(draws)
    model_path = save_gap_model(model, DEFAULT_GAP_MODEL_PATH)
    report_path = write_gap_model_report(model, DEFAULT_GAP_REPORT_PATH)

    print("Gap / Interval Next-Draw Probability Model")
    print("-" * 40)
    print(f"Training draws: {model['training_draws']}")
    print(f"Model saved to: {model_path}")
    print(f"Report saved to: {report_path}")
    print(f"Recommended gap ticket: {model['recommended_ticket']}")
    print(f"Baseline probability per number: {model['baseline_next_draw_probability']:.2%}")
    print()

    print("Top next-draw probability numbers")
    print("-" * 40)

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

    if len(draws) > 10:
        backtest = run_gap_backtest(
            draws,
            min_train_size=10,
            random_seed=456,
        )
        backtest_report_path = write_gap_backtest_report(
            backtest,
            DEFAULT_GAP_BACKTEST_REPORT_PATH,
        )

        print("Gap model backtest")
        print("-" * 40)
        print(f"Tested draws: {backtest['test_count']}")
        print(f"Gap model average matches: {backtest['gap_average_matches']:.4f}")
        print(f"Hot frequency model average matches: {backtest['hot_average_matches']:.4f}")
        print(f"Cold model average matches: {backtest['cold_average_matches']:.4f}")
        print(f"Middle model average matches: {backtest['middle_average_matches']:.4f}")
        print(f"Random baseline average matches: {backtest['random_average_matches']:.4f}")
        print(f"Backtest report saved to: {backtest_report_path}")
        print(backtest["conclusion"])
    else:
        print("Backtest skipped: add more historical draws for a useful test.")


if __name__ == "__main__":
    main()
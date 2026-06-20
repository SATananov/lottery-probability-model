from src.middle_number_model import (
    DEFAULT_DATA_PATH,
    DEFAULT_MIDDLE_BACKTEST_REPORT_PATH,
    DEFAULT_MIDDLE_MODEL_PATH,
    DEFAULT_MIDDLE_REPORT_PATH,
    load_draws,
    run_middle_backtest,
    save_middle_model,
    train_middle_number_model,
    write_middle_backtest_report,
    write_middle_model_report,
)


def main() -> None:
    draws = load_draws(DEFAULT_DATA_PATH)

    model = train_middle_number_model(
        draws,
        recent_window=20,
        closeness_weight=0.60,
        gap_balance_weight=0.25,
        recent_balance_weight=0.15,
    )

    model_path = save_middle_model(model, DEFAULT_MIDDLE_MODEL_PATH)
    report_path = write_middle_model_report(model, DEFAULT_MIDDLE_REPORT_PATH)

    print("Middle / Balanced Numbers Model")
    print("-" * 40)
    print(f"Training draws: {model['training_draws']}")
    print(f"Model saved to: {model_path}")
    print(f"Report saved to: {report_path}")
    print(f"Recommended middle ticket: {model['recommended_ticket']}")
    print()

    print("Top balanced numbers")
    print("-" * 40)

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

    if len(draws) > 10:
        backtest = run_middle_backtest(
            draws,
            min_train_size=10,
            recent_window=20,
            random_seed=123,
        )
        backtest_report_path = write_middle_backtest_report(
            backtest,
            DEFAULT_MIDDLE_BACKTEST_REPORT_PATH,
        )

        print("Middle model backtest")
        print("-" * 40)
        print(f"Tested draws: {backtest['test_count']}")
        print(f"Middle model average matches: {backtest['middle_average_matches']:.4f}")
        print(f"Hot frequency model average matches: {backtest['hot_average_matches']:.4f}")
        print(f"Cold model average matches: {backtest['cold_average_matches']:.4f}")
        print(f"Random baseline average matches: {backtest['random_average_matches']:.4f}")
        print(f"Backtest report saved to: {backtest_report_path}")
        print(backtest["conclusion"])
    else:
        print("Backtest skipped: add more historical draws for a useful test.")


if __name__ == "__main__":
    main()


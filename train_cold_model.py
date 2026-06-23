from src.cold_number_model import (
    DEFAULT_COLD_BACKTEST_REPORT_PATH,
    DEFAULT_COLD_MODEL_PATH,
    DEFAULT_COLD_REPORT_PATH,
    DEFAULT_DATA_PATH,
    load_draws,
    run_cold_backtest,
    save_cold_model,
    train_cold_number_model,
    write_cold_backtest_report,
    write_cold_model_report,
)


def main() -> None:
    draws = load_draws(DEFAULT_DATA_PATH)

    model = train_cold_number_model(
        draws,
        recent_window=20,
        deficit_weight=0.50,
        gap_weight=0.30,
        recent_cold_weight=0.20,
    )

    model_path = save_cold_model(model, DEFAULT_COLD_MODEL_PATH)
    report_path = write_cold_model_report(model, DEFAULT_COLD_REPORT_PATH)

    print("Cold Numbers / Underrepresented Numbers Model")
    print("-" * 40)
    print(f"Training draws: {model['training_draws']}")
    print(f"Model saved to: {model_path}")
    print(f"Report saved to: {report_path}")
    print(f"Recommended cold ticket: {model['recommended_ticket']}")
    print()

    print("Top underrepresented numbers")
    print("-" * 40)

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

    if len(draws) > 10:
        backtest = run_cold_backtest(
            draws,
            min_train_size=10,
            recent_window=20,
            random_seed=99,
        )
        backtest_report_path = write_cold_backtest_report(
            backtest,
            DEFAULT_COLD_BACKTEST_REPORT_PATH,
        )

        print("Cold model backtest")
        print("-" * 40)
        print(f"Проверени тиражи: {backtest['test_count']}")
        print(f"Cold model average matches: {backtest['cold_average_matches']:.4f}")
        print(f"Hot frequency model average matches: {backtest['hot_average_matches']:.4f}")
        print(f"Random baseline average matches: {backtest['random_average_matches']:.4f}")
        print(f"Backtest report saved to: {backtest_report_path}")
        print(backtest["conclusion"])
    else:
        print("Backtest skipped: add more historical draws for a useful test.")


if __name__ == "__main__":
    main()
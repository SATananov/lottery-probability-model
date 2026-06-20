from src.backtesting import run_rolling_backtest, write_backtest_report
from src.frequency_model import (
    DEFAULT_DATA_PATH,
    DEFAULT_MODEL_PATH,
    DEFAULT_REPORT_PATH,
    load_draws,
    save_model,
    train_frequency_model,
    write_frequency_model_report,
)


def main() -> None:
    draws = load_draws(DEFAULT_DATA_PATH)

    model = train_frequency_model(
        draws,
        recent_window=20,
        frequency_weight=0.55,
        recent_weight=0.30,
        gap_weight=0.15,
    )

    model_path = save_model(model, DEFAULT_MODEL_PATH)
    report_path = write_frequency_model_report(model, DEFAULT_REPORT_PATH)

    print("Historical Frequency Probability Model")
    print("-" * 40)
    print(f"Training draws: {model['training_draws']}")
    print(f"Model saved to: {model_path}")
    print(f"Report saved to: {report_path}")
    print(f"Recommended ticket: {model['recommended_ticket']}")
    print()

    print("Top scored numbers")
    print("-" * 40)

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

    if len(draws) > 10:
        backtest = run_rolling_backtest(
            draws,
            min_train_size=10,
            recent_window=20,
            random_seed=42,
        )
        backtest_report_path = write_backtest_report(backtest)

        print("Backtest")
        print("-" * 40)
        print(f"Tested draws: {backtest['test_count']}")
        print(f"Model average matches: {backtest['model_average_matches']:.4f}")
        print(f"Random average matches: {backtest['random_average_matches']:.4f}")
        print(f"Backtest report saved to: {backtest_report_path}")
        print(backtest["conclusion"])
    else:
        print("Backtest skipped: add more historical draws for a useful test.")


if __name__ == "__main__":
    main()
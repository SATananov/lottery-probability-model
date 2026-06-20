from src.advanced_methods import (
    DEFAULT_BACKTEST_JSON_PATH,
    DEFAULT_BACKTEST_REPORT_PATH,
    run_advanced_backtest,
    save_advanced_backtest,
    write_advanced_backtest_report,
)


def main() -> None:
    backtest = run_advanced_backtest()
    save_advanced_backtest(backtest, DEFAULT_BACKTEST_JSON_PATH)
    report_path = write_advanced_backtest_report(backtest, DEFAULT_BACKTEST_REPORT_PATH)

    print("Advanced backtesting engine")
    print("----------------------------------------")
    print(f"Tested draws: {backtest['tested_draws']}")
    print(f"Best strategy: {backtest['best_strategy']}")
    print("Average matches:")
    for strategy, average in backtest["averages"].items():
        print(
            f"{strategy}: avg={average:.4f}, "
            f">=3={backtest['hit_rates'][strategy]['at_least_3']:.2%}, "
            f">=4={backtest['hit_rates'][strategy]['at_least_4']:.2%}"
        )
    print(backtest["conclusion"])
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main()

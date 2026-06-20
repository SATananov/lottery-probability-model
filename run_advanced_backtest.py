from src.advanced_methods import (
    _bg_strategy_name,
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

    print("Разширен модул за историческа проверка")
    print("----------------------------------------")
    print(f"Тествани тиражи: {backtest['tested_draws']}")
    print(f"Най-добра стратегия: {_bg_strategy_name(backtest['best_strategy'])}")
    print("Средни съвпадения:")
    for strategy, average in backtest["averages"].items():
        print(
            f"{_bg_strategy_name(strategy)}: средно={average:.4f}, "
            f">=3={backtest['hit_rates'][strategy]['at_least_3']:.2%}, "
            f">=4={backtest['hit_rates'][strategy]['at_least_4']:.2%}"
        )
    print("Това е проверка на модела назад във времето, не доказателство за бъдеща предвидимост.")
    print(f"Отчетът е записан в: {report_path}")


if __name__ == "__main__":
    main()

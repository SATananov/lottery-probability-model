from src.advanced_methods import (
    DEFAULT_MODEL_PATH,
    DEFAULT_REPORT_PATH,
    save_advanced_model,
    train_advanced_ensemble_model,
    write_advanced_report,
)


def main() -> None:
    model = train_advanced_ensemble_model()
    save_advanced_model(model, DEFAULT_MODEL_PATH)
    report_path = write_advanced_report(model, DEFAULT_REPORT_PATH)

    print("Trained advanced combined statistical model")
    print("----------------------------------------")
    print(f"Model: {model['model_name']} v{model['model_version']}")
    print(f"Training draws: {model['training_draws']}")
    print(f"Candidate combinations: {model['candidate_count']}")
    print(f"Fairness p-value: {model['fairness_test']['p_value']:.6f}")
    print(f"Fairness interpretation: {model['fairness_test']['interpretation']}")
    print("Top advanced recommendations:")
    for item in model["recommended_combinations"][:10]:
        print(
            f"Rank {item['relative_rank']:2d}: {item['numbers']} | "
            f"confidence={item['confidence_score']:.2f}/100 | "
            f"relative_model_probability={item['relative_model_probability']:.6%} | "
            f"top={item['relative_top_percent']:.2f}%"
        )
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main()

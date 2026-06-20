from src.ml_extensions import train_save_report


if __name__ == "__main__":
    model = train_save_report()
    print("Lottery ML extensions trained")
    print("----------------------------------------")
    print(f"Training draws: {model['training_draws']}")
    print(f"Candidate combinations: {model['candidate_count']}")
    print("Top recommendations:")
    for item in model.get("recommended_combinations", [])[:10]:
        print(
            f"Rank {item['rank']}: {item['numbers']} | score={item['confidence_score']}/100 | "
            f"class={item['classification']} | cluster={item['cluster_label']}"
        )

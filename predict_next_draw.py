from __future__ import annotations

from src.prediction_engine import train_save_report


def main() -> None:
    model = train_save_report()
    best = model.get("recommended_prediction", {})
    print("Прогнозен статистически модул v36")
    print("-" * 40)
    print(f"Обучени тиражи: {model.get('training_draws')}")
    print(f"Кандидат-комбинации: {model.get('candidate_count')}")
    print(f"Реален шанс за точна комбинация: {model.get('theoretical_jackpot_odds')}")
    print()
    print("Основна прогноза:")
    print(f"Числа: {best.get('numbers')}")
    print(f"Моделна оценка: {best.get('prediction_score')}/100")
    print(f"Клас: {best.get('classification')}")
    print(f"Клъстер: {best.get('cluster_label')}")
    print("Причини:")
    for reason in best.get("reasons", []):
        print(f"- {reason}")
    print()
    print("Топ 10 прогнозни комбинации:")
    for item in model.get("recommended_combinations", [])[:10]:
        print(f"Ранг {item.get('rank')}: {item.get('numbers')} - оценка {item.get('prediction_score')}/100")
    print()
    print("Отчет: reports/prediction_report.md")
    print("Модел: models/lottery_prediction_model.json")


if __name__ == "__main__":
    main()

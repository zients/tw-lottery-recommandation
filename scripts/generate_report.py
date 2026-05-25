"""Generate daily HTML prediction report for all lottery types."""
import os
from pathlib import Path

from data.db import init_db, get_all_draws
from scraper.scraper import LOTTERY_CONFIG
from analyzer.analyzer import recommend, recommend_special
from ml.predict import has_model, predict as ml_predict
from report.generator import LotteryPrediction, write_report

DB_PATH = os.environ.get("LOTTERY_DB", "data/lottery.db")
OUTPUT_DIR = Path(os.environ.get("REPORT_OUTPUT", "dist"))

LOTTERY_NAMES = {
    "539": "今彩539",
    "649": "大樂透",
    "638": "威力彩",
    "3d": "3星彩",
    "4d": "4星彩",
}


def _predict(lottery_type: str) -> LotteryPrediction:
    draws = get_all_draws(DB_PATH, lottery_type)
    cfg = LOTTERY_CONFIG[lottery_type]
    draw_list = [(d, nums[: cfg["analyze_count"]]) for d, nums in draws]

    if has_model(lottery_type):
        try:
            combos = ml_predict(
                draws,
                lottery_type,
                num_range=cfg["num_range"],
                analyze_count=cfg["analyze_count"],
                pick=cfg["analyze_count"],
            )
            method = "ML"
        except Exception as e:
            print(f"[{lottery_type}] ML failed ({e}), falling back to frequency")
            combos = recommend(draw_list, cfg)
            method = "Frequency"
    else:
        combos = recommend(draw_list, cfg)
        method = "Frequency"

    special = None
    if cfg.get("special_range"):
        special = recommend_special(draws, cfg["special_range"])

    return LotteryPrediction(
        lottery_type=lottery_type,
        name=LOTTERY_NAMES[lottery_type],
        method=method,
        combos=combos,
        special=special,
    )


def main() -> None:
    init_db(DB_PATH)
    predictions = [_predict(t) for t in LOTTERY_NAMES]
    dated, index = write_report(predictions, OUTPUT_DIR)
    print(f"Written: {dated.name}, {index.name}")


if __name__ == "__main__":
    main()

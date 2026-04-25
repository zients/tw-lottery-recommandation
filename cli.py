# cli.py
import os
import argparse
from rich.console import Console
from rich.table import Table
from data.db import init_db, insert_draw, get_all_draws
from scraper.scraper import fetch_draws, LOTTERY_CONFIG
from analyzer.analyzer import frequency, hot_numbers, cold_numbers, recommend, recommend_special
from ml.predict import has_model, predict as ml_predict
from ml.train import train as ml_train

DB_PATH = os.environ.get("LOTTERY_DB", "data/lottery.db")
console = Console()

LOTTERY_TYPES = {
    "539": "今彩539",
    "649": "大樂透",
    "638": "威力彩",
    "3d":  "3星彩",
    "4d":  "4星彩",
}


def cmd_update(start_month: str | None = None, lottery_type: str = "539") -> None:
    init_db(DB_PATH)
    existing = {row[0] for row in get_all_draws(DB_PATH, lottery_type)}
    # auto-detect start month from latest DB record if not specified
    if start_month is None and existing:
        latest = max(existing)
        start_month = latest[:7]  # "YYYY-MM-DD" → "YYYY-MM"
    draws = fetch_draws(start_month=start_month, lottery_type=lottery_type)
    new_count = 0
    for date, numbers in draws:
        if date not in existing:
            insert_draw(DB_PATH, date, numbers, lottery_type)
            new_count += 1
    console.print(f"[green]{new_count} new draw(s) saved.[/green]")


def cmd_stats(lottery_type: str = "539") -> None:
    draws = get_all_draws(DB_PATH, lottery_type)
    if not draws:
        console.print("[red]No data. Run: python cli.py update[/red]")
        return
    cfg = LOTTERY_CONFIG[lottery_type]
    num_range = cfg["num_range"]
    analyze_count = cfg["analyze_count"]
    draw_list = [(d, nums[:analyze_count]) for d, nums in draws]

    freq = frequency(draw_list, num_range)
    hot = hot_numbers(draw_list, num_range=num_range)
    cold = cold_numbers(draw_list, num_range=num_range)

    console.print(f"\n[bold]彩種：[/bold]{LOTTERY_TYPES[lottery_type]}  [bold]總期數：[/bold]{len(draw_list)}")

    table = Table(title="號碼頻率 Top 10")
    table.add_column("號碼", style="cyan")
    table.add_column("出現次數", style="magenta")
    for n, c in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]:
        table.add_row(str(n), str(c))
    console.print(table)

    console.print(f"\n[bold yellow]熱號（近30期）：[/bold yellow] {', '.join(str(n) for n in hot)}")
    console.print(f"[bold blue]冷號（近30期）：[/bold blue] {', '.join(str(n) for n in cold)}")

    special_range = cfg.get("special_range")
    if special_range:
        special_draws = [(d, [nums[-1]]) for d, nums in draws if nums]
        special_freq = frequency(special_draws, special_range)
        sp_table = Table(title=f"特別號頻率 Top 5")
        sp_table.add_column("號碼", style="cyan")
        sp_table.add_column("出現次數", style="magenta")
        for n, c in sorted(special_freq.items(), key=lambda x: x[1], reverse=True)[:5]:
            sp_table.add_row(str(n), str(c))
        console.print(sp_table)


def cmd_recommend(lottery_type: str = "539") -> None:
    draws = get_all_draws(DB_PATH, lottery_type)
    if not draws:
        console.print("[red]No data. Run: lottery update[/red]")
        return
    cfg = LOTTERY_CONFIG[lottery_type]
    special_range = cfg.get("special_range")
    draw_list = [(d, nums[:cfg["analyze_count"]]) for d, nums in draws]

    if has_model(lottery_type):
        try:
            combos = ml_predict(
                draws, lottery_type,
                num_range=cfg["num_range"],
                analyze_count=cfg["analyze_count"],
                pick=cfg["analyze_count"],
            )
            method = "ML"
        except Exception as e:
            # ML can fail for many reasons (corrupt checkpoint, shape mismatch
            # after config change, missing torch, OOM, etc). Fall back rather
            # than crashing — frequency-based recommend is always safe.
            console.print(f"[yellow]ML 預測失敗，改用頻率法：{type(e).__name__}: {e}[/yellow]")
            combos = recommend(draw_list, cfg)
            method = "頻率"
    else:
        combos = recommend(draw_list, cfg)
        method = "頻率"

    special = recommend_special(draws, special_range) if special_range else None
    console.print(f"\n[bold green]{LOTTERY_TYPES[lottery_type]} 推薦號碼（{method}）：[/bold green]")
    for i, combo in enumerate(combos, 1):
        nums = "  ".join(str(n) for n in combo)
        line = f"  組合 {i}：{nums}"
        if special is not None:
            line += f"  ＋特別號 {special}"
        console.print(line)


def cmd_train(lottery_type: str = "539", epochs: int = 100) -> None:
    draws = get_all_draws(DB_PATH, lottery_type)
    if not draws:
        console.print("[red]No data. Run: lottery update[/red]")
        return
    cfg = LOTTERY_CONFIG[lottery_type]
    console.print(f"[bold]訓練 {LOTTERY_TYPES[lottery_type]} Transformer（{epochs} epochs）...[/bold]")
    ml_train(
        draws,
        lottery_type=lottery_type,
        num_range=cfg["num_range"],
        analyze_count=cfg["analyze_count"],
        pick=cfg["analyze_count"],
        epochs=epochs,
    )


def main():
    parser = argparse.ArgumentParser(description="台灣539分析工具")
    subparsers = parser.add_subparsers(dest="command")

    type_choices = list(LOTTERY_TYPES.keys())
    type_help = "彩種：" + "、".join(f"{k}={v}" for k, v in LOTTERY_TYPES.items()) + "（預設：539）"

    update_p = subparsers.add_parser("update", help="更新開獎資料")
    update_p.add_argument("--from-month", type=str, default=None,
                          help="起始月份 YYYY-MM，預設自動從最新資料繼續")
    update_p.add_argument("--type", type=str, default="539", choices=type_choices, help=type_help)

    stats_p = subparsers.add_parser("stats", help="查看統計")
    stats_p.add_argument("--type", type=str, default="539", choices=type_choices, help=type_help)

    rec_p = subparsers.add_parser("recommend", help="產生推薦號碼（有 ML 模型則用 ML）")
    rec_p.add_argument("--type", type=str, default="539", choices=type_choices, help=type_help)

    train_p = subparsers.add_parser("train", help="訓練 ML 預測模型")
    train_p.add_argument("--type", type=str, default="539", choices=type_choices, help=type_help)
    train_p.add_argument("--epochs", type=int, default=100, help="訓練 epochs（預設 100）")

    args = parser.parse_args()
    if args.command == "update":
        cmd_update(start_month=args.from_month, lottery_type=args.type)
    elif args.command == "stats":
        cmd_stats(lottery_type=args.type)
    elif args.command == "train":
        cmd_train(lottery_type=args.type, epochs=args.epochs)
    elif args.command == "recommend":
        cmd_recommend(lottery_type=args.type)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

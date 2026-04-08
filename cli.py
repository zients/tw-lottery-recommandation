# cli.py
import os
import argparse
from rich.console import Console
from rich.table import Table
from data.db import init_db, insert_draw, get_all_draws
from scraper.scraper import fetch_draws, LOTTERY_CONFIG
from analyzer.analyzer import frequency, hot_numbers, cold_numbers, recommend, recommend_special

DB_PATH = os.environ.get("LOTTERY_DB", "data/lottery.db")
console = Console()

LOTTERY_TYPES = {
    "539": "今彩539",
    "649": "大樂透",
    "638": "威力彩",
    "3d":  "3星彩",
    "4d":  "4星彩",
    "49m6": "49樂合彩",
    "39m5": "39樂合彩",
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


def cmd_recommend(lottery_type: str = "539") -> None:
    draws = get_all_draws(DB_PATH, lottery_type)
    if not draws:
        console.print("[red]No data. Run: python cli.py update[/red]")
        return
    cfg = LOTTERY_CONFIG[lottery_type]
    special_range = cfg.get("special_range")
    draw_list = [(d, nums[:cfg["analyze_count"]]) for d, nums in draws]
    combos = recommend(draw_list, cfg)
    special = recommend_special(draws, special_range) if special_range else None
    console.print(f"\n[bold green]{LOTTERY_TYPES[lottery_type]} 推薦號碼：[/bold green]")
    for i, combo in enumerate(combos, 1):
        nums = "  ".join(str(n) for n in combo)
        line = f"  組合 {i}：{nums}"
        if special is not None:
            line += f"  ＋特別號 {special}"
        console.print(line)


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

    rec_p = subparsers.add_parser("recommend", help="產生推薦號碼")
    rec_p.add_argument("--type", type=str, default="539", choices=type_choices, help=type_help)

    args = parser.parse_args()
    if args.command == "update":
        cmd_update(start_month=args.from_month, lottery_type=args.type)
    elif args.command == "stats":
        cmd_stats(lottery_type=args.type)
    elif args.command == "recommend":
        cmd_recommend(lottery_type=args.type)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

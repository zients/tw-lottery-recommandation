# cli.py
import os
import argparse
from rich.console import Console
from rich.table import Table
from data.db import init_db, insert_draw, get_all_draws
from scraper.scraper import fetch_draws
from analyzer.analyzer import frequency, hot_numbers, cold_numbers, recommend

DB_PATH = os.environ.get("LOTTERY_DB", "data/lottery.db")
console = Console()


def cmd_update(pages: int = 10) -> None:
    init_db(DB_PATH)
    existing = {row[0] for row in get_all_draws(DB_PATH)}
    draws = fetch_draws(pages=pages)
    new_count = 0
    for date, numbers in draws:
        if date not in existing:
            insert_draw(DB_PATH, date, numbers)
            new_count += 1
    console.print(f"[green]{new_count} new draw(s) saved.[/green]")


def cmd_stats() -> None:
    draws = get_all_draws(DB_PATH)
    if not draws:
        console.print("[red]No data. Run: python cli.py update[/red]")
        return
    draw_list = [(row[0], list(row[1:])) for row in draws]

    freq = frequency(draw_list)
    hot = hot_numbers(draw_list)
    cold = cold_numbers(draw_list)

    console.print(f"\n[bold]總期數：[/bold]{len(draw_list)}")

    table = Table(title="號碼頻率 Top 10")
    table.add_column("號碼", style="cyan")
    table.add_column("出現次數", style="magenta")
    for n, c in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]:
        table.add_row(f"{n:02d}", str(c))
    console.print(table)

    console.print(f"\n[bold yellow]熱號（近30期）：[/bold yellow] {', '.join(f'{n:02d}' for n in hot)}")
    console.print(f"[bold blue]冷號（近30期）：[/bold blue] {', '.join(f'{n:02d}' for n in cold)}")


def cmd_recommend() -> None:
    draws = get_all_draws(DB_PATH)
    if not draws:
        console.print("[red]No data. Run: python cli.py update[/red]")
        return
    draw_list = [(row[0], list(row[1:])) for row in draws]
    combos = recommend(draw_list)
    console.print("\n[bold green]推薦號碼：[/bold green]")
    for i, combo in enumerate(combos, 1):
        nums = "  ".join(f"{n:02d}" for n in combo)
        console.print(f"  組合 {i}：{nums}")


def main():
    parser = argparse.ArgumentParser(description="台灣539分析工具")
    subparsers = parser.add_subparsers(dest="command")

    update_p = subparsers.add_parser("update", help="更新開獎資料")
    update_p.add_argument("--pages", type=int, default=10)

    subparsers.add_parser("stats", help="查看統計")
    subparsers.add_parser("recommend", help="產生推薦號碼")

    args = parser.parse_args()
    if args.command == "update":
        cmd_update(pages=args.pages)
    elif args.command == "stats":
        cmd_stats()
    elif args.command == "recommend":
        cmd_recommend()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

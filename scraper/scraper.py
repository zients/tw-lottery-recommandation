# scraper/scraper.py
import requests
from datetime import date

API_BASE = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery"
HEADERS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}

# Config per lottery type: API path, response list key, numbers field, expected count, valid range, start date
LOTTERY_CONFIG: dict[str, dict] = {
    "539": {
        "path": "Daily539Result",
        "res_key": "daily539Res",
        "num_field": "drawNumberSize",
        "num_count": 5,
        "num_range": (1, 39),
        "start": (2007, 1),
        "analyze_count": 5,
        "odd_range": (2, 3),
        "sum_range": (80, 120),
    },
    "649": {
        "path": "Lotto649Result",
        "res_key": "lotto649Res",
        "num_field": "drawNumberSize",
        "num_count": 7,   # 6 regular + 1 special ball
        "num_range": (1, 49),
        "start": (2007, 1),
        "analyze_count": 6,  # analyze only the 6 regular balls
        "odd_range": (2, 4),
        "sum_range": (90, 200),
    },
    "638": {
        "path": "SuperLotto638Result",
        "res_key": "superLotto638Res",
        "num_field": "drawNumberSize",
        "num_count": 7,   # 6 regular + 1 special (stored as flat list, special is last)
        "num_range": (1, 38),
        "start": (2008, 1),
        "analyze_count": 6,  # analyze only the 6 regular balls
        "odd_range": (2, 4),
        "sum_range": (70, 165),
    },
    "3d": {
        "path": "3DResult",
        "res_key": "lotto3DRes",
        "num_field": "drawNumberSize",
        "num_count": 3,
        "num_range": (0, 9),
        "start": (2007, 1),
        "analyze_count": 3,
        "odd_range": None,  # digit games: skip odd/even filter
        "sum_range": None,
    },
    "4d": {
        "path": "4DResult",
        "res_key": "lotto4DRes",
        "num_field": "drawNumberSize",
        "num_count": 4,
        "num_range": (0, 9),
        "start": (2007, 1),
        "analyze_count": 4,
        "odd_range": None,
        "sum_range": None,
    },
    "49m6": {
        "path": "49M6Result",
        "res_key": "m649Res",
        "num_field": "drawNumberSize",
        "num_count": 6,
        "num_range": (1, 49),
        "start": (2007, 1),
        "analyze_count": 6,
        "odd_range": (2, 4),
        "sum_range": (90, 200),
    },
    "39m5": {
        "path": "39M5Result",
        "res_key": "m539Res",
        "num_field": "drawNumberSize",
        "num_count": 5,
        "num_range": (1, 39),
        "start": (2011, 1),
        "analyze_count": 5,
        "odd_range": (2, 3),
        "sum_range": (80, 120),
    },
}


def parse_draws(data: dict, lottery_type: str = "539") -> list[tuple[str, list[int]]]:
    """Parse draw records from official Taiwan Lottery API response."""
    cfg = LOTTERY_CONFIG[lottery_type]
    draws = []
    for item in data.get(cfg["res_key"]) or []:
        try:
            draw_date = item["lotteryDate"][:10]
            numbers = item[cfg["num_field"]]
            lo, hi = cfg["num_range"]
            if len(numbers) == cfg["num_count"] and all(lo <= n <= hi for n in numbers):
                draws.append((draw_date, numbers))
        except (KeyError, TypeError):
            continue
    return draws


def fetch_draws(start_month: str | None = None, lottery_type: str = "539") -> list[tuple[str, list[int]]]:
    """Fetch all draws for a given lottery type, month by month.

    Args:
        start_month: "YYYY-MM" to start from. Defaults to the type's earliest date.
        lottery_type: One of the keys in LOTTERY_CONFIG (e.g. "539", "649").

    Returns:
        List of (date, numbers) tuples, oldest first.
    """
    cfg = LOTTERY_CONFIG[lottery_type]
    if start_month:
        year, month = int(start_month[:4]), int(start_month[5:7])
    else:
        year, month = cfg["start"]

    today = date.today()
    all_draws = []

    while (year, month) <= (today.year, today.month):
        month_str = f"{year}-{month:02d}"
        response = requests.get(
            f"{API_BASE}/{cfg['path']}",
            params={
                "period": "",
                "month": month_str,
                "endMonth": month_str,
                "pageNum": 1,
                "pageSize": 31,
            },
            headers=HEADERS,
            timeout=10,
        )
        data = response.json().get("content", {})
        batch = parse_draws(data, lottery_type)
        all_draws.extend(sorted(batch))

        month += 1
        if month > 12:
            month = 1
            year += 1

    return all_draws

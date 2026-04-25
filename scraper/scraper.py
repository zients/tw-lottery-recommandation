# scraper/scraper.py
import time
import requests
from datetime import date

API_BASE = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery"
HEADERS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # seconds, doubled each retry

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
        "num_count": 7,   # 6 regular + 1 special ball (stored as flat list, special is last)
        "num_range": (1, 49),
        "start": (2007, 1),
        "analyze_count": 6,
        "odd_range": (2, 4),
        "sum_range": (90, 200),
    },
    "638": {
        "path": "SuperLotto638Result",
        "res_key": "superLotto638Res",
        "num_field": "drawNumberSize",
        "num_count": 7,   # 6 regular + 1 special ball (stored as flat list, special is last)
        "num_range": (1, 38),
        "start": (2008, 1),
        "analyze_count": 6,
        "odd_range": (2, 4),
        "sum_range": (70, 165),
        "special_range": (1, 8),
    },
    "3d": {
        "path": "3DResult",
        "res_key": "lotto3DRes",
        "num_field": "drawNumberAppear",
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
        "num_field": "drawNumberAppear",
        "num_count": 4,
        "num_range": (0, 9),
        "start": (2007, 1),
        "analyze_count": 4,
        "odd_range": None,
        "sum_range": None,
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


def _fetch_month(month_str: str, cfg: dict, lottery_type: str) -> list[tuple[str, list[int]]]:
    """Fetch one month with retries. Returns [] if all retries fail."""
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
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
            response.raise_for_status()
            data = response.json().get("content", {})
            return parse_draws(data, lottery_type)
        except (requests.RequestException, ValueError) as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF * (2**attempt))
    print(f"[warn] failed to fetch {month_str} after {MAX_RETRIES} attempts: {last_err}")
    return []


def fetch_draws(start_month: str | None = None, lottery_type: str = "539") -> list[tuple[str, list[int]]]:
    """Fetch all draws for a given lottery type, month by month.

    On per-month failure, retries up to MAX_RETRIES times with exponential
    backoff. If a month still fails, prints a warning and continues — partial
    results are returned so already-fetched draws aren't lost. Re-running
    update will resume from the latest stored date.

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
        batch = _fetch_month(month_str, cfg, lottery_type)
        all_draws.extend(sorted(batch))

        month += 1
        if month > 12:
            month = 1
            year += 1

    return all_draws

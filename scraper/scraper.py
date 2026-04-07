# scraper/scraper.py
import json
import requests

API_URL = "https://www.pilio.idv.tw/Json_lto.asp"


def parse_draws(data: dict) -> list[tuple[str, list[int]]]:
    """Parse draw records from pilio JSON response.

    Expected item format:
        {"date": "2007/01/01<br>(一)", "num": "09, 11, 27, 28, 38", "dex": "1"}
    """
    draws = []
    for item in data.get("lotto", []):
        try:
            # "2007/01/01<br>(一)" → "2007-01-01"
            raw_date = item["date"].split("<")[0].strip()
            date = raw_date.replace("/", "-")

            # "09, 11, 27, 28, 38" → [9, 11, 27, 28, 38]
            numbers = [int(n.strip()) for n in item["num"].split(",")]
            if len(numbers) == 5 and all(1 <= n <= 39 for n in numbers):
                draws.append((date, numbers))
        except (KeyError, ValueError):
            continue
    return draws


def fetch_draws(pages: int = 10) -> list[tuple[str, list[int]]]:
    """Fetch draw history from pilio API.

    Each page returns 10 records; pagination uses the last dex value.
    Ascending order (oldest first) with Ldesc=1.
    """
    all_draws = []
    index = 0
    for _ in range(pages):
        response = requests.post(
            API_URL,
            params={"Lkind": "lto539", "Lindex": index, "Ldesc": 1},
            timeout=10,
        )
        data = json.loads(response.text)
        batch = parse_draws(data)
        if not batch:
            break
        all_draws.extend(batch)
        index = int(data["lotto"][-1]["dex"])
    return all_draws

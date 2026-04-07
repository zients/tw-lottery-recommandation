# scraper/scraper.py
import requests
from bs4 import BeautifulSoup

HISTORY_URL = "https://www.taiwanlottery.com.tw/lotto/lotto539/history.aspx"


def parse_draws(html: str) -> list[tuple[str, list[int]]]:
    """Parse draw history from Taiwan Lottery 539 history page HTML.

    Each data row has 7 cells: draw_no | ROC_date | n1 | n2 | n3 | n4 | n5.
    ROC dates look like "114/04/06"; year is converted to CE by adding 1911.
    """
    soup = BeautifulSoup(html, "html.parser")
    draws = []
    for row in soup.select("table tr"):
        cells = row.find_all("td")
        if len(cells) < 7:
            continue
        try:
            raw_date = cells[1].get_text(strip=True)
            parts = raw_date.split("/")
            if len(parts) != 3:
                continue
            year = int(parts[0]) + 1911
            date = f"{year}-{parts[1]}-{parts[2]}"
            numbers = [int(cells[i].get_text(strip=True)) for i in range(2, 7)]
            if all(1 <= n <= 39 for n in numbers):
                draws.append((date, numbers))
        except (ValueError, IndexError):
            continue
    return draws


def fetch_draws(pages: int = 1) -> list[tuple[str, list[int]]]:
    """Fetch draw history from the Taiwan Lottery website.

    Args:
        pages: Number of history pages to fetch.

    Returns:
        List of (date, numbers) tuples where date is YYYY-MM-DD and
        numbers is a list of 5 integers in the range 1–39.
    """
    all_draws = []
    for page in range(1, pages + 1):
        params = {"p": page} if page > 1 else {}
        response = requests.get(HISTORY_URL, params=params, timeout=10)
        response.encoding = "utf-8"
        draws = parse_draws(response.text)
        all_draws.extend(draws)
        if not draws:
            break
    return all_draws

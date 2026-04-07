# tests/test_scraper.py
from pathlib import Path
from unittest.mock import patch, MagicMock
from scraper.scraper import parse_draws, fetch_draws

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_page.html"

def test_parse_draws_returns_list():
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    draws = parse_draws(html)
    assert isinstance(draws, list)
    assert len(draws) > 0

def test_parse_draws_structure():
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    draws = parse_draws(html)
    date, numbers = draws[0]
    assert isinstance(date, str)
    assert len(date) == 10  # YYYY-MM-DD
    assert isinstance(numbers, list)
    assert len(numbers) == 5
    assert all(1 <= n <= 39 for n in numbers)

def test_fetch_draws_calls_requests():
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    mock_response = MagicMock()
    mock_response.text = html
    with patch("scraper.scraper.requests.get", return_value=mock_response) as mock_get:
        result = fetch_draws(pages=1)
    mock_get.assert_called_once()
    assert isinstance(result, list)

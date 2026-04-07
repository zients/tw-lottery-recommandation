# tests/test_scraper.py
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from scraper.scraper import parse_draws, fetch_draws

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_response.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_parse_draws_returns_list():
    draws = parse_draws(load_fixture())
    assert isinstance(draws, list)
    assert len(draws) == 3


def test_parse_draws_structure():
    draws = parse_draws(load_fixture())
    date, numbers = draws[0]
    assert date == "2007-01-01"
    assert numbers == [9, 11, 27, 28, 38]


def test_parse_draws_all_numbers_in_range():
    draws = parse_draws(load_fixture())
    for _, numbers in draws:
        assert len(numbers) == 5
        assert all(1 <= n <= 39 for n in numbers)


def test_fetch_draws_calls_api():
    mock_response = MagicMock()
    mock_response.text = FIXTURE_PATH.read_text(encoding="utf-8")
    with patch("scraper.scraper.requests.post", return_value=mock_response) as mock_post:
        result = fetch_draws(pages=1)
    mock_post.assert_called_once()
    assert len(result) == 3


def test_fetch_draws_stops_on_empty():
    empty = json.dumps({"lotto": []})
    mock_response = MagicMock()
    mock_response.text = empty
    with patch("scraper.scraper.requests.post", return_value=mock_response):
        result = fetch_draws(pages=5)
    assert result == []

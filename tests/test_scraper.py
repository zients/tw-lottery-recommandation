# tests/test_scraper.py
import json
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock
from scraper.scraper import parse_draws, fetch_draws

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_response.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_parse_draws_returns_list():
    draws = parse_draws(load_fixture(), "539")
    assert isinstance(draws, list)
    assert len(draws) == 3


def test_parse_draws_structure():
    draws = parse_draws(load_fixture(), "539")
    # API returns newest-first; fixture has 3 items
    date, numbers = draws[0]
    assert date == "2007-01-03"
    assert numbers == [22, 23, 27, 29, 30]


def test_parse_draws_all_numbers_in_range():
    draws = parse_draws(load_fixture(), "539")
    for _, numbers in draws:
        assert len(numbers) == 5
        assert all(1 <= n <= 39 for n in numbers)


def test_fetch_draws_calls_api():
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": load_fixture()}
    with patch("scraper.scraper.requests.get", return_value=mock_response) as mock_get:
        result = fetch_draws(start_month="2007-01", lottery_type="539")
    mock_get.assert_called()
    assert len(result) >= 3


def test_fetch_draws_stops_on_empty():
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": {"totalSize": 0, "daily539Res": []}}
    with patch("scraper.scraper.requests.get", return_value=mock_response):
        result = fetch_draws(start_month="2007-01", lottery_type="539")
    assert result == []


def test_fetch_draws_sorted_oldest_first():
    # fixture has items newest-first; fetch_draws should return oldest-first
    current = f"{date.today().year}-{date.today().month:02d}"
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": load_fixture()}
    with patch("scraper.scraper.requests.get", return_value=mock_response):
        result = fetch_draws(start_month=current, lottery_type="539")
    dates = [r[0] for r in result]
    assert dates == sorted(dates)


def test_fetch_draws_uses_correct_endpoint_for_649():
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": {"lotto649Res": []}}
    with patch("scraper.scraper.requests.get", return_value=mock_response) as mock_get:
        fetch_draws(start_month="2007-01", lottery_type="649")
    url = mock_get.call_args[0][0]
    assert "Lotto649Result" in url


def _ok_response(content: dict) -> MagicMock:
    r = MagicMock()
    r.json.return_value = {"content": content}
    r.raise_for_status = MagicMock()
    return r


def test_fetch_draws_retries_on_transient_failure(monkeypatch):
    import requests as _requests
    monkeypatch.setattr("scraper.scraper.time.sleep", lambda *_: None)

    current = f"{date.today().year}-{date.today().month:02d}"
    ok = _ok_response(load_fixture())
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _requests.ConnectionError("boom")
        return ok

    with patch("scraper.scraper.requests.get", side_effect=flaky):
        result = fetch_draws(start_month=current, lottery_type="539")

    assert calls["n"] == 2  # retried once, then succeeded
    assert len(result) >= 3


def test_fetch_draws_gives_up_after_max_retries(monkeypatch, capsys):
    import requests as _requests
    monkeypatch.setattr("scraper.scraper.time.sleep", lambda *_: None)

    current = f"{date.today().year}-{date.today().month:02d}"
    with patch("scraper.scraper.requests.get",
               side_effect=_requests.ConnectionError("nope")):
        result = fetch_draws(start_month=current, lottery_type="539")

    assert result == []
    out = capsys.readouterr().out
    assert "failed to fetch" in out


def test_fetch_draws_returns_partial_when_some_months_fail(monkeypatch):
    import requests as _requests
    monkeypatch.setattr("scraper.scraper.time.sleep", lambda *_: None)

    today = date.today()
    # start two months ago so we span 3 months: T-2, T-1, T
    start_year, start_month = today.year, today.month - 2
    if start_month <= 0:
        start_month += 12
        start_year -= 1
    start = f"{start_year}-{start_month:02d}"

    ok = _ok_response(load_fixture())
    state = {"call": 0}

    def per_call(*args, **kwargs):
        state["call"] += 1
        # Month 1 → call 1 (ok). Month 2 → calls 2,3,4 (all fail = give up).
        # Month 3 → call 5 (ok).
        if 2 <= state["call"] <= 4:
            raise _requests.ConnectionError("middle month down")
        return ok

    with patch("scraper.scraper.requests.get", side_effect=per_call):
        result = fetch_draws(start_month=start, lottery_type="539")

    # 2 successful months × 3 fixture rows each = 6, middle month skipped
    assert len(result) == 6

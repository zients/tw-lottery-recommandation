from pathlib import Path

import pytest

from report.generator import LotteryPrediction, generate_html, write_report


def _pred539():
    return LotteryPrediction(
        lottery_type="539",
        name="今彩539",
        method="ML",
        combos=[[3, 12, 21, 30, 37], [5, 14, 22, 31, 38], [1, 9, 18, 27, 36]],
    )


def _pred638():
    return LotteryPrediction(
        lottery_type="638",
        name="威力彩",
        method="頻率",
        combos=[[2, 10, 18, 26, 33, 37], [4, 11, 19, 27, 34, 38]],
        special=5,
    )


def _pred3d():
    return LotteryPrediction(
        lottery_type="3d",
        name="3星彩",
        method="ML",
        combos=[[3, 7, 2]],
    )


def test_generate_html_contains_date():
    html = generate_html([_pred539()], "2026-05-25")
    assert "2026-05-25" in html


def test_generate_html_contains_lottery_name():
    html = generate_html([_pred539()], "2026-05-25")
    assert "今彩539" in html


def test_generate_html_shows_method_badge():
    html = generate_html([_pred539()], "2026-05-25")
    assert "ML" in html
    html2 = generate_html([_pred638()], "2026-05-25")
    assert "頻率" in html2


def test_generate_html_includes_numbers():
    html = generate_html([_pred539()], "2026-05-25")
    assert "21" in html
    assert "37" in html


def test_generate_html_special_ball():
    html = generate_html([_pred638()], "2026-05-25")
    assert "ball-s" in html


def test_generate_html_no_special_when_absent():
    html = generate_html([_pred539()], "2026-05-25")
    assert 'class="ball ball-s"' not in html


def test_generate_html_digit_style_for_3d():
    html = generate_html([_pred3d()], "2026-05-25")
    assert "ball-d" in html


def test_generate_html_is_valid_html():
    html = generate_html([_pred539()], "2026-05-25")
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_write_report_creates_index(tmp_path):
    index = write_report([_pred539()], tmp_path, "2026-05-25")
    assert index == tmp_path / "index.html"
    assert index.exists()


def test_write_report_defaults_to_today(tmp_path):
    from datetime import date
    index = write_report([_pred539()], tmp_path)
    assert index.name == "index.html"
    assert index.exists()


def test_write_report_creates_output_dir(tmp_path):
    out = tmp_path / "nested" / "dir"
    write_report([_pred539()], out, "2026-05-25")
    assert out.exists()


def test_write_report_multiple_lottery_types(tmp_path):
    preds = [_pred539(), _pred638(), _pred3d()]
    index = write_report(preds, tmp_path, "2026-05-25")
    html = index.read_text()
    assert "今彩539" in html
    assert "威力彩" in html
    assert "3星彩" in html

import pytest
from unittest.mock import patch
from data.db import init_db, insert_draw, get_all_draws
from cli import cmd_update, cmd_stats, cmd_recommend, cmd_train, main

@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path

@pytest.fixture
def seeded_db(db):
    for i in range(10):
        insert_draw(db, f"2024-01-{i+1:02d}", [i+1, i+2, i+3, i+4, i+5])
    return db

def test_update_inserts_new_draws(db):
    mock_draws = [("2024-01-01", [1, 2, 3, 4, 5])]
    with patch("cli.fetch_draws", return_value=mock_draws), patch("cli.DB_PATH", db):
        cmd_update(start_month="2024-01")
    assert len(get_all_draws(db)) == 1

def test_update_skips_duplicates(db):
    mock_draws = [("2024-01-01", [1, 2, 3, 4, 5])]
    with patch("cli.fetch_draws", return_value=mock_draws), patch("cli.DB_PATH", db):
        cmd_update(start_month="2024-01")
        cmd_update(start_month="2024-01")
    assert len(get_all_draws(db)) == 1

def test_update_auto_detects_start_month(seeded_db):
    mock_draws = [("2024-01-11", [5, 6, 7, 8, 9])]
    with patch("cli.fetch_draws", return_value=mock_draws), patch("cli.DB_PATH", seeded_db):
        cmd_update()  # no start_month - should auto-detect from DB
    assert len(get_all_draws(seeded_db)) == 11

def test_stats_runs_without_error(seeded_db):
    with patch("cli.DB_PATH", seeded_db):
        cmd_stats()

def test_recommend_runs_without_error(seeded_db):
    with patch("cli.DB_PATH", seeded_db):
        cmd_recommend()


def test_update_accepts_lottery_type(db):
    mock_draws = [("2024-01-01", [1, 2, 3, 4, 5, 6])]
    with patch("cli.fetch_draws", return_value=mock_draws), patch("cli.DB_PATH", db):
        cmd_update(start_month="2024-01", lottery_type="649")
    assert len(get_all_draws(db, "649")) == 1


def test_stats_accepts_lottery_type(seeded_db):
    with patch("cli.DB_PATH", seeded_db):
        cmd_stats(lottery_type="649")


def test_recommend_accepts_lottery_type(seeded_db):
    with patch("cli.DB_PATH", seeded_db):
        cmd_recommend(lottery_type="649")


def test_recommend_uses_ml_when_prediction_succeeds(seeded_db, capsys):
    with patch("cli.DB_PATH", seeded_db), \
         patch("cli.has_model", return_value=True), \
         patch("cli.ml_predict", return_value=[[1, 2, 3, 4, 5]]):
        cmd_recommend()
    out = capsys.readouterr().out
    assert "ML" in out
    assert "組合 1" in out


def test_recommend_falls_back_when_ml_raises_runtime_error(seeded_db, capsys):
    # Simulate a corrupt-checkpoint / shape-mismatch style failure (not ValueError)
    with patch("cli.DB_PATH", seeded_db), \
         patch("cli.has_model", return_value=True), \
         patch("cli.ml_predict", side_effect=RuntimeError("boom")):
        cmd_recommend()
    out = capsys.readouterr().out
    assert "ML 預測失敗" in out
    assert "頻率" in out


def test_recommend_falls_back_when_ml_raises_value_error(seeded_db):
    # Existing behavior (ValueError) must still work after broadening to Exception
    with patch("cli.DB_PATH", seeded_db), \
         patch("cli.has_model", return_value=True), \
         patch("cli.ml_predict", side_effect=ValueError("not enough data")):
        cmd_recommend()  # should not raise


# --- 638 (威力彩) special ball path -------------------------------------

@pytest.fixture
def seeded_638_db(db):
    # 638 stores 6 regular + 1 special (range 1-8) as a flat 7-element list
    for i in range(40):  # >30 so stats has data for hot/cold window
        regulars = [
            ((i + j) % 38) + 1 for j in range(6)
        ]
        special = (i % 8) + 1
        insert_draw(db, f"2024-01-{(i % 28) + 1:02d}", regulars + [special],
                    lottery_type="638")
    return db


def test_stats_638_runs_and_includes_special_table(seeded_638_db, capsys):
    with patch("cli.DB_PATH", seeded_638_db):
        cmd_stats(lottery_type="638")
    out = capsys.readouterr().out
    assert "威力彩" in out
    assert "特別號" in out  # special-ball table title


def test_recommend_638_outputs_special_number(seeded_638_db, capsys):
    with patch("cli.DB_PATH", seeded_638_db):
        cmd_recommend(lottery_type="638")
    out = capsys.readouterr().out
    assert "威力彩" in out
    assert "特別號" in out  # "+特別號 X" suffix on each combo


def test_recommend_539_does_not_output_special(seeded_db, capsys):
    # 539 has no special_range, so output should not mention 特別號
    with patch("cli.DB_PATH", seeded_db):
        cmd_recommend(lottery_type="539")
    out = capsys.readouterr().out
    assert "特別號" not in out


def test_train_prints_no_data_without_calling_ml_train(db, capsys):
    with patch("cli.DB_PATH", db), patch("cli.ml_train") as ml_train:
        cmd_train()
    out = capsys.readouterr().out
    assert "No data" in out
    ml_train.assert_not_called()


def test_train_passes_draws_and_config_to_ml_train(seeded_db):
    with patch("cli.DB_PATH", seeded_db), patch("cli.ml_train") as ml_train:
        cmd_train(lottery_type="539", epochs=7)

    ml_train.assert_called_once()
    args, kwargs = ml_train.call_args
    assert len(args[0]) == 10
    assert kwargs == {
        "lottery_type": "539",
        "num_range": (1, 39),
        "analyze_count": 5,
        "pick": 5,
        "epochs": 7,
    }


@pytest.mark.parametrize(
    ("argv", "mock_name", "expected_kwargs"),
    [
        (
            ["update", "--from-month", "2024-02", "--type", "649"],
            "cmd_update",
            {"start_month": "2024-02", "lottery_type": "649"},
        ),
        (
            ["stats", "--type", "638"],
            "cmd_stats",
            {"lottery_type": "638"},
        ),
        (
            ["train", "--type", "3d", "--epochs", "7"],
            "cmd_train",
            {"lottery_type": "3d", "epochs": 7},
        ),
        (
            ["recommend", "--type", "4d"],
            "cmd_recommend",
            {"lottery_type": "4d"},
        ),
    ],
)
def test_main_dispatches_subcommands(argv, mock_name, expected_kwargs):
    with patch("sys.argv", ["lottery", *argv]), patch(f"cli.{mock_name}") as command:
        main()

    command.assert_called_once_with(**expected_kwargs)


def test_main_prints_help_when_no_command(capsys):
    with patch("sys.argv", ["lottery"]):
        main()

    out = capsys.readouterr().out
    assert "台灣彩券分析與推薦工具" in out

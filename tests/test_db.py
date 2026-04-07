# tests/test_db.py
import sqlite3
from data.db import init_db, insert_draw, get_all_draws, get_recent_draws

def test_init_db_creates_table(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='draws'")
    assert cursor.fetchone() is not None
    conn.close()

def test_insert_and_get_all(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    insert_draw(db_path, "2024-01-01", [1, 2, 3, 4, 5])
    insert_draw(db_path, "2024-01-02", [6, 7, 8, 9, 10])
    rows = get_all_draws(db_path)
    assert len(rows) == 2
    assert rows[0] == ("2024-01-01", 1, 2, 3, 4, 5)
    assert rows[1] == ("2024-01-02", 6, 7, 8, 9, 10)

def test_get_recent_draws(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    for i in range(1, 11):
        insert_draw(db_path, f"2024-01-{i:02d}", [i, i+1, i+2, i+3, i+4])
    recent = get_recent_draws(db_path, 3)
    assert len(recent) == 3
    assert recent[0][0] == "2024-01-10"

def test_insert_duplicate_date_ignored(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    insert_draw(db_path, "2024-01-01", [1, 2, 3, 4, 5])
    insert_draw(db_path, "2024-01-01", [1, 2, 3, 4, 5])
    rows = get_all_draws(db_path)
    assert len(rows) == 1

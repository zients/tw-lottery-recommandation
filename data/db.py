# data/db.py
import sqlite3


def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS draws (
            date TEXT PRIMARY KEY,
            n1 INTEGER, n2 INTEGER, n3 INTEGER, n4 INTEGER, n5 INTEGER
        )
    """)
    conn.commit()
    conn.close()


def insert_draw(db_path: str, date: str, numbers: list[int]) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR IGNORE INTO draws (date, n1, n2, n3, n4, n5) VALUES (?, ?, ?, ?, ?, ?)",
        [date] + numbers
    )
    conn.commit()
    conn.close()


def get_all_draws(db_path: str) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT date, n1, n2, n3, n4, n5 FROM draws ORDER BY date ASC"
    ).fetchall()
    conn.close()
    return rows


def get_recent_draws(db_path: str, n: int) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT date, n1, n2, n3, n4, n5 FROM draws ORDER BY date DESC LIMIT ?", (n,)
    ).fetchall()
    conn.close()
    return rows

import os
import sqlite3
from pathlib import Path

DB_PATH = os.environ.get("IMVEST_DB", str(Path(__file__).parent.parent / "imvest.db"))


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init() -> None:
    with connect() as con:
        con.executescript((Path(__file__).parent / "schema_sqlite.sql").read_text())

import os
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
# Vercel: filesystem hanya-baca kecuali /tmp. Snapshot dibuat saat build (data/snapshot.sqlite3) lalu disalin ke /tmp.
SNAPSHOT = ROOT / "data" / "snapshot.sqlite3"
ON_VERCEL = bool(os.environ.get("VERCEL"))
DB_PATH = os.environ.get("IMVEST_DB", "/tmp/imvest.db" if ON_VERCEL else str(ROOT / "imvest.db"))


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init() -> None:
    if ON_VERCEL and SNAPSHOT.exists() and not Path(DB_PATH).exists():
        shutil.copy(SNAPSHOT, DB_PATH)
    with connect() as con:
        con.executescript((Path(__file__).parent / "schema_sqlite.sql").read_text())

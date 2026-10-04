import pytest

from app.nlp import sentiment
from app.nlp.sentiment import score


@pytest.mark.parametrize("title,expected", [
    ("Laba ANTM melonjak, saham menguat", "POSITIVE"),
    ("Nickel prices surge to record high", "POSITIVE"),
    ("Saham anjlok setelah kasus korupsi", "NEGATIVE"),
    ("Profit falls", "NEUTRAL"),
    ("Harga nikel tidak naik", "NEGATIVE"),
    ("Rapat pemegang saham digelar Selasa", "NEUTRAL"),
])
def test_score(title, expected):
    assert score(title) == expected


def test_run_fills_only_missing_and_is_idempotent(env):
    with env.connect() as con:
        con.execute("INSERT INTO news(title,url,published_at) VALUES ('Laba naik','u1','2026-01-01')")
        con.execute("INSERT INTO news(title,url,published_at,sentiment) VALUES ('Saham anjlok','u2','2026-01-01','POSITIVE')")
    assert sentiment.run() == 1 and sentiment.run() == 0
    with env.connect() as con:
        got = {r["url"]: r["sentiment"] for r in con.execute("SELECT url, sentiment FROM news")}
    assert got == {"u1": "POSITIVE", "u2": "POSITIVE"}

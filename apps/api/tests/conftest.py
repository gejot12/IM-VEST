import pytest
from fastapi.testclient import TestClient

PW = "test-password"


@pytest.fixture()
def env(tmp_path, monkeypatch):
    from app import db, seed
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "t.db"))
    seed.run(PW, fake_prices=True)
    return db


@pytest.fixture()
def client(env):
    from app.main import app
    return TestClient(app)


def login(c, email="investor@imvest.local"):
    r = c.post("/api/v1/auth/login", json={"email": email, "password": PW})
    assert r.status_code == 200
    return r

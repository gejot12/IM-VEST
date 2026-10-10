from conftest import PW, login


def test_requires_login_and_bad_password(client):
    assert client.get("/api/v1/market/overview").status_code == 401
    r = client.post("/api/v1/auth/login", json={"email": "investor@imvest.local", "password": "wrong"})
    assert r.status_code == 401


def test_login_lockout_after_repeated_failures(client):
    bad = {"email": "admin@imvest.local", "password": "salah"}
    assert [client.post("/api/v1/auth/login", json=bad).status_code for _ in range(5)] == [401] * 5
    assert client.post("/api/v1/auth/login", json=bad).status_code == 429
    # kunci tetap berlaku walau password benar, sampai jendela waktu lewat
    assert client.post("/api/v1/auth/login", json={"email": "admin@imvest.local", "password": PW}).status_code == 429
    from app import main
    main.FAILS.clear()


def test_company_search_and_page(client):
    login(client)
    assert client.get("/api/v1/companies", params={"q": "ANTM"}).json()[0]["ticker"] == "ANTM"
    c = client.get("/api/v1/companies/ANTM").json()
    assert c["price"]["source_type"] == "SEED" and "NICKEL" in c["commodities"]
    assert c["market_cap"] is None  # tidak mengarang saat fundamental belum ada


def test_prices_range(client):
    login(client)
    assert len(client.get("/api/v1/companies/ANTM/prices", params={"range": "1M"}).json()) == 30
    assert client.get("/api/v1/companies/ANTM/prices", params={"range": "9Y"}).status_code == 422


def test_no_data_is_explicit(client):
    login(client)
    r = client.get("/api/v1/companies/ANTM/fundamentals")
    assert r.status_code == 404 and r.json()["detail"]["code"] == "NO_DATA"
    assert client.get("/api/v1/companies/NOPE").status_code == 404


def test_sectors_dashboard_and_brief(client):
    login(client)
    assert len(client.get("/api/v1/market/sectors").json()) >= 5
    sec = client.get("/api/v1/sectors/ENERGY").json()
    assert sec["name"] == "Energy" and {c["ticker"] for c in sec["companies"]} >= {"PTBA", "ADRO"}
    d = client.get("/api/v1/dashboard").json()
    assert d["priorities"] and d["brief"]
    b = client.get("/api/v1/companies/ANTM/brief").json()
    assert b["facts"] and b["uncertainties"] and "bukan rekomendasi" in b["note"]


def test_analysis_needs_analyst_and_config(client, monkeypatch):
    login(client)
    assert client.post("/api/v1/companies/ANTM/analysis").status_code == 403
    login(client, "admin@imvest.local")
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    r = client.post("/api/v1/companies/ANTM/analysis")
    assert r.status_code == 503 and r.json()["detail"]["code"] == "NOT_CONFIGURED"


def test_login_with_plain_username_and_case_insensitive(client):
    for name, role in (("mahroja", "ADMIN"), ("Investor", "INVESTOR"), ("RM", "RM"), ("investor@imvest.local", "INVESTOR")):
        r = client.post("/api/v1/auth/login", json={"email": name, "password": PW})
        assert r.status_code == 200 and r.json()["role"] == role, name
    bad = client.post("/api/v1/auth/login", json={"email": "mahroja", "password": "salah"})
    assert bad.status_code == 401 and "username" in bad.json()["detail"]["message"]
    assert client.post("/api/v1/auth/login", json={"email": "tidak-ada", "password": PW}).status_code == 401

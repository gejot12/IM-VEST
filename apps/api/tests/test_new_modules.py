import json

from app import mapapi, scoring
from app.ingest import gnews, yahoo
from conftest import login


def test_scoring_normalizes_missing_and_labels():
    full = scoring.priority({"r1m": 0.1, "r3m": 0.2, "roe": 0.2, "pe": 8, "sentiment": 1, "catalyst": 0.5, "sector_change": 2})
    assert full["score"] >= 80 and full["label"] == "HIGH" and full["missing"] == [] and full["data_confidence"] == 1
    empty = scoring.priority({})
    assert empty["missing"] and empty["data_confidence"] == 0 and empty["label"] in ("LOW", "WATCH")
    bad = scoring.priority({"r1m": -0.3, "r3m": -0.3, "roe": -0.1, "pe": 40, "sentiment": 0, "catalyst": -0.5, "sector_change": -3})
    assert bad["label"] == "LOW"


def test_yahoo_parse_summary_tolerates_missing():
    f = yahoo.parse_summary({"summaryDetail": {"marketCap": {"raw": 5e12}, "trailingPE": {}}, "financialData": {}})
    assert f["market_cap"] == 5e12 and f["pe"] is None and f["roe"] is None


def test_yahoo_prices_store_and_skip_failures(env):
    def fake(sym, rng="1y"):
        if sym == "BBCA.JK":
            raise RuntimeError("boom")
        return [("2026-01-01", 100.0, 5), ("2026-01-02", 110.0, 6)]
    out = yahoo.prices(["ANTM", "BBCA"], fetcher=fake, delay=0)
    assert out == {"ANTM": 2}


def test_gnews_parse_strips_publisher_suffix():
    xml = b"""<rss><channel><item><title>Harga nikel naik - Kontan</title><link>https://x/1</link>
              <pubDate>Sun, 04 Oct 2026 05:00:00 GMT</pubDate><source url="u">Kontan</source></item></channel></rss>"""
    a = gnews.parse(xml)[0]
    assert a["title"] == "Harga nikel naik" and a["publisher"] == "Kontan" and a["url"] == "https://x/1"


def test_portfolio_and_rm_isolation(client, env):
    login(client)
    p = client.get("/api/v1/portfolio").json()
    assert p["positions"] and p["allocation"] and p["concentration_risk"] in ("LOW", "MODERATE", "HIGH")
    assert client.get("/api/v1/clients/radar").status_code == 403   # INVESTOR bukan RM
    login(client, "rm@imvest.local")
    radar = client.get("/api/v1/clients/radar").json()
    assert len(radar) == 8 and radar[0]["score"] >= radar[-1]["score"] and all(r["is_dummy"] for r in radar)
    brief = client.get(f"/api/v1/clients/{radar[0]['id']}/meeting-brief").json()
    assert brief["questions"] and "DUMMY" in brief["disclaimer"]
    with env.connect() as con:
        assert con.execute("SELECT COUNT(*) FROM audit_log WHERE action='VIEW_CLIENT'").fetchone()[0] == 1
        # klien milik RM lain tak boleh terlihat
        other = con.execute("INSERT INTO users(email,password_hash,role) VALUES ('rm2@x','x','RM')").lastrowid
        con.execute("UPDATE clients SET rm_id=? WHERE id=?", (other, radar[0]["id"]))
    assert client.get(f"/api/v1/clients/{radar[0]['id']}/meeting-brief").status_code == 404
    assert len(client.get("/api/v1/clients/radar").json()) == 7


def test_map_assets_flag_unverified_and_fires_need_key(client, monkeypatch):
    login(client)
    f = client.get("/api/v1/map/assets", params={"commodity": "nickel"}).json()["features"]
    assert f and all(not x["properties"]["verified"] for x in f)
    monkeypatch.delenv("FIRMS_MAP_KEY", raising=False)
    assert client.get("/api/v1/map/fires").json()["detail"]["code"] == "NEEDS_KEY"


def test_earthquakes_filtered_to_indonesia(client, monkeypatch):
    mapapi._cache.clear()
    feed = {"features": [
        {"geometry": {"coordinates": [120.0, -2.0, 10]}, "properties": {"mag": 5.1, "place": "Sulawesi", "time": 1, "url": "u"}},
        {"geometry": {"coordinates": [-100.0, 30.0, 5]}, "properties": {"mag": 4.0, "place": "Texas", "time": 1, "url": "u"}}]}
    monkeypatch.setattr(mapapi, "_json", lambda url: feed)
    login(client)
    got = client.get("/api/v1/map/earthquakes").json()["features"]
    assert [g["properties"]["place"] for g in got] == ["Sulawesi"]


def test_copilot_routes_and_refuses_unknown(client, env):
    login(client)

    def ask(q):
        return client.post("/api/v1/copilot/chat", json={"message": q}).json()
    a = ask("Analisis ANTM")
    assert "search_company" in a["tools"] and "FAKTA" in a["answer"] and "bukan rekomendasi" in a["answer"].lower()
    assert "search_commodity" in ask("Saham terkait nikel")["tools"]
    assert "search_location" in ask("Tampilkan aset nikel di peta")["tools"]
    assert "get_portfolio" in ask("risiko konsentrasi portofolio saya")["tools"]
    assert "RM" in ask("klien mana yang perlu dihubungi?")["answer"]
    assert ask("blablabla")["tools"] == []
    login(client, "rm@imvest.local")
    assert "list_client_opportunities" in ask("klien mana yang perlu dihubungi?")["tools"]


def test_watchlist_alerts_are_per_user_and_computed(client, env):
    login(client)
    assert client.get("/api/v1/watchlist/ANTM").json() == {"watched": False}
    assert client.put("/api/v1/watchlist/ANTM").status_code == 200 and client.put("/api/v1/watchlist/ANTM").status_code == 200  # idempoten
    assert client.put("/api/v1/watchlist/ZZZZ").status_code == 404
    with env.connect() as con:   # harga naik tajam + berita negatif berulang + event
        cid = con.execute("SELECT id FROM companies WHERE ticker='ANTM'").fetchone()["id"]
        last = con.execute("SELECT ts, close FROM prices WHERE company_id=? ORDER BY ts DESC LIMIT 1", (cid,)).fetchone()
        con.execute("UPDATE prices SET close=? WHERE company_id=? AND ts=?", (last["close"] * 1.2, cid, last["ts"]))
        for i in range(2):
            n = con.execute("INSERT INTO news(title,url,published_at,sentiment) VALUES (?,?,date('now'),'NEGATIVE')", (f"ANTM rugi {i}", f"u{i}")).lastrowid
            con.execute("INSERT INTO news_entities VALUES (?, 'COMPANY', ?)", (n, cid))
    kinds = {a["type"] for a in client.get("/api/v1/alerts").json()}
    assert {"PRICE", "NEWS"} <= kinds
    assert client.get("/api/v1/watchlist").json()[0]["alerts"] >= 2
    login(client, "rm@imvest.local")
    assert client.get("/api/v1/alerts").json() == []      # watchlist milik investor, bukan RM
    login(client)
    client.delete("/api/v1/watchlist/ANTM")
    assert client.get("/api/v1/alerts").json() == []


def test_supply_chain_fills_only_stages_with_data(client):
    login(client)
    r = client.get("/api/v1/supply-chain/nickel").json()
    by = {s["stage"]: s for s in r["stages"]}
    assert {a["ticker"] for a in by["Penambangan bijih"]["assets"]} >= {"INCO", "NCKL"}
    assert by["Baterai"]["assets"] == [] and by["Baterai"]["asset_type"] is None
    assert "ANTM" in r["exposed_companies"] and "generik" in r["note"]
    assert client.get("/api/v1/supply-chain/plutonium").status_code == 404


def test_production_requires_explicit_seed_password(env, monkeypatch):
    from app import auth, seed
    monkeypatch.setattr(auth, "PRODUCTION", True)
    monkeypatch.delenv("IMVEST_SEED_PASSWORD", raising=False)
    import pytest
    with pytest.raises(RuntimeError, match="IMVEST_SEED_PASSWORD"):
        seed.run()
    monkeypatch.setenv("IMVEST_SEED_PASSWORD", "x" * 12)
    seed.run()   # dengan password eksplisit berjalan


def test_bootstrap_fills_only_an_empty_database(tmp_path, monkeypatch):
    from app import db, main
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "empty.db"))
    db.init()
    calls = []
    assert main._bootstrap(spawn=calls.append) is True and len(calls) == 1
    from app import seed
    seed.run("pw-for-test")
    assert main._bootstrap(spawn=calls.append) is False and len(calls) == 1


def test_vercel_copies_snapshot_to_writable_path(tmp_path, monkeypatch):
    import sqlite3
    from app import db
    snap = tmp_path / "snap.sqlite3"
    c = sqlite3.connect(snap); c.execute("CREATE TABLE marker(x)"); c.execute("INSERT INTO marker VALUES (42)"); c.commit(); c.close()
    target = tmp_path / "tmp" / "imvest.db"
    target.parent.mkdir()
    monkeypatch.setattr(db, "ON_VERCEL", True)
    monkeypatch.setattr(db, "SNAPSHOT", snap)
    monkeypatch.setattr(db, "DB_PATH", str(target))
    db.init()
    with db.connect() as con:
        assert con.execute("SELECT x FROM marker").fetchone()[0] == 42   # data snapshot terbawa
        assert con.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0  # skema tetap dibuat
    # dingin kedua: tidak menimpa DB yang sudah ada (watchlist pengguna tetap)
    with db.connect() as con:
        con.execute("INSERT INTO marker VALUES (7)")
    db.init()
    with db.connect() as con:
        assert con.execute("SELECT COUNT(*) FROM marker").fetchone()[0] == 2


def test_production_secret_is_derived_or_refuses():
    import os
    import subprocess
    import sys
    base = {k: v for k, v in os.environ.items() if k not in ("IMVEST_JWT_SECRET", "IMVEST_SEED_PASSWORD", "VERCEL", "IMVEST_ENV")}
    cmd = [sys.executable, "-c", "import app.auth as a; print(a.SECRET[:8], a.PRODUCTION)"]
    refuse = subprocess.run(cmd, env={**base, "VERCEL": "1"}, capture_output=True, text=True)
    assert refuse.returncode != 0 and "IMVEST_SEED_PASSWORD" in refuse.stderr
    ok = subprocess.run(cmd, env={**base, "VERCEL": "1", "IMVEST_SEED_PASSWORD": "kata-sandi-uji-123"}, capture_output=True, text=True)
    assert ok.returncode == 0 and ok.stdout.split()[1] == "True" and not ok.stdout.startswith("dev-only")


def test_assets_cover_all_sectors_and_seed_is_idempotent(client, env):
    from app import seed
    login(client)
    f = client.get("/api/v1/map/assets").json()["features"]
    types = {x["properties"]["asset_type"] for x in f}
    assert {"MINE", "SMELTER", "PORT", "POWER_PLANT", "FACTORY", "PLANTATION", "TOLL_ROAD", "GAS_FIELD", "OFFICE", "AIRPORT", "BRANCH"} <= types
    sectors = {x["properties"]["sector"] for x in f}
    assert {"Financials", "Technology", "Infrastructures", "Energy", "Basic Materials", "Publik"} <= sectors  # bukan hanya tambang
    assert all(not x["properties"]["verified"] for x in f)
    n = len(f)
    seed.run(PW_FOR_SEED)   # jalan ulang tidak menggandakan aset
    assert len(client.get("/api/v1/map/assets").json()["features"]) == n
    ports = client.get("/api/v1/map/assets", params={"commodity": "coal"}).json()["features"]
    assert any(x["properties"]["asset_type"] == "PORT" for x in ports)
    chain = {s["stage"]: s for s in client.get("/api/v1/supply-chain/COAL").json()["stages"]}
    assert chain["Pengangkutan & pelabuhan"]["assets"]            # tahap pelabuhan kini berisi


PW_FOR_SEED = "test-password"


def test_airports_and_branches(client):
    login(client)
    f = client.get("/api/v1/map/assets").json()["features"]
    airports = [x for x in f if x["properties"]["asset_type"] == "AIRPORT"]
    assert len(airports) >= 20 and all(x["properties"]["ticker"] is None for x in airports)
    assert any("Soekarno-Hatta" in x["properties"]["name"] for x in airports)
    branches = [x for x in f if x["properties"]["asset_type"] == "BRANCH"]
    assert {x["properties"]["ticker"] for x in branches} == {"BBCA", "BBRI", "BMRI", "BBNI", "BRIS"}
    assert len(branches) == 5 * 12
    # filter emiten: hanya aset milik emiten itu, tanpa bandara umum
    bca = client.get("/api/v1/map/assets", params={"ticker": "BBCA"}).json()["features"]
    assert bca and all(x["properties"]["ticker"] == "BBCA" for x in bca)
    assert not any(x["properties"]["asset_type"] == "AIRPORT" for x in bca)

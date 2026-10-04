from app.nlp import events
from app.nlp.events import analyze, direction
from conftest import login

EXPO = {"COAL": [(1, "PTBA"), (2, "ADRO")], "NICKEL": [(3, "ANTM")]}


def impacts(title):
    r = analyze(title, EXPO)
    return r["event_type"], {i["ticker"]: i["direction"] for i in r["impacts"]}


def test_policy_cost_up_hurts_producers():
    want = ("POLICY", {"PTBA": "NEGATIVE", "ADRO": "NEGATIVE"})
    assert impacts("Pemerintah naikkan royalti batu bara") == want
    assert impacts("Pemerintah menaikkan royalti batu bara") == want


def test_policy_cut_helps_producers():
    assert impacts("Government cuts coal royalty") == ("POLICY", {"PTBA": "POSITIVE", "ADRO": "POSITIVE"})


def test_commodity_price_up_helps_producers_down_hurts():
    assert impacts("Harga nikel melonjak") == ("COMMODITY", {"ANTM": "POSITIVE"})
    assert impacts("Nickel prices plunge") == ("COMMODITY", {"ANTM": "NEGATIVE"})


def test_negation_flips_direction():
    assert direction("Harga nikel tidak naik") == -1
    assert impacts("Harga nikel tidak naik") == ("COMMODITY", {"ANTM": "NEGATIVE"})


def test_every_impact_has_reason_and_low_confidence():
    for i in analyze("Harga nikel naik", EXPO)["impacts"]:
        assert i["reason"] and i["confidence"] == "LOW" and abs(i["score"]) == 0.5


def test_volume_or_output_news_is_not_a_price_event():
    assert analyze("Volume Ekspor Batu Bara Januari-Agustus 2026 Merosot 9,33%", EXPO) is None
    assert analyze("Produksi nikel naik", EXPO) is None
    assert impacts("Harga batu bara turun, volume ekspor naik")[0] == "COMMODITY"   # kata harga ada


def test_not_an_event_and_disaster():
    assert analyze("Rapat pemegang saham digelar", EXPO) is None
    assert analyze("Harga nikel", EXPO) is None
    assert analyze("Gempa M6 guncang Sulawesi", EXPO) == {"event_type": "DISASTER", "impacts": []}


def test_events_api_and_role_gate(client, env):
    with env.connect() as con:
        con.execute("INSERT INTO news(title,url,published_at) VALUES ('Harga nikel melonjak','u1','2026-01-01')")
        con.execute("INSERT INTO news(title,url,published_at) VALUES ('Rapat digelar','u2','2026-01-02')")
    assert events.run() == 1 and events.run() == 0
    login(client)
    evs = client.get("/api/v1/events").json()
    assert [e["event_type"] for e in evs] == ["COMMODITY"]
    imp = client.get(f"/api/v1/events/{evs[0]['id']}/impacts").json()
    assert imp[0]["ticker"] == "ANTM" and imp[0]["reason"]
    assert client.get("/api/v1/events/999/impacts").status_code == 404
    assert client.post("/api/v1/events/analyze", json={"text": "Harga nikel naik"}).status_code == 403
    login(client, "admin@imvest.local")
    assert client.post("/api/v1/events/analyze", json={"text": "Harga nikel naik"}).json()["event_type"] == "COMMODITY"
    assert client.post("/api/v1/events/analyze", json={"text": "tidak relevan"}).status_code == 404

from app.nlp import rules

COMPANIES = [
    {"id": 1, "ticker": "ANTM", "name": "Aneka Tambang Tbk", "sector": "Basic Materials"},
    {"id": 2, "ticker": "BUMI", "name": "Bumi Resources Tbk", "sector": "Energy"},
    {"id": 3, "ticker": "BBCA", "name": "Bank Central Asia Tbk", "sector": "Financials"},
]
SECTORS = {"Basic Materials": 10, "Energy": 11, "Financials": 12}
COMMS = {"NICKEL": 20, "COAL": 21}


def ex(title):
    return rules.extract(title, COMPANIES, SECTORS, COMMS)


def test_company_by_name_and_ticker_adds_its_sector():
    assert ex("Aneka Tambang expands") == {("COMPANY", 1), ("SECTOR", 10)}
    assert ("COMPANY", 3) in ex("BBCA naik, perbankan menguat")


def test_commodity_implies_sector_and_is_bilingual():
    assert ex("Harga nikel naik, pemerintah ubah kebijakan") == {("COMMODITY", 20), ("SECTOR", 10)}
    assert ("COMMODITY", 21) in ex("Coal royalty raised")


def test_ticker_is_case_sensitive_but_name_match_is_not():
    assert ex("Kondisi bumi memanas") == set()
    assert ("COMPANY", 2) in ex("Bumi Resources rights issue")


def test_unrelated_title_yields_nothing():
    assert ex("Cuaca cerah di Jakarta") == set()


def test_run_is_idempotent(env):
    with env.connect() as con:
        con.execute("INSERT INTO news(title,url,published_at) VALUES ('Harga nikel naik, ANTM untung','u1','2026-01-01')")
    assert rules.run() >= 3 and rules.run() == 0


def test_short_name():
    assert rules.short_name("Bank Mandiri (Persero) Tbk") == "Bank Mandiri"
    assert rules.short_name("Aneka Tambang Tbk") == "Aneka Tambang"

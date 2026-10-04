"""Data referensi + data DUMMY. Harga/fundamental/berita nyata datang dari `python -m app.refresh`.

Semua yang ditandai SEED (aset perkiraan, klien, portofolio contoh) bukan data nyata.
"""
import csv
import os
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from . import db
from . import auth
from .auth import hash_password

CSV = Path(__file__).parents[3] / "seed" / "companies.csv"
DEV_USERS = [("admin@imvest.local", "ADMIN"), ("rm@imvest.local", "RM"), ("investor@imvest.local", "INVESTOR")]
COMMODITIES = ("NICKEL", "COAL", "CPO", "GOLD", "OIL", "COPPER")

# Lokasi kawasan operasi, PERKIRAAN (pusat kota/kawasan tambang), belum diverifikasi: verified_at NULL.
ASSETS = [  # ticker, tipe, nama, komoditas, lat, lng, provinsi
    ("ANTM", "SMELTER", "Pabrik feronikel Pomalaa", "NICKEL", -4.18, 121.62, "Sulawesi Tenggara"),
    ("ANTM", "MINE", "Tambang emas Pongkor", "GOLD", -6.65, 106.55, "Jawa Barat"),
    ("INCO", "MINE", "Tambang & pabrik Sorowako", "NICKEL", -2.53, 121.36, "Sulawesi Selatan"),
    ("NCKL", "MINE", "Tambang nikel Pulau Obi", "NICKEL", -1.55, 127.60, "Maluku Utara"),
    ("MBMA", "SMELTER", "Kawasan smelter Morowali", "NICKEL", -2.85, 122.17, "Sulawesi Tengah"),
    ("AMMN", "MINE", "Tambang Batu Hijau", "COPPER", -8.97, 116.87, "Nusa Tenggara Barat"),
    ("MDKA", "MINE", "Tambang Tujuh Bukit", "GOLD", -8.58, 114.05, "Jawa Timur"),
    ("PTBA", "MINE", "Tambang Tanjung Enim", "COAL", -3.77, 103.80, "Sumatera Selatan"),
    ("ADRO", "MINE", "Tambang Tabalong", "COAL", -2.20, 115.40, "Kalimantan Selatan"),
    ("ITMG", "MINE", "Tambang Indominco (Bontang)", "COAL", 0.10, 117.40, "Kalimantan Timur"),
    ("BUMI", "MINE", "Tambang Sangatta", "COAL", 0.50, 117.50, "Kalimantan Timur"),
]
HOLDINGS = {  # klien contoh: ticker -> lembar
    "A": {"BBCA": 200000, "BBRI": 300000, "BMRI": 150000},
    "B": {"ANTM": 400000, "INCO": 20000, "PTBA": 100000},
    "C": {"TLKM": 300000},
    "D": {"BBCA": 50000, "ASII": 80000, "UNVR": 60000, "ICBP": 20000},
    "E": {"ADRO": 100000, "ITMG": 5000, "PTBA": 200000, "BUMI": 3000000},
    "F": {"BBRI": 500000},
    "G": {"MDKA": 300000, "AMMN": 200000, "ANTM": 200000},
    "H": {"KLBF": 400000, "TLKM": 200000, "BBCA": 30000},
}


def _source(con, name, provider, kind):
    con.execute("INSERT OR IGNORE INTO data_sources(name, provider, source_type) VALUES (?,?,?)", (name, provider, kind))
    return con.execute("SELECT id FROM data_sources WHERE name=?", (name,)).fetchone()["id"]


def run(password: str | None = None, fake_prices: bool = False) -> None:
    password = password or os.environ.get("IMVEST_SEED_PASSWORD")
    if not password:
        if auth.PRODUCTION:  # tidak ada password bawaan di produksi
            raise RuntimeError("Set IMVEST_SEED_PASSWORD saat IMVEST_ENV=production")
        password = "dev-password"
    db.init()
    rng = random.Random(42)
    with db.connect() as con:
        seed_src = _source(con, "SEED mock", "IM-VEST", "SEED")
        for email, role in DEV_USERS:
            con.execute("INSERT OR IGNORE INTO users(email, password_hash, role) VALUES (?,?,?)",
                        (email, hash_password(password), role))
        for code in COMMODITIES:
            con.execute("INSERT OR IGNORE INTO commodities(code) VALUES (?)", (code,))
        ids = {}
        for row in csv.DictReader(CSV.open(encoding="utf-8")):
            sector = row["sector"]
            con.execute("INSERT OR IGNORE INTO sectors(code, name) VALUES (?,?)", (sector.upper().replace(" ", "_"), sector))
            sid = con.execute("SELECT id FROM sectors WHERE name=?", (sector,)).fetchone()["id"]
            con.execute("INSERT OR IGNORE INTO companies(ticker, name, sector_id) VALUES (?,?,?)", (row["ticker"], row["name"], sid))
            cid = ids[row["ticker"]] = con.execute("SELECT id FROM companies WHERE ticker=?", (row["ticker"],)).fetchone()["id"]
            for c in filter(None, row["commodity_exposure"].split(";")):
                con.execute("INSERT OR IGNORE INTO company_commodities VALUES (?,?)", (cid, c))
            if fake_prices:  # hanya untuk tes
                price = rng.uniform(500, 8000)
                for i in range(250, -1, -1):
                    price = max(50, price * (1 + rng.gauss(0, 0.015)))
                    con.execute("INSERT OR IGNORE INTO prices VALUES (?,?,?,?,?)",
                                (cid, (date.today() - timedelta(days=i)).isoformat(), round(price), 10**6, seed_src))
        if con.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 0:
            for t, typ, name, comm, lat, lng, prov in ASSETS:
                lid = con.execute("INSERT INTO locations(name, location_type, lat, lng, province, source_id) VALUES (?,?,?,?,?,?)",
                                  (name, typ, lat, lng, prov, seed_src)).lastrowid
                con.execute("INSERT INTO assets(company_id, asset_type, name, location_id, commodity, status) VALUES (?,?,?,?,?,?)",
                            (ids[t], typ, name, lid, comm, "UNKNOWN"))
        users = {r["email"]: r["id"] for r in con.execute("SELECT id, email FROM users")}
        if con.execute("SELECT COUNT(*) FROM clients").fetchone()[0] == 0:
            profiles = ["CONSERVATIVE", "MODERATE", "AGGRESSIVE"]
            for n, (key, hold) in enumerate(HOLDINGS.items(), 1):
                aum = rng.choice([2.5e9, 4.2e9, 8.2e9, 15e9, 6e9])
                cash = aum * rng.choice([0.05, 0.12, 0.25, 0.4])
                last = datetime.now() - timedelta(days=rng.choice([3, 12, 35, 70, 120]))
                cur = con.execute("""INSERT INTO clients(client_code, name, rm_id, risk_profile, aum, cash_balance, last_transaction_at)
                                     VALUES (?,?,?,?,?,?,?)""",
                                  (f"C-{n:03d}", f"Nasabah Contoh {key}", users["rm@imvest.local"], profiles[n % 3],
                                   aum, cash, last.isoformat(timespec="seconds")))
                for t, q in hold.items():
                    con.execute("INSERT INTO positions(client_id, company_id, quantity) VALUES (?,?,?)", (cur.lastrowid, ids[t], q))
        if con.execute("SELECT COUNT(*) FROM positions WHERE user_id IS NOT NULL").fetchone()[0] == 0:
            for t, q in {"BBCA": 20000, "ANTM": 50000, "TLKM": 30000, "ASII": 10000}.items():
                con.execute("INSERT INTO positions(user_id, company_id, quantity) VALUES (?,?,?)",
                            (users["investor@imvest.local"], ids[t], q))


if __name__ == "__main__":
    run()
    print("seeded")

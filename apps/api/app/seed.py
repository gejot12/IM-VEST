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

_LOCAL = Path(__file__).parent.parent / "data" / "companies.csv"
CSV = _LOCAL if _LOCAL.exists() else Path(__file__).parents[3] / "seed" / "companies.csv"
DEV_USERS = [("admin@imvest.local", "ADMIN"), ("rm@imvest.local", "RM"), ("investor@imvest.local", "INVESTOR"),
             ("mahroja@imvest.local", "ADMIN")]  # login cukup dengan username: mahroja
COMMODITIES = ("NICKEL", "COAL", "CPO", "GOLD", "OIL", "COPPER")

# Lokasi KAWASAN (pusat kota/distrik/kawasan operasi), PERKIRAAN dan belum diverifikasi: verified_at NULL.
# Tipe: MINE, SMELTER, PORT, POWER_PLANT, FACTORY, PLANTATION, GAS_FIELD, TOLL_ROAD, OFFICE.
ASSETS = [  # ticker, tipe, nama, komoditas, lat, lng, provinsi
    # Pertambangan & logam
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
    # Pelabuhan, energi, pembangkit
    ("PTBA", "PORT", "Pelabuhan Tarahan", "COAL", -5.47, 105.32, "Lampung"),
    ("PTBA", "PORT", "Dermaga Kertapati", "COAL", -3.00, 104.73, "Sumatera Selatan"),
    ("ITMG", "PORT", "Terminal batu bara Bontang", "COAL", 0.13, 117.49, "Kalimantan Timur"),
    ("BUMI", "PORT", "Pelabuhan Tanjung Bara (Sangatta)", "COAL", 0.57, 117.68, "Kalimantan Timur"),
    ("ADRO", "POWER_PLANT", "PLTU Batang (kemitraan)", "COAL", -6.88, 109.83, "Jawa Tengah"),
    ("AKRA", "PORT", "Kawasan pelabuhan & industri JIIPE (Gresik)", None, -7.00, 112.62, "Jawa Timur"),
    ("AKRA", "PORT", "Terminal BBM Tanjung Priok", None, -6.10, 106.88, "DKI Jakarta"),
    ("MEDC", "GAS_FIELD", "Lapangan gas Senoro-Toili", None, -1.35, 121.95, "Sulawesi Tengah"),
    # Infrastruktur
    ("JSMR", "TOLL_ROAD", "Koridor Tol Jakarta-Cikampek", None, -6.30, 107.20, "Jawa Barat"),
    ("JSMR", "TOLL_ROAD", "Koridor Tol Jagorawi", None, -6.40, 106.85, "Jawa Barat"),
    # Industri, konsumer, kesehatan, agribisnis
    ("ASII", "FACTORY", "Pabrik Astra Daihatsu Motor (kawasan Karawang)", None, -6.32, 107.30, "Jawa Barat"),
    ("UNVR", "FACTORY", "Pabrik Cikarang", None, -6.31, 107.17, "Jawa Barat"),
    ("INDF", "FACTORY", "Pabrik tepung Bogasari (Jakarta)", None, -6.105, 106.885, "DKI Jakarta"),
    ("KLBF", "FACTORY", "Pabrik Cikarang", None, -6.315, 107.15, "Jawa Barat"),
    ("AALI", "PLANTATION", "Perkebunan sawit (kawasan Kalimantan Tengah)", "CPO", -2.50, 112.30, "Kalimantan Tengah"),
    # Kantor pusat (kawasan)
    ("ANTM", "OFFICE", "Kantor pusat (Jakarta Selatan)", None, -6.292, 106.816, "DKI Jakarta"),
    ("INCO", "OFFICE", "Kantor pusat (Jakarta)", None, -6.243, 106.803, "DKI Jakarta"),
    ("MBMA", "OFFICE", "Kantor pusat (SCBD Jakarta)", None, -6.224, 106.8095, "DKI Jakarta"),
    ("NCKL", "OFFICE", "Kantor pusat (Jakarta Selatan)", None, -6.240, 106.820, "DKI Jakarta"),
    ("MDKA", "OFFICE", "Kantor pusat (SCBD Jakarta)", None, -6.2245, 106.810, "DKI Jakarta"),
    ("AMMN", "OFFICE", "Kantor pusat (SCBD Jakarta)", None, -6.225, 106.809, "DKI Jakarta"),
    ("ADRO", "OFFICE", "Kantor pusat (Kuningan Jakarta)", None, -6.221, 106.830, "DKI Jakarta"),
    ("ITMG", "OFFICE", "Kantor pusat (Pondok Indah Jakarta)", None, -6.265, 106.784, "DKI Jakarta"),
    ("BUMI", "OFFICE", "Kantor pusat (Kuningan Jakarta)", None, -6.218, 106.834, "DKI Jakarta"),
    ("PTBA", "OFFICE", "Kantor (Tanjung Enim)", None, -3.75, 103.78, "Sumatera Selatan"),
    ("PGAS", "OFFICE", "Kantor pusat (Jakarta Pusat)", None, -6.149, 106.816, "DKI Jakarta"),
    ("MEDC", "OFFICE", "Kantor pusat (SCBD Jakarta)", None, -6.225, 106.809, "DKI Jakarta"),
    ("AKRA", "OFFICE", "Kantor pusat (Kebon Jeruk Jakarta)", None, -6.190, 106.765, "DKI Jakarta"),
    ("BBCA", "OFFICE", "Kantor pusat (Thamrin Jakarta)", None, -6.195, 106.823, "DKI Jakarta"),
    ("BBRI", "OFFICE", "Kantor pusat (Sudirman Jakarta)", None, -6.2146, 106.8227, "DKI Jakarta"),
    ("BMRI", "OFFICE", "Kantor pusat (Gatot Subroto Jakarta)", None, -6.234, 106.818, "DKI Jakarta"),
    ("BBNI", "OFFICE", "Kantor pusat (Sudirman Jakarta)", None, -6.225, 106.8145, "DKI Jakarta"),
    ("BRIS", "OFFICE", "Kantor pusat (Jakarta)", None, -6.180, 106.818, "DKI Jakarta"),
    ("TLKM", "OFFICE", "Kantor pusat (Bandung)", None, -6.9175, 107.6191, "Jawa Barat"),
    ("ISAT", "OFFICE", "Kantor pusat (Jakarta Pusat)", None, -6.1722, 106.8227, "DKI Jakarta"),
    ("JSMR", "OFFICE", "Kantor pusat (TMII Jakarta)", None, -6.302, 106.895, "DKI Jakarta"),
    ("ASII", "OFFICE", "Kantor pusat (Sunter Jakarta)", None, -6.143, 106.870, "DKI Jakarta"),
    ("UNTR", "OFFICE", "Kantor pusat (Cakung Jakarta)", None, -6.195, 106.947, "DKI Jakarta"),
    ("UNVR", "OFFICE", "Kantor pusat (BSD Tangerang Selatan)", None, -6.302, 106.653, "Banten"),
    ("ICBP", "OFFICE", "Kantor pusat (Sudirman Jakarta)", None, -6.220, 106.8195, "DKI Jakarta"),
    ("INDF", "OFFICE", "Kantor pusat (Sudirman Jakarta)", None, -6.2205, 106.820, "DKI Jakarta"),
    ("AALI", "OFFICE", "Kantor pusat (Pulogadung Jakarta)", None, -6.185, 106.906, "DKI Jakarta"),
    ("KLBF", "OFFICE", "Kantor pusat (Cempaka Putih Jakarta)", None, -6.170, 106.871, "DKI Jakarta"),
    ("CPIN", "OFFICE", "Kantor pusat (Ancol Jakarta)", None, -6.128, 106.841, "DKI Jakarta"),
    ("GOTO", "OFFICE", "Kantor pusat (Blok M Jakarta)", None, -6.244, 106.799, "DKI Jakarta"),
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
        have = {(r["company_id"], r["name"]) for r in con.execute("SELECT company_id, name FROM assets")}
        for t, typ, name, comm, lat, lng, prov in ASSETS:   # idempoten: hanya yang belum ada
            if (ids[t], name) in have:
                continue
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

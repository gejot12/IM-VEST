"""Day 9: ekstraksi entitas berita berbasis kata kunci (tanpa LLM). Deterministik, bisa diuji.

Batas yang diketahui: tebakan judul saja, tanpa konteks. Ticker yang juga kata biasa
(BUMI, GOTO) bisa salah-tautan; ticker dicocokkan case-sensitive agar "bumi" biasa tidak kena.
Diganti/diperkuat LLM di tahap berikutnya; hasil aturan ini jadi baseline pembanding.
"""
import re

from .. import db

def short_name(name: str) -> str:
    return re.sub(r"\s*(\(Persero\)|Tbk)\s*", " ", name).strip()


COMMODITY_KW = {
    "NICKEL": r"nikel|nickel", "COAL": r"batu ?bara|coal", "CPO": r"\bcpo\b|palm oil|kelapa sawit|sawit",
    "GOLD": r"\bemas\b|\bgold\b", "OIL": r"minyak|crude|\boil\b", "COPPER": r"tembaga|copper",
}
COMMODITY_SECTOR = {"NICKEL": "Basic Materials", "GOLD": "Basic Materials", "COPPER": "Basic Materials",
                    "COAL": "Energy", "OIL": "Energy", "CPO": "Consumer Non-Cyclicals"}
SECTOR_KW = {"Financials": r"\bbank\b|perbankan|banking", "Infrastructures": r"telekomunikasi|telecom|jalan tol"}


def extract(title: str, companies: list[dict], sectors: dict[str, int], commodities: dict[str, int]):
    """companies: [{id, ticker, name, sector}]; sectors/commodities: nama/kode → id. Return set (type, id)."""
    found: set[tuple[str, int]] = set()
    sector_names: set[str] = set()
    for c in companies:
        if re.search(rf"\b{c['ticker']}\b", title) or short_name(c["name"]).lower() in title.lower():
            found.add(("COMPANY", c["id"]))
            if c["sector"]:
                sector_names.add(c["sector"])
    for code, pat in COMMODITY_KW.items():
        if re.search(pat, title, re.I) and code in commodities:
            found.add(("COMMODITY", commodities[code]))
            sector_names.add(COMMODITY_SECTOR[code])
    for name, pat in SECTOR_KW.items():
        if re.search(pat, title, re.I):
            sector_names.add(name)
    found |= {("SECTOR", sectors[n]) for n in sector_names if n in sectors}
    return found


def run() -> int:
    """Ekstrak semua berita; idempoten. Return jumlah tautan baru."""
    with db.connect() as con:
        companies = [dict(r) for r in con.execute(
            "SELECT c.id, c.ticker, c.name, s.name AS sector FROM companies c LEFT JOIN sectors s ON s.id=c.sector_id")]
        sectors = {r["name"]: r["id"] for r in con.execute("SELECT id, name FROM sectors")}
        commodities = {r["code"]: r["id"] for r in con.execute("SELECT id, code FROM commodities")}
        added = 0
        for n in con.execute("SELECT id, title FROM news").fetchall():
            for etype, eid in extract(n["title"], companies, sectors, commodities):
                added += con.execute("INSERT OR IGNORE INTO news_entities VALUES (?,?,?)", (n["id"], etype, eid)).rowcount
    return added


if __name__ == "__main__":
    print(run())

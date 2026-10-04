"""Day 11: event engine berbasis aturan. Judul berita -> event + dampak per emiten (dengan alasan).

Dua pola saja (sengaja kecil):
  POLICY    royalti/pajak/bea naik|turun + komoditas  -> emiten berekposur: NEGATIVE|POSITIVE
  COMMODITY harga komoditas naik|turun                -> emiten berekposur: POSITIVE|NEGATIVE
  DISASTER  gempa/banjir/kebakaran hutan              -> event saja, dampak butuh data lokasi (Minggu 3)
Semua dampak: confidence LOW, inference_kind INFERENCE, skor ±0.5 tetap. Besaran sebenarnya tidak diketahui
dan eksposur berasal dari seed/company_commodities yang belum diverifikasi; jangan dibaca sebagai prediksi.
Tanpa konteks: "harga nikel tidak naik" ditangani negasi sederhana, kalimat kompleks tidak.
"""
import re

from .. import db
from .rules import COMMODITY_KW
from .sentiment import NEGATORS

UP = set("naik naikkan menaik menaikkan melonjak meroket menguat melesat surge surges surged rise rises rose rising jump jumps jumped rally soar soars soared raise raises hike hikes increase increases".split())
DOWN = set("turun menurunkan anjlok merosot melemah fall falls fell drop drops dropped plunge slump decline declines cut cuts lower reduce scrap hapus".split())
POLICY_KW = r"royalti|royalty|pajak|\btax\b|bea keluar|export duty|tarif"
DISASTER_KW = r"gempa|earthquake|banjir|flood|kebakaran hutan|wildfire"
PRICE_KW = r"harga|price|\bhba\b|\bhpe\b"
NONPRICE_KW = r"volume|ekspor|impor|produksi|export|import|output|saham|laba|dividen"
SCORE = 0.5


def direction(title: str) -> int:
    """+1 / -1 menurut kata arah pertama (dibalik oleh negasi di depannya); 0 bila tak ada."""
    words = re.findall(r"\w+", title.lower())
    for i, w in enumerate(words):
        if w in UP or w in DOWN:
            sign = 1 if w in UP else -1
            return -sign if i and words[i - 1] in NEGATORS else sign
    return 0


def analyze(title: str, exposure: dict[str, list[tuple[int, str]]]) -> dict | None:
    """exposure: komoditas -> [(company_id, ticker)]. Return {event_type, impacts} atau None bila bukan event."""
    if re.search(DISASTER_KW, title, re.I):
        return {"event_type": "DISASTER", "impacts": []}
    d = direction(title)
    commodity = next((c for c, p in COMMODITY_KW.items() if re.search(p, title, re.I)), None)
    if not d or not commodity:
        return None
    policy = bool(re.search(POLICY_KW, title, re.I))
    # "volume ekspor batu bara merosot" bukan harga turun: tanpa kata harga, topik non-harga dibuang
    if not policy and re.search(NONPRICE_KW, title, re.I) and not re.search(PRICE_KW, title, re.I):
        return None
    # kebijakan biaya naik merugikan produsen; harga naik menguntungkan produsen
    sign = -d if policy else d
    what = f"Biaya/kebijakan {commodity} {'naik' if d > 0 else 'turun'}" if policy else f"Harga {commodity} {'naik' if d > 0 else 'turun'}"
    return {
        "event_type": "POLICY" if policy else "COMMODITY",
        "impacts": [{
            "company_id": cid, "ticker": t, "direction": "POSITIVE" if sign > 0 else "NEGATIVE",
            "score": sign * SCORE, "confidence": "LOW",
            "reason": f"{what} (dari judul); {t} tercatat berekposur {commodity}. Inferensi kata kunci, besaran tidak diketahui.",
        } for cid, t in exposure.get(commodity, [])],
    }


def exposure_map(con) -> dict[str, list[tuple[int, str]]]:
    out: dict[str, list[tuple[int, str]]] = {}
    for r in con.execute("""SELECT cc.commodity, c.id, c.ticker FROM company_commodities cc
                            JOIN companies c ON c.id=cc.company_id"""):
        out.setdefault(r["commodity"], []).append((r["id"], r["ticker"]))
    return out


def run() -> int:
    """Buat event dari berita yang belum diproses; idempoten (satu event per berita). Return jumlah event baru."""
    created = 0
    with db.connect() as con:
        exposure = exposure_map(con)
        for n in con.execute("SELECT id, title, published_at FROM news WHERE id NOT IN (SELECT news_id FROM events)").fetchall():
            a = analyze(n["title"], exposure)
            if not a:
                continue
            eid = con.execute("INSERT INTO events(news_id, event_type, title, ts, confidence) VALUES (?,?,?,?,'LOW')",
                              (n["id"], a["event_type"], n["title"], n["published_at"])).lastrowid
            con.executemany(
                "INSERT INTO event_impacts VALUES (?,?,?,?,?,?,?)",
                [(eid, "COMPANY", i["company_id"], i["direction"], i["score"], i["confidence"], i["reason"]) for i in a["impacts"]])
            created += 1
    return created


if __name__ == "__main__":
    print(run())

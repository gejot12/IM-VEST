"""Ringkasan berbasis aturan: FAKTA (dari data bersumber) dipisah dari INFERENSI dan KETIDAKPASTIAN. Tanpa LLM."""
from . import queries, scoring


def _pct(v):
    return "n/a" if v is None else f"{v * 100:+.1f}%"


def _idr(v):
    return "n/a" if v is None else (f"Rp{v / 1e12:,.1f} T" if v >= 1e12 else f"Rp{v / 1e9:,.1f} M")


def company_brief(con, c) -> dict:
    facts, inf, unc = [], [], []
    p, st = queries.price_info(con, c["id"]), queries.stats(con, c["id"])
    if p:
        facts.append(f"Harga {p['close']:,.0f} per {p['as_of']} ({p['source']}); harian {p['change_pct']}%, 1 bulan {_pct(p['r1m'])}, 3 bulan {_pct(p['r3m'])}.")
    else:
        unc.append("Harga belum tersedia; jalankan refresh data.")
    if st:
        facts.append(f"Market cap {_idr(st['market_cap'])}, PER {st['pe'] if st['pe'] is None else round(st['pe'], 1)}, PBV "
                     f"{st['pbv'] if st['pbv'] is None else round(st['pbv'], 2)}, ROE {_pct(st['roe'])} ({st['source']}, TTM per {st['as_of']}).")
    else:
        unc.append("Fundamental belum tersedia.")
    comms = [r["commodity"] for r in con.execute("SELECT commodity FROM company_commodities WHERE company_id=?", (c["id"],))]
    if comms:
        inf.append(f"Tercatat berekposur komoditas {', '.join(comms)} (daftar internal, belum diverifikasi ke laporan perusahaan).")
        unc.append("Besar kecilnya eksposur komoditas terhadap pendapatan tidak diketahui.")
    items = queries.news(con, ("COMPANY", c["id"]), days=7, limit=50)
    if items:
        counts = {s: sum(1 for n in items if n["sentiment"] == s) for s in ("POSITIVE", "NEUTRAL", "NEGATIVE")}
        facts.append(f"{len(items)} berita 7 hari terakhir: {counts['POSITIVE']} positif, {counts['NEUTRAL']} netral, {counts['NEGATIVE']} negatif (nada judul, aturan kata kunci).")
    else:
        unc.append("Tidak ada berita 7 hari terakhir yang tertaut ke emiten ini.")
    for i in queries.recent_impacts(con, c["id"]):
        inf.append(f"{i['title']} → {i['direction']} ({i['confidence']}): {i['reason']}")
    unc.append("Analisis berita hanya dari judul dengan kata kunci; belum membaca isi artikel.")
    pr = scoring.priority(queries.score_inputs(con, c))
    return {"facts": facts, "inferences": inf, "uncertainties": unc, "priority": pr,
            "note": "Research Priority Score = urutan bahan riset, bukan rekomendasi beli/jual."}


def top_priorities(con, n: int = 6) -> list[dict]:
    out = []
    for c in con.execute("SELECT id, ticker, name, sector_id FROM companies").fetchall():
        pr = scoring.priority(queries.score_inputs(con, c))
        out.append({"ticker": c["ticker"], "name": c["name"], **pr})
    return sorted(out, key=lambda x: -x["score"])[:n]


def market_brief(con) -> list[str]:
    """Kalimat ringkas hari ini, semuanya turunan angka tersimpan."""
    lines, sec = [], queries.sector_changes(con)
    if sec:
        up, dn = sec[0], sec[-1]
        lines.append(f"Sektor terkuat: {up['name']} ({up['change_pct']:+.2f}%); terlemah: {dn['name']} ({dn['change_pct']:+.2f}%).")
    movers = []
    for c in con.execute("SELECT id, ticker FROM companies").fetchall():
        p = queries.price_info(con, c["id"])
        if p and p["change_pct"] is not None:
            movers.append((c["ticker"], p["change_pct"]))
    movers.sort(key=lambda x: -x[1])
    if movers:
        lines.append("Naik terbesar: " + ", ".join(f"{t} {v:+.1f}%" for t, v in movers[:3]) +
                     ". Turun terbesar: " + ", ".join(f"{t} {v:+.1f}%" for t, v in movers[-3:][::-1]) + ".")
    ev = con.execute("SELECT COUNT(*) FROM events WHERE ts >= date('now','-3 day')").fetchone()[0]
    lines.append(f"{ev} event terdeteksi 3 hari terakhir (aturan kata kunci)." if ev else "Belum ada event terdeteksi 3 hari terakhir.")
    return lines

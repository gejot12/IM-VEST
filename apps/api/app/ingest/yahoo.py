"""Harga, kuotasi pasar, dan fundamental TTM dari Yahoo Finance (endpoint TIDAK resmi, tanpa key).

Cocok untuk prototipe/pemakaian pribadi. Produksi: ganti dengan IDX Data Services (berlisensi).
Setiap baris ditandai source 'Yahoo Finance (unofficial)'. Data tak tersedia dilewati, bukan ditebak.
"""
import http.cookiejar
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from .. import db

UA = {"User-Agent": "Mozilla/5.0"}
SOURCE = ("Yahoo Finance (unofficial)", "Yahoo", "THIRD_PARTY")
QUOTES = [("IHSG", "IHSG", "^JKSE"), ("LQ45", "LQ45", "^JKLQ45"), ("USDIDR", "USD/IDR", "IDR=X"),
          ("GOLD", "Emas (USD/oz)", "GC=F"), ("OIL", "Minyak WTI (USD/bbl)", "CL=F"),
          ("COAL", "Batu bara Newcastle (USD/t)", "MTF=F"), ("COPPER", "Tembaga (USD/lb)", "HG=F")]
# Nikel tidak tersedia gratis di Yahoo: sengaja tidak ada baris (UI menampilkan "tidak tersedia").


def _get(url: str, opener=None) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with (opener.open(req, timeout=30) if opener else urllib.request.urlopen(req, timeout=30)) as r:
        return json.loads(r.read())


def chart(symbol: str, rng: str = "1y") -> list[tuple[str, float, int | None]]:
    d = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?range={rng}&interval=1d")
    res = (d.get("chart") or {}).get("result")
    if not res:
        return []
    r = res[0]
    q = r["indicators"]["quote"][0] if r.get("indicators", {}).get("quote") else {}
    closes = q.get("close")
    if not closes or not r.get("timestamp"):
        return []
    vols = q.get("volume") or [None] * len(closes)
    off = r["meta"].get("gmtoffset", 0)
    return [(datetime.fromtimestamp(t + off, timezone.utc).date().isoformat(), c, v)
            for t, c, v in zip(r["timestamp"], closes, vols) if c is not None]


def _source_id(con) -> int:
    con.execute("INSERT OR IGNORE INTO data_sources(name, provider, source_type) VALUES (?,?,?)", SOURCE)
    return con.execute("SELECT id FROM data_sources WHERE name=?", (SOURCE[0],)).fetchone()["id"]


def prices(tickers: list[str] | None = None, fetcher=chart, delay: float = 0.25) -> dict[str, int]:
    out = {}
    with db.connect() as con:
        src = _source_id(con)
        rows = con.execute("SELECT id, ticker FROM companies").fetchall()
        for c in rows:
            if tickers and c["ticker"] not in tickers:
                continue
            try:
                bars = fetcher(c["ticker"] + ".JK")
            except Exception as e:  # satu ticker gagal tidak menghentikan yang lain
                print(f"skip {c['ticker']}: {e}")
                continue
            con.executemany("INSERT OR REPLACE INTO prices VALUES (?,?,?,?,?)",
                            [(c["id"], d, round(p, 2), v, src) for d, p, v in bars])
            out[c["ticker"]] = len(bars)
            time.sleep(delay)
    return out


def quotes(fetcher=chart) -> list[str]:
    ok = []
    with db.connect() as con:
        src = _source_id(con)
        for code, name, sym in QUOTES:
            try:
                bars = fetcher(sym, "5d")
            except Exception as e:
                print(f"skip {code}: {e}")
                continue
            if len(bars) < 2:
                continue
            (_, prev, _), (d, last, _) = bars[-2], bars[-1]
            con.execute("INSERT OR REPLACE INTO market_quotes VALUES (?,?,?,?,?,?)",
                        (code, name, round(last, 2), round((last / prev - 1) * 100, 2), d, src))
            ok.append(code)
    return ok


def _raw(d: dict, module: str, key: str):
    v = ((d.get(module) or {}).get(key) or {})
    return v.get("raw") if isinstance(v, dict) else None


def parse_summary(d: dict) -> dict:
    return {"market_cap": _raw(d, "summaryDetail", "marketCap"), "pe": _raw(d, "summaryDetail", "trailingPE"),
            "dividend_yield": _raw(d, "summaryDetail", "dividendYield"), "pbv": _raw(d, "defaultKeyStatistics", "priceToBook"),
            "net_income": _raw(d, "defaultKeyStatistics", "netIncomeToCommon"),
            "revenue": _raw(d, "financialData", "totalRevenue"), "ebitda": _raw(d, "financialData", "ebitda"),
            "roe": _raw(d, "financialData", "returnOnEquity")}


def _session():
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    try:
        op.open(urllib.request.Request("https://fc.yahoo.com", headers=UA), timeout=20)
    except urllib.error.HTTPError:
        pass  # 404 dari fc.yahoo.com normal; cookie tetap terpasang
    crumb = op.open(urllib.request.Request("https://query1.finance.yahoo.com/v1/test/getcrumb", headers=UA), timeout=20).read().decode()
    return op, crumb


def fundamentals(tickers: list[str] | None = None, delay: float = 0.3) -> dict[str, bool]:
    op, crumb = _session()
    out = {}
    with db.connect() as con:
        src = _source_id(con)
        for c in con.execute("SELECT id, ticker FROM companies").fetchall():
            if tickers and c["ticker"] not in tickers:
                continue
            url = (f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{c['ticker']}.JK"
                   f"?modules=summaryDetail,defaultKeyStatistics,financialData&crumb={urllib.parse.quote(crumb)}")
            try:
                res = _get(url, op)["quoteSummary"]["result"][0]
            except Exception as e:
                print(f"skip {c['ticker']}: {e}")
                out[c["ticker"]] = False
                continue
            f = parse_summary(res)
            con.execute("""INSERT OR REPLACE INTO fundamentals(company_id, period, revenue, ebitda, net_income, roe,
                           market_cap, pe, pbv, dividend_yield, as_of, source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (c["id"], "TTM", f["revenue"], f["ebitda"], f["net_income"], f["roe"], f["market_cap"], f["pe"],
                         f["pbv"], f["dividend_yield"], datetime.now().date().isoformat(), src))
            out[c["ticker"]] = True
            time.sleep(delay)
    return out


if __name__ == "__main__":
    print("quotes", quotes())
    print("prices", prices())
    print("fundamentals", fundamentals())

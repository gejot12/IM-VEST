"""Query bersama (dipakai routes, copilot, portofolio). Semua mengembalikan dict biasa."""
from datetime import date, timedelta

SENT = {"POSITIVE": 1.0, "NEUTRAL": 0.5, "NEGATIVE": 0.0}


def company(con, ticker: str):
    return con.execute("""SELECT c.id, c.ticker, c.name, c.sector_id, s.name AS sector FROM companies c
                          LEFT JOIN sectors s ON s.id=c.sector_id WHERE c.ticker=?""", (ticker.upper(),)).fetchone()


def sector_changes(con) -> list[dict]:
    """Rata-rata perubahan close terakhir vs sebelumnya per sektor."""
    return [dict(r) for r in con.execute("""
      WITH ranked AS (
        SELECT c.sector_id, p.company_id, p.close, ROW_NUMBER() OVER (PARTITION BY p.company_id ORDER BY p.ts DESC) rn
        FROM prices p JOIN companies c ON c.id = p.company_id),
      chg AS (SELECT a.sector_id, (a.close / b.close - 1) * 100 AS pct
              FROM ranked a JOIN ranked b ON a.company_id = b.company_id AND a.rn = 1 AND b.rn = 2)
      SELECT s.id, s.code, s.name, ROUND(AVG(pct), 2) AS change_pct, COUNT(*) AS companies
      FROM chg JOIN sectors s ON s.id = chg.sector_id GROUP BY s.id ORDER BY change_pct DESC""")]


def price_info(con, company_id: int) -> dict | None:
    """Harga terakhir + return harian/1B/3B dari data tersimpan."""
    rows = con.execute("""SELECT p.ts, p.close, ds.name AS source, ds.source_type FROM prices p
                          JOIN data_sources ds ON ds.id=p.source_id WHERE p.company_id=? ORDER BY p.ts DESC LIMIT 64""",
                       (company_id,)).fetchall()
    if not rows:
        return None
    last = rows[0]

    def ret(n):
        return (last["close"] / rows[n]["close"] - 1) if len(rows) > n else None
    return {"as_of": last["ts"], "close": last["close"], "source": last["source"], "source_type": last["source_type"],
            "change_pct": round(ret(1) * 100, 2) if ret(1) is not None else None, "r1m": ret(21), "r3m": ret(63)}


def stats(con, company_id: int) -> dict | None:
    r = con.execute("""SELECT f.*, s.name AS source FROM fundamentals f JOIN data_sources s ON s.id=f.source_id
                       WHERE f.company_id=? ORDER BY f.period DESC LIMIT 1""", (company_id,)).fetchone()
    return dict(r) if r else None


NEWS_SQL = """
SELECT n.id, n.title, n.url, n.publisher, n.published_at, n.sentiment, s.name AS source, s.source_type,
 (SELECT group_concat(label, '|') FROM (
    SELECT c.ticker AS label FROM news_entities e JOIN companies c ON e.entity_type='COMPANY' AND c.id=e.entity_id WHERE e.news_id=n.id
    UNION ALL SELECT sc.name FROM news_entities e JOIN sectors sc ON e.entity_type='SECTOR' AND sc.id=e.entity_id WHERE e.news_id=n.id
    UNION ALL SELECT cm.code FROM news_entities e JOIN commodities cm ON e.entity_type='COMMODITY' AND cm.id=e.entity_id WHERE e.news_id=n.id
 )) AS entities
FROM news n LEFT JOIN data_sources s ON s.id=n.source_id"""


def news(con, entity: tuple[str, int] | None = None, sentiment: str | None = None, days: int | None = None, limit: int = 30):
    where, args = [], []
    if entity:
        where.append("EXISTS (SELECT 1 FROM news_entities e WHERE e.news_id=n.id AND e.entity_type=? AND e.entity_id=?)")
        args += list(entity)
    if sentiment:
        where.append("n.sentiment=?")
        args.append(sentiment)
    if days:
        where.append("n.published_at >= ?")
        args.append((date.today() - timedelta(days=days)).isoformat())
    sql = NEWS_SQL + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY n.published_at DESC LIMIT ?"
    out = []
    for r in con.execute(sql, args + [limit]):
        d = dict(r)
        d["entities"] = d["entities"].split("|") if d["entities"] else []
        out.append(d)
    return out


def recent_impacts(con, company_id: int, days: int = 14) -> list[dict]:
    return [dict(r) for r in con.execute("""
        SELECT e.id AS event_id, e.title, e.event_type, e.ts, i.direction, i.score, i.confidence, i.reason
        FROM event_impacts i JOIN events e ON e.id=i.event_id
        WHERE i.entity_type='COMPANY' AND i.entity_id=? AND e.ts >= ? ORDER BY e.ts DESC""",
                                    (company_id, (date.today() - timedelta(days=days)).isoformat()))]


def score_inputs(con, c) -> dict:
    """Bahan skor prioritas untuk satu emiten (None = tidak ada data)."""
    p, st = price_info(con, c["id"]), stats(con, c["id"])
    ns = [SENT[n["sentiment"]] for n in news(con, ("COMPANY", c["id"]), days=7, limit=50) if n["sentiment"]]
    imp = recent_impacts(con, c["id"])
    chg = next((s["change_pct"] for s in sector_changes(con) if s["id"] == c["sector_id"]), None)
    return {"r1m": p and p["r1m"], "r3m": p and p["r3m"], "roe": st and st["roe"], "pe": st and st["pe"],
            "sentiment": sum(ns) / len(ns) if ns else None, "catalyst": sum(i["score"] for i in imp) / len(imp) if imp else None,
            "sector_change": chg}

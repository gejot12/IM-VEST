"""Watchlist per pengguna + alert yang dihitung saat diminta (tanpa penjadwal): gerak harga, event berdampak, berita negatif."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from . import db, queries
from .auth import current_user, require

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require("INVESTOR"))])
PRICE_MOVE = 3.0        # % harian
NEG_NEWS = 2            # jumlah berita negatif 3 hari terakhir
SEVERITY = {"EVENT": 0, "PRICE": 1, "NEWS": 2}


def alerts_for(con, company) -> list[dict]:
    out, t = [], company["ticker"]
    p = queries.price_info(con, company["id"])
    if p and p["change_pct"] is not None and abs(p["change_pct"]) >= PRICE_MOVE:
        out.append({"type": "PRICE", "ticker": t, "text": f"{t} bergerak {p['change_pct']:+.2f}% (per {p['as_of']})", "direction": "POSITIVE" if p["change_pct"] > 0 else "NEGATIVE"})
    groups: dict[str, list[dict]] = {}
    for i in queries.recent_impacts(con, company["id"], days=3):
        groups.setdefault(i["direction"], []).append(i)
    for direction, items in groups.items():   # satu alert per arah: banyak judul biasanya satu cerita
        first = items[0]
        more = f" (+{len(items) - 1} berita serupa)" if len(items) > 1 else ""
        out.append({"type": "EVENT", "ticker": t, "direction": direction,
                    "text": f"{first['title']}{more} → {direction} ({first['confidence']}): {first['reason']}"})
    neg = [n for n in queries.news(con, ("COMPANY", company["id"]), sentiment="NEGATIVE", days=3, limit=10)]
    if len(neg) >= NEG_NEWS:
        out.append({"type": "NEWS", "ticker": t, "text": f"{len(neg)} berita bernada negatif dalam 3 hari (judul, aturan kata kunci)", "direction": "NEGATIVE"})
    return out


def _watched(con, user_id: int):
    return con.execute("""SELECT c.id, c.ticker, c.name, s.name AS sector FROM watchlist w JOIN companies c ON c.id=w.company_id
                          LEFT JOIN sectors s ON s.id=c.sector_id WHERE w.user_id=? ORDER BY c.ticker""", (user_id,)).fetchall()


@router.get("/watchlist")
def watchlist(user: dict = Depends(current_user)):
    with db.connect() as con:
        items = []
        for c in _watched(con, user["id"]):
            p = queries.price_info(con, c["id"])
            items.append({"ticker": c["ticker"], "name": c["name"], "sector": c["sector"], "close": p and p["close"],
                          "change_pct": p and p["change_pct"], "as_of": p and p["as_of"], "alerts": len(alerts_for(con, c))})
        return items


@router.get("/alerts")
def alerts(user: dict = Depends(current_user)):
    with db.connect() as con:
        out = [a for c in _watched(con, user["id"]) for a in alerts_for(con, c)]
    return sorted(out, key=lambda a: (SEVERITY[a["type"]], a["ticker"]))


def _company_id(con, ticker: str) -> int:
    c = queries.company(con, ticker)
    if not c:
        raise HTTPException(404, {"code": "NO_DATA", "message": f"Emiten {ticker} tidak tersedia"})
    return c["id"]


@router.put("/watchlist/{ticker}")
def add(ticker: str, user: dict = Depends(current_user)):
    with db.connect() as con:
        con.execute("INSERT OR IGNORE INTO watchlist VALUES (?,?)", (user["id"], _company_id(con, ticker)))
    return {"ok": True}


@router.delete("/watchlist/{ticker}")
def remove(ticker: str, user: dict = Depends(current_user)):
    with db.connect() as con:
        con.execute("DELETE FROM watchlist WHERE user_id=? AND company_id=?", (user["id"], _company_id(con, ticker)))
    return {"ok": True}


@router.get("/watchlist/{ticker}")
def is_watched(ticker: str, user: dict = Depends(current_user)):
    with db.connect() as con:
        return {"watched": bool(con.execute("SELECT 1 FROM watchlist WHERE user_id=? AND company_id=?", (user["id"], _company_id(con, ticker))).fetchone())}

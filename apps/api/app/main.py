import os
import threading
import time
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel

from . import clients, copilot, db, insights, mapapi, queries, supply, watch
from .auth import PRODUCTION, current_user, make_token, require, verify_password
from .nlp import events


def _auto_refresh(hours: float) -> None:
    from . import refresh
    while True:
        time.sleep(hours * 3600)
        try:
            refresh.main(quick=True)
        except Exception as e:  # satu putaran gagal tidak boleh mematikan server
            print(f"auto-refresh gagal: {e}")


def _bootstrap(spawn=lambda f: threading.Thread(target=f, daemon=True).start()) -> bool:
    """DB kosong (mis. host dengan disk sementara): isi data di thread latar agar server langsung siap menjawab."""
    with db.connect() as con:
        empty = con.execute("SELECT COUNT(*) FROM companies").fetchone()[0] == 0
    if empty:
        from . import refresh
        spawn(refresh.main)
    return empty


@asynccontextmanager
async def lifespan(app):
    db.init()
    _bootstrap()
    hours = float(os.environ.get("IMVEST_AUTO_REFRESH_HOURS", 0))
    if hours > 0:  # opsional: perbarui harga/berita berkala di thread latar
        threading.Thread(target=_auto_refresh, args=(hours,), daemon=True).start()
    yield


app = FastAPI(title="IM-VEST Intelligence API", lifespan=lifespan)
api = APIRouter(prefix="/api/v1")
RANGE_DAYS = {"1M": 30, "3M": 90, "1Y": 366}
inv = [Depends(require("INVESTOR"))]


def no_data(what: str) -> HTTPException:
    return HTTPException(404, {"code": "NO_DATA", "message": f"{what} tidak tersedia"})


def get_company(con, ticker: str):
    c = queries.company(con, ticker)
    if not c:
        raise no_data(f"Emiten {ticker}")
    return c


class Login(BaseModel):
    email: str
    password: str


FAILS: dict[str, list[float]] = {}  # email -> waktu gagal; 5 gagal dalam 5 menit = kunci sementara (in-memory, per proses)


def normalize_login(value: str) -> str:
    """Boleh username saja ("mahroja") atau email lengkap; username dipetakan ke <nama>@imvest.local."""
    ident = value.strip().lower()
    return ident if "@" in ident else f"{ident}@imvest.local"


@api.post("/auth/login")
def login(body: Login, response: Response):
    ident = normalize_login(body.email)
    now = time.time()
    recent = [t for t in FAILS.get(ident, []) if now - t < 300]
    if len(recent) >= 5:
        raise HTTPException(429, {"code": "RATE_LIMIT", "message": "Terlalu banyak percobaan, coba lagi beberapa menit lagi"})
    with db.connect() as con:
        u = con.execute("SELECT * FROM users WHERE email=?", (ident,)).fetchone()
    if not u or not verify_password(body.password, u["password_hash"]):
        FAILS[ident] = recent + [now]
        raise HTTPException(401, {"code": "UNAUTHENTICATED", "message": "username atau password salah"})
    FAILS.pop(ident, None)
    response.set_cookie("session", make_token(u["id"], u["role"]), httponly=True, samesite="lax", secure=PRODUCTION, max_age=8 * 3600)
    return {"email": u["email"], "role": u["role"]}


@api.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"ok": True}


@api.get("/auth/me")
def me(user: dict = Depends(current_user)):
    with db.connect() as con:
        email = con.execute("SELECT email FROM users WHERE id=?", (user["id"],)).fetchone()["email"]
    return {**user, "email": email}


@api.get("/market/overview", dependencies=inv)
def market_overview():
    with db.connect() as con:
        rows = con.execute("""SELECT q.code, q.name, q.value, q.change_pct, q.as_of, s.name AS source, s.source_type
                              FROM market_quotes q JOIN data_sources s ON s.id=q.source_id""").fetchall()
    return [dict(r) for r in rows]


@api.get("/market/sectors", dependencies=inv)
def market_sectors():
    with db.connect() as con:
        return queries.sector_changes(con)


@api.get("/dashboard", dependencies=inv)
def dashboard():
    with db.connect() as con:
        return {"brief": insights.market_brief(con), "priorities": insights.top_priorities(con),
                "events": [dict(r) for r in con.execute("SELECT id, event_type, title, ts FROM events ORDER BY ts DESC LIMIT 6")]}


@api.get("/companies", dependencies=inv)
def search_companies(q: str = ""):
    like = f"%{q}%"
    with db.connect() as con:
        rows = con.execute("""SELECT c.ticker, c.name, s.name AS sector FROM companies c LEFT JOIN sectors s ON s.id=c.sector_id
                              WHERE c.ticker LIKE ? OR c.name LIKE ? ORDER BY c.ticker LIMIT 20""", (like, like)).fetchall()
    return [dict(r) for r in rows]


@api.get("/companies/{ticker}", dependencies=inv)
def company(ticker: str):
    with db.connect() as con:
        c = get_company(con, ticker)
        price, st = queries.price_info(con, c["id"]), queries.stats(con, c["id"])
        comms = [r["commodity"] for r in con.execute("SELECT commodity FROM company_commodities WHERE company_id=?", (c["id"],))]
    if price:
        price = {k: v for k, v in price.items() if k not in ("r1m", "r3m")}
    return {"ticker": c["ticker"], "name": c["name"], "sector": c["sector"], "commodities": comms, "price": price,
            "market_cap": st and st["market_cap"], "per": st and st["pe"], "pbv": st and st["pbv"],
            "roe": st and st["roe"], "dividend_yield": st and st["dividend_yield"],
            "stats_source": st and st["source"], "stats_as_of": st and st["as_of"]}


@api.get("/companies/{ticker}/prices", dependencies=inv)
def prices(ticker: str, range: str = "3M"):
    days = RANGE_DAYS.get(range)
    if not days:
        raise HTTPException(422, {"code": "BAD_RANGE", "message": f"range harus salah satu {list(RANGE_DAYS)}"})
    with db.connect() as con:
        c = get_company(con, ticker)
        rows = con.execute("""SELECT ts, close, volume FROM (SELECT * FROM prices WHERE company_id=?
                              ORDER BY ts DESC LIMIT ?) ORDER BY ts""", (c["id"], days)).fetchall()
    return [dict(r) for r in rows]


@api.get("/companies/{ticker}/fundamentals", dependencies=inv)
def fundamentals(ticker: str):
    with db.connect() as con:
        c = get_company(con, ticker)
        rows = con.execute("""SELECT f.period, f.revenue, f.ebitda, f.net_income, f.roe, f.as_of, s.name AS source
                              FROM fundamentals f JOIN data_sources s ON s.id=f.source_id
                              WHERE f.company_id=? ORDER BY f.period DESC""", (c["id"],)).fetchall()
    if not rows:
        raise no_data(f"Fundamental {c['ticker']}")
    return [dict(r) for r in rows]


@api.get("/companies/{ticker}/news", dependencies=inv)
def company_news(ticker: str):
    with db.connect() as con:
        return queries.news(con, ("COMPANY", get_company(con, ticker)["id"]), limit=20)


@api.get("/companies/{ticker}/brief", dependencies=inv)
def company_brief(ticker: str):
    with db.connect() as con:
        return insights.company_brief(con, get_company(con, ticker))


@api.post("/companies/{ticker}/analysis", dependencies=[Depends(require("ANALYST"))])
def deep_analysis(ticker: str):
    """Analisis multi-agent TradingAgents (lihat app/research). Butuh LLM + paket; jujur 503 bila belum dikonfigurasi."""
    from . import research
    with db.connect() as con:
        get_company(con, ticker)
    return research.run(ticker)


@api.get("/sectors/{code}", dependencies=inv)
def sector(code: str):
    with db.connect() as con:
        s = con.execute("SELECT id, code, name FROM sectors WHERE code=?", (code.upper(),)).fetchone()
        if not s:
            raise no_data(f"Sektor {code}")
        perf = next((x["change_pct"] for x in queries.sector_changes(con) if x["id"] == s["id"]), None)
        comps = []
        for c in con.execute("SELECT id, ticker, name FROM companies WHERE sector_id=? ORDER BY ticker", (s["id"],)).fetchall():
            p = queries.price_info(con, c["id"])
            comps.append({"ticker": c["ticker"], "name": c["name"], "close": p and p["close"], "change_pct": p and p["change_pct"],
                          "commodities": [r["commodity"] for r in con.execute("SELECT commodity FROM company_commodities WHERE company_id=?", (c["id"],))]})
        return {"code": s["code"], "name": s["name"], "change_pct": perf, "companies": comps,
                "news": queries.news(con, ("SECTOR", s["id"]), days=14, limit=10)}


@api.get("/news", dependencies=inv)
def news(ticker: str | None = None, sector: str | None = None, commodity: str | None = None, sentiment: str | None = None):
    with db.connect() as con:
        entity = None
        if ticker:
            entity = ("COMPANY", get_company(con, ticker)["id"])
        elif sector:
            r = con.execute("SELECT id FROM sectors WHERE code=?", (sector.upper(),)).fetchone()
            entity = ("SECTOR", r["id"]) if r else None
        elif commodity:
            r = con.execute("SELECT id FROM commodities WHERE code=?", (commodity.upper(),)).fetchone()
            entity = ("COMMODITY", r["id"]) if r else None
        return queries.news(con, entity, sentiment.upper() if sentiment else None, limit=50)


@api.get("/events", dependencies=inv)
def list_events():
    with db.connect() as con:
        rows = con.execute("""SELECT e.id, e.event_type, e.title, e.ts, e.confidence, n.url, n.publisher,
                                     (SELECT COUNT(*) FROM event_impacts i WHERE i.event_id=e.id) AS impacts
                              FROM events e LEFT JOIN news n ON n.id=e.news_id ORDER BY e.ts DESC LIMIT 50""").fetchall()
    return [dict(r) for r in rows]


@api.get("/events/{event_id}/impacts", dependencies=inv)
def event_impacts(event_id: int):
    with db.connect() as con:
        if not con.execute("SELECT 1 FROM events WHERE id=?", (event_id,)).fetchone():
            raise no_data(f"Event {event_id}")
        rows = con.execute("""SELECT c.ticker, c.name, i.direction, i.score, i.confidence, i.reason FROM event_impacts i
                              JOIN companies c ON c.id=i.entity_id AND i.entity_type='COMPANY'
                              WHERE i.event_id=? ORDER BY i.score""", (event_id,)).fetchall()
    return [dict(r) for r in rows]


class EventText(BaseModel):
    text: str


@api.post("/events/analyze", dependencies=[Depends(require("ANALYST"))])
def analyze_event(body: EventText):
    """Analisis teks bebas tanpa menyimpan. 404 NO_DATA bila bukan event yang dikenali aturan."""
    with db.connect() as con:
        result = events.analyze(body.text, events.exposure_map(con))
    if not result:
        raise no_data("Event dari teks ini")
    return result


app.include_router(api)
app.include_router(clients.router)
app.include_router(mapapi.router)
app.include_router(copilot.router)
app.include_router(watch.router)
app.include_router(supply.router)

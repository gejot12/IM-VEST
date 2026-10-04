"""Portofolio investor + Client Radar/Next Best Action/Meeting Brief untuk RM. Semua klien = DUMMY (clients.is_dummy).

Skor RM dan peluang dihitung deterministik di sini; teks hanya templat dari angka tersebut (tanpa LLM).
Akses: RM hanya melihat klien miliknya (rm_id), ADMIN semua; setiap pembukaan klien dicatat di audit_log.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from . import db, queries
from .auth import current_user, require

router = APIRouter(prefix="/api/v1")

POS_SQL = """SELECT c.id AS company_id, c.ticker, c.name, s.name AS sector, p.quantity, p.avg_cost
             FROM positions p JOIN companies c ON c.id=p.company_id LEFT JOIN sectors s ON s.id=c.sector_id WHERE """


def summarize(con, positions: list[dict]) -> dict:
    rows, total = [], 0.0
    for p in positions:
        info = queries.price_info(con, p["company_id"])
        value = p["quantity"] * info["close"] if info else None
        total += value or 0
        rows.append({**p, "price": info and info["close"], "value": value, "as_of": info and info["as_of"]})
    for r in rows:
        r["weight_pct"] = round(r["value"] / total * 100, 1) if r["value"] and total else None
    by_sector: dict[str, float] = {}
    for r in rows:
        by_sector[r["sector"] or "-"] = by_sector.get(r["sector"] or "-", 0) + (r["value"] or 0)
    alloc = sorted(({"sector": k, "pct": round(v / total * 100, 1)} for k, v in by_sector.items()), key=lambda x: -x["pct"]) if total else []
    top = max(rows, key=lambda r: r["value"] or 0, default=None)
    top_sector = alloc[0]["pct"] if alloc else 0
    risk = "HIGH" if top_sector >= 60 else "MODERATE" if top_sector >= 40 else "LOW"
    note = (f"Eksposur sektor {alloc[0]['sector']} {top_sector}% dari nilai saham: konsentrasi {risk.lower()}." if alloc else
            "Belum ada posisi bernilai.")
    return {"positions": rows, "total_value": total, "allocation": alloc, "top_holding": top and {"ticker": top["ticker"], "weight_pct": top["weight_pct"]},
            "top_sector_pct": top_sector, "concentration_risk": risk, "note": note,
            "unpriced": [r["ticker"] for r in rows if r["value"] is None]}


def impact_context(con) -> dict:
    imp: dict[str, list] = {}
    for r in con.execute("""SELECT c.ticker, e.title, i.direction, i.score, i.reason FROM event_impacts i
                            JOIN events e ON e.id=i.event_id JOIN companies c ON c.id=i.entity_id AND i.entity_type='COMPANY'
                            WHERE e.ts >= ?""", ((datetime.now() - timedelta(days=14)).isoformat(),)):
        imp.setdefault(r["ticker"], []).append(dict(r))
    return imp


def opportunities(client: dict, summ: dict, imp: dict, max_cash: float) -> tuple[float, list[dict]]:
    cash_ratio = client["cash_balance"] / client["aum"]
    idle = (datetime.now() - datetime.fromisoformat(client["last_transaction_at"])).days if client["last_transaction_at"] else 999
    held = {p["ticker"] for p in summ["positions"]}
    relevant = [t for t in held if t in imp]
    score = 100 * (0.30 * min(1, cash_ratio / 0.3) + 0.25 * min(1, client["cash_balance"] / max_cash if max_cash else 0)
                   + 0.20 * min(1, idle / 90) + 0.15 * min(1, summ["top_sector_pct"] / 80) + 0.10 * (1 if relevant else 0))
    ops = []
    if cash_ratio >= 0.2:
        ops.append(("CASH_DEPLOYMENT", client["cash_balance"], f"Kas {cash_ratio:.0%} dari AUM menganggur.", "Hubungi nasabah, diskusikan penempatan kas."))
    if client["risk_profile"] == "CONSERVATIVE" and cash_ratio >= 0.15:
        ops.append(("BOND", client["cash_balance"] * 0.5, "Profil konservatif dengan kas besar.", "Presentasikan opsi obligasi."))
    if idle >= 60:
        ops.append(("REACTIVATION", None, f"Tidak bertransaksi {idle} hari.", "Follow up, tanyakan kebutuhan dan pandangan pasar."))
    if summ["top_sector_pct"] >= 50:
        ops.append(("REBALANCING", None, summ["note"], "Tinjau konsentrasi sektor dan diversifikasi."))
    positive = sorted({t for t, v in imp.items() if t not in held and sum(i["score"] for i in v) > 0})
    if positive and client["risk_profile"] != "CONSERVATIVE":
        ops.append(("STOCK", None, f"Event terbaru berdampak positif (inferensi kata kunci) pada {', '.join(positive[:4])}, belum dimiliki.",
                    "Diskusikan sebagai bahan riset, bukan rekomendasi."))
    if relevant:
        ops.append(("REVIEW_HOLDINGS", None, f"Event terbaru terkait kepemilikan: {', '.join(sorted(relevant))}.", "Bahas dampak ke posisi nasabah."))
    return round(score, 1), [{"type": t, "estimated_value": v, "reason": r, "recommended_action": a} for t, v, r, a in ops]


def _clients(con, user: dict) -> list[dict]:
    sql = "SELECT * FROM clients" + ("" if user["role"] == "ADMIN" else " WHERE rm_id=?")
    return [dict(r) for r in con.execute(sql, () if user["role"] == "ADMIN" else (user["id"],))]


def _radar_row(con, c, imp, max_cash):
    summ = summarize(con, [dict(r) for r in con.execute(POS_SQL + "p.client_id=?", (c["id"],))])
    score, ops = opportunities(c, summ, imp, max_cash)
    return {**{k: c[k] for k in ("id", "client_code", "name", "risk_profile", "aum", "cash_balance", "last_transaction_at", "is_dummy")},
            "score": score, "priority": "HIGH" if score >= 70 else "MEDIUM" if score >= 50 else "LOW",
            "opportunities": ops, "top_sector_pct": summ["top_sector_pct"]}, summ


@router.get("/portfolio", dependencies=[Depends(require("INVESTOR"))])
def my_portfolio(user: dict = Depends(current_user)):
    with db.connect() as con:
        return summarize(con, [dict(r) for r in con.execute(POS_SQL + "p.user_id=?", (user["id"],))])


@router.get("/clients/radar", dependencies=[Depends(require("RM"))])
def radar(user: dict = Depends(current_user)):
    with db.connect() as con:
        clients, imp = _clients(con, user), impact_context(con)
        max_cash = max((c["cash_balance"] for c in clients), default=0)
        return sorted((_radar_row(con, c, imp, max_cash)[0] for c in clients), key=lambda r: -r["score"])


def _own_client(con, client_id: int, user: dict) -> dict:
    c = next((c for c in _clients(con, user) if c["id"] == client_id), None)
    if not c:  # klien milik RM lain diperlakukan sama dengan tidak ada
        raise HTTPException(404, {"code": "NO_DATA", "message": "Klien tidak ditemukan"})
    con.execute("INSERT INTO audit_log(user_id, action, target) VALUES (?,?,?)", (user["id"], "VIEW_CLIENT", c["client_code"]))
    return c


@router.get("/clients/{client_id}/meeting-brief", dependencies=[Depends(require("RM"))])
def meeting_brief(client_id: int, user: dict = Depends(current_user)):
    with db.connect() as con:
        c = _own_client(con, client_id, user)
        clients, imp = _clients(con, user), impact_context(con)
        row, summ = _radar_row(con, c, imp, max((x["cash_balance"] for x in clients), default=0))
        held_ids = [p["company_id"] for p in summ["positions"]]
        related = []
        for cid in held_ids:
            related += queries.news(con, ("COMPANY", cid), days=14, limit=3)
        related = list({n["url"]: n for n in related}.values())[:8]
        sectors = queries.sector_changes(con)
    qs = ["Apa tujuan investasi dan horizon waktu terbaru?", "Apakah ada kebutuhan likuiditas dalam 6 bulan ke depan?"]
    if row["top_sector_pct"] >= 50:
        qs.append("Apakah nasabah nyaman dengan konsentrasi sektor saat ini?")
    if any(o["type"] == "CASH_DEPLOYMENT" for o in row["opportunities"]):
        qs.append("Berapa porsi kas yang ingin tetap dijaga sebagai cadangan?")
    return {"client": row, "portfolio": summ, "recent_news": related, "market_context": sectors[:3] + sectors[-2:],
            "event_impacts": {t: v for t, v in imp.items() if t in {p["ticker"] for p in summ["positions"]}},
            "questions": qs, "generated_at": datetime.now().isoformat(timespec="seconds"),
            "disclaimer": "Data nasabah DUMMY. Bahan diskusi, bukan rekomendasi investasi."}

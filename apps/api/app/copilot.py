"""Copilot berbasis aturan: memetakan pertanyaan ke 'tool' (query nyata) dan menyusun jawaban dari hasilnya.

Bukan LLM: tidak ada kalimat bebas, tidak ada angka yang tak berasal dari tool. Setiap jawaban memuat daftar tool
yang dipanggil, sumber data, dan tingkat keyakinan (MEDIUM = data tersimpan bersumber tidak resmi; LOW = ada inferensi).
Arsitektur siap diganti LLM tool-calling (docs/04-ai-copilot.md): fungsi `tool_*` di bawah = skema tool-nya.
"""
import os
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from . import clients, db, insights, llm_copilot, queries
from .auth import RANK, current_user, require
from .nlp.rules import COMMODITY_KW, short_name

router = APIRouter(prefix="/api/v1/copilot")
HELP = ("Coba: “Apa yang bergerak hari ini?”, “Analisis ANTM”, “Saham terkait nikel”, “Perusahaan apa yang terdampak event terbaru?”, "
        "“Tampilkan aset nikel di peta”, “Berita batu bara”, “Risiko konsentrasi portofolio saya”, “Klien mana yang perlu dihubungi?”.")


def has(msg: str, pat: str) -> bool:
    return bool(re.search(pat, msg, re.I))


def tool_search_company(con, msg: str):
    for c in con.execute("SELECT c.id, c.ticker, c.name, c.sector_id, s.name AS sector FROM companies c LEFT JOIN sectors s ON s.id=c.sector_id").fetchall():
        if re.search(rf"\b{c['ticker']}\b", msg, re.I) or short_name(c["name"]).lower() in msg.lower():
            return c
    return None


def tool_commodity(msg: str):
    return next((c for c, p in COMMODITY_KW.items() if has(msg, p)), None)


def _fmt_change(v):
    return "n/a" if v is None else f"{v:+.2f}%"


def answer(con, user: dict, msg: str) -> dict:
    tools, links, sources, conf = [], [], set(), "MEDIUM"
    lines: list[str] = []
    comp, comm = tool_search_company(con, msg), tool_commodity(msg)

    if has(msg, r"klien|client|nasabah|follow.?up|hubungi|\bcall\b|siapa.*(telepon|hubungi)"):
        tools.append("list_client_opportunities")
        if RANK[user["role"]] < RANK["RM"]:
            return {"answer": "Fitur klien hanya untuk peran RM/Admin.", "tools": tools, "links": [], "sources": [], "confidence": "HIGH"}
        radar = clients.radar(user)[:5]
        lines.append("Prioritas follow-up (skor RM deterministik; data klien DUMMY):")
        for r in radar:
            ops = ", ".join(o["type"] for o in r["opportunities"]) or "-"
            lines.append(f"• {r['name']} — skor {r['score']} ({r['priority']}), kas Rp{r['cash_balance'] / 1e9:.1f} M; peluang: {ops}")
            links.append({"text": f"Meeting brief {r['name']}", "href": f"/clients/{r['id']}/brief"})
        sources.add("clients (dummy)")
    elif has(msg, r"portofolio|portfolio|konsentrasi"):
        tools.append("get_portfolio")
        p = clients.my_portfolio(user)
        lines += [p["note"], f"Total nilai saham Rp{p['total_value'] / 1e6:,.1f} jt; top holding {p['top_holding']['ticker']} {p['top_holding']['weight_pct']}%." if p["top_holding"] else ""]
        links.append({"text": "Buka portofolio", "href": "/portfolio"})
        sources.add("posisi contoh + harga Yahoo")
    elif has(msg, r"peta|\bmap\b|aset|lokasi|asset"):
        tools.append("search_location")
        from .mapapi import assets
        feats = assets(ticker=comp["ticker"] if comp else None, commodity=comm)["features"]
        if not feats:
            lines.append("Tidak ada aset tercatat untuk filter itu.")
        for f in feats:
            p = f["properties"]
            lines.append(f"• {p['ticker']} — {p['name']} ({p['province']}), komoditas {p['commodity']}"
                         + ("" if p["verified"] else " [lokasi perkiraan, belum diverifikasi]"))
        links.append({"text": "Buka peta", "href": "/map"})
        sources.add("assets (internal, perkiraan)")
        conf = "LOW"
    elif has(msg, r"event|dampak|terdampak|affected|kebijakan|policy"):
        tools += ["search_events", "analyze_impact"]
        evs = [dict(r) for r in con.execute("""SELECT e.id, e.title, e.event_type, e.ts FROM events e
                   WHERE EXISTS (SELECT 1 FROM event_impacts i WHERE i.event_id=e.id) ORDER BY e.ts DESC LIMIT 3""")]
        if not evs:
            lines.append("Belum ada event berdampak terdeteksi. Jalankan refresh data.")
        for e in evs:
            imp = [dict(r) for r in con.execute("""SELECT c.ticker, i.direction FROM event_impacts i JOIN companies c ON c.id=i.entity_id
                                                   WHERE i.event_id=? ORDER BY i.score""", (e["id"],))]
            lines.append(f"• [{e['event_type']}] {e['title']} → " + ", ".join(f"{i['ticker']} {i['direction']}" for i in imp[:8]))
        lines.append("Dampak = inferensi aturan kata kunci (keyakinan LOW), bukan prediksi.")
        links.append({"text": "Semua event & alasannya", "href": "/events"})
        sources.add("events (aturan kata kunci atas berita)")
        conf = "LOW"
    elif comm and not comp:
        tools += ["search_commodity", "search_companies"]
        rows = con.execute("""SELECT c.id, c.ticker, c.name FROM company_commodities cc JOIN companies c ON c.id=cc.company_id
                              WHERE cc.commodity=? ORDER BY c.ticker""", (comm,)).fetchall()
        lines.append(f"Emiten tercatat berekposur {comm} (daftar internal, belum diverifikasi):")
        for r in rows:
            p = queries.price_info(con, r["id"])
            lines.append(f"• {r['ticker']} — {r['name']}" + (f", harga {p['close']:,.0f} ({_fmt_change(p['change_pct'])})" if p else ""))
            links.append({"text": r["ticker"], "href": f"/companies/{r['ticker']}"})
        if has(msg, r"berita|news"):
            lines.append("")
            for n in queries.news(con, ("COMMODITY", con.execute("SELECT id FROM commodities WHERE code=?", (comm,)).fetchone()["id"]), limit=3):
                lines.append(f"• {n['title']} ({n['publisher']})")
        sources |= {"company_commodities (internal)", "Yahoo Finance (unofficial)"}
        conf = "LOW"
    elif comp:
        tools += ["search_company", "get_price", "get_fundamental", "search_news", "analyze_impact"]
        b = insights.company_brief(con, comp)
        pr = b["priority"]
        lines += [f"{comp['ticker']} — {comp['name']} ({comp['sector']})", "", "FAKTA:"] + [f"• {x}" for x in b["facts"]]
        if b["inferences"]:
            lines += ["", "INFERENSI:"] + [f"• {x}" for x in b["inferences"]]
            conf = "LOW"
        lines += ["", "KETIDAKPASTIAN:"] + [f"• {x}" for x in b["uncertainties"]]
        lines += ["", f"Research Priority Score {pr['score']} ({pr['label']}), keyakinan data {pr['data_confidence']:.0%}. Bukan rekomendasi beli/jual."]
        links.append({"text": f"Halaman {comp['ticker']}", "href": f"/companies/{comp['ticker']}"})
        sources |= {"Yahoo Finance (unofficial)", "Google News RSS"}
    elif has(msg, r"berita|news"):
        tools.append("search_news")
        for n in queries.news(con, days=3, limit=6):
            lines.append(f"• {n['title']} — {n['publisher']} [{n['sentiment']}]")
        links.append({"text": "Semua berita", "href": "/news"})
        sources.add("Google News RSS")
    elif has(msg, r"bergerak|hari ini|today|moving|pasar|market|sektor|sector"):
        tools += ["get_market_overview", "search_sector"]
        lines += insights.market_brief(con)
        for q in con.execute("SELECT name, value, change_pct FROM market_quotes"):
            lines.append(f"• {q['name']}: {q['value']:,.2f} ({_fmt_change(q['change_pct'])})")
        links.append({"text": "Dashboard", "href": "/"})
        sources.add("Yahoo Finance (unofficial)")
    else:
        return {"answer": "Saya belum mengerti pertanyaan itu. " + HELP, "tools": [], "links": [], "sources": [], "confidence": "HIGH"}
    return {"answer": "\n".join(lines), "tools": tools, "links": links, "sources": sorted(sources), "confidence": conf}


class Chat(BaseModel):
    message: str


@router.post("/chat", dependencies=[Depends(require("INVESTOR"))])
def chat(body: Chat, user: dict = Depends(current_user)):
    with db.connect() as con:
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                return llm_copilot.answer(con, user, body.message)
            except Exception as e:  # jatuh ke mode aturan, jujur soal alasannya
                res = answer(con, user, body.message)
                return {**res, "answer": f"[LLM tidak tersedia: {type(e).__name__}; memakai mode aturan]\n" + res["answer"]}
        return {**answer(con, user, body.message), "mode": "rules"}

"""Copilot LLM dengan tool-calling (Anthropic Messages API lewat urllib, tanpa SDK). Aktif bila ANTHROPIC_API_KEY ada.

LLM tidak pernah memegang data: ia hanya memanggil tool di bawah (query nyata ke DB). Akses klien dicek di server
berdasar peran sesi, bukan argumen dari LLM. Dilindungi tes dengan klien palsu; BELUM diuji ke API sungguhan (tanpa key).
"""
import json
import os
import urllib.request
from datetime import date

from . import clients, insights, mapapi, queries
from .auth import RANK

MODEL = os.environ.get("IMVEST_COPILOT_MODEL", "claude-sonnet-5-5")
MAX_TURNS = 6
SYSTEM = """You are IM-VEST Intelligence Copilot. Help users understand Indonesian capital-market companies, sectors, news and events.
RULES: 1) Never invent prices, fundamentals, company relations or asset locations; use tools. 2) If a tool returns no data, say so.
3) Separate FACT (from a tool, cite source+as_of) from INFERENCE from UNCERTAINTY. 4) Explain reasoning. 5) No guaranteed returns;
never tell the user to buy or sell. Research Priority Score is a research ordering, not a rating. 6) Event impacts are keyword
inferences with LOW confidence; say so. 7) Only discuss clients returned by tools. Client data is DUMMY.
Answer in Indonesian unless asked otherwise, concisely. End with 'Keyakinan: HIGH|MEDIUM|LOW' and a short reason. Today is {today}."""

_S = lambda **p: {"type": "object", "properties": {k: {"type": "string"} for k in p}}  # noqa: E731
TOOLS = [
    {"name": "search_company", "description": "Cari emiten berdasar nama/ticker.", "input_schema": {**_S(query=1), "required": ["query"]}},
    {"name": "get_price", "description": "Harga terakhir, perubahan harian/1B/3B, sumber, as_of.", "input_schema": {**_S(ticker=1), "required": ["ticker"]}},
    {"name": "get_fundamental", "description": "Market cap, PER, PBV, ROE, dll (TTM).", "input_schema": {**_S(ticker=1), "required": ["ticker"]}},
    {"name": "get_company_brief", "description": "Fakta/inferensi/ketidakpastian + Research Priority Score satu emiten.", "input_schema": {**_S(ticker=1), "required": ["ticker"]}},
    {"name": "search_news", "description": "Berita terbaru, filter ticker/sector(code)/commodity.", "input_schema": _S(ticker=1, sector=1, commodity=1)},
    {"name": "search_events", "description": "Event terdeteksi terbaru beserta emiten terdampak dan alasan.", "input_schema": _S()},
    {"name": "search_sector", "description": "Performa sektor (kode mis. ENERGY) dan emitennya.", "input_schema": {**_S(code=1), "required": ["code"]}},
    {"name": "search_location", "description": "Aset/lokasi perusahaan (perkiraan) per ticker atau komoditas.", "input_schema": _S(ticker=1, commodity=1)},
    {"name": "list_client_opportunities", "description": "Peluang klien milik RM saat ini (hanya RM/Admin).", "input_schema": _S()},
]


def run_tool(con, user: dict, name: str, args: dict):
    t = (args.get("ticker") or "").upper()
    if name == "search_company":
        q = f"%{args.get('query', '')}%"
        return [dict(r) for r in con.execute("SELECT ticker, name FROM companies WHERE ticker LIKE ? OR name LIKE ? LIMIT 10", (q, q))]
    if name in ("get_price", "get_fundamental", "get_company_brief"):
        c = queries.company(con, t)
        if not c:
            return {"error": f"emiten {t} tidak ditemukan"}
        if name == "get_price":
            return queries.price_info(con, c["id"]) or {"error": "harga tidak tersedia"}
        if name == "get_fundamental":
            return queries.stats(con, c["id"]) or {"error": "fundamental tidak tersedia"}
        return insights.company_brief(con, c)
    if name == "search_news":
        entity = None
        if t and (c := queries.company(con, t)):
            entity = ("COMPANY", c["id"])
        elif args.get("sector") and (r := con.execute("SELECT id FROM sectors WHERE code=?", (args["sector"].upper(),)).fetchone()):
            entity = ("SECTOR", r["id"])
        elif args.get("commodity") and (r := con.execute("SELECT id FROM commodities WHERE code=?", (args["commodity"].upper(),)).fetchone()):
            entity = ("COMMODITY", r["id"])
        return queries.news(con, entity, days=14, limit=8)
    if name == "search_events":
        out = []
        for e in con.execute("SELECT id, event_type, title, ts FROM events ORDER BY ts DESC LIMIT 6").fetchall():
            imp = [dict(r) for r in con.execute("""SELECT c.ticker, i.direction, i.confidence, i.reason FROM event_impacts i
                       JOIN companies c ON c.id=i.entity_id WHERE i.event_id=? LIMIT 8""", (e["id"],))]
            out.append({**dict(e), "impacts": imp})
        return out
    if name == "search_sector":
        s = con.execute("SELECT id, name FROM sectors WHERE code=?", (args.get("code", "").upper(),)).fetchone()
        if not s:
            return {"error": "sektor tidak ditemukan"}
        perf = next((x["change_pct"] for x in queries.sector_changes(con) if x["id"] == s["id"]), None)
        comps = [dict(r) for r in con.execute("SELECT ticker, name FROM companies WHERE sector_id=?", (s["id"],))]
        return {"name": s["name"], "change_pct": perf, "companies": comps}
    if name == "search_location":
        return mapapi.assets(ticker=t or None, commodity=args.get("commodity"))["features"]
    if name == "list_client_opportunities":
        if RANK[user["role"]] < RANK["RM"]:
            return {"error": "hanya RM/Admin"}
        return [{k: r[k] for k in ("name", "score", "priority", "cash_balance", "opportunities")} for r in clients.radar(user)[:8]]
    return {"error": f"tool {name} tidak dikenal"}


def _anthropic(body: dict) -> dict:
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                 headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
                                          "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def answer(con, user: dict, message: str, post=_anthropic) -> dict:
    msgs = [{"role": "user", "content": message}]
    used: list[str] = []
    sources: set[str] = set()
    for _ in range(MAX_TURNS):
        resp = post({"model": MODEL, "max_tokens": 1500, "system": SYSTEM.format(today=date.today()), "tools": TOOLS, "messages": msgs})
        calls = [b for b in resp["content"] if b["type"] == "tool_use"]
        if resp.get("stop_reason") != "tool_use" or not calls:
            text = "".join(b["text"] for b in resp["content"] if b["type"] == "text")
            conf = "LOW" if "search_events" in used else "MEDIUM"
            return {"answer": text, "tools": used, "links": [], "sources": sorted(sources), "confidence": conf, "mode": "llm"}
        msgs.append({"role": "assistant", "content": resp["content"]})
        results = []
        for c in calls:
            used.append(c["name"])
            out = run_tool(con, user, c["name"], c["input"])
            sources |= {r["source"] for r in (out if isinstance(out, list) else [out]) if isinstance(r, dict) and r.get("source")}
            results.append({"type": "tool_result", "tool_use_id": c["id"], "content": json.dumps(out, default=str)[:12000]})
        msgs.append({"role": "user", "content": results})
    return {"answer": "Terlalu banyak langkah; persempit pertanyaan.", "tools": used, "links": [], "sources": sorted(sources),
            "confidence": "LOW", "mode": "llm"}

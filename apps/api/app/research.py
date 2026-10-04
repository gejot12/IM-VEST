"""Adaptor TradingAgents (satu-satunya tempat `tradingagents` di-import). BELUM DIUJI end-to-end: butuh
paket `tradingagents` terpasang + API key LLM (ANTHROPIC_API_KEY/OPENAI_API_KEY/GOOGLE_API_KEY).
Tanpa itu endpoint menjawab 503 NOT_CONFIGURED, bukan hasil palsu.

Rating beli/jual dari TradingAgents SENGAJA dibuang; hanya laporan analis yang disimpan (aturan produk #10).
Satu run = banyak panggilan LLM (mahal): dijalankan di thread, di-cache per (emiten, tanggal).
"""
import json
import os
import threading
from datetime import date

from fastapi import HTTPException

from . import db

REPORT_KEYS = ("market_report", "sentiment_report", "news_report", "fundamentals_report")
KEYS = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "google": "GOOGLE_API_KEY"}


def _provider() -> str | None:
    return next((p for p, k in KEYS.items() if os.environ.get(k)), None)


def _work(company_id: int, ticker: str, as_of: str, provider: str) -> None:
    status, report, error = "DONE", None, None
    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        cfg = {**DEFAULT_CONFIG, "llm_provider": provider, "output_language": "Indonesian"}
        if provider == "anthropic":
            cfg |= {"deep_think_llm": "claude-sonnet-5-5", "quick_think_llm": "claude-haiku-4-5-20251001"}
        state, _rating = TradingAgentsGraph(debug=False, config=cfg).propagate(f"{ticker}.JK", as_of)
        report = json.dumps({k: state.get(k) for k in REPORT_KEYS if state.get(k)})
    except Exception as e:
        status, error = "FAILED", f"{type(e).__name__}: {e}"
    with db.connect() as con:
        con.execute("UPDATE research_runs SET status=?, report=?, error=? WHERE company_id=? AND as_of=?",
                    (status, report, error, company_id, as_of))


def run(ticker: str) -> dict:
    try:
        import tradingagents  # noqa: F401
    except ImportError:
        raise HTTPException(503, {"code": "NOT_CONFIGURED", "message": "Paket tradingagents belum terpasang (uv pip install ../../../TradingAgents)"})
    provider = _provider()
    if not provider:
        raise HTTPException(503, {"code": "NOT_CONFIGURED", "message": "Set salah satu: " + ", ".join(KEYS.values())})
    as_of = date.today().isoformat()
    with db.connect() as con:
        cid = con.execute("SELECT id FROM companies WHERE ticker=?", (ticker.upper(),)).fetchone()["id"]
        con.execute("DELETE FROM research_runs WHERE company_id=? AND as_of=? AND status='FAILED'", (cid, as_of))
        cur = con.execute("INSERT OR IGNORE INTO research_runs(company_id, as_of, status) VALUES (?,?,'RUNNING')", (cid, as_of))
        if cur.rowcount:
            threading.Thread(target=_work, args=(cid, ticker.upper(), as_of, provider), daemon=True).start()
        row = con.execute("SELECT status, report, error FROM research_runs WHERE company_id=? AND as_of=?", (cid, as_of)).fetchone()
    return {"status": row["status"], "as_of": as_of, "report": json.loads(row["report"]) if row["report"] else None, "error": row["error"],
            "note": "Rating beli/jual dari engine tidak ditampilkan."}

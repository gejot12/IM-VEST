import json

from app import copilot, llm_copilot
from conftest import login


def scripted(*steps):
    """Klien Anthropic palsu: jawaban berurutan; mencatat body yang dikirim."""
    sent = []
    it = iter(steps)

    def post(body):
        sent.append(json.loads(json.dumps(body, default=str)))
        return next(it)
    return post, sent


def tool_use(name, **inp):
    return {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "t1", "name": name, "input": inp}]}


def text(t):
    return {"stop_reason": "end_turn", "content": [{"type": "text", "text": t}]}


def test_loop_calls_tool_then_answers(env):
    post, sent = scripted(tool_use("get_price", ticker="ANTM"), text("ANTM naik. Keyakinan: MEDIUM"))
    with env.connect() as con:
        r = llm_copilot.answer(con, {"id": 1, "role": "INVESTOR"}, "Harga ANTM?", post=post)
    assert r["tools"] == ["get_price"] and r["mode"] == "llm" and "ANTM" in r["answer"]
    result_msg = sent[1]["messages"][-1]["content"][0]
    assert result_msg["type"] == "tool_result" and "close" in result_msg["content"]   # data nyata dari DB dikirim balik
    assert "Never invent" in sent[0]["system"] and {t["name"] for t in sent[0]["tools"]} >= {"get_price", "search_events"}


def test_client_tool_is_gated_by_session_role_not_llm(env):
    with env.connect() as con:
        out = llm_copilot.run_tool(con, {"id": 1, "role": "INVESTOR"}, "list_client_opportunities", {})
    assert out == {"error": "hanya RM/Admin"}


def test_unknown_tool_and_missing_company_are_errors_not_guesses(env):
    with env.connect() as con:
        assert "error" in llm_copilot.run_tool(con, {"id": 1, "role": "ADMIN"}, "drop_tables", {})
        assert "error" in llm_copilot.run_tool(con, {"id": 1, "role": "ADMIN"}, "get_price", {"ticker": "ZZZZ"})


def test_runaway_loop_is_bounded(env):
    post, sent = scripted(*[tool_use("search_events")] * 10)
    with env.connect() as con:
        r = llm_copilot.answer(con, {"id": 1, "role": "ADMIN"}, "x", post=post)
    assert len(sent) == llm_copilot.MAX_TURNS and r["confidence"] == "LOW"


def test_endpoint_falls_back_to_rules_when_llm_fails(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setattr(llm_copilot, "_anthropic", lambda body: (_ for _ in ()).throw(OSError("offline")))
    monkeypatch.setattr(llm_copilot, "answer", lambda con, u, m: (_ for _ in ()).throw(OSError("offline")))
    login(client)
    r = client.post("/api/v1/copilot/chat", json={"message": "Analisis ANTM"}).json()
    assert r["answer"].startswith("[LLM tidak tersedia") and "FAKTA" in r["answer"]
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert client.post("/api/v1/copilot/chat", json={"message": "Analisis ANTM"}).json()["mode"] == "rules"

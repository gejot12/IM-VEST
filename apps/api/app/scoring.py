"""Research Priority Score (BUKAN rating beli/jual). Bobot dari docs/04-ai-copilot.md.

Komponen tanpa data dikeluarkan dan bobot sisanya dinormalisasi; komponen 'data' (5%) = porsi komponen yang tersedia.
"""
WEIGHTS = {"momentum": 25, "fundamental": 20, "valuation": 15, "catalyst": 15, "sentiment": 10, "sector": 10}
LABELS = ((80, "HIGH"), (60, "MEDIUM"), (40, "WATCH"), (0, "LOW"))


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def priority(m: dict) -> dict:
    """m: r1m, r3m (pecahan), roe (pecahan), pe, sentiment (0..1), catalyst (-0.5..0.5), sector_change (% hari ini)."""
    v: dict[str, float | None] = {k: None for k in WEIGHTS}
    r1, r3 = m.get("r1m"), m.get("r3m")
    if r1 is not None or r3 is not None:
        v["momentum"] = _clamp(0.5 + (0.6 * (r3 or 0) + 0.4 * (r1 or 0)) / 0.6)
    if m.get("roe") is not None:
        v["fundamental"] = _clamp(m["roe"] / 0.2)
    pe = m.get("pe")
    if pe is not None:
        v["valuation"] = 0.2 if pe <= 0 else _clamp(1 - (pe - 8) / 22)
    if m.get("catalyst") is not None:
        v["catalyst"] = _clamp(0.5 + m["catalyst"])
    if m.get("sentiment") is not None:
        v["sentiment"] = m["sentiment"]
    if m.get("sector_change") is not None:
        v["sector"] = _clamp(0.5 + m["sector_change"] / 4)
    have = {k: x for k, x in v.items() if x is not None}
    conf = len(have) / len(WEIGHTS)
    total_w = sum(WEIGHTS[k] for k in have) + 5
    score = (sum(WEIGHTS[k] * x for k, x in have.items()) + 5 * conf) / total_w * 100
    return {"score": round(score, 1), "label": next(l for t, l in LABELS if score >= t),
            "components": {k: round(x, 2) for k, x in have.items()},
            "missing": [k for k in WEIGHTS if k not in have], "data_confidence": round(conf, 2)}

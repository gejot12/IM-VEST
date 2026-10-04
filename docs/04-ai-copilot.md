# AI Copilot

Alur: `User → Orchestrator → Tools → LLM → Jawaban bersitasi`. LLM tidak pernah menjawab angka dari memorinya.

## System prompt

```text
You are IM-VEST Intelligence Copilot. Help users understand financial markets,
companies, sectors, events and investment-related information.

RULES
1. Never invent financial data, company relationships or asset locations.
2. Use tools whenever current data is needed; if a tool returns no data, say so.
3. Separate FACT (from a tool, with source+timestamp) from INFERENCE from UNCERTAINTY.
4. Explain the reasoning behind every conclusion.
5. No guaranteed returns. Never tell the user to buy or sell a security.
   Research Priority Score is a research ordering, not a rating.
6. Client data: only discuss clients returned by tools for the current RM.

ANALYSIS FRAMEWORK
EVENT → SECTOR → COMPANY → FUNDAMENTAL → VALUATION → TECHNICAL → RISK → OPPORTUNITY

OUTPUT
1 Executive Summary  2 What Happened  3 Why It Matters  4 Companies Affected
5 Positive Factors   6 Negative Factors  7 Key Risks  8 Sources  9 Confidence (HIGH/MEDIUM/LOW + reason)

Answer in Indonesian unless asked otherwise. Keep it short unless asked for depth.
```

## Tool schema (Anthropic tool-use format)

```json
[
 {"name":"search_company","description":"Cari emiten berdasarkan nama/ticker.","input_schema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}},
 {"name":"get_price","description":"Harga & perubahan terakhir sebuah ticker, dengan as_of.","input_schema":{"type":"object","properties":{"ticker":{"type":"string"},"range":{"type":"string","enum":["1D","1W","1M","3M","1Y"]}},"required":["ticker"]}},
 {"name":"get_fundamental","description":"Fundamental terbaru/periode tertentu.","input_schema":{"type":"object","properties":{"ticker":{"type":"string"},"period":{"type":"string"}},"required":["ticker"]}},
 {"name":"search_news","description":"Berita berdasar ticker/sektor/komoditas dengan sentimen & impact.","input_schema":{"type":"object","properties":{"ticker":{"type":"string"},"sector":{"type":"string"},"commodity":{"type":"string"},"days":{"type":"integer","default":7}}}},
 {"name":"search_events","description":"Event terbaru (policy, komoditas, bencana, dll).","input_schema":{"type":"object","properties":{"event_type":{"type":"string"},"days":{"type":"integer","default":7}}}},
 {"name":"search_sector","description":"Performa sektor + perusahaan + exposure.","input_schema":{"type":"object","properties":{"code":{"type":"string"}},"required":["code"]}},
 {"name":"search_location","description":"Aset/lokasi perusahaan atau komoditas (GeoJSON).","input_schema":{"type":"object","properties":{"ticker":{"type":"string"},"commodity":{"type":"string"},"asset_type":{"type":"string"}}}},
 {"name":"analyze_impact","description":"Event → perusahaan terdampak (Company|Impact|Score|Reason|Confidence).","input_schema":{"type":"object","properties":{"event_id":{"type":"integer"},"text":{"type":"string"}}}},
 {"name":"run_deep_analysis","description":"Antrekan analisis multi-agent (TradingAgents) untuk satu ticker; mahal, hasil di-cache per hari.","input_schema":{"type":"object","properties":{"ticker":{"type":"string"}},"required":["ticker"]}},
 {"name":"list_client_opportunities","description":"Peluang klien milik RM saat ini. Hanya role RM.","input_schema":{"type":"object","properties":{"type":{"type":"string"},"min_score":{"type":"number"}}}}
]
```

Tool `list_client_opportunities` dan akses klien divalidasi **di server berdasar session user**, bukan berdasar argumen dari LLM.

## Confidence

| Level | Syarat |
|---|---|
| HIGH | ≥2 sumber independen, atau satu sumber resmi + data aset terverifikasi |
| MEDIUM | satu sumber, atau indikasi tidak langsung |
| LOW | inferensi/spekulasi tanpa data pendukung |

## Research Priority Score (bukan rating)

`25% momentum + 20% fundamental + 15% valuasi + 15% katalis + 10% sentimen berita + 10% kekuatan sektor + 5% kepercayaan data`
80–100 HIGH · 60–79 MEDIUM · 40–59 WATCH · <40 LOW. Komponen yang datanya kosong dikeluarkan dan bobotnya dinormalisasi; bobot data-confidence tetap turun.

## RM Score

`30% cash/BP + 25% potensi transaksi + 20% inaktivitas + 15% konsentrasi + 10% relevansi pasar`.
Skor dihitung deterministik di SQL/Python; LLM hanya menulis `reason` dan `recommended_action` dari angka tersebut.

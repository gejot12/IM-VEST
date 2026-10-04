# Integration Map

## TradingAgents → riset capital market

Pipeline TradingAgents: 4 analyst (market, news, sentiment, fundamentals) → debat bull/bear → research manager → trader → debat risiko 3 sisi → portfolio manager. Entry: `TradingAgentsGraph.propagate(company_name, trade_date, asset_type, portfolio)` di `tradingagents/graph/trading_graph.py`.

| Fitur IM-VEST | Pakai dari TradingAgents | Catatan |
|---|---|---|
| Company Intelligence "Why it matters" | `agents/analysts/fundamentals_analyst.py`, `market_analyst.py` | Output di-map ke FACT / INFERENCE / UNCERTAINTY |
| News Intelligence / Event→Impact | `agents/analysts/news_analyst.py`, `sentiment_analyst.py` | Tambah langkah ekstraksi entitas (company/sector/commodity) |
| Risk & Confidence | debat `risk_mgmt/*` + `researchers/bull,bear` | Confidence HIGH/MED/LOW dari tingkat kesepakatan debat + jumlah sumber |
| Tool data | `agents/tools.py` (`get_stock_data`, `get_fundamentals`, `get_news`, `get_global_news`, `get_macro_indicators`, …) | Tambah vendor baru di `dataflows/vendors/` untuk IDX/BI/OJK, lewat `dataflows/router.py` |
| Multi-LLM | `llm_clients/` (Anthropic, OpenAI, Google, …) | Atur lewat env `TRADINGAGENTS_*` |
| Memori/refleksi | `memory/` | Opsional, fase 2 |

**Yang TIDAK boleh dibawa mentah:**
- Output akhirnya berbentuk rating beli/jual. Di IM-VEST ini dilarang (prompt AI #10). Ambil hanya analisis, buang rating; tampilkan sebagai Research Priority Score.
- Default data vendor US-sentris (yfinance/Alpha Vantage/SEC EDGAR/FRED). Ticker IDX di Yahoo memakai sufiks `.JK` (mis. `ANTM.JK`); verifikasi perilaku `dataflows/symbols.py` sebelum mengandalkannya.
- Biaya LLM: satu `propagate` = banyak panggilan. Jalankan di worker, cache hasil per (ticker, tanggal), jangan di request path.

## gods-eye-view → Intelligence Map

| Kebutuhan | Rujukan di GEV |
|---|---|
| Layer gempa (USGS) | `server/providers/` + `src/layers/` |
| Layer api/hotspot (NASA FIRMS) | `server/providers/firms.js` |
| Cuaca/angin | `server/providers/weather.js`, `wind.js` |
| Kapal (AIS) | `server/providers/vessels/` (fase 2) |
| Pelabuhan/industri (OSM) | `server/providers/overpass.js` |
| Globe 3D + kontrol | `src/` (Cesium) |
| Kontrol suara / tool-calling | `server/mcp/*`, `src/voice/` — pola MCP dipakai untuk menjembatani Copilot ↔ peta (fase 2) |

Aturan: **salin pola, jangan salin dependensi besar**. GEV memakai Google Photorealistic 3D Tiles (proprietary, key + billing sendiri) — untuk MVP pakai Esri/OSM atau Cesium ion default. `DATA_SOURCES.md` GEV mencatat lisensi per sumber; OpenSky = non-komersial, TeleGeography = NonCommercial. Jangan bawa ke produk komersial tanpa cek.

Aset perusahaan (tambang, smelter, pelabuhan) **tidak ada di GEV**. Itu data milik IM-VEST (`locations`, `assets`) dan harus bersumber jelas (laporan tahunan, OSM, situs perusahaan) dengan `source_id` + `verified_at`. Jangan pernah mengarang koordinat.

## ponytail → audit

- Aktif sebagai mode saat menulis kode (`/ponytail`).
- `ponytail-review` pada setiap diff sebelum merge.
- `ponytail-audit` sekali di akhir tiap minggu (hari 7, 14, 21, 28), hasilnya dicatat di `docs/audits/week-N.md`.
- `ponytail-debt` di hari 29 untuk daftar utang teknis.
- Tidak menggantikan `/code-review` (korektness) dan `/security-review` (wajib sebelum modul Client Radar).

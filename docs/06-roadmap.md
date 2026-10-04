# Roadmap 30 Hari (dengan gerbang audit)

Prioritas jika waktu mepet: Company search/intelligence, News, AI Copilot, Event impact, Market dashboard → 2D map, Client radar, Meeting brief → 3D globe → sisanya fase 2.

| Minggu | Hari | Isi | Gerbang |
|---|---|---|---|
| 1 Foundation | 1 | Monorepo, compose (PostGIS+Redis), Next.js + FastAPI skeleton | `docker compose up` sehat |
| | 2 | Terapkan `01-schema.sql`, load `seed/companies.csv` | tabel terisi |
| | 3 | Auth + role + protected route | tes akses per role |
| | 4 | Company CRUD + search | cari ANTM |
| | 5 | Market dashboard (mock `SEED`, FX BI nyata bila sempat) | |
| | 6 | Halaman company (header, harga, fundamental, chart, news) | |
| | 7 | Polish | **ponytail-audit minggu 1** |
| 2 Intelligence | 8 | Ingest berita (GDELT) | |
| | 9–10 | Ekstraksi entitas + sentimen (LLM, hasil disimpan di `news_entities`) | tes dengan fixture |
| | 11 | Event engine + `event_impacts` | reason wajib |
| | 12 | Halaman sektor | |
| | 13 | `app/research/` adapter TradingAgents + `research_runs` cache | 1 run ANTM, biaya dicatat |
| | 14 | Event→Impact UI | **ponytail-audit minggu 2** |
| 3 Map | 15–17 | MapLibre, lokasi + aset (hanya baris bersumber), klik aset→perusahaan→komoditas | `verified_at` tampil |
| | 18–20 | Layer cuaca, USGS, FIRMS (pola dari GEV) | atribusi tampil |
| | 21 | Prototipe Cesium (globe + marker saja) | **ponytail-audit minggu 3** |
| 4 AI + RM | 22–23 | Copilot UI + tool-calling (04) | tes: tak ada angka tanpa tool |
| | 24 | Portfolio | |
| | 25 | Client DB dummy | **/security-review** sebelum lanjut |
| | 26–27 | Opportunity engine + Next Best Action | skor deterministik teruji |
| | 28 | Meeting brief + PDF | **ponytail-audit minggu 4** |
| | 29 | Integrasi alur penuh + `ponytail-debt` | |
| | 30 | Demo: dashboard → nickel naik → perusahaan terdampak → peta aset → klien → meeting brief PDF | |

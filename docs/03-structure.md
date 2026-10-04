# Struktur Repo

Satu repo, tanpa `packages/ui` dan `packages/types` dulu (YAGNI; tambahkan bila ada konsumen kedua).

```
imvest-intelligence/
├─ apps/
│  ├─ web/                  Next.js (App Router) + Auth.js
│  │  └─ src/app/{dashboard,radar,map,companies/[ticker],sectors,news,portfolio,clients,copilot}
│  └─ api/                  FastAPI
│     ├─ app/{routers,services,models,schemas}
│     ├─ app/research/      adapter ke TradingAgents (satu-satunya tempat import `tradingagents`)
│     ├─ app/copilot/       orchestrator + tools.py (skema di 04)
│     ├─ app/ingest/        satu modul per sumber: bi_fx, usgs, firms, open_meteo, gnews
│     └─ tests/
├─ infrastructure/docker-compose.yml
├─ seed/                    companies.csv, assets.csv (hanya baris ber-sumber), dummy_clients.csv
├─ docs/                    00–06 + audits/
└─ vendor/                  (opsional) TradingAgents sebagai submodule/pin versi
```

Aturan batas:
- `tradingagents` hanya di-import di `app/research/`. Pergantian engine = ganti satu folder.
- Frontend tidak memanggil API pihak ketiga langsung; semua lewat FastAPI (kunci API + cache + lisensi terpusat).
- Worker = proses Python yang sama dengan API (RQ/arq di Redis). Jangan bikin service terpisah sebelum perlu.

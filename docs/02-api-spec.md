# API Spec v1 (FastAPI, prefix `/api/v1`)

Auth: cookie session dari Auth.js; FastAPI memverifikasi JWT. Role: `ADMIN > ANALYST > RM > INVESTOR`.
Setiap respons yang berisi angka/klaim menyertakan `source` (`data_sources.name`) dan `as_of` (ISO timestamp). Tidak ada sumber → field `null`, bukan tebakan.

| Method | Path | Role min | Keterangan |
|---|---|---|---|
| POST | `/auth/login` | – | email+password → session |
| GET | `/market/overview` | INVESTOR | IHSG, LQ45, USD/IDR, gold, oil, nickel |
| GET | `/market/sectors` | INVESTOR | heatmap sektor (% change) |
| GET | `/companies?q=` | INVESTOR | autocomplete ticker/nama |
| GET | `/companies/{ticker}` | INVESTOR | header, harga, valuasi |
| GET | `/companies/{ticker}/prices?range=` | INVESTOR | OHLCV |
| GET | `/companies/{ticker}/fundamentals` | INVESTOR | per periode |
| GET | `/companies/{ticker}/news` | INVESTOR | berita terkait |
| GET | `/companies/{ticker}/assets` | INVESTOR | aset + lokasi (GeoJSON) |
| POST | `/companies/{ticker}/analysis` | INVESTOR | enqueue run TradingAgents → `202 {run_id}` |
| GET | `/analysis/{run_id}` | INVESTOR | status/hasil (FACT/INFERENCE/UNCERTAINTY) |
| GET | `/sectors/{code}` | INVESTOR | performa + perusahaan + exposure |
| GET | `/news?sector=&ticker=&impact=` | INVESTOR | news intelligence |
| GET | `/events` | INVESTOR | event terbaru |
| GET | `/events/{id}/impacts` | INVESTOR | tabel Company/Impact/Score/Reason/Confidence |
| POST | `/events/analyze` | ANALYST | teks event → impacts (bukan persisten sampai di-approve) |
| GET | `/map/layers` | INVESTOR | daftar layer |
| GET | `/map/layers/{layer}?bbox=` | INVESTOR | GeoJSON; layer: companies, assets, earthquakes, fires, weather |
| GET | `/portfolios/{id}` | INVESTOR | posisi, alokasi, konsentrasi |
| GET | `/clients` | RM | hanya klien milik RM tsb (filter `rm_id`) |
| GET | `/clients/radar` | RM | skor RM + filter |
| GET | `/clients/{id}/next-best-action` | RM | |
| POST | `/meeting-briefs` | RM | `{client_id|company_id}` → brief; `?format=pdf` |
| POST | `/copilot/chat` | INVESTOR | SSE stream; tool-calling (lihat 04) |

Error: `{ "error": {"code": "NO_DATA|FORBIDDEN|RATE_LIMIT", "message": "..."} }`.
`NO_DATA` adalah respons sah; UI menampilkan "data tidak tersedia", bukan nilai kosong palsu.

Aturan akses: `/clients*` dan `/meeting-briefs` dengan `client_id` hanya untuk RM pemilik atau ADMIN; semua baca/tulis klien dicatat ke audit log.

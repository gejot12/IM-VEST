# Status vs Roadmap 30 Hari

Dikerjakan dengan aturan kata kunci (tanpa LLM) dan SQLite dev (tanpa Docker/Postgres di mesin pengembangan).

| Hari | Item | Status |
|---|---|---|
| 1–2 | Skeleton, skema | ✅ FastAPI + Next.js. Skema produksi `01-schema.sql` **divalidasi di PostgreSQL 16 tertanam** (29 tabel, constraint lolos); bagian PostGIS belum teruji (tak ada Docker); dev memakai subset SQLite `schema_sqlite.sql` |
| 3 | Auth + role | ✅ cookie JWT, 4 peran, kunci login setelah 5 gagal |
| 4 | Company search | ✅ 30 emiten |
| 5 | Market dashboard | ✅ data nyata; nikel tidak tersedia |
| 6 | Company page | ✅ harga, fundamental, "Why it matters" (FAKTA/INFERENSI/KETIDAKPASTIAN), radar skor, aset, berita |
| 7 | Audit 1 | ✅ ponytail-review; audit akhir menghapus modul GDELT dan wrapper |
| 8 | Ingest berita | ✅ Google News RSS (GDELT dihapus: kena rate limit) |
| 9–10 | Entitas, sentimen | ✅ aturan kata kunci + negasi |
| 11 | Event engine | ✅ POLICY/COMMODITY/DISASTER, dampak per emiten + alasan wajib |
| 12 | Sektor | ✅ `/sectors/{code}` |
| 13 | AI company analysis | ⚠️ ringkasan berbasis aturan ✅; TradingAgents adaptor ditulis **belum diuji** |
| 14 | Event→Impact UI | ✅ |
| 15–17 | Peta + aset | ✅ MapLibre; 11 aset perkiraan, ditandai belum diverifikasi |
| 18–20 | Cuaca, gempa, api | ✅ cuaca, gempa · ⚠️ api butuh `FIRMS_MAP_KEY` (belum diuji dengan key) |
| 21 | Globe 3D Cesium | ✅ prototipe `/globe` (aset + gempa, citra Esri) |
| 22–23 | Copilot + tool-calling | ✅ mode aturan (default) + mode LLM tool-calling bila `ANTHROPIC_API_KEY` ada (**belum diuji ke API sungguhan**) |
| 24 | Portfolio | ✅ alokasi, konsentrasi |
| 25 | Client DB | ✅ 8 klien dummy; akses per RM + audit log |
| 26–27 | Opportunity + next best action | ✅ skor RM deterministik |
| 28 | Meeting brief | ✅ halaman cetak (Cetak/Simpan PDF dari browser) |
| 29 | Integrasi alur | ✅ dashboard → event → emiten → peta → klien → brief |
| – | Tambahan | ✅ watchlist + alert, supply chain dasar, perbaikan XSS/URL di sisi tampilan |
| 30 | Demo | ✅ lihat alur di bawah |

## Demo (login rm@imvest.local)
1. Dashboard: ringkasan, sektor, event penting. 2. Copilot: "Saham terkait nikel" → daftar emiten.
3. Event→Impact: buka event, lihat emiten + alasan. 4. Peta: aset nikel (hijau). 5. Client Radar → klien teratas → Meeting Brief → Cetak.

## Belum ada / langkah berikutnya
- Postgres+PostGIS (jalankan `infrastructure/docker-compose.yml`, ganti `app/db.py`), data IDX berlisensi.
- Uji Copilot LLM dan TradingAgents dengan API key sungguhan; ekstraksi entitas/sentimen berbasis LLM.
- Verifikasi lokasi aset + eksposur komoditas ke laporan tahunan; harga nikel berlisensi.
- Rantai pasok tingkat perusahaan (butuh data hubungan bersumber), kapal AIS, alert terjadwal/email, voice.

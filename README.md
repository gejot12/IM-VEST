# IM-VEST Intelligence

> EVENT → IMPACT → COMPANY → STOCK → OPPORTUNITY → ACTION

Website riset pasar modal Indonesia: dashboard pasar, intelligence emiten, berita→event→dampak, peta aset,
portofolio, Client Radar + Meeting Brief untuk RM, dan Copilot. Berjalan lokal, data nyata dari sumber publik.

## Jalankan (Windows, PowerShell)

Prasyarat: [uv](https://docs.astral.sh/uv/) dan Node.js 20+.

```powershell
.\run.ps1            # pertama kali: pasang dependensi, tarik data (~3 menit), build, buka http://localhost:3000
.\run.ps1 -Refresh   # tarik ulang harga, fundamental, berita
```

Login (password default `dev-password`, ganti dengan env `IMVEST_SEED_PASSWORD` sebelum seed pertama):

| Email | Peran | Akses |
|---|---|---|
| `investor@imvest.local` | INVESTOR | dashboard, emiten, news, event, peta, portofolio, copilot |
| `rm@imvest.local` | RM | + Client Radar, Meeting Brief |
| `admin@imvest.local` | ADMIN | semuanya + analisis teks event |

## Apa yang NYATA dan apa yang CONTOH

| Bagian | Status |
|---|---|
| Harga saham, IHSG, LQ45, kurs, emas, minyak, tembaga | **Nyata**, Yahoo Finance (endpoint tidak resmi) |
| Fundamental (market cap, PER, PBV, ROE, dividen) | **Nyata**, Yahoo (TTM) |
| Berita | **Nyata**, Google News RSS (judul + tautan) |
| Gempa, cuaca | **Nyata**, USGS, Open-Meteo |
| Sentimen, entitas, event, dampak | **Aturan kata kunci** atas judul (bukan LLM). Dampak = inferensi LOW |
| Research Priority Score | Dihitung dari data di atas; urutan bahan riset, **bukan rekomendasi** |
| Lokasi aset (11 titik) | **Perkiraan**, belum diverifikasi; ditandai di UI |
| Eksposur komoditas per emiten | Daftar internal `seed/companies.csv`, belum diverifikasi |
| Klien, portofolio investor | **DUMMY** (`is_dummy`), untuk demo |
| Harga nikel | **Tidak tersedia** (tidak ada sumber gratis); UI menyatakan itu |
| Titik api (FIRMS) | Butuh `FIRMS_MAP_KEY` gratis dari NASA; tanpa itu layer melapor `NEEDS_KEY` |
| Copilot LLM (tool-calling) | Aktif otomatis bila `ANTHROPIC_API_KEY` ada ([llm_copilot.py](apps/api/app/llm_copilot.py)); loop dan batas akses diuji dengan klien palsu, **belum diuji ke API sungguhan**. Tanpa key: mode aturan |
| Watchlist & alert | Per pengguna; alert dihitung saat dibuka (gerak harga ≥3%, event berdampak, berita negatif) |
| Supply Chain | Dasar: tahap **generik** per komoditas + aset tercatat (perkiraan); tahap hilir 'tidak ada data' |
| Globe 3D | Prototipe CesiumJS (CDN) + citra Esri: aset dan gempa |
| Analisis multi-agent TradingAgents | Adaptor ada ([app/research.py](apps/api/app/research.py)) tapi **belum diuji**: butuh paket + API key LLM |

## Batas lisensi (baca sebelum dipakai di luar pribadi)

- Yahoo (tidak resmi) dan Google News RSS (non-komersial) cocok untuk prototipe/pribadi. Produksi: IDX Data Services + provider berita berlisensi.
- Open-Meteo gratis hanya non-komersial. Peta: © OpenStreetMap contributors, OpenFreeMap. Gempa: USGS.
- Jangan masukkan data nasabah asli sebelum ada Postgres, enkripsi, dan review keamanan; saat ini SQLite lokal.

## Konfigurasi opsional (env)

`IMVEST_SEED_PASSWORD`, `IMVEST_JWT_SECRET` (wajib bila `IMVEST_ENV=production`), `FIRMS_MAP_KEY`,
`ANTHROPIC_API_KEY` (Copilot LLM; juga TradingAgents), `IMVEST_COPILOT_MODEL`, `IMVEST_AUTO_REFRESH_HOURS` (mis. `6`: perbarui harga/berita otomatis).

## Catatan keamanan

- Data pihak ketiga (judul/URL berita, nama lokasi USGS) tidak pernah masuk HTML mentah: popup peta dibangun dari node DOM, URL hanya `http(s)`.
- `npm audit` melaporkan advisory pada `maplibre-gl` (sanitizer `setHTML`, **tidak dipakai** di kode ini) dan `postcss` bawaan Next (hanya build-time). Naikkan maplibre ke versi >6.4 bila worker-nya sudah kompatibel dengan Next.
- Login terkunci setelah 5 gagal; cookie `HttpOnly`, `Secure` saat `IMVEST_ENV=production`. Belum ada: CSRF token (mitigasi: `SameSite=Lax`), 2FA, enkripsi DB. Ini bukan `/security-review` penuh.

## Template & tema

UI memakai **Tabler** ([@tabler/core](https://github.com/tabler/tabler) dan [@tabler/icons-webfont](https://github.com/tabler/tabler-icons), keduanya MIT, bebas dipakai komersial) dengan tema **Ocean Depths** dari skill `theme-factory`
(navy `#1a2332`, teal `#2d8b8b`, seafoam `#a8dadc`, cream `#f1faee`). Ganti warna di [globals.css](apps/web/app/globals.css) (blok variabel di atas).

## Struktur

`apps/api` FastAPI + SQLite (dev) · `apps/web` Next.js · `docs/` blueprint (skema PostgreSQL/PostGIS produksi di `01-schema.sql`)
· `seed/` · [docs/07-status.md](docs/07-status.md) status per hari roadmap.

Tes: `cd apps/api; uv run pytest` (43 tes). Uji asap server yang berjalan (3 peran × 14 endpoint + 12 halaman): `python scripts/smoke.py`.

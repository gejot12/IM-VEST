# Deploy gratis tanpa kartu: web + API di Vercel

Dua proyek Vercel (Hobby, gratis) dari repo yang sama:

| Proyek | Root Directory | Isi |
|---|---|---|
| `im-vest` | `apps/web` | Next.js (UI); `API_URL` menunjuk ke proyek API |
| `im-vest-api` | `apps/api` | FastAPI (serverless Python) + snapshot data |

## Cara kerja API di Vercel
- **Saat build** (`apps/api/vercel.json` → `buildCommand`): `python -m app.refresh` menarik harga, fundamental, dan berita ke `data/snapshot.sqlite3` (±8–10 menit; batas build Vercel 45 menit).
- **Saat berjalan**: snapshot disalin ke `/tmp/imvest.db` (satu-satunya folder yang bisa ditulis). Watchlist dan log akses bersifat sementara dan hilang tiap instans baru.
- **Data diperbarui dengan redeploy** (Deployments → Redeploy), atau setiap push ke `main`.
- Variabel wajib: **`IMVEST_SEED_PASSWORD`** (password 3 akun demo; juga dipakai menurunkan secret JWT). Tanpa ini build gagal dengan pesan jelas.
- Opsional: `IMVEST_JWT_SECRET` (≥32 karakter acak) jika mau secret terpisah; `FIRMS_MAP_KEY`; `ANTHROPIC_API_KEY`.

## Langkah
1. Vercel → **Add New → Project** → impor `gejot12/IM-VEST` → **Root Directory `apps/api`** → Framework "Other".
   Environment Variables: `IMVEST_SEED_PASSWORD` = password kuat pilihanmu. **Deploy**.
2. Salin URL proyek API (mis. `https://im-vest-api.vercel.app`).
3. Proyek `im-vest` → Settings → Environment Variables → `API_URL` = URL langkah 2 (tanpa `/` di akhir) → **Redeploy**.
4. Uji: `python scripts/smoke.py PASSWORD https://im-vest.vercel.app`.

## Batasan yang perlu diketahui
- IP build/runtime Vercel bisa dibatasi Yahoo/Google; kalau harga/berita kosong, itu sumbernya, bukan bug.
- Data Yahoo/Google News hanya untuk pemakaian pribadi (lihat README); jangan jadikan layanan publik/komersial tanpa sumber berlisensi.
- Snapshot tidak masuk repo (`.gitignore`); hanya ada di hasil build Vercel.

## Alternatif
Render (butuh kartu), Docker/VPS: `docker build -f apps/api/Dockerfile -t imvest-api .` (belum diuji di mesin pengembangan).

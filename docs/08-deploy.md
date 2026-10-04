# Deploy: web di Vercel, API di Render (gratis)

Arsitektur: browser → **Vercel** (Next.js, proxy `/api/*`) → **Render** (FastAPI + SQLite sementara).
Cookie login ada di domain Vercel (same-origin lewat proxy), jadi tidak perlu CORS.

> Saya (asisten) tidak punya akses ke akun hosting-mu, jadi langkah klik di bawah kamu yang menjalankan. Semua konfigurasi sudah ada di repo.

## 1. API di Render (kerjakan dulu)

1. https://render.com → daftar/login dengan GitHub.
2. **New +** → **Blueprint** → pilih repo `gejot12/IM-VEST` → Render membaca [render.yaml](../render.yaml).
3. Isi variabel yang diminta: **`IMVEST_SEED_PASSWORD`** = password kuat untuk 3 akun demo (min. 12 karakter). `IMVEST_JWT_SECRET` dibuat otomatis.
4. **Apply**. Build Docker ±3–5 menit. Catat URL-nya, mis. `https://imvest-api.onrender.com`.
5. Setelah hidup, server mengisi data sendiri di latar (harga, fundamental, berita; ±3 menit). Selama itu halaman tampil "data tidak tersedia".

Catatan paket gratis: layanan tidur setelah ±15 menit tanpa trafik dan **disk bersifat sementara**, jadi setiap bangun dari tidur/restart database dibangun ulang (±3 menit) dan watchlist pengguna hilang. Untuk data tetap: pakai Postgres (lihat README, "Belum ada").

## 2. Web di Vercel

1. https://vercel.com → login dengan GitHub → **Add New… → Project** → impor `gejot12/IM-VEST`.
2. **Root Directory**: `apps/web` (Framework: Next.js terdeteksi otomatis).
3. **Environment Variables**: `API_URL` = URL Render dari langkah 1 (tanpa garis miring di akhir).
4. **Deploy**. Alamat publik: `https://<nama-proyek>.vercel.app`.
5. Login memakai email `investor@imvest.local`, `rm@imvest.local`, `admin@imvest.local` dan password yang kamu isi di langkah 1.3.

Mengganti `API_URL` setelahnya: ubah variabel lalu **Redeploy** (rewrite dibaca saat build).

## Peringatan sebelum dibuka ke publik

- **Siapa pun yang tahu URL + password bisa masuk.** Jangan bagikan password; akun demo berisi data DUMMY, tapi API-nya meneruskan data Yahoo/Google News ke pengunjung.
- **Ketentuan data:** Yahoo (tidak resmi) dan Google News RSS (non-komersial) dilarang/tidak cocok untuk layanan publik/komersial. Untuk pemakaian pribadi atau demo terbatas, batasi akses; untuk produksi, ganti ke IDX Data Services dan berita berlisensi.
- **IP cloud bisa diblokir Yahoo/Google:** bila harga/berita kosong setelah bootstrap, lihat log Render; itu bukan bug aplikasi.
- Repositori ini **publik**; jangan commit `.env` atau kunci. Variabel rahasia hanya di dashboard Render/Vercel.
- Ini bukan nasihat investasi; disclaimer tampil di tiap halaman analisis dan di `/disclaimer`.

## Alternatif satu server (VPS/Docker)

`docker build -f apps/api/Dockerfile -t imvest-api .` untuk API; web: `cd apps/web && npm ci && npm run build && API_URL=http://api:8000 npm start`.
(Dockerfile belum diuji di mesin pengembangan karena tidak ada Docker; Render akan mengujinya saat build pertama.)

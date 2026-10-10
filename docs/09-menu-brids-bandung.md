# Menambah menu "IM-VEST Intelligence" di website BRIDS Bandung (Vercel)

Proyek: `brids-bandung` (portofolio-nasabah.vercel.app). Stack yang terbaca dari dashboard Vercel (hanya baca):
Vite + React 19 + `react-router-dom` + Tailwind, sidebar di `src/components/Layout.tsx`
(`navLinkClass = ({ isActive }: { isActive: boolean }) => string`, daftar `NavLink` di sekitar baris 100–120).

Proyek itu di-deploy lewat `vercel deploy` (tanpa Git), jadi perubahan dibuat di kode lokal (laptop) lalu di-deploy ulang.

## 1. Edit `src/components/Layout.tsx`

Sisipkan blok ini **tepat setelah** `</NavLink>` milik "Kalender Kunjungan"
(sebelum `{currentUser?.role === 'BM' && (` pertama):

```tsx
        <a
          href="https://im-vest.vercel.app"
          target="_blank"
          rel="noopener noreferrer"
          className={navLinkClass({ isActive: false })}
        >
          🛰️ IM-VEST Intelligence ↗
        </a>
```

Sengaja memakai `<a target="_blank">`, bukan `<NavLink>` atau iframe:
- IM-VEST adalah aplikasi terpisah dengan login sendiri; cookie login `SameSite=Lax` tidak terkirim di dalam iframe lintas situs.
- Link keluar tidak memengaruhi routing SPA (`vercel.json` me-rewrite semua path non-`/api` ke `index.html`).

`navLinkClass({ isActive: false })` sesuai tipe aslinya, jadi `tsc -b` di `npm run build` tetap lolos.

## 2. Build dan deploy (di laptop)

```bash
npm run build
vercel deploy --prod
```

## 3. Prasyarat agar tautannya berguna

- API IM-VEST di Render sudah hidup dan `API_URL` di proyek Vercel `im-vest` sudah diisi (lihat `docs/08-deploy.md`).
- Pengguna IM-VEST memakai akun IM-VEST sendiri (email `@imvest.local`), bukan akun BRIDS.
- Data IM-VEST (Yahoo/Google News) hanya untuk pemakaian pribadi; jangan dipakai sebagai layanan resmi nasabah tanpa sumber berlisensi.

# Globe 3D di halaman Analisa Saham BRIDS Bandung

Tujuan: saat RM membuka **Analisa Saham** sebuah emiten, di halaman itu muncul **peta/globe 3D** berisi aset emiten
tersebut, dan bisa **melihat wilayahnya** (pilih provinsi → semua aset di wilayah itu; klik titik → tombol "Analisa saham").
Hanya globe ini yang dibawa ke BRIDS; menu IM-VEST lain tidak dipasang.

Terbaca dari kode yang ter-deploy (hanya baca): `src/pages/StockDetailPage.tsx` memakai `useParams<{ symbol }>()`,
`cleanSymbol()` dari `../lib/format`, dan `navigate`; bagian halaman bernomor "1." … "8. Berita 1 Bulan Terakhir"
dengan pola `<div className="mb-6"><h2 className="text-sm font-semibold text-gray-700 mb-2">…</h2>…</div>`.

## Arsitektur
```
Halaman Analisa Saham (BRIDS)  --GET (tanpa login, CORS)-->  https://im-vest-api.vercel.app/api/v1/public/*
   <AssetMap ticker="ANTM" />                                  /assets?ticker=ANTM   (aset emiten)
   (CesiumJS dari CDN, citra Esri)                             /assets?province=...  (semua aset wilayah)
                                                               /regions              (daftar provinsi)
```
- Endpoint publik **baca-saja**, tanpa data klien/portofolio; wajib salah satu filter (`ticker` atau `province`).
- CORS hanya untuk `brids-bandung.vercel.app`, `portofolio-nasabah.vercel.app`, `localhost:5173`
  (ubah dengan env `IMVEST_CORS_ORIGINS` di proyek `im-vest-api`).

## Langkah di laptop (±5 menit)

1. **Salin komponen** [`apps/web/app/AssetMap.tsx`](../apps/web/app/AssetMap.tsx) dari repo ini ke proyek BRIDS sebagai
   `src/components/AssetMap.tsx` (tanpa diubah; tidak butuh paket baru).

2. **Edit `src/pages/StockDetailPage.tsx`**
   - Tambah impor di atas, bersama impor lain:
     ```tsx
     import AssetMap from '../components/AssetMap'
     ```
   - Sisipkan bagian baru **setelah** blok "8. Berita 1 Bulan Terakhir" (sebelum `</div>` penutup halaman, ±baris 160):
     ```tsx
     <div className="mb-6">
       <h2 className="text-sm font-semibold text-gray-700 mb-2">9. Peta Aset &amp; Wilayah</h2>
       <AssetMap
         ticker={cleanSymbol(symbol)}
         onAnalyze={(t) =>
           navigate(
             window.location.pathname.replace(/[^/]+\/?$/, t + (symbol.endsWith('.JK') ? '.JK' : '')) +
               window.location.search,
           )
         }
       />
     </div>
     ```
   `onAnalyze` mengganti segmen terakhir URL (simbol) dengan emiten yang diklik, sehingga tidak bergantung pada nama rute;
   `?client=` tetap terbawa. Hapus `onAnalyze` bila tidak perlu tombol itu.

3. **Build & deploy**
   ```bash
   npm run build
   vercel deploy --prod
   ```

## Pemakaian
- Default menampilkan aset emiten yang sedang dianalisis dan terbang ke lokasinya.
- Dropdown **Wilayah** → provinsi (mis. "Sulawesi Tenggara") menampilkan semua aset di wilayah itu (emiten lain,
  bandara, pelabuhan umum); pilih "Aset ANTM" untuk kembali.
- Klik titik atau baris daftar → detail + tombol **Analisa saham {ticker}**.

## Batasan
- Lokasi aset **perkiraan kawasan**, belum diverifikasi (ditandai di komponen).
- Data aset baru tercakup untuk 30 emiten IM-VEST; emiten lain menampilkan "Belum ada aset tercatat".
- Butuh akses internet ke `cesium.com` (CesiumJS) dan `services.arcgisonline.com` (citra).
- Ganti alamat API lewat prop `apiBase` bila API dipindah.

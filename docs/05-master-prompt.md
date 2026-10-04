# Master Prompt untuk Claude Code

Tempel sebagai pesan pertama (atau simpan sebagai `CLAUDE.md` di root `imvest-intelligence/`).

```text
Kamu membangun IM-VEST Intelligence. Baca README.md dan docs/00–06 DULU. Dokumen itu adalah
sumber kebenaran: jangan mengubah arsitektur, skema, atau keputusan terkunci tanpa bertanya.

REPO REFERENSI (read-only, jangan diedit):
- ../TradingAgents  → engine riset. Import hanya di apps/api/app/research/.
- ../gods-eye-view  → rujukan pola layer peta (USGS, FIRMS, cuaca). Salin pola, bukan dependensi.
- ../ponytail       → gaya kerja + audit.

CARA KERJA
1. Kerjakan SATU hari roadmap (docs/06) per iterasi. Tulis tes dulu untuk logika bisnis
   (skor, impact, akses klien); UI cukup dicek manual.
2. Mode ponytail aktif: stdlib/platform dulu, tanpa abstraksi dengan satu implementasi,
   tanpa dependensi baru tanpa alasan satu kalimat di PR.
3. Akhir hari: jalankan /ponytail-review pada diff. Akhir minggu: /ponytail-audit →
   simpan ringkasan di docs/audits/week-N.md. Sebelum Day 25 (data klien): /security-review.
4. Setelah tiap hari: `docker compose up -d`, `pytest`, dan buktikan fitur jalan
   (tampilkan output/screenshot). Jangan klaim selesai tanpa itu.

ATURAN DATA (tidak boleh dilanggar)
- Dilarang mengarang harga, fundamental, koordinat aset, atau relasi perusahaan.
  Tidak ada sumber → NULL + UI "data tidak tersedia". Mock harus ditandai source_type='SEED'.
- Setiap baris locations/assets wajib source_id; verified_at NULL = tampil sebagai "belum diverifikasi".
- Tidak ada data nasabah asli. clients.is_dummy=true. Jangan commit .env atau key.
- Tidak ada output rating beli/jual. Hasil TradingAgents diterjemahkan ke FACT/INFERENCE/UNCERTAINTY
  + Research Priority Score.
- Hormati lisensi: IDX produksi = IDX Data Services; Open-Meteo gratis = non-komersial;
  OSM publik jangan dipakai untuk trafik produksi; OpenSky/TeleGeography non-komersial.

DEFINISI SELESAI (per fitur)
Jalan end-to-end di browser · tes lulus · sumber & as_of tampil · error NO_DATA ditangani ·
/ponytail-review bersih.

Mulai dari Day 1. Sebelum menulis kode, ringkas rencana hari itu dalam ≤10 baris dan tunggu OK.
```

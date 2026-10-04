import { DISCLAIMER } from "../disclaimerText";

export const metadata = { title: "Disclaimer · IM-VEST Intelligence" };

export default function DisclaimerPage() {
  return (
    <>
      <h1>Disclaimer</h1>
      <div className="banner disclaimer" style={{ fontSize: 14 }}>{DISCLAIMER}</div>
      <h2>Sumber data dan batasannya</h2>
      <ul>
        <li>Harga, kuotasi, dan fundamental: Yahoo Finance (endpoint tidak resmi), bisa tertunda, berubah, atau berhenti sewaktu-waktu.</li>
        <li>Berita: judul dan tautan dari Google News RSS; isi artikel milik penerbitnya masing-masing. Sentimen dan entitas ditentukan aturan kata kunci atas judul, bukan membaca isi.</li>
        <li>Gempa: USGS. Cuaca: Open-Meteo. Peta: OpenStreetMap contributors, OpenFreeMap. Citra globe: Esri.</li>
        <li>Lokasi aset dan eksposur komoditas per emiten adalah perkiraan internal yang belum diverifikasi ke dokumen perusahaan.</li>
        <li>Data nasabah, portofolio contoh, dan Client Radar adalah data DUMMY untuk demonstrasi.</li>
      </ul>
    </>
  );
}

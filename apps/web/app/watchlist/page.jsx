"use client";
import { useApi, pct, cls, num, Dir, Loading } from "../lib";

const KIND = { EVENT: "Event berdampak", PRICE: "Gerak harga", NEWS: "Berita negatif" };

export default function Watchlist() {
  const w = useApi("/watchlist");
  const a = useApi("/alerts");
  return (
    <>
      <h1>Watchlist & Alert</h1>
      <div className="muted">Alert dihitung saat halaman dibuka: harga bergerak ≥3% sehari, event berdampak 3 hari terakhir, atau ≥2 berita negatif. Tambahkan emiten dengan tombol ★ di halamannya.</div>
      <h2>Alert</h2>
      <Loading s={a} />
      {a.data?.length ? a.data.map((x, i) => (
        <div key={i} className="row"><span className="tag">{KIND[x.type]}</span> <Dir d={x.direction} /> <a href={`/companies/${x.ticker}`}><b>{x.ticker}</b></a> <span className="muted">{x.text}</span></div>
      )) : !a.loading && <p className="muted">Tidak ada alert{w.data?.length ? "" : " (watchlist masih kosong)"}.</p>}
      <h2>Emiten dipantau</h2>
      <table>
        <thead><tr><th>Ticker</th><th>Nama</th><th>Sektor</th><th>Harga</th><th>Hari ini</th><th>Alert</th></tr></thead>
        <tbody>{w.data?.map((c) => (
          <tr key={c.ticker}><td><a href={`/companies/${c.ticker}`}><b>{c.ticker}</b></a></td><td>{c.name}</td><td>{c.sector}</td><td>{num(c.close)}</td>
            <td className={cls(c.change_pct)}>{pct(c.change_pct)}</td><td>{c.alerts ? <span className="tag warn">{c.alerts}</span> : "–"}</td></tr>))}</tbody>
      </table>
    </>
  );
}

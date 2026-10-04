"use client";
import { use } from "react";
import { useApi, pct, cls, num, NewsList, Loading } from "../../lib";

export default function Sector({ params }) {
  const { code } = use(params);
  const s = useApi(`/sectors/${code}`);
  if (s.error) return <p>{s.error.message}</p>;
  if (!s.data) return <Loading s={s} />;
  const d = s.data;
  return (
    <>
      <h1>{d.name} <span className={cls(d.change_pct)}>{pct(d.change_pct)}</span></h1>
      <div className="muted">Rata-rata perubahan harian emiten sektor ini (harga tersimpan).</div>
      <h2>Emiten</h2>
      <table>
        <thead><tr><th>Ticker</th><th>Nama</th><th>Harga</th><th>Hari ini</th><th>Komoditas</th></tr></thead>
        <tbody>{d.companies.map((c) => (
          <tr key={c.ticker}><td><a href={`/companies/${c.ticker}`}><b>{c.ticker}</b></a></td><td>{c.name}</td><td>{num(c.close)}</td>
            <td className={cls(c.change_pct)}>{pct(c.change_pct)}</td><td>{c.commodities.map((x) => <span className="tag" key={x}>{x}</span>)}</td></tr>))}</tbody>
      </table>
      <h2>Berita sektor (14 hari)</h2>
      <NewsList items={d.news} />
    </>
  );
}

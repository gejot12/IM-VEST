"use client";
import { useApi, num, idr, Loading } from "../lib";

export default function Portfolio() {
  const p = useApi("/portfolio");
  const d = p.data;
  return (
    <>
      <h1>My Portfolio</h1>
      <div className="banner">Posisi di bawah adalah <b>contoh</b> (SEED). Nilai memakai harga terakhir tersimpan. Hanya saham; kas dan obligasi belum ada.</div>
      <Loading s={p} />
      {d && <>
        <div className="grid">
          <div className="card"><div className="muted">Total nilai saham</div><div style={{ fontSize: 22 }}>{idr(d.total_value)}</div></div>
          <div className="card"><div className="muted">Top holding</div><div style={{ fontSize: 22 }}>{d.top_holding?.ticker} {d.top_holding?.weight_pct}%</div></div>
          <div className="card"><div className="muted">Konsentrasi sektor</div><div style={{ fontSize: 22 }}>{d.top_sector_pct}% <span className={`tag ${d.concentration_risk === "HIGH" ? "down" : d.concentration_risk === "LOW" ? "up" : "warn"}`}>{d.concentration_risk}</span></div></div>
        </div>
        <p>{d.note}</p>
        <h2>Alokasi sektor</h2>
        {d.allocation.map((a) => (
          <div key={a.sector} style={{ margin: "6px 0" }}><div>{a.sector} <span className="muted">{a.pct}%</span></div><div className="bar"><i style={{ width: `${a.pct}%` }} /></div></div>
        ))}
        <h2>Posisi</h2>
        <table>
          <thead><tr><th>Ticker</th><th>Sektor</th><th>Lembar</th><th>Harga</th><th>Nilai</th><th>Bobot</th></tr></thead>
          <tbody>{d.positions.map((r) => (
            <tr key={r.ticker}><td><a href={`/companies/${r.ticker}`}><b>{r.ticker}</b></a></td><td>{r.sector}</td><td>{num(r.quantity)}</td>
              <td>{num(r.price)}</td><td>{idr(r.value)}</td><td>{r.weight_pct ?? "–"}%</td></tr>))}</tbody>
        </table>
      </>}
    </>
  );
}

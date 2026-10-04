"use client";
import { Fragment, useState } from "react";
import { useApi, idr, day, Loading } from "../lib";

const FILTERS = [["", "Semua"], ["CASH_DEPLOYMENT", "Kas tinggi"], ["REACTIVATION", "Dormant"], ["REBALANCING", "Terkonsentrasi"], ["BOND", "Peluang obligasi"], ["STOCK", "Peluang saham"]];
const BADGE = { HIGH: "🔥", MEDIUM: "🟡", LOW: "⚪" };

export default function Clients() {
  const r = useApi("/clients/radar");
  const [f, setF] = useState("");
  const [open, setOpen] = useState(null);
  if (r.error) return <p>{r.error.message}</p>;
  const rows = r.data?.filter((c) => !f || c.opportunities.some((o) => o.type === f));
  return (
    <>
      <h1>Client Radar</h1>
      <div className="banner">Seluruh data nasabah adalah <b>DUMMY</b> untuk demo. Skor RM: 30% kas, 25% potensi transaksi, 20% inaktivitas, 15% konsentrasi, 10% relevansi pasar (deterministik).</div>
      <div className="toolbar">{FILTERS.map(([v, l]) => <button key={v} className={f === v ? "" : "ghost"} onClick={() => setF(v)}>{l}</button>)}</div>
      <Loading s={r} />
      <table>
        <thead><tr><th></th><th>Klien</th><th>AUM</th><th>Kas</th><th>Transaksi terakhir</th><th>Skor</th><th>Peluang</th></tr></thead>
        <tbody>{rows?.map((c) => (
          <Fragment key={c.id}>
            <tr onClick={() => setOpen(open === c.id ? null : c.id)} style={{ cursor: "pointer" }}>
              <td>{BADGE[c.priority]}</td><td><b>{c.name}</b><div className="muted">{c.client_code} · {c.risk_profile}</div></td>
              <td>{idr(c.aum)}</td><td>{idr(c.cash_balance)}</td><td>{day(c.last_transaction_at)}</td><td>{c.score}</td>
              <td>{c.opportunities.map((o) => <span key={o.type} className="tag">{o.type}</span>)}</td>
            </tr>
            {open === c.id && (
              <tr><td colSpan={7}>
                <div className="card">
                  <b>Next best action</b>
                  {c.opportunities.length ? c.opportunities.map((o, i) => (
                    <p key={i} style={{ margin: "6px 0" }}><span className="tag">{o.type}</span> {o.reason} <b>→ {o.recommended_action}</b>
                      {o.estimated_value ? <span className="muted"> (potensi ≈ {idr(o.estimated_value)})</span> : null}</p>
                  )) : <p className="muted">Tidak ada peluang terdeteksi.</p>}
                  <a href={`/clients/${c.id}/brief`}>Siapkan meeting brief →</a>
                </div>
              </td></tr>
            )}
          </Fragment>
        ))}</tbody>
      </table>
    </>
  );
}

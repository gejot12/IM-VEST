"use client";
import { use } from "react";
import { useApi, Loading } from "../../lib";

const COMM = ["NICKEL", "COAL", "GOLD", "COPPER", "CPO"];

export default function Supply({ params }) {
  const { commodity } = use(params);
  const r = useApi(`/supply-chain/${commodity}`);
  return (
    <>
      <h1>Supply Chain <span className="tag warn">fase 2 · dasar</span></h1>
      <div className="toolbar">{COMM.map((c) => <a key={c} href={`/supply/${c}`} className={`tag ${c === commodity.toUpperCase() ? "up" : ""}`} style={{ padding: "4px 12px" }}>{c}</a>)}</div>
      <Loading s={r} />
      {r.error && <p className="muted">{r.error.message}</p>}
      {r.data && <>
        <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", alignItems: "stretch" }}>
          {r.data.stages.map((s, i) => (
            <div key={s.stage} className="card">
              <div className="muted">Tahap {i + 1}</div><b>{s.stage}</b>
              {s.assets.length ? s.assets.map((a) => (
                <div key={a.ticker + a.name} className="row"><a href={`/companies/${a.ticker}`}><b>{a.ticker}</b></a> {a.name}
                  <div className="muted">{a.province} {a.verified ? "" : <span className="tag warn">perkiraan</span>}</div></div>
              )) : <p className="muted" style={{ marginTop: 8 }}>{s.asset_type ? "Belum ada aset tercatat" : "Tidak ada data"}</p>}
              {i < r.data.stages.length - 1 && <div className="muted" style={{ textAlign: "right" }}>↓ / →</div>}
            </div>
          ))}
        </div>
        <h2>Emiten berekposur {r.data.commodity}</h2>
        <div>{r.data.exposed_companies.map((t) => <a key={t} href={`/companies/${t}`} className="tag">{t}</a>)}</div>
        <div className="banner" style={{ marginTop: 16 }}>{r.data.note}</div>
      </>}
    </>
  );
}

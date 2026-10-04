"use client";
import { use, useEffect, useState } from "react";
import { useApi, pct, cls, num, idr, Source, NewsList, Loading, Disclaimer, ExportPdf, PrintHeader } from "../../lib";

function Chart({ rows }) {
  const v = rows.map((r) => r.close), lo = Math.min(...v), hi = Math.max(...v);
  const pts = v.map((y, i) => `${(i / (v.length - 1)) * 600},${100 - ((y - lo) / (hi - lo || 1)) * 100}`).join(" ");
  return (
    <>
      <svg viewBox="0 0 600 100" width="100%" height="180" preserveAspectRatio="none"><polyline points={pts} fill="none" stroke="#5fc4c4" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg>
      <div className="muted">{rows[0].ts} → {rows.at(-1).ts} · low {num(lo)} · high {num(hi)}</div>
    </>
  );
}

const Stat = ({ label, children }) => <div className="card"><div className="muted">{label}</div><div style={{ fontSize: 20 }}>{children}</div></div>;
const Comp = { momentum: "Momentum", fundamental: "Fundamental", valuation: "Valuasi", catalyst: "Katalis", sentiment: "Sentimen berita", sector: "Kekuatan sektor" };

function Star({ ticker }) {
  const [on, setOn] = useState(null);
  useEffect(() => { fetch(`/api/v1/watchlist/${ticker}`).then((r) => r.ok && r.json()).then((j) => j && setOn(j.watched)); }, [ticker]);
  if (on === null) return null;
  const toggle = async () => { await fetch(`/api/v1/watchlist/${ticker}`, { method: on ? "DELETE" : "PUT" }); setOn(!on); };
  return <button className="ghost" onClick={toggle} title="Watchlist"><i className={`ti ti-star${on ? "-filled" : ""}`} /> {on ? "Dipantau" : "Pantau"}</button>;
}

export default function Company({ params }) {
  const { ticker } = use(params);
  const c = useApi(`/companies/${ticker}`);
  const p = useApi(`/companies/${ticker}/prices?range=1Y`);
  const n = useApi(`/companies/${ticker}/news`);
  const b = useApi(`/companies/${ticker}/brief`);
  const a = useApi(`/map/assets?ticker=${ticker}`);
  if (c.error) return <p>{c.error.message}</p>;
  if (!c.data) return <Loading s={c} />;
  const d = c.data, pr = b.data?.priority;
  return (
    <>
      <PrintHeader title={`Laporan Analisis ${d.ticker} — ${d.name}`} />
      <div className="toolbar" style={{ justifyContent: "space-between" }}><h1 style={{ margin: 0 }}>{d.ticker} — {d.name}</h1><div className="toolbar noprint"><Star ticker={d.ticker} /><ExportPdf name={d.ticker} /></div></div>
      <div className="muted">{d.sector} {d.commodities.map((x) => <span className="tag" key={x} title="Eksposur dari daftar internal, belum diverifikasi">{x}</span>)}</div>
      <div className="grid" style={{ marginTop: 16 }}>
        <Stat label="Harga">
          {num(d.price?.close)} <span className={cls(d.price?.change_pct)} style={{ fontSize: 14 }}>{pct(d.price?.change_pct)}</span>
          <div>{d.price && <Source type={d.price.source_type} name={d.price.source} asOf={d.price.as_of} />}</div>
        </Stat>
        <Stat label="Market cap">{idr(d.market_cap)}</Stat>
        <Stat label="PER">{d.per == null ? "–" : num(d.per, 1)}</Stat>
        <Stat label="PBV">{d.pbv == null ? "–" : num(d.pbv, 2)}</Stat>
        <Stat label="ROE">{d.roe == null ? "–" : pct(d.roe * 100)}</Stat>
        <Stat label="Dividend yield">{d.dividend_yield == null ? "–" : pct(d.dividend_yield * 100)}</Stat>
      </div>
      {d.stats_source && <div className="muted">Fundamental: {d.stats_source}, TTM per {d.stats_as_of}</div>}

      <h2>Harga 1 tahun</h2>
      <div className="card">{p.data?.length > 1 ? <Chart rows={p.data} /> : <Loading s={p} />}</div>

      <div className="cols">
        <div>
          <h2>Why it matters</h2>
          <div className="card">
            <Loading s={b} />
            {b.data && <>
              <b>FAKTA</b>{b.data.facts.map((x, i) => <p key={i} style={{ margin: "4px 0" }}>• {x}</p>)}
              {b.data.inferences.length > 0 && <><b>INFERENSI</b>{b.data.inferences.map((x, i) => <p key={i} style={{ margin: "4px 0" }}>• {x}</p>)}</>}
              <b>KETIDAKPASTIAN</b>{b.data.uncertainties.map((x, i) => <p key={i} className="muted" style={{ margin: "4px 0" }}>• {x}</p>)}
            </>}
          </div>
        </div>
        <div>
          <h2>Investment Radar</h2>
          <div className="card">
            {pr && <>
              <div style={{ fontSize: 24 }}>{pr.score} <span className="tag">{pr.label}</span></div>
              {Object.entries(Comp).map(([k, label]) => (
                <div key={k} style={{ margin: "6px 0" }}>
                  <div className="muted">{label} {pr.components[k] == null ? "— data tidak tersedia" : ""}</div>
                  <div className="bar"><i style={{ width: `${(pr.components[k] ?? 0) * 100}%` }} /></div>
                </div>
              ))}
              <div className="muted">{b.data.note}</div>
            </>}
          </div>
        </div>
      </div>

      <h2>Aset & lokasi</h2>
      {a.data?.features.length ? (
        <table><tbody>{a.data.features.map((f) => (
          <tr key={f.properties.id}><td>{f.properties.name}</td><td>{f.properties.asset_type} · {f.properties.commodity}</td><td>{f.properties.province}</td>
            <td>{f.properties.verified ? "terverifikasi" : <span className="tag warn">lokasi perkiraan</span>}</td></tr>))}</tbody></table>
      ) : <p className="muted">Aset: data tidak tersedia</p>}
      <p><a href={`/map?ticker=${d.ticker}`}>Lihat di peta →</a></p>

      <h2>Berita</h2>
      <NewsList items={n.data} />
      <Disclaimer />
    </>
  );
}

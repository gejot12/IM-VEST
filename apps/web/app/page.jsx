"use client";
import { useState } from "react";
import { useApi, pct, cls, num, day, Source, Loading } from "./lib";

function Search() {
  const [q, setQ] = useState("");
  const { data } = useApi(q.length >= 2 ? `/companies?q=${encodeURIComponent(q)}` : null);
  return (
    <div>
      <input placeholder="Cari emiten, mis. ANTM atau Bank…" value={q} onChange={(e) => setQ(e.target.value)} />
      {q.length >= 2 && data?.map((c) => (
        <div key={c.ticker} className="row"><a href={`/companies/${c.ticker}`}><b>{c.ticker}</b></a> {c.name} <span className="muted">{c.sector}</span></div>
      ))}
    </div>
  );
}

function Ask() {
  const [q, setQ] = useState("");
  return (
    <form onSubmit={(e) => { e.preventDefault(); if (q) window.location.href = `/copilot?q=${encodeURIComponent(q)}`; }} style={{ margin: "12px 0" }}>
      <input placeholder="🤖 Tanya Copilot: “Apa yang bergerak hari ini?”, “Saham terkait nikel”, “Analisis ANTM”…" value={q} onChange={(e) => setQ(e.target.value)} />
    </form>
  );
}

const heat = (v) => `hsl(${v >= 0 ? 140 : 0} 55% ${Math.max(14, 30 - Math.min(Math.abs(v), 4) * 3)}%)`;

export default function Dashboard() {
  const market = useApi("/market/overview");
  const sectors = useApi("/market/sectors");
  const dash = useApi("/dashboard");
  const alerts = useApi("/alerts");
  return (
    <>
      <Search />
      <Ask />
      <h2>Market</h2>
      <Loading s={market} />
      <div className="grid">
        {market.data?.map((m) => (
          <div className="card" key={m.code}>
            <div className="muted">{m.name}</div>
            <div style={{ fontSize: 20 }}>{num(m.value, 2)}</div>
            <div className={cls(m.change_pct)}>{pct(m.change_pct)}</div>
            <Source type={m.source_type} name={m.source} asOf={m.as_of} />
          </div>
        ))}
        <div className="card"><div className="muted">Nikel</div><div className="muted">harga: data tidak tersedia (tidak ada sumber gratis)</div></div>
      </div>

      <div className="cols">
        <div>
          <h2>Market Radar — sektor</h2>
          <div className="grid">
            {sectors.data?.map((s) => (
              <a key={s.code} href={`/sectors/${s.code}`} className="card" style={{ background: heat(s.change_pct), textDecoration: "none", color: "inherit" }}>
                <b>{s.name}</b><div>{pct(s.change_pct)}</div><div className="muted">{s.companies} emiten</div>
              </a>
            ))}
          </div>
        </div>
        <div>
          <h2>Ringkasan hari ini</h2>
          <div className="card">
            <Loading s={dash} />
            {dash.data?.brief.map((l, i) => <p key={i} style={{ margin: "6px 0" }}>{l}</p>)}
            <div className="muted">Dihitung dari data tersimpan (aturan, bukan LLM).</div>
          </div>
        </div>
      </div>

      <h2>Prioritas riset (Research Priority Score)</h2>
      <div className="muted" style={{ marginBottom: 8 }}>Urutan bahan riset dari momentum, fundamental, valuasi, katalis, sentimen, sektor. Bukan rekomendasi beli/jual.</div>
      <div className="grid">
        {dash.data?.priorities.map((p) => (
          <a key={p.ticker} href={`/companies/${p.ticker}`} className="card" style={{ textDecoration: "none", color: "inherit" }}>
            <b>{p.ticker}</b> <span className={`tag ${p.label === "HIGH" ? "up" : p.label === "LOW" ? "down" : ""}`}>{p.label}</span>
            <div style={{ fontSize: 22 }}>{p.score}</div>
            <div className="bar"><i style={{ width: `${p.score}%` }} /></div>
            <div className="muted">data {Math.round(p.data_confidence * 100)}%</div>
          </a>
        ))}
      </div>

      {alerts.data?.length > 0 && <>
        <h2>Alert watchlist</h2>
        {alerts.data.slice(0, 5).map((x, i) => <div key={i} className="row"><span className="tag warn">{x.type}</span> <a href={`/companies/${x.ticker}`}><b>{x.ticker}</b></a> <span className="muted">{x.text}</span></div>)}
        <p><a href="/watchlist">Semua alert →</a></p>
      </>}

      <h2>Event penting</h2>
      {dash.data?.events.length ? dash.data.events.map((e) => (
        <div key={e.id} className="row"><span className="tag">{e.event_type}</span> {e.title} <span className="muted">{day(e.ts)}</span></div>
      )) : <p className="muted">Belum ada event. Jalankan refresh data.</p>}
      <p><a href="/events">Lihat semua event & dampaknya →</a></p>
    </>
  );
}

"use client";
import { use } from "react";
import { useApi, idr, num, pct, cls, day, NewsList, Loading, Disclaimer, ExportPdf, PrintHeader } from "../../../lib";

export default function Brief({ params }) {
  const { id } = use(params);
  const r = useApi(`/clients/${id}/meeting-brief`);
  if (r.error) return <p>{r.error.message}</p>;
  if (!r.data) return <Loading s={r} />;
  const { client: c, portfolio: p, recent_news, market_context, event_impacts, questions } = r.data;
  return (
    <>
      <div className="noprint toolbar"><ExportPdf name={`Brief_${c.client_code}`} /><a href="/clients">← Client Radar</a></div>
      <PrintHeader title={`Meeting Brief — ${c.name}`} />
      <h1>Meeting Brief — {c.name}</h1>
      <div className="banner">{r.data.disclaimer} Dibuat {r.data.generated_at}.</div>
      <div className="grid">
        <div className="card"><div className="muted">AUM</div>{idr(c.aum)}</div>
        <div className="card"><div className="muted">Kas</div>{idr(c.cash_balance)}</div>
        <div className="card"><div className="muted">Profil risiko</div>{c.risk_profile}</div>
        <div className="card"><div className="muted">Transaksi terakhir</div>{day(c.last_transaction_at)}</div>
        <div className="card"><div className="muted">Skor RM</div>{c.score} ({c.priority})</div>
      </div>
      <h2>Portofolio saat ini</h2>
      <p>{p.note}</p>
      <table><tbody>{p.positions.map((x) => <tr key={x.ticker}><td><b>{x.ticker}</b></td><td>{x.sector}</td><td>{num(x.quantity)} lembar</td><td>{idr(x.value)}</td><td>{x.weight_pct ?? "–"}%</td></tr>)}</tbody></table>
      <h2>Konteks pasar</h2>
      {market_context.map((s) => <div key={s.code} className="row">{s.name} <span className={cls(s.change_pct)}>{pct(s.change_pct)}</span></div>)}
      {Object.keys(event_impacts).length > 0 && <>
        <h2>Event terkait kepemilikan</h2>
        {Object.entries(event_impacts).map(([t, v]) => v.slice(0, 2).map((i, k) => <div key={t + k} className="row"><b>{t}</b> {i.direction}: {i.title} <div className="muted">{i.reason}</div></div>))}
      </>}
      <h2>Berita terkait kepemilikan</h2>
      <NewsList items={recent_news} />
      <h2>Potensi peluang & aksi</h2>
      {c.opportunities.length ? c.opportunities.map((o, i) => <p key={i}><span className="tag">{o.type}</span> {o.reason} <b>→ {o.recommended_action}</b></p>) : <p className="muted">Tidak ada.</p>}
      <h2>Pertanyaan untuk nasabah</h2>
      <ol>{questions.map((q) => <li key={q}>{q}</li>)}</ol>
      <Disclaimer />
    </>
  );
}

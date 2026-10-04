"use client";
import { useState } from "react";
import { useApi, post, day, Dir, Conf, Loading, safeUrl, Disclaimer, ExportPdf, PrintHeader } from "../lib";

function Impacts({ id }) {
  const r = useApi(`/events/${id}/impacts`);
  if (r.loading) return <Loading s={r} />;
  if (!r.data?.length) return <p className="muted">Tidak ada dampak ke emiten tercatat (mis. butuh data lokasi aset).</p>;
  return (
    <table>
      <thead><tr><th>Emiten</th><th>Dampak</th><th>Skor</th><th>Alasan</th></tr></thead>
      <tbody>{r.data.map((i) => (
        <tr key={i.ticker}><td><a href={`/companies/${i.ticker}`}><b>{i.ticker}</b></a></td><td><Dir d={i.direction} /><Conf c={i.confidence} /></td>
          <td>{i.score}</td><td className="muted">{i.reason}</td></tr>))}</tbody>
    </table>
  );
}

function Analyzer() {
  const [text, setText] = useState("");
  const [res, setRes] = useState(null);
  return (
    <div className="card">
      <b>Analisis teks event (Analyst/Admin)</b>
      <div className="toolbar"><input value={text} onChange={(e) => setText(e.target.value)} placeholder="mis. Pemerintah naikkan royalti batu bara" />
        <button onClick={async () => setRes(await post("/events/analyze", { text }))}>Analisis</button></div>
      {res?.error && <p className="muted">{res.error.message}</p>}
      {res?.data && <><p><span className="tag">{res.data.event_type}</span></p>
        <table><tbody>{res.data.impacts.map((i) => <tr key={i.ticker}><td><b>{i.ticker}</b></td><td><Dir d={i.direction} /></td><td>{i.score}</td><td className="muted">{i.reason}</td></tr>)}</tbody></table></>}
    </div>
  );
}

export default function Events() {
  const evs = useApi("/events");
  const [open, setOpen] = useState(null);
  return (
    <>
      <PrintHeader title="Laporan Event → Impact" />
      <div className="toolbar" style={{ justifyContent: "space-between" }}><h1 style={{ margin: 0 }}>Event → Impact</h1><ExportPdf name="Event_Impact" /></div>
      <div className="muted">Event = berita yang cocok pola (kebijakan, harga komoditas, bencana). Dampak = inferensi kata kunci dengan keyakinan LOW dan besaran tetap ±0.5: untuk bahan riset, bukan prediksi.</div>
      <Analyzer />
      <h2>Event terdeteksi</h2>
      <Loading s={evs} />
      {evs.data?.map((e) => (
        <div key={e.id} className="row">
          <span className="tag">{e.event_type}</span> <a href="#" onClick={(x) => { x.preventDefault(); setOpen(open === e.id ? null : e.id); }}>{e.title}</a>
          <div className="muted">{day(e.ts)} · {e.publisher} · {e.impacts} emiten terdampak {safeUrl(e.url) && <a href={safeUrl(e.url)} target="_blank" rel="noreferrer">sumber</a>}</div>
          {open === e.id && <Impacts id={e.id} />}
        </div>
      ))}
      <Disclaimer />
    </>
  );
}

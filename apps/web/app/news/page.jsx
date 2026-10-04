"use client";
import { useState } from "react";
import { useApi, NewsList, Loading } from "../lib";

const COMM = ["", "NICKEL", "COAL", "CPO", "GOLD", "OIL", "COPPER"];

export default function News() {
  const [commodity, setCommodity] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [ticker, setTicker] = useState("");
  const qs = new URLSearchParams(Object.entries({ commodity, sentiment, ticker: ticker.toUpperCase() }).filter(([, v]) => v)).toString();
  const n = useApi(`/news${qs ? `?${qs}` : ""}`);
  return (
    <>
      <h1>News Intelligence</h1>
      <div className="muted">Sumber: Google News RSS (non-komersial). Sentimen & entitas dari aturan kata kunci atas judul, bukan membaca isi.</div>
      <div className="toolbar">
        <select style={{ width: 160 }} value={commodity} onChange={(e) => setCommodity(e.target.value)}>{COMM.map((c) => <option key={c} value={c}>{c || "Semua komoditas"}</option>)}</select>
        <select style={{ width: 160 }} value={sentiment} onChange={(e) => setSentiment(e.target.value)}>
          <option value="">Semua sentimen</option><option>POSITIVE</option><option>NEUTRAL</option><option>NEGATIVE</option></select>
        <input style={{ width: 140 }} placeholder="Ticker" value={ticker} onChange={(e) => setTicker(e.target.value)} />
      </div>
      <Loading s={n} />
      <NewsList items={n.data} />
    </>
  );
}

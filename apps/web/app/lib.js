"use client";
import { useEffect, useState } from "react";
import { DISCLAIMER } from "./disclaimerText";

// GET /api/v1/<path>; 401 → /login. Mengembalikan {data, error, loading}. error.code "NO_DATA" adalah hasil sah.
export function useApi(path) {
  const [state, set] = useState({ data: null, error: null, loading: !!path });
  useEffect(() => {
    if (!path) return set({ data: null, error: null, loading: false });
    set((s) => ({ ...s, loading: true }));
    fetch(`/api/v1${path}`).then(async (r) => {
      if (r.status === 401) return (window.location.href = "/login");
      const j = await r.json();
      set(r.ok ? { data: j, error: null, loading: false } : { data: null, error: j.detail ?? { code: "ERR", message: r.statusText }, loading: false });
    });
  }, [path]);
  return state;
}

export async function post(path, body) {
  const r = await fetch(`/api/v1${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const j = await r.json();
  return r.ok ? { data: j } : { error: j.detail ?? { message: r.statusText } };
}

// Data pihak ketiga (judul/URL berita, nama lokasi USGS) tidak dipercaya: URL hanya http(s), teks di-escape saat masuk HTML mentah.
export const safeUrl = (u) => (/^https?:\/\//i.test(u ?? "") ? u : null);
export const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

export const pct = (v) => (v == null ? "–" : `${v > 0 ? "+" : ""}${v.toFixed(2)}%`);
export const cls = (v) => (v > 0 ? "up" : v < 0 ? "down" : "");
export const num = (v, d = 0) => (v == null ? "–" : v.toLocaleString("id-ID", { maximumFractionDigits: d }));
export const idr = (v) => (v == null ? "–" : v >= 1e12 ? `Rp${num(v / 1e12, 1)} T` : v >= 1e9 ? `Rp${num(v / 1e9, 1)} M` : `Rp${num(v / 1e6, 1)} jt`);
export const day = (s) => (s ? s.slice(0, 10) : "");

export const Source = ({ type, name, asOf }) => (
  <span className="muted">
    {type === "SEED" && <span className="tag warn">SEED/mock</span>} {name} · {asOf}
  </span>
);

const SENT = { POSITIVE: ["up", "positif"], NEGATIVE: ["down", "negatif"], NEUTRAL: ["", "netral"] };
export const Sent = ({ s }) => (s ? <span className={`tag ${SENT[s][0]}`}>{SENT[s][1]}</span> : null);
export const Dir = ({ d }) => <span className={`tag ${d === "POSITIVE" ? "up" : d === "NEGATIVE" ? "down" : ""}`}>{d}</span>;
export const Conf = ({ c }) => <span className="tag">keyakinan {c}</span>;
export const Loading = ({ s }) => (s.loading ? <p className="muted">Memuat…</p> : null);

export function NewsList({ items }) {
  if (!items?.length) return <p className="muted">Berita: data tidak tersedia</p>;
  return items.map((n) => (
    <div key={n.url} className="row">
      {safeUrl(n.url) ? <a href={safeUrl(n.url)} target="_blank" rel="noreferrer">{n.title}</a> : n.title}
      <div className="muted">
        {n.publisher} · {day(n.published_at)} <Sent s={n.sentiment} />{" "}
        {n.entities?.slice(0, 5).map((e) => <span key={e} className="tag">{e}</span>)}
      </div>
    </div>
  ));
}

export const Disclaimer = () => <div className="banner disclaimer">{DISCLAIMER}</div>;

// Judul laporan yang hanya tampil saat dicetak/ekspor PDF.
export const PrintHeader = ({ title }) => (
  <div className="print-only" style={{ marginBottom: 12 }}>
    <div style={{ fontSize: 11, letterSpacing: 2 }}>IM-VEST INTELLIGENCE</div>
    <div style={{ fontSize: 20, fontWeight: 700 }}>{title}</div>
    <div style={{ fontSize: 11 }}>Dibuat {new Date().toLocaleString("id-ID")} · Sumber: Yahoo Finance (tidak resmi), Google News RSS, USGS, Open-Meteo</div>
  </div>
);

// Ekspor PDF = cetak halaman (Simpan sebagai PDF); nama berkas diambil dari judul dokumen.
export function ExportPdf({ name }) {
  const go = () => {
    const prev = document.title;
    document.title = `IM-VEST_${name}_${new Date().toISOString().slice(0, 10)}`;
    window.print();
    setTimeout(() => (document.title = prev), 500);
  };
  return <button className="ghost noprint" onClick={go} title="Simpan halaman ini sebagai PDF"><i className="ti ti-file-type-pdf" /> Export PDF</button>;
}

"use client";
import { useEffect, useRef, useState } from "react";
import { post } from "../lib";

const EXAMPLES = ["Apa yang bergerak hari ini?", "Analisis ANTM", "Saham terkait nikel", "Perusahaan apa yang terdampak event terbaru?",
  "Tampilkan aset nikel di peta", "Berita batu bara", "Risiko konsentrasi portofolio saya", "Klien mana yang perlu dihubungi hari ini?"];

export default function Copilot() {
  const [log, setLog] = useState([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const end = useRef(null);
  async function ask(text) {
    if (!text.trim() || busy) return;
    setBusy(true); setQ(""); setLog((l) => [...l, { role: "user", text }]);
    const r = await post("/copilot/chat", { message: text });
    setLog((l) => [...l, r.data ? { role: "bot", ...r.data } : { role: "bot", answer: r.error?.message ?? "Gagal", tools: [], links: [], sources: [] }]);
    setBusy(false);
  }
  useEffect(() => { const s = new URLSearchParams(window.location.search).get("q"); if (s) ask(s); }, []);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [log]);
  return (
    <>
      <h1>AI Copilot</h1>
      <div className="muted">Berbasis aturan: setiap jawaban berasal dari query data nyata (tool) yang ditampilkan di bawah jawaban, tanpa angka karangan. Bukan rekomendasi investasi.</div>
      <div className="toolbar">{EXAMPLES.map((e) => <button key={e} className="ghost" onClick={() => ask(e)}>{e}</button>)}</div>
      {log.map((m, i) => m.role === "user" ? <div key={i} className="msg user">{m.text}</div> : (
        <div key={i} className="msg bot">
          {m.answer}
          <div className="muted" style={{ marginTop: 8 }}>
            mode: {m.mode ?? "rules"} · tool: {m.tools.join(", ") || "-"} · sumber: {m.sources.join(", ") || "-"} · keyakinan {m.confidence}
          </div>
          <div>{m.links.map((l) => <a key={l.href + l.text} href={l.href} style={{ marginRight: 12 }}>{l.text}</a>)}</div>
        </div>
      ))}
      {busy && <p className="muted">Mencari…</p>}
      <form onSubmit={(e) => { e.preventDefault(); ask(q); }} style={{ position: "sticky", bottom: 0, background: "var(--bg)", padding: "12px 0" }}>
        <input placeholder="Tanya apa saja…" value={q} onChange={(e) => setQ(e.target.value)} />
      </form>
      <div ref={end} />
    </>
  );
}

"use client";
import { useState } from "react";

export default function Login() {
  const [err, setErr] = useState("");
  async function submit(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    const r = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: f.get("email"), password: f.get("password") }),
    });
    if (r.ok) window.location.href = "/";
    else setErr((await r.json()).detail?.message ?? "gagal");
  }
  return (
    <>
      <div className="text-center mb-4">
        <div className="brand-link" style={{ fontSize: 28 }}><i className="ti ti-radar-2" /> IM-VEST<small>INTELLIGENCE</small></div>
        <div className="muted mt-2">EVENT → IMPACT → COMPANY → STOCK → OPPORTUNITY → ACTION</div>
      </div>
      <form onSubmit={submit} className="card" style={{ display: "grid", gap: 12, padding: 24 }}>
        <h2 style={{ margin: 0 }}>Masuk</h2>
        <input name="email" type="email" placeholder="Email" required autoFocus />
        <input name="password" type="password" placeholder="Password" required />
        <button>Sign in</button>
        {err && <span className="down">{err}</span>}
        <div className="muted">Demo: investor@ / rm@ / admin@imvest.local</div>
      </form>
    </>
  );
}

"use client";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

// [href, label, ikon Tabler, peran minimum]
const LINKS = [
  ["/", "Dashboard", "home"], ["/news", "News", "news"], ["/events", "Event → Impact", "bolt"],
  ["/map", "Intelligence Map", "map-2"], ["/globe", "Globe 3D", "world"], ["/watchlist", "Watchlist & Alert", "bell"], ["/portfolio", "Portfolio", "briefcase"], ["/supply/NICKEL", "Supply Chain", "route"],
  ["/clients", "Clients", "users", "RM"], ["/copilot", "AI Copilot", "robot"],
];
const RANK = { INVESTOR: 0, RM: 1, ANALYST: 2, ADMIN: 3 };

export default function Shell({ children }) {
  const path = usePathname();
  const [me, setMe] = useState(null);
  const [open, setOpen] = useState(false);
  useEffect(() => { fetch("/api/v1/auth/me").then((r) => (r.ok ? r.json() : null)).then(setMe); }, [path]);
  useEffect(() => setOpen(false), [path]);
  const out = async (e) => { e.preventDefault(); await fetch("/api/v1/auth/logout", { method: "POST" }); window.location.href = "/login"; };

  if (path === "/login") return <div className="page page-center"><div className="container container-tight py-4">{children}</div></div>;
  const active = (h) => (h === "/" ? path === "/" : path.startsWith(h.startsWith("/supply") ? "/supply" : h));
  return (
    <div className="page">
      <aside className="navbar navbar-vertical navbar-expand-lg noprint">
        <div className="container-fluid">
          <button className="navbar-toggler" type="button" aria-label="Menu" onClick={() => setOpen(!open)}><span className="navbar-toggler-icon" /></button>
          <h1 className="navbar-brand navbar-brand-autodark">
            <a href="/" className="brand-link"><i className="ti ti-radar-2" /> IM-VEST <small>INTELLIGENCE</small></a>
          </h1>
          <div className={`collapse navbar-collapse ${open ? "show" : ""}`}>
            <ul className="navbar-nav pt-lg-3">
              {LINKS.filter(([, , , min]) => !min || (me && RANK[me.role] >= RANK[min])).map(([h, t, ic]) => (
                <li key={h} className={`nav-item ${active(h) ? "active" : ""}`}>
                  <a className="nav-link" href={h}><span className="nav-link-icon"><i className={`ti ti-${ic}`} /></span><span className="nav-link-title">{t}</span></a>
                </li>
              ))}
            </ul>
            <div className="mt-auto pt-4 w-100">
              {me && <div className="muted mb-2"><i className="ti ti-user" /> {me.email}<br />{me.role}</div>}
              <a href="#" className="btn btn-outline-secondary btn-sm w-100" onClick={out}><i className="ti ti-logout me-1" />Keluar</a>
            </div>
          </div>
        </div>
      </aside>
      <div className="page-wrapper">
        <div className="page-body"><div className="container-xl">{children}</div></div>
        <footer className="footer footer-transparent d-print-none noprint">
          <div className="container-xl muted">Template: Tabler (MIT) · Tema Ocean Depths · Data: Yahoo Finance (tidak resmi), Google News RSS, USGS, Open-Meteo · Bukan rekomendasi investasi</div>
        </footer>
      </div>
    </div>
  );
}

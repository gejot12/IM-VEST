"use client";
/**
 * Globe 3D aset untuk halaman ANALISA SAHAM. Mandiri (tanpa dependensi selain React): CesiumJS dimuat dari CDN,
 * data dari API publik IM-VEST (GET, tanpa login). Salin berkas ini apa adanya ke proyek lain (Vite/Next).
 *
 *   <AssetMap ticker="ANTM" onAnalyze={(t) => navigate(`/saham/${t}`)} />
 *
 * - Default: menampilkan aset milik emiten `ticker` dan terbang ke lokasinya.
 * - Pemilih "Wilayah": menampilkan SEMUA aset (emiten lain + bandara/pelabuhan umum) di provinsi itu.
 * - Klik titik / baris daftar: detail + tombol "Analisa saham" (callback `onAnalyze`).
 * Lokasi adalah perkiraan kawasan dan belum diverifikasi (ditandai di UI).
 */
import { useEffect, useMemo, useRef, useState } from "react";

type Feature = { geometry: { coordinates: [number, number] }; properties: Record<string, any> };
type Region = { province: string; count: number };

const CESIUM = "https://cesium.com/downloads/cesiumjs/releases/1.120/Build/Cesium";
const TYPES: Record<string, { label: string; color: string }> = {
  MINE: { label: "Tambang", color: "#f1c40f" },
  SMELTER: { label: "Smelter / pabrik logam", color: "#2ecc71" },
  PORT: { label: "Pelabuhan / terminal", color: "#3498db" },
  POWER_PLANT: { label: "Pembangkit listrik", color: "#b57edc" },
  GAS_FIELD: { label: "Lapangan migas", color: "#00bcd4" },
  FACTORY: { label: "Pabrik", color: "#e67e22" },
  PLANTATION: { label: "Perkebunan", color: "#8bc34a" },
  TOLL_ROAD: { label: "Jalan tol", color: "#ff7043" },
  AIRPORT: { label: "Bandara", color: "#5c6bc0" },
  BRANCH: { label: "Kantor cabang bank", color: "#ec407a" },
  REGIONAL: { label: "Kantor wilayah bank", color: "#ffffff" },
  OFFICE: { label: "Kantor pusat", color: "#90a4ae" },
};

let cesiumPromise: Promise<any> | null = null;
function loadCesium(): Promise<any> {
  const w = window as any;
  if (w.Cesium) return Promise.resolve(w.Cesium);
  if (!cesiumPromise) {
    cesiumPromise = new Promise((resolve, reject) => {
      const css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = `${CESIUM}/Widgets/widgets.css`;
      document.head.appendChild(css);
      const s = document.createElement("script");
      s.src = `${CESIUM}/Cesium.js`;
      s.onload = () => resolve(w.Cesium);
      s.onerror = () => reject(new Error("CesiumJS gagal dimuat (butuh akses ke cesium.com)"));
      document.head.appendChild(s);
    });
  }
  return cesiumPromise;
}

export default function AssetMap({
  ticker,
  apiBase = "https://im-vest-api.vercel.app",
  height = 440,
  theme = "light",
  onAnalyze,
}: {
  ticker: string;
  apiBase?: string;
  height?: number;
  theme?: "light" | "dark";
  onAnalyze?: (ticker: string) => void;
}) {
  const box = useRef<HTMLDivElement>(null);
  const viewer = useRef<any>(null);
  const pickRef = useRef<(i: number) => void>(() => {});
  const [ready, setReady] = useState(false);
  const [regions, setRegions] = useState<Region[]>([]);
  const [province, setProvince] = useState(""); // "" = aset emiten ini
  const [features, setFeatures] = useState<Feature[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [status, setStatus] = useState("Memuat peta…");

  const dark = theme === "dark";
  const c = dark
    ? { bg: "#1a2332", fg: "#e6edf7", mut: "#8da2b8", line: "#2b3a50", chip: "#202c3f", link: "#7fd4d4" }
    : { bg: "#ffffff", fg: "#0f172a", mut: "#64748b", line: "#e2e8f0", chip: "#f1f5f9", link: "#0369a1" };

  // 1) Globe sekali per komponen
  useEffect(() => {
    let alive = true;
    loadCesium()
      .then((C) => {
        if (!alive || !box.current) return;
        C.Ion.defaultAccessToken = ""; // tanpa token ion: citra Esri tanpa key
        const v = new C.Viewer(box.current, {
          baseLayer: C.ImageryLayer.fromProviderAsync(
            C.ArcGisMapServerImageryProvider.fromUrl("https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer"),
          ),
          baseLayerPicker: false, geocoder: false, homeButton: false, navigationHelpButton: false,
          sceneModePicker: true, animation: false, timeline: false, fullscreenButton: false, infoBox: false, selectionIndicator: true,
        });
        v.camera.setView({ destination: C.Cartesian3.fromDegrees(118, -2.5, 4_500_000) });
        const handler = new C.ScreenSpaceEventHandler(v.scene.canvas);
        handler.setInputAction((e: any) => {
          const p = v.scene.pick(e.position);
          if (p?.id?.assetIndex !== undefined) pickRef.current(p.id.assetIndex);
        }, C.ScreenSpaceEventType.LEFT_CLICK);
        viewer.current = v;
        setReady(true);
      })
      .catch((e) => setStatus(String(e?.message ?? e)));
    return () => {
      alive = false;
      viewer.current?.destroy?.();
      viewer.current = null;
    };
  }, []);

  // 2) Daftar wilayah (sekali)
  useEffect(() => {
    fetch(`${apiBase}/api/v1/public/regions`)
      .then((r) => (r.ok ? r.json() : []))
      .then((j) => setRegions(Array.isArray(j) ? j : []))
      .catch(() => setRegions([]));
  }, [apiBase]);

  // 3) Data aset: per emiten, atau per wilayah
  useEffect(() => {
    const q = province ? `province=${encodeURIComponent(province)}` : `ticker=${encodeURIComponent(ticker)}`;
    setStatus("Memuat aset…");
    setSelected(null);
    fetch(`${apiBase}/api/v1/public/assets?${q}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`API ${r.status}`))))
      .then((j) => {
        const f: Feature[] = j.features ?? [];
        setFeatures(f);
        setStatus(f.length ? "" : province ? "Tidak ada aset tercatat di wilayah ini." : `Belum ada aset tercatat untuk ${ticker}.`);
      })
      .catch((e) => {
        setFeatures([]);
        setStatus(`Aset tidak dapat dimuat: ${e.message}`);
      });
  }, [ticker, province, apiBase]);

  // 4) Gambar titik + terbang ke wilayahnya
  useEffect(() => {
    const v = viewer.current;
    const C = (window as any).Cesium;
    if (!ready || !v || !C) return;
    v.entities.removeAll();
    features.forEach((f, i) => {
      const p = f.properties;
      const [lng, lat] = f.geometry.coordinates;
      v.entities.add({
        assetIndex: i,
        position: C.Cartesian3.fromDegrees(lng, lat),
        point: {
          pixelSize: p.ticker === ticker ? 14 : 10,
          color: C.Color.fromCssColorString(TYPES[p.asset_type]?.color ?? "#3b82f6"),
          outlineColor: C.Color.WHITE, outlineWidth: 2,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        label: p.asset_type === "BRANCH" || p.asset_type === "REGIONAL" ? undefined : {
          text: p.ticker ?? String(p.name).replace(/^Bandara |^Pelabuhan /, "").replace(/ \(.*$/, ""),
          font: "12px sans-serif", pixelOffset: new C.Cartesian2(0, -16),
          fillColor: C.Color.WHITE, outlineColor: C.Color.BLACK, outlineWidth: 3, style: C.LabelStyle.FILL_AND_OUTLINE,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
      });
    });
    if (features.length) {
      const lngs = features.map((f) => f.geometry.coordinates[0]);
      const lats = features.map((f) => f.geometry.coordinates[1]);
      const pad = 0.6;
      v.camera.flyTo({
        destination: C.Rectangle.fromDegrees(Math.min(...lngs) - pad, Math.min(...lats) - pad, Math.max(...lngs) + pad, Math.max(...lats) + pad),
        duration: 1.3,
      });
    }
  }, [features, ready, ticker]);

  const choose = (i: number) => {
    setSelected(i);
    const v = viewer.current;
    const C = (window as any).Cesium;
    const f = features[i];
    if (v && C && f) {
      const [lng, lat] = f.geometry.coordinates;
      v.camera.flyTo({ destination: C.Cartesian3.fromDegrees(lng, lat, 250_000), duration: 1 });
    }
  };
  pickRef.current = (i) => setSelected(i);

  const sel = selected !== null ? features[selected]?.properties : null;
  const sorted = useMemo(() => features.map((f, i) => ({ f, i })).sort((a, b) => String(a.f.properties.ticker ?? "~").localeCompare(String(b.f.properties.ticker ?? "~"))), [features]);
  const used = useMemo(() => [...new Set(features.map((f) => f.properties.asset_type))], [features]);

  return (
    <div style={{ background: c.bg, color: c.fg, border: `1px solid ${c.line}`, borderRadius: 10, padding: 12 }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center", marginBottom: 8 }}>
        <b>Peta aset {province ? `— wilayah ${province}` : `— ${ticker}`}</b>
        <span style={{ flex: 1 }} />
        <label style={{ fontSize: 13, color: c.mut }}>
          Wilayah:{" "}
          <select
            value={province}
            onChange={(e) => setProvince(e.target.value)}
            style={{ background: c.chip, color: c.fg, border: `1px solid ${c.line}`, borderRadius: 6, padding: "4px 8px" }}
          >
            <option value="">Aset {ticker}</option>
            {regions.map((r) => (
              <option key={r.province} value={r.province}>{r.province} ({r.count})</option>
            ))}
          </select>
        </label>
      </div>

      <div style={{ position: "relative" }}>
        <div ref={box} style={{ height, borderRadius: 8, overflow: "hidden", background: "#0b1220" }} />
        {status && (
          <div style={{ position: "absolute", left: 10, bottom: 10, background: "rgba(0,0,0,.65)", color: "#fff", padding: "4px 10px", borderRadius: 6, fontSize: 12 }}>
            {status}
          </div>
        )}
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, margin: "8px 0", fontSize: 12, color: c.mut }}>
        {used.map((t) => (
          <span key={t} style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
            <i style={{ width: 10, height: 10, borderRadius: 5, background: TYPES[t]?.color ?? "#3b82f6", display: "inline-block", border: "1px solid rgba(0,0,0,.25)" }} />
            {TYPES[t]?.label ?? t}
          </span>
        ))}
      </div>

      {sel && (
        <div style={{ border: `1px solid ${c.line}`, background: c.chip, borderRadius: 8, padding: 10, marginBottom: 8, fontSize: 14 }}>
          <b>{sel.ticker ? `${sel.ticker} — ` : ""}{sel.name}</b>
          <div style={{ color: c.mut }}>
            {TYPES[sel.asset_type]?.label ?? sel.asset_type}{sel.commodity ? ` · ${sel.commodity}` : ""} · {sel.province}
            {sel.sector ? ` · ${sel.sector}` : ""}
          </div>
          <div style={{ fontSize: 12, color: c.mut }}>{sel.verified ? "Lokasi terverifikasi" : "Lokasi kawasan perkiraan, belum diverifikasi"}</div>
          {sel.ticker && onAnalyze && (
            <button
              onClick={() => onAnalyze(sel.ticker)}
              style={{ marginTop: 6, background: c.link, color: dark ? "#0b1220" : "#fff", border: 0, borderRadius: 6, padding: "5px 12px", cursor: "pointer", fontWeight: 600 }}
            >
              Analisa saham {sel.ticker}
            </button>
          )}
        </div>
      )}

      {sorted.length > 0 && (
        <div style={{ maxHeight: 180, overflowY: "auto", borderTop: `1px solid ${c.line}` }}>
          {sorted.map(({ f, i }) => (
            <div
              key={i}
              onClick={() => choose(i)}
              style={{ padding: "6px 4px", borderBottom: `1px solid ${c.line}`, cursor: "pointer", fontSize: 13, background: i === selected ? c.chip : "transparent" }}
            >
              <b>{f.properties.ticker ?? "Umum"}</b> · {f.properties.name}
              <span style={{ color: c.mut }}> — {TYPES[f.properties.asset_type]?.label ?? f.properties.asset_type}, {f.properties.province}</span>
            </div>
          ))}
        </div>
      )}
      <div style={{ fontSize: 11, color: c.mut, marginTop: 6 }}>
        Lokasi aset adalah perkiraan kawasan. Citra: Esri World Imagery · Globe: CesiumJS · Data: IM-VEST Intelligence. Bukan nasihat investasi.
      </div>
    </div>
  );
}

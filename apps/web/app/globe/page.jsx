"use client";
import { useEffect, useRef, useState } from "react";
import { esc, safeUrl } from "../lib";

const CESIUM = "https://cesium.com/downloads/cesiumjs/releases/1.120/Build/Cesium";
const COLORS = { NICKEL: "#2ecc71", COAL: "#9aa0a6", GOLD: "#f1c40f", COPPER: "#e67e22" };
const load = (tag, attrs) => new Promise((res, rej) => { const el = Object.assign(document.createElement(tag), attrs); el.onload = res; el.onerror = rej; document.head.appendChild(el); });
const get = (p) => fetch(`/api/v1/map${p}`).then((r) => (r.ok ? r.json() : { features: [] }));

export default function Globe() {
  const el = useRef(null);
  const [status, setStatus] = useState("Memuat globe…");
  useEffect(() => {
    let viewer;
    (async () => {
      try {
        await load("link", { rel: "stylesheet", href: `${CESIUM}/Widgets/widgets.css` });
        if (!window.Cesium) await load("script", { src: `${CESIUM}/Cesium.js` });
        const C = window.Cesium;
        C.Ion.defaultAccessToken = "";   // tanpa token ion: pakai citra Esri keyless
        viewer = new C.Viewer(el.current, {
          baseLayer: C.ImageryLayer.fromProviderAsync(C.ArcGisMapServerImageryProvider.fromUrl("https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer")),
          baseLayerPicker: false, geocoder: false, homeButton: false, navigationHelpButton: false, sceneModePicker: true, animation: false, timeline: false, fullscreenButton: false,
        });
        viewer.camera.flyTo({ destination: C.Cartesian3.fromDegrees(118, -3, 4_200_000), duration: 0 });
        const [assets, quakes] = await Promise.all([get("/assets"), get("/earthquakes")]);
        for (const f of assets.features) {
          const [lng, lat] = f.geometry.coordinates, p = f.properties;
          viewer.entities.add({
            position: C.Cartesian3.fromDegrees(lng, lat), name: `${p.ticker} — ${p.name}`,
            point: { pixelSize: 12, color: C.Color.fromCssColorString(COLORS[p.commodity] ?? "#3b82f6"), outlineColor: C.Color.WHITE, outlineWidth: 2 },
            label: { text: p.ticker, font: "13px sans-serif", pixelOffset: new C.Cartesian2(0, -18), fillColor: C.Color.WHITE, outlineColor: C.Color.BLACK, outlineWidth: 3, style: C.LabelStyle.FILL_AND_OUTLINE },
            description: `${esc(p.asset_type)} · ${esc(p.commodity)}<br>${esc(p.province)}<br><i>${p.verified ? "terverifikasi" : "lokasi perkiraan, belum diverifikasi"}</i><br><a href="/companies/${encodeURIComponent(p.ticker)}">Halaman emiten</a>`,
          });
        }
        for (const f of quakes.features) {
          const [lng, lat] = f.geometry.coordinates, p = f.properties;
          viewer.entities.add({
            position: C.Cartesian3.fromDegrees(lng, lat), name: `Gempa M${p.mag}`,
            point: { pixelSize: p.mag * 3, color: C.Color.RED.withAlpha(0.45), outlineColor: C.Color.RED, outlineWidth: 1 },
            description: `${esc(p.place)}<br>kedalaman ${Math.round(p.depth_km)} km` + (safeUrl(p.url) ? `<br><a href="${esc(safeUrl(p.url))}" target="_blank" rel="noreferrer">USGS</a>` : ""),
          });
        }
        setStatus(`${assets.features.length} aset · ${quakes.features.length} gempa. Klik titik untuk detail.`);
      } catch (e) { setStatus(`Globe gagal dimuat: ${e?.message ?? e}. Butuh akses ke cesium.com dan WebGL.`); }
    })();
    return () => viewer?.destroy();
  }, []);
  return (
    <>
      <h1>Globe 3D <span className="tag warn">prototipe</span></h1>
      <div className="muted">{status}</div>
      <div className="banner">Lokasi aset adalah <b>perkiraan kawasan</b>. Citra: Esri World Imagery; globe: CesiumJS (muat dari CDN). Gempa: USGS.</div>
      <div ref={el} style={{ height: 600, borderRadius: 8, overflow: "hidden" }} />
    </>
  );
}

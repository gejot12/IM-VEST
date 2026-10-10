"use client";
import { useEffect, useRef, useState } from "react";
import { esc, safeUrl } from "../lib";
import { ASSET_TYPES } from "../assetTypes";
import AssetFilters, { initialSectors, initialTypes, visible } from "../assetFilters";

const CESIUM = "https://cesium.com/downloads/cesiumjs/releases/1.120/Build/Cesium";
const load = (tag, attrs) => new Promise((res, rej) => { const el = Object.assign(document.createElement(tag), attrs); el.onload = res; el.onerror = rej; document.head.appendChild(el); });
const get = (p) => fetch(`/api/v1/map${p}`).then((r) => (r.ok ? r.json() : { features: [] }));

// Infobox Cesium berlatar putih: paksa warna teks gelap agar terbaca.
const box = (html) => `<div style="color:#111;background:#fff;font:14px/1.5 sans-serif;padding:8px">${html}</div>`;

export default function Globe() {
  const el = useRef(null);
  const [status, setStatus] = useState("Memuat globe…");
  const [types, setTypes] = useState(initialTypes);
  const [sectors, setSectors] = useState(initialSectors);
  const [ready, setReady] = useState(false);
  const [counts, setCounts] = useState({ total: 0, shown: 0, quakes: 0 });
  const ents = useRef([]);   // [{ entity, props }] untuk filter tanpa membuat ulang globe
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
          const entity = viewer.entities.add({
            position: C.Cartesian3.fromDegrees(lng, lat), name: `${p.ticker} — ${p.name}`,
            point: { pixelSize: 12, color: C.Color.fromCssColorString(ASSET_TYPES[p.asset_type]?.color ?? "#3b82f6"), outlineColor: C.Color.WHITE, outlineWidth: 2 },
            label: { text: p.ticker, font: "13px sans-serif", pixelOffset: new C.Cartesian2(0, -18), fillColor: C.Color.WHITE, outlineColor: C.Color.BLACK, outlineWidth: 3, style: C.LabelStyle.FILL_AND_OUTLINE },
            description: box(`<b>${esc(ASSET_TYPES[p.asset_type]?.label ?? p.asset_type)}</b>${p.commodity ? " · " + esc(p.commodity) : ""}<br>${esc(p.sector ?? "")}<br>${esc(p.province)}<br><i>${p.verified ? "terverifikasi" : "lokasi kawasan perkiraan, belum diverifikasi"}</i><br><a href="/companies/${encodeURIComponent(p.ticker)}" target="_blank">Halaman emiten</a>`),
          });
          ents.current.push({ entity, props: p });
        }
        for (const f of quakes.features) {
          const [lng, lat] = f.geometry.coordinates, p = f.properties;
          viewer.entities.add({
            position: C.Cartesian3.fromDegrees(lng, lat), name: `Gempa M${p.mag}`,
            point: { pixelSize: p.mag * 3, color: C.Color.RED.withAlpha(0.45), outlineColor: C.Color.RED, outlineWidth: 1 },
            description: box(`${esc(p.place)}<br>kedalaman ${Math.round(p.depth_km)} km` + (safeUrl(p.url) ? `<br><a href="${esc(safeUrl(p.url))}" target="_blank" rel="noreferrer">USGS</a>` : "")),
          });
        }
        setCounts((c) => ({ ...c, total: assets.features.length, quakes: quakes.features.length }));
        setReady(true);
        setStatus("");
      } catch (e) { setStatus(`Globe gagal dimuat: ${e?.message ?? e}. Butuh akses ke cesium.com dan WebGL.`); }
    })();
    return () => viewer?.destroy();
  }, []);

  useEffect(() => {
    if (!ready) return;
    let n = 0;
    for (const { entity, props } of ents.current) { entity.show = visible(props, sectors, types); n += entity.show ? 1 : 0; }
    setCounts((c) => ({ ...c, shown: n }));
  }, [sectors, types, ready]);
  return (
    <>
      <h1>Globe 3D <span className="tag warn">prototipe</span></h1>
      <div className="muted">{status || `${counts.shown} dari ${counts.total} aset tampil · ${counts.quakes} gempa. Klik titik untuk detail.`}</div>
      <AssetFilters sectors={sectors} setSectors={setSectors} types={types} setTypes={setTypes} />
      <div className="banner">Lokasi aset adalah <b>perkiraan kawasan</b>. Citra: Esri World Imagery; globe: CesiumJS (muat dari CDN). Gempa: USGS.</div>
      <div ref={el} style={{ height: 600, borderRadius: 8, overflow: "hidden" }} />
    </>
  );
}

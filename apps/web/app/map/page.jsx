"use client";
import { useEffect, useRef, useState } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
import { safeUrl } from "../lib";

const get = (p) => fetch(`/api/v1/map${p}`).then(async (r) => (r.ok ? r.json() : { error: (await r.json()).detail }));
// Popup dibangun dari node DOM + textContent (tanpa setHTML): nilai dari USGS/DB tidak pernah diparse sebagai HTML.
function node(lines) {
  const box = document.createElement("div");
  for (const l of lines) {
    const row = document.createElement("div");
    for (const part of [].concat(l)) {
      if (typeof part === "string") row.append(part);
      else if (part.href) { const a = document.createElement("a"); a.href = part.href; a.textContent = part.text; if (part.ext) { a.target = "_blank"; a.rel = "noreferrer"; } row.append(a); }
      else { const b = document.createElement("b"); b.textContent = part.b; row.append(b); }
    }
    box.append(row);
  }
  return box;
}
const empty = { type: "FeatureCollection", features: [] };

export default function MapPage() {
  const el = useRef(null), mapRef = useRef(null), weather = useRef({});
  const [on, setOn] = useState({ assets: true, earthquakes: true, weather: false, fires: false });
  const [notes, setNotes] = useState({});
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let map;
    (async () => {
      const mod = await import("maplibre-gl");
      const maplibregl = mod.default?.Map ? mod.default : mod;
      map = mapRef.current = new maplibregl.Map({ container: el.current, style: "https://tiles.openfreemap.org/styles/liberty", center: [118, -2.5], zoom: 4.2 });
      map.addControl(new maplibregl.NavigationControl());
      map.on("load", () => {
        for (const id of ["assets", "earthquakes", "fires"]) map.addSource(id, { type: "geojson", data: empty });
        map.addLayer({ id: "fires", type: "circle", source: "fires", paint: { "circle-radius": 3, "circle-color": "#ff5a1f", "circle-opacity": 0.8 } });
        map.addLayer({ id: "earthquakes", type: "circle", source: "earthquakes", paint: { "circle-radius": ["*", ["get", "mag"], 2.2], "circle-color": "#e74c3c", "circle-opacity": 0.45, "circle-stroke-color": "#e74c3c", "circle-stroke-width": 1 } });
        map.addLayer({ id: "assets", type: "circle", source: "assets", paint: { "circle-radius": 8, "circle-color": ["match", ["get", "commodity"], "NICKEL", "#2ecc71", "COAL", "#444", "GOLD", "#f1c40f", "COPPER", "#e67e22", "#3b82f6"], "circle-stroke-color": "#fff", "circle-stroke-width": 2 } });
        const popup = (e, lines) => new maplibregl.Popup().setLngLat(e.lngLat).setDOMContent(node(lines)).addTo(map);
        map.on("click", "assets", (e) => {
          const p = e.features[0].properties, w = weather.current[p.id];
          popup(e, [[{ b: p.ticker }, ` — ${p.name}`], `${p.asset_type} · ${p.commodity}`, p.province,
            p.verified === "true" || p.verified === true ? "terverifikasi" : "lokasi perkiraan, belum diverifikasi",
            ...(w ? [`Cuaca: ${w.temperature_2m}°C, hujan ${w.precipitation} mm, angin ${w.wind_speed_10m} km/j`] : []),
            { href: `/companies/${encodeURIComponent(p.ticker)}`, text: "Halaman emiten" }]);
        });
        map.on("click", "earthquakes", (e) => {
          const p = e.features[0].properties;
          popup(e, [[{ b: `M ${p.mag}` }, ` ${p.place}`], `kedalaman ${Math.round(p.depth_km)} km`, ...(safeUrl(p.url) ? [{ href: safeUrl(p.url), text: "USGS", ext: true }] : [])]);
        });
        for (const l of ["assets", "earthquakes"]) { map.on("mouseenter", l, () => (map.getCanvas().style.cursor = "pointer")); map.on("mouseleave", l, () => (map.getCanvas().style.cursor = "")); }
        setReady(true);
      });
    })();
    return () => map?.remove();
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    const q = new URLSearchParams(window.location.search).get("ticker");
    for (const id of ["assets", "earthquakes", "fires"]) map.setLayoutProperty(id, "visibility", on[id] ? "visible" : "none");
    (async () => {
      if (on.assets) {
        const d = await get(`/assets${q ? `?ticker=${q}` : ""}`);
        map.getSource("assets").setData(d.features ? d : empty);
        if (d.features?.length === 1) map.flyTo({ center: d.features[0].geometry.coordinates, zoom: 8 });
      }
      if (on.earthquakes) { const d = await get("/earthquakes"); map.getSource("earthquakes").setData(d.features ? d : empty); setNotes((n) => ({ ...n, earthquakes: d.error?.message ?? d.attribution })); }
      if (on.fires) { const d = await get("/fires"); map.getSource("fires").setData(d.features ? d : empty); setNotes((n) => ({ ...n, fires: d.error?.message ?? d.attribution })); }
      if (on.weather) { const d = await get("/weather"); weather.current = d.by_asset ?? {}; setNotes((n) => ({ ...n, weather: d.error?.message ?? `${d.attribution} · klik aset untuk melihat` })); }
    })();
  }, [on, ready]);

  const Toggle = ({ id, label }) => <label><input type="checkbox" checked={on[id]} onChange={(e) => setOn({ ...on, [id]: e.target.checked })} />{label}</label>;
  return (
    <>
      <h1>Intelligence Map</h1>
      <div className="toolbar">
        <Toggle id="assets" label="Aset perusahaan" /><Toggle id="earthquakes" label="Gempa 7 hari (USGS)" />
        <Toggle id="weather" label="Cuaca di aset" /><Toggle id="fires" label="Titik api (NASA FIRMS)" />
      </div>
      {Object.entries(notes).map(([k, v]) => v && <div key={k} className="muted">{k}: {v}</div>)}
      <div className="banner">Lokasi aset adalah <b>perkiraan kawasan</b> (belum diverifikasi ke dokumen perusahaan). Gambar peta © OpenStreetMap contributors, OpenFreeMap.</div>
      <div id="map" ref={el} />
      <div className="muted" style={{ marginTop: 8 }}>Warna aset: hijau nikel · abu batu bara · kuning emas · oranye tembaga. Layer cuaca (Open-Meteo) gratis hanya untuk non-komersial. Layer FIRMS butuh env FIRMS_MAP_KEY.</div>
    </>
  );
}

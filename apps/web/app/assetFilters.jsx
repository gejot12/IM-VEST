"use client";
import { ASSET_TYPES, SECTORS } from "./assetTypes";

// Filter bersama peta 2D dan globe 3D: chip sektor + jenis aset, tombol "Semua"/"Kosongkan", bisa dilipat.
function Group({ title, items, value, onChange, dot }) {
  const set = (v) => onChange(Object.fromEntries(Object.keys(items).map((k) => [k, v])));
  const n = Object.keys(items).filter((k) => value[k]).length;
  return (
    <div className="filter-group">
      <div className="filter-head">
        <b>{title}</b> <span className="muted">{n}/{Object.keys(items).length}</span>
        <button type="button" className="ghost mini" onClick={() => set(true)}>Semua</button>
        <button type="button" className="ghost mini" onClick={() => set(false)}>Kosongkan</button>
      </div>
      <div className="chips">
        {Object.entries(items).map(([k, v]) => (
          <label key={k} className={`chip ${value[k] ? "on" : ""}`}>
            <input type="checkbox" checked={!!value[k]} onChange={(e) => onChange({ ...value, [k]: e.target.checked })} />
            {dot && <span className="dot" style={{ background: v.color }} />}
            {v.label}
          </label>
        ))}
      </div>
    </div>
  );
}

export const initialSectors = () => Object.fromEntries(Object.keys(SECTORS).map((k) => [k, true]));
export const initialTypes = () => Object.fromEntries(Object.keys(ASSET_TYPES).map((k) => [k, !["OFFICE", "BRANCH", "REGIONAL"].includes(k)]));
export const visible = (props, sectors, types) => !!sectors[props.sector] && !!types[props.asset_type];

export default function AssetFilters({ sectors, setSectors, types, setTypes }) {
  return (
    <details open className="card filters">
      <summary>Filter sektor &amp; jenis aset</summary>
      <Group title="Sektor" items={SECTORS} value={sectors} onChange={setSectors} />
      <Group title="Jenis aset" items={ASSET_TYPES} value={types} onChange={setTypes} dot />
    </details>
  );
}

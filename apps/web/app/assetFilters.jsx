"use client";
import { ASSET_TYPES, SECTORS } from "./assetTypes";

// Filter bersama peta 2D dan globe 3D: pilih sektor dan jenis aset (centang), plus "Semua"/"Kosongkan".
function Group({ title, items, value, onChange, dot }) {
  const set = (v) => onChange(Object.fromEntries(Object.keys(items).map((k) => [k, v])));
  return (
    <div style={{ margin: "6px 0" }}>
      <div className="toolbar" style={{ margin: 0 }}>
        <b style={{ minWidth: 90 }}>{title}</b>
        <button className="ghost" style={{ padding: "2px 10px" }} onClick={() => set(true)}>Semua</button>
        <button className="ghost" style={{ padding: "2px 10px" }} onClick={() => set(false)}>Kosongkan</button>
        {Object.entries(items).map(([k, v]) => (
          <label key={k}>
            <input type="checkbox" checked={!!value[k]} onChange={(e) => onChange({ ...value, [k]: e.target.checked })} />
            {dot && <span style={{ width: 10, height: 10, borderRadius: 5, background: v.color, display: "inline-block" }} />}
            {v.label}
          </label>
        ))}
      </div>
    </div>
  );
}

export const initialSectors = () => Object.fromEntries(Object.keys(SECTORS).map((k) => [k, true]));
export const initialTypes = () => Object.fromEntries(Object.keys(ASSET_TYPES).map((k) => [k, k !== "OFFICE"]));
export const visible = (props, sectors, types) => !!sectors[props.sector] && !!types[props.asset_type];

export default function AssetFilters({ sectors, setSectors, types, setTypes }) {
  return (
    <div className="card" style={{ margin: "10px 0" }}>
      <Group title="Sektor" items={SECTORS} value={sectors} onChange={setSectors} />
      <Group title="Jenis aset" items={ASSET_TYPES} value={types} onChange={setTypes} dot />
    </div>
  );
}

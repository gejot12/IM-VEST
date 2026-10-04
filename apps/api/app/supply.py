"""Rantai pasok per komoditas: tahap GENERIK industri (bukan klaim hubungan antar-perusahaan) + aset/emiten yang tercatat di tiap tahap.

Hanya tahap yang punya tipe aset di DB yang berisi data; tahap hilir ditandai 'tidak ada data' dan tidak diisi tebakan.
"""
from fastapi import APIRouter, Depends, HTTPException

from . import db
from .auth import require

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require("INVESTOR"))])

STAGES = {  # (nama tahap, tipe aset di tabel assets atau None bila belum ada data)
    "NICKEL": [("Penambangan bijih", "MINE"), ("Peleburan / pengolahan (smelter)", "SMELTER"), ("Bahan baku baterai", None), ("Baterai", None), ("Kendaraan listrik", None)],
    "COAL": [("Penambangan", "MINE"), ("Pengangkutan & pelabuhan", "PORT"), ("Pembangkit listrik / ekspor", "POWER_PLANT")],
    "GOLD": [("Penambangan", "MINE"), ("Pemurnian (refinery)", "SMELTER"), ("Perdagangan / perhiasan", None)],
    "COPPER": [("Penambangan", "MINE"), ("Peleburan (smelter)", "SMELTER"), ("Produk jadi (kabel, dll)", None)],
    "CPO": [("Perkebunan", None), ("Pabrik kelapa sawit", "FACTORY"), ("Refinery / ekspor", "PORT")],
}


@router.get("/supply-chain/{commodity}")
def supply_chain(commodity: str):
    code = commodity.upper()
    if code not in STAGES:
        raise HTTPException(404, {"code": "NO_DATA", "message": f"Rantai pasok {commodity} tidak tersedia"})
    with db.connect() as con:
        stages = []
        for name, asset_type in STAGES[code]:
            assets = [] if not asset_type else [dict(r) for r in con.execute("""
                SELECT c.ticker, a.name, a.asset_type, l.province, l.verified_at IS NOT NULL AS verified
                FROM assets a JOIN companies c ON c.id=a.company_id JOIN locations l ON l.id=a.location_id
                WHERE a.commodity=? AND a.asset_type=? ORDER BY c.ticker""", (code, asset_type))]
            stages.append({"stage": name, "asset_type": asset_type, "assets": assets})
        exposed = [r["ticker"] for r in con.execute("""SELECT c.ticker FROM company_commodities cc JOIN companies c ON c.id=cc.company_id
                                                       WHERE cc.commodity=? ORDER BY c.ticker""", (code,))]
    return {"commodity": code, "stages": stages, "exposed_companies": exposed,
            "note": "Tahap bersifat generik; tidak menyatakan hubungan pasokan antar perusahaan. Aset berasal dari data internal (perkiraan)."}

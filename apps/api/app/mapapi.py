"""Layer peta (GeoJSON). Aset = data internal (perkiraan, belum diverifikasi); gempa = USGS; cuaca = Open-Meteo.

Respons pihak ketiga di-cache di memori agar tidak membebani sumbernya. FIRMS (api hotspot) butuh MAP_KEY gratis
dari NASA: set env FIRMS_MAP_KEY untuk mengaktifkan; tanpa itu layer melapor NEEDS_KEY, bukan data kosong palsu.
"""
import json
import os
import time
import urllib.request

from fastapi import APIRouter, Depends, HTTPException

from . import db
from .auth import require

router = APIRouter(prefix="/api/v1/map", dependencies=[Depends(require("INVESTOR"))])
_cache: dict[str, tuple[float, object]] = {}
BBOX = (-11.5, 95.0, 6.5, 141.5)  # lat_min, lng_min, lat_max, lng_max (Indonesia)


def cached(key: str, ttl: int, load):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    val = load()
    _cache[key] = (time.time(), val)
    return val


def _json(url: str):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "imvest/0.1"}), timeout=25) as r:
        return json.loads(r.read())


def in_bbox(lng: float, lat: float) -> bool:
    return BBOX[0] <= lat <= BBOX[2] and BBOX[1] <= lng <= BBOX[3]


@router.get("/layers")
def layers():
    return [{"id": "assets", "name": "Aset perusahaan", "status": "OK", "note": "Lokasi perkiraan, belum diverifikasi"},
            {"id": "earthquakes", "name": "Gempa (USGS, 7 hari)", "status": "OK"},
            {"id": "weather", "name": "Cuaca di aset (Open-Meteo)", "status": "OK", "note": "Gratis hanya non-komersial"},
            {"id": "fires", "name": "Titik api (NASA FIRMS)", "status": "OK" if os.environ.get("FIRMS_MAP_KEY") else "NEEDS_KEY"}]


@router.get("/assets")
def assets(ticker: str | None = None, commodity: str | None = None):
    sql = """SELECT a.id, a.asset_type, a.name, a.commodity, a.status, l.lat, l.lng, l.province, l.verified_at,
                    c.ticker, c.name AS company, s.name AS source, s.source_type
             FROM assets a JOIN locations l ON l.id=a.location_id JOIN companies c ON c.id=a.company_id
             JOIN data_sources s ON s.id=l.source_id WHERE 1=1"""
    args = []
    if ticker:
        sql += " AND c.ticker=?"; args.append(ticker.upper())
    if commodity:
        sql += " AND a.commodity=?"; args.append(commodity.upper())
    with db.connect() as con:
        rows = con.execute(sql, args).fetchall()
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [r["lng"], r["lat"]]},
         "properties": {k: r[k] for k in r.keys() if k not in ("lat", "lng")} | {"verified": r["verified_at"] is not None}} for r in rows]}


def load_quakes():
    d = _json("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson")
    feats = [f for f in d["features"] if in_bbox(*f["geometry"]["coordinates"][:2])]
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": f["geometry"]["coordinates"][:2]},
         "properties": {"mag": f["properties"]["mag"], "place": f["properties"]["place"], "time": f["properties"]["time"],
                        "depth_km": f["geometry"]["coordinates"][2], "url": f["properties"]["url"]}} for f in feats],
        "source": "USGS", "attribution": "Data courtesy of the U.S. Geological Survey"}


@router.get("/earthquakes")
def earthquakes():
    try:
        return cached("quakes", 600, load_quakes)
    except Exception as e:
        raise HTTPException(502, {"code": "UPSTREAM", "message": f"USGS tidak dapat dijangkau: {e}"})


def load_weather():
    with db.connect() as con:
        pts = con.execute("""SELECT a.id, l.lat, l.lng FROM assets a JOIN locations l ON l.id=a.location_id""").fetchall()
    if not pts:
        return {}
    d = _json("https://api.open-meteo.com/v1/forecast?latitude=" + ",".join(str(p["lat"]) for p in pts) +
              "&longitude=" + ",".join(str(p["lng"]) for p in pts) + "&current=temperature_2m,precipitation,wind_speed_10m")
    d = d if isinstance(d, list) else [d]
    return {p["id"]: {k: x["current"][k] for k in ("temperature_2m", "precipitation", "wind_speed_10m")} | {"time": x["current"]["time"]}
            for p, x in zip(pts, d)}


@router.get("/weather")
def weather():
    """Cuaca terkini per id aset. Atribusi: Open-Meteo.com (CC BY 4.0)."""
    try:
        return {"by_asset": cached("weather", 1800, load_weather), "attribution": "Weather data by Open-Meteo.com"}
    except Exception as e:
        raise HTTPException(502, {"code": "UPSTREAM", "message": f"Open-Meteo tidak dapat dijangkau: {e}"})


@router.get("/fires")
def fires():
    key = os.environ.get("FIRMS_MAP_KEY")
    if not key:
        raise HTTPException(503, {"code": "NEEDS_KEY", "message": "Set FIRMS_MAP_KEY (gratis dari NASA FIRMS) untuk layer ini"})
    def load():
        w, s, e, n = BBOX[1], BBOX[0], BBOX[3], BBOX[2]
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/VIIRS_SNPP_NRT/{w},{s},{e},{n}/1"
        with urllib.request.urlopen(url, timeout=30) as r:
            lines = r.read().decode().strip().splitlines()
        head = lines[0].split(",")
        rows = [dict(zip(head, ln.split(","))) for ln in lines[1:]]
        return {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]},
             "properties": {"date": r["acq_date"], "confidence": r.get("confidence")}} for r in rows[:2000]],
            "attribution": "NASA FIRMS"}
    try:
        return cached("fires", 900, load)
    except Exception as e:
        raise HTTPException(502, {"code": "UPSTREAM", "message": f"FIRMS error: {e}"})

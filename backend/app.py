from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import os, csv, io, httpx

# -------------------- Setup --------------------
load_dotenv()
FIRMS_KEY = os.getenv("NASA_FIRMS_API_KEY", "").strip()

if not FIRMS_KEY:
    # हम चलने देंगे, पर first request पर helpful error देंगे
    pass

app = FastAPI(title="Wildfire Tracker Backend", version="1.0.0")

# CORS: React (localhost:3000) के लिए खुला
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],               # dev में *; production में specific origin दें
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FIRMS sources: MODIS_NRT, VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT (commonly used)
VALID_SOURCES = {"MODIS_NRT", "VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT"}

# -------------------- Helpers --------------------
def parse_csv_to_records(csv_bytes: bytes) -> List[Dict[str, Any]]:
    """FIRMS CSV → list[dict] (lat/lon numeric, others as-is)"""
    text = csv_bytes.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    out = []
    for row in reader:
        # Normalize & cast
        def fget(k, default=None): return row.get(k, default)
        try:
            lat = float(fget("latitude", "0") or 0)
            lon = float(fget("longitude", "0") or 0)
        except ValueError:
            continue
        rec = {
            "latitude": lat,
            "longitude": lon,
            "acq_date": fget("acq_date"),
            "acq_time": fget("acq_time"),
            "satellite": fget("satellite"),
            "confidence": fget("confidence"),
            "bright_ti4": fget("bright_ti4") or fget("brightness"),
            "bright_ti5": fget("bright_ti5"),
            "frp": fget("frp"),
            "instrument": fget("instrument"),
            "version": fget("version"),
        }
        out.append(rec)
    return out

async def fetch_firms_csv(client: httpx.AsyncClient, url: str) -> bytes:
    r = await client.get(url, timeout=30)
    if r.status_code == 401:
        raise HTTPException(401, detail="Invalid or missing FIRMS API key.")
    if r.status_code >= 400:
        raise HTTPException(r.status_code, detail=f"FIRMS error: {r.text[:200]}")
    return r.content

def filter_records(
    recs: List[Dict[str, Any]],
    min_conf: Optional[int] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    if min_conf is not None:
        def val(c):
            # confidence कभी-कभी string/int होता है
            try:
                return int(str(c).split(".")[0])
            except:
                return -1
        recs = [r for r in recs if val(r.get("confidence")) >= min_conf]
    if limit:
        recs = recs[:limit]
    return recs

# -------------------- Routes --------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Wildfire Tracker backend is running 🚀"}

@app.get("/fires/area")
async def fires_area(
    bbox: str = Query(..., description="minLon,minLat,maxLon,maxLat (e.g. 70,10,90,30)"),
    days: int = Query(1, ge=1, le=7, description="Past N days (1-7)"),
    source: str = Query("VIIRS_SNPP_NRT", description="FIRMS source"),
    min_confidence: Optional[int] = Query(None, ge=0, le=100),
    limit: Optional[int] = Query(1000, ge=1, le=10000),
):
    """
    Get fires within a bounding box for the last N days.
    """
    if source not in VALID_SOURCES:
        raise HTTPException(400, detail=f"Invalid source. Try one of {sorted(VALID_SOURCES)}.")

    if not FIRMS_KEY:
        raise HTTPException(400, detail="Set NASA_FIRMS_API_KEY in .env")

    # bbox format expected by FIRMS: lonMin,latMin,lonMax,latMax
    # Endpoint (CSV):
    # https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{source}/{lonMin,latMin,lonMax,latMax}/{days}
    bbox_clean = bbox.replace(" ", "")
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{FIRMS_KEY}/{source}/{bbox_clean}/{days}"

    async with httpx.AsyncClient() as client:
        csv_bytes = await fetch_firms_csv(client, url)
    recs = parse_csv_to_records(csv_bytes)
    recs = filter_records(recs, min_confidence, limit)
    return {"count": len(recs), "source": source, "bbox": bbox_clean, "days": days, "fires": recs}

@app.get("/fires/country/{iso3}")
async def fires_country(
    iso3: str,
    days: int = Query(1, ge=1, le=7),
    source: str = Query("VIIRS_SNPP_NRT"),
    min_confidence: Optional[int] = Query(None, ge=0, le=100),
    limit: Optional[int] = Query(1000, ge=1, le=10000),
):
    """
    Get fires for an ISO3 country code (e.g. IND, USA, AUS) for last N days.
    """
    if source not in VALID_SOURCES:
        raise HTTPException(400, detail=f"Invalid source. Try one of {sorted(VALID_SOURCES)}.")

    if not FIRMS_KEY:
        raise HTTPException(400, detail="Set NASA_FIRMS_API_KEY in .env")

    iso3 = iso3.upper().strip()
    # Endpoint (CSV):
    # https://firms.modaps.eosdis.nasa.gov/api/country/csv/{key}/{source}/{ISO3}/{days}
    url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{FIRMS_KEY}/{source}/{iso3}/{days}"

    async with httpx.AsyncClient() as client:
        csv_bytes = await fetch_firms_csv(client, url)
    recs = parse_csv_to_records(csv_bytes)
    recs = filter_records(recs, min_confidence, limit)
    return {"count": len(recs), "source": source, "country": iso3, "days": days, "fires": recs}
# Wildfire Tracker

A small full-stack app to fetch and serve NASA FIRMS wildfire detections and visualize them (Frontend + FastAPI backend).

This repository contains:

- `backend/` — FastAPI backend that proxies NASA FIRMS CSV endpoints and exposes simple JSON APIs.
- `frontend/` — React app (Create React App) that consumes the backend APIs.

## Features

- Query FIRMS by bounding box or ISO3 country code.
- Filter by confidence and result limits.
- Simple health and root endpoints for quick checks.

## Architecture

- Backend: FastAPI, httpx for upstream requests, served with Uvicorn.
- Frontend: React (Create React App), standard dev server at port 3000 in development.

## Prerequisites

- Python 3.10+ (the virtualenv in `backend/env` appears configured for Python 3.10+)
- Node 16+ / npm (for the frontend)
- A NASA FIRMS API key to query FIRMS endpoints (set in backend `.env` as `NASA_FIRMS_API_KEY`).

## Environment variables

Create a `.env` file in the `backend/` directory (there is a `.env` in the repo; ensure values are set). At minimum:

```
NASA_FIRMS_API_KEY=your_nasa_firms_api_key_here
```

## Backend — install & run (recommended)

Two options are shown for Windows PowerShell where `Activate.ps1` may be blocked by system policy.

1) Use the venv python executable directly (no PowerShell activation required):

```powershell
cd backend
.\env\Scripts\python.exe -m pip install -r requirements.txt
.\env\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

2) Or activate the venv in PowerShell (may require changing execution policy):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
cd backend
. .\env\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

If you prefer CMD, use the batch activation script:

```cmd
cd backend
env\Scripts\activate.bat
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Notes:
- The backend ASGI app is defined in `backend/app.py` as `app` (module path: `app:app` when running from inside `backend/`).
- If you get PowerShell script signing errors, using the venv python or CMD activation avoids that.

## Frontend — install & run

```bash
cd frontend
npm install
npm start
```

The React dev server typically runs at http://localhost:3000 and the backend at http://localhost:8000.

## API Reference (backend)

Base URL (development): http://127.0.0.1:8000

- GET /health
  - Returns {"status":"ok"}

- GET /
  - Returns a small message confirming the backend is running.

- GET /fires/area
  - Query parameters:
    - `bbox` (required) — minLon,minLat,maxLon,maxLat (e.g. `70,10,90,30`)
    - `days` (optional, default 1) — integer 1–7
    - `source` (optional, default `VIIRS_SNPP_NRT`) — one of `MODIS_NRT`, `VIIRS_SNPP_NRT`, `VIIRS_NOAA20_NRT`
    - `min_confidence` (optional) — 0–100 integer
    - `limit` (optional, default 1000) — max number of records

  - Example:

    ```bash
    curl "http://127.0.0.1:8000/fires/area?bbox=70,10,90,30&days=1&min_confidence=60&limit=200"
    ```

- GET /fires/country/{ISO3}
  - Path parameter: ISO3 country code (e.g. `IND`, `USA`, `AUS`)
  - Query parameters: `days`, `source`, `min_confidence`, `limit` (same meaning as above)

  - Example:

    ```bash
    curl "http://127.0.0.1:8000/fires/country/USA?days=2&min_confidence=50"
    ```

Response shape (JSON):

```
{
  "count": <number>,
  "source": "VIIRS_SNPP_NRT",
  "bbox" or "country": "...",
  "days": <n>,
  "fires": [ { "latitude": <float>, "longitude": <float>, "acq_date": "YYYY-MM-DD", "acq_time": "HHMM", ... }, ... ]
}
```

## Troubleshooting

- PowerShell script blocked (Activate.ps1 not signed):
  - Use the venv python executable directly (recommended), or change execution policy for CurrentUser:

    ```powershell
    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
    ```

  - Or use `activate.bat` from cmd.exe.

- If backend returns a 400 with message `Set NASA_FIRMS_API_KEY in .env`, ensure your `backend/.env` contains the correct key and restart the server.

## Development notes

- The backend uses `httpx.AsyncClient` to request CSV from the NASA FIRMS API, parses CSV, normalizes records, and exposes filtered JSON.
- Valid FIRMS sources are defined in `backend/app.py` as `VALID_SOURCES`.

## Contributing

- Fixes, improvements, and documentation updates are welcome. Open a PR against `main` or create an issue.

## License

See the `LICENSE` file in the repository root.

---

If you'd like, I can also:

- Add a short `docs/` section with example requests and sample responses saved as JSON.
- Add a Postman collection or simple tests for the API.

Tell me which extras you'd like and I'll add them.

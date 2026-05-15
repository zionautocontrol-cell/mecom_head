import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import DB_PATH, HOST, PORT, TRUSTED_API_KEYS
from database import (
    delete_site,
    get_alarms,
    get_daily_reports,
    get_recent_realtime,
    get_site,
    get_sites,
    init_db,
    register_site,
    save_alarm,
    save_daily_report,
    save_realtime,
    update_site,
)

app = FastAPI(title="MECOM Head Office Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

init_db()


def verify_request(request: Request):
    site_id = request.headers.get("X-Site-ID", "")
    api_key = request.headers.get("X-API-Key", "")
    if not site_id:
        raise HTTPException(status_code=400, detail="Missing X-Site-ID header")
    expected_key = TRUSTED_API_KEYS.get(site_id) if TRUSTED_API_KEYS else None
    if expected_key is not None and api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return site_id


def verify_admin(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    from config import ADMIN_USERNAME, ADMIN_PASSWORD
    token = auth[7:]
    try:
        decoded = json.loads(token)
        if decoded.get("user") != ADMIN_USERNAME or decoded.get("pass") != ADMIN_PASSWORD:
            raise ValueError
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid admin credentials")
    return True


@app.get("/")
def root():
    return {"status": "ok", "server": "MECOM Head Office", "version": "1.0"}


# ── Site management ──────────────────────────────────────

@app.get("/sites")
def list_sites():
    return get_sites()


@app.get("/sites/{site_id}")
def get_site_detail(site_id: str):
    site = get_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@app.post("/api/register")
def api_register(site_id: str, name: str = "", api_key: str = ""):
    local_auth = TRUSTED_API_KEYS.get(site_id) if TRUSTED_API_KEYS else None
    if local_auth and api_key != local_auth:
        raise HTTPException(status_code=403, detail="API key mismatch")
    ok = register_site(site_id, name or site_id, api_key)
    if not ok:
        raise HTTPException(status_code=409, detail="Site already exists")
    return {"success": True, "site_id": site_id}


@app.delete("/api/sites/{site_id}")
def api_delete_site(site_id: str):
    ok = delete_site(site_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Site not found")
    return {"success": True, "site_id": site_id}


@app.put("/api/sites/{site_id}")
async def api_update_site(site_id: str, request: Request):
    body = await request.json()
    name = body.get("name", "")
    api_key = body.get("api_key", "")
    ok = update_site(site_id, name, api_key)
    if not ok:
        raise HTTPException(status_code=404, detail="Site not found")
    return {"success": True, "site_id": site_id}


# ── Data ingestion endpoints ─────────────────────────────

@app.post("/api/daily-report")
async def api_daily_report(request: Request):
    site_id = verify_request(request)
    form = await request.form()
    file = form.get("file")
    if not file:
        raise HTTPException(status_code=400, detail="Missing file")
    csv_data = await file.read()
    report_date = datetime.now().strftime("%Y-%m-%d")
    report_id = save_daily_report(site_id, report_date, csv_data)
    register_site(site_id)
    return {"success": True, "report_id": report_id, "date": report_date}


@app.post("/api/alarm")
async def api_alarm(request: Request):
    site_id = verify_request(request)
    body = await request.json()
    alarm_id = save_alarm(
        site_id=site_id,
        alarm_type=body.get("alarm_type", ""),
        alarm_id=body.get("alarm_id", ""),
        message=body.get("message", ""),
        severity=body.get("severity", ""),
        value=body.get("value", 0.0),
        timestamp=body.get("timestamp", datetime.now().isoformat()),
    )
    register_site(site_id)
    return {"success": True, "alarm_id": alarm_id}


@app.post("/api/realtime")
async def api_realtime(request: Request):
    site_id = verify_request(request)
    body = await request.json()
    save_realtime(
        site_id=site_id,
        timestamp=body.get("timestamp", ""),
        status=body.get("status", "disconnected"),
        bits_json=json.dumps(body.get("bits", [])),
        words_json=json.dumps(body.get("words", [])),
        accum_heat=body.get("accum_heat", 0.0),
    )
    register_site(site_id)
    return {"success": True}


# ── Data query endpoints ─────────────────────────────────

@app.get("/api/alarms")
def api_get_alarms(site_id: Optional[str] = Query(None), limit: int = 50):
    return get_alarms(site_id, limit)


@app.get("/api/realtime-log")
def api_get_realtime_log(site_id: str, limit: int = 100):
    return get_recent_realtime(site_id, limit)


@app.get("/api/daily-reports")
def api_get_daily_reports(site_id: Optional[str] = Query(None), limit: int = 10):
    return get_daily_reports(site_id, limit)


@app.get("/api/health")
def api_health():
    sites = get_sites()
    return {
        "status": "healthy",
        "site_count": len(sites),
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

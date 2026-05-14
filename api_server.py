import json
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import DB_PATH, HOST, PORT, TRUSTED_API_KEYS
from database import (
    get_alarms,
    get_recent_realtime,
    get_sites,
    init_db,
    register_site,
    save_alarm,
    save_daily_report,
    save_realtime,
)

app = FastAPI(title="MECOM Head Office Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

init_db()


def verify_request(request: Request):
    site_id = request.headers.get("X-Site-ID", "")
    api_key = request.headers.get("X-API-Key", "")
    if not site_id:
        raise HTTPException(status_code=400, detail="Missing X-Site-ID header")
    if TRUSTED_API_KEYS and api_key != TRUSTED_API_KEYS.get(site_id, api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return site_id


@app.get("/")
def root():
    return {"status": "ok", "server": "MECOM Head Office"}


@app.get("/sites")
def list_sites():
    return get_sites()


@app.post("/api/register")
def api_register(site_id: str, name: str = "", api_key: str = ""):
    ok = register_site(site_id, name, api_key)
    return {"success": ok, "site_id": site_id}


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


@app.get("/api/alarms")
def api_get_alarms(site_id: str = "", limit: int = 50):
    return get_alarms(site_id or None, limit)


@app.get("/api/realtime-log")
def api_get_realtime_log(site_id: str, limit: int = 100):
    return get_recent_realtime(site_id, limit)


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

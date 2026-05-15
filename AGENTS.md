# MECOM Head Office Server

## Architecture

- `api_server.py` — FastAPI server (port 8000)
- `dashboard.py` — Streamlit admin dashboard
- `database.py` — SQLite database layer
- `config.py` — Environment-variable based configuration

## Data Flow

Field Site (mecom_hmi_head) → HTTP POST → Head Office (mecom_head)
- `/api/realtime` — Real-time sensor data (every 0.5s)
- `/api/alarm` — Alarm events
- `/api/daily-report` — CSV daily report (every 01:00)

## Key Config (env vars)

| Variable | Default | Description |
|----------|---------|-------------|
| MECOM_HEAD_HOST | 0.0.0.0 | Bind address |
| MECOM_HEAD_PORT | 8000 | Port |
| MECOM_TRUSTED_KEYS | "" | Comma-separated site_id=key pairs |
| MECOM_ADMIN_USER | admin | Dashboard login username |
| MECOM_ADMIN_PASS | admin123 | Dashboard login password |
